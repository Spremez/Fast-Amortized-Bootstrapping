
#include "mosfhet.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE170_R
#define STAGE170_R 6
#endif
#ifndef STAGE170_N
#define STAGE170_N 2048
#endif
#ifndef STAGE170_ITEMS
#define STAGE170_ITEMS 256
#endif
#ifndef STAGE170_REPS
#define STAGE170_REPS 8
#endif
#ifndef STAGE170_WARMUPS
#define STAGE170_WARMUPS 2
#endif
#ifndef STAGE170_BG_BIT
#define STAGE170_BG_BIT 23
#endif

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

static void fill_pvmtmlwe_dft(PVW_TMLWE_DFT p, TorusPolynomial tmp, uint64_t seed) {
  fill_poly(tmp, seed ^ 0x6a09e667f3bcc909ULL);
  polynomial_torus_to_DFT(p->a[0], tmp);
  for (int lane = 0; lane < p->r; lane++) {
    fill_poly(tmp, seed ^ ((uint64_t) lane << 28) ^ 0xbb67ae8584caa73bULL);
    polynomial_torus_to_DFT(p->b[lane], tmp);
  }
}

static void fill_selector(MAT_TRGSW_DFT selector) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE170_N);
  const int rows = 1 + STAGE170_R;
  for (int row = 0; row < rows; row++) {
    fill_poly(tmp, 0xabcdef0011223344ULL ^ (uint64_t) row);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < STAGE170_R; lane++) {
      fill_poly(tmp, 0x6677889900aabbccULL ^ ((uint64_t) row << 16) ^ (uint64_t) lane);
      polynomial_torus_to_DFT(selector->samples[row]->b[lane], tmp);
    }
  }
  free_polynomial(tmp);
}

static void zero_pvmtmlwe_dft(PVW_TMLWE_DFT out) {
  memset(out->a[0]->coeffs, 0, sizeof(double) * STAGE170_N);
  for (int lane = 0; lane < out->r; lane++) {
    memset(out->b[lane]->coeffs, 0, sizeof(double) * STAGE170_N);
  }
}

static void sub_decompose_row(PVW_TMLWE in1, PVW_TMLWE in2,
    TorusPolynomial out, int row) {
  const uint64_t half_Bg = (1ULL << (STAGE170_BG_BIT - 1));
  const uint64_t h_mask = (1ULL << STAGE170_BG_BIT) - 1;
  const uint64_t word_size = sizeof(Torus) * 8;
  const uint64_t offset = (1ULL << (word_size - 1));
  const uint64_t h_bit = word_size - STAGE170_BG_BIT;

  TorusPolynomial lhs = row == 0 ? in1->a[0] : in1->b[row - 1];
  TorusPolynomial rhs = row == 0 ? in2->a[0] : in2->b[row - 1];
  for (int c = 0; c < STAGE170_N; c++) {
    const uint64_t diff = rhs->coeffs[c] - lhs->coeffs[c];
    const uint64_t coeff_off = diff + offset;
    out->coeffs[c] = ((coeff_off >> h_bit) & h_mask) - half_Bg;
  }
}

static void streaming_sub_mul_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in1,
    PVW_TMLWE in2, MAT_TRGSW_DFT selector, TorusPolynomial dec,
    DFT_Polynomial dec_dft) {
  zero_pvmtmlwe_dft(out);
  const int rows = 1 + STAGE170_R;
  for (int row = 0; row < rows; row++) {
    sub_decompose_row(in1, in2, dec, row);
    polynomial_torus_to_DFT(dec_dft, dec);
    polynomial_mul_addto_DFT(out->a[0], dec_dft, selector->samples[row]->a[0]);
    for (int lane = 0; lane < STAGE170_R; lane++) {
      polynomial_mul_addto_DFT(out->b[lane], dec_dft, selector->samples[row]->b[lane]);
    }
  }
}

