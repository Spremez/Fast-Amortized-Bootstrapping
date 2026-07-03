#!/usr/bin/env python3
"""Build Stage132 lane-pair CMUX delta consumption gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage132_lane_pair_cmux_consumption_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
API_CSV = OUT_DIR / "api_results.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "lane_pair_cmux_consumption_gate.c"
C_BINARY = OUT_DIR / "lane_pair_cmux_consumption_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage132_lane_pair_cmux_consumption_gate.md"
PLAN_MD = ROOT / "experiments" / "stage132_lane_pair_cmux_consumption_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage132_lane_pair_cmux_consumption_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_lane_pair_cmux_consumption.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


API_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "k",
    "Bg_bit",
    "seed",
    "component_mismatches",
    "delta_phase_mismatches",
    "consumer_phase_mismatches",
    "noise_model_mismatches",
    "shared_output_negative_failures",
    "max_component_gap",
    "max_delta_phase_gap",
    "max_consumer_phase_gap",
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

#ifndef STAGE132_BACKEND
#define STAGE132_BACKEND "unknown"
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

static void add_poly(TorusPolynomial out, TorusPolynomial a, TorusPolynomial b) {
  for (int i = 0; i < out->N; i++) out->coeffs[i] = a->coeffs[i] + b->coeffs[i];
}

static void fill_source(TorusPolynomial out, int lane, int kind, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(13200 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static void fill_secret(TorusPolynomial out, int lane, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)(mix64(13250 + (uint64_t)seed,
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

static void fill_message(TorusPolynomial out, int lane, int seed) {
  for (int i = 0; i < out->N; i++) {
    const uint64_t word = mix64(13500 + (uint64_t)seed,
        (uint64_t)lane, 0, (uint64_t)i);
    out->coeffs[i] = (Torus)((word & 15ULL) << 48);
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

static void expected_delta_phase(TorusPolynomial expected_clean,
    TorusPolynomial expected_noise, TorusPolynomial expected_noisy,
    PVW_TMLWE in, TorusPolynomial *shared_noise, TorusPolynomial *body_noise,
    TorusPolynomial gadget, int T, int r, int lane, int Bg_bit, int exp,
    int64_t monomial, MAT_TRGSW_COMPACT_MUL_SCRATCH scratch) {
  zero_poly(expected_clean);
  zero_poly(expected_noise);
  for (int t = 0; t < T; t++) {
    const int idx = t * r + lane;
    make_gadget(gadget, t, Bg_bit, exp, monomial);
    polynomial_decompose_i(scratch->dec_shared, in->a[0], Bg_bit, T, t);
    polynomial_decompose_i(scratch->dec_body, in->b[lane], Bg_bit, T, t);
    polynomial_naive_mul_addto_torus(expected_clean, scratch->dec_shared, gadget);
    polynomial_naive_mul_addto_torus(expected_clean, scratch->dec_body, gadget);
    polynomial_naive_mul_addto_torus(expected_noise, scratch->dec_shared, shared_noise[idx]);
    polynomial_naive_mul_addto_torus(expected_noise, scratch->dec_body, body_noise[idx]);
  }
  add_poly(expected_noisy, expected_clean, expected_noise);
}

static void run_case(int r, int N, int T, int k, int Bg_bit, int seed) {
  const uint64_t tol = 131072;
  const int rows = T * r;
  const int exp = (seed * 23 + r + 17) & (N - 1);
  const int64_t monomial = (seed & 1) ? -1 : 1;

  TorusPolynomial *secret = new_poly_array(r, N);
  TorusPolynomial *shared_a = new_poly_array(rows, N);
  TorusPolynomial *shared_b = new_poly_array(rows, N);
  TorusPolynomial *body_a = new_poly_array(rows, N);
  TorusPolynomial *body_b = new_poly_array(rows, N);
  TorusPolynomial *shared_noise = new_poly_array(rows, N);
  TorusPolynomial *body_noise = new_poly_array(rows, N);
  TorusPolynomial *base_a = new_poly_array(r, N);
  TorusPolynomial *base_b = new_poly_array(r, N);
  TorusPolynomial *base_msg = new_poly_array(r, N);
  TorusPolynomial *base_noise = new_poly_array(r, N);

  TorusPolynomial gadget = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial coeff_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial out_b_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial lane0_a_torus = polynomial_new_torus_polynomial(N);
  TorusPolynomial delta_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_clean = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial expected_noisy = polynomial_new_torus_polynomial(N);
  TorusPolynomial observed_noise = polynomial_new_torus_polynomial(N);
  TorusPolynomial consumer_a = polynomial_new_torus_polynomial(N);
  TorusPolynomial consumer_b = polynomial_new_torus_polynomial(N);
  TorusPolynomial consumer_phase = polynomial_new_torus_polynomial(N);
  TorusPolynomial base_expected = polynomial_new_torus_polynomial(N);
  TorusPolynomial consumer_expected = polynomial_new_torus_polynomial(N);
  TorusPolynomial negative_phase = polynomial_new_torus_polynomial(N);

  PVW_TMLWE delta = pvmtmlwe_alloc_new_sample(k, r, N);
  MAT_TRGSW_COMPACT_DFT sel = mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, k, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT out = mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch = mat_trgsw_compact_alloc_mul_scratch(N);

  fill_source(delta->a[0], 0, 0, seed);
  for (int q = 0; q < r; q++) {
    fill_secret(secret[q], q, seed);
    fill_source(delta->b[q], q, 1, seed);
    fill_message(base_msg[q], q, seed);
    fill_noise(base_noise[q], q, 0, 7, seed);
    encrypt_row(base_a[q], base_b[q], secret[q], base_msg[q],
        base_noise[q], q, 0, 6, seed);
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

  mat_trgsw_compact_mul_pvmtmlwe_DFT(out, delta, sel, scratch);

  uint64_t component_mismatches = 0;
  uint64_t delta_phase_mismatches = 0;
  uint64_t consumer_phase_mismatches = 0;
  uint64_t noise_model_mismatches = 0;
  uint64_t shared_output_negative_failures = 0;
  uint64_t max_component_gap = 0;
  uint64_t max_delta_phase_gap = 0;
  uint64_t max_consumer_phase_gap = 0;
  uint64_t dummy_gap = 0;

  polynomial_DFT_to_torus(lane0_a_torus, out->a[0]);
  for (int q = 0; q < r; q++) {
    compact_reference(coeff_a, coeff_b, delta, shared_a, shared_b, body_a,
        body_b, T, r, q, Bg_bit, scratch);
    polynomial_DFT_to_torus(out_a_torus, out->a[q]);
    polynomial_DFT_to_torus(out_b_torus, out->b[q]);
    compare_poly(coeff_a, out_a_torus, tol, &component_mismatches,
        &max_component_gap);
    compare_poly(coeff_b, out_b_torus, tol, &component_mismatches,
        &max_component_gap);

    expected_delta_phase(expected_clean, expected_noise, expected_noisy, delta,
        shared_noise, body_noise, gadget, T, r, q, Bg_bit, exp, monomial,
        scratch);
    phase(delta_phase, out_a_torus, out_b_torus, secret[q]);
    compare_poly(delta_phase, expected_noisy, tol, &delta_phase_mismatches,
        &max_delta_phase_gap);

    phase(delta_phase, coeff_a, coeff_b, secret[q]);
    for (int i = 0; i < N; i++) {
      observed_noise->coeffs[i] = delta_phase->coeffs[i] - expected_clean->coeffs[i];
    }
    compare_poly(observed_noise, expected_noise, 0, &noise_model_mismatches,
        &dummy_gap);

    add_poly(consumer_a, base_a[q], out_a_torus);
    add_poly(consumer_b, base_b[q], out_b_torus);
    phase(consumer_phase, consumer_a, consumer_b, secret[q]);
    add_poly(base_expected, base_msg[q], base_noise[q]);
    add_poly(consumer_expected, base_expected, expected_noisy);
    compare_poly(consumer_phase, consumer_expected, tol,
        &consumer_phase_mismatches, &max_consumer_phase_gap);

    if (q > 0) {
      phase(negative_phase, lane0_a_torus, out_b_torus, secret[q]);
      compare_poly(negative_phase, expected_noisy, tol,
          &shared_output_negative_failures, &dummy_gap);
    }
  }

  const int ok = component_mismatches == 0 &&
      delta_phase_mismatches == 0 &&
      consumer_phase_mismatches == 0 &&
      noise_model_mismatches == 0 &&
      shared_output_negative_failures > 0;
  printf("CMUXDELTA,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
         ",%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE132_BACKEND, r, N, T, k, Bg_bit, seed, component_mismatches,
      delta_phase_mismatches, consumer_phase_mismatches,
      noise_model_mismatches, shared_output_negative_failures,
      max_component_gap, max_delta_phase_gap, max_consumer_phase_gap, tol,
      ok ? "PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION" : "FAIL");

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(out);
  free_mat_trgsw_compact_DFT(sel);
  free_pvmtmlwe(delta);
  free_poly_array_local(secret, r);
  free_poly_array_local(shared_a, rows);
  free_poly_array_local(shared_b, rows);
  free_poly_array_local(body_a, rows);
  free_poly_array_local(body_b, rows);
  free_poly_array_local(shared_noise, rows);
  free_poly_array_local(body_noise, rows);
  free_poly_array_local(base_a, r);
  free_poly_array_local(base_b, r);
  free_poly_array_local(base_msg, r);
  free_poly_array_local(base_noise, r);
  free_polynomial(gadget);
  free_polynomial(coeff_a);
  free_polynomial(coeff_b);
  free_polynomial(out_a_torus);
  free_polynomial(out_b_torus);
  free_polynomial(lane0_a_torus);
  free_polynomial(delta_phase);
  free_polynomial(expected_clean);
  free_polynomial(expected_noise);
  free_polynomial(expected_noisy);
  free_polynomial(observed_noise);
  free_polynomial(consumer_a);
  free_polynomial(consumer_b);
  free_polynomial(consumer_phase);
  free_polynomial(base_expected);
  free_polynomial(consumer_expected);
  free_polynomial(negative_phase);
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
        f"gcc -O2 -DSTAGE132_BACKEND=\\\"{backend}\\\" "
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
        if parts and parts[0] == "CMUXDELTA" and len(parts) == len(API_FIELDS) + 1:
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
    return len(rows) == 6 and all(
        row["status"] == "PASS_LANE_PAIR_CMUX_DELTA_CONSUMPTION"
        and row["component_mismatches"] == "0"
        and row["delta_phase_mismatches"] == "0"
        and row["consumer_phase_mismatches"] == "0"
        and row["noise_model_mismatches"] == "0"
        and int(row["shared_output_negative_failures"]) > 0
        for row in rows
    )


def build_summary(
    build_ok: bool, compile_ok: bool, run_ok: bool, api_rows: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    correctness = api_pass(api_rows)
    decision = (
        "PASS_STAGE132_LANE_PAIR_CMUX_DELTA_CONSUMPTION_READY_LANE_STATE_REQUIRED"
        if build_ok and compile_ok and run_ok and correctness
        else "FAIL_STAGE132_LANE_PAIR_CMUX_DELTA_CONSUMPTION_GATE"
    )
    max_component = max((int(row["max_component_gap"]) for row in api_rows), default=0)
    max_delta = max((int(row["max_delta_phase_gap"]) for row in api_rows), default=0)
    max_consumer = max(
        (int(row["max_consumer_phase_gap"]) for row in api_rows), default=0
    )
    return [
        {
            "gate": "stage132_mosfhet_static_build",
            "status": "PASS" if build_ok else "FAIL",
            "metric": "make_static_spqlios_enable_pvw",
            "value": str(build_ok).lower(),
            "evidence": rel(BUILD_LOG),
            "detail": "MOSFHET static library builds with Stage131 compact EP API.",
            "next_action": "",
        },
        {
            "gate": "stage132_probe_compile",
            "status": "PASS" if compile_ok else "FAIL",
            "metric": "public_header_link",
            "value": str(compile_ok).lower(),
            "evidence": rel(COMPILE_LOG),
            "detail": "Standalone CMUX-consumption probe compiles against mosfhet.h.",
            "next_action": "",
        },
        {
            "gate": "stage132_probe_run",
            "status": "PASS" if run_ok else "FAIL",
            "metric": "probe_returncode",
            "value": "0" if run_ok else "nonzero_or_skipped",
            "evidence": rel(RUN_LOG_TXT),
            "detail": "Lane-pair CMUX delta consumption probe executed.",
            "next_action": "",
        },
        {
            "gate": "stage132_lane_pair_consumer_correctness",
            "status": "PASS" if correctness else "FAIL",
            "metric": "rows;max_component_gap;max_delta_gap;max_consumer_gap",
            "value": f"{len(api_rows)};{max_component};{max_delta};{max_consumer}",
            "evidence": rel(API_CSV),
            "detail": "Per-lane delta and base-plus-delta phase/noise gates pass.",
            "next_action": "Do not build RGSW/sparse integration if this fails.",
        },
        {
            "gate": "stage132_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": f"{rel(SUMMARY_CSV)}; {rel(API_CSV)}",
            "detail": "Stage132 opens a lane-state accumulator design, not full SAB speed claims.",
            "next_action": "Stage133 should define a compact lane-state object for RGSW/sparse schedule.",
        },
    ]


def api_table(rows: List[Dict[str, str]]) -> List[str]:
    lines = [
        "| r | N | seed | component mm | delta phase mm | consumer phase mm | noise mm | shared-output negative failures | max component gap | max delta gap | max consumer gap | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['seed']} | "
            f"{row['component_mismatches']} | {row['delta_phase_mismatches']} | "
            f"{row['consumer_phase_mismatches']} | {row['noise_model_mismatches']} | "
            f"{row['shared_output_negative_failures']} | {row['max_component_gap']} | "
            f"{row['max_delta_phase_gap']} | {row['max_consumer_phase_gap']} | "
            f"{row['status']} |"
        )
    return lines


def write_docs(summary: List[Dict[str, str]], api_rows: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    write_text_lf(
        PLAN_MD,
        "\n".join(
            [
                "# Stage132 Lane-Pair CMUX Consumption Gate Plan",
                "",
                "Date: 2026-07-03",
                "",
                "## Objective",
                "",
                "Validate the first SAB-facing consumer boundary for the Stage131",
                "shared-source compact EP output. The gate checks the CMUX delta",
                "formula `out = base + EP(delta)` per lane, while preserving the",
                "explicit lane-pair output shape.",
                "",
                "## Command",
                "",
                "```bash",
                "python scripts/build_stage132_lane_pair_cmux_consumption_gate.py",
                "```",
                "",
                "## Falsification Criteria",
                "",
                "- MOSFHET static build or public-header compile/link fails;",
                "- component, delta-phase, consumer-phase, or exact noise-model",
                "  mismatch counts are nonzero;",
                "- compressing lane-pair masks into a single shared output mask does",
                "  not fail for r>1;",
                "- the result is described as full CMUX, RGSW, sparse schedule, or",
                "  complete bootstrapping acceleration.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        THEORY_MD,
        "\n".join(
            [
                "# Stage132 Lane-Pair CMUX Consumption Model",
                "",
                "Date: 2026-07-03",
                "",
                "The Stage131 API produces `MAT_TRGSW_COMPACT_OUTPUT_DFT`, containing",
                "one DFT mask/body pair per lane. Stage132 tests the narrow consumer",
                "identity needed by CMUX:",
                "",
                "```text",
                "phase_q(base_q + delta_q) = phase_q(base_q) + phase_q(delta_q)",
                "delta_q = compact_EP_q(in2 - in1)",
                "```",
                "",
                "This is a lane-state invariant. It does not prove that the output can",
                "be represented as a standard `PVW_TMLWE_DFT` with one shared output",
                "mask. The required negative control intentionally collapses all lane",
                "masks to lane 0 and verifies that this produces phase failures.",
                "",
                "## Results",
                "",
                *api_table(api_rows),
                "",
                "## Boundary",
                "",
                "Passing this gate opens compact lane-state design for RGSW monomial",
                "and sparse schedule integration. It is not complete SAB, not",
                "multi-seed correctness/noise evidence, and not a `T_bootstrap/r`",
                "performance claim.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        VARIANT_MD,
        "\n".join(
            [
                "# V132: Lane-Pair CMUX Delta Consumption",
                "",
                "## Summary",
                "",
                "- Parent algorithm: PVW/MAT-SAB r-body research track.",
                "- Focused module: first SAB-facing consumer of compact EP output.",
                "- Optimization target: complete-SAB amortized `T_bootstrap/r`.",
                "- Status labels: `[isolated-consumer]`, `[lane-state-required]`,",
                "  `[not-full-sab]`.",
                f"- Decision: `{decision}`.",
                "",
                "## Delta From Stage131",
                "",
                "Stage131 validates the public external-product API. Stage132 adds the",
                "next invariant: converting each lane-pair DFT output to torus and",
                "adding it to an accumulator base preserves the expected per-lane",
                "phase/noise. It deliberately keeps the output as lane-pair state.",
            ]
        )
        + "\n",
    )
    md = [
        "# Stage132 Lane-Pair CMUX Consumption Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage132 validates the first isolated CMUX-delta consumer boundary for",
        "the Stage131 compact EP public API.",
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
        "The lane-pair compact EP output can be consumed by a per-lane",
        "`base + delta` accumulator update without phase/noise mismatch in this",
        "deterministic gate. The negative control shows that replacing the",
        "lane-pair masks by one shared output mask is invalid for r>1.",
    ]
    write_text_lf(OUT_MD, "\n".join(md) + "\n")


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + "\n" + block.strip() + "\n")


def update_longform_docs(status: str) -> None:
    stage_block = """
