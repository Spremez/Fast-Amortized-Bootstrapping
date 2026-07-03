#!/usr/bin/env python3
"""Stage212: standalone multirow reverse-DFT backend API probe."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT = ROOT / "repro" / "stage212_multirow_fft_api_probe"
C_SOURCE = OUT / "stage212_multirow_fft_api_probe.c"
BINARY = OUT / "stage212_multirow_fft_api_probe"

ENV_CSV = OUT / "environment.csv"
CORRECTNESS_CSV = OUT / "correctness.csv"
SAMPLES_CSV = OUT / "benchmark_samples.csv"
AGG_CSV = OUT / "benchmark_aggregate.csv"
COMPARISON_CSV = OUT / "comparison.csv"
PROOF_CSV = OUT / "proof_gate.csv"
NEXT_CSV = OUT / "next_stage_queue.csv"
ARTIFACT_CSV = OUT / "artifact_index.csv"
REPORT = OUT / "multirow_fft_api_probe_report.md"
REPRO_COMMANDS = OUT / "reproduction_commands.md"

DOC = ROOT / "docs" / "stage212_multirow_fft_api_probe.md"
PLAN = ROOT / "experiments" / "stage212_multirow_fft_api_probe_plan.md"
THEORY = ROOT / "theory_checks" / "stage212_multirow_fft_api_probe_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage212_multirow_fft_api_probe.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE211_PROOF = ROOT / "repro" / "stage211_fft_dataflow_preflight" / "proof_gate.csv"
STAGE211_MECHANISM = ROOT / "repro" / "stage211_fft_dataflow_preflight" / "mechanism_matrix.csv"

N_VALUE = 2048
MAX_ROWS = 5
ITEMS = 128
RUNS = 10
REPS = 8
WARMUPS = 2
PROMOTION_THRESHOLD = 1.03
MAKE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def wsl_repo() -> str:
    return wsl_path(ROOT)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.strip() + "\n")


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


def run_wsl(command: str, log: Path, timeout: int = 300) -> int:
    proc = subprocess.run(
        ["wsl.exe", "--cd", wsl_repo(), "bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    write_text(
        log,
        "\n".join(
            [
                f"command: {command}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize(proc.stdout),
                "--- stderr ---",
                sanitize(proc.stderr),
            ]
        ),
    )
    return proc.returncode


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def write_c_source() -> None:
    source = f'''
#include "mosfhet.h"
#include "spqlios-fft.h"
#include <immintrin.h>
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE212_N
#define STAGE212_N {N_VALUE}
#endif
#ifndef STAGE212_MAX_ROWS
#define STAGE212_MAX_ROWS {MAX_ROWS}
#endif
#ifndef STAGE212_ITEMS
#define STAGE212_ITEMS {ITEMS}
#endif
#ifndef STAGE212_RUNS
#define STAGE212_RUNS {RUNS}
#endif
#ifndef STAGE212_REPS
#define STAGE212_REPS {REPS}
#endif
#ifndef STAGE212_WARMUPS
#define STAGE212_WARMUPS {WARMUPS}
#endif

static inline uint64_t now_ns(void) {{
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}}

static inline int idx_of(int item, int row) {{
  return item * STAGE212_MAX_ROWS + row;
}}

static void fill_input(uint64_t *dst, int item, int row) {{
  uint64_t x = 0x9e3779b97f4a7c15ULL ^ ((uint64_t) item << 32) ^ (uint64_t) row;
  for (int i = 0; i < STAGE212_N; i++) {{
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    dst[i] = x * 0x2545f4914f6cdd1dULL + (uint64_t) (i + 17 * row);
  }}
}}

static inline void convert_torus64_to_double(double *restrict dst,
    const uint64_t *restrict src) {{
#if defined(__AVX512F__)
  __m512d *dst_v = (__m512d *) dst;
  const __m512i *src_v = (const __m512i *) src;
  for (int i = 0; i < STAGE212_N / 8; i++) {{
    dst_v[i] = _mm512_cvtepi64_pd(src_v[i]);
  }}
#else
  const int64_t *src_i = (const int64_t *) src;
  for (int i = 0; i < STAGE212_N; i++) {{
    dst[i] = (double) src_i[i];
  }}
#endif
}}

static inline void copy_double_row(double *restrict dst,
    const double *restrict src) {{
#if defined(__AVX512F__)
  __m512d *dst_v = (__m512d *) dst;
  const __m512d *src_v = (const __m512d *) src;
  for (int i = 0; i < STAGE212_N / 8; i++) {{
    dst_v[i] = src_v[i];
  }}
#else
  memcpy(dst, src, sizeof(double) * STAGE212_N);
#endif
}}

static void current_execute_loop(double **out, uint64_t **in, int rows,
    FFT_Processor_Spqlios proc) {{
  for (int item = 0; item < STAGE212_ITEMS; item++) {{
    for (int row = 0; row < rows; row++) {{
      int idx = idx_of(item, row);
      execute_reverse_torus64(out[idx], in[idx], proc);
    }}
  }}
}}

static void multirow_interleaved_scratch(double **out, uint64_t **in, int rows,
    FFT_Processor_Spqlios proc, double **scratch) {{
  for (int item = 0; item < STAGE212_ITEMS; item++) {{
    for (int row = 0; row < rows; row++) {{
      int idx = idx_of(item, row);
      convert_torus64_to_double(scratch[row], in[idx]);
      ifft(proc->tables_reverse, scratch[row]);
      copy_double_row(out[idx], scratch[row]);
    }}
  }}
}}

static void multirow_two_phase_scratch(double **out, uint64_t **in, int rows,
    FFT_Processor_Spqlios proc, double **scratch) {{
  for (int item = 0; item < STAGE212_ITEMS; item++) {{
    for (int row = 0; row < rows; row++) {{
      convert_torus64_to_double(scratch[row], in[idx_of(item, row)]);
    }}
    for (int row = 0; row < rows; row++) {{
      ifft(proc->tables_reverse, scratch[row]);
    }}
    for (int row = 0; row < rows; row++) {{
      copy_double_row(out[idx_of(item, row)], scratch[row]);
    }}
  }}
}}

static void run_variant(const char *variant, double **out, uint64_t **in,
    int rows, FFT_Processor_Spqlios proc, double **scratch) {{
  if (strcmp(variant, "current_execute_loop") == 0) {{
    current_execute_loop(out, in, rows, proc);
  }} else if (strcmp(variant, "multirow_interleaved_scratch") == 0) {{
    multirow_interleaved_scratch(out, in, rows, proc, scratch);
  }} else if (strcmp(variant, "multirow_two_phase_scratch") == 0) {{
    multirow_two_phase_scratch(out, in, rows, proc, scratch);
  }}
}}

static uint64_t checksum_outputs(double **out, int rows) {{
  uint64_t acc = 0xcbf29ce484222325ULL;
  for (int item = 0; item < STAGE212_ITEMS; item += 7) {{
    for (int row = 0; row < rows; row++) {{
      double *p = out[idx_of(item, row)];
      for (int i = 0; i < STAGE212_N; i += 127) {{
        uint64_t bits = 0;
        memcpy(&bits, &p[i], sizeof(bits));
        acc ^= bits + 0x9e3779b97f4a7c15ULL + (acc << 6) + (acc >> 2);
      }}
    }}
  }}
  return acc;
}}

static void compare_outputs(const char *variant, double **baseline,
    double **candidate, int rows) {{
  int mismatches = 0;
  double max_abs_diff = 0.0;
  for (int item = 0; item < STAGE212_ITEMS; item++) {{
    for (int row = 0; row < rows; row++) {{
      int idx = idx_of(item, row);
      for (int i = 0; i < STAGE212_N; i++) {{
        double diff = fabs(baseline[idx][i] - candidate[idx][i]);
        if (diff != 0.0) {{
          mismatches++;
          if (diff > max_abs_diff) max_abs_diff = diff;
        }}
      }}
    }}
  }}
  printf("CORRECT212,%d,%s,%d,%.17g,%s\\n", rows, variant, mismatches,
      max_abs_diff, mismatches == 0 ? "PASS" : "FAIL");
}}

static uint64_t bench_variant(const char *variant, double **out, uint64_t **in,
    int rows, FFT_Processor_Spqlios proc, double **scratch, int run) {{
  for (int w = 0; w < STAGE212_WARMUPS; w++) {{
    run_variant(variant, out, in, rows, proc, scratch);
  }}
  uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE212_REPS; rep++) {{
    run_variant(variant, out, in, rows, proc, scratch);
  }}
  uint64_t total_ns = now_ns() - start;
  uint64_t sink = checksum_outputs(out, rows);
  double per_group_us = (double) total_ns / (double) (STAGE212_ITEMS * STAGE212_REPS) / 1000.0;
  double per_row_us = (double) total_ns / (double) (STAGE212_ITEMS * STAGE212_REPS * rows) / 1000.0;
  printf("BENCH212,%d,%s,%d,%d,%d,%d,%" PRIu64 ",%.9f,%.9f,%" PRIu64 ",PASS\\n",
      rows, variant, run, STAGE212_N, STAGE212_ITEMS, STAGE212_REPS,
      total_ns, per_group_us, per_row_us, sink);
  return sink;
}}

static double *alloc_double_row(void) {{
  return (double *) safe_aligned_malloc(sizeof(double) * STAGE212_N);
}}

static uint64_t *alloc_torus_row(void) {{
  return (uint64_t *) safe_aligned_malloc(sizeof(uint64_t) * STAGE212_N);
}}

int main(void) {{
  const char *variants[] = {{
    "current_execute_loop",
    "multirow_interleaved_scratch",
    "multirow_two_phase_scratch"
  }};
  const int variant_count = 3;
  const int row_cases[] = {{3, 5}};
  const int row_case_count = 2;
  const int total_slots = STAGE212_ITEMS * STAGE212_MAX_ROWS;

  uint64_t **inputs = (uint64_t **) calloc((size_t) total_slots, sizeof(uint64_t *));
  double **baseline = (double **) calloc((size_t) total_slots, sizeof(double *));
  double **candidate = (double **) calloc((size_t) total_slots, sizeof(double *));
  double **scratch = (double **) calloc((size_t) STAGE212_MAX_ROWS, sizeof(double *));
  if (!inputs || !baseline || !candidate || !scratch) return 2;

  for (int idx = 0; idx < total_slots; idx++) {{
    inputs[idx] = alloc_torus_row();
    baseline[idx] = alloc_double_row();
    candidate[idx] = alloc_double_row();
  }}
  for (int row = 0; row < STAGE212_MAX_ROWS; row++) {{
    scratch[row] = alloc_double_row();
  }}
  for (int item = 0; item < STAGE212_ITEMS; item++) {{
    for (int row = 0; row < STAGE212_MAX_ROWS; row++) {{
      fill_input(inputs[idx_of(item, row)], item, row);
    }}
  }}

  FFT_Processor_Spqlios proc = new_FFT_Processor_Spqlios(STAGE212_N);
  if (!proc) return 3;

  for (int case_idx = 0; case_idx < row_case_count; case_idx++) {{
    int rows = row_cases[case_idx];
    current_execute_loop(baseline, inputs, rows, proc);
    for (int v = 1; v < variant_count; v++) {{
      memset(candidate[0], 0, sizeof(double) * STAGE212_N);
      run_variant(variants[v], candidate, inputs, rows, proc, scratch);
      compare_outputs(variants[v], baseline, candidate, rows);
    }}
    for (int run = 0; run < STAGE212_RUNS; run++) {{
      for (int v = 0; v < variant_count; v++) {{
        bench_variant(variants[v], candidate, inputs, rows, proc, scratch, run);
      }}
    }}
  }}
  return 0;
}}
'''
    write_text(C_SOURCE, source)


def record_environment() -> List[Dict[str, str]]:
    log = OUT / "environment.log"
    cmd = (
        "printf 'uname,'; uname -a; "
        "printf 'gcc_version,'; gcc --version | head -n 1; "
        "perf_bin=$(command -v perf 2>/dev/null || true); printf 'perf_path,%s\\n' \"$perf_bin\"; "
        "printf 'cpu_model,'; lscpu | sed -n 's/^Model name:[[:space:]]*//p' | head -n 1; "
        "printf 'flags,'; lscpu | sed -n 's/^Flags:[[:space:]]*//p' | head -n 1"
    )
    rc = run_wsl(cmd, log, timeout=60)
    text = read_text(log)
    rows: List[Dict[str, str]] = [{"key": "environment_rc", "value": str(rc), "evidence": rel(log)}]
    for key in ["uname", "gcc_version", "perf_path", "cpu_model", "flags"]:
        match = re.search(rf"^{key},(.*)$", text, re.MULTILINE)
        value = match.group(1).strip() if match else ""
        if key == "flags":
            rows.append({"key": "has_avx512f", "value": "yes" if "avx512f" in value else "no", "evidence": rel(log)})
        rows.append({"key": key, "value": value, "evidence": rel(log)})
    write_csv(ENV_CSV, rows, ["key", "value", "evidence"])
    return rows


def build_static() -> int:
    cmd = (
        "cd src/mosfhet && "
        "(make clean >/dev/null 2>&1 || true) && "
        f"make static {MAKE_FLAGS} -j$(nproc)"
    )
    return run_wsl(cmd, OUT / "build_static.log", timeout=1200)


def compile_probe() -> int:
    cmd = (
        "gcc -O3 -march=native -Wall -Wextra "
        "-DUSE_SPQLIOS -DAVX512_OPT "
        f"-DSTAGE212_N={N_VALUE} -DSTAGE212_MAX_ROWS={MAX_ROWS} "
        f"-DSTAGE212_ITEMS={ITEMS} -DSTAGE212_RUNS={RUNS} "
        f"-DSTAGE212_REPS={REPS} -DSTAGE212_WARMUPS={WARMUPS} "
        "-I src/mosfhet/include -I src/mosfhet/src/fft/spqlios "
        f"-o {wsl_path(BINARY)} {wsl_path(C_SOURCE)} src/mosfhet/lib/libmosfhet.a -lm"
    )
    return run_wsl(cmd, OUT / "compile_probe.log", timeout=300)


def run_probe() -> Tuple[int, List[Dict[str, str]], List[Dict[str, str]]]:
    log = OUT / "run_probe.log"
    rc = run_wsl(f"stdbuf -o0 {wsl_path(BINARY)}", log, timeout=900)
    text = read_text(log)
    correctness: List[Dict[str, str]] = []
    samples: List[Dict[str, str]] = []
    for line in text.splitlines():
        if line.startswith("CORRECT212,"):
            parts = line.strip().split(",")
            if len(parts) == 6:
                correctness.append(
                    {
                        "rows": parts[1],
                        "variant": parts[2],
                        "mismatches": parts[3],
                        "max_abs_diff": parts[4],
                        "status": parts[5],
                        "evidence": rel(log),
                    }
                )
        elif line.startswith("BENCH212,"):
            parts = line.strip().split(",")
            if len(parts) == 12:
                samples.append(
                    {
                        "rows": parts[1],
                        "variant": parts[2],
                        "run": parts[3],
                        "N": parts[4],
                        "items": parts[5],
                        "reps": parts[6],
                        "total_ns": parts[7],
                        "per_group_us": parts[8],
                        "per_row_us": parts[9],
                        "sink": parts[10],
                        "status": parts[11],
                        "evidence": rel(log),
                    }
                )
    write_csv(CORRECTNESS_CSV, correctness, ["rows", "variant", "mismatches", "max_abs_diff", "status", "evidence"])
    write_csv(SAMPLES_CSV, samples, ["rows", "variant", "run", "N", "items", "reps", "total_ns", "per_group_us", "per_row_us", "sink", "status", "evidence"])
    return rc, correctness, samples


def aggregate(samples: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    keys = sorted({(row["rows"], row["variant"]) for row in samples}, key=lambda x: (int(x[0]), x[1]))
    for row_count, variant in keys:
        vals = [float(row["per_group_us"]) for row in samples if row["rows"] == row_count and row["variant"] == variant]
        row_vals = [float(row["per_row_us"]) for row in samples if row["rows"] == row_count and row["variant"] == variant]
        rows.append(
            {
                "rows": row_count,
                "variant": variant,
                "samples": str(len(vals)),
                "mean_per_group_us": f"{statistics.mean(vals):.9f}",
                "median_per_group_us": f"{statistics.median(vals):.9f}",
                "min_per_group_us": f"{min(vals):.9f}",
                "max_per_group_us": f"{max(vals):.9f}",
                "stdev_per_group_us": f"{statistics.stdev(vals):.9f}" if len(vals) > 1 else "0.000000000",
                "mean_per_row_us": f"{statistics.mean(row_vals):.9f}",
            }
        )
    write_csv(
        AGG_CSV,
        rows,
        [
            "rows",
            "variant",
            "samples",
            "mean_per_group_us",
            "median_per_group_us",
            "min_per_group_us",
            "max_per_group_us",
            "stdev_per_group_us",
            "mean_per_row_us",
        ],
    )
    return rows


def comparison_rows(agg: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    row_counts = sorted({row["rows"] for row in agg}, key=int)
    for row_count in row_counts:
        base = next(row for row in agg if row["rows"] == row_count and row["variant"] == "current_execute_loop")
        base_mean = float(base["mean_per_group_us"])
        for row in agg:
            if row["rows"] != row_count or row["variant"] == "current_execute_loop":
                continue
            variant_mean = float(row["mean_per_group_us"])
            speedup = base_mean / variant_mean if variant_mean else 0.0
            rows.append(
                {
                    "rows": row_count,
                    "variant": row["variant"],
                    "baseline_mean_per_group_us": f"{base_mean:.9f}",
                    "variant_mean_per_group_us": f"{variant_mean:.9f}",
                    "speedup_vs_current": f"{speedup:.9f}",
                    "promotion_threshold": f"{PROMOTION_THRESHOLD:.6f}",
                    "decision": "PROMOTE_COMPONENT_PROBE" if speedup >= PROMOTION_THRESHOLD else "NOT_PROMOTED",
                    "evidence": rel(AGG_CSV),
                }
            )
    write_csv(
        COMPARISON_CSV,
        rows,
        [
            "rows",
            "variant",
            "baseline_mean_per_group_us",
            "variant_mean_per_group_us",
            "speedup_vs_current",
            "promotion_threshold",
            "decision",
            "evidence",
        ],
    )
    return rows


def decide(build_rc: int, compile_rc: int, run_rc: int, correctness: List[Dict[str, str]], comparison: List[Dict[str, str]]) -> str:
    if build_rc != 0 or compile_rc != 0 or run_rc != 0:
        return "BLOCKED_STAGE212_BUILD_OR_RUN"
    if not correctness or any(row["status"] != "PASS" for row in correctness):
        return "FAIL_STAGE212_MULTIROW_WRAPPER_CORRECTNESS"
    best_by_rows: Dict[str, float] = {}
    for row in comparison:
        best_by_rows[row["rows"]] = max(best_by_rows.get(row["rows"], 0.0), float(row["speedup_vs_current"]))
    if best_by_rows and min(best_by_rows.values()) >= PROMOTION_THRESHOLD:
        return "PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213"
    return "PASS_STAGE212_MULTIROW_WRAPPER_NOT_PROMOTED"


def proof_rows(decision: str, build_rc: int, compile_rc: int, run_rc: int, correctness: List[Dict[str, str]], comparison: List[Dict[str, str]]) -> List[Dict[str, str]]:
    correctness_ok = bool(correctness) and all(row["status"] == "PASS" for row in correctness)
    best_speedup = max((float(row["speedup_vs_current"]) for row in comparison), default=0.0)
    min_best_by_rows = 0.0
    if comparison:
        best_by_rows: Dict[str, float] = {}
        for row in comparison:
            best_by_rows[row["rows"]] = max(best_by_rows.get(row["rows"], 0.0), float(row["speedup_vs_current"]))
        min_best_by_rows = min(best_by_rows.values()) if best_by_rows else 0.0
    return [
        {
            "gate": "G1_stage211_entry",
            "status": "PASS" if STAGE211_PROOF.exists() else "FAIL",
            "metric": "stage211_proof_present",
            "value": "1" if STAGE211_PROOF.exists() else "0",
            "evidence": rel(STAGE211_PROOF),
            "detail": "Stage212 is entered only after Stage211 denies direct hot-path code and admits backend/API probing.",
        },
        {
            "gate": "G2_build_compile",
            "status": "PASS" if build_rc == 0 and compile_rc == 0 else "FAIL",
            "metric": "build_rc;compile_rc",
            "value": f"{build_rc};{compile_rc}",
            "evidence": f"{rel(OUT / 'build_static.log')}; {rel(OUT / 'compile_probe.log')}",
            "detail": "Build current spqlios_avx512 static library and compile standalone multirow reverse-DFT probe.",
        },
        {
            "gate": "G3_correctness",
            "status": "PASS" if correctness_ok else "FAIL",
            "metric": "all_variant_mismatches",
            "value": "0" if correctness_ok else "nonzero_or_missing",
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "Multirow wrapper variants must match current execute_reverse_torus64 output exactly.",
        },
        {
            "gate": "G4_microbench_promotion",
            "status": "PASS_PROMOTE" if min_best_by_rows >= PROMOTION_THRESHOLD else "PASS_NOT_PROMOTED",
            "metric": "min_best_speedup_across_3row_5row;best_speedup_any",
            "value": f"{min_best_by_rows:.9f};{best_speedup:.9f}",
            "evidence": rel(COMPARISON_CSV),
            "detail": f"Promotion requires >= {PROMOTION_THRESHOLD:.2f}x for both 3-row and 5-row groups.",
        },
        {
            "gate": "G5_stage212_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(PROOF_CSV),
            "detail": "Stage212 either promotes a standalone wrapper probe to a later integration gate or closes this local wrapper route.",
        },
    ]


def next_rows(decision: str) -> List[Dict[str, str]]:
    promoted = decision == "PASS_STAGE212_MULTIROW_WRAPPER_PROMOTE_STAGE213"
    return [
        {
            "priority": "P0" if promoted else "P2",
            "route": "stage213_flag_only_sab_dft_wrapper_integration_preflight",
            "entry_condition": "Stage212 promotes multirow wrapper component probe.",
            "gate": "Flag-only SAB preflight with staged equivalence and full SAB A/B.",
            "status": "ready" if promoted else "denied_by_stage212",
            "evidence": rel(PROOF_CSV),
        },
        {
            "priority": "P0" if not promoted else "P1",
            "route": "native_counter_or_true_backend_fft_design",
            "entry_condition": "Stage212 local wrapper is not promoted or needs hardware attribution.",
            "gate": "Use native perf counters or implement a genuinely new backend batch FFT primitive outside SAB first.",
            "status": "ready",
            "evidence": rel(COMPARISON_CSV),
        },
        {
            "priority": "P1" if not promoted else "P2",
            "route": "sab_hotpath_integration",
            "entry_condition": "A component probe is promoted and then passes staged SAB gates.",
            "gate": "Correctness, noise/resource, complete-SAB T_bootstrap/r A/B, and claim audit.",
            "status": "not_authorized_now" if not promoted else "requires_stage213",
            "evidence": rel(PROOF_CSV),
        },
    ]


def report_text(decision: str, agg: List[Dict[str, str]], comparison: List[Dict[str, str]], correctness: List[Dict[str, str]], gates: List[Dict[str, str]], queue: List[Dict[str, str]]) -> str:
    return f"""# Stage212 Multirow FFT API Probe

