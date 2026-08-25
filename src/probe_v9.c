/* Standalone v9 path probe: digit spectrum x time-wrapped F spectrum. */
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
  F->coeffs[1] = (Torus) (((__int128) 1) << 60);
  F->coeffs[5] = (Torus) (((__int128) 3) << 60);
  dig->coeffs[0] = (Torus)(1LL << 16); /* digit of 2^62 at layer d=2 */
  /* F_2 = F << 46 (mod 2^64) */
  TorusPolynomial wrap = polynomial_new_torus_polynomial(N);
  for(int q = 0; q < N; q++)
    wrap->coeffs[q] = (Torus)(((uint64_t) F->coeffs[q]) << 46);
  printf("F_2[1]=%ld F_2[5]=%ld (expect 2^42 and 3*2^42 = %ld %ld)\n",
         (long)((int64_t) wrap->coeffs[1] >> 40),
         (long)((int64_t) wrap->coeffs[5] >> 40),
         1L << 2, 3L << 2);
  polynomial_torus_to_DFT(dft[2], wrap);
  polynomial_torus_to_DFT(dft[0], dig);
  polynomial_mul_DFT(dft[1], dft[0], dft[2]);
  polynomial_DFT_to_torus(res, dft[1]);
  for(int q = 0; q < N; q++)
    res->coeffs[q] = (Torus)(res->coeffs[q] << 2);
  printf("res[1]=%ld (expect %ld) res[5]=%ld (expect %ld)\n",
         (long)((int64_t) res->coeffs[1] >> 44), 1L << 16,
         (long)((int64_t) res->coeffs[5] >> 44), 3L << 16);
  /* control: what does dig (2^16) x full F (2^60) give? */
  polynomial_torus_to_DFT(dft[2], F);
  polynomial_mul_DFT(dft[1], dft[0], dft[2]);
  polynomial_DFT_to_torus(res, dft[1]);
  printf("ctrl dig x F: res[1]=%ld (integer 2^76 mod 2^64 = 2^12 -> %ld)\n",
         (long)((int64_t) res->coeffs[1] >> 44),
         (long)(((( __int128)(1LL << 16)) * (((__int128)1) << 60)) >> 64 >> 44));
  free_polynomial(F); free_polynomial(dig); free_polynomial(res);
  free_polynomial(wrap); free_polynomial(dft);
  return 0;
}
