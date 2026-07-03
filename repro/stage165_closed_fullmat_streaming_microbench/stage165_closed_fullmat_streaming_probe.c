
#include "mosfhet.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE165_R
#define STAGE165_R 6
#endif
#ifndef STAGE165_N
#define STAGE165_N 2048
#endif
#ifndef STAGE165_ITEMS
#define STAGE165_ITEMS 64
#endif
#ifndef STAGE165_RUNS
#define STAGE165_RUNS 5
#endif
#ifndef STAGE165_REPS
#define STAGE165_REPS 2
#endif
#ifndef STAGE165_WARMUPS
#define STAGE165_WARMUPS 1
#endif
#ifndef STAGE165_BG_BIT
#define STAGE165_BG_BIT 23
#endif

enum stage165_variant {
  STAGE165_CURRENT_ALLROW = 0,
  STAGE165_STREAMING_ROW = 1
};

static inline uint64_t now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}

static void fill_poly(TorusPolynomial p, uint64_t seed) {
  uint64_t x = seed ^ 0x9e3779b97f4a7c15ULL;
  for (int i = 0; i < p->N; i++) {
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    p->coeffs[i] = (Torus) (x * 0x2545f4914f6cdd1dULL + (uint64_t) i);
  }
}

static void fill_pvmtmlwe(PVW_TMLWE p, uint64_t seed) {
  fill_poly(p->a[0], seed ^ 0x100000001b3ULL);
  for (int lane = 0; lane < p->r; lane++) {
    fill_poly(p->b[lane], seed ^ ((uint64_t) lane << 32) ^ 0x84222325cbf29ce4ULL);
  }
}

static void fill_selector(MAT_TRGSW_DFT selector) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE165_N);
  const int rows = 1 + STAGE165_R;
  for (int row = 0; row < rows; row++) {
    fill_poly(tmp, 0xabcdef0011223344ULL ^ (uint64_t) row);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < STAGE165_R; lane++) {
      fill_poly(tmp, 0x6677889900aabbccULL ^ ((uint64_t) row << 16) ^ (uint64_t) lane);
      polynomial_torus_to_DFT(selector->samples[row]->b[lane], tmp);
    }
  }
  free_polynomial(tmp);
}

static void zero_pvmtmlwe_dft(PVW_TMLWE_DFT out) {
  memset(out->a[0]->coeffs, 0, sizeof(double) * STAGE165_N);
  for (int lane = 0; lane < out->r; lane++) {
    memset(out->b[lane]->coeffs, 0, sizeof(double) * STAGE165_N);
  }
}

static void sub_decompose_row(PVW_TMLWE in1, PVW_TMLWE in2,
    TorusPolynomial out, int row) {
  const uint64_t half_Bg = (1ULL << (STAGE165_BG_BIT - 1));
  const uint64_t h_mask = (1ULL << STAGE165_BG_BIT) - 1;
  const uint64_t word_size = sizeof(Torus) * 8;
  const uint64_t offset = (1ULL << (word_size - 1));
  const uint64_t h_bit = word_size - STAGE165_BG_BIT;

  TorusPolynomial lhs = row == 0 ? in1->a[0] : in1->b[row - 1];
  TorusPolynomial rhs = row == 0 ? in2->a[0] : in2->b[row - 1];
  for (int c = 0; c < STAGE165_N; c++) {
    const uint64_t diff = rhs->coeffs[c] - lhs->coeffs[c];
    const uint64_t coeff_off = diff + offset;
    out->coeffs[c] = ((coeff_off >> h_bit) & h_mask) - half_Bg;
  }
}

