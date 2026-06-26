#!/usr/bin/env python3
"""Audit current scope labels against the latest Stage19+ roadmap range."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
STAGE51 = ROOT / "repro" / "stage51_goal_completion_frontier.csv"
OUT_CSV = ROOT / "repro" / "stage57_scope_label_audit.csv"
OUT_MD = ROOT / "docs" / "stage57_scope_label_audit.md"

CURRENT_SCOPE_FILES = [
    ROOT / "docs" / "goal_sab_max_acceleration.md",
    ROOT / "docs" / "final_goal_recheck_log.md",
    ROOT / "docs" / "stage51_goal_completion_frontier.md",
    ROOT / "scripts" / "build_stage51_goal_completion_frontier.py",
    ROOT / "repro" / "stage51_goal_completion_frontier.csv",
]

LATEST_LABEL_REQUIRED_FILES = [
    ROOT / "docs" / "goal_sab_max_acceleration.md",
    ROOT / "docs" / "final_goal_recheck_log.md",
    ROOT / "docs" / "stage51_goal_completion_frontier.md",
    ROOT / "repro" / "stage51_goal_completion_frontier.csv",
]

STALE_LABELS = [
    "Stage 19-44",
    "Stage19-44",
    "Stage 19-50",
    "Stage19-50",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def roadmap_stages() -> List[int]:
    text = ROADMAP.read_text(encoding="utf-8") if ROADMAP.exists() else ""
    return sorted({int(m.group(1)) for m in re.finditer(r"^## Stage (\d+):", text, re.M)})


def stage51_row(frontier_id: str) -> Dict[str, str]:
    for row in read_csv(STAGE51):
        if row.get("frontier_id") == frontier_id:
            return row
    return {}


def row(audit_id: str, status: str, evidence: str, detail: str, action: str) -> Dict[str, str]:
    return {
        "audit_id": audit_id,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "action": action,
    }


def build_rows() -> List[Dict[str, str]]:
    stages = roadmap_stages()
    latest = stages[-1] if stages else 0
    expected_label_spaced = f"Stage 19-{latest}" if latest else "MISSING"
    expected_label_compact = f"Stage19-{latest}" if latest else "MISSING"
    stage51_g6 = stage51_row("G6")

    stale_hits: List[str] = []
    expected_missing: List[str] = []
    for path in CURRENT_SCOPE_FILES:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        for label in STALE_LABELS:
            if label in text:
                stale_hits.append(f"{rel(path)}:{label}")
    for path in LATEST_LABEL_REQUIRED_FILES:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if path.exists() and (
            expected_label_spaced not in text and expected_label_compact not in text
        ):
            expected_missing.append(rel(path))

    return [
        row(
            "S57-ROADMAP-LATEST-STAGE",
            "PASS" if latest >= 56 else "FAIL",
            rel(ROADMAP),
            f"latest_stage={latest}; expected_label={expected_label_spaced}",
            "Add the current stage to docs/roadmap_stage19_plus.md before relying on scope labels.",
        ),
        row(
            "S57-STAGE51-G6-LABEL",
            "PASS"
            if expected_label_compact in stage51_g6.get("interpretation", "")
            or expected_label_spaced in stage51_g6.get("interpretation", "")
            else "FAIL",
            rel(STAGE51),
            stage51_g6.get("interpretation", "missing G6"),
            "Regenerate Stage51 frontier with the dynamic latest-stage label.",
        ),
        row(
            "S57-NO-STALE-CURRENT-LABELS",
            "PASS" if not stale_hits else "FAIL",
            "; ".join(rel(p) for p in CURRENT_SCOPE_FILES),
            "; ".join(stale_hits) if stale_hits else "No stale Stage19-44/50 labels in current scope files.",
            "Update current-scope control files so they refer to the latest closure range.",
        ),
        row(
            "S57-CURRENT-FILES-MENTION-LATEST",
            "PASS" if not expected_missing else "FAIL",
            "; ".join(rel(p) for p in LATEST_LABEL_REQUIRED_FILES),
            "; ".join(expected_missing) if expected_missing else f"All current scope files mention {expected_label_spaced} or {expected_label_compact}.",
            "Add the latest scope label to current-scope control files.",
        ),
    ]


def decision(rows: List[Dict[str, str]]) -> str:
    return (
        "PASS_SCOPE_LABELS_MATCH_LATEST_STAGE"
        if all(row["status"] == "PASS" for row in rows)
        else "FAIL_SCOPE_LABELS_STALE"
    )


def write_md(rows: List[Dict[str, str]]) -> None:
    status = decision(rows)
    lines = [
        "# Stage 57 Scope Label Audit",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 57 checks that current control-plane scope labels match the latest",
        "Stage19+ roadmap range. It is not a new SAB benchmark or optimization;",
        "it prevents reports from citing stale closure ranges after later stages",
        "extend the evidence chain.",
        "",
        "## Checks",
        "",
        "| audit | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| {item['audit_id']} | {item['status']} | {item['evidence']} | {item['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{status}`",
            "",
            "Scope-label consistency is a claim-control requirement only. It does",
            "not upgrade performance, novelty, theorem-level, or hardware-counter",
            "claims.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows, ["audit_id", "status", "evidence", "detail", "action"])
    write_md(rows)
    status = decision(rows)
    print(f"Stage 57 scope label audit: {rel(OUT_CSV)}")
    print(f"Stage 57 scope label log: {rel(OUT_MD)}")
    print(f"Decision: {status}")
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
