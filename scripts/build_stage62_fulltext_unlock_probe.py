#!/usr/bin/env python3
"""Build the Stage 62 full-text unlock probe summary.

This stage does not perform theorem-level review. It records whether a
recognized 2025/686 full-text artifact is available, and if not, preserves the
claim blocker with direct-route evidence.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage62_fulltext_unlock_probe"
STAGE38_SUMMARY = OUT_DIR / "summary.csv"
STAGE38_CHECKLIST = OUT_DIR / "review_checklist.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
OUT_CSV = OUT_DIR / "unlock_summary.csv"
OUT_MD = ROOT / "docs" / "stage62_fulltext_unlock_probe_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
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


def head_status(source_id: str) -> Dict[str, str]:
    log = OUT_DIR / f"{source_id}_head.log"
    err = OUT_DIR / f"{source_id}_head.err"
    text = ""
    if log.exists():
        text += log.read_text(encoding="utf-8", errors="replace")
    if err.exists():
        text += "\n" + err.read_text(encoding="utf-8", errors="replace")
    if "HTTP/2 403" in text or "HTTP/1.1 403" in text:
        if "cf-mitigated: challenge" in text:
            status = "BLOCKED_CLOUDFLARE_CHALLENGE"
        else:
            status = "BLOCKED_403"
    elif "HTTP/2 200" in text or "HTTP/1.1 200" in text:
        status = "HTTP_200_AVAILABLE"
    elif not text.strip():
        status = "MISSING_PROBE"
    else:
        status = "UNKNOWN"
    return {
        "gate": source_id,
        "status": status,
        "evidence": f"{rel(log)}; {rel(err)}",
        "detail": "direct HEAD probe status recorded",
    }


def summary_row(gate: str, status: str, evidence: str, detail: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
    }


def build_rows() -> List[Dict[str, str]]:
    stage38 = read_csv(STAGE38_SUMMARY)
    checklist = read_csv(STAGE38_CHECKLIST)
    external = read_csv(EXTERNAL)
    fulltext = row_by(stage38, "item", "fulltext_artifact")
    decision = row_by(stage38, "item", "stage38_decision")
    external_fulltext = row_by(external, "evidence_id", "fab686_fulltext")

    checklist_statuses = sorted({row.get("status", "MISSING") for row in checklist})
    fulltext_status = fulltext.get("status", "MISSING")
    decision_status = decision.get("status", "MISSING")
    external_status = external_fulltext.get("status", "MISSING")

    rows = [
        head_status("acm_pdf"),
        head_status("eprint_pdf"),
        summary_row(
            "stage38_fulltext_artifact",
            fulltext_status,
            rel(STAGE38_SUMMARY),
            fulltext.get("detail", ""),
        ),
        summary_row(
            "stage38_decision",
            decision_status,
            rel(STAGE38_SUMMARY),
            decision.get("detail", ""),
        ),
        summary_row(
            "stage38_review_checklist",
            ";".join(checklist_statuses) if checklist_statuses else "MISSING",
            rel(STAGE38_CHECKLIST),
            "manual review checklist statuses",
        ),
        summary_row(
            "external_fulltext_intake",
            external_status,
            rel(EXTERNAL),
            external_fulltext.get("detail", ""),
        ),
    ]

    if decision_status == "FULLTEXT_AVAILABLE_REVIEW_REQUIRED" and fulltext_status == "AVAILABLE_UNREVIEWED":
        stage62_status = "FULLTEXT_AVAILABLE_REVIEW_REQUIRED"
        detail = "full-text artifact is available; manual claim-to-source review is required"
    elif decision_status == "BLOCKED_FULLTEXT_MISSING" and external_status == "MISSING":
        stage62_status = "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW"
        detail = "no recognized full-text artifact is registered; theorem-level claims remain blocked"
    else:
        stage62_status = "REVIEW_STATE_INCONSISTENT"
        detail = (
            f"stage38_decision={decision_status}; fulltext={fulltext_status}; "
            f"external_fulltext={external_status}"
        )

    rows.append(
        summary_row(
            "stage62_decision",
            stage62_status,
            f"{rel(STAGE38_SUMMARY)}; {rel(EXTERNAL)}",
            detail,
        )
    )
    return rows


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "status", "evidence", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    decision = row_by(rows, "gate", "stage62_decision")
    lines = [
        "# Stage 62 Full-Text Unlock Probe Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 62 tests whether a 2025/686 full-text artifact is available for",
        "theorem-level protocol citation and novelty review. It does not modify",
        "scalar SAB or the `sab_pvw_*` implementation.",
        "",
        "## Checks",
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
            "## Decision",
            "",
            f"`{decision.get('status', 'MISSING')}`",
            "",
            "No theorem, algorithm, table, figure, experiment-number, or novelty",
            "claim is upgraded unless Stage62 reaches",
            "`FULLTEXT_AVAILABLE_REVIEW_REQUIRED` and the manual checklist is",
            "completed with concrete source anchors.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(OUT_MD, rows)
    decision = row_by(rows, "gate", "stage62_decision").get("status", "MISSING")
    print(f"Wrote {rel(OUT_CSV)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage 62 full-text unlock probe: {decision}")
    return 0 if decision in {"WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW", "FULLTEXT_AVAILABLE_REVIEW_REQUIRED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
