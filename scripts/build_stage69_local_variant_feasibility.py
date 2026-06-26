#!/usr/bin/env python3
"""Build the Stage69 local-variant feasibility audit.

Stage69 is a control and theory gate. It does not modify SAB code and does not
run a benchmark. Its purpose is to decide whether any remaining local
PVW/MAT-SAB optimization candidate is sufficiently unblocked to justify new
implementation work after the Stage65A negative variant and Stage68 closure
repair.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
STAGE39 = ROOT / "repro" / "stage39_variant_triage.csv"
STAGE61 = ROOT / "repro" / "stage61_native_perf_unlock_probe" / "summary.csv"
STAGE62 = ROOT / "repro" / "stage62_fulltext_unlock_probe" / "unlock_summary.csv"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
H3_THEORY = ROOT / "theory_checks" / "h3_sparse_selector_feasibility.md"
H3_VARIANT = ROOT / "algorithm_variants" / "pvw_sab_sparse_selector_shortcut.md"
OUT_CSV = ROOT / "repro" / "stage69_local_variant_feasibility.csv"
OUT_MD = ROOT / "docs" / "stage69_local_variant_feasibility_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def row(
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


def build_rows() -> List[Dict[str, str]]:
    stage39 = by_key(STAGE39, "candidate_id")
    stage61 = by_key(STAGE61, "probe")
    stage62 = by_key(STAGE62, "gate")
    required_files = [STAGE39, HYPOTHESES, H3_THEORY, H3_VARIANT]
    missing = [p.relative_to(ROOT).as_posix() for p in required_files if not p.exists()]

    postproc = stage39.get("S39-DIRECT-POSTPROC", {})
    schedule = stage39.get("S39-DEEPER-SCHEDULE-FUSION", {})
    layout = stage39.get("S39-MAT-R4-LAYOUT", {})
    rspecific = stage39.get("S39-AVX512-RSPECIFIC", {})
    nonbinary = stage39.get("S39-NONBINARY-PVW-SAB", {})

    native_perf = stage61.get("hardware_counter_gate", {}).get("status", "MISSING")
    fulltext = stage62.get("stage62_decision", {}).get("status", "MISSING")
    h7_evidence_parts = [f"native_perf={native_perf}"]
    for item in [layout.get("current_evidence", ""), rspecific.get("current_evidence", "")]:
        for part in item.split(";"):
            part = part.strip()
            if part and part not in h7_evidence_parts:
                h7_evidence_parts.append(part)

    rows = [
        row(
            "stage69_inputs_available",
            "PASS" if not missing else "FAIL_MISSING_INPUTS",
            "; ".join(p.relative_to(ROOT).as_posix() for p in required_files),
            "all Stage69 hypothesis, triage, and theory files exist"
            if not missing
            else f"missing={missing}",
            "Restore missing inputs before using Stage69 to route implementation work.",
        ),
        row(
            "stage69_h2_postproc_tail",
            "DEFER_TAIL_SMALL"
            if postproc.get("decision") == "DEFER_TAIL_SMALL"
            else "REVIEW_REQUIRED",
            postproc.get("current_evidence", STAGE39.relative_to(ROOT).as_posix()),
            postproc.get("reason", ""),
            postproc.get("next_gate", "Reopen only if a new body optimization raises tail cost."),
        ),
        row(
            "stage69_h3_sparse_selector_theory",
            "REJECT_CURRENT_SPARSE_SELECTOR_SHORTCUT",
            (
                f"{H3_THEORY.relative_to(ROOT).as_posix()}; "
                f"{H3_VARIANT.relative_to(ROOT).as_posix()}"
            ),
            (
                "encrypted MAT_TRGSW_DFT selector rows are dense ciphertext "
                "objects; plaintext skip metadata would either be unavailable "
                "to evaluation or risk leaking secret-dependent SAB gaps"
            ),
            "Do not implement selector-value skipping without a new key-format/security design and full correctness/noise proof.",
        ),
        row(
            "stage69_h4_schedule_fusion",
            "NEUTRAL_NOT_PROMOTED"
            if schedule.get("decision") == "DEFER_PRIOR_NEUTRAL"
            else "REVIEW_REQUIRED",
            schedule.get("current_evidence", STAGE39.relative_to(ROOT).as_posix()),
            schedule.get("reason", ""),
            schedule.get("next_gate", "Only reopen if a new profile changes the bottleneck."),
        ),
        row(
            "stage69_h7_avx512_layout",
            "BLOCKED_NATIVE_COUNTERS_OR_NEGATIVE_PRIOR",
            "; ".join(h7_evidence_parts),
            (
                "Stage65A row-unrolled r=4 was negative; native counters remain "
                f"{native_perf}, so further register/layout work would be blind"
            ),
            "Run native perf-counter gate or propose a different isolated layout hypothesis before new AVX512 code.",
        ),
        row(
            "stage69_h8_nonbinary_branch",
            "BLOCKED_FULLTEXT_NONBINARY_DESIGN",
            f"fulltext={fulltext}; {nonbinary.get('current_evidence', '')}",
            nonbinary.get("reason", ""),
            nonbinary.get("next_gate", "Provide full 2025/686 text and write non-binary PVW-SAB design."),
        ),
    ]

    blocking_statuses = {
        "DEFER_TAIL_SMALL",
        "REJECT_CURRENT_SPARSE_SELECTOR_SHORTCUT",
        "NEUTRAL_NOT_PROMOTED",
        "BLOCKED_NATIVE_COUNTERS_OR_NEGATIVE_PRIOR",
        "BLOCKED_FULLTEXT_NONBINARY_DESIGN",
    }
    candidate_rows = rows[1:]
    no_unblocked = all(r["status"] in blocking_statuses for r in candidate_rows)
    rows.append(
        row(
            "stage69_no_unblocked_local_variant",
            "PASS_NO_UNBLOCKED_LOCAL_VARIANT" if no_unblocked and not missing else "REVIEW_REQUIRED",
            OUT_CSV.relative_to(ROOT).as_posix(),
            "all remaining local candidates are blocked, deferred, neutral, or rejected under current evidence"
            if no_unblocked and not missing
            else "one or more candidates needs review before route selection",
            "Continue via external unlocks or introduce a new falsifiable hypothesis with its own Stage65-style gate.",
        )
    )
    rows.append(
        row(
            "stage69_decision",
            "PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED"
            if no_unblocked and not missing
            else "FAIL_LOCAL_VARIANT_FEASIBILITY_AUDIT",
            OUT_CSV.relative_to(ROOT).as_posix(),
            "No new SAB code variant is justified by the current evidence without native perf, full-text review, or a new hypothesis."
            if no_unblocked and not missing
            else "Stage69 cannot decide the next implementation route.",
            "Preserve the promoted active-buffer path and scalar baseline; do not upgrade claims.",
        )
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage69 Local Variant Feasibility Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage69 audits the remaining local optimization candidates after",
        "Stage65A and Stage68. It does not modify SAB code, run a benchmark,",
        "or upgrade any performance, novelty, theorem-level, or AVX512 theory",
        "claim.",
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
            "## Interpretation",
            "",
            "Under the current evidence, the promoted local implementation remains",
            "`SAB_PVW_ACTIVE_BUFFER_FUSION=true` plus specialized MAT-AVX512.",
            "The next implementation change needs either external evidence",
            "unlocks or a new falsifiable hypothesis with correctness and full",
            "SAB A/B gates.",
        ]
    )
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage69 local variant feasibility: {decision}")
    return 0 if decision.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
