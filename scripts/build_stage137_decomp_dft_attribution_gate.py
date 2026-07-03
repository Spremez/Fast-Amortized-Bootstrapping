#!/usr/bin/env python3
"""Build Stage137 decompose/DFT attribution gate."""

from __future__ import annotations

import csv
import hashlib
import os
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
STAGE134_C = ROOT / "repro" / "stage134_generalized_lane_pair_input_ep_gate" / "generalized_lane_pair_input_ep_gate.c"
STAGE135_TARGET = ROOT / "repro" / "stage135_decomp_dft_reuse_target_gate" / "target_matrix.csv"
OUT_DIR = ROOT / "repro" / "stage137_decomp_dft_attribution_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
ATTR_CSV = OUT_DIR / "attribution.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "decomp_dft_attribution_gate.c"
C_BINARY = OUT_DIR / "decomp_dft_attribution_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage137_decomp_dft_attribution_gate.md"
PLAN_MD = ROOT / "experiments" / "stage137_decomp_dft_attribution_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage137_decomp_dft_attribution_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_decomp_dft_attribution.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"


CORRECTNESS_FIELDS = ["backend", "r", "N", "T", "Bg_bit", "seed", "dft_mismatches", "max_dft_gap", "tolerance", "status"]
BENCH_FIELDS = ["backend", "r", "N", "T", "Bg_bit", "seed", "sample", "reps", "warmups", "variant", "total_ns", "avg_us", "status"]
AGG_FIELDS = ["backend", "r", "N", "T", "Bg_bit", "seed", "variant", "samples", "mean_us", "median_us", "min_us", "max_us", "stdev_us"]
ATTR_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "Bg_bit",
    "seed",
    "current_full_us",
    "decompose_only_us",
    "dft_only_us",
    "split_total_us",
    "split_over_current",
    "decompose_fraction",
    "dft_fraction",
    "stage135_break_even_target",
    "required_dft_speedup_if_decomp_unchanged",
    "dominant_blocker",
    "decision",
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


