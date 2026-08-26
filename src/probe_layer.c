/* Layer-isolation probe with config sweep: for each (bg, layers) config,
 * multiply a mask-scale random polynomial against every layer's
 * prescaled-weighted F spectrum and compare with the exact __int128
 * negacyclic convolution. */
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include "mosfhet.h"

static uint64_t rng_state = 0x9E3779B97F4A7C15ull;
static uint64_t rng(void)
{
  rng_state ^= rng_state << 13;
  rng_state ^= rng_state >> 7;
  rng_state ^= rng_state << 17;
  return rng_state;
}

int main(void)
{
  const int N = 1024;
  init_fft(N);
  TorusPolynomial F = polynomial_new_torus_polynomial(N);
  TorusPolynomial mask = polynomial_new_torus_polynomial(N);
  TorusPolynomial res = polynomial_new_torus_polynomial(N);
  DFT_Polynomial * dft = polynomial_new_array_of_polynomials_DFT(N, 4);
  F->coeffs[1] = (Torus) (((__int128) 1) << 60);
  F->coeffs[5] = (Torus) (((__int128) 3) << 60);
  for(int i = 0; i < N; i++)
    mask->coeffs[i] = (Torus)((int64_t) rng());
  /* noisy channel: spike + EP-scale noise on ALL coefficients */
  mask->coeffs[30] += (Torus)(1LL << 62);
  mask->coeffs[40] += (Torus)(1LL << 62);
  for(int i = 0; i < N; i++)
    mask->coeffs[i] += (Torus)((int64_t)(rng() % (1ULL << 20)) - (1LL << 19));
  const int cfgs[5][2] = {{23, 3}, {32, 2}, {16, 4}, {11, 6}, {8, 8}};
  for(int ci = 0; ci < 5; ci++)
  {
    const int cbg = cfgs[ci][0];
    const int L = cfgs[ci][1];
    int64_t worst_all = 0;
    for(int d = 0; d < L; d++)
    {
      const double w = 1.0 / (double) (((Torus) 1) << (62 - cbg * d));
      polynomial_torus_to_DFT(dft[2], F);
      for(int q = 0; q < dft[2]->N; q++)
        dft[2]->coeffs[q] *= w;
      polynomial_torus_to_DFT(dft[0], mask);
      polynomial_mul_DFT(dft[1], dft[0], dft[2]);
      polynomial_DFT_to_torus(res, dft[1]);
      int64_t worst = 0;
      for(int k = 0; k < N; k++)
      {
        __int128 acc = 0;
        for(int j = 0; j < N; j++)
        {
          int src = (k - j + 2 * N) % N;
          int64_t f = (int64_t) F->coeffs[src];
          if(!f) continue;
          int64_t m = (int64_t) mask->coeffs[j];
          int diff = ((k - j) % (2 * N) + 2 * N) % (2 * N);
          if(diff >= N) f = -f;
          acc += (__int128) m * f;
        }
        int shift = 62 - cbg * d;
        int64_t exact = (int64_t)(acc >> shift);
        int64_t err = (int64_t) res->coeffs[k] - exact;
        if(err < 0) err = -err;
        if(err > worst) worst = err;
      }
      if(worst > worst_all) worst_all = worst;
    }
    /* spectral accumulation: both layers in ONE buffer, one inverse */
    {
      int used = 0;
      TorusPolynomial digp = polynomial_new_torus_polynomial(N);
      const Torus dmask = (((Torus) 1) << cbg) - 1;
      for(int d = 0; d < L; d++)
      {
        const double w = 1.0 / (double) (((Torus) 1) << (62 - cbg * d));
        for(int q = 0; q < N; q++)
          digp->coeffs[q] = (Torus)(
              (((int64_t) mask->coeffs[q]) >> (cbg * d)) & (int64_t) dmask);
        polynomial_torus_to_DFT(dft[0], digp);
        polynomial_torus_to_DFT(dft[2], F);
        for(int q = 0; q < dft[2]->N; q++)
          dft[2]->coeffs[q] *= w;
        if(used == 0)
          polynomial_mul_DFT(dft[1], dft[0], dft[2]);
        else
          polynomial_mul_addto_DFT(dft[1], dft[0], dft[2]);
        used++;
      }
      polynomial_DFT_to_torus(res, dft[1]);
      int64_t worst_acc = 0;
      for(int k = 0; k < N; k++)
      {
        __int128 acc = 0;
        for(int j = 0; j < N; j++)
        {
          int src = (k - j + 2 * N) % N;
          int64_t f = (int64_t) F->coeffs[src];
          if(!f) continue;
          int64_t m = (int64_t) mask->coeffs[j];
          int diff = ((k - j) % (2 * N) + 2 * N) % (2 * N);
          if(diff >= N) f = -f;
          acc += (__int128) m * f;
        }
        int64_t exact = (int64_t)(acc >> 62);
        int64_t err = (int64_t) res->coeffs[k] - exact;
        if(err < 0) err = -err;
        if(err > worst_acc) worst_acc = err;
      }
      printf("cfg bg=%2d L=%d: per-layer=%5ld ACCUM=%5ld u2^44 %s\n",
             cbg, L, (long)(worst_all >> 44), (long)(worst_acc >> 44),
             (worst_acc >> 44) < 16 ? "FEASIBLE" : "BROKEN");
      free_polynomial(digp);
    }
  }
  free_polynomial(F); free_polynomial(mask); free_polynomial(res);
  free_polynomial(dft);
  return 0;
}
