/* probe_rinput_prof.c -- M-A3 per-step noise profiler (stage405, duty 6r).
 *
 * Instrumented mirror of sab_rinput_blind_rotate (same public primitives:
 * wrap_psi / CMUX / sub_a_homtr_opt / final doubling), measured stage by
 * stage against the plaintext model. Noise extraction uses mod-2^63 folding:
 * dev = phase - model reduced into (-2^62, 2^62] maps e and e +- 2^63
 * (HT-7 wrap spuria) to the SAME value -- exact pseudo-strip under the
 * two-guard-bit invariant |mu|+|e| < 2^62 (HT-8), no blind spot.
 *
 * Primitives calibrated per trial on the SAME key:
 *   sig_eps  : decomposition error of a uniform torus polynomial (l=1,Bg=23)
 *   sig_ks_h / sig_ks_m1 : single aut-KS noise (w=1+N and w=2N-1); each
 *              calibration is first validated on a zero-mask input, where
 *              the KS must be EXACT (dev == 0) -- convention check
 *   sig_ep0 / sig_ep1 : single CMUX EP noise, selector message 0/1, operands
 *              = two independent full-entropy-mask ciphertexts with RANDOM
 *              full-entropy messages. (stage403's synthetic calibration
 *              measured the MESSAGE DIFFERENCE as noise when the selector
 *              bit was 1; fixed here: dev = phase(R) - phase(selected).)
 *   sig_psi / sig_suba : single Psi / sub_a step on a known-phase input
 *
 * Prediction = exact event-counted recursion along the real data flow
 * (per slot): bit m=1: sig2 <- sig2[src] + (wrap ? 1.5*sig_ks^2 : 0)
 *                 + sig_ep1^2;
 *              bit m=0: sig2 <- sig2 + sig_ep0^2;
 *              sub_a : sig2 += sig_ks_h^2 / 2;   (U_a weight analysis)
 *              final doubling: sig2 *= 4.
 * Gates: per-stage measured/predicted within 1.3x (|log2 ratio| <= 0.38)
 * and final pair reconciliation within 1.3x. The mirror is asserted
 * BIT-IDENTICAL to the stock sab_rinput_bootstrap_wo_extract (the rotation
 * is deterministic: no fresh randomness inside). */
#include <sab_rinput.h>
#include <sab.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

static int G_in_N = 256, G_out_N = 2048, G_h = 6, G_prec = 3;
static double G_sigma_exp = -70;
static int G_coarse = 0; /* 1: measure only suba/final stages */
static uint64_t G_rprec = 0;

static void rinput_phase(TorusPolynomial out, PVW_TMLWE in,
    PVW_TMLWE_Key key){
  memset(out->coeffs, 0, sizeof(out->coeffs[0]) * out->N);
  for (size_t idx = 0; idx < (size_t) in->k; idx++){
    polynomial_mul_addto_torus(out, in->a[idx], key->s[idx][0]);
  }
  polynomial_sub_torus_polynomials(out, in->b[0], out);
}

/* exact +-2^63 pseudo-strip (valid: |true dev| < 2^62 by HT-8 guard) */
static inline int64_t fold63(int64_t d){
  return (int64_t)(((uint64_t) d + ((uint64_t) 1 << 62))
      & (((uint64_t) 1 << 63) - 1)) - ((int64_t) 1 << 62);
}

/* negacyclic X^e multiply: (X^e f)[i] = +- f[(i-e) mod 2N] */
static void mul_xai(uint64_t * out, const uint64_t * f, int e, int N){
  const int twoN = 2 * N;
  memset(out, 0, sizeof(uint64_t) * N);
  for (int i = 0; i < N; i++){
    int j = i - e;
    j %= twoN; if (j < 0) j += twoN;
    if (j < N) out[i] += f[j];
    else out[i] = (uint64_t)((int64_t) out[i] - (int64_t) f[j - N]);
  }
}
/* sigma_{-1}: x[0]=p[0]; x[i] = -p[N-i] for 0<i<N */
static void perm_m1(uint64_t * x, const uint64_t * p, int N){
  x[0] = p[0];
  for (int i = 1; i < N; i++)
    x[i] = (uint64_t)(-(int64_t) p[N - i]);
}
/* sigma_{1+N}: flip odd coefficients */
static void perm_1pN(uint64_t * x, const uint64_t * p, int N){
  for (int i = 0; i < N; i++)
    x[i] = (i & 1) ? (uint64_t)(-(int64_t) p[i]) : p[i];
}

static uint64_t lcg_next(uint64_t * s){
  *s = *s * 6364136223846793005ULL + 1442695040888963407ULL;
  return *s;
}

/* int64 negacyclic helpers for deterministic DC tracking */
static void dc_shift_addto(int64_t * out, const int64_t * in, int e, int N){
  const int twoN = 2 * N;
  for (int i = 0; i < N; i++){
    if(!in[i]) continue;
    int j = i + e;
    j %= twoN; if (j < 0) j += twoN;
    if(j < N) out[j] += in[i];
    else out[j - N] -= in[i];
  }
}

static double now_us(void){
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1e6 + ts.tv_nsec / 1e3;
}

/* ---------- primitive calibrations (single ops, known phases) ---------- */

typedef struct {
  double sig_eps, sig_ks_h, sig_ks_m1, sig_ep0, sig_ep1, sig_psi, sig_suba;
  double sig_ep0_s, sig_ep1_s;  /* setup-regime operands (zero masks, TV b) */
} prim_t;

static double rms_of(int N, const int64_t * dv){
  double acc = 0;
  for (int i = 0; i < N; i++) acc += (double) dv[i] * (double) dv[i];
  return sqrt(acc / N);
}

/* decomposition error of a uniform torus poly via the REAL decompose */
static double calib_eps(PVW_TMLWE_Key key, int Bg_bit){
  const int N = key->s[0][0]->N;
  PVW_TMLWE triv = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  TorusPolynomial * dec = polynomial_new_array_of_torus_polynomials(N, 2);
  uint64_t s = 0xA24BAED4963EE407ULL;
  for (int i = 0; i < N; i++) triv->b[0]->coeffs[i] = lcg_next(&s);
  memset(triv->a[0]->coeffs, 0, sizeof(uint64_t) * N);
  pvmtmlwe_decompose(dec, triv, Bg_bit, 1);
  const uint64_t scale = 1ULL << (64 - Bg_bit);
  int64_t dv[8192];
  for (int i = 0; i < N; i++)
    dv[i] = (int64_t)(triv->b[0]->coeffs[i]
        - (uint64_t)((int64_t) dec[1]->coeffs[i] * (int64_t) scale));
  free_array_of_polynomials(dec, 2);
  free_pvmtmlwe(triv);
  return rms_of(N, dv);
}

/* trivial ciphertext: full-entropy mask, full-entropy message in b;
 * zero_mask: zero mask (KS must then be exact); seed NULL: zero b too.
 * G_lcg_triv=0: masks/messages from the library AES RNG (pipeline-real). */
static int G_lcg_triv = 1;
static void make_triv(PVW_TMLWE t, uint64_t * seed, int N, int zero_mask){
  if(!G_lcg_triv && !zero_mask && seed){
    uint64_t buf[2];
    for (int i = 0; i < N; i++){
      generate_random_bytes(sizeof(buf), (uint8_t *) buf);
      t->a[0]->coeffs[i] = buf[0];
      t->b[0]->coeffs[i] = buf[1];
    }
    return;
  }
  for (int i = 0; i < N; i++){
    t->a[0]->coeffs[i] = (zero_mask || !seed) ? 0 : lcg_next(seed);
    t->b[0]->coeffs[i] = seed ? lcg_next(seed) : 0;
  }
}

static void phase_perm_check(PVW_TMLWE_Key key, PVW_TMLWE_KS_Key ks,
    uint64_t w, TorusPolynomial ph, int N, const char * name){
  /* zero mask: KS must be exact; validates the permutation convention */
  PVW_TMLWE triv = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  PVW_TMLWE rot = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  make_triv(triv, NULL, N, 1);
  uint64_t seed = 0xDEADBEEFCAFEF00DULL;
  for (int i = 0; i < N; i++) triv->b[0]->coeffs[i] = lcg_next(&seed);
  pvmtmlwe_eval_automorphism(rot, triv, w, ks);
  rinput_phase(ph, triv, key);
  uint64_t x[8192];
  if (w == 1ULL + (uint64_t) N) perm_1pN(x, ph->coeffs, N);
  else perm_m1(x, ph->coeffs, N);
  rinput_phase(ph, rot, key);
  int bad = 0;
  for (int i = 0; i < N; i++)
    if(fold63((int64_t) ph->coeffs[i] - (int64_t) x[i]) != 0) bad++;
  printf("CONV-CHECK %s: %s (%d nonzero dev)\n", name,
      bad == 0 ? "OK" : "WRONG-CONVENTION", bad);
  free_pvmtmlwe(rot); free_pvmtmlwe(triv);
}