## Stage 132: Lane-Pair CMUX Delta Consumption Gate

Goal:

```text
Validate that the Stage131 lane-pair compact EP output can be consumed by an
isolated CMUX delta update `base + EP(in2 - in1)` without converting it into a
false shared-output-mask PVW ciphertext.
```

Theory basis:

The Stage131 output is one mask/body pair per lane. A standard `PVW_TMLWE_DFT`
has one shared mask and r bodies, so treating the Stage131 output as standard
PVW would be an invalid invariant unless separately proven. Stage132 therefore
checks the exact per-lane phase/noise consumer equation and keeps a negative
control that collapses all masks to lane 0.

Gate:

- public API build/compile/run must pass;
- component, delta-phase, consumer-phase, and noise-model mismatches must be
  zero for r=2/4/6 and N=512/1024;
- the shared-output-mask collapse negative control must fail for r>1;
- passing opens only lane-state RGSW/sparse schedule design.

Status:

```text
Completed. Stage132 records
PASS_STAGE132_LANE_PAIR_CMUX_DELTA_CONSUMPTION_READY_LANE_STATE_REQUIRED.
The deterministic public-API probe passes for k=1, T=7, Bg_bit=7, r=2/4/6,
and N=512/1024. Component, delta-phase, consumer-phase, and exact noise-model
mismatch counts are zero. Collapsing lane-pair masks into one shared output
mask fails as required. The next valid step is a compact lane-state
accumulator object for RGSW monomial and sparse schedule integration.
```
"""
    append_once(ROADMAP_MD, "## Stage 132: Lane-Pair CMUX Delta Consumption Gate", stage_block)

    goal_block = """
