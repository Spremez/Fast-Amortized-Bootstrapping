#!/usr/bin/env python3
"""Build the Stage66A post-variant final-recheck log."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / os.environ.get(
    "STAGE66_OUT_DIR", "repro/stage66_post_variant_final_recheck"
)
FINAL_RECHECK = OUT_DIR / "final_recheck" / "summary.csv"
STAGE64A = ROOT / "repro" / "stage64_post_variant_refresh" / "summary.csv"
STAGE65A = ROOT / "repro" / "stage65_r4_unrolled_avx512" / "summary.csv"
OUT_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage66_post_variant_final_recheck_log.md"


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
    rows = {row.get("step"): row for row in read_csv(FINAL_RECHECK)}
    expected_pass = [
        "stage27_final_package",
        "external_evidence_intake",
        "conditional_backlog_audit",
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage50_performance_matrix",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage59_completion_route",
    ]
    expected_skipped = [
        "stage27_citation_probe",
        "stage27_related_work_access_probe",
        "stage28_perf_gate",
        "stage33_current_smoke",
        "stage44_external_reprobe",
        "stage55_external_paper_probe",
        "stage42_evidence_closure",
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
        "gate": "stage66_final_recheck_core",
        "status": "PASS" if not problems and rows else "FAIL",
        "evidence": FINAL_RECHECK.relative_to(ROOT).as_posix(),
        "detail": (
            "lightweight final recheck refreshed Stage27 package, external intake, "
            "conditional backlog, final audit, blocker dashboard, Stage50/51/52/57/59; "
            "external probes and Stage42 closure were intentionally skipped"
        )
        if not problems and rows
        else "; ".join(problems) or "final recheck summary missing",
    }


def stage64a_row() -> Dict[str, str]:
    rows = {row.get("gate"): row for row in read_csv(STAGE64A)}
    status = rows.get("stage64_decision", {}).get("status", "MISSING")
    return {
        "gate": "stage66_stage64a_continuity",
        "status": "PASS" if status == "PASS_POST_VARIANT_REFRESH" else "FAIL",
        "evidence": STAGE64A.relative_to(ROOT).as_posix(),
        "detail": "Stage64A post-variant refresh remains passed"
        if status == "PASS_POST_VARIANT_REFRESH"
        else f"stage64_decision={status}",
    }


def stage65a_row() -> Dict[str, str]:
    rows = {row.get("gate"): row for row in read_csv(STAGE65A)}
    status = rows.get("stage65_decision", {}).get("status", "MISSING")
    return {
        "gate": "stage66_stage65a_negative_variant",
        "status": "PASS" if status == "NEGATIVE_NOT_PROMOTED" else "FAIL",
        "evidence": STAGE65A.relative_to(ROOT).as_posix(),
        "detail": "Stage65A remains recorded as negative/not promoted"
        if status == "NEGATIVE_NOT_PROMOTED"
        else f"stage65_decision={status}",
    }


def build_rows() -> List[Dict[str, str]]:
    rows = [final_recheck_row(), stage64a_row(), stage65a_row()]
    failures = [row["gate"] for row in rows if row["status"] != "PASS"]
    rows.append(
        {
            "gate": "stage66_decision",
            "status": "PASS_POST_VARIANT_FINAL_RECHECK"
            if not failures
            else "FAIL_POST_VARIANT_FINAL_RECHECK",
            "evidence": OUT_CSV.relative_to(ROOT).as_posix(),
            "detail": (
                "Stage66A confirms the post-variant final-recheck control plane "
                "is current while preserving stronger-claim blockers"
            )
            if not failures
            else f"failed_gates={failures}",
        }
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage66A Post-Variant Final-Recheck Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage66A checks that the lightweight final-recheck control plane remains",
        "usable after the Stage65A optional variant and Stage64A continuity",
        "refresh. It does not run new SAB benchmarks and does not upgrade",
        "novelty, theorem-level, or hardware-counter claims.",
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
            "A passing Stage66A means the post-variant evidence state can be",
            "refreshed through the same lightweight final-recheck path used by the",
            "rest of the scoped engineering package. Stage42 closure is rebuilt",
            "after this summary exists so the closure audit can include Stage66A.",
        ]
    )
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = next(row for row in rows if row["gate"] == "stage66_decision")
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage66A post-variant final recheck: {decision['status']}")
    return 0 if decision["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
