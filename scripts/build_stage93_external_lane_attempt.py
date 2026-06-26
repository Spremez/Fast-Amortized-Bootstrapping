#!/usr/bin/env python3
"""Build the Stage93 current external-lane attempt report."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro" / "stage93_external_lane_attempt"
STAGE92 = ROOT / "repro" / "stage92_external_unlock_execution" / "summary.csv"
CLAIMS = ROOT / "repro" / "stage91_final_package" / "claim_boundary.csv"
EXTERNAL_INTAKE = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
OUT_MD = ROOT / "docs" / "stage93_external_lane_attempt_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def row(gate: str, status: str, evidence: str, detail: str, next_action: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def stage92_gate() -> Dict[str, str]:
    stage92 = by_key(STAGE92, "gate")
    decision = stage92.get("stage92_decision", {}).get("status", "MISSING")
    return row(
        "stage93_stage92_precondition",
        "PASS" if decision == "PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED" else "FAIL_STAGE92_PRECONDITION",
        rel(STAGE92),
        f"stage92_decision={decision}",
        "Rerun Stage92 before relying on Stage93 if this gate fails.",
    )


def native_perf_gate(out_dir: Path) -> Dict[str, str]:
    summary = by_key(out_dir / "native_perf_gate" / "summary.csv", "probe")
    hardware = summary.get("hardware_counter_gate", {}).get("status", "MISSING")
    perf_cmd = summary.get("perf_command", {}).get("status", "MISSING")
    if hardware == "PASS":
        status = "PERF_AVAILABLE_REVIEW_REQUIRED"
        next_action = "Interpret counters before upgrading MAT-AVX512 theoretical claims."
    elif hardware == "READY_FOR_BENCH":
        status = "PERF_SMOKE_ONLY"
        next_action = "Rerun Stage93/Stage28 with STAGE28_RUN_BENCH=1 on the same perf-enabled platform."
    elif hardware == "BLOCKED":
        status = "BLOCKED_NATIVE_PERF_CURRENT_ENV"
        next_action = "Use native Linux or install/enable perf before claiming hardware-counter attribution."
    else:
        status = "MISSING_NATIVE_PERF_ATTEMPT"
        next_action = "Rerun scripts/run_stage93_external_lane_attempt.sh."
    return row(
        "stage93_native_perf_attempt",
        status,
        rel(out_dir / "native_perf_gate" / "summary.csv"),
        f"perf_command={perf_cmd}; hardware_counter_gate={hardware}",
        next_action,
    )


def fulltext_gate(out_dir: Path) -> Dict[str, str]:
    rows = read_csv(out_dir / "local_fulltext_search.csv")
    probable = [item for item in rows if item.get("match_reason") == "probable_fab686_filename"]
    if probable:
        status = "FULLTEXT_CANDIDATE_FOUND_REVIEW_REQUIRED"
        detail = "; ".join(item.get("path", "") for item in probable[:5])
        next_action = "Set FAB686_FULLTEXT_PATH to the reviewed candidate and rerun Stage38."
    elif rows:
        status = "NO_RECOGNIZED_2025_686_FULLTEXT"
        detail = f"nonmatching_candidates={len(rows)}"
        next_action = "Supply a recognized 2025/686 PDF/text artifact before theorem-level claims."
    else:
        status = "LOCAL_FULLTEXT_NOT_FOUND"
        detail = "No filename candidate was found in the configured local search roots."
        next_action = "Supply FAB686_FULLTEXT_PATH or extend STAGE93_FULLTEXT_SEARCH_ROOTS."
    return row(
        "stage93_local_fulltext_search",
        status,
        rel(out_dir / "local_fulltext_search.csv"),
        detail,
        next_action,
    )


def external_intake_gate() -> Dict[str, str]:
    rows = by_key(EXTERNAL_INTAKE, "evidence_id")
    fulltext = rows.get("fab686_fulltext", {}).get("status", "MISSING")
    native = rows.get("stage28_native_perf_summary", {}).get("status", "MISSING")
    if fulltext == "AVAILABLE_UNREVIEWED" or native == "PASS_COUNTER_ATTRIBUTION_AVAILABLE":
        status = "EXTERNAL_EVIDENCE_REGISTERED_REVIEW_REQUIRED"
        next_action = "Run Stage90/91/92/93/94/42 refresh after manual review."
    else:
        status = "PASS_EXTERNAL_INTAKE_STILL_MISSING"
        next_action = "Register external artifacts only after actual full-text or native perf evidence exists."
    return row(
        "stage93_external_intake_state",
        status,
        rel(EXTERNAL_INTAKE),
        f"fab686_fulltext={fulltext}; stage28_native_perf_summary={native}",
        next_action,
    )


def claim_guard_gate() -> Dict[str, str]:
    claims = by_key(CLAIMS, "claim_id")
    blocked = [
        claims.get("C3", {}).get("status", ""),
        claims.get("C4", {}).get("status", ""),
        claims.get("C5", {}).get("status", ""),
    ]
    ok = all("BLOCKED" in status or "MISSING_OPTIONAL" in status for status in blocked)
    return row(
        "stage93_claim_guard",
        "PASS_STRONGER_CLAIMS_BLOCKED" if ok else "FAIL_CLAIM_GUARD",
        rel(CLAIMS),
        "C3/C4/C5 remain blocked after current external lane attempts."
        if ok
        else f"claim_statuses={blocked}",
        "Do not change claim wording until Stage90/91/92/93/94/42 acceptance gates pass.",
    )


def build_summary(out_dir: Path) -> List[Dict[str, str]]:
    rows = [
        stage92_gate(),
        native_perf_gate(out_dir),
        fulltext_gate(out_dir),
        external_intake_gate(),
        claim_guard_gate(),
    ]
    precondition_ok = rows[0]["status"] == "PASS"
    attempts_recorded = rows[1]["status"] != "MISSING_NATIVE_PERF_ATTEMPT" and rows[2]["status"] != "MISSING"
    claim_guard_ok = rows[-1]["status"] == "PASS_STRONGER_CLAIMS_BLOCKED"
    decision = (
        "PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED"
        if precondition_ok and attempts_recorded and claim_guard_ok
        else "FAIL_STAGE93_EXTERNAL_LANE_ATTEMPT"
    )
    detail = (
        "Current external lane attempts are recorded; stronger claims remain blocked under current evidence."
        if decision.startswith("PASS_")
        else "One or more Stage93 gates failed."
    )
    rows.append(
        row(
            "stage93_decision",
            decision,
            rel(out_dir / "summary.csv"),
            detail,
            "Supply native perf or reviewed full text, then rerun Stage90/91/92/93/94/42 before claim changes.",
        )
    )
    return rows


def artifact_rows(out_dir: Path) -> List[Dict[str, str]]:
    return [
        {"artifact": rel(out_dir / "summary.csv"), "purpose": "Stage93 gate summary", "producer": "scripts/build_stage93_external_lane_attempt.py"},
        {"artifact": rel(out_dir / "native_perf_gate" / "summary.csv"), "purpose": "Current native/perf lane attempt", "producer": "scripts/run_stage28_native_perf_counter_gate.sh"},
        {"artifact": rel(out_dir / "native_perf_gate.log"), "purpose": "Native/perf runner log", "producer": "scripts/run_stage93_external_lane_attempt.sh"},
        {"artifact": rel(out_dir / "local_fulltext_search.csv"), "purpose": "Local full-text filename search results", "producer": "scripts/run_stage93_external_lane_attempt.sh"},
        {"artifact": rel(OUT_MD), "purpose": "Human-readable Stage93 log", "producer": "scripts/build_stage93_external_lane_attempt.py"},
    ]


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_md(out_dir: Path, rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = rows[-1]
    lines = [
        "# Stage93 External Lane Attempt Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "Stage93 executes only availability checks that are valid in the current",
        "environment. It does not upgrade claims and does not overwrite the",
        "historical Stage28 artifact.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next action |",
        "|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| {item['gate']} | {item['status']} | {esc(item['evidence'])} | {esc(item['detail'])} | {esc(item['next_action'])} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    rows = build_summary(out_dir)
    index = artifact_rows(out_dir)
    write_csv(out_dir / "summary.csv", rows, ["gate", "status", "evidence", "detail", "next_action"])
    write_csv(out_dir / "artifact_index.csv", index, ["artifact", "purpose", "producer"])
    write_md(out_dir, rows)
    decision = rows[-1]["status"]
    print(f"Wrote {rel(out_dir / 'summary.csv')}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage93 external lane attempt: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
