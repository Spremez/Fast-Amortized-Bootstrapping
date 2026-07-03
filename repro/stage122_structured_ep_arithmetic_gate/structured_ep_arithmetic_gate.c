#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

enum { MOD = 2013265921 };

typedef struct {
  size_t N;
  int64_t *coeffs;
} Poly;

typedef struct {
  size_t N;
  int64_t *evals;
} DftPoly;

typedef struct {
  Poly mask;
  Poly body;
} Cipher;

static void *xcalloc(size_t count, size_t size) {
  void *ptr = calloc(count, size);
  if (ptr == NULL) {
    fprintf(stderr, "calloc failed\n");
    exit(2);
  }
  return ptr;
}

static long rss_kb(void) {
  FILE *fd = fopen("/proc/self/statm", "r");
  if (fd == NULL) return -1;
  long pages_total = 0;
  long pages_rss = 0;
  if (fscanf(fd, "%ld %ld", &pages_total, &pages_rss) != 2) {
    fclose(fd);
    return -1;
  }
  fclose(fd);
  long page = sysconf(_SC_PAGESIZE);
  if (page <= 0) page = 4096;
  return (pages_rss * page) / 1024;
}

static int64_t abs64(int64_t x) {
  return x < 0 ? -x : x;
}

static int64_t mod_norm(int64_t x) {
  int64_t v = x % MOD;
  if (v < 0) v += MOD;
  return v;
}

static int64_t mod_signed(int64_t x) {
  int64_t v = mod_norm(x);
  if (v > MOD / 2) v -= MOD;
  return v;
}

static int64_t mod_mul(int64_t a, int64_t b) {
  return (int64_t)(((__int128)mod_norm(a) * (__int128)mod_norm(b)) % MOD);
}

static int64_t mod_pow(int64_t a, int64_t e) {
  int64_t out = 1;
  int64_t base = mod_norm(a);
  while (e > 0) {
    if (e & 1) out = mod_mul(out, base);
    base = mod_mul(base, base);
    e >>= 1;
  }
  return out;
}

static int64_t mod_inv(int64_t x) {
  return mod_pow(x, MOD - 2);
}

static int64_t primitive_root_mod(void) {
  const int64_t factors[] = {2, 3, 5};
  for (int64_t g = 2; g < 128; g++) {
    int ok = 1;
    for (size_t i = 0; i < sizeof(factors) / sizeof(factors[0]); i++) {
      if (mod_pow(g, (MOD - 1) / factors[i]) == 1) {
        ok = 0;
        break;
      }
    }
    if (ok) return g;
  }
  return 0;
}

static int64_t negacyclic_root(size_t N, int *ok) {
  const int64_t g = primitive_root_mod();
  if (g == 0 || ((MOD - 1) % (int64_t)(2 * N)) != 0) {
    *ok = 0;
    return 0;
  }
  const int64_t psi = mod_pow(g, (MOD - 1) / (int64_t)(2 * N));
  *ok = (mod_pow(psi, (int64_t)N) == MOD - 1)
      && (mod_pow(psi, (int64_t)(2 * N)) == 1);
  return psi;
}

static int64_t small_raw(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0xbf58476d1ce4e5b9ULL) * 0x94d049bb133111ebULL;
  x ^= (b + 0x2545f4914f6cdd1dULL) * 0x9e3779b97f4a7c15ULL;
  x ^= (c + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  return (int64_t)x;
}

static int64_t bounded(uint64_t salt, uint64_t a, uint64_t b, uint64_t c,
    int64_t bound) {
  const uint64_t width = (uint64_t)(2 * bound + 1);
  return (int64_t)((uint64_t)small_raw(salt, a, b, c) % width) - bound;
}

static int64_t nonzero_digit(size_t row, size_t lane, size_t coeff, size_t seed) {
  int64_t v = bounded(51 + seed, row, lane, coeff, 1);
  return v == 0 ? 1 : v;
}

