#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE128_BACKEND
#define STAGE128_BACKEND "unknown"
#endif

typedef struct _CompactEpSelectorDft {
  DFT_Polynomial *shared_a;
  DFT_Polynomial *shared_b;
  DFT_Polynomial *body_a;
  DFT_Polynomial *body_b;
  int T;
  int Bg_bit;
  int k;
  int r;
  int N;
} *CompactEpSelectorDft;

typedef struct _CompactEpOutputDft {
  DFT_Polynomial a;
  DFT_Polynomial b;
  int N;
} *CompactEpOutputDft;

typedef struct _CompactEpScratch {
  TorusPolynomial dec_shared;
  TorusPolynomial dec_body;
  DFT_Polynomial dec_shared_dft;
  DFT_Polynomial dec_body_dft;
  int N;
} *CompactEpScratch;

static uint64_t g_api_alloc_polys = 0;
static uint64_t g_api_free_polys = 0;

static TorusPolynomial api_new_torus_polynomial(int N) {
  g_api_alloc_polys++;
  return polynomial_new_torus_polynomial(N);
}

static DFT_Polynomial api_new_dft_polynomial(int N) {
  g_api_alloc_polys++;
  return polynomial_new_DFT_polynomial(N);
}

static void api_free_torus_polynomial(TorusPolynomial p) {
  g_api_free_polys++;
  free_polynomial(p);
}

