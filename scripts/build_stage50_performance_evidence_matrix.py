#!/usr/bin/env python3
"""Build the Stage 50 performance-evidence matrix.

This script does not run benchmarks and does not upgrade claim strength. It
aligns the high-stat Stage 36 target-performance evidence with the post-refactor
current-head Stage 47/49 continuity evidence so performance wording can be
audited without conflating smoke, repeated stability, and high-stat results.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
STAGE36 = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE47 = ROOT / "repro" / "stage47_wsl_active_state_full_sab_smoke" / "summary.csv"
STAGE49 = ROOT / "repro" / "stage49_wsl_repeated_full_sab" / "summary.csv"
OUT_CSV = ROOT / "repro" / "stage50_performance_evidence_matrix.csv"
OUT_MD = ROOT / "docs" / "stage50_performance_evidence_matrix.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def as_float(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def as_int(row: Dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(row.get(key, default))
    except (TypeError, ValueError):
        return default


def stage36_by_r() -> Dict[str, Dict[str, str]]:
    return {row.get("r", ""): row for row in read_csv(STAGE36)}


def stage47_by_r() -> Dict[str, Dict[str, str]]:
    return {row.get("r", ""): row for row in read_csv(STAGE47)}


def stage49_by_r() -> Dict[str, Dict[str, str]]:
    return {row.get("r", ""): row for row in read_csv(STAGE49)}


def consistency_label(stage36_row: Dict[str, str], observed_mean: float) -> str:
    ci_low = as_float(stage36_row, "ci95_low")
    ci_high = as_float(stage36_row, "ci95_high")
    if ci_low <= observed_mean <= ci_high:
        return "CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95"
    stage36_mean = as_float(stage36_row, "mean_speedup")
    if stage36_mean > 0 and abs(observed_mean - stage36_mean) / stage36_mean <= 0.10:
        return "CURRENT_HEAD_MEAN_WITHIN_10_PERCENT_STAGE36_MEAN"
    return "CURRENT_HEAD_MEAN_OUTSIDE_STAGE36_BAND"


def build_rows() -> List[Dict[str, str]]:
    s36 = stage36_by_r()
    s47 = stage47_by_r()
    s49 = stage49_by_r()
    rows: List[Dict[str, str]] = []

    for r_value in ["2", "4"]:
        row36 = s36.get(r_value, {})
        row47 = s47.get(r_value, {})
        row49 = s49.get(r_value, {})

        stage36_status = row36.get("decision", "MISSING")
        stage36_samples = as_int(row36, "samples")
        stage36_mean = as_float(row36, "mean_speedup")
        stage36_min = as_float(row36, "min_speedup")
        stage36_ci_low = as_float(row36, "ci95_low")
        stage36_ci_high = as_float(row36, "ci95_high")
        stage36_ok = (
            stage36_status == "PASS_TARGET_PERF_10RUN"
            and stage36_samples == 10
            and stage36_min > 1.0
            and stage36_ci_low > 1.0
        )
        rows.append(
            {
                "r": r_value,
                "evidence_id": f"stage36_target_perf_r{r_value}",
                "evidence_class": "high_stat_target_performance",
                "runs": str(stage36_samples),
                "status": "PASS" if stage36_ok else "FAIL",
                "mean_speedup": f"{stage36_mean:.3f}",
                "min_speedup": f"{stage36_min:.3f}",
                "max_speedup": f"{as_float(row36, 'max_speedup'):.3f}",
                "ci95_low": f"{stage36_ci_low:.6f}",
                "ci95_high": f"{stage36_ci_high:.6f}",
                "consistency_with_stage36": "REFERENCE_HIGH_STAT",
                "stats_sanity_label": "EXPERIMENT_SUPPORTED_UNDER_TARGET_PROTOCOL",
                "claim_policy": "may_support_scoped_engineering_target_performance; not novelty/theory/all-parameter",
                "source": STAGE36.relative_to(ROOT).as_posix(),
            }
        )

        stage47_speedup = as_float(row47, "speedup_vs_scalar_repeated")
        stage47_ok = row47.get("status") == "PASS" and as_int(row47, "runs") == 1 and stage47_speedup > 1.0
        rows.append(
            {
                "r": r_value,
                "evidence_id": f"stage47_current_head_smoke_r{r_value}",
                "evidence_class": "single_run_current_head_smoke",
                "runs": row47.get("runs", "0"),
                "status": "PASS" if stage47_ok else "FAIL",
                "mean_speedup": f"{stage47_speedup:.3f}",
                "min_speedup": f"{stage47_speedup:.3f}",
                "max_speedup": f"{stage47_speedup:.3f}",
                "ci95_low": "",
                "ci95_high": "",
                "consistency_with_stage36": consistency_label(row36, stage47_speedup) if row36 else "MISSING_STAGE36",
                "stats_sanity_label": "STATISTICAL_EVIDENCE_INSUFFICIENT_FOR_CLAIM",
                "claim_policy": "current-head smoke only; superseded by Stage49 for continuity",
                "source": STAGE47.relative_to(ROOT).as_posix(),
            }
        )

        stage49_mean = as_float(row49, "speedup_mean")
        stage49_min = as_float(row49, "speedup_min")
        stage49_ok = row49.get("status") == "PASS" and as_int(row49, "runs") == 3 and stage49_min > 1.0
        rows.append(
            {
                "r": r_value,
                "evidence_id": f"stage49_current_head_repeated_r{r_value}",
                "evidence_class": "repeated_current_head_stability",
                "runs": row49.get("runs", "0"),
                "status": "PASS" if stage49_ok else "FAIL",
                "mean_speedup": f"{stage49_mean:.3f}",
                "min_speedup": f"{stage49_min:.3f}",
                "max_speedup": f"{as_float(row49, 'speedup_max'):.3f}",
                "ci95_low": "",
                "ci95_high": "",
                "consistency_with_stage36": consistency_label(row36, stage49_mean) if row36 else "MISSING_STAGE36",
                "stats_sanity_label": "CURRENT_HEAD_STABILITY_SUPPORTED_NOT_HIGH_STAT_CLAIM",
                "claim_policy": "may support post-refactor continuity; Stage36 remains performance claim source",
                "source": STAGE49.relative_to(ROOT).as_posix(),
            }
        )

    return rows


def write_csv(rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: List[Dict[str, str]]) -> List[str]:
    cols = [
        "r",
        "evidence_class",
        "runs",
        "status",
        "mean_speedup",
        "min_speedup",
        "ci95_low",
        "ci95_high",
        "consistency_with_stage36",
        "stats_sanity_label",
    ]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(col, "") for col in cols) + " |")
    return lines


def write_md(rows: List[Dict[str, str]]) -> None:
    failures = [row["evidence_id"] for row in rows if row["status"] != "PASS"]
    decision = (
        "PASS_PERFORMANCE_EVIDENCE_MATRIX_STRONGER_CLAIMS_BLOCKED"
        if not failures
        else "FAIL_PERFORMANCE_EVIDENCE_MATRIX"
    )
    lines = [
        "# Stage 50 Performance Evidence Matrix",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 50 aligns the high-stat Stage 36 target-performance evidence with",
        "the post-refactor Stage 47 and Stage 49 current-head continuity evidence.",
        "It is a claim-boundary and reproducibility artifact; it does not run",
        "benchmarks and does not upgrade novelty, theory, hardware-counter,",
        "non-binary, or all-parameter claims.",
        "",
        "## Matrix",
        "",
        *md_table(rows),
        "",
        "## Interpretation",
        "",
        "- Stage 36 remains the performance claim source: 10 same-backend complete-SAB",
        "  runs per r value, with CI95 lower bounds above 1.0.",
        "- Stage 49 is current-head repeated stability evidence after the active-state",
        "  refactor. It checks that the current implementation still agrees with the",
        "  Stage 36 performance band, but it is not a replacement for Stage 36.",
        "- Stage 47 is retained as historical one-run smoke and is superseded by",
        "  Stage 49 for current-head continuity wording.",
        "- The allowed claim remains scoped engineering target performance. Stronger",
        "  MAT-AVX512 theoretical, novelty, theorem-level 2025/686, non-binary, and",
        "  all-parameter claims remain blocked by the existing external gates.",
        "",
        "## Decision",
        "",
        f"`{decision}`" if not failures else f"`{decision}`: {failures}",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    rows = build_rows()
    write_csv(rows)
    write_md(rows)
    failures = [row["evidence_id"] for row in rows if row["status"] != "PASS"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(
        "Stage 50 performance matrix: "
        + (
            "PASS_PERFORMANCE_EVIDENCE_MATRIX_STRONGER_CLAIMS_BLOCKED"
            if not failures
            else "FAIL_PERFORMANCE_EVIDENCE_MATRIX"
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
