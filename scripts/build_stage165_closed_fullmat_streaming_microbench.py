#!/usr/bin/env python3
"""Stage165: closed full-MAT row-streaming decompose/DFT microbench."""

from __future__ import annotations

import csv
import hashlib
import os
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
MOSFHET_DIR = ROOT / "src" / "mosfhet"
OUT_DIR = ROOT / "repro" / "stage165_closed_fullmat_streaming_microbench"

C_SOURCE = OUT_DIR / "stage165_closed_fullmat_streaming_probe.c"
BINARY = OUT_DIR / "stage165_closed_fullmat_streaming_probe"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage165_closed_fullmat_streaming_microbench.md"
PLAN_MD = ROOT / "experiments" / "stage165_closed_fullmat_streaming_microbench_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage165_closed_fullmat_streaming_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_closed_fullmat_streaming.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

R_VALUE = int(os.environ.get("STAGE165_R", "6"))
N_VALUE = int(os.environ.get("STAGE165_N", "2048"))
ITEMS = int(os.environ.get("STAGE165_ITEMS", "64"))
RUNS = int(os.environ.get("STAGE165_RUNS", "5"))
REPS = int(os.environ.get("STAGE165_REPS", "2"))
WARMUPS = int(os.environ.get("STAGE165_WARMUPS", "1"))
BG_BIT = int(os.environ.get("STAGE165_BG_BIT", "23"))
JOBS = os.environ.get("STAGE165_JOBS", "$(nproc)")

MAKE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true"
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
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


