#!/usr/bin/env python3
"""Build the Stage 35 completion-blocker matrix.

The goal is not to upgrade claims. It converts the generated final audit into
an explicit roadmap of what is locally complete, what is optional expansion,
and what requires external evidence before stronger SAB/PVW-MAT claims can be
made.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
AUDIT_CSV = ROOT / "repro/final_goal_completion_audit.csv"
EXTERNAL_CSV = ROOT / "repro/external_evidence_intake/summary.csv"
OUT_CSV = ROOT / "repro/stage35_completion_blockers.csv"
OUT_MD = ROOT / "docs/stage35_completion_blocker_matrix.md"


def read_csv_dicts(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def external_status() -> str:
    rows = read_csv_dicts(EXTERNAL_CSV)
    if not rows:
        return "external evidence intake has not been run"
    parts = []
    for row in rows:
        name = row.get("evidence_id", row.get("artifact", ""))
        status = row.get("status", "")
        parts.append(f"{name}={status}")
    return "; ".join(parts)


def classify(row: Dict[str, str], ext_status: str) -> Dict[str, str]:
    item_id = row["item_id"]
    status = row["status"]
    category = row["category"]
    requirement = row["requirement"]
    evidence = row["evidence"]
    remaining = row["remaining_action"]

    if status.startswith("PASS") and item_id != "A9":
        lane = "complete_or_scoped_complete"
        requires_user = "no"
        next_action = "keep artifact current through final recheck"
        impact = "supports scoped engineering claim"
    elif status == "BLOCKED_EXTERNAL":
        lane = "external_blocker"
        requires_user = "yes"
        next_action = (
            "run Stage 28 on native Linux or perf-enabled WSL with "
            "STAGE28_RUN_BENCH=1 and register the summary"
        )
        impact = "blocks MAT-AVX512 theoretical load/store optimality claim"
    elif status == "MISSING_OPTIONAL_EXTERNAL_EVIDENCE":
        lane = "external_blocker"
        requires_user = "yes"
        next_action = (
            "provide 2025/686 full text and/or native perf summary through "
            "FAB686_FULLTEXT_PATH and STAGE28_NATIVE_PERF_SUMMARY"
        )
        impact = "blocks theorem-level citation review and optional perf upgrade"
    elif status == "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        lane = "overall_scoped_ready"
        requires_user = "conditional"
        next_action = (
            "continue only with explicit stronger-claim scope: full paper "
            "review, native perf counters, broader statistics, or new "
            "algorithmic variants"
        )
        impact = "scoped engineering SAB acceleration is ready; paper-level stronger claims remain open"
    else:
        lane = "review_required"
        requires_user = "conditional"
        next_action = remaining
        impact = "needs manual review before claim upgrade"

    if item_id == "A7" and status == "PASS_SMALL_SAMPLE":
        lane = "optional_expansion"
        requires_user = "no"
        next_action = "increase added-parameter runs/seeds only before broad all-parameter claims"
        impact = "does not block scoped target claim; blocks broad generalization wording"
    if item_id == "A4" and status == "PASS_SMOKE_RESOURCE":
        lane = "optional_expansion"
        requires_user = "no"
        next_action = "repeat resource matrix only if paper needs statistical resource tables"
        impact = "does not block scoped engineering claim"
    if item_id == "A6" and status == "PASS_BLOCKED_BOUNDARY":
        lane = "claim_guardrail"
        requires_user = "yes_for_upgrade"
        next_action = "review full related work and 2025/686 text before changing blocked labels"
        impact = "prevents novelty/theorem overclaim"

    return {
        "item_id": item_id,
        "category": category,
        "status": status,
        "lane": lane,
        "requires_user_or_external_input": requires_user,
        "requirement": requirement,
        "evidence": evidence,
        "next_action": next_action,
        "completion_impact": impact,
        "external_status": ext_status if lane == "external_blocker" else "",
    }


def write_csv(rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, str]]) -> None:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row["lane"]] = counts.get(row["lane"], 0) + 1

    lines = [
        "# Stage 35 Completion Blocker Matrix",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 35 converts the generated final goal audit into a concrete",
        "remaining-work matrix. It separates the already scoped-complete",
        "engineering evidence from optional expansions and external blockers.",
        "",
        "This stage does not change scalar SAB or `sab_pvw_*` code, and it does",
        "not upgrade any claim by itself.",
        "",
        "## Summary",
        "",
    ]
    for lane in sorted(counts):
        lines.append(f"- `{lane}`: {counts[lane]}")

    lines.extend(
        [
            "",
            "## Matrix",
            "",
            "| item | status | lane | external input | external status | next action | impact |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| {item_id} | {status} | {lane} | {requires_user_or_external_input} | {external_status} | "
            "{next_action} | {completion_impact} |".format(**row)
        )

    lines.extend(
        [
            "",
            "## Execution Decision",
            "",
            "The next local-only action is to keep the final recheck current. Stronger",
            "claims require at least one external unlock:",
            "",
            "- 2025/686 full text for theorem-level citation and novelty review;",
            "- native Linux or perf-enabled WSL evidence for MAT-AVX512 load/store",
            "  attribution;",
            "- larger run/seed campaigns only if the target claim is broadened beyond",
            "  the current scoped engineering result.",
            "",
        ]
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    audit_rows = read_csv_dicts(AUDIT_CSV)
    if not audit_rows:
        raise SystemExit(f"missing final audit CSV: {AUDIT_CSV}")

    ext = external_status()
    rows = [classify(row, ext) for row in audit_rows]
    write_csv(rows)
    write_md(rows)
    print(f"Stage 35 completion blocker CSV: {OUT_CSV.relative_to(ROOT)}")
    print(f"Stage 35 completion blocker log: {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
