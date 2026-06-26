#!/usr/bin/env python3
"""Build the Stage81 next-variant triage.

Stage81 is a decision gate only. It chooses whether the current evidence
supports another local code variant after Stage80, or whether the next local
step must be profile-only measurement.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
STAGE24_TAIL = ROOT / "repro" / "stage24_postproc_tail_avx512_runs1" / "summary.csv"
STAGE69 = ROOT / "repro" / "stage69_local_variant_feasibility.csv"
STAGE74 = ROOT / "repro" / "stage74_r_scaling_boundary" / "decision.csv"
STAGE75_PROFILE = ROOT / "repro" / "stage75_rgt4_profile_boundary" / "profile_metrics.csv"
STAGE76 = ROOT / "repro" / "stage76_rgt4_kernel_feasibility" / "summary.csv"
STAGE79 = ROOT / "repro" / "stage79_rgt4_fused_high_stat" / "summary.csv"
STAGE80 = ROOT / "repro" / "stage80_promotion_policy_audit" / "summary.csv"
OUT_CSV = ROOT / "repro" / "stage81_next_variant_triage.csv"
OUT_MD = ROOT / "docs" / "stage81_next_variant_triage_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def max_float(rows: Iterable[Dict[str, str]], field: str) -> float:
    values = []
    for row in rows:
        try:
            values.append(float(row.get(field, "")))
        except ValueError:
            pass
    return max(values) if values else 0.0


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


def build_rows() -> List[Dict[str, str]]:
    stage69 = by_key(STAGE69, "gate")
    stage74 = by_key(STAGE74, "gate")
    stage76 = by_key(STAGE76, "gate")
    stage79 = by_key(STAGE79, "gate")
    stage80 = by_key(STAGE80, "gate")
    stage75_rows = read_csv(STAGE75_PROFILE)
    tail_rows = read_csv(STAGE24_TAIL)

    required = [STAGE24_TAIL, STAGE69, STAGE74, STAGE75_PROFILE, STAGE76, STAGE79, STAGE80]
    missing = [p.relative_to(ROOT).as_posix() for p in required if not p.exists()]

    h3_status = stage69.get("stage69_h3_sparse_selector_theory", {}).get("status", "MISSING")
    h4_status = stage69.get("stage69_h4_schedule_fusion", {}).get("status", "MISSING")
    h7_status = stage69.get("stage69_h7_avx512_layout", {}).get("status", "MISSING")
    rgt4_boundary = stage74.get("stage74_rgt4_boundary", {}).get("status", "MISSING")
    kernel_boundary = stage76.get("stage76_decision", {}).get("status", "MISSING")
    high_stat_status = stage79.get("stage79_r6_high_stat_full_sab", {}).get("status", "MISSING")
    policy_status = stage80.get("stage80_decision", {}).get("status", "MISSING")
    max_tail = max_float(tail_rows, "max_tail_pct")
    threshold = max_float(tail_rows, "threshold_pct") or 2.0
    max_mat_share = max_float(stage75_rows, "mat_ep_share_of_full")

    rows = [
        row(
            "stage81_inputs_available",
            "PASS" if not missing else "FAIL",
            "; ".join(p.relative_to(ROOT).as_posix() for p in required),
            "all Stage81 input evidence files exist" if not missing else f"missing={missing}",
            "Restore missing evidence before choosing a next local optimization.",
        ),
        row(
            "stage81_h11_policy_state",
            "KEEP_EXPERIMENTAL_NOT_PROMOTED"
            if policy_status == "PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED"
            else "FAIL_POLICY_STATE",
            STAGE80.relative_to(ROOT).as_posix(),
            f"Stage80 decision={policy_status}; Stage79 high-stat status={high_stat_status}",
            "Do not upgrade H11 r=6 fused MAT or make it default without a new promotion campaign.",
        ),
        row(
            "stage81_sparse_structured_mat_candidate",
            "BLOCKED_SECURITY_DESIGN_GAP"
            if h3_status == "REJECT_CURRENT_SPARSE_SELECTOR_SHORTCUT"
            else "REVIEW_REQUIRED",
            STAGE69.relative_to(ROOT).as_posix(),
            f"Stage69 H3 status={h3_status}; encrypted selector rows remain dense ciphertexts",
            "Do not implement sparse selector skipping without a key-format/security design.",
        ),
        row(
            "stage81_rgt4_lane_or_tiling_candidate",
            "NOT_SELECTED_R6_EXPERIMENTAL_R8_WEAK"
            if rgt4_boundary == "NOT_PROMOTED_R_GT4_BELOW_R4_SCREEN"
            and kernel_boundary == "PASS_RGT4_KERNEL_FEASIBILITY_RECORDED_NO_PROMOTION"
            else "REVIEW_REQUIRED",
            f"{STAGE74.relative_to(ROOT).as_posix()}; {STAGE76.relative_to(ROOT).as_posix()}",
            f"direct r>4 boundary={rgt4_boundary}; kernel boundary={kernel_boundary}; H7 status={h7_status}",
            "Do not write another r>4/r=8 tiling variant before profile attribution or native counters.",
        ),
        row(
            "stage81_postprocessing_candidate",
            "DEFER_TAIL_SMALL" if max_tail < threshold else "REOPEN_TAIL_PROFILE",
            STAGE24_TAIL.relative_to(ROOT).as_posix(),
            f"max_tail_pct={max_tail:.6f}; threshold_pct={threshold:.6f}",
            "Reopen PVW-aware extract/packing only if a refreshed body path raises tail cost above threshold.",
        ),
        row(
            "stage81_schedule_body_candidate",
            "SELECT_PROFILE_FIRST",
            f"{STAGE75_PROFILE.relative_to(ROOT).as_posix()}; {STAGE69.relative_to(ROOT).as_posix()}",
            f"max_mat_ep_share_of_full={max_mat_share:.6f}; Stage69 H4 status={h4_status}; H11 is experimental",
            "Run a post-H11 fused r=6 profile attribution before implementing another schedule/body fusion.",
        ),
    ]

    decision_ok = (
        not missing
        and rows[1]["status"] == "KEEP_EXPERIMENTAL_NOT_PROMOTED"
        and rows[2]["status"] == "BLOCKED_SECURITY_DESIGN_GAP"
        and rows[3]["status"] == "NOT_SELECTED_R6_EXPERIMENTAL_R8_WEAK"
        and rows[4]["status"] == "DEFER_TAIL_SMALL"
        and rows[5]["status"] == "SELECT_PROFILE_FIRST"
    )
    rows.append(
        row(
            "stage81_decision",
            "PASS_STAGE81_NEXT_VARIANT_TRIAGE_PROFILE_FIRST_NO_CODE_PROMOTION"
            if decision_ok
            else "FAIL_STAGE81_NEXT_VARIANT_TRIAGE",
            OUT_CSV.relative_to(ROOT).as_posix(),
            "No immediate new hot-path code variant is justified; the next local action is post-H11 fused r=6 profile attribution"
            if decision_ok
            else "Stage81 candidate statuses are inconsistent with the expected profile-first policy",
            "Profile first, then open a new hypothesis only if the profile identifies a concrete bottleneck and gate plan.",
        )
    )
    return rows


def write_csv(rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "status", "evidence", "detail", "next_action"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = rows[-1]["status"] if rows else "MISSING"
    lines = [
        "# Stage81 Next Variant Triage Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage81 selects the next optimization direction after Stage80 keeps H11",
        "r=6 fused MAT as explicit experimental evidence only. It is a",
        "decision gate and does not modify SAB code.",
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
            "## Decision",
            "",
            f"`{decision}`",
            "",
            "Interpretation: Stage81 does not promote a new local code path. The",
            "next local engineering step, if pursued before external unlocks, is",
            "profile-only post-H11 fused r=6 attribution. A real implementation",
            "stage must then start from a new hypothesis, theory check, staged",
            "correctness gate, full-SAB A/B, noise/resource gate, and claim",
            "policy row.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(rows)
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage81 next variant triage: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