Decision: `{decision}`.

Stage212 tests the narrowest executable continuation admitted by Stage211: a
standalone multirow reverse-DFT API wrapper for the current SPQLIOS primitive.
The probe does not modify `sab_pvw_*` or the scalar SAB path. It compares the
current `execute_reverse_torus64` row loop against two exact wrapper shapes:
interleaved per-row scratch and two-phase convert/ifft/copy scratch.

Promotion is deliberately strict: both the 3-row case, corresponding to
MAT rows for r=2 when k=1 and T=1, and the 5-row case, corresponding to r=4,
must pass exact correctness and reach at least `{PROMOTION_THRESHOLD:.2f}x`
component speedup before any SAB integration preflight is allowed.

## Correctness

{table(correctness, ["rows", "variant", "mismatches", "max_abs_diff", "status", "evidence"])}

## Aggregate Timing

{table(agg, ["rows", "variant", "samples", "mean_per_group_us", "min_per_group_us", "max_per_group_us", "mean_per_row_us"])}

## Comparison

{table(comparison, ["rows", "variant", "baseline_mean_per_group_us", "variant_mean_per_group_us", "speedup_vs_current", "promotion_threshold", "decision"])}

## Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "detail"])}

## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])}
"""


def plan_text(decision: str) -> str:
    return f"""# Stage212 Multirow FFT API Probe Plan

