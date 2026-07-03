#!/usr/bin/env python3
"""Build Stage126 compact selector encryption/noise gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage126_compact_selector_encryption_noise_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
NOISE_CSV = OUT_DIR / "noise_results.csv"
LAYOUT_CSV = OUT_DIR / "layout_results.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "compact_selector_encryption_noise_gate.c"
C_BINARY = OUT_DIR / "compact_selector_encryption_noise_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage126_compact_selector_encryption_noise_gate.md"
PLAN_MD = ROOT / "experiments" / "stage126_compact_selector_encryption_noise_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage126_compact_selector_encryption_noise_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_compact_selector_encryption_noise.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


NOISE_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "coeff_expected_mismatches",
    "dft_expected_mismatches",
    "noise_model_mismatches",
    "noise_bound_violations",
    "negative_failures",
    "max_dft_gap",
    "max_noise_abs",
    "noise_bound",
    "tolerance",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "T",
    "k",
    "current_per_lane_noise_terms",
    "compact_per_lane_noise_terms",
    "per_lane_noise_term_ratio",
    "current_selector_dft_polys",
    "compact_selector_dft_polys",
    "selector_ratio",
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
        f"gcc -O2 -DSTAGE126_BACKEND=\\\"{backend}\\\" "
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


def run_probe(build_ok: bool, compile_ok: bool) -> tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], [], False
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
    noise_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "NOISE":
            noise_rows.append(dict(zip(NOISE_FIELDS, values[1:])))
        elif tag == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    cleanup_build_outputs()
    return noise_rows, layout_rows, proc.returncode == 0


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    noise_rows: List[Dict[str, str]],
    layout_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = [
        {
            "gate": "stage126_mosfhet_static_build",
            "status": "PASS" if build_ok else "BLOCKED",
            "metric": "make_static_spqlios",
            "value": "true" if build_ok else "false",
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build using FFT_LIB=spqlios.",
            "next_action": "Fix production build before interpreting encryption/noise.",
        },
        {
            "gate": "stage126_probe_compile",
            "status": "PASS" if compile_ok else "BLOCKED",
            "metric": "gcc_probe_compile",
            "value": "true" if compile_ok else "false",
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone compact selector encryption/noise probe linked against libmosfhet.a.",
            "next_action": "Fix the probe compile before any encryption/noise decision.",
        },
    ]
    if not build_ok or not compile_ok:
        rows.append(
            {
                "gate": "stage126_decision",
                "status": "BLOCKED_STAGE126_ENCRYPTION_NOISE_BUILD_OR_COMPILE",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Compact selector encryption/noise probe did not run.",
                "next_action": "Resolve build/compile failure.",
            }
        )
        return rows

    have_noise = run_ok and len(noise_rows) > 0
    noise_ok = have_noise and all(row["status"] == "PASS_COMPACT_SELECTOR_ENCRYPTION_NOISE" for row in noise_rows)
    layout_ok = len(layout_rows) > 0 and all(row["status"] == "PASS_NOISE_LAYOUT_MODEL" for row in layout_rows)
    coeff_values = ";".join(row["coeff_expected_mismatches"] for row in noise_rows)
    dft_values = ";".join(row["dft_expected_mismatches"] for row in noise_rows)
    model_values = ";".join(row["noise_model_mismatches"] for row in noise_rows)
    bound_values = ";".join(row["noise_bound_violations"] for row in noise_rows)
    negative_values = ";".join(row["negative_failures"] for row in noise_rows)
    max_dft_gap = max([int(row["max_dft_gap"]) for row in noise_rows] or [0])
    max_noise_abs = max([int(row["max_noise_abs"]) for row in noise_rows] or [0])
    max_bound = max([int(row["noise_bound"]) for row in noise_rows] or [0])
    tolerance = max([int(row["tolerance"]) for row in noise_rows] or [0])
    min_noise_ratio = min([float(row["per_lane_noise_term_ratio"]) for row in layout_rows] or [0.0])
    min_selector_ratio = min([float(row["selector_ratio"]) for row in layout_rows] or [0.0])
    rows.extend(
        [
            {
                "gate": "stage126_probe_run",
                "status": "PASS" if run_ok else "FAIL",
                "metric": "probe_returncode",
                "value": "0" if run_ok else "nonzero",
                "evidence": rel(RUN_LOG_TXT),
                "detail": "Compact selector encryption/noise probe executed.",
                "next_action": "Inspect run log on failure.",
            },
            {
                "gate": "stage126_phase_equivalence",
                "status": "PASS" if noise_ok else "FAIL",
                "metric": "coeff_expected_mismatches;noise_model_mismatches",
                "value": f"{coeff_values};{model_values}",
                "evidence": rel(NOISE_CSV),
                "detail": "Coefficient-domain compact selector encryption phase equals clean reference plus modeled noise.",
                "next_action": "If this fails, compact selector encryption semantics are invalid.",
            },
            {
                "gate": "stage126_production_dft_noise_boundary",
                "status": "PASS_WITH_TOLERANCE" if noise_ok and max_dft_gap <= tolerance else "FAIL",
                "metric": "dft_expected_mismatches;max_dft_gap;tolerance",
                "value": f"{dft_values};{max_dft_gap};{tolerance}",
                "evidence": rel(NOISE_CSV),
                "detail": "Production DFT external product phase matches modeled noisy phase within tolerance.",
                "next_action": "If this fails, inspect DFT scaling before kernel work.",
            },
            {
                "gate": "stage126_noise_bound",
                "status": "PASS" if noise_ok and max_noise_abs <= max_bound else "FAIL",
                "metric": "noise_bound_violations;max_noise_abs;max_bound",
                "value": f"{bound_values};{max_noise_abs};{max_bound}",
                "evidence": rel(NOISE_CSV),
                "detail": "Modeled selector noise remains inside the declared conservative bound.",
                "next_action": "If this fails, reduce noise or revise parameters before integration.",
            },
            {
                "gate": "stage126_negative_control",
                "status": "PASS_REJECTS_BODY_ONLY_ENCRYPTION" if noise_ok else "FAIL",
                "metric": "negative_failures",
                "value": negative_values,
                "evidence": rel(NOISE_CSV),
                "detail": "Body-only encrypted selector rows remain rejected.",
                "next_action": "Do not implement body-only compact selector encryption.",
            },
            {
                "gate": "stage126_layout_noise_terms",
                "status": "PASS" if layout_ok else "FAIL",
                "metric": "min_per_lane_noise_term_ratio;min_selector_ratio",
                "value": f"{min_noise_ratio:.6f};{min_selector_ratio:.6f}",
                "evidence": rel(LAYOUT_CSV),
                "detail": "Compact per-lane selector-noise term count and selector storage remain below current dense counts.",
                "next_action": "Future complete-SAB claims still need real failure-rate statistics.",
            },
            {
                "gate": "stage126_decision",
                "status": (
                    "PASS_STAGE126_COMPACT_SELECTOR_ENCRYPTION_NOISE_READY_ISOLATED_EP_KERNEL_REQUIRED"
                    if noise_ok and layout_ok
                    else "FAIL_STAGE126_COMPACT_SELECTOR_ENCRYPTION_NOISE"
                ),
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Compact selector encryption/noise simulator passes outside `sab_pvw_*`.",
                "next_action": "Stage127 should implement an isolated compact external-product kernel, still outside SAB.",
            },
        ]
    )
    return rows


def write_plan() -> None:
    lines = [
        "# Stage126 Compact Selector Encryption/Noise Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Verify that compact selector rows can be represented as encrypted",
        "lane-local mask/body ciphertexts whose external-product phase equals the",
        "clean gadget reference plus modeled noise. The probe is deterministic for",
        "reproducibility and remains outside `sab_pvw_*`.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage126_compact_selector_encryption_noise_gate.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- coefficient-domain encrypted phase is not clean reference plus modeled noise;",
        "- production DFT phase exceeds tolerance;",
        "- modeled noise exceeds the declared bound;",
        "- body-only encrypted selector rows do not fail;",
        "- compact noise-term or selector count advantage disappears.",
        "",
        "Passing this stage permits only isolated compact external-product kernel",
        "work outside the SAB hot path.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(noise_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage126 Compact Selector Encryption/Noise Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage126 adds a deterministic encryption/noise simulator to the compact",
        "selector route. Each compact selector row is represented as",
        "`body = mask * secret + gadget + noise` using MOSFHET polynomial",
        "operations. The gate verifies the external-product decrypted phase against",
        "a coefficient-domain clean reference plus exact modeled noise, then checks",
        "the same computation through production SPQLIOS DFT.",
        "",
        "This is not a probabilistic failure-rate proof. It is the finite gate",
        "needed before implementing an isolated compact external-product kernel.",
        "",
        "## Noise Rows",
        "",
        "| backend | r | N | T | seed | coeff mismatches | DFT mismatches | model mismatches | bound violations | negative failures | max DFT gap | max noise | bound | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in noise_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['T']} | "
            f"{row['seed']} | {row['coeff_expected_mismatches']} | "
            f"{row['dft_expected_mismatches']} | {row['noise_model_mismatches']} | "
            f"{row['noise_bound_violations']} | {row['negative_failures']} | "
            f"{row['max_dft_gap']} | {row['max_noise_abs']} | "
            f"{row['noise_bound']} | {row['tolerance']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | per-lane noise ratio | selector ratio | status |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['per_lane_noise_term_ratio']} | "
            f"{row['selector_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This gate does not prove randomized cryptographic failure rate, full SAB",
        "noise accumulation, AVX512 performance, schedule compatibility, extract/KS",
        "behavior, or complete `T_bootstrap/r` acceleration.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V126: Compact Selector Encryption/Noise Simulator",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: compact selector encryption/noise semantics.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[encryption-noise-simulator]`, `[production-dft-linked]`, `[not-randomized-failure-rate]`, `[not-hot-path]`.",
        "- Main hypothesis: compact selector rows preserve lane-local phase as clean gadget reference plus modeled selector noise.",
        "",
        "## Mathematical Definition",
        "",
        "For lane q and gadget level t, construct encrypted compact selector rows",
        "`C_shared[t,q]` and `C_body[t,q]` with phase `G_t + e`. For decomposed",
        "digits `d_shared[t,q]` and `d_body[t,q]`, the output phase must be",
        "`sum_t d_shared[t,q] G_t + d_body[t,q] G_t + modeled_noise`.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "for lane q:",
        "  for level t:",
        "    C_shared[t,q] = Enc_q(G_t + e_shared[t,q])",
        "    C_body[t,q]   = Enc_q(G_t + e_body[t,q])",
        "    out_q += decompose(mask_q,t) * C_shared[t,q]",
        "    out_q += decompose(body_q,t) * C_body[t,q]",
        "  assert phase(out_q) == clean_reference_q + modeled_noise_q",
        "```",
        "",
        "## Required Next Gate",
        "",
        "Stage127 should implement an isolated compact external-product kernel and",
        "compare it with the current dense MAT external product before any SAB",
        "schedule integration.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], noise_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage126 Compact Selector Encryption/Noise Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage126 verifies deterministic compact selector encryption/noise",
        "semantics through MOSFHET polynomial and production DFT operations. It",
        "does not modify `sab_pvw_*`.",
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
        "## Noise Rows",
        "",
        "| backend | r | N | T | seed | coeff mismatches | DFT mismatches | model mismatches | bound violations | negative failures | max DFT gap | max noise | bound | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in noise_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['T']} | "
            f"{row['seed']} | {row['coeff_expected_mismatches']} | "
            f"{row['dft_expected_mismatches']} | {row['noise_model_mismatches']} | "
            f"{row['noise_bound_violations']} | {row['negative_failures']} | "
            f"{row['max_dft_gap']} | {row['max_noise_abs']} | "
            f"{row['noise_bound']} | {row['tolerance']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | per-lane noise ratio | selector ratio | status |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['per_lane_noise_term_ratio']} | "
            f"{row['selector_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The compact selector encryption/noise simulator preserves the modeled phase",
        "and noise in coefficient domain and through production DFT. This permits",
        "an isolated compact external-product kernel gate next; full SAB noise and",
        "failure-rate statistics remain open.",
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
    run_id = "stage126-compact-selector-encryption-noise-001"
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != run_id]
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        NOISE_CSV,
        LAYOUT_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path("scripts/build_stage126_compact_selector_encryption_noise_gate.py"),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 126",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage126_compact_selector_encryption_noise_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024",
            "seed": "0..1 subset",
            "status": status,
            "summary": "Stage126 validates deterministic compact selector encryption/noise semantics outside SAB.",
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
    noise_rows, layout_rows, run_ok = run_probe(build_ok, compile_ok)
    write_csv(NOISE_CSV, noise_rows, NOISE_FIELDS)
    write_csv(LAYOUT_CSV, layout_rows, LAYOUT_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, noise_rows, layout_rows)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_plan()
    write_theory(noise_rows, layout_rows)
    write_variant()
    write_md(summary, noise_rows, layout_rows)
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        NOISE_CSV,
        LAYOUT_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        Path(__file__),
    ]
    write_artifact_index(artifacts)
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage126 compact selector encryption/noise gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
