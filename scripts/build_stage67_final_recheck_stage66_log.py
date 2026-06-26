#!/usr/bin/env python3
"""Build the Stage67 final-recheck Stage66A integration log."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / os.environ.get("STAGE67_OUT_DIR", "repro/stage67_final_recheck_stage66")
SUMMARY = OUT_DIR / "summary.csv"
STAGE66_SUMMARY = ROOT / "repro" / "stage66_post_variant_final_recheck" / "summary.csv"
OUT_CSV = OUT_DIR / "decision.csv"
OUT_MD = ROOT / "docs" / "stage67_final_recheck_stage66_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "status", "evidence", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def summary_rows() -> Dict[str, Dict[str, str]]:
    return {row.get("step"): row for row in read_csv(SUMMARY)}


def stage66_rows() -> Dict[str, Dict[str, str]]:
    return {row.get("gate"): row for row in read_csv(STAGE66_SUMMARY)}


def final_recheck_row(rows: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    expected = {
        "stage66_post_variant_final_recheck": "PASS",
        "stage42_evidence_closure": "SKIPPED",
        "final_decision": "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
    }
    problems: List[str] = []
    for step, status in expected.items():
        actual = rows.get(step, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{step}:status={actual}")
    return {
        "gate": "stage67_final_recheck_stage66",
        "status": "PASS" if not problems and rows else "FAIL",
        "evidence": SUMMARY.relative_to(ROOT).as_posix(),
        "detail": "final recheck ran Stage66A and intentionally left Stage42 closure for the post-summary rebuild"
        if not problems and rows
        else "; ".join(problems) or "Stage67 final recheck summary missing",
    }


def stage66_row(rows: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    expected = {
        "stage66_final_recheck_core": "PASS",
        "stage66_stage64a_continuity": "PASS",
        "stage66_stage65a_negative_variant": "PASS",
        "stage66_decision": "PASS_POST_VARIANT_FINAL_RECHECK",
    }
    problems: List[str] = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    return {
        "gate": "stage67_stage66_summary",
        "status": "PASS" if not problems and rows else "FAIL",
        "evidence": STAGE66_SUMMARY.relative_to(ROOT).as_posix(),
        "detail": "canonical Stage66A summary remains passed after final-recheck integration"
        if not problems and rows
        else "; ".join(problems) or "Stage66A summary missing",
    }


def build_rows() -> List[Dict[str, str]]:
    rows = [final_recheck_row(summary_rows()), stage66_row(stage66_rows())]
    failures = [row["gate"] for row in rows if row["status"] != "PASS"]
    rows.append(
        {
            "gate": "stage67_decision",
            "status": "PASS_FINAL_RECHECK_STAGE66_INTEGRATION"
            if not failures
            else "FAIL_FINAL_RECHECK_STAGE66_INTEGRATION",
            "evidence": OUT_CSV.relative_to(ROOT).as_posix(),
            "detail": "Stage67 integrates Stage66A into the explicit final-recheck path without upgrading stronger claims"
            if not failures
            else f"failed_gates={failures}",
        }
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage67 Final-Recheck Stage66A Integration Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage67 verifies that `scripts/run_final_goal_recheck.sh` can run",
        "Stage66A before rebuilding Stage42 closure. This closes the manual",
        "handoff left by Stage66A and keeps the final recheck path auditable.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['evidence']} | {row['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A passing Stage67 is reproducibility evidence only. It does not run a",
            "new SAB benchmark and does not upgrade native-perf, full-text,",
            "novelty, or theorem-level claims.",
        ]
    )
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage67 final-recheck Stage66A integration: {decision}")
    return 0 if decision.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
