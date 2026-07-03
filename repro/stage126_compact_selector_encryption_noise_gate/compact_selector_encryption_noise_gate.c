#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef STAGE126_BACKEND
#define STAGE126_BACKEND "unknown"
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

static Torus signed_torus(int64_t v) {
  return (Torus)v;
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

static void fill_source(TorusPolynomial out, int lane, int kind, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(9000 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static void fill_secret(TorusPolynomial out, int lane, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)(mix64(9100 + (uint64_t)seed,
        (uint64_t)lane, 0, (uint64_t)i) & 1ULL);
  }
}

static void fill_small_mask(TorusPolynomial out, int lane, int t, int kind,
    int seed) {
  for (int i = 0; i < out->N; i++) {
    const int64_t v = (int64_t)(mix64(9200 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)(10 * t + kind), (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(v);
  }
}

static void fill_noise(TorusPolynomial out, int lane, int t, int kind,
    int seed, int noise_bound) {
  for (int i = 0; i < out->N; i++) {
    const int64_t span = 2 * noise_bound + 1;
    const int64_t v = (int64_t)(mix64(9300 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)(10 * t + kind), (uint64_t)i)
        % (uint64_t)span) - noise_bound;
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

static void dft_mul_add_torus(DFT_Polynomial out, TorusPolynomial digit,
    DFT_Polynomial row) {
  DFT_Polynomial dd = polynomial_new_DFT_polynomial(digit->N);
  polynomial_torus_to_DFT(dd, digit);
  polynomial_mul_addto_DFT(out, dd, row);
  free_DFT_polynomial(dd);
}

static void compare_poly(TorusPolynomial a, TorusPolynomial b, uint64_t tol,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static uint64_t max_abs_poly(TorusPolynomial p) {
  uint64_t out = 0;
  for (int i = 0; i < p->N; i++) {
    const uint64_t gap = abs_gap(p->coeffs[i], 0);
    if (gap > out) out = gap;
  }
  return out;
}

static void run_case(int r, int N, int T, int k, int Bg_bit, int seed) {
  const uint64_t tol = 131072;
  const int noise_coeff_bound = 1;
  const uint64_t half_bg = 1ULL << (Bg_bit - 1);
  const uint64_t noise_bound =
      2ULL * (uint64_t)T * (uint64_t)N * half_bg * (uint64_t)noise_coeff_bound;
  const int rows = T * r;
  const int exp = (seed * 13 + r + 5) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial *source_mask = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *shared_a = new_poly_array(rows, N);
  TorusPolynomial *shared_b = new_poly_array(rows, N);
  TorusPolynomial *body_a = new_poly_array(rows, N);
  TorusPolynomial *body_b = new_poly_array(rows, N);
  TorusPolynomial *shared_noise = new_poly_array(rows, N);
  TorusPolynomial *body_noise = new_poly_array(rows, N);
  DFT_Polynomial *shared_a_dft = new_dft_array(rows, N);
  DFT_Polynomial *shared_b_dft = new_dft_array(rows, N);
  DFT_Polynomial *body_a_dft = new_dft_array(rows, N);
  DFT_Polynomial *body_b_dft = new_dft_array(rows, N);

  TorusPolynomial dec_mask = polynomial_new_torus_polynomial(N);
  TorusPolynomial dec_body = polynomial_new_torus_polynomial(N);
  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noisy = polynomial_new_torus_polynomial(N);
  TorusPolynomial observed_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_a_dft_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_b_dft_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial phase_coeff = polynomial_new_torus_polynomial(N);
  TorusPolynomial phase_dft = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial phase_neg = polynomial_new_torus_polynomial(N);
  DFT_Polynomial out_a_dft = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial out_b_dft = polynomial_new_DFT_polynomial(N);

  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(source_mask[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }

  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      fill_noise(shared_noise[idx], q, t, 0, seed, noise_coeff_bound);
      fill_noise(body_noise[idx], q, t, 1, seed, noise_coeff_bound);
      encrypt_row(shared_a[idx], shared_b[idx], secret[q], gadget,
          shared_noise[idx], q, t, 0, seed);
      encrypt_row(body_a[idx], body_b[idx], secret[q], gadget,
          body_noise[idx], q, t, 1, seed);
      polynomial_torus_to_DFT(shared_a_dft[idx], shared_a[idx]);
      polynomial_torus_to_DFT(shared_b_dft[idx], shared_b[idx]);
      polynomial_torus_to_DFT(body_a_dft[idx], body_a[idx]);
      polynomial_torus_to_DFT(body_b_dft[idx], body_b[idx]);
    }
  }

  uint64_t coeff_mismatches = 0;
  uint64_t dft_mismatches = 0;
  uint64_t noise_model_mismatches = 0;
  uint64_t noise_bound_violations = 0;
  uint64_t negative_failures = 0;
  uint64_t max_dft_gap = 0;
  uint64_t max_noise_abs = 0;

  for (int q = 0; q < r; q++) {
    zero_poly(out_a);
    zero_poly(out_b);
    zero_dft(out_a_dft);
    zero_dft(out_b_dft);
    zero_poly(expected_clean);
    zero_poly(expected_noise);
    zero_poly(neg_a);
    zero_poly(neg_b);
    for (int t = 0; t < T; t++) {
      make_gadget(gadget, t, Bg_bit, exp, monomial);
      const int idx = t * r + q;
      polynomial_decompose_i(dec_mask, source_mask[q], Bg_bit, T, t);
      polynomial_decompose_i(dec_body, source_body[q], Bg_bit, T, t);

      polynomial_naive_mul_addto_torus(out_a, dec_mask, shared_a[idx]);
      polynomial_naive_mul_addto_torus(out_b, dec_mask, shared_b[idx]);
      polynomial_naive_mul_addto_torus(out_a, dec_body, body_a[idx]);
      polynomial_naive_mul_addto_torus(out_b, dec_body, body_b[idx]);

      dft_mul_add_torus(out_a_dft, dec_mask, shared_a_dft[idx]);
      dft_mul_add_torus(out_b_dft, dec_mask, shared_b_dft[idx]);
      dft_mul_add_torus(out_a_dft, dec_body, body_a_dft[idx]);
      dft_mul_add_torus(out_b_dft, dec_body, body_b_dft[idx]);

      polynomial_naive_mul_addto_torus(expected_clean, dec_mask, gadget);
      polynomial_naive_mul_addto_torus(expected_clean, dec_body, gadget);
      polynomial_naive_mul_addto_torus(expected_noise, dec_mask, shared_noise[idx]);
      polynomial_naive_mul_addto_torus(expected_noise, dec_body, body_noise[idx]);

      polynomial_naive_mul_addto_torus(neg_a, dec_body, body_a[idx]);
      polynomial_naive_mul_addto_torus(neg_b, dec_body, body_b[idx]);
    }

    for (int i = 0; i < N; i++) {
      expected_noisy->coeffs[i] = expected_clean->coeffs[i] + expected_noise->coeffs[i];
    }

    phase(phase_coeff, out_a, out_b, secret[q]);
    polynomial_DFT_to_torus(out_a_dft_torus, out_a_dft);
    polynomial_DFT_to_torus(out_b_dft_torus, out_b_dft);
    phase(phase_dft, out_a_dft_torus, out_b_dft_torus, secret[q]);
    phase(phase_neg, neg_a, neg_b, secret[q]);

    uint64_t dummy_gap = 0;
    compare_poly(phase_coeff, expected_noisy, 0, &coeff_mismatches, &dummy_gap);
    compare_poly(phase_dft, expected_noisy, tol, &dft_mismatches, &max_dft_gap);

    for (int i = 0; i < N; i++) {
      observed_noise->coeffs[i] = phase_coeff->coeffs[i] - expected_clean->coeffs[i];
    }
    compare_poly(observed_noise, expected_noise, 0, &noise_model_mismatches, &dummy_gap);
    const uint64_t lane_noise = max_abs_poly(expected_noise);
    if (lane_noise > max_noise_abs) max_noise_abs = lane_noise;
    if (lane_noise > noise_bound) noise_bound_violations++;
    compare_poly(phase_neg, expected_noisy, 0, &negative_failures, &dummy_gap);
  }

  const int ok = coeff_mismatches == 0 && dft_mismatches == 0
      && noise_model_mismatches == 0 && noise_bound_violations == 0
      && negative_failures > 0;
  printf("NOISE,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE126_BACKEND, r, N, T, k, Bg_bit, seed, coeff_mismatches,
      dft_mismatches, noise_model_mismatches, noise_bound_violations,
      negative_failures, max_dft_gap, max_noise_abs, noise_bound, tol,
      ok ? "PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE" : "FAIL");

  const uint64_t current_noise_terms = (uint64_t)T * (uint64_t)(k + r);
  const uint64_t compact_noise_terms = 2ULL * (uint64_t)T;
  const double noise_ratio = (double)current_noise_terms / (double)compact_noise_terms;
  const uint64_t current_sel = (uint64_t)T * (uint64_t)(k + r) * (uint64_t)(k + r);
  const uint64_t compact_sel = 2ULL * (uint64_t)T * (uint64_t)r * (uint64_t)(k + 1);
  const double selector_ratio = (double)current_sel / (double)compact_sel;
  const int layout_ok = noise_ratio > 1.0 && selector_ratio > 1.0;
  printf("LAYOUT,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64
         ",%" PRIu64 ",%.6f,%s\n",
      r, N, T, k, current_noise_terms, compact_noise_terms, noise_ratio,
      current_sel, compact_sel, selector_ratio,
      layout_ok ? "PASS_NOISE_LAYOUT_MODEL" : "FAIL");

  free_poly_array_local(secret, r);
  free_poly_array_local(source_mask, r);
  free_poly_array_local(source_body, r);
  free_poly_array_local(shared_a, rows);
  free_poly_array_local(shared_b, rows);
  free_poly_array_local(body_a, rows);
  free_poly_array_local(body_b, rows);
  free_poly_array_local(shared_noise, rows);
  free_poly_array_local(body_noise, rows);
  free_dft_array_local(shared_a_dft, rows);
  free_dft_array_local(shared_b_dft, rows);
  free_dft_array_local(body_a_dft, rows);
  free_dft_array_local(body_b_dft, rows);
  free_polynomial(dec_mask);
  free_polynomial(dec_body);
  free_polynomial(gadget);
  free_polynomial(expected_clean);
  free_polynomial(expected_noise);
  free_polynomial(expected_noisy);
  free_polynomial(observed_noise);
  free_polynomial(out_a);
  free_polynomial(out_b);
  free_polynomial(out_a_dft_torus);
  free_polynomial(out_b_dft_torus);
  free_polynomial(phase_coeff);
  free_polynomial(phase_dft);
  free_polynomial(neg_a);
  free_polynomial(neg_b);
  free_polynomial(phase_neg);
  free_DFT_polynomial(out_a_dft);
  free_DFT_polynomial(out_b_dft);
}

int main(void) {
  const int k = 1;
  const int T = 7;
  const int Bg_bit = 7;
  run_case(2, 512, T, k, Bg_bit, 0);
  run_case(2, 512, T, k, Bg_bit, 1);
  run_case(4, 512, T, k, Bg_bit, 0);
  run_case(4, 512, T, k, Bg_bit, 1);
  run_case(6, 512, T, k, Bg_bit, 0);
  run_case(6, 512, T, k, Bg_bit, 1);
  run_case(2, 1024, T, k, Bg_bit, 0);
  run_case(4, 1024, T, k, Bg_bit, 0);
  run_case(6, 1024, T, k, Bg_bit, 0);
  return 0;
}
