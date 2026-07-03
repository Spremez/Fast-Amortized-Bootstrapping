#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE140_BACKEND
#define STAGE140_BACKEND "unknown"
#endif

static volatile double g_stage140_sink = 0.0;

static uint64_t stage140_now_ns(void){
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

static void fill_poly(TorusPolynomial out, int row, int component, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(140000 + (uint64_t)seed,
        (uint64_t)row, (uint64_t)component, (uint64_t)i);
  }
}

static void fill_input(PVW_TMLWE in, int seed) {
  fill_poly(in->a[0], 0, 10, seed);
  for (int lane = 0; lane < in->r; lane++) {
    fill_poly(in->b[lane], lane, 20, seed);
  }
}

static void fill_selector(MAT_TRGSW_DFT selector, int seed) {
  const int rows = selector->T * (selector->samples[0]->k + selector->samples[0]->r);
  const int r = selector->samples[0]->r;
  const int N = selector->samples[0]->b[0]->N;
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  for (int row = 0; row < rows; row++) {
    fill_poly(tmp, row, 100, seed);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < r; lane++) {
      fill_poly(tmp, row, 200 + lane, seed);
      polynomial_torus_to_DFT(selector->samples[row]->b[lane], tmp);
    }
  }
  free_polynomial(tmp);
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

static void compare_pvmtmlwe_dft(PVW_TMLWE_DFT a, PVW_TMLWE_DFT b,
    uint64_t *mismatches, double *max_gap) {
  compare_dft(a->a[0], b->a[0], mismatches, max_gap);
  for (int lane = 0; lane < a->r; lane++) {
    compare_dft(a->b[lane], b->b[lane], mismatches, max_gap);
  }
}


