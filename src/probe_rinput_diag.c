/* probe_rinput_diag.c -- stage-locked diagnostic for the r-input pipeline.
 *
 * Runs the interleaved ciphertext pipeline stage by stage in lockstep with
 * an exact plaintext simulation (the probe knows the secret key, so every
 * butterfly / sub_a is reproducible in the clear). Reports the max phase
 * deviation per stage: the first stage whose deviation reaches torus scale
 * (~2^63) is the buggy one. */
#include <sab_rinput.h>
#include <sab.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int N_, TWO_N;

static void phase_of(PVW_TMLWE in, PVW_TMLWE_Key key, TorusPolynomial out){
  memset(out->coeffs, 0, sizeof(out->coeffs[0]) * out->N);
  for (size_t idx = 0; idx < (size_t) in->k; idx++){
    polynomial_mul_addto_torus(out, in->a[idx], key->s[idx][0]);
  }
  polynomial_sub_torus_polynomials(out, in->b[0], out);
}

/* dst = sigma_w(src), w odd; exponents mod 2N with X^N = -1 fold. */
static void sigma_poly(uint64_t * dst, const uint64_t * src, uint64_t w){
  memset(dst, 0, sizeof(uint64_t) * N_);
  for (int i = 0; i < N_; i++){
    uint64_t e = ((uint64_t) i * w) % TWO_N;
    if(e >= (uint64_t) N_){ e -= N_; dst[e] -= src[i]; }
    else dst[e] += src[i];
  }
}

/* dst += X^a * src */
static void xai_addto(uint64_t * dst, const uint64_t * src, int a){
  for (int i = 0; i < N_; i++){
    uint64_t e = ((uint64_t) i + (uint64_t) a) % TWO_N;
    if(e >= (uint64_t) N_){ e -= N_; dst[e] -= src[i]; }
    else dst[e] += src[i];
  }
}

/* dst = round(dst/2) componentwise (same formula as sab_rinput_rescale2) */
static void rshift2(uint64_t * dst, const uint64_t * src){
  for (int i = 0; i < N_; i++)
    dst[i] = (src[i] + 1) >> 1;
}

/* expected U_a sub_a: S+ = c + sigma_h(c); S- = c - sigma_h(c);
 * out = X^{2a0} S+ + X^{2a1} S-; /2 */
static void suba_expected(uint64_t * out, const uint64_t * c,
    uint64_t a0, uint64_t a1, uint64_t * t_h, uint64_t * sp, uint64_t * sm,
    int rescale){
  sigma_poly(t_h, c, 1 + N_);
  for (int i = 0; i < N_; i++){ sp[i] = c[i] + t_h[i]; sm[i] = c[i] - t_h[i]; }
  memset(out, 0, sizeof(uint64_t) * N_);
  xai_addto(out, sp, (int) ((2 * a0) % TWO_N));
  xai_addto(out, sm, (int) ((2 * a1) % TWO_N));
  if(rescale) rshift2(out, out);
}

/* expected Psi = U_(0,1) o sigma_{-1} with /2 rounding */
static void psi_expected(uint64_t * out, const uint64_t * src,
    uint64_t * t_m1, uint64_t * t_h, uint64_t * sp, uint64_t * sm){
  sigma_poly(t_m1, src, TWO_N - 1);
  sigma_poly(t_h, t_m1, 1 + N_);
  for (int i = 0; i < N_; i++){ sp[i] = t_m1[i] + t_h[i]; sm[i] = t_m1[i] - t_h[i]; }
  memset(out, 0, sizeof(uint64_t) * N_);
  for (int i = 0; i < N_; i++) out[i] = sp[i];
  xai_addto(out, sm, 2);
  rshift2(out, out);
}

static int stage_in_N = 0;

static double stage_dev(PVW_TMLWE * acc, uint64_t ** exp,
    PVW_TMLWE_Key pvw_key, TorusPolynomial ph){
  uint64_t dev = 0;
  for (int t = 0; t < stage_in_N; t++){
    phase_of(acc[t], pvw_key, ph);
    for (int i = 0; i < N_; i++){
      int64_t dv = (int64_t) ph->coeffs[i] - (int64_t) exp[t][i];
      if(dv < 0) dv = -dv;
      if((uint64_t) dv > dev) dev = (uint64_t) dv;
    }
  }
  return log2((double) dev + 1.0);
}

/* masked variant: ignores bit 63 (harmless +-2^63 wrap quirks of
 * intermediate rescales cancel at the next doubling; see stage396 HT-7) */
static double stage_dev_masked(PVW_TMLWE * acc, uint64_t ** exp,
    PVW_TMLWE_Key pvw_key, TorusPolynomial ph, int mask_msb){
  uint64_t dev = 0;
  const uint64_t mask = mask_msb ? ~((uint64_t) 1 << 63) : ~(uint64_t) 0;
  for (int t = 0; t < stage_in_N; t++){
    phase_of(acc[t], pvw_key, ph);
    for (int i = 0; i < N_; i++){
      int64_t dv = (int64_t) ((ph->coeffs[i] - exp[t][i]) << 1) >> 1;
      if(dv < 0) dv = -dv; if((uint64_t) dv > dev) dev = (uint64_t) dv;
    }
  }
  return log2((double) dev + 1.0);
}

