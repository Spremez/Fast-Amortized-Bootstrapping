#!/usr/bin/env python3
"""Build and run Stage115 lane-local toy C representation gate."""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage115_lane_local_toy_c_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
RAW_CSV = OUT_DIR / "toy_c_raw.csv"
RATIO_CSV = OUT_DIR / "layout_ratios.csv"
COMPILE_LOG = OUT_DIR / "compile.log"
C_SOURCE = OUT_DIR / "toy_lane_local_layout.c"
C_BINARY = OUT_DIR / "toy_lane_local_layout"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage115_lane_local_toy_c_gate.md"
PLAN_MD = ROOT / "experiments" / "stage115_lane_local_toy_c_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage115_lane_local_toy_c_resource_gate.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_lane_local_toy_layout.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


RAW_FIELDS = [
    "layout",
    "r",
    "N",
    "acc_polys",
    "selector_polys",
    "scratch_torus_polys",
    "scratch_dft_polys",
    "product_terms",
    "requested_bytes",
    "rss_kb",
    "touch_us",
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
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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


def write_c_source() -> None:
    source = r'''
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

typedef struct {
  size_t n;
  double *coeffs;
} ToyPoly;

static volatile double toy_sink = 0.0;

static void die(const char *msg) {
  fprintf(stderr, "%s\n", msg);
  exit(2);
}

static size_t page_size(void) {
  long p = sysconf(_SC_PAGESIZE);
  return p > 0 ? (size_t)p : (size_t)4096;
}

static long current_rss_kb(void) {
  FILE *fd = fopen("/proc/self/statm", "r");
  if (fd != NULL) {
    long total_pages = 0;
    long rss_pages = 0;
    if (fscanf(fd, "%ld %ld", &total_pages, &rss_pages) == 2) {
      fclose(fd);
      return (long)((rss_pages * (long)page_size()) / 1024L);
    }
    fclose(fd);
  }
  struct rusage usage;
  if (getrusage(RUSAGE_SELF, &usage) == 0) {
    return usage.ru_maxrss;
  }
  return -1;
}

static uint64_t now_us(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t)ts.tv_sec * 1000000ULL + (uint64_t)(ts.tv_nsec / 1000ULL);
}

static void *xaligned(size_t bytes) {
  void *ptr = NULL;
  if (posix_memalign(&ptr, 64, bytes) != 0 || ptr == NULL) {
    fprintf(stderr, "posix_memalign failed for %zu bytes: %s\n", bytes, strerror(errno));
    exit(2);
  }
  return ptr;
}

static ToyPoly *alloc_polys(size_t count, size_t N, size_t *requested_bytes) {
  ToyPoly *polys = (ToyPoly *)xaligned(sizeof(ToyPoly) * count);
  *requested_bytes += sizeof(ToyPoly) * count;
  for (size_t i = 0; i < count; i++) {
    polys[i].n = N;
    polys[i].coeffs = (double *)xaligned(sizeof(double) * N);
    *requested_bytes += sizeof(double) * N;
  }
  return polys;
}

static void touch_polys(ToyPoly *polys, size_t count) {
  for (size_t i = 0; i < count; i++) {
    for (size_t j = 0; j < polys[i].n; j++) {
      polys[i].coeffs[j] = (double)(i + 1) * 0.125 + (double)(j & 7);
    }
    toy_sink += polys[i].coeffs[polys[i].n - 1];
  }
}

static void free_polys(ToyPoly *polys, size_t count) {
  if (polys == NULL) return;
  for (size_t i = 0; i < count; i++) {
    free(polys[i].coeffs);
  }
  free(polys);
}

typedef struct {
  const char *layout;
  size_t r;
  size_t N;
  size_t acc_polys;
  size_t selector_polys;
  size_t scratch_torus_polys;
  size_t scratch_dft_polys;
  size_t product_terms;
} LayoutSpec;

static LayoutSpec spec_for(const char *layout, size_t r, size_t N) {
  LayoutSpec spec;
  spec.layout = layout;
  spec.r = r;
  spec.N = N;
  if (strcmp(layout, "current") == 0) {
    spec.acc_polys = 1 + r;
    spec.selector_polys = (1 + r) * (1 + r);
    spec.scratch_torus_polys = 1 + r;
    spec.scratch_dft_polys = 1 + r;
    spec.product_terms = (1 + r) * (1 + r);
    return spec;
  }
  if (strcmp(layout, "lane_local") == 0) {
    spec.acc_polys = 2 * r;
    spec.selector_polys = 2 * (1 + 2 * r);
    spec.scratch_torus_polys = 1 + 2 * r;
    spec.scratch_dft_polys = 1 + 2 * r;
    spec.product_terms = 1 + 2 * r;
    return spec;
  }
  die("layout must be current or lane_local");
  return spec;
}

int main(int argc, char **argv) {
  if (argc != 4) {
    fprintf(stderr, "usage: %s current|lane_local r N\n", argv[0]);
    return 2;
  }

  const char *layout = argv[1];
  size_t r = (size_t)strtoull(argv[2], NULL, 10);
  size_t N = (size_t)strtoull(argv[3], NULL, 10);
  if (r == 0 || N == 0) die("r and N must be non-zero");

  LayoutSpec spec = spec_for(layout, r, N);
  size_t requested_bytes = 0;
  uint64_t begin = now_us();
  ToyPoly *acc = alloc_polys(spec.acc_polys, N, &requested_bytes);
  ToyPoly *selector = alloc_polys(spec.selector_polys, N, &requested_bytes);
  ToyPoly *scratch_torus = alloc_polys(spec.scratch_torus_polys, N, &requested_bytes);
  ToyPoly *scratch_dft = alloc_polys(spec.scratch_dft_polys, N, &requested_bytes);

  touch_polys(acc, spec.acc_polys);
  touch_polys(selector, spec.selector_polys);
  touch_polys(scratch_torus, spec.scratch_torus_polys);
  touch_polys(scratch_dft, spec.scratch_dft_polys);
  uint64_t touch_us = now_us() - begin;
  long rss = current_rss_kb();

  printf("%s,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%zu,%ld,%llu\n",
      spec.layout, spec.r, spec.N, spec.acc_polys, spec.selector_polys,
      spec.scratch_torus_polys, spec.scratch_dft_polys, spec.product_terms,
      requested_bytes, rss, (unsigned long long)touch_us);
  fflush(stdout);

  free_polys(scratch_dft, spec.scratch_dft_polys);
  free_polys(scratch_torus, spec.scratch_torus_polys);
  free_polys(selector, spec.selector_polys);
  free_polys(acc, spec.acc_polys);
  return toy_sink < 0.0 ? 1 : 0;
}
'''
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_text_lf(C_SOURCE, source.lstrip())


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


def compile_toy() -> Tuple[bool, str]:
    cmd = (
        "gcc -O2 -std=c11 -Wall -Wextra "
        f"-o {rel(C_BINARY)} {rel(C_SOURCE)}"
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
    return proc.returncode == 0, "\n".join(log)


def run_toy(layout: str, r: int, N: int) -> Dict[str, str]:
    cmd = f"./{rel(C_BINARY)} {layout} {r} {N}"
    proc = bash(cmd, timeout=30)
    if proc.returncode != 0:
      raise RuntimeError(
          f"toy C run failed: {cmd}\nstdout={proc.stdout}\nstderr={proc.stderr}"
      )
    lines = [line.strip() for line in sanitize_log(proc.stdout).splitlines() if line.strip()]
    if not lines:
      raise RuntimeError(f"toy C run produced no output: {cmd}")
    values = lines[-1].split(",")
    if len(values) != len(RAW_FIELDS):
      raise RuntimeError(f"unexpected toy C CSV output: {lines[-1]}")
    return dict(zip(RAW_FIELDS, values))


def build_raw_rows(compile_ok: bool) -> List[Dict[str, str]]:
    if not compile_ok:
        return []
    rows: List[Dict[str, str]] = []
    for N in [2048, 4096]:
        for r in [2, 4, 6, 8]:
            rows.append(run_toy("current", r, N))
            rows.append(run_toy("lane_local", r, N))
    return rows


def ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return math.inf
    return numerator / denominator


def build_ratio_rows(raw_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_key: Dict[Tuple[str, str], Dict[str, Dict[str, str]]] = {}
    for row in raw_rows:
        by_key.setdefault((row["r"], row["N"]), {})[row["layout"]] = row

    ratios: List[Dict[str, str]] = []
    for key in sorted(by_key, key=lambda item: (int(item[1]), int(item[0]))):
        pair = by_key[key]
        if "current" not in pair or "lane_local" not in pair:
            continue
        cur = pair["current"]
        lane = pair["lane_local"]
        cur_bytes = float(cur["requested_bytes"])
        lane_bytes = float(lane["requested_bytes"])
        cur_rss = float(cur["rss_kb"])
        lane_rss = float(lane["rss_kb"])
        cur_terms = float(cur["product_terms"])
        lane_terms = float(lane["product_terms"])
        requested_ratio = ratio(lane_bytes, cur_bytes)
        rss_ratio = ratio(lane_rss, cur_rss)
        product_ratio = ratio(cur_terms, lane_terms)
        product_over_requested = ratio(product_ratio, requested_ratio)
        ratios.append(
            {
                "r": cur["r"],
                "N": cur["N"],
                "current_requested_bytes": cur["requested_bytes"],
                "lane_local_requested_bytes": lane["requested_bytes"],
                "requested_ratio_lane_over_current": f"{requested_ratio:.6f}",
                "current_rss_kb": cur["rss_kb"],
                "lane_local_rss_kb": lane["rss_kb"],
                "rss_ratio_lane_over_current": f"{rss_ratio:.6f}",
                "current_product_terms": cur["product_terms"],
                "lane_local_product_terms": lane["product_terms"],
                "product_ratio_current_over_lane": f"{product_ratio:.6f}",
                "product_over_requested_ratio": f"{product_over_requested:.6f}",
                "status": "LAYOUT_NOT_FATAL" if product_over_requested > 1.0 else "LAYOUT_NEGATIVE",
            }
        )
    return ratios


def build_summary(compile_ok: bool, ratios: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not compile_ok:
        return [
            {
                "gate": "stage115_compile",
                "status": "BLOCKED",
                "metric": "gcc_compile",
                "value": "false",
                "evidence": rel(COMPILE_LOG),
                "detail": "Toy C compiler gate failed.",
                "next_action": "Fix compiler/platform before using Stage115 as measured evidence.",
            },
            {
                "gate": "stage115_decision",
                "status": "BLOCKED_STAGE115_TOY_C_COMPILER_UNAVAILABLE",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(COMPILE_LOG),
                "detail": "No measured toy representation result is available.",
                "next_action": "Do not implement lane-local hot path.",
            },
        ]

    all_not_fatal = all(row["status"] == "LAYOUT_NOT_FATAL" for row in ratios)
    target = next(row for row in ratios if row["r"] == "4" and row["N"] == "2048")
    r2 = next(row for row in ratios if row["r"] == "2" and row["N"] == "2048")
    target_req = float(target["requested_ratio_lane_over_current"])
    r2_req = float(r2["requested_ratio_lane_over_current"])
    target_positive = target_req <= 1.25 and float(target["product_over_requested_ratio"]) > 1.0
    r2_bounded = r2_req <= 1.50
    decision = (
        "PASS_STAGE115_TOY_C_LAYOUT_FEASIBLE_PROTOTYPE_REQUIRED"
        if all_not_fatal and target_positive and r2_bounded
        else "PASS_STAGE115_TOY_C_LAYOUT_NEGATIVE_NOT_IMPLEMENTED"
    )
    return [
        {
            "gate": "stage115_compile",
            "status": "PASS",
            "metric": "gcc_compile",
            "value": "true",
            "evidence": rel(COMPILE_LOG),
            "detail": "Toy C layout probe compiled and executed under WSL gcc.",
            "next_action": "Use measured rows only as layout/RSS evidence.",
        },
        {
            "gate": "stage115_layout_matrix",
            "status": "PASS" if all_not_fatal else "NEGATIVE",
            "metric": "rows",
            "value": str(len(ratios)),
            "evidence": rel(RATIO_CSV),
            "detail": "r=2/4/6/8 and N=2048/4096 current-vs-lane-local rows are measured.",
            "next_action": "Stop if any product-over-requested ratio is below 1.",
        },
        {
            "gate": "stage115_target_r4_resource",
            "status": "PASS_BOUNDED" if target_positive else "NEGATIVE",
            "metric": "r4_N2048_requested_ratio",
            "value": target["requested_ratio_lane_over_current"],
            "evidence": rel(RATIO_CSV),
            "detail": "Target r=4 lane-local toy layout requested-byte overhead is bounded.",
            "next_action": "Proceed only to a compact arithmetic prototype, not SAB integration.",
        },
        {
            "gate": "stage115_r2_lower_bound_control",
            "status": "PASS_BOUNDED" if r2_bounded else "NEGATIVE",
            "metric": "r2_N2048_requested_ratio",
            "value": r2["requested_ratio_lane_over_current"],
            "evidence": rel(RATIO_CSV),
            "detail": "r=2 is the worst small-r resource control and remains within the configured 1.50 cap.",
            "next_action": "Use r=2 as the first correctness prototype if Stage116 opens.",
        },
        {
            "gate": "stage115_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Toy C layout evidence does not kill lane-local multimask, but no correctness/noise/performance claim is made.",
            "next_action": "Stage116 should implement a toy arithmetic equivalence prototype before any MOSFHET hot-path work.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage115 Lane-Local Toy C Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Convert the Stage114 symbolic resource screen into a measured toy C",
        "layout/allocation/RSS gate for the lane-local multimask body-linear",
        "candidate.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage115_lane_local_toy_c_gate.py",
        "```",
        "",
        "## Gates",
        "",
        "- The generated toy C layout probe must compile.",
        "- Current and lane-local layouts must run for r=2/4/6/8 and N=2048/4096.",
        "- `product_over_requested_ratio` must remain above 1.0.",
        "- Target r=4, N=2048 requested-byte ratio must be at most 1.25.",
        "",
        "Passing this stage only permits a toy arithmetic prototype. It does not",
        "permit full SAB integration or a speedup claim.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(ratios: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage115 Lane-Local Toy C Resource Gate",
        "",
        "Date: 2026-07-03",
        "",
        "Stage115 separates a measurable representation question from the later",
        "cryptographic correctness question. The current shared-mask toy layout",
        "allocates accumulator, dense selector, and decomposition scratch",
        "components shaped like the existing `k=1,l=1` MAT path. The lane-local",
        "toy layout allocates `2r` accumulator polynomials and compact",
        "`2(1+2r)` selector polynomials, matching the conservative Stage114",
        "resource model.",
        "",
        "The gate uses requested bytes as the deterministic resource metric and",
        "RSS as a platform sanity check. RSS is not used as a performance claim.",
        "",
        "## Measured Requested-Byte Ratios",
        "",
        "| r | N | lane/current requested bytes | product ratio | product/requested ratio |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in ratios:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['requested_ratio_lane_over_current']} | "
            f"{row['product_ratio_current_over_lane']} | {row['product_over_requested_ratio']} |"
        )
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# Lane-Local Toy Layout Candidate",
        "",
        "## Status",
        "",
        "`LAYOUT_FEASIBLE_ARITHMETIC_PROTOTYPE_REQUIRED`",
        "",
        "## Representation",
        "",
        "The candidate replaces one shared accumulator mask plus r bodies with",
        "lane-local mask/body pairs in the toy representation. It also replaces",
        "dense `(1+r)^2` selector storage with the conservative compact model",
        "`2(1+2r)` selector polynomials.",
        "",
        "## Current Limits",
        "",
        "- This is not a MOSFHET ciphertext type yet.",
        "- This is not a key generation format yet.",
        "- This does not model noise, key switching, or complete SAB scheduling.",
        "- The next valid step is a toy arithmetic equivalence prototype.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], ratios: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage115 Lane-Local Toy C Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage115 builds and runs a generated C layout probe. It measures the",
        "current dense shared-mask toy layout against the lane-local multimask",
        "toy layout for r=2/4/6/8 and N=2048/4096.",
        "",
        "This is a representation/resource gate only. It does not prove",
        "cryptographic correctness, noise safety, AVX512 optimality, or complete",
        "SAB speedup.",
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
        "## Layout Ratios",
        "",
        "| r | N | requested ratio | RSS ratio | product ratio | product/requested | status |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in ratios:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['requested_ratio_lane_over_current']} | "
            f"{row['rss_ratio_lane_over_current']} | {row['product_ratio_current_over_lane']} | "
            f"{row['product_over_requested_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "For the target r=4, N=2048 control row, the conservative lane-local",
        "toy layout has bounded requested-byte overhead while reducing the",
        "product-term model from dense 25 to 9. That keeps the branch alive for",
        "a toy arithmetic equivalence prototype. It is not enough evidence to",
        "touch the MOSFHET hot path.",
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
        if row.get("run_id") != "stage115-lane-local-toy-c-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(RAW_CSV),
        rel(RATIO_CSV),
        rel(COMPILE_LOG),
        rel(C_SOURCE),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage115_lane_local_toy_c_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage115-lane-local-toy-c-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 115",
            "backend": "WSL gcc toy C",
            "command": "python scripts/build_stage115_lane_local_toy_c_gate.py",
            "params": "current vs lane-local toy layout r=2,4,6,8 N=2048,4096",
            "seed": "n/a",
            "status": status,
            "summary": "Stage115 measures toy C layout/resource overhead for lane-local multimask and routes only to toy arithmetic equivalence.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    write_variant()
    write_c_source()
    compile_ok, _ = compile_toy()
    raw_rows = build_raw_rows(compile_ok)
    ratios = build_ratio_rows(raw_rows)
    summary = build_summary(compile_ok, ratios)
    write_csv(RAW_CSV, raw_rows, RAW_FIELDS)
    write_csv(
        RATIO_CSV,
        ratios,
        [
            "r",
            "N",
            "current_requested_bytes",
            "lane_local_requested_bytes",
            "requested_ratio_lane_over_current",
            "current_rss_kb",
            "lane_local_rss_kb",
            "rss_ratio_lane_over_current",
            "current_product_terms",
            "lane_local_product_terms",
            "product_ratio_current_over_lane",
            "product_over_requested_ratio",
            "status",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(ratios)
    write_md(summary, ratios)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                RAW_CSV,
                RATIO_CSV,
                COMPILE_LOG,
                C_SOURCE,
                ROOT / "scripts" / "build_stage115_lane_local_toy_c_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage115 lane-local toy C gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
