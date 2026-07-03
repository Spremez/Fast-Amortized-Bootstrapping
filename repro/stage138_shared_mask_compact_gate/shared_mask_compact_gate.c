#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE138_BACKEND
#define STAGE138_BACKEND "unknown"
#endif

static volatile double g_stage138_sink = 0.0;

static uint64_t stage138_now_ns(void){
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static uint64_t mix64(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  return x;
}

static void fill_source(TorusPolynomial out, int lane, int kind, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(138000 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static TorusPolynomial * new_poly_array(int count, int N) {
  TorusPolynomial *out =
      (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * count);
  for (int i = 0; i < count; i++) out[i] = polynomial_new_torus_polynomial(N);
  return out;
}

static void free_poly_array_local(TorusPolynomial *in, int count) {
  for (int i = 0; i < count; i++) free_polynomial(in[i]);
  free(in);
}

static void zero_dft(DFT_Polynomial p) {
  memset(p->coeffs, 0, sizeof(double) * p->N);
}

static void zero_compact_output(MAT_TRGSW_COMPACT_OUTPUT_DFT out) {
  for (int lane = 0; lane < out->r; lane++) {
    zero_dft(out->a[lane]);
    zero_dft(out->b[lane]);
  }
}

static double abs_double(double x) {
  return x < 0.0 ? -x : x;
}

static void compare_dft(DFT_Polynomial a, DFT_Polynomial b,
    uint64_t *mismatches, double *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const double gap = abs_double(a->coeffs[i] - b->coeffs[i]);
    if (gap != 0.0) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void consume_output(MAT_TRGSW_COMPACT_OUTPUT_DFT out) {
  double acc = 0.0;
  for (int lane = 0; lane < out->r; lane++) {
    for (int i = 0; i < out->N; i += 17) {
      acc += out->a[lane]->coeffs[i] * 0.0000000001;
      acc += out->b[lane]->coeffs[i] * 0.0000000002;
    }
  }
  g_stage138_sink += acc;
}

static void repeated_lane_pair_compact_mul(MAT_TRGSW_COMPACT_OUTPUT_DFT out,
    PVW_TMLWE in, MAT_TRGSW_COMPACT_DFT selector,
    MAT_TRGSW_COMPACT_MUL_SCRATCH scratch) {
  zero_compact_output(out);
  for (int lane = 0; lane < selector->r; lane++) {
    for (int t = 0; t < selector->T; t++) {
      const int idx = t * selector->r + lane;
      polynomial_decompose_i(scratch->dec_shared, in->a[0],
          selector->Q, selector->T, t);
      polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
      polynomial_decompose_i(scratch->dec_body, in->b[lane],
          selector->Q, selector->T, t);
      polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
      polynomial_mul_addto_DFT(out->a[lane], scratch->dec_shared_dft,
          selector->shared_a[idx]);
      polynomial_mul_addto_DFT(out->b[lane], scratch->dec_shared_dft,
          selector->shared_b[idx]);
      polynomial_mul_addto_DFT(out->a[lane], scratch->dec_body_dft,
          selector->body_a[idx]);
      polynomial_mul_addto_DFT(out->b[lane], scratch->dec_body_dft,
          selector->body_b[idx]);
    }
  }
}

static void fill_case(PVW_TMLWE in, MAT_TRGSW_COMPACT_DFT selector,
    int r, int N, int T, int Bg_bit, int seed) {
  (void)N;
  (void)T;
  (void)Bg_bit;
  fill_source(in->a[0], 0, 100, seed);
  for (int lane = 0; lane < r; lane++) {
    fill_source(in->b[lane], lane, 200, seed);
  }

  const int rows = T * r;
  TorusPolynomial *shared_a = new_poly_array(rows, N);
  TorusPolynomial *shared_b = new_poly_array(rows, N);
  TorusPolynomial *body_a = new_poly_array(rows, N);
  TorusPolynomial *body_b = new_poly_array(rows, N);
  for (int t = 0; t < T; t++) {
    for (int lane = 0; lane < r; lane++) {
      const int idx = t * r + lane;
      fill_source(shared_a[idx], lane, 300 + t, seed);
      fill_source(shared_b[idx], lane, 400 + t, seed);
      fill_source(body_a[idx], lane, 500 + t, seed);
      fill_source(body_b[idx], lane, 600 + t, seed);
      mat_trgsw_compact_set_row_from_torus(selector, t, lane,
          shared_a[idx], shared_b[idx], body_a[idx], body_b[idx]);
    }
  }
  free_poly_array_local(shared_a, rows);
  free_poly_array_local(shared_b, rows);
  free_poly_array_local(body_a, rows);
  free_poly_array_local(body_b, rows);
}

static void correctness_case(int r, int N, int T, int Bg_bit, int seed) {
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_COMPACT_DFT selector =
      mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT repeated =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT shared =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch =
      mat_trgsw_compact_alloc_mul_scratch(N);

  fill_case(in, selector, r, N, T, Bg_bit, seed);
  repeated_lane_pair_compact_mul(repeated, in, selector, scratch);
  mat_trgsw_compact_mul_pvmtmlwe_DFT(shared, in, selector, scratch);

  uint64_t mismatches = 0;
  double max_gap = 0.0;
  for (int lane = 0; lane < r; lane++) {
    compare_dft(repeated->a[lane], shared->a[lane], &mismatches, &max_gap);
    compare_dft(repeated->b[lane], shared->b[lane], &mismatches, &max_gap);
  }
  const uint64_t repeated_dft = 2ULL * (uint64_t)r * (uint64_t)T;
  const uint64_t shared_dft = ((uint64_t)r + 1ULL) * (uint64_t)T;
  printf("CORRECT138,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,0.000000000,%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE138_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap,
      repeated_dft, shared_dft,
      mismatches == 0 ? "PASS_SHARED_MASK_EQUIV" : "FAIL");

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(shared);
  free_mat_trgsw_compact_output_DFT(repeated);
  free_mat_trgsw_compact_DFT(selector);
  free_pvmtmlwe(in);
}

static void emit_bench_row(int r, int N, int T, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant, uint64_t total_ns,
    uint64_t dft_count) {
  const double avg_us = (double)total_ns / (1000.0 * (double)reps);
  const double per_lane_us = avg_us / (double)r;
  printf("BENCH138,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%.6f,%" PRIu64 ",PASS\n",
      STAGE138_BACKEND, r, N, T, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, per_lane_us, dft_count);
}

static void bench_case(int r, int N, int T, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_COMPACT_DFT selector =
      mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT repeated =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT shared =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch =
      mat_trgsw_compact_alloc_mul_scratch(N);
  const uint64_t repeated_dft = 2ULL * (uint64_t)r * (uint64_t)T;
  const uint64_t shared_dft = ((uint64_t)r + 1ULL) * (uint64_t)T;

  fill_case(in, selector, r, N, T, Bg_bit, seed);
  for (int i = 0; i < warmups; i++) {
    repeated_lane_pair_compact_mul(repeated, in, selector, scratch);
    consume_output(repeated);
    mat_trgsw_compact_mul_pvmtmlwe_DFT(shared, in, selector, scratch);
    consume_output(shared);
  }

  for (int sample = 0; sample < samples; sample++) {
    uint64_t begin = stage138_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      repeated_lane_pair_compact_mul(repeated, in, selector, scratch);
      consume_output(repeated);
    }
    uint64_t total = stage138_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "repeated_lane_pair", total, repeated_dft);

    begin = stage138_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      mat_trgsw_compact_mul_pvmtmlwe_DFT(shared, in, selector, scratch);
      consume_output(shared);
    }
    total = stage138_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "shared_mask_compact", total, shared_dft);
  }

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(shared);
  free_mat_trgsw_compact_output_DFT(repeated);
  free_mat_trgsw_compact_DFT(selector);
  free_pvmtmlwe(in);
}

int main(void) {
  const int T = 7;
  const int Bg_bit = 7;
  const int seed = 0;
  const int samples = 5;
  const int reps = 20;
  const int warmups = 2;
  correctness_case(2, 512, T, Bg_bit, seed);
  correctness_case(4, 512, T, Bg_bit, seed);
  correctness_case(6, 512, T, Bg_bit, seed);
  correctness_case(2, 1024, T, Bg_bit, seed);
  correctness_case(4, 1024, T, Bg_bit, seed);
  correctness_case(6, 1024, T, Bg_bit, seed);
  bench_case(2, 512, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(4, 512, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(6, 512, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(2, 1024, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(4, 1024, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(6, 1024, T, Bg_bit, seed, samples, reps, warmups);
  fprintf(stderr, "stage138_sink=%f\n", g_stage138_sink);
  return 0;
}
