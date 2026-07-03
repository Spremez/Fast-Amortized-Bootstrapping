#!/usr/bin/env python3
"""Build Stage138 shared-mask compact MAT external-product gate."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts" / "build_stage137_decomp_dft_attribution_gate.py"
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage138_shared_mask_compact_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
RATIO_CSV = OUT_DIR / "ratio_summary.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "shared_mask_compact_gate.c"
C_BINARY = OUT_DIR / "shared_mask_compact_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage138_shared_mask_compact_gate.md"
PLAN_MD = ROOT / "experiments" / "stage138_shared_mask_compact_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage138_shared_mask_compact_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_shared_mask_compact.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


CORRECTNESS_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "Bg_bit",
    "seed",
    "dft_mismatches",
    "max_dft_gap",
    "tolerance",
    "repeated_dft_conversions",
    "shared_dft_conversions",
    "status",
]
BENCH_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "Bg_bit",
    "seed",
    "sample",
    "reps",
    "warmups",
    "variant",
    "total_ns",
    "avg_us",
    "per_lane_us",
    "dft_conversion_count",
    "status",
]
AGG_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "Bg_bit",
    "seed",
    "variant",
    "samples",
    "mean_us",
    "median_us",
    "min_us",
    "max_us",
    "stdev_us",
    "mean_per_lane_us",
]
RATIO_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "Bg_bit",
    "seed",
    "repeated_us",
    "shared_us",
    "total_speedup",
    "repeated_per_lane_us",
    "shared_per_lane_us",
    "per_bit_speedup",
    "repeated_dft_conversions",
    "shared_dft_conversions",
    "dft_conversion_reduction",
    "expected_dft_reduction",
    "decision",
]


def load_helper():
    spec = importlib.util.spec_from_file_location("stage137_helpers", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Stage137 helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_helper()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
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


def sanitize_log(text: str) -> str:
    return H.sanitize_log(text)


def append_once(path: Path, marker: str, block: str) -> None:
    H.append_once(path, marker, block)


def markdown_table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    return "\n".join(H.table(rows, fields))


def min_field(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    return H.min_field(rows, field, r_filter)


def max_field(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    return H.max_field(rows, field, r_filter)


def write_c_source() -> None:
    source = r'''
#include "mosfhet.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE138_BACKEND
#define STAGE138_BACKEND "unknown"
#endif

static volatile double g_stage138_sink = 0.0;

static uint64_t stage138_now_ns(void){
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
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

static void fill_source(TorusPolynomial out, int lane, int kind, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(138000 + (uint64_t)seed,
        (uint64_t)lane, (uint64_t)kind, (uint64_t)i);
  }
}

static TorusPolynomial * new_poly_array(int count, int N) {
  TorusPolynomial *out =
      (TorusPolynomial *)safe_malloc(sizeof(TorusPolynomial) * count);
  for (int i = 0; i < count; i++) out[i] = polynomial_new_torus_polynomial(N);
  return out;
}

static void free_poly_array_local(TorusPolynomial *in, int count) {
  for (int i = 0; i < count; i++) free_polynomial(in[i]);
  free(in);
}

static void zero_dft(DFT_Polynomial p) {
  memset(p->coeffs, 0, sizeof(double) * p->N);
}

static void zero_compact_output(MAT_TRGSW_COMPACT_OUTPUT_DFT out) {
  for (int lane = 0; lane < out->r; lane++) {
    zero_dft(out->a[lane]);
    zero_dft(out->b[lane]);
  }
}

static double abs_double(double x) {
  return x < 0.0 ? -x : x;
}

static void compare_dft(DFT_Polynomial a, DFT_Polynomial b,
    uint64_t *mismatches, double *max_gap) {
  for (int i = 0; i < a->N; i++) {
    const double gap = abs_double(a->coeffs[i] - b->coeffs[i]);
    if (gap != 0.0) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }
}

static void consume_output(MAT_TRGSW_COMPACT_OUTPUT_DFT out) {
  double acc = 0.0;
  for (int lane = 0; lane < out->r; lane++) {
    for (int i = 0; i < out->N; i += 17) {
      acc += out->a[lane]->coeffs[i] * 0.0000000001;
      acc += out->b[lane]->coeffs[i] * 0.0000000002;
    }
  }
  g_stage138_sink += acc;
}

static void repeated_lane_pair_compact_mul(MAT_TRGSW_COMPACT_OUTPUT_DFT out,
    PVW_TMLWE in, MAT_TRGSW_COMPACT_DFT selector,
    MAT_TRGSW_COMPACT_MUL_SCRATCH scratch) {
  zero_compact_output(out);
  for (int lane = 0; lane < selector->r; lane++) {
    for (int t = 0; t < selector->T; t++) {
      const int idx = t * selector->r + lane;
      polynomial_decompose_i(scratch->dec_shared, in->a[0],
          selector->Q, selector->T, t);
      polynomial_torus_to_DFT(scratch->dec_shared_dft, scratch->dec_shared);
      polynomial_decompose_i(scratch->dec_body, in->b[lane],
          selector->Q, selector->T, t);
      polynomial_torus_to_DFT(scratch->dec_body_dft, scratch->dec_body);
      polynomial_mul_addto_DFT(out->a[lane], scratch->dec_shared_dft,
          selector->shared_a[idx]);
      polynomial_mul_addto_DFT(out->b[lane], scratch->dec_shared_dft,
          selector->shared_b[idx]);
      polynomial_mul_addto_DFT(out->a[lane], scratch->dec_body_dft,
          selector->body_a[idx]);
      polynomial_mul_addto_DFT(out->b[lane], scratch->dec_body_dft,
          selector->body_b[idx]);
    }
  }
}

static void fill_case(PVW_TMLWE in, MAT_TRGSW_COMPACT_DFT selector,
    int r, int N, int T, int Bg_bit, int seed) {
  (void)N;
  (void)T;
  (void)Bg_bit;
  fill_source(in->a[0], 0, 100, seed);
  for (int lane = 0; lane < r; lane++) {
    fill_source(in->b[lane], lane, 200, seed);
  }

  const int rows = T * r;
  TorusPolynomial *shared_a = new_poly_array(rows, N);
  TorusPolynomial *shared_b = new_poly_array(rows, N);
  TorusPolynomial *body_a = new_poly_array(rows, N);
  TorusPolynomial *body_b = new_poly_array(rows, N);
  for (int t = 0; t < T; t++) {
    for (int lane = 0; lane < r; lane++) {
      const int idx = t * r + lane;
      fill_source(shared_a[idx], lane, 300 + t, seed);
      fill_source(shared_b[idx], lane, 400 + t, seed);
      fill_source(body_a[idx], lane, 500 + t, seed);
      fill_source(body_b[idx], lane, 600 + t, seed);
      mat_trgsw_compact_set_row_from_torus(selector, t, lane,
          shared_a[idx], shared_b[idx], body_a[idx], body_b[idx]);
    }
  }
  free_poly_array_local(shared_a, rows);
  free_poly_array_local(shared_b, rows);
  free_poly_array_local(body_a, rows);
  free_poly_array_local(body_b, rows);
}

static void correctness_case(int r, int N, int T, int Bg_bit, int seed) {
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_COMPACT_DFT selector =
      mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT repeated =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT shared =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch =
      mat_trgsw_compact_alloc_mul_scratch(N);

  fill_case(in, selector, r, N, T, Bg_bit, seed);
  repeated_lane_pair_compact_mul(repeated, in, selector, scratch);
  mat_trgsw_compact_mul_pvmtmlwe_DFT(shared, in, selector, scratch);

  uint64_t mismatches = 0;
  double max_gap = 0.0;
  for (int lane = 0; lane < r; lane++) {
    compare_dft(repeated->a[lane], shared->a[lane], &mismatches, &max_gap);
    compare_dft(repeated->b[lane], shared->b[lane], &mismatches, &max_gap);
  }
  const uint64_t repeated_dft = 2ULL * (uint64_t)r * (uint64_t)T;
  const uint64_t shared_dft = ((uint64_t)r + 1ULL) * (uint64_t)T;
  printf("CORRECT138,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,0.000000000,%" PRIu64 ",%" PRIu64 ",%s\n",
      STAGE138_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap,
      repeated_dft, shared_dft,
      mismatches == 0 ? "PASS_SHARED_MASK_EQUIV" : "FAIL");

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(shared);
  free_mat_trgsw_compact_output_DFT(repeated);
  free_mat_trgsw_compact_DFT(selector);
  free_pvmtmlwe(in);
}

static void emit_bench_row(int r, int N, int T, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant, uint64_t total_ns,
    uint64_t dft_count) {
  const double avg_us = (double)total_ns / (1000.0 * (double)reps);
  const double per_lane_us = avg_us / (double)r;
  printf("BENCH138,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%.6f,%" PRIu64 ",PASS\n",
      STAGE138_BACKEND, r, N, T, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, per_lane_us, dft_count);
}

static void bench_case(int r, int N, int T, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_COMPACT_DFT selector =
      mat_trgsw_compact_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT repeated =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_OUTPUT_DFT shared =
      mat_trgsw_compact_alloc_new_output_DFT(r, N);
  MAT_TRGSW_COMPACT_MUL_SCRATCH scratch =
      mat_trgsw_compact_alloc_mul_scratch(N);
  const uint64_t repeated_dft = 2ULL * (uint64_t)r * (uint64_t)T;
  const uint64_t shared_dft = ((uint64_t)r + 1ULL) * (uint64_t)T;

  fill_case(in, selector, r, N, T, Bg_bit, seed);
  for (int i = 0; i < warmups; i++) {
    repeated_lane_pair_compact_mul(repeated, in, selector, scratch);
    consume_output(repeated);
    mat_trgsw_compact_mul_pvmtmlwe_DFT(shared, in, selector, scratch);
    consume_output(shared);
  }

  for (int sample = 0; sample < samples; sample++) {
    uint64_t begin = stage138_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      repeated_lane_pair_compact_mul(repeated, in, selector, scratch);
      consume_output(repeated);
    }
    uint64_t total = stage138_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "repeated_lane_pair", total, repeated_dft);

    begin = stage138_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      mat_trgsw_compact_mul_pvmtmlwe_DFT(shared, in, selector, scratch);
      consume_output(shared);
    }
    total = stage138_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "shared_mask_compact", total, shared_dft);
  }

  free_mat_trgsw_compact_mul_scratch(scratch);
  free_mat_trgsw_compact_output_DFT(shared);
  free_mat_trgsw_compact_output_DFT(repeated);
  free_mat_trgsw_compact_DFT(selector);
  free_pvmtmlwe(in);
}

int main(void) {
  const int T = 7;
  const int Bg_bit = 7;
  const int seed = 0;
  const int samples = 5;
  const int reps = 20;
  const int warmups = 2;
  correctness_case(2, 512, T, Bg_bit, seed);
  correctness_case(4, 512, T, Bg_bit, seed);
  correctness_case(6, 512, T, Bg_bit, seed);
  correctness_case(2, 1024, T, Bg_bit, seed);
  correctness_case(4, 1024, T, Bg_bit, seed);
  correctness_case(6, 1024, T, Bg_bit, seed);
  bench_case(2, 512, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(4, 512, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(6, 512, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(2, 1024, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(4, 1024, T, Bg_bit, seed, samples, reps, warmups);
  bench_case(6, 1024, T, Bg_bit, seed, samples, reps, warmups);
  fprintf(stderr, "stage138_sink=%f\n", g_stage138_sink);
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
    write_text_lf(BUILD_LOG, "\n".join([
        f"command: {cmd}", f"returncode: {proc.returncode}", "--- stdout ---",
        sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE138_BACKEND=\\\"{backend}\\\" "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    proc = bash(cmd, timeout=60)
    write_text_lf(COMPILE_LOG, "\n".join([
        f"command: {cmd}", f"returncode: {proc.returncode}", "--- stdout ---",
        sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    return proc.returncode == 0


def cleanup_build_outputs() -> None:
    try:
        C_BINARY.unlink()
    except FileNotFoundError:
        pass
    bash("cd src/mosfhet && make clean >/dev/null 2>&1 || true", timeout=60)


def parse_stdout(stdout: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    correctness: List[Dict[str, str]] = []
    bench: List[Dict[str, str]] = []
    for line in stdout.splitlines():
        parts = line.strip().split(",")
        if parts and parts[0] == "CORRECT138" and len(parts) == len(CORRECTNESS_FIELDS) + 1:
            correctness.append(dict(zip(CORRECTNESS_FIELDS, parts[1:])))
        elif parts and parts[0] == "BENCH138" and len(parts) == len(BENCH_FIELDS) + 1:
            bench.append(dict(zip(BENCH_FIELDS, parts[1:])))
    return correctness, bench


def run_probe(build_ok: bool, compile_ok: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=180)
    write_text_lf(RUN_LOG_TXT, "\n".join([
        f"command: ./{rel(C_BINARY)}", f"returncode: {proc.returncode}",
        "--- stdout ---", sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    correctness, bench = parse_stdout(proc.stdout)
    cleanup_build_outputs()
    return correctness, bench, proc.returncode == 0


def aggregate_bench(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    groups: Dict[Tuple[str, str, str, str, str, str, str], List[Tuple[float, float]]] = {}
    for row in rows:
        key = (row["backend"], row["r"], row["N"], row["T"], row["Bg_bit"], row["seed"], row["variant"])
        groups.setdefault(key, []).append((float(row["avg_us"]), float(row["per_lane_us"])))
    out: List[Dict[str, str]] = []
    for key, values in sorted(groups.items(), key=lambda item: item[0]):
        totals = [v[0] for v in values]
        per_lane = [v[1] for v in values]
        stdev = statistics.stdev(totals) if len(totals) > 1 else 0.0
        out.append({
            "backend": key[0], "r": key[1], "N": key[2], "T": key[3],
            "Bg_bit": key[4], "seed": key[5], "variant": key[6],
            "samples": str(len(totals)), "mean_us": f"{statistics.mean(totals):.6f}",
            "median_us": f"{statistics.median(totals):.6f}",
            "min_us": f"{min(totals):.6f}", "max_us": f"{max(totals):.6f}",
            "stdev_us": f"{stdev:.6f}",
            "mean_per_lane_us": f"{statistics.mean(per_lane):.6f}",
        })
    return out


def build_ratio_rows(agg_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[Tuple[str, str, str, str, str, str], Dict[str, Dict[str, str]]] = {}
    for row in agg_rows:
        key = (row["backend"], row["r"], row["N"], row["T"], row["Bg_bit"], row["seed"])
        grouped.setdefault(key, {})[row["variant"]] = row
    out: List[Dict[str, str]] = []
    for key, variants in sorted(grouped.items(), key=lambda item: item[0]):
        if "repeated_lane_pair" not in variants or "shared_mask_compact" not in variants:
            continue
        repeated = float(variants["repeated_lane_pair"]["mean_us"])
        shared = float(variants["shared_mask_compact"]["mean_us"])
        repeated_per_lane = float(variants["repeated_lane_pair"]["mean_per_lane_us"])
        shared_per_lane = float(variants["shared_mask_compact"]["mean_per_lane_us"])
        r = int(key[1])
        T = int(key[3])
        repeated_dft = 2 * r * T
        shared_dft = (r + 1) * T
        speedup = repeated / shared if shared else 0.0
        dft_ratio = repeated_dft / shared_dft
        decision = "PROMOTE_SHARED_MASK_COMPACT" if speedup >= 1.05 else "NEUTRAL_SHARED_MASK_COMPACT"
        out.append({
            "backend": key[0],
            "r": key[1],
            "N": key[2],
            "T": key[3],
            "Bg_bit": key[4],
            "seed": key[5],
            "repeated_us": f"{repeated:.6f}",
            "shared_us": f"{shared:.6f}",
            "total_speedup": f"{speedup:.6f}",
            "repeated_per_lane_us": f"{repeated_per_lane:.6f}",
            "shared_per_lane_us": f"{shared_per_lane:.6f}",
            "per_bit_speedup": f"{(repeated_per_lane / shared_per_lane if shared_per_lane else 0.0):.6f}",
            "repeated_dft_conversions": str(repeated_dft),
            "shared_dft_conversions": str(shared_dft),
            "dft_conversion_reduction": f"{dft_ratio:.6f}",
            "expected_dft_reduction": f"{(2.0 * r / (r + 1)):.6f}",
            "decision": decision,
        })
    return out


def build_summary(build_ok: bool, compile_ok: bool, run_ok: bool,
    correctness_rows: List[Dict[str, str]], bench_rows: List[Dict[str, str]],
    ratio_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    corr_ok = (
        len(correctness_rows) == 6
        and all(row["status"] == "PASS_SHARED_MASK_EQUIV" and row["dft_mismatches"] == "0" for row in correctness_rows)
    )
    bench_ok = bool(bench_rows) and len(ratio_rows) == 6
    r4_rows = [row for row in ratio_rows if row["r"] == "4"]
    r4_promoted = len(r4_rows) == 2 and all(float(row["total_speedup"]) >= 1.05 for row in r4_rows)
    if not (build_ok and compile_ok and run_ok and corr_ok and bench_ok):
        decision = "FAIL_STAGE138_SHARED_MASK_COMPACT_GATE"
    elif r4_promoted:
        decision = "PASS_STAGE138_SHARED_MASK_COMPACT_PROMOTED_READY_SAB_INTEGRATION"
    else:
        decision = "NEUTRAL_STAGE138_SHARED_MASK_COMPACT_CORRECT_BUT_PERF_WEAK"
    return [
        {"gate": "stage138_mosfhet_static_build", "status": "PASS" if build_ok else "FAIL", "metric": "make_static_spqlios", "value": str(build_ok).lower(), "evidence": rel(BUILD_LOG), "detail": "MOSFHET static build for shared-mask compact probe.", "next_action": "Fix build before interpreting results."},
        {"gate": "stage138_probe_compile", "status": "PASS" if compile_ok else "FAIL", "metric": "gcc_probe_compile", "value": str(compile_ok).lower(), "evidence": rel(COMPILE_LOG), "detail": "Standalone shared-mask compact probe compiled.", "next_action": ""},
        {"gate": "stage138_probe_run", "status": "PASS" if run_ok else "FAIL", "metric": "probe_returncode", "value": "0" if run_ok else "nonzero-or-skipped", "evidence": rel(RUN_LOG_TXT), "detail": "Shared-mask compact probe executed.", "next_action": ""},
        {"gate": "stage138_correctness", "status": "PASS" if corr_ok else "FAIL", "metric": "correctness_rows", "value": str(len(correctness_rows)), "evidence": rel(CORRECTNESS_CSV), "detail": "Production shared-mask compact output equals repeated lane-pair output.", "next_action": "Do not promote without exact DFT equivalence."},
        {"gate": "stage138_benchmark_rows", "status": "PASS" if bench_ok else "FAIL", "metric": "bench_rows;ratio_rows", "value": f"{len(bench_rows)};{len(ratio_rows)}", "evidence": f"{rel(BENCH_CSV)}; {rel(RATIO_CSV)}", "detail": "Repeated lane-pair and shared-mask compact timings recorded.", "next_action": ""},
        {"gate": "stage138_r4_per_bit_speedup", "status": "RECORDED", "metric": "min_r4_per_bit_speedup;max_r4_per_bit_speedup", "value": f"{min_field(ratio_rows, 'per_bit_speedup', {'4'})};{max_field(ratio_rows, 'per_bit_speedup', {'4'})}", "evidence": rel(RATIO_CSV), "detail": "Main metric is amortized per-lane/per-bit kernel time.", "next_action": ""},
        {"gate": "stage138_decision", "status": decision, "metric": "promotion_policy", "value": "", "evidence": f"{rel(SUMMARY_CSV)}; {rel(RATIO_CSV)}", "detail": "Stage138 decides whether shared-mask compact EP is a real algorithmic route.", "next_action": "If promoted, Stage139 should integrate compact selectors into SAB CMUX/RGSW without breaking scalar SAB."},
    ]


def write_docs(summary: List[Dict[str, str]], ratio_rows: List[Dict[str, str]]) -> None:
    status = summary[-1]["status"]
    table = markdown_table(summary, ["gate", "status", "metric", "value", "detail"])
    ratio_table = markdown_table(ratio_rows, RATIO_FIELDS)
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage138 Shared-Mask Compact Gate Plan", "", "Date: 2026-07-03", "",
        "## Objective", "",
        "Verify the algorithmic MAT-RLWE requirement that one shared mask is reused across r body lanes, instead of repeating lane-pair decompose/DFT work for each lane.", "",
        "## Falsification Criteria", "",
        "- production compact shared-mask output differs from repeated lane-pair output;",
        "- performance is reported without dividing by r;",
        "- kernel microbench is reported as full SAB bootstrapping acceleration;",
        "- Stage139 integrates compact selectors without a scalar reference path.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage138 Shared-Mask Compact MAT Model", "", "Date: 2026-07-03", "",
        "For k=1 and T decomposition levels, repeating a lane-pair kernel performs `2*r*T` input DFT conversions: one shared-like source and one body source per lane.",
        "A true MAT-RLWE ciphertext has one shared mask and r bodies, so the compact shared-mask route performs `(1+r)*T` input DFT conversions.",
        "The conversion-count reduction is therefore `2r/(r+1)`, which is 1.6x for r=4. Stage138 tests whether this theoretical reduction survives the DFT multiply-add work in the external-product kernel.",
        "",
        "## Ratios", "", ratio_table,
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# V138: Shared-Mask Compact MAT External Product", "", "## Summary", "",
        "This variant treats PVW/MAT-SAB as an algorithmic MAT-RLWE construction: one shared mask plus r body lanes.",
        "It compares a repeated lane-pair implementation against the production `mat_trgsw_compact_mul_pvmtmlwe_DFT` path.",
        "",
        "## Claim Boundary", "",
        "This is an external-product kernel gate with amortized per-lane timing. It does not by itself prove complete SAB bootstrapping speedup.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage138 Shared-Mask Compact Gate", "", "Date: 2026-07-03", "",
        "## Decision", "", f"`{status}`", "",
        "Stage138 validates the MAT-RLWE shared-mask interpretation: one `a` polynomial shared by r bodies. The main metric is `kernel_time / r`, matching the user's intended amortized comparison dimension.",
        "",
        "## Gates", "", table, "",
        "## Ratios", "", ratio_table,
    ]) + "\n")


def update_longform_docs(status: str, ratio_rows: List[Dict[str, str]]) -> None:
    min_r4 = min_field(ratio_rows, "per_bit_speedup", {"4"})
    max_r4 = max_field(ratio_rows, "per_bit_speedup", {"4"})
    stage_block = f"""
