/* probe_bind4.c -- stage356/D4 handoff: standalone reproduction of the
 * full 4-product bind path (g = id/tau channels x d = 0..L-1 digit layers,
 * bg=32/L=2 weights), crypto-free, per the sess_b54cd3f0 capsule.
 *
 * Question: does the content-scale (quarter-scale) leak appear in the
 * isolated 4-product spectral accumulation when the channel value carries
 * EP-noise (2^49-class ints), while each single-layer product is exact?
 *
 * Reference: exact __int128 negacyclic convolution of each digit layer
 * against the weighted multiplier polynomial, accumulated, /2^64 mod 2^64
 * (the execute_reverse/direct envelope semantics inside the safe regime).
 */
#include <mosfhet.h>
#include <stdio.h>
#include <stdlib.h>

static void conv128(uint64_t * out, const uint64_t * a, const int64_t * b, int N){
  /* exact negacyclic convolution of unsigned digits a with signed b */
  for (int k = 0; k < N; k++){
    __int128 acc = 0;
    for (int i = 0; i < N; i++){
      const int j = k - i;
      if (j >= 0) acc += (__int128) a[i] * b[j];
      else acc -= (__int128) a[i] * b[j + N];
    }
    out[k] = (uint64_t) acc; /* envelope: conv mod 2^64 (low word), which
                              * is what frac(x/2^64)*2^64 computes as long
                              * as the true conv stays under ~2^116 */
  }
}

