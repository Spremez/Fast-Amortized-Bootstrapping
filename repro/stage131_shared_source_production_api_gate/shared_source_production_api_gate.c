#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef STAGE131_BACKEND
#define STAGE131_BACKEND "unknown"
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

static Torus signed_torus(int64_t v) { return (Torus)v; }

static TorusPolynomial *new_poly_array(int count, int N) {
  TorusPolynomial *out =
      (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * count);
  for (int i = 0; i < count; i++) out[i] = polynomial_new_torus_polynomial(N);
  return out;
}

static void free_poly_array_local(TorusPolynomial *in, int count) {
  for (int i = 0; i < count; i++) free_polynomial(in[i]);
  free(in);
}

static void zero_poly(TorusPolynomial p) {
  memset(p->coeffs, 0, sizeof(Torus) * p->N);
}

static void fill_source(TorusPolynomial out, int lane, int kind, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(13100 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static void fill_secret(TorusPolynomial out, int lane, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)(mix64(13200 + (uint64_t)seed,
        (uint64_t)lane, 0, (uint64_t)i) & 1ULL);
  }
}

static void fill_small_mask(TorusPolynomial out, int lane, int t, int kind,
    int seed) {
  for (int i = 0; i < out->N; i++) {
    const int64_t v = (int64_t)(mix64(13300 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)(10 * t + kind), (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(v);
  }
}

static void fill_noise(TorusPolynomial out, int lane, int t, int kind,
    int seed) {
  for (int i = 0; i < out->N; i++) {
    const int64_t v = (int64_t)(mix64(13400 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)(10 * t + kind), (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(v);
  }
}

static void make_gadget(TorusPolynomial out, int t, int Bg_bit, int exp,
    int64_t m) {
  zero_poly(out);
  const int word_size = (int)(sizeof(Torus) * 8);
  const Torus h = (Torus)1ULL << (word_size - (t + 1) * Bg_bit);
  out->coeffs[exp & (out->N - 1)] = (Torus)(m * (int64_t)h);
}

static void encrypt_row(TorusPolynomial a, TorusPolynomial b,
    TorusPolynomial secret, TorusPolynomial message, TorusPolynomial noise,
    int lane, int t, int kind, int seed) {
  fill_small_mask(a, lane, t, kind, seed);
  zero_poly(b);
  polynomial_naive_mul_addto_torus(b, a, secret);
  polynomial_addto_torus_polynomial(b, message);
  polynomial_addto_torus_polynomial(b, noise);
}

static void phase(TorusPolynomial out, TorusPolynomial a, TorusPolynomial b,
    TorusPolynomial secret) {
  TorusPolynomial prod = polynomial_new_torus_polynomial(secret->N);
  zero_poly(prod);
  polynomial_naive_mul_addto_torus(prod, a, secret);
  for (int i = 0; i < secret->N; i++) out->coeffs[i] = b->coeffs[i] - prod->coeffs[i];
  free_polynomial(prod);
}

static void compare_poly(TorusPolynomial a, TorusPolynomial b, uint64_t tol,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void compact_reference(TorusPolynomial out_a, TorusPolynomial out_b,
    PVW_TMLWE in, TorusPolynomial *shared_a, TorusPolynomial *shared_b,
    TorusPolynomial *body_a, TorusPolynomial *body_b, int T, int r, int lane,
    int Bg_bit, MAT_TRGSW_COMPACT_MUL_SCRATCH scratch) {
  zero_poly(out_a);
  zero_poly(out_b);
  for (int t = 0; t < T; t++) {
    const int idx = t * r + lane;
    polynomial_decompose_i(scratch->dec_shared, in->a[0], Bg_bit, T, t);
    polynomial_decompose_i(scratch->dec_body, in->b[lane], Bg_bit, T, t);
    polynomial_naive_mul_addto_torus(out_a, scratch->dec_shared, shared_a[idx]);
    polynomial_naive_mul_addto_torus(out_b, scratch->dec_shared, shared_b[idx]);
    polynomial_naive_mul_addto_torus(out_a, scratch->dec_body, body_a[idx]);
    polynomial_naive_mul_addto_torus(out_b, scratch->dec_body, body_b[idx]);
  }
}

static void run_case(int r, int N, int T, int k, int Bg_bit, int seed) {
  const uint64_t tol = 131072;
  const int rows = T * r;
  const int exp = (seed * 19 + r + 11) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial *shared_a = new_poly_array(rows, N);
  TorusPolynomial *shared_b = new_poly_array(rows, N);
  TorusPolynomial *body_a = new_poly_array(rows, N);
  TorusPolynomial *body_b = new_poly_array(rows, N);
  TorusPolynomial *shared_noise = new_poly_array(rows, N);
  TorusPolynomial *body_noise = new_poly_array(rows, N);
  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_b_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial api_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noisy = polynomial_new_torus_polynomial(N);
  TorusPolynomial observed_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_b_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_phase = polynomial_new_torus_polynomial(N);

  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE neg_in = pvmtmlwe_alloc_new_sample(k, r, N);
  MAT_TRGSW_COMPACT_DFT sel = mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, k, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT out = mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT neg_out = mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch = mat_trgsw_compact_alloc_mul_scratch(N);

  fill_source(in->a[0], 0, 0, seed);
  zero_poly(neg_in->a[0]);
  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(in->b[q], q, 1, seed);
    polynomial_copy_torus_polynomial(neg_in->b[q], in->b[q]);
  }
  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      fill_noise(shared_noise[idx], q, t, 0, seed);
      fill_noise(body_noise[idx], q, t, 1, seed);
      encrypt_row(shared_a[idx], shared_b[idx], secret[q], gadget,
          shared_noise[idx], q, t, 0, seed);
      encrypt_row(body_a[idx], body_b[idx], secret[q], gadget,
          body_noise[idx], q, t, 1, seed);
      mat_trgsw_compact_set_row_from_torus(sel, t, q, shared_a[idx],
          shared_b[idx], body_a[idx], body_b[idx]);
    }
  }

  uint64_t guard_failures = 0;
  if (mat_trgsw_compact_set_row_from_torus(sel, T, 0, shared_a[0], shared_b[0],
      body_a[0], body_b[0]) == 0) guard_failures++;
  if (mat_trgsw_compact_set_row_from_torus(sel, 0, r, shared_a[0], shared_b[0],
      body_a[0], body_b[0]) == 0) guard_failures++;

  mat_trgsw_compact_mul_pvmtmlwe_DFT(out, in, sel, scratch);
  mat_trgsw_compact_mul_pvmtmlwe_DFT(neg_out, neg_in, sel, scratch);

  uint64_t component_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t noise_model_mismatches = 0;
  uint64_t negative_failures = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_phase_gap = 0;
  uint64_t dummy_gap = 0;

  for (int q = 0; q < r; q++) {
    compact_reference(coeff_a, coeff_b, in, shared_a, shared_b, body_a,
        body_b, T, r, q, Bg_bit, scratch);
    polynomial_DFT_to_torus(out_a_torus, out->a[q]);
    polynomial_DFT_to_torus(out_b_torus, out->b[q]);
    compare_poly(coeff_a, out_a_torus, tol, &component_mismatches,
        &max_component_gap);
    compare_poly(coeff_b, out_b_torus, tol, &component_mismatches,
        &max_component_gap);

    zero_poly(expected_clean);
    zero_poly(expected_noise);
    for (int t = 0; t < T; t++) {
      const int idx = t * r + q;
      make_gadget(gadget, t, Bg_bit, exp, monomial);
      polynomial_decompose_i(scratch->dec_shared, in->a[0], Bg_bit, T, t);
      polynomial_decompose_i(scratch->dec_body, in->b[q], Bg_bit, T, t);
      polynomial_naive_mul_addto_torus(expected_clean, scratch->dec_shared, gadget);
      polynomial_naive_mul_addto_torus(expected_clean, scratch->dec_body, gadget);
      polynomial_naive_mul_addto_torus(expected_noise, scratch->dec_shared, shared_noise[idx]);
      polynomial_naive_mul_addto_torus(expected_noise, scratch->dec_body, body_noise[idx]);
    }
    for (int i = 0; i < N; i++) {
      expected_noisy->coeffs[i] = expected_clean->coeffs[i] + expected_noise->coeffs[i];
    }
    phase(coeff_phase, coeff_a, coeff_b, secret[q]);
    phase(api_phase, out_a_torus, out_b_torus, secret[q]);
    compare_poly(api_phase, expected_noisy, tol, &phase_mismatches,
        &max_phase_gap);
    for (int i = 0; i < N; i++) {
      observed_noise->coeffs[i] = coeff_phase->coeffs[i] - expected_clean->coeffs[i];
    }
    compare_poly(observed_noise, expected_noise, 0, &noise_model_mismatches,
        &dummy_gap);

    polynomial_DFT_to_torus(neg_a_torus, neg_out->a[q]);
    polynomial_DFT_to_torus(neg_b_torus, neg_out->b[q]);
    phase(neg_phase, neg_a_torus, neg_b_torus, secret[q]);
    compare_poly(neg_phase, expected_noisy, 0, &negative_failures, &dummy_gap);
  }

  const int ok = guard_failures == 0 && component_mismatches == 0 &&
      phase_mismatches == 0 && noise_model_mismatches == 0 &&
      negative_failures > 0;
  printf("PRODAPI,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%s\n",
      STAGE131_BACKEND, r, N, T, k, Bg_bit, seed, guard_failures,
      component_mismatches, phase_mismatches, noise_model_mismatches,
      negative_failures, max_component_gap, max_phase_gap, tol,
      ok ? "PASS_SHARED_SOURCE_PRODUCTION_API" : "FAIL");

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(neg_out);
  free_mat_trgsw_compact_output_DFT(out);
  free_mat_trgsw_compact_DFT(sel);
  free_pvmtmlwe(neg_in);
  free_pvmtmlwe(in);
  free_poly_array_local(secret, r);
  free_poly_array_local(shared_a, rows);
  free_poly_array_local(shared_b, rows);
  free_poly_array_local(body_a, rows);
  free_poly_array_local(body_b, rows);
  free_poly_array_local(shared_noise, rows);
  free_poly_array_local(body_noise, rows);
  free_polynomial(gadget);
  free_polynomial(coeff_a);
  free_polynomial(coeff_b);
  free_polynomial(out_a_torus);
  free_polynomial(out_b_torus);
  free_polynomial(coeff_phase);
  free_polynomial(api_phase);
  free_polynomial(expected_clean);
  free_polynomial(expected_noise);
  free_polynomial(expected_noisy);
  free_polynomial(observed_noise);
  free_polynomial(neg_a_torus);
  free_polynomial(neg_b_torus);
  free_polynomial(neg_phase);
}

int main(void) {
  const int k = 1;
  const int T = 7;
  const int Bg_bit = 7;
  run_case(2, 512, T, k, Bg_bit, 0);
  run_case(4, 512, T, k, Bg_bit, 0);
  run_case(6, 512, T, k, Bg_bit, 0);
  run_case(2, 1024, T, k, Bg_bit, 0);
  run_case(4, 1024, T, k, Bg_bit, 0);
  run_case(6, 1024, T, k, Bg_bit, 0);
  return 0;
}