static int64_t message_coeff(size_t row, size_t lane, size_t coeff, size_t seed) {
  if (row == 0) {
    return bounded(61 + seed, lane, coeff, 0, 2);
  }
  if (row == lane + 1) {
    return bounded(71 + seed, lane, coeff, row, 2);
  }
  return 0;
}

static int64_t noise_coeff(size_t row, size_t lane, size_t coeff, size_t seed) {
  return bounded(81 + seed, row, lane, coeff, 1);
}

static Poly alloc_poly(size_t N, size_t *bytes) {
  Poly p;
  p.N = N;
  p.coeffs = (int64_t *)xcalloc(N, sizeof(int64_t));
  *bytes += sizeof(int64_t) * N;
  return p;
}

static DftPoly alloc_dft(size_t N, size_t *bytes) {
  DftPoly p;
  p.N = N;
  p.evals = (int64_t *)xcalloc(N, sizeof(int64_t));
  *bytes += sizeof(int64_t) * N;
  return p;
}

static Cipher alloc_cipher(size_t N, size_t *bytes) {
  Cipher c;
  c.mask = alloc_poly(N, bytes);
  c.body = alloc_poly(N, bytes);
  return c;
}

static void free_poly(Poly *p) {
  free(p->coeffs);
  p->coeffs = NULL;
  p->N = 0;
}

static void free_dft(DftPoly *p) {
  free(p->evals);
  p->evals = NULL;
  p->N = 0;
}

static void free_cipher(Cipher *c) {
  free_poly(&c->mask);
  free_poly(&c->body);
}

static void zero_poly(Poly *p) {
  memset(p->coeffs, 0, sizeof(int64_t) * p->N);
}

static void zero_dft(DftPoly *p) {
  memset(p->evals, 0, sizeof(int64_t) * p->N);
}

static void zero_cipher(Cipher *c) {
  zero_poly(&c->mask);
  zero_poly(&c->body);
}

static void negacyclic_mul(Poly *out, const Poly *a, const Poly *b) {
  const size_t N = out->N;
  memset(out->coeffs, 0, sizeof(int64_t) * N);
  for (size_t i = 0; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      size_t idx = i + j;
      int64_t sign = 1;
      if (idx >= N) {
        idx -= N;
        sign = -1;
      }
      out->coeffs[idx] += sign * a->coeffs[i] * b->coeffs[j];
    }
  }
}

static void negacyclic_mul_add(Poly *out, const Poly *a, const Poly *b) {
  const size_t N = out->N;
  for (size_t i = 0; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      size_t idx = i + j;
      int64_t sign = 1;
      if (idx >= N) {
        idx -= N;
        sign = -1;
      }
      out->coeffs[idx] += sign * a->coeffs[i] * b->coeffs[j];
    }
  }
}

static void forward_dft(DftPoly *out, const Poly *in, int64_t psi) {
  const size_t N = in->N;
  for (size_t j = 0; j < N; j++) {
    const int64_t root = mod_pow(psi, (int64_t)(2 * j + 1));
    int64_t power = 1;
    int64_t acc = 0;
    for (size_t i = 0; i < N; i++) {
      acc = mod_norm(acc + mod_mul(in->coeffs[i], power));
      power = mod_mul(power, root);
    }
    out->evals[j] = acc;
  }
}

static void inverse_dft(Poly *out, const DftPoly *in, int64_t psi) {
  const size_t N = out->N;
  const int64_t n_inv = mod_inv((int64_t)N);
  for (size_t i = 0; i < N; i++) {
    int64_t acc = 0;
    for (size_t j = 0; j < N; j++) {
      const int64_t root = mod_pow(psi, (int64_t)(2 * j + 1));
      const int64_t inv_root = mod_inv(root);
      const int64_t factor = mod_pow(inv_root, (int64_t)i);
      acc = mod_norm(acc + mod_mul(in->evals[j], factor));
    }
    out->coeffs[i] = mod_signed(mod_mul(acc, n_inv));
  }
}

static void dft_mul_add(DftPoly *out, const DftPoly *a, const DftPoly *b) {
  for (size_t i = 0; i < out->N; i++) {
    out->evals[i] = mod_norm(out->evals[i] + mod_mul(a->evals[i], b->evals[i]));
  }
}

