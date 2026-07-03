#!/usr/bin/env python3
"""Build Stage127 isolated compact external-product kernel gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage127_isolated_compact_ep_kernel_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
KERNEL_CSV = OUT_DIR / "kernel_results.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "isolated_compact_ep_kernel_gate.c"
C_BINARY = OUT_DIR / "isolated_compact_ep_kernel_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage127_isolated_compact_ep_kernel_gate.md"
PLAN_MD = ROOT / "experiments" / "stage127_isolated_compact_ep_kernel_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage127_isolated_compact_ep_kernel_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_isolated_compact_ep_kernel.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


KERNEL_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "component_mismatches",
    "phase_mismatches",
    "noise_model_mismatches",
    "negative_failures",
    "max_component_gap",
    "max_phase_gap",
    "tolerance",
    "dense_dft_terms",
    "compact_dft_terms",
    "dft_term_ratio",
    "dense_total_terms",
    "compact_total_terms",
    "total_term_ratio",
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
'''
    write_text_lf(C_SOURCE, source.lstrip())


def build_mosfhet_static(backend: str) -> bool:
    cmd = (
        "cd src/mosfhet && "
        "make clean >/dev/null 2>&1 || true && "
        f"make static FFT_LIB={backend} A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=false -j$(nproc)"
    )
    proc = bash(cmd, timeout=180)
    log = [
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(BUILD_LOG, "\n".join(log) + "\n")
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE127_BACKEND=\\\"{backend}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
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


def cleanup_build_outputs() -> None:
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)


def run_probe(build_ok: bool, compile_ok: bool) -> tuple[List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=120)
    log = [
        f"command: ./{rel(C_BINARY)}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize_log(proc.stdout),
        "--- stderr ---",
        sanitize_log(proc.stderr),
    ]
    write_text_lf(RUN_LOG_TXT, "\n".join(log) + "\n")
    kernel_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "KERNEL":
            kernel_rows.append(dict(zip(KERNEL_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    cleanup_build_outputs()
    return kernel_rows, proc.returncode == 0


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    kernel_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = [
        {
            "gate": "stage127_mosfhet_static_build",
            "status": "PASS" if build_ok else "BLOCKED",
            "metric": "make_static_spqlios",
            "value": "true" if build_ok else "false",
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build using FFT_LIB=spqlios.",
            "next_action": "Fix production build before interpreting the isolated kernel.",
        },
        {
            "gate": "stage127_probe_compile",
            "status": "PASS" if compile_ok else "BLOCKED",
            "metric": "gcc_probe_compile",
            "value": "true" if compile_ok else "false",
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone isolated compact EP kernel probe linked against libmosfhet.a.",
            "next_action": "Fix the probe compile before any kernel decision.",
        },
    ]
    if not build_ok or not compile_ok:
        rows.append(
            {
                "gate": "stage127_decision",
                "status": "BLOCKED_STAGE127_KERNEL_BUILD_OR_COMPILE",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Isolated compact EP kernel probe did not run.",
                "next_action": "Resolve build/compile failure.",
            }
        )
        return rows

    have_kernel = run_ok and len(kernel_rows) > 0
    kernel_ok = have_kernel and all(row["status"] == "PASS_ISOLATED_COMPACT_EP_KERNEL" for row in kernel_rows)
    component_values = ";".join(row["component_mismatches"] for row in kernel_rows)
    phase_values = ";".join(row["phase_mismatches"] for row in kernel_rows)
    noise_values = ";".join(row["noise_model_mismatches"] for row in kernel_rows)
    negative_values = ";".join(row["negative_failures"] for row in kernel_rows)
    max_component_gap = max([int(row["max_component_gap"]) for row in kernel_rows] or [0])
    max_phase_gap = max([int(row["max_phase_gap"]) for row in kernel_rows] or [0])
    tolerance = max([int(row["tolerance"]) for row in kernel_rows] or [0])
    min_dft_ratio = min([float(row["dft_term_ratio"]) for row in kernel_rows] or [0.0])
    min_total_ratio = min([float(row["total_term_ratio"]) for row in kernel_rows] or [0.0])
    rows.extend(
        [
            {
                "gate": "stage127_probe_run",
                "status": "PASS" if run_ok else "FAIL",
                "metric": "probe_returncode",
                "value": "0" if run_ok else "nonzero",
                "evidence": rel(RUN_LOG_TXT),
                "detail": "Isolated compact EP kernel probe executed.",
                "next_action": "Inspect run log on failure.",
            },
            {
                "gate": "stage127_kernel_component_equivalence",
                "status": "PASS_WITH_TOLERANCE" if kernel_ok and max_component_gap <= tolerance else "FAIL",
                "metric": "component_mismatches;max_component_gap;tolerance",
                "value": f"{component_values};{max_component_gap};{tolerance}",
                "evidence": rel(KERNEL_CSV),
                "detail": "DFT compact kernel output components match coefficient reference within tolerance.",
                "next_action": "If this fails, fix kernel decomposition/conversion before API work.",
            },
            {
                "gate": "stage127_kernel_phase_noise",
                "status": "PASS_WITH_TOLERANCE" if kernel_ok and max_phase_gap <= tolerance else "FAIL",
                "metric": "phase_mismatches;noise_model_mismatches;max_phase_gap;tolerance",
                "value": f"{phase_values};{noise_values};{max_phase_gap};{tolerance}",
                "evidence": rel(KERNEL_CSV),
                "detail": "DFT compact kernel phase equals modeled noisy reference while coefficient noise model remains exact.",
                "next_action": "If this fails, do not promote the isolated kernel.",
            },
            {
                "gate": "stage127_negative_control",
                "status": "PASS_REJECTS_BODY_ONLY_KERNEL" if kernel_ok else "FAIL",
                "metric": "negative_failures",
                "value": negative_values,
                "evidence": rel(KERNEL_CSV),
                "detail": "Body-only compact EP kernel remains rejected.",
                "next_action": "Do not implement body-only compact EP.",
            },
            {
                "gate": "stage127_complexity_model",
                "status": "PASS" if kernel_ok and min_dft_ratio > 1.0 and min_total_ratio >= 1.0 else "FAIL",
                "metric": "min_dft_term_ratio;min_total_term_ratio",
                "value": f"{min_dft_ratio:.6f};{min_total_ratio:.6f}",
                "evidence": rel(KERNEL_CSV),
                "detail": "Isolated compact EP kernel preserves positive DFT-term ratio and non-negative total-term ratio.",
                "next_action": "Stage128 may define MOSFHET-adjacent API only after this gate passes.",
            },
            {
                "gate": "stage127_decision",
                "status": (
                    "PASS_STAGE127_ISOLATED_COMPACT_EP_KERNEL_READY_API_BOUNDARY_REQUIRED"
                    if kernel_ok
                    else "FAIL_STAGE127_ISOLATED_COMPACT_EP_KERNEL"
                ),
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Reusable isolated compact EP DFT kernel passes outside `sab_pvw_*`.",
                "next_action": "Stage128 should define a MOSFHET-adjacent compact EP API boundary, still outside SAB.",
            },
        ]
    )
    return rows


def write_plan() -> None:
    lines = [
        "# Stage127 Isolated Compact EP Kernel Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Turn the Stage126 compact selector encryption/noise semantics into a",
        "reusable isolated DFT external-product kernel with explicit scratch,",
        "without modifying MOSFHET headers or `sab_pvw_*`.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage127_isolated_compact_ep_kernel_gate.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- MOSFHET build or probe compile fails;",
        "- kernel DFT components diverge from coefficient reference beyond tolerance;",
        "- kernel phase fails to match the modeled noisy reference;",
        "- body-only kernel does not fail as a negative control;",
        "- compact DFT-term ratio is not positive or total-term ratio falls below 1.0.",
        "",
        "Passing this stage permits only a MOSFHET-adjacent compact EP API boundary",
        "stage, not SAB hot-path integration.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(kernel_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage127 Isolated Compact EP Kernel Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage127 factors Stage126's inline external-product computation into a",
        "reusable isolated DFT kernel:",
        "",
        "```text",
        "compact_ep_kernel_dft(out_a, out_b, source_shared_q, source_body_q, selector, q, scratch)",
        "```",
        "",
        "For each lane q and gadget level t, the kernel decomposes the lane-local",
        "shared/body source polynomials, converts those digits to DFT, and applies",
        "the compact selector rows `shared[t,q]` and `body[t,q]`. It compares output",
        "components with a coefficient reference and compares decrypted phase with",
        "the modeled noisy reference.",
        "",
        "## Kernel Rows",
        "",
        "| backend | r | N | seed | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | DFT ratio | total ratio | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in kernel_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['component_mismatches']} | {row['phase_mismatches']} | "
            f"{row['noise_model_mismatches']} | {row['negative_failures']} | "
            f"{row['max_component_gap']} | {row['max_phase_gap']} | "
            f"{row['dft_term_ratio']} | {row['total_term_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This is still an isolated generated probe. It does not add production",
        "MOSFHET structs, AVX512 specialization, SAB schedule integration,",
        "multi-seed randomized failure-rate evidence, or complete `T_bootstrap/r`",
        "performance.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V127: Isolated Compact External-Product Kernel",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: isolated compact external-product kernel.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[isolated-kernel]`, `[production-dft-linked]`, `[not-api]`, `[not-hot-path]`.",
        "- Main hypothesis: Stage126 compact selector encryption/noise semantics can be factored into a reusable DFT kernel without losing phase/noise correctness or the count model.",
        "",
        "## Mathematical Definition",
        "",
        "For lane q, the compact EP kernel computes:",
        "",
        "```text",
        "Out_q = sum_t D_shared[t,q] * C_shared[t,q] + D_body[t,q] * C_body[t,q]",
        "```",
        "",
        "where `D_*` are decomposed lane-local source digits and `C_*` are compact",
        "encrypted selector rows.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "Input: source_shared_q, source_body_q, compact selector rows",
        "Output: DFT mask/body output for lane q",
        "for t in 0..T-1:",
        "  dec_shared = decompose(source_shared_q, t)",
        "  dec_body   = decompose(source_body_q, t)",
        "  out_a += DFT(dec_shared) * shared_a[t,q]",
        "  out_b += DFT(dec_shared) * shared_b[t,q]",
        "  out_a += DFT(dec_body) * body_a[t,q]",
        "  out_b += DFT(dec_body) * body_b[t,q]",
        "```",
        "",
        "## Required Next Gate",
        "",
        "Stage128 should define MOSFHET-adjacent structs/function signatures and",
        "compile-check API ownership around this kernel. SAB integration remains",
        "blocked until API, multi-seed noise, and isolated microbench gates pass.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], kernel_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage127 Isolated Compact EP Kernel Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage127 factors compact selector external product into a reusable",
        "`compact_ep_kernel_dft` in a standalone generated C probe. It remains",
        "outside MOSFHET production headers and `sab_pvw_*`.",
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
        "## Kernel Rows",
        "",
        "| backend | r | N | seed | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | DFT ratio | total ratio | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in kernel_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['component_mismatches']} | {row['phase_mismatches']} | "
            f"{row['noise_model_mismatches']} | {row['negative_failures']} | "
            f"{row['max_component_gap']} | {row['max_phase_gap']} | "
            f"{row['dft_term_ratio']} | {row['total_term_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The compact EP arithmetic has now been isolated behind a reusable kernel",
        "shape. The result is still a generated probe, so the next step is an API",
        "boundary stage before any production MOSFHET or SAB hot-path changes.",
    ]
    write_text_lf(OUT_MD, "\n".join(lines) + "\n")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


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
    run_id = "stage127-isolated-compact-ep-kernel-001"
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != run_id]
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        KERNEL_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path("scripts/build_stage127_isolated_compact_ep_kernel_gate.py"),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 127",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage127_isolated_compact_ep_kernel_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024",
            "seed": "0..1 subset",
            "status": status,
            "summary": "Stage127 validates a reusable isolated compact EP DFT kernel outside SAB.",
            "artifacts": "; ".join(rel(p if p.is_absolute() else ROOT / p) for p in artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    write_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    kernel_rows, run_ok = run_probe(build_ok, compile_ok)
    write_csv(KERNEL_CSV, kernel_rows, KERNEL_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, kernel_rows)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_plan()
    write_theory(kernel_rows)
    write_variant()
    write_md(summary, kernel_rows)
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        KERNEL_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        Path(__file__),
    ]
    write_artifact_index(artifacts)
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage127 isolated compact EP kernel gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
