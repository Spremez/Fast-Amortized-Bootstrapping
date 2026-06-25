#!/usr/bin/env python3
"""Build the Stage 39 optional variant triage matrix."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro" / "stage39_variant_triage.csv"
OUT_MD = ROOT / "docs" / "stage39_variant_triage_log.md"

FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
BRANCH_SUMMARY = ROOT / "repro" / "stage26_parameter_branch_smoke_avx512" / "branch_summary.csv"
POSTPROC_SUMMARY = ROOT / "repro" / "stage24_postproc_tail_avx512_runs1" / "summary.csv"
STAGE23_R4 = ROOT / "repro" / "stage23_schedule_fused_bench_r4_reps1_runs3_seq" / "summary.csv"
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


def max_float(rows: List[Dict[str, str]], key: str) -> float:
    vals = []
    for row in rows:
        try:
            vals.append(float(row.get(key, "")))
        except ValueError:
            pass
    return max(vals) if vals else 0.0


def mean_float(rows: List[Dict[str, str]], key: str) -> float:
    vals = []
    for row in rows:
        try:
            vals.append(float(row.get(key, "")))
        except ValueError:
            pass
    return sum(vals) / len(vals) if vals else 0.0


def build_rows() -> List[Dict[str, str]]:
    audit = {row.get("item_id"): row for row in read_csv(FINAL_AUDIT)}
    branch = read_csv(BRANCH_SUMMARY)
    postproc = read_csv(POSTPROC_SUMMARY)
    stage23 = read_csv(STAGE23_R4)
    stage37 = {row.get("item"): row for row in read_csv(STAGE37)}
    stage38 = {row.get("item"): row for row in read_csv(STAGE38)}

    stage37_decision = stage37.get("stage37_decision", {}).get("status", "MISSING")
    stage38_decision = stage38.get("stage38_decision", {}).get("status", "MISSING")
    a8 = audit.get("A8", {}).get("status", "MISSING")
    a9 = audit.get("A9", {}).get("status", "MISSING")
    nonbinary = row_by(branch, "mode", "pvw_target")
    tail_max = max_float(postproc, "max_tail_pct")
    schedule_r4_mean = mean_float(stage23, "speedup_vs_scalar_repeated")

    rows = [
        {
            "candidate_id": "S39-NONBINARY-PVW-SAB",
            "candidate": "non-binary PVW-SAB branch support",
            "current_evidence": (
                f"branch_summary pvw_target={nonbinary.get('status','MISSING')}; "
                f"Stage38={stage38_decision}"
            ),
            "decision": "BLOCKED_REQUIRES_PROTOCOL_DESIGN_AND_FULLTEXT",
            "reason": (
                "Current PVW target harness is explicitly binary-only, scalar ternary "
                "build is only a guard, and theorem-level branch semantics require "
                "2025/686 full-text review."
            ),
            "next_gate": (
                "Provide full 2025/686 text, write non-binary PVW-SAB design, then "
                "start with staged r=1/2 correctness before performance work."
            ),
            "implementation_policy": "new explicit flag/path only; do not touch scalar default",
        },
        {
            "candidate_id": "S39-DEEPER-SCHEDULE-FUSION",
            "candidate": "deeper sparse-schedule fusion beyond Stage 23",
            "current_evidence": f"Stage23 r=4 schedule-fused mean speedup {schedule_r4_mean:.3f}x; recorded neutral",
            "decision": "DEFER_PRIOR_NEUTRAL",
            "reason": (
                "The Stage 23 schedule-fused CMUX/NCMUX candidate was correct but "
                "did not beat the promoted active-buffer path."
            ),
            "next_gate": (
                "Only reopen if a new profile shows a larger schedule/copy/materialization "
                "cost than the Stage 23/24 evidence."
            ),
            "implementation_policy": "explicit ablation flag; require full-SAB A/B before promotion",
        },
        {
            "candidate_id": "S39-MAT-R4-LAYOUT",
            "candidate": "MAT key/layout or coefficient-blocked r=4 experiment",
            "current_evidence": f"final audit A8={a8}; Stage37={stage37_decision}",
            "decision": "BLOCKED_NATIVE_COUNTERS_OR_ISOLATED_LAYOUT_EXPERIMENT",
            "reason": (
                "The useful question is load/store/FMA attribution versus dense MAT "
                "multiply pressure; current platform lacks hardware counters."
            ),
            "next_gate": (
                "Run Stage37 on native/perf-enabled Linux, or implement a reversible "
                "isolated key-layout experiment with no default key-format change."
            ),
            "implementation_policy": "experimental layout only; default key layout unchanged",
        },
        {
            "candidate_id": "S39-DIRECT-POSTPROC",
            "candidate": "PVW-aware direct extract/packing-KS post-processing",
            "current_evidence": f"Stage24 max post-processing tail {tail_max:.6f}% below 2.0% threshold",
            "decision": "DEFER_TAIL_SMALL",
            "reason": (
                "Tail cost is too small to justify high-risk post-processing changes "
                "under the current promoted body path."
            ),
            "next_gate": "Reopen only if a new body optimization raises tail cost above the threshold.",
            "implementation_policy": "no implementation until profile threshold is crossed",
        },
        {
            "candidate_id": "S39-AVX512-RSPECIFIC",
            "candidate": "additional r-specific AVX512 kernels",
            "current_evidence": f"Stage37={stage37_decision}; final audit A8={a8}",
            "decision": "BLOCKED_NATIVE_COUNTERS",
            "reason": (
                "Further AVX512 specialization needs counter-backed evidence to avoid "
                "optimizing the wrong memory/register bottleneck."
            ),
            "next_gate": "Collect native perf counters and compare against Stage22 specialized/generic data.",
            "implementation_policy": "small-r specialization behind compile flag only",
        },
        {
            "candidate_id": "S39-OVERALL",
            "candidate": "Stage39 implementation decision",
            "current_evidence": f"final audit A9={a9}",
            "decision": "NO_NEW_VARIANT_PROMOTED_CURRENTLY",
            "reason": (
                "The promoted active-buffer MAT-SAB path already has scoped engineering "
                "evidence; remaining stronger claims are external or optional rather "
                "than an immediate new-code requirement."
            ),
            "next_gate": (
                "Proceed to Stage40 freeze for current scoped claim, or select one "
                "blocked/optional candidate explicitly after supplying its prerequisite evidence."
            ),
            "implementation_policy": "keep scalar baseline and promoted PVW path unchanged",
        },
    ]
    return rows


def write_csv(rows: List[Dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "candidate_id",
        "candidate",
        "current_evidence",
        "decision",
        "reason",
        "next_gate",
        "implementation_policy",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage 39 Optional Variant Triage Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 39 decides whether to start new algorithmic variant work beyond "
        "the promoted active-buffer MAT-SAB path. It preserves prior neutral "
        "and blocked evidence instead of repeatedly modifying hot paths without "
        "a new gate.",
        "",
        "## Candidate Matrix",
        "",
        "| candidate | decision | current evidence | next gate |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['candidate_id']} | {row['decision']} | "
            f"{row['current_evidence']} | {row['next_gate']} |"
        )
    overall = row_by(rows, "candidate_id", "S39-OVERALL")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            overall.get("reason", "No overall decision row generated."),
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    write_csv(rows)
    write_md(rows)
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
