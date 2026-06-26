#!/usr/bin/env python3
"""Build the Stage 51 goal-completion frontier.

This script summarizes what is locally complete for the scoped PVW/MAT-SAB
engineering chain and what remains externally blocked for stronger claims. It
does not mark the active goal complete and it does not upgrade claim strength.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
BLOCKERS = ROOT / "repro" / "remaining_blocker_dashboard.csv"
STAGE42 = ROOT / "repro" / "stage42_evidence_closure_audit.csv"
STAGE50 = ROOT / "repro" / "stage50_performance_evidence_matrix.csv"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
OUT_CSV = ROOT / "repro" / "stage51_goal_completion_frontier.csv"
OUT_MD = ROOT / "docs" / "stage51_goal_completion_frontier.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def frontier_row(
    frontier_id: str,
    lane: str,
    requirement: str,
    status: str,
    evidence: str,
    interpretation: str,
    next_action: str,
    completion_effect: str,
) -> Dict[str, str]:
    return {
        "frontier_id": frontier_id,
        "lane": lane,
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "interpretation": interpretation,
        "next_action": next_action,
        "completion_effect": completion_effect,
    }


def audit_status(audit: Dict[str, Dict[str, str]], item_id: str) -> str:
    return audit.get(item_id, {}).get("status", "MISSING")


def audit_evidence(audit: Dict[str, Dict[str, str]], item_id: str) -> str:
    return audit.get(item_id, {}).get("evidence", "")


def blocker_status(blockers: Dict[str, Dict[str, str]], blocker_id: str) -> str:
    return blockers.get(blocker_id, {}).get("current_status", "MISSING")


def latest_stage_label() -> str:
    if not ROADMAP.exists():
        return "Stage19+"
    text = ROADMAP.read_text(encoding="utf-8")
    stages = sorted({int(m.group(1)) for m in re.finditer(r"^## Stage (\d+):", text, re.M)})
    if not stages:
        return "Stage19+"
    return f"Stage19-{stages[-1]}"


def build_rows() -> List[Dict[str, str]]:
    audit = by_key(FINAL_AUDIT, "item_id")
    blockers = by_key(BLOCKERS, "blocker_id")
    stage42 = by_key(STAGE42, "check_id")
    stage50_rows = read_csv(STAGE50)

    stage50_ok = bool(stage50_rows) and all(row.get("status") == "PASS" for row in stage50_rows)
    stage42_overall = stage42.get("S42-OVERALL", {}).get("status", "MISSING")
    current_stage_range = latest_stage_label()
    stage64a_closed = stage42.get("S42-STAGE64A-POST-VARIANT-REFRESH", {}).get("status") == "PASS"
    stage65a_closed = stage42.get("S42-STAGE65A-R4-UNROLLED", {}).get("status") == "PASS"
    stage66a_closed = (
        stage42.get("S42-STAGE66A-POST-VARIANT-FINAL-RECHECK", {}).get("status")
        == "PASS"
    )
    stage67_closed = (
        stage42.get("S42-STAGE67-FINAL-RECHECK-STAGE66", {}).get("status") == "PASS"
    )
    stage68_closed = (
        stage42.get("S42-STAGE68-FRONTIER-CLOSURE-CONSISTENCY", {}).get("status")
        == "PASS"
    )
    stage69_closed = (
        stage42.get("S42-STAGE69-LOCAL-VARIANT-FEASIBILITY", {}).get("status")
        == "PASS"
    )
    stage70_closed = (
        stage42.get("S42-STAGE70-EXTERNAL-UNLOCK-PREFLIGHT", {}).get("status")
        == "PASS"
    )
    stage71_closed = (
        stage42.get("S42-STAGE71-FINAL-RECHECK-STAGE70", {}).get("status")
        == "PASS"
    )
    stage72_closed = (
        stage42.get("S42-STAGE72-EXTERNAL-SOURCE-REFRESH", {}).get("status")
        == "PASS"
    )
    optional_notes = []
    if stage64a_closed:
        optional_notes.append("Stage64A post-variant refresh")
    if stage65a_closed:
        optional_notes.append("Stage65A optional negative variant")
    if stage66a_closed:
        optional_notes.append("Stage66A post-variant final recheck")
    if stage67_closed:
        optional_notes.append("Stage67 final-recheck Stage66A integration")
    if stage68_closed:
        optional_notes.append("Stage68 frontier/closure consistency")
    if stage69_closed:
        optional_notes.append("Stage69 local variant feasibility")
    if stage70_closed:
        optional_notes.append("Stage70 external unlock preflight")
    if stage71_closed:
        optional_notes.append("Stage71 final-recheck Stage70 integration")
    if stage72_closed:
        optional_notes.append("Stage72 external source refresh")
    optional_stage_note = " plus " + " and ".join(optional_notes) if optional_notes else ""
    spaced_stage_range = current_stage_range.replace("Stage", "Stage ")
    stage42_overall_detail = stage42.get("S42-OVERALL", {}).get("detail", "")
    stage42_matches_current_range = (
        current_stage_range in stage42_overall_detail
        or spaced_stage_range in stage42_overall_detail
        or stage42_overall == "PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED"
    )
    stage42_rebuildable = (
        stage42.get("S42-ROADMAP-STAGES", {}).get("status") == "PASS"
        and stage42.get("S42-CLAIM-GUARDRAILS", {}).get("status") == "PASS"
    )

    rows = [
        frontier_row(
            "G1",
            "local_engineering",
            "Scalar SAB baseline and explicit sab_pvw_* path remain separately auditable.",
            "LOCAL_READY" if audit_status(audit, "A5b") == "PASS_CURRENT_SMOKE" else "MISSING_LOCAL_EVIDENCE",
            audit_evidence(audit, "A5b"),
            "Current-commit smoke evidence exists; scalar path is preserved as the comparison baseline.",
            "Rerun current smoke after implementation changes.",
            "Supports scoped engineering continuity only.",
        ),
        frontier_row(
            "G2",
            "performance",
            "Complete SAB A/B throughput evidence exists for target binary r=2/r=4.",
            "LOCAL_READY"
            if audit_status(audit, "A2b") == "PASS_10RUN_TARGET_PERF" and stage50_ok
            else "MISSING_LOCAL_EVIDENCE",
            f"{audit_evidence(audit, 'A2b')}; {STAGE50.relative_to(ROOT).as_posix()}",
            "Stage36 remains the high-stat performance source and Stage50 verifies current-head continuity boundaries.",
            "Rerun Stage36/Stage49 only after code, backend, or platform changes.",
            "Supports scoped target complete-SAB performance wording.",
        ),
        frontier_row(
            "G3",
            "correctness_noise",
            "Final-output and stage-level noise/correctness evidence exists for target r=2/r=4.",
            "LOCAL_READY"
            if audit_status(audit, "A3c") == "PASS_TARGET_NOISE_50SEED"
            and audit_status(audit, "A3b") == "PASS_STAGE_NOISE_10SEED"
            else "MISSING_LOCAL_EVIDENCE",
            f"{audit_evidence(audit, 'A3c')}; {audit_evidence(audit, 'A3b')}",
            "Target final-output noise has 50-seed zero-failure support and stage-level noise has 10-seed support.",
            "Rerun noise gates after parameter, arithmetic, or key-format changes.",
            "Supports scoped target correctness/noise wording.",
        ),
        frontier_row(
            "G4",
            "resources",
            "Resource/key/time snapshots are available for scalar and PVW r=1/2/4.",
            "LOCAL_READY" if audit_status(audit, "A4b") == "PASS_RESOURCE_3RUN" else "MISSING_LOCAL_EVIDENCE",
            audit_evidence(audit, "A4b"),
            "Resource evidence is repeated enough for scoped reporting, with resource cost kept explicit.",
            "Rerun resource matrix after implementation or key-layout changes.",
            "Supports scoped resource reporting, not universal deployment claims.",
        ),
        frontier_row(
            "G5",
            "added_binary_generalization",
            "Added binary parameter evidence exists beyond SET_2_3_2048.",
            "LOCAL_SCOPED_READY"
            if audit_status(audit, "A7") == "PASS_ADDED_PARAM_10RUN_20SEED"
            else "MISSING_LOCAL_EVIDENCE",
            audit_evidence(audit, "A7"),
            "Added binary parameters have repeated performance/noise support; non-binary/all-parameter claims remain outside scope.",
            "Add separate branch coverage before claiming non-binary or all-parameter generality.",
            "Supports added-binary wording only.",
        ),
        frontier_row(
            "G6",
            "reproducibility",
            "Stage19+ evidence chain is machine-checked and registered.",
            "LOCAL_READY"
            if stage42_overall == "PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED"
            and stage42_matches_current_range
            else "LOCAL_REFRESH_PENDING"
            if stage42_rebuildable
            else "MISSING_LOCAL_EVIDENCE",
            STAGE42.relative_to(ROOT).as_posix(),
            f"Stage42 closure currently verifies the {current_stage_range} evidence chain{optional_stage_note} and preserves stronger-claim blockers.",
            "Extend closure/verifier whenever new stages or artifacts are added.",
            "Supports reproducibility of the scoped engineering chain.",
        ),
        frontier_row(
            "B1",
            "external_perf_theory",
            "MAT-AVX512 theoretical load/store/FMA attribution requires native hardware-counter evidence.",
            "EXTERNAL_BLOCKED" if "BLOCKED" in blocker_status(blockers, "CB5") else "REVIEW_REQUIRED",
            blockers.get("CB5", {}).get("evidence", ""),
            blocker_status(blockers, "CB5"),
            blockers.get("CB5", {}).get("unlock_command", ""),
            "Blocks theoretical MAT-AVX512 optimality or load/store-superiority claims.",
        ),
        frontier_row(
            "B2",
            "external_novelty",
            "Novelty and related-work distinction require full-text claim-to-source review.",
            "EXTERNAL_REVIEW_BLOCKED" if "BLOCKED" in blocker_status(blockers, "CB6") else "REVIEW_REQUIRED",
            blockers.get("CB6", {}).get("evidence", ""),
            blocker_status(blockers, "CB6"),
            blockers.get("CB6", {}).get("unlock_command", ""),
            "Blocks novelty wording beyond scoped engineering/systems contribution.",
        ),
        frontier_row(
            "B3",
            "external_2025_686_fulltext",
            "2025/686 theorem-level protocol/citation review requires a registered full text.",
            "EXTERNAL_FULLTEXT_BLOCKED" if "BLOCKED" in blocker_status(blockers, "CB7") else "REVIEW_REQUIRED",
            blockers.get("CB7", {}).get("evidence", ""),
            blocker_status(blockers, "CB7"),
            blockers.get("CB7", {}).get("unlock_command", ""),
            "Blocks theorem, algorithm, table, figure, or experiment-number claims from 2025/686.",
        ),
        frontier_row(
            "G9",
            "overall",
            "Original goal status under current evidence.",
            audit_status(audit, "A9"),
            audit_evidence(audit, "A9"),
            audit.get("A9", {}).get("scope", ""),
            audit.get("A9", {}).get("remaining_action", ""),
            "Goal remains active: scoped engineering chain is ready, stronger claims remain blocked.",
        ),
    ]
    return rows


def gate_status(rows: List[Dict[str, str]]) -> str:
    required_ready = ["G1", "G2", "G3", "G4", "G5", "G6"]
    required_blocked = ["B1", "B2", "B3"]
    by_id = {row["frontier_id"]: row for row in rows}
    ready_ok = all(by_id.get(fid, {}).get("status", "").startswith("LOCAL") for fid in required_ready)
    blocked_ok = all("BLOCKED" in by_id.get(fid, {}).get("status", "") for fid in required_blocked)
    overall_ok = (
        by_id.get("G9", {}).get("status")
        == "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    )
    if ready_ok and blocked_ok and overall_ok:
        return "PASS_GOAL_FRONTIER_SCOPED_READY_STRONGER_BLOCKED"
    return "FAIL_GOAL_FRONTIER_INCONSISTENT"


def write_csv(rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: List[Dict[str, str]]) -> List[str]:
    cols = ["frontier_id", "lane", "status", "completion_effect", "next_action"]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(col, "") for col in cols) + " |")
    return lines


def write_md(rows: List[Dict[str, str]]) -> None:
    decision = gate_status(rows)
    current_stage_range = latest_stage_label()
    lines = [
        "# Stage 51 Goal Completion Frontier",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 51 converts the current evidence state into an auditable frontier:",
        "what is locally ready for the scoped PVW/MAT-SAB engineering claim, and",
        "what still blocks stronger paper-level or theory-level claims. It is not",
        "a goal-complete declaration.",
        "",
        "## Frontier",
        "",
        f"- current closure range: `{current_stage_range}`",
        "",
        *md_table(rows),
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "The active goal remains open because the scoped engineering acceleration",
        "chain is ready, but external native perf evidence, full-text 2025/686",
        "review, and novelty claim review remain unresolved.",
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
    print(f"Stage 51 goal frontier: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
