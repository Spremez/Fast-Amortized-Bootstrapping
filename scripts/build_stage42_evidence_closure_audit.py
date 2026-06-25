#!/usr/bin/env python3
"""Build the Stage 42 evidence-closure audit.

This script checks whether the current scoped PVW/MAT-SAB evidence chain is
internally consistent through Stage 43. It does not run benchmarks or upgrade
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

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
LOOP = ROOT / "docs" / "loop_engineering.md"
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"
FREEZE_MANIFEST = ROOT / "repro" / "stage40_final_freeze_manifest.csv"
POSTFREEZE = ROOT / "repro" / "stage40_postfreeze_verify" / "summary.csv"
STAGE41 = ROOT / "repro" / "stage41_external_unlock_packet.csv"
STAGE43_SMOKE = ROOT / "repro" / "stage43_current_smoke_after_stage42" / "summary.csv"
ARTIFACT_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
REPRO_CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"


EXPECTED_AUDIT_STATUS = {
    "A1": "PASS_SCOPED",
    "A2": "PASS_SCOPED",
    "A2b": "PASS_10RUN_TARGET_PERF",
    "A3": "PASS_SCOPED",
    "A3b": "PASS_STAGE_NOISE_10SEED",
    "A4": "PASS_SMOKE_RESOURCE",
    "A4b": "PASS_RESOURCE_3RUN",
    "A5": "PASS_SCOPED",
    "A5b": "PASS_CURRENT_SMOKE",
    "A6": "PASS_BLOCKED_BOUNDARY",
    "A7": "PASS_SMALL_SAMPLE",
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

REQUIRED_FILES = [
    "docs/goal_sab_max_acceleration.md",
    "docs/roadmap_stage19_plus.md",
    "docs/loop_engineering.md",
    "docs/stage41_external_unlock_packet.md",
    "experiments/stage41_external_unlock_plan.md",
    "scripts/build_stage41_external_unlock_packet.py",
    "scripts/build_stage42_evidence_closure_audit.py",
    "repro/stage41_external_unlock_packet.csv",
    "docs/stage43_postclosure_current_smoke_log.md",
    "experiments/stage43_postclosure_current_smoke_plan.md",
    "repro/stage43_current_smoke_after_stage42/summary.csv",
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


def check_roadmap() -> List[Dict[str, str]]:
    text = ROADMAP.read_text(encoding="utf-8") if ROADMAP.exists() else ""
    stages = sorted({int(m.group(1)) for m in re.finditer(r"^## Stage (\d+):", text, re.M)})
    expected = list(range(19, 44))
    return [
        row(
            "S42-ROADMAP-STAGES",
            "roadmap",
            pass_fail(stages == expected),
            ROADMAP.relative_to(ROOT).as_posix(),
            f"observed={stages}; expected={expected}",
            "Restore one Stage 19-43 section per stage before using the roadmap as the active plan.",
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
            if 19 <= n <= 43:
                stages[n] = stages.get(n, 0) + 1
        if r.get("run_id") == "stage41-external-unlock-packet-001":
            stage41_status = r.get("status", "MISSING")
    missing = [n for n in range(19, 44) if n not in stages]
    ok = not missing and stage41_status == "WAIT_EXTERNAL_EVIDENCE"
    detail = (
        f"stages 19-43 registered; stage41 status={stage41_status}"
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
            "all required Stage 41-43 files exist" if not missing else f"missing={missing}",
            "Restore missing Stage 41-43 control-plane artifacts.",
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
    ]
    missing = [m for m in required_mentions if m not in text]
    return [
        row(
            "S42-ARTIFACT-MANIFEST",
            "reproducibility",
            pass_fail(not missing),
            ARTIFACT_MANIFEST.relative_to(ROOT).as_posix(),
            "Stage 23 flag plus Stage 41 and Stage 43 artifacts are registered"
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
        check_freeze_manifest,
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
            "Stage 19-43 scoped evidence chain is internally closed; stronger claims remain blocked"
            if not failures
            else f"failed_checks={failures}",
            "Fix all failed checks before relying on the Stage 19-43 evidence closure.",
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
        "Stage 42 machine-checks whether the Stage 19-43 PVW/MAT-SAB evidence",
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
