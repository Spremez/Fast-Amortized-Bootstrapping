#!/usr/bin/env python3
"""Build the Stage 59 completion-route readiness table.

Stage 59 does not upgrade the PVW/MAT-SAB claim. It codifies the remaining
route after the Stage 58 closure: which lanes are already locally evidenced,
which lanes are local refreshes after future code changes, and which lanes are
blocked on external native-perf/full-text/manual-review inputs.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "repro" / "stage51_goal_completion_frontier.csv"
UNLOCK = ROOT / "repro" / "stage52_external_unlock_readiness.csv"
BLOCKERS = ROOT / "repro" / "remaining_blocker_dashboard.csv"
PERF_MATRIX = ROOT / "repro" / "stage50_performance_evidence_matrix.csv"
OUT_CSV = ROOT / "repro" / "stage59_completion_route_readiness.csv"
OUT_MD = ROOT / "docs" / "stage59_completion_route_readiness.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def route_row(
    route_id: str,
    planned_stage: str,
    lane: str,
    status: str,
    evidence: str,
    gate: str,
    next_action: str,
    claim_effect: str,
) -> Dict[str, str]:
    return {
        "route_id": route_id,
        "planned_stage": planned_stage,
        "lane": lane,
        "status": status,
        "evidence": evidence,
        "gate": gate,
        "next_action": next_action,
        "claim_effect": claim_effect,
    }


def status_of(rows: Dict[str, Dict[str, str]], row_id: str, field: str = "status") -> str:
    return rows.get(row_id, {}).get(field, "MISSING")


def perf_ready(perf_rows: List[Dict[str, str]]) -> bool:
    by_id = {row.get("evidence_id"): row for row in perf_rows}
    required = [
        "stage36_target_perf_r2",
        "stage36_target_perf_r4",
        "stage49_current_head_repeated_r2",
        "stage49_current_head_repeated_r4",
    ]
    return all(by_id.get(item, {}).get("status") == "PASS" for item in required)


def build_rows() -> List[Dict[str, str]]:
    frontier = by_key(FRONTIER, "frontier_id")
    unlock = by_key(UNLOCK, "unlock_id")
    blockers = by_key(BLOCKERS, "blocker_id")
    perf_rows = read_csv(PERF_MATRIX)

    local_ready = all(
        status_of(frontier, row_id).startswith("LOCAL")
        for row_id in ["G1", "G2", "G3", "G4", "G5", "G6"]
    )
    perf_ok = perf_ready(perf_rows)
    native_perf_waiting = status_of(unlock, "S52-NATIVE-PERF", "readiness") == "WAIT_NATIVE_PERF"
    fulltext_waiting = (
        status_of(unlock, "S52-FULLTEXT-686", "readiness") == "WAIT_EXTERNAL_FULLTEXT"
    )
    novelty_waiting = (
        status_of(unlock, "S52-NOVELTY-REVIEW", "readiness")
        == "WAIT_MANUAL_FULLTEXT_REVIEW"
    )
    final_waiting = status_of(unlock, "S52-FINAL-RECHECK", "readiness") == "WAIT_UNLOCKS"

    rows = [
        route_row(
            "S59-R1-SCOPED-ENGINEERING",
            "current",
            "local scoped engineering evidence",
            "LOCAL_READY" if local_ready and perf_ok else "MISSING_LOCAL_EVIDENCE",
            (
                "repro/stage51_goal_completion_frontier.csv; "
                "repro/stage50_performance_evidence_matrix.csv"
            ),
            "G1-G6 must start with LOCAL and Stage50 target/current-head rows must pass.",
            "After future implementation changes, rerun Stage33/36/49/50/51/52/57/42 as needed.",
            "Supports only the scoped engineering acceleration claim.",
        ),
        route_row(
            "S59-R2-CURRENT-HEAD-REFRESH",
            "next local refresh",
            "current-head correctness/performance continuity",
            "READY_LOCAL_REFRESH" if local_ready else "WAIT_LOCAL_EVIDENCE",
            (
                "repro/stage33_current_smoke/summary.csv; "
                "repro/stage49_wsl_repeated_full_sab/summary.csv; "
                "repro/stage64_post_variant_refresh/summary.csv; "
                "repro/stage66_post_variant_final_recheck/summary.csv; "
                "repro/stage67_final_recheck_stage66/summary.csv"
            ),
            "Current-head smoke/repeated full-SAB continuity must pass after code or backend changes.",
            "Stage64A, Stage66A, and Stage67 passed after Stage65A; rerun Stage64A, Stage66A, and Stage67 before claiming continuity for any future implementation change.",
            "Can refresh continuity wording; does not replace Stage36 high-stat evidence.",
        ),
        route_row(
            "S59-R3-NATIVE-PERF",
            "external unlock",
            "MAT-AVX512 hardware-counter attribution",
            "EXTERNAL_BLOCKED" if native_perf_waiting else "REVIEW_REQUIRED",
            blockers.get("CB5", {}).get("evidence", ""),
            unlock.get("S52-NATIVE-PERF", {}).get("acceptance_gate", ""),
            unlock.get("S52-NATIVE-PERF", {}).get("command", ""),
            "Blocks theoretical load/store/FMA optimality claims.",
        ),
        route_row(
            "S59-R4-FULLTEXT-686",
            "external unlock",
            "2025/686 theorem/protocol source review",
            "EXTERNAL_FULLTEXT_BLOCKED" if fulltext_waiting else "REVIEW_REQUIRED",
            blockers.get("CB7", {}).get("evidence", ""),
            unlock.get("S52-FULLTEXT-686", {}).get("acceptance_gate", ""),
            unlock.get("S52-FULLTEXT-686", {}).get("command", ""),
            "Blocks theorem, algorithm, table, figure, and experiment-number claims from 2025/686.",
        ),
        route_row(
            "S59-R5-NOVELTY-REVIEW",
            "manual review",
            "novelty and related-work distinction",
            "EXTERNAL_REVIEW_BLOCKED" if novelty_waiting else "REVIEW_REQUIRED",
            blockers.get("CB6", {}).get("evidence", ""),
            unlock.get("S52-NOVELTY-REVIEW", {}).get("acceptance_gate", ""),
            unlock.get("S52-NOVELTY-REVIEW", {}).get("command", ""),
            "Blocks novelty wording beyond scoped engineering/systems evidence.",
        ),
        route_row(
            "S59-R6-OPTIONAL-VARIANTS",
            "optional local expansion",
            "future algorithmic variants",
            "READY_OPTIONAL_LOCAL_TRIAGE",
            (
                "repro/stage39_optional_variant_triage.csv; "
                "hypotheses/hypothesis_register.yaml; "
                "repro/stage65_r4_unrolled_avx512/summary.csv; "
                "repro/stage69_local_variant_feasibility.csv; "
                "repro/stage74_r_scaling_boundary/decision.csv; "
                "repro/stage75_rgt4_profile_boundary/decision.csv; "
                "repro/stage76_rgt4_kernel_feasibility/summary.csv; "
                "repro/stage77_rgt4_fused_mat_kernel/summary.csv; "
                "repro/stage78_rgt4_fused_repeated_gates/summary.csv"
            ),
            "Each variant must enter the loop as promote/neutral/reject with full correctness gates.",
            "Stage78 makes H11 r=6 a promotion candidate: repeated full-SAB, final-output noise, and resource gates pass under the explicit fused r>4 flag. Next local work is Stage79 high-stat confirmation before any default/path promotion or claim upgrade.",
            "May improve engineering evidence; no claim upgrade without high-stat confirmation and current-head refresh.",
        ),
        route_row(
            "S59-R7-FINAL-PAPER-PACKAGE",
            "final freeze",
            "paper/release claim package",
            "WAIT_STRONGER_UNLOCKS" if final_waiting else "REVIEW_REQUIRED",
            "repro/stage52_external_unlock_readiness.csv; repro/remaining_blocker_dashboard.csv",
            "A9 may move only after CB5/CB6/CB7 are resolved or the scope is explicitly narrowed.",
            "Run final recheck and Stage40-style freeze after external unlocks and manual claim review.",
            "Keeps the active goal open under current evidence.",
        ),
    ]
    return rows


def decision(rows: List[Dict[str, str]]) -> str:
    by_id = {row["route_id"]: row for row in rows}
    expected = {
        "S59-R1-SCOPED-ENGINEERING": "LOCAL_READY",
        "S59-R2-CURRENT-HEAD-REFRESH": "READY_LOCAL_REFRESH",
        "S59-R3-NATIVE-PERF": "EXTERNAL_BLOCKED",
        "S59-R4-FULLTEXT-686": "EXTERNAL_FULLTEXT_BLOCKED",
        "S59-R5-NOVELTY-REVIEW": "EXTERNAL_REVIEW_BLOCKED",
        "S59-R6-OPTIONAL-VARIANTS": "READY_OPTIONAL_LOCAL_TRIAGE",
        "S59-R7-FINAL-PAPER-PACKAGE": "WAIT_STRONGER_UNLOCKS",
    }
    ok = all(by_id.get(route_id, {}).get("status") == status for route_id, status in expected.items())
    if ok:
        return "PASS_COMPLETION_ROUTE_READY__STRONGER_CLAIMS_BLOCKED"
    return "FAIL_COMPLETION_ROUTE_INCONSISTENT"


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "route_id",
                "planned_stage",
                "lane",
                "status",
                "evidence",
                "gate",
                "next_action",
                "claim_effect",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: List[Dict[str, str]], gate: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Stage 59 Completion Route Readiness\n\n")
        f.write(
            "Stage 59 turns the post-Stage58 state into an explicit route to "
            "completion. It does not modify SAB code and does not upgrade "
            "the scoped engineering claim.\n\n"
        )
        f.write("| route_id | planned_stage | lane | status | next_action |\n")
        f.write("|---|---|---|---|---|\n")
        for row in rows:
            f.write(
                "| {route_id} | {planned_stage} | {lane} | {status} | {next_action} |\n".format(
                    **{k: row[k].replace("|", "\\|") for k in row}
                )
            )
        f.write("\n")
        f.write(f"Decision: `{gate}`\n\n")
        f.write(
            "Interpretation: local scoped engineering evidence remains ready, "
            "while stronger MAT-AVX512 theory, novelty, and theorem-level "
            "2025/686 claims remain blocked until the external gates in "
            "`repro/stage52_external_unlock_readiness.csv` are satisfied.\n"
        )


def main() -> int:
    rows = build_rows()
    gate = decision(rows)
    write_csv(OUT_CSV, rows)
    write_md(OUT_MD, rows, gate)
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    print(f"Stage 59 completion route readiness: {gate}")
    return 0 if gate.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