int main(int argc, char ** argv){
  setvbuf(stdout, NULL, _IONBF, 0);
  const int N = 2048;
  int bg = 32, layers = 2;
  double noise_log2 = 49.0;
  if (argc > 1) bg = atoi(argv[1]);
  if (argc > 2) layers = atoi(argv[2]);
  if (argc > 3) noise_log2 = atof(argv[3]);
  printf("BIND4 probe: bg=%d L=%d noise=2^%.1f\n", bg, layers, noise_log2);

  /* public LUT and its tau_{-1} reflection, same shape as the equiv test */
  TorusPolynomial F = polynomial_new_torus_polynomial(N);
  TorusPolynomial tF = polynomial_new_torus_polynomial(N);
  polynomial_zero_torus_polynomial(F);
  polynomial_zero_torus_polynomial(tF);
  F->coeffs[1] = int2torus(1, 4);
  F->coeffs[5] = int2torus(3, 4);
  int pos_tau = (argc > 4 && argv[4][0] == 'p');   /* tau without the minus */
  tF->coeffs[0] = F->coeffs[0];
  for (int j = 1; j < N; j++) tF->coeffs[N - j] = pos_tau ? F->coeffs[j] : -F->coeffs[j];
  if (pos_tau) printf("BIND4 POS-TAU: reversed multiplier without negation\n");

  /* synthetic channels: quarter-scale unit spikes + noise, the capsule's
   * trigger recipe (id at pos 30, tau at pos 40) */
  const double sigma = pow(2.0, noise_log2 - 64.0);
  TorusPolynomial comp[2] = {
    polynomial_new_torus_polynomial(N), polynomial_new_torus_polynomial(N)};
  comp[0]->coeffs[30] += (Torus)(1LL << 62);
  comp[1]->coeffs[40] += (Torus)(1LL << 62);
  for (int g = 0; g < 2; g++)
    for (int q = 0; q < N; q++)
      comp[g]->coeffs[q] += (Torus) double2torus(generate_normal_random(sigma));

  /* multiplier spectra exactly as sab_operator_bind builds them */
  init_fft(N);
  DFT_Polynomial * dft = polynomial_new_array_of_polynomials_DFT(N, 10);
  for (int d = 0; d < layers; d++){
    const double w = 1.0 / (double) (((Torus) 1) << (62 - bg * d));
    polynomial_torus_to_DFT(dft[4 + d], F);
    polynomial_torus_to_DFT(dft[4 + layers + d], tF);
    for (int q = 0; q < N; q++){
      dft[4 + d]->coeffs[q] *= w;
      dft[4 + layers + d]->coeffs[q] *= w;
    }
  }

  TorusPolynomial dig = polynomial_new_torus_polynomial(N);
  TorusPolynomial got = polynomial_new_torus_polynomial(N);
  uint64_t * ref = (uint64_t *) safe_malloc(sizeof(uint64_t) * N);
  uint64_t * layer_ref = (uint64_t *) safe_malloc(sizeof(uint64_t) * N);
  int64_t * mult_int = (int64_t *) safe_malloc(sizeof(int64_t) * N);
  const Torus mask = (((Torus) 1) << bg) - 1;

  /* envelope path (the bind inner loop, single component) */
  int swap_mult = (argc > 4 && argv[4][0] == 's');   /* g=1 -> F */
  int exch_mult = (argc > 4 && argv[4][0] == 'x');   /* exchange g=0 <-> g=1 */
  if (swap_mult) printf("BIND4 SWAP: g=1 multiplier forced to F (tau unused)\n");
  if (exch_mult) printf("BIND4 EXCH: multipliers exchanged between channels\n");
  int used = 0;
  TorusPolynomial sep = polynomial_new_torus_polynomial(N);
  TorusPolynomial seplayer = polynomial_new_torus_polynomial(N);
  for (int g = 0; g < 2; g++)
    for (int d = 0; d < layers; d++){
      const int shift = bg * d;
      bool any = false;
      for (int q = 0; q < N; q++){
        const Torus v = (Torus)((((int64_t) comp[g]->coeffs[q]) >> shift) & (int64_t) mask);
        dig->coeffs[q] = v;
        if (v) any = true;
      }
      if (!any) continue;
      polynomial_torus_to_DFT(dft[0], dig);
      int mrow = g;
      if (swap_mult) mrow = 0;
      if (exch_mult) mrow = 1 - g;
      DFT_Polynomial mult = dft[4 + (mrow ? layers : 0) + d];
      if (used == 0) polynomial_mul_DFT(dft[1], dft[0], mult);
      else polynomial_mul_addto_DFT(dft[1], dft[0], mult);
      /* separation mode: inverse each layer alone, sum as integers */
      polynomial_mul_DFT(dft[2], dft[0], mult);
      polynomial_DFT_to_torus(seplayer, dft[2]);
      for (int q = 0; q < N; q++) sep->coeffs[q] += seplayer->coeffs[q];
      /* per-layer envelope vs exact reference for this (g,d) */
      {
        const double w2 = pow(2.0, (double)(bg * d - 62));
        const TorusPolynomial Fg2 = (mrow ? tF : F);
        int64_t md2 = 0;
        for (int q = 0; q < N; q++)
          mult_int[q] = (int64_t) llroundl((long double) Fg2->coeffs[q] * (long double) w2);
        conv128(layer_ref, dig->coeffs, mult_int, N);
        for (int q = 0; q < N; q++){
          int64_t dv = (int64_t)(seplayer->coeffs[q] - layer_ref[q]);
          if (dv < 0) dv = -dv;
          if (dv > md2) md2 = dv;
        }
        printf("LAYER g=%d d=%d envelope-vs-exact max log2 = %.2f\n",
               g, d, log2((double)(md2 + 1)));
        {
          /* digit/comp magnitude sanity: distinguishes 2^17/2^30-class
           * digits (healthy) from 2^31+-class (pathological noise) */
          uint64_t dmax = 0; int dpos = -1;
          for (int q = 0; q < N; q++)
            if(dig->coeffs[q] > dmax){ dmax = dig->coeffs[q]; dpos = q; }
          printf("  DIGSTAT g=%d d=%d max=%llu (2^%.1f) at %d\n",
                 g, d, (unsigned long long) dmax,
                 log2((double)(dmax + 1)), dpos);
        }
        if(md2 > (1LL << 40)){
          /* export the worst mismatch for external exact arbitration */
          int worst_q = -1;
          int64_t worst_dv = 0;
          for (int q = 0; q < N; q++){
            int64_t dv = (int64_t)(seplayer->coeffs[q] - layer_ref[q]);
            if(dv < 0) dv = -dv;
            if(dv > worst_dv){ worst_dv = dv; worst_q = q; }
          }
          printf("  WORST g=%d d=%d k=%d env=%lld ref=%lld\n", g, d, worst_q,
                 (long long)(int64_t)seplayer->coeffs[worst_q],
                 (long long)(int64_t)layer_ref[worst_q]);
          for (int t = 0; t < 3; t++){
            int64_t best = 0; int bi = -1;
            for (int i = 0; i < N; i++){
              const int j = ((worst_q - i) % N + N) % N;
              const int64_t term = (int64_t) dig->coeffs[i] * mult_int[j];
              if (i + j == worst_q ? false : false) continue;
              if (llabs(term) > llabs(best)){ best = term; bi = i; }
            }
            (void) bi; (void) best;
            break;
          }
          /* dump dig + mult for python arbitration of the worst k */
          char fn[128];
          snprintf(fn, sizeof fn, "/mnt/d/bind4_dump_g%d_d%d.bin", g, d);
          FILE * fh = fopen(fn, "wb");
          if(fh){
            fwrite(dig->coeffs, sizeof(Torus), N, fh);
            fwrite(mult_int, sizeof(int64_t), N, fh);
            fprintf(fh, "WORSTK %d", worst_q);
            fclose(fh);
            printf("  dumped %s (worst k=%d)\n", fn, worst_q);
          }
        }
      }
      used++;
    }
  polynomial_DFT_to_torus(got, dft[1]);
  {
    int64_t md = 0;
    for (int q = 0; q < N; q++){
      int64_t dv = (int64_t)(sep->coeffs[q] - got->coeffs[q]);
      if (dv < 0) dv = -dv;
      if (dv > md) md = dv;
    }
    printf("BIND4 separate-inverse vs accumulated: max diff log2 = %.2f %s\n",
           log2((double)(md + 1)), md < (1LL << 40) ? "(same)" : "(DIFFER: accumulation is the trigger)");
  }

  /* exact reference with the same weights: mult_d(x) = F * 2^(bg*d-62)
   * rounded to the nearest int64 (the double spectrum carries F*w). */
  for (int k = 0; k < N; k++) ref[k] = 0;
  for (int g = 0; g < 2; g++)
    for (int d = 0; d < layers; d++){
      const int shift = bg * d;
      const double w = pow(2.0, (double)(bg * d - 62));
      bool any = false;
      for (int q = 0; q < N; q++){
        const Torus v = (Torus)((((int64_t) comp[g]->coeffs[q]) >> shift) & (int64_t) mask);
        dig->coeffs[q] = v;
        if (v) any = true;
      }
      if (!any) continue;
      const TorusPolynomial Fg = g ? tF : F;
      for (int q = 0; q < N; q++){
        /* multiplier coefficient as the double spectrum encodes it */
        long double m = (long double) Fg->coeffs[q] * (long double) w;
        mult_int[q] = (int64_t) llroundl(m);
      }
      conv128(layer_ref, dig->coeffs, mult_int, N);
      for (int k = 0; k < N; k++) ref[k] += layer_ref[k];
    }

  /* report: envelope vs exact reference, and the expected signal peaks */
  int64_t max_dev = 0; int worst = -1;
  for (int k = 0; k < N; k++){
    int64_t dv = (int64_t)(got->coeffs[k] - ref[k]);
    if (dv < 0) dv = -dv;
    if (dv > max_dev){ max_dev = dv; worst = k; }
  }
  const int e1 = (40 - 1 + N) % N, e5 = (40 - 5 + N) % N; /* tau reflections */
  printf("BIND4 got[1]=%ld got[5]=%ld got[e1=%d]=%ld got[e5=%d]=%ld\n",
         (long)((int64_t)got->coeffs[1] >> 44), (long)((int64_t)got->coeffs[5] >> 44),
         e1, (long)((int64_t)got->coeffs[e1] >> 44),
         e5, (long)((int64_t)got->coeffs[e5] >> 44));
  printf("BIND4 ref[1]=%ld ref[5]=%ld ref[e1]=%ld ref[e5]=%ld\n",
         (long)((int64_t)ref[1] >> 44), (long)((int64_t)ref[5] >> 44),
         (long)((int64_t)ref[e1] >> 44), (long)((int64_t)ref[e5] >> 44));
  printf("BIND4 max|got-ref| log2 = %.2f at [%d] (F-scale is 2^60; quarter-scale 2^62) %s\n",
         log2((double)(max_dev + 1)), worst,
         max_dev < (1LL << 40) ? "EXACT-CLASS" : "LEAK");
  return 0;
}
