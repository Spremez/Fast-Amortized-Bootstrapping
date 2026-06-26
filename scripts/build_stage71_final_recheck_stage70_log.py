#!/usr/bin/env python3
"""Build the Stage71 final-recheck Stage70 integration log."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / os.environ.get("STAGE71_OUT_DIR", "repro/stage71_final_recheck_stage70")
SUMMARY = OUT_DIR / "summary.csv"
STAGE70 = ROOT / "repro" / "stage70_external_unlock_preflight.csv"
OUT_CSV = OUT_DIR / "decision.csv"
OUT_MD = ROOT / "docs" / "stage71_final_recheck_stage70_log.md"


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


def final_recheck_row() -> Dict[str, str]:
    rows = {row.get("step"): row for row in read_csv(SUMMARY)}
    expected_pass = [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage59_completion_route",
        "stage70_external_unlock_preflight",
        "stage42_evidence_closure",
    ]
    expected_skipped = [
        "stage27_citation_probe",
        "stage27_related_work_access_probe",
        "stage28_perf_gate",
        "stage27_final_package",
        "external_evidence_intake",
        "stage33_current_smoke",
        "conditional_backlog_audit",
        "stage44_external_reprobe",
        "stage55_external_paper_probe",
        "stage50_performance_matrix",
        "stage66_post_variant_final_recheck",
    ]
    problems: List[str] = []
    for step in expected_pass:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{step}:status={status}")
    for step in expected_skipped:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "SKIPPED":
            problems.append(f"{step}:status={status}")
    final_decision = rows.get("final_decision", {}).get("status", "MISSING")
    if final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        problems.append(f"final_decision:status={final_decision}")

    return {
        "gate": "stage71_final_recheck_stage70",
        "status": "PASS" if not problems and rows else "FAIL",
        "evidence": SUMMARY.relative_to(ROOT).as_posix(),
        "detail": (
            "final recheck refreshed Stage51, Stage52, Stage57, Stage59, "
            "Stage70, and Stage42 closure while preserving stronger blockers"
        )
        if not problems and rows
        else "; ".join(problems) or "Stage71 final recheck summary missing",
    }


def stage70_row() -> Dict[str, str]:
    rows = {row.get("gate"): row for row in read_csv(STAGE70)}
    expected = {
        "stage70_route_inputs": "PASS",
        "stage70_native_perf_preflight": "WAIT_NATIVE_PERF",
        "stage70_fulltext_stage62_preflight": "WAIT_FULLTEXT_ARTIFACT",
        "stage70_novelty_preflight": "WAIT_FULLTEXT_OR_MANUAL_REVIEW",
        "stage70_local_variant_preflight": "NO_LOCAL_VARIANT_READY",
        "stage70_decision": "PASS_EXTERNAL_UNLOCK_PREFLIGHT_STRONGER_CLAIMS_BLOCKED",
    }
    problems: List[str] = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    fulltext_env = rows.get("stage70_fulltext_env_preflight", {}).get(
        "status", "MISSING"
    )
    if fulltext_env not in {
        "MISSING_ENV",
        "PATH_NOT_FOUND",
        "INVALID_FILE",
        "AVAILABLE_UNREVIEWED",
    }:
        problems.append(f"stage70_fulltext_env_preflight:status={fulltext_env}")
    return {
        "gate": "stage71_stage70_summary",
        "status": "PASS" if not problems and rows else "FAIL",
        "evidence": STAGE70.relative_to(ROOT).as_posix(),
        "detail": "Stage70 preflight remains passed after final-recheck integration"
        if not problems and rows
        else "; ".join(problems) or "Stage70 summary missing",
    }


def build_rows() -> List[Dict[str, str]]:
    rows = [final_recheck_row(), stage70_row()]
    failures = [row["gate"] for row in rows if row["status"] != "PASS"]
    rows.append(
        {
            "gate": "stage71_decision",
            "status": "PASS_FINAL_RECHECK_STAGE70_INTEGRATION"
            if not failures
            else "FAIL_FINAL_RECHECK_STAGE70_INTEGRATION",
            "evidence": OUT_CSV.relative_to(ROOT).as_posix(),
            "detail": "Stage71 integrates Stage70 into the explicit final-recheck path without upgrading stronger claims"
            if not failures
            else f"failed_gates={failures}",
        }
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage71 Final-Recheck Stage70 Integration Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage71 verifies that `scripts/run_final_goal_recheck.sh` can refresh",
        "Stage70 external-unlock preflight before rebuilding Stage42 closure.",
        "This is reproducibility/control-plane evidence only.",
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
            "A passing Stage71 means Stage70 can be kept current through the",
            "unified final recheck. It does not run a SAB benchmark and does not",
            "upgrade speedup, novelty, theorem-level, non-binary, all-parameter,",
            "or hardware-counter claims.",
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
    print(f"Stage71 final-recheck Stage70 integration: {decision}")
    return 0 if decision.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
