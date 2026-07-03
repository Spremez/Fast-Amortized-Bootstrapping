#!/usr/bin/env python3
"""Build Stage123 production MOSFHET torus/FFT smoke gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage123_production_fft_smoke_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
SMOKE_CSV = OUT_DIR / "smoke_results.csv"
LAYOUT_CSV = OUT_DIR / "layout_results.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "production_fft_smoke_gate.c"
C_BINARY = OUT_DIR / "production_fft_smoke_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage123_production_fft_smoke_gate.md"
PLAN_MD = ROOT / "experiments" / "stage123_production_fft_smoke_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage123_production_fft_smoke_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_vector_shared_production_fft_smoke.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


SMOKE_FIELDS = [
    "backend",
    "r",
    "N",
    "seed",
    "tolerance",
    "coeff_expected_mismatches",
    "dft_coeff_mismatches",
    "noisy_dft_coeff_mismatches",
    "negative_control_failures",
    "max_coeff_expected_gap",
    "max_dft_coeff_gap",
    "max_noisy_dft_coeff_gap",
    "structured_terms",
    "status",
]

LAYOUT_FIELDS = [
    "r",
    "N",
    "dense_ep_terms",
    "structured_ep_terms",
    "ep_term_ratio",
    "smoke_scope",
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
        f"gcc -O2 -DSTAGE123_BACKEND=\\\"{backend}\\\" "
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


def run_probe(build_ok: bool, compile_ok: bool) -> tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
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
    smoke_rows: List[Dict[str, str]] = []
    layout_rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        tag = values[0]
        if tag == "SMOKE":
            smoke_rows.append(dict(zip(SMOKE_FIELDS, values[1:])))
        elif tag == "LAYOUT":
            layout_rows.append(dict(zip(LAYOUT_FIELDS, values[1:])))
        else:
            raise RuntimeError(f"unexpected probe row: {line}")
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)
    return smoke_rows, layout_rows, proc.returncode == 0


def build_summary(
    build_ok: bool,
    compile_ok: bool,
    run_ok: bool,
    smoke_rows: List[Dict[str, str]],
    layout_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = [
        {
            "gate": "stage123_mosfhet_static_build",
            "status": "PASS" if build_ok else "BLOCKED",
            "metric": "make_static_spqlios",
            "value": "true" if build_ok else "false",
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build using FFT_LIB=spqlios.",
            "next_action": "Fix production build before any smoke interpretation.",
        },
        {
            "gate": "stage123_probe_compile",
            "status": "PASS" if compile_ok else "BLOCKED",
            "metric": "gcc_probe_compile",
            "value": "true" if compile_ok else "false",
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone structured EP smoke probe linked against libmosfhet.a.",
            "next_action": "Fix the standalone probe before any smoke interpretation.",
        },
    ]
    if not build_ok or not compile_ok:
        rows.append(
            {
                "gate": "stage123_decision",
                "status": "BLOCKED_STAGE123_PRODUCTION_FFT_BUILD_OR_COMPILE",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Production FFT smoke did not run.",
                "next_action": "Resolve build/compile failure.",
            }
        )
        return rows

    have_smoke = run_ok and len(smoke_rows) > 0
    coeff_ok = have_smoke and all(int(row["coeff_expected_mismatches"]) == 0 for row in smoke_rows)
    dft_ok = have_smoke and all(int(row["dft_coeff_mismatches"]) == 0 for row in smoke_rows)
    noisy_ok = have_smoke and all(int(row["noisy_dft_coeff_mismatches"]) == 0 for row in smoke_rows)
    negative_ok = have_smoke and all(int(row["negative_control_failures"]) > 0 for row in smoke_rows)
    smoke_ok = coeff_ok and dft_ok and noisy_ok and negative_ok
    layout_ok = len(layout_rows) > 0 and all(row["status"] == "PASS_LAYOUT" for row in layout_rows)
    coeff_values = ";".join(row["coeff_expected_mismatches"] for row in smoke_rows)
    dft_values = ";".join(row["dft_coeff_mismatches"] for row in smoke_rows)
    noisy_values = ";".join(row["noisy_dft_coeff_mismatches"] for row in smoke_rows)
    negative_values = ";".join(row["negative_control_failures"] for row in smoke_rows)
    max_gap = max([int(row["max_dft_coeff_gap"]) for row in smoke_rows] or [0])
    max_noisy_gap = max([int(row["max_noisy_dft_coeff_gap"]) for row in smoke_rows] or [0])
    tolerance = max([int(row["tolerance"]) for row in smoke_rows] or [0])
    min_ratio = min([float(row["ep_term_ratio"]) for row in layout_rows] or [0.0])
    rows.extend(
        [
            {
                "gate": "stage123_probe_run",
                "status": "PASS" if run_ok else "FAIL",
                "metric": "probe_returncode",
                "value": "0" if run_ok else "nonzero",
                "evidence": rel(RUN_LOG_TXT),
                "detail": "Production FFT smoke probe executed.",
                "next_action": "Inspect run log on failure.",
            },
            {
                "gate": "stage123_coeff_reference",
                "status": "PASS" if coeff_ok else "FAIL",
                "metric": "coeff_expected_mismatches",
                "value": coeff_values,
                "evidence": rel(SMOKE_CSV),
                "detail": "Coefficient-domain structured EP phase matches dense message-reference phase exactly.",
                "next_action": "Fix coefficient structured EP before production FFT work if this fails.",
            },
            {
                "gate": "stage123_production_fft_boundary",
                "status": "PASS_WITH_TOLERANCE" if dft_ok and max_gap <= tolerance else "FAIL",
                "metric": "dft_coeff_mismatches;max_gap;tolerance",
                "value": f"{dft_values};{max_gap};{tolerance}",
                "evidence": rel(SMOKE_CSV),
                "detail": "Production SPQLIOS DFT multiply-add structured EP matches coefficient EP within tolerance.",
                "next_action": "If this fails, inspect torus scaling/roundoff before MOSFHET-adjacent types.",
            },
            {
                "gate": "stage123_noisy_fft_boundary",
                "status": "PASS_WITH_TOLERANCE" if noisy_ok and max_noisy_gap <= tolerance else "FAIL",
                "metric": "noisy_dft_coeff_mismatches;max_gap;tolerance",
                "value": f"{noisy_values};{max_noisy_gap};{tolerance}",
                "evidence": rel(SMOKE_CSV),
                "detail": "Noisy structured EP also crosses production FFT within tolerance.",
                "next_action": "Production cryptographic noise still requires later parameter gates.",
            },
            {
                "gate": "stage123_negative_control",
                "status": "PASS_REJECTS_BODY_ONLY_SKIP"
                if negative_ok
                else "FAIL",
                "metric": "negative_control_failures",
                "value": negative_values,
                "evidence": rel(SMOKE_CSV),
                "detail": "Body-only off-lane skip remains rejected under the production smoke model.",
                "next_action": "Do not implement current-format body-only skipping.",
            },
            {
                "gate": "stage123_layout_terms",
                "status": "PASS" if layout_ok else "FAIL",
                "metric": "min_ep_term_ratio",
                "value": f"{min_ratio:.6f}",
                "evidence": rel(LAYOUT_CSV),
                "detail": "Smoke scope preserves Stage122 structured term ratios.",
                "next_action": "Key/type resource modeling remains a separate gate.",
            },
            {
                "gate": "stage123_decision",
                "status": (
                    "PASS_STAGE123_PRODUCTION_FFT_SMOKE_READY_MOSFHET_TYPE_SKETCH_REQUIRED"
                    if smoke_ok and layout_ok
                    else "FAIL_STAGE123_PRODUCTION_FFT_SMOKE"
                ),
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(SUMMARY_CSV),
                "detail": "Production FFT smoke passes outside `sab_pvw_*`.",
                "next_action": "Stage124 should sketch MOSFHET-adjacent vector-shared types and API boundaries.",
            },
        ]
    )
    return rows


def write_plan() -> None:
    lines = [
        "# Stage123 Production FFT Smoke Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Move Stage122 structured EP arithmetic across the actual MOSFHET",
        "`TorusPolynomial` and SPQLIOS DFT API boundary. This stage builds",
        "`libmosfhet.a` with `FFT_LIB=spqlios`, compiles a standalone smoke probe,",
        "and compares coefficient-domain structured EP against production",
        "DFT-domain structured EP.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage123_production_fft_smoke_gate.py",
        "```",
        "",
        "## Falsification Criteria",
        "",
        "- MOSFHET static library cannot build with `FFT_LIB=spqlios`;",
        "- standalone probe cannot link against production MOSFHET symbols;",
        "- coefficient structured EP does not match dense message reference;",
        "- production DFT structured EP exceeds the declared tolerance;",
        "- noisy structured EP exceeds the declared tolerance;",
        "- body-only off-lane skip does not fail as a negative control.",
        "",
        "Passing this stage permits only MOSFHET-adjacent type/API sketching",
        "outside `sab_pvw_*`.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(smoke_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage123 Production FFT Smoke Model",
        "",
        "Date: 2026-07-03",
        "",
        "Stage123 is the first vector-shared structured EP gate that links against",
        "the production MOSFHET polynomial and SPQLIOS DFT API. It still uses a",
        "standalone smoke probe, not SAB hot-path integration. The smoke compares",
        "three phases:",
        "",
        "1. dense message-reference phase from active shared/body messages;",
        "2. coefficient-domain structured EP phase using MOSFHET torus",
        "   polynomial multiplication;",
        "3. production DFT-domain structured EP phase using",
        "   `polynomial_torus_to_DFT`, `polynomial_mul_addto_DFT`, and",
        "   `polynomial_DFT_to_torus`.",
        "",
        "DFT comparisons use a fixed 1024 torus-unit tolerance because",
        "production SPQLIOS uses floating-point transforms. This is smoke",
        "evidence, not a noise proof.",
        "",
        "## Smoke Rows",
        "",
        "| backend | r | N | seed | coeff mismatches | DFT mismatches | noisy DFT mismatches | negative failures | max DFT gap | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in smoke_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['coeff_expected_mismatches']} | {row['dft_coeff_mismatches']} | "
            f"{row['noisy_dft_coeff_mismatches']} | {row['negative_control_failures']} | "
            f"{row['max_dft_coeff_gap']} | {row['tolerance']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | dense terms | structured terms | ratio | scope |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_ep_terms']} | "
            f"{row['structured_ep_terms']} | {row['ep_term_ratio']} | "
            f"{row['smoke_scope']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This gate does not define new MOSFHET ciphertext structs, key generation,",
        "gadget decomposition, extraction, key switching, AVX512 optimality, SAB",
        "schedule integration, or complete `T_bootstrap/r` acceleration.",
    ]
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V123: Production FFT Smoke for Vector-Shared Structured EP",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB r-body research track.",
        "- Focused module: production MOSFHET torus/FFT boundary for structured EP.",
        "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
        "- Status labels: `[production-fft-smoke]`, `[not-hot-path]`, `[not-keygen]`, `[not-complete-sab]`.",
        "- Main hypothesis: Stage122 structured EP arithmetic survives the production MOSFHET SPQLIOS DFT boundary within a fixed 1024 torus-unit tolerance.",
        "",
        "## Mathematical Definition",
        "",
        "For each lane q, the smoke constructs active shared/body terms",
        "`D_i * C_i` in coefficient domain and in production DFT domain. It compares",
        "the decrypted phases after inverse transform. The dense reference is the",
        "message-domain phase because clean ciphertexts are constructed as",
        "`body = mask * secret + message`.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "Input: r, N, seed",
        "Output: production FFT smoke status",
        "1. Build libmosfhet.a with FFT_LIB=spqlios.",
        "2. Generate small torus secret, digit, mask, message, and noise polynomials.",
        "3. Build coefficient structured EP output using MOSFHET naive torus multiplication.",
        "4. Build production DFT structured EP output using MOSFHET DFT routines.",
        "5. Convert DFT output to torus and decrypt phases.",
        "6. Compare coefficient phase to message reference exactly.",
        "7. Compare DFT phase to coefficient phase within tolerance.",
        "8. Keep body-only off-lane skipping as a failing negative control.",
        "```",
        "",
        "## Complexity Change",
        "",
        "This smoke does not add a new complexity claim. It preserves Stage122 term",
        "ratios inside a production FFT API test and opens only type/API boundary",
        "sketching.",
        "",
        "## Required Experiments",
        "",
        "- MOSFHET-adjacent vector-shared type/API sketch;",
        "- gadget decomposition compatibility;",
        "- real selector/key construction;",
        "- isolated kernel equivalence;",
        "- full SAB `T_bootstrap/r` only after the above pass.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], smoke_rows: List[Dict[str, str]], layout_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage123 Production FFT Smoke Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage123 links a standalone structured EP smoke probe against the actual",
        "MOSFHET static library built with `FFT_LIB=spqlios`. It remains outside",
        "`sab_pvw_*` and does not change scalar/default behavior.",
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
        "## Smoke Rows",
        "",
        "| backend | r | N | seed | coeff mismatches | DFT mismatches | noisy DFT mismatches | negative failures | max DFT gap | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in smoke_rows:
        lines.append(
            f"| {row['backend']} | {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['coeff_expected_mismatches']} | {row['dft_coeff_mismatches']} | "
            f"{row['noisy_dft_coeff_mismatches']} | {row['negative_control_failures']} | "
            f"{row['max_dft_coeff_gap']} | {row['tolerance']} | {row['status']} |"
        )
    lines += [
        "",
        "## Layout Rows",
        "",
        "| r | N | dense EP | structured EP | ratio | status |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_ep_terms']} | "
            f"{row['structured_ep_terms']} | {row['ep_term_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "This removes the production FFT smoke blocker for small structured EP",
        "instances. It still does not prove a new MOSFHET type, real selector/key",
        "generation, gadget decomposition, AVX512 optimality, SAB schedule",
        "integration, or complete-SAB speedup.",
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
        if row.get("run_id") != "stage123-production-fft-smoke-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(SMOKE_CSV),
        rel(LAYOUT_CSV),
        rel(BUILD_LOG),
        rel(COMPILE_LOG),
        rel(RUN_LOG_TXT),
        rel(C_SOURCE),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage123_production_fft_smoke_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage123-production-fft-smoke-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 123",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage123_production_fft_smoke_gate.py",
            "params": "structured EP smoke r=2,4,6 N=1024 plus r=2 N=2048 seeds listed in smoke_results.csv",
            "seed": "0..1 subset",
            "status": status,
            "summary": "Stage123 validates structured EP across MOSFHET TorusPolynomial/SPQLIOS DFT smoke boundary outside SAB.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    write_plan()
    write_variant()
    write_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    smoke_rows, layout_rows, run_ok = run_probe(build_ok, compile_ok)
    summary = build_summary(build_ok, compile_ok, run_ok, smoke_rows, layout_rows)
    write_csv(SMOKE_CSV, smoke_rows, SMOKE_FIELDS)
    write_csv(LAYOUT_CSV, layout_rows, LAYOUT_FIELDS)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(smoke_rows, layout_rows)
    write_md(summary, smoke_rows, layout_rows)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                SMOKE_CSV,
                LAYOUT_CSV,
                BUILD_LOG,
                COMPILE_LOG,
                RUN_LOG_TXT,
                C_SOURCE,
                ROOT / "scripts" / "build_stage123_production_fft_smoke_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage123 production FFT smoke gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
