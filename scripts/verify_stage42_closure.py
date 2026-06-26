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
STAGE44_RECHECK = ROOT / "repro" / "final_goal_recheck_stage44_reprobe" / "summary.csv"
DEFAULT_RECHECK = ROOT / "repro" / "final_goal_recheck" / "summary.csv"
CLOSURE_RECHECK = ROOT / "repro" / "final_goal_recheck_stage42_closure" / "summary.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"
ARTIFACT_MANIFEST = ROOT / "repro" / "artifact_manifest.md"


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
    stage44_recheck = {row.get("step"): row for row in read_csv(STAGE44_RECHECK)}
    default_recheck = {row.get("step"): row for row in read_csv(DEFAULT_RECHECK)}
    closure_recheck = {row.get("step"): row for row in read_csv(CLOSURE_RECHECK)}
    run_log = read_csv(RUN_LOG)
    artifact_manifest = ARTIFACT_MANIFEST.read_text(encoding="utf-8") if ARTIFACT_MANIFEST.exists() else ""

    stage41_mismatches = []
    expected_stage41 = {
        "S41-FULLTEXT-INTAKE": "WAIT_EXTERNAL_FULLTEXT",
        "S41-NATIVE-PERF-INTAKE": "WAIT_NATIVE_PERF",
        "S41-EXTERNAL-REGISTRATION": "WAIT_EXTERNAL_ARTIFACTS",
        "S41-FINAL-RECHECK": "WAIT_UNLOCKS",
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
    for frontier_id in ["B1", "B2", "B3"]:
        status = stage51.get(frontier_id, {}).get("status", "MISSING")
        if "BLOCKED" not in status:
            stage51_mismatches.append(f"{frontier_id}:status={status}")
    g9_status = stage51.get("G9", {}).get("status", "MISSING")
    if g9_status != "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED":
        stage51_mismatches.append(f"G9:status={g9_status}")
    stage42_stage51_ok = (
        stage42.get("S42-STAGE51-GOAL-FRONTIER", {}).get("status") == "PASS"
    )
    stage52_mismatches = []
    expected_stage52 = {
        "S52-NATIVE-PERF": "WAIT_NATIVE_PERF",
        "S52-FULLTEXT-686": "WAIT_EXTERNAL_FULLTEXT",
        "S52-NOVELTY-REVIEW": "WAIT_MANUAL_FULLTEXT_REVIEW",
        "S52-EXTERNAL-REGISTRATION": "WAIT_EXTERNAL_ARTIFACTS",
        "S52-FINAL-RECHECK": "WAIT_UNLOCKS",
    }
    for unlock_id, expected_readiness in expected_stage52.items():
        row_data = stage52.get(unlock_id)
        if not row_data:
            stage52_mismatches.append(f"{unlock_id}:missing")
            continue
        if row_data.get("readiness") != expected_readiness:
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
        "S59-R4-FULLTEXT-686": "EXTERNAL_FULLTEXT_BLOCKED",
        "S59-R5-NOVELTY-REVIEW": "EXTERNAL_REVIEW_BLOCKED",
        "S59-R6-OPTIONAL-VARIANTS": "READY_OPTIONAL_LOCAL_TRIAGE",
        "S59-R7-FINAL-PAPER-PACKAGE": "WAIT_STRONGER_UNLOCKS",
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
            "detail": status_before_outputs.replace("\n", "; ")
            if status_before_outputs.strip()
            else "tracked and untracked worktree was clean before verifier outputs.",
        },
        {
            "check": "final_audit_A9",
            "status": "PASS"
            if final_audit.get("A9", {}).get("status")
            == "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
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
            "detail": "all Stage42/43/44/45/46/47/48/49/50/51/52/53/54/55/56/57/58/59/60/61/62 plus Stage64A/Stage65A/Stage66A/Stage67/Stage68/Stage69/Stage70/Stage71/Stage72/Stage73/Stage74/Stage75/Stage76 closure run rows are present"
            if not missing_run_ids
            else "; ".join(missing_run_ids),
        },
        {
            "check": "artifact_manifest_mentions",
            "status": "PASS" if not missing_manifest_mentions else "FAIL",
            "evidence": "repro/artifact_manifest.md",
            "detail": "Stage42 verifier, closure manifest, Stage44 re-probe, Stage45 refactor, Stage46 target smoke, Stage47 full-SAB smoke, Stage48 noise smoke, Stage49 repeated full-SAB stability, Stage50 performance matrix, Stage51 goal frontier, Stage52 external unlock readiness, Stage53 final recheck integration, Stage54 default final recheck, Stage55 paper probe, Stage56 final recheck integration, Stage57 scope-label audit, Stage58 final recheck integration, Stage59 completion route, Stage60 final recheck integration, Stage61 native perf unlock probe, Stage62 full-text unlock probe, Stage64A post-variant refresh, Stage65A r4 unrolled variant, Stage66A post-variant final recheck, Stage67 final-recheck Stage66A integration, Stage68 frontier/closure consistency, Stage69 local variant feasibility, Stage70 external unlock preflight, Stage71 final-recheck Stage70 integration, Stage72 external source refresh, Stage73 final-recheck Stage72 integration, Stage74 r-scaling boundary, Stage75 r>4 profile boundary, and Stage76 r>4 kernel feasibility are registered"
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
