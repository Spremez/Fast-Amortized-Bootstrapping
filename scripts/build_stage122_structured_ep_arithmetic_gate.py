#!/usr/bin/env python3
"""Build Stage122 structured vector-shared external-product arithmetic gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage122_structured_ep_arithmetic_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
ARITH_CSV = OUT_DIR / "arithmetic_results.csv"
LAYOUT_CSV = OUT_DIR / "layout_results.csv"
COMPILE_LOG = OUT_DIR / "compile.log"
C_SOURCE = OUT_DIR / "structured_ep_arithmetic_gate.c"
C_BINARY = OUT_DIR / "structured_ep_arithmetic_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage122_structured_ep_arithmetic_gate.md"
PLAN_MD = ROOT / "experiments" / "stage122_structured_ep_arithmetic_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage122_structured_ep_arithmetic_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_vector_shared_structured_ep.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


ARITH_FIELDS = [
    "r",
    "N",
    "seed",
    "modulus",
    "root_status",
    "dense_structured_phase_mismatches",
    "structured_coeff_dft_mismatches",
    "structured_noisy_bound_violations",
    "negative_control_failures",
    "max_dense_structured_abs_gap",
    "max_coeff_dft_abs_gap",
    "max_noisy_abs_delta",
    "max_noise_bound",
    "dense_ep_terms",
    "structured_ep_terms",
    "ep_term_ratio",
    "requested_bytes",
    "rss_kb",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "dense_ep_terms",
    "structured_ep_terms",
    "ep_term_ratio",
    "dense_selector_polys",
    "structured_selector_polys",
    "selector_poly_ratio",
    "status",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize_log(text: str) -> str:
    if text is None:
        return ""
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ch.isprintable())
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def bash(command: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def write_c_source() -> None:
    source = r'''
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
'''
    write_text_lf(C_SOURCE, source.lstrip())


def compile_probe() -> bool:
    cmd = (
        "gcc -O2 -std=c11 -Wall -Wextra "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)}"
    )
    proc = bash(cmd, timeout=60)
    log = [
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(COMPILE_LOG, "\n".join(log) + "\n")
    return proc.returncode == 0


def run_probe(compile_ok: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    if not compile_ok:
        return [], []
    proc = bash(f"./{rel(C_BINARY)}", timeout=90)
    if proc.returncode != 0:
        raise RuntimeError(
            f"structured EP arithmetic probe failed\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    arith_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "ARITH":
            arith_rows.append(dict(zip(ARITH_FIELDS, values[1:])))
        elif tag == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    return arith_rows, layout_rows


def build_summary(
    compile_ok: bool,
    arith_rows: List[Dict[str, str]],
    layout_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    if not compile_ok:
        return [
            {
                "gate": "stage122_compile",
                "status": "BLOCKED",
                "metric": "gcc_compile",
                "value": "false",
                "evidence": rel(COMPILE_LOG),
                "detail": "Generated structured EP arithmetic probe did not compile.",
                "next_action": "Stop before structured EP work.",
            },
            {
                "gate": "stage122_decision",
                "status": "BLOCKED_STAGE122_STRUCTURED_EP_COMPILER",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(COMPILE_LOG),
                "detail": "No structured EP arithmetic evidence is available.",
                "next_action": "Fix the standalone prototype.",
            },
        ]

    arith_ok = all(row["status"] == "PASS_STRUCTURED_EP_ARITHMETIC" for row in arith_rows)
    layout_ok = all(row["status"] == "PASS_LAYOUT" for row in layout_rows)
    root_values = ";".join(row["root_status"] for row in arith_rows)
    dense_struct_values = ";".join(
        row["dense_structured_phase_mismatches"] for row in arith_rows
    )
    dft_values = ";".join(row["structured_coeff_dft_mismatches"] for row in arith_rows)
    noise_values = ";".join(row["structured_noisy_bound_violations"] for row in arith_rows)
    negative_values = ";".join(row["negative_control_failures"] for row in arith_rows)
    min_term_ratio = min(float(row["ep_term_ratio"]) for row in arith_rows)
    min_selector_ratio = min(float(row["selector_poly_ratio"]) for row in layout_rows)
    max_noise = max(int(row["max_noisy_abs_delta"]) for row in arith_rows)
    max_bound = max(int(row["max_noise_bound"]) for row in arith_rows)
    decision = (
        "PASS_STAGE122_STRUCTURED_EP_ARITHMETIC_READY_PRODUCTION_FFT_SMOKE_REQUIRED"
        if arith_ok and layout_ok and max_noise <= max_bound
        else "FAIL_STAGE122_STRUCTURED_EP_ARITHMETIC"
    )
    return [
        {
            "gate": "stage122_compile",
            "status": "PASS",
            "metric": "gcc_compile",
            "value": "true",
            "evidence": rel(COMPILE_LOG),
            "detail": "Generated structured EP arithmetic C probe compiled under WSL gcc.",
            "next_action": "Use as standalone arithmetic evidence only.",
        },
        {
            "gate": "stage122_dense_vs_structured_phase",
            "status": "PASS" if arith_ok else "FAIL",
            "metric": "dense_structured_phase_mismatches",
            "value": dense_struct_values,
            "evidence": rel(ARITH_CSV),
            "detail": "Structured vector-shared clean EP phase matches dense clean reference.",
            "next_action": "If this fails, do not enter production FFT smoke.",
        },
        {
            "gate": "stage122_coeff_vs_dft_ep",
            "status": "PASS" if arith_ok else "FAIL",
            "metric": "structured_coeff_dft_mismatches",
            "value": dft_values,
            "evidence": rel(ARITH_CSV),
            "detail": "Structured coefficient-domain EP matches exact DFT-domain EP.",
            "next_action": "If this fails, fix DFT EP arithmetic before any MOSFHET work.",
        },
        {
            "gate": "stage122_noisy_bound",
            "status": "PASS_BOUNDED" if arith_ok and max_noise <= max_bound else "FAIL",
            "metric": "structured_noisy_bound_violations",
            "value": noise_values,
            "evidence": rel(ARITH_CSV),
            "detail": "Structured noisy EP remains within the conservative digit/noise bound.",
            "next_action": "Production torus/FFT noise remains a later gate.",
        },
        {
            "gate": "stage122_negative_control",
            "status": "PASS_REJECTS_BODY_ONLY_SKIP"
            if arith_ok and all(int(v) > 0 for v in negative_values.split(";"))
            else "FAIL",
            "metric": "negative_control_failures",
            "value": negative_values,
            "evidence": rel(ARITH_CSV),
            "detail": "Body-only off-lane skip fails as expected, preserving the Stage112 warning.",
            "next_action": "Do not implement current-format body-only skipping.",
        },
        {
            "gate": "stage122_layout_terms",
            "status": "PASS" if layout_ok else "FAIL",
            "metric": "min_ep_term_ratio;min_selector_poly_ratio",
            "value": f"{min_term_ratio:.6f};{min_selector_ratio:.6f}",
            "evidence": rel(LAYOUT_CSV),
            "detail": "Structured EP keeps the term-count and selector-polynomial advantages in the prototype.",
            "next_action": "Production type/key layout still needs MOSFHET-adjacent smoke.",
        },
        {
            "gate": "stage122_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Structured EP arithmetic passes outside SAB.",
            "next_action": "Stage123 should run a production torus/FFT smoke gate outside `sab_pvw_*`.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage122 Structured EP Arithmetic Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Move the Stage121 vector-shared exact conversion prototype into a",
        "structured external-product arithmetic gate. The gate still runs outside",
        "`sab_pvw_*`: it compares dense clean reference phase, structured",
        "coefficient-domain EP, exact DFT-domain EP, noisy structured EP, and a",
        "body-only off-lane skip negative control.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage122_structured_ep_arithmetic_gate.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- no valid exact root for tested N;",
        "- structured clean EP phase differs from dense clean reference;",
        "- exact DFT-domain structured EP differs from coefficient-domain EP;",
        "- noisy structured EP exceeds the conservative digit/noise bound;",
        "- body-only off-lane skip does not fail as a negative control;",
        "- structured term ratios do not remain above 1.0.",
        "",
        "Passing this stage permits only a production torus/FFT smoke prototype",
        "outside `sab_pvw_*`.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(arith_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage122 Structured EP Arithmetic Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage122 checks selector-application arithmetic after the Stage121",
        "conversion gate. The dense reference evaluates all `r(r+1)` lane-row",
        "external-product terms. The structured vector-shared variant evaluates",
        "only two terms per lane: the lane-specific shared object and the lane",
        "body object. Equality is required at the decrypted phase, not at the",
        "ciphertext coefficient level, because masks differ between dense and",
        "vector-shared objects.",
        "",
        "The exact DFT gate computes the same structured EP by multiplying digit",
        "polynomials and ciphertext mask/body polynomials in the frequency domain",
        "and then converting back.",
        "",
        "## Arithmetic Rows",
        "",
        "| r | N | seed | dense/structured mismatches | coeff/DFT mismatches | noise violations | negative failures | EP ratio |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in arith_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['dense_structured_phase_mismatches']} | "
            f"{row['structured_coeff_dft_mismatches']} | "
            f"{row['structured_noisy_bound_violations']} | "
            f"{row['negative_control_failures']} | {row['ep_term_ratio']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | dense EP terms | structured EP terms | EP ratio | dense selector polys | structured selector polys | selector ratio |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_ep_terms']} | "
            f"{row['structured_ep_terms']} | {row['ep_term_ratio']} | "
            f"{row['dense_selector_polys']} | {row['structured_selector_polys']} | "
            f"{row['selector_poly_ratio']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This gate does not prove production torus scaling, floating FFT roundoff,",
        "gadget decomposition, real key generation, AVX512 performance, SAB",
        "schedule compatibility, or complete `T_bootstrap/r` acceleration.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V122: Vector-Shared Structured External Product",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: vector-shared selector/external-product arithmetic.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[structured-ep-prototype]`, `[phase-supported]`, `[not-production-fft]`, `[not-hot-path]`.",
        "- Main hypothesis: vector-shared objects can apply selector digits with two EP terms per lane while matching dense clean-reference phase.",
        "",
        "## Mathematical Definition",
        "",
        "For lane q, let `C_shared,q` and `C_body,q` be vector-shared ciphertext-like",
        "objects. The structured EP output is",
        "",
        "```text",
        "Out_q = D_shared,q * C_shared,q + D_body,q * C_body,q.",
        "```",
        "",
        "The dense clean reference uses rows `0..r`, but off-lane rows carry zero",
        "message. Stage122 requires `phase(Out_q)` to equal the dense clean",
        "reference phase for every tested coefficient. It separately requires the",
        "coefficient-domain structured EP and exact DFT-domain structured EP to",
        "match.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "Input: r, N, seed",
        "Output: structured EP arithmetic gate status",
        "1. Generate lane secrets, dense clean rows, and vector-shared clean/noisy rows.",
        "2. Build dense clean reference output using all rows.",
        "3. Build structured output using only shared/body rows per lane.",
        "4. Build the same structured output through exact DFT multiply-add.",
        "5. Decrypt phases and compare dense vs structured and coefficient vs DFT.",
        "6. Check noisy structured output against a conservative bound.",
        "7. Verify body-only off-lane skip fails as a negative control.",
        "```",
        "",
        "## Complexity Change",
        "",
        "- Dense EP arithmetic terms: `r(r+1)` per packed object in this prototype.",
        "- Structured EP arithmetic terms: `2r`.",
        "- Term ratio: `(r+1)/2`; this is arithmetic potential only.",
        "- Selector-polynomial ratio: `(r+1)^2/(4r)`.",
        "- What must be measured later: production FFT conversion, gadget",
        "  decomposition, real key size, cache behavior, SAB schedule integration,",
        "  and full `T_bootstrap/r`.",
        "",
        "## Paper Contribution Candidate",
        "",
        "`[experimental-gate-only]` Exact arithmetic evidence supports continuing",
        "the vector-shared MAT-RLWE SAB branch. It is not yet a paper-level",
        "bootstrapping acceleration claim.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(
    summary: List[Dict[str, str]],
    arith_rows: List[Dict[str, str]],
    layout_rows: List[Dict[str, str]],
) -> None:
    lines = [
        "# Stage122 Structured EP Arithmetic Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage122 checks vector-shared structured external-product arithmetic",
        "against a dense clean phase reference and an exact DFT-domain",
        "implementation. It remains outside `sab_pvw_*` and outside production",
        "MOSFHET FFT/AVX512 code.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | "
            f"{row['value']} | {row['detail']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | dense EP | structured EP | EP ratio | dense selector | structured selector | selector ratio | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_ep_terms']} | "
            f"{row['structured_ep_terms']} | {row['ep_term_ratio']} | "
            f"{row['dense_selector_polys']} | {row['structured_selector_polys']} | "
            f"{row['selector_poly_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Arithmetic Rows",
        "",
        "| r | N | seed | dense/structured | coeff/DFT | noise violations | negative failures | EP ratio | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in arith_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['dense_structured_phase_mismatches']} | "
            f"{row['structured_coeff_dft_mismatches']} | "
            f"{row['structured_noisy_bound_violations']} | "
            f"{row['negative_control_failures']} | {row['ep_term_ratio']} | "
            f"{row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "This removes the next finite arithmetic blocker: structured vector-shared",
        "EP matches dense clean-reference phase and exact DFT EP matches",
        "coefficient EP. It still does not prove production FFT behavior, gadget",
        "decomposition, SAB schedule integration, or complete-SAB speedup.",
    ]
    write_text_lf(OUT_MD, "\n".join(lines) + "\n")


def artifact_index(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def upsert_run_log(status: str) -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = [
        row for row in read_csv(RUN_LOG)
        if row.get("run_id") != "stage122-structured-ep-arithmetic-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(ARITH_CSV),
        rel(LAYOUT_CSV),
        rel(COMPILE_LOG),
        rel(C_SOURCE),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage122_structured_ep_arithmetic_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage122-structured-ep-arithmetic-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 122",
            "backend": "WSL gcc exact modular structured EP prototype",
            "command": "python scripts/build_stage122_structured_ep_arithmetic_gate.py",
            "params": "structured EP r=2,4,6 N=32,64 seeds=0..4 modulus=2013265921",
            "seed": "0..4",
            "status": status,
            "summary": "Stage122 validates structured vector-shared external-product arithmetic against dense clean reference and exact DFT EP outside SAB.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    write_variant()
    write_c_source()
    compile_ok = compile_probe()
    arith_rows, layout_rows = run_probe(compile_ok)
    summary = build_summary(compile_ok, arith_rows, layout_rows)
    write_csv(ARITH_CSV, arith_rows, ARITH_FIELDS)
    write_csv(LAYOUT_CSV, layout_rows, LAYOUT_FIELDS)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(arith_rows, layout_rows)
    write_md(summary, arith_rows, layout_rows)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                ARITH_CSV,
                LAYOUT_CSV,
                COMPILE_LOG,
                C_SOURCE,
                ROOT / "scripts" / "build_stage122_structured_ep_arithmetic_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage122 structured EP arithmetic gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