static void api_free_dft_polynomial(DFT_Polynomial p) {
  g_api_free_polys++;
  free_DFT_polynomial(p);
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

static void free_poly_array_local(TorusPolynomial *in, int count) {
  for (int i = 0; i < count; i++) free_polynomial(in[i]);
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
    out->coeffs[i] = (Torus)mix64(12000 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static void fill_secret(TorusPolynomial out, int lane, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)(mix64(12100 + (uint64_t)seed,
        (uint64_t)lane, 0, (uint64_t)i) & 1ULL);
  }
}

static void fill_small_mask(TorusPolynomial out, int lane, int t, int kind,
    int seed) {
  for (int i = 0; i < out->N; i++) {
    const int64_t v = (int64_t)(mix64(12200 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)(10 * t + kind), (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(v);
  }
}

static void fill_noise(TorusPolynomial out, int lane, int t, int kind,
    int seed, int noise_bound) {
  for (int i = 0; i < out->N; i++) {
    const int64_t span = 2 * noise_bound + 1;
    const int64_t v = (int64_t)(mix64(12300 + (uint64_t)seed,
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

static CompactEpSelectorDft compact_ep_selector_dft_alloc(int T, int Bg_bit,
    int k, int r, int N) {
  CompactEpSelectorDft sel =
      (CompactEpSelectorDft)safe_malloc(sizeof(*sel));
  const int rows = T * r;
  sel->shared_a = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * rows);
  sel->shared_b = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * rows);
  sel->body_a = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * rows);
  sel->body_b = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * rows);
  for (int i = 0; i < rows; i++) {
    sel->shared_a[i] = api_new_dft_polynomial(N);
    sel->shared_b[i] = api_new_dft_polynomial(N);
    sel->body_a[i] = api_new_dft_polynomial(N);
    sel->body_b[i] = api_new_dft_polynomial(N);
  }
  sel->T = T;
  sel->Bg_bit = Bg_bit;
  sel->k = k;
  sel->r = r;
  sel->N = N;
  return sel;
}

static void compact_ep_selector_dft_free(CompactEpSelectorDft sel) {
  const int rows = sel->T * sel->r;
  for (int i = 0; i < rows; i++) {
    api_free_dft_polynomial(sel->shared_a[i]);
    api_free_dft_polynomial(sel->shared_b[i]);
    api_free_dft_polynomial(sel->body_a[i]);
    api_free_dft_polynomial(sel->body_b[i]);
  }
  free(sel->shared_a);
  free(sel->shared_b);
  free(sel->body_a);
  free(sel->body_b);
  free(sel);
}

static CompactEpOutputDft compact_ep_output_dft_alloc(int N) {
  CompactEpOutputDft out =
      (CompactEpOutputDft)safe_malloc(sizeof(*out));
  out->a = api_new_dft_polynomial(N);
  out->b = api_new_dft_polynomial(N);
  out->N = N;
  return out;
}

static void compact_ep_output_dft_free(CompactEpOutputDft out) {
  api_free_dft_polynomial(out->a);
  api_free_dft_polynomial(out->b);
  free(out);
}

static CompactEpScratch compact_ep_scratch_alloc(int N) {
  CompactEpScratch scratch =
      (CompactEpScratch)safe_malloc(sizeof(*scratch));
  scratch->dec_shared = api_new_torus_polynomial(N);
  scratch->dec_body = api_new_torus_polynomial(N);
  scratch->dec_shared_dft = api_new_dft_polynomial(N);
  scratch->dec_body_dft = api_new_dft_polynomial(N);
  scratch->N = N;
  return scratch;
}

static void compact_ep_scratch_free(CompactEpScratch scratch) {
  api_free_torus_polynomial(scratch->dec_shared);
  api_free_torus_polynomial(scratch->dec_body);
  api_free_dft_polynomial(scratch->dec_shared_dft);
  api_free_dft_polynomial(scratch->dec_body_dft);
  free(scratch);
}

static int compact_ep_selector_set_row_from_torus(CompactEpSelectorDft sel,
    int t, int lane, TorusPolynomial shared_a, TorusPolynomial shared_b,
    TorusPolynomial body_a, TorusPolynomial body_b) {
  if (sel == NULL || t < 0 || lane < 0 || t >= sel->T || lane >= sel->r) return -1;
  if (shared_a->N != sel->N || shared_b->N != sel->N ||
      body_a->N != sel->N || body_b->N != sel->N) return -2;
  const int idx = t * sel->r + lane;
  polynomial_torus_to_DFT(sel->shared_a[idx], shared_a);
  polynomial_torus_to_DFT(sel->shared_b[idx], shared_b);
  polynomial_torus_to_DFT(sel->body_a[idx], body_a);
  polynomial_torus_to_DFT(sel->body_b[idx], body_b);
  return 0;
}

static int compact_ep_kernel_dft_api(CompactEpOutputDft out,
    TorusPolynomial source_shared, TorusPolynomial source_body,
    CompactEpSelectorDft sel, int lane, CompactEpScratch scratch) {
  if (out == NULL || source_shared == NULL || source_body == NULL ||
      sel == NULL || scratch == NULL) return -1;
  if (lane < 0 || lane >= sel->r) return -2;
  if (out->N != sel->N || scratch->N != sel->N ||
      source_shared->N != sel->N || source_body->N != sel->N) return -3;
  zero_dft(out->a);
  zero_dft(out->b);
  for (int t = 0; t < sel->T; t++) {
    const int idx = t * sel->r + lane;
    polynomial_decompose_i(scratch->dec_shared, source_shared, sel->Bg_bit, sel->T, t);
    polynomial_decompose_i(scratch->dec_body, source_body, sel->Bg_bit, sel->T, t);
    polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
    polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
    polynomial_mul_addto_DFT(out->a, scratch->dec_shared_dft, sel->shared_a[idx]);
    polynomial_mul_addto_DFT(out->b, scratch->dec_shared_dft, sel->shared_b[idx]);
    polynomial_mul_addto_DFT(out->a, scratch->dec_body_dft, sel->body_a[idx]);
    polynomial_mul_addto_DFT(out->b, scratch->dec_body_dft, sel->body_b[idx]);
  }
  return 0;
}

static int compact_ep_body_only_kernel_dft_api(CompactEpOutputDft out,
    TorusPolynomial source_body, CompactEpSelectorDft sel, int lane,
    CompactEpScratch scratch) {
  if (out == NULL || source_body == NULL || sel == NULL || scratch == NULL) return -1;
  if (lane < 0 || lane >= sel->r) return -2;
  if (out->N != sel->N || scratch->N != sel->N || source_body->N != sel->N) return -3;
  zero_dft(out->a);
  zero_dft(out->b);
  for (int t = 0; t < sel->T; t++) {
    const int idx = t * sel->r + lane;
    polynomial_decompose_i(scratch->dec_body, source_body, sel->Bg_bit, sel->T, t);
    polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
    polynomial_mul_addto_DFT(out->a, scratch->dec_body_dft, sel->body_a[idx]);
    polynomial_mul_addto_DFT(out->b, scratch->dec_body_dft, sel->body_b[idx]);
  }
  return 0;
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

static uint64_t pointer_failures(void **ptrs, int count) {
  uint64_t failures = 0;
  for (int i = 0; i < count; i++) {
    if (ptrs[i] == NULL) failures++;
    for (int j = i + 1; j < count; j++) {
      if (ptrs[i] == ptrs[j]) failures++;
    }
  }
  return failures;
}

static uint64_t api_ownership_failures(CompactEpSelectorDft sel,
    CompactEpOutputDft out, CompactEpScratch scratch) {
  const int rows = sel->T * sel->r;
  const int count = 4 * rows + 6;
  void **ptrs = (void **)safe_malloc(sizeof(void *) * count);
  int n = 0;
  for (int i = 0; i < rows; i++) {
    ptrs[n++] = sel->shared_a[i]->coeffs;
    ptrs[n++] = sel->shared_b[i]->coeffs;
    ptrs[n++] = sel->body_a[i]->coeffs;
    ptrs[n++] = sel->body_b[i]->coeffs;
  }
  ptrs[n++] = out->a->coeffs;
  ptrs[n++] = out->b->coeffs;
  ptrs[n++] = scratch->dec_shared->coeffs;
  ptrs[n++] = scratch->dec_body->coeffs;
  ptrs[n++] = scratch->dec_shared_dft->coeffs;
  ptrs[n++] = scratch->dec_body_dft->coeffs;
  const uint64_t failures = pointer_failures(ptrs, n);
  free(ptrs);
  return failures;
}

static uint64_t api_metadata_failures(CompactEpSelectorDft sel,
    CompactEpOutputDft out, CompactEpScratch scratch, int T, int Bg_bit,
    int k, int r, int N) {
  uint64_t failures = 0;
  if (sel->T != T || sel->Bg_bit != Bg_bit || sel->k != k ||
      sel->r != r || sel->N != N) failures++;
  if (out->N != N) failures++;
  if (scratch->N != N) failures++;
  return failures;
}

static void compact_ep_reference_coeff(TorusPolynomial out_a,
    TorusPolynomial out_b, TorusPolynomial source_shared,
    TorusPolynomial source_body, TorusPolynomial *shared_a,
    TorusPolynomial *shared_b, TorusPolynomial *body_a,
    TorusPolynomial *body_b, int T, int r, int lane, int Bg_bit,
    CompactEpScratch scratch) {
  zero_poly(out_a);
  zero_poly(out_b);
  for (int t = 0; t < T; t++) {
    const int idx = t * r + lane;
    polynomial_decompose_i(scratch->dec_shared, source_shared, Bg_bit, T, t);
    polynomial_decompose_i(scratch->dec_body, source_body, Bg_bit, T, t);
    polynomial_naive_mul_addto_torus(out_a, scratch->dec_shared, shared_a[idx]);
    polynomial_naive_mul_addto_torus(out_b, scratch->dec_shared, shared_b[idx]);
    polynomial_naive_mul_addto_torus(out_a, scratch->dec_body, body_a[idx]);
    polynomial_naive_mul_addto_torus(out_b, scratch->dec_body, body_b[idx]);
  }
}

static void run_case(int r, int N, int T, int k, int Bg_bit, int seed) {
  const uint64_t tol = 131072;
  const int noise_coeff_bound = 1;
  const int rows = T * r;
  const int exp = (seed * 19 + r + 11) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
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
  TorusPolynomial neg_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_b_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial api_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial neg_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noisy = polynomial_new_torus_polynomial(N);
  TorusPolynomial observed_noise = polynomial_new_torus_polynomial(N);

  CompactEpSelectorDft sel = compact_ep_selector_dft_alloc(T, Bg_bit, k, r, N);
  CompactEpOutputDft out = compact_ep_output_dft_alloc(N);
  CompactEpOutputDft neg_out = compact_ep_output_dft_alloc(N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);

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
      encrypt_row(shared_a[idx], shared_b[idx], secret[q], gadget,
          shared_noise[idx], q, t, 0, seed);
      encrypt_row(body_a[idx], body_b[idx], secret[q], gadget,
          body_noise[idx], q, t, 1, seed);
      compact_ep_selector_set_row_from_torus(sel, t, q, shared_a[idx],
          shared_b[idx], body_a[idx], body_b[idx]);
    }
  }

  uint64_t ownership_failures = api_ownership_failures(sel, out, scratch);
  uint64_t metadata_failures = api_metadata_failures(sel, out, scratch, T,
      Bg_bit, k, r, N);
  uint64_t guard_failures = 0;
  if (compact_ep_selector_set_row_from_torus(sel, T, 0, shared_a[0], shared_b[0],
      body_a[0], body_b[0]) == 0) guard_failures++;
  if (compact_ep_kernel_dft_api(out, source_shared[0], source_body[0], sel, r,
      scratch) == 0) guard_failures++;

  uint64_t component_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t noise_model_mismatches = 0;
  uint64_t negative_failures = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_phase_gap = 0;
  uint64_t dummy_gap = 0;
  uint64_t kernel_allocations = 0;

  for (int q = 0; q < r; q++) {
    compact_ep_reference_coeff(coeff_a, coeff_b, source_shared[q],
        source_body[q], shared_a, shared_b, body_a, body_b, T, r, q, Bg_bit,
        scratch);
    const uint64_t alloc_before = g_api_alloc_polys;
    compact_ep_kernel_dft_api(out, source_shared[q], source_body[q], sel, q,
        scratch);
    kernel_allocations += g_api_alloc_polys - alloc_before;
    polynomial_DFT_to_torus(out_a_torus, out->a);
    polynomial_DFT_to_torus(out_b_torus, out->b);
    compare_poly(coeff_a, out_a_torus, tol, &component_mismatches,
        &max_component_gap);
    compare_poly(coeff_b, out_b_torus, tol, &component_mismatches,
        &max_component_gap);

    zero_poly(expected_clean);
    zero_poly(expected_noise);
    for (int t = 0; t < T; t++) {
      const int idx = t * r + q;
      make_gadget(gadget, t, Bg_bit, exp, monomial);
      polynomial_decompose_i(scratch->dec_shared, source_shared[q], Bg_bit, T, t);
      polynomial_decompose_i(scratch->dec_body, source_body[q], Bg_bit, T, t);
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

    compact_ep_body_only_kernel_dft_api(neg_out, source_body[q], sel, q, scratch);
    polynomial_DFT_to_torus(neg_a_torus, neg_out->a);
    polynomial_DFT_to_torus(neg_b_torus, neg_out->b);
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

  compact_ep_scratch_free(scratch);
  compact_ep_output_dft_free(neg_out);
  compact_ep_output_dft_free(out);
  compact_ep_selector_dft_free(sel);
  if (g_api_alloc_polys != g_api_free_polys) ownership_failures++;

  const int ok = ownership_failures == 0 && metadata_failures == 0
      && guard_failures == 0 && kernel_allocations == 0
      && component_mismatches == 0 && phase_mismatches == 0
      && noise_model_mismatches == 0 && negative_failures > 0
      && dft_ratio > 1.0 && total_ratio >= 1.0;

  printf("API,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%.6f"
         ",%.6f,%s\n",
      STAGE128_BACKEND, r, N, T, k, Bg_bit, seed, ownership_failures,
      metadata_failures, guard_failures, kernel_allocations,
      component_mismatches, phase_mismatches, noise_model_mismatches,
      negative_failures, max_component_gap, max_phase_gap, tol, dft_ratio,
      total_ratio, ok ? "PASS_COMPACT_EP_API_BOUNDARY" : "FAIL");

  free_poly_array_local(secret, r);
  free_poly_array_local(source_shared, r);
  free_poly_array_local(source_body, r);
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
  free_polynomial(neg_a_torus);
  free_polynomial(neg_b_torus);
  free_polynomial(coeff_phase);
  free_polynomial(api_phase);
  free_polynomial(neg_phase);
  free_polynomial(expected_clean);
  free_polynomial(expected_noise);
  free_polynomial(expected_noisy);
  free_polynomial(observed_noise);
}

#ifndef CLOCK_MONOTONIC_RAW
#define CLOCK_MONOTONIC_RAW CLOCK_MONOTONIC
#endif

static volatile double g_stage130_sink = 0.0;

static uint64_t now_ns_stage130(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
  return ((uint64_t)ts.tv_sec * 1000000000ULL) + (uint64_t)ts.tv_nsec;
}

static DFT_Polynomial *new_dft_array_api_stage130(int count, int N) {
  DFT_Polynomial *out = (DFT_Polynomial *)safe_malloc(sizeof(DFT_Polynomial) * count);
  for (int i = 0; i < count; i++) out[i] = api_new_dft_polynomial(N);
  return out;
}

static void free_dft_array_api_stage130(DFT_Polynomial *in, int count) {
  for (int i = 0; i < count; i++) api_free_dft_polynomial(in[i]);
  free(in);
}

static void consume_dft_array_stage130(DFT_Polynomial *arr, int count) {
  double s = 0.0;
  for (int i = 0; i < count; i++) s += arr[i]->coeffs[(i * 17) & (arr[i]->N - 1)];
  g_stage130_sink += s;
}

static void consume_outputs_stage130(CompactEpOutputDft *out, int r) {
  double s = 0.0;
  for (int q = 0; q < r; q++) {
    const int idx = (q * 19) & (out[q]->N - 1);
    s += out[q]->a->coeffs[idx] + out[q]->b->coeffs[idx];
  }
  g_stage130_sink += s;
}

static void fill_dense_rows_stage130(DFT_Polynomial *dense_rows, int m, int T,
    int N, int seed) {
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      for (int o = 0; o < m; o++) {
        fill_small_mask(tmp, c, t, o, seed + 2000);
        polynomial_torus_to_DFT(dense_rows[(t * m + c) * m + o], tmp);
      }
    }
  }
  free_polynomial(tmp);
}

static void dense_kernel_all_stage130(DFT_Polynomial *out,
    TorusPolynomial *source, DFT_Polynomial *dense_rows, int m, int T,
    int Bg_bit, CompactEpScratch scratch) {
  for (int o = 0; o < m; o++) zero_dft(out[o]);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      polynomial_decompose_i(scratch->dec_shared, source[c], Bg_bit, T, t);
      polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
      for (int o = 0; o < m; o++) {
        polynomial_mul_addto_DFT(out[o], scratch->dec_shared_dft,
            dense_rows[(t * m + c) * m + o]);
      }
    }
  }
}

