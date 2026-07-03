#!/usr/bin/env python3
"""Stage163: from_DFT backend batching/vectorization microbench gate."""

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
OUT_DIR = ROOT / "repro" / "stage163_from_dft_batching_microbench"

C_SOURCE = OUT_DIR / "stage163_from_dft_batching_probe.c"
BINARY = OUT_DIR / "stage163_from_dft_batching_probe"
SUMMARY_CSV = OUT_DIR / "summary.csv"
CORRECTNESS_CSV = OUT_DIR / "correctness.csv"
BENCH_CSV = OUT_DIR / "benchmark_samples.csv"
AGG_CSV = OUT_DIR / "benchmark_aggregate.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage163_from_dft_batching_microbench.md"
PLAN_MD = ROOT / "experiments" / "stage163_from_dft_batching_microbench_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage163_from_dft_batching_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_from_dft_batching_microbench.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

R_VALUE = int(os.environ.get("STAGE163_R", "6"))
N_VALUE = int(os.environ.get("STAGE163_N", "2048"))
ITEMS = int(os.environ.get("STAGE163_ITEMS", "256"))
RUNS = int(os.environ.get("STAGE163_RUNS", "7"))
REPS = int(os.environ.get("STAGE163_REPS", "3"))
WARMUPS = int(os.environ.get("STAGE163_WARMUPS", "1"))
JOBS = os.environ.get("STAGE163_JOBS", "$(nproc)")

MAKE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "ENABLE_PVW_TMLWE=true"
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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef STAGE163_R
#define STAGE163_R {R_VALUE}
#endif
#ifndef STAGE163_N
#define STAGE163_N {N_VALUE}
#endif
#ifndef STAGE163_ITEMS
#define STAGE163_ITEMS {ITEMS}
#endif
#ifndef STAGE163_RUNS
#define STAGE163_RUNS {RUNS}
#endif
#ifndef STAGE163_REPS
#define STAGE163_REPS {REPS}
#endif
#ifndef STAGE163_WARMUPS
#define STAGE163_WARMUPS {WARMUPS}
#endif

enum stage163_variant {{
  STAGE163_SEPARATE_CURRENT = 0,
  STAGE163_BACKEND_CURRENT = 1,
  STAGE163_BACKEND_COMPONENT_MAJOR = 2
}};

static inline uint64_t now_ns(void) {{
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ((uint64_t) ts.tv_sec * 1000000000ULL) + (uint64_t) ts.tv_nsec;
}}

static inline int idx_of(int item, int component) {{
  return item * (1 + STAGE163_R) + component;
}}

static void addto_poly(TorusPolynomial out, TorusPolynomial in) {{
#if defined(__AVX512F__)
  __m512i *out_v = (__m512i *) out->coeffs;
  const __m512i *in_v = (const __m512i *) in->coeffs;
  for (int i = 0; i < out->N / 8; i++) {{
    out_v[i] = _mm512_add_epi64(out_v[i], in_v[i]);
  }}
#else
  polynomial_addto_torus_polynomial(out, in);
#endif
}}

static void fill_source(TorusPolynomial p, int item, int component) {{
  uint64_t x = 0x9e3779b97f4a7c15ULL ^ ((uint64_t) item << 32) ^ (uint64_t) component;
  for (int i = 0; i < p->N; i++) {{
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    p->coeffs[i] = (Torus) (x * 0x2545f4914f6cdd1dULL + (uint64_t) (i + 17 * component));
  }}
}}

static void fill_addend(TorusPolynomial p, int item, int component) {{
  uint64_t x = 0xd1b54a32d192ed03ULL ^ ((uint64_t) component << 40) ^ (uint64_t) item;
  for (int i = 0; i < p->N; i++) {{
    x += 0x9e3779b97f4a7c15ULL + (uint64_t) (i * 1315423911U);
    x ^= x >> 29;
    p->coeffs[i] = (Torus) (x + ((uint64_t) item << 11) + (uint64_t) component);
  }}
}}

