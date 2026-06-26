#!/usr/bin/env python3
"""Build the Stage 42 evidence-closure audit.

This script checks whether the current scoped PVW/MAT-SAB evidence chain is
internally consistent through Stage 44. It does not run benchmarks or upgrade
claims; it verifies that the committed artifacts still support the recorded
scope.
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
    "A6": "PASS_BLOCKED_BOUNDARY",
    "A7": "PASS_ADDED_PARAM_10RUN_20SEED",
    "A8": "BLOCKED_EXTERNAL",
    "A8b": "MISSING_OPTIONAL_EXTERNAL_EVIDENCE",
    "A9": "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
}

EXPECTED_STAGE41_READINESS = {
    "S41-FULLTEXT-INTAKE": "WAIT_EXTERNAL_FULLTEXT",
    "S41-NATIVE-PERF-INTAKE": "WAIT_NATIVE_PERF",
    "S41-EXTERNAL-REGISTRATION": "WAIT_EXTERNAL_ARTIFACTS",
    "S41-FINAL-RECHECK": "WAIT_UNLOCKS",
}

EXPECTED_REMAINING_BLOCKERS = {
    "CB5": {
        "status_tokens": [
            "final_A8=BLOCKED_EXTERNAL",
            "cb5=BLOCKED_EXTERNAL",
            "stage44_perf=BLOCKED",
            "external_perf=MISSING",
        ],
        "policy_tokens": ["Do not claim theoretical MAT-AVX512"],
    },
    "CB6": {
        "status_tokens": [
            "cb6=BLOCKED_EXTERNAL_REVIEW",
            "related=SCOPED_RELATED_WORK_REFRESHED__NOVELTY_STILL_BLOCKED",
            "novelty_gate=BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW",
        ],
        "policy_tokens": ["scoped engineering/systems"],
    },
    "CB7": {
        "status_tokens": [
            "final_A8b=MISSING_OPTIONAL_EXTERNAL_EVIDENCE",
            "cb7=BLOCKED_EXTERNAL_FULLTEXT",
            "stage44_fulltext=BLOCKED",
            "related_fulltext=BLOCKED_FULLTEXT",
            "external_fulltext=MISSING",
        ],
        "policy_tokens": ["Do not cite theorem"],
    },
    "A9": {
        "status_tokens": [
            "final_A9=SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED",
            "stage44_decision=WAIT_EXTERNAL_UNLOCKS",
            "stage41_final=WAIT_UNLOCKS",
        ],
        "policy_tokens": ["SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"],
    },
}

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
    expected = list(range(19, 46))
    return [
        row(
            "S42-ROADMAP-STAGES",
            "roadmap",
            pass_fail(stages == expected),
            ROADMAP.relative_to(ROOT).as_posix(),
            f"observed={stages}; expected={expected}",
            "Restore one Stage 19-45 section per stage before using the roadmap as the active plan.",
        )
    ]


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
            if 19 <= n <= 45:
                stages[n] = stages.get(n, 0) + 1
        if r.get("run_id") == "stage41-external-unlock-packet-001":
            stage41_status = r.get("status", "MISSING")
    missing = [n for n in range(19, 46) if n not in stages]
    ok = not missing and stage41_status == "WAIT_EXTERNAL_EVIDENCE"
    detail = (
        f"stages 19-45 registered; stage41 status={stage41_status}"
        if ok
        else f"missing_stages={missing}; stage41 status={stage41_status}"
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
            "all required Stage 41-45 files exist" if not missing else f"missing={missing}",
            "Restore missing Stage 41-45 control-plane artifacts.",
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
    ]
    missing = [m for m in required_mentions if m not in text]
    return [
        row(
            "S42-ARTIFACT-MANIFEST",
            "reproducibility",
            pass_fail(not missing),
            ARTIFACT_MANIFEST.relative_to(ROOT).as_posix(),
            "Stage 23 flag plus conditional backlog and Stage 41, Stage 43, and Stage 44 artifacts are registered"
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
    checks.append(
        row(
            "S42-OVERALL",
            "overall",
            "PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED" if not failures else "FAIL_EVIDENCE_CLOSURE",
            OUT_CSV.relative_to(ROOT).as_posix(),
            "Stage 19-45 scoped evidence chain is internally closed; stronger claims remain blocked"
            if not failures
            else f"failed_checks={failures}",
            "Fix all failed checks before relying on the Stage 19-45 evidence closure.",
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
        "Stage 42 machine-checks whether the Stage 19-45 PVW/MAT-SAB evidence",
        "chain remains internally consistent. It is a reproducibility and claim",
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