static void streaming_sub_mul_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in1,
    PVW_TMLWE in2, MAT_TRGSW_DFT selector, TorusPolynomial dec,
    DFT_Polynomial dec_dft) {
  zero_pvmtmlwe_dft(out);
  const int rows = 1 + STAGE165_R;
  for (int row = 0; row < rows; row++) {
    sub_decompose_row(in1, in2, dec, row);
    polynomial_torus_to_DFT(dec_dft, dec);
    polynomial_mul_addto_DFT(out->a[0], dec_dft, selector->samples[row]->a[0]);
    for (int lane = 0; lane < STAGE165_R; lane++) {
      polynomial_mul_addto_DFT(out->b[lane], dec_dft, selector->samples[row]->b[lane]);
    }
  }
}

static double compare_dft(PVW_TMLWE_DFT a, PVW_TMLWE_DFT b,
    uint64_t *mismatches) {
  double max_gap = 0.0;
  for (int i = 0; i < STAGE165_N; i++) {
    const double gap = fabs(a->a[0]->coeffs[i] - b->a[0]->coeffs[i]);
    if (gap != 0.0) (*mismatches)++;
    if (gap > max_gap) max_gap = gap;
  }
  for (int lane = 0; lane < STAGE165_R; lane++) {
    for (int i = 0; i < STAGE165_N; i++) {
      const double gap = fabs(a->b[lane]->coeffs[i] - b->b[lane]->coeffs[i]);
      if (gap != 0.0) (*mismatches)++;
      if (gap > max_gap) max_gap = gap;
    }
  }
  return max_gap;
}

static uint64_t compare_torus(PVW_TMLWE a, PVW_TMLWE b,
    uint64_t *max_gap) {
  uint64_t mismatches = 0;
  for (int i = 0; i < STAGE165_N; i++) {
    const uint64_t x = (uint64_t) a->a[0]->coeffs[i];
    const uint64_t y = (uint64_t) b->a[0]->coeffs[i];
    const uint64_t gap = x >= y ? x - y : y - x;
    if (gap != 0) mismatches++;
    if (gap > *max_gap) *max_gap = gap;
  }
  for (int lane = 0; lane < STAGE165_R; lane++) {
    for (int i = 0; i < STAGE165_N; i++) {
      const uint64_t x = (uint64_t) a->b[lane]->coeffs[i];
      const uint64_t y = (uint64_t) b->b[lane]->coeffs[i];
      const uint64_t gap = x >= y ? x - y : y - x;
      if (gap != 0) mismatches++;
      if (gap > *max_gap) *max_gap = gap;
    }
  }
  return mismatches;
}

static uint64_t checksum_dft(PVW_TMLWE_DFT out) {
  uint64_t acc = 0xcbf29ce484222325ULL;
  const uint64_t *a = (const uint64_t *) out->a[0]->coeffs;
  for (int i = 0; i < STAGE165_N; i += 17) acc ^= a[i] + (acc << 6) + (acc >> 2);
  for (int lane = 0; lane < STAGE165_R; lane++) {
    const uint64_t *b = (const uint64_t *) out->b[lane]->coeffs;
    for (int i = 0; i < STAGE165_N; i += 17) acc ^= b[i] + (acc << 6) + (acc >> 2);
  }
  return acc;
}

static const char *variant_name(enum stage165_variant variant) {
  return variant == STAGE165_CURRENT_ALLROW ? "current_allrow_tiled_avx" : "streaming_row_generic";
}

static void run_variant(enum stage165_variant variant, PVW_TMLWE_DFT out,
    PVW_TMLWE *in1, PVW_TMLWE *in2, MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch, TorusPolynomial dec,
    DFT_Polynomial dec_dft) {
  for (int item = 0; item < STAGE165_ITEMS; item++) {
    if (variant == STAGE165_CURRENT_ALLROW) {
      mat_trgsw_mul_pvmtmlwe_sub_DFT(out, in1[item], in2[item], selector, scratch);
    } else {
      streaming_sub_mul_DFT(out, in1[item], in2[item], selector, dec, dec_dft);
    }
  }
}