/* single aut-KS noise on a full-entropy-mask input */
static double calib_ks(PVW_TMLWE_Key key, PVW_TMLWE_KS_Key ks, uint64_t w,
    uint64_t * seed, TorusPolynomial ph, int N){
  PVW_TMLWE triv = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  PVW_TMLWE rot = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  make_triv(triv, seed, N, 0);
  pvmtmlwe_eval_automorphism(rot, triv, w, ks);
  rinput_phase(ph, triv, key);
  uint64_t x[8192];
  if (w == 1ULL + (uint64_t) N) perm_1pN(x, ph->coeffs, N);
  else perm_m1(x, ph->coeffs, N);
  rinput_phase(ph, rot, key);
  int64_t dv[8192];
  for (int i = 0; i < N; i++)
    dv[i] = fold63((int64_t) ph->coeffs[i] - (int64_t) x[i]);
  free_pvmtmlwe(rot); free_pvmtmlwe(triv);
  return rms_of(N, dv);
}

/* single CMUX: dev = phase(R) - phase(selected) = pure EP noise.
 * setup=1: operands mimic the pipeline's FIRST bit (zero masks, TV-
 * quantized b-values) instead of full-entropy masks/messages. */
static double calib_ep(PVW_TMLWE_Key key, SAB_RINPUT_Key ri, int msg_sel,
    uint64_t * seed, TorusPolynomial ph, int N, int setup){
  PVW_TMLWE A = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  PVW_TMLWE B = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  PVW_TMLWE R = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  if(setup){
    for (int i = 0; i < N; i++){
      A->a[0]->coeffs[i] = 0; B->a[0]->coeffs[i] = 0;
      A->b[0]->coeffs[i] = int2torus((3 * i + 1) & 7, 5);
      B->b[0]->coeffs[i] = int2torus((5 * i + 2) & 7, 5);
    }
  }else{
    make_triv(A, seed, N, 0);
    make_triv(B, seed, N, 0);
  }
  MAT_TRGSW_DFT sel = mat_trgsw_alloc_new_DFT_sample((int) ri->mat_key->T,
      (int) ri->mat_key->Q, (int) key->k, 1, N);
  mat_trgsw_monomial_DFT_sample(sel, msg_sel, 0, ri->mat_key);
  sab_rinput_CMUX(R, A, B, sel, ri);
  rinput_phase(ph, msg_sel ? B : A, key);
  uint64_t ref[8192];
  memcpy(ref, ph->coeffs, sizeof(uint64_t) * N);
  rinput_phase(ph, R, key);
  int64_t dv[8192];
  for (int i = 0; i < N; i++)
    dv[i] = fold63((int64_t) ph->coeffs[i] - (int64_t) ref[i]);
  free_mat_trgsw_DFT(sel);
  free_pvmtmlwe(R); free_pvmtmlwe(B); free_pvmtmlwe(A);
  return rms_of(N, dv);
}

/* first-bit EP calibration on the TRUE pipeline operands AND the TRUE
 * first-bit selector instance (passed in; its message = m0 = gaps[0]&1):
 * pairs (arr[j], arr[j-1]); reference = the input this selector selects. */
static double calib_ep_arr2(PVW_TMLWE_Key key, SAB_RINPUT_Key ri,
    PVW_TMLWE * arr, MAT_TRGSW_DFT sel, int msg_sel, TorusPolynomial ph,
    int in_N){
  const int N = (int) ri->out_N;
  PVW_TMLWE R = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  double acc = 0; long cnt = 0;
  const int jsamp = in_N > 32 ? 32 : in_N;
  for (int j = 1; j < jsamp; j++){
    sab_rinput_CMUX(R, arr[j], arr[j - 1], sel, ri);
    rinput_phase(ph, msg_sel ? arr[j - 1] : arr[j], key);
    uint64_t ref[8192];
    memcpy(ref, ph->coeffs, sizeof(uint64_t) * N);
    rinput_phase(ph, R, key);
    for (int i = 0; i < N; i++){
      int64_t dv = fold63((int64_t) ph->coeffs[i] - (int64_t) ref[i]);
      acc += (double) dv * dv; cnt++;
    }
  }
  free_pvmtmlwe(R);
  return cnt ? sqrt(acc / cnt) : 0;
}

/* single Psi: expected = ((t+ft) + Y(t-ft))/2, t = sigma_{-1} phi */
static double calib_psi(PVW_TMLWE_Key key, SAB_RINPUT_Key ri,
    uint64_t * seed, TorusPolynomial ph, int N){
  PVW_TMLWE triv = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  PVW_TMLWE out = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  make_triv(triv, seed, N, 0);
  sab_rinput_wrap_psi(out, triv, ri);
  rinput_phase(ph, triv, key);
  uint64_t t[8192], ft[8192], sp[8192], sm[8192], ysm[8192];
  perm_m1(t, ph->coeffs, N);
  perm_1pN(ft, t, N);
  for (int i = 0; i < N; i++){
    sp[i] = (uint64_t)((int64_t) t[i] + (int64_t) ft[i]);
    sm[i] = (uint64_t)((int64_t) t[i] - (int64_t) ft[i]);
  }
  mul_xai(ysm, sm, 2, N);
  rinput_phase(ph, out, key);
  int64_t dv[8192];
  for (int i = 0; i < N; i++){
    int64_t raw = (int64_t) sp[i] + (int64_t) ysm[i];
    dv[i] = fold63((int64_t) ph->coeffs[i] - (raw >> 1));
  }
  free_pvmtmlwe(out); free_pvmtmlwe(triv);
  return rms_of(N, dv);
}

/* single sub_a on slot 0: expected = (Y^{2a0} sp + Y^{2a1} sm)/2 */
static double calib_suba(PVW_TMLWE_Key key, SAB_RINPUT_Key ri,
    uint64_t * seed, TorusPolynomial ph, int N, int in_N){
  PVW_TMLWE triv = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  make_triv(triv, seed, N, 0);
  PVW_TMLWE * p = pvmtmlwe_alloc_new_sample_array(in_N, (int) key->k, 1, N);
  for (int t = 0; t < in_N; t++){
    memcpy(p[t]->a[0]->coeffs, t ? p[0]->a[0]->coeffs : triv->a[0]->coeffs,
        sizeof(uint64_t) * N);
    memcpy(p[t]->b[0]->coeffs, t ? p[0]->b[0]->coeffs : triv->b[0]->coeffs,
        sizeof(uint64_t) * N);
  }
  uint64_t * a0 = (uint64_t *) malloc(sizeof(uint64_t) * in_N);
  uint64_t * a1 = (uint64_t *) malloc(sizeof(uint64_t) * in_N);
  for (int t = 0; t < in_N; t++){
    a0[t] = lcg_next(seed) % (uint64_t) N;   /* a in [0,2d) = [0,N) */
    a1[t] = lcg_next(seed) % (uint64_t) N;
  }
  rinput_phase(ph, triv, key);
  uint64_t phi[8192];
  memcpy(phi, ph->coeffs, sizeof(uint64_t) * N);
  sab_rinput_sub_a_homtr(p, a0, a1, ri);
  rinput_phase(ph, p[0], key);
  uint64_t sh[8192], sp[8192], sm[8192], y0[8192], y1[8192];
  perm_1pN(sh, phi, N);
  for (int i = 0; i < N; i++){
    sp[i] = (uint64_t)((int64_t) phi[i] + (int64_t) sh[i]);
    sm[i] = (uint64_t)((int64_t) phi[i] - (int64_t) sh[i]);
  }
  mul_xai(y0, sp, (int) ((2 * a0[0]) % (2 * (uint64_t) N)), N);
  mul_xai(y1, sm, (int) ((2 * a1[0]) % (2 * (uint64_t) N)), N);
  int64_t dv[8192];
  for (int i = 0; i < N; i++){
    int64_t raw = (int64_t) y0[i] + (int64_t) y1[i];
    dv[i] = fold63((int64_t) ph->coeffs[i] - (raw >> 1));
  }
  free(a0); free(a1);
  free_pvmtmlwe_array(p, in_N); free_pvmtmlwe(triv);
  return rms_of(N, dv);
}

/* ---------------- micro-EP adjudication (env SAB_RINPUT_MICRO=1) ----------
 * Rebuilds ONE external product by hand in EXACT integer arithmetic:
 *   rows S0,S1 = mat_trgsw_monomial_sample (m, e=0), read back before DFT;
 *   dec(D.a), dec(D.b) via the real pvmtmlwe_decompose;
 *   hand_EP.a = dec(D.a) (x) S0.a + dec(D.b) (x) S1.a   ((x) = negacyclic)
 *   hand_EP.b likewise;   compare with the LIBRARY CMUX result (R - A).
 * Also reconstructs e_0/e_1 = row phases exactly. Adjudicates whether the
 * EP identity (three-term) or the library DFT path is responsible for any
 * measured excess. */
static void negacyc_conv(uint64_t * out, const uint64_t * f,
    const uint64_t * g, int N){
  memset(out, 0, sizeof(uint64_t) * N);
  for (int i = 0; i < N; i++){
    const int64_t fi = (int64_t) f[i];
    if(!fi) continue;
    for (int j = 0; j < N; j++){
      const int k = i + j;
      const int64_t t = fi * (int64_t) g[j];
      if(k < N) out[k] += (uint64_t) t;
      else out[k - N] -= (uint64_t) t;
    }
  }
}

