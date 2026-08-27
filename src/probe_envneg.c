/* probe_envneg.c -- minimal arbitration for the negative-multiplier leak.
 * dig = dense unsigned u32 values, mult = single spike of +-2^30 at
 * position p; envelope vs exact __int128 negacyclic conv. Sweeps the
 * sign and the position (wrap-relevant positions near N included). */
#include <mosfhet.h>
#include <stdio.h>
#include <stdlib.h>

static void conv128(uint64_t * out, const uint64_t * a, const int64_t * b, int N){
  for (int k = 0; k < N; k++){
    __int128 acc = 0;
    for (int i = 0; i < N; i++){
      const int j = k - i;
      if (j >= 0) acc += (__int128) a[i] * b[j];
      else acc -= (__int128) a[i] * b[j + N];
    }
    out[k] = (uint64_t) acc;
  }
}

int main(int argc, char ** argv){
  setvbuf(stdout, NULL, _IONBF, 0);
  const int N = 2048;
  /* argv[1] selects the bind4-replica decomposition:
   *   0 = minimal (default, done above)
   *   bit0 (1) = dig = 2^30 spike@40 + noise_high (as d=1 of bind4)
   *   bit1 (2) = mult = two negative spikes at 2043/2047 (tF shape)
   *   bit2 (4) = multiplier built spectrum-prescaled from 2^60-scale tF */
  int mode = (argc > 1) ? atoi(argv[1]) : 0;
  init_fft(N);
  TorusPolynomial dig = polynomial_new_torus_polynomial(N);
  TorusPolynomial mul = polynomial_new_torus_polynomial(N);
  TorusPolynomial got = polynomial_new_torus_polynomial(N);
  DFT_Polynomial dd = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial md = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial od = polynomial_new_DFT_polynomial(N);
  uint64_t * ref = (uint64_t *) safe_malloc(sizeof(uint64_t) * N);
  int64_t * mi = (int64_t *) safe_malloc(sizeof(int64_t) * N);

  /* deterministic dense unsigned digits */
  uint64_t st = 0x9E3779B97F4A7C15ULL;
  for (int q = 0; q < N; q++){
    st += 0xBF58476D1CE4E5B9ULL;
    dig->coeffs[q] = (st >> 33) & 0xFFFFFFFFULL;
  }
  double noise_log2 = (argc > 2) ? atof(argv[2]) : 17.0;
  if(mode & 1){
    for (int q = 0; q < N; q++)
      dig->coeffs[q] = (Torus) (((int64_t) double2torus(generate_normal_random(pow(2.0, noise_log2 - 64.0)))) >> 32 & 0xFFFFFFFFULL);
    dig->coeffs[40] += (Torus)(1LL << 30); /* the channel spike's top word */
  }
  if(mode & 8){
    /* experiment B: DENSE 2^60-class LUT multiplier (the real bind's F is
     * the full packing LUT, not sparse spikes), spectrum-prescaled, against
     * sign-extended noise digits + spike -- the last unreproduced element */
    uint64_t st2 = 0x2545F4914F6CDD1DULL;
    for (int q = 0; q < N; q++){
      st2 ^= st2 << 13; st2 ^= st2 >> 7; st2 ^= st2 << 17;
      mul->coeffs[q] = (st2 >> 44) << 52; /* dense ~2^60-class 12-bit values */
    }
    const double w8 = 1.0 / (double)(((Torus)1) << 30);
    polynomial_torus_to_DFT(md, mul);
    for (int q = 0; q < N; q++) md->coeffs[q] *= w8;
    for (int q = 0; q < N; q++) mi[q] = (int64_t)(mul->coeffs[q] >> 30);
    for (int q = 0; q < N; q++)
      dig->coeffs[q] = (Torus) (((int64_t) double2torus(generate_normal_random(pow(2.0, noise_log2 - 64.0)))) >> 32 & 0xFFFFFFFFULL);
    dig->coeffs[40] += (Torus)(1LL << 30);
  }else if(mode & 2){
    polynomial_zero_torus_polynomial(mul);
    if(mode & 4){
      /* spectrum-prescaled from a 2^60-scale tau_F, exactly as bind4 */
      TorusPolynomial tF = polynomial_new_torus_polynomial(N);
      polynomial_zero_torus_polynomial(tF);
      tF->coeffs[2043] = -(Torus)(3LL << 60);
      tF->coeffs[2047] = -(Torus)(1LL << 60);
      const double w = 1.0 / (double)(((Torus)1) << 30);
      polynomial_torus_to_DFT(md, tF);
      for (int q = 0; q < N; q++) md->coeffs[q] *= w;
      free_polynomial(tF);
      /* ref multiplier = the prescaled values the spectrum encodes */
      for (int q = 0; q < N; q++) mi[q] = (q == 2043) ? -(3LL << 30) : (q == 2047) ? -(1LL << 30) : 0;
    }else{
      mul->coeffs[2043] = (Torus)(-(3LL << 30));
      mul->coeffs[2047] = (Torus)(-(1LL << 30));
      polynomial_torus_to_DFT(md, mul);
      for (int q = 0; q < N; q++) mi[q] = (int64_t) mul->coeffs[q];
    }
  }else{
    mul->coeffs[2043] = (Torus)(-(3LL << 30));
    polynomial_torus_to_DFT(md, mul);
    for (int q = 0; q < N; q++) mi[q] = (int64_t) mul->coeffs[q];
  }
  polynomial_torus_to_DFT(dd, dig);
  polynomial_mul_DFT(od, dd, md);
  polynomial_DFT_to_torus(got, od);
  conv128(ref, dig->coeffs, mi, N);
  int64_t md2 = 0; int wk = -1;
  for (int q = 0; q < N; q++){
    int64_t dv = (int64_t)(got->coeffs[q] - ref[q]);
    if(dv < 0) dv = -dv;
    if(dv > md2){ md2 = dv; wk = q; }
  }
  printf("ENVNEG-REPLICA mode=%d noise=2^%.0f maxdiff log2 = %.2f at [%d] %s\n",
         mode, noise_log2, log2((double)(md2 + 1)), wk,
         md2 < (1LL << 40) ? "exact" : "LEAK");
  return 0;
}