static void fill_secret(Poly *secret, size_t lane, size_t seed) {
  for (size_t i = 0; i < secret->N; i++) {
    secret->coeffs[i] = bounded(21 + seed, lane, i, 0, 1);
  }
}

static void fill_digit(Poly *digit, size_t row, size_t lane, size_t seed) {
  for (size_t i = 0; i < digit->N; i++) {
    digit->coeffs[i] = nonzero_digit(row, lane, i, seed);
  }
}

static void make_cipher(Cipher *ct, const Poly *secret, size_t row, size_t lane,
    size_t seed, uint64_t format_salt, int with_noise) {
  const size_t N = secret->N;
  Poly prod = alloc_poly(N, &(size_t){0});
  for (size_t i = 0; i < N; i++) {
    ct->mask.coeffs[i] = bounded(format_salt + 31 + seed, row, lane, i, 1);
  }
  negacyclic_mul(&prod, &ct->mask, secret);
  for (size_t i = 0; i < N; i++) {
    const int active = row == 0 || row == lane + 1;
    const int64_t e = with_noise && active ? noise_coeff(row, lane, i, seed) : 0;
    ct->body.coeffs[i] = prod.coeffs[i] + message_coeff(row, lane, i, seed) + e;
  }
  free_poly(&prod);
}

static void cipher_mul_add_coeff(Cipher *out, const Poly *digit,
    const Cipher *ct) {
  negacyclic_mul_add(&out->mask, digit, &ct->mask);
  negacyclic_mul_add(&out->body, digit, &ct->body);
}

static void cipher_mul_add_dft(DftPoly *out_mask, DftPoly *out_body,
    const Poly *digit, const Cipher *ct, int64_t psi, size_t *bytes) {
  DftPoly digit_d = alloc_dft(digit->N, bytes);
  DftPoly mask_d = alloc_dft(digit->N, bytes);
  DftPoly body_d = alloc_dft(digit->N, bytes);
  forward_dft(&digit_d, digit, psi);
  forward_dft(&mask_d, &ct->mask, psi);
  forward_dft(&body_d, &ct->body, psi);
  dft_mul_add(out_mask, &digit_d, &mask_d);
  dft_mul_add(out_body, &digit_d, &body_d);
  free_dft(&digit_d);
  free_dft(&mask_d);
  free_dft(&body_d);
}

static void cipher_from_dft(Cipher *out, const DftPoly *mask_d,
    const DftPoly *body_d, int64_t psi) {
  inverse_dft(&out->mask, mask_d, psi);
  inverse_dft(&out->body, body_d, psi);
}

static void decrypt_phase(Poly *out, const Cipher *ct, const Poly *secret) {
  Poly prod = alloc_poly(secret->N, &(size_t){0});
  negacyclic_mul(&prod, &ct->mask, secret);
  for (size_t i = 0; i < secret->N; i++) {
    out->coeffs[i] = ct->body.coeffs[i] - prod.coeffs[i];
  }
  free_poly(&prod);
}

