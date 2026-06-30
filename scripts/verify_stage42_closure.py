#!/usr/bin/env python3
"""Verify the Stage 42 evidence-closure package without regenerating it."""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
STAGE41 = ROOT / "repro" / "stage41_external_unlock_packet.csv"
STAGE42_AUDIT = ROOT / "repro" / "stage42_evidence_closure_audit.csv"
STAGE42_MANIFEST = ROOT / "repro" / "stage42_evidence_closure_manifest.csv"
STAGE43_SMOKE = ROOT / "repro" / "stage43_current_smoke_after_stage42" / "summary.csv"
STAGE44_REPROBE = ROOT / "repro" / "stage44_external_unlock_reprobe" / "summary.csv"
STAGE45_ACTIVE_STATE = ROOT / "repro" / "stage45_active_state_refactor" / "summary.csv"
STAGE46_WSL_TARGET = ROOT / "repro" / "stage46_wsl_active_state_target_smoke" / "summary.csv"
STAGE47_WSL_FULL_SAB = ROOT / "repro" / "stage47_wsl_active_state_full_sab_smoke" / "summary.csv"
STAGE48_WSL_NOISE = ROOT / "repro" / "stage48_wsl_active_state_noise_smoke" / "aggregate.csv"
STAGE49_WSL_REPEATED_FULL_SAB = ROOT / "repro" / "stage49_wsl_repeated_full_sab" / "summary.csv"
STAGE50_PERF_MATRIX = ROOT / "repro" / "stage50_performance_evidence_matrix.csv"
STAGE51_GOAL_FRONTIER = ROOT / "repro" / "stage51_goal_completion_frontier.csv"
STAGE52_UNLOCK_READINESS = ROOT / "repro" / "stage52_external_unlock_readiness.csv"
STAGE53_FINAL_RECHECK = ROOT / "repro" / "stage53_final_recheck_stage50_52" / "summary.csv"
STAGE54_DEFAULT_FINAL_RECHECK = ROOT / "repro" / "stage54_default_final_recheck" / "summary.csv"
STAGE55_EXTERNAL_PAPER_PROBE = ROOT / "repro" / "stage55_external_paper_probe" / "summary.csv"
STAGE56_FINAL_RECHECK_STAGE55 = ROOT / "repro" / "stage56_final_recheck_stage55" / "summary.csv"
STAGE57_SCOPE_LABEL_AUDIT = ROOT / "repro" / "stage57_scope_label_audit.csv"
STAGE58_FINAL_RECHECK_STAGE57 = ROOT / "repro" / "stage58_final_recheck_stage57" / "summary.csv"
STAGE59_COMPLETION_ROUTE = ROOT / "repro" / "stage59_completion_route_readiness.csv"
STAGE60_FINAL_RECHECK_STAGE59 = ROOT / "repro" / "stage60_final_recheck_stage59" / "summary.csv"
STAGE61_NATIVE_PERF_UNLOCK = ROOT / "repro" / "stage61_native_perf_unlock_probe" / "summary.csv"
STAGE62_FULLTEXT_UNLOCK = ROOT / "repro" / "stage62_fulltext_unlock_probe" / "unlock_summary.csv"
STAGE64A_POST_VARIANT_REFRESH = ROOT / "repro" / "stage64_post_variant_refresh" / "summary.csv"
STAGE65A_R4_UNROLLED = ROOT / "repro" / "stage65_r4_unrolled_avx512" / "summary.csv"
STAGE66A_POST_VARIANT_FINAL_RECHECK = (
    ROOT / "repro" / "stage66_post_variant_final_recheck" / "summary.csv"
)
STAGE67_FINAL_RECHECK_STAGE66 = ROOT / "repro" / "stage67_final_recheck_stage66" / "summary.csv"
STAGE67_FINAL_RECHECK_STAGE66_DECISION = (
    ROOT / "repro" / "stage67_final_recheck_stage66" / "decision.csv"
)
STAGE68_FRONTIER_CLOSURE_CONSISTENCY = (
    ROOT / "repro" / "stage68_frontier_closure_consistency.csv"
)
STAGE69_LOCAL_VARIANT_FEASIBILITY = (
    ROOT / "repro" / "stage69_local_variant_feasibility.csv"
)
STAGE70_EXTERNAL_UNLOCK_PREFLIGHT = (
    ROOT / "repro" / "stage70_external_unlock_preflight.csv"
)
STAGE71_FINAL_RECHECK_STAGE70 = ROOT / "repro" / "stage71_final_recheck_stage70" / "summary.csv"
STAGE71_FINAL_RECHECK_STAGE70_DECISION = (
    ROOT / "repro" / "stage71_final_recheck_stage70" / "decision.csv"
)
STAGE72_EXTERNAL_SOURCE_REFRESH = (
    ROOT / "repro" / "stage72_external_source_refresh" / "summary.csv"
)
STAGE73_FINAL_RECHECK_STAGE72 = (
    ROOT / "repro" / "stage73_final_recheck_stage72" / "summary.csv"
)
STAGE73_FINAL_RECHECK_STAGE72_DECISION = (
    ROOT / "repro" / "stage73_final_recheck_stage72" / "decision.csv"
)
STAGE74_R_SCALING_BOUNDARY = (
    ROOT / "repro" / "stage74_r_scaling_boundary" / "decision.csv"
)
STAGE75_RGT4_PROFILE_BOUNDARY = (
    ROOT / "repro" / "stage75_rgt4_profile_boundary" / "decision.csv"
)
STAGE76_RGT4_KERNEL_FEASIBILITY = (
    ROOT / "repro" / "stage76_rgt4_kernel_feasibility" / "summary.csv"
)
STAGE77_RGT4_FUSED_MAT_KERNEL = (
    ROOT / "repro" / "stage77_rgt4_fused_mat_kernel" / "summary.csv"
)
STAGE78_RGT4_FUSED_REPEATED_GATES = (
    ROOT / "repro" / "stage78_rgt4_fused_repeated_gates" / "summary.csv"
)
STAGE79_RGT4_FUSED_HIGH_STAT = (
    ROOT / "repro" / "stage79_rgt4_fused_high_stat" / "summary.csv"
)
STAGE80_PROMOTION_POLICY_AUDIT = (
    ROOT / "repro" / "stage80_promotion_policy_audit" / "summary.csv"
)
STAGE81_NEXT_VARIANT_TRIAGE = ROOT / "repro" / "stage81_next_variant_triage.csv"
STAGE82_POST_H11_PROFILE = ROOT / "repro" / "stage82_post_h11_profile" / "decision.csv"
STAGE83_MAT_BODY_DESIGN_CHECK = (
    ROOT / "repro" / "stage83_mat_body_design_check" / "decision.csv"
)
STAGE84_H13_R6_TILE_SWEEP = (
    ROOT / "repro" / "stage84_h13_r6_tile_sweep_preflight" / "summary.csv"
)
STAGE86_SECONDARY_CMUX_MATERIALIZATION = (
    ROOT / "repro" / "stage86_secondary_cmux_materialization" / "decision.csv"
)
STAGE87_H14_BACKEND_FROM_DFT_ADD = (
    ROOT / "repro" / "stage87_h14_backend_from_dft_add_preflight" / "summary.csv"
)
STAGE88_H14_BACKEND_REPEATED_GATES = (
    ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "summary.csv"
)
STAGE89_H14_PROMOTION_POLICY = (
    ROOT / "repro" / "stage89_h14_promotion_policy_integration" / "summary.csv"
)
STAGE90_EXTERNAL_CLAIM_UNLOCK = (
    ROOT / "repro" / "stage90_external_claim_unlock" / "summary.csv"
)
STAGE91_FINAL_PACKAGE = ROOT / "repro" / "stage91_final_package" / "summary.csv"
STAGE92_EXTERNAL_UNLOCK_EXECUTION = (
    ROOT / "repro" / "stage92_external_unlock_execution" / "summary.csv"
)
STAGE93_EXTERNAL_LANE_ATTEMPT = (
    ROOT / "repro" / "stage93_external_lane_attempt" / "summary.csv"
)
STAGE94_LOCAL_FRONTIER_AUDIT = (
    ROOT / "repro" / "stage94_local_frontier_audit" / "summary.csv"
)
STAGE95_PUBLIC_SOURCE_REPROBE = (
    ROOT / "repro" / "stage95_public_source_reprobe" / "summary.csv"
)
STAGE96_UPSTREAM_DELTA_AUDIT = (
    ROOT / "repro" / "stage96_upstream_delta_audit" / "summary.csv"
)
STAGE97_SOURCE_DELTA_GUARD = (
    ROOT / "repro" / "stage97_source_delta_guard" / "summary.csv"
)
STAGE98_CURRENT_SMOKE_REFRESH = (
    ROOT / "repro" / "stage98_current_smoke_refresh" / "summary.csv"
)
STAGE99_EXTERNAL_BLOCKER_REPROBE = (
    ROOT / "repro" / "stage99_external_blocker_reprobe" / "summary.csv"
)
STAGE100_FULLTEXT_ANCHOR_PREFILL = (
    ROOT / "repro" / "stage100_fulltext_anchor_prefill" / "summary.csv"
)
STAGE44_RECHECK = ROOT / "repro" / "final_goal_recheck_stage44_reprobe" / "summary.csv"
DEFAULT_RECHECK = ROOT / "repro" / "final_goal_recheck" / "summary.csv"
CLOSURE_RECHECK = ROOT / "repro" / "final_goal_recheck_stage42_closure" / "summary.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"
ARTIFACT_MANIFEST = ROOT / "repro" / "artifact_manifest.md"

STAGE88_ARTIFACTS = [
    "docs/stage88_h14_backend_repeated_gates_log.md",
    "experiments/stage88_h14_backend_repeated_gates_plan.md",
    "scripts/run_stage88_h14_backend_repeated_gates.sh",
    "scripts/build_stage88_h14_backend_repeated_gates.py",
    "theory_checks/h14_secondary_cmux_materialization.md",
    "algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage88_h14_backend_repeated_gates/stage88_run.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/build.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/run_0.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/run_1.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/run_2.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_wrapper_r6_runs3/summary.csv",
    "repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/build.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/run_0.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/run_1.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/run_2.log",
    "repro/stage88_h14_backend_repeated_gates/full_sab_backend_r6_runs3/summary.csv",
    "repro/stage88_h14_backend_repeated_gates/full_sab_repeated.csv",
    "repro/stage88_h14_backend_repeated_gates/backend_vs_wrapper.csv",
    "repro/stage88_h14_backend_repeated_gates/final_noise/summary.csv",
    "repro/stage88_h14_backend_repeated_gates/final_noise/aggregate.csv",
    "repro/stage88_h14_backend_repeated_gates/final_noise/r6/seed_6868025.log",
    "repro/stage88_h14_backend_repeated_gates/final_noise/r6/seed_6868026.log",
    "repro/stage88_h14_backend_repeated_gates/final_noise/r6/seed_6868027.log",
    "repro/stage88_h14_backend_repeated_gates/noise_summary.csv",
    "repro/stage88_h14_backend_repeated_gates/resource_run_0/summary.csv",
    "repro/stage88_h14_backend_repeated_gates/resource_run_0/r6/pvw.log",
    "repro/stage88_h14_backend_repeated_gates/resource_run_0/r6/pvw.time.log",
    "repro/stage88_h14_backend_repeated_gates/resource_run_0/r6/scalar.log",
    "repro/stage88_h14_backend_repeated_gates/resource_run_0/r6/scalar.time.log",
    "repro/stage88_h14_backend_repeated_gates/resource_samples.csv",
    "repro/stage88_h14_backend_repeated_gates/resource_summary.csv",
    "repro/stage88_h14_backend_repeated_gates/summary.csv",
]

STAGE89_ARTIFACTS = [
    "docs/stage89_h14_promotion_policy_integration_log.md",
    "experiments/stage89_h14_promotion_policy_integration_plan.md",
    "scripts/run_stage89_h14_promotion_policy_integration.sh",
    "scripts/build_stage89_h14_promotion_policy_integration.py",
    "theory_checks/h14_secondary_cmux_materialization.md",
    "algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage89_h14_promotion_policy_integration/stage89_run.log",
    "repro/stage89_h14_promotion_policy_integration/current_smoke/summary.csv",
    "repro/stage89_h14_promotion_policy_integration/current_smoke/scalar_binary_SET_2_3_2048/build.log",
    "repro/stage89_h14_promotion_policy_integration/current_smoke/scalar_binary_SET_2_3_2048/run.log",
    "repro/stage89_h14_promotion_policy_integration/current_smoke/backend_pvw_target_SET_2_3_2048/build.log",
    "repro/stage89_h14_promotion_policy_integration/current_smoke/backend_pvw_target_SET_2_3_2048/run.log",
    "repro/stage89_h14_promotion_policy_integration/current_smoke/scalar_ternary_SET_2_3_2048/build.log",
    "repro/stage89_h14_promotion_policy_integration/summary.csv",
]

STAGE90_ARTIFACTS = [
    "docs/stage90_external_claim_unlock_log.md",
    "experiments/stage90_external_claim_unlock_plan.md",
    "scripts/run_stage90_external_claim_unlock.sh",
    "scripts/build_stage90_external_claim_unlock.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage90_external_claim_unlock/summary.csv",
    "repro/stage90_external_claim_unlock/citation_probe/summary.csv",
    "repro/stage90_external_claim_unlock/citation_probe/access_probe.csv",
    "repro/stage90_external_claim_unlock/native_perf_gate/summary.csv",
    "repro/stage90_external_claim_unlock/native_perf_gate/environment.log",
    "repro/stage90_external_claim_unlock/native_perf_gate/perf_smoke.log",
    "repro/stage90_external_claim_unlock/citation_probe.log",
    "repro/stage90_external_claim_unlock/native_perf_gate.log",
    "repro/stage90_external_claim_unlock/external_evidence_intake.log",
    "repro/stage90_external_claim_unlock/stage90_builder.log",
]

STAGE91_ARTIFACTS = [
    "docs/stage91_final_sab_optimization_package.md",
    "experiments/stage91_final_package_plan.md",
    "scripts/run_stage91_final_package.sh",
    "scripts/build_stage91_final_package.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage91_final_package/summary.csv",
    "repro/stage91_final_package/performance_claims.csv",
    "repro/stage91_final_package/noise_resource_claims.csv",
    "repro/stage91_final_package/claim_boundary.csv",
    "repro/stage91_final_package/reproduction_commands.csv",
    "repro/stage91_final_package/artifact_index.csv",
]

STAGE92_ARTIFACTS = [
    "docs/stage92_external_unlock_execution_packet.md",
    "experiments/stage92_external_unlock_execution_plan.md",
    "scripts/run_stage92_external_unlock_execution_packet.sh",
    "scripts/build_stage92_external_unlock_execution_packet.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage92_external_unlock_execution/summary.csv",
    "repro/stage92_external_unlock_execution/lane_matrix.csv",
    "repro/stage92_external_unlock_execution/commands.csv",
    "repro/stage92_external_unlock_execution/acceptance_matrix.csv",
    "repro/stage92_external_unlock_execution/artifact_index.csv",
]

STAGE93_ARTIFACTS = [
    "docs/stage93_external_lane_attempt_log.md",
    "experiments/stage93_external_lane_attempt_plan.md",
    "scripts/run_stage93_external_lane_attempt.sh",
    "scripts/build_stage93_external_lane_attempt.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage93_external_lane_attempt/summary.csv",
    "repro/stage93_external_lane_attempt/artifact_index.csv",
    "repro/stage93_external_lane_attempt/native_perf_gate/summary.csv",
    "repro/stage93_external_lane_attempt/native_perf_gate/environment.log",
    "repro/stage93_external_lane_attempt/native_perf_gate/perf_smoke.log",
    "repro/stage93_external_lane_attempt/native_perf_gate.log",
    "repro/stage93_external_lane_attempt/local_fulltext_search.csv",
]

STAGE94_ARTIFACTS = [
    "docs/stage94_local_frontier_audit_log.md",
    "experiments/stage94_local_frontier_audit_plan.md",
    "scripts/run_stage94_local_frontier_audit.sh",
    "scripts/build_stage94_local_frontier_audit.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage94_local_frontier_audit/summary.csv",
    "repro/stage94_local_frontier_audit/candidates.csv",
    "repro/stage94_local_frontier_audit/artifact_index.csv",
]

STAGE95_ARTIFACTS = [
    "docs/stage95_public_source_reprobe_log.md",
    "experiments/stage95_public_source_reprobe_plan.md",
    "scripts/run_stage95_public_source_reprobe.sh",
    "scripts/build_stage95_public_source_reprobe.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage95_public_source_reprobe/summary.csv",
    "repro/stage95_public_source_reprobe/route_matrix.csv",
    "repro/stage95_public_source_reprobe/artifact_index.csv",
]

STAGE96_ARTIFACTS = [
    "docs/stage96_upstream_delta_audit_log.md",
    "experiments/stage96_upstream_delta_audit_plan.md",
    "scripts/run_stage96_upstream_delta_audit.sh",
    "scripts/build_stage96_upstream_delta_audit.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage96_upstream_delta_audit/summary.csv",
    "repro/stage96_upstream_delta_audit/delta_by_area.csv",
    "repro/stage96_upstream_delta_audit/delta_files.csv",
    "repro/stage96_upstream_delta_audit/commit_range.csv",
    "repro/stage96_upstream_delta_audit/flag_guard.csv",
    "repro/stage96_upstream_delta_audit/stage96_run.log",
    "repro/stage96_upstream_delta_audit/artifact_index.csv",
]

STAGE97_ARTIFACTS = [
    "docs/stage97_source_delta_guard_log.md",
    "experiments/stage97_source_delta_guard_plan.md",
    "scripts/run_stage97_source_delta_guard.sh",
    "scripts/build_stage97_source_delta_guard.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage97_source_delta_guard/summary.csv",
    "repro/stage97_source_delta_guard/source_delta.csv",
    "repro/stage97_source_delta_guard/symbol_guard.csv",
    "repro/stage97_source_delta_guard/build_flag_guard.csv",
    "repro/stage97_source_delta_guard/smoke_evidence.csv",
    "repro/stage97_source_delta_guard/stage97_run.log",
    "repro/stage97_source_delta_guard/artifact_index.csv",
]