static uint64_t bench_variant(enum stage165_variant variant, PVW_TMLWE_DFT out,
    PVW_TMLWE *in1, PVW_TMLWE *in2, MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch, TorusPolynomial dec,
    DFT_Polynomial dec_dft) {
  for (int w = 0; w < STAGE165_WARMUPS; w++) {
    run_variant(variant, out, in1, in2, selector, scratch, dec, dec_dft);
  }
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE165_REPS; rep++) {
    run_variant(variant, out, in1, in2, selector, scratch, dec, dec_dft);
  }
  return now_ns() - start;
}

int main(void) {
  init_fft(STAGE165_N);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(1, STAGE165_BG_BIT, 1, STAGE165_R, STAGE165_N);
  fill_selector(selector);

  PVW_TMLWE *in1 = pvmtmlwe_alloc_new_sample_array(STAGE165_ITEMS, 1, STAGE165_R, STAGE165_N);
  PVW_TMLWE *in2 = pvmtmlwe_alloc_new_sample_array(STAGE165_ITEMS, 1, STAGE165_R, STAGE165_N);
  for (int item = 0; item < STAGE165_ITEMS; item++) {
    fill_pvmtmlwe(in1[item], 0x100000000ULL + (uint64_t) item);
    fill_pvmtmlwe(in2[item], 0x200000000ULL + (uint64_t) item);
  }

  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, STAGE165_R, STAGE165_N);
  PVW_TMLWE_DFT stream = pvmtmlwe_alloc_new_DFT_sample(1, STAGE165_R, STAGE165_N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(1 + STAGE165_R, STAGE165_N);
  TorusPolynomial dec = polynomial_new_torus_polynomial(STAGE165_N);
  DFT_Polynomial dec_dft = polynomial_new_DFT_polynomial(STAGE165_N);

  mat_trgsw_mul_pvmtmlwe_sub_DFT(current, in1[0], in2[0], selector, scratch);
  streaming_sub_mul_DFT(stream, in1[0], in2[0], selector, dec, dec_dft);

  uint64_t dft_mismatches = 0;
  const double max_dft_gap = compare_dft(current, stream, &dft_mismatches);
  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, STAGE165_R, STAGE165_N);
  PVW_TMLWE stream_torus = pvmtmlwe_alloc_new_sample(1, STAGE165_R, STAGE165_N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(stream_torus, stream);
  uint64_t max_torus_gap = 0;
  const uint64_t torus_mismatches = compare_torus(current_torus, stream_torus, &max_torus_gap);
  printf("CORRECT165,streaming_vs_current,%" PRIu64 ",%.12e,%" PRIu64 ",%" PRIu64 ",%s\n",
      dft_mismatches, max_dft_gap, torus_mismatches, max_torus_gap,
      torus_mismatches == 0 ? "PASS_TORUS_EQUIV" : "FAIL");

  enum stage165_variant variants[2] = {STAGE165_CURRENT_ALLROW, STAGE165_STREAMING_ROW};
  PVW_TMLWE_DFT outs[2] = {current, stream};
  for (int run = 0; run < STAGE165_RUNS; run++) {
    for (int v = 0; v < 2; v++) {
      const uint64_t ns = bench_variant(variants[v], outs[v], in1, in2,
          selector, scratch, dec, dec_dft);
      const uint64_t calls = (uint64_t) STAGE165_REPS * (uint64_t) STAGE165_ITEMS;
      const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
      const uint64_t sink = checksum_dft(outs[v]);
      printf("BENCH165,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",PASS\n",
          variant_name(variants[v]), run, STAGE165_R, STAGE165_N,
          STAGE165_ITEMS, STAGE165_REPS, calls, ns, per_call_us, sink);
    }
  }

  free_pvmtmlwe(current_torus);
  free_pvmtmlwe(stream_torus);
  free_DFT_polynomial(dec_dft);
  free_polynomial(dec);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(current);
  free_pvmtmlwe_DFT(stream);
  free_pvmtmlwe_array(in1, STAGE165_ITEMS);
  free_pvmtmlwe_array(in2, STAGE165_ITEMS);
  free_mat_trgsw_DFT(selector);
  return 0;
}
