#!/usr/bin/env python3
"""Build Stage118 real-type/noise/key design gate for lane-local MAT-SAB."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage118_real_type_design_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
LAYOUT_CSV = OUT_DIR / "type_layout.csv"
NOISE_CSV = OUT_DIR / "noise_key_model.csv"
COMPILE_LOG = OUT_DIR / "compile.log"
C_SOURCE = OUT_DIR / "real_type_design_gate.c"
C_BINARY = OUT_DIR / "real_type_design_gate"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage118_real_type_design_gate.md"
PLAN_MD = ROOT / "experiments" / "stage118_real_type_design_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage118_real_type_noise_key_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_lane_local_real_type_design.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


LAYOUT_FIELDS = [
    "r",
    "N",
    "current_acc_polys",
    "lane_acc_polys",
    "acc_ratio",
    "current_selector_polys",
    "lane_selector_polys",
    "selector_ratio",
    "current_dft_bytes",
    "lane_dft_bytes",
    "dft_byte_ratio",
    "key_secret_polys_current",
    "key_secret_polys_lane",
    "key_secret_ratio",
    "status",
]

NOISE_FIELDS = [
    "r",
    "dense_noise_terms",
    "lane_noise_terms",
    "noise_term_ratio_lane_over_dense",
    "dense_over_lane_product_ratio",
    "new_noise_unknowns",
    "required_next_gate",
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

typedef struct {
  uint64_t k;
  uint64_t r;
  uint64_t N;
  uint64_t mask_polys;
  uint64_t body_polys;
  uint64_t selector_terms;
  uint64_t selector_polys;
  uint64_t key_secret_polys;
} LaneLocalTypeDesign;

static LaneLocalTypeDesign make_design(uint64_t r, uint64_t N) {
  LaneLocalTypeDesign d;
  d.k = 1;
  d.r = r;
  d.N = N;
  d.mask_polys = r;
  d.body_polys = r;
  d.selector_terms = 1 + 2 * r;
  d.selector_polys = 2 * d.selector_terms;
  d.key_secret_polys = r;
  return d;
}

static int validate(uint64_t r, uint64_t N) {
  LaneLocalTypeDesign d = make_design(r, N);
  const uint64_t current_acc_polys = 1 + r;
  const uint64_t current_selector_polys = (1 + r) * (1 + r);
  const uint64_t lane_acc_polys = d.mask_polys + d.body_polys;
  const uint64_t current_key_secret_polys = r;
  const uint64_t dft_poly_bytes = N * sizeof(double);
  const uint64_t current_dft_bytes =
      (current_acc_polys + current_selector_polys) * dft_poly_bytes;
  const uint64_t lane_dft_bytes =
      (lane_acc_polys + d.selector_polys) * dft_poly_bytes;
  const int ok = d.k == 1 && lane_acc_polys == 2 * r &&
      d.selector_terms == 1 + 2 * r &&
      d.selector_polys == 2 * (1 + 2 * r) &&
      d.key_secret_polys == current_key_secret_polys &&
      current_selector_polys > d.selector_terms;
  printf("%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%.6f,"
         "%" PRIu64 ",%" PRIu64 ",%.6f,%" PRIu64 ",%" PRIu64 ",%.6f,"
         "%" PRIu64 ",%" PRIu64 ",%.6f,%s\n",
      r, N, current_acc_polys, lane_acc_polys,
      (double)lane_acc_polys / (double)current_acc_polys,
      current_selector_polys, d.selector_polys,
      (double)d.selector_polys / (double)current_selector_polys,
      current_dft_bytes, lane_dft_bytes,
      (double)lane_dft_bytes / (double)current_dft_bytes,
      current_key_secret_polys, d.key_secret_polys,
      (double)d.key_secret_polys / (double)current_key_secret_polys,
      ok ? "PASS_TYPE_SHAPE" : "FAIL");
  return ok ? 0 : 1;
}

int main(void) {
  const uint64_t rs[] = {2, 4, 6, 8};
  const uint64_t Ns[] = {2048, 4096};
  int failures = 0;
  for (size_t i = 0; i < sizeof(rs) / sizeof(rs[0]); i++) {
    for (size_t j = 0; j < sizeof(Ns) / sizeof(Ns[0]); j++) {
      failures += validate(rs[i], Ns[j]);
    }
  }
  return failures == 0 ? 0 : 1;
}
'''
    write_text_lf(C_SOURCE, source.lstrip())


def compile_probe() -> bool:
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


def run_probe(compile_ok: bool) -> List[Dict[str, str]]:
    if not compile_ok:
        return []
    proc = bash(f"./{rel(C_BINARY)}", timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(
            f"real type design probe failed\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    rows: List[Dict[str, str]] = []
    for line in sanitize_log(proc.stdout).splitlines():
        line = line.strip()
        if not line:
            continue
        values = line.split(",")
        if len(values) != len(LAYOUT_FIELDS):
            raise RuntimeError(f"unexpected type-layout row: {line}")
        rows.append(dict(zip(LAYOUT_FIELDS, values)))
    return rows


def build_noise_rows(layout_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = sorted({int(row["r"]) for row in layout_rows})
    rows: List[Dict[str, str]] = []
    for r in seen:
        dense_terms = (1 + r) * (1 + r)
        lane_terms = 1 + 2 * r
        term_ratio = lane_terms / dense_terms
        product_ratio = dense_terms / lane_terms
        rows.append(
            {
                "r": str(r),
                "dense_noise_terms": str(dense_terms),
                "lane_noise_terms": str(lane_terms),
                "noise_term_ratio_lane_over_dense": f"{term_ratio:.6f}",
                "dense_over_lane_product_ratio": f"{product_ratio:.6f}",
                "new_noise_unknowns": "lane-local encryption variance; DFT roundoff; extract/KS compatibility; inter-lane independence",
                "required_next_gate": "real object phase/noise simulator before MOSFHET hot path",
                "status": "NOISE_MODEL_RECORDED_NOT_PROVEN",
            }
        )
    return rows


def build_summary(compile_ok: bool, layout_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if not compile_ok:
        return [
            {
                "gate": "stage118_compile",
                "status": "BLOCKED",
                "metric": "gcc_compile",
                "value": "false",
                "evidence": rel(COMPILE_LOG),
                "detail": "Real-type design C probe did not compile.",
                "next_action": "Stop before type design.",
            },
            {
                "gate": "stage118_decision",
                "status": "BLOCKED_STAGE118_REAL_TYPE_COMPILER",
                "metric": "next_gate_policy",
                "value": "",
                "evidence": rel(COMPILE_LOG),
                "detail": "No type-design evidence is available.",
                "next_action": "Stop the branch.",
            },
        ]

    shape_ok = all(row["status"] == "PASS_TYPE_SHAPE" for row in layout_rows)
    key_ok = all(row["key_secret_ratio"] == "1.000000" for row in layout_rows)
    r4 = next(row for row in layout_rows if row["r"] == "4" and row["N"] == "2048")
    r4_dft_ratio = float(r4["dft_byte_ratio"])
    noise_recorded = all(row["status"] == "NOISE_MODEL_RECORDED_NOT_PROVEN" for row in noise_rows)
    decision = (
        "PASS_STAGE118_REAL_TYPE_DESIGN_READY_OBJECT_PROTOTYPE_REQUIRED"
        if shape_ok and key_ok and r4_dft_ratio <= 1.10 and noise_recorded
        else "FAIL_STAGE118_REAL_TYPE_DESIGN"
    )
    return [
        {
            "gate": "stage118_compile",
            "status": "PASS",
            "metric": "gcc_compile",
            "value": "true",
            "evidence": rel(COMPILE_LOG),
            "detail": "Generated real-type design C probe compiled under WSL gcc.",
            "next_action": "Use only as type-shape evidence.",
        },
        {
            "gate": "stage118_type_shape",
            "status": "PASS" if shape_ok else "FAIL",
            "metric": "rows",
            "value": str(len(layout_rows)),
            "evidence": rel(LAYOUT_CSV),
            "detail": "Lane-local type shape preserves 2r accumulator polynomials and 2(1+2r) selector polynomials.",
            "next_action": "If this fails, do not design real objects.",
        },
        {
            "gate": "stage118_key_secret_count",
            "status": "PASS" if key_ok else "FAIL",
            "metric": "key_secret_ratio",
            "value": ";".join(row["key_secret_ratio"] for row in layout_rows),
            "evidence": rel(LAYOUT_CSV),
            "detail": "The design reuses r lane secrets for k=1 rather than increasing secret polynomial count.",
            "next_action": "Object prototype must verify key compatibility.",
        },
        {
            "gate": "stage118_target_r4_bytes",
            "status": "PASS_BOUNDED" if r4_dft_ratio <= 1.10 else "FAIL",
            "metric": "r4_N2048_dft_byte_ratio",
            "value": f"{r4_dft_ratio:.6f}",
            "evidence": rel(LAYOUT_CSV),
            "detail": "Target r=4 combined accumulator+selector DFT byte model is bounded.",
            "next_action": "Measured allocation still required in the object prototype.",
        },
        {
            "gate": "stage118_noise_key_model",
            "status": "RECORDED_NOT_PROVEN" if noise_recorded else "FAIL",
            "metric": "noise_rows",
            "value": str(len(noise_rows)),
            "evidence": rel(NOISE_CSV),
            "detail": "Noise term count is favorable, but real encryption/noise safety remains unproven.",
            "next_action": "Stage119 must implement phase/noise simulation for real objects.",
        },
        {
            "gate": "stage118_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Real-type design is ready only for object prototype, not SAB integration.",
            "next_action": "Stage119 should build real-object allocation/phase/noise prototype outside the hot path.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage118 Real-Type Design Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Convert the Stage117 selector skeleton into a MOSFHET-adjacent type, key,",
        "and noise design gate without touching `src/mosfhet` or `sab_pvw_*`.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage118_real_type_design_gate.py",
        "```",
        "",
        "## Gates",
        "",
        "- generated C type-shape probe must compile;",
        "- lane-local accumulator shape must be `2r` polynomials for k=1;",
        "- selector shape must be `2(1+2r)` conservative DFT polynomials;",
        "- key secret polynomial count must remain `r` for k=1;",
        "- target r=4,N=2048 combined DFT byte ratio must be bounded;",
        "- noise model is recorded as not proven and must route to Stage119.",
    ]
    write_text_lf(PLAN_MD, "\n".join(lines) + "\n")


def write_theory(layout_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage118 Real-Type Noise/Key Model",
        "",
        "Date: 2026-07-03",
        "",
        "For k=1, the current shared-mask PVW_TMLWE accumulator has `1+r`",
        "polynomial components. The lane-local design requires one mask/body pair",
        "per lane, or `2r` components. The current dense MAT selector stores",
        "`(1+r)^2` DFT polynomials, while the conservative lane-local selector",
        "stores `2(1+2r)` DFT polynomials.",
        "",
        "The key secret polynomial count remains `r` for k=1 because each lane",
        "already has a lane secret in the current PVW key model. This is a design",
        "claim that must be verified by a real object phase/noise prototype.",
        "",
        "## Layout Rows",
        "",
        "| r | N | acc ratio | selector ratio | DFT byte ratio | key ratio |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['acc_ratio']} | "
            f"{row['selector_ratio']} | {row['dft_byte_ratio']} | "
            f"{row['key_secret_ratio']} |"
        )
    lines += [
        "",
        "## Noise Rows",
        "",
        "| r | dense terms | lane terms | lane/dense term ratio | status |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in noise_rows:
        lines.append(
            f"| {row['r']} | {row['dense_noise_terms']} | {row['lane_noise_terms']} | "
            f"{row['noise_term_ratio_lane_over_dense']} | {row['status']} |"
        )
    write_text_lf(THEORY_MD, "\n".join(lines) + "\n")


def write_variant() -> None:
    lines = [
        "# V118: Lane-Local Real-Type Design",
        "",
        "## Summary",
        "",
        "- Parent algorithm: 2025/686 binary sparse amortized bootstrapping with local PVW/MAT-SAB batching.",
        "- Focused module: MAT-RLWE/r-body external-product representation.",
        "- Optimization target: amortized complete-SAB latency `T_bootstrap/r`.",
        "- Status labels: `[theory-partial]`, `[experiment-gated]`, `[not-hot-path]`.",
        "- Main hypothesis: lane-local type design can preserve Stage116 arithmetic while reducing dense selector terms.",
        "",
        "## Mathematical Definition",
        "",
        "For k=1 and r lanes, define a lane-local accumulator with one mask/body",
        "pair per lane, giving `2r` polynomial components. Define a selector",
        "skeleton with one shared term and two lane-local terms per lane, giving",
        "`1+2r` product terms and `2(1+2r)` conservative DFT polynomials.",
        "",
        "## Pseudocode",
        "",
        "```text",
        "Input: r lane count, N polynomial dimension",
        "Output: lane-local type shape and gate status",
        "1. Allocate conceptual accumulator fields mask[q], body[q].",
        "2. Allocate conceptual selector fields shared plus lane_mask[q], lane_body[q].",
        "3. Check no off-lane body fields exist.",
        "4. Check key secret polynomial count equals r for k=1.",
        "5. Record noise/key unknowns and stop before hot-path integration.",
        "```",
        "",
        "## Delta From Original Algorithm",
        "",
        "| Original component | Variant component | Relationship | Evidence/status |",
        "| --- | --- | --- | --- |",
        "| shared-mask PVW_TMLWE `1+r` accumulator | lane-local `2r` accumulator | changes data structure | Stage118 design gate |",
        "| dense MAT selector `(1+r)^2` polys | compact selector `2(1+2r)` polys | reduces term/storage model | Stage117-118 |",
        "| current PVW key `r` lane secrets | same `r` lane secrets | intended key reuse | must be verified by Stage119 |",
        "",
        "## Complexity Change",
        "",
        "- Time: target external-product terms change from `(1+r)^2` to `1+2r`.",
        "- Memory: accumulator grows from `1+r` to `2r`; selector storage shrinks for r>=4.",
        "- What must be measured: real allocation, phase equivalence, noise, DFT conversion, and complete-SAB timing.",
        "",
        "## Theory Dependencies",
        "",
        "- Inherited assumptions: binary SAB schedule and lane-independent outputs.",
        "- New assumptions: lane-local mask encryption preserves phase and security.",
        "- Proof steps affected: selector encryption, external product correctness, extract/KS compatibility, noise accumulation.",
        "- Current status: design gate passed; proof and real-object evidence missing.",
        "",
        "## Potential Failure Reasons",
        "",
        "- Real encryption cannot preserve the lane-local invariant.",
        "- Noise or key switching grows beyond scalar/PVW baseline.",
        "- DFT layout or AVX512 implementation loses the product-count advantage.",
        "- Complete SAB schedule reintroduces dense cancellation.",
        "",
        "## Required Experiments",
        "",
        "- Baselines: dense shared-mask PVW/MAT and repeated scalar SAB.",
        "- Metrics: phase mismatches, noise gap, key/RSS ratio, `T_bootstrap/r`.",
        "- Ablations: r=2/4 first, then r=6 if real-object gates pass.",
        "- Success criteria: real-object phase/noise pass before any hot-path code.",
        "- Failure criteria: any phase mismatch, unexplained noise growth, or memory blowup.",
        "",
        "## Paper Contribution Candidate",
        "",
        "A lane-local MAT-RLWE SAB representation may reduce body-output external",
        "product terms `[theory-partial][experiment-gated]`. It is not paper-ready",
        "until real-object, noise, complete-SAB, and related-work gates pass.",
    ]
    write_text_lf(VARIANT_MD, "\n".join(lines) + "\n")


def write_md(summary: List[Dict[str, str]], layout_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage118 Real-Type Design Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage118 converts the Stage117 selector skeleton into a finite",
        "MOSFHET-adjacent type/key/noise design gate. It does not change source",
        "hot paths.",
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
        "## Type Layout",
        "",
        "| r | N | acc ratio | selector ratio | DFT byte ratio | key ratio | status |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in layout_rows:
        lines.append(
            f"| {row['r']} | {row['N']} | {row['acc_ratio']} | "
            f"{row['selector_ratio']} | {row['dft_byte_ratio']} | "
            f"{row['key_secret_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Noise/Key Status",
        "",
        "| r | lane/dense noise terms | product ratio | status |",
        "|---:|---:|---:|---|",
    ]
    for row in noise_rows:
        lines.append(
            f"| {row['r']} | {row['noise_term_ratio_lane_over_dense']} | "
            f"{row['dense_over_lane_product_ratio']} | {row['status']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The type-shape gate is positive, but the noise/key row is explicitly",
        "`RECORDED_NOT_PROVEN`. The next stage must build a real-object",
        "allocation/phase/noise prototype before any integration with SAB.",
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
        if row.get("run_id") != "stage118-real-type-design-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(LAYOUT_CSV),
        rel(NOISE_CSV),
        rel(COMPILE_LOG),
        rel(C_SOURCE),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage118_real_type_design_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage118-real-type-design-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 118",
            "backend": "WSL gcc design C",
            "command": "python scripts/build_stage118_real_type_design_gate.py",
            "params": "lane-local real-type design r=2,4,6,8 N=2048,4096",
            "seed": "n/a",
            "status": status,
            "summary": "Stage118 validates lane-local real-type shape and records noise/key risks before object prototype.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    write_variant()
    write_c_source()
    compile_ok = compile_probe()
    layout_rows = run_probe(compile_ok)
    noise_rows = build_noise_rows(layout_rows)
    summary = build_summary(compile_ok, layout_rows, noise_rows)
    write_csv(LAYOUT_CSV, layout_rows, LAYOUT_FIELDS)
    write_csv(NOISE_CSV, noise_rows, NOISE_FIELDS)
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(layout_rows, noise_rows)
    write_md(summary, layout_rows, noise_rows)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                LAYOUT_CSV,
                NOISE_CSV,
                COMPILE_LOG,
                C_SOURCE,
                ROOT / "scripts" / "build_stage118_real_type_design_gate.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage118 real type design gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") or status.startswith("BLOCKED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
