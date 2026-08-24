/* Standalone primitive probe: find the valid magnitude range of
 * polynomial_mul_torus. Motivated by the D4 unit probe: (2^62 at 0)
 * convolved with (16 at 1) returned zero. */
#include <stdio.h>
#include <stdlib.h>
#include "mosfhet.h"

int main(void)
{
  const int PN = 1024;
  init_fft(PN);
  TorusPolynomial A = polynomial_new_torus_polynomial(PN);
  TorusPolynomial B = polynomial_new_torus_polynomial(PN);
  TorusPolynomial C = polynomial_new_torus_polynomial(PN);
  const int64_t mags[6] = {1LL << 62, 1LL << 58, 1LL << 54, 1LL << 50,
                           1LL << 46, 1LL << 40};
  const int64_t bm[4] = {16, 256, 1LL << 20, 1LL << 30};
  printf("%-12s %-12s %-22s %s\n", "A", "B", "C[1] (int64)", "expect (A*B>>64)");
  for(int mi = 0; mi < 6; mi++)
  {
    for(int bi = 0; bi < 4; bi++)
    {
      polynomial_zero_torus_polynomial(A);
      polynomial_zero_torus_polynomial(B);
      A->coeffs[0] = (Torus) mags[mi];
      B->coeffs[1] = (Torus) bm[bi];
      polynomial_mul_torus(C, A, B);
      __int128 expect = ((__int128) mags[mi]) * ((__int128) bm[bi]) >> 64;
      printf("2^%-10d 2^%-10d %-22lld %lld\n", 62 - 4 * mi,
             4 + 2 * bi == 4 ? 4 : 4 + 2 * bi == 6 ? 8 : 4 + 2 * bi == 8 ? 20 : 30,
             (long long)((int64_t) C->coeffs[1]), (long long) expect);
    }
  }
  free_polynomial(A);
  free_polynomial(B);
  free_polynomial(C);
  return 0;
}
