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
TARGET_PERF_SUMMARY = ROOT / "repro/stage36_target_perf_summary.csv"
TARGET_PERF_EXCLUSIONS = ROOT / "repro/stage36_target_perf_exclusions.csv"
TARGET_PERF_SUPPLEMENTAL = ROOT / "repro/stage36_target_perf_supplemental.csv"
STAGE_NOISE_AGGREGATE = ROOT / "repro/stage36_stage_noise_seeds10/aggregate.csv"
RESOURCE_SUMMARY = ROOT / "repro/stage36_resource_summary.csv"


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


def read_csv_if_exists(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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

    target_perf = read_csv_if_exists(TARGET_PERF_SUMMARY)
    if target_perf:
        lines.extend(
            [
                "",
                "## Target Performance Result",
                "",
                "| r | samples | mean speedup | min | max | ci95 low | ci95 high | decision | notes |",
                "|---|---:|---:|---:|---:|---:|---:|---|---|",
            ]
        )
        for item in target_perf:
            lines.append(
                "| {r} | {samples} | {mean_speedup} | {min_speedup} | {max_speedup} | "
                "{ci95_low} | {ci95_high} | {decision} | {notes} |".format(**item)
            )

        exclusions = read_csv_if_exists(TARGET_PERF_EXCLUSIONS)
        if exclusions:
            lines.extend(
                [
                    "",
                    "Exclusion/review records:",
                    "",
                    "| source | r | decision | reason |",
                    "|---|---:|---|---|",
                ]
            )
            for item in exclusions:
                lines.append(
                    "| {source_label} | {r} | {decision} | {reason} |".format(**item)
                )

        supplemental = read_csv_if_exists(TARGET_PERF_SUPPLEMENTAL)
        if supplemental:
            lines.extend(
                [
                    "",
                    "Supplemental samples not included in the primary 10-run statistic:",
                    "",
                    "| sample | r | speedup | decision |",
                    "|---|---:|---:|---|",
                ]
            )
            for item in supplemental:
                lines.append(
                    "| {sample_id} | {r} | {speedup_vs_scalar_repeated} | {decision} |".format(**item)
                )

    stage_noise = read_csv_if_exists(STAGE_NOISE_AGGREGATE)
    if stage_noise:
        lines.extend(
            [
                "",
                "## Stage-Noise Result",
                "",
                "| r | stage | seeds | pair failures | avg sigma | worst max abs | status |",
                "|---|---|---:|---:|---:|---:|---|",
            ]
        )
        for item in stage_noise:
            lines.append(
                "| {r} | {stage} | {seeds} | {pair_failures} | "
                "{avg_pair_log2_sigma} | {worst_pair_log2_max_abs} | {status} |".format(**item)
            )

    resource = read_csv_if_exists(RESOURCE_SUMMARY)
    if resource:
        lines.extend(
            [
                "",
                "## Resource Result",
                "",
                "| r | mode | runs | keygen lane mean us | key bytes ratio mean | max RSS KB | decision |",
                "|---|---|---:|---:|---:|---:|---|",
            ]
        )
        for item in resource:
            lines.append(
                "| {r} | {mode} | {runs} | {keygen_lane_mean_us} | "
                "{key_bytes_ratio_mean} | {time_max_rss_max_kb} | {decision} |".format(**item)
            )

    if target_perf and stage_noise and resource:
        decision_text = (
            "The target performance campaign has 10 primary same-backend "
            "samples for r=2 and r=4, the stage-noise campaign has 10 "
            "deterministic seeds for r=2 and r=4 with zero pair failures at "
            "all reported stages, and the resource campaign has 3 repeated "
            "snapshots for scalar/PVW r=1/2/4. This strengthens target "
            "performance, stage-level noise, and resource statistics, but it "
            "does not upgrade novelty, theorem-level citation, non-binary, "
            "all-parameter, or hardware-counter claims."
        )
    elif target_perf and stage_noise:
        decision_text = (
            "The target performance campaign has 10 primary same-backend "
            "samples for r=2 and r=4, and the stage-noise campaign has 10 "
            "deterministic seeds for r=2 and r=4 with zero pair failures at "
            "all reported stages. This strengthens target performance and "
            "stage-level noise statistics, but it does not upgrade novelty, "
            "theorem-level citation, non-binary, all-parameter, or "
            "hardware-counter claims."
        )
    elif target_perf:
        decision_text = (
            "The target performance campaign now has 10 primary same-backend "
            "samples for r=2 and r=4. This strengthens target performance "
            "statistics, but it does not upgrade novelty, theorem-level "
            "citation, non-binary, all-parameter, or hardware-counter claims."
        )
    elif stage_noise:
        decision_text = (
            "The stage-noise campaign has 10 deterministic seeds for r=2 and "
            "r=4 with zero pair failures at all reported stages. This "
            "strengthens stage-level noise statistics, but it does not upgrade "
            "performance, novelty, theorem-level citation, non-binary, "
            "all-parameter, or hardware-counter claims."
        )
    else:
        decision_text = (
            "No Stage 36 heavy campaign has been promoted yet. The next "
            "reasonable local campaign, if broader statistical performance "
            "wording is desired, is `S36-TARGET-PERF` with 10 sequential "
            "process runs for r=2 and r=4."
        )

    lines.extend(
        [
            "",
            "## Current Decision",
            "",
            decision_text,
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