static void micro_ep(PVW_TMLWE_Key key, SAB_RINPUT_Key ri, uint64_t * seed,
    TorusPolynomial ph, int N, int msg_sel, int zero_mask){
  PVW_TMLWE A = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  PVW_TMLWE B = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  PVW_TMLWE R = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  make_triv(A, seed, N, zero_mask);
  make_triv(B, seed, N, zero_mask);
  /* ONE selector instance: sample plain, hand-compute from it, then convert
   * THE SAME instance to DFT for the library CMUX (deterministic compare). */
  MAT_TRGSW sel = mat_trgsw_alloc_new_sample((int) ri->mat_key->T,
      (int) ri->mat_key->Q, (int) key->k, 1, N);
  mat_trgsw_monomial_sample(sel, msg_sel, 0, ri->mat_key);
  MAT_TRGSW_DFT sel_dft = mat_trgsw_alloc_new_DFT_sample(
      (int) ri->mat_key->T, (int) ri->mat_key->Q, (int) key->k, 1, N);
  mat_trgsw_to_DFT(sel_dft, sel);
  sab_rinput_CMUX(R, A, B, sel_dft, ri);
  PVW_TMLWE D = pvmtmlwe_alloc_new_sample((int) key->k, 1, N);
  pvmtmlwe_sub(D, B, A);
  TorusPolynomial * dec = polynomial_new_array_of_torus_polynomials(N, 2);
  pvmtmlwe_decompose(dec, D, (int) ri->mat_key->Q, 1);
  uint64_t * ha = (uint64_t *) malloc(sizeof(uint64_t) * N);
  uint64_t * hb = (uint64_t *) malloc(sizeof(uint64_t) * N);
  uint64_t * t1 = (uint64_t *) malloc(sizeof(uint64_t) * N);
  uint64_t * t2c = (uint64_t *) malloc(sizeof(uint64_t) * N);
  negacyc_conv(t1, dec[0]->coeffs, sel->samples[0]->a[0]->coeffs, N);
  negacyc_conv(t2c, dec[1]->coeffs, sel->samples[1]->a[0]->coeffs, N);
  for (int i = 0; i < N; i++)
    ha[i] = (uint64_t)((int64_t) t1[i] + (int64_t) t2c[i]);
  negacyc_conv(t1, dec[0]->coeffs, sel->samples[0]->b[0]->coeffs, N);
  negacyc_conv(t2c, dec[1]->coeffs, sel->samples[1]->b[0]->coeffs, N);
  for (int i = 0; i < N; i++)
    hb[i] = (uint64_t)((int64_t) t1[i] + (int64_t) t2c[i]);
  /* 1) library vs hand: component-level AND phase-level */
  { uint64_t * has = (uint64_t *) malloc(sizeof(uint64_t) * N);
    negacyc_conv(has, ha, key->s[0][0]->coeffs, N);
    double a1 = 0, a2 = 0;
    for (int i = 0; i < N; i++){
      int64_t da = fold63((int64_t)(R->a[0]->coeffs[i] - A->a[0]->coeffs[i])
          - (int64_t) ha[i]);
      int64_t db = fold63((int64_t)(R->b[0]->coeffs[i] - A->b[0]->coeffs[i])
          - (int64_t) hb[i]);
      a1 += (double) da * da; a2 += (double) db * db;
    }
    /* phase-level: (R - A) with LIBRARY a-part, exact conv */
    uint64_t * liba = (uint64_t *) malloc(sizeof(uint64_t) * N);
    for (int i = 0; i < N; i++)
      liba[i] = R->a[0]->coeffs[i] - A->a[0]->coeffs[i];
    uint64_t * libas = (uint64_t *) malloc(sizeof(uint64_t) * N);
    negacyc_conv(libas, liba, key->s[0][0]->coeffs, N);
    double accp = 0; int64_t mxp = 0;
    for (int i = 0; i < N; i++){
      int64_t lib_ph = (int64_t)(R->b[0]->coeffs[i] - A->b[0]->coeffs[i])
          - (int64_t) libas[i];
      int64_t hand_ph = (int64_t) hb[i] - (int64_t) has[i];
      int64_t dv = fold63(lib_ph - hand_ph);
      accp += (double) dv * dv; if(llabs(dv) > llabs(mxp)) mxp = dv;
    }
    printf("MICRO m=%d zm=%d lib-vs-hand: a rms=%.2f b rms=%.2f | phase rms=%.2f max=%lld\n",
        msg_sel, zero_mask, log2(sqrt(a1 / N) + 1.0), log2(sqrt(a2 / N) + 1.0),
        log2(sqrt(accp / N) + 1.0), (long long) mxp);
    free(has); free(liba); free(libas);
  }
  /* 2) hand phase vs pure identity: hand_ph = de0 + de1 (row phases with
   *    message placement already inside e0/e1) -- must be EXACT */
  { uint64_t * e0 = (uint64_t *) malloc(sizeof(uint64_t) * N);
    uint64_t * e1 = (uint64_t *) malloc(sizeof(uint64_t) * N);
    uint64_t * s = (uint64_t *) malloc(sizeof(uint64_t) * N);
    negacyc_conv(e0, sel->samples[0]->a[0]->coeffs, key->s[0][0]->coeffs, N);
    for (int i = 0; i < N; i++)
      e0[i] = (uint64_t)((int64_t) sel->samples[0]->b[0]->coeffs[i]
          - (int64_t) e0[i]);
    negacyc_conv(e1, sel->samples[1]->a[0]->coeffs, key->s[0][0]->coeffs, N);
    for (int i = 0; i < N; i++)
      e1[i] = (uint64_t)((int64_t) sel->samples[1]->b[0]->coeffs[i]
          - (int64_t) e1[i]);
    for (int i = 0; i < N; i++) s[i] = key->s[0][0]->coeffs[i];
    uint64_t * de0 = (uint64_t *) malloc(sizeof(uint64_t) * N);
    uint64_t * de1 = (uint64_t *) malloc(sizeof(uint64_t) * N);
    negacyc_conv(de0, dec[0]->coeffs, e0, N);
    negacyc_conv(de1, dec[1]->coeffs, e1, N);
    const uint64_t scale = 1ULL << (64 - (int) ri->mat_key->Q);
    double t1r = 0, t2r = 0, r0 = 0, r1 = 0;
    for (int i = 0; i < N; i++){
      int64_t epsa = (int64_t)(D->a[0]->coeffs[i]
          - (uint64_t)((int64_t) dec[0]->coeffs[i] * (int64_t) scale));
      int64_t epsb = (int64_t)(D->b[0]->coeffs[i]
          - (uint64_t)((int64_t) dec[1]->coeffs[i] * (int64_t) scale));
      t1r += (double) epsa * epsa; t2r += (double) epsb * epsb;
      r0 += (double)(int64_t) e0[i] * (int64_t) e0[i];
      r1 += (double)(int64_t) e1[i] * (int64_t) e1[i];
    }
    uint64_t * has = (uint64_t *) malloc(sizeof(uint64_t) * N);
    negacyc_conv(has, ha, s, N);
    double acc2 = 0; int64_t mx2 = 0;
    for (int i = 0; i < N; i++){
      int64_t handph = (int64_t) hb[i] - (int64_t) has[i];
      int64_t ident2 = (int64_t) de0[i] + (int64_t) de1[i];
      int64_t dv = fold63(handph - ident2);
      acc2 += (double) dv * dv; if(llabs(dv) > llabs(mx2)) mx2 = dv;
    }
    /* definitive decomposition: hand_noise = ndec0 + ndec1 + (eps_a(x)s - eps_b)
     * with the message placement stripped from the row phases (s in {0,1}
     * keeps m*sc*s[i] exact in uint64). */
    { const uint64_t sc = 1ULL << (64 - (int) ri->mat_key->Q);
      uint64_t * ekg0 = (uint64_t *) malloc(sizeof(uint64_t) * N);
      uint64_t * ekg1 = (uint64_t *) malloc(sizeof(uint64_t) * N);
      uint64_t * epsa = (uint64_t *) malloc(sizeof(uint64_t) * N);
      uint64_t * epsb = (uint64_t *) malloc(sizeof(uint64_t) * N);
      uint64_t * ndec0 = (uint64_t *) malloc(sizeof(uint64_t) * N);
      uint64_t * ndec1 = (uint64_t *) malloc(sizeof(uint64_t) * N);
      uint64_t * eas = (uint64_t *) malloc(sizeof(uint64_t) * N);
      uint64_t * das_ = (uint64_t *) malloc(sizeof(uint64_t) * N);
      for (int i = 0; i < N; i++){
        ekg0[i] = (uint64_t)((int64_t) e0[i]
            + (msg_sel && s[i] ? (int64_t) sc : 0));
        ekg1[i] = (uint64_t)((int64_t) e1[i]
            - (msg_sel && i == 0 ? (int64_t) sc : 0));
        epsa[i] = (uint64_t)((int64_t) D->a[0]->coeffs[i]
            - (int64_t)((uint64_t)((int64_t) dec[0]->coeffs[i] * (int64_t) sc)));
        epsb[i] = (uint64_t)((int64_t) D->b[0]->coeffs[i]
            - (int64_t)((uint64_t)((int64_t) dec[1]->coeffs[i] * (int64_t) sc)));
      }
      negacyc_conv(ndec0, dec[0]->coeffs, ekg0, N);
      negacyc_conv(ndec1, dec[1]->coeffs, ekg1, N);
      negacyc_conv(eas, epsa, s, N);
      negacyc_conv(das_, D->a[0]->coeffs, s, N);
      { /* input sanity: |epsa| bound, s support, predicted vs measured rms,
         *   plus a WHITE-SYNTHETIC control with the same marginal (same D.a
         *   low bits shuffled by an independent LCG) to detect correlation */
        int64_t mxa = 0; double sums2 = 0, sea2 = 0;
        int64_t mxe = 0;
        for (int i = 0; i < N; i++){
          int64_t v = fold63((int64_t) epsa[i]);
          if(llabs(v) > mxa) mxa = v;
          int64_t sv = (int64_t) s[i];
          sums2 += (double) sv * sv;
          sea2 += (double) v * v;
          int64_t ev = fold63((int64_t) eas[i]);
          if(llabs(ev) > mxe) mxe = ev;
        }
        uint64_t * weps = (uint64_t *) malloc(sizeof(uint64_t) * N);
        uint64_t * wout = (uint64_t *) malloc(sizeof(uint64_t) * N);
        uint64_t ws = 0x853c49e6748fea9bULL ^ (uint64_t) msg_sel;
        for (int i = 0; i < N; i++){
          int64_t v = fold63((int64_t) epsa[i]);
          /* same marginal via fresh uniform draw on the same range */
          int64_t w = (int64_t)(lcg_next(&ws) % ((uint64_t) 2 * (uint64_t) llabs(mxa) + 1))
              - llabs(mxa);
          (void) v;
          weps[i] = (uint64_t) w;
        }
        negacyc_conv(wout, weps, s, N);
        double wacc = 0;
        for (int i = 0; i < N; i++){
          int64_t v = fold63((int64_t) wout[i]);
          wacc += (double) v * v;
        }
        { /* aligned & shifted cross-correlation between real eps_a and s,
           *   plus eps_a autocorrelation (lag 1) and total sum */
          double c0 = 0, sum_e = 0;
          int64_t e_prev = 0; double lag1 = 0, sea2b = 0;
          for (int i = 0; i < N; i++){
            int64_t e = fold63((int64_t) epsa[i]);
            c0 += (double) e * (double)((int64_t) s[i]);
            sum_e += (double) e;
            if(i) lag1 += (double) e * (double) e_prev;
            sea2b += (double) e * e;
            e_prev = e;
          }
          printf("  xcorr(eps_a,s)=%.2e sum(eps_a)=%.3e (N*mu_pred=%.3e) ac1=%.3f\n",
              c0, sum_e, (double) N * 1099511627776.0,
              lag1 / (sea2b > 0 ? sea2b : 1.0));
          printf("  eps_a[0..5] = %lld %lld %lld %lld %lld %lld; s[0..15] =",
              (long long) fold63((int64_t) epsa[0]), (long long) fold63((int64_t) epsa[1]),
              (long long) fold63((int64_t) epsa[2]), (long long) fold63((int64_t) epsa[3]),
              (long long) fold63((int64_t) epsa[4]), (long long) fold63((int64_t) epsa[5]));
          for (int i = 0; i < 16; i++) printf(" %lld", (long long)(int64_t) s[i]);
          printf("; eas[0..3] =");
          for (int i = 0; i < 4; i++)
            printf(" %lld", (long long) fold63((int64_t) eas[i]));
          printf("\n");
        }
        printf("MICRO m=%d zm=%d sanity: max|eps_a|=%lld rms=%.2f | sum s^2=%.0f | max|eps_a(x)s|=%lld pred_rms=%.2f white-ctrl=%.2f\n",
            msg_sel, zero_mask, (long long) mxa, log2(sqrt(sea2 / N) + 1.0),
            sums2, (long long) mxe,
            log2(sqrt(sums2 * sea2 / N) + 1.0),
            log2(sqrt(wacc / N) + 1.0));
        free(weps); free(wout);
      }
      double rn0 = 0, rn1 = 0, reas = 0, rebs = 0, rhn = 0, rchk = 0;
      for (int i = 0; i < N; i++){
        int64_t v;
        v = fold63((int64_t) ndec0[i]); rn0 += (double) v * v;
        v = fold63((int64_t) ndec1[i]); rn1 += (double) v * v;
        v = fold63((int64_t) eas[i]); reas += (double) v * v;
        v = fold63((int64_t) epsb[i]); rebs += (double) v * v;
        int64_t handph = (int64_t) hb[i] - (int64_t) has[i];
        int64_t phiD = (int64_t) D->b[0]->coeffs[i] - (int64_t) das_[i];
        int64_t hn = fold63(handph - phiD);
        rhn += (double) hn * hn;
        int64_t predn = (int64_t) ndec0[i] + (int64_t) ndec1[i]
            + (int64_t) eas[i] - (int64_t) epsb[i];
        int64_t chk = fold63(predn - (int64_t) 0 - hn);
        rchk += (double) chk * chk;
      }
      printf("MICRO m=%d zm=%d parts: ndec0=%.2f ndec1=%.2f eps_a(x)s=%.2f eps_b=%.2f | hand_noise=%.2f check=%.2f\n",
          msg_sel, zero_mask, log2(sqrt(rn0 / N) + 1.0),
          log2(sqrt(rn1 / N) + 1.0), log2(sqrt(reas / N) + 1.0),
          log2(sqrt(rebs / N) + 1.0), log2(sqrt(rhn / N) + 1.0),
          log2(sqrt(rchk / N) + 1.0));
      free(ekg0); free(ekg1); free(epsa); free(epsb); free(ndec0);
      free(ndec1); free(eas); free(das_);
    }
    printf("MICRO m=%d zm=%d hand-vs-identity: max=%lld rms=%.2f (rms eps_a=%.2f eps_b=%.2f e0=%.2f e1=%.2f)\n",
        msg_sel, zero_mask, (long long) mx2, log2(sqrt(acc2 / N) + 1.0),
        log2(sqrt(t1r / N) + 1.0), log2(sqrt(t2r / N) + 1.0),
        log2(sqrt(r0 / N) + 1.0), log2(sqrt(r1 / N) + 1.0));
    free(e0); free(e1); free(s); free(de0); free(de1); free(has);
  }
  /* 3) library EP noise vs selected-input phase (the operative number) */
  rinput_phase(ph, msg_sel ? B : A, key);
  uint64_t ref[8192];
  memcpy(ref, ph->coeffs, sizeof(uint64_t) * N);
  rinput_phase(ph, R, key);
  double acc = 0; int64_t mx = 0;
  for (int i = 0; i < N; i++){
    int64_t dv = fold63((int64_t) ph->coeffs[i] - (int64_t) ref[i]);
    acc += (double) dv * dv; if(llabs(dv) > llabs(mx)) mx = dv;
  }
  printf("MICRO m=%d zm=%d lib-EP-noise: rms=%.2f max=%lld\n", msg_sel,
      zero_mask, log2(sqrt(acc / N) + 1.0), (long long) mx);
  free(ha); free(hb); free(t1); free(t2c);
  free_array_of_polynomials(dec, 2);
  free_pvmtmlwe(D); free_mat_trgsw(sel); free_mat_trgsw_DFT(sel_dft);
  free_pvmtmlwe(R); free_pvmtmlwe(B); free_pvmtmlwe(A);
}

