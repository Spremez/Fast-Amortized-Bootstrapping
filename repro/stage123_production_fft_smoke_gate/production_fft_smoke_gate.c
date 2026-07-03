#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef STAGE123_BACKEND
#define STAGE123_BACKEND "unknown"
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

static Torus small_torus(uint64_t salt, uint64_t a, uint64_t b, uint64_t c,
    uint64_t bound, int nonzero) {
  uint64_t v = mix64(salt, a, b, c) % (bound + 1);
  if (nonzero && v == 0) v = 1;
  return (Torus)v;
}

static uint64_t abs_gap(Torus a, Torus b) {
  const uint64_t d = (uint64_t)(a - b);
  if (d <= (1ULL << 63)) return d;
  return (~d) + 1ULL;
}

static void zero_poly(TorusPolynomial p) {
  memset(p->coeffs, 0, sizeof(Torus) * p->N);
}

static void zero_dft(DFT_Polynomial p) {
  memset(p->coeffs, 0, sizeof(double) * p->N);
}

static void fill_secret(TorusPolynomial out, size_t lane, size_t seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = small_torus(11 + seed, lane, (uint64_t)i, 0, 1, 0);
  }
}

static void fill_digit(TorusPolynomial out, size_t row, size_t lane, size_t seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = small_torus(21 + seed, row, lane, (uint64_t)i, 1, 1);
  }
}

static void fill_message(TorusPolynomial out, size_t row, size_t lane,
    size_t seed) {
  for (int i = 0; i < out->N; i++) {
    if (row == 0 || row == lane + 1) {
      out->coeffs[i] = small_torus(31 + seed, row, lane, (uint64_t)i, 2, 0);
    } else {
      out->coeffs[i] = 0;
    }
  }
}

static void fill_noise(TorusPolynomial out, size_t row, size_t lane,
    size_t seed) {
  for (int i = 0; i < out->N; i++) {
    if (row == 0 || row == lane + 1) {
      out->coeffs[i] = small_torus(41 + seed, row, lane, (uint64_t)i, 1, 0);
    } else {
      out->coeffs[i] = 0;
    }
  }
}

static void fill_mask(TorusPolynomial out, size_t row, size_t lane,
    size_t seed, uint64_t salt) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = small_torus(salt + seed, row, lane, (uint64_t)i, 1, 0);
  }
}

static void make_cipher(TorusPolynomial mask, TorusPolynomial body,
    TorusPolynomial secret, TorusPolynomial message, TorusPolynomial noise,
    size_t row, size_t lane, size_t seed, uint64_t mask_salt) {
  fill_mask(mask, row, lane, seed, mask_salt);
  zero_poly(body);
  polynomial_naive_mul_addto_torus(body, mask, secret);
  polynomial_addto_torus_polynomial(body, message);
  if (noise != NULL) {
    polynomial_addto_torus_polynomial(body, noise);
  }
}

static void dft_mul_add_torus(DFT_Polynomial out, TorusPolynomial a,
    TorusPolynomial b) {
  DFT_Polynomial a_d = polynomial_new_DFT_polynomial(a->N);
  DFT_Polynomial b_d = polynomial_new_DFT_polynomial(a->N);
  polynomial_torus_to_DFT(a_d, a);
  polynomial_torus_to_DFT(b_d, b);
  polynomial_mul_addto_DFT(out, a_d, b_d);
  free_DFT_polynomial(a_d);
  free_DFT_polynomial(b_d);
}

static void decrypt_phase(TorusPolynomial out, TorusPolynomial mask,
    TorusPolynomial body, TorusPolynomial secret) {
  TorusPolynomial prod = polynomial_new_torus_polynomial(secret->N);
  zero_poly(prod);
  polynomial_naive_mul_addto_torus(prod, mask, secret);
  for (int i = 0; i < secret->N; i++) {
    out->coeffs[i] = body->coeffs[i] - prod->coeffs[i];
  }
  free_polynomial(prod);
}