static void prepare_inputs(DFT_Polynomial *dft, TorusPolynomial *addend,
    int total) {{
  TorusPolynomial tmp = polynomial_new_torus_polynomial(STAGE163_N);
  for (int item = 0; item < STAGE163_ITEMS; item++) {{
    for (int component = 0; component < 1 + STAGE163_R; component++) {{
      int idx = idx_of(item, component);
      dft[idx] = polynomial_new_DFT_polynomial(STAGE163_N);
      addend[idx] = polynomial_new_torus_polynomial(STAGE163_N);
      fill_source(tmp, item, component);
      polynomial_torus_to_DFT(dft[idx], tmp);
      fill_addend(addend[idx], item, component);
    }}
  }}
  (void) total;
  free_polynomial(tmp);
}}

static void run_variant(enum stage163_variant variant, DFT_Polynomial *dft,
    TorusPolynomial *addend, TorusPolynomial *out) {{
  if (variant == STAGE163_BACKEND_COMPONENT_MAJOR) {{
    for (int component = 0; component < 1 + STAGE163_R; component++) {{
      for (int item = 0; item < STAGE163_ITEMS; item++) {{
        const int idx = idx_of(item, component);
        polynomial_DFT_to_torus_add(out[idx], dft[idx], addend[idx]);
      }}
    }}
    return;
  }}

  for (int item = 0; item < STAGE163_ITEMS; item++) {{
    for (int component = 0; component < 1 + STAGE163_R; component++) {{
      const int idx = idx_of(item, component);
      if (variant == STAGE163_SEPARATE_CURRENT) {{
        polynomial_DFT_to_torus(out[idx], dft[idx]);
        addto_poly(out[idx], addend[idx]);
      }} else {{
        polynomial_DFT_to_torus_add(out[idx], dft[idx], addend[idx]);
      }}
    }}
  }}
}}

static uint64_t checksum_outputs(TorusPolynomial *out, int total) {{
  uint64_t acc = 0x84222325cbf29ce4ULL;
  for (int idx = 0; idx < total; idx++) {{
    for (int i = 0; i < STAGE163_N; i += 17) {{
      const uint64_t v = (uint64_t) out[idx]->coeffs[i];
      acc ^= v + 0x9e3779b97f4a7c15ULL + (acc << 6) + (acc >> 2);
    }}
  }}
  return acc;
}}

static void compare_outputs(const char *variant, TorusPolynomial *ref,
    TorusPolynomial *got, int total) {{
  uint64_t mismatches = 0;
  uint64_t max_gap = 0;
  for (int idx = 0; idx < total; idx++) {{
    for (int i = 0; i < STAGE163_N; i++) {{
      const uint64_t a = (uint64_t) ref[idx]->coeffs[i];
      const uint64_t b = (uint64_t) got[idx]->coeffs[i];
      const uint64_t gap = (a >= b) ? (a - b) : (b - a);
      if (gap != 0) mismatches++;
      if (gap > max_gap) max_gap = gap;
    }}
  }}
  printf("CORRECT163,%s,%" PRIu64 ",%" PRIu64 ",%s\n",
      variant, mismatches, max_gap, mismatches == 0 ? "PASS" : "FAIL");
}}

static const char *variant_name(enum stage163_variant variant) {{
  switch (variant) {{
    case STAGE163_SEPARATE_CURRENT: return "separate_current_order";
    case STAGE163_BACKEND_CURRENT: return "backend_current_order";
    case STAGE163_BACKEND_COMPONENT_MAJOR: return "backend_component_major";
  }}
  return "unknown";
}}

static uint64_t bench_variant(enum stage163_variant variant, DFT_Polynomial *dft,
    TorusPolynomial *addend, TorusPolynomial *out, int total) {{
  for (int w = 0; w < STAGE163_WARMUPS; w++) {{
    run_variant(variant, dft, addend, out);
  }}
  const uint64_t start = now_ns();
  for (int rep = 0; rep < STAGE163_REPS; rep++) {{
    run_variant(variant, dft, addend, out);
  }}
  const uint64_t end = now_ns();
  (void) total;
  return end - start;
}}

