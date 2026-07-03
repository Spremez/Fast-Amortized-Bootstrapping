#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef STAGE127_BACKEND
#define STAGE127_BACKEND "unknown"
#endif

typedef struct _CompactSelector {
  TorusPolynomial *shared_a;
  TorusPolynomial *shared_b;
  TorusPolynomial *body_a;
  TorusPolynomial *body_b;
  DFT_Polynomial *shared_a_dft;
  DFT_Polynomial *shared_b_dft;
  DFT_Polynomial *body_a_dft;
  DFT_Polynomial *body_b_dft;
  int T;
  int r;
  int N;
} CompactSelector;

typedef struct _CompactEpScratch {
  TorusPolynomial dec_shared;
  TorusPolynomial dec_body;
  DFT_Polynomial dec_shared_dft;
  DFT_Polynomial dec_body_dft;
} CompactEpScratch;

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
    out->coeffs[i] = (Torus)mix64(11000 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static void fill_secret(TorusPolynomial out, int lane, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)(mix64(11100 + (uint64_t)seed,
        (uint64_t)lane, 0, (uint64_t)i) & 1ULL);
  }
}

static void fill_small_mask(TorusPolynomial out, int lane, int t, int kind,
    int seed) {
  for (int i = 0; i < out->N; i++) {
    const int64_t v = (int64_t)(mix64(11200 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)(10 * t + kind), (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(v);
  }
}

static void fill_noise(TorusPolynomial out, int lane, int t, int kind,
    int seed, int noise_bound) {
  for (int i = 0; i < out->N; i++) {
    const int64_t span = 2 * noise_bound + 1;
    const int64_t v = (int64_t)(mix64(11300 + (uint64_t)seed,
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

static CompactSelector compact_selector_alloc(int T, int r, int N) {
  const int rows = T * r;
  CompactSelector sel;
  sel.shared_a = new_poly_array(rows, N);
  sel.shared_b = new_poly_array(rows, N);
  sel.body_a = new_poly_array(rows, N);
  sel.body_b = new_poly_array(rows, N);
  sel.shared_a_dft = new_dft_array(rows, N);
  sel.shared_b_dft = new_dft_array(rows, N);
  sel.body_a_dft = new_dft_array(rows, N);
  sel.body_b_dft = new_dft_array(rows, N);
  sel.T = T;
  sel.r = r;
  sel.N = N;
  return sel;
}

static void compact_selector_free(CompactSelector *sel) {
  const int rows = sel->T * sel->r;
  free_poly_array_local(sel->shared_a, rows);
  free_poly_array_local(sel->shared_b, rows);
  free_poly_array_local(sel->body_a, rows);
  free_poly_array_local(sel->body_b, rows);
  free_dft_array_local(sel->shared_a_dft, rows);
  free_dft_array_local(sel->shared_b_dft, rows);
  free_dft_array_local(sel->body_a_dft, rows);
  free_dft_array_local(sel->body_b_dft, rows);
}

static CompactEpScratch compact_ep_scratch_alloc(int N) {
  CompactEpScratch s;
  s.dec_shared = polynomial_new_torus_polynomial(N);
  s.dec_body = polynomial_new_torus_polynomial(N);
  s.dec_shared_dft = polynomial_new_DFT_polynomial(N);
  s.dec_body_dft = polynomial_new_DFT_polynomial(N);
  return s;
}

static void compact_ep_scratch_free(CompactEpScratch *s) {
  free_polynomial(s->dec_shared);
  free_polynomial(s->dec_body);
  free_DFT_polynomial(s->dec_shared_dft);
  free_DFT_polynomial(s->dec_body_dft);
}

static void selector_to_dft(CompactSelector *sel) {
  const int rows = sel->T * sel->r;
  for (int i = 0; i < rows; i++) {
    polynomial_torus_to_DFT(sel->shared_a_dft[i], sel->shared_a[i]);
    polynomial_torus_to_DFT(sel->shared_b_dft[i], sel->shared_b[i]);
    polynomial_torus_to_DFT(sel->body_a_dft[i], sel->body_a[i]);
    polynomial_torus_to_DFT(sel->body_b_dft[i], sel->body_b[i]);
  }
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

static void compact_ep_reference_coeff(TorusPolynomial out_a,
    TorusPolynomial out_b, TorusPolynomial source_shared,
    TorusPolynomial source_body, CompactSelector *sel, int lane, int Bg_bit,
    CompactEpScratch *scratch) {
  zero_poly(out_a);
  zero_poly(out_b);
  for (int t = 0; t < sel->T; t++) {
    const int idx = t * sel->r + lane;
    polynomial_decompose_i(scratch->dec_shared, source_shared, Bg_bit, sel->T, t);
    polynomial_decompose_i(scratch->dec_body, source_body, Bg_bit, sel->T, t);
    polynomial_naive_mul_addto_torus(out_a, scratch->dec_shared, sel->shared_a[idx]);
    polynomial_naive_mul_addto_torus(out_b, scratch->dec_shared, sel->shared_b[idx]);
    polynomial_naive_mul_addto_torus(out_a, scratch->dec_body, sel->body_a[idx]);
    polynomial_naive_mul_addto_torus(out_b, scratch->dec_body, sel->body_b[idx]);
  }
}

static void compact_ep_kernel_dft(DFT_Polynomial out_a, DFT_Polynomial out_b,
    TorusPolynomial source_shared, TorusPolynomial source_body,
    CompactSelector *sel, int lane, int Bg_bit, CompactEpScratch *scratch) {
  zero_dft(out_a);
  zero_dft(out_b);
  for (int t = 0; t < sel->T; t++) {
    const int idx = t * sel->r + lane;
    polynomial_decompose_i(scratch->dec_shared, source_shared, Bg_bit, sel->T, t);
    polynomial_decompose_i(scratch->dec_body, source_body, Bg_bit, sel->T, t);
    polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
    polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
    polynomial_mul_addto_DFT(out_a, scratch->dec_shared_dft, sel->shared_a_dft[idx]);
    polynomial_mul_addto_DFT(out_b, scratch->dec_shared_dft, sel->shared_b_dft[idx]);
    polynomial_mul_addto_DFT(out_a, scratch->dec_body_dft, sel->body_a_dft[idx]);
    polynomial_mul_addto_DFT(out_b, scratch->dec_body_dft, sel->body_b_dft[idx]);
  }
}

static void compact_ep_body_only_dft(DFT_Polynomial out_a, DFT_Polynomial out_b,
    TorusPolynomial source_body, CompactSelector *sel, int lane, int Bg_bit,
    CompactEpScratch *scratch) {
  zero_dft(out_a);
  zero_dft(out_b);
  for (int t = 0; t < sel->T; t++) {
    const int idx = t * sel->r + lane;
    polynomial_decompose_i(scratch->dec_body, source_body, Bg_bit, sel->T, t);
    polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
    polynomial_mul_addto_DFT(out_a, scratch->dec_body_dft, sel->body_a_dft[idx]);
    polynomial_mul_addto_DFT(out_b, scratch->dec_body_dft, sel->body_b_dft[idx]);
  }
}

static void run_case(int r, int N, int T, int k, int Bg_bit, int seed) {
  const uint64_t tol = 131072;
  const int noise_coeff_bound = 1;
  const int rows = T * r;
  const int exp = (seed * 17 + r + 9) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *shared_noise = new_poly_array(rows, N);
  TorusPolynomial *body_noise = new_poly_array(rows, N);
  CompactSelector sel = compact_selector_alloc(T, r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);

  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_b_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_b_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial dft_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noisy = polynomial_new_torus_polynomial(N);
  TorusPolynomial observed_noise = polynomial_new_torus_polynomial(N);
  DFT_Polynomial dft_a = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial dft_b = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial neg_a = polynomial_new_DFT_polynomial(N);
  DFT_Polynomial neg_b = polynomial_new_DFT_polynomial(N);

  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }

  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      fill_noise(shared_noise[idx], q, t, 0, seed, noise_coeff_bound);
      fill_noise(body_noise[idx], q, t, 1, seed, noise_coeff_bound);
      encrypt_row(sel.shared_a[idx], sel.shared_b[idx], secret[q], gadget,
          shared_noise[idx], q, t, 0, seed);
      encrypt_row(sel.body_a[idx], sel.body_b[idx], secret[q], gadget,
          body_noise[idx], q, t, 1, seed);
    }
  }
  selector_to_dft(&sel);

  uint64_t component_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t noise_model_mismatches = 0;
  uint64_t negative_failures = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_phase_gap = 0;
  uint64_t dummy_gap = 0;

  for (int q = 0; q < r; q++) {
    compact_ep_reference_coeff(coeff_a, coeff_b, source_shared[q],
        source_body[q], &sel, q, Bg_bit, &scratch);
    compact_ep_kernel_dft(dft_a, dft_b, source_shared[q], source_body[q],
        &sel, q, Bg_bit, &scratch);
    polynomial_DFT_to_torus(dft_a_torus, dft_a);
    polynomial_DFT_to_torus(dft_b_torus, dft_b);
    compare_poly(coeff_a, dft_a_torus, tol, &component_mismatches,
        &max_component_gap);
    compare_poly(coeff_b, dft_b_torus, tol, &component_mismatches,
        &max_component_gap);

    zero_poly(expected_clean);
    zero_poly(expected_noise);
    for (int t = 0; t < T; t++) {
      const int idx = t * r + q;
      make_gadget(gadget, t, Bg_bit, exp, monomial);
      polynomial_decompose_i(scratch.dec_shared, source_shared[q], Bg_bit, T, t);
      polynomial_decompose_i(scratch.dec_body, source_body[q], Bg_bit, T, t);
      polynomial_naive_mul_addto_torus(expected_clean, scratch.dec_shared, gadget);
      polynomial_naive_mul_addto_torus(expected_clean, scratch.dec_body, gadget);
      polynomial_naive_mul_addto_torus(expected_noise, scratch.dec_shared, shared_noise[idx]);
      polynomial_naive_mul_addto_torus(expected_noise, scratch.dec_body, body_noise[idx]);
    }
    for (int i = 0; i < N; i++) {
      expected_noisy->coeffs[i] = expected_clean->coeffs[i] + expected_noise->coeffs[i];
    }

    phase(coeff_phase, coeff_a, coeff_b, secret[q]);
    phase(dft_phase, dft_a_torus, dft_b_torus, secret[q]);
    compare_poly(dft_phase, expected_noisy, tol, &phase_mismatches,
        &max_phase_gap);

    for (int i = 0; i < N; i++) {
      observed_noise->coeffs[i] = coeff_phase->coeffs[i] - expected_clean->coeffs[i];
    }
    compare_poly(observed_noise, expected_noise, 0, &noise_model_mismatches,
        &dummy_gap);

    compact_ep_body_only_dft(neg_a, neg_b, source_body[q], &sel, q, Bg_bit,
        &scratch);
    polynomial_DFT_to_torus(neg_a_torus, neg_a);
    polynomial_DFT_to_torus(neg_b_torus, neg_b);
    phase(neg_phase, neg_a_torus, neg_b_torus, secret[q]);
    compare_poly(neg_phase, expected_noisy, 0, &negative_failures, &dummy_gap);
  }

  const uint64_t dense_dft_terms = (uint64_t)T * (uint64_t)(k + r) * (uint64_t)(k + r);
  const uint64_t compact_dft_terms = 4ULL * (uint64_t)T * (uint64_t)r;
  const uint64_t dense_dec_terms = (uint64_t)T * (uint64_t)(k + r);
  const uint64_t compact_dec_terms = 2ULL * (uint64_t)T * (uint64_t)r;
  const uint64_t dense_total_terms = dense_dft_terms + dense_dec_terms;
  const uint64_t compact_total_terms = compact_dft_terms + compact_dec_terms;
  const double dft_ratio = (double)dense_dft_terms / (double)compact_dft_terms;
  const double total_ratio = (double)dense_total_terms / (double)compact_total_terms;
  const int ok = component_mismatches == 0 && phase_mismatches == 0
      && noise_model_mismatches == 0 && negative_failures > 0
      && dft_ratio > 1.0 && total_ratio >= 1.0;

  printf("KERNEL,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64
         ",%.6f,%s\n",
      STAGE127_BACKEND, r, N, T, k, Bg_bit, seed, component_mismatches,
      phase_mismatches, noise_model_mismatches, negative_failures,
      max_component_gap, max_phase_gap, tol, dense_dft_terms,
      compact_dft_terms, dft_ratio, dense_total_terms, compact_total_terms,
      total_ratio, ok ? "PASS_ISOLATED_COMPACT_EP_KERNEL" : "FAIL");

  free_poly_array_local(secret, r);
  free_poly_array_local(source_shared, r);
  free_poly_array_local(source_body, r);
  free_poly_array_local(shared_noise, rows);
  free_poly_array_local(body_noise, rows);
  compact_selector_free(&sel);
  compact_ep_scratch_free(&scratch);
  free_polynomial(gadget);
  free_polynomial(coeff_a);
  free_polynomial(coeff_b);
  free_polynomial(dft_a_torus);
  free_polynomial(dft_b_torus);
  free_polynomial(neg_a_torus);
  free_polynomial(neg_b_torus);
  free_polynomial(coeff_phase);
  free_polynomial(dft_phase);
  free_polynomial(neg_phase);
  free_polynomial(expected_clean);
  free_polynomial(expected_noise);
  free_polynomial(expected_noisy);
  free_polynomial(observed_noise);
  free_DFT_polynomial(dft_a);
  free_DFT_polynomial(dft_b);
  free_DFT_polynomial(neg_a);
  free_DFT_polynomial(neg_b);
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