static void compact_shared_all_lanes(CompactEpOutputDft *out,
    TorusPolynomial source_shared, TorusPolynomial *source_body,
    CompactEpSelectorDft sel, CompactEpScratch scratch) {
  for (int q = 0; q < sel->r; q++) {
    zero_dft(out[q]->a);
    zero_dft(out[q]->b);
  }
  for (int t = 0; t < sel->T; t++) {
    polynomial_decompose_i(scratch->dec_shared, source_shared, sel->Bg_bit, sel->T, t);
    polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
    for (int q = 0; q < sel->r; q++) {
      const int idx = t * sel->r + q;
      polynomial_decompose_i(scratch->dec_body, source_body[q], sel->Bg_bit, sel->T, t);
      polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
      polynomial_mul_addto_DFT(out[q]->a, scratch->dec_shared_dft, sel->shared_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, scratch->dec_shared_dft, sel->shared_b[idx]);
      polynomial_mul_addto_DFT(out[q]->a, scratch->dec_body_dft, sel->body_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, scratch->dec_body_dft, sel->body_b[idx]);
    }
  }
}

static void compact_shared_body_only_all(CompactEpOutputDft *out,
    TorusPolynomial *source_body, CompactEpSelectorDft sel,
    CompactEpScratch scratch) {
  for (int q = 0; q < sel->r; q++) {
    zero_dft(out[q]->a);
    zero_dft(out[q]->b);
  }
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      const int idx = t * sel->r + q;
      polynomial_decompose_i(scratch->dec_body, source_body[q], sel->Bg_bit, sel->T, t);
      polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
      polynomial_mul_addto_DFT(out[q]->a, scratch->dec_body_dft, sel->body_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, scratch->dec_body_dft, sel->body_b[idx]);
    }
  }
}