Decision: `{decision}`.

Loop:

1. Hypothesis: a source-local multirow reverse-DFT wrapper can reduce per-row
   conversion/copy overhead enough to justify later SAB integration.
2. Implementation: standalone probe only; no production SAB code.
3. Correctness gate: wrapper outputs must match `execute_reverse_torus64`
   exactly for 3-row and 5-row groups.
4. Performance gate: best wrapper must reach at least `{PROMOTION_THRESHOLD:.2f}x`
   speedup for both row groups.
5. Exit: promote only to a later flag-only SAB preflight, or close the local
   wrapper route and move to native counters or a true backend batch FFT design.
"""


def theory_text(decision: str) -> str:
    return f"""# Stage212 Multirow FFT API Probe Model

Decision: `{decision}`.

The wrapper tested here does not reduce the number of inverse FFT calls. It can
only affect the input conversion, scratch ownership, output copy, and row-order
memory behavior around the same SPQLIOS `ifft` primitive.

Therefore its theoretical upside is bounded by the non-FFT fraction of
`execute_reverse_torus64`. If the measured wrapper does not clear a component
promotion threshold, a production SAB integration would only add complexity
without evidence of complete-SAB gain. A larger gain would require a true
backend batch FFT primitive or a representation-changing proof, both outside
this local wrapper stage.
"""


def variant_text(decision: str) -> str:
    return f"""# Stage212 Multirow FFT API Probe Variant