/* ------------------------- one trial ------------------------- */

typedef struct {
  int gate_bad;
  double pair_rms, sig_s;
  double final_meas, final_pred;
  double max_stage_logratio;
  prim_t prim;
  double t_int, t_or;
} trial_res_t;

static int run_trial(int trial, int reps, trial_res_t * res){
  const int in_N = G_in_N, out_N = G_out_N, h = G_h, prec = G_prec;
  const int d = out_N / 2;
  const int in_k = 1, out_k = 1, l = 1, bg_bit = 23;
  printf("== trial %d/%d: in_N=%d out_N=%d (d=%d) h=%d ==\n", trial + 1,
      reps, in_N, out_N, d, h);

  TRLWE_Key input_key = NULL, packing_key = NULL;
  { /* target_r_prec = FINAL rho (7): at n=2048/h=42 the typical max gap
     * is ~2^7.5, so target 6 exhausts the internal 2^15-attempt loop and
     * leaves the key pointer garbage (observed SIGSEGV). 7 succeeds with
     * ~1/22 acceptance. */
    const uint64_t rs_target = 7;
    RS_sparse_binary_key(&input_key, in_N, in_k, h, pow(2, -15), rs_target);
    RS_sparse_binary_key(&packing_key, in_N, in_k, h, pow(2, -44), rs_target);
    if(input_key == NULL || input_key->s[0] == NULL
        || packing_key == NULL || packing_key->s[0] == NULL){
      printf("RS keygen FAILED (target_r_prec=%lu) -- abort\n",
          (unsigned long) rs_target);
      res->gate_bad = -1;
      return 1;
    }
  }
  uint64_t max_gap = 0, previous = in_N;
  for (int scan = 0; scan < in_N; scan++){
    const int current = in_N - scan - 1;
    if(input_key->s[0]->coeffs[current] == 0) continue;
    if((uint64_t)(previous - current) > max_gap) max_gap = previous - current;
    previous = current;
  }
  if(previous > max_gap) max_gap = previous;
  uint64_t r_prec = 1;
  while((1ULL << r_prec) <= max_gap) r_prec++;
  if(G_rprec) r_prec = G_rprec;
  uint64_t gaps[h + 2];
  {
    uint64_t prev = in_N, gi = 0;
    for (int scan = 0; scan < in_N; scan++){
      const int cur = in_N - scan - 1;
      if(input_key->s[0]->coeffs[cur] == 0) continue;
      gaps[gi++] = prev - cur;
      prev = cur;
    }
    gaps[gi] = prev;
  }

  TorusPolynomial msg0 = polynomial_new_torus_polynomial(in_N);
  TorusPolynomial msg1 = polynomial_new_torus_polynomial(in_N);
  for (int i = 0; i < in_N; i++){
    msg0->coeffs[i] = int2torus(i & 7, prec);
    msg1->coeffs[i] = int2torus((3 * i + 1) & 7, prec);
  }
  TRLWE in0 = trlwe_new_sample(msg0, input_key);
  TRLWE in1 = trlwe_new_sample(msg1, input_key);

  TorusPolynomial tv0 = polynomial_new_torus_polynomial(d);
  TorusPolynomial tv1 = polynomial_new_torus_polynomial(d);
  for (int q = 0; q < d; q++){
    tv0->coeffs[q] = int2torus(q & 7, prec + 2);
    tv1->coeffs[q] = int2torus((5 * q + 2) & 7, prec + 2);
  }

  { double sg = -70;
    const char * e = getenv("SAB_RINPUT_SIGMA");
    if(e) sg = atof(e);
    G_sigma_exp = sg; }
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, out_k, 1,
      pow(2, G_sigma_exp));
  SAB_RINPUT_Key ri = sab_rinput_new_key(input_key, pvw_key, prec, h,
      r_prec, l, bg_bit);

  /* ---- primitives on this key ---- */
  TorusPolynomial ph = polynomial_new_torus_polynomial(out_N);
  uint64_t seed = 0x243F6A8885A308D3ULL ^ (uint64_t) trial * 0x9E3779B9ULL;
  prim_t pr;
  { long hw = 0;
    for (int i = 0; i < out_N; i++) if(pvw_key->s[0][0]->coeffs[i]) hw++;
    printf("key hw = %ld / N = %d, r_prec = %lu\n", hw, out_N,
        (unsigned long) r_prec);
  }
  if(trial == 0){
    phase_perm_check(pvw_key, ri->aut_h, 1 + (uint64_t) out_N, ph, out_N,
        "aut_h");
    phase_perm_check(pvw_key, ri->aut_minus1, 2 * (uint64_t) out_N - 1, ph,
        out_N, "aut_minus1");
  }
  pr.sig_eps = calib_eps(pvw_key, bg_bit);
  pr.sig_ks_h = calib_ks(pvw_key, ri->aut_h, 1 + (uint64_t) out_N, &seed,
      ph, out_N);
  pr.sig_ks_m1 = calib_ks(pvw_key, ri->aut_minus1,
      2 * (uint64_t) out_N - 1, &seed, ph, out_N);
  pr.sig_ep1 = calib_ep(pvw_key, ri, 1, &seed, ph, out_N, 0);
  pr.sig_ep0 = calib_ep(pvw_key, ri, 0, &seed, ph, out_N, 0);
  pr.sig_ep1_s = 0; pr.sig_ep0_s = 0;  /* filled after setup (true operands) */
  pr.sig_psi = calib_psi(pvw_key, ri, &seed, ph, out_N);
  pr.sig_suba = calib_suba(pvw_key, ri, &seed, ph, out_N, in_N);
  printf("PRIM: eps=%.2f ks_h=%.2f ks_m1=%.2f ep1=%.2f ep0=%.2f psi=%.2f suba=%.2f\n",
      log2(pr.sig_eps + 1.0), log2(pr.sig_ks_h + 1.0),
      log2(pr.sig_ks_m1 + 1.0), log2(pr.sig_ep1 + 1.0),
      log2(pr.sig_ep0 + 1.0), log2(pr.sig_psi + 1.0),
      log2(pr.sig_suba + 1.0));
  if(getenv("SAB_RINPUT_MICRO")){
    micro_ep(pvw_key, ri, &seed, ph, out_N, 1, 0);
    micro_ep(pvw_key, ri, &seed, ph, out_N, 0, 0);
    micro_ep(pvw_key, ri, &seed, ph, out_N, 1, 1);
    micro_ep(pvw_key, ri, &seed, ph, out_N, 0, 1);
  }

  /* ---- accumulators + plaintext model ---- */
  PVW_TMLWE * acc = pvmtmlwe_alloc_new_sample_array(in_N, out_k, 1, out_N);
  PVW_TMLWE * acc2 = pvmtmlwe_alloc_new_sample_array(in_N, out_k, 1, out_N);
  sab_rinput_setup_tv(acc, in0, in1, tv0, tv1, ri);
  /* first-bit calibration on the TRUE operands: (acc[j], acc[j-1]) pairs
   * of the SAME setup array (the pipeline's first CMUX is exactly
   * CMUX(acc[j], acc[j-1], sel) with both slots from one array). */
  { const int m0 = (int) (gaps[0] & 1);
    pr.sig_ep1_s = pr.sig_ep0_s = calib_ep_arr2(pvw_key, ri, acc,
        ri->s[0][0][0], m0, ph, in_N); /* first-bit m = m0: one primitive */ }
  res->prim = pr;
  printf("PRIM1: ep_s(first bit, own selector)=%.2f\n",
      log2(pr.sig_ep1_s + 1.0));

  uint64_t ** mdl = (uint64_t **) malloc(sizeof(uint64_t *) * in_N);
  uint64_t ** mdtmp = (uint64_t **) malloc(sizeof(uint64_t *) * in_N);
  for (int t = 0; t < in_N; t++){
    mdl[t] = (uint64_t *) calloc(out_N, sizeof(uint64_t));
    mdtmp[t] = (uint64_t *) calloc(out_N, sizeof(uint64_t));
  }
  const int log_2d = (int) log2(2 * d);
  const uint64_t po = 1ULL << (64 - prec - 1);
  for (int t = 0; t < in_N; t++){
    for (int lane = 0; lane < 2; lane++){
      TRLWE in = lane == 0 ? in0 : in1;
      TorusPolynomial tv = lane == 0 ? tv0 : tv1;
      const uint64_t bbar = torus2int(in->b->coeffs[t] + po, log_2d);
      for (int q = 0; q < d; q++){
        const uint64_t pos = (q + bbar) % (2 * (uint64_t) d);
        if(pos < (uint64_t) d) mdl[t][lane + 2 * pos] += tv->coeffs[q];
        else mdl[t][lane + 2 * (pos - d)] -= tv->coeffs[q];
      }
    }
  }
  uint64_t * a_mod0 = (uint64_t *) malloc(sizeof(uint64_t) * in_N);
  uint64_t * a_mod1 = (uint64_t *) malloc(sizeof(uint64_t) * in_N);
  for (int t = 0; t < in_N; t++){
    a_mod0[t] = torus2int(in0->a[0]->coeffs[t], log_2d);
    a_mod1[t] = torus2int(in1->a[0]->coeffs[t], log_2d);
  }

  /* ---- instrumented pipeline + prediction + per-stage measurement ---- */
  double * sig2 = (double *) malloc(sizeof(double) * in_N);
  double * sig2n = (double *) malloc(sizeof(double) * in_N);
  for (int t = 0; t < in_N; t++) sig2[t] = 0.0;
  /* deterministic DC-walk tracking: w[i] = mu_eps*(2H[i]-hw) (key-dependent,
   * coherent across m=1 events); per-slot noise polynomial DC_t[i]. */
  uint64_t * Hcnt = (uint64_t *) calloc(out_N, sizeof(uint64_t));
  {
    uint64_t c = 0;
    for (int i = 0; i < out_N; i++){
      if(pvw_key->s[0][0]->coeffs[i]) c++;
      Hcnt[i] = c;
    }
  }
  const uint64_t hw_key = Hcnt[out_N - 1];
  int64_t * wpat = (int64_t *) malloc(sizeof(int64_t) * out_N);
  const int64_t mu_eps = (int64_t) 1 << (64 - bg_bit - 1); /* E[eps]=2^40 */
  for (int i = 0; i < out_N; i++)
    wpat[i] = mu_eps * (int64_t)(2 * (int64_t) Hcnt[i] - (int64_t) hw_key);
  double w_rms2 = 0;
  for (int i = 0; i < out_N; i++) w_rms2 += (double) wpat[i] * wpat[i];
  w_rms2 /= out_N;
  const double white1_2 = pr.sig_ep1 * pr.sig_ep1 > w_rms2
      ? pr.sig_ep1 * pr.sig_ep1 - w_rms2 : 0.0;
  const double white1_s2 = pr.sig_ep1_s * pr.sig_ep1_s; /* no DC (zero mask) */
  int64_t ** dc = (int64_t **) malloc(sizeof(int64_t *) * in_N);
  int64_t ** dcn = (int64_t **) malloc(sizeof(int64_t *) * in_N);
  for (int t = 0; t < in_N; t++){
    dc[t] = (int64_t *) calloc(out_N, sizeof(int64_t));
    dcn[t] = (int64_t *) calloc(out_N, sizeof(int64_t));
  }
  printf("DCWALK: hw=%lu w_rms=%.2f (pred coherent unit), sigma_EP1=%.2f white1=%.2f\n",
      (unsigned long) hw_key, log2(sqrt(w_rms2) + 1.0),
      log2(pr.sig_ep1 + 1.0), log2(sqrt(white1_2) + 1.0));
  PVW_TMLWE * buf[2] = {acc, ri->tmp->buf2};
  int active = 0;
  double max_lr = 0;
  int n_stages = 0;
  uint64_t cur_power = 0;   /* wrapped-slot range of the stage just run */
  double slot_max = 0;      /* worst per-slot rms this trial */
  const double w_psi_ks2 = 1.5;   /* ks_m1^2 * 1 + ks_h^2 * 1/2, applied per-key below */
  uint64_t * sbuf = (uint64_t *) malloc(sizeof(uint64_t) * out_N);
  uint64_t * smbuf = (uint64_t *) malloc(sizeof(uint64_t) * out_N);
  uint64_t * ybuf = (uint64_t *) malloc(sizeof(uint64_t) * out_N);
  int64_t * sbuf64 = (int64_t *) malloc(sizeof(int64_t) * out_N);
  int64_t * ybuf64 = (int64_t *) malloc(sizeof(int64_t) * out_N);
  const int twoN = 2 * out_N;
  const double psi_ks2 = pr.sig_ks_m1 * pr.sig_ks_m1
      + 0.5 * pr.sig_ks_h * pr.sig_ks_h;