int main(void) {{
  const int components = 1 + STAGE163_R;
  const int total = STAGE163_ITEMS * components;
  init_fft(STAGE163_N);

  DFT_Polynomial *dft = (DFT_Polynomial *) calloc((size_t) total, sizeof(*dft));
  TorusPolynomial *addend = (TorusPolynomial *) calloc((size_t) total, sizeof(*addend));
  TorusPolynomial *out_sep = polynomial_new_array_of_torus_polynomials(STAGE163_N, total);
  TorusPolynomial *out_backend = polynomial_new_array_of_torus_polynomials(STAGE163_N, total);
  TorusPolynomial *out_batch = polynomial_new_array_of_torus_polynomials(STAGE163_N, total);

  if (!dft || !addend || !out_sep || !out_backend || !out_batch) {{
    fprintf(stderr, "allocation failed\n");
    return 2;
  }}

  prepare_inputs(dft, addend, total);
  run_variant(STAGE163_SEPARATE_CURRENT, dft, addend, out_sep);
  run_variant(STAGE163_BACKEND_CURRENT, dft, addend, out_backend);
  run_variant(STAGE163_BACKEND_COMPONENT_MAJOR, dft, addend, out_batch);
  compare_outputs("backend_current_order", out_sep, out_backend, total);
  compare_outputs("backend_component_major", out_sep, out_batch, total);

  enum stage163_variant variants[3] = {{
    STAGE163_SEPARATE_CURRENT,
    STAGE163_BACKEND_CURRENT,
    STAGE163_BACKEND_COMPONENT_MAJOR,
  }};
  TorusPolynomial *outs[3] = {{out_sep, out_backend, out_batch}};

  for (int run = 0; run < STAGE163_RUNS; run++) {{
    for (int v = 0; v < 3; v++) {{
      const uint64_t ns = bench_variant(variants[v], dft, addend, outs[v], total);
      const uint64_t calls = (uint64_t) STAGE163_REPS * (uint64_t) total;
      const double per_call_us = ((double) ns) / ((double) calls) / 1000.0;
      const uint64_t sink = checksum_outputs(outs[v], total);
      printf("BENCH163,%s,%d,%d,%d,%d,%d,%d,%" PRIu64 ",%" PRIu64 ",%.9f,%" PRIu64 ",PASS\n",
          variant_name(variants[v]), run, STAGE163_R, STAGE163_N,
          STAGE163_ITEMS, components, STAGE163_REPS, calls, ns,
          per_call_us, sink);
    }}
  }}

  for (int idx = 0; idx < total; idx++) {{
    free_DFT_polynomial(dft[idx]);
    free_polynomial(addend[idx]);
  }}
  free(dft);
  free(addend);
  free_array_of_polynomials(out_sep, total);
  free_array_of_polynomials(out_backend, total);
  free_array_of_polynomials(out_batch, total);
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
        f"-DSTAGE163_R={R_VALUE} -DSTAGE163_N={N_VALUE} "
        f"-DSTAGE163_ITEMS={ITEMS} -DSTAGE163_RUNS={RUNS} "
        f"-DSTAGE163_REPS={REPS} -DSTAGE163_WARMUPS={WARMUPS} "
        f"-I {rel(MOSFHET_DIR / 'include')} "
        f"-o {rel(BINARY)} {rel(C_SOURCE)} "
        f"{rel(MOSFHET_DIR / 'lib' / 'libmosfhet.a')} -lm"
    )
    return run_wsl(cmd, OUT_DIR / "compile_probe.log", timeout=180)


def run_probe() -> Tuple[int, List[Dict[str, str]], List[Dict[str, str]]]:
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
        if parts and parts[0] == "CORRECT163" and len(parts) == 5:
            correctness.append({
                "variant": parts[1],
                "mismatches": parts[2],
                "max_gap": parts[3],
                "status": parts[4],
            })
        elif parts and parts[0] == "BENCH163" and len(parts) == 13:
            bench.append({
                "variant": parts[1],
                "run": parts[2],
                "r": parts[3],
                "N": parts[4],
                "items": parts[5],
                "components": parts[6],
                "reps": parts[7],
                "calls": parts[8],
                "total_ns": parts[9],
                "per_call_us": parts[10],
                "checksum": parts[11],
                "status": parts[12],
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
    backend_vs_separate: List[float] = []
    batch_vs_backend: List[float] = []
    for variants in by_run.values():
        sep = variants.get("separate_current_order")
        backend = variants.get("backend_current_order")
        batch = variants.get("backend_component_major")
        if sep and backend and backend > 0:
            backend_vs_separate.append(sep / backend)
        if backend and batch and batch > 0:
            batch_vs_backend.append(backend / batch)

    def row(metric: str, values: List[float], meaning: str) -> Dict[str, str]:
        if not values:
            return {
                "metric": metric,
                "samples": "0",
                "mean": "0.000000000",
                "min": "0.000000000",
                "max": "0.000000000",
                "stdev": "0.000000000",
                "meaning": meaning,
            }
        return {
            "metric": metric,
            "samples": str(len(values)),
            "mean": f"{statistics.mean(values):.9f}",
            "min": f"{min(values):.9f}",
            "max": f"{max(values):.9f}",
            "stdev": f"{statistics.stdev(values):.9f}" if len(values) > 1 else "0.000000000",
            "meaning": meaning,
        }

    return [
        row(
            "backend_add_over_separate",
            backend_vs_separate,
            ">1 means execute_direct_torus64_add beats DFT_to_torus plus explicit add.",
        ),
        row(
            "component_major_batch_over_backend_current",
            batch_vs_backend,
            ">1 means component-major batching beats current item-major backend add order.",
        ),
    ]


def decide(
    avx512_ok: bool,
    build_rc: int,
    compile_rc: int,
    run_rc: int,
    correctness: List[Dict[str, str]],
    comparisons: List[Dict[str, str]],
) -> str:
    if not avx512_ok:
        return "BLOCKED_STAGE163_AVX512_PLATFORM_UNAVAILABLE"
    if build_rc != 0:
        return "FAIL_STAGE163_BUILD_STATIC"
    if compile_rc != 0:
        return "FAIL_STAGE163_COMPILE_PROBE"
    if run_rc != 0:
        return "FAIL_STAGE163_RUN_PROBE"
    if not correctness or any(row.get("status") != "PASS" for row in correctness):
        return "FAIL_STAGE163_FROM_DFT_BATCHING_CORRECTNESS"

    comp = {row["metric"]: row for row in comparisons}
    backend_mean = float(comp.get("backend_add_over_separate", {}).get("mean", "0") or "0")
    batch_mean = float(comp.get("component_major_batch_over_backend_current", {}).get("mean", "0") or "0")
    batch_min = float(comp.get("component_major_batch_over_backend_current", {}).get("min", "0") or "0")
    if batch_mean >= 1.02 and batch_min >= 1.0:
        return "PASS_STAGE163_FROM_DFT_BATCHING_MICROBENCH_CANDIDATE"
    if batch_mean > 1.0:
        return "NEUTRAL_STAGE163_BATCHING_LOW_SIGNAL_NOT_PROMOTED"
    if backend_mean >= 1.02:
        return "NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED"
    return "REJECT_STAGE163_FROM_DFT_BATCHING_NO_WALLTIME_GAIN"


def build_summary(
    decision: str,
    avx512_ok: bool,
    build_rc: int,
    compile_rc: int,
    run_rc: int,
    correctness: List[Dict[str, str]],
    comparisons: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    comp = {row["metric"]: row for row in comparisons}
    correctness_ok = correctness and all(row.get("status") == "PASS" for row in correctness)
    backend_mean = comp.get("backend_add_over_separate", {}).get("mean", "0.000000000")
    batch_mean = comp.get("component_major_batch_over_backend_current", {}).get("mean", "0.000000000")
    batch_min = comp.get("component_major_batch_over_backend_current", {}).get("min", "0.000000000")
    return [
        {
            "gate": "stage163_platform",
            "status": "PASS" if avx512_ok else "BLOCKED",
            "metric": "avx512f",
            "value": "present" if avx512_ok else "missing",
            "evidence": rel(OUT_DIR / "environment.log"),
            "detail": "Stage163 is a spqlios_avx512 backend microbench.",
            "next_action": "Use native/WSL AVX512 host before interpreting this gate.",
        },
        {
            "gate": "stage163_build_static",
            "status": "PASS" if build_rc == 0 else "FAIL",
            "metric": "make_static_rc",
            "value": str(build_rc),
            "evidence": rel(OUT_DIR / "build_static.log"),
            "detail": "Build MOSFHET static library with FFT_LIB=spqlios_avx512.",
            "next_action": "Fix build before using timing evidence.",
        },
        {
            "gate": "stage163_compile_probe",
            "status": "PASS" if compile_rc == 0 else "FAIL",
            "metric": "gcc_rc",
            "value": str(compile_rc),
            "evidence": rel(OUT_DIR / "compile_probe.log"),
            "detail": "Compile a standalone probe linked to current libmosfhet.a.",
            "next_action": "Fix probe or link flags before using timing evidence.",
        },
        {
            "gate": "stage163_correctness",
            "status": "PASS" if correctness_ok else "FAIL",
            "metric": "mismatches",
            "value": ";".join(f"{row.get('variant')}={row.get('mismatches')}" for row in correctness) if correctness else "missing",
            "evidence": rel(CORRECTNESS_CSV),
            "detail": "Backend-add and component-major batching must match separate DFT-to-torus plus add exactly.",
            "next_action": "Do not promote any batching variant if correctness fails.",
        },
        {
            "gate": "stage163_backend_add_microbench",
            "status": "PASS" if float(backend_mean or 0) >= 1.02 else "WEAK",
            "metric": "backend_add_over_separate_mean",
            "value": backend_mean,
            "evidence": rel(COMPARISON_CSV),
            "detail": "Confirms whether current execute_direct_torus64_add remains useful relative to separate add.",
            "next_action": "Keep scoped as backend wall-time evidence, not algorithmic count reduction.",
        },
        {
            "gate": "stage163_batching_microbench",
            "status": "PASS" if float(batch_mean or 0) >= 1.02 and float(batch_min or 0) >= 1.0 else "NEUTRAL",
            "metric": "component_major_batch_over_backend_current_mean_min",
            "value": f"{batch_mean};{batch_min}",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Tests whether a batched component-major loop order improves over current item-major backend-add order.",
            "next_action": "Only integrate into full SAB if this gate is clearly positive.",
        },
        {
            "gate": "stage163_decision",
            "status": decision,
            "metric": "from_dft_backend_batching_route",
            "value": "backend_wall_time_only",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage163 separates backend batching from materialization-count reduction.",
            "next_action": "If neutral/rejected, route to representation-changing exact-state designs rather than repeat backend batching.",
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
    agg: List[Dict[str, str]],
    comparisons: List[Dict[str, str]],
) -> None:
    summary_fields = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
    agg_fields = [
        "variant", "samples", "mean_per_call_us", "median_per_call_us",
        "min_per_call_us", "max_per_call_us", "stdev_per_call_us",
    ]
    comp_fields = ["metric", "samples", "mean", "min", "max", "stdev", "meaning"]

    write_text_lf(OUT_MD, f"""# Stage163 From-DFT Backend Batching Microbench

Decision: `{decision}`.

Stage163 is deliberately scoped to backend wall-time. It does not reduce the
Stage160/Stage162 `573440` from_DFT materialization count and therefore cannot
be reported as an algorithmic materialization-count reduction.

## Gate Summary

{table(summary, summary_fields)}

## Benchmark Aggregate

{table(agg, agg_fields)}

## Comparisons

{table(comparisons, comp_fields)}

## Interpretation

- `backend_add_over_separate > 1` means the existing
  `execute_direct_torus64_add` callback is faster than `DFT_to_torus` followed
  by a separate torus add pass.
- `component_major_batch_over_backend_current > 1` means a component-major
  batched loop order improves over the current item-major backend-add order.
- A positive Stage163 result only authorizes a later full-SAB A/B gate; it
  does not by itself change `sab_pvw_*` production behavior.
""")

    write_text_lf(PLAN_MD, f"""# Stage163 Validation Plan

Goal: test whether `from_DFT` backend batching or loop-order vectorization can
lower per-call wall time under the current exact torus-input MAT-RLWE SAB API.

Primary endpoint: `per_call_us` for `N={N_VALUE}`, `r={R_VALUE}`,
`items={ITEMS}`, `runs={RUNS}`, `reps={REPS}`.

Variants:

1. `separate_current_order`: `polynomial_DFT_to_torus` plus an explicit torus
   add in current item-major order.
2. `backend_current_order`: `polynomial_DFT_to_torus_add` in current
   item-major order.
3. `backend_component_major`: `polynomial_DFT_to_torus_add` with the batch
   loop grouped by component/lane.

Gates:

- exact output equality against `separate_current_order`;
- `backend_add_over_separate` records current backend fused-add value;
- `component_major_batch_over_backend_current >= 1.02` with positive minimum
  is required before any production batching integration;
- all claims remain backend wall-time claims until complete SAB `T_bootstrap/r`
  A/B passes.
""")

    write_text_lf(THEORY_MD, """# Stage163 From-DFT Batching Model

Stage162 proves that the current same-format SAB state cannot reduce the number
of `from_DFT` materializations: each CMUX/NCMUX update must return to torus
coefficients before the next gadget decomposition or final extraction.

Stage163 therefore tests only the constant factor of each materialization. The
existing backend fused-add path can save one torus add pass by doing the add in
the conversion store loop. A batched loop order may improve cache locality or
branch overhead, but it cannot change the asymptotic count:

```text
from_DFT calls = (h + 1) * r_prec * N = 40 * 7 * 2048 = 573440
```

If batching is neutral, the next meaningful acceleration route is not another
same-format loop-order attempt. It is a representation/API change that remains
closed under exact decomposition, rotation/sign, CMUX update, and extraction.
""")

    write_text_lf(VARIANT_MD, f"""# MAT-RLWE SAB From-DFT Backend Batching

This is an isolated backend microbench variant, not a production `sab_pvw_*`
algorithm variant.

Delta from current explicit H14 r=6 path:

- keep the same `PVW_TMLWE` torus accumulator semantics;
- keep the same `573440` materialization count;
- compare current item-major `polynomial_DFT_to_torus_add` calls against a
  component-major batched loop order;
- require exact output equality against separate materialization plus add.

Decision: `{decision}`.

Promotion rule: only a clearly positive microbench can proceed to a guarded
full SAB `T_bootstrap/r` A/B. A neutral or rejected result routes the research
loop to representation-changing exact-state designs.
""")


def update_global_docs(decision: str) -> None:
    append_once(ROADMAP_MD, "## Stage 163: From-DFT Backend Batching Microbench", f"""
## Stage 163: From-DFT Backend Batching Microbench

Goal:

```text
Measure whether backend batching or component-major loop order can lower each
from_DFT materialization's wall time after Stage162 closes same-format count
reduction.
```

Status:

```text
Completed. Stage163 records {decision}. This is backend wall-time evidence
only; it does not reduce the 573440 materialization count and cannot be used
as a complete-SAB acceleration claim without a later T_bootstrap/r gate.
```
""")

    append_once(GOAL_MD, "Stage163 tests from_DFT backend batching", f"""
Stage163 tests `from_DFT` backend batching after Stage162. Decision:
`{decision}`. The result is explicitly scoped to backend wall-time; it does
not change the algorithmic materialization count or scalar/default behavior.
""")

    append_once(CURRENT_GOAL_MD, "67. Treat Stage163 as the from_DFT backend batching microbench", f"""
67. Treat Stage163 as the from_DFT backend batching microbench:
    `{decision}`. This stage decides whether component-major batching of
    `polynomial_DFT_to_torus_add` deserves a later complete-SAB gate. It must
    not be used as an algorithmic count-reduction or final bootstrapping claim.
""")

    append_once(HYPOTHESIS_YAML, "id: H87_from_dft_backend_batching", f"""
  - id: H87_from_dft_backend_batching
    statement: >
      Under the current exact torus-input MAT-RLWE SAB API, batching or
      component-major loop order for from_DFT materialization may reduce
      per-call wall time but cannot reduce the materialization count.
    mechanism: >
      `execute_direct_torus64_add` fuses inverse-DFT conversion with the addend
      store path; component-major ordering may improve locality across the
      r-body MAT state while preserving exact torus outputs.
    status: stage163_from_dft_batching_microbench
    evidence: docs/stage163_from_dft_batching_microbench.md; experiments/stage163_from_dft_batching_microbench_plan.md; theory_checks/stage163_from_dft_batching_model.md; repro/stage163_from_dft_batching_microbench/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - backend-add or batched outputs differ from separate materialization plus add
      - component-major batching does not beat current backend-add order beyond the promotion threshold
      - backend batching is reported as algorithmic materialization-count reduction
""")

    append_once(RUN_LOG, "stage163-from-dft-batching-microbench-001", f"""
stage163-from-dft-batching-microbench-001,2026-07-03,{git_head()},Stage 163,spqlios_avx512,python scripts/build_stage163_from_dft_batching_microbench.py,r={R_VALUE}; N={N_VALUE}; items={ITEMS}; runs={RUNS}; reps={REPS}; backend_batching,deterministic-probe,{decision},From-DFT backend batching microbench gate.,repro/stage163_from_dft_batching_microbench
""")

    append_once(MANIFEST, "stage163_from_dft_batching_microbench", f"""
- stage163_from_dft_batching_microbench: `{decision}`
  - `docs/stage163_from_dft_batching_microbench.md`
  - `experiments/stage163_from_dft_batching_microbench_plan.md`
  - `theory_checks/stage163_from_dft_batching_model.md`
  - `algorithm_variants/mat_rlwe_sab_from_dft_batching_microbench.md`
  - `repro/stage163_from_dft_batching_microbench/`
""")

    append_once(CHECKLIST, "Stage163 from_DFT backend batching microbench pack recorded", """
- [x] Stage163 from_DFT backend batching microbench pack recorded.
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

    write_csv(CORRECTNESS_CSV, correctness, ["variant", "mismatches", "max_gap", "status"])
    write_csv(BENCH_CSV, bench, [
        "variant", "run", "r", "N", "items", "components", "reps",
        "calls", "total_ns", "per_call_us", "checksum", "status",
    ])
    write_csv(AGG_CSV, agg, [
        "variant", "samples", "mean_per_call_us", "median_per_call_us",
        "min_per_call_us", "max_per_call_us", "stdev_per_call_us",
    ])
    write_csv(COMPARISON_CSV, comparisons, ["metric", "samples", "mean", "min", "max", "stdev", "meaning"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    write_docs(decision, summary, agg, comparisons)
    update_global_docs(decision)

    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, C_SOURCE,
        SUMMARY_CSV, CORRECTNESS_CSV, BENCH_CSV, AGG_CSV, COMPARISON_CSV,
        OUT_DIR / "environment.log", OUT_DIR / "build_static.log",
        OUT_DIR / "compile_probe.log", OUT_DIR / "run_probe.log",
        OUT_DIR / "cleanup.log",
        Path(__file__),
    ]
    artifact_index(artifacts)

    print(decision)
    for row in comparisons:
        print(f"{row['metric']} mean={row['mean']} min={row['min']} max={row['max']}")


if __name__ == "__main__":
    main()