Decision: `{decision}`.

This is a standalone backend API probe. It defines no production SAB variant.

Tested shapes:

- `current_execute_loop`: current row loop over `execute_reverse_torus64`.
- `multirow_interleaved_scratch`: explicit per-row scratch, convert/ifft/copy
  for each row.
- `multirow_two_phase_scratch`: convert all rows, run ifft for all rows, then
  copy all rows.

Only a promoted result may enter a later flag-only SAB preflight.
"""


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 212: Multirow FFT API Probe",
        f"""
## Stage 212: Multirow FFT API Probe

Goal:

```text
Execute a standalone multirow reverse-DFT wrapper probe for the current
SPQLIOS primitive before considering SAB hot-path integration.
```

Status:

```text
Completed. Stage212 records {decision}. The probe is correctness-gated for
3-row and 5-row MAT cases and uses T_bootstrap/r research discipline by
requiring a component win before any complete-SAB claim. See
repro/stage212_multirow_fft_api_probe/comparison.csv for the promotion result.
```
""",
    )
    append_once(
        GOAL,
        "Stage212 multirow FFT API probe",
        f"""

## Stage212 multirow FFT API probe

At commit `{head}`, Stage212 executes the bounded backend/API probe selected
by Stage211. The result is `{decision}` and does not change scalar SAB or
`sab_pvw_*` production behavior.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage212 multirow FFT API probe",
        f"""

### Stage212 multirow FFT API probe

`{decision}` records whether a local multirow reverse-DFT wrapper is worth
carrying toward SAB integration. This keeps the loop executable and prevents
reopening DFT theory without measured evidence.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage212_multirow_fft_api_probe",
        f"""