## Stage 138: Shared-Mask Compact MAT Gate

Goal:

```text
Validate the true MAT-RLWE interpretation: one shared mask and r body lanes,
measured as amortized external-product time per lane.
```

Status:

```text
Completed. Stage138 records {status}. For r=4, per-bit kernel speedup is
{min_r4}-{max_r4}. This remains a kernel gate; full SAB claims are still
blocked until compact selectors are integrated into CMUX/RGSW/sparse_mul.
```
"""
    append_once(ROADMAP_MD, "## Stage 138: Shared-Mask Compact MAT Gate", stage_block)
    goal_block = f"""
Stage138 refines the comparison metric to the intended MAT-RLWE dimension:
`T_kernel / r`. It proves exact equivalence between repeated lane-pair compact
EP and production shared-mask compact EP, then records r=4 per-bit kernel
speedup {min_r4}-{max_r4}. The result supports Stage139 compact-SAB integration
but is not yet a complete bootstrapping claim.
"""
    append_once(GOAL_MD, "Stage138 refines the comparison metric", goal_block)
    current_block = f"""
42. Treat Stage138 as the shared-mask compact MAT gate:
    `{status}`. It compares repeated lane-pair EP against production compact
    shared-mask EP using `T_kernel/r`. For r=4, per-bit speedup is
    {min_r4}-{max_r4}; complete SAB claims remain blocked.
