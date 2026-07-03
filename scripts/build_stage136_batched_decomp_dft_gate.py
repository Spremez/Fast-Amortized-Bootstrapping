#!/usr/bin/env python3
"""Build Stage136 batched decompose/DFT gate."""

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
OUT_DIR = ROOT / "repro" / "stage136_batched_decomp_dft_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
RATIO_CSV = OUT_DIR / "ratio_summary.csv"
BUILD_LOG = OUT_DIR / "mosfhet_static_build.log"
COMPILE_LOG = OUT_DIR / "compile_probe.log"
RUN_LOG_TXT = OUT_DIR / "run_probe.log"
C_SOURCE = OUT_DIR / "batched_decomp_dft_gate.c"
C_BINARY = OUT_DIR / "batched_decomp_dft_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage136_batched_decomp_dft_gate.md"
PLAN_MD = ROOT / "experiments" / "stage136_batched_decomp_dft_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage136_batched_decomp_dft_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_batched_decomp_dft.md"
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
    "torus_mismatches",
    "dft_mismatches",
    "max_dft_gap",
    "tolerance",
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
]
RATIO_FIELDS = [
    "backend",
    "r",
    "N",
    "T",
    "Bg_bit",
    "seed",
    "current_mean_us",
    "batched_mean_us",
    "speedup_current_over_batched",
    "stage135_break_even_target",
    "stage135_5pct_target",
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
    include_path = Path(os.path.relpath(STAGE134_C, C_SOURCE.parent)).as_posix()
    source = f'''
#define main stage134_original_main
#include "{include_path}"
#undef main

#ifndef STAGE136_BACKEND
#define STAGE136_BACKEND "unknown"
#endif

static void stage136_exact_decompose_all(TorusPolynomial *out,
    TorusPolynomial in, int Bg_bit, int l) {{
  const int N = in->N;
  const int bit_size = (int)(sizeof(Torus) * 8);
  const uint64_t half_Bg = (1ULL << (Bg_bit - 1));
  const uint64_t h_mask = (1ULL << Bg_bit) - 1;
  uint64_t offset = 1ULL << (bit_size - l * Bg_bit - 1);
  for (int t = 0; t < l; t++) {{
    offset += (1ULL << (bit_size - t * Bg_bit - 1));
  }}
  for (int c = 0; c < N; c++) {{
    const uint64_t coeff_off = in->coeffs[c] + offset;
    for (int t = 0; t < l; t++) {{
      const uint64_t h_bit = bit_size - (t + 1) * Bg_bit;
      out[t]->coeffs[c] = ((coeff_off >> h_bit) & h_mask) - half_Bg;
    }}
  }}
}}

static void stage136_batched_decomp_dft(DFT_Polynomial *digits_shared,
    DFT_Polynomial *digits_body, TorusPolynomial *source_shared,
    TorusPolynomial *source_body, int r, int T, int Bg_bit,
    TorusPolynomial *scratch_digits) {{
  for (int q = 0; q < r; q++) {{
    stage136_exact_decompose_all(scratch_digits, source_shared[q], Bg_bit, T);
    for (int t = 0; t < T; t++) {{
      polynomial_torus_to_DFT(digits_shared[t * r + q], scratch_digits[t]);
    }}
    stage136_exact_decompose_all(scratch_digits, source_body[q], Bg_bit, T);
    for (int t = 0; t < T; t++) {{
      polynomial_torus_to_DFT(digits_body[t * r + q], scratch_digits[t]);
    }}
  }}
}}

static void stage136_compare_torus(TorusPolynomial a, TorusPolynomial b,
    uint64_t *mismatches) {{
  for (int i = 0; i < a->N; i++) {{
    if (a->coeffs[i] != b->coeffs[i]) (*mismatches)++;
  }}
}}

static void stage136_compare_dft(DFT_Polynomial a, DFT_Polynomial b,
    double tol, uint64_t *mismatches, double *max_gap) {{
  for (int i = 0; i < a->N; i++) {{
    double gap = a->coeffs[i] - b->coeffs[i];
    if (gap < 0) gap = -gap;
    if (gap > tol) (*mismatches)++;
    if (gap > *max_gap) *max_gap = gap;
  }}
}}

static void stage136_correctness_case(int r, int N, int T, int Bg_bit,
    int seed) {{
  const double tol = 0.0;
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  TorusPolynomial ref = polynomial_new_torus_polynomial(N);
  TorusPolynomial *batched = new_poly_array(T, N);
  TorusPolynomial *scratch = new_poly_array(T, N);
  DFT_Polynomial *cur_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *cur_body = new_dft_array_api(T * r, N);
  DFT_Polynomial *bat_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *bat_body = new_dft_array_api(T * r, N);
  CompactEpScratch ep_scratch = compact_ep_scratch_alloc(N);
  for (int q = 0; q < r; q++) {{
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }}
  compact_decomp_dft_only(cur_shared, cur_body, source_shared, source_body,
      r, T, Bg_bit, ep_scratch);
  stage136_batched_decomp_dft(bat_shared, bat_body, source_shared,
      source_body, r, T, Bg_bit, scratch);

  uint64_t torus_mismatches = 0;
  uint64_t dft_mismatches = 0;
  double max_dft_gap = 0.0;
  for (int q = 0; q < r; q++) {{
    stage136_exact_decompose_all(batched, source_shared[q], Bg_bit, T);
    for (int t = 0; t < T; t++) {{
      polynomial_decompose_i(ref, source_shared[q], Bg_bit, T, t);
      stage136_compare_torus(ref, batched[t], &torus_mismatches);
      stage136_compare_dft(cur_shared[t * r + q], bat_shared[t * r + q],
          tol, &dft_mismatches, &max_dft_gap);
    }}
    stage136_exact_decompose_all(batched, source_body[q], Bg_bit, T);
    for (int t = 0; t < T; t++) {{
      polynomial_decompose_i(ref, source_body[q], Bg_bit, T, t);
      stage136_compare_torus(ref, batched[t], &torus_mismatches);
      stage136_compare_dft(cur_body[t * r + q], bat_body[t * r + q],
          tol, &dft_mismatches, &max_dft_gap);
    }}
  }}
  const int ok = torus_mismatches == 0 && dft_mismatches == 0;
  printf("CORRECT,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%.9f,%s\\n",
      STAGE136_BACKEND, r, N, T, Bg_bit, seed, torus_mismatches,
      dft_mismatches, max_dft_gap, tol,
      ok ? "PASS_BATCHED_DECOMP_DFT_EQUIV" : "FAIL");

  compact_ep_scratch_free(ep_scratch);
  free_dft_array_api(bat_body, T * r);
  free_dft_array_api(bat_shared, T * r);
  free_dft_array_api(cur_body, T * r);
  free_dft_array_api(cur_shared, T * r);
  free_poly_array_local(scratch, T);
  free_poly_array_local(batched, T);
  free_polynomial(ref);
  free_poly_array_local(source_body, r);
  free_poly_array_local(source_shared, r);
}}

static void stage136_print_bench(int r, int N, int T, int Bg_bit, int seed,
    int sample, int reps, int warmups, const char *variant,
    uint64_t total_ns) {{
  const double avg_us = ((double)total_ns / (double)reps) / 1000.0;
  printf("BENCH136,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s,%" PRIu64 ",%.6f,%s\\n",
      STAGE136_BACKEND, r, N, T, Bg_bit, seed, sample, reps, warmups,
      variant, total_ns, avg_us, "PASS_BENCH_ROW");
}}

static void stage136_bench_case(int r, int N, int T, int Bg_bit, int seed,
    int samples, int reps, int warmups) {{
  TorusPolynomial *source_shared = new_poly_array(r, N);
  TorusPolynomial *source_body = new_poly_array(r, N);
  DFT_Polynomial *cur_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *cur_body = new_dft_array_api(T * r, N);
  DFT_Polynomial *bat_shared = new_dft_array_api(T * r, N);
  DFT_Polynomial *bat_body = new_dft_array_api(T * r, N);
  TorusPolynomial *scratch_digits = new_poly_array(T, N);
  CompactEpScratch ep_scratch = compact_ep_scratch_alloc(N);
  for (int q = 0; q < r; q++) {{
    fill_source(source_shared[q], q, 0, seed);
    fill_source(source_body[q], q, 1, seed);
  }}
  for (int sample = 0; sample < samples; sample++) {{
    uint64_t start = 0;
    uint64_t total = 0;
    for (int i = 0; i < warmups; i++) {{
      compact_decomp_dft_only(cur_shared, cur_body, source_shared, source_body,
          r, T, Bg_bit, ep_scratch);
    }}
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {{
      compact_decomp_dft_only(cur_shared, cur_body, source_shared, source_body,
          r, T, Bg_bit, ep_scratch);
    }}
    total = stage129_now_ns() - start;
    consume_dft_array(cur_shared, T * r);
    consume_dft_array(cur_body, T * r);
    stage136_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "current_decomp_dft", total);

    for (int i = 0; i < warmups; i++) {{
      stage136_batched_decomp_dft(bat_shared, bat_body, source_shared,
          source_body, r, T, Bg_bit, scratch_digits);
    }}
    start = stage129_now_ns();
    for (int i = 0; i < reps; i++) {{
      stage136_batched_decomp_dft(bat_shared, bat_body, source_shared,
          source_body, r, T, Bg_bit, scratch_digits);
    }}
    total = stage129_now_ns() - start;
    consume_dft_array(bat_shared, T * r);
    consume_dft_array(bat_body, T * r);
    stage136_print_bench(r, N, T, Bg_bit, seed, sample, reps, warmups,
        "batched_decomp_dft", total);
  }}
  compact_ep_scratch_free(ep_scratch);
  free_poly_array_local(scratch_digits, T);
  free_dft_array_api(bat_body, T * r);
  free_dft_array_api(bat_shared, T * r);
  free_dft_array_api(cur_body, T * r);
  free_dft_array_api(cur_shared, T * r);
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
  stage136_correctness_case(2, 512, T, Bg_bit, seed);
  stage136_correctness_case(4, 512, T, Bg_bit, seed);
  stage136_correctness_case(6, 512, T, Bg_bit, seed);
  stage136_correctness_case(2, 1024, T, Bg_bit, seed);
  stage136_correctness_case(4, 1024, T, Bg_bit, seed);
  stage136_correctness_case(6, 1024, T, Bg_bit, seed);
  stage136_bench_case(2, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(4, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(6, 512, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(2, 1024, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(4, 1024, T, Bg_bit, seed, samples, reps, warmups);
  stage136_bench_case(6, 1024, T, Bg_bit, seed, samples, reps, warmups);
  fprintf(stderr, "stage136_sink=%f\\n", g_stage129_sink);
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
        f"gcc -O2 -DSTAGE128_BACKEND=\\\"{backend}\\\" "
        f"-DSTAGE136_BACKEND=\\\"{backend}\\\" "
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


def parse_stdout(stdout: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    correctness: List[Dict[str, str]] = []
    bench: List[Dict[str, str]] = []
    for line in stdout.splitlines():
        parts = line.strip().split(",")
        if parts and parts[0] == "CORRECT" and len(parts) == len(CORRECTNESS_FIELDS) + 1:
            correctness.append(dict(zip(CORRECTNESS_FIELDS, parts[1:])))
        elif parts and parts[0] == "BENCH136" and len(parts) == len(BENCH_FIELDS) + 1:
            bench.append(dict(zip(BENCH_FIELDS, parts[1:])))
    return correctness, bench


def run_probe(build_ok: bool, compile_ok: bool) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], bool]:
    if not build_ok or not compile_ok:
        cleanup_build_outputs()
        return [], [], False
    proc = bash(f"./{rel(C_BINARY)}", timeout=180)
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
        out.append(
            {
                "backend": key[0],
                "r": key[1],
                "N": key[2],
                "T": key[3],
                "Bg_bit": key[4],
                "seed": key[5],
                "variant": key[6],
                "samples": str(len(values)),
                "mean_us": f"{statistics.mean(values):.6f}",
                "median_us": f"{statistics.median(values):.6f}",
                "min_us": f"{min(values):.6f}",
                "max_us": f"{max(values):.6f}",
                "stdev_us": f"{stdev:.6f}",
            }
        )
    return out


def stage135_targets() -> Dict[Tuple[str, str], Tuple[float, float]]:
    target_rows = read_csv(ROOT / "repro" / "stage135_decomp_dft_reuse_target_gate" / "target_matrix.csv")
    return {
        (row["r"], row["N"]): (
            float(row["required_decomp_speedup_break_even"]),
            float(row["required_decomp_speedup_5pct"]),
        )
        for row in target_rows
    }


def build_ratio_rows(agg_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_case: Dict[Tuple[str, str, str, str, str, str], Dict[str, Dict[str, str]]] = {}
    for row in agg_rows:
        key = (row["backend"], row["r"], row["N"], row["T"], row["Bg_bit"], row["seed"])
        by_case.setdefault(key, {})[row["variant"]] = row
    targets = stage135_targets()
    ratios: List[Dict[str, str]] = []
    for key, variants in sorted(by_case.items(), key=lambda item: item[0]):
        current = float(variants["current_decomp_dft"]["mean_us"])
        batched = float(variants["batched_decomp_dft"]["mean_us"])
        speedup = current / batched if batched else 0.0
        target_break, target_5pct = targets.get((key[1], key[2]), (1.0, 1.0))
        if speedup >= target_5pct:
            decision = "MEETS_STAGE135_5PCT_TARGET"
        elif speedup >= target_break:
            decision = "MEETS_STAGE135_BREAK_EVEN_TARGET"
        else:
            decision = "MISSES_STAGE135_TARGET"
        ratios.append(
            {
                "backend": key[0],
                "r": key[1],
                "N": key[2],
                "T": key[3],
                "Bg_bit": key[4],
                "seed": key[5],
                "current_mean_us": f"{current:.6f}",
                "batched_mean_us": f"{batched:.6f}",
                "speedup_current_over_batched": f"{speedup:.6f}",
                "stage135_break_even_target": f"{target_break:.6f}",
                "stage135_5pct_target": f"{target_5pct:.6f}",
                "decision": decision,
            }
        )
    return ratios


def correctness_pass(rows: List[Dict[str, str]]) -> bool:
    return len(rows) == 6 and all(
        row["status"] == "PASS_BATCHED_DECOMP_DFT_EQUIV"
        and row["torus_mismatches"] == "0"
        and row["dft_mismatches"] == "0"
        for row in rows
    )


def min_speed(rows: List[Dict[str, str]], r_filter: set[str] | None = None) -> str:
    selected = [row for row in rows if r_filter is None or row["r"] in r_filter]
    if not selected:
        return ""
    return f"{min(float(row['speedup_current_over_batched']) for row in selected):.6f}"


def build_summary(build_ok: bool, compile_ok: bool, run_ok: bool,
    correctness_rows: List[Dict[str, str]], bench_rows: List[Dict[str, str]],
    ratio_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
  corr_ok = correctness_pass(correctness_rows)
  bench_ok = bool(bench_rows) and len(ratio_rows) == 6
  r4_rows = [row for row in ratio_rows if row["r"] == "4"]
  r4_meets = bool(r4_rows) and all(row["decision"] != "MISSES_STAGE135_TARGET" for row in r4_rows)
  if not (build_ok and compile_ok and run_ok and corr_ok and bench_ok):
      decision = "FAIL_STAGE136_BATCHED_DECOMP_DFT_GATE"
  elif r4_meets:
      decision = "PASS_STAGE136_BATCHED_DECOMP_DFT_READY_FULL_EP_REBENCH"
  else:
      decision = "NEUTRAL_STAGE136_BATCHED_DECOMP_DFT_MISSES_TARGET"
  return [
      {
          "gate": "stage136_mosfhet_static_build",
          "status": "PASS" if build_ok else "FAIL",
          "metric": "make_static_spqlios",
          "value": str(build_ok).lower(),
          "evidence": rel(BUILD_LOG),
          "detail": "MOSFHET static library build for batched decompose/DFT probe.",
          "next_action": "",
      },
      {
          "gate": "stage136_probe_compile",
          "status": "PASS" if compile_ok else "FAIL",
          "metric": "gcc_probe_compile",
          "value": str(compile_ok).lower(),
          "evidence": rel(COMPILE_LOG),
          "detail": "Standalone batched decompose/DFT probe compiled.",
          "next_action": "",
      },
      {
          "gate": "stage136_probe_run",
          "status": "PASS" if run_ok else "FAIL",
          "metric": "probe_returncode",
          "value": "0" if run_ok else "nonzero_or_skipped",
          "evidence": rel(RUN_LOG_TXT),
          "detail": "Batched decompose/DFT correctness and microbench probe executed.",
          "next_action": "",
      },
      {
          "gate": "stage136_correctness",
          "status": "PASS" if corr_ok else "FAIL",
          "metric": "correctness_rows",
          "value": str(len(correctness_rows)),
          "evidence": rel(CORRECTNESS_CSV),
          "detail": "Batched decomposition exactly matches decompose_i and DFT output.",
          "next_action": "Do not interpret timing if correctness fails.",
      },
      {
          "gate": "stage136_microbench_rows",
          "status": "PASS" if bench_ok else "FAIL",
          "metric": "bench_rows;ratio_rows",
          "value": f"{len(bench_rows)};{len(ratio_rows)}",
          "evidence": f"{rel(BENCH_CSV)}; {rel(RATIO_CSV)}",
          "detail": "Current and batched decompose/DFT timings recorded.",
          "next_action": "",
      },
      {
          "gate": "stage136_r4_target",
          "status": "PASS" if r4_meets else "NEUTRAL_OR_NEGATIVE",
          "metric": "min_r4_speedup",
          "value": min_speed(ratio_rows, {"4"}),
          "evidence": rel(RATIO_CSV),
          "detail": "Stage136 must meet Stage135 r=4 break-even targets to proceed.",
          "next_action": "If neutral, reject this batching variant and choose another decompose/DFT route.",
      },
      {
          "gate": "stage136_decision",
          "status": decision,
          "metric": "promotion_policy",
          "value": "",
          "evidence": f"{rel(SUMMARY_CSV)}; {rel(RATIO_CSV)}",
          "detail": "Stage136 decides whether batched decompose/DFT is enough for full EP rebench.",
          "next_action": "Only proceed to full EP rebench if r=4 targets pass.",
      },
  ]


def table(rows: List[Dict[str, str]], fields: List[str]) -> List[str]:
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return lines


def write_docs(summary: List[Dict[str, str]], ratio_rows: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    write_text_lf(
        PLAN_MD,
        "\n".join(
            [
                "# Stage136 Batched Decompose/DFT Gate Plan",
                "",
                "Date: 2026-07-03",
                "",
                "## Objective",
                "",
                "Prototype exact batched gadget decomposition for generalized lane-pair",
                "input EP and benchmark it against Stage134's decompose_i loop.",
                "",
                "## Command",
                "",
                "```bash",
                "python scripts/build_stage136_batched_decomp_dft_gate.py",
                "```",
                "",
                "## Falsification Criteria",
                "",
                "- batched decomposition differs from polynomial_decompose_i;",
                "- DFT outputs differ;",
                "- r=4 speedup misses the Stage135 break-even target;",
                "- any result is claimed as full SAB acceleration.",
            ]
        )
        + "\n",
    )
    write_text_lf(
        THEORY_MD,
        "\n".join(
            [
                "# Stage136 Batched Decompose/DFT Model",
                "",
                "Date: 2026-07-03",
                "",
                "The candidate computes all T gadget digits for one source polynomial",
                "in one coefficient pass, matching `polynomial_decompose_i` exactly",
                "including its offset. It then performs the same number of DFT",
                "conversions as Stage134. Therefore it can only remove decomposition",
                "loop overhead, not the DFT conversion count.",
                "",
                "## Ratio Results",
                "",
                *table(ratio_rows, RATIO_FIELDS),
            ]
        )
        + "\n",
    )
    write_text_lf(
        VARIANT_MD,
        "\n".join(
            [
                "# V136: Batched Decompose/DFT",
                "",
                "## Summary",
                "",
                "- Parent algorithm: generalized lane-pair input compact EP.",
                "- Focused module: decompose/DFT blocker from Stage134/135.",
                "- Optimization target: meet r=4 Stage135 break-even target.",
                "- Status labels: `[prototype]`, `[microbench-only]`, `[not-full-sab]`.",
                f"- Decision: `{decision}`.",
            ]
        )
        + "\n",
    )
    md = [
        "# Stage136 Batched Decompose/DFT Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage136 tests the first concrete decompose/DFT optimization candidate",
        "after Stage135 quantified the target.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        md.append(f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['detail']} |")
    md += ["", "## Ratio Results", "", *table(ratio_rows, RATIO_FIELDS)]
    md += [
        "",
        "## Interpretation",
        "",
        "This candidate preserves correctness. If it misses the r=4 target, the",
        "bottleneck is likely DFT conversion count or memory traffic rather than",
        "only the `decompose_i` loop overhead.",
    ]
    write_text_lf(OUT_MD, "\n".join(md) + "\n")


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + "\n" + block.strip() + "\n")


def update_longform_docs(status: str, ratio_rows: List[Dict[str, str]]) -> None:
    min_r4 = min_speed(ratio_rows, {"4"})
    stage_block = f"""
## Stage 136: Batched Decompose/DFT Gate

Goal:

```text
Prototype exact batched decompose-to-DFT for generalized lane-pair input and
check whether it meets the Stage135 r=4 target.
```

Status:

```text
Completed. Stage136 records {status}. The minimum r=4 batched/current
decompose-DFT speedup is {min_r4}. This is a microbench-only result and does
not prove full EP, RGSW, sparse schedule, or complete `T_bootstrap/r`.
```
"""
    append_once(ROADMAP_MD, "## Stage 136: Batched Decompose/DFT Gate", stage_block)
    goal_block = f"""
Stage136 implements the first Stage135-targeted decompose/DFT optimization
candidate. It tests exact batched decomposition plus unchanged DFT conversion.
Decision: `{status}` with minimum r=4 speedup {min_r4}. This determines whether
to rebench full generalized EP or reject this batching route.
"""
    append_once(GOAL_MD, "Stage136 implements the first Stage135-targeted", goal_block)
    current_goal_block = f"""
40. Treat Stage136 as the current batched decompose/DFT gate:
    `{status}`. It checks exact equivalence against `polynomial_decompose_i`
    and benchmarks current versus batched decompose/DFT. Minimum r=4 speedup is
    {min_r4}; full SAB claims remain blocked.
"""
    append_once(CURRENT_GOAL_MD, "40. Treat Stage136 as the current batched", current_goal_block)


def upsert_hypothesis(status: str, ratio_rows: List[Dict[str, str]]) -> None:
    min_r4 = min_speed(ratio_rows, {"4"})
    block = f"""  - id: H60_batched_decomp_dft
    statement: >
      Computing all gadget digits for a lane-pair source polynomial in one
      coefficient pass may reduce Stage134's decompose/DFT blocker enough to
      meet the Stage135 r=4 break-even target.
    mechanism: >
      Stage136 implements exact batched decomposition matching
      `polynomial_decompose_i`, keeps the same DFT conversion count, and
      microbenchmarks current versus batched decompose/DFT.
    status: stage136_batched_decomp_dft_gate
    evidence: docs/stage136_batched_decomp_dft_gate.md; experiments/stage136_batched_decomp_dft_gate_plan.md; theory_checks/stage136_batched_decomp_dft_model.md; algorithm_variants/mat_rlwe_sab_batched_decomp_dft.md; scripts/build_stage136_batched_decomp_dft_gate.py; repro/stage136_batched_decomp_dft_gate/summary.csv; repro/stage136_batched_decomp_dft_gate/correctness.csv; repro/stage136_batched_decomp_dft_gate/ratio_summary.csv; repro/stage136_batched_decomp_dft_gate/artifact_index.csv
    current_decision: >
      Stage136 records {status}. The minimum r=4 decompose/DFT speedup is
      {min_r4}. If this misses Stage135 targets, the batching route is not
      sufficient and the next candidate must attack DFT conversion or memory
      traffic more directly.
    failure_criteria:
      - batched decomposition differs from `polynomial_decompose_i`
      - r=4 speedup misses Stage135 target but full EP/RGSW integration proceeds
      - this microbench is reported as complete SAB acceleration
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8")
    marker = "  - id: H60_batched_decomp_dft"
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
    run_id = "stage136-batched-decomp-dft-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, RATIO_CSV, BUILD_LOG, COMPILE_LOG, RUN_LOG_TXT, C_SOURCE, ARTIFACT_INDEX, Path(__file__).resolve()]
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 136",
        "backend": "MOSFHET FFT_LIB=spqlios",
        "command": "python scripts/build_stage136_batched_decomp_dft_gate.py",
        "params": "r=2,4,6 N=512,1024 T=7 Bg_bit=7 samples=5 reps=20",
        "seed": "0 subset",
        "status": status,
        "summary": "Stage136 tests exact batched decompose/DFT against Stage135 targets.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 136 Batched Decompose/DFT Gate

- `docs/stage136_batched_decomp_dft_gate.md`
- `experiments/stage136_batched_decomp_dft_gate_plan.md`
- `theory_checks/stage136_batched_decomp_dft_model.md`
- `algorithm_variants/mat_rlwe_sab_batched_decomp_dft.md`
- `scripts/build_stage136_batched_decomp_dft_gate.py`
- `repro/stage136_batched_decomp_dft_gate/summary.csv`
- `repro/stage136_batched_decomp_dft_gate/correctness.csv`
- `repro/stage136_batched_decomp_dft_gate/benchmark_samples.csv`
- `repro/stage136_batched_decomp_dft_gate/benchmark_aggregate.csv`
- `repro/stage136_batched_decomp_dft_gate/ratio_summary.csv`
- `repro/stage136_batched_decomp_dft_gate/mosfhet_static_build.log`
- `repro/stage136_batched_decomp_dft_gate/compile_probe.log`
- `repro/stage136_batched_decomp_dft_gate/run_probe.log`
- `repro/stage136_batched_decomp_dft_gate/batched_decomp_dft_gate.c`
- `repro/stage136_batched_decomp_dft_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 136 Batched Decompose/DFT Gate", block)


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
    print(f"Stage136 batched decompose/DFT gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not status.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
