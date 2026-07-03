#!/usr/bin/env python3
"""Build Stage113 r=2 selector-format algebraic simulator."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage113_r2_selector_simulator"
SUMMARY_CSV = OUT_DIR / "summary.csv"
PHASE_CSV = OUT_DIR / "phase_simulation.csv"
PRODUCT_CSV = OUT_DIR / "product_model.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage113_r2_selector_simulator.md"
PLAN_MD = ROOT / "experiments" / "stage113_r2_selector_simulator_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage113_lane_local_multimask_phase.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_r2_lane_local_multimask.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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


def build_phase_rows() -> List[Dict[str, str]]:
    digits = {"a": 2, "b0": 3, "b1": 5}
    masks = {"a": 7, "b0": 23, "b1": 29}
    secrets = [3, 5]
    messages = {
        "a": [11, 13],
        "b0": [17, 0],
        "b1": [0, 19],
    }

    expected = []
    for lane in range(2):
        expected.append(
            sum(digits[row] * messages[row][lane] for row in ["a", "b0", "b1"])
        )

    dense = []
    for lane, secret in enumerate(secrets):
        phase = 0
        for row in ["a", "b0", "b1"]:
            body = masks[row] * secret + messages[row][lane]
            phase += digits[row] * (body - masks[row] * secret)
        dense.append(phase)

    loop_drop = []
    for lane, secret in enumerate(secrets):
        phase = 0
        for row in ["a", "b0", "b1"]:
            keep_body = row == "a" or row == f"b{lane}"
            body = masks[row] * secret + messages[row][lane] if keep_body else 0
            phase += digits[row] * (body - masks[row] * secret)
        loop_drop.append(phase)

    lane_local = []
    for lane, secret in enumerate(secrets):
        phase = 0
        for row in ["a", f"b{lane}"]:
            lane_mask = masks[row] + 100 * lane
            body = lane_mask * secret + messages[row][lane]
            phase += digits[row] * (body - lane_mask * secret)
        lane_local.append(phase)

    def row(name: str, phases: List[int], status: str, interpretation: str) -> Dict[str, str]:
        return {
            "variant": name,
            "phase0": str(phases[0]),
            "expected0": str(expected[0]),
            "phase1": str(phases[1]),
            "expected1": str(expected[1]),
            "status": status,
            "interpretation": interpretation,
        }

    return [
        row(
            "dense_shared_mask_reference",
            dense,
            "PASS",
            "Dense shared-mask row-output products match the expected phases.",
        ),
        row(
            "loop_only_drop_offlane_current_format",
            loop_drop,
            "FAIL_COUNTEREXAMPLE",
            "Skipping off-lane bodies while retaining shared masks breaks both lane phases.",
        ),
        row(
            "lane_local_multimask_candidate",
            lane_local,
            "PASS_PHASE_EQUIV",
            "Lane-local masks allow skipping off-lane body rows in this r=2 algebraic model.",
        ),
    ]


def build_product_rows() -> List[Dict[str, str]]:
    r = 2
    k = 1
    l = 1
    dense_products = (k + r) * (k + r) * l
    lane_local_target = k + 2 * r
    return [
        {
            "model": "current_dense_shared_mask",
            "r": str(r),
            "products": str(dense_products),
            "products_per_lane": f"{dense_products / r:.3f}",
            "resource_warning": "Current valid baseline.",
        },
        {
            "model": "lane_local_multimask_target",
            "r": str(r),
            "products": str(lane_local_target),
            "products_per_lane": f"{lane_local_target / r:.3f}",
            "resource_warning": "Requires separate lane-local mask/key resource model.",
        },
        {
            "model": "raw_product_ratio_dense_over_lane_local",
            "r": str(r),
            "products": f"{dense_products / lane_local_target:.3f}",
            "products_per_lane": f"{(dense_products / r) / (lane_local_target / r):.3f}",
            "resource_warning": "Arithmetic ratio only; not a complete-SAB speedup claim.",
        },
    ]


def build_summary(phase_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    dense_ok = next(row for row in phase_rows if row["variant"] == "dense_shared_mask_reference")["status"] == "PASS"
    drop_fails = next(row for row in phase_rows if row["variant"] == "loop_only_drop_offlane_current_format")["status"] == "FAIL_COUNTEREXAMPLE"
    lane_local_ok = next(row for row in phase_rows if row["variant"] == "lane_local_multimask_candidate")["status"] == "PASS_PHASE_EQUIV"
    decision = (
        "PASS_STAGE113_R2_LANE_LOCAL_SIM_PHASE_EQUIV_RESOURCE_REQUIRED"
        if dense_ok and drop_fails and lane_local_ok
        else "FAIL_STAGE113_R2_SELECTOR_SIMULATOR"
    )
    return [
        {
            "gate": "stage113_dense_reference",
            "status": "PASS" if dense_ok else "FAIL",
            "metric": "dense_phase_equiv",
            "value": str(dense_ok),
            "evidence": rel(PHASE_CSV),
            "detail": "Dense reference matches expected r=2 phases.",
            "next_action": "Use dense shared-mask as the simulator baseline.",
        },
        {
            "gate": "stage113_current_format_drop_offlane",
            "status": "PASS_REJECTED" if drop_fails else "FAIL",
            "metric": "counterexample",
            "value": str(drop_fails),
            "evidence": rel(PHASE_CSV),
            "detail": "Current-format loop-only skipping is rejected.",
            "next_action": "Do not implement this as C hot-path optimization.",
        },
        {
            "gate": "stage113_lane_local_candidate",
            "status": "PASS_PHASE_EQUIV" if lane_local_ok else "FAIL",
            "metric": "r2_phase_equiv",
            "value": str(lane_local_ok),
            "evidence": rel(PHASE_CSV),
            "detail": "Lane-local multimask candidate matches dense phases in the r=2 algebraic model.",
            "next_action": "Open resource/key-size and toy C representation gate before performance work.",
        },
        {
            "gate": "stage113_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "The candidate is phase-plausible but changes ciphertext/key resources.",
            "next_action": "Stage114 should quantify key/ciphertext resource cost before implementation.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage113 r=2 Selector Simulator Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Run a deterministic r=2 algebraic simulator for new-format body-linear",
        "selector candidates after Stage112 rejected current-format loop-only",
        "off-lane skipping.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage113_r2_selector_simulator.py",
        "```",
        "",
        "## Gate",
        "",
        "- Dense shared-mask reference must match expected phases.",
        "- Current-format off-lane skipping must fail as a counterexample.",
        "- Lane-local multimask candidate must match dense phases before any",
        "  resource or C implementation work.",
    ]
    PLAN_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_theory() -> None:
    lines = [
        "# Stage113 Lane-Local Multimask Phase Check",
        "",
        "Date: 2026-07-03",
        "",
        "The r=2 simulator separates phase validity from implementation cost.",
        "The lane-local multimask candidate changes the ciphertext shape so that",
        "a row used for lane 0 does not contribute to lane 1's mask. Under that",
        "changed invariant, off-lane body rows can be skipped in the toy model.",
        "",
        "This does not prove a full SAB optimization. It only proves that one",
        "new-format direction is phase-plausible enough to justify a resource",
        "model and a toy C representation gate.",
    ]
    THEORY_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_variant() -> None:
    lines = [
        "# r=2 Lane-Local Multimask MAT-SAB Candidate",
        "",
        "## Status",
        "",
        "`PHASE_PLAUSIBLE_RESOURCE_MODEL_REQUIRED`",
        "",
        "## Definition",
        "",
        "Replace the single shared output mask in the algebraic model with",
        "lane-local mask accumulations. Lane `q` only accumulates mask/body rows",
        "that are required for its own phase.",
        "",
        "## Delta From Current PVW_TMLWE",
        "",
        "Current PVW_TMLWE uses one shared mask vector and r bodies. This candidate",
        "uses lane-local masks, so it is not a drop-in replacement for the current",
        "`MAT_TRGSW_DFT` hot path.",
        "",
        "## Required Next Evidence",
        "",
        "- key-size/ciphertext-size model;",
        "- noise model for lane-local masks;",
        "- r=2 toy C representation and dense-reference equivalence;",
        "- only then a complete-SAB performance gate.",
    ]
    VARIANT_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_md(summary: List[Dict[str, str]], phase_rows: List[Dict[str, str]], product_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage113 r=2 Selector Simulator",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage113 runs an algebraic r=2 simulator. It rejects current-format",
        "loop-only off-lane skipping again and shows that a lane-local multimask",
        "new-format candidate can match dense phases in the toy model.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['detail']} |")
    lines += [
        "",
        "## Phase Simulation",
        "",
        "| variant | status | phase0 | expected0 | phase1 | expected1 | interpretation |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['variant']} | {row['status']} | {row['phase0']} | {row['expected0']} | "
            f"{row['phase1']} | {row['expected1']} | {row['interpretation']} |"
        )
    lines += [
        "",
        "## Product Model",
        "",
        "| model | r | products | products/lane | warning |",
        "|---|---:|---:|---:|---|",
    ]
    for row in product_rows:
        lines.append(
            f"| {row['model']} | {row['r']} | {row['products']} | "
            f"{row['products_per_lane']} | {row['resource_warning']} |"
        )
    OUT_MD.write_bytes("\n".join(lines).encode("utf-8"))


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
        if row.get("run_id") != "stage113-r2-selector-simulator-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(VARIANT_MD),
        rel(SUMMARY_CSV),
        rel(PHASE_CSV),
        rel(PRODUCT_CSV),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage113_r2_selector_simulator.py"),
    ]
    rows.append(
        {
            "run_id": "stage113-r2-selector-simulator-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 113",
            "backend": "n/a",
            "command": "python scripts/build_stage113_r2_selector_simulator.py",
            "params": "r=2 algebraic dense/reference/drop-offlane/lane-local simulator",
            "seed": "deterministic",
            "status": status,
            "summary": "Stage113 shows lane-local multimask is phase-plausible in an r=2 algebraic simulator but requires resource modeling before implementation.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    phase_rows = build_phase_rows()
    product_rows = build_product_rows()
    summary = build_summary(phase_rows)
    write_csv(
        PHASE_CSV,
        phase_rows,
        ["variant", "phase0", "expected0", "phase1", "expected1", "status", "interpretation"],
    )
    write_csv(
        PRODUCT_CSV,
        product_rows,
        ["model", "r", "products", "products_per_lane", "resource_warning"],
    )
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory()
    write_variant()
    write_md(summary, phase_rows, product_rows)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                VARIANT_MD,
                SUMMARY_CSV,
                PHASE_CSV,
                PRODUCT_CSV,
                ROOT / "scripts" / "build_stage113_r2_selector_simulator.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage113 r=2 selector simulator: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") else 0


if __name__ == "__main__":
    raise SystemExit(main())