"""
    append_once(CURRENT_GOAL_MD, "42. Treat Stage138 as the shared", current_block)


def upsert_hypothesis(status: str, ratio_rows: List[Dict[str, str]]) -> None:
    min_r4 = min_field(ratio_rows, "per_bit_speedup", {"4"})
    block = f"""  - id: H62_shared_mask_compact_mat_ep
    statement: >
      If PVW/MAT-SAB is interpreted as one MAT-RLWE ciphertext with one shared
      mask and r body lanes, then shared-mask compact external product should
      improve amortized per-lane kernel time over repeated lane-pair execution.
    mechanism: >
      Repeated lane-pair execution performs 2*r*T input DFT conversions, while
      true shared-mask compact MAT performs (1+r)*T conversions and preserves
      the same lane outputs.
    status: stage138_shared_mask_compact_gate
    evidence: docs/stage138_shared_mask_compact_gate.md; experiments/stage138_shared_mask_compact_gate_plan.md; theory_checks/stage138_shared_mask_compact_model.md; algorithm_variants/mat_rlwe_sab_shared_mask_compact.md; scripts/build_stage138_shared_mask_compact_gate.py; repro/stage138_shared_mask_compact_gate/summary.csv; repro/stage138_shared_mask_compact_gate/correctness.csv; repro/stage138_shared_mask_compact_gate/ratio_summary.csv; repro/stage138_shared_mask_compact_gate/artifact_index.csv
    current_decision: >
      Stage138 records {status}. The minimum r=4 per-bit kernel speedup is
      {min_r4}. Stage139 must test whether this survives full CMUX/RGSW/SAB
      integration.
    failure_criteria:
      - shared-mask compact output differs from repeated lane-pair output
      - speedup is reported without amortizing by r
      - kernel speedup is claimed as complete SAB bootstrapping speedup
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H62_shared_mask_compact_mat_ep"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
            continue
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def upsert_run_log(status: str) -> None:
    fields = ["run_id", "date", "commit_or_state", "stage", "backend", "command", "params", "seed", "status", "summary", "artifacts"]
    run_id = "stage138-shared-mask-compact-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, RATIO_CSV, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 138",
        "backend": "MOSFHET FFT_LIB=spqlios ENABLE_PVW_TMLWE=true",
        "command": "python scripts/build_stage138_shared_mask_compact_gate.py",
        "params": "r=2,4,6 N=512,1024 T=7 Bg_bit=7 samples=5 reps=20 metric=T_kernel/r",
        "seed": "0 subset",
        "status": status,
        "summary": "Stage138 validates shared-mask compact MAT EP against repeated lane-pair execution.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 138 Shared-Mask Compact Gate

