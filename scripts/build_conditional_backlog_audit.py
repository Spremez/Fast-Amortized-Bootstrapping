#!/usr/bin/env python3
"""Build an audit for conditional checklist items.

The reproduction checklist intentionally kept several early-stage follow-ups as
"if promoted" or "if justified" items. Later stages now provide enough evidence
to decide that those conditions are not active under the current promoted
PVW/MAT-SAB path. This script records that decision without upgrading any
external or paper-level claim.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro" / "conditional_backlog_audit.csv"
OUT_MD = ROOT / "docs" / "conditional_backlog_audit.md"


ROWS: List[Dict[str, str]] = [
    {
        "item_id": "CB1",
        "checklist_item": "Add Stage 12 v2 three-process full SAB sweep if the variant remains worth promoting.",
        "status": "CONDITION_NOT_ACTIVE",
        "evidence": "docs/stage12_avx512_gate_and_v2_kernel_log.md; repro/stage12_avx512_v2_summary.csv; repro/stage39_variant_triage.csv",
        "rationale": (
            "Stage 12 v2 remained kernel/smoke evidence, while the later promoted "
            "path is active-buffer plus specialized MAT-AVX512. Stage 39 records "
            "no new variant promoted currently."
        ),
        "next_gate": "Reopen only if a new Stage 12-derived variant is explicitly selected for full-SAB promotion.",
    },
    {
        "item_id": "CB2",
        "checklist_item": "Add Stage 12 v2 noise/seed gate if promoted beyond kernel experiment.",
        "status": "CONDITION_NOT_ACTIVE",
        "evidence": "docs/stage12_avx512_gate_and_v2_kernel_log.md; repro/stage12_avx512_v2_summary.csv; repro/stage39_variant_triage.csv",
        "rationale": (
            "The Stage 12 v2 path was not promoted beyond kernel/smoke evidence, "
            "so its seed/noise gate is not required for the current scoped claim."
        ),
        "next_gate": "Run seed/noise gates only after a Stage 12-derived candidate is promoted by full-SAB A/B evidence.",
    },
    {
        "item_id": "CB3",
        "checklist_item": "Add Stage 13 direct extraction three-process full SAB sweep only if promoted beyond cleanup.",
        "status": "CONDITION_NOT_ACTIVE",
        "evidence": "docs/stage13_postproc_profile_log.md; repro/stage13_postproc_summary.csv; docs/stage24_postproc_tail_log.md; repro/stage39_variant_triage.csv",
        "rationale": (
            "Direct extraction stayed as a cleanup/profile-supported path. Stage 24 "
            "then measured the promoted path's post-processing tail below the "
            "implementation threshold, and Stage 39 deferred direct post-processing."
        ),
        "next_gate": "Reopen only if a new body optimization raises post-processing tail above the Stage 24 threshold.",
    },
    {
        "item_id": "CB4",
        "checklist_item": "Implement PVW-aware direct-to-packing KS only if the measured tail justifies the complexity.",
        "status": "CONDITION_NOT_ACTIVE",
        "evidence": "docs/stage24_postproc_tail_log.md; repro/stage24_postproc_tail_avx512_runs1/summary.csv; repro/stage39_variant_triage.csv",
        "rationale": (
            "Stage 24 max tail was 1.261195%, below the 2.0% implementation "
            "threshold. Stage 39 records S39-DIRECT-POSTPROC as DEFER_TAIL_SMALL."
        ),
        "next_gate": "Do not implement until a refreshed profile crosses the tail threshold.",
    },
    {
        "item_id": "CB5",
        "checklist_item": "Re-run Stage 22 hardware perf-counter attribution on native Linux if a theoretical load/store claim is needed.",
        "status": "BLOCKED_EXTERNAL",
        "evidence": "docs/stage37_native_perf_counter_log.md; repro/stage37_native_perf_counter_audit/summary.csv; repro/final_goal_completion_audit.csv",
        "rationale": (
            "The current WSL2 environment lacks perf hardware-counter access. "
            "Final audit A8 remains BLOCKED_EXTERNAL."
        ),
        "next_gate": "Run Stage 37/Stage 28 on native Linux or perf-enabled WSL and register the resulting summary.",
    },
    {
        "item_id": "CB6",
        "checklist_item": "Review full related-work papers before promoting any novelty claim.",
        "status": "BLOCKED_EXTERNAL_REVIEW",
        "evidence": "docs/stage27_novelty_paper_package_log.md; docs/stage38_fulltext_review_log.md; repro/final_goal_completion_audit.csv",
        "rationale": (
            "The scoped engineering claim is ready, but novelty wording still "
            "requires full related-work and base-paper review."
        ),
        "next_gate": "Supply full texts and run the manual claim-to-source review before any novelty upgrade.",
    },
    {
        "item_id": "CB7",
        "checklist_item": "Obtain and inspect full 2025/686 paper before theorem-level manuscript citations.",
        "status": "BLOCKED_EXTERNAL_FULLTEXT",
        "evidence": "docs/stage38_fulltext_review_log.md; repro/stage38_fulltext_review_gate/summary.csv; repro/final_goal_completion_audit.csv",
        "rationale": (
            "No FAB686_FULLTEXT_PATH has been supplied. Final audit A8b remains "
            "MISSING_OPTIONAL_EXTERNAL_EVIDENCE."
        ),
        "next_gate": "Set FAB686_FULLTEXT_PATH to the paper PDF/text artifact and rerun Stage 38.",
    },
]


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["item_id", "checklist_item", "status", "evidence", "rationale", "next_gate"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Conditional Backlog Audit",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "This audit resolves conditional reproduction-checklist items whose",
        "execution depended on later promotion, profile thresholds, or external",
        "evidence. It does not modify scalar SAB or `sab_pvw_*`, and it does not",
        "upgrade novelty, theorem-level citation, non-binary, all-parameter, or",
        "hardware-counter claims.",
        "",
        "## Matrix",
        "",
        "| item | status | evidence | next gate |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['item_id']} | {row['status']} | {row['evidence']} | {row['next_gate']} |"
        )

    lines.extend(["", "## Decision", ""])
    lines.append(
        "Local conditional engineering follow-ups CB1-CB4 are closed as "
        "`CONDITION_NOT_ACTIVE` under the current promoted active-buffer "
        "PVW/MAT-SAB path. CB5-CB7 remain external-review or external-platform "
        "blockers and do not become local implementation tasks without the "
        "listed evidence."
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> int:
    write_csv(OUT_CSV, ROWS)
    write_md(ROWS)
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