static void dense_decomp_dft_stage130(DFT_Polynomial *digits,
    TorusPolynomial *source, int m, int T, int Bg_bit, CompactEpScratch scratch) {
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      const int idx = t * m + c;
      polynomial_decompose_i(scratch->dec_shared, source[c], Bg_bit, T, t);
      polynomial_torus_to_DFT(digits[idx], scratch->dec_shared);
    }
  }
}

static void compact_shared_decomp_dft(DFT_Polynomial *digits_shared,
    DFT_Polynomial *digits_body, TorusPolynomial source_shared,
    TorusPolynomial *source_body, int r, int T, int Bg_bit,
    CompactEpScratch scratch) {
  for (int t = 0; t < T; t++) {
    polynomial_decompose_i(scratch->dec_shared, source_shared, Bg_bit, T, t);
    polynomial_torus_to_DFT(digits_shared[t], scratch->dec_shared);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      polynomial_decompose_i(scratch->dec_body, source_body[q], Bg_bit, T, t);
      polynomial_torus_to_DFT(digits_body[idx], scratch->dec_body);
    }
  }
}

static void dense_addmul_stage130(DFT_Polynomial *out, DFT_Polynomial *digits,
    DFT_Polynomial *dense_rows, int m, int T) {
  for (int o = 0; o < m; o++) zero_dft(out[o]);
  for (int t = 0; t < T; t++) {
    for (int c = 0; c < m; c++) {
      const int didx = t * m + c;
      for (int o = 0; o < m; o++) {
        polynomial_mul_addto_DFT(out[o], digits[didx],
            dense_rows[(t * m + c) * m + o]);
      }
    }
  }
}