def run_wsl(command: str, log: Path, timeout: int = 300) -> int:
    proc = bash(command, timeout=timeout)
    write_text_lf(log, "\n".join([
        f"command: {command}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize(proc.stdout),
        "--- stderr ---",
        sanitize(proc.stderr),
    ]))
    return proc.returncode


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def write_c_source() -> None:
    source = fr'''
#include "mosfhet.h"
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifndef STAGE165_R
#define STAGE165_R {R_VALUE}
#endif
#ifndef STAGE165_N
#define STAGE165_N {N_VALUE}
#endif
#ifndef STAGE165_ITEMS
#define STAGE165_ITEMS {ITEMS}
#endif
#ifndef STAGE165_RUNS
#define STAGE165_RUNS {RUNS}
#endif
#ifndef STAGE165_REPS
#define STAGE165_REPS {REPS}
#endif
#ifndef STAGE165_WARMUPS
#define STAGE165_WARMUPS {WARMUPS}
#endif
#ifndef STAGE165_BG_BIT
#define STAGE165_BG_BIT {BG_BIT}
#endif

enum stage165_variant {{
  STAGE165_CURRENT_ALLROW = 0,
  STAGE165_STREAMING_ROW = 1
}};

static inline uint64_t now_ns(void) {{
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}}

static void fill_poly(TorusPolynomial p, uint64_t seed) {{
  uint64_t x = seed ^ 0x9e3779b97f4a7c15ULL;
  for (int i = 0; i < p->N; i++) {{
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    p->coeffs[i] = (Torus) (x * 0x2545f4914f6cdd1dULL + (uint64_t) i);
  }}
}}

static void fill_pvmtmlwe(PVW_TMLWE p, uint64_t seed) {{
  fill_poly(p->a[0], seed ^ 0x100000001b3ULL);
  for (int lane = 0; lane < p->r; lane++) {{
    fill_poly(p->b[lane], seed ^ ((uint64_t) lane << 32) ^ 0x84222325cbf29ce4ULL);
  }}
}}

static void fill_selector(MAT_TRGSW_DFT selector) {{
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE165_N);
  const int rows = 1 + STAGE165_R;
  for (int row = 0; row < rows; row++) {{
    fill_poly(tmp, 0xabcdef0011223344ULL ^ (uint64_t) row);
    polynomial_torus_to_DFT(selector->samples[row]->a[0], tmp);
    for (int lane = 0; lane < STAGE165_R; lane++) {{
      fill_poly(tmp, 0x6677889900aabbccULL ^ ((uint64_t) row << 16) ^ (uint64_t) lane);
      polynomial_torus_to_DFT(selector->samples[row]->b[lane], tmp);
    }}
  }}
  free_polynomial(tmp);
}}

static void zero_pvmtmlwe_dft(PVW_TMLWE_DFT out) {{
  memset(out->a[0]->coeffs, 0, sizeof(double) * STAGE165_N);
  for (int lane = 0; lane < out->r; lane++) {{
    memset(out->b[lane]->coeffs, 0, sizeof(double) * STAGE165_N);
  }}
}}

static void sub_decompose_row(PVW_TMLWE in1, PVW_TMLWE in2,
    TorusPolynomial out, int row) {{
  const uint64_t half_Bg = (1ULL << (STAGE165_BG_BIT - 1));
  const uint64_t h_mask = (1ULL << STAGE165_BG_BIT) - 1;
  const uint64_t word_size = sizeof(Torus) * 8;
  const uint64_t offset = (1ULL << (word_size - 1));
  const uint64_t h_bit = word_size - STAGE165_BG_BIT;

  TorusPolynomial lhs = row == 0 ? in1->a[0] : in1->b[row - 1];
  TorusPolynomial rhs = row == 0 ? in2->a[0] : in2->b[row - 1];
  for (int c = 0; c < STAGE165_N; c++) {{
    const uint64_t diff = rhs->coeffs[c] - lhs->coeffs[c];
    const uint64_t coeff_off = diff + offset;
    out->coeffs[c] = ((coeff_off >> h_bit) & h_mask) - half_Bg;
  }}
}}

static void streaming_sub_mul_DFT(PVW_TMLWE_DFT out, PVW_TMLWE in1,
    PVW_TMLWE in2, MAT_TRGSW_DFT selector, TorusPolynomial dec,
    DFT_Polynomial dec_dft) {{
  zero_pvmtmlwe_dft(out);
  const int rows = 1 + STAGE165_R;
  for (int row = 0; row < rows; row++) {{
    sub_decompose_row(in1, in2, dec, row);
    polynomial_torus_to_DFT(dec_dft, dec);
    polynomial_mul_addto_DFT(out->a[0], dec_dft, selector->samples[row]->a[0]);
    for (int lane = 0; lane < STAGE165_R; lane++) {{
      polynomial_mul_addto_DFT(out->b[lane], dec_dft, selector->samples[row]->b[lane]);
    }}
  }}
}}

static double compare_dft(PVW_TMLWE_DFT a, PVW_TMLWE_DFT b,
    uint64_t *mismatches) {{
  double max_gap = 0.0;
  for (int i = 0; i < STAGE165_N; i++) {{
    const double gap = fabs(a->a[0]->coeffs[i] - b->a[0]->coeffs[i]);
    if (gap != 0.0) (*mismatches)++;
    if (gap > max_gap) max_gap = gap;
  }}
  for (int lane = 0; lane < STAGE165_R; lane++) {{
    for (int i = 0; i < STAGE165_N; i++) {{
      const double gap = fabs(a->b[lane]->coeffs[i] - b->b[lane]->coeffs[i]);
      if (gap != 0.0) (*mismatches)++;
      if (gap > max_gap) max_gap = gap;
    }}
  }}
  return max_gap;
}}

static uint64_t compare_torus(PVW_TMLWE a, PVW_TMLWE b,
    uint64_t *max_gap) {{
  uint64_t mismatches = 0;
  for (int i = 0; i < STAGE165_N; i++) {{
    const uint64_t x = (uint64_t) a->a[0]->coeffs[i];
    const uint64_t y = (uint64_t) b->a[0]->coeffs[i];
    const uint64_t gap = x >= y ? x - y : y - x;
    if (gap != 0) mismatches++;
    if (gap > *max_gap) *max_gap = gap;
  }}
  for (int lane = 0; lane < STAGE165_R; lane++) {{
    for (int i = 0; i < STAGE165_N; i++) {{
      const uint64_t x = (uint64_t) a->b[lane]->coeffs[i];
      const uint64_t y = (uint64_t) b->b[lane]->coeffs[i];
      const uint64_t gap = x >= y ? x - y : y - x;
      if (gap != 0) mismatches++;
      if (gap > *max_gap) *max_gap = gap;
    }}
  }}
  return mismatches;
}}

static uint64_t checksum_dft(PVW_TMLWE_DFT out) {{
  uint64_t acc = 0xcbf29ce484222325ULL;
  const uint64_t *a = (const uint64_t *) out->a[0]->coeffs;
  for (int i = 0; i < STAGE165_N; i += 17) acc ^= a[i] + (acc << 6) + (acc >> 2);
  for (int lane = 0; lane < STAGE165_R; lane++) {{
    const uint64_t *b = (const uint64_t *) out->b[lane]->coeffs;
    for (int i = 0; i < STAGE165_N; i += 17) acc ^= b[i] + (acc << 6) + (acc >> 2);
  }}
  return acc;
}}

static const char *variant_name(enum stage165_variant variant) {{
  return variant == STAGE165_CURRENT_ALLROW ? "current_allrow_tiled_avx" : "streaming_row_generic";
}}

static void run_variant(enum stage165_variant variant, PVW_TMLWE_DFT out,
    PVW_TMLWE *in1, PVW_TMLWE *in2, MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch, TorusPolynomial dec,
    DFT_Polynomial dec_dft) {{
  for (int item = 0; item < STAGE165_ITEMS; item++) {{
    if (variant == STAGE165_CURRENT_ALLROW) {{
      mat_trgsw_mul_pvmtmlwe_sub_DFT(out, in1[item], in2[item], selector, scratch);
    }} else {{
      streaming_sub_mul_DFT(out, in1[item], in2[item], selector, dec, dec_dft);
    }}
  }}
}}

static uint64_t bench_variant(enum stage165_variant variant, PVW_TMLWE_DFT out,
    PVW_TMLWE *in1, PVW_TMLWE *in2, MAT_TRGSW_DFT selector,
    MAT_TRGSW_MUL_SCRATCH scratch, TorusPolynomial dec,
    DFT_Polynomial dec_dft) {{
  for (int w = 0; w < STAGE165_WARMUPS; w++) {{
    run_variant(variant, out, in1, in2, selector, scratch, dec, dec_dft);
  }}
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE165_REPS; rep++) {{
    run_variant(variant, out, in1, in2, selector, scratch, dec, dec_dft);
  }}
  return now_ns() - start;
}}

int main(void) {{
  init_fft(STAGE165_N);
  MAT_TRGSW_DFT selector = mat_trgsw_alloc_new_DFT_sample(1, STAGE165_BG_BIT, 1, STAGE165_R, STAGE165_N);
  fill_selector(selector);

  PVW_TMLWE *in1 = pvmtmlwe_alloc_new_sample_array(STAGE165_ITEMS, 1, STAGE165_R, STAGE165_N);
  PVW_TMLWE *in2 = pvmtmlwe_alloc_new_sample_array(STAGE165_ITEMS, 1, STAGE165_R, STAGE165_N);
  for (int item = 0; item < STAGE165_ITEMS; item++) {{
    fill_pvmtmlwe(in1[item], 0x100000000ULL + (uint64_t) item);
    fill_pvmtmlwe(in2[item], 0x200000000ULL + (uint64_t) item);
  }}

  PVW_TMLWE_DFT current = pvmtmlwe_alloc_new_DFT_sample(1, STAGE165_R, STAGE165_N);
  PVW_TMLWE_DFT stream = pvmtmlwe_alloc_new_DFT_sample(1, STAGE165_R, STAGE165_N);
  MAT_TRGSW_MUL_SCRATCH scratch = mat_trgsw_alloc_mul_scratch(1 + STAGE165_R, STAGE165_N);
  TorusPolynomial dec = polynomial_new_torus_polynomial(STAGE165_N);
  DFT_Polynomial dec_dft = polynomial_new_DFT_polynomial(STAGE165_N);

  mat_trgsw_mul_pvmtmlwe_sub_DFT(current, in1[0], in2[0], selector, scratch);
  streaming_sub_mul_DFT(stream, in1[0], in2[0], selector, dec, dec_dft);

  uint64_t dft_mismatches = 0;
  const double max_dft_gap = compare_dft(current, stream, &dft_mismatches);
  PVW_TMLWE current_torus = pvmtmlwe_alloc_new_sample(1, STAGE165_R, STAGE165_N);
  PVW_TMLWE stream_torus = pvmtmlwe_alloc_new_sample(1, STAGE165_R, STAGE165_N);
  pvmtmlwe_from_DFT(current_torus, current);
  pvmtmlwe_from_DFT(stream_torus, stream);
  uint64_t max_torus_gap = 0;
  const uint64_t torus_mismatches = compare_torus(current_torus, stream_torus, &max_torus_gap);
  printf("CORRECT165,streaming_vs_current,%" PRIu64 ",%.12e,%" PRIu64 ",%" PRIu64 ",%s\n",
      dft_mismatches, max_dft_gap, torus_mismatches, max_torus_gap,
      torus_mismatches == 0 ? "PASS_TORUS_EQUIV" : "FAIL");

  enum stage165_variant variants[2] = {{STAGE165_CURRENT_ALLROW, STAGE165_STREAMING_ROW}};
  PVW_TMLWE_DFT outs[2] = {{current, stream}};
  for (int run = 0; run < STAGE165_RUNS; run++) {{
    for (int v = 0; v < 2; v++) {{
      const uint64_t ns = bench_variant(variants[v], outs[v], in1, in2,
          selector, scratch, dec, dec_dft);
      const uint64_t calls = (uint64_t) STAGE165_REPS * (uint64_t) STAGE165_ITEMS;
      const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
      const uint64_t sink = checksum_dft(outs[v]);
      printf("BENCH165,%s,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",PASS\n",
          variant_name(variants[v]), run, STAGE165_R, STAGE165_N,
          STAGE165_ITEMS, STAGE165_REPS, calls, ns, per_call_us, sink);
    }}
  }}

  free_pvmtmlwe(current_torus);
  free_pvmtmlwe(stream_torus);
  free_DFT_polynomial(dec_dft);
  free_polynomial(dec);
  free_mat_trgsw_mul_scratch(scratch);
  free_pvmtmlwe_DFT(current);
  free_pvmtmlwe_DFT(stream);
  free_pvmtmlwe_array(in1, STAGE165_ITEMS);
  free_pvmtmlwe_array(in2, STAGE165_ITEMS);
  free_mat_trgsw_DFT(selector);
  return 0;
}}
'''
    write_text_lf(C_SOURCE, source)


