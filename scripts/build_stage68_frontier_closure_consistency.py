#!/usr/bin/env python3
"""Build the Stage68 frontier/closure consistency audit."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
STAGE42 = ROOT / "repro" / "stage42_evidence_closure_audit.csv"
STAGE51 = ROOT / "repro" / "stage51_goal_completion_frontier.csv"
STAGE57 = ROOT / "repro" / "stage57_scope_label_audit.csv"
STAGE59 = ROOT / "repro" / "stage59_completion_route_readiness.csv"
OUT_CSV = ROOT / "repro" / "stage68_frontier_closure_consistency.csv"
OUT_MD = ROOT / "docs" / "stage68_frontier_closure_consistency_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def row(gate: str, status: str, evidence: str, detail: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
    }


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "status", "evidence", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def latest_labels() -> Tuple[str, str]:
    text = ROADMAP.read_text(encoding="utf-8") if ROADMAP.exists() else ""
    stages = sorted({int(m.group(1)) for m in re.finditer(r"^## Stage (\d+):", text, re.M)})
    latest = stages[-1] if stages else 0
    if not latest:
        return ("Stage 19-62", "Stage19-62")
    return (f"Stage 19-{latest}", f"Stage19-{latest}")


def build_rows() -> List[Dict[str, str]]:
    stage42 = by_key(STAGE42, "check_id")
    stage51 = by_key(STAGE51, "frontier_id")
    stage57 = by_key(STAGE57, "audit_id")
    stage59 = by_key(STAGE59, "route_id")
    spaced_label, compact_label = latest_labels()

    stage42_overall = stage42.get("S42-OVERALL", {})
    stage42_detail = stage42_overall.get("detail", "")
    failed_stage42_checks = [
        check_id
        for check_id, item in stage42.items()
        if item.get("status") != "PASS"
        and check_id
        not in {
            "S42-OVERALL",
            "S42-STAGE68-FRONTIER-CLOSURE-CONSISTENCY",
        }
    ]
    stage42_self_refresh_only = (
        stage42_overall.get("status") == "FAIL_EVIDENCE_CLOSURE"
        and not failed_stage42_checks
    )
    stage42_ok = (
        (
            stage42_overall.get("status")
            == "PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED"
            or stage42_self_refresh_only
        )
        and (
            stage42_self_refresh_only
            or (
                "Stage67 final-recheck Stage66A integration" in stage42_detail
                and "Stage82 post-H11 profile" in stage42_detail
                and "Stage83 MAT body design check" in stage42_detail
                and "Stage84 H13 r=6 tile-sweep preflight" in stage42_detail
                and "Stage86 secondary CMUX materialization design gate" in stage42_detail
                and "Stage87 H14 backend FromDFT-add preflight" in stage42_detail
                and "Stage88 H14 backend repeated gates" in stage42_detail
                and "Stage89 H14 promotion policy integration" in stage42_detail
                and "Stage90 external claim unlock probe" in stage42_detail
                and "Stage91 final scoped SAB package" in stage42_detail
                and "Stage92 external unlock execution packet" in stage42_detail
                and "Stage93 external lane attempt" in stage42_detail
                and "Stage94 local frontier audit" in stage42_detail
                and "Stage95 public source reprobe" in stage42_detail
                and "Stage96 upstream delta audit" in stage42_detail
                and "Stage97 source delta guard" in stage42_detail
                and "Stage98 current-head smoke refresh" in stage42_detail
                and "Stage99 external blocker reprobe" in stage42_detail
                and "Stage100 full-text anchor prefill" in stage42_detail
            )
        )
    )

    g6 = stage51.get("G6", {})
    g6_detail = g6.get("interpretation", "")
    g6_status = g6.get("status")
    g6_accepts_refresh_pending = (
        g6_status == "LOCAL_REFRESH_PENDING"
        and stage42_self_refresh_only
        and compact_label in g6_detail
    )
    g6_ok = (
        (g6_status == "LOCAL_READY" or g6_accepts_refresh_pending)
        and compact_label in g6_detail
        and "Stage67 final-recheck Stage66A integration" in g6_detail
        and "Stage82 post-H11 profile" in g6_detail
        and "Stage83 MAT body design check" in g6_detail
        and "Stage84 H13 r=6 tile-sweep preflight" in g6_detail
        and "Stage86 secondary CMUX materialization design gate" in g6_detail
        and "Stage87 H14 backend FromDFT-add preflight" in g6_detail
        and "Stage88 H14 backend repeated gates" in g6_detail
        and "Stage89 H14 promotion policy integration" in g6_detail
        and "Stage90 external claim unlock" in g6_detail
        and "Stage91 final scoped SAB package" in g6_detail
        and "Stage92 external unlock execution packet" in g6_detail
        and "Stage93 external lane attempt" in g6_detail
        and "Stage94 local frontier audit" in g6_detail
        and "Stage95 public source reprobe" in g6_detail
        and "Stage96 upstream delta audit" in g6_detail
        and "Stage97 source delta guard" in g6_detail
        and "Stage98 current-head smoke refresh" in g6_detail
        and "Stage99 external blocker reprobe" in g6_detail
        and "Stage100 full-text anchor prefill" in g6_detail
    )

    stage57_ok = bool(stage57) and all(r.get("status") == "PASS" for r in stage57.values())
    stage57_detail = stage57.get("S57-ROADMAP-LATEST-STAGE", {}).get("detail", "")
    stage57_ok = stage57_ok and spaced_label in stage57_detail

    r1 = stage59.get("S59-R1-SCOPED-ENGINEERING", {})
    r2 = stage59.get("S59-R2-CURRENT-HEAD-REFRESH", {})
    r6 = stage59.get("S59-R6-OPTIONAL-VARIANTS", {})
    r7 = stage59.get("S59-R7-FINAL-PAPER-PACKAGE", {})
    stage59_ok = (
        r1.get("status") == "LOCAL_READY"
        and r2.get("status") == "READY_LOCAL_REFRESH"
        and "stage67_final_recheck_stage66" in r2.get("evidence", "")
        and "stage98_current_smoke_refresh" in r2.get("evidence", "")
        and r6.get("status") == "READY_OPTIONAL_LOCAL_TRIAGE"
        and "stage74_r_scaling_boundary" in r6.get("evidence", "")
        and "stage75_rgt4_profile_boundary" in r6.get("evidence", "")
        and "stage76_rgt4_kernel_feasibility" in r6.get("evidence", "")
        and "stage77_rgt4_fused_mat_kernel" in r6.get("evidence", "")
        and "stage78_rgt4_fused_repeated_gates" in r6.get("evidence", "")
        and "stage79_rgt4_fused_high_stat" in r6.get("evidence", "")
        and "stage80_promotion_policy_audit" in r6.get("evidence", "")
        and "stage81_next_variant_triage" in r6.get("evidence", "")
        and "stage82_post_h11_profile" in r6.get("evidence", "")
        and "stage83_mat_body_design_check" in r6.get("evidence", "")
        and "stage84_h13_r6_tile_sweep_preflight" in r6.get("evidence", "")
        and "stage86_secondary_cmux_materialization" in r6.get("evidence", "")
        and "stage87_h14_backend_from_dft_add_preflight" in r6.get("evidence", "")
        and "stage88_h14_backend_repeated_gates" in r6.get("evidence", "")
        and "stage89_h14_promotion_policy_integration" in r6.get("evidence", "")
        and "stage90_external_claim_unlock" in r6.get("evidence", "")
        and "stage94_local_frontier_audit" in r6.get("evidence", "")
        and r7.get("status") in {
            "SCOPED_FINAL_PACKAGE_READY_STRONGER_BLOCKED",
            "SCOPED_FINAL_PACKAGE_READY_EXTERNAL_REVIEW_REQUIRED",
        }
        and "stage91_final_package" in r7.get("evidence", "")
        and "stage92_external_unlock_execution" in r7.get("evidence", "")
        and "stage93_external_lane_attempt" in r7.get("evidence", "")
        and "stage94_local_frontier_audit" in r7.get("evidence", "")
        and "stage95_public_source_reprobe" in r7.get("evidence", "")
        and "stage96_upstream_delta_audit" in r7.get("evidence", "")
        and "stage97_source_delta_guard" in r7.get("evidence", "")
        and "stage98_current_smoke_refresh" in r7.get("evidence", "")
        and "stage99_external_blocker_reprobe" in r7.get("evidence", "")
        and "stage100_fulltext_anchor_prefill" in r7.get("evidence", "")
    )

    rows = [
        row(
            "stage68_stage42_label",
            "PASS" if stage42_ok else "FAIL",
            STAGE42.relative_to(ROOT).as_posix(),
            stage42_detail or "missing S42-OVERALL detail",
        ),
        row(
            "stage68_stage51_g6",
            "PASS" if g6_ok else "FAIL",
            STAGE51.relative_to(ROOT).as_posix(),
            f"status={g6.get('status', 'MISSING')}; interpretation={g6_detail}",
        ),
        row(
            "stage68_stage57_scope_label",
            "PASS" if stage57_ok else "FAIL",
            STAGE57.relative_to(ROOT).as_posix(),
            stage57_detail or "missing Stage57 latest-stage row",
        ),
        row(
            "stage68_stage59_route",
            "PASS" if stage59_ok else "FAIL",
            STAGE59.relative_to(ROOT).as_posix(),
            f"R1={r1.get('status', 'MISSING')}; R2={r2.get('status', 'MISSING')}; R2_evidence={r2.get('evidence', '')}; R6={r6.get('status', 'MISSING')}; R6_evidence={r6.get('evidence', '')}; R7={r7.get('status', 'MISSING')}; R7_evidence={r7.get('evidence', '')}",
        ),
    ]
    failures = [item["gate"] for item in rows if item["status"] != "PASS"]
    rows.append(
        row(
            "stage68_decision",
            "PASS_FRONTIER_CLOSURE_CONSISTENCY"
            if not failures
            else "FAIL_FRONTIER_CLOSURE_CONSISTENCY",
            OUT_CSV.relative_to(ROOT).as_posix(),
            f"Stage42, Stage51 G6, Stage57, and Stage59 are consistent for {spaced_label}"
            if not failures
            else f"failed_gates={failures}",
        )
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    spaced_label, compact_label = latest_labels()
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage68 Frontier Closure Consistency Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        f"Stage68 verifies that the current {compact_label} control-plane label",
        "propagated from Stage42 closure into Stage51 goal frontier, Stage57 scope-label audit,",
        "and Stage59 completion-route readiness. It is a consistency audit only.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| {item['gate']} | {item['status']} | {item['evidence']} | {item['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A passing Stage68 means the local scoped evidence chain is internally",
            f"consistent at the control-plane level for {spaced_label}. It does not run",
            "a new SAB benchmark and does not upgrade stronger claims.",
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
    print(f"Stage68 frontier closure consistency: {decision}")
    return 0 if decision.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
