#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef STAGE125_BACKEND
#define STAGE125_BACKEND "unknown"
#endif

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

static uint64_t abs_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static TorusPolynomial *new_poly_array(int count, int N) {
  TorusPolynomial *out =
      (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * count);
  for (int i = 0; i < count; i++) out[i] = polynomial_new_torus_polynomial(N);
  return out;
}

static DFT_Polynomial *new_dft_array(int count, int N) {
  DFT_Polynomial *out =
      (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * count);
  for (int i = 0; i < count; i++) out[i] = polynomial_new_DFT_polynomial(N);
  return out;
}

static void free_poly_array_local(TorusPolynomial *in, int count) {
  for (int i = 0; i < count; i++) free_polynomial(in[i]);
  free(in);
}

static void free_dft_array_local(DFT_Polynomial *in, int count) {
  for (int i = 0; i < count; i++) free_DFT_polynomial(in[i]);
  free(in);
}

static void zero_poly(TorusPolynomial p) {
  memset(p->coeffs, 0, sizeof(Torus) * p->N);
}

static void zero_dft(DFT_Polynomial p) {
  memset(p->coeffs, 0, sizeof(double) * p->N);
}

static void fill_component(TorusPolynomial out, int lane, int kind, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(1000 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static void make_gadget(TorusPolynomial out, int t, int Bg_bit, int exp,
    int64_t m) {
  zero_poly(out);
  const int word_size = (int)(sizeof(Torus) * 8);
  const Torus h = (Torus)1ULL << (word_size - (t + 1) * Bg_bit);
  out->coeffs[exp & (out->N - 1)] = (Torus)(m * (int64_t)h);
}

static void dft_mul_add_torus(DFT_Polynomial out, TorusPolynomial a,
    TorusPolynomial b) {
  DFT_Polynomial da = polynomial_new_DFT_polynomial(a->N);
  DFT_Polynomial db = polynomial_new_DFT_polynomial(a->N);
  polynomial_torus_to_DFT(da, a);
  polynomial_torus_to_DFT(db, b);
  polynomial_mul_addto_DFT(out, da, db);
  free_DFT_polynomial(da);
  free_DFT_polynomial(db);
}

static void compare_poly(TorusPolynomial a, TorusPolynomial b, uint64_t tol,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void run_case(int r, int N, int T, int k, int Bg_bit, int seed) {
  const uint64_t tol = 16384;
  const int lanes = r;
  const int streams = 2 * T * r;
  const int exp = (seed * 11 + r + 3) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *mask = new_poly_array(lanes, N);
  TorusPolynomial *body = new_poly_array(lanes, N);
  TorusPolynomial *dec_mask = new_poly_array(T * r, N);
  TorusPolynomial *dec_body = new_poly_array(T * r, N);
  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);
  TorusPolynomial *ref_a = new_poly_array(lanes, N);
  TorusPolynomial *ref_b = new_poly_array(lanes, N);
  DFT_Polynomial *dft_a = new_dft_array(lanes, N);
  DFT_Polynomial *dft_b = new_dft_array(lanes, N);
  TorusPolynomial *out_a = new_poly_array(lanes, N);
  TorusPolynomial *out_b = new_poly_array(lanes, N);
  TorusPolynomial *neg_a = new_poly_array(lanes, N);
  TorusPolynomial *neg_b = new_poly_array(lanes, N);

  for (int q = 0; q < r; q++) {
    fill_component(mask[q], q, 0, seed);
    fill_component(body[q], q, 1, seed);
    zero_poly(ref_a[q]);
    zero_poly(ref_b[q]);
    zero_dft(dft_a[q]);
    zero_dft(dft_b[q]);
    zero_poly(neg_a[q]);
    zero_poly(neg_b[q]);
  }

  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      polynomial_decompose_i(dec_mask[idx], mask[q], Bg_bit, T, t);
      polynomial_decompose_i(dec_body[idx], body[q], Bg_bit, T, t);
      polynomial_naive_mul_addto_torus(ref_a[q], dec_mask[idx], gadget);
      polynomial_naive_mul_addto_torus(ref_b[q], dec_body[idx], gadget);
      dft_mul_add_torus(dft_a[q], dec_mask[idx], gadget);
      dft_mul_add_torus(dft_b[q], dec_body[idx], gadget);
      polynomial_naive_mul_addto_torus(neg_b[q], dec_body[idx], gadget);
    }
  }

  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  uint64_t negative_failures = 0;
  for (int q = 0; q < r; q++) {
    polynomial_DFT_to_torus(out_a[q], dft_a[q]);
    polynomial_DFT_to_torus(out_b[q], dft_b[q]);
    compare_poly(ref_a[q], out_a[q], tol, &mismatches, &max_gap);
    compare_poly(ref_b[q], out_b[q], tol, &mismatches, &max_gap);
    uint64_t neg_gap = 0;
    compare_poly(ref_a[q], neg_a[q], 0, &negative_failures, &neg_gap);
    compare_poly(ref_b[q], neg_b[q], 0, &negative_failures, &neg_gap);
  }

  const int ok = mismatches == 0 && negative_failures > 0;
  printf("GADGET,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE125_BACKEND, r, N, T, k, Bg_bit, seed, mismatches,
      negative_failures, max_gap, tol,
      ok ? "PASS_COMPACT_SELECTOR_GADGET" : "FAIL");

  const uint64_t current_sel = (uint64_t)T * (uint64_t)(k + r) * (uint64_t)(k + r);
  const uint64_t compact_sel = 2ULL * (uint64_t)T * (uint64_t)r * (uint64_t)(k + 1);
  const uint64_t current_dec = (uint64_t)T * (uint64_t)(k + r);
  const uint64_t compact_dec = 2ULL * (uint64_t)T * (uint64_t)r;
  const uint64_t current_total = current_sel + current_dec;
  const uint64_t compact_total = compact_sel + compact_dec;
  const double selector_ratio = (double)current_sel / (double)compact_sel;
  const double dec_overhead = (double)compact_dec / (double)current_dec;
  const double total_ratio = (double)current_total / (double)compact_total;
  const int layout_ok = selector_ratio > 1.0 && total_ratio >= 1.0;
  printf("LAYOUT,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64
         ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64 ",%.6f,%s\n",
      r, N, T, k, current_sel, compact_sel, selector_ratio, current_dec,
      compact_dec, dec_overhead, current_total, compact_total, total_ratio,
      layout_ok ? "PASS_LAYOUT_MODEL" : "FAIL");

  free_poly_array_local(mask, lanes);
  free_poly_array_local(body, lanes);
  free_poly_array_local(dec_mask, T * r);
  free_poly_array_local(dec_body, T * r);
  free_polynomial(gadget);
  free_poly_array_local(ref_a, lanes);
  free_poly_array_local(ref_b, lanes);
  free_dft_array_local(dft_a, lanes);
  free_dft_array_local(dft_b, lanes);
  free_poly_array_local(out_a, lanes);
  free_poly_array_local(out_b, lanes);
  free_poly_array_local(neg_a, lanes);
  free_poly_array_local(neg_b, lanes);
  (void)streams;
}

int main(void) {
  const int k = 1;
  const int T = 7;
  const int Bg_bit = 7;
  run_case(2, 1024, T, k, Bg_bit, 0);
  run_case(2, 1024, T, k, Bg_bit, 1);
  run_case(4, 1024, T, k, Bg_bit, 0);
  run_case(4, 1024, T, k, Bg_bit, 1);
  run_case(6, 1024, T, k, Bg_bit, 0);
  run_case(6, 1024, T, k, Bg_bit, 1);
  run_case(2, 2048, T, k, Bg_bit, 0);
  run_case(4, 2048, T, k, Bg_bit, 0);
  run_case(6, 2048, T, k, Bg_bit, 0);
  return 0;
}