def write_c_source() -> None:
    include_path = Path(os.path.relpath(STAGE134_C, C_SOURCE.parent)).as_posix()
    source = f'''
#define main stage134_original_main
#include "{include_path}"
#undef main

#ifndef STAGE137_BACKEND
#define STAGE137_BACKEND "unknown"
#endif

static void stage137_decompose_only(TorusPolynomial *digits_shared,
    TorusPolynomial *digits_body, TorusPolynomial *source_shared,
    TorusPolynomial *source_body, int r, int T, int Bg_bit) {{
  for (int q = 0; q < r; q++) {{
    for (int t = 0; t < T; t++) {{
      const int idx = t * r + q;
      polynomial_decompose_i(digits_shared[idx], source_shared[q], Bg_bit, T, t);
      polynomial_decompose_i(digits_body[idx], source_body[q], Bg_bit, T, t);
    }}
  }}
}}

static void stage137_dft_only(DFT_Polynomial *out_shared,
    DFT_Polynomial *out_body, TorusPolynomial *digits_shared,
    TorusPolynomial *digits_body, int r, int T) {{
  for (int t = 0; t < T; t++) {{
    for (int q = 0; q < r; q++) {{
      const int idx = t * r + q;
      polynomial_torus_to_DFT(out_shared[idx], digits_shared[idx]);
      polynomial_torus_to_DFT(out_body[idx], digits_body[idx]);
    }}
  }}
}}

static void stage137_compare_dft(DFT_Polynomial a, DFT_Polynomial b,
    double tol, uint64_t *mismatches, double *max_gap) {{
  for (int i = 0; i < a->N; i++) {{
    double gap = a->coeffs[i] - b->coeffs[i];
    if (gap < 0) gap = -gap;
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }}
}}

static void stage137_correctness_case(int r, int N, int T, int Bg_bit,
    int seed) {{
  const double tol = 0.0;
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *digits_shared = new_poly_array(T * r, N);
  TorusPolynomial *digits_body = new_poly_array(T * r, N);
  DFT_Polynomial *current_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *current_body = new_dft_array_api(T * r, N);
  DFT_Polynomial *split_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *split_body = new_dft_array_api(T * r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);
  for (int q = 0; q < r; q++) {{
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }}
  compact_decomp_dft_only(current_shared, current_body, source_shared,
      source_body, r, T, Bg_bit, scratch);
  stage137_decompose_only(digits_shared, digits_body, source_shared,
      source_body, r, T, Bg_bit);
  stage137_dft_only(split_shared, split_body, digits_shared, digits_body, r, T);
  uint64_t mismatches = 0;
  double max_gap = 0.0;
  for (int i = 0; i < T * r; i++) {{
    stage137_compare_dft(current_shared[i], split_shared[i], tol, &mismatches, &max_gap);
    stage137_compare_dft(current_body[i], split_body[i], tol, &mismatches, &max_gap);
  }}
  printf("CORRECT137,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%.9f,%.9f,%s\\n",
      STAGE137_BACKEND, r, N, T, Bg_bit, seed, mismatches, max_gap, tol,
      mismatches == 0 ? "PASS_SPLIT_DECOMP_DFT_EQUIV" : "FAIL");
  compact_ep_scratch_free(scratch);
  free_dft_array_api(split_body, T * r);
  free_dft_array_api(split_shared, T * r);
  free_dft_array_api(current_body, T * r);
  free_dft_array_api(current_shared, T * r);
  free_poly_array_local(digits_body, T * r);
  free_poly_array_local(digits_shared, T * r);
  free_poly_array_local(source_body, r);
  free_poly_array_local(source_shared, r);
}}

static void stage137_print_bench(int r, int N, int T, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant, uint64_t total_ns) {{
  const double avg_us = ((double)total_ns / (double)reps) / 1000.0;
  printf("BENCH137,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%s\\n",
      STAGE137_BACKEND, r, N, T, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, "PASS_BENCH_ROW");
}}

static void stage137_bench_case(int r, int N, int T, int Bg_bit, int seed,
    int samples, int reps, int warmups) {{
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial *digits_shared = new_poly_array(T * r, N);
  TorusPolynomial *digits_body = new_poly_array(T * r, N);
  DFT_Polynomial *current_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *current_body = new_dft_array_api(T * r, N);
  DFT_Polynomial *split_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *split_body = new_dft_array_api(T * r, N);
  CompactEpScratch scratch = compact_ep_scratch_alloc(N);
  for (int q = 0; q < r; q++) {{
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }}
  stage137_decompose_only(digits_shared, digits_body, source_shared,
      source_body, r, T, Bg_bit);
  for (int sample = 0; sample < samples; sample++) {{
    uint64_t start = 0;
    uint64_t total = 0;
    for (int i = 0; i < warmups; i++) {{
      compact_decomp_dft_only(current_shared, current_body, source_shared,
          source_body, r, T, Bg_bit, scratch);
    }}
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {{
      compact_decomp_dft_only(current_shared, current_body, source_shared,
          source_body, r, T, Bg_bit, scratch);
    }}
    total = stage129_now_ns() - start;
    consume_dft_array(current_shared, T * r);
    consume_dft_array(current_body, T * r);
    stage137_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "current_full_decomp_dft", total);

    for (int i = 0; i < warmups; i++) {{
      stage137_decompose_only(digits_shared, digits_body, source_shared,
          source_body, r, T, Bg_bit);
    }}
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {{
      stage137_decompose_only(digits_shared, digits_body, source_shared,
          source_body, r, T, Bg_bit);
    }}
    total = stage129_now_ns() - start;
    stage137_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "decompose_only", total);

    for (int i = 0; i < warmups; i++) {{
      stage137_dft_only(split_shared, split_body, digits_shared, digits_body, r, T);
    }}
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {{
      stage137_dft_only(split_shared, split_body, digits_shared, digits_body, r, T);
    }}
    total = stage129_now_ns() - start;
    consume_dft_array(split_shared, T * r);
    consume_dft_array(split_body, T * r);
    stage137_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "dft_only", total);
  }}
  compact_ep_scratch_free(scratch);
  free_dft_array_api(split_body, T * r);
  free_dft_array_api(split_shared, T * r);
  free_dft_array_api(current_body, T * r);
  free_dft_array_api(current_shared, T * r);
  free_poly_array_local(digits_body, T * r);
  free_poly_array_local(digits_shared, T * r);
  free_poly_array_local(source_body, r);
  free_poly_array_local(source_shared, r);
}}

int main(void) {{
  const int T = 7;
  const int Bg_bit = 7;
  const int seed = 0;
  const int samples = 5;
  const int reps = 20;
  const int warmups = 2;
  stage137_correctness_case(2, 512, T, Bg_bit, seed);
  stage137_correctness_case(4, 512, T, Bg_bit, seed);
  stage137_correctness_case(6, 512, T, Bg_bit, seed);
  stage137_correctness_case(2, 1024, T, Bg_bit, seed);
  stage137_correctness_case(4, 1024, T, Bg_bit, seed);
  stage137_correctness_case(6, 1024, T, Bg_bit, seed);
  stage137_bench_case(2, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(4, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(6, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(2, 1024, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(4, 1024, T, Bg_bit, seed, samples, reps, warmups);
  stage137_bench_case(6, 1024, T, Bg_bit, seed, samples, reps, warmups);
  fprintf(stderr, "stage137_sink=%f\\n", g_stage129_sink);
  return 0;
}}
'''
    write_text_lf(C_SOURCE, source.lstrip())


