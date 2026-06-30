#!/usr/bin/env python3
"""Build Stage105 requirement-by-requirement goal-completion audit."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage105_goal_completion_audit"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_REQUIREMENTS = OUT_DIR / "requirement_matrix.csv"
OUT_CLAIM_LIMITS = OUT_DIR / "claim_limit_matrix.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage105_goal_completion_audit.md"

FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
STAGE20 = ROOT / "repro" / "stage20_active_buffer_summary.csv"
STAGE36_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE36_NOISE = ROOT / "repro" / "stage36_target_noise_seeds50" / "aggregate.csv"
STAGE36_RESOURCE = ROOT / "repro" / "stage36_resource_summary.csv"
STAGE42_VERIFY = ROOT / "repro" / "stage42_closure_verify" / "summary.csv"
STAGE97 = ROOT / "repro" / "stage97_source_delta_guard" / "summary.csv"
STAGE101 = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "summary.csv"
STAGE102 = ROOT / "repro" / "stage102_686_source_anchor_review" / "summary.csv"
STAGE103 = ROOT / "repro" / "stage103_related_work_novelty_review" / "summary.csv"
STAGE104 = ROOT / "repro" / "stage104_post_external_final_package" / "summary.csv"
STAGE104_CLAIMS = ROOT / "repro" / "stage104_post_external_final_package" / "claim_boundary.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"
ARTIFACT_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
REPRO_CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def status(path: Path, key: str, value: str, field: str = "status") -> str:
    for row in read_csv(path):
        if row.get(key) == value:
            return row.get(field, "MISSING")
    return "MISSING"


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def stage20_pass() -> bool:
    rows = read_csv(STAGE20)
    profile = [
        row for row in rows
        if row.get("variant") == "active_buffer_profile"
        and row.get("status") == "PASS"
        and row.get("copyback_calls") == "0"
        and row.get("legacy_copyback_calls") == "40"
    ]
    full = [
        row for row in rows
        if row.get("variant") == "active_buffer_full_sab"
        and row.get("status") == "PASS"
        and float(row.get("speedup_min", "0")) > 1.0
    ]
    return len(profile) >= 2 and len(full) >= 2


def stage36_perf_pass() -> bool:
    rows = read_csv(STAGE36_PERF)
    passed = {
        row.get("r") for row in rows
        if row.get("decision") == "PASS_TARGET_PERF_10RUN"
        and int(row.get("samples", "0")) >= 10
        and float(row.get("ci95_low", "0")) > 1.0
    }
    return {"2", "4"}.issubset(passed)


def stage36_noise_pass() -> bool:
    rows = read_csv(STAGE36_NOISE)
    passed = {
        row.get("r") for row in rows
        if row.get("status") == "PASS"
        and int(row.get("seeds", "0")) >= 50
        and row.get("pvw_failures") == "0"
        and row.get("scalar_failures") == "0"
        and row.get("pair_failures") == "0"
    }
    return {"2", "4"}.issubset(passed)


def stage36_resource_pass() -> bool:
    rows = read_csv(STAGE36_RESOURCE)
    expected = {
        ("1", "pvw"),
        ("1", "scalar"),
        ("2", "pvw"),
        ("2", "scalar"),
        ("4", "pvw"),
        ("4", "scalar"),
    }
    passed = {
        (row.get("r"), row.get("mode")) for row in rows
        if row.get("decision") == "PASS_RESOURCE_3RUN"
        and int(row.get("runs", "0")) >= 3
    }
    return expected.issubset(passed)


def build_requirements() -> List[Dict[str, str]]:
    final_a9 = status(FINAL_AUDIT, "item_id", "A9")
    stage97 = status(STAGE97, "gate", "stage97_decision")
    stage101 = status(STAGE101, "gate", "stage101_cb5_decision")
    stage102 = status(STAGE102, "gate", "stage102_decision")
    stage103 = status(STAGE103, "gate", "stage103_decision")
    stage104 = status(STAGE104, "gate", "stage104_decision")
    verifier = status(STAGE42_VERIFY, "check", "stage42_verify_decision")
    rows = [
        {
            "requirement_id": "R1",
            "requirement": "Preserve scalar/default SAB baseline while adding explicit PVW/MAT-SAB paths.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage97 == "PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED" else "MISSING_OR_FAILING",
            "evidence": rel(STAGE97),
            "proof_scope": "Source-delta, symbol, flag, and smoke-evidence guards preserve scalar/default separation.",
            "residual_limit": "Rerun scalar smoke if source/backend/default flags change.",
        },
        {
            "requirement_id": "R2",
            "requirement": "Implement and verify Stage20 active-buffer/copyback fusion.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage20_pass() else "MISSING_OR_FAILING",
            "evidence": f"{rel(STAGE20)}; docs/stage20_active_buffer_log.md",
            "proof_scope": "Profile count gate records copyback 40 -> 0 for r=2/r=4 and full-SAB three-run speedup_min > 1.",
            "residual_limit": "Active-buffer remains explicit/gated, not a default-path proof by itself.",
        },
        {
            "requirement_id": "R3",
            "requirement": "Demonstrate complete-SAB throughput improvement over repeated scalar under same backend.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage36_perf_pass() else "MISSING_OR_FAILING",
            "evidence": rel(STAGE36_PERF),
            "proof_scope": "Target binary SET_2_3_2048 r=2/r=4 have 10-run complete-SAB positive CI95 lower bounds.",
            "residual_limit": "Does not generalize to all parameters, non-binary branches, or default enablement.",
        },
        {
            "requirement_id": "R4",
            "requirement": "Verify correctness/noise for promoted target complete-SAB path.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage36_noise_pass() else "MISSING_OR_FAILING",
            "evidence": rel(STAGE36_NOISE),
            "proof_scope": "Target r=2/r=4 50-seed final-output noise has zero PVW/scalar/pair failures.",
            "residual_limit": "Additional branches still need separate gates.",
        },
        {
            "requirement_id": "R5",
            "requirement": "Record resource/key/keygen overhead for scalar and PVW comparison.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage36_resource_pass() else "MISSING_OR_FAILING",
            "evidence": rel(STAGE36_RESOURCE),
            "proof_scope": "Scalar/PVW r=1/2/4 3-run resource matrix is present and passing.",
            "residual_limit": "Use reported overheads with throughput claims; do not omit key/memory costs.",
        },
        {
            "requirement_id": "R6",
            "requirement": "Resolve native perf/counter attribution blocker where claimed.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage101 == "PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED" else "MISSING_OR_FAILING",
            "evidence": rel(STAGE101),
            "proof_scope": "Native Linux perf evidence records complete-SAB correctness plus retired load/store and AVX512 FP counters.",
            "residual_limit": "Counter evidence is attribution-only; theoretical optimality still requires model/assembly proof.",
        },
        {
            "requirement_id": "R7",
            "requirement": "Resolve 2025/686 source-anchor review for scoped protocol/citation claims.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage102 == "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED" else "MISSING_OR_FAILING",
            "evidence": rel(STAGE102),
            "proof_scope": "All Stage38 checklist rows have reviewed 2025/686 anchors and claim limits.",
            "residual_limit": "Do not use 2025/686 anchors as proof that the original paper proposed the local PVW/MAT path.",
        },
        {
            "requirement_id": "R8",
            "requirement": "Resolve related-work/novelty review without overclaiming.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage103 == "PASS_STAGE103_RELATED_WORK_NOVELTY_REVIEW_SCOPED" else "MISSING_OR_FAILING",
            "evidence": rel(STAGE103),
            "proof_scope": "Real-source novelty matrix allows scoped systems wording and rejects broad shared-mask/batch/asymptotic novelty.",
            "residual_limit": "Broad novelty, all-parameter, non-binary, and new theorem claims remain blocked.",
        },
        {
            "requirement_id": "R9",
            "requirement": "Assemble current post-external final scoped package.",
            "status": "PROVEN_SCOPED_COMPLETE" if stage104 == "PASS_STAGE104_POST_EXTERNAL_FINAL_PACKAGE_REFRESHED_SCOPED" else "MISSING_OR_FAILING",
            "evidence": rel(STAGE104),
            "proof_scope": "Stage104 bridges Stage91 performance/noise/resource evidence with Stage101-103 external-review evidence.",
            "residual_limit": "Stage104 does not rerun heavy benchmarks and does not upgrade claim scope.",
        },
        {
            "requirement_id": "R10",
            "requirement": "Maintain reproducible, auditable evidence chain.",
            "status": "PROVEN_SCOPED_COMPLETE"
            if verifier == "PASS_STAGE42_VERIFY_STRONGER_CLAIMS_BLOCKED"
            and final_a9 == "SCOPED_ENGINEERING_CHAIN_READY__EXTERNAL_REVIEWED_STRONGER_CLAIMS_SCOPED"
            else "MISSING_OR_FAILING",
            "evidence": f"{rel(STAGE42_VERIFY)}; {rel(FINAL_AUDIT)}; {rel(RUN_LOG)}; {rel(ARTIFACT_MANIFEST)}; {rel(REPRO_CHECKLIST)}",
            "proof_scope": "Stage42 verifier passes from a clean input state and final audit records scoped-reviewed A9 status.",
            "residual_limit": "Any new source/backend/claim-scope change must regenerate the pack.",
        },
    ]
    return rows


def build_claim_limits() -> List[Dict[str, str]]:
    claims = read_csv(STAGE104_CLAIMS)
    rows = []
    for claim in claims:
        rows.append(
            {
                "claim_id": claim.get("claim_id", ""),
                "status": claim.get("status", ""),
                "allowed_wording": claim.get("allowed_wording", ""),
                "blocked_wording": claim.get("blocked_wording", ""),
                "evidence": claim.get("evidence", ""),
            }
        )
    return rows


def upsert_run_log(decision: str) -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != "stage105-goal-completion-audit-001"]
    rows.append(
        {
            "run_id": "stage105-goal-completion-audit-001",
            "date": "2026-06-30",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 105",
            "backend": "n/a",
            "command": "python scripts/build_stage105_goal_completion_audit.py",
            "params": "requirement-by-requirement scoped goal completion audit",
            "seed": "audit",
            "status": decision,
            "summary": "Stage105 maps the active PVW/MAT-SAB goal to current evidence and records that the scoped systems/engineering SAB acceleration evidence chain is complete while stronger claims remain blocked by explicit claim limits.",
            "artifacts": "docs/stage105_goal_completion_audit.md; experiments/stage105_goal_completion_audit_plan.md; scripts/build_stage105_goal_completion_audit.py; repro/stage105_goal_completion_audit/summary.csv; repro/stage105_goal_completion_audit/requirement_matrix.csv; repro/stage105_goal_completion_audit/claim_limit_matrix.csv; repro/stage105_goal_completion_audit/artifact_index.csv",
        }
    )
    write_csv(RUN_LOG, rows, fields)


def write_md(summary_rows: List[Dict[str, str]], requirements: List[Dict[str, str]], claim_limits: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    lines = [
        "# Stage105 Goal Completion Audit",
        "",
        "Date: 2026-06-30",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage105 audits the active PVW/MAT-SAB goal requirement by requirement.",
        "It treats the completed goal as scoped systems/engineering evidence,",
        "not as unrestricted novelty, all-parameter, non-binary, or theoretical",
        "optimality evidence.",
        "",
        "## Summary",
        "",
        "| gate | status | detail |",
        "|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(f"| {row['gate']} | {row['status']} | {row['detail']} |")
    lines.extend(["", "## Requirements", "", "| id | status | requirement | proof scope | residual limit |", "|---|---|---|---|---|"])
    for row in requirements:
        lines.append(
            f"| {row['requirement_id']} | {row['status']} | {row['requirement']} | {row['proof_scope']} | {row['residual_limit']} |"
        )
    lines.extend(["", "## Claim Limits", "", "| claim | status | allowed | blocked |", "|---|---|---|---|"])
    for row in claim_limits:
        lines.append(
            f"| {row['claim_id']} | {row['status']} | {row['allowed_wording']} | {row['blocked_wording']} |"
        )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    requirements = build_requirements()
    claim_limits = build_claim_limits()
    missing = [row["requirement_id"] for row in requirements if row["status"] != "PROVEN_SCOPED_COMPLETE"]
    broad_claims_blocked = all(
        "blocked" in row.get("status", "").lower()
        or "NOT_OPTIMALITY" in row.get("status", "")
        or row.get("claim_id") in {"C1", "C2", "C5"}
        for row in claim_limits
    )
    decision = (
        "PASS_STAGE105_SCOPED_GOAL_COMPLETE_STRONGER_CLAIMS_BLOCKED"
        if not missing and broad_claims_blocked
        else "FAIL_STAGE105_GOAL_COMPLETION_AUDIT"
    )
    summary_rows = [
        {
            "gate": "stage105_requirement_coverage",
            "status": "PASS" if not missing else "FAIL",
            "evidence": rel(OUT_REQUIREMENTS),
            "detail": "all scoped goal requirements have direct evidence" if not missing else f"missing={missing}",
            "next_action": "Fill missing evidence before treating the scoped goal as complete.",
        },
        {
            "gate": "stage105_claim_limit_guard",
            "status": "PASS" if broad_claims_blocked else "FAIL",
            "evidence": rel(OUT_CLAIM_LIMITS),
            "detail": "stronger claims remain explicitly bounded",
            "next_action": "Restore claim limits before reporting Stage105 completion.",
        },
        {
            "gate": "stage105_decision",
            "status": decision,
            "evidence": rel(OUT_SUMMARY),
            "detail": "Scoped PVW/MAT-SAB evidence chain is complete; stronger claims remain blocked."
            if decision.startswith("PASS_")
            else "Scoped completion is not yet proven.",
            "next_action": "Use Stage105 as the completion audit until source/backend/claim scope changes.",
        },
    ]
    write_csv(
        OUT_REQUIREMENTS,
        requirements,
        ["requirement_id", "requirement", "status", "evidence", "proof_scope", "residual_limit"],
    )
    write_csv(
        OUT_CLAIM_LIMITS,
        claim_limits,
        ["claim_id", "status", "allowed_wording", "blocked_wording", "evidence"],
    )
    write_csv(
        OUT_SUMMARY,
        summary_rows,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_md(summary_rows, requirements, claim_limits)
    write_csv(
        OUT_INDEX,
        artifact_index([OUT_SUMMARY, OUT_REQUIREMENTS, OUT_CLAIM_LIMITS, OUT_MD]),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    upsert_run_log(decision)
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_REQUIREMENTS)}")
    print(f"Wrote {rel(OUT_CLAIM_LIMITS)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage105 goal completion audit: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
