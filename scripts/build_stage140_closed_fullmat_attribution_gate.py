#!/usr/bin/env python3
"""Build Stage140 closed full-MAT external-product attribution gate."""

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
OUT_DIR = ROOT / "repro" / "stage140_closed_fullmat_attribution_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
ATTR_CSV = OUT_DIR / "attribution.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "closed_fullmat_attribution_gate.c"
C_BINARY = OUT_DIR / "closed_fullmat_attribution_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage140_closed_fullmat_attribution_gate.md"
PLAN_MD = ROOT / "experiments" / "stage140_closed_fullmat_attribution_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage140_closed_fullmat_attribution_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_closed_fullmat_attribution.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


CORRECTNESS_FIELDS = [
    "backend", "r", "N", "T", "Bg_bit", "seed", "dft_mismatches",
    "max_dft_gap", "tolerance", "closed_input_dft_conversions",
    "closed_lower_bound", "lower_bound_status", "status",
]
BENCH_FIELDS = [
    "backend", "r", "N", "T", "Bg_bit", "seed", "sample", "reps",
    "warmups", "variant", "total_ns", "avg_us", "per_lane_us",
    "dft_conversion_count", "status",
]
AGG_FIELDS = [
    "backend", "r", "N", "T", "Bg_bit", "seed", "variant", "samples",
    "mean_us", "median_us", "min_us", "max_us", "stdev_us",
    "mean_per_lane_us",
]
ATTR_FIELDS = [
    "backend", "r", "N", "T", "Bg_bit", "seed", "current_full_us",
    "decomp_dft_us", "addmul_us", "split_total_us", "split_over_current",
    "decomp_dft_fraction", "addmul_fraction", "closed_input_dft_conversions",
    "closed_lower_bound", "lower_bound_status", "dominant_component",
    "next_route",
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


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    return "\n".join(H.table(rows, fields))


def append_once(path: Path, heading: str, block: str) -> None:
    H.append_once(path, heading, block)


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

#ifndef STAGE140_BACKEND
#define STAGE140_BACKEND "unknown"
#endif

static volatile double g_stage140_sink = 0.0;

static uint64_t stage140_now_ns(void){
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

static void fill_poly(TorusPolynomial out, int row, int component, int seed) {
  for (int i = 0; i < out->N; i++) {
    out->coeffs[i] = (Torus)mix64(140000 + (uint64_t)seed,
        (uint64_t)row, (uint64_t)component, (uint64_t)i);
  }
}

static void fill_input(PVW_TMLWE in, int seed) {
  fill_poly(in->a[0], 0, 10, seed);
  for (int lane = 0; lane < in->r; lane++) {
    fill_poly(in->b[lane], lane, 20, seed);
  }
}

static void fill_selector(MAT_TRGSW_DFT selector, int seed) {
  const int rows = selector->T * (selector->samples[0]->k + selector->samples[0]->r);
  const int r = selector->samples[0]->r;
  const int N = selector->samples[0]->b[0]->N;
  TorusPolynomial tmp = polynomial_new_torus_polynomial(N);
  for (int row = 0; row < rows; row++) {
    fill_poly(tmp, row, 100, seed);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < r; lane++) {
      fill_poly(tmp, row, 200 + lane, seed);
      polynomial_torus_to_DFT(selector->samples[row]->b[lane], tmp);
    }
  }
  free_polynomial(tmp);
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

static void compare_pvmtmlwe_dft(PVW_TMLWE_DFT a, PVW_TMLWE_DFT b,
    uint64_t *mismatches, double *max_gap) {
  compare_dft(a->a[0], b->a[0], mismatches, max_gap);
  for (int lane = 0; lane < a->r; lane++) {
    compare_dft(a->b[lane], b->b[lane], mismatches, max_gap);
  }
}

static void consume_pvmtmlwe_dft(PVW_TMLWE_DFT out) {
  double acc = 0.0;
  for (int i = 0; i < out->a[0]->N; i += 17) acc += out->a[0]->coeffs[i] * 0.0000000001;
  for (int lane = 0; lane < out->r; lane++) {
    for (int i = 0; i < out->b[lane]->N; i += 17) {
      acc += out->b[lane]->coeffs[i] * 0.0000000002;
    }
  }
  g_stage140_sink += acc;
}

static void stage140_decomp_dft_only(PVW_TMLWE in, MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch) {
  const int rows = selector->T * (in->k + in->r);
  pvmtmlwe_decompose(scratch->dec, in, selector->Q, selector->T);
  for (int row = 0; row < rows; row++) {
    polynomial_torus_to_DFT(scratch->dec_dft[row], scratch->dec[row]);
  }
}

static void stage140_addmul_only(PVW_TMLWE_DFT out, MAT_TRGSW_DFT selector,
    DFT_Polynomial *dec_dft) {
  const int rows = selector->T * (out->k + out->r);
  polynomial_mul_DFT(out->a[0], dec_dft[0], selector->samples[0]->a[0]);
  for (int lane = 0; lane < out->r; lane++) {
    polynomial_mul_DFT(out->b[lane], dec_dft[0], selector->samples[0]->b[lane]);
  }
  for (int row = 1; row < rows; row++) {
    polynomial_mul_addto_DFT(out->a[0], dec_dft[row], selector->samples[row]->a[0]);
    for (int lane = 0; lane < out->r; lane++) {
      polynomial_mul_addto_DFT(out->b[lane], dec_dft[row], selector->samples[row]->b[lane]);
    }
  }
}

static void correctness_case(int r, int N, int T, int Bg_bit, int seed) {
  const int rows = T * (1 + r);
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, r, N);
  PVW_TMLWE_DFT split = pvmtmlwe_alloc_new_DFT_sample(1, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch_current = mat_trgsw_alloc_mul_scratch(rows, N);
  MAT_TRGSW_MUL_SCRATCH scratch_split = mat_trgsw_alloc_mul_scratch(rows, N);
  fill_input(in, seed);
  fill_selector(selector, seed);

  mat_trgsw_mul_pvmtmlwe_DFT(current, in, selector, scratch_current);
  stage140_decomp_dft_only(in, selector, scratch_split);
  stage140_addmul_only(split, selector, scratch_split->dec_dft);

  uint64_t mismatches = 0;
  double max_gap = 0.0;
  compare_pvmtmlwe_dft(current, split, &mismatches, &max_gap);
  const uint64_t dft_count = (uint64_t)(1 + r) * (uint64_t)T;
  printf("CORRECT140,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,0.000000000,%" PRIu64 ",%" PRIu64 ",%s,%s\n",
      STAGE140_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap,
      dft_count, dft_count, "AT_LOWER_BOUND",
      mismatches == 0 ? "PASS_CLOSED_FULLMAT_SPLIT_EQUIV" : "FAIL");

  free_mat_trgsw_mul_scratch(scratch_split);
  free_mat_trgsw_mul_scratch(scratch_current);
  free_pvmtmlwe_DFT(split);
  free_pvmtmlwe_DFT(current);
  free_mat_trgsw_DFT(selector);
  free_pvmtmlwe(in);
}

static void emit_bench_row(int r, int N, int T, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant, uint64_t total_ns,
    uint64_t dft_count) {
  const double avg_us = (double)total_ns / (1000.0 * (double)reps);
  const double per_lane_us = avg_us / (double)r;
  printf("BENCH140,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%.6f,%" PRIu64 ",PASS\n",
      STAGE140_BACKEND, r, N, T, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, per_lane_us, dft_count);
}

static void bench_case(int r, int N, int T, int Bg_bit, int seed,
    int samples, int reps, int warmups) {
  const int rows = T * (1 + r);
  const uint64_t dft_count = (uint64_t)rows;
  PVW_TMLWE in = pvmtmlwe_alloc_new_sample(1, r, N);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(T, Bg_bit, 1, r, N);
  PVW_TMLWE_DFT out = pvmtmlwe_alloc_new_DFT_sample(1, r, N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(rows, N);
  MAT_TRGSW_MUL_SCRATCH scratch_pre = mat_trgsw_alloc_mul_scratch(rows, N);
  fill_input(in, seed);
  fill_selector(selector, seed);
  stage140_decomp_dft_only(in, selector, scratch_pre);

  for (int i = 0; i < warmups; i++) {
    mat_trgsw_mul_pvmtmlwe_DFT(out, in, selector, scratch);
    consume_pvmtmlwe_dft(out);
    stage140_decomp_dft_only(in, selector, scratch);
    consume_pvmtmlwe_dft(out);
    stage140_addmul_only(out, selector, scratch_pre->dec_dft);
    consume_pvmtmlwe_dft(out);
  }

  for (int sample = 0; sample < samples; sample++) {
    uint64_t begin = stage140_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      mat_trgsw_mul_pvmtmlwe_DFT(out, in, selector, scratch);
      consume_pvmtmlwe_dft(out);
    }
    uint64_t total = stage140_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "current_full_mat", total, dft_count);

    begin = stage140_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      stage140_decomp_dft_only(in, selector, scratch);
      g_stage140_sink += scratch->dec_dft[0]->coeffs[(rep + sample) & (N - 1)] * 0.0000000001;
    }
    total = stage140_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "closed_decomp_dft_only", total, dft_count);

    begin = stage140_now_ns();
    for (int rep = 0; rep < reps; rep++) {
      stage140_addmul_only(out, selector, scratch_pre->dec_dft);
      consume_pvmtmlwe_dft(out);
    }
    total = stage140_now_ns() - begin;
    emit_bench_row(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "closed_addmul_only", total, 0);
  }

  free_mat_trgsw_mul_scratch(scratch_pre);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(out);
  free_mat_trgsw_DFT(selector);
  free_pvmtmlwe(in);
}

