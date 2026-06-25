#!/usr/bin/env python3
"""Generate the Stage 37 native perf-counter audit log."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage37_native_perf_counter_audit"
SUMMARY = OUT_DIR / "summary.csv"
STAGE28_SUMMARY = OUT_DIR / "stage28_gate" / "summary.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
OUT_MD = ROOT / "docs" / "stage37_native_perf_counter_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def row_by(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    summary = read_csv(SUMMARY)
    stage28 = read_csv(STAGE28_SUMMARY)
    external = read_csv(EXTERNAL)
    audit = read_csv(FINAL_AUDIT)

    stage37_decision = row_by(summary, "item", "stage37_decision")
    hardware_gate = row_by(stage28, "probe", "hardware_counter_gate")
    external_perf = row_by(external, "evidence_id", "stage28_native_perf_summary")
    audit_a8 = row_by(audit, "item_id", "A8")
    audit_a8b = row_by(audit, "item_id", "A8b")
    audit_a9 = row_by(audit, "item_id", "A9")

    lines = [
        "# Stage 37 Native Perf-Counter Evidence Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 37 checks whether the MAT-AVX512 theoretical load/store/FMA "
        "claim can be upgraded with native hardware-counter evidence. It "
        "does not change the scalar SAB baseline or the PVW/MAT-SAB path.",
        "",
        "## Stage 37 Summary",
        "",
        "| item | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row.get('item','')} | {row.get('status','')} | "
            f"{row.get('evidence','')} | {row.get('detail','')} |"
        )

    lines.extend(
        [
            "",
            "## Stage 28 Gate",
            "",
            "| probe | status | evidence | detail |",
            "|---|---|---|---|",
        ]
    )
    for row in stage28:
        lines.append(
            f"| {row.get('probe','')} | {row.get('status','')} | "
            f"{row.get('evidence','')} | {row.get('detail','')} |"
        )

    lines.extend(
        [
            "",
            "## External Intake / Final Audit",
            "",
            "| item | status | detail |",
            "|---|---|---|",
            f"| external stage28_native_perf_summary | {external_perf.get('status','MISSING')} | {external_perf.get('detail','')} |",
            f"| final audit A8 | {audit_a8.get('status','MISSING')} | {audit_a8.get('scope','')} |",
            f"| final audit A8b | {audit_a8b.get('status','MISSING')} | {audit_a8b.get('scope','')} |",
            f"| final audit A9 | {audit_a9.get('status','MISSING')} | {audit_a9.get('scope','')} |",
            "",
            "## Decision",
            "",
        ]
    )

    decision = stage37_decision.get("status", "MISSING")
    if decision == "PASS_NATIVE_COUNTER_EVIDENCE":
        text = (
            "Native hardware-counter evidence is available and registered. "
            "The next step is manual interpretation against Stage 22 timing "
            "and objdump evidence before upgrading theoretical wording."
        )
    elif decision == "BLOCKED_EXTERNAL_PERF":
        text = (
            "The current platform still blocks hardware-counter evidence. "
            "MAT-AVX512 theoretical load/store optimality remains an external "
            "blocker; scoped engineering SAB acceleration evidence is unchanged."
        )
    else:
        text = (
            "Stage 37 did not produce a usable final decision. Inspect the "
            "summary and Stage 28 logs before changing claim scope."
        )
    lines.append(text)

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {rel(OUT_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