STAGE98_ARTIFACTS = [
    "docs/stage98_current_smoke_refresh_log.md",
    "experiments/stage98_current_smoke_refresh_plan.md",
    "scripts/run_stage98_current_smoke_refresh.sh",
    "scripts/build_stage98_current_smoke_refresh.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage98_current_smoke_refresh/summary.csv",
    "repro/stage98_current_smoke_refresh/raw_smoke.csv",
    "repro/stage98_current_smoke_refresh/artifact_index.csv",
    "repro/stage98_current_smoke_refresh/stage98_run.log",
    "repro/stage98_current_smoke_refresh/scalar_binary_SET_2_3_2048/build.log",
    "repro/stage98_current_smoke_refresh/scalar_binary_SET_2_3_2048/run.log",
    "repro/stage98_current_smoke_refresh/active_pvw_target_SET_2_3_2048/build.log",
    "repro/stage98_current_smoke_refresh/active_pvw_target_SET_2_3_2048/run.log",
    "repro/stage98_current_smoke_refresh/backend_pvw_target_SET_2_3_2048/build.log",
    "repro/stage98_current_smoke_refresh/backend_pvw_target_SET_2_3_2048/run.log",
    "repro/stage98_current_smoke_refresh/scalar_ternary_SET_2_3_2048/build.log",
]

STAGE99_ARTIFACTS = [
    "docs/current_codex_goal_sab_completion.md",
    "docs/stage99_external_blocker_reprobe_log.md",
    "experiments/stage99_external_blocker_reprobe_plan.md",
    "scripts/run_stage99_external_blocker_reprobe.sh",
    "scripts/build_stage99_external_blocker_reprobe.py",
    "hypotheses/hypothesis_register.yaml",
    "repro/stage99_external_blocker_reprobe/summary.csv",
    "repro/stage99_external_blocker_reprobe/route_matrix.csv",
    "repro/stage99_external_blocker_reprobe/local_fulltext_search.csv",
    "repro/stage99_external_blocker_reprobe/artifact_index.csv",
    "repro/stage99_external_blocker_reprobe/stage99_run.log",
    "repro/stage99_external_blocker_reprobe/native_perf_probe.log",
    "repro/stage99_external_blocker_reprobe/citation_probe.log",
    "repro/stage99_external_blocker_reprobe/native_perf_probe/summary.csv",
    "repro/stage99_external_blocker_reprobe/native_perf_probe/environment.log",
    "repro/stage99_external_blocker_reprobe/native_perf_probe/perf_smoke.log",
    "repro/stage99_external_blocker_reprobe/citation_probe/summary.csv",
    "repro/stage99_external_blocker_reprobe/citation_probe/access_probe.csv",
]

STAGE100_ARTIFACTS = [
    "docs/stage100_fulltext_anchor_prefill_log.md",
    "experiments/stage100_fulltext_anchor_prefill_plan.md",
    "scripts/run_stage100_fulltext_anchor_prefill.sh",
    "scripts/build_stage100_fulltext_anchor_prefill.py",
    "repro/stage100_fulltext_anchor_prefill/summary.csv",
    "repro/stage100_fulltext_anchor_prefill/page_keyword_hits.csv",
    "repro/stage100_fulltext_anchor_prefill/anchor_candidates.csv",
    "repro/stage100_fulltext_anchor_prefill/artifact_index.csv",
    "repro/stage100_fulltext_anchor_prefill/stage100_run.log",
    "repro/stage100_fulltext_anchor_prefill/stage100_build.log",
    "repro/stage38_fulltext_review_gate/review_checklist.csv",
]


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


