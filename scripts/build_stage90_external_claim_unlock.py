#!/usr/bin/env python3
"""Build the Stage90 external-claim unlock report.

This stage records whether the project can move beyond the scoped engineering
PVW/MAT-SAB claim after Stage89. It intentionally does not upgrade any claim
unless native perf, reviewed 2025/686 full text, and novelty-review inputs are
available.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage90_external_claim_unlock"
OUT_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage90_external_claim_unlock_log.md"

STAGE89 = ROOT / "repro" / "stage89_h14_promotion_policy_integration" / "summary.csv"
STAGE90_CITATION = OUT_DIR / "citation_probe" / "summary.csv"
STAGE90_ACCESS = OUT_DIR / "citation_probe" / "access_probe.csv"
STAGE90_NATIVE_PERF = OUT_DIR / "native_perf_gate" / "summary.csv"
EXTERNAL_INTAKE = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
STAGE62 = ROOT / "repro" / "stage62_fulltext_unlock_probe" / "unlock_summary.csv"
STAGE72 = ROOT / "repro" / "stage72_external_source_refresh" / "summary.csv"
BLOCKERS = ROOT / "repro" / "remaining_blocker_dashboard.csv"


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


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "status", "evidence", "detail", "next_action"],
            lineterminator="\n",
        )
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


def stage89_precondition() -> Dict[str, str]:
    stage89 = by_key(STAGE89, "gate")
    decision = stage89.get("stage89_decision", {}).get("status", "MISSING")
    return row(
        "stage90_stage89_precondition",
        "PASS" if decision == "PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT" else "FAIL_STAGE89_PRECONDITION",
        rel(STAGE89),
        f"stage89_decision={decision}",
        "Repair or rerun Stage89 before external claim unlock decisions.",
    )


def citation_probe() -> Dict[str, str]:
    summary = by_key(STAGE90_CITATION, "gate")
    access_rows = read_csv(STAGE90_ACCESS)
    direct = summary.get("direct_pdf_access", {}).get("status", "MISSING")
    citation_decision = summary.get("citation_decision", {}).get("status", "MISSING")
    blocked_routes = [
        f"{item.get('id')}={item.get('status')}"
        for item in access_rows
        if item.get("status", "").startswith("BLOCKED")
    ]
    if direct == "PASS":
        status = "FULLTEXT_ROUTE_AVAILABLE_REVIEW_REQUIRED"
        next_action = "Register the full text and perform source-anchor review before theorem-level claims."
    elif summary and access_rows:
        status = "PASS_PROBE_RECORDED_WAIT_FULLTEXT"
        next_action = "Supply FAB686_FULLTEXT_PATH or another reviewed full-text artifact."
    else:
        status = "MISSING_PROBE_OUTPUT"
        next_action = "Rerun scripts/run_stage90_external_claim_unlock.sh."
    detail = (
        f"direct_pdf_access={direct}; citation_decision={citation_decision}; "
        f"blocked_routes={'; '.join(blocked_routes) if blocked_routes else 'none_recorded'}"
    )
    return row(
        "stage90_citation_fulltext_probe",
        status,
        f"{rel(STAGE90_CITATION)}; {rel(STAGE90_ACCESS)}",
        detail,
        next_action,
    )


def native_perf_probe() -> Dict[str, str]:
    native = by_key(STAGE90_NATIVE_PERF, "probe")
    external = by_key(EXTERNAL_INTAKE, "evidence_id")
    hardware = native.get("hardware_counter_gate", {}).get("status", "MISSING")
    perf_cmd = native.get("perf_command", {}).get("status", "MISSING")
    external_perf = external.get("stage28_native_perf_summary", {}).get("status", "MISSING")
    if hardware == "PASS" or external_perf == "PASS_COUNTER_ATTRIBUTION_AVAILABLE":
        status = "PERF_COUNTERS_AVAILABLE_REVIEW_REQUIRED"
        next_action = "Interpret counters with Stage22 timings and objdump before any MAT-AVX512 theory claim."
    elif hardware == "READY_FOR_BENCH" or external_perf == "COUNTER_SMOKE_ONLY":
        status = "WAIT_NATIVE_PERF_BENCH"
        next_action = "Run Stage28 with STAGE28_RUN_BENCH=1 on the perf-enabled platform."
    elif native:
        status = "WAIT_NATIVE_PERF"
        next_action = "Run on native/perf-enabled Linux before claiming load/store or FMA optimality."
    else:
        status = "MISSING_NATIVE_PERF_PROBE"
        next_action = "Rerun scripts/run_stage90_external_claim_unlock.sh."
    return row(
        "stage90_native_perf_unlock",
        status,
        f"{rel(STAGE90_NATIVE_PERF)}; {rel(EXTERNAL_INTAKE)}",
        f"perf_command={perf_cmd}; hardware_counter_gate={hardware}; external_perf={external_perf}",
        next_action,
    )


def source_refresh_status() -> Dict[str, str]:
    stage72 = by_key(STAGE72, "gate")
    author = stage72.get("stage72_author_metadata_route", {}).get("status", "MISSING")
    doi = stage72.get("stage72_doi_metadata_route", {}).get("status", "MISSING")
    code = stage72.get("stage72_code_route", {}).get("status", "MISSING")
    fulltext = stage72.get("stage72_official_fulltext_routes", {}).get("status", "MISSING")
    ok = author == "PASS" and doi == "PASS" and code == "PASS"
    return row(
        "stage90_source_refresh_context",
        "PASS_METADATA_CODE_CONTEXT" if ok else "MISSING_SOURCE_CONTEXT",
        rel(STAGE72),
        f"author={author}; doi={doi}; code={code}; fulltext={fulltext}",
        "Metadata/code context is useful for engineering reports but does not replace full-text review.",
    )


def fulltext_unlock() -> Dict[str, str]:
    stage62 = by_key(STAGE62, "gate")
    external = by_key(EXTERNAL_INTAKE, "evidence_id")
    stage62_decision = stage62.get("stage62_decision", {}).get("status", "MISSING")
    stage38_artifact = stage62.get("stage38_fulltext_artifact", {}).get("status", "MISSING")
    external_fulltext = external.get("fab686_fulltext", {}).get("status", "MISSING")
    if external_fulltext == "AVAILABLE_UNREVIEWED" or stage38_artifact.startswith("PASS"):
        status = "FULLTEXT_AVAILABLE_REVIEW_REQUIRED"
        next_action = "Complete manual protocol, theorem, table, and experiment source-anchor review."
    else:
        status = "WAIT_FULLTEXT_ARTIFACT"
        next_action = "Set FAB686_FULLTEXT_PATH and rerun the full-text review gate."
    return row(
        "stage90_fulltext_unlock",
        status,
        f"{rel(STAGE62)}; {rel(EXTERNAL_INTAKE)}",
        f"stage62_decision={stage62_decision}; stage38_artifact={stage38_artifact}; external_fulltext={external_fulltext}",
        next_action,
    )


def novelty_review_unlock() -> Dict[str, str]:
    blockers = by_key(BLOCKERS, "blocker_id")
    cb6 = blockers.get("CB6", {})
    current = cb6.get("current_status", "MISSING")
    if "BLOCKED" in current:
        status = "WAIT_FULLTEXT_OR_MANUAL_REVIEW"
        next_action = cb6.get("unlock_command", "Run related-work/source-anchor review after full text is available.")
    else:
        status = "REVIEW_REQUIRED"
        next_action = "Manually map each novelty sentence to source anchors before paper wording upgrade."
    return row(
        "stage90_novelty_review_unlock",
        status,
        cb6.get("evidence", rel(BLOCKERS)),
        current,
        next_action,
    )


def blocker_dashboard_guard() -> Dict[str, str]:
    blockers = by_key(BLOCKERS, "blocker_id")
    missing = [bid for bid in ["CB5", "CB6", "CB7", "A9"] if bid not in blockers]
    blocked = [
        bid
        for bid in ["CB5", "CB6", "CB7"]
        if "BLOCKED" in blockers.get(bid, {}).get("current_status", "")
    ]
    status = "PASS_BLOCKERS_REGISTERED" if not missing and blocked else "MISSING_OR_UNLOCKED_BLOCKERS"
    return row(
        "stage90_blocker_dashboard_guard",
        status,
        rel(BLOCKERS),
        f"missing={missing or 'none'}; blocked={blocked or 'none'}",
        "Keep CB5/CB6/CB7 visible until native perf, full-text, and novelty review are resolved.",
    )


def build_rows() -> List[Dict[str, str]]:
    rows = [
        stage89_precondition(),
        citation_probe(),
        native_perf_probe(),
        source_refresh_status(),
        fulltext_unlock(),
        novelty_review_unlock(),
        blocker_dashboard_guard(),
    ]
    statuses = {item["gate"]: item["status"] for item in rows}
    precondition_ok = statuses["stage90_stage89_precondition"] == "PASS"
    evidence_recorded = (
        statuses["stage90_citation_fulltext_probe"]
        in {"PASS_PROBE_RECORDED_WAIT_FULLTEXT", "FULLTEXT_ROUTE_AVAILABLE_REVIEW_REQUIRED"}
        and statuses["stage90_native_perf_unlock"]
        in {"WAIT_NATIVE_PERF", "WAIT_NATIVE_PERF_BENCH", "PERF_COUNTERS_AVAILABLE_REVIEW_REQUIRED"}
        and statuses["stage90_source_refresh_context"] == "PASS_METADATA_CODE_CONTEXT"
        and statuses["stage90_blocker_dashboard_guard"] in {"PASS_BLOCKERS_REGISTERED", "MISSING_OR_UNLOCKED_BLOCKERS"}
    )
    all_review_ready = (
        statuses["stage90_native_perf_unlock"] == "PERF_COUNTERS_AVAILABLE_REVIEW_REQUIRED"
        and statuses["stage90_fulltext_unlock"] == "FULLTEXT_AVAILABLE_REVIEW_REQUIRED"
        and statuses["stage90_novelty_review_unlock"] == "REVIEW_REQUIRED"
    )

    if precondition_ok and all_review_ready:
        decision = "PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_REVIEW_REQUIRED"
        detail = "External artifacts are available; manual interpretation/review is required before claim upgrade."
        next_action = "Run source-anchor and perf-interpretation reviews, then rebuild claim matrices."
    elif precondition_ok and evidence_recorded:
        decision = "PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED"
        detail = "Stage90 probe completed; native perf, reviewed full text, or novelty review inputs remain unavailable."
        next_action = "Proceed to Stage91 scoped final package only if stronger claims remain explicitly blocked or scope is narrowed."
    else:
        decision = "FAIL_STAGE90_EXTERNAL_CLAIM_UNLOCK"
        detail = "Stage90 did not record enough evidence to make an external-claim decision."
        next_action = "Inspect failed Stage90 gates and rerun the probe."

    rows.append(
        row(
            "stage90_decision",
            decision,
            rel(OUT_CSV),
            detail,
            next_action,
        )
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = rows[-1]
    lines = [
        "# Stage90 External Claim Unlock Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage90 checks whether any stronger paper/theory claim can be unlocked",
        "after Stage89 promoted H14-C1 as the preferred explicit r=6 engineering",
        "path. It is a claim-control and external-evidence stage only.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next_action |",
        "|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            "| {gate} | {status} | {evidence} | {detail} | {next_action} |".format(
                **{k: item[k].replace("|", "\\|") for k in item}
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{decision['status']}`",
            "",
            decision["detail"],
            "",
            "Interpretation: Stage90 can only upgrade the project to a review-ready",
            "state. It cannot by itself make novelty, theorem-level, or",
            "hardware-counter optimality claims.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {rel(OUT_CSV)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage90 external claim unlock: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
