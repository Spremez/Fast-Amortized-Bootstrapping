#!/usr/bin/env python3
"""Build a dashboard for remaining stronger-claim blockers.

This dashboard aggregates the current scoped-ready state, conditional backlog,
external unlock packet, Stage 44 re-probe, and related-work access probe. It
does not change SAB code and does not upgrade any claim.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro" / "remaining_blocker_dashboard.csv"
OUT_MD = ROOT / "docs" / "remaining_blocker_dashboard.md"

FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
CONDITIONAL = ROOT / "repro" / "conditional_backlog_audit.csv"
STAGE41 = ROOT / "repro" / "stage41_external_unlock_packet.csv"
STAGE44 = ROOT / "repro" / "stage44_external_unlock_reprobe" / "summary.csv"
RELATED = ROOT / "repro" / "stage27_related_work_access_probe" / "summary.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def by_key(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def row(
    blocker_id: str,
    claim_lane: str,
    current_status: str,
    blocking_condition: str,
    evidence: str,
    unlock_command: str,
    review_gate: str,
    claim_policy: str,
) -> Dict[str, str]:
    return {
        "blocker_id": blocker_id,
        "claim_lane": claim_lane,
        "current_status": current_status,
        "blocking_condition": blocking_condition,
        "evidence": evidence,
        "unlock_command": unlock_command,
        "review_gate": review_gate,
        "claim_policy": claim_policy,
    }


def build_rows() -> List[Dict[str, str]]:
    final = read_csv(FINAL_AUDIT)
    conditional = read_csv(CONDITIONAL)
    stage41 = read_csv(STAGE41)
    stage44 = read_csv(STAGE44)
    related = read_csv(RELATED)
    external = read_csv(EXTERNAL)

    a8 = by_key(final, "item_id", "A8").get("status", "MISSING")
    a8b = by_key(final, "item_id", "A8b").get("status", "MISSING")
    a9 = by_key(final, "item_id", "A9").get("status", "MISSING")

    cb5 = by_key(conditional, "item_id", "CB5")
    cb6 = by_key(conditional, "item_id", "CB6")
    cb7 = by_key(conditional, "item_id", "CB7")

    s41_perf = by_key(stage41, "unlock_id", "S41-NATIVE-PERF-INTAKE")
    s41_fulltext = by_key(stage41, "unlock_id", "S41-FULLTEXT-INTAKE")
    s41_final = by_key(stage41, "unlock_id", "S41-FINAL-RECHECK")

    stage44_perf = by_key(stage44, "item", "native_perf_hardware_counter_gate").get("status", "MISSING")
    stage44_fulltext = by_key(stage44, "item", "fulltext_pdf_access").get("status", "MISSING")
    stage44_decision = by_key(stage44, "item", "stage44_decision").get("status", "MISSING")

    related_decision = by_key(related, "gate", "related_work_decision").get("status", "MISSING")
    related_novelty = by_key(related, "gate", "novelty_claim_gate").get("status", "MISSING")
    related_fulltext = by_key(related, "gate", "base_2025_686_fulltext").get("status", "MISSING")

    fulltext_external = by_key(external, "evidence_id", "fab686_fulltext").get("status", "MISSING")
    perf_external = by_key(external, "evidence_id", "stage28_native_perf_summary").get("status", "MISSING")

    return [
        row(
            "CB5",
            "MAT-AVX512 theoretical load/store/FMA attribution",
            f"final_A8={a8}; cb5={cb5.get('status', 'MISSING')}; stage44_perf={stage44_perf}; external_perf={perf_external}",
            "Native Linux/perf hardware-counter evidence is not available in the current WSL2 environment.",
            f"{rel(FINAL_AUDIT)}; {rel(CONDITIONAL)}; {rel(STAGE44)}; {rel(EXTERNAL)}",
            "STAGE28_RUN_BENCH=1 bash scripts/run_stage28_native_perf_counter_gate.sh",
            s41_perf.get("review_gate", "Compare counters with Stage 22 specialized/generic timing before any claim upgrade."),
            "Do not claim theoretical MAT-AVX512 optimality or load/store superiority without native/perf evidence and manual interpretation.",
        ),
        row(
            "CB6",
            "Novelty and related-work distinction",
            f"cb6={cb6.get('status', 'MISSING')}; related={related_decision}; novelty_gate={related_novelty}",
            "Related-work source access is refreshed, but manual full-text claim-to-source review is still missing.",
            f"{rel(CONDITIONAL)}; {rel(RELATED)}; {rel(STAGE41)}",
            "FINAL_RECHECK_RELATED_WORK=1 bash scripts/run_final_goal_recheck.sh",
            "Manually map each novelty/distinction sentence to full-text anchors before upgrading novelty wording.",
            "Keep the contribution framed as scoped engineering/systems evidence until novelty review is complete.",
        ),
        row(
            "CB7",
            "2025/686 theorem-level protocol and citation review",
            f"final_A8b={a8b}; cb7={cb7.get('status', 'MISSING')}; stage44_fulltext={stage44_fulltext}; related_fulltext={related_fulltext}; external_fulltext={fulltext_external}",
            "The 2025/686 full text is not registered or accessible through current direct routes.",
            f"{rel(FINAL_AUDIT)}; {rel(CONDITIONAL)}; {rel(STAGE44)}; {rel(RELATED)}; {rel(EXTERNAL)}",
            "FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf bash scripts/run_stage38_fulltext_review_gate.sh",
            s41_fulltext.get("review_gate", "Map protocol stages, complexity formulas, and assumptions to concrete source anchors."),
            "Do not cite theorem, algorithm, table, figure, or experiment numbers from 2025/686 until full text is supplied and reviewed.",
        ),
        row(
            "A9",
            "Overall final decision",
            f"final_A9={a9}; stage44_decision={stage44_decision}; stage41_final={s41_final.get('readiness', 'MISSING')}",
            "The scoped engineering chain is ready, but stronger claims remain blocked by the rows above.",
            f"{rel(FINAL_AUDIT)}; {rel(STAGE41)}; {rel(STAGE44)}; {rel(OUT_CSV)}",
            "FINAL_RECHECK_CITATION=1 FINAL_RECHECK_RELATED_WORK=1 FINAL_RECHECK_STAGE44_REPROBE=1 bash scripts/run_final_goal_recheck.sh",
            s41_final.get("review_gate", "Only upgrade A9 after external evidence and manual claim review."),
            "Keep `SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED` until CB5/CB6/CB7 are resolved or the goal scope is explicitly narrowed.",
        ),
    ]


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Remaining Blocker Dashboard",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "This dashboard aggregates the remaining stronger-claim blockers after the",
        "scoped PVW/MAT-SAB engineering evidence chain has closed. It is a",
        "reproducibility/control-plane artifact only: it does not change scalar",
        "SAB, `sab_pvw_*`, benchmark results, or claim labels.",
        "",
        "## Dashboard",
        "",
        "| blocker | status | blocking condition | unlock command | claim policy |",
        "|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| {item['blocker_id']} | {item['current_status']} | "
            f"{item['blocking_condition']} | `{item['unlock_command']}` | "
            f"{item['claim_policy']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The project remains in the scoped engineering-ready state. The remaining",
            "work is external evidence and manual review for stronger claims, not a",
            "local SAB implementation blocker.",
            "",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    print(f"Remaining blocker dashboard: {rel(OUT_CSV)}")
    print(f"Remaining blocker log: {rel(OUT_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
