#!/usr/bin/env python3
"""Build and run Stage117 lane-local selector skeleton gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage117_selector_skeleton_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
MAP_CSV = OUT_DIR / "selector_skeleton.csv"
COMPILE_LOG = OUT_DIR / "compile.log"
C_SOURCE = OUT_DIR / "selector_skeleton_gate.c"
C_BINARY = OUT_DIR / "selector_skeleton_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage117_selector_skeleton_gate.md"
PLAN_MD = ROOT / "experiments" / "stage117_selector_skeleton_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage117_selector_skeleton_invariants.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_lane_local_selector_skeleton.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

MAP_FIELDS = [
    "r",
    "dense_terms",
    "skeleton_terms",
    "selector_polys",
    "accumulator_polys",
    "product_ratio",
    "shared_terms",
    "lane_mask_terms",
    "lane_body_terms",
    "offlane_body_terms",
    "missing_lane_terms",
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

enum TermKind {
  TERM_SHARED = 0,
  TERM_LANE_MASK = 1,
  TERM_LANE_BODY = 2
};

typedef struct {
  enum TermKind kind;
  size_t lane;
  size_t source_row;
} SelectorTerm;

static SelectorTerm *build_terms(size_t r, size_t *term_count) {
  *term_count = 1 + 2 * r;
  SelectorTerm *terms = (SelectorTerm *)calloc(*term_count, sizeof(SelectorTerm));
  if (terms == NULL) {
    fprintf(stderr, "calloc failed\n");
    exit(2);
  }
  terms[0].kind = TERM_SHARED;
  terms[0].lane = (size_t)-1;
  terms[0].source_row = 0;
  for (size_t lane = 0; lane < r; lane++) {
    const size_t mask_idx = 1 + 2 * lane;
    const size_t body_idx = mask_idx + 1;
    terms[mask_idx].kind = TERM_LANE_MASK;
    terms[mask_idx].lane = lane;
    terms[mask_idx].source_row = 0;
    terms[body_idx].kind = TERM_LANE_BODY;
    terms[body_idx].lane = lane;
    terms[body_idx].source_row = lane + 1;
  }
  return terms;
}

static int validate(size_t r) {
  size_t term_count = 0;
  SelectorTerm *terms = build_terms(r, &term_count);
  uint64_t shared_terms = 0;
  uint64_t lane_mask_terms = 0;
  uint64_t lane_body_terms = 0;
  uint64_t offlane_body_terms = 0;
  uint64_t missing_lane_terms = 0;

  for (size_t i = 0; i < term_count; i++) {
    if (terms[i].kind == TERM_SHARED) {
      shared_terms++;
      if (terms[i].source_row != 0) missing_lane_terms++;
    } else if (terms[i].kind == TERM_LANE_MASK) {
      lane_mask_terms++;
      if (terms[i].lane >= r || terms[i].source_row != 0) missing_lane_terms++;
    } else if (terms[i].kind == TERM_LANE_BODY) {
      lane_body_terms++;
      if (terms[i].lane >= r) {
        missing_lane_terms++;
      } else if (terms[i].source_row != terms[i].lane + 1) {
        offlane_body_terms++;
      }
    } else {
      missing_lane_terms++;
    }
  }

  for (size_t lane = 0; lane < r; lane++) {
    uint64_t has_mask = 0;
    uint64_t has_body = 0;
    for (size_t i = 0; i < term_count; i++) {
      if (terms[i].lane == lane && terms[i].kind == TERM_LANE_MASK) has_mask++;
      if (terms[i].lane == lane && terms[i].kind == TERM_LANE_BODY) has_body++;
    }
    if (has_mask != 1 || has_body != 1) missing_lane_terms++;
  }

  const uint64_t dense_terms = (uint64_t)(r + 1) * (uint64_t)(r + 1);
  const uint64_t skeleton_terms = (uint64_t)term_count;
  const uint64_t selector_polys = 2 * skeleton_terms;
  const uint64_t accumulator_polys = 2 * (uint64_t)r;
  const double product_ratio = (double)dense_terms / (double)skeleton_terms;
  const int ok = shared_terms == 1 && lane_mask_terms == r && lane_body_terms == r &&
      offlane_body_terms == 0 && missing_lane_terms == 0 && product_ratio > 1.0;

  printf("%zu,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%.6f,"
         "%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%s\n",
      r, dense_terms, skeleton_terms, selector_polys, accumulator_polys,
      product_ratio, shared_terms, lane_mask_terms, lane_body_terms,
      offlane_body_terms, missing_lane_terms, ok ? "PASS_SKELETON" : "FAIL");

  free(terms);
  return ok ? 0 : 1;
}

int main(void) {
  const size_t rs[] = {2, 4, 6, 8};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    failures += validate(rs[i]);
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
            f"selector skeleton run failed\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        if len(values) != len(MAP_FIELDS):
            raise RuntimeError(f"unexpected skeleton row: {line}")
        rows.append(dict(zip(MAP_FIELDS, values)))
    return rows


def build_summary(compile_ok: bool, rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not compile_ok:
        return [
            {
                "gate": "stage117_compile",
                "status": "BLOCKED",
                "metric": "gcc_compile",
                "value": "false",
                "evidence": rel(COMPILE_LOG),
                "detail": "Selector skeleton probe did not compile.",
                "next_action": "Stop before selector/key design.",
            },
            {
                "gate": "stage117_decision",
                "status": "BLOCKED_STAGE117_SELECTOR_SKELETON_COMPILER",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(COMPILE_LOG),
                "detail": "No selector skeleton evidence is available.",
                "next_action": "Stop the branch.",
            },
        ]

    all_pass = all(row["status"] == "PASS_SKELETON" for row in rows)
    no_offlane = all(row["offlane_body_terms"] == "0" for row in rows)
    no_missing = all(row["missing_lane_terms"] == "0" for row in rows)
    min_ratio = min(float(row["product_ratio"]) for row in rows)
    decision = (
        "PASS_STAGE117_SELECTOR_SKELETON_READY_REAL_TYPE_DESIGN_REQUIRED"
        if all_pass and no_offlane and no_missing and min_ratio > 1.0
        else "FAIL_STAGE117_SELECTOR_SKELETON"
    )
    return [
        {
            "gate": "stage117_compile",
            "status": "PASS",
            "metric": "gcc_compile",
            "value": "true",
            "evidence": rel(COMPILE_LOG),
            "detail": "Generated selector skeleton C probe compiled under WSL gcc.",
            "next_action": "Use only as skeleton invariant evidence.",
        },
        {
            "gate": "stage117_mapping_invariants",
            "status": "PASS" if all_pass else "FAIL",
            "metric": "rows",
            "value": str(len(rows)),
            "evidence": rel(MAP_CSV),
            "detail": "Every r row has one shared term and exactly one mask/body pair per lane.",
            "next_action": "If this fails, revise the selector skeleton before code.",
        },
        {
            "gate": "stage117_no_offlane",
            "status": "PASS" if no_offlane else "FAIL",
            "metric": "offlane_body_terms",
            "value": ";".join(row["offlane_body_terms"] for row in rows),
            "evidence": rel(MAP_CSV),
            "detail": "Skeleton has no off-lane body terms.",
            "next_action": "Preserve this invariant in any real type.",
        },
        {
            "gate": "stage117_product_model",
            "status": "PASS",
            "metric": "min_dense_over_skeleton_terms",
            "value": f"{min_ratio:.6f}",
            "evidence": rel(MAP_CSV),
            "detail": "Skeleton term counts match the Stage114-116 product model.",
            "next_action": "Real type design must preserve the same term accounting.",
        },
        {
            "gate": "stage117_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Selector skeleton is ready only for real-type design outside the SAB hot path.",
            "next_action": "Stage118 should design real MOSFHET-adjacent structs and noise/key gates.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage117 Selector Skeleton Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Turn Stage116 toy arithmetic into a finite selector/key skeleton invariant",
        "gate. The skeleton must expose `1+2r` terms, complete lane coverage, and",
        "no off-lane body terms.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage117_selector_skeleton_gate.py",
        "```",
        "",
        "Passing this stage opens real-type design only. It does not change",
        "`sab_pvw_*` or the MOSFHET hot path.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage117 Selector Skeleton Invariants",
        "",
        "Date: 2026-07-03",
        "",
        "The selector skeleton is a term map, not a ciphertext implementation. It",
        "has one global shared term and, for each lane, one lane-local mask term",
        "and one lane-local body term. This gives `1+2r` product terms and",
        "`2(1+2r)` conservative selector polynomials.",
        "",
        "| r | dense terms | skeleton terms | selector polys | acc polys | ratio |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['dense_terms']} | {row['skeleton_terms']} | "
            f"{row['selector_polys']} | {row['accumulator_polys']} | "
            f"{row['product_ratio']} |"
        )
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# Lane-Local Selector Skeleton",
        "",
        "## Status",
        "",
        "`SELECTOR_SKELETON_READY_REAL_TYPE_DESIGN_REQUIRED`",
        "",
        "## Skeleton",
        "",
        "- one global shared term;",
        "- one lane-local mask term per lane;",
        "- one lane-local body term per lane;",
        "- no off-lane body term;",
        "- conservative selector polynomial count `2(1+2r)`.",
        "",
        "## Boundary",
        "",
        "This is not encryption, DFT storage, key generation, noise analysis, or",
        "SAB integration. It is the term-map invariant for the next real-type",
        "design gate.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage117 Selector Skeleton Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage117 compiles and runs a generated C term-map skeleton. It checks",
        "that the lane-local route has complete per-lane mask/body coverage and",
        "no off-lane body terms before any MOSFHET type design.",
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
        "## Skeleton Rows",
        "",
        "| r | dense terms | skeleton terms | selector polys | acc polys | ratio | offlane | missing | status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['dense_terms']} | {row['skeleton_terms']} | "
            f"{row['selector_polys']} | {row['accumulator_polys']} | "
            f"{row['product_ratio']} | {row['offlane_body_terms']} | "
            f"{row['missing_lane_terms']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The skeleton preserves the Stage114-116 term model for r=2/4/6/8. The",
        "next stage must still design real MOSFHET-adjacent structs, encryption",
        "semantics, noise accounting, and conversion gates before any SAB code is",
        "touched.",
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
        if row.get("run_id") != "stage117-selector-skeleton-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(MAP_CSV),
        rel(COMPILE_LOG),
        rel(C_SOURCE),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage117_selector_skeleton_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage117-selector-skeleton-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 117",
            "backend": "WSL gcc toy C",
            "command": "python scripts/build_stage117_selector_skeleton_gate.py",
            "params": "lane-local selector skeleton r=2,4,6,8",
            "seed": "n/a",
            "status": status,
            "summary": "Stage117 validates a finite lane-local selector term-map skeleton outside the SAB hot path.",
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
    write_csv(MAP_CSV, rows, MAP_FIELDS)
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
                MAP_CSV,
                COMPILE_LOG,
                C_SOURCE,
                ROOT / "scripts" / "build_stage117_selector_skeleton_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage117 selector skeleton gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