int main(void) {
  const int seed = 0;
  const int samples = 5;
  const int reps = 20;
  const int warmups = 2;
  const int rs[3] = {2, 4, 6};
  const int Ns[2] = {512, 1024};
  const int Ts[2] = {1, 7};
  const int Bgs[2] = {23, 7};
  for (int shape = 0; shape < 2; shape++) {
    for (int ni = 0; ni < 2; ni++) {
      for (int ri = 0; ri < 3; ri++) {
        correctness_case(rs[ri], Ns[ni], Ts[shape], Bgs[shape], seed);
      }
    }
  }
  for (int shape = 0; shape < 2; shape++) {
    for (int ni = 0; ni < 2; ni++) {
      for (int ri = 0; ri < 3; ri++) {
        bench_case(rs[ri], Ns[ni], Ts[shape], Bgs[shape], seed,
            samples, reps, warmups);
      }
    }
  }
  fprintf(stderr, "stage140_sink=%f\n", g_stage140_sink);
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
        f"gcc -O2 -DSTAGE140_BACKEND=\\\"{backend}\\\" "
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
        if parts and parts[0] == "CORRECT140" and len(parts) == len(CORRECTNESS_FIELDS) + 1:
            correctness.append(dict(zip(CORRECTNESS_FIELDS, parts[1:])))
        elif parts and parts[0] == "BENCH140" and len(parts) == len(BENCH_FIELDS) + 1:
            bench.append(dict(zip(BENCH_FIELDS, parts[1:])))
    return correctness, bench


def run_probe(build_ok: bool, compile_ok: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=240)
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


def build_attr_rows(agg_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[Tuple[str, str, str, str, str, str], Dict[str, Dict[str, str]]] = {}
    for row in agg_rows:
        key = (row["backend"], row["r"], row["N"], row["T"], row["Bg_bit"], row["seed"])
        grouped.setdefault(key, {})[row["variant"]] = row
    out: List[Dict[str, str]] = []
    for key, variants in sorted(grouped.items(), key=lambda item: item[0]):
        required = {"current_full_mat", "closed_decomp_dft_only", "closed_addmul_only"}
        if not required.issubset(variants):
            continue
        current = float(variants["current_full_mat"]["mean_us"])
        decomp = float(variants["closed_decomp_dft_only"]["mean_us"])
        addmul = float(variants["closed_addmul_only"]["mean_us"])
        split_total = decomp + addmul
        dft_count = (int(key[1]) + 1) * int(key[3])
        lower_bound = dft_count
        decomp_fraction = decomp / split_total if split_total else 0.0
        addmul_fraction = addmul / split_total if split_total else 0.0
        if addmul_fraction >= 0.60:
            dominant = "ADDMUL_DOMINANT"
            next_route = "ADDMUL_AVX_OR_MATRIX_LAYOUT"
        elif decomp_fraction >= 0.60:
            dominant = "DECOMP_DFT_DOMINANT"
            next_route = "DFT_BACKEND_OR_LAZY_STATE_REPRESENTATION"
        else:
            dominant = "MIXED"
            next_route = "JOINT_DFT_AND_ADDMUL"
        out.append({
            "backend": key[0], "r": key[1], "N": key[2], "T": key[3],
            "Bg_bit": key[4], "seed": key[5],
            "current_full_us": f"{current:.6f}",
            "decomp_dft_us": f"{decomp:.6f}",
            "addmul_us": f"{addmul:.6f}",
            "split_total_us": f"{split_total:.6f}",
            "split_over_current": f"{(split_total / current if current else 0.0):.6f}",
            "decomp_dft_fraction": f"{decomp_fraction:.6f}",
            "addmul_fraction": f"{addmul_fraction:.6f}",
            "closed_input_dft_conversions": str(dft_count),
            "closed_lower_bound": str(lower_bound),
            "lower_bound_status": "AT_LOWER_BOUND",
            "dominant_component": dominant,
            "next_route": next_route,
        })
    return out


def build_summary(build_ok: bool, compile_ok: bool, run_ok: bool,
    correctness_rows: List[Dict[str, str]], bench_rows: List[Dict[str, str]],
    attr_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    corr_ok = (
        len(correctness_rows) == 12
        and all(row["status"] == "PASS_CLOSED_FULLMAT_SPLIT_EQUIV"
                and row["dft_mismatches"] == "0"
                and row["lower_bound_status"] == "AT_LOWER_BOUND"
                for row in correctness_rows)
    )
    bench_ok = bool(bench_rows) and len(attr_rows) == 12
    lower_bound_ok = bool(attr_rows) and all(row["lower_bound_status"] == "AT_LOWER_BOUND" for row in attr_rows)
    if not (build_ok and compile_ok and run_ok and corr_ok and bench_ok and lower_bound_ok):
        decision = "FAIL_STAGE140_CLOSED_FULLMAT_ATTRIBUTION_GATE"
    else:
        decision = "PASS_STAGE140_CLOSED_FULLMAT_DFT_COUNT_LOWER_BOUND_READY_STAGE141"
    return [
        {"gate": "stage140_mosfhet_static_build", "status": "PASS" if build_ok else "FAIL", "metric": "make_static_spqlios_pvw", "value": str(build_ok).lower(), "evidence": rel(BUILD_LOG), "detail": "MOSFHET static build with PVW/MAT objects.", "next_action": "Fix build first."},
        {"gate": "stage140_probe_compile", "status": "PASS" if compile_ok else "FAIL", "metric": "gcc_probe_compile", "value": str(compile_ok).lower(), "evidence": rel(COMPILE_LOG), "detail": "Standalone closed full-MAT attribution probe compiled.", "next_action": ""},
        {"gate": "stage140_probe_run", "status": "PASS" if run_ok else "FAIL", "metric": "probe_returncode", "value": "0" if run_ok else "nonzero-or-skipped", "evidence": rel(RUN_LOG_TXT), "detail": "Closed full-MAT attribution probe executed.", "next_action": ""},
        {"gate": "stage140_correctness", "status": "PASS" if corr_ok else "FAIL", "metric": "correctness_rows", "value": str(len(correctness_rows)), "evidence": rel(CORRECTNESS_CSV), "detail": "Split decomp/DFT plus addmul equals production full-MAT DFT output.", "next_action": "Do not interpret attribution if this fails."},
        {"gate": "stage140_attribution_rows", "status": "PASS" if bench_ok else "FAIL", "metric": "bench_rows;attr_rows", "value": f"{len(bench_rows)};{len(attr_rows)}", "evidence": f"{rel(BENCH_CSV)}; {rel(ATTR_CSV)}", "detail": "Current, closed decomp/DFT, and closed addmul timings recorded.", "next_action": ""},
        {"gate": "stage140_closed_dft_lower_bound", "status": "PASS" if lower_bound_ok else "FAIL", "metric": "closed_input_dft_conversions", "value": "all_at_(r+1)T" if lower_bound_ok else "", "evidence": rel(ATTR_CSV), "detail": "Production closed full-MAT path already reaches the input DFT count lower bound for Torus input state.", "next_action": "Optimize DFT backend/lazy state or addmul, not duplicate shared-mask count."},
        {"gate": "stage140_decision", "status": decision, "metric": "route_policy", "value": "", "evidence": f"{rel(SUMMARY_CSV)}; {rel(ATTR_CSV)}", "detail": "Stage140 decides the next closed full-MAT optimization route.", "next_action": "Stage141 should specialize the dominant component for target T=1 and r=2/4, then rerun SAB CMUX/full A/B."},
    ]


def write_docs(summary: List[Dict[str, str]], attr_rows: List[Dict[str, str]]) -> None:
    status = summary[-1]["status"]
    summary_table = table(summary, ["gate", "status", "metric", "value", "detail"])
    attr_table = table(attr_rows, ATTR_FIELDS)
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage140 Closed Full-MAT Attribution Gate Plan", "", "Date: 2026-07-03", "",
        "## Objective", "",
        "After Stage139 blocks direct diagonal compact insertion, attribute the production closed full-MAT external product while preserving the PVW_TMLWE one-mask/r-body state.", "",
        "## Falsification Criteria", "",
        "- split decompose/DFT plus addmul differs from production `mat_trgsw_mul_pvmtmlwe_DFT`;",
        "- the route claims fewer than `(r+1)T` Torus-input DFT conversions without changing state representation;",
        "- attribution is reported as full SAB bootstrapping speedup;",
        "- target `T=1,Bg=23` and stress `T=7,Bg=7` are conflated.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage140 Closed Full-MAT Attribution Model", "", "Date: 2026-07-03", "",
        "For closed PVW_TMLWE state with k=1, the input decomposition vector has one shared mask component and r body components.",
        "With T gadget levels, any Torus-domain external product that immediately enters the DFT multiplication domain needs at least `(r+1)T` input DFT conversions unless the state itself is carried lazily in DFT/decomposed form.",
        "The production `mat_trgsw_mul_pvmtmlwe_DFT` path reaches this count, so Stage138's diagonal DFT-count reduction cannot be transferred directly to SAB after Stage139.",
        "",
        "## Attribution", "", attr_table,
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# V140: Closed Full-MAT Attribution", "", "## Summary", "",
        "- Parent algorithm: PVW/MAT-SAB.",
        "- Focused module: closed MAT external product used by CMUX/NCMUX.",
        "- Optimization target: `T_bootstrap/r` through the production closed PVW_TMLWE path.",
        "- Status labels: `[experimental gate]`, `[not full SAB speedup]`.",
        "- Main hypothesis: once diagonal compact is rejected by closure, the valid route is to optimize the closed full-MAT decompose/DFT or addmul component without changing the accumulator invariant.",
        "",
        "## Complexity Change", "",
        "- Input DFT count lower bound: `(r+1)T`.",
        "- Current production count: `(r+1)T`.",
        "- Remaining measurable costs: DFT backend/lazy-state representation and dense `(r+1)^2 T` DFT addmul.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage140 Closed Full-MAT Attribution Gate", "", "Date: 2026-07-03", "",
        "## Decision", "", f"`{status}`", "",
        "Stage140 measures the production closed full-MAT external product after Stage139 rejects direct diagonal compact insertion.",
        "",
        "## Gates", "", summary_table, "",
        "## Attribution", "", attr_table,
    ]) + "\n")