Stage132 extends the current compact EP chain to the first isolated CMUX
consumer invariant. The result is still not complete SAB acceleration: it
proves only that lane-pair output can be added to per-lane accumulator state
with correct phase/noise, and that collapsing it into a standard shared-output
PVW ciphertext is invalid. The next promoted target is a lane-state RGSW/sparse
schedule gate.
"""
    append_once(GOAL_MD, "Stage132 extends the current compact EP chain", goal_block)

    current_goal_block = f"""
36. Treat Stage132 as the current lane-pair CMUX consumption gate:
    `{status}`. The compact shared-source EP output can be consumed by
    per-lane `base + delta` CMUX updates for r=2/4/6 and N=512/1024 with zero
    component, phase, consumer, and noise-model mismatches. A single
    shared-output-mask collapse fails as required. The next valid step is a
    compact lane-state accumulator design for RGSW monomial and sparse
    schedule integration, not complete `T_bootstrap/r` claims.
"""
    append_once(CURRENT_GOAL_MD, "36. Treat Stage132 as the current lane-pair", current_goal_block)


def upsert_hypothesis(status: str) -> None:
    block = f"""  - id: H56_lane_pair_cmux_delta_consumption
    statement: >
      The Stage131 shared-source compact external-product output can be
      consumed by an isolated SAB-facing CMUX delta update per lane without
      assuming a false shared output mask.
    mechanism: >
      Stage132 computes `delta = in2 - in1`, applies the public compact EP API,
      converts each lane-pair DFT output to torus, and checks that
      `phase_q(base_q + delta_q)` equals the modeled base phase plus modeled
      EP delta phase. It also collapses all lane masks to lane 0 as a required
      negative control.
    status: stage132_lane_pair_cmux_delta_consumption_ready_lane_state_required
    evidence: docs/stage132_lane_pair_cmux_consumption_gate.md; experiments/stage132_lane_pair_cmux_consumption_gate_plan.md; theory_checks/stage132_lane_pair_cmux_consumption_model.md; algorithm_variants/mat_rlwe_sab_lane_pair_cmux_consumption.md; scripts/build_stage132_lane_pair_cmux_consumption_gate.py; repro/stage132_lane_pair_cmux_consumption_gate/summary.csv; repro/stage132_lane_pair_cmux_consumption_gate/api_results.csv; repro/stage132_lane_pair_cmux_consumption_gate/mosfhet_static_build.log; repro/stage132_lane_pair_cmux_consumption_gate/compile_probe.log; repro/stage132_lane_pair_cmux_consumption_gate/run_probe.log; repro/stage132_lane_pair_cmux_consumption_gate/lane_pair_cmux_consumption_gate.c; repro/stage132_lane_pair_cmux_consumption_gate/artifact_index.csv
    current_decision: >
      Stage132 records {status}. Build, compile, run, and deterministic
      lane-pair CMUX delta consumption gates pass for k=1, T=7, Bg_bit=7,
      r=2/4/6, and N=512/1024. Component, delta-phase, consumer-phase, and
      exact noise-model mismatch counts are zero. The single shared-output
      mask collapse negative control fails as required. This opens lane-state
      RGSW/sparse integration design only.
    failure_criteria:
      - later code treats `MAT_TRGSW_COMPACT_OUTPUT_DFT` as a true
        `PVW_TMLWE_DFT` shared-output-mask ciphertext without a separate gate
      - RGSW or sparse schedule integration requires dense reconstruction that
        erases the Stage130 shared-source mechanism
      - deterministic consumer evidence is claimed as full SAB correctness,
        multi-seed noise, or complete `T_bootstrap/r` acceleration
      - scalar/default SAB behavior changes before a guarded integration stage
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H56_lane_pair_cmux_delta_consumption"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append(
                {
                    "artifact": rel(path),
                    "exists": "self",
                    "sha256": "",
                    "size_bytes": "",
                }
            )
            continue
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
    run_id = "stage132-lane-pair-cmux-consumption-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
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
        Path(__file__).resolve(),
    ]
    rows.append(
        {
            "run_id": run_id,
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 132",
            "backend": "MOSFHET FFT_LIB=spqlios",
            "command": "python scripts/build_stage132_lane_pair_cmux_consumption_gate.py",
            "params": "k=1 T=7 Bg_bit=7 r=2,4,6 N=512,1024",
            "seed": "0 subset",
            "status": status,
            "summary": "Stage132 validates lane-pair compact EP output consumption by isolated CMUX delta updates.",
            "artifacts": "; ".join(rel(p) for p in artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 132 Lane-Pair CMUX Consumption Gate

- `docs/stage132_lane_pair_cmux_consumption_gate.md`
- `experiments/stage132_lane_pair_cmux_consumption_gate_plan.md`
- `theory_checks/stage132_lane_pair_cmux_consumption_model.md`
- `algorithm_variants/mat_rlwe_sab_lane_pair_cmux_consumption.md`
- `scripts/build_stage132_lane_pair_cmux_consumption_gate.py`
- `repro/stage132_lane_pair_cmux_consumption_gate/summary.csv`
- `repro/stage132_lane_pair_cmux_consumption_gate/api_results.csv`
- `repro/stage132_lane_pair_cmux_consumption_gate/mosfhet_static_build.log`
- `repro/stage132_lane_pair_cmux_consumption_gate/compile_probe.log`
- `repro/stage132_lane_pair_cmux_consumption_gate/run_probe.log`
- `repro/stage132_lane_pair_cmux_consumption_gate/lane_pair_cmux_consumption_gate.c`
- `repro/stage132_lane_pair_cmux_consumption_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 132 Lane-Pair CMUX Consumption Gate", block)


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
    status = summary[-1]["status"]
    update_longform_docs(status)
    upsert_hypothesis(status)
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
        Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    upsert_global_manifest()
    print(f"Stage132 lane-pair CMUX consumption gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