static uint64_t compare_torus(PVW_TMLWE a, PVW_TMLWE b, uint64_t *max_gap) {
  uint64_t mismatches = 0;
  for (int i = 0; i < STAGE170_N; i++) {
    const uint64_t x = (uint64_t) a->a[0]->coeffs[i];
    const uint64_t y = (uint64_t) b->a[0]->coeffs[i];
    const uint64_t gap = x >= y ? x - y : y - x;
    if (gap != 0) mismatches++;
    if (gap > *max_gap) *max_gap = gap;
  }
  for (int lane = 0; lane < STAGE170_R; lane++) {
    for (int i = 0; i < STAGE170_N; i++) {
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
  for (int i = 0; i < STAGE170_N; i += 17) acc ^= a[i] + (acc << 6) + (acc >> 2);
  for (int lane = 0; lane < STAGE170_R; lane++) {
    const uint64_t *b = (const uint64_t *) out->b[lane]->coeffs;
    for (int i = 0; i < STAGE170_N; i += 17) acc ^= b[i] + (acc << 6) + (acc >> 2);
  }
  return acc;
}

static uint64_t checksum_torus(PVW_TMLWE out) {
  uint64_t acc = 0x84222325cbf29ce4ULL;
  for (int i = 0; i < STAGE170_N; i += 17) {
    acc ^= (uint64_t) out->a[0]->coeffs[i] + (acc << 6) + (acc >> 2);
  }
  for (int lane = 0; lane < STAGE170_R; lane++) {
    for (int i = 0; i < STAGE170_N; i += 17) {
      acc ^= (uint64_t) out->b[lane]->coeffs[i] + (acc << 6) + (acc >> 2);
    }
  }
  return acc;
}

static void run_mat_loop(PVW_TMLWE_DFT out, PVW_TMLWE *in1,
    PVW_TMLWE *in2, MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch) {
  for (int item = 0; item < STAGE170_ITEMS; item++) {
    mat_trgsw_mul_pvmtmlwe_sub_DFT(out, in1[item], in2[item], selector, scratch);
  }
}

static int run_mat_ep_subdecomp(void) {
  init_fft(STAGE170_N);
  MAT_TRGSW_DFT selector =
      mat_trgsw_alloc_new_DFT_sample(1, STAGE170_BG_BIT, 1, STAGE170_R, STAGE170_N);
  fill_selector(selector);

  PVW_TMLWE *in1 = pvmtmlwe_alloc_new_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  PVW_TMLWE *in2 = pvmtmlwe_alloc_new_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  for (int item = 0; item < STAGE170_ITEMS; item++) {
    fill_pvmtmlwe(in1[item], 0x100000000ULL + (uint64_t) item);
    fill_pvmtmlwe(in2[item], 0x200000000ULL + (uint64_t) item);
  }

  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, STAGE170_R, STAGE170_N);
  PVW_TMLWE_DFT stream = pvmtmlwe_alloc_new_DFT_sample(1, STAGE170_R, STAGE170_N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(1 + STAGE170_R, STAGE170_N);
  TorusPolynomial dec = polynomial_new_torus_polynomial(STAGE170_N);
  DFT_Polynomial dec_dft = polynomial_new_DFT_polynomial(STAGE170_N);

  mat_trgsw_mul_pvmtmlwe_sub_DFT(current, in1[0], in2[0], selector, scratch);
  streaming_sub_mul_DFT(stream, in1[0], in2[0], selector, dec, dec_dft);
  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, STAGE170_R, STAGE170_N);
  PVW_TMLWE stream_torus = pvmtmlwe_alloc_new_sample(1, STAGE170_R, STAGE170_N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(stream_torus, stream);
  uint64_t max_gap = 0;
  const uint64_t mismatches = compare_torus(current_torus, stream_torus, &max_gap);
  printf("CORRECT170,mat_ep_subdecomp,streaming_reference,%" PRIu64 ",%" PRIu64 ",%s\n",
      mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");

  for (int w = 0; w < STAGE170_WARMUPS; w++) {
    run_mat_loop(current, in1, in2, selector, scratch);
  }
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE170_REPS; rep++) {
    run_mat_loop(current, in1, in2, selector, scratch);
  }
  const uint64_t ns = now_ns() - start;
  const uint64_t calls = (uint64_t) STAGE170_REPS * (uint64_t) STAGE170_ITEMS;
  const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
  const uint64_t sink = checksum_dft(current);
  printf("RESULT170,mat_ep_subdecomp,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",%s\n",
      STAGE170_R, STAGE170_N, STAGE170_ITEMS, STAGE170_REPS,
      calls, ns, per_call_us, sink, mismatches == 0 ? "PASS" : "FAIL");

  free_pvmtmlwe(current_torus);
  free_pvmtmlwe(stream_torus);
  free_DFT_polynomial(dec_dft);
  free_polynomial(dec);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(current);
  free_pvmtmlwe_DFT(stream);
  free_pvmtmlwe_array(in1, STAGE170_ITEMS);
  free_pvmtmlwe_array(in2, STAGE170_ITEMS);
  free_mat_trgsw_DFT(selector);
  return mismatches == 0 ? 0 : 1;
}

static void run_from_dft_loop(PVW_TMLWE *out, PVW_TMLWE_DFT *dft,
    PVW_TMLWE *addend) {
  for (int item = 0; item < STAGE170_ITEMS; item++) {
    pvmtmlwe_from_DFT_add(out[item], dft[item], addend[item]);
  }
}

static int run_from_dft_materialize(void) {
  init_fft(STAGE170_N);
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE170_N);
  PVW_TMLWE_DFT *dft = pvmtmlwe_alloc_new_DFT_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  PVW_TMLWE *addend = pvmtmlwe_alloc_new_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  PVW_TMLWE *out = pvmtmlwe_alloc_new_sample_array(STAGE170_ITEMS, 1, STAGE170_R, STAGE170_N);
  for (int item = 0; item < STAGE170_ITEMS; item++) {
    fill_pvmtmlwe_dft(dft[item], tmp, 0x300000000ULL + (uint64_t) item);
    fill_pvmtmlwe(addend[item], 0x400000000ULL + (uint64_t) item);
  }

  PVW_TMLWE fused = pvmtmlwe_alloc_new_sample(1, STAGE170_R, STAGE170_N);
  PVW_TMLWE separate = pvmtmlwe_alloc_new_sample(1, STAGE170_R, STAGE170_N);
  pvmtmlwe_from_DFT_add(fused, dft[0], addend[0]);
  pvmtmlwe_from_DFT(separate, dft[0]);
  pvmtmlwe_addto(separate, addend[0]);
  uint64_t max_gap = 0;
  const uint64_t mismatches = compare_torus(fused, separate, &max_gap);
  printf("CORRECT170,from_dft_materialize,fused_add_reference,%" PRIu64 ",%" PRIu64 ",%s\n",
      mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");

  for (int w = 0; w < STAGE170_WARMUPS; w++) {
    run_from_dft_loop(out, dft, addend);
  }
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE170_REPS; rep++) {
    run_from_dft_loop(out, dft, addend);
  }
  const uint64_t ns = now_ns() - start;
  const uint64_t calls = (uint64_t) STAGE170_REPS * (uint64_t) STAGE170_ITEMS;
  const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
  const uint64_t sink = checksum_torus(out[STAGE170_ITEMS - 1]);
  printf("RESULT170,from_dft_materialize,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",%s\n",
      STAGE170_R, STAGE170_N, STAGE170_ITEMS, STAGE170_REPS,
      calls, ns, per_call_us, sink, mismatches == 0 ? "PASS" : "FAIL");

  free_pvmtmlwe(fused);
  free_pvmtmlwe(separate);
  free_pvmtmlwe_array(out, STAGE170_ITEMS);
  free_pvmtmlwe_array(addend, STAGE170_ITEMS);
  for (int item = 0; item < STAGE170_ITEMS; item++) {
    free_pvmtmlwe_DFT(dft[item]);
  }
  free(dft);
  free_polynomial(tmp);
  return mismatches == 0 ? 0 : 1;
}

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s mat_ep_subdecomp|from_dft_materialize\n", argv[0]);
    return 2;
  }
  if (strcmp(argv[1], "mat_ep_subdecomp") == 0) {
    return run_mat_ep_subdecomp();
  }
  if (strcmp(argv[1], "from_dft_materialize") == 0) {
    return run_from_dft_materialize();
  }
  fprintf(stderr, "unknown variant: %s\n", argv[1]);
  return 2;
}