def platform_supports_avx512() -> bool:
    proc = bash("lscpu | grep -qi avx512f", timeout=10)
    return proc.returncode == 0


def record_environment() -> None:
    run_wsl(
        "printf 'uname: '; uname -a; printf '\\n--- lscpu ---\\n'; lscpu",
        OUT_DIR / "environment.log",
        timeout=30,
    )


def build_static_library() -> int:
    cmd = (
        "cd src/mosfhet && make clean >/dev/null 2>&1 || true && "
        f"make static {MAKE_FLAGS} -j{JOBS}"
    )
    return run_wsl(cmd, OUT_DIR / "build_static.log", timeout=600)


def compile_probe() -> int:
    cmd = (
        "gcc -O3 -march=native -Wall -Wextra "
        f"-DSTAGE165_R={R_VALUE} -DSTAGE165_N={N_VALUE} "
        f"-DSTAGE165_ITEMS={ITEMS} -DSTAGE165_RUNS={RUNS} "
        f"-DSTAGE165_REPS={REPS} -DSTAGE165_WARMUPS={WARMUPS} "
        f"-DSTAGE165_BG_BIT={BG_BIT} "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    return run_wsl(cmd, OUT_DIR / "compile_probe.log", timeout=180)


def run_probe() -> tuple[int, List[Dict[str, str]], List[Dict[str, str]]]:
    proc = bash(f"./{rel(BINARY)}", timeout=900)
    write_text_lf(OUT_DIR / "run_probe.log", "\n".join([
        f"command: ./{rel(BINARY)}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize(proc.stdout),
        "--- stderr ---",
        sanitize(proc.stderr),
    ]))
    correctness: List[Dict[str, str]] = []
    bench: List[Dict[str, str]] = []
    for line in proc.stdout.splitlines():
        parts = line.strip().split(",")
        if parts and parts[0] == "CORRECT165" and len(parts) == 7:
            correctness.append({
                "case": parts[1],
                "dft_mismatches": parts[2],
                "max_dft_gap": parts[3],
                "torus_mismatches": parts[4],
                "max_torus_gap": parts[5],
                "status": parts[6],
            })
        elif parts and parts[0] == "BENCH165" and len(parts) == 12:
            bench.append({
                "variant": parts[1],
                "run": parts[2],
                "r": parts[3],
                "N": parts[4],
                "items": parts[5],
                "reps": parts[6],
                "calls": parts[7],
                "total_ns": parts[8],
                "per_call_us": parts[9],
                "checksum": parts[10],
                "status": parts[11],
            })
    return proc.returncode, correctness, bench


def cleanup_outputs() -> None:
    run_wsl("cd src/mosfhet && make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=120)
    try:
        BINARY.unlink()
    except FileNotFoundError:
        pass


def aggregate_bench(bench: List[Dict[str, str]]) -> List[Dict[str, str]]:
    groups: Dict[str, List[float]] = {}
    for row in bench:
        groups.setdefault(row["variant"], []).append(float(row["per_call_us"]))
    rows: List[Dict[str, str]] = []
    for variant, values in sorted(groups.items()):
        rows.append({
            "variant": variant,
            "samples": str(len(values)),
            "mean_per_call_us": f"{statistics.mean(values):.9f}",
            "median_per_call_us": f"{statistics.median(values):.9f}",
            "min_per_call_us": f"{min(values):.9f}",
            "max_per_call_us": f"{max(values):.9f}",
            "stdev_per_call_us": f"{statistics.stdev(values):.9f}" if len(values) > 1 else "0.000000000",
        })
    return rows


def comparison_rows(bench: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_run: Dict[str, Dict[str, float]] = {}
    for row in bench:
        by_run.setdefault(row["run"], {})[row["variant"]] = float(row["per_call_us"])
    ratios: List[float] = []
    for variants in by_run.values():
        current = variants.get("current_allrow_tiled_avx")
        stream = variants.get("streaming_row_generic")
        if current and stream and stream > 0:
            ratios.append(current / stream)
    if not ratios:
        return [{
            "metric": "current_over_streaming",
            "samples": "0",
            "mean": "0.000000000",
            "min": "0.000000000",
            "max": "0.000000000",
            "stdev": "0.000000000",
            "meaning": ">1 means row-streaming beats current all-row tiled AVX.",
        }]
    return [{
        "metric": "current_over_streaming",
        "samples": str(len(ratios)),
        "mean": f"{statistics.mean(ratios):.9f}",
        "min": f"{min(ratios):.9f}",
        "max": f"{max(ratios):.9f}",
        "stdev": f"{statistics.stdev(ratios):.9f}" if len(ratios) > 1 else "0.000000000",
        "meaning": ">1 means row-streaming beats current all-row tiled AVX.",
    }]


def decide(
    avx512_ok: bool,
    build_rc: int,
    compile_rc: int,
    run_rc: int,
    correctness: List[Dict[str, str]],
    comparisons: List[Dict[str, str]],
) -> str:
    if not avx512_ok:
        return "BLOCKED_STAGE165_AVX512_PLATFORM_UNAVAILABLE"
    if build_rc != 0:
        return "FAIL_STAGE165_BUILD_STATIC"
    if compile_rc != 0:
        return "FAIL_STAGE165_COMPILE_PROBE"
    if run_rc != 0:
        return "FAIL_STAGE165_RUN_PROBE"
    if not correctness or any(row.get("torus_mismatches") != "0" for row in correctness):
        return "FAIL_STAGE165_STREAMING_EQUIVALENCE"
    ratio = float(comparisons[0].get("mean", "0") if comparisons else "0")
    ratio_min = float(comparisons[0].get("min", "0") if comparisons else "0")
    if ratio >= 1.02 and ratio_min >= 1.0:
        return "PASS_STAGE165_STREAMING_MICROBENCH_CANDIDATE"
    if ratio > 1.0:
        return "NEUTRAL_STAGE165_STREAMING_LOW_SIGNAL_NOT_PROMOTED"
    return "REJECT_STAGE165_STREAMING_LOSES_TO_CURRENT_TILED_AVX"


def build_summary(
    decision: str,
    avx512_ok: bool,
    build_rc: int,
    compile_rc: int,
    run_rc: int,
    correctness: List[Dict[str, str]],
    comparisons: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    corr_ok = correctness and all(row.get("torus_mismatches") == "0" for row in correctness)
    ratio = comparisons[0].get("mean", "0.000000000") if comparisons else "0.000000000"
    ratio_min = comparisons[0].get("min", "0.000000000") if comparisons else "0.000000000"
    return [
        {
            "gate": "stage165_platform",
            "status": "PASS" if avx512_ok else "BLOCKED",
            "metric": "avx512f",
            "value": "present" if avx512_ok else "missing",
            "evidence": rel(OUT_DIR / "environment.log"),
            "detail": "Stage165 compares against the current r=6 tiled AVX512 MAT path.",
            "next_action": "Use AVX512 platform before interpreting timing.",
        },
        {
            "gate": "stage165_build_static",
            "status": "PASS" if build_rc == 0 else "FAIL",
            "metric": "make_static_rc",
            "value": str(build_rc),
            "evidence": rel(OUT_DIR / "build_static.log"),
            "detail": "Build MOSFHET with MAT_TRGSW_AVX512_RGT4_FUSED=true.",
            "next_action": "Fix build before using timing evidence.",
        },
        {
            "gate": "stage165_compile_probe",
            "status": "PASS" if compile_rc == 0 else "FAIL",
            "metric": "gcc_rc",
            "value": str(compile_rc),
            "evidence": rel(OUT_DIR / "compile_probe.log"),
            "detail": "Compile standalone streaming/full-MAT probe against libmosfhet.a.",
            "next_action": "Fix compile/link before using timing evidence.",
        },
        {
            "gate": "stage165_correctness",
            "status": "PASS" if corr_ok else "FAIL",
            "metric": "torus_mismatches",
            "value": ";".join(row.get("torus_mismatches", "") for row in correctness) if correctness else "missing",
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "Row-streamed DFT output must materialize to the same torus PVW_TMLWE as current all-row MAT EP.",
            "next_action": "Do not use streaming if torus equivalence fails.",
        },
        {
            "gate": "stage165_microbench",
            "status": "PASS" if float(ratio or 0) >= 1.02 and float(ratio_min or 0) >= 1.0 else "NEUTRAL_OR_REJECT",
            "metric": "current_over_streaming_mean_min",
            "value": f"{ratio};{ratio_min}",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Ratio is current_allrow_tiled_avx per-call time divided by streaming_row_generic per-call time.",
            "next_action": "Only productionize if streaming clearly wins.",
        },
        {
            "gate": "stage165_decision",
            "status": decision,
            "metric": "closed_fullmat_streaming_route",
            "value": "microbench_only",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage165 decides whether row-streaming deserves production integration.",
            "next_action": "If rejected, keep current tiled AVX path and move to compact keygen proof or native counters.",
        },
    ]


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() and path.is_file() else "",
            "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def write_docs(
    decision: str,
    summary: List[Dict[str, str]],
    correctness: List[Dict[str, str]],
    agg: List[Dict[str, str]],
    comparisons: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    corr_fields = ["case", "dft_mismatches", "max_dft_gap", "torus_mismatches", "max_torus_gap", "status"]
    agg_fields = [
        "variant", "samples", "mean_per_call_us", "median_per_call_us",
        "min_per_call_us", "max_per_call_us", "stdev_per_call_us",
    ]
    comp_fields = ["metric", "samples", "mean", "min", "max", "stdev", "meaning"]

    write_text_lf(OUT_MD, f"""# Stage165 Closed Full-MAT Streaming Microbench

Decision: `{decision}`.

Stage165 tests the Stage164 P0 route without modifying production SAB code.
The current baseline is `mat_trgsw_mul_pvmtmlwe_sub_DFT` compiled with the
r>4 tiled AVX512 path. The candidate streams one decomposed row through DFT and
generic DFT addmul at a time, reducing scratch lifetime but potentially losing
the MAT-aware tiled AVX accumulation.

## Gate Summary

{table(summary, summary_fields)}

## Correctness

{table(correctness, corr_fields)}

## Benchmark Aggregate

{table(agg, agg_fields)}

## Comparison

{table(comparisons, comp_fields)}
""")

    write_text_lf(PLAN_MD, f"""# Stage165 Validation Plan

Goal: test whether row-streaming the closed full-MAT decompose/DFT/addmul
boundary can beat the current all-row r=6 tiled AVX512 implementation.

Primary endpoint: per external-product call time for `r={R_VALUE}`,
`N={N_VALUE}`, `items={ITEMS}`, `runs={RUNS}`, `reps={REPS}`.

Variants:

- `current_allrow_tiled_avx`: current production MAT EP with all decomposed
  rows converted to DFT before the r>4 tiled AVX512 addmul.
- `streaming_row_generic`: one row is decomposed, converted, and added to the
  DFT output at a time.

Promotion requires torus equivalence and `current_over_streaming >= 1.02` with
positive minimum across paired runs. If not, the streaming route is closed.
""")

    write_text_lf(THEORY_MD, """# Stage165 Closed Full-MAT Streaming Model

The current r=6 path stores all `(1+r)` decomposed rows and DFT rows, then uses
a MAT-aware tiled AVX512 kernel to accumulate all output polynomials. A
row-streamed implementation can reduce scratch lifetime and row-array traffic,
but it repeatedly touches the output DFT polynomials and does not use the
current register-tiled r>4 AVX512 addmul.

Expected tradeoff:

- possible win: less scratch row storage and simpler lifecycle;
- possible loss: more output read/write traffic and loss of multi-row tiled
  AVX512 accumulation.

The microbench decides this empirically under exact torus-output equivalence.
""")

    write_text_lf(VARIANT_MD, f"""# Closed Full-MAT Row-Streaming Candidate

This candidate preserves the PVW_TMLWE shared-mask state and dense MAT selector
semantics. It does not reduce the SAB schedule count or `from_DFT` count.

Implementation tested:

```text
for each decomposed row:
    compute decompose(in2 - in1)[row]
    torus_to_DFT(row)
    addmul row into output DFT
```

Decision: `{decision}`.

The result is microbench-only. A positive result would still require a guarded
production path and complete SAB `T_bootstrap/r` A/B.
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 165: Closed Full-MAT Streaming Microbench", f"""
## Stage 165: Closed Full-MAT Streaming Microbench

Goal:

```text
Test whether row-streaming decompose/DFT/addmul beats the current all-row r=6
tiled AVX512 closed full-MAT external product.
```

Status:

```text
Completed. Stage165 records {decision}. The route is microbench-only and does
not modify production SAB code.
```
""")

    append_once(GOAL_MD, "Stage165 tests closed full-MAT row streaming", f"""
Stage165 tests closed full-MAT row streaming after Stage164. Decision:
`{decision}`. This is an exact-output external-product microbench; it is not a
complete bootstrapping speedup claim unless a later full-SAB gate is added.
""")

    append_once(CURRENT_GOAL_MD, "69. Treat Stage165 as the closed full-MAT streaming microbench", f"""
69. Treat Stage165 as the closed full-MAT streaming microbench:
    `{decision}`. It decides whether row-streamed decompose/DFT/addmul should
    be integrated; if not positive, keep the current tiled AVX path.
""")

    append_once(HYPOTHESIS_YAML, "id: H89_closed_fullmat_streaming", f"""
  - id: H89_closed_fullmat_streaming
    statement: >
      Row-streaming the closed full-MAT decompose/DFT/addmul boundary may
      reduce scratch traffic enough to beat the current all-row r=6 tiled
      AVX512 MAT EP while preserving exact torus output.
    mechanism: >
      Streaming removes the lifetime of all decomposed/DFT rows, but may lose
      MAT-aware register-tiled accumulation and increase output DFT traffic.
    status: stage165_closed_fullmat_streaming_microbench
    evidence: docs/stage165_closed_fullmat_streaming_microbench.md; experiments/stage165_closed_fullmat_streaming_microbench_plan.md; theory_checks/stage165_closed_fullmat_streaming_model.md; repro/stage165_closed_fullmat_streaming_microbench/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - torus output differs from current all-row MAT EP
      - per-call timing does not beat current all-row tiled AVX beyond threshold
      - microbench result is reported as complete-SAB acceleration
""")

    append_once(RUN_LOG, "stage165-closed-fullmat-streaming-microbench-001", f"""
stage165-closed-fullmat-streaming-microbench-001,2026-07-03,{git_head()},Stage 165,spqlios_avx512,python scripts/build_stage165_closed_fullmat_streaming_microbench.py,r={R_VALUE}; N={N_VALUE}; items={ITEMS}; runs={RUNS}; reps={REPS}; row_streaming,deterministic-probe,{decision},Closed full-MAT row-streaming microbench gate.,repro/stage165_closed_fullmat_streaming_microbench
""")

    append_once(MANIFEST, "stage165_closed_fullmat_streaming_microbench", f"""
- stage165_closed_fullmat_streaming_microbench: `{decision}`
  - `docs/stage165_closed_fullmat_streaming_microbench.md`
  - `experiments/stage165_closed_fullmat_streaming_microbench_plan.md`
  - `theory_checks/stage165_closed_fullmat_streaming_model.md`
  - `algorithm_variants/mat_rlwe_sab_closed_fullmat_streaming.md`
  - `repro/stage165_closed_fullmat_streaming_microbench/`
""")

    append_once(CHECKLIST, "Stage165 closed full-MAT streaming microbench pack recorded", """
- [x] Stage165 closed full-MAT streaming microbench pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_c_source()
    record_environment()
    avx512_ok = platform_supports_avx512()
    build_rc = build_static_library() if avx512_ok else 1
    compile_rc = compile_probe() if build_rc == 0 else 1
    run_rc, correctness, bench = run_probe() if compile_rc == 0 else (1, [], [])
    cleanup_outputs()

    agg = aggregate_bench(bench)
    comparisons = comparison_rows(bench)
    decision = decide(avx512_ok, build_rc, compile_rc, run_rc, correctness, comparisons)
    summary = build_summary(decision, avx512_ok, build_rc, compile_rc, run_rc, correctness, comparisons)

    write_csv(CORRECTNESS_CSV, correctness, ["case", "dft_mismatches", "max_dft_gap", "torus_mismatches", "max_torus_gap", "status"])
    write_csv(BENCH_CSV, bench, [
        "variant", "run", "r", "N", "items", "reps", "calls",
        "total_ns", "per_call_us", "checksum", "status",
    ])
    write_csv(AGG_CSV, agg, [
        "variant", "samples", "mean_per_call_us", "median_per_call_us",
        "min_per_call_us", "max_per_call_us", "stdev_per_call_us",
    ])
    write_csv(COMPARISON_CSV, comparisons, ["metric", "samples", "mean", "min", "max", "stdev", "meaning"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, correctness, agg, comparisons)
    update_global_docs(decision)
    artifact_index([
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, C_SOURCE, SUMMARY_CSV,
        CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, COMPARISON_CSV,
        OUT_DIR / "environment.log", OUT_DIR / "build_static.log",
        OUT_DIR / "compile_probe.log", OUT_DIR / "run_probe.log",
        OUT_DIR / "cleanup.log", Path(__file__),
    ])

    print(decision)
    for row in comparisons:
        print(f"{row['metric']} mean={row['mean']} min={row['min']} max={row['max']}")


if __name__ == "__main__":
    main()