static void compact_shared_addmul(CompactEpOutputDft *out,
    DFT_Polynomial *digits_shared, DFT_Polynomial *digits_body,
    CompactEpSelectorDft sel) {
  for (int q = 0; q < sel->r; q++) {
    zero_dft(out[q]->a);
    zero_dft(out[q]->b);
  }
  for (int t = 0; t < sel->T; t++) {
    for (int q = 0; q < sel->r; q++) {
      const int idx = t * sel->r + q;
      polynomial_mul_addto_DFT(out[q]->a, digits_shared[t], sel->shared_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, digits_shared[t], sel->shared_b[idx]);
      polynomial_mul_addto_DFT(out[q]->a, digits_body[idx], sel->body_a[idx]);
      polynomial_mul_addto_DFT(out[q]->b, digits_body[idx], sel->body_b[idx]);
    }
  }
}

static void print_bench_stage130(int r, int N, int T, int k, int Bg_bit,
    int seed, int sample, int reps, int warmups, const char *variant,
    uint64_t total_ns) {
  const double avg_us = ((double)total_ns / (double)reps) / 1000.0;
  printf("BENCH,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%.6f,%s\n",
      STAGE128_BACKEND, r, N, T, k, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, avg_us / (double)r, "PASS_BENCH_ROW");
}