def git_short() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def git_status_short() -> str:
    return subprocess.check_output(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "evidence", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def manifest_problems() -> List[str]:
    rows = read_csv(STAGE42_MANIFEST)
    problems: List[str] = []
    if not rows:
        return ["manifest_missing_or_empty"]
    for row in rows:
        artifact = row.get("artifact", "")
        path = ROOT / artifact
        if row.get("exists") != "yes":
            problems.append(f"{artifact}:exists={row.get('exists')}")
        elif not path.exists():
            problems.append(f"{artifact}:missing")
        elif row.get("size_bytes") != str(path.stat().st_size):
            problems.append(f"{artifact}:size_mismatch")
        elif not row.get("sha256"):
            problems.append(f"{artifact}:missing_hash")
        elif sha256_file(path) != row.get("sha256"):
            problems.append(f"{artifact}:hash_mismatch")
    return problems


def build_checks(status_before_outputs: str, decision_evidence: str) -> List[Dict[str, str]]:
    final_audit = {row.get("item_id"): row for row in read_csv(FINAL_AUDIT)}
    stage41 = {row.get("unlock_id"): row for row in read_csv(STAGE41)}
    stage42 = {row.get("check_id"): row for row in read_csv(STAGE42_AUDIT)}
    stage43 = {row.get("step"): row for row in read_csv(STAGE43_SMOKE)}
    stage44 = {row.get("item"): row for row in read_csv(STAGE44_REPROBE)}
    stage45 = {row.get("check"): row for row in read_csv(STAGE45_ACTIVE_STATE)}
    stage46 = {row.get("check"): row for row in read_csv(STAGE46_WSL_TARGET)}
    stage47 = {row.get("r"): row for row in read_csv(STAGE47_WSL_FULL_SAB)}
    stage48 = {row.get("r"): row for row in read_csv(STAGE48_WSL_NOISE)}
    stage49 = {row.get("r"): row for row in read_csv(STAGE49_WSL_REPEATED_FULL_SAB)}
    stage50 = {row.get("evidence_id"): row for row in read_csv(STAGE50_PERF_MATRIX)}
    stage51 = {row.get("frontier_id"): row for row in read_csv(STAGE51_GOAL_FRONTIER)}
    stage52 = {row.get("unlock_id"): row for row in read_csv(STAGE52_UNLOCK_READINESS)}
    stage53 = {row.get("step"): row for row in read_csv(STAGE53_FINAL_RECHECK)}
    stage54 = {row.get("step"): row for row in read_csv(STAGE54_DEFAULT_FINAL_RECHECK)}
    stage55 = {row.get("gate"): row for row in read_csv(STAGE55_EXTERNAL_PAPER_PROBE)}
    stage56 = {row.get("step"): row for row in read_csv(STAGE56_FINAL_RECHECK_STAGE55)}
    stage57 = {row.get("audit_id"): row for row in read_csv(STAGE57_SCOPE_LABEL_AUDIT)}
    stage58 = {row.get("step"): row for row in read_csv(STAGE58_FINAL_RECHECK_STAGE57)}
    stage59 = {row.get("route_id"): row for row in read_csv(STAGE59_COMPLETION_ROUTE)}
    stage60 = {row.get("step"): row for row in read_csv(STAGE60_FINAL_RECHECK_STAGE59)}
    stage61 = {row.get("probe"): row for row in read_csv(STAGE61_NATIVE_PERF_UNLOCK)}
    stage62 = {row.get("gate"): row for row in read_csv(STAGE62_FULLTEXT_UNLOCK)}
    stage64a = {row.get("gate"): row for row in read_csv(STAGE64A_POST_VARIANT_REFRESH)}
    stage65a = {row.get("gate"): row for row in read_csv(STAGE65A_R4_UNROLLED)}
    stage66a = {row.get("gate"): row for row in read_csv(STAGE66A_POST_VARIANT_FINAL_RECHECK)}
    stage67 = {row.get("step"): row for row in read_csv(STAGE67_FINAL_RECHECK_STAGE66)}
    stage67_decision = {
        row.get("gate"): row for row in read_csv(STAGE67_FINAL_RECHECK_STAGE66_DECISION)
    }
    stage68 = {row.get("gate"): row for row in read_csv(STAGE68_FRONTIER_CLOSURE_CONSISTENCY)}
    stage69 = {row.get("gate"): row for row in read_csv(STAGE69_LOCAL_VARIANT_FEASIBILITY)}
    stage70 = {row.get("gate"): row for row in read_csv(STAGE70_EXTERNAL_UNLOCK_PREFLIGHT)}
    stage71 = {row.get("step"): row for row in read_csv(STAGE71_FINAL_RECHECK_STAGE70)}
    stage71_decision = {
        row.get("gate"): row for row in read_csv(STAGE71_FINAL_RECHECK_STAGE70_DECISION)
    }
    stage72 = {row.get("gate"): row for row in read_csv(STAGE72_EXTERNAL_SOURCE_REFRESH)}
    stage73 = {row.get("step"): row for row in read_csv(STAGE73_FINAL_RECHECK_STAGE72)}
    stage73_decision = {
        row.get("gate"): row for row in read_csv(STAGE73_FINAL_RECHECK_STAGE72_DECISION)
    }
    stage74 = {row.get("gate"): row for row in read_csv(STAGE74_R_SCALING_BOUNDARY)}
    stage75 = {row.get("gate"): row for row in read_csv(STAGE75_RGT4_PROFILE_BOUNDARY)}
    stage76 = {row.get("gate"): row for row in read_csv(STAGE76_RGT4_KERNEL_FEASIBILITY)}
    stage77 = {row.get("gate"): row for row in read_csv(STAGE77_RGT4_FUSED_MAT_KERNEL)}
    stage78 = {row.get("gate"): row for row in read_csv(STAGE78_RGT4_FUSED_REPEATED_GATES)}
    stage79 = {row.get("gate"): row for row in read_csv(STAGE79_RGT4_FUSED_HIGH_STAT)}
    stage80 = {row.get("gate"): row for row in read_csv(STAGE80_PROMOTION_POLICY_AUDIT)}
    stage81 = {row.get("gate"): row for row in read_csv(STAGE81_NEXT_VARIANT_TRIAGE)}
    stage82 = {row.get("gate"): row for row in read_csv(STAGE82_POST_H11_PROFILE)}
    stage83 = {row.get("gate"): row for row in read_csv(STAGE83_MAT_BODY_DESIGN_CHECK)}
    stage84 = {row.get("gate"): row for row in read_csv(STAGE84_H13_R6_TILE_SWEEP)}
    stage86 = {
        row.get("gate"): row for row in read_csv(STAGE86_SECONDARY_CMUX_MATERIALIZATION)
    }
    stage87 = {
        row.get("gate"): row for row in read_csv(STAGE87_H14_BACKEND_FROM_DFT_ADD)
    }
    stage88 = {
        row.get("gate"): row for row in read_csv(STAGE88_H14_BACKEND_REPEATED_GATES)
    }
    stage89 = {
        row.get("gate"): row for row in read_csv(STAGE89_H14_PROMOTION_POLICY)
    }
    stage90 = {
        row.get("gate"): row for row in read_csv(STAGE90_EXTERNAL_CLAIM_UNLOCK)
    }
    stage91 = {row.get("gate"): row for row in read_csv(STAGE91_FINAL_PACKAGE)}
    stage92 = {
        row.get("gate"): row for row in read_csv(STAGE92_EXTERNAL_UNLOCK_EXECUTION)
    }
    stage93 = {
        row.get("gate"): row for row in read_csv(STAGE93_EXTERNAL_LANE_ATTEMPT)
    }
    stage94 = {
        row.get("gate"): row for row in read_csv(STAGE94_LOCAL_FRONTIER_AUDIT)
    }
    stage95 = {
        row.get("gate"): row for row in read_csv(STAGE95_PUBLIC_SOURCE_REPROBE)
    }
    stage96 = {
        row.get("gate"): row for row in read_csv(STAGE96_UPSTREAM_DELTA_AUDIT)
    }
    stage97 = {
        row.get("gate"): row for row in read_csv(STAGE97_SOURCE_DELTA_GUARD)
    }
    stage98 = {
        row.get("gate"): row for row in read_csv(STAGE98_CURRENT_SMOKE_REFRESH)
    }
    stage99 = {
        row.get("gate"): row for row in read_csv(STAGE99_EXTERNAL_BLOCKER_REPROBE)
    }
    stage100 = {
        row.get("gate"): row for row in read_csv(STAGE100_FULLTEXT_ANCHOR_PREFILL)
    }
    stage44_recheck = {row.get("step"): row for row in read_csv(STAGE44_RECHECK)}
    default_recheck = {row.get("step"): row for row in read_csv(DEFAULT_RECHECK)}
    closure_recheck = {row.get("step"): row for row in read_csv(CLOSURE_RECHECK)}
    run_log = read_csv(RUN_LOG)
    artifact_manifest = ARTIFACT_MANIFEST.read_text(encoding="utf-8") if ARTIFACT_MANIFEST.exists() else ""

    stage41_mismatches = []
    expected_stage41 = {
        "S41-FULLTEXT-INTAKE": "READY_FOR_MANUAL_REVIEW",
        "S41-NATIVE-PERF-INTAKE": "WAIT_NATIVE_PERF",
        "S41-EXTERNAL-REGISTRATION": "READY_TO_REGISTER",
        "S41-FINAL-RECHECK": "READY_AFTER_UNLOCKS",
    }
    for unlock_id, expected in expected_stage41.items():
        got = stage41.get(unlock_id, {}).get("readiness", "MISSING")
        if got != expected:
            stage41_mismatches.append(f"{unlock_id}:{got}!={expected}")

    stage43_mismatches = []
    for step in ["scalar_binary_full_run", "pvw_target_full_gate", "scalar_ternary_build"]:
        got = stage43.get(step, {}).get("status", "MISSING")
        if got != "PASS":
            stage43_mismatches.append(f"{step}:{got}!=PASS")

    stage44_mismatches = []
    expected_stage44 = {
        "citation_probe_command": "PASS",
        "fulltext_pdf_access": "BLOCKED",
        "native_perf_hardware_counter_gate": "BLOCKED",
        "external_fulltext_intake": "MISSING",
        "external_native_perf_intake": "MISSING",
        "stage44_decision": "WAIT_EXTERNAL_UNLOCKS",
    }
    for item, expected in expected_stage44.items():
        got = stage44.get(item, {}).get("status", "MISSING")
        if got != expected:
            stage44_mismatches.append(f"{item}:{got}!={expected}")

    stage45_mismatches = []
    expected_stage45 = {
        "ffnt_active_state_kernel_gate": "PASS",
        "spqlios_avx512_windows_build": "BLOCKED_WINDOWS_ASSEMBLER",
    }
    for item, expected in expected_stage45.items():
        got = stage45.get(item, {}).get("status", "MISSING")
        if got != expected:
            stage45_mismatches.append(f"{item}:{got}!={expected}")

    stage42_stage45_ok = (
        stage42.get("S42-STAGE45-ACTIVE-STATE", {}).get("status") == "PASS"
    )
    stage46_status = stage46.get("wsl_spqlios_avx512_target_gate", {}).get(
        "status", "MISSING"
    )
    stage42_stage46_ok = stage42.get("S42-STAGE46-WSL-TARGET", {}).get("status") == "PASS"
    stage47_mismatches = []
    for r_value in ["2", "4"]:
        row_data = stage47.get(r_value)
        if not row_data:
            stage47_mismatches.append(f"r={r_value}:missing")
            continue
        if row_data.get("status") != "PASS":
            stage47_mismatches.append(f"r={r_value}:status={row_data.get('status')}")
        try:
            speedup = float(row_data.get("speedup_vs_scalar_repeated", "0"))
        except ValueError:
            speedup = 0.0
        if speedup <= 1.0:
            stage47_mismatches.append(
                f"r={r_value}:speedup={row_data.get('speedup_vs_scalar_repeated')}"
            )
    stage42_stage47_ok = (
        stage42.get("S42-STAGE47-WSL-FULL-SAB", {}).get("status") == "PASS"
    )
    stage48_mismatches = []
    for r_value in ["2", "4"]:
        row_data = stage48.get(r_value)
        if not row_data:
            stage48_mismatches.append(f"r={r_value}:missing")
            continue
        if row_data.get("status") != "PASS":
            stage48_mismatches.append(f"r={r_value}:status={row_data.get('status')}")
        for field in ["pvw_failures", "scalar_failures", "pair_failures"]:
            if row_data.get(field) != "0":
                stage48_mismatches.append(f"r={r_value}:{field}={row_data.get(field)}")
    stage42_stage48_ok = stage42.get("S42-STAGE48-WSL-NOISE", {}).get("status") == "PASS"
    stage49_mismatches = []
    for r_value in ["2", "4"]:
        row_data = stage49.get(r_value)
        if not row_data:
            stage49_mismatches.append(f"r={r_value}:missing")
            continue
        if row_data.get("status") != "PASS":
            stage49_mismatches.append(f"r={r_value}:status={row_data.get('status')}")
        if row_data.get("runs") != "3":
            stage49_mismatches.append(f"r={r_value}:runs={row_data.get('runs')}")
        try:
            speedup_min = float(row_data.get("speedup_min", "0"))
        except ValueError:
            speedup_min = 0.0
        if speedup_min <= 1.0:
            stage49_mismatches.append(f"r={r_value}:speedup_min={row_data.get('speedup_min')}")
    stage42_stage49_ok = (
        stage42.get("S42-STAGE49-WSL-REPEATED-FULL-SAB", {}).get("status") == "PASS"
    )
    stage50_mismatches = []
    required_stage50_ids = [
        "stage36_target_perf_r2",
        "stage47_current_head_smoke_r2",
        "stage49_current_head_repeated_r2",
        "stage36_target_perf_r4",
        "stage47_current_head_smoke_r4",
        "stage49_current_head_repeated_r4",
    ]
    for evidence_id in required_stage50_ids:
        row_data = stage50.get(evidence_id)
        if not row_data:
            stage50_mismatches.append(f"{evidence_id}:missing")
            continue
        if row_data.get("status") != "PASS":
            stage50_mismatches.append(f"{evidence_id}:status={row_data.get('status')}")
    for evidence_id in ["stage36_target_perf_r2", "stage36_target_perf_r4"]:
        row_data = stage50.get(evidence_id, {})
        try:
            ci95_low = float(row_data.get("ci95_low", "0"))
        except ValueError:
            ci95_low = 0.0
        if ci95_low <= 1.0:
            stage50_mismatches.append(f"{evidence_id}:ci95_low={row_data.get('ci95_low')}")
        if "not novelty/theory/all-parameter" not in row_data.get("claim_policy", ""):
            stage50_mismatches.append(f"{evidence_id}:claim_policy_missing_guardrail")
    for evidence_id in ["stage49_current_head_repeated_r2", "stage49_current_head_repeated_r4"]:
        row_data = stage50.get(evidence_id, {})
        if row_data.get("consistency_with_stage36") != "CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95":
            stage50_mismatches.append(f"{evidence_id}:consistency={row_data.get('consistency_with_stage36')}")
        if row_data.get("stats_sanity_label") != "CURRENT_HEAD_STABILITY_SUPPORTED_NOT_HIGH_STAT_CLAIM":
            stage50_mismatches.append(f"{evidence_id}:stats_label={row_data.get('stats_sanity_label')}")
    stage42_stage50_ok = (
        stage42.get("S42-STAGE50-PERFORMANCE-MATRIX", {}).get("status") == "PASS"
    )
    stage51_mismatches = []
    for frontier_id in ["G1", "G2", "G3", "G4", "G5", "G6"]:
        status = stage51.get(frontier_id, {}).get("status", "MISSING")
        if not status.startswith("LOCAL"):
            stage51_mismatches.append(f"{frontier_id}:status={status}")
    for frontier_id in ["B1", "B2"]:
        status = stage51.get(frontier_id, {}).get("status", "MISSING")
        if "BLOCKED" not in status:
            stage51_mismatches.append(f"{frontier_id}:status={status}")
    b3_status = stage51.get("B3", {}).get("status", "MISSING")
    if "BLOCKED" not in b3_status and b3_status != "EXTERNAL_REVIEW_REQUIRED":
        stage51_mismatches.append(f"B3:status={b3_status}")
    g9_status = stage51.get("G9", {}).get("status", "MISSING")
    if g9_status not in {
        "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
        "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED",
    }:
        stage51_mismatches.append(f"G9:status={g9_status}")
    stage42_stage51_ok = (
        stage42.get("S42-STAGE51-GOAL-FRONTIER", {}).get("status") == "PASS"
    )
    stage52_mismatches = []
    expected_stage52 = {
        "S52-NATIVE-PERF": {"WAIT_NATIVE_PERF"},
        "S52-FULLTEXT-686": {"WAIT_EXTERNAL_FULLTEXT", "READY_FOR_MANUAL_REVIEW"},
        "S52-NOVELTY-REVIEW": {"WAIT_MANUAL_FULLTEXT_REVIEW"},
        "S52-EXTERNAL-REGISTRATION": {"WAIT_EXTERNAL_ARTIFACTS", "READY_TO_REGISTER"},
        "S52-FINAL-RECHECK": {"WAIT_UNLOCKS", "READY_AFTER_UNLOCKS"},
    }
    for unlock_id, expected_readiness in expected_stage52.items():
        row_data = stage52.get(unlock_id)
        if not row_data:
            stage52_mismatches.append(f"{unlock_id}:missing")
            continue
        if row_data.get("readiness") not in expected_readiness:
            stage52_mismatches.append(f"{unlock_id}:readiness={row_data.get('readiness')}")
        for field in ["command", "expected_artifacts", "acceptance_gate", "failure_policy"]:
            if not row_data.get(field, "").strip():
                stage52_mismatches.append(f"{unlock_id}:{field}=empty")
    stage42_stage52_ok = (
        stage42.get("S42-STAGE52-EXTERNAL-UNLOCK-READINESS", {}).get("status") == "PASS"
    )
    stage53_mismatches = []
    for step in [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage50_performance_matrix",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage42_evidence_closure",
    ]:
        status = stage53.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            stage53_mismatches.append(f"{step}:status={status}")
    final_decision = stage53.get("final_decision", {}).get("status", "MISSING")
    if final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        stage53_mismatches.append(f"final_decision:status={final_decision}")
    stage42_stage53_ok = (
        stage42.get("S42-STAGE53-FINAL-RECHECK-INTEGRATION", {}).get("status") == "PASS"
    )
    stage54_mismatches = []
    for step in [
        "stage28_perf_gate",
        "stage27_final_package",
        "external_evidence_intake",
        "conditional_backlog_audit",
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage50_performance_matrix",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage42_evidence_closure",
    ]:
        status = stage54.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            stage54_mismatches.append(f"{step}:status={status}")
    final_decision = stage54.get("final_decision", {}).get("status", "MISSING")
    if final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        stage54_mismatches.append(f"final_decision:status={final_decision}")
    stage42_stage54_ok = (
        stage42.get("S42-STAGE54-DEFAULT-FINAL-RECHECK", {}).get("status") == "PASS"
    )
    stage55_mismatches = []
    stage55_expected = {
        "crossref_doi_metadata": "PASS",
        "official_metadata_visibility": "PASS",
        "official_fulltext_pdf_access": "BLOCKED",
        "cloudflare_block_recorded": "PASS",
        "stage55_decision": "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW",
    }
    for gate, expected in stage55_expected.items():
        got = stage55.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage55_mismatches.append(f"{gate}:{got}!={expected}")
    stage42_stage55_ok = (
        stage42.get("S42-STAGE55-EXTERNAL-PAPER-PROBE", {}).get("status") == "PASS"
    )
    stage56_mismatches = []
    for step in [
        "stage55_external_paper_probe",
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage42_evidence_closure",
    ]:
        got = stage56.get(step, {}).get("status", "MISSING")
        if got != "PASS":
            stage56_mismatches.append(f"{step}:status={got}")
    final_decision = stage56.get("final_decision", {}).get("status", "MISSING")
    if final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        stage56_mismatches.append(f"final_decision:status={final_decision}")
    if stage56.get("stage50_performance_matrix", {}).get("status", "MISSING") != "SKIPPED":
        stage56_mismatches.append(
            "stage50_performance_matrix:status="
            f"{stage56.get('stage50_performance_matrix', {}).get('status', 'MISSING')}"
        )
    stage42_stage56_ok = (
        stage42.get("S42-STAGE56-FINAL-RECHECK-STAGE55", {}).get("status") == "PASS"
    )
    stage57_mismatches = []
    for audit_id in [
        "S57-ROADMAP-LATEST-STAGE",
        "S57-STAGE51-G6-LABEL",
        "S57-NO-STALE-CURRENT-LABELS",
        "S57-CURRENT-FILES-MENTION-LATEST",
    ]:
        got = stage57.get(audit_id, {}).get("status", "MISSING")
        if got != "PASS":
            stage57_mismatches.append(f"{audit_id}:status={got}")
    stage42_stage57_ok = (
        stage42.get("S42-STAGE57-SCOPE-LABEL-AUDIT", {}).get("status") == "PASS"
    )
    stage58_mismatches = []
    for step in [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage42_evidence_closure",
    ]:
        got = stage58.get(step, {}).get("status", "MISSING")
        if got != "PASS":
            stage58_mismatches.append(f"{step}:status={got}")
    final_decision = stage58.get("final_decision", {}).get("status", "MISSING")
    if final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        stage58_mismatches.append(f"final_decision:status={final_decision}")
    stage42_stage58_ok = (
        stage42.get("S42-STAGE58-FINAL-RECHECK-STAGE57", {}).get("status") == "PASS"
    )
    stage59_mismatches = []
    expected_stage59 = {
        "S59-R1-SCOPED-ENGINEERING": "LOCAL_READY",
        "S59-R2-CURRENT-HEAD-REFRESH": "READY_LOCAL_REFRESH",
        "S59-R3-NATIVE-PERF": "EXTERNAL_BLOCKED",
        "S59-R4-FULLTEXT-686": "EXTERNAL_REVIEW_REQUIRED",
        "S59-R5-NOVELTY-REVIEW": "EXTERNAL_REVIEW_BLOCKED",
        "S59-R6-OPTIONAL-VARIANTS": "READY_OPTIONAL_LOCAL_TRIAGE",
        "S59-R7-FINAL-PAPER-PACKAGE": "SCOPED_FINAL_PACKAGE_READY_EXTERNAL_REVIEW_REQUIRED",
    }
    for route_id, expected_status in expected_stage59.items():
        got = stage59.get(route_id, {}).get("status", "MISSING")
        if got != expected_status:
            stage59_mismatches.append(f"{route_id}:status={got}")
    stage42_stage59_ok = (
        stage42.get("S42-STAGE59-COMPLETION-ROUTE", {}).get("status") == "PASS"
    )
    stage60_mismatches = []
    for step in [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage59_completion_route",
        "stage42_evidence_closure",
    ]:
        got = stage60.get(step, {}).get("status", "MISSING")
        if got != "PASS":
            stage60_mismatches.append(f"{step}:status={got}")
    final_decision = stage60.get("final_decision", {}).get("status", "MISSING")
    if final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        stage60_mismatches.append(f"final_decision:status={final_decision}")
    for step in [
        "stage27_citation_probe",
        "stage27_related_work_access_probe",
        "stage28_perf_gate",
        "stage55_external_paper_probe",
        "stage50_performance_matrix",
    ]:
        got = stage60.get(step, {}).get("status", "MISSING")
        if got != "SKIPPED":
            stage60_mismatches.append(f"{step}:status={got}")
    stage42_stage60_ok = (
        stage42.get("S42-STAGE60-FINAL-RECHECK-STAGE59", {}).get("status") == "PASS"
    )
    stage61_mismatches = []
    stage61_environment = stage61.get("environment", {}).get("status", "MISSING")
    stage61_hardware = stage61.get("hardware_counter_gate", {}).get("status", "MISSING")
    stage61_perf_command = stage61.get("perf_command", {}).get("status", "MISSING")
    stage61_bench_correctness = stage61.get("bench_correctness", {}).get("status")
    if stage61_environment != "RECORDED":
        stage61_mismatches.append(f"environment:status={stage61_environment}")
    if stage61_hardware not in {"PASS", "BLOCKED", "READY_FOR_BENCH"}:
        stage61_mismatches.append(f"hardware_counter_gate:status={stage61_hardware}")
    if stage61_hardware == "PASS" and stage61_bench_correctness != "PASS":
        stage61_mismatches.append(f"bench_correctness:status={stage61_bench_correctness}")
    if stage61_hardware == "BLOCKED" and stage61_perf_command not in {"MISSING", "AVAILABLE"}:
        stage61_mismatches.append(f"perf_command:status={stage61_perf_command}")
    stage42_stage61_ok = (
        stage42.get("S42-STAGE61-NATIVE-PERF-UNLOCK", {}).get("status") == "PASS"
    )
    stage62_mismatches = []
    stage62_decision = stage62.get("stage62_decision", {}).get("status", "MISSING")
    stage62_artifact = stage62.get("stage38_fulltext_artifact", {}).get("status", "MISSING")
    stage62_stage38 = stage62.get("stage38_decision", {}).get("status", "MISSING")
    stage62_external = stage62.get("external_fulltext_intake", {}).get("status", "MISSING")
    stage62_checklist = stage62.get("stage38_review_checklist", {}).get("status", "MISSING")
    if stage62_decision not in {
        "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW",
        "FULLTEXT_AVAILABLE_REVIEW_REQUIRED",
    }:
        stage62_mismatches.append(f"stage62_decision:status={stage62_decision}")
    if stage62_decision == "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW":
        expected = {
            "stage38_fulltext_artifact": stage62_artifact == "MISSING",
            "stage38_decision": stage62_stage38 == "BLOCKED_FULLTEXT_MISSING",
            "external_fulltext_intake": stage62_external == "MISSING",
            "stage38_review_checklist": "BLOCKED_FULLTEXT_MISSING" in stage62_checklist,
        }
        for item, ok in expected.items():
            if not ok:
                stage62_mismatches.append(f"{item}:unexpected")
    if stage62_decision == "FULLTEXT_AVAILABLE_REVIEW_REQUIRED" and stage62_artifact != "AVAILABLE_UNREVIEWED":
        stage62_mismatches.append(f"stage38_fulltext_artifact:status={stage62_artifact}")
    stage42_stage62_ok = (
        stage42.get("S42-STAGE62-FULLTEXT-UNLOCK", {}).get("status") == "PASS"
    )
    stage64a_mismatches = []
    expected_stage64a = {
        "stage64_current_smoke": "PASS",
        "stage64_full_sab_r2": "PASS",
        "stage64_full_sab_r4": "PASS",
        "stage64_final_noise": "PASS",
        "stage64_stage50_matrix": "PASS",
        "stage64_decision": "PASS_POST_VARIANT_REFRESH",
    }
    for gate, expected in expected_stage64a.items():
        got = stage64a.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage64a_mismatches.append(f"{gate}:status={got}")
    stage42_stage64a_ok = (
        stage42.get("S42-STAGE64A-POST-VARIANT-REFRESH", {}).get("status") == "PASS"
    )
    stage65a_mismatches = []
    expected_stage65a = {
        "stage65_correctness": "PASS",
        "stage65_kernel_dft_output": "NEGATIVE",
        "stage65_kernel_full_output": "NEGATIVE",
        "stage65_full_sab_r4": "NEGATIVE",
        "stage65_instruction_proxy": "RECORDED",
        "stage65_scalar_baseline_smoke": "PASS",
        "stage65_decision": "NEGATIVE_NOT_PROMOTED",
    }
    for gate, expected in expected_stage65a.items():
        got = stage65a.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage65a_mismatches.append(f"{gate}:status={got}")
    stage42_stage65a_ok = (
        stage42.get("S42-STAGE65A-R4-UNROLLED", {}).get("status") == "PASS"
    )
    stage66a_mismatches = []
    expected_stage66a = {
        "stage66_final_recheck_core": "PASS",
        "stage66_stage64a_continuity": "PASS",
        "stage66_stage65a_negative_variant": "PASS",
        "stage66_decision": "PASS_POST_VARIANT_FINAL_RECHECK",
    }
    for gate, expected in expected_stage66a.items():
        got = stage66a.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage66a_mismatches.append(f"{gate}:status={got}")
    stage42_stage66a_ok = (
        stage42.get("S42-STAGE66A-POST-VARIANT-FINAL-RECHECK", {}).get("status")
        == "PASS"
    )
    stage67_mismatches = []
    expected_stage67_summary = {
        "stage66_post_variant_final_recheck": "PASS",
        "stage42_evidence_closure": "SKIPPED",
        "final_decision": "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
    }
    expected_stage67_decision = {
        "stage67_final_recheck_stage66": "PASS",
        "stage67_stage66_summary": "PASS",
        "stage67_decision": "PASS_FINAL_RECHECK_STAGE66_INTEGRATION",
    }
    for step, expected in expected_stage67_summary.items():
        got = stage67.get(step, {}).get("status", "MISSING")
        if got != expected:
            stage67_mismatches.append(f"{step}:status={got}")
    for gate, expected in expected_stage67_decision.items():
        got = stage67_decision.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage67_mismatches.append(f"{gate}:status={got}")
    stage42_stage67_ok = (
        stage42.get("S42-STAGE67-FINAL-RECHECK-STAGE66", {}).get("status") == "PASS"
    )
    stage68_mismatches = []
    expected_stage68 = {
        "stage68_stage42_label": "PASS",
        "stage68_stage51_g6": "PASS",
        "stage68_stage57_scope_label": "PASS",
        "stage68_stage59_route": "PASS",
        "stage68_decision": "PASS_FRONTIER_CLOSURE_CONSISTENCY",
    }
    for gate, expected in expected_stage68.items():
        got = stage68.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage68_mismatches.append(f"{gate}:status={got}")
    stage42_stage68_ok = (
        stage42.get("S42-STAGE68-FRONTIER-CLOSURE-CONSISTENCY", {}).get("status")
        == "PASS"
    )
    stage69_mismatches = []
    expected_stage69 = {
        "stage69_inputs_available": "PASS",
        "stage69_h2_postproc_tail": "DEFER_TAIL_SMALL",
        "stage69_h3_sparse_selector_theory": "REJECT_CURRENT_SPARSE_SELECTOR_SHORTCUT",
        "stage69_h4_schedule_fusion": "NEUTRAL_NOT_PROMOTED",
        "stage69_h7_avx512_layout": "BLOCKED_NATIVE_COUNTERS_OR_NEGATIVE_PRIOR",
        "stage69_h8_nonbinary_branch": "BLOCKED_FULLTEXT_NONBINARY_DESIGN",
        "stage69_no_unblocked_local_variant": "PASS_NO_UNBLOCKED_LOCAL_VARIANT",
        "stage69_decision": "PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED",
    }
    for gate, expected in expected_stage69.items():
        got = stage69.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage69_mismatches.append(f"{gate}:status={got}")
    stage42_stage69_ok = (
        stage42.get("S42-STAGE69-LOCAL-VARIANT-FEASIBILITY", {}).get("status")
        == "PASS"
    )
    stage70_mismatches = []
    expected_stage70 = {
        "stage70_route_inputs": "PASS",
        "stage70_native_perf_preflight": "WAIT_NATIVE_PERF",
        "stage70_fulltext_stage62_preflight": "WAIT_FULLTEXT_ARTIFACT",
        "stage70_novelty_preflight": "WAIT_FULLTEXT_OR_MANUAL_REVIEW",
        "stage70_local_variant_preflight": "NO_LOCAL_VARIANT_READY",
        "stage70_decision": "PASS_EXTERNAL_UNLOCK_PREFLIGHT_STRONGER_CLAIMS_BLOCKED",
    }
    for gate, expected in expected_stage70.items():
        got = stage70.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage70_mismatches.append(f"{gate}:status={got}")
    stage70_fulltext_env = stage70.get("stage70_fulltext_env_preflight", {}).get(
        "status", "MISSING"
    )
    if stage70_fulltext_env not in {
        "MISSING_ENV",
        "PATH_NOT_FOUND",
        "INVALID_FILE",
        "AVAILABLE_UNREVIEWED",
    }:
        stage70_mismatches.append(
            f"stage70_fulltext_env_preflight:status={stage70_fulltext_env}"
        )
    stage42_stage70_ok = (
        stage42.get("S42-STAGE70-EXTERNAL-UNLOCK-PREFLIGHT", {}).get("status")
        == "PASS"
    )
    stage71_mismatches = []
    for step in [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage59_completion_route",
        "stage70_external_unlock_preflight",
        "stage42_evidence_closure",
    ]:
        got = stage71.get(step, {}).get("status", "MISSING")
        if got != "PASS":
            stage71_mismatches.append(f"{step}:status={got}")
    for step in [
        "stage27_citation_probe",
        "stage27_related_work_access_probe",
        "stage28_perf_gate",
        "stage27_final_package",
        "external_evidence_intake",
        "stage33_current_smoke",
        "conditional_backlog_audit",
        "stage44_external_reprobe",
        "stage55_external_paper_probe",
        "stage50_performance_matrix",
        "stage66_post_variant_final_recheck",
    ]:
        got = stage71.get(step, {}).get("status", "MISSING")
        if got != "SKIPPED":
            stage71_mismatches.append(f"{step}:status={got}")
    stage71_final_decision = stage71.get("final_decision", {}).get("status", "MISSING")
    if stage71_final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        stage71_mismatches.append(f"final_decision:status={stage71_final_decision}")
    expected_stage71_decision = {
        "stage71_final_recheck_stage70": "PASS",
        "stage71_stage70_summary": "PASS",
        "stage71_decision": "PASS_FINAL_RECHECK_STAGE70_INTEGRATION",
    }
    for gate, expected in expected_stage71_decision.items():
        got = stage71_decision.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage71_mismatches.append(f"{gate}:status={got}")
    stage42_stage71_ok = (
        stage42.get("S42-STAGE71-FINAL-RECHECK-STAGE70", {}).get("status")
        == "PASS"
    )
    stage72_mismatches = []
    expected_stage72 = {
        "stage72_author_metadata_route": "PASS",
        "stage72_doi_metadata_route": "PASS",
        "stage72_code_route": "PASS",
        "stage72_official_fulltext_routes": "WAIT_FULLTEXT_ARTIFACT",
        "stage72_claim_policy": "KEEP_STRONGER_CLAIMS_BLOCKED",
        "stage72_decision": "PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED",
    }
    for gate, expected in expected_stage72.items():
        got = stage72.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage72_mismatches.append(f"{gate}:status={got}")
    stage42_stage72_ok = (
        stage42.get("S42-STAGE72-EXTERNAL-SOURCE-REFRESH", {}).get("status")
        == "PASS"
    )
    stage73_mismatches = []
    for step in [
        "stage72_external_source_refresh",
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage59_completion_route",
        "stage70_external_unlock_preflight",
        "stage42_evidence_closure",
    ]:
        got = stage73.get(step, {}).get("status", "MISSING")
        if got != "PASS":
            stage73_mismatches.append(f"{step}:status={got}")
    for step in [
        "stage27_citation_probe",
        "stage27_related_work_access_probe",
        "stage28_perf_gate",
        "stage27_final_package",
        "external_evidence_intake",
        "stage33_current_smoke",
        "conditional_backlog_audit",
        "stage44_external_reprobe",
        "stage55_external_paper_probe",
        "stage50_performance_matrix",
        "stage66_post_variant_final_recheck",
    ]:
        got = stage73.get(step, {}).get("status", "MISSING")
        if got != "SKIPPED":
            stage73_mismatches.append(f"{step}:status={got}")
    stage73_final_decision = stage73.get("final_decision", {}).get("status", "MISSING")
    if stage73_final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        stage73_mismatches.append(f"final_decision:status={stage73_final_decision}")
    expected_stage73_decision = {
        "stage73_final_recheck_stage72": "PASS",
        "stage73_stage72_summary": "PASS",
        "stage73_decision": "PASS_FINAL_RECHECK_STAGE72_INTEGRATION",
    }
    for gate, expected in expected_stage73_decision.items():
        got = stage73_decision.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage73_mismatches.append(f"{gate}:status={got}")
    stage42_stage73_ok = (
        stage42.get("S42-STAGE73-FINAL-RECHECK-STAGE72", {}).get("status")
        == "PASS"
    )
    stage74_mismatches = []
    expected_stage74 = {
        "stage74_r6_full_sab_smoke": "PASS",
        "stage74_r8_full_sab_smoke": "PASS",
        "stage74_rgt4_boundary": "NOT_PROMOTED_R_GT4_BELOW_R4_SCREEN",
        "stage74_decision": "PASS_R_GT4_BOUNDARY_RECORDED_NOT_PROMOTED",
    }
    for gate, expected in expected_stage74.items():
        got = stage74.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage74_mismatches.append(f"{gate}:status={got}")
    stage42_stage74_ok = (
        stage42.get("S42-STAGE74-R-SCALING-BOUNDARY", {}).get("status")
        == "PASS"
    )
    stage75_mismatches = []
    expected_stage75 = {
        "stage75_r6_body_profile": "PASS",
        "stage75_r8_body_profile": "PASS",
        "stage75_schedule_count_invariant": "PASS",
        "stage75_rgt4_profile_boundary": "NOT_PROMOTED_PROFILE_BOUNDARY",
        "stage75_decision": "PASS_RGT4_PROFILE_BOUNDARY_RECORDED_NOT_PROMOTED",
    }
    for gate, expected in expected_stage75.items():
        got = stage75.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage75_mismatches.append(f"{gate}:status={got}")
    stage42_stage75_ok = (
        stage42.get("S42-STAGE75-RGT4-PROFILE-BOUNDARY", {}).get("status")
        == "PASS"
    )
    stage76_mismatches = []
    expected_stage76 = {
        "stage76_rgt4_kernel_correctness": "PASS",
        "stage76_r6_dft_output_kernel": "NEGATIVE_DFT_OUTPUT_NOT_PROMOTED",
        "stage76_r6_full_output_kernel": "SMOKE_POSITIVE_FULL_OUTPUT",
        "stage76_r8_dft_output_kernel": "NEGATIVE_DFT_OUTPUT_NOT_PROMOTED",
        "stage76_r8_full_output_kernel": "SMOKE_POSITIVE_LOW_MARGIN_FULL_OUTPUT",
        "stage76_mul_share_boundary": "PASS",
        "stage76_decision": "PASS_RGT4_KERNEL_FEASIBILITY_RECORDED_NO_PROMOTION",
    }
    for gate, expected in expected_stage76.items():
        got = stage76.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage76_mismatches.append(f"{gate}:status={got}")
    stage42_stage76_ok = (
        stage42.get("S42-STAGE76-RGT4-KERNEL-FEASIBILITY", {}).get("status")
        == "PASS"
    )
    stage77_mismatches = []
    expected_stage77 = {
        "stage77_generic_kernel_correctness": "PASS",
        "stage77_fused_kernel_correctness": "PASS",
        "stage77_kernel_fused_vs_generic": "PASS",
        "stage77_fused_dft_vs_scalar": "PARTIAL_R6_ONLY",
        "stage77_full_sab_smoke": "PASS",
        "stage77_r4_boundary": "REPEATED_GATES_REQUIRED",
        "stage77_decision": "PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED",
    }
    for gate, expected in expected_stage77.items():
        got = stage77.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage77_mismatches.append(f"{gate}:status={got}")
    stage42_stage77_ok = (
        stage42.get("S42-STAGE77-RGT4-FUSED-MAT-KERNEL", {}).get("status")
        == "PASS"
    )
    stage78_mismatches = []
    expected_stage78 = {
        "stage78_stage77_precondition": "PASS",
        "stage78_r6_repeated_full_sab": "PASS",
        "stage78_r8_stress_full_sab": "PASS",
        "stage78_r6_noise": "PASS",
        "stage78_r8_noise": "PASS",
        "stage78_resource": "PASS",
        "stage78_decision": "PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE",
    }
    for gate, expected in expected_stage78.items():
        got = stage78.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage78_mismatches.append(f"{gate}:status={got}")
    stage42_stage78_ok = (
        stage42.get("S42-STAGE78-RGT4-FUSED-REPEATED-GATES", {}).get("status")
        == "PASS"
    )
    stage79_mismatches = []
    expected_stage79 = {
        "stage79_stage78_precondition": "PASS",
        "stage79_r6_high_stat_full_sab": "PASS_R4_REGION_NOT_CONFIRMED",
        "stage79_r6_final_noise": "PASS",
        "stage79_r6_resource": "PASS",
        "stage79_decision": "PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED",
    }
    for gate, expected in expected_stage79.items():
        got = stage79.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage79_mismatches.append(f"{gate}:status={got}")
    stage42_stage79_ok = (
        stage42.get("S42-STAGE79-RGT4-FUSED-HIGH-STAT", {}).get("status")
        == "PASS"
    )
    stage80_mismatches = []
    expected_stage80 = {
        "stage80_stage79_precondition": "PASS",
        "stage80_performance_policy": "KEEP_EXPERIMENTAL_NOT_PROMOTED",
        "stage80_noise_resource_guard": "PASS",
        "stage80_default_path_guard": "PASS",
        "stage80_current_head_smoke": "PASS",
        "stage80_decision": "PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED",
    }
    for gate, expected in expected_stage80.items():
        got = stage80.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage80_mismatches.append(f"{gate}:status={got}")
    stage42_stage80_ok = (
        stage42.get("S42-STAGE80-PROMOTION-POLICY-AUDIT", {}).get("status")
        == "PASS"
    )
    stage81_mismatches = []
    expected_stage81 = {
        "stage81_inputs_available": "PASS",
        "stage81_h11_policy_state": "KEEP_EXPERIMENTAL_NOT_PROMOTED",
        "stage81_sparse_structured_mat_candidate": "BLOCKED_SECURITY_DESIGN_GAP",
        "stage81_rgt4_lane_or_tiling_candidate": "NOT_SELECTED_R6_EXPERIMENTAL_R8_WEAK",
        "stage81_postprocessing_candidate": "DEFER_TAIL_SMALL",
        "stage81_schedule_body_candidate": "SELECT_PROFILE_FIRST",
        "stage81_decision": "PASS_STAGE81_NEXT_VARIANT_TRIAGE_PROFILE_FIRST_NO_CODE_PROMOTION",
    }
    for gate, expected in expected_stage81.items():
        got = stage81.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage81_mismatches.append(f"{gate}:status={got}")
    stage42_stage81_ok = (
        stage42.get("S42-STAGE81-NEXT-VARIANT-TRIAGE", {}).get("status")
        == "PASS"
    )
    stage82_mismatches = []
    expected_stage82 = {
        "stage82_inputs_available": "PASS",
        "stage82_fused_r6_profile_counts": "PASS",
        "stage82_fused_vs_generic_profile": "PROFILE_ONLY_RECORDED",
        "stage82_component_attribution": "MAT_BODY_REMAINS_PRIMARY",
        "stage82_decision": "PASS_STAGE82_POST_H11_PROFILE_MAT_BODY_PRIMARY",
    }
    for gate, expected in expected_stage82.items():
        got = stage82.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage82_mismatches.append(f"{gate}:status={got}")
    stage42_stage82_ok = (
        stage42.get("S42-STAGE82-POST-H11-PROFILE", {}).get("status")
        == "PASS"
    )
    stage83_mismatches = []
    expected_stage83 = {
        "stage83_inputs_available": "PASS",
        "stage83_profile_bound": "PASS_MAT_BODY_PRIMARY_BUT_NOT_EXCLUSIVE",
        "stage83_amdahl_bound": "PASS_RECORDED",
        "stage83_security_boundary": "PASS_BLOCK_SPARSE_SKIP_WITHOUT_KEY_SECURITY_DESIGN",
        "stage83_candidate_screen": "SELECT_STAGE84_R6_TILE_SWEEP_PREFLIGHT",
        "stage83_decision": "PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT",
    }
    for gate, expected in expected_stage83.items():
        got = stage83.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage83_mismatches.append(f"{gate}:status={got}")
    stage42_stage83_ok = (
        stage42.get("S42-STAGE83-MAT-BODY-DESIGN-CHECK", {}).get("status")
        == "PASS"
    )
    stage84_mismatches = []
    expected_stage84 = {
        "stage84_inputs_available": "PASS",
        "stage84_kernel_correctness": "PASS",
        "stage84_r6_kernel_comparison": "PASS_KERNEL_POSITIVE",
        "stage84_r8_guard": "RECORDED_DIAGNOSTIC",
        "stage84_full_sab_smoke": "NEUTRAL_OR_NEGATIVE_FULL_SAB",
        "stage84_decision": "PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED",
    }
    for gate, expected in expected_stage84.items():
        got = stage84.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage84_mismatches.append(f"{gate}:status={got}")
    stage42_stage84_ok = (
        stage42.get("S42-STAGE84-H13-R6-TILE-SWEEP", {}).get("status")
        == "PASS"
    )
    stage86_mismatches = []
    expected_stage86 = {
        "stage86_inputs_available": "PASS",
        "stage86_non_mat_materiality": "PASS_NON_MAT_MATERIAL",
        "stage86_prior_neutral_guard": "PASS_DIFFERENT_LAYER_REQUIRED",
        "stage86_candidate_screen": "SELECT_BACKEND_FROM_DFT_ADD_CALLBACK_PREFLIGHT",
        "stage86_security_boundary": "PASS_NO_KEY_FORMAT_CHANGE",
        "stage86_decision": "PASS_STAGE86_SECONDARY_CMUX_MATERIALIZATION_SELECT_BACKEND_PREFLIGHT",
    }
    for gate, expected in expected_stage86.items():
        got = stage86.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage86_mismatches.append(f"{gate}:status={got}")
    stage42_stage86_ok = (
        stage42.get("S42-STAGE86-SECONDARY-CMUX-MATERIALIZATION", {}).get("status")
        == "PASS"
    )
    stage87_mismatches = []
    expected_stage87 = {
        "stage87_explicit_flag": "PASS_EXPLICIT_FLAG",
        "stage87_correctness_smoke": "PASS",
        "stage87_full_sab_smoke": "PASS_FULL_SAB_POSITIVE",
        "stage87_decision": "PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE",
    }
    for gate, expected in expected_stage87.items():
        got = stage87.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage87_mismatches.append(f"{gate}:status={got}")
    stage42_stage87_ok = (
        stage42.get("S42-STAGE87-H14-BACKEND-FROM-DFT-ADD", {}).get("status")
        == "PASS"
    )
    stage88_mismatches = []
    expected_stage88 = {
        "stage88_stage87_precondition": "PASS",
        "stage88_repeated_full_sab": "PASS_BACKEND_FASTER",
        "stage88_backend_vs_scalar": "PASS",
        "stage88_wrapper_reference": "PASS",
        "stage88_final_noise": "PASS",
        "stage88_resource": "PASS",
        "stage88_decision": "PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE",
    }
    for gate, expected in expected_stage88.items():
        got = stage88.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage88_mismatches.append(f"{gate}:status={got}")
    stage42_stage88_ok = (
        stage42.get("S42-STAGE88-H14-BACKEND-REPEATED-GATES", {}).get("status")
        == "PASS"
    )
    stage89_mismatches = []
    expected_stage89 = {
        "stage89_stage88_precondition": "PASS",
        "stage89_current_head_smoke": "PASS",
        "stage89_default_path_guard": "PASS",
        "stage89_stage80_policy_precedent": "PASS",
        "stage89_performance_policy": "PROMOTE_EXPLICIT_PATH_NOT_DEFAULT",
        "stage89_noise_resource_guard": "PASS",
        "stage89_claim_guard": "PASS",
        "stage89_decision": "PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT",
    }
    for gate, expected in expected_stage89.items():
        got = stage89.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage89_mismatches.append(f"{gate}:status={got}")
    stage42_stage89_ok = (
        stage42.get("S42-STAGE89-H14-PROMOTION-POLICY", {}).get("status")
        == "PASS"
    )
    stage90_mismatches = []
    expected_stage90 = {
        "stage90_stage89_precondition": "PASS",
        "stage90_citation_fulltext_probe": "PASS_PROBE_RECORDED_WAIT_FULLTEXT",
        "stage90_native_perf_unlock": "WAIT_NATIVE_PERF",
        "stage90_source_refresh_context": "PASS_METADATA_CODE_CONTEXT",
        "stage90_fulltext_unlock": "WAIT_FULLTEXT_ARTIFACT",
        "stage90_novelty_review_unlock": "WAIT_FULLTEXT_OR_MANUAL_REVIEW",
        "stage90_blocker_dashboard_guard": "PASS_BLOCKERS_REGISTERED",
        "stage90_decision": "PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED",
    }
    for gate, expected in expected_stage90.items():
        got = stage90.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage90_mismatches.append(f"{gate}:status={got}")
    stage42_stage90_ok = (
        stage42.get("S42-STAGE90-EXTERNAL-CLAIM-UNLOCK", {}).get("status")
        == "PASS"
    )
    stage91_mismatches = []
    expected_stage91 = {
        "stage91_smoke_current_code_guard": "PASS_CURRENT_SMOKE_INHERITED_SOURCE_UNCHANGED",
        "stage91_performance_gate": "PASS_SCOPED_COMPLETE_SAB_PERFORMANCE",
        "stage91_noise_resource_gate": "PASS_SCOPED_NOISE_RESOURCE",
        "stage91_stage89_policy_gate": "PASS_EXPLICIT_R6_POLICY_RECORDED",
        "stage91_external_claim_gate": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage91_existing_closure_gate": "PASS_PRE_STAGE91_CLOSURE_READY",
        "stage91_decision": "PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED",
    }
    for gate, expected in expected_stage91.items():
        got = stage91.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage91_mismatches.append(f"{gate}:status={got}")
    stage42_stage91_ok = (
        stage42.get("S42-STAGE91-FINAL-PACKAGE", {}).get("status") == "PASS"
    )
    stage92_mismatches = []
    expected_stage92 = {
        "stage92_stage91_precondition": "PASS",
        "stage92_unlock_sources": "PASS",
        "stage92_lane_packet": "PASS_EXTERNAL_LANES_RECORDED",
        "stage92_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage92_decision": "PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED",
    }
    for gate, expected in expected_stage92.items():
        got = stage92.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage92_mismatches.append(f"{gate}:status={got}")
    stage42_stage92_ok = (
        stage42.get("S42-STAGE92-EXTERNAL-UNLOCK-EXECUTION", {}).get("status")
        == "PASS"
    )
    stage93_mismatches = []
    expected_stage93 = {
        "stage93_stage92_precondition": "PASS",
        "stage93_native_perf_attempt": "BLOCKED_NATIVE_PERF_CURRENT_ENV",
        "stage93_local_fulltext_search": "LOCAL_FULLTEXT_NOT_FOUND",
        "stage93_external_intake_state": "PASS_EXTERNAL_INTAKE_STILL_MISSING",
        "stage93_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage93_decision": "PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED",
    }
    for gate, expected in expected_stage93.items():
        got = stage93.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage93_mismatches.append(f"{gate}:status={got}")
    stage42_stage93_ok = (
        stage42.get("S42-STAGE93-EXTERNAL-LANE-ATTEMPT", {}).get("status")
        == "PASS"
    )
    stage94_mismatches = []
    expected_stage94 = {
        "stage94_inputs_available": "PASS",
        "stage94_preferred_path_guard": "PASS_H14_C1_EXPLICIT_PATH_PREFERRED",
        "stage94_no_new_hotpath_guard": "PASS_NO_SAB_SOURCE_CHANGES_AFTER_STAGE89",
        "stage94_candidate_frontier": "PASS_NO_UNBLOCKED_LOCAL_HOTPATH_CANDIDATE",
        "stage94_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage94_decision": "PASS_STAGE94_LOCAL_FRONTIER_AUDIT_NO_NEW_HOTPATH",
    }
    for gate, expected in expected_stage94.items():
        got = stage94.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage94_mismatches.append(f"{gate}:status={got}")
    stage42_stage94_ok = (
        stage42.get("S42-STAGE94-LOCAL-FRONTIER-AUDIT", {}).get("status")
        == "PASS"
    )
    stage95_mismatches = []
    expected_stage95 = {
        "stage95_stage94_precondition": "PASS",
        "stage95_stage72_refresh": "PASS",
        "stage95_public_metadata_routes": "PASS_METADATA_CODE_VISIBLE",
        "stage95_direct_fulltext_routes": "WAIT_FULLTEXT_ARTIFACT",
        "stage95_stage93_consistency": "PASS",
        "stage95_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage95_decision": "PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED",
    }
    for gate, expected in expected_stage95.items():
        got = stage95.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage95_mismatches.append(f"{gate}:status={got}")
    stage42_stage95_ok = (
        stage42.get("S42-STAGE95-PUBLIC-SOURCE-REPROBE", {}).get("status")
        == "PASS"
    )
    stage96_mismatches = []
    expected_stage96 = {
        "stage96_stage95_precondition": "PASS",
        "stage96_remote_origin_main": "PASS_UPSTREAM_REF_AVAILABLE",
        "stage96_upstream_relation": "PASS_LOCAL_AHEAD_OF_UPSTREAM",
        "stage96_delta_classification": "PASS_DELTA_CLASSIFIED",
        "stage96_default_guard": "PASS_EXPLICIT_FLAGS_DEFAULT_FALSE",
        "stage96_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage96_decision": "PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED",
    }
    for gate, expected in expected_stage96.items():
        got = stage96.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage96_mismatches.append(f"{gate}:status={got}")
    stage42_stage96_ok = (
        stage42.get("S42-STAGE96-UPSTREAM-DELTA-AUDIT", {}).get("status")
        == "PASS"
    )
    stage97_mismatches = []
    expected_stage97 = {
        "stage97_stage96_precondition": "PASS",
        "stage97_source_delta_inventory": "PASS_SOURCE_DELTA_CLASSIFIED",
        "stage97_scalar_symbol_guard": "PASS_SCALAR_SYMBOLS_ISOLATED",
        "stage97_shared_backend_symbol_guard": "PASS_SHARED_BACKEND_SYMBOLS_ISOLATED",
        "stage97_build_flag_guard": "PASS_BUILD_FLAGS_DEFAULT_FALSE_AND_GATED",
        "stage97_smoke_evidence_guard": "PASS_SCALAR_SMOKE_EVIDENCE_PRESENT",
        "stage97_claim_guard": "PASS_SOURCE_GUARD_ONLY_NO_SPEEDUP_CLAIM",
        "stage97_decision": "PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED",
    }
    for gate, expected in expected_stage97.items():
        got = stage97.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage97_mismatches.append(f"{gate}:status={got}")
    stage42_stage97_ok = (
        stage42.get("S42-STAGE97-SOURCE-DELTA-GUARD", {}).get("status")
        == "PASS"
    )
    stage98_mismatches = []
    expected_stage98 = {
        "stage98_stage97_precondition": "PASS",
        "stage98_scalar_binary_smoke": "PASS_SCALAR_BINARY_FULL_RUN",
        "stage98_active_pvw_target_smoke": "PASS_ACTIVE_PVW_TARGET_GATE",
        "stage98_backend_pvw_target_smoke": "PASS_BACKEND_PVW_TARGET_GATE",
        "stage98_scalar_ternary_build": "PASS_SCALAR_TERNARY_BUILD",
        "stage98_raw_log_guard": "PASS_RAW_LOGS_PRESENT",
        "stage98_claim_guard": "PASS_CURRENT_SMOKE_ONLY_NO_SPEEDUP_CLAIM",
        "stage98_decision": "PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH",
    }
    for gate, expected in expected_stage98.items():
        got = stage98.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage98_mismatches.append(f"{gate}:status={got}")
    stage42_stage98_ok = (
        stage42.get("S42-STAGE98-CURRENT-SMOKE-REFRESH", {}).get("status")
        == "PASS"
    )
    stage99_mismatches = []
    expected_stage99 = {
        "stage99_stage98_precondition": "PASS",
        "stage99_native_perf_reprobe": "RECORDED_WAIT_NATIVE_PERF",
        "stage99_fulltext_reprobe": "RECORDED_FULLTEXT_CANDIDATE_REVIEW_REQUIRED",
        "stage99_public_route_matrix": "PASS_PUBLIC_ROUTES_RECORDED",
        "stage99_novelty_review_gate": "RECORDED_WAIT_NOVELTY_REVIEW",
        "stage99_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED_UNTIL_EXTERNAL_REVIEW",
        "stage99_decision": "PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_REVIEW_REQUIRED",
    }
    for gate, expected in expected_stage99.items():
        got = stage99.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage99_mismatches.append(f"{gate}:status={got}")
    stage42_stage99_ok = (
        stage42.get("S42-STAGE99-EXTERNAL-BLOCKER-REPROBE", {}).get("status")
        == "PASS"
    )
    stage100_mismatches = []
    expected_stage100 = {
        "stage100_stage99_precondition": "PASS",
        "stage100_fulltext_artifact": "PASS",
        "stage100_text_extract": "PASS",
        "stage100_anchor_candidates": "CANDIDATE_ANCHORS_GENERATED_REVIEW_REQUIRED",
        "stage100_stage38_prefill": "REVIEW_CHECKLIST_PREFILLED_REVIEW_REQUIRED",
        "stage100_claim_guard": "PASS_NO_CLAIM_UPGRADE",
        "stage100_decision": "PASS_STAGE100_FULLTEXT_ANCHOR_PREFILL_REVIEW_REQUIRED",
    }
    for gate, expected in expected_stage100.items():
        got = stage100.get(gate, {}).get("status", "MISSING")
        if got != expected:
            stage100_mismatches.append(f"{gate}:status={got}")
    stage42_stage100_ok = (
        stage42.get("S42-STAGE100-FULLTEXT-ANCHOR-PREFILL", {}).get("status")
        == "PASS"
    )

    stage44_recheck_mismatches = []
    expected_stage44_recheck = {
        "stage44_external_reprobe": "PASS",
        "final_goal_audit": "PASS",
        "stage42_evidence_closure": "PASS",
        "final_decision": "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
    }
    for step, expected in expected_stage44_recheck.items():
        got = stage44_recheck.get(step, {}).get("status", "MISSING")
        if got != expected:
            stage44_recheck_mismatches.append(f"{step}:{got}!={expected}")

    default_ok = (
        default_recheck.get("stage42_evidence_closure", {}).get("status") == "PASS"
        and default_recheck.get("final_decision", {}).get("status")
        == "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    )
    closure_ok = (
        closure_recheck.get("stage42_evidence_closure", {}).get("status") == "PASS"
        and closure_recheck.get("final_decision", {}).get("status")
        == "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    )

    manifest_mismatches = manifest_problems()
    run_ids = {row.get("run_id") for row in run_log}
    required_run_ids = [
        "stage42-evidence-closure-audit-001",
        "stage42-closure-manifest-001",
        "stage42-final-recheck-closure-001",
        "stage42-final-recheck-default-closure-001",
        "stage43-postclosure-current-smoke-001",
        "stage44-external-unlock-reprobe-001",
        "stage44-final-recheck-reprobe-001",
        "stage45-active-state-refactor-001",
        "stage46-wsl-active-state-target-smoke-001",
        "stage47-wsl-full-sab-smoke-001",
        "stage48-wsl-noise-smoke-001",
        "stage49-wsl-repeated-full-sab-001",
        "stage50-performance-evidence-matrix-001",
        "stage51-goal-completion-frontier-001",
        "stage52-external-unlock-readiness-001",
        "stage53-final-recheck-stage50-52-001",
        "stage54-default-final-recheck-001",
        "stage55-external-paper-probe-001",
        "stage56-final-recheck-stage55-001",
        "stage57-scope-label-audit-001",
        "stage58-final-recheck-stage57-001",
        "stage59-completion-route-readiness-001",
        "stage60-final-recheck-stage59-001",
        "stage61-native-perf-unlock-probe-001",
        "stage62-fulltext-unlock-probe-001",
        "stage64-post-variant-refresh-001",
        "stage65a-r4-unrolled-avx512-001",
        "stage66a-post-variant-final-recheck-001",
        "stage67-final-recheck-stage66-001",
        "stage68-frontier-closure-consistency-001",
        "stage69-local-variant-feasibility-001",
        "stage70-external-unlock-preflight-001",
        "stage71-final-recheck-stage70-001",
        "stage72-external-source-refresh-001",
        "stage73-final-recheck-stage72-001",
        "stage74-r-scaling-boundary-001",
        "stage75-rgt4-profile-boundary-001",
        "stage76-rgt4-kernel-feasibility-001",
        "stage77-rgt4-fused-mat-kernel-001",
        "stage78-rgt4-fused-repeated-gates-001",
        "stage79-rgt4-fused-high-stat-001",
        "stage80-promotion-policy-audit-001",
        "stage81-next-variant-triage-001",
        "stage82-post-h11-profile-001",
        "stage83-mat-body-design-check-001",
        "stage84-h13-r6-tile-sweep-preflight-001",
        "stage86-secondary-cmux-materialization-001",
        "stage87-h14-backend-from-dft-add-preflight-001",
        "stage88-h14-backend-repeated-gates-001",
        "stage89-h14-promotion-policy-integration-001",
        "stage90-external-claim-unlock-001",
        "stage91-final-scoped-package-001",
        "stage92-external-unlock-execution-001",
        "stage93-external-lane-attempt-001",
        "stage94-local-frontier-audit-001",
        "stage95-public-source-reprobe-001",
        "stage96-upstream-delta-audit-001",
        "stage97-source-delta-guard-001",
        "stage98-current-smoke-refresh-001",
        "stage99-external-blocker-reprobe-001",
        "stage100-fulltext-anchor-prefill-001",
    ]
    missing_run_ids = [run_id for run_id in required_run_ids if run_id not in run_ids]
    required_manifest_mentions = [
        "scripts/verify_stage42_closure.py",
        "repro/stage42_evidence_closure_manifest.csv",
        "repro/final_goal_recheck/stage70_external_unlock_preflight.log",
        "scripts/run_stage44_external_unlock_reprobe.sh",
        "scripts/build_stage44_external_unlock_reprobe.py",
        "repro/stage44_external_unlock_reprobe/summary.csv",
        "repro/final_goal_recheck_stage44_reprobe/summary.csv",
        "docs/stage45_active_state_refactor_log.md",
        "repro/stage45_active_state_refactor/summary.csv",
        "repro/stage45_active_state_refactor/ffnt_kernel_run.log",
        "repro/stage45_active_state_refactor/spqlios_avx512_windows_build.log",
        "docs/stage46_wsl_active_state_target_smoke_log.md",
        "repro/stage46_wsl_active_state_target_smoke/summary.csv",
        "repro/stage46_wsl_active_state_target_smoke/build.log",
        "repro/stage46_wsl_active_state_target_smoke/run.log",
        "docs/stage47_wsl_full_sab_smoke_log.md",
        "repro/stage47_wsl_active_state_full_sab_smoke/summary.csv",
        "repro/stage47_wsl_active_state_full_sab_smoke/r2/summary.csv",
        "repro/stage47_wsl_active_state_full_sab_smoke/r2/run_0.log",
        "repro/stage47_wsl_active_state_full_sab_smoke/r4/summary.csv",
        "repro/stage47_wsl_active_state_full_sab_smoke/r4/run_0.log",
        "docs/stage48_wsl_noise_smoke_log.md",
        "repro/stage48_wsl_active_state_noise_smoke/summary.csv",
        "repro/stage48_wsl_active_state_noise_smoke/aggregate.csv",
        "repro/stage48_wsl_active_state_noise_smoke/r2/seed_6862025.log",
        "repro/stage48_wsl_active_state_noise_smoke/r4/seed_6862025.log",
        "docs/stage49_wsl_repeated_full_sab_log.md",
        "repro/stage49_wsl_repeated_full_sab/summary.csv",
        "repro/stage49_wsl_repeated_full_sab/r2/summary.csv",
        "repro/stage49_wsl_repeated_full_sab/r2/driver.log",
        "repro/stage49_wsl_repeated_full_sab/r2/run_0.log",
        "repro/stage49_wsl_repeated_full_sab/r2/run_1.log",
        "repro/stage49_wsl_repeated_full_sab/r2/run_2.log",
        "repro/stage49_wsl_repeated_full_sab/r4/summary.csv",
        "repro/stage49_wsl_repeated_full_sab/r4/driver.log",
        "repro/stage49_wsl_repeated_full_sab/r4/run_0.log",
        "repro/stage49_wsl_repeated_full_sab/r4/run_1.log",
        "repro/stage49_wsl_repeated_full_sab/r4/run_2.log",
        "docs/stage50_performance_evidence_matrix.md",
        "scripts/build_stage50_performance_evidence_matrix.py",
        "repro/stage50_performance_evidence_matrix.csv",
        "docs/stage51_goal_completion_frontier.md",
        "scripts/build_stage51_goal_completion_frontier.py",
        "repro/stage51_goal_completion_frontier.csv",
        "docs/stage52_external_unlock_readiness.md",
        "scripts/build_stage52_external_unlock_readiness.py",
        "repro/stage52_external_unlock_readiness.csv",
        "docs/stage53_final_recheck_integration_log.md",
        "repro/stage53_final_recheck_stage50_52/summary.csv",
        "repro/stage53_final_recheck_stage50_52/stage50_performance_matrix.log",
        "repro/stage53_final_recheck_stage50_52/stage51_goal_frontier.log",
        "repro/stage53_final_recheck_stage50_52/stage52_external_unlock_readiness.log",
        "repro/stage53_final_recheck_stage50_52/stage42_evidence_closure.log",
        "docs/stage54_default_final_recheck_log.md",
        "repro/stage54_default_final_recheck/summary.csv",
        "repro/stage54_default_final_recheck/stage50_performance_matrix.log",
        "repro/stage54_default_final_recheck/stage51_goal_frontier.log",
        "repro/stage54_default_final_recheck/stage52_external_unlock_readiness.log",
        "repro/stage54_default_final_recheck/stage42_evidence_closure.log",
        "docs/stage55_external_paper_probe_log.md",
        "scripts/build_stage55_external_paper_probe.py",
        "repro/stage55_external_paper_probe/summary.csv",
        "repro/stage55_external_paper_probe/access_probe.csv",
        "repro/stage55_external_paper_probe/crossref_summary.csv",
        "repro/stage55_external_paper_probe/crossref_metadata.json",
        "docs/stage56_final_recheck_stage55_log.md",
        "repro/stage56_final_recheck_stage55/summary.csv",
        "repro/stage56_final_recheck_stage55/stage55_external_paper_probe.log",
        "repro/stage56_final_recheck_stage55/final_goal_audit.log",
        "repro/stage56_final_recheck_stage55/remaining_blocker_dashboard.log",
        "repro/stage56_final_recheck_stage55/stage51_goal_frontier.log",
        "repro/stage56_final_recheck_stage55/stage52_external_unlock_readiness.log",
        "repro/stage56_final_recheck_stage55/stage42_evidence_closure.log",
        "docs/stage57_scope_label_audit.md",
        "scripts/build_stage57_scope_label_audit.py",
        "repro/stage57_scope_label_audit.csv",
        "docs/stage58_final_recheck_stage57_log.md",
        "repro/stage58_final_recheck_stage57/summary.csv",
        "repro/stage58_final_recheck_stage57/stage51_goal_frontier.log",
        "repro/stage58_final_recheck_stage57/stage52_external_unlock_readiness.log",
        "repro/stage58_final_recheck_stage57/stage57_scope_label_audit.log",
        "repro/stage58_final_recheck_stage57/stage42_evidence_closure.log",
        "docs/roadmap_to_completion_after_stage58.md",
        "docs/stage59_completion_route_readiness.md",
        "scripts/build_stage59_completion_route_readiness.py",
        "repro/stage59_completion_route_readiness.csv",
        "docs/stage60_final_recheck_stage59_log.md",
        "repro/stage60_final_recheck_stage59/summary.csv",
        "repro/stage60_final_recheck_stage59/stage51_goal_frontier.log",
        "repro/stage60_final_recheck_stage59/stage52_external_unlock_readiness.log",
        "repro/stage60_final_recheck_stage59/stage57_scope_label_audit.log",
        "repro/stage60_final_recheck_stage59/stage59_completion_route.log",
        "repro/stage60_final_recheck_stage59/stage42_evidence_closure.log",
        "docs/stage61_native_perf_unlock_probe_log.md",
        "repro/stage61_native_perf_unlock_probe/summary.csv",
        "repro/stage61_native_perf_unlock_probe/environment.log",
        "repro/stage61_native_perf_unlock_probe/perf_smoke.log",
        "docs/stage62_fulltext_unlock_probe_log.md",
        "scripts/build_stage62_fulltext_unlock_probe.py",
        "repro/stage62_fulltext_unlock_probe/unlock_summary.csv",
        "repro/stage62_fulltext_unlock_probe/summary.csv",
        "repro/stage62_fulltext_unlock_probe/review_checklist.csv",
        "repro/stage62_fulltext_unlock_probe/acm_pdf_head.log",
        "repro/stage62_fulltext_unlock_probe/acm_pdf_head.err",
        "repro/stage62_fulltext_unlock_probe/eprint_pdf_head.log",
        "repro/stage62_fulltext_unlock_probe/eprint_pdf_head.err",
        "docs/stage64_post_variant_refresh_log.md",
        "scripts/run_stage64_post_variant_refresh.sh",
        "scripts/build_stage64_post_variant_refresh_log.py",
        "repro/stage64_post_variant_refresh/summary.csv",
        "repro/stage64_post_variant_refresh/current_smoke/summary.csv",
        "repro/stage64_post_variant_refresh/full_sab_r2/summary.csv",
        "repro/stage64_post_variant_refresh/full_sab_r4/summary.csv",
        "repro/stage64_post_variant_refresh/final_noise/aggregate.csv",
        "docs/stage65_r4_unrolled_avx512_log.md",
        "experiments/stage65_r4_unrolled_avx512_plan.md",
        "algorithm_variants/pvw_sab_r4_unrolled_avx512.md",
        "scripts/run_stage65_r4_unrolled_avx512.sh",
        "scripts/build_stage65_r4_unrolled_avx512_log.py",
        "repro/stage65_r4_unrolled_avx512/summary.csv",
        "repro/stage65_r4_unrolled_avx512/kernel_microbench.csv",
        "repro/stage65_r4_unrolled_avx512/full_sab_smoke.csv",
        "repro/stage65_r4_unrolled_avx512/instruction_counts.csv",
        "repro/stage65_r4_unrolled_avx512/default_scalar_ffnt_smoke.log",
        "docs/stage66_post_variant_final_recheck_log.md",
        "experiments/stage66_post_variant_final_recheck_plan.md",
        "scripts/run_stage66_post_variant_final_recheck.sh",
        "scripts/build_stage66_post_variant_final_recheck_log.py",
        "repro/stage66_post_variant_final_recheck/summary.csv",
        "repro/stage66_post_variant_final_recheck/final_recheck/summary.csv",
        "docs/stage67_final_recheck_stage66_log.md",
        "experiments/stage67_final_recheck_stage66_plan.md",
        "scripts/build_stage67_final_recheck_stage66_log.py",
        "repro/stage67_final_recheck_stage66/summary.csv",
        "repro/stage67_final_recheck_stage66/decision.csv",
        "docs/stage68_frontier_closure_consistency_log.md",
        "experiments/stage68_frontier_closure_consistency_plan.md",
        "scripts/build_stage68_frontier_closure_consistency.py",
        "repro/stage68_frontier_closure_consistency.csv",
        "docs/stage69_local_variant_feasibility_log.md",
        "experiments/stage69_local_variant_feasibility_plan.md",
        "scripts/build_stage69_local_variant_feasibility.py",
        "repro/stage69_local_variant_feasibility.csv",
        "theory_checks/h3_sparse_selector_feasibility.md",
        "algorithm_variants/pvw_sab_sparse_selector_shortcut.md",
        "docs/stage70_external_unlock_preflight_log.md",
        "experiments/stage70_external_unlock_preflight_plan.md",
        "scripts/build_stage70_external_unlock_preflight.py",
        "repro/stage70_external_unlock_preflight.csv",
        "docs/stage71_final_recheck_stage70_log.md",
        "experiments/stage71_final_recheck_stage70_plan.md",
        "scripts/build_stage71_final_recheck_stage70_log.py",
        "repro/stage71_final_recheck_stage70/summary.csv",
        "repro/stage71_final_recheck_stage70/decision.csv",
        "repro/stage71_final_recheck_stage70/final_goal_audit.log",
        "repro/stage71_final_recheck_stage70/remaining_blocker_dashboard.log",
        "repro/stage71_final_recheck_stage70/stage51_goal_frontier.log",
        "repro/stage71_final_recheck_stage70/stage52_external_unlock_readiness.log",
        "repro/stage71_final_recheck_stage70/stage57_scope_label_audit.log",
        "repro/stage71_final_recheck_stage70/stage59_completion_route.log",
        "repro/stage71_final_recheck_stage70/stage70_external_unlock_preflight.log",
        "repro/stage71_final_recheck_stage70/stage42_evidence_closure.log",
        "repro/stage71_final_recheck_stage70_failed_attempt1/decision.csv",
        "repro/stage71_final_recheck_stage70_failed_attempt1/stage71_log_failed.md",
        "docs/stage72_external_source_refresh_log.md",
        "experiments/stage72_external_source_refresh_plan.md",
        "scripts/build_stage72_external_source_refresh.py",
        "repro/stage72_external_source_refresh/summary.csv",
        "repro/stage72_external_source_refresh/access_probe.csv",
        "repro/stage72_external_source_refresh/crossref_summary.csv",
        "repro/stage72_external_source_refresh/crossref_metadata.json",
        "repro/stage72_external_source_refresh/author_cite.bib",
        "docs/stage73_final_recheck_stage72_log.md",
        "experiments/stage73_final_recheck_stage72_plan.md",
        "scripts/build_stage73_final_recheck_stage72_log.py",
        "repro/stage73_final_recheck_stage72/summary.csv",
        "repro/stage73_final_recheck_stage72/decision.csv",
        "repro/stage73_final_recheck_stage72/stage72_external_source_refresh.log",
        "repro/stage73_final_recheck_stage72/final_goal_audit.log",
        "repro/stage73_final_recheck_stage72/remaining_blocker_dashboard.log",
        "repro/stage73_final_recheck_stage72/stage51_goal_frontier.log",
        "repro/stage73_final_recheck_stage72/stage52_external_unlock_readiness.log",
        "repro/stage73_final_recheck_stage72/stage57_scope_label_audit.log",
        "repro/stage73_final_recheck_stage72/stage59_completion_route.log",
        "repro/stage73_final_recheck_stage72/stage70_external_unlock_preflight.log",
        "repro/stage73_final_recheck_stage72/stage42_evidence_closure.log",
        "docs/stage74_r_scaling_boundary_log.md",
        "experiments/stage74_r_scaling_boundary_plan.md",
        "scripts/build_stage74_r_scaling_boundary.py",
        "theory_checks/h10_r_gt4_lane_scaling.md",
        "algorithm_variants/pvw_sab_r_gt4_lane_scaling.md",
        "repro/stage74_r_scaling_boundary/decision.csv",
        "repro/stage74_r_scaling_boundary/r6_reps1_runs1/summary.csv",
        "repro/stage74_r_scaling_boundary/r6_reps1_runs1/run_0.log",
        "repro/stage74_r_scaling_boundary/r8_reps1_runs1/summary.csv",
        "repro/stage74_r_scaling_boundary/r8_reps1_runs1/run_0.log",
        "docs/stage75_rgt4_profile_boundary_log.md",
        "experiments/stage75_rgt4_profile_boundary_plan.md",
        "scripts/build_stage75_rgt4_profile_boundary.py",
        "repro/stage75_rgt4_profile_boundary/decision.csv",
        "repro/stage75_rgt4_profile_boundary/profile_metrics.csv",
        "repro/stage75_rgt4_profile_boundary/body_profile_r6/summary.csv",
        "repro/stage75_rgt4_profile_boundary/body_profile_r6/r6/run_0.log",
        "repro/stage75_rgt4_profile_boundary/body_profile_r8/summary.csv",
        "repro/stage75_rgt4_profile_boundary/body_profile_r8/r8/run_0.log",
        "docs/stage76_rgt4_kernel_feasibility_log.md",
        "experiments/stage76_rgt4_kernel_feasibility_plan.md",
        "scripts/build_stage76_rgt4_kernel_feasibility.py",
        "theory_checks/h11_rgt4_fused_mat_kernel.md",
        "algorithm_variants/pvw_sab_rgt4_fused_mat_kernel.md",
        "repro/stage76_rgt4_kernel_feasibility/rgt4_kernel_smoke.log",
        "repro/stage76_rgt4_kernel_feasibility/kernel_microbench.csv",
        "repro/stage76_rgt4_kernel_feasibility/ep_breakdown.csv",
        "repro/stage76_rgt4_kernel_feasibility/summary.csv",
        "docs/stage77_rgt4_fused_mat_kernel_log.md",
        "experiments/stage77_rgt4_fused_mat_kernel_plan.md",
        "scripts/build_stage77_rgt4_fused_mat_kernel.py",
        "repro/stage77_rgt4_fused_mat_kernel/generic.log",
        "repro/stage77_rgt4_fused_mat_kernel/fused.log",
        "repro/stage77_rgt4_fused_mat_kernel/kernel_comparison.csv",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_smoke.csv",
        "repro/stage77_rgt4_fused_mat_kernel/summary.csv",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r6/summary.csv",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r6/run_0.log",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r8/summary.csv",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r8/run_0.log",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r6/summary.csv",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r6/run_0.log",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r8/summary.csv",
        "repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r8/run_0.log",
        "docs/stage78_rgt4_fused_repeated_gates_log.md",
        "experiments/stage78_rgt4_fused_repeated_gates_plan.md",
        "scripts/run_stage78_rgt4_fused_repeated_gates.sh",
        "scripts/build_stage78_rgt4_fused_repeated_gates.py",
        "repro/stage78_rgt4_fused_repeated_gates/stage78_run.log",
        "repro/stage78_rgt4_fused_repeated_gates/full_sab_repeated.csv",
        "repro/stage78_rgt4_fused_repeated_gates/summary.csv",
        "repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/summary.csv",
        "repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/run_0.log",
        "repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/run_1.log",
        "repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/run_2.log",
        "repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r8_runs1/summary.csv",
        "repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r8_runs1/run_0.log",
        "repro/stage78_rgt4_fused_repeated_gates/final_noise/summary.csv",
        "repro/stage78_rgt4_fused_repeated_gates/final_noise/aggregate.csv",
        "repro/stage78_rgt4_fused_repeated_gates/final_noise/r6/seed_6862025.log",
        "repro/stage78_rgt4_fused_repeated_gates/final_noise/r6/seed_6862026.log",
        "repro/stage78_rgt4_fused_repeated_gates/final_noise/r6/seed_6862027.log",
        "repro/stage78_rgt4_fused_repeated_gates/final_noise/r8/seed_6862025.log",
        "repro/stage78_rgt4_fused_repeated_gates/final_noise/r8/seed_6862026.log",
        "repro/stage78_rgt4_fused_repeated_gates/final_noise/r8/seed_6862027.log",
        "repro/stage78_rgt4_fused_repeated_gates/noise_summary.csv",
        "repro/stage78_rgt4_fused_repeated_gates/resource/summary.csv",
        "repro/stage78_rgt4_fused_repeated_gates/resource_summary.csv",
        "repro/stage78_rgt4_fused_repeated_gates/resource/r6/pvw.log",
        "repro/stage78_rgt4_fused_repeated_gates/resource/r6/pvw.time.log",
        "repro/stage78_rgt4_fused_repeated_gates/resource/r6/scalar.log",
        "repro/stage78_rgt4_fused_repeated_gates/resource/r6/scalar.time.log",
        "repro/stage78_rgt4_fused_repeated_gates/resource/r8/pvw.log",
        "repro/stage78_rgt4_fused_repeated_gates/resource/r8/pvw.time.log",
        "repro/stage78_rgt4_fused_repeated_gates/resource/r8/scalar.log",
        "repro/stage78_rgt4_fused_repeated_gates/resource/r8/scalar.time.log",
        "docs/stage79_rgt4_fused_high_stat_log.md",
        "experiments/stage79_rgt4_fused_high_stat_plan.md",
        "scripts/run_stage79_rgt4_fused_high_stat.sh",
        "scripts/build_stage79_rgt4_fused_high_stat.py",
        "repro/stage79_rgt4_fused_high_stat/stage79_run.log",
        "repro/stage79_rgt4_fused_high_stat/full_sab_high_stat.csv",
        "repro/stage79_rgt4_fused_high_stat/noise_summary.csv",
        "repro/stage79_rgt4_fused_high_stat/resource_samples.csv",
        "repro/stage79_rgt4_fused_high_stat/resource_summary.csv",
        "repro/stage79_rgt4_fused_high_stat/summary.csv",
        "docs/stage80_promotion_policy_audit_log.md",
        "experiments/stage80_promotion_policy_audit_plan.md",
        "scripts/run_stage80_promotion_policy_audit.sh",
        "scripts/build_stage80_promotion_policy_audit.py",
        "repro/stage80_promotion_policy_audit/stage80_run.log",
        "repro/stage80_promotion_policy_audit/summary.csv",
        "repro/stage80_promotion_policy_audit/current_smoke/summary.csv",
        "docs/stage81_next_variant_triage_log.md",
        "experiments/stage81_next_variant_triage_plan.md",
        "scripts/build_stage81_next_variant_triage.py",
        "repro/stage81_next_variant_triage.csv",
        "docs/stage82_post_h11_profile_log.md",
        "experiments/stage82_post_h11_profile_plan.md",
        "scripts/run_stage82_post_h11_profile.sh",
        "scripts/build_stage82_post_h11_profile.py",
        "repro/stage82_post_h11_profile/stage82_run.log",
        "repro/stage82_post_h11_profile/body_profile_fused_r6/summary.csv",
        "repro/stage82_post_h11_profile/body_profile_fused_r6/r6/run_0.log",
        "repro/stage82_post_h11_profile/profile_metrics.csv",
        "repro/stage82_post_h11_profile/decision.csv",
        "docs/stage83_mat_body_design_check_log.md",
        "experiments/stage83_mat_body_design_check_plan.md",
        "scripts/build_stage83_mat_body_design_check.py",
        "theory_checks/h13_mat_body_reduction_design.md",
        "algorithm_variants/pvw_sab_h13_mat_body_design.md",
        "repro/stage83_mat_body_design_check/candidates.csv",
        "repro/stage83_mat_body_design_check/decision.csv",
        "docs/stage84_h13_r6_tile_sweep_preflight_log.md",
        "experiments/stage84_h13_r6_tile_sweep_preflight_plan.md",
        "scripts/run_stage84_h13_r6_tile_sweep_preflight.sh",
        "scripts/build_stage84_h13_r6_tile_sweep_preflight.py",
        "src/mosfhet/Makefile.def",
        "src/mosfhet/src/mattrgsw.c",
        "repro/stage84_h13_r6_tile_sweep_preflight/stage84_run.log",
        "repro/stage84_h13_r6_tile_sweep_preflight/tile4.log",
        "repro/stage84_h13_r6_tile_sweep_preflight/fulltile.log",
        "repro/stage84_h13_r6_tile_sweep_preflight/kernel_comparison.csv",
        "repro/stage84_h13_r6_tile_sweep_preflight/full_sab_smoke.csv",
        "repro/stage84_h13_r6_tile_sweep_preflight/summary.csv",
        "repro/stage84_h13_r6_tile_sweep_preflight/full_sab_tile4_r6/summary.csv",
        "repro/stage84_h13_r6_tile_sweep_preflight/full_sab_tile4_r6/run_0.log",
        "repro/stage84_h13_r6_tile_sweep_preflight/full_sab_fulltile_r6/summary.csv",
        "repro/stage84_h13_r6_tile_sweep_preflight/full_sab_fulltile_r6/run_0.log",
        "docs/stage86_secondary_cmux_materialization_log.md",
        "experiments/stage86_secondary_cmux_materialization_plan.md",
        "scripts/build_stage86_secondary_cmux_materialization.py",
        "theory_checks/h14_secondary_cmux_materialization.md",
        "algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md",
        "repro/stage86_secondary_cmux_materialization/candidates.csv",
        "repro/stage86_secondary_cmux_materialization/decision.csv",
        "docs/stage87_h14_backend_from_dft_add_preflight_log.md",
        "experiments/stage87_h14_backend_from_dft_add_preflight_plan.md",
        "scripts/run_stage87_h14_backend_from_dft_add_preflight.sh",
        "scripts/build_stage87_h14_backend_from_dft_add_preflight.py",
        "src/mosfhet/Makefile.def",
        "src/mosfhet/include/mosfhet.h",
        "src/mosfhet/src/polynomial.c",
        "src/mosfhet/src/pvwtmlwe.c",
        "src/mosfhet/src/fft/spqlios/fft_processor_spqlios.c",
        "src/mosfhet/src/fft/spqlios/spqlios-fft.h",
        "src/mosfhet/src/fft/ffnt/ffnt.c",
        "src/mosfhet/src/fft/ffnt/ffnt.h",
        "repro/stage87_h14_backend_from_dft_add_preflight/kernel_build.log",
        "repro/stage87_h14_backend_from_dft_add_preflight/kernel_run.log",
        "repro/stage87_h14_backend_from_dft_add_preflight/target_build.log",
        "repro/stage87_h14_backend_from_dft_add_preflight/target_run.log",
        "repro/stage87_h14_backend_from_dft_add_preflight/full_sab_wrapper_r6/build.log",
        "repro/stage87_h14_backend_from_dft_add_preflight/full_sab_wrapper_r6/run_0.log",
        "repro/stage87_h14_backend_from_dft_add_preflight/full_sab_backend_r6/build.log",
        "repro/stage87_h14_backend_from_dft_add_preflight/full_sab_backend_r6/run_0.log",
        "repro/stage87_h14_backend_from_dft_add_preflight/full_sab_smoke.csv",
        "repro/stage87_h14_backend_from_dft_add_preflight/summary.csv",
        *STAGE88_ARTIFACTS,
        *STAGE89_ARTIFACTS,
        *STAGE90_ARTIFACTS,
        *STAGE91_ARTIFACTS,
        *STAGE92_ARTIFACTS,
        *STAGE93_ARTIFACTS,
        *STAGE94_ARTIFACTS,
        *STAGE95_ARTIFACTS,
        *STAGE96_ARTIFACTS,
        *STAGE97_ARTIFACTS,
        *STAGE98_ARTIFACTS,
        *STAGE99_ARTIFACTS,
        *STAGE100_ARTIFACTS,
    ]
    missing_manifest_mentions = [
        token for token in required_manifest_mentions if token not in artifact_manifest
    ]

    checks = [
        {
            "check": "verification_input_commit",
            "status": git_short(),
            "evidence": "git rev-parse --short HEAD",
            "detail": "Commit checked before writing verifier output artifacts.",
        },
        {
            "check": "worktree_clean_before_outputs",
            "status": "PASS" if not status_before_outputs.strip() else "FAIL_DIRTY",
            "evidence": "git status --short --untracked-files=all",
            "detail": "; ".join(line.strip() for line in status_before_outputs.splitlines() if line.strip())
            if status_before_outputs.strip()
            else "tracked and untracked worktree was clean before verifier outputs.",
        },
        {
            "check": "final_audit_A9",
            "status": "PASS"
            if final_audit.get("A9", {}).get("status")
            in {
                "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
                "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED",
                "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED",
            }
            else "FAIL",
            "evidence": "repro/final_goal_completion_audit.csv",
            "detail": final_audit.get("A9", {}).get("status", "MISSING"),
        },
        {
            "check": "stage41_readiness",
            "status": "PASS" if not stage41_mismatches else "FAIL",
            "evidence": "repro/stage41_external_unlock_packet.csv",
            "detail": "all readiness rows remain waiting for external evidence"
            if not stage41_mismatches
            else "; ".join(stage41_mismatches),
        },
        {
            "check": "stage42_overall",
            "status": "PASS"
            if stage42.get("S42-OVERALL", {}).get("status")
            == "PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED"
            else "FAIL",
            "evidence": "repro/stage42_evidence_closure_audit.csv",
            "detail": stage42.get("S42-OVERALL", {}).get("status", "MISSING"),
        },
        {
            "check": "stage42_manifest_hashes",
            "status": "PASS" if not manifest_mismatches else "FAIL",
            "evidence": "repro/stage42_evidence_closure_manifest.csv",
            "detail": "all closure manifest hashes match"
            if not manifest_mismatches
            else "; ".join(manifest_mismatches),
        },
        {
            "check": "stage43_current_smoke",
            "status": "PASS" if not stage43_mismatches else "FAIL",
            "evidence": "repro/stage43_current_smoke_after_stage42/summary.csv",
            "detail": "scalar binary, PVW target, and scalar ternary smoke rows pass"
            if not stage43_mismatches
                else "; ".join(stage43_mismatches),
        },
        {
            "check": "stage44_external_reprobe",
            "status": "PASS" if not stage44_mismatches else "FAIL",
            "evidence": "repro/stage44_external_unlock_reprobe/summary.csv",
            "detail": "external full-text/native-perf unlocks remain unavailable and recorded"
            if not stage44_mismatches
            else "; ".join(stage44_mismatches),
        },
        {
            "check": "stage45_active_state",
            "status": "PASS" if not stage45_mismatches and stage42_stage45_ok else "FAIL",
            "evidence": "repro/stage45_active_state_refactor/summary.csv",
            "detail": "Stage45 active-state correctness passes and closure audit records it"
            if not stage45_mismatches and stage42_stage45_ok
            else "; ".join(stage45_mismatches)
            or f"S42-STAGE45-ACTIVE-STATE:{stage42.get('S42-STAGE45-ACTIVE-STATE', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage46_wsl_target",
            "status": "PASS" if stage46_status == "PASS" and stage42_stage46_ok else "FAIL",
            "evidence": "repro/stage46_wsl_active_state_target_smoke/summary.csv",
            "detail": "Stage46 WSL spqlios_avx512 target gate passes and closure audit records it"
            if stage46_status == "PASS" and stage42_stage46_ok
            else f"stage46_status={stage46_status}; S42-STAGE46-WSL-TARGET={stage42.get('S42-STAGE46-WSL-TARGET', {}).get('status', 'MISSING')}",
        },
        {
            "check": "stage47_wsl_full_sab",
            "status": "PASS" if not stage47_mismatches and stage42_stage47_ok else "FAIL",
            "evidence": "repro/stage47_wsl_active_state_full_sab_smoke/summary.csv",
            "detail": "Stage47 WSL r=2/r=4 full-SAB smoke passes with positive A/B speedup and closure audit records it"
            if not stage47_mismatches and stage42_stage47_ok
            else "; ".join(stage47_mismatches)
            or f"S42-STAGE47-WSL-FULL-SAB:{stage42.get('S42-STAGE47-WSL-FULL-SAB', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage48_wsl_noise",
            "status": "PASS" if not stage48_mismatches and stage42_stage48_ok else "FAIL",
            "evidence": "repro/stage48_wsl_active_state_noise_smoke/aggregate.csv",
            "detail": "Stage48 WSL r=2/r=4 final-output noise smoke passes with zero failures and closure audit records it"
            if not stage48_mismatches and stage42_stage48_ok
            else "; ".join(stage48_mismatches)
            or f"S42-STAGE48-WSL-NOISE:{stage42.get('S42-STAGE48-WSL-NOISE', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage49_wsl_repeated_full_sab",
            "status": "PASS" if not stage49_mismatches and stage42_stage49_ok else "FAIL",
            "evidence": "repro/stage49_wsl_repeated_full_sab/summary.csv",
            "detail": "Stage49 WSL r=2/r=4 repeated full-SAB stability passes and closure audit records it"
            if not stage49_mismatches and stage42_stage49_ok
            else "; ".join(stage49_mismatches)
            or f"S42-STAGE49-WSL-REPEATED-FULL-SAB:{stage42.get('S42-STAGE49-WSL-REPEATED-FULL-SAB', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage50_performance_matrix",
            "status": "PASS" if not stage50_mismatches and stage42_stage50_ok else "FAIL",
            "evidence": "repro/stage50_performance_evidence_matrix.csv",
            "detail": "Stage50 performance evidence matrix preserves high-stat/current-head/smoke claim boundaries and closure audit records it"
            if not stage50_mismatches and stage42_stage50_ok
            else "; ".join(stage50_mismatches)
            or f"S42-STAGE50-PERFORMANCE-MATRIX:{stage42.get('S42-STAGE50-PERFORMANCE-MATRIX', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage51_goal_frontier",
            "status": "PASS" if not stage51_mismatches and stage42_stage51_ok else "FAIL",
            "evidence": "repro/stage51_goal_completion_frontier.csv",
            "detail": "Stage51 goal frontier separates local scoped-ready evidence from stronger external blockers and closure audit records it"
            if not stage51_mismatches and stage42_stage51_ok
            else "; ".join(stage51_mismatches)
            or f"S42-STAGE51-GOAL-FRONTIER:{stage42.get('S42-STAGE51-GOAL-FRONTIER', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage52_external_unlock_readiness",
            "status": "PASS" if not stage52_mismatches and stage42_stage52_ok else "FAIL",
            "evidence": "repro/stage52_external_unlock_readiness.csv",
            "detail": "Stage52 external unlock readiness packet records external inputs, commands, artifacts, gates, and failure policies"
            if not stage52_mismatches and stage42_stage52_ok
            else "; ".join(stage52_mismatches)
            or f"S42-STAGE52-EXTERNAL-UNLOCK-READINESS:{stage42.get('S42-STAGE52-EXTERNAL-UNLOCK-READINESS', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage53_final_recheck_integration",
            "status": "PASS" if not stage53_mismatches and stage42_stage53_ok else "FAIL",
            "evidence": "repro/stage53_final_recheck_stage50_52/summary.csv",
            "detail": "Stage53 final recheck integrates Stage50, Stage51, Stage52, and Stage42 closure"
            if not stage53_mismatches and stage42_stage53_ok
            else "; ".join(stage53_mismatches)
            or f"S42-STAGE53-FINAL-RECHECK-INTEGRATION:{stage42.get('S42-STAGE53-FINAL-RECHECK-INTEGRATION', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage54_default_final_recheck",
            "status": "PASS" if not stage54_mismatches and stage42_stage54_ok else "FAIL",
            "evidence": "repro/stage54_default_final_recheck/summary.csv",
            "detail": "Stage54 default final recheck covers Stage50, Stage51, Stage52, and Stage42 closure"
            if not stage54_mismatches and stage42_stage54_ok
            else "; ".join(stage54_mismatches)
            or f"S42-STAGE54-DEFAULT-FINAL-RECHECK:{stage42.get('S42-STAGE54-DEFAULT-FINAL-RECHECK', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage55_external_paper_probe",
            "status": "PASS" if not stage55_mismatches and stage42_stage55_ok else "FAIL",
            "evidence": "repro/stage55_external_paper_probe/summary.csv",
            "detail": "Stage55 records Crossref metadata while preserving the 2025/686 full-text review blocker"
            if not stage55_mismatches and stage42_stage55_ok
            else "; ".join(stage55_mismatches)
            or f"S42-STAGE55-EXTERNAL-PAPER-PROBE:{stage42.get('S42-STAGE55-EXTERNAL-PAPER-PROBE', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage56_final_recheck_stage55",
            "status": "PASS" if not stage56_mismatches and stage42_stage56_ok else "FAIL",
            "evidence": "repro/stage56_final_recheck_stage55/summary.csv",
            "detail": "Stage56 final recheck refreshes Stage55 and propagates it through blockers/frontier/unlock/closure"
            if not stage56_mismatches and stage42_stage56_ok
            else "; ".join(stage56_mismatches)
            or f"S42-STAGE56-FINAL-RECHECK-STAGE55:{stage42.get('S42-STAGE56-FINAL-RECHECK-STAGE55', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage57_scope_label_audit",
            "status": "PASS" if not stage57_mismatches and stage42_stage57_ok else "FAIL",
            "evidence": "repro/stage57_scope_label_audit.csv",
            "detail": "Stage57 confirms current scope labels match the latest Stage19+ closure range"
            if not stage57_mismatches and stage42_stage57_ok
            else "; ".join(stage57_mismatches)
            or f"S42-STAGE57-SCOPE-LABEL-AUDIT:{stage42.get('S42-STAGE57-SCOPE-LABEL-AUDIT', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage58_final_recheck_stage57",
            "status": "PASS" if not stage58_mismatches and stage42_stage58_ok else "FAIL",
            "evidence": "repro/stage58_final_recheck_stage57/summary.csv",
            "detail": "Stage58 final recheck refreshes Stage57 before Stage42 closure"
            if not stage58_mismatches and stage42_stage58_ok
            else "; ".join(stage58_mismatches)
            or f"S42-STAGE58-FINAL-RECHECK-STAGE57:{stage42.get('S42-STAGE58-FINAL-RECHECK-STAGE57', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage59_completion_route",
            "status": "PASS" if not stage59_mismatches and stage42_stage59_ok else "FAIL",
            "evidence": "repro/stage59_completion_route_readiness.csv",
            "detail": "Stage59 completion route separates local refresh lanes from external blocker lanes"
            if not stage59_mismatches and stage42_stage59_ok
            else "; ".join(stage59_mismatches)
            or f"S42-STAGE59-COMPLETION-ROUTE:{stage42.get('S42-STAGE59-COMPLETION-ROUTE', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage60_final_recheck_stage59",
            "status": "PASS" if not stage60_mismatches and stage42_stage60_ok else "FAIL",
            "evidence": "repro/stage60_final_recheck_stage59/summary.csv",
            "detail": "Stage60 final recheck refreshes Stage59 before Stage42 closure"
            if not stage60_mismatches and stage42_stage60_ok
            else "; ".join(stage60_mismatches)
            or f"S42-STAGE60-FINAL-RECHECK-STAGE59:{stage42.get('S42-STAGE60-FINAL-RECHECK-STAGE59', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage61_native_perf_unlock_probe",
            "status": "PASS" if not stage61_mismatches and stage42_stage61_ok else "FAIL",
            "evidence": "repro/stage61_native_perf_unlock_probe/summary.csv",
            "detail": "Stage61 native perf unlock probe is recorded; current platform remains blocked"
            if not stage61_mismatches and stage42_stage61_ok
            else "; ".join(stage61_mismatches)
            or f"S42-STAGE61-NATIVE-PERF-UNLOCK:{stage42.get('S42-STAGE61-NATIVE-PERF-UNLOCK', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage62_fulltext_unlock_probe",
            "status": "PASS" if not stage62_mismatches and stage42_stage62_ok else "FAIL",
            "evidence": "repro/stage62_fulltext_unlock_probe/unlock_summary.csv",
            "detail": "Stage62 full-text unlock probe is recorded; current environment still needs a full-text artifact"
            if not stage62_mismatches and stage42_stage62_ok
            else "; ".join(stage62_mismatches)
            or f"S42-STAGE62-FULLTEXT-UNLOCK:{stage42.get('S42-STAGE62-FULLTEXT-UNLOCK', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage64a_post_variant_refresh",
            "status": "PASS" if not stage64a_mismatches and stage42_stage64a_ok else "FAIL",
            "evidence": "repro/stage64_post_variant_refresh/summary.csv",
            "detail": "Stage64A post-variant refresh passes for current smoke, repeated full-SAB, noise, and Stage50"
            if not stage64a_mismatches and stage42_stage64a_ok
            else "; ".join(stage64a_mismatches)
            or f"S42-STAGE64A-POST-VARIANT-REFRESH:{stage42.get('S42-STAGE64A-POST-VARIANT-REFRESH', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage65a_r4_unrolled_variant",
            "status": "PASS" if not stage65a_mismatches and stage42_stage65a_ok else "FAIL",
            "evidence": "repro/stage65_r4_unrolled_avx512/summary.csv",
            "detail": "Stage65A r4 row-unrolled AVX512 variant is recorded as negative/not promoted"
            if not stage65a_mismatches and stage42_stage65a_ok
            else "; ".join(stage65a_mismatches)
            or f"S42-STAGE65A-R4-UNROLLED:{stage42.get('S42-STAGE65A-R4-UNROLLED', {}).get('status', 'MISSING')}!=PASS",
        },
        {
            "check": "stage66a_post_variant_final_recheck",
            "status": "PASS" if not stage66a_mismatches and stage42_stage66a_ok else "FAIL",
            "evidence": "repro/stage66_post_variant_final_recheck/summary.csv",
            "detail": "Stage66A post-variant final-recheck control plane passes and closure audit records it"
            if not stage66a_mismatches and stage42_stage66a_ok
            else "; ".join(stage66a_mismatches)
            or (
                "S42-STAGE66A-POST-VARIANT-FINAL-RECHECK:"
                f"{stage42.get('S42-STAGE66A-POST-VARIANT-FINAL-RECHECK', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage67_final_recheck_stage66",
            "status": "PASS" if not stage67_mismatches and stage42_stage67_ok else "FAIL",
            "evidence": "repro/stage67_final_recheck_stage66/summary.csv; repro/stage67_final_recheck_stage66/decision.csv",
            "detail": "Stage67 final recheck runs Stage66A and closure audit records the post-summary Stage42 rebuild"
            if not stage67_mismatches and stage42_stage67_ok
            else "; ".join(stage67_mismatches)
            or (
                "S42-STAGE67-FINAL-RECHECK-STAGE66:"
                f"{stage42.get('S42-STAGE67-FINAL-RECHECK-STAGE66', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage68_frontier_closure_consistency",
            "status": "PASS" if not stage68_mismatches and stage42_stage68_ok else "FAIL",
            "evidence": "repro/stage68_frontier_closure_consistency.csv",
            "detail": "Stage68 confirms Stage42, Stage51 G6, Stage57, and Stage59 labels are consistent"
            if not stage68_mismatches and stage42_stage68_ok
            else "; ".join(stage68_mismatches)
            or (
                "S42-STAGE68-FRONTIER-CLOSURE-CONSISTENCY:"
                f"{stage42.get('S42-STAGE68-FRONTIER-CLOSURE-CONSISTENCY', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage69_local_variant_feasibility",
            "status": "PASS" if not stage69_mismatches and stage42_stage69_ok else "FAIL",
            "evidence": "repro/stage69_local_variant_feasibility.csv",
            "detail": "Stage69 records no unblocked local variant and rejects the direct H3 sparse-selector shortcut"
            if not stage69_mismatches and stage42_stage69_ok
            else "; ".join(stage69_mismatches)
            or (
                "S42-STAGE69-LOCAL-VARIANT-FEASIBILITY:"
                f"{stage42.get('S42-STAGE69-LOCAL-VARIANT-FEASIBILITY', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage70_external_unlock_preflight",
            "status": "PASS" if not stage70_mismatches and stage42_stage70_ok else "FAIL",
            "evidence": "repro/stage70_external_unlock_preflight.csv",
            "detail": "Stage70 records native-perf, full-text, novelty, and local-variant unlock prerequisites"
            if not stage70_mismatches and stage42_stage70_ok
            else "; ".join(stage70_mismatches)
            or (
                "S42-STAGE70-EXTERNAL-UNLOCK-PREFLIGHT:"
                f"{stage42.get('S42-STAGE70-EXTERNAL-UNLOCK-PREFLIGHT', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage71_final_recheck_stage70",
            "status": "PASS" if not stage71_mismatches and stage42_stage71_ok else "FAIL",
            "evidence": "repro/stage71_final_recheck_stage70/summary.csv; repro/stage71_final_recheck_stage70/decision.csv",
            "detail": "Stage71 final recheck refreshes Stage70 before Stage42 closure"
            if not stage71_mismatches and stage42_stage71_ok
            else "; ".join(stage71_mismatches)
            or (
                "S42-STAGE71-FINAL-RECHECK-STAGE70:"
                f"{stage42.get('S42-STAGE71-FINAL-RECHECK-STAGE70', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage72_external_source_refresh",
            "status": "PASS" if not stage72_mismatches and stage42_stage72_ok else "FAIL",
            "evidence": "repro/stage72_external_source_refresh/summary.csv",
            "detail": "Stage72 refreshes author/DOI/code routes and preserves full-text blockers"
            if not stage72_mismatches and stage42_stage72_ok
            else "; ".join(stage72_mismatches)
            or (
                "S42-STAGE72-EXTERNAL-SOURCE-REFRESH:"
                f"{stage42.get('S42-STAGE72-EXTERNAL-SOURCE-REFRESH', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage73_final_recheck_stage72",
            "status": "PASS" if not stage73_mismatches and stage42_stage73_ok else "FAIL",
            "evidence": "repro/stage73_final_recheck_stage72/summary.csv; repro/stage73_final_recheck_stage72/decision.csv",
            "detail": "Stage73 final recheck refreshes Stage72 before blocker/frontier/closure rebuilds"
            if not stage73_mismatches and stage42_stage73_ok
            else "; ".join(stage73_mismatches)
            or (
                "S42-STAGE73-FINAL-RECHECK-STAGE72:"
                f"{stage42.get('S42-STAGE73-FINAL-RECHECK-STAGE72', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage74_r_scaling_boundary",
            "status": "PASS" if not stage74_mismatches and stage42_stage74_ok else "FAIL",
            "evidence": "repro/stage74_r_scaling_boundary/decision.csv",
            "detail": "Stage74 records r=6/r=8 smoke and rejects direct r>4 promotion under current evidence"
            if not stage74_mismatches and stage42_stage74_ok
            else "; ".join(stage74_mismatches)
            or (
                "S42-STAGE74-R-SCALING-BOUNDARY:"
                f"{stage42.get('S42-STAGE74-R-SCALING-BOUNDARY', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage75_rgt4_profile_boundary",
            "status": "PASS" if not stage75_mismatches and stage42_stage75_ok else "FAIL",
            "evidence": "repro/stage75_rgt4_profile_boundary/decision.csv",
            "detail": "Stage75 records profile-backed r=6/r=8 boundary attribution under invariant SAB counts"
            if not stage75_mismatches and stage42_stage75_ok
            else "; ".join(stage75_mismatches)
            or (
                "S42-STAGE75-RGT4-PROFILE-BOUNDARY:"
                f"{stage42.get('S42-STAGE75-RGT4-PROFILE-BOUNDARY', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage76_rgt4_kernel_feasibility",
            "status": "PASS" if not stage76_mismatches and stage42_stage76_ok else "FAIL",
            "evidence": "repro/stage76_rgt4_kernel_feasibility/summary.csv",
            "detail": "Stage76 records correct r=6/r=8 generic MAT kernel behavior but rejects direct r>4 kernel promotion"
            if not stage76_mismatches and stage42_stage76_ok
            else "; ".join(stage76_mismatches)
            or (
                "S42-STAGE76-RGT4-KERNEL-FEASIBILITY:"
                f"{stage42.get('S42-STAGE76-RGT4-KERNEL-FEASIBILITY', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage77_rgt4_fused_mat_kernel",
            "status": "PASS" if not stage77_mismatches and stage42_stage77_ok else "FAIL",
            "evidence": "repro/stage77_rgt4_fused_mat_kernel/summary.csv",
            "detail": "Stage77 records H11 fused r>4 MAT as positive smoke and requires repeated gates before promotion"
            if not stage77_mismatches and stage42_stage77_ok
            else "; ".join(stage77_mismatches)
            or (
                "S42-STAGE77-RGT4-FUSED-MAT-KERNEL:"
                f"{stage42.get('S42-STAGE77-RGT4-FUSED-MAT-KERNEL', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage78_rgt4_fused_repeated_gates",
            "status": "PASS" if not stage78_mismatches and stage42_stage78_ok else "FAIL",
            "evidence": "repro/stage78_rgt4_fused_repeated_gates/summary.csv",
            "detail": "Stage78 records H11 r=6 fused r>4 MAT as a promotion candidate and keeps Stage79 high-stat confirmation required"
            if not stage78_mismatches and stage42_stage78_ok
            else "; ".join(stage78_mismatches)
            or (
                "S42-STAGE78-RGT4-FUSED-REPEATED-GATES:"
                f"{stage42.get('S42-STAGE78-RGT4-FUSED-REPEATED-GATES', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage79_rgt4_fused_high_stat",
            "status": "PASS" if not stage79_mismatches and stage42_stage79_ok else "FAIL",
            "evidence": "repro/stage79_rgt4_fused_high_stat/summary.csv",
            "detail": "Stage79 records H11 r=6 fused r>4 MAT high-stat evidence as review-required, not automatically promoted"
            if not stage79_mismatches and stage42_stage79_ok
            else "; ".join(stage79_mismatches)
            or (
                "S42-STAGE79-RGT4-FUSED-HIGH-STAT:"
                f"{stage42.get('S42-STAGE79-RGT4-FUSED-HIGH-STAT', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage80_promotion_policy_audit",
            "status": "PASS" if not stage80_mismatches and stage42_stage80_ok else "FAIL",
            "evidence": "repro/stage80_promotion_policy_audit/summary.csv",
            "detail": "Stage80 keeps H11 r=6 fused MAT as explicit experimental evidence only and does not promote or default it"
            if not stage80_mismatches and stage42_stage80_ok
            else "; ".join(stage80_mismatches)
            or (
                "S42-STAGE80-PROMOTION-POLICY-AUDIT:"
                f"{stage42.get('S42-STAGE80-PROMOTION-POLICY-AUDIT', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage81_next_variant_triage",
            "status": "PASS" if not stage81_mismatches and stage42_stage81_ok else "FAIL",
            "evidence": "repro/stage81_next_variant_triage.csv",
            "detail": "Stage81 selects post-H11 fused r=6 profile attribution and does not promote new hot-path code"
            if not stage81_mismatches and stage42_stage81_ok
            else "; ".join(stage81_mismatches)
            or (
                "S42-STAGE81-NEXT-VARIANT-TRIAGE:"
                f"{stage42.get('S42-STAGE81-NEXT-VARIANT-TRIAGE', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage82_post_h11_profile",
            "status": "PASS" if not stage82_mismatches and stage42_stage82_ok else "FAIL",
            "evidence": "repro/stage82_post_h11_profile/decision.csv",
            "detail": "Stage82 profiles explicit H11 fused r=6 and records MAT body as the primary profile target"
            if not stage82_mismatches and stage42_stage82_ok
            else "; ".join(stage82_mismatches)
            or (
                "S42-STAGE82-POST-H11-PROFILE:"
                f"{stage42.get('S42-STAGE82-POST-H11-PROFILE', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage83_mat_body_design_check",
            "status": "PASS" if not stage83_mismatches and stage42_stage83_ok else "FAIL",
            "evidence": "repro/stage83_mat_body_design_check/decision.csv",
            "detail": "Stage83 selects H13 r=6 full-output tile-sweep preflight and keeps sparse selector skipping blocked"
            if not stage83_mismatches and stage42_stage83_ok
            else "; ".join(stage83_mismatches)
            or (
                "S42-STAGE83-MAT-BODY-DESIGN-CHECK:"
                f"{stage42.get('S42-STAGE83-MAT-BODY-DESIGN-CHECK', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage84_h13_r6_tile_sweep_preflight",
            "status": "PASS" if not stage84_mismatches and stage42_stage84_ok else "FAIL",
            "evidence": "repro/stage84_h13_r6_tile_sweep_preflight/summary.csv",
            "detail": "Stage84 records H13 r=6 tile-sweep as kernel-positive but complete-SAB neutral/negative and not promoted"
            if not stage84_mismatches and stage42_stage84_ok
            else "; ".join(stage84_mismatches)
            or (
                "S42-STAGE84-H13-R6-TILE-SWEEP:"
                f"{stage42.get('S42-STAGE84-H13-R6-TILE-SWEEP', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage86_secondary_cmux_materialization",
            "status": "PASS" if not stage86_mismatches and stage42_stage86_ok else "FAIL",
            "evidence": "repro/stage86_secondary_cmux_materialization/decision.csv",
            "detail": "Stage86 selects H14 backend FromDFT+add materialization preflight without promoting code"
            if not stage86_mismatches and stage42_stage86_ok
            else "; ".join(stage86_mismatches)
            or (
                "S42-STAGE86-SECONDARY-CMUX-MATERIALIZATION:"
                f"{stage42.get('S42-STAGE86-SECONDARY-CMUX-MATERIALIZATION', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage87_h14_backend_from_dft_add_preflight",
            "status": "PASS" if not stage87_mismatches and stage42_stage87_ok else "FAIL",
            "evidence": "repro/stage87_h14_backend_from_dft_add_preflight/summary.csv",
            "detail": "Stage87 records H14 backend FromDFT-add as a one-run promotion candidate without promoting code"
            if not stage87_mismatches and stage42_stage87_ok
            else "; ".join(stage87_mismatches)
            or (
                "S42-STAGE87-H14-BACKEND-FROM-DFT-ADD:"
                f"{stage42.get('S42-STAGE87-H14-BACKEND-FROM-DFT-ADD', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage88_h14_backend_repeated_gates",
            "status": "PASS" if not stage88_mismatches and stage42_stage88_ok else "FAIL",
            "evidence": "repro/stage88_h14_backend_repeated_gates/summary.csv",
            "detail": "Stage88 records H14 backend FromDFT-add as a repeated/noise/resource promotion candidate without promoting defaults"
            if not stage88_mismatches and stage42_stage88_ok
            else "; ".join(stage88_mismatches)
            or (
                "S42-STAGE88-H14-BACKEND-REPEATED-GATES:"
                f"{stage42.get('S42-STAGE88-H14-BACKEND-REPEATED-GATES', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage89_h14_promotion_policy",
            "status": "PASS" if not stage89_mismatches and stage42_stage89_ok else "FAIL",
            "evidence": "repro/stage89_h14_promotion_policy_integration/summary.csv",
            "detail": "Stage89 promotes H14 backend FromDFT-add as the preferred explicit r=6 path while defaults remain unchanged"
            if not stage89_mismatches and stage42_stage89_ok
            else "; ".join(stage89_mismatches)
            or (
                "S42-STAGE89-H14-PROMOTION-POLICY:"
                f"{stage42.get('S42-STAGE89-H14-PROMOTION-POLICY', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage90_external_claim_unlock",
            "status": "PASS" if not stage90_mismatches and stage42_stage90_ok else "FAIL",
            "evidence": "repro/stage90_external_claim_unlock/summary.csv",
            "detail": "Stage90 records the external-claim probe and preserves native-perf/full-text/novelty blockers"
            if not stage90_mismatches and stage42_stage90_ok
            else "; ".join(stage90_mismatches)
            or (
                "S42-STAGE90-EXTERNAL-CLAIM-UNLOCK:"
                f"{stage42.get('S42-STAGE90-EXTERNAL-CLAIM-UNLOCK', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage91_final_package",
            "status": "PASS" if not stage91_mismatches and stage42_stage91_ok else "FAIL",
            "evidence": "repro/stage91_final_package/summary.csv",
            "detail": "Stage91 freezes the scoped SAB optimization package while preserving stronger-claim blockers"
            if not stage91_mismatches and stage42_stage91_ok
            else "; ".join(stage91_mismatches)
            or (
                "S42-STAGE91-FINAL-PACKAGE:"
                f"{stage42.get('S42-STAGE91-FINAL-PACKAGE', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage92_external_unlock_execution",
            "status": "PASS" if not stage92_mismatches and stage42_stage92_ok else "FAIL",
            "evidence": "repro/stage92_external_unlock_execution/summary.csv",
            "detail": "Stage92 records executable external unlock lanes while preserving stronger-claim blockers"
            if not stage92_mismatches and stage42_stage92_ok
            else "; ".join(stage92_mismatches)
            or (
                "S42-STAGE92-EXTERNAL-UNLOCK-EXECUTION:"
                f"{stage42.get('S42-STAGE92-EXTERNAL-UNLOCK-EXECUTION', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage93_external_lane_attempt",
            "status": "PASS" if not stage93_mismatches and stage42_stage93_ok else "FAIL",
            "evidence": "repro/stage93_external_lane_attempt/summary.csv",
            "detail": "Stage93 records current external lane attempts while preserving stronger-claim blockers"
            if not stage93_mismatches and stage42_stage93_ok
            else "; ".join(stage93_mismatches)
            or (
                "S42-STAGE93-EXTERNAL-LANE-ATTEMPT:"
                f"{stage42.get('S42-STAGE93-EXTERNAL-LANE-ATTEMPT', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage94_local_frontier_audit",
            "status": "PASS" if not stage94_mismatches and stage42_stage94_ok else "FAIL",
            "evidence": "repro/stage94_local_frontier_audit/summary.csv",
            "detail": "Stage94 records no justified new local hot-path candidate under current evidence"
            if not stage94_mismatches and stage42_stage94_ok
            else "; ".join(stage94_mismatches)
            or (
                "S42-STAGE94-LOCAL-FRONTIER-AUDIT:"
                f"{stage42.get('S42-STAGE94-LOCAL-FRONTIER-AUDIT', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage95_public_source_reprobe",
            "status": "PASS" if not stage95_mismatches and stage42_stage95_ok else "FAIL",
            "evidence": "repro/stage95_public_source_reprobe/summary.csv",
            "detail": "Stage95 refreshes public source routes while preserving full-text/claim blockers"
            if not stage95_mismatches and stage42_stage95_ok
            else "; ".join(stage95_mismatches)
            or (
                "S42-STAGE95-PUBLIC-SOURCE-REPROBE:"
                f"{stage42.get('S42-STAGE95-PUBLIC-SOURCE-REPROBE', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage96_upstream_delta_audit",
            "status": "PASS" if not stage96_mismatches and stage42_stage96_ok else "FAIL",
            "evidence": "repro/stage96_upstream_delta_audit/summary.csv",
            "detail": "Stage96 records upstream/local provenance and default-false flag guards"
            if not stage96_mismatches and stage42_stage96_ok
            else "; ".join(stage96_mismatches)
            or (
                "S42-STAGE96-UPSTREAM-DELTA-AUDIT:"
                f"{stage42.get('S42-STAGE96-UPSTREAM-DELTA-AUDIT', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage97_source_delta_guard",
            "status": "PASS" if not stage97_mismatches and stage42_stage97_ok else "FAIL",
            "evidence": "repro/stage97_source_delta_guard/summary.csv",
            "detail": "Stage97 records source-delta isolation, default-false flags, and scalar/default smoke guards"
            if not stage97_mismatches and stage42_stage97_ok
            else "; ".join(stage97_mismatches)
            or (
                "S42-STAGE97-SOURCE-DELTA-GUARD:"
                f"{stage42.get('S42-STAGE97-SOURCE-DELTA-GUARD', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage98_current_smoke_refresh",
            "status": "PASS" if not stage98_mismatches and stage42_stage98_ok else "FAIL",
            "evidence": "repro/stage98_current_smoke_refresh/summary.csv",
            "detail": "Stage98 current-head smoke refresh passes scalar/default, active PVW target, backend PVW target, and scalar ternary checks"
            if not stage98_mismatches and stage42_stage98_ok
            else "; ".join(stage98_mismatches)
            or (
                "S42-STAGE98-CURRENT-SMOKE-REFRESH:"
                f"{stage42.get('S42-STAGE98-CURRENT-SMOKE-REFRESH', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage99_external_blocker_reprobe",
            "status": "PASS" if not stage99_mismatches and stage42_stage99_ok else "FAIL",
            "evidence": "repro/stage99_external_blocker_reprobe/summary.csv",
            "detail": "Stage99 records post-Stage98 external blocker reprobe and full-text review-required state"
            if not stage99_mismatches and stage42_stage99_ok
            else "; ".join(stage99_mismatches)
            or (
                "S42-STAGE99-EXTERNAL-BLOCKER-REPROBE:"
                f"{stage42.get('S42-STAGE99-EXTERNAL-BLOCKER-REPROBE', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage100_fulltext_anchor_prefill",
            "status": "PASS" if not stage100_mismatches and stage42_stage100_ok else "FAIL",
            "evidence": "repro/stage100_fulltext_anchor_prefill/summary.csv",
            "detail": "Stage100 records candidate-only 2025/686 source anchors while preserving manual review requirements"
            if not stage100_mismatches and stage42_stage100_ok
            else "; ".join(stage100_mismatches)
            or (
                "S42-STAGE100-FULLTEXT-ANCHOR-PREFILL:"
                f"{stage42.get('S42-STAGE100-FULLTEXT-ANCHOR-PREFILL', {}).get('status', 'MISSING')}!=PASS"
            ),
        },
        {
            "check": "stage44_recheck_integration",
            "status": "PASS" if not stage44_recheck_mismatches else "FAIL",
            "evidence": "repro/final_goal_recheck_stage44_reprobe/summary.csv",
            "detail": "final recheck can refresh Stage44, final audit, and Stage42 closure"
            if not stage44_recheck_mismatches
            else "; ".join(stage44_recheck_mismatches),
        },
        {
            "check": "default_recheck_closure",
            "status": "PASS" if default_ok else "FAIL",
            "evidence": "repro/final_goal_recheck/summary.csv",
            "detail": "default final recheck includes stage42_evidence_closure=PASS"
            if default_ok
            else "default recheck closure or final decision missing",
        },
        {
            "check": "closure_only_recheck",
            "status": "PASS" if closure_ok else "FAIL",
            "evidence": "repro/final_goal_recheck_stage42_closure/summary.csv",
            "detail": "closure-only final recheck includes stage42_evidence_closure=PASS"
            if closure_ok
            else "closure-only recheck closure or final decision missing",
        },
        {
            "check": "stage42_run_log_rows",
            "status": "PASS" if not missing_run_ids else "FAIL",
            "evidence": "repro/run_log.csv",
            "detail": "all Stage42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62 plus Stage64A/Stage65A/Stage66A/Stage67/Stage68/Stage69/Stage70/Stage71/Stage72/Stage73/Stage74/Stage75/Stage76/Stage77/Stage78/Stage79/Stage80/Stage81/Stage82/Stage83/Stage84/Stage86/Stage87/Stage88/Stage89/Stage90/Stage91/Stage92/Stage93/Stage94/Stage95/Stage96/Stage97/Stage98/Stage99/Stage100 closure run rows are present"
            if not missing_run_ids
            else "; ".join(missing_run_ids),
        },
        {
            "check": "artifact_manifest_mentions",
            "status": "PASS" if not missing_manifest_mentions else "FAIL",
            "evidence": "repro/artifact_manifest.md",
            "detail": "Stage42 verifier, closure manifest, Stage44 re-probe, Stage45 refactor, Stage46 target smoke, Stage47 full-SAB smoke, Stage48 noise smoke, Stage49 repeated full-SAB stability, Stage50 performance matrix, Stage51 goal frontier, Stage52 external unlock readiness, Stage53 final recheck integration, Stage54 default final recheck, Stage55 paper probe, Stage56 final recheck integration, Stage57 scope-label audit, Stage58 final recheck integration, Stage59 completion route, Stage60 final recheck integration, Stage61 native perf unlock probe, Stage62 full-text unlock probe, Stage64A post-variant refresh, Stage65A r4 unrolled variant, Stage66A post-variant final recheck, Stage67 final-recheck Stage66A integration, Stage68 frontier/closure consistency, Stage69 local variant feasibility, Stage70 external unlock preflight, Stage71 final-recheck Stage70 integration, Stage72 external source refresh, Stage73 final-recheck Stage72 integration, Stage74 r-scaling boundary, Stage75 r>4 profile boundary, Stage76 r>4 kernel feasibility, Stage77 r>4 fused MAT smoke, Stage78 r>4 fused repeated gates, Stage79 r>4 fused high-stat review gate, Stage80 promotion policy audit, Stage81 next-variant triage, Stage82 post-H11 profile, Stage83 MAT body design check, Stage84 H13 r=6 tile-sweep preflight, Stage86 secondary CMUX materialization design gate, Stage87 H14 backend FromDFT-add preflight, Stage88 H14 backend repeated gates, Stage89 H14 promotion policy integration, Stage90 external claim unlock, Stage91 final scoped package, Stage92 external unlock packet, Stage93 external lane attempt, Stage94 local frontier audit, Stage95 public source reprobe, Stage96 upstream delta audit, Stage97 source delta guard, Stage98 current-head smoke refresh, Stage99 external blocker reprobe, and Stage100 full-text anchor prefill are registered"
            if not missing_manifest_mentions
            else "; ".join(missing_manifest_mentions),
        },
    ]

    pass_all = all(
        row["status"] == "PASS" or row["check"] == "verification_input_commit"
        for row in checks
    )
    checks.append(
        {
            "check": "stage42_verify_decision",
            "status": "PASS_STAGE42_VERIFY_STRONGER_CLAIMS_BLOCKED"
            if pass_all
            else "FAIL_STAGE42_VERIFY",
            "evidence": decision_evidence,
            "detail": "Stage42 closure package is internally consistent; stronger claims remain blocked."
            if pass_all
            else "Inspect failing checks before relying on Stage42 closure evidence.",
        }
    )
    return checks


def write_md(rows: List[Dict[str, str]], out_md: Path) -> None:
    lines = [
        "# Stage 42 Closure Verification Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "This verifier checks the Stage 42 evidence-closure package without",
        "regenerating the Stage 42 audit or manifest.",
        "",
        "## Checks",
        "",
        "| check | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['check']} | {row['status']} | {row['evidence']} | {row['detail']} |")
    decision = row_by(rows, "check", "stage42_verify_decision")
    lines.extend(["", "## Decision", "", decision.get("detail", "No decision row generated.")])
    out_md.parent.mkdir(parents=True, exist_ok=True)
    with out_md.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default="repro/stage42_closure_verify",
        help="Output directory for the verifier summary CSV.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Print verification CSV to stdout without writing repo artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status_before_outputs = git_status_short()
    rows = build_checks(
        status_before_outputs,
        "stdout" if args.check_only else "repro/stage42_closure_verify/summary.csv",
    )
    decision = row_by(rows, "check", "stage42_verify_decision")
    if args.check_only:
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=["check", "status", "evidence", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        return 0 if decision.get("status") == "PASS_STAGE42_VERIFY_STRONGER_CLAIMS_BLOCKED" else 1

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    write_csv(out_dir / "summary.csv", rows)
    write_md(rows, ROOT / "docs" / "stage42_closure_verify_log.md")
    print(f"Wrote {(out_dir / 'summary.csv').relative_to(ROOT).as_posix()}")
    print("Wrote docs/stage42_closure_verify_log.md")
    return 0 if decision.get("status") == "PASS_STAGE42_VERIFY_STRONGER_CLAIMS_BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