H10_stage212_multirow_fft_api_probe:
  status: standalone_backend_probe_recorded
  evidence:
    - repro/stage212_multirow_fft_api_probe/comparison.csv
    - repro/stage212_multirow_fft_api_probe/proof_gate.csv
    - docs/stage212_multirow_fft_api_probe.md
  conclusion: >
    Stage212 tests source-local multirow reverse-DFT wrappers against the
    current SPQLIOS execute_reverse_torus64 row loop. Decision: {decision}.
""",
    )
    append_once(
        RUN_LOG,
        "stage212-multirow-fft-api-probe-001",
        f"""stage212-multirow-fft-api-probe-001,2026-07-04,{head},Stage 212,spqlios_avx512,python scripts/build_stage212_multirow_fft_api_probe.py,standalone multirow reverse-DFT wrapper probe,N={N_VALUE};rows=3/5;items={ITEMS};runs={RUNS};reps={REPS},{decision},"No SAB hot-path code changed; promotion depends on component microbench gate.",docs/stage212_multirow_fft_api_probe.md; repro/stage212_multirow_fft_api_probe/comparison.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage212_multirow_fft_api_probe:",
        """

- stage212_multirow_fft_api_probe:
  - `docs/stage212_multirow_fft_api_probe.md`
  - `experiments/stage212_multirow_fft_api_probe_plan.md`
  - `theory_checks/stage212_multirow_fft_api_probe_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage212_multirow_fft_api_probe.md`
  - `scripts/build_stage212_multirow_fft_api_probe.py`
  - `repro/stage212_multirow_fft_api_probe/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage212 multirow FFT API probe",
        f"""
