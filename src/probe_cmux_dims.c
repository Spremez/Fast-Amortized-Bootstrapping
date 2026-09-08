/* probe_cmux_dims.c -- isolate the TRLWE CMUX primitive by dimension.
 * Builds only the minimal pieces (no SAB oracle): for each dim in
 * {512, 1024}: trivial A, B; selector encrypting 1; bare CMUX; compare
 * against B. Also bare sigma_-1 KS. Reveals dim-specific local-build
 * breakage independent of the r-input work. */
#include <sab.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

int main(void){
  setvbuf(stdout, NULL, _IONBF, 0);
  const int dims[] = {256, 512, 1024};
  for (size_t di = 0; di < sizeof(dims) / sizeof(dims[0]); di++){
    const int d = dims[di];
    mosfhet_set_deterministic_seed(11 + di);
    TRLWE_Key key = trlwe_new_binary_key(d, 1, pow(2, -70));
    TRGSW_Key skey = trgsw_new_key(key, 1, 23);
    TRLWE_KS_Key autm1 = trlwe_new_automorphism_KS_keyset_2(key,
        (uint64_t[]){2 * d - 1}, 1, 1, 23)[0];
    TRLWE A = trlwe_alloc_new_sample(1, d);
    TRLWE B = trlwe_alloc_new_sample(1, d);
    TRLWE R = trlwe_alloc_new_sample(1, d);
    uint64_t *bv = calloc(d, sizeof(uint64_t));
    uint64_t *sig = calloc(d, sizeof(uint64_t));
    for (int q = 0; q < d; q++){
      B->b->coeffs[q] = int2torus((q * 5 + 2) & 7, 4);
      bv[q] = B->b->coeffs[q];
      A->b->coeffs[q] = int2torus((q * 3 + 1) & 7, 4);
      A->a[0]->coeffs[q] = 0;
      B->a[0]->coeffs[q] = 0;
    }
    for (int q = 0; q < d; q++){
      uint64_t e = ((uint64_t)(-(uint64_t) q)) % (2 * d);
      if(e < (uint64_t) d) sig[q] += bv[e];
      else sig[q] -= bv[e - d];
    }
    TorusPolynomial ph = polynomial_new_torus_polynomial(d);
    /* sigma_-1 KS */
    trlwe_eval_automorphism(R, B, 2 * d - 1, autm1);
    trlwe_phase(ph, R, key);
    { uint64_t dev = 0;
      for (int q = 0; q < d; q++){
        int64_t dv = (int64_t) ph->coeffs[q] - (int64_t) sig[q];
        if(dv < 0) dv = -dv; if((uint64_t) dv > dev) dev = (uint64_t) dv; }
      printf("dim %4d: sigma_-1 KS dev log2 = %.2f\n", d,
          log2((double) dev + 1.0)); }
    /* bare CMUX sel=1: R should equal B + noise */
    TRGSW_DFT sel1 = trgsw_alloc_new_DFT_sample(1, 23, 1, d);
    { TRGSW tmps = trgsw_alloc_new_sample(1, 23, 1, d);
      trgsw_monomial_sample(tmps, 1, 0, skey);
      trgsw_to_DFT(sel1, tmps);
      free_trgsw(tmps); }
    /* inline CMUX: R = A + sel1 (x) (B - A) */
    { TRLWE_DFT df = trlwe_alloc_new_DFT_sample(1, d);
      TRLWE diff = trlwe_alloc_new_sample(1, d);
      trlwe_sub(diff, B, A);
      trgsw_mul_trlwe_DFT(df, diff, sel1);
      trlwe_from_DFT(diff, df);
      trlwe_add(R, A, diff);
      trlwe_phase(ph, R, key);
      uint64_t dev = 0;
      for (int q = 0; q < d; q++){
        int64_t dv = (int64_t) ph->coeffs[q] - (int64_t) bv[q];
        if(dv < 0) dv = -dv; if((uint64_t) dv > dev) dev = (uint64_t) dv; }
      printf("dim %4d: CMUX(sel=1) dev log2 = %.2f %s\n", d,
          log2((double) dev + 1.0), dev < (1ULL << 55) ? "OK" : "<< FAIL");
      free_trlwe(diff); free(df->a); free(df->b); free(df); }
    free_polynomial(ph);
    free(bv); free(sig);
    free_trlwe(A); free_trlwe(B); free_trlwe(R);
    free_trlwe_ks_key(autm1);
    free_trgsw_key(skey);
    free_trlwe_key(key);
  }
  return 0;
}
