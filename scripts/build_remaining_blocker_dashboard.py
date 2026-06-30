#!/usr/bin/env python3
"""Build a dashboard for remaining stronger-claim blockers.

This dashboard aggregates the current scoped-ready state, conditional backlog,
external unlock packet, Stage 44 re-probe, Stage 55 external paper probe, and
related-work access probe. Stage72 adds a current external-source refresh. It
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
STAGE55 = ROOT / "repro" / "stage55_external_paper_probe" / "summary.csv"
STAGE72 = ROOT / "repro" / "stage72_external_source_refresh" / "summary.csv"
RELATED = ROOT / "repro" / "stage27_related_work_access_probe" / "summary.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
STAGE101 = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "summary.csv"
STAGE102 = ROOT / "repro" / "stage102_686_source_anchor_review" / "summary.csv"
STAGE103 = ROOT / "repro" / "stage103_related_work_novelty_review" / "summary.csv"


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
    stage55 = read_csv(STAGE55)
    stage72 = read_csv(STAGE72)
    related = read_csv(RELATED)
    external = read_csv(EXTERNAL)
    stage101 = read_csv(STAGE101)
    stage102 = read_csv(STAGE102)
    stage103 = read_csv(STAGE103)

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
    stage55_fulltext = by_key(stage55, "gate", "official_fulltext_pdf_access").get("status", "MISSING")
    stage55_metadata = by_key(stage55, "gate", "crossref_doi_metadata").get("status", "MISSING")
    stage55_decision = by_key(stage55, "gate", "stage55_decision").get("status", "MISSING")
    stage72_fulltext = by_key(stage72, "gate", "stage72_official_fulltext_routes").get("status", "MISSING")
    stage72_author = by_key(stage72, "gate", "stage72_author_metadata_route").get("status", "MISSING")
    stage72_decision = by_key(stage72, "gate", "stage72_decision").get("status", "MISSING")

    related_decision = by_key(related, "gate", "related_work_decision").get("status", "MISSING")
    related_novelty = by_key(related, "gate", "novelty_claim_gate").get("status", "MISSING")
    related_fulltext = by_key(related, "gate", "base_2025_686_fulltext").get("status", "MISSING")

    fulltext_external = by_key(external, "evidence_id", "fab686_fulltext").get("status", "MISSING")
    perf_external = by_key(external, "evidence_id", "stage28_native_perf_summary").get("status", "MISSING")
    stage101_decision = by_key(stage101, "gate", "stage101_cb5_decision").get("status", "MISSING")
    stage102_decision = by_key(stage102, "gate", "stage102_decision").get("status", "MISSING")
    stage103_decision = by_key(stage103, "gate", "stage103_decision").get("status", "MISSING")
    fulltext_registered = (
        a8b == "EXTERNAL_EVIDENCE_AVAILABLE_REVIEW_REQUIRED"
        or a8b == "PASS_EXTERNAL_EVIDENCE_REVIEWED"
        or fulltext_external == "AVAILABLE_UNREVIEWED"
    )
    cb7_condition = (
        "A 2025/686 full-text artifact is registered and hashed, but manual claim-to-source review is still incomplete."
        if fulltext_registered
        else "The 2025/686 DOI/author metadata is available, but the full text is not registered or accessible through current direct routes."
    )
    cb7_unlock = (
        "Complete repro/stage38_fulltext_review_gate/review_checklist.csv with concrete paper anchors."
        if fulltext_registered
        else "FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf bash scripts/run_stage38_fulltext_review_gate.sh"
    )
    cb5_resolved = stage101_decision == "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED"
    cb6_resolved = stage103_decision == "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED"
    cb7_resolved = stage102_decision == "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED"

    return [
        row(
            "CB5",
            "MAT-AVX512 theoretical load/store/FMA attribution",
            f"final_A8={a8}; cb5={cb5.get('status', 'MISSING')}; stage101={stage101_decision}; external_perf={perf_external}",
            "Resolved by Stage101 native Linux perf run; theoretical-optimality wording is still interpretation-gated."
            if cb5_resolved
            else "Native Linux/perf hardware-counter evidence is not available in the current WSL2 environment.",
            f"{rel(FINAL_AUDIT)}; {rel(CONDITIONAL)}; {rel(STAGE101)}; {rel(EXTERNAL)}",
            "python scripts/build_stage101_cb5_remote_native_perf.py",
            s41_perf.get("review_gate", "Compare counters with Stage 22 specialized/generic timing before any claim upgrade."),
            "Do not claim theoretical MAT-AVX512 optimality or load/store superiority without native/perf evidence and manual interpretation.",
        ),
        row(
            "CB6",
            "Novelty and related-work distinction",
            f"cb6={cb6.get('status', 'MISSING')}; stage103={stage103_decision}; related={related_decision}; novelty_gate={related_novelty}",
            "Resolved by Stage103 scoped novelty review; broad shared-mask, batch/SIMD, new-asymptotic, and all-parameter claims remain blocked."
            if cb6_resolved
            else "Related-work source access is refreshed, but manual full-text claim-to-source review is still missing.",
            f"{rel(CONDITIONAL)}; {rel(STAGE103)}; {rel(RELATED)}; {rel(STAGE55)}; {rel(STAGE72)}",
            "python scripts/build_stage103_related_work_novelty_review.py",
            "Use only the Stage103 allowed wording unless a later theorem and full literature review justify stronger claims.",
            "Use scoped engineering/systems wording; broad novelty claims remain blocked by Stage103.",
        ),
        row(
            "CB7",
            "2025/686 theorem-level protocol and citation review",
            f"final_A8b={a8b}; cb7={cb7.get('status', 'MISSING')}; stage102={stage102_decision}; external_fulltext={fulltext_external}; stage55_metadata={stage55_metadata}; stage72_author={stage72_author}",
            "Resolved by Stage102 verified 2025/686 source anchors; PVW/MAT statements still require local evidence and claim limits."
            if cb7_resolved
            else cb7_condition,
            f"{rel(FINAL_AUDIT)}; {rel(CONDITIONAL)}; {rel(STAGE102)}; {rel(STAGE55)}; {rel(STAGE72)}; {rel(EXTERNAL)}",
            "python scripts/build_stage102_686_source_anchor_review.py" if cb7_resolved else cb7_unlock,
            s41_fulltext.get("review_gate", "Map protocol stages, complexity formulas, and assumptions to concrete source anchors."),
            "Use only reviewed Stage102 anchors and pair PVW/MAT claims with local implementation evidence.",
        ),
        row(
            "A9",
            "Overall final decision",
            f"final_A9={a9}; stage44_decision={stage44_decision}; stage41_final={s41_final.get('readiness', 'MISSING')}",
            "Former external blockers are resolved; remaining limits are claim-scope limits, not missing-evidence blockers."
            if all([cb5_resolved, cb6_resolved, cb7_resolved])
            else "The scoped engineering chain is ready, but stronger claims remain blocked by the rows above.",
            f"{rel(FINAL_AUDIT)}; {rel(STAGE101)}; {rel(STAGE102)}; {rel(STAGE103)}; {rel(OUT_CSV)}",
            "python scripts/build_final_goal_completion_audit.py",
            "Only upgrade beyond scoped systems claims after new theorem/literature/performance evidence.",
            "Final status may be scoped-reviewed; claims beyond scoped engineering remain blocked without new evidence.",
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
            "The project remains scoped to engineering/systems claims. Stage101,",
            "Stage102, and Stage103 resolve the previous external evidence/review",
            "blockers; remaining limits are deliberate claim-scope boundaries, not",
            "missing local SAB implementation work.",
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
