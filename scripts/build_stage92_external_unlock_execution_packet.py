#!/usr/bin/env python3
"""Build the Stage92 external unlock execution packet.

Stage92 is a control-plane handoff stage. It translates the remaining
post-Stage91 blockers into concrete commands and acceptance gates without
executing external downloads, native perf counters, or manual novelty review.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage92_external_unlock_execution"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_LANES = OUT_DIR / "lane_matrix.csv"
OUT_COMMANDS = OUT_DIR / "commands.csv"
OUT_ACCEPTANCE = OUT_DIR / "acceptance_matrix.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage92_external_unlock_execution_packet.md"

STAGE91 = ROOT / "repro" / "stage91_final_package" / "summary.csv"
STAGE52 = ROOT / "repro" / "stage52_external_unlock_readiness.csv"
BLOCKERS = ROOT / "repro" / "remaining_blocker_dashboard.csv"
CLAIMS = ROOT / "repro" / "stage91_final_package" / "claim_boundary.csv"


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


def summary_row(
    gate: str,
    status: str,
    evidence: str,
    detail: str,
    next_action: str,
) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def lane_rows() -> List[Dict[str, str]]:
    blockers = by_key(BLOCKERS, "blocker_id")
    unlocks = by_key(STAGE52, "blocker_id")
    lane_ids = [
        ("native_perf", "CB5", "S52-NATIVE-PERF"),
        ("fulltext_686", "CB7", "S52-FULLTEXT-686"),
        ("novelty_review", "CB6", "S52-NOVELTY-REVIEW"),
        ("final_recheck", "A9", "S52-FINAL-RECHECK"),
    ]
    rows = []
    for lane_id, blocker_id, unlock_id in lane_ids:
        blocker = blockers.get(blocker_id, {})
        unlock = unlocks.get(blocker_id, {})
        packet_status = "READY_EXTERNAL_EXECUTION"
        if not blocker or not unlock:
            packet_status = "MISSING_INPUT"
        elif "BLOCKED" not in blocker.get("current_status", "") and blocker_id != "A9":
            packet_status = "REVIEW_REQUIRED"
        rows.append(
            {
                "lane_id": lane_id,
                "blocker_id": blocker_id,
                "unlock_id": unlock_id,
                "claim_lane": blocker.get("claim_lane", unlock.get("claim_lane", "")),
                "current_status": blocker.get("current_status", "MISSING"),
                "readiness": unlock.get("readiness", "MISSING"),
                "required_input": unlock.get("required_input", ""),
                "unlock_command": unlock.get("command", blocker.get("unlock_command", "")),
                "expected_artifacts": unlock.get("expected_artifacts", ""),
                "acceptance_gate": unlock.get("acceptance_gate", blocker.get("review_gate", "")),
                "failure_policy": unlock.get("failure_policy", ""),
                "claim_policy": blocker.get("claim_policy", ""),
                "packet_status": packet_status,
            }
        )
    return rows


def command_rows() -> List[Dict[str, str]]:
    return [
        {
            "command_id": "C92-1-native-perf",
            "environment": "native Linux or perf-enabled WSL with target AVX512 hardware",
            "command": "STAGE28_RUN_BENCH=1 bash scripts/run_stage28_native_perf_counter_gate.sh",
            "purpose": "Collect hardware-counter and correctness evidence for MAT-AVX512 load/store/FMA attribution.",
            "expected_outputs": "repro/stage28_native_perf_counter_gate/summary.csv; repro/stage28_native_perf_counter_gate/environment.log; repro/stage28_native_perf_counter_gate/perf_smoke.log; repro/stage28_native_perf_counter_gate/bench_perf.log; repro/stage28_native_perf_counter_gate/bench_run.log",
            "pass_condition": "summary.csv records hardware_counter_gate=PASS and bench_correctness=PASS.",
            "claim_effect": "Only moves CB5/A8 to review-required; manual interpretation is still required before theoretical-optimality wording.",
        },
        {
            "command_id": "C92-2-fulltext",
            "environment": "local environment with reviewed 2025/686 PDF or text artifact",
            "command": "FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf bash scripts/run_stage38_fulltext_review_gate.sh",
            "purpose": "Register and hash the 2025/686 full text so theorem/protocol/table/figure claims can be reviewed.",
            "expected_outputs": "repro/stage38_fulltext_review_gate/summary.csv; repro/external_evidence_intake/summary.csv; docs/stage38_fulltext_review_log.md",
            "pass_condition": "Stage38 reports FULLTEXT_AVAILABLE_REVIEW_REQUIRED or stronger and the artifact hash is registered.",
            "claim_effect": "Only moves CB7/A8b to review-required; theorem-level citations remain blocked until source anchors are written.",
        },
        {
            "command_id": "C92-3-register-external",
            "environment": "local environment after collecting full text or native perf artifacts",
            "command": "FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf STAGE28_NATIVE_PERF_SUMMARY=/path/to/summary.csv python scripts/register_external_evidence.py",
            "purpose": "Register external artifact paths, sizes, and SHA-256 values in the external evidence intake.",
            "expected_outputs": "repro/external_evidence_intake/summary.csv",
            "pass_condition": "External intake rows are non-missing and contain path, size, hash, and status.",
            "claim_effect": "Registration enables review gates; it never upgrades a claim alone.",
        },
        {
            "command_id": "C92-4-novelty-review",
            "environment": "local environment with full-text anchors for 2025/686 and related work",
            "command": "FINAL_RECHECK_RELATED_WORK=1 bash scripts/run_final_goal_recheck.sh",
            "purpose": "Refresh related-work/novelty gates after manual claim-to-source mapping is supplied.",
            "expected_outputs": "repro/stage27_related_work_access_probe/summary.csv; docs/stage27_related_work_access_probe_log.md; repro/final_goal_recheck/summary.csv",
            "pass_condition": "Novelty gate no longer reports BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW.",
            "claim_effect": "Only after manual source-anchor review may novelty wording move beyond scoped engineering/systems wording.",
        },
        {
            "command_id": "C92-5-final-refresh",
            "environment": "local environment after external artifacts and manual reviews are complete",
            "command": "FINAL_RECHECK_CITATION=1 FINAL_RECHECK_PERF=1 FINAL_RECHECK_EXTERNAL_INTAKE=1 FINAL_RECHECK_RELATED_WORK=1 bash scripts/run_final_goal_recheck.sh && bash scripts/run_stage90_external_claim_unlock.sh && bash scripts/run_stage91_final_package.sh",
            "purpose": "Refresh final audit, external claim gate, and scoped/final package after unlock evidence changes.",
            "expected_outputs": "repro/final_goal_recheck/summary.csv; repro/final_goal_completion_audit.csv; repro/remaining_blocker_dashboard.csv; repro/stage90_external_claim_unlock/summary.csv; repro/stage91_final_package/summary.csv",
            "pass_condition": "A8/A8b/CB5/CB6/CB7 are no longer blocked and claim wording has been manually checked.",
            "claim_effect": "Only this path can support moving beyond the Stage91 scoped package.",
        },
    ]


def acceptance_rows() -> List[Dict[str, str]]:
    return [
        {
            "acceptance_id": "A92-CB5",
            "requirement": "Native/perf-backed MAT-AVX512 attribution.",
            "evidence": "repro/stage28_native_perf_counter_gate/summary.csv; perf logs; Stage22 timing context",
            "pass_condition": "hardware_counter_gate=PASS, bench_correctness=PASS, and manual interpretation ties counters to the MAT path.",
            "fail_condition": "perf missing, WSL proxy only, correctness fails, or counters are not interpreted.",
            "decision_effect": "Keep theoretical optimality blocked unless pass_condition is met.",
        },
        {
            "acceptance_id": "A92-CB7",
            "requirement": "2025/686 full-text protocol/theorem citation review.",
            "evidence": "FAB686_FULLTEXT_PATH artifact hash; docs/stage38_fulltext_review_log.md; source-anchor notes",
            "pass_condition": "Full text is registered and protocol stages, complexity formulas, noise/security assumptions, and tables/figures are mapped to anchors.",
            "fail_condition": "metadata-only evidence, blocked download route, unreviewed PDF, or missing anchors.",
            "decision_effect": "Keep theorem/table/figure/experiment citations blocked unless pass_condition is met.",
        },
        {
            "acceptance_id": "A92-CB6",
            "requirement": "Novelty and related-work distinction review.",
            "evidence": "related-work source anchors; manual claim-to-source mapping; refreshed novelty gate",
            "pass_condition": "Every novelty/distinction sentence maps to reviewed source anchors and the novelty gate is no longer blocked.",
            "fail_condition": "source access only, incomplete full text, or unmapped novelty wording.",
            "decision_effect": "Keep novelty wording scoped to engineering/systems evidence unless pass_condition is met.",
        },
        {
            "acceptance_id": "A92-A9",
            "requirement": "Final claim upgrade beyond scoped engineering.",
            "evidence": "refreshed final audit, Stage90, Stage91, and Stage42 verifier",
            "pass_condition": "CB5, CB6, and CB7 are no longer blocked; final audit upgrades A9; Stage42 verifier passes from a clean worktree.",
            "fail_condition": "Any stronger-claim blocker remains blocked or verifier fails.",
            "decision_effect": "Keep the active goal open and scoped if any fail_condition remains.",
        },
    ]


def claim_guard_ok() -> bool:
    claims = by_key(CLAIMS, "claim_id")
    blocked = [
        claims.get("C3", {}).get("status", ""),
        claims.get("C4", {}).get("status", ""),
        claims.get("C5", {}).get("status", ""),
    ]
    return all("BLOCKED" in status or "MISSING_OPTIONAL" in status for status in blocked)


def build_summary(lanes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stage91 = by_key(STAGE91, "gate")
    blockers = by_key(BLOCKERS, "blocker_id")
    unlocks = by_key(STAGE52, "unlock_id")
    stage91_decision = stage91.get("stage91_decision", {}).get("status", "MISSING")
    missing_blockers = [item for item in ["CB5", "CB6", "CB7", "A9"] if item not in blockers]
    missing_unlocks = [
        item
        for item in [
            "S52-NATIVE-PERF",
            "S52-FULLTEXT-686",
            "S52-NOVELTY-REVIEW",
            "S52-FINAL-RECHECK",
        ]
        if item not in unlocks
    ]
    lane_missing = [row["lane_id"] for row in lanes if row["packet_status"] == "MISSING_INPUT"]
    claim_guard = claim_guard_ok()

    rows = [
        summary_row(
            "stage92_stage91_precondition",
            "PASS" if stage91_decision == "PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED" else "FAIL_STAGE91_PRECONDITION",
            rel(STAGE91),
            f"stage91_decision={stage91_decision}",
            "Rerun Stage91 before relying on Stage92 if this gate fails.",
        ),
        summary_row(
            "stage92_unlock_sources",
            "PASS" if not missing_blockers and not missing_unlocks else "FAIL_MISSING_UNLOCK_SOURCE",
            f"{rel(BLOCKERS)}; {rel(STAGE52)}",
            f"missing_blockers={missing_blockers or 'none'}; missing_unlocks={missing_unlocks or 'none'}",
            "Restore Stage52/blocker rows before executing external unlock commands.",
        ),
        summary_row(
            "stage92_lane_packet",
            "PASS_EXTERNAL_LANES_RECORDED" if not lane_missing else "FAIL_LANE_PACKET",
            rel(OUT_LANES),
            f"lanes={'; '.join(row['lane_id'] + ':' + row['packet_status'] for row in lanes)}",
            "Execute the lane commands only on the required external platform or with supplied full-text artifacts.",
        ),
        summary_row(
            "stage92_claim_guard",
            "PASS_STRONGER_CLAIMS_BLOCKED" if claim_guard else "FAIL_CLAIM_GUARD",
            rel(CLAIMS),
            "Stage91 blocked C3/C4/C5 stronger claims remain blocked."
            if claim_guard
            else "Stage91 claim boundary no longer blocks C3/C4/C5.",
            "Do not upgrade claim wording until the Stage92 acceptance matrix passes.",
        ),
    ]
    ok = all(row["status"].startswith("PASS") for row in rows)
    rows.append(
        summary_row(
            "stage92_decision",
            "PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED"
            if ok
            else "FAIL_STAGE92_EXTERNAL_UNLOCK_PACKET",
            rel(OUT_SUMMARY),
            "External unlock execution packet is recorded; stronger claims remain blocked until external evidence is supplied and reviewed."
            if ok
            else "One or more Stage92 gates failed.",
            "Run only the relevant external unlock lane, then rerun Stage90/91/92/42 verification before changing claims.",
        )
    )
    return rows


def artifact_rows() -> List[Dict[str, str]]:
    return [
        {"artifact": rel(OUT_SUMMARY), "purpose": "Stage92 gate summary", "producer": "scripts/build_stage92_external_unlock_execution_packet.py"},
        {"artifact": rel(OUT_LANES), "purpose": "External unlock lane matrix", "producer": "scripts/build_stage92_external_unlock_execution_packet.py"},
        {"artifact": rel(OUT_COMMANDS), "purpose": "Concrete external execution commands", "producer": "scripts/build_stage92_external_unlock_execution_packet.py"},
        {"artifact": rel(OUT_ACCEPTANCE), "purpose": "Acceptance and failure matrix", "producer": "scripts/build_stage92_external_unlock_execution_packet.py"},
        {"artifact": rel(OUT_MD), "purpose": "Human-readable Stage92 packet", "producer": "scripts/build_stage92_external_unlock_execution_packet.py"},
    ]


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_md(
    summary: List[Dict[str, str]],
    lanes: List[Dict[str, str]],
    commands: List[Dict[str, str]],
    acceptance: List[Dict[str, str]],
) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = summary[-1]
    lines = [
        "# Stage92 External Unlock Execution Packet",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "Stage92 is an execution handoff for remaining external blockers. It does",
        "not run native perf, does not fetch or review the 2025/686 full text,",
        "and does not upgrade the Stage91 scoped final package.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next action |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row['gate']} | {row['status']} | {escape_md(row['evidence'])} | {escape_md(row['detail'])} | {escape_md(row['next_action'])} |"
        )

    lines.extend(["", "## Unlock Lanes", "", "| lane | blocker | readiness | command | packet status |", "|---|---|---|---|---|"])
    for row in lanes:
        lines.append(
            f"| {row['lane_id']} | {row['blocker_id']} | {escape_md(row['readiness'])} | `{escape_md(row['unlock_command'])}` | {row['packet_status']} |"
        )

    lines.extend(["", "## Commands", "", "| command | environment | pass condition | claim effect |", "|---|---|---|---|"])
    for row in commands:
        lines.append(
            f"| `{escape_md(row['command'])}` | {escape_md(row['environment'])} | {escape_md(row['pass_condition'])} | {escape_md(row['claim_effect'])} |"
        )

    lines.extend(["", "## Acceptance Matrix", "", "| id | requirement | pass condition | decision effect |", "|---|---|---|---|"])
    for row in acceptance:
        lines.append(
            f"| {row['acceptance_id']} | {escape_md(row['requirement'])} | {escape_md(row['pass_condition'])} | {escape_md(row['decision_effect'])} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    lanes = lane_rows()
    commands = command_rows()
    acceptance = acceptance_rows()
    summary = build_summary(lanes)
    index = artifact_rows()

    write_csv(
        OUT_SUMMARY,
        summary,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_csv(
        OUT_LANES,
        lanes,
        [
            "lane_id",
            "blocker_id",
            "unlock_id",
            "claim_lane",
            "current_status",
            "readiness",
            "required_input",
            "unlock_command",
            "expected_artifacts",
            "acceptance_gate",
            "failure_policy",
            "claim_policy",
            "packet_status",
        ],
    )
    write_csv(
        OUT_COMMANDS,
        commands,
        [
            "command_id",
            "environment",
            "command",
            "purpose",
            "expected_outputs",
            "pass_condition",
            "claim_effect",
        ],
    )
    write_csv(
        OUT_ACCEPTANCE,
        acceptance,
        [
            "acceptance_id",
            "requirement",
            "evidence",
            "pass_condition",
            "fail_condition",
            "decision_effect",
        ],
    )
    write_csv(OUT_INDEX, index, ["artifact", "purpose", "producer"])
    write_md(summary, lanes, commands, acceptance)

    decision = summary[-1]["status"]
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage92 external unlock execution packet: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
