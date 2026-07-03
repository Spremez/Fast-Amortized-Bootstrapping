#!/usr/bin/env python3
"""Build Stage131 shared-source compact EP production API gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage131_shared_source_production_api_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
API_CSV = OUT_DIR / "api_results.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "shared_source_production_api_gate.c"
C_BINARY = OUT_DIR / "shared_source_production_api_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage131_shared_source_production_api_gate.md"
PLAN_MD = ROOT / "experiments" / "stage131_shared_source_production_api_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage131_shared_source_production_api_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_shared_source_production_api.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


API_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "guard_failures",
    "component_mismatches",
    "phase_mismatches",
    "noise_model_mismatches",
    "negative_failures",
    "max_component_gap",
    "max_phase_gap",
    "tolerance",
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

#ifndef STAGE131_BACKEND
#define STAGE131_BACKEND "unknown"
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

static Torus signed_torus(int64_t v) { return (Torus)v; }

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

static void fill_source(TorusPolynomial out, int lane, int kind, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(13100 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static void fill_secret(TorusPolynomial out, int lane, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)(mix64(13200 + (uint64_t)seed,
        (uint64_t)lane, 0, (uint64_t)i) & 1ULL);
  }
}

static void fill_small_mask(TorusPolynomial out, int lane, int t, int kind,
    int seed) {
  for (int i = 0; i < out->N; i++) {
    const int64_t v = (int64_t)(mix64(13300 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)(10 * t + kind), (uint64_t)i) % 3ULL) - 1;
    out->coeffs[i] = signed_torus(v);
  }
}

static void fill_noise(TorusPolynomial out, int lane, int t, int kind,
    int seed) {
  for (int i = 0; i < out->N; i++) {
    const int64_t v = (int64_t)(mix64(13400 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)(10 * t + kind), (uint64_t)i) % 3ULL) - 1;
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

static void compare_poly(TorusPolynomial a, TorusPolynomial b, uint64_t tol,
    uint64_t *mismatches, uint64_t *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const uint64_t gap = abs_gap(a->coeffs[i], b->coeffs[i]);
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void compact_reference(TorusPolynomial out_a, TorusPolynomial out_b,
    PVW_TMLWE in, TorusPolynomial *shared_a, TorusPolynomial *shared_b,
    TorusPolynomial *body_a, TorusPolynomial *body_b, int T, int r, int lane,
    int Bg_bit, MAT_TRGSW_COMPACT_MUL_SCRATCH scratch) {
  zero_poly(out_a);
  zero_poly(out_b);
  for (int t = 0; t < T; t++) {
    const int idx = t * r + lane;
    polynomial_decompose_i(scratch->dec_shared, in->a[0], Bg_bit, T, t);
    polynomial_decompose_i(scratch->dec_body, in->b[lane], Bg_bit, T, t);
    polynomial_naive_mul_addto_torus(out_a, scratch->dec_shared, shared_a[idx]);
    polynomial_naive_mul_addto_torus(out_b, scratch->dec_shared, shared_b[idx]);
    polynomial_naive_mul_addto_torus(out_a, scratch->dec_body, body_a[idx]);
    polynomial_naive_mul_addto_torus(out_b, scratch->dec_body, body_b[idx]);
  }
}

static void run_case(int r, int N, int T, int k, int Bg_bit, int seed) {
  const uint64_t tol = 131072;
  const int rows = T * r;
  const int exp = (seed * 19 + r + 11) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
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

  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(k, r, N);
  PVW_TMLWE neg_in = pvmtmlwe_alloc_new_sample(k, r, N);
  MAT_TRGSW_COMPACT_DFT sel = mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, k, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT out = mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT neg_out = mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch = mat_trgsw_compact_alloc_mul_scratch(N);

  fill_source(in->a[0], 0, 0, seed);
  zero_poly(neg_in->a[0]);
  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(in->b[q], q, 1, seed);
    polynomial_copy_torus_polynomial(neg_in->b[q], in->b[q]);
  }
  for (int t = 0; t < T; t++) {
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    for (int q = 0; q < r; q++) {
      const int idx = t * r + q;
      fill_noise(shared_noise[idx], q, t, 0, seed);
      fill_noise(body_noise[idx], q, t, 1, seed);
      encrypt_row(shared_a[idx], shared_b[idx], secret[q], gadget,
          shared_noise[idx], q, t, 0, seed);
      encrypt_row(body_a[idx], body_b[idx], secret[q], gadget,
          body_noise[idx], q, t, 1, seed);
      mat_trgsw_compact_set_row_from_torus(sel, t, q, shared_a[idx],
          shared_b[idx], body_a[idx], body_b[idx]);
    }
  }

  uint64_t guard_failures = 0;
  if (mat_trgsw_compact_set_row_from_torus(sel, T, 0, shared_a[0], shared_b[0],
      body_a[0], body_b[0]) == 0) guard_failures++;
  if (mat_trgsw_compact_set_row_from_torus(sel, 0, r, shared_a[0], shared_b[0],
      body_a[0], body_b[0]) == 0) guard_failures++;

  mat_trgsw_compact_mul_pvmtmlwe_DFT(out, in, sel, scratch);
  mat_trgsw_compact_mul_pvmtmlwe_DFT(neg_out, neg_in, sel, scratch);

  uint64_t component_mismatches = 0;
  uint64_t phase_mismatches = 0;
  uint64_t noise_model_mismatches = 0;
  uint64_t negative_failures = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_phase_gap = 0;
  uint64_t dummy_gap = 0;

  for (int q = 0; q < r; q++) {
    compact_reference(coeff_a, coeff_b, in, shared_a, shared_b, body_a,
        body_b, T, r, q, Bg_bit, scratch);
    polynomial_DFT_to_torus(out_a_torus, out->a[q]);
    polynomial_DFT_to_torus(out_b_torus, out->b[q]);
    compare_poly(coeff_a, out_a_torus, tol, &component_mismatches,
        &max_component_gap);
    compare_poly(coeff_b, out_b_torus, tol, &component_mismatches,
        &max_component_gap);

    zero_poly(expected_clean);
    zero_poly(expected_noise);
    for (int t = 0; t < T; t++) {
      const int idx = t * r + q;
      make_gadget(gadget, t, Bg_bit, exp, monomial);
      polynomial_decompose_i(scratch->dec_shared, in->a[0], Bg_bit, T, t);
      polynomial_decompose_i(scratch->dec_body, in->b[q], Bg_bit, T, t);
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

    polynomial_DFT_to_torus(neg_a_torus, neg_out->a[q]);
    polynomial_DFT_to_torus(neg_b_torus, neg_out->b[q]);
    phase(neg_phase, neg_a_torus, neg_b_torus, secret[q]);
    compare_poly(neg_phase, expected_noisy, 0, &negative_failures, &dummy_gap);
  }

  const int ok = guard_failures == 0 && component_mismatches == 0 &&
      phase_mismatches == 0 && noise_model_mismatches == 0 &&
      negative_failures > 0;
  printf("PRODAPI,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%s\n",
      STAGE131_BACKEND, r, N, T, k, Bg_bit, seed, guard_failures,
      component_mismatches, phase_mismatches, noise_model_mismatches,
      negative_failures, max_component_gap, max_phase_gap, tol,
      ok ? "PASS_SHARED_SOURCE_PRODUCTION_API" : "FAIL");

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(neg_out);
  free_mat_trgsw_compact_output_DFT(out);
  free_mat_trgsw_compact_DFT(sel);
  free_pvmtmlwe(neg_in);
  free_pvmtmlwe(in);
  free_poly_array_local(secret, r);
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

int main(void) {
  const int k = 1;
  const int T = 7;
  const int Bg_bit = 7;
  run_case(2, 512, T, k, Bg_bit, 0);
  run_case(4, 512, T, k, Bg_bit, 0);
  run_case(6, 512, T, k, Bg_bit, 0);
  run_case(2, 1024, T, k, Bg_bit, 0);
  run_case(4, 1024, T, k, Bg_bit, 0);
  run_case(6, 1024, T, k, Bg_bit, 0);
  return 0;
}
'''
    write_text_lf(C_SOURCE, source.lstrip())


def build_mosfhet_static(backend: str) -> bool:
    cmd = (
        "cd src/mosfhet && make clean >/dev/null 2>&1 || true && "
        f"make static FFT_LIB={backend} A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=true -j$(nproc)"
    )
    proc = bash(cmd, timeout=180)
    write_text_lf(
        BUILD_LOG,
        "\n".join(
            [
                f"command: {cmd}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        )
        + "\n",
    )
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE131_BACKEND=\\\"{backend}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    proc = bash(cmd, timeout=60)
    write_text_lf(
        COMPILE_LOG,
        "\n".join(
            [
                f"command: {cmd}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        )
        + "\n",
    )
    return proc.returncode == 0


def cleanup_build_outputs() -> None:
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)


def parse_stdout(stdout: str) -> List[Dict[str, str]]:
    rows = []
    for line in stdout.splitlines():
        parts = line.strip().split(",")
        if parts and parts[0] == "PRODAPI" and len(parts) == 17:
            rows.append(dict(zip(API_FIELDS, parts[1:])))
    return rows


def run_probe(build_ok: bool, compile_ok: bool) -> Tuple[List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=120)
    write_text_lf(
        RUN_LOG_TXT,
        "\n".join(
            [
                f"command: ./{rel(C_BINARY)}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize_log(proc.stdout),
                "--- stderr ---",
                sanitize_log(proc.stderr),
            ]
        )
        + "\n",
    )
    rows = parse_stdout(proc.stdout)
    cleanup_build_outputs()
    return rows, proc.returncode == 0


def api_pass(rows: List[Dict[str, str]]) -> bool:
    return bool(rows) and all(
        row["status"] == "PASS_SHARED_SOURCE_PRODUCTION_API"
        and row["guard_failures"] == "0"
        and row["component_mismatches"] == "0"
        and row["phase_mismatches"] == "0"
        and row["noise_model_mismatches"] == "0"
        and int(row["negative_failures"]) > 0
        for row in rows
    )


def build_summary(
    build_ok: bool, compile_ok: bool, run_ok: bool, api_rows: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    correctness = api_pass(api_rows)
    decision = (
        "PASS_STAGE131_SHARED_SOURCE_PRODUCTION_API_READY_SAB_INTEGRATION_DESIGN"
        if build_ok and compile_ok and run_ok and correctness
        else "FAIL_STAGE131_SHARED_SOURCE_PRODUCTION_API_GATE"
    )
    max_component = max((int(row["max_component_gap"]) for row in api_rows), default=0)
    max_phase = max((int(row["max_phase_gap"]) for row in api_rows), default=0)
    return [
        {
            "gate": "stage131_mosfhet_static_build",
            "status": "PASS" if build_ok else "FAIL",
            "metric": "make_static_spqlios_enable_pvw",
            "value": str(build_ok).lower(),
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library build includes production compact EP API.",
            "next_action": "",
        },
        {
            "gate": "stage131_probe_compile",
            "status": "PASS" if compile_ok else "FAIL",
            "metric": "public_header_link",
            "value": str(compile_ok).lower(),
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone probe compiles against mosfhet.h and libmosfhet.a.",
            "next_action": "",
        },
        {
            "gate": "stage131_probe_run",
            "status": "PASS" if run_ok else "FAIL",
            "metric": "probe_returncode",
            "value": "0" if run_ok else "nonzero_or_skipped",
            "evidence": rel(RUN_LOG_TXT),
            "detail": "Production API probe executed.",
            "next_action": "",
        },
        {
            "gate": "stage131_public_api_correctness",
            "status": "PASS" if correctness else "FAIL",
            "metric": "rows;max_component_gap;max_phase_gap",
            "value": f"{len(api_rows)};{max_component};{max_phase}",
            "evidence": rel(API_CSV),
            "detail": "Public API preserves component, phase, noise, and negative-control gates.",
            "next_action": "Do not enter SAB integration if this fails.",
        },
        {
            "gate": "stage131_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": f"{rel(SUMMARY_CSV)}; {rel(API_CSV)}",
            "detail": "Stage131 permits SAB integration design only, not full SAB claims.",
            "next_action": "Stage132 should design isolated SAB CMUX integration around this output type.",
        },
    ]


def api_table(rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "| r | N | seed | guards | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['seed']} | {row['guard_failures']} | "
            f"{row['component_mismatches']} | {row['phase_mismatches']} | "
            f"{row['noise_model_mismatches']} | {row['negative_failures']} | "
            f"{row['max_component_gap']} | {row['max_phase_gap']} | {row['status']} |"
        )
    return lines


def write_docs(summary: List[Dict[str, str]], api_rows: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    write_text_lf(
        PLAN_MD,
        "\n".join(
            [
                "# Stage131 Shared-Source Production API Gate Plan",
                "",
                "Date: 2026-07-03",
                "",
                "## Objective",
                "",
                "Move the Stage130 shared-source compact EP shape from generated probe",
                "code into MOSFHET public headers and `mattrgsw.c`, without changing",
                "existing dense MAT or scalar SAB paths.",
                "",
                "## Command",
                "",
                "```bash",
                "python scripts/build_stage131_shared_source_production_api_gate.py",
                "```",
                "",
                "## Falsification Criteria",
                "",
                "- MOSFHET static build fails with `ENABLE_PVW_TMLWE=true`;",
                "- public header compile/link fails;",
                "- component, phase, or noise-model mismatches are nonzero;",
                "- body-only negative control does not fail;",
                "- the result is described as full SAB acceleration.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        THEORY_MD,
        "\n".join(
            [
                "# Stage131 Shared-Source Production API Model",
                "",
                "Date: 2026-07-03",
                "",
                "Stage131 productionizes only the Stage130 evidence boundary. The output",
                "type is `MAT_TRGSW_COMPACT_OUTPUT_DFT`, which stores one mask/body DFT",
                "pair per lane. It intentionally does not claim a true `PVW_TMLWE_DFT`",
                "shared-output mask; that requires a later invariant gate.",
                "",
                "## Public API",
                "",
                "```text",
                "MAT_TRGSW_COMPACT_DFT",
                "MAT_TRGSW_COMPACT_OUTPUT_DFT",
                "MAT_TRGSW_COMPACT_MUL_SCRATCH",
                "mat_trgsw_compact_set_row_from_torus(...)",
                "mat_trgsw_compact_mul_pvmtmlwe_DFT(...)",
                "```",
                "",
                "## Results",
                "",
                *api_table(api_rows),
                "",
                "## Boundary",
                "",
                "This is public API and correctness evidence only. It is not SAB CMUX",
                "integration, complete `T_bootstrap/r`, AVX512 optimality, or a final",
                "paper-level speedup claim.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        VARIANT_MD,
        "\n".join(
            [
                "# V131: Shared-Source Compact EP Production API",
                "",
                "## Summary",
                "",
                "- Parent algorithm: PVW/MAT-SAB r-body research track.",
                "- Focused module: production API/header boundary for shared-source compact EP.",
                "- Optimization target: eventual complete-SAB `T_bootstrap/r`.",
                "- Status labels: `[production-api]`, `[not-sab-integrated]`, `[not-full-bootstrap]`.",
                f"- Decision: `{decision}`.",
                "",
                "## Output Semantics",
                "",
                "The API returns `MAT_TRGSW_COMPACT_OUTPUT_DFT`, one DFT mask/body pair",
                "per lane. Compressing this into a single shared-output-mask",
                "`PVW_TMLWE_DFT` is not part of this stage and must be separately tested.",
            ]
        )
        + "\n",
    )
    md = [
        "# Stage131 Shared-Source Production API Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage131 adds the shared-source compact EP public API to MOSFHET and",
        "validates it with an external probe linked through `mosfhet.h`.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        md.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | "
            f"{row['value']} | {row['detail']} |"
        )
    md += ["", "## API Rows", "", *api_table(api_rows), "", "## Interpretation", ""]
    md += [
        "The production API preserves the Stage130 correctness invariant. It still",
        "does not integrate with SAB or prove complete bootstrapping speedup.",
    ]
    write_text_lf(OUT_MD, "\n".join(md) + "\n")


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
    run_id = "stage131-shared-source-production-api-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        MOSFHET_DIR / "include" / "mosfhet.h",
        MOSFHET_DIR / "src" / "mattrgsw.c",
        SUMMARY_CSV,
        API_CSV,
        BUILD_LOG,
        COMPILE_LOG,
        RUN_LOG_TXT,
        C_SOURCE,
        ARTIFACT_INDEX,
        Path("scripts/build_stage131_shared_source_production_api_gate.py"),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 131",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage131_shared_source_production_api_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024",
            "seed": "0 subset",
            "status": status,
            "summary": "Stage131 validates the shared-source compact EP public API outside SAB.",
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
    write_docs(summary, api_rows)
    artifacts = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        MOSFHET_DIR / "include" / "mosfhet.h",
        MOSFHET_DIR / "src" / "mattrgsw.c",
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
    print(f"Stage131 shared-source production API gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