def build_mosfhet_static(backend: str) -> bool:
    cmd = (
        "cd src/mosfhet && make clean >/dev/null 2>&1 || true && "
        f"make static FFT_LIB={backend} A_PRNG=none ENABLE_VAES=false "
        "ENABLE_PVW_TMLWE=false -j$(nproc)"
    )
    proc = bash(cmd, timeout=180)
    write_text_lf(BUILD_LOG, "\n".join([
        f"command: {cmd}", f"returncode: {proc.returncode}", "--- stdout ---",
        sanitize_log(proc.stdout), "--- stderr ---", sanitize_log(proc.stderr)
    ]) + "\n")
    return proc.returncode == 0


def compile_probe(backend: str) -> bool:
    cmd = (
        f"gcc -O2 -DSTAGE128_BACKEND=\\\"{backend}\\\" "
        f"-DSTAGE137_BACKEND=\\\"{backend}\\\" "
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
        if parts and parts[0] == "CORRECT137" and len(parts) == len(CORRECTNESS_FIELDS) + 1:
            correctness.append(dict(zip(CORRECTNESS_FIELDS, parts[1:])))
        elif parts and parts[0] == "BENCH137" and len(parts) == len(BENCH_FIELDS) + 1:
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
    groups: Dict[Tuple[str, str, str, str, str, str, str], List[float]] = {}
    for row in rows:
        key = (row["backend"], row["r"], row["N"], row["T"], row["Bg_bit"], row["seed"], row["variant"])
        groups.setdefault(key, []).append(float(row["avg_us"]))
    out: List[Dict[str, str]] = []
    for key, values in sorted(groups.items(), key=lambda item: item[0]):
        stdev = statistics.stdev(values) if len(values) > 1 else 0.0
        out.append({
            "backend": key[0], "r": key[1], "N": key[2], "T": key[3],
            "Bg_bit": key[4], "seed": key[5], "variant": key[6],
            "samples": str(len(values)), "mean_us": f"{statistics.mean(values):.6f}",
            "median_us": f"{statistics.median(values):.6f}",
            "min_us": f"{min(values):.6f}", "max_us": f"{max(values):.6f}",
            "stdev_us": f"{stdev:.6f}",
        })
    return out


def stage135_targets() -> Dict[Tuple[str, str], float]:
    return {
        (row["r"], row["N"]): float(row["required_decomp_speedup_break_even"])
        for row in read_csv(STAGE135_TARGET)
    }


def build_attribution_rows(agg_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_case: Dict[Tuple[str, str, str, str, str, str], Dict[str, Dict[str, str]]] = {}
    for row in agg_rows:
        key = (row["backend"], row["r"], row["N"], row["T"], row["Bg_bit"], row["seed"])
        by_case.setdefault(key, {})[row["variant"]] = row
    targets = stage135_targets()
    rows: List[Dict[str, str]] = []
    for key, variants in sorted(by_case.items(), key=lambda item: item[0]):
        full = float(variants["current_full_decomp_dft"]["mean_us"])
        decomp = float(variants["decompose_only"]["mean_us"])
        dft = float(variants["dft_only"]["mean_us"])
        split_total = decomp + dft
        dft_fraction = dft / split_total if split_total else 0.0
        decomp_fraction = decomp / split_total if split_total else 0.0
        target = targets.get((key[1], key[2]), 1.0)
        target_total = full / target if target else full
        if target_total <= decomp:
            required_dft_speed = 999.0
        else:
            required_dft_speed = dft / (target_total - decomp)
        if dft_fraction >= 0.60:
            dominant = "DFT_CONVERSION_DOMINANT"
        elif decomp_fraction >= 0.50:
            dominant = "DECOMPOSE_DOMINANT"
        else:
            dominant = "MIXED"
        if dominant == "DFT_CONVERSION_DOMINANT" and required_dft_speed <= 1.50:
            decision = "DFT_ROUTE_PLAUSIBLE"
        elif dominant == "DFT_CONVERSION_DOMINANT":
            decision = "DFT_ROUTE_HIGH_RISK"
        else:
            decision = "NON_DFT_OR_MIXED_ROUTE"
        rows.append({
            "backend": key[0], "r": key[1], "N": key[2], "T": key[3],
            "Bg_bit": key[4], "seed": key[5],
            "current_full_us": f"{full:.6f}",
            "decompose_only_us": f"{decomp:.6f}",
            "dft_only_us": f"{dft:.6f}",
            "split_total_us": f"{split_total:.6f}",
            "split_over_current": f"{split_total / full if full else 0.0:.6f}",
            "decompose_fraction": f"{decomp_fraction:.6f}",
            "dft_fraction": f"{dft_fraction:.6f}",
            "stage135_break_even_target": f"{target:.6f}",
            "required_dft_speedup_if_decomp_unchanged": f"{required_dft_speed:.6f}",
            "dominant_blocker": dominant,
            "decision": decision,
        })
    return rows


def correctness_pass(rows: List[Dict[str, str]]) -> bool:
    return len(rows) == 6 and all(
        row["status"] == "PASS_SPLIT_DECOMP_DFT_EQUIV"
        and row["dft_mismatches"] == "0"
        for row in rows
    )


def min_field(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    selected = [row for row in rows if r_filter is None or row["r"] in r_filter]
    if not selected:
        return ""
    return f"{min(float(row[field]) for row in selected):.6f}"


def max_field(rows: List[Dict[str, str]], field: str, r_filter: set[str] | None = None) -> str:
    selected = [row for row in rows if r_filter is None or row["r"] in r_filter]
    if not selected:
        return ""
    return f"{max(float(row[field]) for row in selected):.6f}"


def build_summary(build_ok: bool, compile_ok: bool, run_ok: bool,
    correctness_rows: List[Dict[str, str]], bench_rows: List[Dict[str, str]],
    attr_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    corr_ok = correctness_pass(correctness_rows)
    bench_ok = bool(bench_rows) and len(attr_rows) == 6
    r4_dft = [row for row in attr_rows if row["r"] == "4" and row["dominant_blocker"] == "DFT_CONVERSION_DOMINANT"]
    if not (build_ok and compile_ok and run_ok and corr_ok and bench_ok):
        decision = "FAIL_STAGE137_DECOMP_DFT_ATTRIBUTION_GATE"
    elif len(r4_dft) == 2:
        decision = "PASS_STAGE137_DFT_CONVERSION_DOMINANT_READY_DFT_ROUTE"
    else:
        decision = "NEUTRAL_STAGE137_ATTRIBUTION_MIXED_OR_DECOMP_DOMINANT"
    return [
        {"gate": "stage137_mosfhet_static_build", "status": "PASS" if build_ok else "FAIL", "metric": "make_static_spqlios", "value": str(build_ok).lower(), "evidence": rel(BUILD_LOG), "detail": "MOSFHET static build for attribution probe.", "next_action": ""},
        {"gate": "stage137_probe_compile", "status": "PASS" if compile_ok else "FAIL", "metric": "gcc_probe_compile", "value": str(compile_ok).lower(), "evidence": rel(COMPILE_LOG), "detail": "Standalone attribution probe compiled.", "next_action": ""},
        {"gate": "stage137_probe_run", "status": "PASS" if run_ok else "FAIL", "metric": "probe_returncode", "value": "0" if run_ok else "nonzero_or_skipped", "evidence": rel(RUN_LOG_TXT), "detail": "Attribution probe executed.", "next_action": ""},
        {"gate": "stage137_correctness", "status": "PASS" if corr_ok else "FAIL", "metric": "correctness_rows", "value": str(len(correctness_rows)), "evidence": rel(CORRECTNESS_CSV), "detail": "Split decompose-only plus DFT-only output matches current full decomp/DFT.", "next_action": "Do not interpret attribution if this fails."},
        {"gate": "stage137_attribution_rows", "status": "PASS" if bench_ok else "FAIL", "metric": "bench_rows;attr_rows", "value": f"{len(bench_rows)};{len(attr_rows)}", "evidence": f"{rel(BENCH_CSV)}; {rel(ATTR_CSV)}", "detail": "Current full, decompose-only, and DFT-only timings recorded.", "next_action": ""},
        {"gate": "stage137_r4_dft_fraction", "status": "RECORDED", "metric": "min_r4_dft_fraction;max_required_dft_speedup_r4", "value": f"{min_field(attr_rows, 'dft_fraction', {'4'})};{max_field(attr_rows, 'required_dft_speedup_if_decomp_unchanged', {'4'})}", "evidence": rel(ATTR_CSV), "detail": "DFT fraction and required DFT-only speedup for r=4.", "next_action": ""},
        {"gate": "stage137_decision", "status": decision, "metric": "promotion_policy", "value": "", "evidence": f"{rel(SUMMARY_CSV)}; {rel(ATTR_CSV)}", "detail": "Stage137 decides the next decompose/DFT optimization route.", "next_action": "If DFT-dominant, Stage138 should target DFT conversion count/layout directly."},
    ]


def table(rows: List[Dict[str, str]], fields: List[str]) -> List[str]:
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return lines


def write_docs(summary: List[Dict[str, str]], attr_rows: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage137 Decompose/DFT Attribution Gate Plan", "", "Date: 2026-07-03", "",
        "## Objective", "", "Split Stage134/136 decompose/DFT time into decompose-only and DFT-only parts to choose the next finite implementation route.", "",
        "## Command", "", "```bash", "python scripts/build_stage137_decomp_dft_attribution_gate.py", "```", "",
        "## Falsification Criteria", "", "- split output does not match current full decompose/DFT;", "- attribution rows are missing;", "- DFT route is selected without r=4 DFT-dominant evidence;", "- any result is claimed as full SAB acceleration.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage137 Decompose/DFT Attribution Model", "", "Date: 2026-07-03", "",
        "Stage136 showed exact batched decomposition is slower, so Stage137 decomposes the bottleneck into three measured components: current full decompose/DFT, decompose-only, and DFT-only over precomputed digits.",
        "",
        "A DFT route is justified only if r=4 DFT-only time is the dominant split component and the required DFT-only speedup to meet Stage135 is finite and plausible.",
        "", "## Attribution", "", *table(attr_rows, ATTR_FIELDS),
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# V137: Decompose/DFT Attribution", "", "## Summary", "",
        "- Parent algorithm: generalized lane-pair input compact EP.",
        "- Focused module: decompose/DFT blocker.",
        "- Optimization target: choose DFT-count/layout versus decomposition route.",
        "- Status labels: `[attribution]`, `[microbench-only]`, `[not-full-sab]`.",
        f"- Decision: `{decision}`.",
    ]) + "\n")
    md = [
        "# Stage137 Decompose/DFT Attribution Gate", "", "Date: 2026-07-03", "",
        "## Decision", "", f"`{decision}`", "",
        "Stage137 splits the Stage134/136 decompose-DFT blocker into decompose-only and DFT-only timing.",
        "", "## Gates", "", "| gate | status | metric | value | detail |", "|---|---|---|---|---|",
    ]
    for row in summary:
        md.append(f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['detail']} |")
    md += ["", "## Attribution", "", *table(attr_rows, ATTR_FIELDS), "", "## Interpretation", ""]
    md += [
        "If r=4 is DFT-dominant, the next candidate should reduce DFT conversion count or change DFT data layout. If it is mixed, Stage138 must not assume a DFT-only fix is enough.",
    ]
    write_text_lf(OUT_MD, "\n".join(md) + "\n")


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + "\n" + block.strip() + "\n")


def update_longform_docs(status: str, attr_rows: List[Dict[str, str]]) -> None:
    min_r4_dft = min_field(attr_rows, "dft_fraction", {"4"})
    max_r4_req = max_field(attr_rows, "required_dft_speedup_if_decomp_unchanged", {"4"})
    stage_block = f"""
## Stage 137: Decompose/DFT Attribution Gate

Goal:

```text
Split generalized lane-pair input decompose/DFT timing into decompose-only and
DFT-only parts after Stage136 rejected simple batched decomposition.
```

Status:

```text
Completed. Stage137 records {status}. For r=4, minimum DFT fraction is
{min_r4_dft} and maximum required DFT-only speedup is {max_r4_req}. This is an
attribution gate only, not full EP or SAB acceleration.
```
"""
    append_once(ROADMAP_MD, "## Stage 137: Decompose/DFT Attribution Gate", stage_block)
    goal_block = f"""
Stage137 provides the next empirical route choice after Stage136: r=4 DFT
fraction is at least {min_r4_dft}, with required DFT-only speedup up to
{max_r4_req}. This determines whether Stage138 should target DFT conversion
count/layout or a broader mixed memory-traffic path.
"""
    append_once(GOAL_MD, "Stage137 provides the next empirical route choice", goal_block)
    current_block = f"""
41. Treat Stage137 as the current decompose/DFT attribution gate:
    `{status}`. It measures current full decompose/DFT, decompose-only, and
    DFT-only timing. For r=4, minimum DFT fraction is {min_r4_dft}; full SAB
    claims remain blocked.
"""
    append_once(CURRENT_GOAL_MD, "41. Treat Stage137 as the current decompose", current_block)


def upsert_hypothesis(status: str, attr_rows: List[Dict[str, str]]) -> None:
    min_r4_dft = min_field(attr_rows, "dft_fraction", {"4"})
    block = f"""  - id: H61_decomp_dft_attribution
    statement: >
      After Stage136 rejects simple batched decomposition, the next valid route
      depends on whether Stage134's generalized lane-pair decompose/DFT blocker
      is dominated by DFT conversion or by decomposition/memory traffic.
    mechanism: >
      Stage137 measures current full decompose/DFT, decompose-only, and
      DFT-only over precomputed digits, while verifying that split output
      equals current output.
    status: stage137_decomp_dft_attribution_gate
    evidence: docs/stage137_decomp_dft_attribution_gate.md; experiments/stage137_decomp_dft_attribution_gate_plan.md; theory_checks/stage137_decomp_dft_attribution_model.md; algorithm_variants/mat_rlwe_sab_decomp_dft_attribution.md; scripts/build_stage137_decomp_dft_attribution_gate.py; repro/stage137_decomp_dft_attribution_gate/summary.csv; repro/stage137_decomp_dft_attribution_gate/correctness.csv; repro/stage137_decomp_dft_attribution_gate/attribution.csv; repro/stage137_decomp_dft_attribution_gate/artifact_index.csv
    current_decision: >
      Stage137 records {status}. The minimum r=4 DFT fraction is {min_r4_dft}.
      Stage138 must follow the measured attribution rather than assuming a
      decompose-only fix.
    failure_criteria:
      - split output differs from current decompose/DFT
      - DFT route is chosen without r=4 DFT-dominant evidence
      - attribution microbench is reported as full SAB speedup
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H61_decomp_dft_attribution"
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
    run_id = "stage137-decomp-dft-attribution-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, ATTR_CSV, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 137",
        "backend": "MOSFHET FFT_LIB=spqlios",
        "command": "python scripts/build_stage137_decomp_dft_attribution_gate.py",
        "params": "r=2,4,6 N=512,1024 T=7 Bg_bit=7 samples=5 reps=20",
        "seed": "0 subset",
        "status": status,
        "summary": "Stage137 attributes generalized lane-pair decompose/DFT timing.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 137 Decompose/DFT Attribution Gate

- `docs/stage137_decomp_dft_attribution_gate.md`
- `experiments/stage137_decomp_dft_attribution_gate_plan.md`
- `theory_checks/stage137_decomp_dft_attribution_model.md`
- `algorithm_variants/mat_rlwe_sab_decomp_dft_attribution.md`
- `scripts/build_stage137_decomp_dft_attribution_gate.py`
- `repro/stage137_decomp_dft_attribution_gate/summary.csv`
- `repro/stage137_decomp_dft_attribution_gate/correctness.csv`
- `repro/stage137_decomp_dft_attribution_gate/benchmark_samples.csv`
- `repro/stage137_decomp_dft_attribution_gate/benchmark_aggregate.csv`
- `repro/stage137_decomp_dft_attribution_gate/attribution.csv`
- `repro/stage137_decomp_dft_attribution_gate/mosfhet_static_build.log`
- `repro/stage137_decomp_dft_attribution_gate/compile_probe.log`
- `repro/stage137_decomp_dft_attribution_gate/run_probe.log`
- `repro/stage137_decomp_dft_attribution_gate/decomp_dft_attribution_gate.c`
- `repro/stage137_decomp_dft_attribution_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 137 Decompose/DFT Attribution Gate", block)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = "spqlios"
    write_c_source()
    build_ok = build_mosfhet_static(backend)
    compile_ok = compile_probe(backend) if build_ok else False
    correctness_rows, bench_rows, run_ok = run_probe(build_ok, compile_ok)
    agg_rows = aggregate_bench(bench_rows)
    attr_rows = build_attribution_rows(agg_rows)
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
    print(f"Stage137 decompose/DFT attribution gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