- [x] Stage212 multirow FFT API probe records correctness, microbench,
  promotion decision, and next queue. Decision: `{decision}`.
""",
    )


def main() -> None:
    if not STAGE211_PROOF.exists():
        raise SystemExit(f"missing Stage211 input: {STAGE211_PROOF}")

    OUT.mkdir(parents=True, exist_ok=True)
    write_c_source()
    env_rows = record_environment()
    build_rc = build_static()
    compile_rc = compile_probe() if build_rc == 0 else 1
    if compile_rc == 0:
        run_rc, correctness, samples = run_probe()
    else:
        run_rc, correctness, samples = 1, [], []
        write_csv(CORRECTNESS_CSV, [], ["rows", "variant", "mismatches", "max_abs_diff", "status", "evidence"])
        write_csv(SAMPLES_CSV, [], ["rows", "variant", "run", "N", "items", "reps", "total_ns", "per_group_us", "per_row_us", "sink", "status", "evidence"])

    agg = aggregate(samples) if samples else []
    comparison = comparison_rows(agg) if agg else []
    decision = decide(build_rc, compile_rc, run_rc, correctness, comparison)
    gates = proof_rows(decision, build_rc, compile_rc, run_rc, correctness, comparison)
    queue = next_rows(decision)

    write_csv(PROOF_CSV, gates, ["gate", "status", "metric", "value", "evidence", "detail"])
    write_csv(NEXT_CSV, queue, ["priority", "route", "entry_condition", "gate", "status", "evidence"])
    text = report_text(decision, agg, comparison, correctness, gates, queue)
    write_text(DOC, text)
    write_text(REPORT, text)
    write_text(PLAN, plan_text(decision))
    write_text(THEORY, theory_text(decision))
    write_text(VARIANT, variant_text(decision))
    write_text(
        REPRO_COMMANDS,
        "# Stage212 Reproduction Commands\n\n```bash\npython3 scripts/build_stage212_multirow_fft_api_probe.py\n```\n",
    )
    if BINARY.exists():
        BINARY.unlink()
    write_csv(
        ARTIFACT_CSV,
        artifact_rows(
            [
                DOC,
                PLAN,
                THEORY,
                VARIANT,
                C_SOURCE,
                ENV_CSV,
                OUT / "environment.log",
                OUT / "build_static.log",
                OUT / "compile_probe.log",
                OUT / "run_probe.log",
                CORRECTNESS_CSV,
                SAMPLES_CSV,
                AGG_CSV,
                COMPARISON_CSV,
                PROOF_CSV,
                NEXT_CSV,
                REPORT,
                REPRO_COMMANDS,
                Path(__file__),
            ]
        ),
        ["path", "exists", "sha256", "bytes"],
    )
    update_tracking(decision)
    print(decision)
    for row in comparison:
        print(
            "COMPARE212,"
            + ",".join(
                [
                    row["rows"],
                    row["variant"],
                    row["speedup_vs_current"],
                    row["decision"],
                ]
            )
        )


if __name__ == "__main__":
    main()
