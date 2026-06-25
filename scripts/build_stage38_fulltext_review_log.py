#!/usr/bin/env python3
"""Generate the Stage 38 full-text review log."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage38_fulltext_review_gate"
SUMMARY = OUT_DIR / "summary.csv"
CHECKLIST = OUT_DIR / "review_checklist.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
OUT_MD = ROOT / "docs" / "stage38_fulltext_review_log.md"


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
    checklist = read_csv(CHECKLIST)
    external = read_csv(EXTERNAL)
    audit = read_csv(FINAL_AUDIT)

    decision = row_by(summary, "item", "stage38_decision")
    artifact = row_by(summary, "item", "fulltext_artifact")
    external_fulltext = row_by(external, "evidence_id", "fab686_fulltext")
    audit_a8b = row_by(audit, "item_id", "A8b")
    audit_a9 = row_by(audit, "item_id", "A9")

    lines = [
        "# Stage 38 Full 2025/686 Source Review Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 38 records whether the full 2025/686 paper is available for "
        "theorem-level protocol citations and novelty review. It does not "
        "change scalar SAB or PVW/MAT-SAB code.",
        "",
        "## Artifact Gate",
        "",
        "| item | status | kind | path | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row.get('item','')} | {row.get('status','')} | "
            f"{row.get('kind','')} | {row.get('path','')} | {row.get('detail','')} |"
        )

    lines.extend(
        [
            "",
            "## Manual Review Checklist",
            "",
            "| review item | status | required evidence |",
            "|---|---|---|",
        ]
    )
    for row in checklist:
        lines.append(
            f"| {row.get('review_item','')} | {row.get('status','')} | "
            f"{row.get('required_evidence','')} |"
        )

    lines.extend(
        [
            "",
            "## External Intake / Final Audit",
            "",
            "| item | status | detail |",
            "|---|---|---|",
            f"| external fab686_fulltext | {external_fulltext.get('status','MISSING')} | {external_fulltext.get('detail','')} |",
            f"| final audit A8b | {audit_a8b.get('status','MISSING')} | {audit_a8b.get('scope','')} |",
            f"| final audit A9 | {audit_a9.get('status','MISSING')} | {audit_a9.get('scope','')} |",
            "",
            "## Decision",
            "",
        ]
    )

    status = decision.get("status", "MISSING")
    if status == "FULLTEXT_AVAILABLE_REVIEW_REQUIRED":
        text = (
            "A full-text artifact is available and hashed. The next step is "
            "manual claim-to-source mapping before theorem-level or novelty "
            "wording is upgraded."
        )
    elif status == "BLOCKED_FULLTEXT_MISSING":
        text = (
            "No full-text artifact is available. Theorem-level 2025/686 "
            "citations and novelty review remain blocked; metadata-only "
            "evidence is insufficient."
        )
    else:
        text = (
            "Stage 38 did not reach a review-ready state. Inspect the artifact "
            "gate before changing claim scope."
        )
    lines.append(text)

    if artifact.get("sha256"):
        lines.extend(["", f"Registered artifact SHA-256: `{artifact.get('sha256')}`"])

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {rel(OUT_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