#define MEASURE_STAGE(TAG) \
  do { \
    double macc = 0, wacc = 0, dacc = 0, oacc = 0; \
    long mcnt = 0, wcnt = 0, dcnt = 0, ocnt = 0; \
    uint64_t mmx = 0; int mmx_slot = -1; long alias_sus = 0; \
    for (int t = 0; t < in_N; t++){ \
      double sacc = 0; \
      rinput_phase(ph, buf[active][t], pvw_key); \
      for (int i = 0; i < out_N; i++){ \
        int64_t dv = fold63((int64_t) ph->coeffs[i] - (int64_t) mdl[t][i]); \
        double dd = (double) dv * (double) dv; \
        macc += dd; mcnt++; sacc += dd; \
        if((uint64_t) llabs(dv) > mmx){ mmx = (uint64_t) llabs(dv); mmx_slot = t; } \
        if((i & 1) == 0){ \
          if(cur_power && (uint64_t) t < cur_power){ wacc += dd; wcnt++; } \
          else { dacc += dd; dcnt++; } \
        } else { \
          oacc += dd; ocnt++; \
          if((uint64_t) llabs(dv) > ((uint64_t) 1 << 61)) alias_sus++; \
        } \
      } \
      if(sacc > 0){ double sr = sqrt(sacc / out_N); \
        if(sr > slot_max) slot_max = sr; } \
    } \
    double meas = sqrt(macc / mcnt); \
    double meas_e = sqrt((dacc + wacc) / (dcnt + wcnt > 0 ? dcnt + wcnt : 1)); \
    double meas_o = sqrt(oacc / (ocnt ? ocnt : 1)); \
    double mp = 0; \
    for (int t = 0; t < in_N; t++){ \
      double d2 = 0; \
      for (int i = 0; i < out_N; i += 2) d2 += (double) dc[t][i] * dc[t][i]; \
      mp += sig2[t] + d2 / (out_N / 2.0); \
    } \
    double pred = sqrt(mp / in_N); \
    double lr = log2((meas_e + 1.0) / (pred + 1.0)); \
    if(fabs(lr) > max_lr) max_lr = fabs(lr); \
    printf("STAGE %-16s even=%.2f (wrap=%.2f dir=%.2f) odd=%.2f pred=%.2f lr=%+.2f max=%.2f@%d alias=%ld\n", \
        TAG, log2(meas_e + 1.0), \
        wcnt ? log2(sqrt(wacc / wcnt) + 1.0) : 0.0, \
        log2(sqrt(dacc / dcnt) + 1.0), log2(meas_o + 1.0), \
        log2(pred + 1.0), lr, log2((double) mmx + 1.0), mmx_slot, alias_sus); \
    res->final_meas = meas_e; res->final_pred = pred; \
    n_stages++; cur_power = 0; \
  } while (0)

  MEASURE_STAGE("setup");
  for (int step = 0; step <= h; step++){
    for (uint64_t bit = 0; bit < r_prec; bit++){
      const uint64_t power = 1ULL << bit;
      const int m = (int) ((gaps[step] >> bit) & 1);
      const int src = active, dst = active ^ 1;
      for (uint64_t j = 0; j < power; j++){
        sab_rinput_wrap_psi(ri->tmp->s_plus, buf[src][in_N - power + j], ri);
        sab_rinput_CMUX(buf[dst][j], buf[src][j], ri->tmp->s_plus,
            ri->s[0][step][bit], ri);
      }
      for (uint64_t j = power; j < (uint64_t) in_N; j++){
        sab_rinput_CMUX(buf[dst][j], buf[src][j], buf[src][j - power],
            ri->s[0][step][bit], ri);
      }
      active = dst;
      /* --- prediction (first-ever bit stage: setup-regime operands) ---
       * white part quadratic; DC-walk pattern wpat added coherently. */
      const double ep1w_2 = (step == 0 && bit == 0) ? white1_s2 : white1_2;
      const double ep0_2 = (step == 0 && bit == 0)
          ? pr.sig_ep0_s * pr.sig_ep0_s : pr.sig_ep0 * pr.sig_ep0;
      const double psi2_use = (step == 0 && bit == 0) ? 0.0 : psi_ks2;
      const int add_dc = !(step == 0 && bit == 0);
      if(m){
        for (uint64_t j = 0; j < power; j++){
          sig2n[j] = sig2[in_N - power + j] + psi2_use + ep1w_2;
          /* Psi DC transform: t = sigma_-1(dc); out[even i]=t[i],
           * out[odd i]=t[i-2 fold]; then + w */
          const int64_t * dsrc = dc[in_N - power + j];
          int64_t * dd = dcn[j];
          memset(dd, 0, sizeof(int64_t) * out_N);
          for (int i = 0; i < out_N; i += 2){
            const int64_t tv = i == 0 ? dsrc[0] : -dsrc[out_N - i];
            dd[i] = tv;
          }
          { /* odd i: t[i-2] with negacyclic +2 shift of the sm part:
               sm lives on odd positions; sm[i] = 2*t[i]; y = sp + X^2*sm */
            int64_t * tmpsm = sbuf64;
            memset(tmpsm, 0, sizeof(int64_t) * out_N);
            for (int i = 1; i < out_N; i += 2){
              const int64_t tv = -dsrc[out_N - i];
              tmpsm[i] = tv;   /* t on odd positions (sm = 2t -> /2 = t) */
            }
            /* y_odd[i] = sm[i-2 folded]: DC_odd[i] = t_odd[i-2] */
            for (int i = 1; i < out_N; i += 2){
              int p = i - 2;
              if(p < 0){
                /* i=1: source position -1 -> 2N-1 >= N -> -t[N-1] */
                dd[i] = -tmpsm[out_N - 1];
              }else{
                dd[i] = tmpsm[p];
              }
            }
          }
          if(add_dc) for (int i = 0; i < out_N; i++) dd[i] += wpat[i];
        }
        for (uint64_t j = power; j < (uint64_t) in_N; j++){
          sig2n[j] = sig2[j - power] + ep1w_2;
          if(add_dc){
            for (int i = 0; i < out_N; i++)
              dcn[j][i] = dc[j - power][i] + wpat[i];
          }else{
            memcpy(dcn[j], dc[j - power], sizeof(int64_t) * out_N);
          }
        }
      }else{
        for (int j = 0; j < in_N; j++){
          sig2n[j] = sig2[j] + ep0_2;
          memcpy(dcn[j], dc[j], sizeof(int64_t) * out_N);
        }
      }
      { double * sw = sig2; sig2 = sig2n; sig2n = sw;
        int64_t ** sd = dc; dc = dcn; dcn = sd; }
      /* --- model (only m=1 bits move data; m=0 = identity) --- */
      if(m){
        for (uint64_t j = 0; j < power; j++){
          const uint64_t * x = mdl[in_N - power + j];
          /* sigma_{-1} then U_(0,1) then rescale: reuse sbuf/smbuf/ybuf */
          sbuf[0] = x[0]; /* sbuf <- sigma_{-1}(x) */
          for (int i = 1; i < out_N; i++)
            sbuf[i] = (uint64_t)(-(int64_t) x[out_N - i]);
          for (int i = 0; i < out_N; i++){
            int64_t sh = (i & 1) ? -(int64_t) sbuf[i] : (int64_t) sbuf[i];
            smbuf[i] = (uint64_t)((int64_t) sbuf[i] + sh);  /* sp */
            sbuf[i] = (uint64_t)((int64_t) sbuf[i] - sh);   /* sm (reuse) */
          }
          memset(ybuf, 0, sizeof(uint64_t) * out_N);
          for (int i = 0; i < out_N; i++){
            ybuf[i] = smbuf[i];
            uint64_t e = ((uint64_t) i + 2) % twoN;
            if(e < (uint64_t) out_N) ybuf[e] += sbuf[i];
            else ybuf[e - out_N] -= sbuf[i];
          }
          for (int i = 0; i < out_N; i++) mdtmp[j][i] = (ybuf[i] + 1) >> 1;
        }
        for (uint64_t j = power; j < (uint64_t) in_N; j++)
          memcpy(mdtmp[j], mdl[j - power], sizeof(uint64_t) * out_N);
        uint64_t ** swp = mdl; mdl = mdtmp; mdtmp = swp;
      }
      if(!G_coarse){
        char tag[32]; snprintf(tag, sizeof tag, "bit p%d.b%llu m=%d", step,
            (unsigned long long) bit, m);
        cur_power = power;
        MEASURE_STAGE(tag);
      } else n_stages++;
    }
    if(step < h){
      sab_rinput_sub_a_homtr_opt(buf[active], a_mod0, a_mod1, ri, 1);
      for (int t = 0; t < in_N; t++)
        sig2[t] += 0.5 * pr.sig_ks_h * pr.sig_ks_h;
      /* DC transform: U_a even/odd split with Y-shifts 2a0/2a1 (exact) */
      for (int t = 0; t < in_N; t++){
        const int64_t * d = dc[t];
        memset(sbuf64, 0, sizeof(int64_t) * out_N); /* sp on even pos */
        memset(ybuf64, 0, sizeof(int64_t) * out_N); /* sm on odd pos */
        for (int i = 0; i < out_N; i += 2) sbuf64[i] = d[i];
        for (int i = 1; i < out_N; i += 2) ybuf64[i] = d[i];
        memset(dc[t], 0, sizeof(int64_t) * out_N);
        dc_shift_addto(dc[t], sbuf64, (int) ((2 * a_mod0[t]) % twoN), out_N);
        dc_shift_addto(dc[t], ybuf64, (int) ((2 * a_mod1[t]) % twoN), out_N);
      }
      for (int t = 0; t < in_N; t++){
        for (int i = 0; i < out_N; i++){
          int64_t sh = (i & 1) ? -(int64_t) mdl[t][i] : (int64_t) mdl[t][i];
          sbuf[i] = (uint64_t)((int64_t) mdl[t][i] + sh);
          smbuf[i] = (uint64_t)((int64_t) mdl[t][i] - sh);
        }
        memset(ybuf, 0, sizeof(uint64_t) * out_N);
        for (int i = 0; i < out_N; i++){
          uint64_t e0 = ((uint64_t) i + 2 * a_mod0[t]) % twoN;
          if(e0 < (uint64_t) out_N) ybuf[e0] += sbuf[i];
          else ybuf[e0 - out_N] -= sbuf[i];
          uint64_t e1 = ((uint64_t) i + 2 * a_mod1[t]) % twoN;
          if(e1 < (uint64_t) out_N) ybuf[e1] += smbuf[i];
          else ybuf[e1 - out_N] -= smbuf[i];
        }
        for (int i = 0; i < out_N; i++) mdl[t][i] = (ybuf[i] + 1) >> 1;
      }
      { char tag[32]; snprintf(tag, sizeof tag, "suba p%d", step);
        MEASURE_STAGE(tag); }
    }
  }
  /* final identity doubling (U_(0,0)) */
  for (int t = 0; t < in_N; t++){
    PVW_TMLWE c = buf[active][t];
    for (size_t idx = 0; idx < (size_t) c->k; idx++)
      for (int q = 0; q < out_N; q++)
        c->a[idx]->coeffs[q] += c->a[idx]->coeffs[q];
    for (size_t lane = 0; lane < (size_t) c->r; lane++)
      for (int q = 0; q < out_N; q++)
        c->b[lane]->coeffs[q] += c->b[lane]->coeffs[q];
  }
  for (int t = 0; t < in_N; t++) sig2[t] *= 4;
  for (int t = 0; t < in_N; t++)
    for (int i = 0; i < out_N; i++) dc[t][i] *= 2;
  for (int t = 0; t < in_N; t++)
    for (int q = 0; q < out_N; q++) mdl[t][q] += mdl[t][q];
  MEASURE_STAGE("final x2");
  { /* final anatomy: where does the 2^60-class live? per-parity columns,
     * extraction columns, and raw dumps for slots 0/1/6 */
    for (int t = 0; t < 3 && t < in_N; t++){
      rinput_phase(ph, buf[active][t], pvw_key);
      double ev = 0, od = 0, ex = 0;
      long nev = 0, nod = 0, nex = 0;
      for (int i = 0; i < out_N; i++){
        int64_t dv = fold63((int64_t) ph->coeffs[i] - (int64_t) mdl[t][i]);
        double dd = (double) dv * dv;
        if(i & 1){ od += dd; nod++; } else { ev += dd; nev++; }
        if(i < 2){ ex += dd; nex++; }
      }
      printf("ANAT slot%d: even=%.2f odd=%.2f cols01=%.2f | dev[0..5]=",
          t, log2(sqrt(ev / nev) + 1.0), log2(sqrt(od / nod) + 1.0),
          log2(sqrt(ex / nex) + 1.0));
      for (int i = 0; i < 6; i++)
        printf(" %lld", (long long) fold63((int64_t) ph->coeffs[i]
            - (int64_t) mdl[t][i]));
      printf(" | mdl[0..5]=");
      for (int i = 0; i < 6; i++)
        printf(" %lld", (long long) fold63((int64_t) mdl[t][i]));
      printf("\n");
      if(t == 0){ /* displacement test: dev[odd i] = -mdl[odd i-4] + eps? */
        long hit4 = 0, hit0 = 0, tot = 0; double res4 = 0;
        for (int i = 5; i < out_N; i += 2){
          int64_t dv = fold63((int64_t) ph->coeffs[i] - (int64_t) mdl[t][i]);
          int64_t m0 = fold63((int64_t) mdl[t][i]);
          int64_t m4 = fold63((int64_t) mdl[t][i - 4]);
          tot++;
          if(llabs(dv + m4) < (1LL << 55)) hit4++;
          if(llabs(dv + m0) < (1LL << 55)) hit0++;
          int64_t r4 = dv + m4;
          res4 += (double) r4 * r4;
        }
        printf("ANAT displace-test: dev[odd i]=-mdl[i-4] hits %ld/%ld (self-hits %ld), resid rms=%.2f\n",
            hit4, tot, hit0, log2(sqrt(res4 / (tot ? tot : 1)) + 1.0));
      }
    }
  }
  if(active != 0){
    for (int j = 0; j < in_N; j++) pvmtmlwe_copy(acc[j], ri->tmp->buf2[j]);
  }
  printf("stages=%d worst|log2ratio|=%.3f worst-slot-rms=%.2f\n", n_stages,
      max_lr, log2(slot_max + 1.0));
  res->max_stage_logratio = max_lr;
  (void) w_psi_ks2;

  /* ---- mirror validation vs stock pipeline (bit-identical) ---- */
  {
    double t0 = now_us();
    sab_rinput_bootstrap_wo_extract(acc2, in0, in1, tv0, tv1, ri);
    res->t_int = now_us() - t0;
    int diff = 0;
    for (int t = 0; t < in_N; t++){
      for (int i = 0; i < out_N; i++){
        if(acc2[t]->a[0]->coeffs[i] != acc[t]->a[0]->coeffs[i]
            || acc2[t]->b[0]->coeffs[i] != acc[t]->b[0]->coeffs[i]) diff++;
      }
    }
    printf("MIRROR: %s (%d coeff diffs)\n", diff == 0 ? "IDENTICAL" : "FAIL",
        diff);
    if(diff != 0){ res->gate_bad = -1; goto cleanup; }
  }

  /* ---- oracle gate + pair noise (same build/semantics as probe_rinput) ---- */
  {
    TorusPolynomial p1 = polynomial_new_torus_polynomial(d);
    int mism = 0;
    uint64_t pair_dev_max = 0;
    double pair_sq = 0; long pair_cnt = 0;
    double s_acc = 0; long s_cnt = 0;
    double t_or = 0;
    for (int lane = 0; lane < 2; lane++){
      TRLWE in = lane == 0 ? in0 : in1;
      TorusPolynomial tv = lane == 0 ? tv0 : tv1;
      TRLWE_Key lane_key = trlwe_new_binary_key(d, out_k, pow(2, -70));
      TRGSW_Key skey = trgsw_new_key(lane_key, l, bg_bit);
      SAB_Key oracle = min_oracle_key(input_key, skey, prec, h, r_prec);
      TRLWE tv_rlwe = trlwe_alloc_new_sample(in_k, d);
      memset(tv_rlwe->a[0]->coeffs, 0, sizeof(tv_rlwe->a[0]->coeffs[0]) * d);
      memcpy(tv_rlwe->b->coeffs, tv->coeffs, sizeof(tv->coeffs[0]) * d);
      TRLWE * sacc = trlwe_alloc_new_sample_array(in_N, in_k, d);
      double tb = now_us();
      sab_rlwe_bootstrap_wo_extract(sacc, in, tv_rlwe, oracle);
      t_or += now_us() - tb;
      for (int t = 0; t < in_N; t++){
        trlwe_phase(p1, sacc[t], lane_key);
        rinput_phase(ph, acc[t], pvw_key);
        const int64_t v_scalar =
            (((int64_t) p1->coeffs[0]) + ((int64_t) 1 << (62 - prec - 1)))
            >> (62 - prec);
        const int64_t v_int =
            (((int64_t) ph->coeffs[lane]) + ((int64_t) 1 << (62 - prec)))
            >> (62 - prec + 1);
        if(v_scalar != v_int) mism++;
        { const int64_t grid = (int64_t) 1 << (62 - prec - 1);
          int64_t rr = ((int64_t) p1->coeffs[0]) % grid;
          if(rr < 0) rr = -rr; if(rr > grid / 2) rr = grid - rr;
          s_acc += (double) rr * (double) rr; s_cnt++; }
        const int64_t dev = (int64_t) p1->coeffs[0]
            - (((int64_t) ph->coeffs[lane]) >> 1);
        const int64_t adev = dev < 0 ? -dev : dev;
        if((uint64_t) adev > pair_dev_max) pair_dev_max = (uint64_t) adev;
        pair_sq += (double) dev * (double) dev; pair_cnt++;
      }
      free_trlwe_array(sacc, in_N);
      free_trlwe(tv_rlwe);
      free_trlwe_key(lane_key);
      free_trgsw_key(skey);
    }
    res->gate_bad = mism;
    res->pair_rms = sqrt(pair_sq / (pair_cnt > 0 ? pair_cnt : 1));
    res->sig_s = sqrt(s_acc / (s_cnt > 0 ? s_cnt : 1));
    res->t_or = t_or;
    printf("GATE: mismatch %d / %d -- %s; pair rms = %.2f (max %.2f); sig_s = %.2f\n",
        mism, 2 * in_N, mism == 0 ? "Pass" : "FAIL",
        log2(res->pair_rms + 1.0),
        log2((double) pair_dev_max + 1.0), log2(res->sig_s + 1.0));
    free_polynomial(p1);
  }