static void run_shared_source_case(int r, int N, int T, int k, int Bg_bit,
    int seed) {
  const uint64_t tol = 131072;
  const int rows = T * r;
  const int exp = (seed * 19 + r + 11) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial source_shared = polynomial_new_torus_polynomial(N);
  TorusPolynomial *source_body = new_poly_array(r, N);
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

  CompactEpSelectorDft sel = compact_ep_selector_dft_alloc(T, Bg_bit, k, r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);
  CompactEpOutputDft *out =
      (CompactEpOutputDft *)safe_malloc(sizeof(CompactEpOutputDft) * r);
  CompactEpOutputDft *neg_out =
      (CompactEpOutputDft *)safe_malloc(sizeof(CompactEpOutputDft) * r);
  for (int q = 0; q < r; q++) {
    out[q] = compact_ep_output_dft_alloc(N);
    neg_out[q] = compact_ep_output_dft_alloc(N);
  }

  fill_source(source_shared, 0, 0, seed);
  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      fill_noise(shared_noise[idx], q, t, 0, seed, 1);
      fill_noise(body_noise[idx], q, t, 1, seed, 1);
      encrypt_row(shared_a[idx], shared_b[idx], secret[q], gadget,
          shared_noise[idx], q, t, 0, seed);
      encrypt_row(body_a[idx], body_b[idx], secret[q], gadget,
          body_noise[idx], q, t, 1, seed);
      compact_ep_selector_set_row_from_torus(sel, t, q, shared_a[idx],
          shared_b[idx], body_a[idx], body_b[idx]);
    }
  }

  compact_shared_all_lanes(out, source_shared, source_body, sel, scratch);
  compact_shared_body_only_all(neg_out, source_body, sel, scratch);

  uint64_t component_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t noise_model_mismatches = 0;
  uint64_t negative_failures = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_phase_gap = 0;
  uint64_t dummy_gap = 0;
  for (int q = 0; q < r; q++) {
    compact_ep_reference_coeff(coeff_a, coeff_b, source_shared,
        source_body[q], shared_a, shared_b, body_a, body_b, T, r, q, Bg_bit,
        scratch);
    polynomial_DFT_to_torus(out_a_torus, out[q]->a);
    polynomial_DFT_to_torus(out_b_torus, out[q]->b);
    compare_poly(coeff_a, out_a_torus, tol, &component_mismatches, &max_component_gap);
    compare_poly(coeff_b, out_b_torus, tol, &component_mismatches, &max_component_gap);

    zero_poly(expected_clean);
    zero_poly(expected_noise);
    for (int t = 0; t < T; t++) {
      const int idx = t * r + q;
      make_gadget(gadget, t, Bg_bit, exp, monomial);
      polynomial_decompose_i(scratch->dec_shared, source_shared, Bg_bit, T, t);
      polynomial_decompose_i(scratch->dec_body, source_body[q], Bg_bit, T, t);
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
    compare_poly(api_phase, expected_noisy, tol, &phase_mismatches, &max_phase_gap);
    for (int i = 0; i < N; i++) {
      observed_noise->coeffs[i] = coeff_phase->coeffs[i] - expected_clean->coeffs[i];
    }
    compare_poly(observed_noise, expected_noise, 0, &noise_model_mismatches, &dummy_gap);

    polynomial_DFT_to_torus(neg_a_torus, neg_out[q]->a);
    polynomial_DFT_to_torus(neg_b_torus, neg_out[q]->b);
    phase(neg_phase, neg_a_torus, neg_b_torus, secret[q]);
    compare_poly(neg_phase, expected_noisy, 0, &negative_failures, &dummy_gap);
  }

  const uint64_t dense_dft_terms = (uint64_t)T * (uint64_t)(k + r) * (uint64_t)(k + r);
  const uint64_t compact_dft_terms = 4ULL * (uint64_t)T * (uint64_t)r;
  const uint64_t dense_dec_terms = (uint64_t)T * (uint64_t)(k + r);
  const uint64_t compact_dec_terms = (uint64_t)T * (uint64_t)(k + r);
  const double dft_ratio = (double)dense_dft_terms / (double)compact_dft_terms;
  const double total_ratio =
      (double)(dense_dft_terms + dense_dec_terms) /
      (double)(compact_dft_terms + compact_dec_terms);
  const int ok = component_mismatches == 0 && phase_mismatches == 0 &&
      noise_model_mismatches == 0 && negative_failures > 0;
  printf("SHAREDAPI,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%.6f,%.6f,%s\n",
      STAGE128_BACKEND, r, N, T, k, Bg_bit, seed, component_mismatches,
      phase_mismatches, noise_model_mismatches, negative_failures,
      max_component_gap, max_phase_gap, tol, dft_ratio, total_ratio,
      ok ? "PASS_SHARED_SOURCE_COMPACT_EP" : "FAIL");

  for (int q = 0; q < r; q++) {
    compact_ep_output_dft_free(neg_out[q]);
    compact_ep_output_dft_free(out[q]);
  }
  free(neg_out);
  free(out);
  compact_ep_scratch_free(scratch);
  compact_ep_selector_dft_free(sel);
  free_poly_array_local(secret, r);
  free_polynomial(source_shared);
  free_poly_array_local(source_body, r);
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

static void bench_shared_case(int r, int N, int T, int k, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  const int rows = T * r;
  const int m = k + r;
  const int dense_row_count = T * m * m;
  const int dense_digit_count = T * m;
  const int body_digit_count = T * r;
  const int exp = (seed * 19 + r + 11) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial source_shared = polynomial_new_torus_polynomial(N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *dense_source = new_poly_array(m, N);
  TorusPolynomial *shared_a = new_poly_array(rows, N);
  TorusPolynomial *shared_b = new_poly_array(rows, N);
  TorusPolynomial *body_a = new_poly_array(rows, N);
  TorusPolynomial *body_b = new_poly_array(rows, N);
  TorusPolynomial noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);

  CompactEpSelectorDft sel = compact_ep_selector_dft_alloc(T, Bg_bit, k, r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);
  CompactEpOutputDft *compact_out =
      (CompactEpOutputDft *)safe_malloc(sizeof(CompactEpOutputDft) * r);
  for (int q = 0; q < r; q++) compact_out[q] = compact_ep_output_dft_alloc(N);

  DFT_Polynomial *dense_rows = new_dft_array_api_stage130(dense_row_count, N);
  DFT_Polynomial *dense_out = new_dft_array_api_stage130(m, N);
  DFT_Polynomial *dense_digits = new_dft_array_api_stage130(dense_digit_count, N);
  DFT_Polynomial *shared_digits = new_dft_array_api_stage130(T, N);
  DFT_Polynomial *body_digits = new_dft_array_api_stage130(body_digit_count, N);

  fill_source(source_shared, 0, 0, seed);
  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(source_body[q], q, 1, seed);
  }
  for (int i = 0; i < N; i++) dense_source[0]->coeffs[i] = source_shared->coeffs[i];
  for (int q = 0; q < r; q++) {
    for (int i = 0; i < N; i++) dense_source[1 + q]->coeffs[i] = source_body[q]->coeffs[i];
  }
  zero_poly(noise);
  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      encrypt_row(shared_a[idx], shared_b[idx], secret[q], gadget, noise,
          q, t, 0, seed);
      encrypt_row(body_a[idx], body_b[idx], secret[q], gadget, noise,
          q, t, 1, seed);
      compact_ep_selector_set_row_from_torus(sel, t, q, shared_a[idx],
          shared_b[idx], body_a[idx], body_b[idx]);
    }
  }
  fill_dense_rows_stage130(dense_rows, m, T, N, seed);
  dense_decomp_dft_stage130(dense_digits, dense_source, m, T, Bg_bit, scratch);
  compact_shared_decomp_dft(shared_digits, body_digits, source_shared,
      source_body, r, T, Bg_bit, scratch);

  for (int sample = 0; sample < samples; sample++) {
    uint64_t start = 0;
    uint64_t total = 0;
    for (int i = 0; i < warmups; i++) {
      dense_kernel_all_stage130(dense_out, dense_source, dense_rows, m, T, Bg_bit, scratch);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      dense_kernel_all_stage130(dense_out, dense_source, dense_rows, m, T, Bg_bit, scratch);
    }
    total = now_ns_stage130() - start;
    consume_dft_array_stage130(dense_out, m);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_all_proxy", total);

    for (int i = 0; i < warmups; i++) {
      compact_shared_all_lanes(compact_out, source_shared, source_body, sel, scratch);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      compact_shared_all_lanes(compact_out, source_shared, source_body, sel, scratch);
    }
    total = now_ns_stage130() - start;
    consume_outputs_stage130(compact_out, r);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_shared_all_lanes", total);

    for (int i = 0; i < warmups; i++) {
      dense_decomp_dft_stage130(dense_digits, dense_source, m, T, Bg_bit, scratch);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      dense_decomp_dft_stage130(dense_digits, dense_source, m, T, Bg_bit, scratch);
    }
    total = now_ns_stage130() - start;
    consume_dft_array_stage130(dense_digits, dense_digit_count);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_decomp_dft_proxy", total);

    for (int i = 0; i < warmups; i++) {
      compact_shared_decomp_dft(shared_digits, body_digits, source_shared,
          source_body, r, T, Bg_bit, scratch);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      compact_shared_decomp_dft(shared_digits, body_digits, source_shared,
          source_body, r, T, Bg_bit, scratch);
    }
    total = now_ns_stage130() - start;
    consume_dft_array_stage130(shared_digits, T);
    consume_dft_array_stage130(body_digits, body_digit_count);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_shared_decomp_dft", total);

    for (int i = 0; i < warmups; i++) {
      dense_addmul_stage130(dense_out, dense_digits, dense_rows, m, T);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      dense_addmul_stage130(dense_out, dense_digits, dense_rows, m, T);
    }
    total = now_ns_stage130() - start;
    consume_dft_array_stage130(dense_out, m);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "dense_addmul_proxy", total);

    for (int i = 0; i < warmups; i++) {
      compact_shared_addmul(compact_out, shared_digits, body_digits, sel);
    }
    start = now_ns_stage130();
    for (int i = 0; i < reps; i++) {
      compact_shared_addmul(compact_out, shared_digits, body_digits, sel);
    }
    total = now_ns_stage130() - start;
    consume_outputs_stage130(compact_out, r);
    print_bench_stage130(r, N, T, k, Bg_bit, seed, sample, reps, warmups,
        "compact_shared_addmul", total);
  }

  free_dft_array_api_stage130(body_digits, body_digit_count);
  free_dft_array_api_stage130(shared_digits, T);
  free_dft_array_api_stage130(dense_digits, dense_digit_count);
  free_dft_array_api_stage130(dense_out, m);
  free_dft_array_api_stage130(dense_rows, dense_row_count);
  for (int q = 0; q < r; q++) compact_ep_output_dft_free(compact_out[q]);
  free(compact_out);
  compact_ep_scratch_free(scratch);
  compact_ep_selector_dft_free(sel);
  free_poly_array_local(secret, r);
  free_polynomial(source_shared);
  free_poly_array_local(source_body, r);
  free_poly_array_local(dense_source, m);
  free_poly_array_local(shared_a, rows);
  free_poly_array_local(shared_b, rows);
  free_poly_array_local(body_a, rows);
  free_poly_array_local(body_b, rows);
  free_polynomial(noise);
  free_polynomial(gadget);
}

int main(void) {
  const int k = 1;
  const int T = 7;
  const int Bg_bit = 7;
  const int samples = 5;
  const int reps = 6;
  const int warmups = 1;

  run_shared_source_case(2, 512, T, k, Bg_bit, 0);
  run_shared_source_case(4, 512, T, k, Bg_bit, 0);
  run_shared_source_case(6, 512, T, k, Bg_bit, 0);
  run_shared_source_case(2, 1024, T, k, Bg_bit, 0);
  run_shared_source_case(4, 1024, T, k, Bg_bit, 0);
  run_shared_source_case(6, 1024, T, k, Bg_bit, 0);

  bench_shared_case(2, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(4, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(6, 512, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(2, 1024, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(4, 1024, T, k, Bg_bit, 0, samples, reps, warmups);
  bench_shared_case(6, 1024, T, k, Bg_bit, 0, samples, reps, warmups);

  fprintf(stderr, "stage130_sink=%f\n", g_stage130_sink);
  return 0;
}
