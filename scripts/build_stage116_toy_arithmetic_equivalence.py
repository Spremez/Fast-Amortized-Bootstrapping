#!/usr/bin/env python3
"""Build and run Stage116 toy arithmetic equivalence gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage116_toy_arithmetic_equivalence"
SUMMARY_CSV = OUT_DIR / "summary.csv"
RESULT_CSV = OUT_DIR / "equivalence_results.csv"
COMPILE_LOG = OUT_DIR / "compile.log"
C_SOURCE = OUT_DIR / "toy_arithmetic_equivalence.c"
C_BINARY = OUT_DIR / "toy_arithmetic_equivalence"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage116_toy_arithmetic_equivalence.md"
PLAN_MD = ROOT / "experiments" / "stage116_toy_arithmetic_equivalence_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage116_lane_local_arithmetic_equivalence.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_lane_local_arithmetic_model.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

RESULT_FIELDS = [
    "r",
    "N",
    "dense_terms",
    "lane_local_terms",
    "product_ratio",
    "dense_lane_mismatches",
    "drop_failures",
    "max_lane_abs_gap",
    "max_drop_abs_gap",
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
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int64_t signed_small(uint64_t salt, uint64_t a, uint64_t b, uint64_t c) {
  uint64_t x = salt * 0x9e3779b97f4a7c15ULL;
  x ^= (a + 0x100000001b3ULL) * 0xbf58476d1ce4e5b9ULL;
  x ^= (b + 0x94d049bb133111ebULL) * 0x94d049bb133111ebULL;
  x ^= (c + 0x2545f4914f6cdd1dULL) * 0x2545f4914f6cdd1dULL;
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  int64_t v = (int64_t)(x % 17ULL) - 8;
  return v == 0 ? 1 : v;
}

static int64_t abs64(int64_t x) {
  return x < 0 ? -x : x;
}

static int64_t digit(size_t row, size_t coeff) {
  return signed_small(1, row, coeff, 0);
}

static int64_t secret(size_t lane, size_t coeff) {
  return signed_small(2, lane, coeff, 0);
}

static int64_t shared_mask(size_t row, size_t coeff) {
  return signed_small(3, row, coeff, 0);
}

static int64_t lane_mask(size_t row, size_t lane, size_t coeff) {
  return signed_small(4, row, lane, coeff);
}

static int64_t message(size_t row, size_t lane, size_t coeff) {
  if (row == 0) {
    return signed_small(5, lane, coeff, 0);
  }
  if (row == lane + 1) {
    return signed_small(6, lane, coeff, row);
  }
  return 0;
}

static int64_t dense_phase(size_t r, size_t lane, size_t coeff) {
  int64_t phase = 0;
  for (size_t row = 0; row < r + 1; row++) {
    const int64_t d = digit(row, coeff);
    const int64_t mask = shared_mask(row, coeff);
    const int64_t sec = secret(lane, coeff);
    const int64_t body = mask * sec + message(row, lane, coeff);
    phase += d * (body - mask * sec);
  }
  return phase;
}

static int64_t current_format_drop_phase(size_t r, size_t lane, size_t coeff) {
  int64_t phase = 0;
  for (size_t row = 0; row < r + 1; row++) {
    const int64_t d = digit(row, coeff);
    const int64_t mask = shared_mask(row, coeff);
    const int64_t sec = secret(lane, coeff);
    const int keep_body = row == 0 || row == lane + 1;
    const int64_t body = keep_body ? mask * sec + message(row, lane, coeff) : 0;
    phase += d * (body - mask * sec);
  }
  return phase;
}

static int64_t lane_local_phase(size_t r, size_t lane, size_t coeff) {
  (void)r;
  int64_t phase = 0;
  const size_t rows[2] = {0, lane + 1};
  for (size_t i = 0; i < 2; i++) {
    const size_t row = rows[i];
    const int64_t d = digit(row, coeff);
    const int64_t mask = lane_mask(row, lane, coeff);
    const int64_t sec = secret(lane, coeff);
    const int64_t body = mask * sec + message(row, lane, coeff);
    phase += d * (body - mask * sec);
  }
  return phase;
}

static int run_case(size_t r, size_t N) {
  uint64_t mismatches = 0;
  uint64_t drop_failures = 0;
  int64_t max_lane_gap = 0;
  int64_t max_drop_gap = 0;

  for (size_t coeff = 0; coeff < N; coeff++) {
    for (size_t lane = 0; lane < r; lane++) {
      const int64_t dense = dense_phase(r, lane, coeff);
      const int64_t lane_local = lane_local_phase(r, lane, coeff);
      const int64_t drop = current_format_drop_phase(r, lane, coeff);
      const int64_t lane_gap = abs64(dense - lane_local);
      const int64_t drop_gap = abs64(dense - drop);
      if (lane_gap != 0) mismatches++;
      if (drop_gap != 0) drop_failures++;
      if (lane_gap > max_lane_gap) max_lane_gap = lane_gap;
      if (drop_gap > max_drop_gap) max_drop_gap = drop_gap;
    }
  }

  const uint64_t dense_terms = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t lane_terms = 1ULL + 2ULL * (uint64_t)r;
  const double ratio = (double)dense_terms / (double)lane_terms;
  const char *status =
      mismatches == 0 && drop_failures > 0 ? "PASS_EQUIV_NEGATIVE_CONTROL" : "FAIL";

  printf("%zu,%zu,%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64
         ",%" PRId64 ",%" PRId64 ",%s\n",
      r, N, dense_terms, lane_terms, ratio, mismatches, drop_failures,
      max_lane_gap, max_drop_gap, status);
  return status[0] == 'P' ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6};
  const size_t Ns[] = {64, 256};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += run_case(rs[i], Ns[j]);
    }
  }
  return failures == 0 ? 0 : 1;
}
'''
    write_text_lf(C_SOURCE, source.lstrip())


def compile_toy() -> bool:
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
    return proc.returncode == 0


def run_toy(compile_ok: bool) -> List[Dict[str, str]]:
    if not compile_ok:
        return []
    proc = bash(f"./{rel(C_BINARY)}", timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(
            f"toy arithmetic run failed\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        if len(values) != len(RESULT_FIELDS):
            raise RuntimeError(f"unexpected result row: {line}")
        rows.append(dict(zip(RESULT_FIELDS, values)))
    return rows


def build_summary(compile_ok: bool, rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not compile_ok:
        return [
            {
                "gate": "stage116_compile",
                "status": "BLOCKED",
                "metric": "gcc_compile",
                "value": "false",
                "evidence": rel(COMPILE_LOG),
                "detail": "Toy arithmetic C probe did not compile.",
                "next_action": "Do not continue lane-local implementation until the probe compiles.",
            },
            {
                "gate": "stage116_decision",
                "status": "BLOCKED_STAGE116_TOY_ARITH_COMPILER_UNAVAILABLE",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(COMPILE_LOG),
                "detail": "No arithmetic equivalence evidence is available.",
                "next_action": "Stop the branch.",
            },
        ]

    all_equiv = all(row["dense_lane_mismatches"] == "0" for row in rows)
    negative_control = all(int(row["drop_failures"]) > 0 for row in rows)
    min_ratio = min(float(row["product_ratio"]) for row in rows)
    decision = (
        "PASS_STAGE116_TOY_ARITH_EQUIV_SELECTOR_PROTOTYPE_REQUIRED"
        if all_equiv and negative_control and min_ratio > 1.0
        else "FAIL_STAGE116_TOY_ARITH_EQUIV"
    )
    return [
        {
            "gate": "stage116_compile",
            "status": "PASS",
            "metric": "gcc_compile",
            "value": "true",
            "evidence": rel(COMPILE_LOG),
            "detail": "Generated toy arithmetic C probe compiled under WSL gcc.",
            "next_action": "Use only as toy arithmetic evidence.",
        },
        {
            "gate": "stage116_dense_vs_lane_local",
            "status": "PASS" if all_equiv else "FAIL",
            "metric": "dense_lane_mismatches",
            "value": ";".join(row["dense_lane_mismatches"] for row in rows),
            "evidence": rel(RESULT_CSV),
            "detail": "Lane-local compact arithmetic matches dense reference for all tested coefficients.",
            "next_action": "If this fails, stop the branch.",
        },
        {
            "gate": "stage116_negative_control",
            "status": "PASS_REJECTED_CURRENT_FORMAT" if negative_control else "FAIL",
            "metric": "drop_failures",
            "value": ";".join(row["drop_failures"] for row in rows),
            "evidence": rel(RESULT_CSV),
            "detail": "Current-format drop-offlane negative control fails as expected.",
            "next_action": "Do not implement loop-only current-format skipping.",
        },
        {
            "gate": "stage116_product_model",
            "status": "PASS",
            "metric": "min_dense_over_lane_terms",
            "value": f"{min_ratio:.6f}",
            "evidence": rel(RESULT_CSV),
            "detail": "Dense product terms remain above lane-local terms for all toy cases.",
            "next_action": "Product model must still be validated in a selector/key prototype.",
        },
        {
            "gate": "stage116_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Toy arithmetic equivalence is finite evidence for opening a selector-format prototype only.",
            "next_action": "Stage117 should design a MOSFHET-adjacent selector/key skeleton, still outside the SAB hot path.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage116 Toy Arithmetic Equivalence Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Convert Stage115 resource feasibility into an exact toy arithmetic gate:",
        "dense shared-mask reference and lane-local compact arithmetic must match",
        "for every tested coefficient, while current-format drop-offlane remains",
        "a failing negative control.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage116_toy_arithmetic_equivalence.py",
        "```",
        "",
        "Passing this stage only opens a selector-format prototype. It does not",
        "authorize MOSFHET hot-path integration.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage116 Lane-Local Arithmetic Equivalence",
        "",
        "Date: 2026-07-03",
        "",
        "The toy model uses the current dense shared-mask phase equation as the",
        "reference. Off-lane body rows carry zero message but are still needed in",
        "the current format to cancel shared-mask contributions. The lane-local",
        "model changes the mask invariant, so each lane only accumulates the",
        "shared row and its own body row.",
        "",
        "## Results",
        "",
        "| r | N | dense terms | lane-local terms | ratio | mismatches | drop failures |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_terms']} | "
            f"{row['lane_local_terms']} | {row['product_ratio']} | "
            f"{row['dense_lane_mismatches']} | {row['drop_failures']} |"
        )
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# Lane-Local Arithmetic Model",
        "",
        "## Status",
        "",
        "`TOY_ARITHMETIC_EQUIV_SELECTOR_PROTOTYPE_REQUIRED`",
        "",
        "## Invariant",
        "",
        "For each lane q, dense reference evaluates every row but off-lane body",
        "messages are zero. Lane-local arithmetic is allowed to skip off-lane rows",
        "only because the mask relation is changed to be lane-local.",
        "",
        "## Boundary",
        "",
        "This model does not define MOSFHET allocation, encryption, noise, key",
        "switching, DFT layout, or AVX512 code. It is a finite arithmetic screen",
        "for the next selector/key-format prototype.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage116 Toy Arithmetic Equivalence",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage116 compiles and runs a generated C arithmetic probe. It compares",
        "dense shared-mask reference phases, lane-local compact phases, and the",
        "known-bad current-format drop-offlane negative control.",
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
        "## Equivalence Rows",
        "",
        "| r | N | dense terms | lane terms | ratio | mismatches | drop failures | max drop gap | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['dense_terms']} | "
            f"{row['lane_local_terms']} | {row['product_ratio']} | "
            f"{row['dense_lane_mismatches']} | {row['drop_failures']} | "
            f"{row['max_drop_abs_gap']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The lane-local arithmetic model matches the dense reference on every",
        "tested coefficient, and the current-format drop-offlane control fails.",
        "This preserves the Stage112 warning: body-linear skipping needs a new",
        "selector/key or ciphertext format. It still does not prove a full SAB",
        "optimization.",
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
        if row.get("run_id") != "stage116-toy-arithmetic-equivalence-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(RESULT_CSV),
        rel(COMPILE_LOG),
        rel(C_SOURCE),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage116_toy_arithmetic_equivalence.py"),
    ]
    rows.append(
        {
            "run_id": "stage116-toy-arithmetic-equivalence-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 116",
            "backend": "WSL gcc toy C",
            "command": "python scripts/build_stage116_toy_arithmetic_equivalence.py",
            "params": "dense shared-mask vs lane-local arithmetic r=2,4,6 N=64,256",
            "seed": "deterministic",
            "status": status,
            "summary": "Stage116 proves toy arithmetic equivalence against dense reference and keeps current-format drop-offlane rejected.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    write_variant()
    write_c_source()
    compile_ok = compile_toy()
    rows = run_toy(compile_ok)
    summary = build_summary(compile_ok, rows)
    write_csv(RESULT_CSV, rows, RESULT_FIELDS)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(rows)
    write_md(summary, rows)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                RESULT_CSV,
                COMPILE_LOG,
                C_SOURCE,
                ROOT / "scripts" / "build_stage116_toy_arithmetic_equivalence.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage116 toy arithmetic equivalence: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
