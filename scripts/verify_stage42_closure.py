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
    ]
    missing_run_ids = [run_id for run_id in required_run_ids if run_id not in run_ids]
    required_manifest_mentions = [
        "scripts/verify_stage42_closure.py",
        "repro/stage42_evidence_closure_manifest.csv",
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
            "detail": "all Stage42/43/44/45/46/47/48/49/50/51/52 closure run rows are present"
            if not missing_run_ids
            else "; ".join(missing_run_ids),
        },
        {
            "check": "artifact_manifest_mentions",
            "status": "PASS" if not missing_manifest_mentions else "FAIL",
            "evidence": "repro/artifact_manifest.md",
            "detail": "Stage42 verifier, closure manifest, Stage44 re-probe, Stage45 refactor, Stage46 target smoke, Stage47 full-SAB smoke, Stage48 noise smoke, Stage49 repeated full-SAB stability, Stage50 performance matrix, Stage51 goal frontier, and Stage52 external unlock readiness are registered"
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
