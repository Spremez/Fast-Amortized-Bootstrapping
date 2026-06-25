#!/usr/bin/env python3
"""Build Stage 44 external-unlock re-probe summary and log."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "repro" / "stage44_external_unlock_reprobe"
DOC = ROOT / "docs" / "stage44_external_unlock_reprobe_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def by_key(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def csv_row(item: str, status: str, evidence: str, detail: str) -> Dict[str, str]:
    return {
        "item": item,
        "status": status,
        "evidence": evidence,
        "detail": detail,
    }


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build(out_dir: Path) -> List[Dict[str, str]]:
    citation_summary = out_dir / "citation_probe" / "summary.csv"
    citation_access = out_dir / "citation_probe" / "access_probe.csv"
    native_summary = out_dir / "native_perf_gate" / "summary.csv"
    external_summary = ROOT / "repro" / "external_evidence_intake" / "summary.csv"

    citation_rows = read_csv(citation_summary)
    access_rows = read_csv(citation_access)
    native_rows = read_csv(native_summary)
    external_rows = read_csv(external_summary)

    direct_pdf = by_key(citation_rows, "gate", "direct_pdf_access")
    citation_decision = by_key(citation_rows, "gate", "citation_decision")
    semantic_pdf = by_key(citation_rows, "gate", "semantic_scholar_open_access_pdf_url")
    hardware_gate = by_key(native_rows, "probe", "hardware_counter_gate")
    perf_command = by_key(native_rows, "probe", "perf_command")
    fulltext_external = by_key(external_rows, "evidence_id", "fab686_fulltext")
    perf_external = by_key(external_rows, "evidence_id", "stage28_native_perf_summary")

    direct_status = direct_pdf.get("status", "MISSING")
    citation_status = citation_decision.get("status", "MISSING")
    semantic_pdf_status = semantic_pdf.get("status", "MISSING")
    hardware_status = hardware_gate.get("status", "MISSING")
    perf_cmd_status = perf_command.get("status", "MISSING")
    fulltext_status = fulltext_external.get("status", "MISSING")
    perf_external_status = perf_external.get("status", "MISSING")

    direct_pdf_available = direct_status == "PASS"
    hardware_available = hardware_status == "PASS"
    fulltext_registered = fulltext_status == "AVAILABLE_UNREVIEWED"
    perf_registered = perf_external_status == "PASS_COUNTER_ATTRIBUTION_AVAILABLE"

    if direct_pdf_available or fulltext_registered or hardware_available or perf_registered:
        decision = "READY_FOR_MANUAL_REVIEW_OR_PERF_INTERPRETATION"
        decision_detail = (
            "At least one external unlock input is available; manual review or "
            "perf interpretation is still required before any claim upgrade."
        )
    else:
        decision = "WAIT_EXTERNAL_UNLOCKS"
        decision_detail = (
            "Direct full text and hardware-counter attribution remain unavailable "
            "under the current environment."
        )

    blocked_routes = [
        f"{row.get('id')}={row.get('status')}"
        for row in access_rows
        if row.get("status", "").startswith("BLOCKED")
    ]

    return [
        csv_row(
            "citation_probe_command",
            "PASS" if citation_rows and access_rows else "MISSING",
            rel(citation_summary),
            "Stage 27 citation probe was rerun in the Stage 44 output directory."
            if citation_rows and access_rows
            else "Citation probe output is missing.",
        ),
        csv_row(
            "fulltext_pdf_access",
            direct_status,
            rel(citation_summary),
            citation_decision.get("detail", citation_status),
        ),
        csv_row(
            "semantic_scholar_open_access_pdf",
            semantic_pdf_status,
            rel(citation_summary),
            semantic_pdf.get("detail", ""),
        ),
        csv_row(
            "blocked_fulltext_routes",
            "RECORDED" if blocked_routes else "NONE_RECORDED",
            rel(citation_access),
            "; ".join(blocked_routes) if blocked_routes else "No blocked HTTP routes were recorded.",
        ),
        csv_row(
            "native_perf_command",
            perf_cmd_status,
            rel(native_summary),
            perf_command.get("detail", "perf command row missing."),
        ),
        csv_row(
            "native_perf_hardware_counter_gate",
            hardware_status,
            rel(native_summary),
            hardware_gate.get("detail", "hardware counter row missing."),
        ),
        csv_row(
            "external_fulltext_intake",
            fulltext_status,
            rel(external_summary),
            fulltext_external.get("detail", "External full-text intake row missing."),
        ),
        csv_row(
            "external_native_perf_intake",
            perf_external_status,
            rel(external_summary),
            perf_external.get("detail", "External native perf intake row missing."),
        ),
        csv_row("stage44_decision", decision, rel(out_dir / "summary.csv"), decision_detail),
    ]


def write_doc(rows: List[Dict[str, str]], out_dir: Path) -> None:
    decision = by_key(rows, "item", "stage44_decision")
    lines = [
        "# Stage 44 External Unlock Re-probe Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 44 reruns the external-unlock checks after the Stage 42/43",
        "closure package. It records whether the project can move beyond the",
        "current scoped engineering claim into theorem-level 2025/686 review or",
        "MAT-AVX512 hardware-counter attribution.",
        "",
        "This stage does not change scalar SAB or `sab_pvw_*` code and does not",
        "upgrade any claim by itself.",
        "",
        "## Summary",
        "",
        f"- decision: `{decision.get('status', 'MISSING')}`",
        f"- detail: {decision.get('detail', 'missing decision row')}",
        "",
        "## Checks",
        "",
        "| item | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['item']} | {row['status']} | {row['evidence']} | {row['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The scoped PVW/MAT-SAB engineering acceleration package remains the",
            "strongest completed claim unless this stage reports an available full",
            "text or hardware-counter artifact and the required manual review is",
            "performed.",
            "",
        ]
    )
    DOC.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Stage 44 output directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    rows = build(out_dir)
    write_csv(out_dir / "summary.csv", rows, ["item", "status", "evidence", "detail"])
    write_doc(rows, out_dir)
    print(f"Stage 44 summary: {rel(out_dir / 'summary.csv')}")
    print(f"Stage 44 log: {rel(DOC)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