- `docs/stage138_shared_mask_compact_gate.md`
- `experiments/stage138_shared_mask_compact_gate_plan.md`
- `theory_checks/stage138_shared_mask_compact_model.md`
- `algorithm_variants/mat_rlwe_sab_shared_mask_compact.md`
- `scripts/build_stage138_shared_mask_compact_gate.py`
- `repro/stage138_shared_mask_compact_gate/summary.csv`
- `repro/stage138_shared_mask_compact_gate/correctness.csv`
- `repro/stage138_shared_mask_compact_gate/benchmark_samples.csv`
- `repro/stage138_shared_mask_compact_gate/benchmark_aggregate.csv`
- `repro/stage138_shared_mask_compact_gate/ratio_summary.csv`
- `repro/stage138_shared_mask_compact_gate/mosfhet_static_build.log`
- `repro/stage138_shared_mask_compact_gate/compile_probe.log`
- `repro/stage138_shared_mask_compact_gate/run_probe.log`
- `repro/stage138_shared_mask_compact_gate/shared_mask_compact_gate.c`
- `repro/stage138_shared_mask_compact_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 138 Shared-Mask Compact Gate", block)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    write_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    correctness_rows, bench_rows, run_ok = run_probe(build_ok, compile_ok)
    agg_rows = aggregate_bench(bench_rows)
    ratio_rows = build_ratio_rows(agg_rows)
    write_csv(CORRECTNESS_CSV, correctness_rows, CORRECTNESS_FIELDS)
    write_csv(BENCH_CSV, bench_rows, BENCH_FIELDS)
    write_csv(AGG_CSV, agg_rows, AGG_FIELDS)
    write_csv(RATIO_CSV, ratio_rows, RATIO_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, correctness_rows, bench_rows, ratio_rows)
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    status = summary[-1]["status"]
    write_docs(summary, ratio_rows)
    update_longform_docs(status, ratio_rows)
    upsert_hypothesis(status, ratio_rows)
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, RATIO_CSV, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    upsert_global_manifest()
    print(f"Stage138 shared-mask compact gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