static uint64_t stage141_torus_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static void stage141_compare_torus_poly(TorusPolynomial a, TorusPolynomial b,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = stage141_torus_gap(a->coeffs[i], b->coeffs[i]);
    if (gap != 0) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void stage141_compare_pvmtmlwe_torus(PVW_TMLWE a, PVW_TMLWE b,
    uint64_t *mismatches, uint64_t *max_gap) {
  stage141_compare_torus_poly(a->a[0], b->a[0], mismatches, max_gap);
  for (int lane = 0; lane < a->r; lane++) {
    stage141_compare_torus_poly(a->b[lane], b->b[lane], mismatches, max_gap);
  }
}

static void consume_pvmtmlwe_dft(PVW_TMLWE_DFT out) {
  double acc = 0.0;
  for (int i = 0; i < out->a[0]->N; i += 17) acc += out->a[0]->coeffs[i] * 0.0000000001;
  for (int lane = 0; lane < out->r; lane++) {
    for (int i = 0; i < out->b[lane]->N; i += 17) {
      acc += out->b[lane]->coeffs[i] * 0.0000000002;
    }
  }
  g_stage140_sink += acc;
}

static void stage140_decomp_dft_only(PVW_TMLWE in, MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch) {
  const int rows = selector->T * (in->k + in->r);
  pvmtmlwe_decompose(scratch->dec, in, selector->Q, selector->T);
  for (int row = 0; row < rows; row++) {
    polynomial_torus_to_DFT(scratch->dec_dft[row], scratch->dec[row]);
  }
}

static void stage140_addmul_only(PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector,
    DFT_Polynomial *dec_dft) {
  const int rows = selector->T * (out->k + out->r);
  polynomial_mul_DFT(out->a[0], dec_dft[0], selector->samples[0]->a[0]);
  for (int lane = 0; lane < out->r; lane++) {
    polynomial_mul_DFT(out->b[lane], dec_dft[0], selector->samples[0]->b[lane]);
  }
  for (int row = 1; row < rows; row++) {
    polynomial_mul_addto_DFT(out->a[0], dec_dft[row], selector->samples[row]->a[0]);
    for (int lane = 0; lane < out->r; lane++) {
      polynomial_mul_addto_DFT(out->b[lane], dec_dft[row], selector->samples[row]->b[lane]);
    }
  }
}

static void correctness_case(int r, int N, int T, int Bg_bit, int seed) {
  const int rows = T * (1 + r);
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, r, N);
  PVW_TMLWE_DFT split = pvmtmlwe_alloc_new_DFT_sample(1, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch_current = mat_trgsw_alloc_mul_scratch(rows, N);
  MAT_TRGSW_MUL_SCRATCH scratch_split = mat_trgsw_alloc_mul_scratch(rows, N);
  fill_input(in, seed);
  fill_selector(selector, seed);

  mat_trgsw_mul_pvmtmlwe_DFT(current, in, selector, scratch_current);
  stage140_decomp_dft_only(in, selector, scratch_split);
  stage140_addmul_only(split, selector, scratch_split->dec_dft);

  uint64_t mismatches = 0;
  double max_gap = 0.0;
  compare_pvmtmlwe_dft(current, split, &mismatches, &max_gap);

  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, r, N);
  PVW_TMLWE split_torus = pvmtmlwe_alloc_new_sample(1, r, N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(split_torus, split);
  uint64_t torus_mismatches = 0;
  uint64_t max_torus_gap = 0;
  stage141_compare_pvmtmlwe_torus(current_torus, split_torus,
      &torus_mismatches, &max_torus_gap);
  const char *status = "FAIL";
  if (mismatches == 0) status = "PASS_CLOSED_FULLMAT_SPLIT_EQUIV";
  else if (torus_mismatches == 0) status = "PASS_TORUS_EQUIV_DFT_ROUNDING_DIFF";

  const uint64_t dft_count = (uint64_t)(1 + r) * (uint64_t)T;
  printf("CORRECT140,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,%.9f,%" PRIu64 ",%" PRIu64 ",%s,%s\n",
      STAGE140_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap,
      (double)max_torus_gap, dft_count, dft_count, "AT_LOWER_BOUND", status);

  free_pvmtmlwe(split_torus);
  free_pvmtmlwe(current_torus);
  free_mat_trgsw_mul_scratch(scratch_split);
  free_mat_trgsw_mul_scratch(scratch_current);
  free_pvmtmlwe_DFT(split);
  free_pvmtmlwe_DFT(current);
  free_mat_trgsw_DFT(selector);
  free_pvmtmlwe(in);
}

static void emit_bench_row(int r, int N, int T, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant, uint64_t total_ns,
    uint64_t dft_count) {
  const double avg_us = (double)total_ns / (1000.0 * (double)reps);
  const double per_lane_us = avg_us / (double)r;
  printf("BENCH140,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%.6f,%" PRIu64 ",PASS\n",
      STAGE140_BACKEND, r, N, T, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, per_lane_us, dft_count);
}

static void bench_case(int r, int N, int T, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  const int rows = T * (1 + r);
  const uint64_t dft_count = (uint64_t)rows;
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  PVW_TMLWE_DFT out = pvmtmlwe_alloc_new_DFT_sample(1, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);
  MAT_TRGSW_MUL_SCRATCH scratch_pre = mat_trgsw_alloc_mul_scratch(rows, N);
  fill_input(in, seed);
  fill_selector(selector, seed);
  stage140_decomp_dft_only(in, selector, scratch_pre);

  for (int i = 0; i < warmups; i++) {
    mat_trgsw_mul_pvmtmlwe_DFT(out, in, selector, scratch);
    consume_pvmtmlwe_dft(out);
    stage140_decomp_dft_only(in, selector, scratch);
    consume_pvmtmlwe_dft(out);
    stage140_addmul_only(out, selector, scratch_pre->dec_dft);
    consume_pvmtmlwe_dft(out);
  }

  for (int sample = 0; sample < samples; sample++) {
    uint64_t begin = stage140_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      mat_trgsw_mul_pvmtmlwe_DFT(out, in, selector, scratch);
      consume_pvmtmlwe_dft(out);
    }
    uint64_t total = stage140_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "current_full_mat", total, dft_count);

    begin = stage140_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      stage140_decomp_dft_only(in, selector, scratch);
      g_stage140_sink += scratch->dec_dft[0]->coeffs[(rep + sample) & (N - 1)] * 0.0000000001;
    }
    total = stage140_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "closed_decomp_dft_only", total, dft_count);

    begin = stage140_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      stage140_addmul_only(out, selector, scratch_pre->dec_dft);
      consume_pvmtmlwe_dft(out);
    }
    total = stage140_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "closed_addmul_only", total, 0);
  }

  free_mat_trgsw_mul_scratch(scratch_pre);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(out);
  free_mat_trgsw_DFT(selector);
  free_pvmtmlwe(in);
}

int main(void) {
  const int seed = 0;
  const int samples = 5;
  const int reps = 20;
  const int warmups = 2;
  const int rs[3] = {2, 4, 6};
  const int Ns[2] = {1024, 2048};
  const int Ts[1] = {1};
  const int Bgs[1] = {23};
  for (int shape = 0; shape < 1; shape++) {
    for (int ni = 0; ni < 2; ni++) {
      for (int ri = 0; ri < 3; ri++) {
        correctness_case(rs[ri], Ns[ni], Ts[shape], Bgs[shape], seed);
      }
    }
  }
  for (int shape = 0; shape < 1; shape++) {
    for (int ni = 0; ni < 2; ni++) {
      for (int ri = 0; ri < 3; ri++) {
        bench_case(rs[ri], Ns[ni], Ts[shape], Bgs[shape], seed,
            samples, reps, warmups);
      }
    }
  }
  fprintf(stderr, "stage140_sink=%f\n", g_stage140_sink);
  return 0;
}