int main(void){
  setvbuf(stdout, NULL, _IONBF, 0);
  int in_N = 256, out_N = 1024, h = 6, prec = 3, bg_bit = 23, l = 1;
  {
    const char *e;
    if((e = getenv("SAB_RINPUT_IN_N"))) in_N = atoi(e);
    if((e = getenv("SAB_RINPUT_OUT_N"))) out_N = atoi(e);
    if((e = getenv("SAB_RINPUT_H"))) h = atoi(e);
  }
  const int d = out_N / 2;
  N_ = out_N; TWO_N = 2 * out_N; stage_in_N = in_N;
  printf("diag: in_N=%d out_N=%d h=%d\n", in_N, out_N, h);

  TRLWE_Key input_key, packing_key;
  RS_sparse_binary_key(&input_key, in_N, 1, h, pow(2, -15), 6);
  RS_sparse_binary_key(&packing_key, in_N, 1, h, pow(2, -44), 6);
  uint64_t max_gap = 0, previous = in_N;
  for (int scan = 0; scan < in_N; scan++){
    const int current = in_N - scan - 1;
    if(input_key->s[0]->coeffs[current] == 0) continue;
    if(previous - current > max_gap) max_gap = previous - current;
    previous = current;
  }
  if(previous > max_gap) max_gap = previous;
  uint64_t r_prec = 1;
  while((1ULL << r_prec) <= max_gap) r_prec++;
  uint64_t gaps[h + 1];
  { uint64_t prev = in_N, gi = 0;
    for (int scan = 0; scan < in_N; scan++){
      const int cur = in_N - scan - 1;
      if(input_key->s[0]->coeffs[cur] == 0) continue;
      gaps[gi++] = prev - cur;
      prev = cur;
    }
    gaps[gi++] = prev;
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
    tv0->coeffs[q] = int2torus(q & 7, prec + 1);
    tv1->coeffs[q] = int2torus((5 * q + 2) & 7, prec + 1);
  }
  PVW_TMLWE_Key pvw_key = pvmtmlwe_new_binary_key(out_N, 1, 1, pow(2, -70));
  SAB_RINPUT_Key ri = sab_rinput_new_key(input_key, pvw_key, prec, h,
      r_prec, l, bg_bit);
  PVW_TMLWE *acc = pvmtmlwe_alloc_new_sample_array(in_N, 1, 1, out_N);

  /* expected state + scratch */
  uint64_t **exp = (uint64_t **) malloc(sizeof(uint64_t *) * in_N);
  uint64_t **ex2 = (uint64_t **) malloc(sizeof(uint64_t *) * in_N);
  for (int t = 0; t < in_N; t++){
    exp[t] = (uint64_t *) calloc(out_N, sizeof(uint64_t));
    ex2[t] = (uint64_t *) calloc(out_N, sizeof(uint64_t));
  }
  uint64_t *t_m1 = calloc(out_N, sizeof(uint64_t));
  uint64_t *t_h = calloc(out_N, sizeof(uint64_t));
  uint64_t *sp = calloc(out_N, sizeof(uint64_t));
  uint64_t *sm = calloc(out_N, sizeof(uint64_t));
  TorusPolynomial ph = polynomial_new_torus_polynomial(out_N);

  /* setup both */
  sab_rinput_setup_tv(acc, in0, in1, tv0, tv1, ri);
  const int log_2d = (int) log2(2 * d);
  const uint64_t prec_offset = 1ULL << (64 - prec - 1);
  for (int t = 0; t < in_N; t++){
    for (int lane = 0; lane < 2; lane++){
      TRLWE in = lane == 0 ? in0 : in1;
      TorusPolynomial tv = lane == 0 ? tv0 : tv1;
      const uint64_t bbar = torus2int(in->b->coeffs[t] + prec_offset,
          log_2d);
      for (int q = 0; q < d; q++){
        const uint64_t pos = (q + bbar) % (2 * d);
        if(pos < (uint64_t) d) exp[t][lane + 2 * pos] += tv->coeffs[q];
        else exp[t][lane + 2 * (pos - d)] -= tv->coeffs[q];
      }
    }
  }
  uint64_t am0[in_N], am1[in_N];
  for (int t = 0; t < in_N; t++){
    am0[t] = torus2int(in0->a[0]->coeffs[t], log_2d);
    am1[t] = torus2int(in1->a[0]->coeffs[t], log_2d);
  }
  printf("stage setup: max dev log2 = %.2f\n", stage_dev(acc, exp, pvw_key, ph));

  for (int step = 0; step <= h; step++){
    /* ciphertext butterfly */
    sab_rinput_RGSW_monomial_mul(acc, ri->s[0][step], ri);
    /* expected butterfly (double-buffered) */
    for (size_t bit = 0; bit < r_prec; bit++){
      const uint64_t power = 1ULL << bit;
      if((gaps[step] >> bit) & 1){
        for (int j = 0; j < (int) power; j++)
          psi_expected(ex2[j], exp[in_N - power + j], t_m1, t_h, sp, sm);
        for (int j = power; j < in_N; j++)
          memcpy(ex2[j], exp[j - power], sizeof(uint64_t) * out_N);
        uint64_t **sw = exp; exp = ex2; ex2 = sw;
      }
    }
    printf("stage bfly %d: max dev log2 = %.2f\n", step,
        stage_dev_masked(acc, exp, pvw_key, ph, 1));
    if(step < h){
      sab_rinput_sub_a_homtr_opt(acc, am0, am1, ri, step + 1 < h);
      for (int t = 0; t < in_N; t++)
        suba_expected(exp[t], exp[t], am0[t], am1[t], t_h, sp, sm, step + 1 < h);
      /* note: intermediate rescales keep their harmless +-2^63 quirks on
       * both sides identically; masked in stage_dev */
      printf("stage suba %d: max dev log2 = %.2f\n", step,
          stage_dev_masked(acc, exp, pvw_key, ph, step + 1 < h));
    }
  }
  return 0;
}
