/* probe_prealigned2.c -- COMPLETE pre-aligned combined packing+batching.
 *
 * Full multi-input: per-body-group b̄'_l setup (different rotation per
 * input), shared ā_common sub_a (single plaintext monomial), full
 * r1*r2 oracle gate. Pre-alignment simulated at plaintext level
 * (b'_l = b_l + (a_common - a_l)·s_in, phase-preserving by construction).
 *
 * Pipeline = STANDARD packing butterfly (sab_pvw path) with multi-body
 * TV pack; sub_a = per-slot plaintext monomial from a_common.
 */
#include <sab.h>
#include <sab_pvw.h>
#include <sab_rinput.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

static double now_us(void){
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1e6 + ts.tv_nsec / 1e3;
}

#define MAX_R1 4
#define MAX_R2 4
#define MAX_BODIES (MAX_R1 * MAX_R2)

static int run_trial(int trial, int reps){
  setvbuf(stdout, NULL, _IONBF, 0);
  int in_N = 256, out_N = 2048, h = 6, prec = 3;
  int r1 = 2, r2 = 2, rprec = 7;
  { const char *e;
    if((e = getenv("SAB_PA_IN_N"))) in_N = atoi(e);
    if((e = getenv("SAB_PA_OUT_N"))) out_N = atoi(e);
    if((e = getenv("SAB_PA_H"))) h = atoi(e);
    if((e = getenv("SAB_PA_R1"))) r1 = atoi(e);
    if((e = getenv("SAB_PA_R2"))) r2 = atoi(e);
    if((e = getenv("SAB_PA_RPREC"))) rprec = atoi(e); }
  const int trace = getenv("SAB_PA_TRACE") != NULL;
  if(r1 > MAX_R1) r1 = MAX_R1; if(r2 > MAX_R2) r2 = MAX_R2;
  const int bodies = r1 * r2;
  /* trace state (SAB_PA_TRACE): terminal-exponent extraction */
  static uint64_t ac_mod_g[8192], a0_mod_g[8192], bo_g[8192], bj_g[8192];
  static int Ej_g[8192], Eo_g[8192];
  static int qpos_g[16], gaps_g[17], nq_g = 0;
  printf("== PA2 trial %d/%d: in_N=%d out_N=%d h=%d r1=%d r2=%d rprec=%d ==\n",
      trial + 1, reps, in_N, out_N, h, r1, r2, rprec);

  /* sparse input key */
  TRLWE_Key input_key = NULL;
  RS_sparse_binary_key(&input_key, in_N, 1, h, pow(2, -15), rprec);
  if(!input_key || !input_key->s[0]){ printf("keygen FAIL\n"); return 1; }

  /* r1 inputs + common mask */
  TRLWE ins[MAX_R1];
  TorusPolynomial msgs[MAX_R1];
  uint64_t a_common_raw[8192];
  { memset(a_common_raw, 0, sizeof(uint64_t)*in_N); /* zero = simplest */
    if(!getenv("SAB_PA_RANDOM_AC")){
      uint64_t lcg = 0x123456789ABCDEFULL;
      for(int i=0;i<in_N;i++){ lcg = lcg*6364136223846793005ULL+1442695040888963407ULL;
        a_common_raw[i] = lcg; } } }
  /* Pre-aligned b'_l = b_l + (a_common - a_l)·s_in (plaintext simulation) */
  uint64_t bpa[MAX_R1][8192]; /* pre-aligned b values */
  for(int l=0;l<r1;l++){
    msgs[l] = polynomial_new_torus_polynomial(in_N);
    for(int i=0;i<in_N;i++) msgs[l]->coeffs[i] = int2torus((i+3*l)&7, prec);
    ins[l] = trlwe_new_sample(msgs[l], input_key);
    /* compute b'_l[t] = b_l[t] + Σ_i (a_common[i]-a_l[i])·s_in[t-i] */
    for(int t=0;t<in_N;t++){
      /* Accumulate in uint64_t (torus wrap-around semantics).
       * int64_t overflow: h+1 terms each ~2^63 sum past int64 range. */
      uint64_t corr = 0;
      for(int i=0;i<in_N;i++){
        int j = (t - i + 2*in_N) % (2*in_N);
        int sign;
        if(j >= in_N){ j -= in_N; sign = -1; } else { sign = 1; }
        if(!input_key->s[0]->coeffs[j]) continue; /* sparse: skip zeros */
        uint64_t diff = a_common_raw[i] - ins[l]->a[0]->coeffs[i];
        if(sign > 0) corr += diff;
        else corr -= diff; /* uint64_t wraps = torus negation */
      }
      /* b'_l = b_l + (a_common - a_l) ⊗ s: phase-preserving swap of the
       * mask to a_common (negacyclic convolution signs = wrap of t-i). */
      bpa[l][t] = ins[l]->b->coeffs[t] + corr;
    }
  }

  /* Build TV pack: body (l*r2+j) carries TV_{l,j} */
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, 1, bodies, pow(2,-70));
  SAB_PVW_Key pvw = sab_pvw_new_binary_key(input_key, pvw_key, prec, h, rprec, 1, 23);

  /* Custom setup: per-body-group rotation by b̄'_l */
  const int log_2N = (int)log2(2*out_N);
  const uint64_t po = 1ULL << (64 - prec - 1);
  PVW_TMLWE *acc = pvmtmlwe_alloc_new_sample_array(in_N, 1, bodies, out_N);
  /* TV values per (l,j) */
  /* Piecewise-constant LUT: level q>>shift, distinct per body.
   * This is REAL bootstrapping semantics (ramp TV amplifies modswitch
   * rounding artifacts -- Direction A finding). */
  TorusPolynomial tvs[MAX_BODIES];
  { /* SAB_PA_LUT_FINE=1: 256-coeff blocks (2x over-resolved LUT) --
     * nonstandard, kept ONLY as the trace instrument: the finer grid makes
     * the extracted terminal exponent unique (no mod-512 aliasing), at the
     * cost of knife-edge reads that flip one level on +-1 rounding. */
    const int fine = getenv("SAB_PA_LUT_FINE") != NULL;
    const int nlev = 1 << prec;         /* 2^prec LUT levels */
    const int block = out_N / nlev;      /* coefficients per level */
    for(int x=0;x<bodies;x++){
      tvs[x] = polynomial_new_torus_polynomial(out_N);
      for(int q=0;q<out_N;q++){
        /* LUT value constant on 512-unit spans of the 2N circle (pairs of
         * 256-coeff blocks): the modswitched read lands at 512m+256
         * (+/-1 rounding), i.e. mid-span, 256 units from any value
         * boundary. A 256-block grid would put every read exactly ON a
         * boundary, where the +/-1 rounding difference between the joint
         * (bpa) and oracle (b) paths flips one LUT level (root cause of
         * the 107/256 failures: exponent match, value flip). */
        const int level = fine ? q / block : (q / block) >> 1;
        const int val = (level + 3*x + 1) & (nlev - 1);
        tvs[x]->coeffs[q] = int2torus(val, prec);
      }
    }
  }
  for(int t=0;t<in_N;t++){
    /* mask AND all bodies = 0 */
    memset(acc[t]->a[0]->coeffs, 0, sizeof(uint64_t)*out_N);
    for(int b=0;b<bodies;b++)
      memset(acc[t]->b[b]->coeffs, 0, sizeof(uint64_t)*out_N);
    for(int l=0;l<r1;l++){
      uint64_t bbar = torus2int(bpa[l][t] + po, log_2N);
      for(int j=0;j<r2;j++){
        int body = l*r2 + j;
        /* b[body] = X^{bbar} · TV_{l,j} */
        memset(acc[t]->b[body]->coeffs, 0, sizeof(uint64_t)*out_N);
        for(int q=0;q<out_N;q++){
          uint64_t pos = (q + bbar) % (2*out_N);
          if(pos < (uint64_t)out_N)
            acc[t]->b[body]->coeffs[pos] += tvs[l*r2+j]->coeffs[q];
          else
            acc[t]->b[body]->coeffs[pos - out_N] -= tvs[l*r2+j]->coeffs[q];
        }
      }
    }
  }

  /* Run the packing butterfly (uses input 0 for the selector schedule;
   * the SELECTORS depend only on the key's gap structure, not on which
   * input's a/b we pass for the sub_a — we handle sub_a ourselves below) */
  /* Build a "virtual" TRLWE with mask a_common for sub_a derivation */
  TRLWE virtual_in = trlwe_alloc_new_sample(1, in_N);
  memcpy(virtual_in->a[0]->coeffs, a_common_raw, sizeof(uint64_t)*in_N);
  memcpy(virtual_in->b->coeffs, ins[0]->b->coeffs, sizeof(uint64_t)*in_N);

  double t0 = now_us();
  /* DIAGNOSTIC: verify setup is correct for slot 0, body 0 */
  if(trial == 0){
    const int body = 0, t = 0;
    uint64_t bbar = torus2int(bpa[0][t] + po, log_2N);
    /* coefficient 0 of X^bbar*TV reads TV at r=(0-bbar) mod 2N */
    int r0 = (int)(-(int64_t)bbar) % (2*out_N);
    if(r0 < 0) r0 += 2*out_N;
    uint64_t expect = r0 < out_N ? tvs[body]->coeffs[r0]
        : (uint64_t)0 - tvs[body]->coeffs[r0 - out_N];
    printf("SETUP-CHK: bbar=%llu acc=%llu exp=%llu m=%s\n",
        (unsigned long long)bbar,
        (unsigned long long)acc[t]->b[body]->coeffs[0],
        (unsigned long long)expect,
        acc[t]->b[body]->coeffs[0] == expect ? "YES" : "NO");
  }
  /* Use the library's TESTED butterfly + sub_a */
  { const uint64_t log2_2N = (uint64_t)log2(2*out_N);
    static uint64_t ac_mod[8192];
    const char *npa = getenv("SAB_PA_NOALIGN");
    if(npa){ /* use ORIGINAL input 0's a and b (no pre-alignment) */
      for(int t=0;t<in_N;t++){
        ac_mod[t] = torus2int(ins[0]->a[0]->coeffs[t], log2_2N);
        uint64_t bbar = torus2int(ins[0]->b->coeffs[t] +
            (1ULL<<(64-prec-1)), log2_2N);
        /* redo setup with original b */
        for(int b=0;b<bodies;b++){
          memset(acc[t]->b[b]->coeffs,0,sizeof(uint64_t)*out_N);
          for(int q=0;q<out_N;q++){
            uint64_t pos=(q+bbar)%(2*out_N);
            if(pos<(uint64_t)out_N) acc[t]->b[b]->coeffs[pos]+=tvs[b]->coeffs[q];
            else acc[t]->b[b]->coeffs[pos-out_N]-=tvs[b]->coeffs[q]; } }
      }
    } else {
      for(int t=0;t<in_N;t++)
        ac_mod[t] = torus2int(a_common_raw[t], log2_2N);
    }
    sab_pvw_sparse_mul_binary(acc, ac_mod, 0, pvw);

    /* ---- SAB_PA_TRACE: extract terminal exponents, compare with bpa ----
     * Empirically arbitrates the +/- sign-split of the sub_a station sum
     * (Direction A closed form E(t) = sum_{p<=t} a[t-p] - b - sum_{p>t}
     * a[t-p] vs the stage418 sec.7 crossing-phase form). */
    if(trace){
      const int N2 = 2*out_N;
      { uint64_t previous = in_N; int gi = 0;
        nq_g = 0;
        for(int scan=0; scan<in_N && nq_g<16; scan++){
          int current = in_N - scan - 1;
          if(input_key->s[0]->coeffs[current]){
            qpos_g[nq_g++] = current;
            gaps_g[gi++] = (int)(previous - current);
            previous = current; } }
        gaps_g[gi] = (int)previous; }
      printf("TRACE secret: h=%d positions=[", h);
      for(int i=0;i<nq_g;i++) printf("%s%d", i?",":"", qpos_g[i]);
      printf("] gaps=[");
      for(int i=0;i<=nq_g;i++) printf("%s%d", i?",":"", gaps_g[i]);
      printf("]\n");
      printf("TRACE a0_mod=[");
      for(int u=0;u<in_N;u++){
        a0_mod_g[u] = torus2int(ins[0]->a[0]->coeffs[u], log2_2N);
        printf("%s%llu", u?",":"", (unsigned long long)a0_mod_g[u]); }
      printf("]\nTRACE ac_mod=[");
      for(int u=0;u<in_N;u++){
        ac_mod_g[u] = ac_mod[u];
        printf("%s%llu", u?",":"", (unsigned long long)ac_mod_g[u]); }
      printf("]\nTRACE bo=[");
      for(int t=0;t<in_N;t++){
        bo_g[t] = torus2int(ins[0]->b->coeffs[t] + po, log2_2N);
        bj_g[t] = torus2int(bpa[0][t] + po, log2_2N);
        printf("%s%llu", t?",":"", (unsigned long long)bo_g[t]); }
      printf("]\nTRACE bj=[");
      for(int t=0;t<in_N;t++)
        printf("%s%llu", t?",":"", (unsigned long long)bj_g[t]);
      printf("]\n");
      /* joint terminal exponents: argmin_e dist(phase, X^e * TV_0) */
      { TorusPolynomial ph = polynomial_new_torus_polynomial(out_N);
        unsigned __int128 dmax = 0;
        for(int t=0;t<in_N;t++){
          memset(ph->coeffs, 0, sizeof(uint64_t)*out_N);
          polynomial_mul_addto_torus(ph, acc[t]->a[0], pvw_key->s[0][0]);
          polynomial_sub_torus_polynomials(ph, acc[t]->b[0], ph);
          unsigned __int128 best = ~(unsigned __int128)0; int be = -1;
          for(int e=0;e<N2;e++){
            unsigned __int128 acc_d = 0;
            for(int qq=0; qq<out_N; qq++){
              int rq = (qq - e) & (N2 - 1);
              uint64_t expect = rq < out_N ? tvs[0]->coeffs[rq]
                  : (uint64_t)0 - tvs[0]->coeffs[rq - out_N];
              uint64_t d = ph->coeffs[qq] - expect;
              if(d > 0x8000000000000000ULL) d = (uint64_t)0 - d;
              acc_d += d;
              if(acc_d >= best) break; }
            if(acc_d < best){ best = acc_d; be = e; } }
          Ej_g[t] = be; if(best > dmax) dmax = best; }
        printf("TRACE E_j=[");
        for(int t=0;t<in_N;t++)
          printf("%s%d", t?",":"", Ej_g[t]);
        printf("] (max match dist log2=%.1f)\n",
            log2((double)dmax+1.0));
        free_polynomial(ph); }
    }
  }
  double t_joint = now_us() - t0;

  /* Oracle gate: scalar SAB per (l,j) */
  int mism = 0, mism_ch[MAX_BODIES] = {0};
  double t_or = 0;
  TorusPolynomial p1 = polynomial_new_torus_polynomial(out_N);
  for(int l=0;l<r1;l++)
    for(int j=0;j<r2;j++){
      int ch = l*r2+j;
      TRLWE_Key lk = trlwe_new_binary_key(out_N, 1, pow(2,-70));
      TRGSW_Key sk = trgsw_new_key(lk, 1, 23);
      SAB_Key orc = min_oracle_key(input_key, sk, prec, h, rprec);
      TRLWE tvr = trlwe_alloc_new_sample(1, out_N);
      memset(tvr->a[0]->coeffs, 0, sizeof(uint64_t)*out_N);
      memcpy(tvr->b->coeffs, tvs[ch]->coeffs, sizeof(uint64_t)*out_N);
      TRLWE *sa = trlwe_alloc_new_sample_array(in_N, 1, out_N);
      double tb = now_us();
      { const char *npa2 = getenv("SAB_PA_NOALIGN");
        sab_rlwe_bootstrap_wo_extract(sa,
            npa2 ? ins[0] : ins[l], tvr, orc); }
      t_or += now_us() - tb;
      for(int t=0;t<in_N;t++){
        trlwe_phase(p1, sa[t], lk);
        if(trace && ch == 0){
          /* oracle terminal exponent: argmin_e dist(phase, X^e * TV_ch) */
          const int N2 = 2*out_N;
          unsigned __int128 best = ~(unsigned __int128)0; int be = -1;
          for(int e=0;e<N2;e++){
            unsigned __int128 acc_d = 0;
            for(int qq=0; qq<out_N; qq++){
              int rq = (qq - e) & (N2 - 1);
              uint64_t expect = rq < out_N ? tvs[ch]->coeffs[rq]
                  : (uint64_t)0 - tvs[ch]->coeffs[rq - out_N];
              uint64_t d = p1->coeffs[qq] - expect;
              if(d > 0x8000000000000000ULL) d = (uint64_t)0 - d;
              acc_d += d;
              if(acc_d >= best) break; }
            if(acc_d < best){ best = acc_d; be = e; } }
          Eo_g[t] = be; }
        /* joint body ch phase */
        TorusPolynomial ph = polynomial_new_torus_polynomial(out_N);
        memset(ph->coeffs, 0, sizeof(uint64_t)*out_N);
        polynomial_mul_addto_torus(ph, acc[t]->a[0], pvw_key->s[0][ch]);
        polynomial_sub_torus_polynomials(ph, acc[t]->b[ch], ph);
        const int64_t vs = (((int64_t)p1->coeffs[0])
            + ((int64_t)1<<(62-prec-1))) >> (62-prec);
        const int64_t vj = (((int64_t)ph->coeffs[0])
            + ((int64_t)1<<(62-prec-1))) >> (62-prec);
        if(vs != vj){ mism++; mism_ch[ch]++;
          if(trace && ch == 0 && mism <= 12)
            printf("MISM t=%d vs=%lld vj=%lld phase_o=%lld phase_j=%lld "
                "diff=%lld (2^%.1f) Eo=%d Ej=%d\n",
                t, (long long)vs, (long long)vj,
                (long long)((int64_t)p1->coeffs[0]),
                (long long)((int64_t)ph->coeffs[0]),
                (long long)(((int64_t)ph->coeffs[0])
                  - ((int64_t)p1->coeffs[0])),
                log2(fabs((double)((int64_t)ph->coeffs[0]
                  - (int64_t)p1->coeffs[0]))+1.0),
                Eo_g[t], Ej_g[t]); }
        free_polynomial(ph);
      }
      free_trlwe_array(sa,in_N); free_trlwe(tvr);
      free_trlwe_key(lk); free_trgsw_key(sk);
    }

  printf("PA2-GATE: mismatch %d / %d -- %s\n", mism, bodies*in_N,
      mism==0 ? "Pass" : "FAIL");
  if(mism) for(int x=0;x<bodies;x++) if(mism_ch[x])
    printf("  ch(l=%d,j=%d): %d\n", x/r2, x%r2, mism_ch[x]);

  /* ---- trace verdict: which +/- convention does the pipeline implement? ----
   * Direction A: E(t) = sum_{p<=t} a[t-p] - b[t] - sum_{p>t} a[t-p]
   *   (= -b + negacyclic convolution modswitch, signs by read-index wrap)
   * Negated A (stage418 sec.7 Direction B as written): overall sign flipped
   *   on the station sum. Pre-alignment needs A to hold for BOTH paths. */
  if(trace){
    const int N2 = 2*out_N;
    int n_A_o = 0, n_A_j = 0, n_nA_o = 0, n_nA_j = 0, n_R0 = 0;
    int n_A257_o = 0, n_A257_j = 0;    int slots = in_N;
    { const char *e = getenv("SAB_PA_TRACE_SLOTS");
      if(e){ slots = atoi(e); if(slots < 1) slots = 1; if(slots > in_N) slots = in_N; } }
    printf("TRACE E_o=[");
    for(int t=0;t<in_N;t++) printf("%s%d", t?",":"", Eo_g[t]);
    printf("]\n");
    printf("TRACE t | bo bj dms | Eo Ej | predA_o predA_j | R=Ej-Eo-dms\n");
    for(int t=0;t<in_N;t++){
      int64_t sA_o = 0, sA_j = 0;
      for(int i=0;i<nq_g;i++){
        const int read = ((t - qpos_g[i]) % in_N + in_N) % in_N;
        const int sgn = (qpos_g[i] <= t) ? 1 : -1;
        sA_o += (int64_t)sgn * (int64_t)a0_mod_g[read];
        sA_j += (int64_t)sgn * (int64_t)ac_mod_g[read]; }
      const int predA_o = (int)(((int64_t) -bo_g[t] + sA_o) % N2 + N2) % N2;
      const int predA_j = (int)(((int64_t) -bj_g[t] + sA_j) % N2 + N2) % N2;
      const int predNA_o = (int)(((int64_t) -bo_g[t] - sA_o) % N2 + N2) % N2;
      const int predNA_j = (int)(((int64_t) -bj_g[t] - sA_j) % N2 + N2) % N2;
      const int dms = (int)(bj_g[t] - bo_g[t] + (uint64_t)N2) % N2;
      /* pre-alignment residual: joint terminal exponent must EQUAL the
       * oracle's (bpa swaps the mask phase-preservingly). Round-level
       * deviations (|R| or N2-|R| <= h+2) are modswitch noise. */
      const int R = ((Ej_g[t] - Eo_g[t]) % N2 + N2) % N2;
      const int Rm = R > N2/2 ? R - N2 : R;
      if(Eo_g[t] == predA_o) n_A_o++;
      if(Ej_g[t] == predA_j) n_A_j++;
      if(Eo_g[t] == predNA_o) n_nA_o++;
      if(Ej_g[t] == predNA_j) n_nA_j++;
      /* the standard LUT (value spans = 2N/2^prec units) makes the
       * extracted exponent well-defined only mod (2N/2^prec)=512;
       * compare the closed form at that granularity */
      if((((Eo_g[t] - predA_o - 257) % 512) + 512) % 512 == 0) n_A257_o++;
      if((((Ej_g[t] - predA_j - 257) % 512) % 512 + 512) % 512 == 0) n_A257_j++;
      { const int R512 = (((Ej_g[t] - Eo_g[t]) % 512) + 512) % 512;
        const int R512m = R512 > 256 ? R512 - 512 : R512;
        if(R512m >= -(h+2) && R512m <= h+2) n_R0++; }
      if(t < slots)
        printf("  t=%-3d | %llu %llu %d | %d %d | %d %d | R=%d (co=%d cj=%d)\n",
            t, (unsigned long long)bo_g[t], (unsigned long long)bj_g[t],
            dms, Eo_g[t], Ej_g[t], predA_o, predA_j, Rm,
            ((Eo_g[t] - predA_o) % N2 + N2) % N2,
            ((Ej_g[t] - predA_j) % N2 + N2) % N2);
    }
    printf("TRACE verdict: E_o==predA %d/%d, E_j==predA %d/%d, "
        "E_o==predNegA %d/%d, E_j==predNegA %d/%d, "
        "E==predA+257 o:%d/%d j:%d/%d, |E_j-E_o|<=h+2 %d/%d\n",
        n_A_o, in_N, n_A_j, in_N, n_nA_o, in_N, n_nA_j, in_N,
        n_A257_o, in_N, n_A257_j, in_N, n_R0, in_N);
  }
  printf("timing: joint=%.0f us, %dx-scalar=%.0f us\n",
      t_joint, bodies, t_or);

  for(int x=0;x<bodies;x++) free_polynomial(tvs[x]);
  free_polynomial(p1); free_trlwe(virtual_in);
  free_pvmtmlwe_array(acc, in_N);
  free_pvmtmlwe_key(pvw_key);
  for(int l=0;l<r1;l++){ free_trlwe(ins[l]); free_polynomial(msgs[l]); }
  free_trlwe_key(input_key);
  return mism==0 ? 0 : 1;
}

int main(void){
  int reps = 1;
  { const char *e = getenv("SAB_PA_REPS");
    if(e){ reps = atoi(e); if(reps<1) reps=1; if(reps>16) reps=16; } }
  int ok = 1;
  for(int r=0;r<reps;r++) if(run_trial(r,reps)!=0) ok=0;
  printf("PA2 %s\n", ok ? "ALL PASS" : "FAIL");
  return ok ? 0 : 1;
}