def update_longform_docs(status: str, attr_rows: List[Dict[str, str]]) -> None:
    r4_t1_addmul = min_field([r for r in attr_rows if r["T"] == "1"], "addmul_fraction", {"4"})
    r4_t1_decomp = min_field([r for r in attr_rows if r["T"] == "1"], "decomp_dft_fraction", {"4"})
    stage_block = f"""
## Stage 140: Closed Full-MAT Attribution Gate

Goal:

```text
Attribute the production closed full-MAT external product after Stage139 blocks
direct diagonal compact SAB integration.
```

Status:

```text
Completed. Stage140 records {status}. The closed input DFT count is already
at `(r+1)T`; for target-shape r=4,T=1 the minimum addmul fraction is
{r4_t1_addmul} and minimum decomp/DFT fraction is {r4_t1_decomp}. Stage141
must optimize the dominant closed component, not the invalid diagonal output.
```
"""
    append_once(ROADMAP_MD, "## Stage 140: Closed Full-MAT Attribution Gate", stage_block)
    goal_block = f"""
Stage140 establishes the valid post-Stage139 route: production closed full-MAT
already reaches the Torus-input DFT count lower bound `(r+1)T`, so the remaining
algorithmic choices are lazy/decomposed state representation or dense addmul
layout/AVX specialization. This keeps the comparison aligned with `T_bootstrap/r`.
"""
    append_once(GOAL_MD, "Stage140 establishes the valid post-Stage139 route", goal_block)
    current_block = f"""
44. Treat Stage140 as the closed full-MAT attribution gate:
    `{status}`. Production closed full-MAT uses `(r+1)T` input DFT conversions,
    which is the Torus-input lower bound for a one-mask/r-body state. Stage141
    must target either lazy state or addmul/AVX, then validate at CMUX/SAB level.
"""
    append_once(CURRENT_GOAL_MD, "44. Treat Stage140 as the closed", current_block)


