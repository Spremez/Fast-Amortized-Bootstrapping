#!/usr/bin/env python3
"""Generate the Stage 36 high-statistics expansion plan.

Stage 36 is optional for the current scoped engineering claim. This generator
pre-registers the endpoints, budgets, commands, and promotion gates needed
before broader statistical or paper-level wording can be justified.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro/stage36_high_stat_plan.csv"
OUT_MD = ROOT / "docs/stage36_high_stat_expansion_log.md"


def row(
    item_id: str,
    endpoint: str,
    scope: str,
    existing_evidence: str,
    current_limit: str,
    recommended_budget: str,
    command: str,
    promotion_gate: str,
    failure_handling: str,
    priority: str,
) -> Dict[str, str]:
    return {
        "item_id": item_id,
        "endpoint": endpoint,
        "scope": scope,
        "required_for_current_scoped_claim": "no",
        "existing_evidence": existing_evidence,
        "current_limit": current_limit,
        "recommended_budget": recommended_budget,
        "command": command,
        "promotion_gate": promotion_gate,
        "failure_handling": failure_handling,
        "priority": priority,
    }


def build_rows() -> List[Dict[str, str]]:
    return [
        row(
            "S36-TARGET-PERF",
            "target complete-SAB A/B performance",
            "SET_2_3_2048, r=2/4, spqlios_avx512, active-buffer MAT-SAB",
            "Stage 27 final rerun: 3 process runs for r=2 and r=4",
            "r=2 remains positive but noisy; r=4 is stronger but still only 3 runs",
            "10 process runs per r, same backend, same reps, sequential one-workspace execution",
            "STAGE36_MODE=target_perf STAGE36_EXECUTE=1 STAGE36_TARGET_RUNS=10 bash scripts/run_stage36_high_stat_expansion.sh",
            "all correctness gates pass; mean speedup > 1.0; report min/max/stddev/CI; no backend changes",
            "if mean speedup <= 1.0 or correctness fails, keep scoped claim at older evidence and record failure",
            "high",
        ),
        row(
            "S36-TARGET-NOISE",
            "target final-output correctness/noise rerun",
            "SET_2_3_2048, r=2/4, deterministic seeds",
            "Stage 25 target 50-seed final-output noise support exists",
            "already adequate for scoped target claim; rerun only after code or platform changes",
            "50 deterministic seeds per r, same max log2 gap, same backend",
            "STAGE36_MODE=target_noise STAGE36_EXECUTE=1 STAGE36_TARGET_NOISE_SEEDS=50 bash scripts/run_stage36_high_stat_expansion.sh",
            "zero PVW/scalar/pair failures; report gap min/max/average",
            "any failure blocks promotion until explained by parameter or implementation analysis",
            "medium",
        ),
        row(
            "S36-STAGE-NOISE",
            "stage-level noise expansion",
            "SET_2_3_2048, r=2/4, staged phase/noise checkpoints",
            "Stage 25 stage-level noise smoke: one deterministic seed",
            "supports debugging only; too weak for stage-by-stage paper claim",
            "10 seeds per r as an intermediate campaign; 50 seeds if used in paper tables",
            "STAGE36_MODE=stage_noise STAGE36_EXECUTE=1 STAGE36_STAGE_NOISE_SEEDS=10 bash scripts/run_stage36_high_stat_expansion.sh",
            "zero pair failures at every reported stage; report per-stage max and sigma",
            "failed stage isolates the next debugging target; do not upgrade stage-level noise claim",
            "medium",
        ),
        row(
            "S36-ADDED-PARAM",
            "added binary parameter performance/noise expansion",
            "SET_4_5_2048 and SET_2_3_4096, r=2/4",
            "Stage 26 added-binary matrix: 5 runs and 5 seeds per parameter/r",
            "small-sample only; SET_4_5_2048 r=2 has visible timing variance",
            "10 process runs and 20 noise seeds per parameter/r before broader wording",
            "STAGE36_MODE=added_params STAGE36_EXECUTE=1 STAGE36_ADDED_RUNS=10 STAGE36_ADDED_SEEDS=20 bash scripts/run_stage36_high_stat_expansion.sh",
            "all correctness/noise gates pass; mean speedup > 1.0; report CI and high-variance cases",
            "if gains are parameter-specific, downgrade to parameter-scoped claim",
            "medium",
        ),
        row(
            "S36-RESOURCE",
            "resource matrix replication",
            "SET_2_3_2048, r=1/2/4, keygen/key size/RSS",
            "Stage 25 resource snapshot exists",
            "smoke resource evidence only; enough for scoped report but not statistical resource tables",
            "3 repeated resource runs per r/mode after final implementation freeze",
            "STAGE36_MODE=resource STAGE36_EXECUTE=1 STAGE36_RESOURCE_RUNS=3 bash scripts/run_stage36_high_stat_expansion.sh",
            "all gates pass; report mean/max RSS, keygen time, key-size ratios with performance",
            "if resource cost is unstable or too high, keep resource claim descriptive and scoped",
            "low",
        ),
    ]


def write_csv(rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage 36 High-Statistics Expansion Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 36 pre-registers optional higher-statistics experiments for claims",
        "that go beyond the current scoped engineering PVW/MAT-SAB result. It",
        "does not change scalar SAB or `sab_pvw_*` code, and it does not upgrade",
        "any claim by itself.",
        "",
        "## Execution Policy",
        "",
        "- The current scoped engineering claim does not require Stage 36.",
        "- Stage 36 is required before broader statistical, all-parameter,",
        "  stage-level-noise, or statistical resource claims.",
        "- The primary endpoint must be declared before running each campaign.",
        "- Same-backend comparisons remain mandatory.",
        "- Failed or neutral results must be preserved.",
        "",
        "## Budget Matrix",
        "",
        "| item | priority | endpoint | scope | budget | promotion gate |",
        "|---|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            "| {item_id} | {priority} | {endpoint} | {scope} | "
            "{recommended_budget} | {promotion_gate} |".format(**item)
        )

    lines.extend(
        [
            "",
            "## Command Matrix",
            "",
            "| item | command | failure handling |",
            "|---|---|---|",
        ]
    )
    for item in rows:
        lines.append(
            "| {item_id} | `{command}` | {failure_handling} |".format(**item)
        )

    lines.extend(
        [
            "",
            "## Current Decision",
            "",
            "No Stage 36 heavy campaign has been promoted yet. The next reasonable",
            "local campaign, if broader statistical performance wording is desired,",
            "is `S36-TARGET-PERF` with 10 sequential process runs for r=2 and r=4.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = build_rows()
    write_csv(rows)
    write_md(rows)
    print(f"Stage 36 high-stat plan CSV: {OUT_CSV.relative_to(ROOT)}")
    print(f"Stage 36 high-stat log: {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