cleanup:
  free(sbuf); free(smbuf); free(ybuf);
  free(sbuf64); free(ybuf64);
  free(Hcnt); free(wpat);
  for (int t = 0; t < in_N; t++){ free(dc[t]); free(dcn[t]); }
  free(dc); free(dcn);
  free_polynomial(ph);
  free(sig2); free(sig2n);
  for (int t = 0; t < in_N; t++){ free(mdl[t]); free(mdtmp[t]); }
  free(mdl); free(mdtmp);
  free(a_mod0); free(a_mod1);
  free_pvmtmlwe_array(acc, in_N);
  free_pvmtmlwe_array(acc2, in_N);
  free_sab_rinput_key(ri);
  free_pvmtmlwe_key(pvw_key);
  free_polynomial(tv0); free_polynomial(tv1);
  free_trlwe(in0); free_trlwe(in1);
  free_polynomial(msg0); free_polynomial(msg1);
  free_trlwe_key(input_key); free_trlwe_key(packing_key);
  return res->gate_bad < 0 ? 1 : 0;
}

int main(void){
  setvbuf(stdout, NULL, _IONBF, 0);
  int reps = 6;
  { const char *e = getenv("SAB_RINPUT_REPS");
    if(e) reps = atoi(e); if(reps < 1) reps = 1; if(reps > 64) reps = 64; }
  { const char *e;
    if((e = getenv("SAB_RINPUT_IN_N"))) G_in_N = atoi(e);
    if((e = getenv("SAB_RINPUT_OUT_N"))) G_out_N = atoi(e);
    if((e = getenv("SAB_RINPUT_H"))) G_h = atoi(e);
    if((e = getenv("SAB_RINPUT_RPREC"))) G_rprec = (uint64_t) atoi(e);
    if((e = getenv("SAB_RINPUT_AES"))) G_lcg_triv = !atoi(e);
    if((e = getenv("SAB_RINPUT_COARSE"))) G_coarse = atoi(e); }

  int all_ok = 1;
  double worst_stage = 0;
  prim_t pr_sum; memset(&pr_sum, 0, sizeof pr_sum);
  double sig_s_sum = 0, final_meas_sum = 0, final_pred_sum = 0;
  double pair_sq_sum = 0; long pair_cnt_sum = 0;
  double t_int_med = 0, t_or_med = 0;
  double t_ints[64], t_ors[64];
  for (int rep = 0; rep < reps; rep++){
    trial_res_t res; memset(&res, 0, sizeof res);
    if(run_trial(rep, reps, &res) != 0){ printf("ABORT trial %d\n", rep);
      return 1; }
    if(res.gate_bad != 0) all_ok = 0;
    if(res.max_stage_logratio > worst_stage)
      worst_stage = res.max_stage_logratio;
    pr_sum.sig_eps += res.prim.sig_eps; pr_sum.sig_ks_h += res.prim.sig_ks_h;
    pr_sum.sig_ks_m1 += res.prim.sig_ks_m1; pr_sum.sig_ep0 += res.prim.sig_ep0;
    pr_sum.sig_ep1_s += res.prim.sig_ep1_s; pr_sum.sig_ep0_s += res.prim.sig_ep0_s;
    pr_sum.sig_ep1 += res.prim.sig_ep1; pr_sum.sig_psi += res.prim.sig_psi;
    pr_sum.sig_suba += res.prim.sig_suba;
    sig_s_sum += res.sig_s;
    final_meas_sum += res.final_meas; final_pred_sum += res.final_pred;
    pair_sq_sum += res.pair_rms * res.pair_rms * (2.0 * G_in_N);
    pair_cnt_sum += 2 * G_in_N;
    t_ints[rep] = res.t_int; t_ors[rep] = res.t_or;
  }
  const double r = (double) reps;
  { double k = t_ints[reps - 1]; /* insertion sort for medians */
    double k2 = t_ors[reps - 1];
    int j = reps - 2;
    while (j >= 0 && t_ints[j] > k){
      t_ints[j + 1] = t_ints[j]; t_ors[j + 1] = t_ors[j]; j--; }
    t_ints[j + 1] = k; t_ors[j + 1] = k2; }
  t_int_med = t_ints[reps / 2]; t_or_med = t_ors[reps / 2];

  printf("\n==== SUMMARY (%d trials) ====\n", reps);
  printf("PRIM(mean): eps=%.2f ks_h=%.2f ks_m1=%.2f ep1=%.2f ep0=%.2f ep1s=%.2f ep0s=%.2f psi=%.2f suba=%.2f\n",
      log2(pr_sum.sig_eps / r + 1.0), log2(pr_sum.sig_ks_h / r + 1.0),
      log2(pr_sum.sig_ks_m1 / r + 1.0), log2(pr_sum.sig_ep1 / r + 1.0),
      log2(pr_sum.sig_ep0 / r + 1.0), log2(pr_sum.sig_ep1_s / r + 1.0),
      log2(pr_sum.sig_ep0_s / r + 1.0), log2(pr_sum.sig_psi / r + 1.0),
      log2(pr_sum.sig_suba / r + 1.0));
  { double ks_h = pr_sum.sig_ks_h / r, suba = pr_sum.sig_suba / r;
    double psi = pr_sum.sig_psi / r, ep1 = pr_sum.sig_ep1 / r;
    double ks_m1 = pr_sum.sig_ks_m1 / r;
    printf("XCHECK: suba/(ks_h/sqrt2)=%.3f (pred 1), psi/pred=%.3f (pred 1), ep1/ks_h=%.3f (theory ~1.00)\n",
        suba / (ks_h / sqrt(2.0)),
        psi / sqrt(ks_m1 * ks_m1 + 0.5 * ks_h * ks_h), ep1 / ks_h);
  }
  printf("STAGE-GATE: worst |log2 ratio| = %.3f -- %s\n", worst_stage,
      worst_stage <= 0.38 ? "Pass" : "FAIL");
  printf("FINAL: meas=%.2f pred=%.2f log2ratio=%+.2f\n",
      log2(final_meas_sum / r + 1.0), log2(final_pred_sum / r + 1.0),
      log2((final_meas_sum / r + 1.0) / (final_pred_sum / r + 1.0)));
  { /* pair reconciliation: pred = sqrt(sig_s^2 + sig_int_native^2) */
    double sig_s = sig_s_sum / r;
    double sig_int_native = (final_pred_sum / r) / 2.0;
    double pred_pair = sqrt(sig_s * sig_s + sig_int_native * sig_int_native);
    double meas_pair = sqrt(pair_sq_sum / (pair_cnt_sum > 0 ? pair_cnt_sum : 1));
    double lr = log2((meas_pair + 1.0) / (pred_pair + 1.0));
    printf("PAIR: meas rms=%.2f pred=%.2f log2ratio=%+.2f -- %s\n",
        log2(meas_pair + 1.0), log2(pred_pair + 1.0), lr,
        fabs(lr) <= 0.38 ? "Pass" : "FAIL");
    if(fabs(lr) > 0.38) all_ok = 0;
  }
  printf("BENCH(median): interleaved=%.0f us 2x-scalar=%.0f us ratio=%.3f\n",
      t_int_med, t_or_med, t_int_med / (t_or_med > 0 ? t_or_med : 1));
  if(worst_stage > 0.38) all_ok = 0;
  printf("OVERALL: %s\n", all_ok ? "ALL PASS" : "FAIL");
  return all_ok ? 0 : 1;
}
