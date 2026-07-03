#!/usr/bin/env python3
"""Build Stage128 MOSFHET-adjacent compact EP API boundary gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage128_compact_ep_api_boundary_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
API_CSV = OUT_DIR / "api_results.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "compact_ep_api_boundary_gate.c"
C_BINARY = OUT_DIR / "compact_ep_api_boundary_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage128_compact_ep_api_boundary_gate.md"
PLAN_MD = ROOT / "experiments" / "stage128_compact_ep_api_boundary_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage128_compact_ep_api_boundary_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_compact_ep_api_boundary.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


API_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "ownership_failures",
    "metadata_failures",
    "guard_failures",
    "kernel_allocations",
    "component_mismatches",
    "phase_mismatches",
    "noise_model_mismatches",
    "negative_failures",
    "max_component_gap",
    "max_phase_gap",
    "tolerance",
    "dft_term_ratio",
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
        f"gcc -O2 -DSTAGE128_BACKEND=\\\"{backend}\\\" "
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
    api_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "API":
            api_rows.append(dict(zip(API_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    cleanup_build_outputs()
    return api_rows, proc.returncode == 0


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    api_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = [
        {
            "gate": "stage128_mosfhet_static_build",
            "status": "PASS" if build_ok else "BLOCKED",
            "metric": "make_static_spqlios",
            "value": "true" if build_ok else "false",
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build using FFT_LIB=spqlios.",
            "next_action": "Fix production build before interpreting the API boundary.",
        },
        {
            "gate": "stage128_probe_compile",
            "status": "PASS" if compile_ok else "BLOCKED",
            "metric": "gcc_probe_compile",
            "value": "true" if compile_ok else "false",
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone compact EP API boundary probe linked against libmosfhet.a.",
            "next_action": "Fix the probe compile before any API decision.",
        },
    ]
    if not build_ok or not compile_ok:
        rows.append(
            {
                "gate": "stage128_decision",
                "status": "BLOCKED_STAGE128_API_BUILD_OR_COMPILE",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Compact EP API boundary probe did not run.",
                "next_action": "Resolve build/compile failure.",
            }
        )
        return rows

    have_api = run_ok and len(api_rows) > 0
    api_ok = have_api and all(row["status"] == "PASS_COMPACT_EP_API_BOUNDARY" for row in api_rows)
    ownership_values = ";".join(row["ownership_failures"] for row in api_rows)
    metadata_values = ";".join(row["metadata_failures"] for row in api_rows)
    guard_values = ";".join(row["guard_failures"] for row in api_rows)
    allocation_values = ";".join(row["kernel_allocations"] for row in api_rows)
    component_values = ";".join(row["component_mismatches"] for row in api_rows)
    phase_values = ";".join(row["phase_mismatches"] for row in api_rows)
    noise_values = ";".join(row["noise_model_mismatches"] for row in api_rows)
    negative_values = ";".join(row["negative_failures"] for row in api_rows)
    max_component_gap = max([int(row["max_component_gap"]) for row in api_rows] or [0])
    max_phase_gap = max([int(row["max_phase_gap"]) for row in api_rows] or [0])
    tolerance = max([int(row["tolerance"]) for row in api_rows] or [0])
    min_dft_ratio = min([float(row["dft_term_ratio"]) for row in api_rows] or [0.0])
    min_total_ratio = min([float(row["total_term_ratio"]) for row in api_rows] or [0.0])
    rows.extend(
        [
            {
                "gate": "stage128_probe_run",
                "status": "PASS" if run_ok else "FAIL",
                "metric": "probe_returncode",
                "value": "0" if run_ok else "nonzero",
                "evidence": rel(RUN_LOG_TXT),
                "detail": "Compact EP API boundary probe executed.",
                "next_action": "Inspect run log on failure.",
            },
            {
                "gate": "stage128_api_ownership_metadata",
                "status": "PASS" if api_ok else "FAIL",
                "metric": "ownership_failures;metadata_failures;guard_failures",
                "value": f"{ownership_values};{metadata_values};{guard_values}",
                "evidence": rel(API_CSV),
                "detail": "Selector/output/scratch ownership, metadata, and invalid-lane guards are valid.",
                "next_action": "Fix API lifecycle before microbench or production code.",
            },
            {
                "gate": "stage128_no_allocation_hot_kernel",
                "status": "PASS" if api_ok else "FAIL",
                "metric": "kernel_allocations",
                "value": allocation_values,
                "evidence": rel(API_CSV),
                "detail": "Kernel API uses caller-provided scratch and performs no API-owned allocations in the hot call.",
                "next_action": "If this fails, redesign scratch ownership.",
            },
            {
                "gate": "stage128_api_kernel_equivalence",
                "status": "PASS_WITH_TOLERANCE" if api_ok and max_component_gap <= tolerance and max_phase_gap <= tolerance else "FAIL",
                "metric": "component_mismatches;phase_mismatches;noise_model_mismatches;max_gaps;tolerance",
                "value": f"{component_values};{phase_values};{noise_values};{max_component_gap};{max_phase_gap};{tolerance}",
                "evidence": rel(API_CSV),
                "detail": "API-boundary kernel preserves component, phase, and modeled-noise equivalence.",
                "next_action": "If this fails, do not implement production API.",
            },
            {
                "gate": "stage128_negative_control",
                "status": "PASS_REJECTS_BODY_ONLY_API" if api_ok else "FAIL",
                "metric": "negative_failures",
                "value": negative_values,
                "evidence": rel(API_CSV),
                "detail": "Body-only API kernel remains rejected.",
                "next_action": "Do not expose body-only compact EP as a valid API.",
            },
            {
                "gate": "stage128_complexity_model",
                "status": "PASS" if api_ok and min_dft_ratio > 1.0 and min_total_ratio >= 1.0 else "FAIL",
                "metric": "min_dft_term_ratio;min_total_term_ratio",
                "value": f"{min_dft_ratio:.6f};{min_total_ratio:.6f}",
                "evidence": rel(API_CSV),
                "detail": "API boundary preserves the isolated kernel count model.",
                "next_action": "Stage129 may run isolated microbench/profiling after this passes.",
            },
            {
                "gate": "stage128_decision",
                "status": (
                    "PASS_STAGE128_COMPACT_EP_API_BOUNDARY_READY_MICROBENCH_REQUIRED"
                    if api_ok
                    else "FAIL_STAGE128_COMPACT_EP_API_BOUNDARY"
                ),
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "MOSFHET-adjacent compact EP API boundary passes outside `sab_pvw_*`.",
                "next_action": "Stage129 should run isolated microbench/profiling before production integration.",
            },
        ]
    )
    return rows


def write_plan() -> None:
    lines = [
        "# Stage128 Compact EP API Boundary Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Wrap the Stage127 isolated compact EP kernel in MOSFHET-adjacent API",
        "shapes for selector, output, and scratch ownership. This remains a",
        "standalone generated probe and does not modify production headers.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage128_compact_ep_api_boundary_gate.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- MOSFHET build or probe compile fails;",
        "- API-owned polynomial buffers are null, aliased, or leaked;",
        "- metadata or invalid-lane guards fail;",
        "- the hot kernel allocates instead of using caller scratch;",
        "- API-bound kernel loses Stage127 component/phase/noise equivalence;",
        "- body-only API kernel does not fail.",
        "",
        "Passing this stage permits isolated microbench/profiling only; it still",
        "does not permit SAB hot-path integration.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(api_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage128 Compact EP API Boundary Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage128 defines MOSFHET-adjacent API shapes around the Stage127 isolated",
        "kernel:",
        "",
        "```text",
        "CompactEpSelectorDft",
        "CompactEpOutputDft",
        "CompactEpScratch",
        "compact_ep_selector_set_row_from_torus(...)",
        "compact_ep_kernel_dft_api(...)",
        "```",
        "",
        "The gate checks ownership, metadata, invalid-lane rejection, no API-owned",
        "allocation inside the hot kernel, and the same component/phase/noise",
        "equivalence as Stage127.",
        "",
        "## API Rows",
        "",
        "| backend | r | N | seed | ownership | metadata | guards | kernel allocs | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | DFT ratio | total ratio | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in api_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['ownership_failures']} | {row['metadata_failures']} | "
            f"{row['guard_failures']} | {row['kernel_allocations']} | "
            f"{row['component_mismatches']} | {row['phase_mismatches']} | "
            f"{row['noise_model_mismatches']} | {row['negative_failures']} | "
            f"{row['max_component_gap']} | {row['max_phase_gap']} | "
            f"{row['dft_term_ratio']} | {row['total_term_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This is not a production MOSFHET header change, AVX512 specialization,",
        "randomized noise/failure-rate proof, SAB schedule integration, or complete",
        "`T_bootstrap/r` benchmark.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V128: Compact EP API Boundary",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: MOSFHET-adjacent compact EP API boundary.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[api-boundary]`, `[production-dft-linked]`, `[not-production-header]`, `[not-hot-path]`.",
        "- Main hypothesis: the isolated compact EP kernel can be wrapped in explicit selector/output/scratch ownership without losing correctness or count invariants.",
        "",
        "## API Shape",
        "",
        "```text",
        "CompactEpSelectorDft compact_ep_selector_dft_alloc(T, Bg_bit, k, r, N)",
        "CompactEpOutputDft   compact_ep_output_dft_alloc(N)",
        "CompactEpScratch     compact_ep_scratch_alloc(N)",
        "int compact_ep_selector_set_row_from_torus(selector, t, q, rows...)",
        "int compact_ep_kernel_dft_api(out, source_shared, source_body, selector, q, scratch)",
        "```",
        "",
        "## Required Next Gate",
        "",
        "Stage129 should benchmark the isolated API-shaped kernel and attribute",
        "time to decomposition, torus-to-DFT conversion, and DFT multiply-add before",
        "any production MOSFHET or SAB integration.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], api_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage128 Compact EP API Boundary Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage128 wraps the isolated compact EP kernel in MOSFHET-adjacent",
        "selector/output/scratch API shapes. It remains a standalone generated",
        "probe outside production headers and `sab_pvw_*`.",
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
        "## API Rows",
        "",
        "| backend | r | N | seed | ownership | metadata | guards | kernel allocs | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | DFT ratio | total ratio | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in api_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['ownership_failures']} | {row['metadata_failures']} | "
            f"{row['guard_failures']} | {row['kernel_allocations']} | "
            f"{row['component_mismatches']} | {row['phase_mismatches']} | "
            f"{row['noise_model_mismatches']} | {row['negative_failures']} | "
            f"{row['max_component_gap']} | {row['max_phase_gap']} | "
            f"{row['dft_term_ratio']} | {row['total_term_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The compact EP kernel now has an API-shaped ownership and scratch boundary",
        "suitable for isolated microbench/profiling. It still has not been added to",
        "MOSFHET production headers or integrated into SAB.",
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
    run_id = "stage128-compact-ep-api-boundary-001"
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != run_id]
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        API_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path("scripts/build_stage128_compact_ep_api_boundary_gate.py"),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 128",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage128_compact_ep_api_boundary_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024",
            "seed": "0..1 subset",
            "status": status,
            "summary": "Stage128 validates MOSFHET-adjacent compact EP API ownership/scratch boundary outside SAB.",
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
    api_rows, run_ok = run_probe(build_ok, compile_ok)
    write_csv(API_CSV, api_rows, API_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, api_rows)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_plan()
    write_theory(api_rows)
    write_variant()
    write_md(summary, api_rows)
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        API_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        Path(__file__),
    ]
    write_artifact_index(artifacts)
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage128 compact EP API boundary gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