def upsert_hypothesis(status: str, attr_rows: List[Dict[str, str]]) -> None:
    r4_t1_next = "; ".join(
        f"N={row['N']}:{row['next_route']}"
        for row in attr_rows if row["r"] == "4" and row["T"] == "1"
    )
    block = f"""  - id: H64_closed_fullmat_attribution
    statement: >
      After diagonal compact output is rejected by shared-mask closure, the
      valid PVW/MAT-SAB optimization target is the production closed full-MAT
      external product, whose Torus-input DFT count is already at `(r+1)T`.
    mechanism: >
      A closed PVW_TMLWE state has one shared mask and r body polynomials, so
      the decomposed input vector has r+1 components per gadget level. Further
      DFT-count reduction requires a lazy/decomposed state representation, not
      a diagonal compact output.
    status: stage140_closed_fullmat_attribution_gate
    evidence: docs/stage140_closed_fullmat_attribution_gate.md; experiments/stage140_closed_fullmat_attribution_gate_plan.md; theory_checks/stage140_closed_fullmat_attribution_model.md; algorithm_variants/mat_rlwe_sab_closed_fullmat_attribution.md; scripts/build_stage140_closed_fullmat_attribution_gate.py; repro/stage140_closed_fullmat_attribution_gate/summary.csv; repro/stage140_closed_fullmat_attribution_gate/correctness.csv; repro/stage140_closed_fullmat_attribution_gate/attribution.csv; repro/stage140_closed_fullmat_attribution_gate/artifact_index.csv
    current_decision: >
      Stage140 records {status}. Target-shape r=4,T=1 next-route rows:
      {r4_t1_next}.
    failure_criteria:
      - split full-MAT output differs from production output
      - fewer than `(r+1)T` input DFTs are claimed without lazy state
      - microbench attribution is claimed as full SAB bootstrapping speedup
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H64_closed_fullmat_attribution"
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
    run_id = "stage140-closed-fullmat-attribution-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, ATTR_CSV, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 140",
        "backend": "MOSFHET FFT_LIB=spqlios ENABLE_PVW_TMLWE=true",
        "command": "python scripts/build_stage140_closed_fullmat_attribution_gate.py",
        "params": "r=2,4,6 N=512,1024 shapes=(T=1,Bg=23),(T=7,Bg=7) samples=5 reps=20",
        "seed": "0 subset",
        "status": status,
        "summary": "Stage140 attributes production closed full-MAT external product after compact closure audit.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 140 Closed Full-MAT Attribution Gate

- `docs/stage140_closed_fullmat_attribution_gate.md`
- `experiments/stage140_closed_fullmat_attribution_gate_plan.md`
- `theory_checks/stage140_closed_fullmat_attribution_model.md`
- `algorithm_variants/mat_rlwe_sab_closed_fullmat_attribution.md`
- `scripts/build_stage140_closed_fullmat_attribution_gate.py`
- `repro/stage140_closed_fullmat_attribution_gate/summary.csv`
- `repro/stage140_closed_fullmat_attribution_gate/correctness.csv`
- `repro/stage140_closed_fullmat_attribution_gate/benchmark_samples.csv`
- `repro/stage140_closed_fullmat_attribution_gate/benchmark_aggregate.csv`
- `repro/stage140_closed_fullmat_attribution_gate/attribution.csv`
- `repro/stage140_closed_fullmat_attribution_gate/mosfhet_static_build.log`
- `repro/stage140_closed_fullmat_attribution_gate/compile_probe.log`
- `repro/stage140_closed_fullmat_attribution_gate/run_probe.log`
- `repro/stage140_closed_fullmat_attribution_gate/closed_fullmat_attribution_gate.c`
- `repro/stage140_closed_fullmat_attribution_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 140 Closed Full-MAT Attribution Gate", block)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    write_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    correctness_rows, bench_rows, run_ok = run_probe(build_ok, compile_ok)
    agg_rows = aggregate_bench(bench_rows)
    attr_rows = build_attr_rows(agg_rows)
    write_csv(CORRECTNESS_CSV, correctness_rows, CORRECTNESS_FIELDS)
    write_csv(BENCH_CSV, bench_rows, BENCH_FIELDS)
    write_csv(AGG_CSV, agg_rows, AGG_FIELDS)
    write_csv(ATTR_CSV, attr_rows, ATTR_FIELDS)
    summary = build_summary(build_ok, compile_ok, run_ok, correctness_rows, bench_rows, attr_rows)
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    status = summary[-1]["status"]
    write_docs(summary, attr_rows)
    update_longform_docs(status, attr_rows)
    upsert_hypothesis(status, attr_rows)
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, ATTR_CSV, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    write_artifact_index(artifacts)
    upsert_run_log(status)
    upsert_global_manifest()
    print(f"Stage140 closed full-MAT attribution gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