static void compare_phase(const Poly *a, const Poly *b, uint64_t *mismatches,
    int64_t *max_gap) {
  for (size_t i = 0; i < a->N; i++) {
    const int64_t gap = abs64(a->coeffs[i] - b->coeffs[i]);
    if (gap != 0) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static int run_case(size_t r, size_t N, size_t seed) {
  int root_ok = 0;
  const int64_t psi = negacyclic_root(N, &root_ok);
  size_t bytes = 0;
  Poly *secrets = (Poly *)xcalloc(r, sizeof(Poly));
  bytes += r * sizeof(Poly);
  for (size_t lane = 0; lane < r; lane++) {
    secrets[lane] = alloc_poly(N, &bytes);
    fill_secret(&secrets[lane], lane, seed);
  }

  uint64_t dense_structured_mismatches = 0;
  uint64_t coeff_dft_mismatches = 0;
  uint64_t noisy_bound_violations = 0;
  uint64_t negative_failures = 0;
  int64_t max_dense_structured_gap = 0;
  int64_t max_coeff_dft_gap = 0;
  int64_t max_noisy_delta = 0;
  int64_t max_noise_bound = 0;

  if (root_ok) {
    for (size_t lane = 0; lane < r; lane++) {
      Cipher dense = alloc_cipher(N, &bytes);
      Cipher structured_coeff = alloc_cipher(N, &bytes);
      Cipher structured_dft = alloc_cipher(N, &bytes);
      Cipher structured_noisy = alloc_cipher(N, &bytes);
      Cipher negative = alloc_cipher(N, &bytes);
      zero_cipher(&dense);
      zero_cipher(&structured_coeff);
      zero_cipher(&structured_dft);
      zero_cipher(&structured_noisy);
      zero_cipher(&negative);

      DftPoly structured_mask_d = alloc_dft(N, &bytes);
      DftPoly structured_body_d = alloc_dft(N, &bytes);
      DftPoly noisy_mask_d = alloc_dft(N, &bytes);
      DftPoly noisy_body_d = alloc_dft(N, &bytes);
      zero_dft(&structured_mask_d);
      zero_dft(&structured_body_d);
      zero_dft(&noisy_mask_d);
      zero_dft(&noisy_body_d);

      for (size_t row = 0; row < r + 1; row++) {
        Poly digit = alloc_poly(N, &bytes);
        Cipher ct = alloc_cipher(N, &bytes);
        fill_digit(&digit, row, lane, seed);
        make_cipher(&ct, &secrets[lane], row, lane, seed, 0, 0);
        cipher_mul_add_coeff(&dense, &digit, &ct);
        negacyclic_mul_add(&negative.mask, &digit, &ct.mask);
        if (row == 0 || row == lane + 1) {
          negacyclic_mul_add(&negative.body, &digit, &ct.body);
        }
        free_cipher(&ct);
        free_poly(&digit);
      }

      const size_t kept_rows[2] = {0, lane + 1};
      for (size_t k = 0; k < 2; k++) {
        const size_t row = kept_rows[k];
        Poly digit = alloc_poly(N, &bytes);
        Cipher clean_ct = alloc_cipher(N, &bytes);
        Cipher noisy_ct = alloc_cipher(N, &bytes);
        fill_digit(&digit, row, lane, seed);
        make_cipher(&clean_ct, &secrets[lane], row, lane, seed, 100, 0);
        make_cipher(&noisy_ct, &secrets[lane], row, lane, seed, 100, 1);
        cipher_mul_add_coeff(&structured_coeff, &digit, &clean_ct);
        cipher_mul_add_dft(&structured_mask_d, &structured_body_d, &digit,
            &clean_ct, psi, &bytes);
        cipher_mul_add_dft(&noisy_mask_d, &noisy_body_d, &digit,
            &noisy_ct, psi, &bytes);
        free_cipher(&clean_ct);
        free_cipher(&noisy_ct);
        free_poly(&digit);
      }

      cipher_from_dft(&structured_dft, &structured_mask_d, &structured_body_d, psi);
      cipher_from_dft(&structured_noisy, &noisy_mask_d, &noisy_body_d, psi);

      Poly dense_phase = alloc_poly(N, &bytes);
      Poly structured_coeff_phase = alloc_poly(N, &bytes);
      Poly structured_dft_phase = alloc_poly(N, &bytes);
      Poly structured_noisy_phase = alloc_poly(N, &bytes);
      Poly negative_phase = alloc_poly(N, &bytes);
      decrypt_phase(&dense_phase, &dense, &secrets[lane]);
      decrypt_phase(&structured_coeff_phase, &structured_coeff, &secrets[lane]);
      decrypt_phase(&structured_dft_phase, &structured_dft, &secrets[lane]);
      decrypt_phase(&structured_noisy_phase, &structured_noisy, &secrets[lane]);
      decrypt_phase(&negative_phase, &negative, &secrets[lane]);

      compare_phase(&dense_phase, &structured_coeff_phase,
          &dense_structured_mismatches, &max_dense_structured_gap);
      compare_phase(&structured_coeff_phase, &structured_dft_phase,
          &coeff_dft_mismatches, &max_coeff_dft_gap);
      for (size_t i = 0; i < N; i++) {
        const int64_t delta = abs64(
            structured_noisy_phase.coeffs[i] - structured_dft_phase.coeffs[i]);
        const int64_t bound = (int64_t)(2 * N);
        if (delta > bound) noisy_bound_violations++;
        if (delta > max_noisy_delta) max_noisy_delta = delta;
        if (bound > max_noise_bound) max_noise_bound = bound;
        if (negative_phase.coeffs[i] != dense_phase.coeffs[i]) {
          negative_failures++;
        }
      }

      free_poly(&dense_phase);
      free_poly(&structured_coeff_phase);
      free_poly(&structured_dft_phase);
      free_poly(&structured_noisy_phase);
      free_poly(&negative_phase);
      free_dft(&structured_mask_d);
      free_dft(&structured_body_d);
      free_dft(&noisy_mask_d);
      free_dft(&noisy_body_d);
      free_cipher(&dense);
      free_cipher(&structured_coeff);
      free_cipher(&structured_dft);
      free_cipher(&structured_noisy);
      free_cipher(&negative);
    }
  }

  for (size_t lane = 0; lane < r; lane++) {
    free_poly(&secrets[lane]);
  }
  free(secrets);

  const uint64_t dense_terms = (uint64_t)r * (uint64_t)(r + 1);
  const uint64_t structured_terms = 2ULL * (uint64_t)r;
  const double term_ratio = (double)dense_terms / (double)structured_terms;
  const long rss = rss_kb();
  const int ok = root_ok
      && dense_structured_mismatches == 0
      && coeff_dft_mismatches == 0
      && noisy_bound_violations == 0
      && negative_failures > 0
      && term_ratio > 1.0;
  printf("ARITH,%zu,%zu,%zu,%d,%s,%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRId64 ",%" PRId64 ",%" PRId64 ",%" PRId64
         ",%" PRIu64 ",%" PRIu64 ",%.6f,%zu,%ld,%s\n",
      r, N, seed, MOD, root_ok ? "PASS_ROOT" : "FAIL_ROOT",
      dense_structured_mismatches, coeff_dft_mismatches,
      noisy_bound_violations, negative_failures, max_dense_structured_gap,
      max_coeff_dft_gap, max_noisy_delta, max_noise_bound, dense_terms,
      structured_terms, term_ratio, bytes, rss,
      ok ? "PASS_STRUCTURED_EP_ARITHMETIC" : "FAIL");
  return ok ? 0 : 1;
}

static int layout_case(size_t r, size_t N) {
  (void)N;
  const uint64_t dense_terms = (uint64_t)r * (uint64_t)(r + 1);
  const uint64_t structured_terms = 2ULL * (uint64_t)r;
  const double term_ratio = (double)dense_terms / (double)structured_terms;
  const uint64_t dense_selector = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t structured_selector = 4ULL * (uint64_t)r;
  const double selector_ratio = (double)dense_selector / (double)structured_selector;
  const int ok = term_ratio > 1.0 && selector_ratio > 1.0;
  printf("LAYOUT,%zu,%zu,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64
         ",%" PRIu64 ",%.6f,%s\n",
      r, N, dense_terms, structured_terms, term_ratio,
      dense_selector, structured_selector, selector_ratio,
      ok ? "PASS_LAYOUT" : "FAIL");
  return ok ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6};
  const size_t Ns[] = {32, 64};
  const size_t seeds[] = {0, 1, 2, 3, 4};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += layout_case(rs[i], Ns[j]);
      for (size_t k = 0; k < sizeof(seeds) / sizeof(seeds[0]); k++) {
        failures += run_case(rs[i], Ns[j], seeds[k]);
      }
    }
  }
  return failures == 0 ? 0 : 1;
}
