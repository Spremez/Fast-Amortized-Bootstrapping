#!/usr/bin/env python3
"""Build the Stage 41 external-unlock packet.

Stage 41 does not upgrade claims. It records the exact external evidence and
manual review gates needed to move beyond the current scoped engineering SAB
acceleration result.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro" / "stage41_external_unlock_packet.csv"
OUT_MD = ROOT / "docs" / "stage41_external_unlock_packet.md"

FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
BLOCKERS = ROOT / "repro" / "stage35_completion_blockers.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
STAGE37 = ROOT / "repro" / "stage37_native_perf_counter_audit" / "summary.csv"
STAGE38 = ROOT / "repro" / "stage38_fulltext_review_gate" / "summary.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def row_by(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def status(rows: List[Dict[str, str]], key: str, value: str, field: str = "status") -> str:
    return row_by(rows, key, value).get(field, "MISSING")


def build_rows() -> List[Dict[str, str]]:
    audit = read_csv(FINAL_AUDIT)
    blockers = read_csv(BLOCKERS)
    external = read_csv(EXTERNAL)
    stage37 = read_csv(STAGE37)
    stage38 = read_csv(STAGE38)

    a8 = status(audit, "item_id", "A8")
    a8b = status(audit, "item_id", "A8b")
    a9 = status(audit, "item_id", "A9")
    fulltext = status(external, "evidence_id", "fab686_fulltext")
    native_perf = status(external, "evidence_id", "stage28_native_perf_summary")
    stage37_decision = status(stage37, "item", "stage37_decision")
    stage38_decision = status(stage38, "item", "stage38_decision")
    fulltext_blocker = status(blockers, "item_id", "A8b")
    perf_blocker = status(blockers, "item_id", "A8")

    fulltext_ready = fulltext == "AVAILABLE_UNREVIEWED"
    perf_ready = native_perf == "PASS_COUNTER_ATTRIBUTION_AVAILABLE"

    return [
        {
            "unlock_id": "S41-FULLTEXT-INTAKE",
            "claim_lane": "2025/686 theorem-level protocol and citation review",
            "current_status": f"external={fulltext}; stage38={stage38_decision}; audit_A8b={a8b}",
            "readiness": "READY_FOR_MANUAL_REVIEW" if fulltext_ready else "WAIT_EXTERNAL_FULLTEXT",
            "required_evidence": "Recognized PDF/text artifact for 2025/686 with path, size, and SHA-256 recorded.",
            "command": "FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf bash scripts/run_stage38_fulltext_review_gate.sh",
            "review_gate": "Map protocol stages, complexity formulas, noise/security assumptions, and PVW-SAB delta to concrete page or section anchors.",
            "claim_policy": "No theorem, algorithm, table, figure, or novelty wording may be upgraded until manual review replaces blocked checklist rows.",
        },
        {
            "unlock_id": "S41-NATIVE-PERF-INTAKE",
            "claim_lane": "MAT-AVX512 load/store/FMA attribution",
            "current_status": f"external={native_perf}; stage37={stage37_decision}; audit_A8={a8}",
            "readiness": "READY_FOR_PERF_INTERPRETATION" if perf_ready else "WAIT_NATIVE_PERF",
            "required_evidence": "Stage 28 summary.csv from native Linux or perf-enabled WSL with hardware_counter_gate=PASS.",
            "command": "STAGE28_RUN_BENCH=1 bash scripts/run_stage28_native_perf_counter_gate.sh",
            "review_gate": "Compare cycles, instructions, cache counters, objdump evidence, and Stage 22 specialized/generic timing.",
            "claim_policy": "Do not claim theoretical MAT-AVX512 optimality or load/store superiority from current WSL2 proxy evidence.",
        },
        {
            "unlock_id": "S41-EXTERNAL-REGISTRATION",
            "claim_lane": "external evidence intake",
            "current_status": f"A8={perf_blocker}; A8b={fulltext_blocker}",
            "readiness": "READY_TO_REGISTER" if fulltext_ready or perf_ready else "WAIT_EXTERNAL_ARTIFACTS",
            "required_evidence": "Full-text path and/or native Stage 28 summary path supplied through environment variables.",
            "command": "FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf STAGE28_NATIVE_PERF_SUMMARY=/path/to/summary.csv python scripts/register_external_evidence.py",
            "review_gate": "Registered hashes are intake evidence only; manual interpretation remains required.",
            "claim_policy": "Registration alone changes status to review-required, not paper-ready.",
        },
        {
            "unlock_id": "S41-FINAL-RECHECK",
            "claim_lane": "overall final goal audit",
            "current_status": f"audit_A9={a9}",
            "readiness": "READY_AFTER_UNLOCKS" if fulltext_ready or perf_ready else "WAIT_UNLOCKS",
            "required_evidence": "Updated external intake, Stage 38/Stage 28 outputs, and regenerated final audit.",
            "command": "FINAL_RECHECK_CITATION=1 FINAL_RECHECK_PERF=1 FINAL_RECHECK_EXTERNAL_INTAKE=1 bash scripts/run_final_goal_recheck.sh",
            "review_gate": "A9 may only move beyond scoped-ready after A8/A8b are no longer blocked and claim wording is manually checked.",
            "claim_policy": "Keep SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED until all stronger-claim rows have direct evidence.",
        },
    ]


def write_csv(rows: List[Dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "unlock_id",
        "claim_lane",
        "current_status",
        "readiness",
        "required_evidence",
        "command",
        "review_gate",
        "claim_policy",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage 41 External Unlock Packet",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 41 turns the remaining external blockers into executable gates.",
        "It does not change scalar SAB, the promoted `sab_pvw_*` path, or any",
        "claim label by itself. It records what must be supplied and reviewed",
        "before the project can move beyond the current scoped engineering result.",
        "",
        "## Unlock Matrix",
        "",
        "| unlock | readiness | current status | command | review gate |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['unlock_id']} | {row['readiness']} | {row['current_status']} | "
            f"`{row['command']}` | {row['review_gate']} |"
        )

    lines.extend(
        [
            "",
            "## Claim Policy",
            "",
        ]
    )
    for row in rows:
        lines.append(f"- `{row['unlock_id']}`: {row['claim_policy']}")

    lines.extend(
        [
            "",
            "## Current Decision",
            "",
            "The local engineering evidence chain remains frozen as scoped-ready.",
            "The next meaningful upgrades require external full text and/or",
            "native perf evidence, followed by manual interpretation and a final",
            "goal recheck.",
            "",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = build_rows()
    write_csv(rows)
    write_md(rows)
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