static void compare_exact(TorusPolynomial a, TorusPolynomial b,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if (gap != 0) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void compare_tol(TorusPolynomial a, TorusPolynomial b, uint64_t tol,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static int run_case(size_t r, int N, size_t seed) {
  const uint64_t tol = 1024;
  uint64_t coeff_expected_mismatches = 0;
  uint64_t dft_coeff_mismatches = 0;
  uint64_t noisy_dft_coeff_mismatches = 0;
  uint64_t negative_failures = 0;
  uint64_t max_coeff_expected_gap = 0;
  uint64_t max_dft_coeff_gap = 0;
  uint64_t max_noisy_dft_coeff_gap = 0;

  for (size_t lane = 0; lane < r; lane++) {
    TorusPolynomial secret = polynomial_new_torus_polynomial(N);
    fill_secret(secret, lane, seed);

    TorusPolynomial expected_clean = polynomial_new_torus_polynomial(N);
    TorusPolynomial expected_noisy = polynomial_new_torus_polynomial(N);
    TorusPolynomial coeff_mask = polynomial_new_torus_polynomial(N);
    TorusPolynomial coeff_body = polynomial_new_torus_polynomial(N);
    TorusPolynomial noisy_coeff_mask = polynomial_new_torus_polynomial(N);
    TorusPolynomial noisy_coeff_body = polynomial_new_torus_polynomial(N);
    TorusPolynomial dft_mask = polynomial_new_torus_polynomial(N);
    TorusPolynomial dft_body = polynomial_new_torus_polynomial(N);
    TorusPolynomial noisy_dft_mask = polynomial_new_torus_polynomial(N);
    TorusPolynomial noisy_dft_body = polynomial_new_torus_polynomial(N);
    TorusPolynomial negative_mask = polynomial_new_torus_polynomial(N);
    TorusPolynomial negative_body = polynomial_new_torus_polynomial(N);
    TorusPolynomial phase_coeff = polynomial_new_torus_polynomial(N);
    TorusPolynomial phase_noisy_coeff = polynomial_new_torus_polynomial(N);
    TorusPolynomial phase_dft = polynomial_new_torus_polynomial(N);
    TorusPolynomial phase_noisy_dft = polynomial_new_torus_polynomial(N);
    TorusPolynomial phase_negative = polynomial_new_torus_polynomial(N);
    DFT_Polynomial dft_mask_acc = polynomial_new_DFT_polynomial(N);
    DFT_Polynomial dft_body_acc = polynomial_new_DFT_polynomial(N);
    DFT_Polynomial noisy_dft_mask_acc = polynomial_new_DFT_polynomial(N);
    DFT_Polynomial noisy_dft_body_acc = polynomial_new_DFT_polynomial(N);

    zero_poly(expected_clean);
    zero_poly(expected_noisy);
    zero_poly(coeff_mask);
    zero_poly(coeff_body);
    zero_poly(noisy_coeff_mask);
    zero_poly(noisy_coeff_body);
    zero_poly(negative_mask);
    zero_poly(negative_body);
    zero_dft(dft_mask_acc);
    zero_dft(dft_body_acc);
    zero_dft(noisy_dft_mask_acc);
    zero_dft(noisy_dft_body_acc);

    const size_t kept_rows[2] = {0, lane + 1};
    for (size_t k = 0; k < 2; k++) {
      const size_t row = kept_rows[k];
      TorusPolynomial digit = polynomial_new_torus_polynomial(N);
      TorusPolynomial msg = polynomial_new_torus_polynomial(N);
      TorusPolynomial noise = polynomial_new_torus_polynomial(N);
      TorusPolynomial msg_noise = polynomial_new_torus_polynomial(N);
      TorusPolynomial mask = polynomial_new_torus_polynomial(N);
      TorusPolynomial body = polynomial_new_torus_polynomial(N);
      TorusPolynomial noisy_body = polynomial_new_torus_polynomial(N);

      fill_digit(digit, row, lane, seed);
      fill_message(msg, row, lane, seed);
      fill_noise(noise, row, lane, seed);
      polynomial_add_torus_polynomials(msg_noise, msg, noise);
      make_cipher(mask, body, secret, msg, NULL, row, lane, seed, 101);
      make_cipher(mask, noisy_body, secret, msg, noise, row, lane, seed, 101);

      polynomial_naive_mul_addto_torus(expected_clean, digit, msg);
      polynomial_naive_mul_addto_torus(expected_noisy, digit, msg_noise);
      polynomial_naive_mul_addto_torus(coeff_mask, digit, mask);
      polynomial_naive_mul_addto_torus(coeff_body, digit, body);
      polynomial_naive_mul_addto_torus(noisy_coeff_mask, digit, mask);
      polynomial_naive_mul_addto_torus(noisy_coeff_body, digit, noisy_body);
      dft_mul_add_torus(dft_mask_acc, digit, mask);
      dft_mul_add_torus(dft_body_acc, digit, body);
      dft_mul_add_torus(noisy_dft_mask_acc, digit, mask);
      dft_mul_add_torus(noisy_dft_body_acc, digit, noisy_body);

      free_polynomial(digit);
      free_polynomial(msg);
      free_polynomial(noise);
      free_polynomial(msg_noise);
      free_polynomial(mask);
      free_polynomial(body);
      free_polynomial(noisy_body);
    }

    polynomial_DFT_to_torus(dft_mask, dft_mask_acc);
    polynomial_DFT_to_torus(dft_body, dft_body_acc);
    polynomial_DFT_to_torus(noisy_dft_mask, noisy_dft_mask_acc);
    polynomial_DFT_to_torus(noisy_dft_body, noisy_dft_body_acc);

    decrypt_phase(phase_coeff, coeff_mask, coeff_body, secret);
    decrypt_phase(phase_noisy_coeff, noisy_coeff_mask, noisy_coeff_body, secret);
    decrypt_phase(phase_dft, dft_mask, dft_body, secret);
    decrypt_phase(phase_noisy_dft, noisy_dft_mask, noisy_dft_body, secret);

    compare_exact(phase_coeff, expected_clean, &coeff_expected_mismatches,
        &max_coeff_expected_gap);
    compare_tol(phase_dft, phase_coeff, tol, &dft_coeff_mismatches,
        &max_dft_coeff_gap);
    compare_tol(phase_noisy_dft, phase_noisy_coeff, tol,
        &noisy_dft_coeff_mismatches, &max_noisy_dft_coeff_gap);

    for (size_t row = 0; row < r + 1; row++) {
      TorusPolynomial digit = polynomial_new_torus_polynomial(N);
      TorusPolynomial msg = polynomial_new_torus_polynomial(N);
      TorusPolynomial mask = polynomial_new_torus_polynomial(N);
      TorusPolynomial body = polynomial_new_torus_polynomial(N);
      fill_digit(digit, row, lane, seed);
      fill_message(msg, row, lane, seed);
      make_cipher(mask, body, secret, msg, NULL, row, lane, seed, 201);
      polynomial_naive_mul_addto_torus(negative_mask, digit, mask);
      if (row == 0 || row == lane + 1) {
        polynomial_naive_mul_addto_torus(negative_body, digit, body);
      }
      free_polynomial(digit);
      free_polynomial(msg);
      free_polynomial(mask);
      free_polynomial(body);
    }
    decrypt_phase(phase_negative, negative_mask, negative_body, secret);
    for (int i = 0; i < N; i++) {
      if (phase_negative->coeffs[i] != expected_clean->coeffs[i]) {
        negative_failures++;
      }
    }

    free_polynomial(secret);
    free_polynomial(expected_clean);
    free_polynomial(expected_noisy);
    free_polynomial(coeff_mask);
    free_polynomial(coeff_body);
    free_polynomial(noisy_coeff_mask);
    free_polynomial(noisy_coeff_body);
    free_polynomial(dft_mask);
    free_polynomial(dft_body);
    free_polynomial(noisy_dft_mask);
    free_polynomial(noisy_dft_body);
    free_polynomial(negative_mask);
    free_polynomial(negative_body);
    free_polynomial(phase_coeff);
    free_polynomial(phase_noisy_coeff);
    free_polynomial(phase_dft);
    free_polynomial(phase_noisy_dft);
    free_polynomial(phase_negative);
    free_DFT_polynomial(dft_mask_acc);
    free_DFT_polynomial(dft_body_acc);
    free_DFT_polynomial(noisy_dft_mask_acc);
    free_DFT_polynomial(noisy_dft_body_acc);
  }

  const uint64_t structured_terms = 2ULL * (uint64_t)r;
  const int ok = coeff_expected_mismatches == 0
      && dft_coeff_mismatches == 0
      && noisy_dft_coeff_mismatches == 0
      && negative_failures > 0;
  printf("SMOKE,%s,%zu,%d,%zu,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%s\n",
      STAGE123_BACKEND, r, N, seed, tol, coeff_expected_mismatches,
      dft_coeff_mismatches, noisy_dft_coeff_mismatches, negative_failures,
      max_coeff_expected_gap, max_dft_coeff_gap, max_noisy_dft_coeff_gap,
      structured_terms, ok ? "PASS_PRODUCTION_FFT_SMOKE" : "FAIL");
  return ok ? 0 : 1;
}

static void print_layout(size_t r, int N) {
  const uint64_t dense_terms = (uint64_t)r * (uint64_t)(r + 1);
  const uint64_t structured_terms = 2ULL * (uint64_t)r;
  const double ratio = (double)dense_terms / (double)structured_terms;
  printf("LAYOUT,%zu,%d,%" PRIu64 ",%" PRIu64 ",%.6f,production_fft_smoke,%s\n",
      r, N, dense_terms, structured_terms, ratio,
      ratio > 1.0 ? "PASS_LAYOUT" : "FAIL");
}

int main(void) {
  const struct {
    size_t r;
    int N;
    size_t seed;
  } cases[] = {
      {2, 1024, 0},
      {2, 1024, 1},
      {4, 1024, 0},
      {4, 1024, 1},
      {6, 1024, 0},
      {6, 1024, 1},
      {2, 2048, 0},
  };
  int failures = 0;
  print_layout(2, 1024);
  print_layout(4, 1024);
  print_layout(6, 1024);
  print_layout(2, 2048);
  for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); i++) {
    failures += run_case(cases[i].r, cases[i].N, cases[i].seed);
  }
  return failures == 0 ? 0 : 1;
}
