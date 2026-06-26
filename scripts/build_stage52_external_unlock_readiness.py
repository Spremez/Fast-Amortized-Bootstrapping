#!/usr/bin/env python3
"""Build the Stage 52 external-unlock readiness packet.

This script records the exact external inputs, commands, expected artifacts,
and acceptance gates needed to move beyond the current scoped PVW/MAT-SAB
engineering claim. It does not run the heavy commands and does not upgrade
claims.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
STAGE41 = ROOT / "repro" / "stage41_external_unlock_packet.csv"
BLOCKERS = ROOT / "repro" / "remaining_blocker_dashboard.csv"
FRONTIER = ROOT / "repro" / "stage51_goal_completion_frontier.csv"
OUT_CSV = ROOT / "repro" / "stage52_external_unlock_readiness.csv"
OUT_MD = ROOT / "docs" / "stage52_external_unlock_readiness.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def row(
    unlock_id: str,
    blocker_id: str,
    claim_lane: str,
    current_status: str,
    readiness: str,
    required_input: str,
    command: str,
    expected_artifacts: str,
    acceptance_gate: str,
    failure_policy: str,
    next_action: str,
) -> Dict[str, str]:
    return {
        "unlock_id": unlock_id,
        "blocker_id": blocker_id,
        "claim_lane": claim_lane,
        "current_status": current_status,
        "readiness": readiness,
        "required_input": required_input,
        "command": command,
        "expected_artifacts": expected_artifacts,
        "acceptance_gate": acceptance_gate,
        "failure_policy": failure_policy,
        "next_action": next_action,
    }


def build_rows() -> List[Dict[str, str]]:
    stage41 = by_key(STAGE41, "unlock_id")
    blockers = by_key(BLOCKERS, "blocker_id")
    frontier = by_key(FRONTIER, "frontier_id")

    native_perf = stage41.get("S41-NATIVE-PERF-INTAKE", {})
    fulltext = stage41.get("S41-FULLTEXT-INTAKE", {})
    registration = stage41.get("S41-EXTERNAL-REGISTRATION", {})
    final_recheck = stage41.get("S41-FINAL-RECHECK", {})

    return [
        row(
            "S52-NATIVE-PERF",
            "CB5",
            native_perf.get("claim_lane", "MAT-AVX512 load/store/FMA attribution"),
            blockers.get("CB5", {}).get("current_status", ""),
            native_perf.get("readiness", ""),
            native_perf.get("required_evidence", ""),
            native_perf.get("command", ""),
            "repro/stage28_native_perf_counter_gate/summary.csv; "
            "repro/stage28_native_perf_counter_gate/environment.log; "
            "repro/stage28_native_perf_counter_gate/perf_smoke.log; "
            "repro/stage28_native_perf_counter_gate/bench_perf.log; "
            "repro/stage28_native_perf_counter_gate/bench_run.log",
            "summary.csv must contain hardware_counter_gate=PASS and bench_correctness=PASS.",
            "If perf is missing, blocked, or correctness fails, keep CB5/A8 blocked.",
            blockers.get("CB5", {}).get("unlock_command", ""),
        ),
        row(
            "S52-FULLTEXT-686",
            "CB7",
            fulltext.get("claim_lane", "2025/686 theorem-level protocol and citation review"),
            blockers.get("CB7", {}).get("current_status", ""),
            fulltext.get("readiness", ""),
            fulltext.get("required_evidence", ""),
            fulltext.get("command", ""),
            "repro/stage38_fulltext_review_gate/summary.csv; "
            "repro/external_evidence_intake/summary.csv; "
            "docs/stage38_fulltext_review_log.md",
            "Stage38 must report FULLTEXT_AVAILABLE_REVIEW_REQUIRED or stronger, and the full-text hash must be registered.",
            "If full text is missing, unrecognized, or unreviewed, keep CB7/A8b blocked.",
            blockers.get("CB7", {}).get("unlock_command", ""),
        ),
        row(
            "S52-NOVELTY-REVIEW",
            "CB6",
            blockers.get("CB6", {}).get("claim_lane", "Novelty and related-work distinction"),
            blockers.get("CB6", {}).get("current_status", ""),
            "WAIT_MANUAL_FULLTEXT_REVIEW",
            "Full-text anchors for 2025/686 and related work, with claim-to-source mapping for each novelty sentence.",
            blockers.get("CB6", {}).get("unlock_command", ""),
            "repro/stage27_related_work_access_probe/summary.csv; "
            "docs/stage27_related_work_access_probe_log.md; "
            "manual claim-to-source review notes",
            "Novelty gate must no longer report BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW.",
            "If source anchors are incomplete, keep novelty wording scoped to engineering/systems evidence.",
            blockers.get("CB6", {}).get("unlock_command", ""),
        ),
        row(
            "S52-EXTERNAL-REGISTRATION",
            "A8/A8b",
            registration.get("claim_lane", "external evidence intake"),
            registration.get("current_status", ""),
            registration.get("readiness", ""),
            registration.get("required_evidence", ""),
            registration.get("command", ""),
            "repro/external_evidence_intake/summary.csv",
            "Registered external rows must include paths, sizes, SHA-256 values, and non-missing statuses.",
            "Registration alone never upgrades claims; it only enables review-required status.",
            registration.get("command", ""),
        ),
        row(
            "S52-FINAL-RECHECK",
            "A9",
            final_recheck.get("claim_lane", "overall final goal audit"),
            blockers.get("A9", {}).get("current_status", ""),
            final_recheck.get("readiness", ""),
            final_recheck.get("required_evidence", ""),
            final_recheck.get("command", ""),
            "repro/final_goal_recheck/summary.csv; repro/final_goal_completion_audit.csv; repro/remaining_blocker_dashboard.csv",
            "A9 may move only after A8/A8b/CB5/CB6/CB7 are no longer blocked and claim wording is manually checked.",
            "If any stronger-claim blocker remains blocked or review-required, preserve the scoped/review-required final status.",
            frontier.get("G9", {}).get("next_action", ""),
        ),
    ]


def gate_status(rows: List[Dict[str, str]]) -> str:
    expected = {
        "S52-NATIVE-PERF": {"WAIT_NATIVE_PERF"},
        "S52-FULLTEXT-686": {"WAIT_EXTERNAL_FULLTEXT", "READY_FOR_MANUAL_REVIEW"},
        "S52-NOVELTY-REVIEW": {"WAIT_MANUAL_FULLTEXT_REVIEW"},
        "S52-EXTERNAL-REGISTRATION": {"WAIT_EXTERNAL_ARTIFACTS", "READY_TO_REGISTER"},
        "S52-FINAL-RECHECK": {"WAIT_UNLOCKS", "READY_AFTER_UNLOCKS"},
    }
    by_id = {row["unlock_id"]: row for row in rows}
    ok = True
    for unlock_id, readiness_values in expected.items():
        ok = ok and by_id.get(unlock_id, {}).get("readiness") in readiness_values
        ok = ok and bool(by_id.get(unlock_id, {}).get("command", "").strip())
        ok = ok and bool(by_id.get(unlock_id, {}).get("expected_artifacts", "").strip())
        ok = ok and bool(by_id.get(unlock_id, {}).get("acceptance_gate", "").strip())
    return (
        "PASS_EXTERNAL_UNLOCK_READINESS_PACKET"
        if ok
        else "FAIL_EXTERNAL_UNLOCK_READINESS_PACKET"
    )


def write_csv(rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: List[Dict[str, str]]) -> List[str]:
    cols = ["unlock_id", "blocker_id", "readiness", "command", "acceptance_gate"]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for item in rows:
        lines.append("| " + " | ".join(item.get(col, "") for col in cols) + " |")
    return lines


def write_md(rows: List[Dict[str, str]]) -> None:
    decision = gate_status(rows)
    lines = [
        "# Stage 52 External-Unlock Readiness Packet",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 52 records the exact external inputs, commands, expected artifacts,",
        "acceptance gates, and failure policies required to move beyond the current",
        "scoped PVW/MAT-SAB engineering claim. It does not execute the heavy",
        "external commands and does not upgrade claims.",
        "",
        "## Readiness Matrix",
        "",
        *md_table(rows),
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "The current local evidence chain remains scoped-ready. Stronger claims",
        "can only be revisited after the required external artifacts are supplied",
        "and the listed gates pass.",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    rows = build_rows()
    write_csv(rows)
    write_md(rows)
    decision = gate_status(rows)
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage 52 external unlock readiness: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
