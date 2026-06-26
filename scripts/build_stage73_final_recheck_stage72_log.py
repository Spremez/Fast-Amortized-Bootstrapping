#!/usr/bin/env python3
"""Build the Stage73 final-recheck Stage72 integration log."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / os.environ.get("STAGE73_OUT_DIR", "repro/stage73_final_recheck_stage72")
SUMMARY = OUT_DIR / "summary.csv"
STAGE72 = ROOT / "repro" / "stage72_external_source_refresh" / "summary.csv"
OUT_CSV = OUT_DIR / "decision.csv"
OUT_MD = ROOT / "docs" / "stage73_final_recheck_stage72_log.md"


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
        "stage72_external_source_refresh",
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
        "gate": "stage73_final_recheck_stage72",
        "status": "PASS" if not problems and rows else "FAIL",
        "evidence": SUMMARY.relative_to(ROOT).as_posix(),
        "detail": (
            "final recheck refreshed Stage72, blocker dashboard, Stage51, "
            "Stage52, Stage57, Stage59, Stage70, and Stage42 closure"
        )
        if not problems and rows
        else "; ".join(problems) or "Stage73 final recheck summary missing",
    }


def stage72_row() -> Dict[str, str]:
    rows = {row.get("gate"): row for row in read_csv(STAGE72)}
    expected = {
        "stage72_author_metadata_route": "PASS",
        "stage72_doi_metadata_route": "PASS",
        "stage72_code_route": "PASS",
        "stage72_official_fulltext_routes": "WAIT_FULLTEXT_ARTIFACT",
        "stage72_claim_policy": "KEEP_STRONGER_CLAIMS_BLOCKED",
        "stage72_decision": "PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED",
    }
    problems: List[str] = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    return {
        "gate": "stage73_stage72_summary",
        "status": "PASS" if not problems and rows else "FAIL",
        "evidence": STAGE72.relative_to(ROOT).as_posix(),
        "detail": "Stage72 external-source refresh remains passed after final-recheck integration"
        if not problems and rows
        else "; ".join(problems) or "Stage72 summary missing",
    }


def build_rows() -> List[Dict[str, str]]:
    rows = [final_recheck_row(), stage72_row()]
    failures = [row["gate"] for row in rows if row["status"] != "PASS"]
    rows.append(
        {
            "gate": "stage73_decision",
            "status": "PASS_FINAL_RECHECK_STAGE72_INTEGRATION"
            if not failures
            else "FAIL_FINAL_RECHECK_STAGE72_INTEGRATION",
            "evidence": OUT_CSV.relative_to(ROOT).as_posix(),
            "detail": "Stage73 integrates Stage72 into the explicit final-recheck path without upgrading stronger claims"
            if not failures
            else f"failed_gates={failures}",
        }
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage73 Final-Recheck Stage72 Integration Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage73 verifies that `scripts/run_final_goal_recheck.sh` can refresh",
        "Stage72 external source availability before rebuilding Stage42 closure.",
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
            "A passing Stage73 means Stage72 can be kept current through the",
            "unified final recheck before Stage42 closure. It does not run a SAB",
            "benchmark and does not upgrade speedup, novelty, theorem-level,",
            "non-binary, all-parameter, or hardware-counter claims.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage73 final-recheck Stage72 integration: {decision}")
    return 0 if decision.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
