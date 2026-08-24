/* Standalone v6-bind path probe: digit -> DFT -> (scale) -> mul_DFT ->
 * inverse, against the expected F * X^pos, plus a magnitude sweep of the
 * to_DFT -> mul_DFT -> inverse envelope. */
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include "mosfhet.h"

int main(void)
{
  const int N = 1024;
  init_fft(N);
  TorusPolynomial F = polynomial_new_torus_polynomial(N);
  TorusPolynomial dig = polynomial_new_torus_polynomial(N);
  TorusPolynomial res = polynomial_new_torus_polynomial(N);
  DFT_Polynomial * dft = polynomial_new_array_of_polynomials_DFT(N, 4);
  const int pos = 7;
  const int64_t channel = (int64_t) (((Torus) 1) << 62); /* 1/4 X^pos */
  const int64_t digit =
      (channel >> 46) & ((1LL << 23) - 1); /* layer d=2 chunk */
  F->coeffs[1] = (Torus) (((__int128) 1) << 60);
  F->coeffs[5] = (Torus) (((__int128) 3) << 60);
  dig->coeffs[pos] = (Torus) digit;
  printf("digit=%lld (expect %lld) dftN=%d\n",
         (long long) digit, (long long) (1LL << 16), dft[0]->N);
  polynomial_torus_to_DFT(dft[2], F);
  polynomial_torus_to_DFT(dft[0], dig);
  const double scale = (double) (((uint64_t) 1) << 48);
  for(int q = 0; q < dft[0]->N; q++)
    dft[0]->coeffs[q] *= scale;
  polynomial_mul_DFT(dft[1], dft[0], dft[2]);
  polynomial_DFT_to_torus(res, dft[1]);
  const int p1 = (pos + 1) % N, p5 = (pos + 5) % N;
  printf("res[%d]=%ld (expect %ld) res[%d]=%ld (expect %ld)\n",
         p1, (long)((int64_t) res->coeffs[p1] >> 44), 1L << 16,
         p5, (long)((int64_t) res->coeffs[p5] >> 44), 3L << 16);
  /* magnitude sweep through the to_DFT -> mul_DFT -> inverse path */
  const int64_t am[4] = {1LL << 40, 1LL << 32, 1LL << 24, 1LL << 16};
  const int64_t bm[4] = {1LL << 20, 1LL << 30, 1LL << 44, 1LL << 52};
  printf("sweep (A@0 x B@1 -> expect (A*B>>64)@1):\n");
  for(int ai = 0; ai < 4; ai++)
  {
    for(int bi = 0; bi < 4; bi++)
    {
      polynomial_zero_torus_polynomial(dig);
      polynomial_zero_torus_polynomial(F);
      dig->coeffs[0] = (Torus) am[ai];
      F->coeffs[1] = (Torus) bm[bi];
      polynomial_torus_to_DFT(dft[0], dig);
      polynomial_torus_to_DFT(dft[2], F);
      polynomial_mul_DFT(dft[1], dft[0], dft[2]);
      polynomial_DFT_to_torus(res, dft[1]);
      printf("A=2^%2d B=2^%2d -> res=%12ld expect %10lld\n",
             40 - 8 * ai, 20 + 10 * bi,
             (long)((int64_t) res->coeffs[1] >> 44),
             (long long)((((__int128) am[ai]) * bm[bi]) >> 64 >> 44));
    }
  }
  free_polynomial(F);
  free_polynomial(dig);
  free_polynomial(res);
  free_polynomial(dft);
  return 0;
}
