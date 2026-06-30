#!/usr/bin/env python3
"""Build the Stage 42 evidence-closure audit.

This script checks whether the current scoped PVW/MAT-SAB evidence chain and
Stage90 control-plane/claim-guard extensions are internally consistent. It does not run
benchmarks or upgrade claims; it verifies that the committed artifacts still
support the recorded scope.
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro" / "stage42_evidence_closure_audit.csv"
OUT_MD = ROOT / "docs" / "stage42_evidence_closure_audit.md"
OUT_MANIFEST = ROOT / "repro" / "stage42_evidence_closure_manifest.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
LOOP = ROOT / "docs" / "loop_engineering.md"
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"
FREEZE_MANIFEST = ROOT / "repro" / "stage40_final_freeze_manifest.csv"
POSTFREEZE = ROOT / "repro" / "stage40_postfreeze_verify" / "summary.csv"
STAGE41 = ROOT / "repro" / "stage41_external_unlock_packet.csv"
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
STAGE101_CB5_REMOTE_NATIVE_PERF = (
    ROOT / "repro" / "stage101_cb5_remote_native_perf" / "summary.csv"
)
STAGE102_686_SOURCE_ANCHOR_REVIEW = (
    ROOT / "repro" / "stage102_686_source_anchor_review" / "summary.csv"
)
STAGE103_RELATED_WORK_NOVELTY_REVIEW = (
    ROOT / "repro" / "stage103_related_work_novelty_review" / "summary.csv"
)
ARTIFACT_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
REPRO_CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
REMAINING_BLOCKERS = ROOT / "repro" / "remaining_blocker_dashboard.csv"


EXPECTED_AUDIT_STATUS = {
    "A1": "PASS_SCOPED",
    "A2": "PASS_SCOPED",
    "A2b": "PASS_10RUN_TARGET_PERF",
    "A3": "PASS_SCOPED",
    "A3b": "PASS_STAGE_NOISE_10SEED",
    "A3c": "PASS_TARGET_NOISE_50SEED",
    "A4": "PASS_SMOKE_RESOURCE",
    "A4b": "PASS_RESOURCE_3RUN",
    "A5": "PASS_SCOPED",
    "A5b": "PASS_CURRENT_SMOKE",
    "A6": "PASS_SCOPED_BOUNDARY_REVIEWED",
    "A7": "PASS_ADDED_PARAM_10RUN_20SEED",
    "A8": "PASS_COUNTER_ATTRIBUTION_EXTERNAL",
    "A8b": "PASS_EXTERNAL_EVIDENCE_REVIEWED",
    "A9": "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED",
}

EXPECTED_STAGE41_READINESS = {
    "S41-FULLTEXT-INTAKE": "READY_FOR_MANUAL_REVIEW",
    "S41-NATIVE-PERF-INTAKE": "WAIT_NATIVE_PERF",
    "S41-EXTERNAL-REGISTRATION": "READY_TO_REGISTER",
    "S41-FINAL-RECHECK": "READY_AFTER_UNLOCKS",
}

EXPECTED_REMAINING_BLOCKERS = {
    "CB5": {
        "status_tokens": [
            "final_A8=PASS_COUNTER_ATTRIBUTION_EXTERNAL",
            "cb5=RESOLVED_NATIVE_PERF_COUNTER_EVIDENCE",
            "stage101=PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED",
            "external_perf=PASS_COUNTER_ATTRIBUTION_AVAILABLE",
        ],
        "policy_tokens": ["Do not claim theoretical MAT-AVX512"],
    },
    "CB6": {
        "status_tokens": [
            "cb6=RESOLVED_REVIEWED_SCOPED_NOVELTY",
            "stage103=PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED",
            "related=SCOPED_RELATED_WORK_REFRESHED__NOVELTY_STILL_BLOCKED",
            "novelty_gate=BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW",
        ],
        "policy_tokens": ["scoped engineering/systems", "broad novelty claims remain blocked"],
    },
    "CB7": {
        "status_tokens": [
            "final_A8b=PASS_EXTERNAL_EVIDENCE_REVIEWED",
            "cb7=RESOLVED_FULLTEXT_SOURCE_ANCHORS_VERIFIED",
            "stage102=PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED",
            "stage55_metadata=PASS",
            "external_fulltext=AVAILABLE_UNREVIEWED",
        ],
        "policy_tokens": ["reviewed Stage102 anchors", "local implementation evidence"],
    },
    "A9": {
        "status_tokens": [
            "final_A9=SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED",
            "stage44_decision=WAIT_EXTERNAL_UNLOCKS",
            "stage41_final=READY_AFTER_UNLOCKS",
        ],
        "policy_tokens": ["scoped-reviewed", "claims beyond scoped engineering remain blocked"],
    },
}

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

STAGE101_ARTIFACTS = [
    "docs/stage101_cb5_remote_native_perf_log.md",
    "experiments/stage101_cb5_remote_native_perf_plan.md",
    "scripts/build_stage101_cb5_remote_native_perf.py",
    "repro/stage101_cb5_remote_native_perf/summary.csv",
    "repro/stage101_cb5_remote_native_perf/counter_metrics.csv",
    "repro/stage101_cb5_remote_native_perf/artifact_index.csv",
    "repro/stage101_cb5_remote_native_perf/stage101_remote_env.log",
    "repro/stage101_cb5_remote_native_perf/stage28_native_perf_counter_gate/summary.csv",
    "repro/stage101_cb5_remote_native_perf/stage28_native_perf_counter_gate/bench_perf.log",
    "repro/stage101_cb5_remote_native_perf/stage28_native_perf_counter_gate/bench_run.log",
    "repro/stage101_cb5_remote_native_perf/attribution_probe/event_support.csv",
    "repro/stage101_cb5_remote_native_perf/attribution_probe/bench_attribution_perf.log",
    "repro/stage101_cb5_remote_native_perf/attribution_probe/bench_attribution_run.log",
]

STAGE102_ARTIFACTS = [
    "docs/stage102_686_source_anchor_review_log.md",
    "experiments/stage102_686_source_anchor_review_plan.md",
    "scripts/build_stage102_686_source_anchor_review.py",
    "repro/stage102_686_source_anchor_review/summary.csv",
    "repro/stage102_686_source_anchor_review/review_matrix.csv",
    "repro/stage102_686_source_anchor_review/artifact_index.csv",
    "repro/stage38_fulltext_review_gate/review_checklist.csv",
]

STAGE103_ARTIFACTS = [
    "docs/stage103_related_work_novelty_review_log.md",
    "experiments/stage103_related_work_novelty_review_plan.md",
    "scripts/build_stage103_related_work_novelty_review.py",
    "repro/stage103_related_work_novelty_review/summary.csv",
    "repro/stage103_related_work_novelty_review/related_work_matrix.csv",
    "repro/stage103_related_work_novelty_review/novelty_claim_matrix.csv",
    "repro/stage103_related_work_novelty_review/source_verification.csv",
    "repro/stage103_related_work_novelty_review/artifact_index.csv",
]

REQUIRED_FILES = [
    "docs/goal_sab_max_acceleration.md",
    "docs/roadmap_stage19_plus.md",
    "docs/loop_engineering.md",
    "docs/remaining_blocker_dashboard.md",
    "docs/stage41_external_unlock_packet.md",
    "experiments/stage41_external_unlock_plan.md",
    "scripts/build_remaining_blocker_dashboard.py",
    "scripts/build_stage41_external_unlock_packet.py",
    "scripts/build_stage42_evidence_closure_audit.py",
    "repro/remaining_blocker_dashboard.csv",
    "repro/stage41_external_unlock_packet.csv",
    "docs/stage43_postclosure_current_smoke_log.md",
    "experiments/stage43_postclosure_current_smoke_plan.md",
    "repro/stage43_current_smoke_after_stage42/summary.csv",
    "docs/stage44_external_unlock_reprobe_log.md",
    "experiments/stage44_external_unlock_reprobe_plan.md",
    "scripts/build_stage44_external_unlock_reprobe.py",
    "scripts/run_stage44_external_unlock_reprobe.sh",
    "repro/stage44_external_unlock_reprobe/summary.csv",
    "docs/stage45_active_state_refactor_log.md",
    "repro/stage45_active_state_refactor/summary.csv",
    "docs/stage46_wsl_active_state_target_smoke_log.md",
    "repro/stage46_wsl_active_state_target_smoke/summary.csv",
    "docs/stage47_wsl_full_sab_smoke_log.md",
    "repro/stage47_wsl_active_state_full_sab_smoke/summary.csv",
    "docs/stage48_wsl_noise_smoke_log.md",
    "repro/stage48_wsl_active_state_noise_smoke/summary.csv",
    "repro/stage48_wsl_active_state_noise_smoke/aggregate.csv",
    "docs/stage49_wsl_repeated_full_sab_log.md",
    "repro/stage49_wsl_repeated_full_sab/summary.csv",
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
    "docs/stage54_default_final_recheck_log.md",
    "repro/stage54_default_final_recheck/summary.csv",
    "docs/stage55_external_paper_probe_log.md",
    "scripts/build_stage55_external_paper_probe.py",
    "repro/stage55_external_paper_probe/summary.csv",
    "repro/stage55_external_paper_probe/access_probe.csv",
    "repro/stage55_external_paper_probe/crossref_summary.csv",
    "repro/stage55_external_paper_probe/crossref_metadata.json",
    "docs/stage56_final_recheck_stage55_log.md",
    "repro/stage56_final_recheck_stage55/summary.csv",
    "docs/stage57_scope_label_audit.md",
    "scripts/build_stage57_scope_label_audit.py",
    "repro/stage57_scope_label_audit.csv",
    "docs/stage58_final_recheck_stage57_log.md",
    "repro/stage58_final_recheck_stage57/summary.csv",
    "docs/roadmap_to_completion_after_stage58.md",
    "docs/stage59_completion_route_readiness.md",
    "scripts/build_stage59_completion_route_readiness.py",
    "repro/stage59_completion_route_readiness.csv",
    "docs/stage60_final_recheck_stage59_log.md",
    "repro/stage60_final_recheck_stage59/summary.csv",
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
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_0.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_1.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_2.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_3.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_4.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_5.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_6.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_7.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_8.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_9.log",
    "repro/stage79_rgt4_fused_high_stat/final_noise/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/final_noise/aggregate.csv",
    "repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866025.log",
    "repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866044.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_0/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/resource_run_0/r6/pvw.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_0/r6/scalar.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_1/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/resource_run_1/r6/pvw.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_1/r6/scalar.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_2/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/resource_run_2/r6/pvw.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_2/r6/scalar.log",
    "docs/stage80_promotion_policy_audit_log.md",
    "experiments/stage80_promotion_policy_audit_plan.md",
    "scripts/run_stage80_promotion_policy_audit.sh",
    "scripts/build_stage80_promotion_policy_audit.py",
    "repro/stage80_promotion_policy_audit/stage80_run.log",
    "repro/stage80_promotion_policy_audit/summary.csv",
    "repro/stage80_promotion_policy_audit/current_smoke/summary.csv",
    "repro/stage80_promotion_policy_audit/current_smoke/scalar_binary_SET_2_3_2048/build.log",
    "repro/stage80_promotion_policy_audit/current_smoke/scalar_binary_SET_2_3_2048/run.log",
    "repro/stage80_promotion_policy_audit/current_smoke/pvw_target_SET_2_3_2048/build.log",
    "repro/stage80_promotion_policy_audit/current_smoke/pvw_target_SET_2_3_2048/run.log",
    "repro/stage80_promotion_policy_audit/current_smoke/scalar_ternary_SET_2_3_2048/build.log",
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
        *STAGE101_ARTIFACTS,
        *STAGE102_ARTIFACTS,
        *STAGE103_ARTIFACTS,
    "repro/final_goal_recheck_stage42_closure/summary.csv",
    "repro/stage42_evidence_closure_manifest.csv",
]

POSTFREEZE_MANIFEST_ARTIFACTS = [
    "docs/goal_sab_max_acceleration.md",
    "docs/roadmap_stage19_plus.md",
    "docs/final_goal_recheck_log.md",
    "docs/remaining_blocker_dashboard.md",
    "docs/conditional_backlog_audit.md",
    "docs/stage41_external_unlock_packet.md",
    "docs/stage43_postclosure_current_smoke_log.md",
    "docs/stage44_external_unlock_reprobe_log.md",
    "experiments/final_goal_recheck_plan.md",
    "experiments/stage41_external_unlock_plan.md",
    "experiments/stage42_evidence_closure_audit_plan.md",
    "experiments/stage42_closure_verify_plan.md",
    "experiments/stage43_postclosure_current_smoke_plan.md",
    "experiments/stage44_external_unlock_reprobe_plan.md",
    "scripts/build_stage41_external_unlock_packet.py",
    "scripts/build_conditional_backlog_audit.py",
    "scripts/build_stage42_evidence_closure_audit.py",
    "scripts/verify_stage42_closure.py",
    "scripts/build_stage44_external_unlock_reprobe.py",
    "scripts/run_stage44_external_unlock_reprobe.sh",
    "scripts/run_final_goal_recheck.sh",
    "scripts/build_remaining_blocker_dashboard.py",
    "repro/artifact_manifest.md",
    "repro/reproduction_checklist.md",
    "repro/run_log.csv",
    "repro/conditional_backlog_audit.csv",
    "repro/remaining_blocker_dashboard.csv",
    "repro/stage41_external_unlock_packet.csv",
    "repro/stage43_current_smoke_after_stage42/summary.csv",
    "repro/stage43_current_smoke_after_stage42/scalar_binary_SET_2_3_2048/build.log",
    "repro/stage43_current_smoke_after_stage42/scalar_binary_SET_2_3_2048/run.log",
    "repro/stage43_current_smoke_after_stage42/pvw_target_SET_2_3_2048/build.log",
    "repro/stage43_current_smoke_after_stage42/pvw_target_SET_2_3_2048/run.log",
    "repro/stage43_current_smoke_after_stage42/scalar_ternary_SET_2_3_2048/build.log",
    "repro/stage44_external_unlock_reprobe/summary.csv",
    "repro/stage44_external_unlock_reprobe/citation_probe/summary.csv",
    "repro/stage44_external_unlock_reprobe/citation_probe/access_probe.csv",
    "repro/stage44_external_unlock_reprobe/native_perf_gate/summary.csv",
    "docs/stage45_active_state_refactor_log.md",
    "repro/stage45_active_state_refactor/summary.csv",
    "repro/stage45_active_state_refactor/ffnt_kernel_build.log",
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
    "repro/stage53_final_recheck_stage50_52/final_goal_audit.log",
    "repro/stage53_final_recheck_stage50_52/remaining_blocker_dashboard.log",
    "repro/stage53_final_recheck_stage50_52/stage50_performance_matrix.log",
    "repro/stage53_final_recheck_stage50_52/stage51_goal_frontier.log",
    "repro/stage53_final_recheck_stage50_52/stage52_external_unlock_readiness.log",
    "repro/stage53_final_recheck_stage50_52/stage42_evidence_closure.log",
    "docs/stage54_default_final_recheck_log.md",
    "repro/stage54_default_final_recheck/summary.csv",
    "repro/stage54_default_final_recheck/stage28_perf_gate.log",
    "repro/stage54_default_final_recheck/stage27_final_package.log",
    "repro/stage54_default_final_recheck/external_evidence_intake.log",
    "repro/stage54_default_final_recheck/conditional_backlog_audit.log",
    "repro/stage54_default_final_recheck/final_goal_audit.log",
    "repro/stage54_default_final_recheck/remaining_blocker_dashboard.log",
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
    "docs/stage51_goal_completion_frontier.md",
    "repro/stage51_goal_completion_frontier.csv",
    "docs/stage52_external_unlock_readiness.md",
    "repro/stage52_external_unlock_readiness.csv",
    "repro/stage57_scope_label_audit.csv",
    "docs/stage58_final_recheck_stage57_log.md",
    "repro/stage58_final_recheck_stage57/summary.csv",
    "repro/stage58_final_recheck_stage57/final_goal_audit.log",
    "repro/stage58_final_recheck_stage57/remaining_blocker_dashboard.log",
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
    "repro/stage60_final_recheck_stage59/final_goal_audit.log",
    "repro/stage60_final_recheck_stage59/remaining_blocker_dashboard.log",
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
    "repro/stage62_fulltext_unlock_probe/fulltext_gate.log",
    "repro/stage62_fulltext_unlock_probe/acm_pdf_head.log",
    "repro/stage62_fulltext_unlock_probe/acm_pdf_head.err",
    "repro/stage62_fulltext_unlock_probe/eprint_pdf_head.log",
    "repro/stage62_fulltext_unlock_probe/eprint_pdf_head.err",
    "docs/stage64_post_variant_refresh_log.md",
    "scripts/run_stage64_post_variant_refresh.sh",
    "scripts/build_stage64_post_variant_refresh_log.py",
    "repro/stage64_post_variant_refresh/summary.csv",
    "repro/stage64_post_variant_refresh/run.log",
    "repro/stage64_post_variant_refresh/current_smoke/summary.csv",
    "repro/stage64_post_variant_refresh/current_smoke/scalar_binary_SET_2_3_2048/build.log",
    "repro/stage64_post_variant_refresh/current_smoke/scalar_binary_SET_2_3_2048/run.log",
    "repro/stage64_post_variant_refresh/current_smoke/pvw_target_SET_2_3_2048/build.log",
    "repro/stage64_post_variant_refresh/current_smoke/pvw_target_SET_2_3_2048/run.log",
    "repro/stage64_post_variant_refresh/current_smoke/scalar_ternary_SET_2_3_2048/build.log",
    "repro/stage64_post_variant_refresh/full_sab_r2/summary.csv",
    "repro/stage64_post_variant_refresh/full_sab_r2/run_0.log",
    "repro/stage64_post_variant_refresh/full_sab_r2/run_1.log",
    "repro/stage64_post_variant_refresh/full_sab_r2/run_2.log",
    "repro/stage64_post_variant_refresh/full_sab_r4/summary.csv",
    "repro/stage64_post_variant_refresh/full_sab_r4/run_0.log",
    "repro/stage64_post_variant_refresh/full_sab_r4/run_1.log",
    "repro/stage64_post_variant_refresh/full_sab_r4/run_2.log",
    "repro/stage64_post_variant_refresh/final_noise/summary.csv",
    "repro/stage64_post_variant_refresh/final_noise/aggregate.csv",
    "repro/stage64_post_variant_refresh/final_noise/r2/seed_6864025.log",
    "repro/stage64_post_variant_refresh/final_noise/r4/seed_6864025.log",
    "docs/stage65_r4_unrolled_avx512_log.md",
    "experiments/stage65_r4_unrolled_avx512_plan.md",
    "algorithm_variants/pvw_sab_r4_unrolled_avx512.md",
    "scripts/run_stage65_r4_unrolled_avx512.sh",
    "scripts/build_stage65_r4_unrolled_avx512_log.py",
    "repro/stage65_r4_unrolled_avx512/summary.csv",
    "repro/stage65_r4_unrolled_avx512/kernel_microbench.csv",
    "repro/stage65_r4_unrolled_avx512/full_sab_smoke.csv",
    "repro/stage65_r4_unrolled_avx512/instruction_counts.csv",
    "repro/stage65_r4_unrolled_avx512/run.log",
    "repro/stage65_r4_unrolled_avx512/default_scalar_ffnt_smoke.log",
    "repro/stage65_r4_unrolled_avx512/specialized/kernel_run_0.log",
    "repro/stage65_r4_unrolled_avx512/specialized/full_r4/run_0.log",
    "repro/stage65_r4_unrolled_avx512/specialized/objdump_mattrgsw_polynomial.txt",
    "repro/stage65_r4_unrolled_avx512/r4_unrolled/kernel_run_0.log",
    "repro/stage65_r4_unrolled_avx512/r4_unrolled/full_r4/run_0.log",
    "repro/stage65_r4_unrolled_avx512/r4_unrolled/objdump_mattrgsw_polynomial.txt",
    "docs/stage66_post_variant_final_recheck_log.md",
    "experiments/stage66_post_variant_final_recheck_plan.md",
    "scripts/run_stage66_post_variant_final_recheck.sh",
    "scripts/build_stage66_post_variant_final_recheck_log.py",
    "repro/stage66_post_variant_final_recheck/summary.csv",
    "repro/stage66_post_variant_final_recheck/final_recheck/summary.csv",
    "repro/stage66_post_variant_final_recheck/final_recheck/stage27_final_package.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/external_evidence_intake.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/conditional_backlog_audit.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/final_goal_audit.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/remaining_blocker_dashboard.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/stage50_performance_matrix.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/stage51_goal_frontier.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/stage52_external_unlock_readiness.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/stage57_scope_label_audit.log",
    "repro/stage66_post_variant_final_recheck/final_recheck/stage59_completion_route.log",
    "docs/stage67_final_recheck_stage66_log.md",
    "experiments/stage67_final_recheck_stage66_plan.md",
    "scripts/build_stage67_final_recheck_stage66_log.py",
    "repro/stage67_final_recheck_stage66/summary.csv",
    "repro/stage67_final_recheck_stage66/decision.csv",
    "repro/stage67_final_recheck_stage66/stage66_post_variant_final_recheck.log",
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
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_0.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_1.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_2.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_3.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_4.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_5.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_6.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_7.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_8.log",
    "repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/run_9.log",
    "repro/stage79_rgt4_fused_high_stat/final_noise/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/final_noise/aggregate.csv",
    "repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866025.log",
    "repro/stage79_rgt4_fused_high_stat/final_noise/r6/seed_6866044.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_0/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/resource_run_0/r6/pvw.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_0/r6/scalar.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_1/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/resource_run_1/r6/pvw.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_1/r6/scalar.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_2/summary.csv",
    "repro/stage79_rgt4_fused_high_stat/resource_run_2/r6/pvw.log",
    "repro/stage79_rgt4_fused_high_stat/resource_run_2/r6/scalar.log",
    "docs/stage80_promotion_policy_audit_log.md",
    "experiments/stage80_promotion_policy_audit_plan.md",
    "scripts/run_stage80_promotion_policy_audit.sh",
    "scripts/build_stage80_promotion_policy_audit.py",
    "repro/stage80_promotion_policy_audit/stage80_run.log",
    "repro/stage80_promotion_policy_audit/summary.csv",
    "repro/stage80_promotion_policy_audit/current_smoke/summary.csv",
    "repro/stage80_promotion_policy_audit/current_smoke/scalar_binary_SET_2_3_2048/build.log",
    "repro/stage80_promotion_policy_audit/current_smoke/scalar_binary_SET_2_3_2048/run.log",
    "repro/stage80_promotion_policy_audit/current_smoke/pvw_target_SET_2_3_2048/build.log",
    "repro/stage80_promotion_policy_audit/current_smoke/pvw_target_SET_2_3_2048/run.log",
    "repro/stage80_promotion_policy_audit/current_smoke/scalar_ternary_SET_2_3_2048/build.log",
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
    *STAGE101_ARTIFACTS,
    *STAGE102_ARTIFACTS,
    *STAGE103_ARTIFACTS,
    "repro/final_goal_recheck_stage42_closure/summary.csv",
    "repro/final_goal_recheck_stage42_closure/stage42_evidence_closure.log",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row(
    check_id: str,
    category: str,
    status: str,
    evidence: str,
    detail: str,
    failure_action: str,
) -> Dict[str, str]:
    return {
        "check_id": check_id,
        "category": category,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "failure_action": failure_action,
    }


def pass_fail(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def manifest_row(artifact: str) -> Dict[str, str]:
    path = ROOT / artifact
    if not path.exists():
        return {
            "artifact": artifact,
            "exists": "no",
            "size_bytes": "",
            "sha256": "",
        }
    return {
        "artifact": artifact,
        "exists": "yes",
        "size_bytes": str(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def write_closure_manifest() -> None:
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rows = [manifest_row(artifact) for artifact in POSTFREEZE_MANIFEST_ARTIFACTS]
    with OUT_MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["artifact", "exists", "size_bytes", "sha256"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def check_roadmap() -> List[Dict[str, str]]:
    text = ROADMAP.read_text(encoding="utf-8") if ROADMAP.exists() else ""
    stages = sorted({int(m.group(1)) for m in re.finditer(r"^## Stage (\d+):", text, re.M)})
    expected = list(range(19, 63))
    missing_core = [stage for stage in expected if stage not in stages]
    unexpected_early = [stage for stage in stages if stage < 19]
    ok = not missing_core and not unexpected_early
    return [
        row(
            "S42-ROADMAP-STAGES",
            "roadmap",
            pass_fail(ok),
            ROADMAP.relative_to(ROOT).as_posix(),
            f"observed={stages}; required_core={expected}; missing_core={missing_core}; extra_post_core={[stage for stage in stages if stage > 62]}",
            "Restore Stage 19-62 core sections before using the roadmap as the active plan.",
        )
    ]


def latest_control_stage_label() -> str:
    text = ROADMAP.read_text(encoding="utf-8") if ROADMAP.exists() else ""
    stages = sorted({int(m.group(1)) for m in re.finditer(r"^## Stage (\d+):", text, re.M)})
    if not stages:
        return "Stage 19-62"
    return f"Stage 19-{stages[-1]}"


def check_final_audit() -> List[Dict[str, str]]:
    rows = {r.get("item_id"): r for r in read_csv(FINAL_AUDIT)}
    mismatches = []
    for item_id, expected in EXPECTED_AUDIT_STATUS.items():
        got = rows.get(item_id, {}).get("status", "MISSING")
        if got != expected:
            mismatches.append(f"{item_id}:{got}!={expected}")
    return [
        row(
            "S42-FINAL-AUDIT",
            "claim_scope",
            pass_fail(not mismatches),
            FINAL_AUDIT.relative_to(ROOT).as_posix(),
            "all expected scoped/blocker statuses present" if not mismatches else "; ".join(mismatches),
            "Regenerate and inspect the final goal audit before relying on scoped or blocked claim labels.",
        )
    ]


def check_stage41() -> List[Dict[str, str]]:
    rows = {r.get("unlock_id"): r for r in read_csv(STAGE41)}
    mismatches = []
    for unlock_id, expected in EXPECTED_STAGE41_READINESS.items():
        got = rows.get(unlock_id, {}).get("readiness", "MISSING")
        if got != expected:
            mismatches.append(f"{unlock_id}:{got}!={expected}")
    return [
        row(
            "S42-STAGE41-READINESS",
            "external_unlock",
            pass_fail(not mismatches),
            STAGE41.relative_to(ROOT).as_posix(),
            "all external-unlock rows remain waiting for external evidence"
            if not mismatches
            else "; ".join(mismatches),
            "Regenerate Stage 41 and manually review any readiness change before claim upgrade.",
        )
    ]


def check_stage43_smoke() -> List[Dict[str, str]]:
    rows = {r.get("step"): r for r in read_csv(STAGE43_SMOKE)}
    expected = {
        "scalar_binary_full_run": "PASS",
        "pvw_target_full_gate": "PASS",
        "scalar_ternary_build": "PASS",
    }
    mismatches = []
    for step, expected_status in expected.items():
        got = rows.get(step, {}).get("status", "MISSING")
        if got != expected_status:
            mismatches.append(f"{step}:{got}!={expected_status}")
    return [
        row(
            "S42-STAGE43-CURRENT-SMOKE",
            "current_smoke",
            pass_fail(not mismatches),
            STAGE43_SMOKE.relative_to(ROOT).as_posix(),
            "scalar binary, PVW target, and scalar ternary smoke rows pass"
            if not mismatches
            else "; ".join(mismatches),
            "Rerun Stage 43 current smoke before relying on current-head build/correctness evidence.",
        )
    ]


def check_stage44_reprobe() -> List[Dict[str, str]]:
    rows = {r.get("item"): r for r in read_csv(STAGE44_REPROBE)}
    expected = {
        "citation_probe_command": "PASS",
        "fulltext_pdf_access": "BLOCKED",
        "native_perf_hardware_counter_gate": "BLOCKED",
        "external_fulltext_intake": "MISSING",
        "external_native_perf_intake": "MISSING",
        "stage44_decision": "WAIT_EXTERNAL_UNLOCKS",
    }
    mismatches = []
    for item, expected_status in expected.items():
        got = rows.get(item, {}).get("status", "MISSING")
        if got != expected_status:
            mismatches.append(f"{item}:{got}!={expected_status}")
    return [
        row(
            "S42-STAGE44-EXTERNAL-REPROBE",
            "external_unlock",
            pass_fail(not mismatches),
            STAGE44_REPROBE.relative_to(ROOT).as_posix(),
            "external full-text/native-perf unlocks remain unavailable and recorded"
            if not mismatches
            else "; ".join(mismatches),
            "Rerun Stage 44 or update claim status if external unlock evidence becomes available.",
        )
    ]


def check_stage45_active_state() -> List[Dict[str, str]]:
    rows = {r.get("check"): r for r in read_csv(STAGE45_ACTIVE_STATE)}
    expected = {
        "ffnt_active_state_kernel_gate": "PASS",
        "spqlios_avx512_windows_build": "BLOCKED_WINDOWS_ASSEMBLER",
    }
    mismatches = []
    for check, expected_status in expected.items():
        got = rows.get(check, {}).get("status", "MISSING")
        if got != expected_status:
            mismatches.append(f"{check}:{got}!={expected_status}")
    return [
        row(
            "S42-STAGE45-ACTIVE-STATE",
            "current_smoke",
            pass_fail(not mismatches),
            STAGE45_ACTIVE_STATE.relative_to(ROOT).as_posix(),
            "active-state refactor correctness passed and Windows AVX512 platform block is recorded"
            if not mismatches
            else "; ".join(mismatches),
            "Rerun or repair Stage 45 active-state refactor evidence before relying on the post-closure code state.",
        )
    ]


def check_stage46_wsl_target() -> List[Dict[str, str]]:
    rows = {r.get("check"): r for r in read_csv(STAGE46_WSL_TARGET)}
    status = rows.get("wsl_spqlios_avx512_target_gate", {}).get("status", "MISSING")
    return [
        row(
            "S42-STAGE46-WSL-TARGET",
            "current_smoke",
            pass_fail(status == "PASS"),
            STAGE46_WSL_TARGET.relative_to(ROOT).as_posix(),
            "WSL spqlios_avx512 target full bootstrap gate passes after active-state refactor"
            if status == "PASS"
            else f"wsl_spqlios_avx512_target_gate:{status}!=PASS",
            "Rerun or repair Stage 46 WSL target smoke before relying on current-head target correctness.",
        )
    ]


def check_stage47_wsl_full_sab() -> List[Dict[str, str]]:
    rows = {r.get("r"): r for r in read_csv(STAGE47_WSL_FULL_SAB)}
    problems = []
    for r_value in ["2", "4"]:
        row_data = rows.get(r_value)
        if not row_data:
            problems.append(f"r={r_value}:missing")
            continue
        if row_data.get("status") != "PASS":
            problems.append(f"r={r_value}:status={row_data.get('status')}")
        try:
            speedup = float(row_data.get("speedup_vs_scalar_repeated", "0"))
        except ValueError:
            speedup = 0.0
        if speedup <= 1.0:
            problems.append(f"r={r_value}:speedup={row_data.get('speedup_vs_scalar_repeated')}")
    return [
        row(
            "S42-STAGE47-WSL-FULL-SAB",
            "current_smoke",
            pass_fail(not problems and bool(rows)),
            STAGE47_WSL_FULL_SAB.relative_to(ROOT).as_posix(),
            "WSL spqlios_avx512 r=2/r=4 full-SAB current-head smoke passes with positive A/B speedup"
            if not problems and rows
            else "; ".join(problems) or "summary missing or empty",
            "Rerun or repair Stage 47 WSL full-SAB smoke before relying on current-head A/B continuity.",
        )
    ]


def check_stage48_wsl_noise() -> List[Dict[str, str]]:
    rows = {r.get("r"): r for r in read_csv(STAGE48_WSL_NOISE)}
    problems = []
    for r_value in ["2", "4"]:
        row_data = rows.get(r_value)
        if not row_data:
            problems.append(f"r={r_value}:missing")
            continue
        if row_data.get("status") != "PASS":
            problems.append(f"r={r_value}:status={row_data.get('status')}")
        for field in ["pvw_failures", "scalar_failures", "pair_failures"]:
            if row_data.get(field) != "0":
                problems.append(f"r={r_value}:{field}={row_data.get(field)}")
    return [
        row(
            "S42-STAGE48-WSL-NOISE",
            "current_smoke",
            pass_fail(not problems and bool(rows)),
            STAGE48_WSL_NOISE.relative_to(ROOT).as_posix(),
            "WSL spqlios_avx512 r=2/r=4 final-output noise smoke passes with zero PVW/scalar/pair failures"
            if not problems and rows
            else "; ".join(problems) or "aggregate missing or empty",
            "Rerun or repair Stage 48 WSL noise smoke before relying on current-head noise continuity.",
        )
    ]


def check_stage49_wsl_repeated_full_sab() -> List[Dict[str, str]]:
    rows = {r.get("r"): r for r in read_csv(STAGE49_WSL_REPEATED_FULL_SAB)}
    problems = []
    for r_value in ["2", "4"]:
        row_data = rows.get(r_value)
        if not row_data:
            problems.append(f"r={r_value}:missing")
            continue
        if row_data.get("status") != "PASS":
            problems.append(f"r={r_value}:status={row_data.get('status')}")
        if row_data.get("runs") != "3":
            problems.append(f"r={r_value}:runs={row_data.get('runs')}")
        try:
            speedup_min = float(row_data.get("speedup_min", "0"))
        except ValueError:
            speedup_min = 0.0
        if speedup_min <= 1.0:
            problems.append(f"r={r_value}:speedup_min={row_data.get('speedup_min')}")
    return [
        row(
            "S42-STAGE49-WSL-REPEATED-FULL-SAB",
            "current_smoke",
            pass_fail(not problems and bool(rows)),
            STAGE49_WSL_REPEATED_FULL_SAB.relative_to(ROOT).as_posix(),
            "WSL spqlios_avx512 r=2/r=4 repeated full-SAB current-head stability passes with speedup_min > 1"
            if not problems and rows
            else "; ".join(problems) or "summary missing or empty",
            "Rerun or repair Stage 49 WSL repeated full-SAB check before relying on current-head stability evidence.",
        )
    ]


def check_stage50_performance_matrix() -> List[Dict[str, str]]:
    rows = read_csv(STAGE50_PERF_MATRIX)
    by_id = {r.get("evidence_id"): r for r in rows}
    problems = []
    required_ids = [
        "stage36_target_perf_r2",
        "stage47_current_head_smoke_r2",
        "stage49_current_head_repeated_r2",
        "stage36_target_perf_r4",
        "stage47_current_head_smoke_r4",
        "stage49_current_head_repeated_r4",
    ]
    for evidence_id in required_ids:
        row_data = by_id.get(evidence_id)
        if not row_data:
            problems.append(f"{evidence_id}:missing")
            continue
        if row_data.get("status") != "PASS":
            problems.append(f"{evidence_id}:status={row_data.get('status')}")
    for evidence_id in ["stage36_target_perf_r2", "stage36_target_perf_r4"]:
        row_data = by_id.get(evidence_id, {})
        try:
            ci95_low = float(row_data.get("ci95_low", "0"))
        except ValueError:
            ci95_low = 0.0
        if ci95_low <= 1.0:
            problems.append(f"{evidence_id}:ci95_low={row_data.get('ci95_low')}")
        if "not novelty/theory/all-parameter" not in row_data.get("claim_policy", ""):
            problems.append(f"{evidence_id}:claim_policy_missing_guardrail")
    for evidence_id in ["stage49_current_head_repeated_r2", "stage49_current_head_repeated_r4"]:
        row_data = by_id.get(evidence_id, {})
        if row_data.get("consistency_with_stage36") != "CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95":
            problems.append(f"{evidence_id}:consistency={row_data.get('consistency_with_stage36')}")
        if row_data.get("stats_sanity_label") != "CURRENT_HEAD_STABILITY_SUPPORTED_NOT_HIGH_STAT_CLAIM":
            problems.append(f"{evidence_id}:stats_label={row_data.get('stats_sanity_label')}")
    return [
        row(
            "S42-STAGE50-PERFORMANCE-MATRIX",
            "claim_scope",
            pass_fail(not problems and bool(rows)),
            STAGE50_PERF_MATRIX.relative_to(ROOT).as_posix(),
            "Stage50 performance evidence matrix preserves high-stat/current-head/smoke claim boundaries"
            if not problems and rows
            else "; ".join(problems) or "matrix missing or empty",
            "Regenerate or repair Stage50 before relying on performance claim-boundary wording.",
        )
    ]


def check_stage51_goal_frontier() -> List[Dict[str, str]]:
    rows = {r.get("frontier_id"): r for r in read_csv(STAGE51_GOAL_FRONTIER)}
    problems = []
    for frontier_id in ["G1", "G2", "G3", "G4", "G5", "G6"]:
        status = rows.get(frontier_id, {}).get("status", "MISSING")
        if not status.startswith("LOCAL"):
            problems.append(f"{frontier_id}:status={status}")
    for frontier_id in ["B1", "B2"]:
        status = rows.get(frontier_id, {}).get("status", "MISSING")
        if "BLOCKED" not in status:
            problems.append(f"{frontier_id}:status={status}")
    b3_status = rows.get("B3", {}).get("status", "MISSING")
    if "BLOCKED" not in b3_status and b3_status != "EXTERNAL_REVIEW_REQUIRED":
        problems.append(f"B3:status={b3_status}")
    g9_status = rows.get("G9", {}).get("status", "MISSING")
    if g9_status not in {
        "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
        "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEW_REQUIRED",
    }:
        problems.append(f"G9:status={g9_status}")
    return [
        row(
            "S42-STAGE51-GOAL-FRONTIER",
            "claim_scope",
            pass_fail(not problems and bool(rows)),
            STAGE51_GOAL_FRONTIER.relative_to(ROOT).as_posix(),
            "Stage51 goal frontier separates local scoped-ready evidence from stronger external blockers"
            if not problems and rows
            else "; ".join(problems) or "frontier missing or empty",
            "Regenerate Stage51 before relying on local-ready versus externally-blocked goal frontier wording.",
        )
    ]


def check_stage52_external_unlock_readiness() -> List[Dict[str, str]]:
    rows = {r.get("unlock_id"): r for r in read_csv(STAGE52_UNLOCK_READINESS)}
    expected = {
        "S52-NATIVE-PERF": {"WAIT_NATIVE_PERF"},
        "S52-FULLTEXT-686": {"WAIT_EXTERNAL_FULLTEXT", "READY_FOR_MANUAL_REVIEW"},
        "S52-NOVELTY-REVIEW": {"WAIT_MANUAL_FULLTEXT_REVIEW"},
        "S52-EXTERNAL-REGISTRATION": {"WAIT_EXTERNAL_ARTIFACTS", "READY_TO_REGISTER"},
        "S52-FINAL-RECHECK": {"WAIT_UNLOCKS", "READY_AFTER_UNLOCKS"},
    }
    problems = []
    for unlock_id, expected_readiness in expected.items():
        row_data = rows.get(unlock_id)
        if not row_data:
            problems.append(f"{unlock_id}:missing")
            continue
        if row_data.get("readiness") not in expected_readiness:
            problems.append(f"{unlock_id}:readiness={row_data.get('readiness')}")
        for field in ["command", "expected_artifacts", "acceptance_gate", "failure_policy"]:
            if not row_data.get(field, "").strip():
                problems.append(f"{unlock_id}:{field}=empty")
    return [
        row(
            "S42-STAGE52-EXTERNAL-UNLOCK-READINESS",
            "external_unlock",
            pass_fail(not problems and bool(rows)),
            STAGE52_UNLOCK_READINESS.relative_to(ROOT).as_posix(),
            "Stage52 external unlock readiness packet records inputs, commands, artifacts, gates, and failure policies"
            if not problems and rows
            else "; ".join(problems) or "readiness packet missing or empty",
            "Regenerate Stage52 before relying on external unlock handoff instructions.",
        )
    ]


def check_stage53_final_recheck_integration() -> List[Dict[str, str]]:
    rows = {r.get("step"): r for r in read_csv(STAGE53_FINAL_RECHECK)}
    problems = []
    required_pass = [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage50_performance_matrix",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
    ]
    for step in required_pass:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{step}:status={status}")
    closure_status = rows.get("stage42_evidence_closure", {}).get("status")
    if closure_status is not None and closure_status != "PASS":
        problems.append(f"stage42_evidence_closure:status={closure_status}")
    final_decision = rows.get("final_decision", {}).get("status")
    if final_decision is not None and final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        problems.append(f"final_decision:status={final_decision}")
    return [
        row(
            "S42-STAGE53-FINAL-RECHECK-INTEGRATION",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            STAGE53_FINAL_RECHECK.relative_to(ROOT).as_posix(),
            "Stage53 final recheck integrates Stage50, Stage51, Stage52, and Stage42 closure"
            if not problems and rows
            else "; ".join(problems) or "final recheck summary missing or empty",
            "Rerun Stage53 final recheck before relying on unified Stage50-52 recheck integration.",
        )
    ]


def check_stage54_default_final_recheck() -> List[Dict[str, str]]:
    rows = {r.get("step"): r for r in read_csv(STAGE54_DEFAULT_FINAL_RECHECK)}
    problems = []
    required_pass = [
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
    ]
    for step in required_pass:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{step}:status={status}")
    final_decision = rows.get("final_decision", {}).get("status")
    if (
        final_decision is not None
        and final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    ):
        problems.append(f"final_decision:status={final_decision}")
    return [
        row(
            "S42-STAGE54-DEFAULT-FINAL-RECHECK",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            STAGE54_DEFAULT_FINAL_RECHECK.relative_to(ROOT).as_posix(),
            "Stage54 default final recheck covers Stage50, Stage51, Stage52, and Stage42 closure"
            if not problems and rows
            else "; ".join(problems) or "default final recheck summary missing or empty",
            "Rerun Stage54 default final recheck before relying on default recheck coverage.",
        )
    ]


def check_stage55_external_paper_probe() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE55_EXTERNAL_PAPER_PROBE)}
    problems = []
    crossref_status = rows.get("crossref_doi_metadata", {}).get("status", "MISSING")
    fulltext_status = rows.get("official_fulltext_pdf_access", {}).get("status", "MISSING")
    decision_status = rows.get("stage55_decision", {}).get("status", "MISSING")

    if crossref_status != "PASS":
        problems.append(f"crossref_doi_metadata:status={crossref_status}")
    if fulltext_status not in {"PASS", "BLOCKED"}:
        problems.append(f"official_fulltext_pdf_access:status={fulltext_status}")
    if decision_status not in {
        "FULLTEXT_AVAILABLE_REVIEW_REQUIRED",
        "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW",
    }:
        problems.append(f"stage55_decision:status={decision_status}")
    if decision_status == "FULLTEXT_AVAILABLE_REVIEW_REQUIRED" and fulltext_status != "PASS":
        problems.append("decision/fulltext mismatch")
    if decision_status == "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW" and fulltext_status != "BLOCKED":
        problems.append("blocked full-text route should keep wait decision")

    return [
        row(
            "S42-STAGE55-EXTERNAL-PAPER-PROBE",
            "external_evidence",
            pass_fail(not problems and bool(rows)),
            STAGE55_EXTERNAL_PAPER_PROBE.relative_to(ROOT).as_posix(),
            "Stage55 records Crossref metadata while preserving the 2025/686 full-text review blocker"
            if not problems and rows
            else "; ".join(problems) or "Stage55 paper probe summary missing or empty",
            "Regenerate Stage55 and preserve theorem-level claim blockers before relying on 2025/686 source state.",
        )
    ]


def check_stage56_final_recheck_stage55() -> List[Dict[str, str]]:
    rows = {r.get("step"): r for r in read_csv(STAGE56_FINAL_RECHECK_STAGE55)}
    problems = []
    required_pass = [
        "stage55_external_paper_probe",
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage42_evidence_closure",
    ]
    for step in required_pass:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{step}:status={status}")
    final_decision = rows.get("final_decision", {}).get("status")
    if (
        final_decision is not None
        and final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    ):
        problems.append(f"final_decision:status={final_decision}")
    skipped_ok = rows.get("stage50_performance_matrix", {}).get("status", "MISSING") == "SKIPPED"
    if not skipped_ok:
        problems.append(
            f"stage50_performance_matrix:status={rows.get('stage50_performance_matrix', {}).get('status', 'MISSING')}"
        )
    return [
        row(
            "S42-STAGE56-FINAL-RECHECK-STAGE55",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            STAGE56_FINAL_RECHECK_STAGE55.relative_to(ROOT).as_posix(),
            "Stage56 final recheck refreshes Stage55 and propagates it through blockers/frontier/unlock/closure"
            if not problems and rows
            else "; ".join(problems) or "Stage56 final recheck summary missing or empty",
            "Rerun Stage56 final recheck before relying on refreshed Stage55 propagation.",
        )
    ]


def check_stage57_scope_label_audit() -> List[Dict[str, str]]:
    rows = {r.get("audit_id"): r for r in read_csv(STAGE57_SCOPE_LABEL_AUDIT)}
    problems = []
    required = [
        "S57-ROADMAP-LATEST-STAGE",
        "S57-STAGE51-G6-LABEL",
        "S57-NO-STALE-CURRENT-LABELS",
        "S57-CURRENT-FILES-MENTION-LATEST",
    ]
    for audit_id in required:
        status = rows.get(audit_id, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{audit_id}:status={status}")
    return [
        row(
            "S42-STAGE57-SCOPE-LABEL-AUDIT",
            "claim_scope",
            pass_fail(not problems and bool(rows)),
            STAGE57_SCOPE_LABEL_AUDIT.relative_to(ROOT).as_posix(),
            "Stage57 confirms current scope labels match the latest Stage19+ closure range"
            if not problems and rows
            else "; ".join(problems) or "Stage57 scope-label audit missing or empty",
            "Regenerate Stage57 before relying on current Stage19+ closure-range wording.",
        )
    ]


def check_stage58_final_recheck_stage57() -> List[Dict[str, str]]:
    rows = {r.get("step"): r for r in read_csv(STAGE58_FINAL_RECHECK_STAGE57)}
    problems = []
    required_pass = [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage42_evidence_closure",
    ]
    for step in required_pass:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{step}:status={status}")
    final_decision = rows.get("final_decision", {}).get("status")
    if (
        final_decision is not None
        and final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    ):
        problems.append(f"final_decision:status={final_decision}")
    skipped_expected = {
        "stage27_citation_probe",
        "stage27_related_work_access_probe",
        "stage28_perf_gate",
        "stage55_external_paper_probe",
        "stage50_performance_matrix",
    }
    for step in skipped_expected:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "SKIPPED":
            problems.append(f"{step}:status={status}")
    return [
        row(
            "S42-STAGE58-FINAL-RECHECK-STAGE57",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            STAGE58_FINAL_RECHECK_STAGE57.relative_to(ROOT).as_posix(),
            "Stage58 final recheck refreshes Stage57 before Stage42 closure"
            if not problems and rows
            else "; ".join(problems) or "Stage58 final recheck summary missing or empty",
            "Rerun Stage58 final recheck before relying on Stage57 final-recheck integration.",
        )
    ]


def check_stage59_completion_route() -> List[Dict[str, str]]:
    rows = {r.get("route_id"): r for r in read_csv(STAGE59_COMPLETION_ROUTE)}
    expected = {
        "S59-R1-SCOPED-ENGINEERING": "LOCAL_READY",
        "S59-R2-CURRENT-HEAD-REFRESH": "READY_LOCAL_REFRESH",
        "S59-R3-NATIVE-PERF": "EXTERNAL_BLOCKED",
        "S59-R4-FULLTEXT-686": "EXTERNAL_REVIEW_REQUIRED",
        "S59-R5-NOVELTY-REVIEW": "EXTERNAL_REVIEW_BLOCKED",
        "S59-R6-OPTIONAL-VARIANTS": "READY_OPTIONAL_LOCAL_TRIAGE",
        "S59-R7-FINAL-PAPER-PACKAGE": "SCOPED_FINAL_PACKAGE_READY_EXTERNAL_REVIEW_REQUIRED",
    }
    problems = []
    for route_id, expected_status in expected.items():
        route = rows.get(route_id)
        if not route:
            problems.append(f"{route_id}:missing")
            continue
        if route.get("status") != expected_status:
            problems.append(f"{route_id}:status={route.get('status')}")
        for field in ["evidence", "gate", "next_action", "claim_effect"]:
            if not route.get(field, "").strip():
                problems.append(f"{route_id}:{field}=empty")
    return [
        row(
            "S42-STAGE59-COMPLETION-ROUTE",
            "roadmap",
            pass_fail(not problems and bool(rows)),
            STAGE59_COMPLETION_ROUTE.relative_to(ROOT).as_posix(),
            "Stage59 completion route separates local refresh lanes from external blocker lanes"
            if not problems and rows
            else "; ".join(problems) or "Stage59 completion-route readiness missing or empty",
            "Regenerate Stage59 before relying on the post-Stage58 route to completion.",
        )
    ]


def check_stage60_final_recheck_stage59() -> List[Dict[str, str]]:
    rows = {r.get("step"): r for r in read_csv(STAGE60_FINAL_RECHECK_STAGE59)}
    problems = []
    required_pass = [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage59_completion_route",
    ]
    for step in required_pass:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{step}:status={status}")
    final_decision = rows.get("final_decision", {}).get("status")
    if (
        final_decision is not None
        and final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    ):
        problems.append(f"final_decision:status={final_decision}")
    closure_status = rows.get("stage42_evidence_closure", {}).get("status")
    if closure_status is not None and closure_status != "PASS":
        problems.append(f"stage42_evidence_closure:status={closure_status}")
    skipped_expected = {
        "stage27_citation_probe",
        "stage27_related_work_access_probe",
        "stage28_perf_gate",
        "stage55_external_paper_probe",
        "stage50_performance_matrix",
    }
    for step in skipped_expected:
        status = rows.get(step, {}).get("status", "MISSING")
        if status != "SKIPPED":
            problems.append(f"{step}:status={status}")
    return [
        row(
            "S42-STAGE60-FINAL-RECHECK-STAGE59",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            STAGE60_FINAL_RECHECK_STAGE59.relative_to(ROOT).as_posix(),
            "Stage60 final recheck refreshes Stage59 before Stage42 closure"
            if not problems and rows
            else "; ".join(problems) or "Stage60 final recheck summary missing or empty",
            "Rerun Stage60 final recheck before relying on Stage59 final-recheck integration.",
        )
    ]


def check_stage61_native_perf_unlock() -> List[Dict[str, str]]:
    rows = {r.get("probe"): r for r in read_csv(STAGE61_NATIVE_PERF_UNLOCK)}
    problems = []
    environment_status = rows.get("environment", {}).get("status", "MISSING")
    hardware_status = rows.get("hardware_counter_gate", {}).get("status", "MISSING")
    perf_status = rows.get("perf_command", {}).get("status", "MISSING")
    bench_status = rows.get("bench_correctness", {}).get("status")

    if environment_status != "RECORDED":
        problems.append(f"environment:status={environment_status}")
    if hardware_status not in {"PASS", "BLOCKED", "READY_FOR_BENCH"}:
        problems.append(f"hardware_counter_gate:status={hardware_status}")
    if hardware_status == "PASS" and bench_status != "PASS":
        problems.append(f"bench_correctness:status={bench_status}")
    if hardware_status == "BLOCKED" and perf_status not in {"MISSING", "AVAILABLE"}:
        problems.append(f"perf_command:status={perf_status}")

    detail = (
        "Stage61 native perf unlock probe is recorded; current platform remains blocked"
        if hardware_status == "BLOCKED"
        else "Stage61 native perf unlock probe is recorded and hardware counters are available"
        if hardware_status in {"PASS", "READY_FOR_BENCH"}
        else "; ".join(problems) or "Stage61 native perf unlock summary missing or empty"
    )
    return [
        row(
            "S42-STAGE61-NATIVE-PERF-UNLOCK",
            "external_unlock",
            pass_fail(not problems and bool(rows)),
            STAGE61_NATIVE_PERF_UNLOCK.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage61 on native Linux or perf-enabled WSL before changing MAT-AVX512 theory claims.",
        )
    ]


def check_stage62_fulltext_unlock() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE62_FULLTEXT_UNLOCK)}
    problems = []
    decision = rows.get("stage62_decision", {}).get("status", "MISSING")
    stage38_decision = rows.get("stage38_decision", {}).get("status", "MISSING")
    artifact_status = rows.get("stage38_fulltext_artifact", {}).get("status", "MISSING")
    external_status = rows.get("external_fulltext_intake", {}).get("status", "MISSING")
    checklist_status = rows.get("stage38_review_checklist", {}).get("status", "MISSING")

    if decision not in {
        "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW",
        "FULLTEXT_AVAILABLE_REVIEW_REQUIRED",
    }:
        problems.append(f"stage62_decision:status={decision}")
    if decision == "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW":
        if stage38_decision != "BLOCKED_FULLTEXT_MISSING":
            problems.append(f"stage38_decision:status={stage38_decision}")
        if artifact_status != "MISSING":
            problems.append(f"stage38_fulltext_artifact:status={artifact_status}")
        if external_status != "MISSING":
            problems.append(f"external_fulltext_intake:status={external_status}")
        if "BLOCKED_FULLTEXT_MISSING" not in checklist_status:
            problems.append(f"stage38_review_checklist:status={checklist_status}")
    if decision == "FULLTEXT_AVAILABLE_REVIEW_REQUIRED":
        if artifact_status != "AVAILABLE_UNREVIEWED":
            problems.append(f"stage38_fulltext_artifact:status={artifact_status}")
        if external_status not in {"AVAILABLE_UNREVIEWED", "MISSING"}:
            problems.append(f"external_fulltext_intake:status={external_status}")

    detail = (
        "Stage62 full-text unlock probe is recorded; current environment still needs a full-text artifact"
        if decision == "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW"
        else "Stage62 full-text artifact is available; manual review is required"
        if decision == "FULLTEXT_AVAILABLE_REVIEW_REQUIRED"
        else "; ".join(problems) or "Stage62 full-text unlock summary missing or empty"
    )
    return [
        row(
            "S42-STAGE62-FULLTEXT-UNLOCK",
            "external_unlock",
            pass_fail(not problems and bool(rows)),
            STAGE62_FULLTEXT_UNLOCK.relative_to(ROOT).as_posix(),
            detail,
            "Supply FAB686_FULLTEXT_PATH and rerun Stage62 before theorem-level or novelty claim upgrades.",
        )
    ]


def check_stage65a_r4_unrolled_variant() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE65A_R4_UNROLLED)}
    expected = {
        "stage65_correctness": "PASS",
        "stage65_kernel_dft_output": "NEGATIVE",
        "stage65_kernel_full_output": "NEGATIVE",
        "stage65_full_sab_r4": "NEGATIVE",
        "stage65_instruction_proxy": "RECORDED",
        "stage65_scalar_baseline_smoke": "PASS",
        "stage65_decision": "NEGATIVE_NOT_PROMOTED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")

    detail = (
        "Stage65A r4 row-unrolled AVX512 variant is recorded as negative/not promoted"
        if not problems and rows
        else "; ".join(problems) or "Stage65A summary missing or empty"
    )
    return [
        row(
            "S42-STAGE65A-R4-UNROLLED",
            "optional_variant",
            pass_fail(not problems and bool(rows)),
            STAGE65A_R4_UNROLLED.relative_to(ROOT).as_posix(),
            detail,
            "Keep the variant behind MAT_TRGSW_AVX512_R4_UNROLLED_ROWS and do not promote without new full-SAB evidence.",
        )
    ]


def check_stage64a_post_variant_refresh() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE64A_POST_VARIANT_REFRESH)}
    expected = {
        "stage64_current_smoke": "PASS",
        "stage64_full_sab_r2": "PASS",
        "stage64_full_sab_r4": "PASS",
        "stage64_final_noise": "PASS",
        "stage64_stage50_matrix": "PASS",
        "stage64_decision": "PASS_POST_VARIANT_REFRESH",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")

    detail = (
        "Stage64A post-variant refresh passed for smoke, repeated full-SAB, noise, and Stage50"
        if not problems and rows
        else "; ".join(problems) or "Stage64A summary missing or empty"
    )
    return [
        row(
            "S42-STAGE64A-POST-VARIANT-REFRESH",
            "current_smoke",
            pass_fail(not problems and bool(rows)),
            STAGE64A_POST_VARIANT_REFRESH.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage64A after future implementation changes before relying on current-head continuity.",
        )
    ]


def check_stage66a_post_variant_final_recheck() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE66A_POST_VARIANT_FINAL_RECHECK)}
    expected = {
        "stage66_final_recheck_core": "PASS",
        "stage66_stage64a_continuity": "PASS",
        "stage66_stage65a_negative_variant": "PASS",
        "stage66_decision": "PASS_POST_VARIANT_FINAL_RECHECK",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")

    detail = (
        "Stage66A post-variant final-recheck control plane passed and preserves stronger blockers"
        if not problems and rows
        else "; ".join(problems) or "Stage66A summary missing or empty"
    )
    return [
        row(
            "S42-STAGE66A-POST-VARIANT-FINAL-RECHECK",
            "final_recheck",
            pass_fail(not problems and bool(rows)),
            STAGE66A_POST_VARIANT_FINAL_RECHECK.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage66A after future post-variant refreshes before relying on final-recheck continuity.",
        )
    ]


def check_stage67_final_recheck_stage66() -> List[Dict[str, str]]:
    summary = {r.get("step"): r for r in read_csv(STAGE67_FINAL_RECHECK_STAGE66)}
    decision_rows = {r.get("gate"): r for r in read_csv(STAGE67_FINAL_RECHECK_STAGE66_DECISION)}
    expected_summary = {
        "stage66_post_variant_final_recheck": "PASS",
        "stage42_evidence_closure": "SKIPPED",
        "final_decision": "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
    }
    expected_decision = {
        "stage67_final_recheck_stage66": "PASS",
        "stage67_stage66_summary": "PASS",
        "stage67_decision": "PASS_FINAL_RECHECK_STAGE66_INTEGRATION",
    }
    problems = []
    for step, status in expected_summary.items():
        actual = summary.get(step, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{step}:status={actual}")
    for gate, status in expected_decision.items():
        actual = decision_rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")

    detail = (
        "Stage67 final recheck runs Stage66A and then Stage42 closure is rebuilt after the finalized summary"
        if not problems and summary and decision_rows
        else "; ".join(problems) or "Stage67 summary or decision missing"
    )
    return [
        row(
            "S42-STAGE67-FINAL-RECHECK-STAGE66",
            "final_recheck",
            pass_fail(not problems and bool(summary) and bool(decision_rows)),
            (
                f"{STAGE67_FINAL_RECHECK_STAGE66.relative_to(ROOT).as_posix()}; "
                f"{STAGE67_FINAL_RECHECK_STAGE66_DECISION.relative_to(ROOT).as_posix()}"
            ),
            detail,
            "Rerun Stage67 before relying on unified final-recheck coverage for Stage66A.",
        )
    ]


def check_stage68_frontier_closure_consistency() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE68_FRONTIER_CLOSURE_CONSISTENCY)}
    expected = {
        "stage68_stage42_label": "PASS",
        "stage68_stage51_g6": "PASS",
        "stage68_stage57_scope_label": "PASS",
        "stage68_stage59_route": "PASS",
        "stage68_decision": "PASS_FRONTIER_CLOSURE_CONSISTENCY",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")

    detail = (
        "Stage68 confirms Stage42, Stage51 G6, Stage57, and Stage59 labels are consistent for the latest control stage"
        if not problems and rows
        else "; ".join(problems) or "Stage68 summary missing or empty"
    )
    return [
        row(
            "S42-STAGE68-FRONTIER-CLOSURE-CONSISTENCY",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            STAGE68_FRONTIER_CLOSURE_CONSISTENCY.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage68 after changing Stage42, Stage51, Stage57, Stage59, or roadmap labels.",
        )
    ]


def check_stage69_local_variant_feasibility() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE69_LOCAL_VARIANT_FEASIBILITY)}
    expected = {
        "stage69_inputs_available": "PASS",
        "stage69_h2_postproc_tail": "DEFER_TAIL_SMALL",
        "stage69_h3_sparse_selector_theory": "REJECT_CURRENT_SPARSE_SELECTOR_SHORTCUT",
        "stage69_h4_schedule_fusion": "NEUTRAL_NOT_PROMOTED",
        "stage69_h7_avx512_layout": "BLOCKED_NATIVE_COUNTERS_OR_NEGATIVE_PRIOR",
        "stage69_h8_nonbinary_branch": "BLOCKED_FULLTEXT_NONBINARY_DESIGN",
        "stage69_no_unblocked_local_variant": "PASS_NO_UNBLOCKED_LOCAL_VARIANT",
        "stage69_decision": "PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")

    detail = (
        "Stage69 records no unblocked local variant; H3 sparse-selector shortcut is rejected under current encrypted-selector/key-format evidence"
        if not problems and rows
        else "; ".join(problems) or "Stage69 summary missing or empty"
    )
    return [
        row(
            "S42-STAGE69-LOCAL-VARIANT-FEASIBILITY",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            STAGE69_LOCAL_VARIANT_FEASIBILITY.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage69 before selecting a new local implementation variant.",
        )
    ]


def check_stage70_external_unlock_preflight() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE70_EXTERNAL_UNLOCK_PREFLIGHT)}
    expected = {
        "stage70_route_inputs": "PASS",
        "stage70_native_perf_preflight": "WAIT_NATIVE_PERF",
        "stage70_fulltext_stage62_preflight": "WAIT_FULLTEXT_ARTIFACT",
        "stage70_novelty_preflight": "WAIT_FULLTEXT_OR_MANUAL_REVIEW",
        "stage70_local_variant_preflight": "NO_LOCAL_VARIANT_READY",
        "stage70_decision": "PASS_EXTERNAL_UNLOCK_PREFLIGHT_STRONGER_CLAIMS_BLOCKED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    fulltext_env = rows.get("stage70_fulltext_env_preflight", {}).get(
        "status", "MISSING"
    )
    if fulltext_env not in {
        "MISSING_ENV",
        "PATH_NOT_FOUND",
        "INVALID_FILE",
        "AVAILABLE_UNREVIEWED",
    }:
        problems.append(f"stage70_fulltext_env_preflight:status={fulltext_env}")

    detail = (
        "Stage70 records external unlock prerequisites; stronger claims remain blocked until native perf/full-text/novelty gates are satisfied"
        if not problems and rows
        else "; ".join(problems) or "Stage70 summary missing or empty"
    )
    return [
        row(
            "S42-STAGE70-EXTERNAL-UNLOCK-PREFLIGHT",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            STAGE70_EXTERNAL_UNLOCK_PREFLIGHT.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage70 before relying on external-unlock readiness.",
        )
    ]


def check_stage71_final_recheck_stage70() -> List[Dict[str, str]]:
    summary = {r.get("step"): r for r in read_csv(STAGE71_FINAL_RECHECK_STAGE70)}
    decision_rows = {
        r.get("gate"): r for r in read_csv(STAGE71_FINAL_RECHECK_STAGE70_DECISION)
    }
    problems = []
    required_pass = [
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage59_completion_route",
        "stage70_external_unlock_preflight",
        "stage42_evidence_closure",
    ]
    for step in required_pass:
        status = summary.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{step}:status={status}")
    final_decision = summary.get("final_decision", {}).get("status", "MISSING")
    if final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        problems.append(f"final_decision:status={final_decision}")
    expected_decision = {
        "stage71_final_recheck_stage70": "PASS",
        "stage71_stage70_summary": "PASS",
        "stage71_decision": "PASS_FINAL_RECHECK_STAGE70_INTEGRATION",
    }
    for gate, status in expected_decision.items():
        actual = decision_rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")

    detail = (
        "Stage71 final recheck refreshes Stage70 and Stage42 closure while preserving stronger-claim blockers"
        if not problems and summary and decision_rows
        else "; ".join(problems) or "Stage71 summary or decision missing"
    )
    return [
        row(
            "S42-STAGE71-FINAL-RECHECK-STAGE70",
            "final_recheck",
            pass_fail(not problems and bool(summary) and bool(decision_rows)),
            (
                f"{STAGE71_FINAL_RECHECK_STAGE70.relative_to(ROOT).as_posix()}; "
                f"{STAGE71_FINAL_RECHECK_STAGE70_DECISION.relative_to(ROOT).as_posix()}"
            ),
            detail,
            "Rerun Stage71 before relying on unified final-recheck coverage for Stage70.",
        )
    ]


def check_stage72_external_source_refresh() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE72_EXTERNAL_SOURCE_REFRESH)}
    expected = {
        "stage72_author_metadata_route": "PASS",
        "stage72_doi_metadata_route": "PASS",
        "stage72_code_route": "PASS",
        "stage72_official_fulltext_routes": "WAIT_FULLTEXT_ARTIFACT",
        "stage72_claim_policy": "KEEP_STRONGER_CLAIMS_BLOCKED",
        "stage72_decision": "PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage72 refreshes author/DOI/code source routes while preserving full-text and stronger-claim blockers"
        if not problems and rows
        else "; ".join(problems) or "Stage72 summary missing"
    )
    return [
        row(
            "S42-STAGE72-EXTERNAL-SOURCE-REFRESH",
            "external_evidence",
            pass_fail(not problems and bool(rows)),
            STAGE72_EXTERNAL_SOURCE_REFRESH.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage72 before relying on current external source availability.",
        )
    ]


def check_stage73_final_recheck_stage72() -> List[Dict[str, str]]:
    summary = {r.get("step"): r for r in read_csv(STAGE73_FINAL_RECHECK_STAGE72)}
    decision_rows = {
        r.get("gate"): r for r in read_csv(STAGE73_FINAL_RECHECK_STAGE72_DECISION)
    }
    problems = []
    required_pass = [
        "stage72_external_source_refresh",
        "final_goal_audit",
        "remaining_blocker_dashboard",
        "stage51_goal_frontier",
        "stage52_external_unlock_readiness",
        "stage57_scope_label_audit",
        "stage59_completion_route",
        "stage70_external_unlock_preflight",
        "stage42_evidence_closure",
    ]
    required_skipped = [
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
    ]
    for step in required_pass:
        status = summary.get(step, {}).get("status", "MISSING")
        if status != "PASS":
            problems.append(f"{step}:status={status}")
    for step in required_skipped:
        status = summary.get(step, {}).get("status", "MISSING")
        if status != "SKIPPED":
            problems.append(f"{step}:status={status}")
    final_decision = summary.get("final_decision", {}).get("status", "MISSING")
    if final_decision != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        problems.append(f"final_decision:status={final_decision}")
    expected_decision = {
        "stage73_final_recheck_stage72": "PASS",
        "stage73_stage72_summary": "PASS",
        "stage73_decision": "PASS_FINAL_RECHECK_STAGE72_INTEGRATION",
    }
    for gate, status in expected_decision.items():
        actual = decision_rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")

    detail = (
        "Stage73 final recheck refreshes Stage72 before blocker/frontier/closure rebuilds while preserving stronger-claim blockers"
        if not problems and summary and decision_rows
        else "; ".join(problems) or "Stage73 summary or decision missing"
    )
    return [
        row(
            "S42-STAGE73-FINAL-RECHECK-STAGE72",
            "final_recheck",
            pass_fail(not problems and bool(summary) and bool(decision_rows)),
            (
                f"{STAGE73_FINAL_RECHECK_STAGE72.relative_to(ROOT).as_posix()}; "
                f"{STAGE73_FINAL_RECHECK_STAGE72_DECISION.relative_to(ROOT).as_posix()}"
            ),
            detail,
            "Rerun Stage73 before relying on unified final-recheck coverage for Stage72.",
        )
    ]


def check_stage74_r_scaling_boundary() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE74_R_SCALING_BOUNDARY)}
    expected = {
        "stage74_r6_full_sab_smoke": "PASS",
        "stage74_r8_full_sab_smoke": "PASS",
        "stage74_rgt4_boundary": "NOT_PROMOTED_R_GT4_BELOW_R4_SCREEN",
        "stage74_decision": "PASS_R_GT4_BOUNDARY_RECORDED_NOT_PROMOTED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage74 records r=6/r=8 complete-SAB smoke and rejects direct r>4 promotion under current evidence"
        if not problems and rows
        else "; ".join(problems) or "Stage74 decision missing"
    )
    return [
        row(
            "S42-STAGE74-R-SCALING-BOUNDARY",
            "variant_boundary",
            pass_fail(not problems and bool(rows)),
            STAGE74_R_SCALING_BOUNDARY.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage74 before relying on the direct r>4 scaling boundary.",
        )
    ]


def check_stage75_rgt4_profile_boundary() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE75_RGT4_PROFILE_BOUNDARY)}
    expected = {
        "stage75_r6_body_profile": "PASS",
        "stage75_r8_body_profile": "PASS",
        "stage75_schedule_count_invariant": "PASS",
        "stage75_rgt4_profile_boundary": "NOT_PROMOTED_PROFILE_BOUNDARY",
        "stage75_decision": "PASS_RGT4_PROFILE_BOUNDARY_RECORDED_NOT_PROMOTED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage75 profiles r=6/r=8 and attributes the r>4 boundary to per-update MAT/body cost under invariant SAB counts"
        if not problems and rows
        else "; ".join(problems) or "Stage75 decision missing"
    )
    return [
        row(
            "S42-STAGE75-RGT4-PROFILE-BOUNDARY",
            "variant_boundary",
            pass_fail(not problems and bool(rows)),
            STAGE75_RGT4_PROFILE_BOUNDARY.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage75 before relying on the profile-backed r>4 scaling boundary.",
        )
    ]


def check_stage76_rgt4_kernel_feasibility() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE76_RGT4_KERNEL_FEASIBILITY)}
    expected = {
        "stage76_rgt4_kernel_correctness": "PASS",
        "stage76_r6_dft_output_kernel": "NEGATIVE_DFT_OUTPUT_NOT_PROMOTED",
        "stage76_r6_full_output_kernel": "SMOKE_POSITIVE_FULL_OUTPUT",
        "stage76_r8_dft_output_kernel": "NEGATIVE_DFT_OUTPUT_NOT_PROMOTED",
        "stage76_r8_full_output_kernel": "SMOKE_POSITIVE_LOW_MARGIN_FULL_OUTPUT",
        "stage76_mul_share_boundary": "PASS",
        "stage76_decision": "PASS_RGT4_KERNEL_FEASIBILITY_RECORDED_NO_PROMOTION",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage76 records correct r=6/r=8 generic MAT kernel behavior but rejects direct r>4 promotion; future work is H11 fused MAT multiply/layout"
        if not problems and rows
        else "; ".join(problems) or "Stage76 decision missing"
    )
    return [
        row(
            "S42-STAGE76-RGT4-KERNEL-FEASIBILITY",
            "variant_boundary",
            pass_fail(not problems and bool(rows)),
            STAGE76_RGT4_KERNEL_FEASIBILITY.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage76 before relying on the r>4 kernel feasibility boundary.",
        )
    ]


def check_stage77_rgt4_fused_mat_kernel() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE77_RGT4_FUSED_MAT_KERNEL)}
    expected = {
        "stage77_generic_kernel_correctness": "PASS",
        "stage77_fused_kernel_correctness": "PASS",
        "stage77_kernel_fused_vs_generic": "PASS",
        "stage77_fused_dft_vs_scalar": "PARTIAL_R6_ONLY",
        "stage77_full_sab_smoke": "PASS",
        "stage77_r4_boundary": "REPEATED_GATES_REQUIRED",
        "stage77_decision": "PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage77 records H11 fused r>4 MAT as a positive smoke candidate and requires repeated full-SAB/noise/resource gates before promotion"
        if not problems and rows
        else "; ".join(problems) or "Stage77 decision missing"
    )
    return [
        row(
            "S42-STAGE77-RGT4-FUSED-MAT-KERNEL",
            "variant_smoke",
            pass_fail(not problems and bool(rows)),
            STAGE77_RGT4_FUSED_MAT_KERNEL.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage77 before relying on the H11 fused r>4 MAT smoke result.",
        )
    ]


def check_stage78_rgt4_fused_repeated_gates() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE78_RGT4_FUSED_REPEATED_GATES)}
    expected = {
        "stage78_stage77_precondition": "PASS",
        "stage78_r6_repeated_full_sab": "PASS",
        "stage78_r8_stress_full_sab": "PASS",
        "stage78_r6_noise": "PASS",
        "stage78_r8_noise": "PASS",
        "stage78_resource": "PASS",
        "stage78_decision": "PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage78 records H11 r=6 fused r>4 MAT as a promotion candidate after repeated full-SAB/noise/resource gates; Stage79 high-stat confirmation remains required"
        if not problems and rows
        else "; ".join(problems) or "Stage78 decision missing"
    )
    return [
        row(
            "S42-STAGE78-RGT4-FUSED-REPEATED-GATES",
            "variant_repeated_gate",
            pass_fail(not problems and bool(rows)),
            STAGE78_RGT4_FUSED_REPEATED_GATES.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage78 before relying on the H11 fused r>4 MAT promotion-candidate result.",
        )
    ]


def check_stage79_rgt4_fused_high_stat() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE79_RGT4_FUSED_HIGH_STAT)}
    expected = {
        "stage79_stage78_precondition": "PASS",
        "stage79_r6_high_stat_full_sab": "PASS_R4_REGION_NOT_CONFIRMED",
        "stage79_r6_final_noise": "PASS",
        "stage79_r6_resource": "PASS",
        "stage79_decision": "PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage79 records r=6 fused MAT high-stat evidence: full-SAB/noise/resource pass, but performance does not strongly confirm promotion over the r=4 reference; Stage80 review/rejection audit is required"
        if not problems and rows
        else "; ".join(problems) or "Stage79 decision missing"
    )
    return [
        row(
            "S42-STAGE79-RGT4-FUSED-HIGH-STAT",
            "variant_high_stat_gate",
            pass_fail(not problems and bool(rows)),
            STAGE79_RGT4_FUSED_HIGH_STAT.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage79 before relying on the H11 fused r>4 MAT high-stat review result.",
        )
    ]


def check_stage80_promotion_policy_audit() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE80_PROMOTION_POLICY_AUDIT)}
    expected = {
        "stage80_stage79_precondition": "PASS",
        "stage80_performance_policy": "KEEP_EXPERIMENTAL_NOT_PROMOTED",
        "stage80_noise_resource_guard": "PASS",
        "stage80_default_path_guard": "PASS",
        "stage80_current_head_smoke": "PASS",
        "stage80_decision": "PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage80 keeps H11 r=6 fused MAT as an explicit experimental flag only; it is not promoted and scalar/default paths remain smoke-tested"
        if not problems and rows
        else "; ".join(problems) or "Stage80 decision missing"
    )
    return [
        row(
            "S42-STAGE80-PROMOTION-POLICY-AUDIT",
            "variant_policy",
            pass_fail(not problems and bool(rows)),
            STAGE80_PROMOTION_POLICY_AUDIT.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage80 before relying on the H11 r=6 fused keep/reject policy decision.",
        )
    ]


def check_stage81_next_variant_triage() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE81_NEXT_VARIANT_TRIAGE)}
    expected = {
        "stage81_inputs_available": "PASS",
        "stage81_h11_policy_state": "KEEP_EXPERIMENTAL_NOT_PROMOTED",
        "stage81_sparse_structured_mat_candidate": "BLOCKED_SECURITY_DESIGN_GAP",
        "stage81_rgt4_lane_or_tiling_candidate": "NOT_SELECTED_R6_EXPERIMENTAL_R8_WEAK",
        "stage81_postprocessing_candidate": "DEFER_TAIL_SMALL",
        "stage81_schedule_body_candidate": "SELECT_PROFILE_FIRST",
        "stage81_decision": "PASS_STAGE81_NEXT_VARIANT_TRIAGE_PROFILE_FIRST_NO_CODE_PROMOTION",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage81 selects post-H11 fused r=6 profile attribution as the next local step and does not promote new hot-path code"
        if not problems and rows
        else "; ".join(problems) or "Stage81 triage missing"
    )
    return [
        row(
            "S42-STAGE81-NEXT-VARIANT-TRIAGE",
            "variant_policy",
            pass_fail(not problems and bool(rows)),
            STAGE81_NEXT_VARIANT_TRIAGE.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage81 before choosing or implementing another local SAB/MAT optimization.",
        )
    ]


def check_stage82_post_h11_profile() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE82_POST_H11_PROFILE)}
    expected = {
        "stage82_inputs_available": "PASS",
        "stage82_fused_r6_profile_counts": "PASS",
        "stage82_fused_vs_generic_profile": "PROFILE_ONLY_RECORDED",
        "stage82_component_attribution": "MAT_BODY_REMAINS_PRIMARY",
        "stage82_decision": "PASS_STAGE82_POST_H11_PROFILE_MAT_BODY_PRIMARY",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage82 profiles explicit H11 fused r=6 and records MAT body as the primary profile target without promoting new code"
        if not problems and rows
        else "; ".join(problems) or "Stage82 profile missing"
    )
    return [
        row(
            "S42-STAGE82-POST-H11-PROFILE",
            "profile_attribution",
            pass_fail(not problems and bool(rows)),
            STAGE82_POST_H11_PROFILE.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage82 before opening another local SAB/MAT implementation hypothesis.",
        )
    ]


def check_stage83_mat_body_design_check() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE83_MAT_BODY_DESIGN_CHECK)}
    expected = {
        "stage83_inputs_available": "PASS",
        "stage83_profile_bound": "PASS_MAT_BODY_PRIMARY_BUT_NOT_EXCLUSIVE",
        "stage83_amdahl_bound": "PASS_RECORDED",
        "stage83_security_boundary": "PASS_BLOCK_SPARSE_SKIP_WITHOUT_KEY_SECURITY_DESIGN",
        "stage83_candidate_screen": "SELECT_STAGE84_R6_TILE_SWEEP_PREFLIGHT",
        "stage83_decision": "PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage83 screens H13 MAT body candidates and selects explicit r=6 tile-sweep preflight without promoting code"
        if not problems and rows
        else "; ".join(problems) or "Stage83 design check missing"
    )
    return [
        row(
            "S42-STAGE83-MAT-BODY-DESIGN-CHECK",
            "design_gate",
            pass_fail(not problems and bool(rows)),
            STAGE83_MAT_BODY_DESIGN_CHECK.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage83 before implementing Stage84 H13 preflight.",
        )
    ]


def check_stage84_h13_r6_tile_sweep_preflight() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE84_H13_R6_TILE_SWEEP)}
    expected = {
        "stage84_inputs_available": "PASS",
        "stage84_kernel_correctness": "PASS",
        "stage84_r6_kernel_comparison": "PASS_KERNEL_POSITIVE",
        "stage84_r8_guard": "RECORDED_DIAGNOSTIC",
        "stage84_full_sab_smoke": "NEUTRAL_OR_NEGATIVE_FULL_SAB",
        "stage84_decision": "PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage84 records H13 r=6 tile-sweep as kernel-positive but complete-SAB neutral/negative, so it is not promoted"
        if not problems and rows
        else "; ".join(problems) or "Stage84 preflight missing"
    )
    return [
        row(
            "S42-STAGE84-H13-R6-TILE-SWEEP",
            "preflight_gate",
            pass_fail(not problems and bool(rows)),
            STAGE84_H13_R6_TILE_SWEEP.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage84 before relying on H13 r=6 tile-sweep routing or opening Stage85.",
        )
    ]


def check_stage86_secondary_cmux_materialization() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE86_SECONDARY_CMUX_MATERIALIZATION)}
    expected = {
        "stage86_inputs_available": "PASS",
        "stage86_non_mat_materiality": "PASS_NON_MAT_MATERIAL",
        "stage86_prior_neutral_guard": "PASS_DIFFERENT_LAYER_REQUIRED",
        "stage86_candidate_screen": "SELECT_BACKEND_FROM_DFT_ADD_CALLBACK_PREFLIGHT",
        "stage86_security_boundary": "PASS_NO_KEY_FORMAT_CHANGE",
        "stage86_decision": "PASS_STAGE86_SECONDARY_CMUX_MATERIALIZATION_SELECT_BACKEND_PREFLIGHT",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage86 selects H14 backend FromDFT+add materialization preflight without promoting code"
        if not problems and rows
        else "; ".join(problems) or "Stage86 materialization decision missing"
    )
    return [
        row(
            "S42-STAGE86-SECONDARY-CMUX-MATERIALIZATION",
            "design_gate",
            pass_fail(not problems and bool(rows)),
            STAGE86_SECONDARY_CMUX_MATERIALIZATION.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage86 before implementing the backend materialization preflight.",
        )
    ]


def check_stage87_h14_backend_from_dft_add_preflight() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE87_H14_BACKEND_FROM_DFT_ADD)}
    expected = {
        "stage87_explicit_flag": "PASS_EXPLICIT_FLAG",
        "stage87_correctness_smoke": "PASS",
        "stage87_full_sab_smoke": "PASS_FULL_SAB_POSITIVE",
        "stage87_decision": "PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage87 records H14 backend FromDFT-add as a one-run promotion candidate without promoting code"
        if not problems and rows
        else "; ".join(problems) or "Stage87 backend FromDFT-add preflight missing"
    )
    return [
        row(
            "S42-STAGE87-H14-BACKEND-FROM-DFT-ADD",
            "implementation_preflight",
            pass_fail(not problems and bool(rows)),
            STAGE87_H14_BACKEND_FROM_DFT_ADD.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage87 before opening Stage88 repeated/noise/resource gates.",
        )
    ]


def check_stage88_h14_backend_repeated_gates() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE88_H14_BACKEND_REPEATED_GATES)}
    expected = {
        "stage88_stage87_precondition": "PASS",
        "stage88_repeated_full_sab": "PASS_BACKEND_FASTER",
        "stage88_backend_vs_scalar": "PASS",
        "stage88_wrapper_reference": "PASS",
        "stage88_final_noise": "PASS",
        "stage88_resource": "PASS",
        "stage88_decision": "PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage88 records H14 backend FromDFT-add as a repeated/noise/resource promotion candidate without promoting defaults"
        if not problems and rows
        else "; ".join(problems) or "Stage88 H14 backend repeated gate missing"
    )
    return [
        row(
            "S42-STAGE88-H14-BACKEND-REPEATED-GATES",
            "repeated_gate",
            pass_fail(not problems and bool(rows)),
            STAGE88_H14_BACKEND_REPEATED_GATES.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage88 before opening Stage89 promotion-policy integration.",
        )
    ]


def check_stage89_h14_promotion_policy() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE89_H14_PROMOTION_POLICY)}
    expected = {
        "stage89_stage88_precondition": "PASS",
        "stage89_current_head_smoke": "PASS",
        "stage89_default_path_guard": "PASS",
        "stage89_stage80_policy_precedent": "PASS",
        "stage89_performance_policy": "PROMOTE_EXPLICIT_PATH_NOT_DEFAULT",
        "stage89_noise_resource_guard": "PASS",
        "stage89_claim_guard": "PASS",
        "stage89_decision": "PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage89 promotes H14 backend FromDFT-add as the preferred explicit r=6 path while defaults remain unchanged"
        if not problems and rows
        else "; ".join(problems) or "Stage89 H14 promotion policy missing"
    )
    return [
        row(
            "S42-STAGE89-H14-PROMOTION-POLICY",
            "promotion_policy",
            pass_fail(not problems and bool(rows)),
            STAGE89_H14_PROMOTION_POLICY.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage89 before treating H14 backend as the preferred explicit r=6 path.",
        )
    ]


def check_stage90_external_claim_unlock() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE90_EXTERNAL_CLAIM_UNLOCK)}
    expected = {
        "stage90_stage89_precondition": "PASS",
        "stage90_citation_fulltext_probe": "PASS_PROBE_RECORDED_WAIT_FULLTEXT",
        "stage90_native_perf_unlock": "WAIT_NATIVE_PERF",
        "stage90_source_refresh_context": "PASS_METADATA_CODE_CONTEXT",
        "stage90_fulltext_unlock": "WAIT_FULLTEXT_ARTIFACT",
        "stage90_novelty_review_unlock": "WAIT_FULLTEXT_OR_MANUAL_REVIEW",
        "stage90_blocker_dashboard_guard": "PASS_BLOCKERS_REGISTERED",
        "stage90_decision": "PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage90 external claim probe is recorded and keeps native-perf, full-text, and novelty claims blocked"
        if not problems and rows
        else "; ".join(problems) or "Stage90 external claim unlock summary missing"
    )
    return [
        row(
            "S42-STAGE90-EXTERNAL-CLAIM-UNLOCK",
            "claim_scope",
            pass_fail(not problems and bool(rows)),
            STAGE90_EXTERNAL_CLAIM_UNLOCK.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage90 before Stage91 final package if external evidence or claim scope changes.",
        )
    ]


def check_stage91_final_package() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE91_FINAL_PACKAGE)}
    expected = {
        "stage91_smoke_current_code_guard": "PASS_CURRENT_SMOKE_INHERITED_SOURCE_UNCHANGED",
        "stage91_performance_gate": "PASS_SCOPED_COMPLETE_SAB_PERFORMANCE",
        "stage91_noise_resource_gate": "PASS_SCOPED_NOISE_RESOURCE",
        "stage91_stage89_policy_gate": "PASS_EXPLICIT_R6_POLICY_RECORDED",
        "stage91_external_claim_gate": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage91_existing_closure_gate": "PASS_PRE_STAGE91_CLOSURE_READY",
        "stage91_decision": "PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage91 final scoped SAB package is assembled and stronger claims remain blocked"
        if not problems and rows
        else "; ".join(problems) or "Stage91 final package summary missing"
    )
    return [
        row(
            "S42-STAGE91-FINAL-PACKAGE",
            "final_package",
            pass_fail(not problems and bool(rows)),
            STAGE91_FINAL_PACKAGE.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage91 after source, backend, external-evidence, or claim-scope changes.",
        )
    ]


def check_stage92_external_unlock_execution() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE92_EXTERNAL_UNLOCK_EXECUTION)}
    expected = {
        "stage92_stage91_precondition": "PASS",
        "stage92_unlock_sources": "PASS",
        "stage92_lane_packet": "PASS_EXTERNAL_LANES_RECORDED",
        "stage92_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage92_decision": "PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage92 external unlock execution packet is recorded and stronger claims remain blocked"
        if not problems and rows
        else "; ".join(problems) or "Stage92 external unlock packet summary missing"
    )
    return [
        row(
            "S42-STAGE92-EXTERNAL-UNLOCK-EXECUTION",
            "external_unlock",
            pass_fail(not problems and bool(rows)),
            STAGE92_EXTERNAL_UNLOCK_EXECUTION.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage92 after external evidence, claim-scope, or unlock-command changes.",
        )
    ]


def check_stage93_external_lane_attempt() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE93_EXTERNAL_LANE_ATTEMPT)}
    expected = {
        "stage93_stage92_precondition": "PASS",
        "stage93_native_perf_attempt": "BLOCKED_NATIVE_PERF_CURRENT_ENV",
        "stage93_local_fulltext_search": "LOCAL_FULLTEXT_NOT_FOUND",
        "stage93_external_intake_state": "PASS_EXTERNAL_INTAKE_STILL_MISSING",
        "stage93_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage93_decision": "PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage93 current external lane attempt is recorded and stronger claims remain blocked"
        if not problems and rows
        else "; ".join(problems) or "Stage93 external lane attempt summary missing"
    )
    return [
        row(
            "S42-STAGE93-EXTERNAL-LANE-ATTEMPT",
            "external_unlock",
            pass_fail(not problems and bool(rows)),
            STAGE93_EXTERNAL_LANE_ATTEMPT.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage93 after native perf availability or local full-text artifacts change.",
        )
    ]


def check_stage94_local_frontier_audit() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE94_LOCAL_FRONTIER_AUDIT)}
    expected = {
        "stage94_inputs_available": "PASS",
        "stage94_preferred_path_guard": "PASS_H14_C1_EXPLICIT_PATH_PREFERRED",
        "stage94_no_new_hotpath_guard": "PASS_NO_SAB_SOURCE_CHANGES_AFTER_STAGE89",
        "stage94_candidate_frontier": "PASS_NO_UNBLOCKED_LOCAL_HOTPATH_CANDIDATE",
        "stage94_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage94_decision": "PASS_STAGE94_LOCAL_FRONTIER_AUDIT_NO_NEW_HOTPATH",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage94 local frontier audit records no justified new hot-path candidate"
        if not problems and rows
        else "; ".join(problems) or "Stage94 local frontier audit summary missing"
    )
    return [
        row(
            "S42-STAGE94-LOCAL-FRONTIER-AUDIT",
            "local_frontier",
            pass_fail(not problems and bool(rows)),
            STAGE94_LOCAL_FRONTIER_AUDIT.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage94 after any source, profile, external-evidence, or hypothesis change.",
        )
    ]


def check_stage95_public_source_reprobe() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE95_PUBLIC_SOURCE_REPROBE)}
    expected = {
        "stage95_stage94_precondition": "PASS",
        "stage95_stage72_refresh": "PASS",
        "stage95_public_metadata_routes": "PASS_METADATA_CODE_VISIBLE",
        "stage95_direct_fulltext_routes": "WAIT_FULLTEXT_ARTIFACT",
        "stage95_stage93_consistency": "PASS",
        "stage95_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage95_decision": "PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage95 public source reprobe refreshed metadata/code routes and keeps full-text claims blocked"
        if not problems and rows
        else "; ".join(problems) or "Stage95 public source reprobe summary missing"
    )
    return [
        row(
            "S42-STAGE95-PUBLIC-SOURCE-REPROBE",
            "external_unlock",
            pass_fail(not problems and bool(rows)),
            STAGE95_PUBLIC_SOURCE_REPROBE.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage95 when public source availability or full-text artifact state changes.",
        )
    ]


def check_stage96_upstream_delta_audit() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE96_UPSTREAM_DELTA_AUDIT)}
    expected = {
        "stage96_stage95_precondition": "PASS",
        "stage96_remote_origin_main": "PASS_UPSTREAM_REF_AVAILABLE",
        "stage96_upstream_relation": "PASS_LOCAL_AHEAD_OF_UPSTREAM",
        "stage96_delta_classification": "PASS_DELTA_CLASSIFIED",
        "stage96_default_guard": "PASS_EXPLICIT_FLAGS_DEFAULT_FALSE",
        "stage96_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED",
        "stage96_decision": "PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage96 upstream delta audit records public-code provenance and default-false flag guards"
        if not problems and rows
        else "; ".join(problems) or "Stage96 upstream delta audit summary missing"
    )
    return [
        row(
            "S42-STAGE96-UPSTREAM-DELTA-AUDIT",
            "provenance",
            pass_fail(not problems and bool(rows)),
            STAGE96_UPSTREAM_DELTA_AUDIT.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage96 when upstream code, local source delta, or default flag state changes.",
        )
    ]


def check_stage97_source_delta_guard() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE97_SOURCE_DELTA_GUARD)}
    expected = {
        "stage97_stage96_precondition": "PASS",
        "stage97_source_delta_inventory": "PASS_SOURCE_DELTA_CLASSIFIED",
        "stage97_scalar_symbol_guard": "PASS_SCALAR_SYMBOLS_ISOLATED",
        "stage97_shared_backend_symbol_guard": "PASS_SHARED_BACKEND_SYMBOLS_ISOLATED",
        "stage97_build_flag_guard": "PASS_BUILD_FLAGS_DEFAULT_FALSE_AND_GATED",
        "stage97_smoke_evidence_guard": "PASS_SCALAR_SMOKE_EVIDENCE_PRESENT",
        "stage97_claim_guard": "PASS_SOURCE_GUARD_ONLY_NO_SPEEDUP_CLAIM",
        "stage97_decision": "PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage97 source delta guard records scalar/default separation, symbol isolation, default-false flags, and smoke evidence"
        if not problems and rows
        else "; ".join(problems) or "Stage97 source delta guard summary missing"
    )
    return [
        row(
            "S42-STAGE97-SOURCE-DELTA-GUARD",
            "source_guard",
            pass_fail(not problems and bool(rows)),
            STAGE97_SOURCE_DELTA_GUARD.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage97 when source deltas, scalar/default symbols, build flags, or smoke evidence change.",
        )
    ]


def check_stage98_current_smoke_refresh() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE98_CURRENT_SMOKE_REFRESH)}
    expected = {
        "stage98_stage97_precondition": "PASS",
        "stage98_scalar_binary_smoke": "PASS_SCALAR_BINARY_FULL_RUN",
        "stage98_active_pvw_target_smoke": "PASS_ACTIVE_PVW_TARGET_GATE",
        "stage98_backend_pvw_target_smoke": "PASS_BACKEND_PVW_TARGET_GATE",
        "stage98_scalar_ternary_build": "PASS_SCALAR_TERNARY_BUILD",
        "stage98_raw_log_guard": "PASS_RAW_LOGS_PRESENT",
        "stage98_claim_guard": "PASS_CURRENT_SMOKE_ONLY_NO_SPEEDUP_CLAIM",
        "stage98_decision": "PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage98 current-head smoke refresh passes scalar/default, active PVW target, backend PVW target, and scalar ternary checks"
        if not problems and rows
        else "; ".join(problems) or "Stage98 current-head smoke refresh summary missing"
    )
    return [
        row(
            "S42-STAGE98-CURRENT-SMOKE-REFRESH",
            "current_smoke",
            pass_fail(not problems and bool(rows)),
            STAGE98_CURRENT_SMOKE_REFRESH.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage98 after source, build, backend, scalar/default, or explicit PVW path changes.",
        )
    ]


def check_stage99_external_blocker_reprobe() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE99_EXTERNAL_BLOCKER_REPROBE)}
    expected = {
        "stage99_stage98_precondition": "PASS",
        "stage99_native_perf_reprobe": "RECORDED_WAIT_NATIVE_PERF",
        "stage99_fulltext_reprobe": "RECORDED_FULLTEXT_CANDIDATE_REVIEW_REQUIRED",
        "stage99_public_route_matrix": "PASS_PUBLIC_ROUTES_RECORDED",
        "stage99_novelty_review_gate": "RECORDED_WAIT_NOVELTY_REVIEW",
        "stage99_claim_guard": "PASS_STRONGER_CLAIMS_BLOCKED_UNTIL_EXTERNAL_REVIEW",
        "stage99_decision": "PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_REVIEW_REQUIRED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage99 records native perf still blocked and 2025/686 full text available for review, with stronger claims still guarded"
        if not problems and rows
        else "; ".join(problems) or "Stage99 external blocker reprobe summary missing"
    )
    return [
        row(
            "S42-STAGE99-EXTERNAL-BLOCKER-REPROBE",
            "external_review",
            pass_fail(not problems and bool(rows)),
            STAGE99_EXTERNAL_BLOCKER_REPROBE.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage99 after Stage98, external full-text, native perf, or source-route state changes.",
        )
    ]


def check_stage100_fulltext_anchor_prefill() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE100_FULLTEXT_ANCHOR_PREFILL)}
    expected = {
        "stage100_stage99_precondition": "PASS",
        "stage100_fulltext_artifact": "PASS",
        "stage100_text_extract": "PASS",
        "stage100_anchor_candidates": "CANDIDATE_ANCHORS_GENERATED_REVIEW_REQUIRED",
        "stage100_stage38_prefill": "REVIEW_CHECKLIST_PREFILLED_REVIEW_REQUIRED",
        "stage100_claim_guard": "PASS_NO_CLAIM_UPGRADE",
        "stage100_decision": "PASS_STAGE100_FULLTEXT_ANCHOR_PREFILL_REVIEW_REQUIRED",
    }
    problems = []
    for gate, status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage100 generated candidate-only 2025/686 anchors and preserved manual review requirements"
        if not problems and rows
        else "; ".join(problems) or "Stage100 full-text anchor prefill summary missing"
    )
    return [
        row(
            "S42-STAGE100-FULLTEXT-ANCHOR-PREFILL",
            "external_review",
            pass_fail(not problems and bool(rows)),
            STAGE100_FULLTEXT_ANCHOR_PREFILL.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage100 after Stage99, Stage38 artifact registration, or source-review checklist changes.",
        )
    ]


def check_stage101_cb5_remote_native_perf() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE101_CB5_REMOTE_NATIVE_PERF)}
    expected = {
        "stage101_raw_artifacts": "PASS",
        "stage101_stage28_hardware_counter_gate": "PASS",
        "stage101_complete_sab_correctness": "PASS",
        "stage101_attribution_events": "PASS",
        "stage101_speed_sample": "PASS",
        "stage101_cb5_decision": "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED",
    }
    problems = []
    for gate, expected_status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != expected_status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage101 records native perf/counter evidence and resolves CB5 as a platform blocker"
        if not problems and rows
        else "; ".join(problems) or "Stage101 summary missing"
    )
    return [
        row(
            "S42-STAGE101-CB5-REMOTE-NATIVE-PERF",
            "external_review",
            pass_fail(not problems and bool(rows)),
            STAGE101_CB5_REMOTE_NATIVE_PERF.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage101 parser or recopy remote perf logs before relying on native counter evidence.",
        )
    ]


def check_stage102_686_source_anchor_review() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE102_686_SOURCE_ANCHOR_REVIEW)}
    expected = {
        "stage102_fulltext_precondition": "PASS",
        "stage102_candidate_precondition": "PASS",
        "stage102_review_matrix": "PASS",
        "stage102_stage38_update": "PASS",
        "stage102_decision": "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED",
    }
    problems = []
    for gate, expected_status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != expected_status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage102 verifies 2025/686 source anchors and resolves CB7 for scoped citations"
        if not problems and rows
        else "; ".join(problems) or "Stage102 summary missing"
    )
    return [
        row(
            "S42-STAGE102-686-SOURCE-ANCHOR-REVIEW",
            "external_review",
            pass_fail(not problems and bool(rows)),
            STAGE102_686_SOURCE_ANCHOR_REVIEW.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage102 before relying on 2025/686 reviewed anchors.",
        )
    ]


def check_stage103_related_work_novelty_review() -> List[Dict[str, str]]:
    rows = {r.get("gate"): r for r in read_csv(STAGE103_RELATED_WORK_NOVELTY_REVIEW)}
    expected = {
        "stage103_stage102_precondition": "PASS",
        "stage103_source_verification": "PASS",
        "stage103_related_work_matrix": "PASS",
        "stage103_novelty_boundary": "PASS_SCOPED_BOUNDARY",
        "stage103_decision": "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED",
    }
    problems = []
    for gate, expected_status in expected.items():
        actual = rows.get(gate, {}).get("status", "MISSING")
        if actual != expected_status:
            problems.append(f"{gate}:status={actual}")
    detail = (
        "Stage103 resolves CB6 by scoped related-work and novelty-boundary review"
        if not problems and rows
        else "; ".join(problems) or "Stage103 summary missing"
    )
    return [
        row(
            "S42-STAGE103-RELATED-WORK-NOVELTY-REVIEW",
            "external_review",
            pass_fail(not problems and bool(rows)),
            STAGE103_RELATED_WORK_NOVELTY_REVIEW.relative_to(ROOT).as_posix(),
            detail,
            "Rerun Stage103 before relying on scoped novelty wording.",
        )
    ]


def check_remaining_blocker_dashboard() -> List[Dict[str, str]]:
    rows = {r.get("blocker_id"): r for r in read_csv(REMAINING_BLOCKERS)}
    problems = []
    required_columns = [
        "blocking_condition",
        "evidence",
        "unlock_command",
        "review_gate",
        "claim_policy",
    ]
    for blocker_id, expected in EXPECTED_REMAINING_BLOCKERS.items():
        blocker_row = rows.get(blocker_id)
        if not blocker_row:
            problems.append(f"{blocker_id}:missing")
            continue
        current_status = blocker_row.get("current_status", "")
        claim_policy = blocker_row.get("claim_policy", "")
        for token in expected["status_tokens"]:
            if token not in current_status:
                problems.append(f"{blocker_id}:status_missing:{token}")
        for token in expected["policy_tokens"]:
            if token not in claim_policy:
                problems.append(f"{blocker_id}:policy_missing:{token}")
        for column in required_columns:
            if not blocker_row.get(column, "").strip():
                problems.append(f"{blocker_id}:{column}=empty")
    return [
        row(
            "S42-REMAINING-BLOCKERS",
            "claim_scope",
            pass_fail(not problems and bool(rows)),
            REMAINING_BLOCKERS.relative_to(ROOT).as_posix(),
            "CB5/CB6/CB7/A9 blocker dashboard preserves stronger-claim blocks"
            if not problems and rows
            else "; ".join(problems) or "dashboard missing or empty",
            "Regenerate remaining blocker dashboard and final recheck before relying on stronger-claim blocker state.",
        )
    ]


def check_freeze_manifest() -> List[Dict[str, str]]:
    rows = read_csv(FREEZE_MANIFEST)
    problems = []
    for r in rows:
        artifact = r.get("artifact", "")
        path = ROOT / artifact
        expected_hash = r.get("sha256", "")
        if r.get("exists") != "yes":
            problems.append(f"{artifact}:exists={r.get('exists')}")
        elif not path.exists():
            problems.append(f"{artifact}:missing")
        elif not expected_hash:
            problems.append(f"{artifact}:missing_hash")
        elif sha256_file(path) != expected_hash:
            problems.append(f"{artifact}:hash_mismatch")
    return [
        row(
            "S42-STAGE40-FREEZE-HASHES",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            FREEZE_MANIFEST.relative_to(ROOT).as_posix(),
            f"{len(rows)} freeze artifacts match recorded SHA-256 hashes"
            if not problems and rows
            else "; ".join(problems) or "manifest missing or empty",
            "Regenerate or repair the Stage 40 freeze manifest before treating the freeze as immutable evidence.",
        )
    ]


def check_closure_manifest() -> List[Dict[str, str]]:
    rows = read_csv(OUT_MANIFEST)
    problems = []
    expected = set(POSTFREEZE_MANIFEST_ARTIFACTS)
    observed = {r.get("artifact", "") for r in rows}
    missing_rows = sorted(expected - observed)
    extra_rows = sorted(observed - expected - {""})
    if missing_rows:
        problems.append(f"missing_rows={missing_rows}")
    if extra_rows:
        problems.append(f"extra_rows={extra_rows}")
    for r in rows:
        artifact = r.get("artifact", "")
        path = ROOT / artifact
        if artifact not in expected:
            continue
        if r.get("exists") != "yes":
            problems.append(f"{artifact}:exists={r.get('exists')}")
        elif not path.exists():
            problems.append(f"{artifact}:missing")
        elif r.get("size_bytes") != str(path.stat().st_size):
            problems.append(f"{artifact}:size_mismatch")
        elif not r.get("sha256"):
            problems.append(f"{artifact}:missing_hash")
        elif sha256_file(path) != r.get("sha256"):
            problems.append(f"{artifact}:hash_mismatch")
    return [
        row(
            "S42-CLOSURE-MANIFEST-HASHES",
            "reproducibility",
            pass_fail(not problems and bool(rows)),
            OUT_MANIFEST.relative_to(ROOT).as_posix(),
            f"{len(rows)} post-freeze control artifacts match recorded SHA-256 hashes"
            if not problems and rows
            else "; ".join(problems) or "manifest missing or empty",
            "Regenerate or repair the Stage 42 closure manifest before relying on post-freeze control-plane evidence.",
        )
    ]


def check_postfreeze() -> List[Dict[str, str]]:
    rows = {r.get("check"): r for r in read_csv(POSTFREEZE)}
    expected = {
        "postfreeze_decision": "PASS_POSTFREEZE_VERIFY",
        "freeze_manifest_hashes": "PASS",
        "external_blockers_preserved": "PASS",
    }
    mismatches = []
    for check, expected_status in expected.items():
        got = rows.get(check, {}).get("status", "MISSING")
        if got != expected_status:
            mismatches.append(f"{check}:{got}!={expected_status}")
    return [
        row(
            "S42-POSTFREEZE-VERIFY",
            "reproducibility",
            pass_fail(not mismatches),
            POSTFREEZE.relative_to(ROOT).as_posix(),
            "post-freeze verifier preserves hashes and external blockers"
            if not mismatches
            else "; ".join(mismatches),
            "Rerun the Stage 40 post-freeze verifier from a clean worktree input.",
        )
    ]


def check_run_log() -> List[Dict[str, str]]:
    rows = read_csv(RUN_LOG)
    stages: Dict[int, int] = {}
    stage41_status = "MISSING"
    for r in rows:
        stage = r.get("stage", "")
        if stage.startswith("Stage "):
            try:
                n = int(stage.split()[1])
            except (IndexError, ValueError):
                continue
            if 19 <= n <= 62:
                stages[n] = stages.get(n, 0) + 1
        if r.get("run_id") == "stage41-external-unlock-packet-001":
            stage41_status = r.get("status", "MISSING")
    missing = [n for n in range(19, 63) if n not in stages]
    ok = not missing and stage41_status == "WAIT_EXTERNAL_EVIDENCE"
    stage66_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage66a-post-variant-final-recheck-001":
            stage66_status = r.get("status", "MISSING")
    stage67_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage67-final-recheck-stage66-001":
            stage67_status = r.get("status", "MISSING")
    stage68_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage68-frontier-closure-consistency-001":
            stage68_status = r.get("status", "MISSING")
    stage69_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage69-local-variant-feasibility-001":
            stage69_status = r.get("status", "MISSING")
    stage70_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage70-external-unlock-preflight-001":
            stage70_status = r.get("status", "MISSING")
    stage71_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage71-final-recheck-stage70-001":
            stage71_status = r.get("status", "MISSING")
    stage72_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage72-external-source-refresh-001":
            stage72_status = r.get("status", "MISSING")
    stage73_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage73-final-recheck-stage72-001":
            stage73_status = r.get("status", "MISSING")
    stage74_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage74-r-scaling-boundary-001":
            stage74_status = r.get("status", "MISSING")
    stage75_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage75-rgt4-profile-boundary-001":
            stage75_status = r.get("status", "MISSING")
    stage76_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage76-rgt4-kernel-feasibility-001":
            stage76_status = r.get("status", "MISSING")
    stage77_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage77-rgt4-fused-mat-kernel-001":
            stage77_status = r.get("status", "MISSING")
    stage78_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage78-rgt4-fused-repeated-gates-001":
            stage78_status = r.get("status", "MISSING")
    stage79_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage79-rgt4-fused-high-stat-001":
            stage79_status = r.get("status", "MISSING")
    stage80_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage80-promotion-policy-audit-001":
            stage80_status = r.get("status", "MISSING")
    stage81_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage81-next-variant-triage-001":
            stage81_status = r.get("status", "MISSING")
    stage82_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage82-post-h11-profile-001":
            stage82_status = r.get("status", "MISSING")
    stage83_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage83-mat-body-design-check-001":
            stage83_status = r.get("status", "MISSING")
    stage84_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage84-h13-r6-tile-sweep-preflight-001":
            stage84_status = r.get("status", "MISSING")
    stage86_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage86-secondary-cmux-materialization-001":
            stage86_status = r.get("status", "MISSING")
    stage87_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage87-h14-backend-from-dft-add-preflight-001":
            stage87_status = r.get("status", "MISSING")
    stage88_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage88-h14-backend-repeated-gates-001":
            stage88_status = r.get("status", "MISSING")
    stage89_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage89-h14-promotion-policy-integration-001":
            stage89_status = r.get("status", "MISSING")
    stage90_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage90-external-claim-unlock-001":
            stage90_status = r.get("status", "MISSING")
    stage91_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage91-final-scoped-package-001":
            stage91_status = r.get("status", "MISSING")
    stage92_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage92-external-unlock-execution-001":
            stage92_status = r.get("status", "MISSING")
    stage93_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage93-external-lane-attempt-001":
            stage93_status = r.get("status", "MISSING")
    stage94_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage94-local-frontier-audit-001":
            stage94_status = r.get("status", "MISSING")
    stage95_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage95-public-source-reprobe-001":
            stage95_status = r.get("status", "MISSING")
    stage96_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage96-upstream-delta-audit-001":
            stage96_status = r.get("status", "MISSING")
    stage97_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage97-source-delta-guard-001":
            stage97_status = r.get("status", "MISSING")
    stage98_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage98-current-smoke-refresh-001":
            stage98_status = r.get("status", "MISSING")
    stage99_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage99-external-blocker-reprobe-001":
            stage99_status = r.get("status", "MISSING")
    stage100_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage100-fulltext-anchor-prefill-001":
            stage100_status = r.get("status", "MISSING")
    stage101_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage101-cb5-remote-native-perf-001":
            stage101_status = r.get("status", "MISSING")
    stage102_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage102-686-source-anchor-review-001":
            stage102_status = r.get("status", "MISSING")
    stage103_status = "MISSING"
    for r in rows:
        if r.get("run_id") == "stage103-related-work-novelty-review-001":
            stage103_status = r.get("status", "MISSING")
    ok = (
        ok
        and stage66_status == "PASS_POST_VARIANT_FINAL_RECHECK"
        and stage67_status == "PASS_FINAL_RECHECK_STAGE66_INTEGRATION"
        and stage68_status == "PASS_FRONTIER_CLOSURE_CONSISTENCY"
        and stage69_status == "PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED"
        and stage70_status == "PASS_EXTERNAL_UNLOCK_PREFLIGHT_STRONGER_CLAIMS_BLOCKED"
        and stage71_status == "PASS_FINAL_RECHECK_STAGE70_INTEGRATION"
        and stage72_status == "PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED"
        and stage73_status == "PASS_FINAL_RECHECK_STAGE72_INTEGRATION"
        and stage74_status == "PASS_R_GT4_BOUNDARY_RECORDED_NOT_PROMOTED"
        and stage75_status == "PASS_RGT4_PROFILE_BOUNDARY_RECORDED_NOT_PROMOTED"
        and stage76_status == "PASS_RGT4_KERNEL_FEASIBILITY_RECORDED_NO_PROMOTION"
        and stage77_status == "PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED"
        and stage78_status == "PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE"
        and stage79_status == "PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED"
        and stage80_status == "PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED"
        and stage81_status == "PASS_STAGE81_NEXT_VARIANT_TRIAGE_PROFILE_FIRST_NO_CODE_PROMOTION"
        and stage82_status == "PASS_STAGE82_POST_H11_PROFILE_MAT_BODY_PRIMARY"
        and stage83_status == "PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT"
        and stage84_status == "PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED"
        and stage86_status == "PASS_STAGE86_SECONDARY_CMUX_MATERIALIZATION_SELECT_BACKEND_PREFLIGHT"
        and stage87_status == "PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE"
        and stage88_status == "PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE"
        and stage89_status == "PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT"
        and stage90_status == "PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED"
        and stage91_status == "PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED"
        and stage92_status == "PASS_STAGE92_EXTERNAL_UNLOCK_PACKET_RECORDED_STRONGER_CLAIMS_BLOCKED"
        and stage93_status == "PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED"
        and stage94_status == "PASS_STAGE94_LOCAL_FRONTIER_AUDIT_NO_NEW_HOTPATH"
        and stage95_status == "PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED"
        and stage96_status == "PASS_STAGE96_UPSTREAM_DELTA_AUDIT_LOCAL_PROVENANCE_RECORDED"
        and stage97_status == "PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED"
        and stage98_status == "PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH"
        and stage99_status == "PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_REVIEW_REQUIRED"
        and stage100_status == "PASS_STAGE100_FULLTEXT_ANCHOR_PREFILL_REVIEW_REQUIRED"
        and stage101_status == "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED"
        and stage102_status == "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED"
        and stage103_status == "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED"
    )
    detail = (
        f"stages 19-62 registered; stage41 status={stage41_status}; stage66 status={stage66_status}; stage67 status={stage67_status}; stage68 status={stage68_status}; stage69 status={stage69_status}; stage70 status={stage70_status}; stage71 status={stage71_status}; stage72 status={stage72_status}; stage73 status={stage73_status}; stage74 status={stage74_status}; stage75 status={stage75_status}; stage76 status={stage76_status}; stage77 status={stage77_status}; stage78 status={stage78_status}; stage79 status={stage79_status}; stage80 status={stage80_status}; stage81 status={stage81_status}; stage82 status={stage82_status}; stage83 status={stage83_status}; stage84 status={stage84_status}; stage86 status={stage86_status}; stage87 status={stage87_status}; stage88 status={stage88_status}; stage89 status={stage89_status}; stage90 status={stage90_status}; stage91 status={stage91_status}; stage92 status={stage92_status}; stage93 status={stage93_status}; stage94 status={stage94_status}; stage95 status={stage95_status}; stage96 status={stage96_status}; stage97 status={stage97_status}; stage98 status={stage98_status}; stage99 status={stage99_status}; stage100 status={stage100_status}; stage101 status={stage101_status}; stage102 status={stage102_status}; stage103 status={stage103_status}"
        if ok
        else f"missing_stages={missing}; stage41 status={stage41_status}; stage66 status={stage66_status}; stage67 status={stage67_status}; stage68 status={stage68_status}; stage69 status={stage69_status}; stage70 status={stage70_status}; stage71 status={stage71_status}; stage72 status={stage72_status}; stage73 status={stage73_status}; stage74 status={stage74_status}; stage75 status={stage75_status}; stage76 status={stage76_status}; stage77 status={stage77_status}; stage78 status={stage78_status}; stage79 status={stage79_status}; stage80 status={stage80_status}; stage81 status={stage81_status}; stage82 status={stage82_status}; stage83 status={stage83_status}; stage84 status={stage84_status}; stage86 status={stage86_status}; stage87 status={stage87_status}; stage88 status={stage88_status}; stage89 status={stage89_status}; stage90 status={stage90_status}; stage91 status={stage91_status}; stage92 status={stage92_status}; stage93 status={stage93_status}; stage94 status={stage94_status}; stage95 status={stage95_status}; stage96 status={stage96_status}; stage97 status={stage97_status}; stage98 status={stage98_status}; stage99 status={stage99_status}; stage100 status={stage100_status}; stage101 status={stage101_status}; stage102 status={stage102_status}; stage103 status={stage103_status}"
    )
    return [
        row(
            "S42-RUN-LOG-COVERAGE",
            "reproducibility",
            pass_fail(ok),
            RUN_LOG.relative_to(ROOT).as_posix(),
            detail,
            "Add missing run-log rows or correct Stage 41 status before claiming a complete audit trail.",
        )
    ]


def check_required_files() -> List[Dict[str, str]]:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    return [
        row(
            "S42-REQUIRED-FILES",
            "reproducibility",
            pass_fail(not missing),
            "; ".join(REQUIRED_FILES),
            "all required Stage 41-62 plus Stage64A/Stage65A/Stage66A/Stage67/Stage68/Stage69/Stage70/Stage71/Stage72/Stage73/Stage74/Stage75/Stage76/Stage77/Stage78/Stage79/Stage80/Stage81/Stage82/Stage83/Stage84/Stage86/Stage87/Stage88/Stage89/Stage90/Stage91/Stage92/Stage93/Stage94/Stage95/Stage96/Stage97/Stage98 files exist" if not missing else f"missing={missing}",
            "Restore missing Stage 41-62, Stage64A, Stage65A, Stage66A, Stage67, Stage68, Stage69, Stage70, Stage71, Stage72, Stage73, Stage74, Stage75, Stage76, Stage77, Stage78, Stage79, Stage80, Stage81, Stage82, Stage83, Stage84, Stage86, Stage87, Stage88, Stage89, Stage90, Stage91, Stage92, Stage93, Stage94, Stage95, Stage96, Stage97, or Stage98 control-plane artifacts.",
        )
    ]


def check_manifest_mentions() -> List[Dict[str, str]]:
    text = ARTIFACT_MANIFEST.read_text(encoding="utf-8") if ARTIFACT_MANIFEST.exists() else ""
    required_mentions = [
        "SAB_PVW_SCHEDULE_FUSED_CMUX",
        "scripts/build_stage41_external_unlock_packet.py",
        "docs/stage41_external_unlock_packet.md",
        "experiments/stage41_external_unlock_plan.md",
        "repro/stage41_external_unlock_packet.csv",
        "docs/stage43_postclosure_current_smoke_log.md",
        "experiments/stage43_postclosure_current_smoke_plan.md",
        "repro/stage43_current_smoke_after_stage42/summary.csv",
        "repro/final_goal_recheck_stage42_closure/summary.csv",
        "repro/final_goal_recheck_stage42_closure/stage42_evidence_closure.log",
        "repro/final_goal_recheck/stage42_evidence_closure.log",
        "repro/final_goal_recheck/stage70_external_unlock_preflight.log",
        "repro/stage42_evidence_closure_manifest.csv",
        "scripts/build_conditional_backlog_audit.py",
        "docs/conditional_backlog_audit.md",
        "repro/conditional_backlog_audit.csv",
        "scripts/build_remaining_blocker_dashboard.py",
        "docs/remaining_blocker_dashboard.md",
        "repro/remaining_blocker_dashboard.csv",
        "repro/final_goal_recheck/remaining_blocker_dashboard.log",
        "docs/stage44_external_unlock_reprobe_log.md",
        "experiments/stage44_external_unlock_reprobe_plan.md",
        "scripts/build_stage44_external_unlock_reprobe.py",
        "scripts/run_stage44_external_unlock_reprobe.sh",
        "repro/stage44_external_unlock_reprobe/summary.csv",
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
        *STAGE101_ARTIFACTS,
        *STAGE102_ARTIFACTS,
        *STAGE103_ARTIFACTS,
    ]
    missing = [m for m in required_mentions if m not in text]
    return [
        row(
            "S42-ARTIFACT-MANIFEST",
            "reproducibility",
            pass_fail(not missing),
            ARTIFACT_MANIFEST.relative_to(ROOT).as_posix(),
            "Stage 23 flag plus conditional backlog and Stage 41, Stage 43, Stage 44, Stage 48, Stage 49, Stage 50, Stage 51, Stage 52, Stage 53, Stage 54, Stage 55, Stage 56, Stage 57, Stage 58, Stage 59, Stage 60, Stage 61, Stage 62, Stage64A, Stage65A, Stage66A, Stage67, Stage68, Stage69, Stage70, Stage71, Stage72, Stage73, Stage74, Stage75, Stage76, Stage77, Stage78, Stage79, Stage80, Stage81, Stage82, Stage83, Stage84, Stage86, Stage87, Stage88, Stage89, Stage90, Stage91, Stage92, Stage93, Stage94, Stage95, Stage96, Stage97, Stage98, Stage99, Stage100, Stage101, Stage102, and Stage103 artifacts are registered"
            if not missing
            else f"missing_mentions={missing}",
            "Update the artifact manifest so the reproducibility pack names all current control artifacts.",
        )
    ]


def check_claim_guardrails() -> List[Dict[str, str]]:
    texts = {
        GOAL.relative_to(ROOT).as_posix(): GOAL.read_text(encoding="utf-8") if GOAL.exists() else "",
        LOOP.relative_to(ROOT).as_posix(): LOOP.read_text(encoding="utf-8") if LOOP.exists() else "",
        ROADMAP.relative_to(ROOT).as_posix(): ROADMAP.read_text(encoding="utf-8") if ROADMAP.exists() else "",
    }
    required_tokens = [
        "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
        "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED",
        "WAIT_EXTERNAL_FULLTEXT",
        "WAIT_NATIVE_PERF",
        "scalar SAB remains unchanged",
    ]
    haystack = "\n".join(texts.values())
    missing = [t for t in required_tokens if t not in haystack]
    return [
        row(
            "S42-CLAIM-GUARDRAILS",
            "claim_scope",
            pass_fail(not missing),
            "; ".join(texts.keys()),
            "scoped-ready and external-waiting guardrails are visible"
            if not missing
            else f"missing_tokens={missing}",
            "Restore claim guardrails before drafting reports or changing final decision labels.",
        )
    ]


def build_rows() -> List[Dict[str, str]]:
    checks: List[Dict[str, str]] = []
    for fn in [
        check_roadmap,
        check_final_audit,
        check_stage41,
        check_stage43_smoke,
        check_stage44_reprobe,
        check_stage45_active_state,
        check_stage46_wsl_target,
        check_stage47_wsl_full_sab,
        check_stage48_wsl_noise,
        check_stage49_wsl_repeated_full_sab,
        check_stage50_performance_matrix,
        check_stage51_goal_frontier,
        check_stage52_external_unlock_readiness,
        check_stage53_final_recheck_integration,
        check_stage54_default_final_recheck,
        check_stage55_external_paper_probe,
        check_stage56_final_recheck_stage55,
        check_stage57_scope_label_audit,
        check_stage58_final_recheck_stage57,
        check_stage59_completion_route,
        check_stage60_final_recheck_stage59,
        check_stage61_native_perf_unlock,
        check_stage62_fulltext_unlock,
        check_stage64a_post_variant_refresh,
        check_stage65a_r4_unrolled_variant,
        check_stage66a_post_variant_final_recheck,
        check_stage67_final_recheck_stage66,
        check_stage68_frontier_closure_consistency,
        check_stage69_local_variant_feasibility,
        check_stage70_external_unlock_preflight,
        check_stage71_final_recheck_stage70,
        check_stage72_external_source_refresh,
        check_stage73_final_recheck_stage72,
        check_stage74_r_scaling_boundary,
        check_stage75_rgt4_profile_boundary,
        check_stage76_rgt4_kernel_feasibility,
        check_stage77_rgt4_fused_mat_kernel,
        check_stage78_rgt4_fused_repeated_gates,
        check_stage79_rgt4_fused_high_stat,
        check_stage80_promotion_policy_audit,
        check_stage81_next_variant_triage,
        check_stage82_post_h11_profile,
        check_stage83_mat_body_design_check,
        check_stage84_h13_r6_tile_sweep_preflight,
        check_stage86_secondary_cmux_materialization,
        check_stage87_h14_backend_from_dft_add_preflight,
        check_stage88_h14_backend_repeated_gates,
        check_stage89_h14_promotion_policy,
        check_stage90_external_claim_unlock,
        check_stage91_final_package,
        check_stage92_external_unlock_execution,
        check_stage93_external_lane_attempt,
        check_stage94_local_frontier_audit,
        check_stage95_public_source_reprobe,
        check_stage96_upstream_delta_audit,
        check_stage97_source_delta_guard,
        check_stage98_current_smoke_refresh,
        check_stage99_external_blocker_reprobe,
        check_stage100_fulltext_anchor_prefill,
        check_stage101_cb5_remote_native_perf,
        check_stage102_686_source_anchor_review,
        check_stage103_related_work_novelty_review,
        check_remaining_blocker_dashboard,
        check_freeze_manifest,
        check_closure_manifest,
        check_postfreeze,
        check_run_log,
        check_required_files,
        check_manifest_mentions,
        check_claim_guardrails,
    ]:
        checks.extend(fn())

    failures = [r["check_id"] for r in checks if r["status"] != "PASS"]
    latest_label = latest_control_stage_label()
    checks.append(
        row(
            "S42-OVERALL",
            "overall",
            "PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED" if not failures else "FAIL_EVIDENCE_CLOSURE",
            OUT_CSV.relative_to(ROOT).as_posix(),
            f"{latest_label} control-plane closure is internally closed: core Stage 19-62 scoped evidence chain plus Stage64A post-variant refresh, Stage65A optional negative variant, Stage66A post-variant final recheck, Stage67 final-recheck Stage66A integration, Stage68 frontier/closure consistency, Stage69 local variant feasibility, Stage70 external unlock preflight, Stage71 final-recheck Stage70 integration, Stage72 external source refresh, Stage73 final-recheck Stage72 integration, Stage74 r-scaling boundary, Stage75 r>4 profile boundary, Stage76 r>4 kernel feasibility, Stage77 r>4 fused MAT smoke, Stage78 r>4 fused repeated gates, Stage79 r>4 fused high-stat review gate, Stage80 promotion policy audit, Stage81 next-variant triage, Stage82 post-H11 profile, Stage83 MAT body design check, Stage84 H13 r=6 tile-sweep preflight, Stage86 secondary CMUX materialization design gate, Stage87 H14 backend FromDFT-add preflight, Stage88 H14 backend repeated gates, Stage89 H14 promotion policy integration, Stage90 external claim unlock probe, Stage91 final scoped SAB package, Stage92 external unlock execution packet, Stage93 external lane attempt, Stage94 local frontier audit, Stage95 public source reprobe, Stage96 upstream delta audit, Stage97 source delta guard, Stage98 current-head smoke refresh, Stage99 external blocker reprobe, Stage100 full-text anchor prefill, Stage101 native perf evidence, Stage102 source-anchor review, and Stage103 scoped novelty review; stronger claims remain scoped or blocked by evidence boundaries"
            if not failures
            else f"failed_checks={failures}",
            "Fix all failed checks before relying on the Stage 19-62 plus Stage64A/Stage65A/Stage66A/Stage67/Stage68/Stage69/Stage70/Stage71/Stage72/Stage73/Stage74/Stage75/Stage76/Stage77/Stage78/Stage79/Stage80/Stage81/Stage82/Stage83/Stage84/Stage86/Stage87/Stage88/Stage89/Stage90/Stage91/Stage92/Stage93/Stage94/Stage95/Stage96/Stage97/Stage98/Stage99/Stage100/Stage101/Stage102/Stage103 evidence closure.",
        )
    )
    return checks


def write_csv(rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: List[Dict[str, str]]) -> None:
    overall = rows[-1]
    lines = [
        "# Stage 42 Evidence Closure Audit",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 42 machine-checks whether the Stage 19-62 PVW/MAT-SAB evidence",
        "chain plus Stage64A post-variant refresh, the Stage65A optional",
        "negative variant, Stage66A post-variant final recheck, Stage67",
        "final-recheck Stage66A integration, and Stage68-103 control-plane",
        "closure extensions remain internally",
        "consistent. It is a reproducibility and claim",
        "guardrail audit, not a new SAB optimization or benchmark.",
        "",
        "## Summary",
        "",
        f"- overall: `{overall['status']}`",
        f"- detail: {overall['detail']}",
        "",
        "## Checks",
        "",
        "| check | status | category | evidence | detail |",
        "|---|---|---|---|---|",
    ]
    for r in rows[:-1]:
        lines.append(
            f"| {r['check_id']} | {r['status']} | {r['category']} | "
            f"{r['evidence']} | {r['detail']} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The scoped engineering acceleration evidence chain is closed under the",
            "currently recorded artifacts if and only if `S42-OVERALL` is",
            "`PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED`.",
            "That status preserves the existing external blockers for full-text",
            "2025/686 review and native perf-counter attribution.",
            "",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    while lines and lines[-1] == "":
        lines.pop()
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    write_closure_manifest()
    rows = build_rows()
    write_csv(rows)
    write_md(rows)
    overall = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage 42 evidence closure: {overall}")
    return 0 if overall.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
