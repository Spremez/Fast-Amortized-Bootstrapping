#!/usr/bin/env python3
"""Build Stage150 final package refresh for the MAT-RLWE/PVW-SAB goal."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]

STAGE148 = ROOT / "repro" / "stage148_h14_r6_repeated_refresh"
STAGE149 = ROOT / "repro" / "stage149_h14_r6_claim_policy"
OUT_DIR = ROOT / "repro" / "stage150_final_package_refresh"

SUMMARY_CSV = OUT_DIR / "summary.csv"
CLAIMS_CSV = OUT_DIR / "claim_table.csv"
EVIDENCE_CSV = OUT_DIR / "evidence_matrix.csv"
BLOCKERS_CSV = OUT_DIR / "blocker_matrix.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage150_final_package_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage150_final_package_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage150_claim_scope_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage150_final_scope.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
STAGE91_MD = ROOT / "docs" / "stage91_final_sab_optimization_package.md"
FINAL_AUDIT_MD = ROOT / "docs" / "final_goal_completion_audit.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
CLAIM_FIELDS = [
    "claim_id",
    "claim_type",
    "status",
    "metric",
    "scope",
    "allowed_wording",
    "blocked_wording",
    "evidence",
]
EVIDENCE_FIELDS = [
    "evidence_id",
    "source",
    "status",
    "metric",
    "value",
    "interpretation",
]
BLOCKER_FIELDS = [
    "blocker_id",
    "status",
    "blocking_condition",
    "required_next_evidence",
    "claim_policy",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def status_by_gate(rows: List[Dict[str, str]], gate: str) -> str:
    for row in rows:
        if row.get("gate") == gate:
            return row.get("status", "")
    return "MISSING"


def first(rows: List[Dict[str, str]]) -> Dict[str, str]:
    return rows[0] if rows else {}


def as_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_tables() -> tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    s148 = read_csv(STAGE148 / "summary.csv")
    perf = first(read_csv(STAGE148 / "perf_comparison.csv"))
    noise = first(read_csv(STAGE148 / "noise_aggregate.csv"))
    resource = first(read_csv(STAGE148 / "resource_comparison.csv"))
    s149 = read_csv(STAGE149 / "summary.csv")
    policy = first(read_csv(STAGE149 / "claim_policy.csv"))

    stage148_decision = status_by_gate(s148, "stage148_decision")
    stage149_decision = status_by_gate(s149, "stage149_decision")
    perf_status = status_by_gate(s148, "stage148_perf")
    noise_status = noise.get("status", "MISSING")
    resource_status = resource.get("status", "MISSING")
    metric_ok = perf.get("metric") == "T_bootstrap_per_lane"
    policy_ok = policy.get("engineering_claim_policy") == "ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM"
    default_ok = policy.get("default_path_policy") == "KEEP_DEFAULT_UNCHANGED_EXPLICIT_FLAG_ONLY"
    novelty_ok = policy.get("paper_novelty_policy") == "DISALLOW_PAPER_NOVELTY_OR_THEORETICAL_OPTIMALITY_CLAIM"

    pass_refresh = (
        stage148_decision == "PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE"
        and stage149_decision == "PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT"
        and perf_status == "PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE"
        and noise_status == "PASS"
        and resource_status == "PASS"
        and metric_ok
        and policy_ok
        and default_ok
        and novelty_ok
    )
    decision = (
        "PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED"
        if pass_refresh
        else "FAIL_STAGE150_FINAL_PACKAGE_REFRESH_REPAIR_REQUIRED"
    )
    next_action = (
        "Stage151 should choose a new optimization branch only after preserving this scoped claim ledger."
        if pass_refresh
        else "Repair Stage148/149 evidence or policy before updating final wording."
    )

    evidence = [
        {
            "evidence_id": "E150_metric",
            "source": rel(STAGE148 / "perf_comparison.csv"),
            "status": "PASS" if metric_ok else "FAIL",
            "metric": "primary_endpoint",
            "value": perf.get("metric", "MISSING"),
            "interpretation": "Speedup is evaluated as complete bootstrapping time divided by processed MAT-RLWE body lanes.",
        },
        {
            "evidence_id": "E150_perf_backend_vs_scalar",
            "source": rel(STAGE148 / "perf_comparison.csv"),
            "status": perf_status,
            "metric": "backend_mean_speedup_vs_repeated_scalar",
            "value": perf.get("backend_mean_speedup_vs_scalar", ""),
            "interpretation": "This is the current explicit-path complete-SAB per-lane throughput result.",
        },
        {
            "evidence_id": "E150_perf_backend_vs_wrapper",
            "source": rel(STAGE148 / "perf_comparison.csv"),
            "status": perf_status,
            "metric": "backend_vs_wrapper_mean_speedup",
            "value": perf.get("backend_vs_wrapper_mean_speedup", ""),
            "interpretation": "This isolates the incremental backend FromDFT-add route over the wrapper fused reference.",
        },
        {
            "evidence_id": "E150_perf_ci_low",
            "source": rel(STAGE148 / "perf_comparison.csv"),
            "status": "PASS" if as_float(perf.get("backend_vs_wrapper_ci95_low", "0")) > 1.0 else "REVIEW",
            "metric": "backend_vs_wrapper_ci95_low",
            "value": perf.get("backend_vs_wrapper_ci95_low", ""),
            "interpretation": "The repeated backend-vs-wrapper lower confidence bound remains above one in Stage148.",
        },
        {
            "evidence_id": "E150_noise",
            "source": rel(STAGE148 / "noise_aggregate.csv"),
            "status": noise_status,
            "metric": "r6_noise_failures",
            "value": f"pvw={noise.get('pvw_failures', '')}; scalar={noise.get('scalar_failures', '')}; pair={noise.get('pair_failures', '')}",
            "interpretation": "The current r=6 refresh records zero final-output failures across the recorded seeds.",
        },
        {
            "evidence_id": "E150_resource_key",
            "source": rel(STAGE148 / "resource_comparison.csv"),
            "status": resource_status,
            "metric": "key_bytes_ratio",
            "value": resource.get("key_bytes_ratio", ""),
            "interpretation": "Key-size overhead is reported with the throughput result.",
        },
        {
            "evidence_id": "E150_resource_rss",
            "source": rel(STAGE148 / "resource_comparison.csv"),
            "status": resource_status,
            "metric": "vmhwm_ratio",
            "value": resource.get("vmhwm_ratio", ""),
            "interpretation": "Peak resident memory overhead is reported with the throughput result.",
        },
        {
            "evidence_id": "E150_policy",
            "source": rel(STAGE149 / "claim_policy.csv"),
            "status": stage149_decision,
            "metric": "claim_policy",
            "value": policy.get("engineering_claim_policy", ""),
            "interpretation": "Allowed wording is scoped to the explicit H14 r=6 engineering path, not default or novelty claims.",
        },
    ]

    claims = [
        {
            "claim_id": "C150_allowed_main",
            "claim_type": "complete_sab_engineering",
            "status": "ALLOW_SCOPED_EXPLICIT_ENGINEERING_CLAIM" if pass_refresh else "BLOCKED",
            "metric": "T_bootstrap/r",
            "scope": "BINARY SET_2_3_2048, r=6, spqlios_avx512, explicit H14 backend FromDFT-add path",
            "allowed_wording": "The explicit MAT-RLWE/PVW-SAB H14 r=6 path improves complete SAB per-lane throughput over repeated scalar SAB under the recorded target backend and parameter set.",
            "blocked_wording": "Default SAB path is faster, all parameters are faster, or the method is theoretically optimal.",
            "evidence": f"{rel(STAGE148 / 'perf_comparison.csv')}; {rel(STAGE149 / 'claim_policy.csv')}",
        },
        {
            "claim_id": "C150_amortized_metric",
            "claim_type": "metric_definition",
            "status": "ALLOW",
            "metric": "T_complete_bootstrap(r)/r",
            "scope": "r independent LUT/SAB body lanes in one MAT-RLWE/PVW run",
            "allowed_wording": "Comparison to scalar SAB is amortized by the number of processed plaintext bits or LUT lanes.",
            "blocked_wording": "Raw total time alone proves the MAT-RLWE SAB advantage.",
            "evidence": rel(STAGE148 / "perf_comparison.csv"),
        },
        {
            "claim_id": "C150_backend_delta",
            "claim_type": "backend_attribution",
            "status": "ALLOW_SCOPED_ENGINEERING_ATTRIBUTION" if pass_refresh else "BLOCKED",
            "metric": "backend_vs_wrapper_mean_speedup",
            "scope": "current-head r=6 wrapper fused reference versus backend FromDFT-add",
            "allowed_wording": "The backend FromDFT-add route adds about the recorded incremental improvement over the wrapper fused path.",
            "blocked_wording": "The incremental backend result is an independent algorithmic complexity improvement.",
            "evidence": rel(STAGE148 / "perf_comparison.csv"),
        },
        {
            "claim_id": "C150_noise_resource",
            "claim_type": "validity_guard",
            "status": "ALLOW_REPORTED_WITH_CLAIM" if pass_refresh else "BLOCKED",
            "metric": "failures; key_bytes_ratio; vmhwm_ratio",
            "scope": "Stage148 r=6 noise/resource refresh",
            "allowed_wording": "The throughput result is reported together with zero recorded final-output failures and measured key/memory overheads.",
            "blocked_wording": "The performance result is presented without resource or noise cost.",
            "evidence": f"{rel(STAGE148 / 'noise_aggregate.csv')}; {rel(STAGE148 / 'resource_comparison.csv')}",
        },
        {
            "claim_id": "C150_novelty_optimality",
            "claim_type": "paper_claim_guard",
            "status": "BLOCK_STRONGER_CLAIM",
            "metric": "novelty; theoretical optimality",
            "scope": "paper-level claim boundary",
            "allowed_wording": "This is a scoped systems/engineering result unless a later literature and proof gate upgrades it.",
            "blocked_wording": "PVW/MAT-SAB is novel, universally optimal, or reaches the r-body theoretical optimum.",
            "evidence": rel(STAGE149 / "claim_policy.csv"),
        },
    ]

    blockers = [
        {
            "blocker_id": "B150_default_promotion",
            "status": "BLOCKED",
            "blocking_condition": "Explicit flags remain default-false by policy.",
            "required_next_evidence": "Separate default-promotion gate with scalar/default smoke, repeated full-SAB A/B, and rollback policy.",
            "claim_policy": "Do not state default-path speedup.",
        },
        {
            "blocker_id": "B150_theoretical_optimality",
            "status": "BLOCKED",
            "blocking_condition": "No lower-bound proof showing the current dense/closed MAT route is optimal for r-body SAB.",
            "required_next_evidence": "Formal lower-bound gap model plus counter evidence for the promoted kernel and complete-SAB A/B.",
            "claim_policy": "Do not state theoretical optimality.",
        },
        {
            "blocker_id": "B150_generalization",
            "status": "BLOCKED",
            "blocking_condition": "Latest H14 r=6 claim is only for the recorded binary target and backend.",
            "required_next_evidence": "Repeated performance/noise/resource matrix across additional parameters and supported ternary/include-zero branches.",
            "claim_policy": "Do not state all-parameter or non-binary speedup.",
        },
        {
            "blocker_id": "B150_novelty",
            "status": "BLOCKED",
            "blocking_condition": "Stage149 policy disallows paper-level novelty from current engineering evidence alone.",
            "required_next_evidence": "Reviewed related-work matrix and exact claim comparison against real sources for the final algorithm statement.",
            "claim_policy": "Do not write novelty claims until a later literature gate upgrades them.",
        },
        {
            "blocker_id": "B150_next_code_target",
            "status": "OPEN",
            "blocking_condition": "Stage150 is a package refresh, not a new hot-path optimization.",
            "required_next_evidence": "Stage151 must pick one implementation branch with a falsifiable expected effect on T_bootstrap/r.",
            "claim_policy": "Continue implementation only through gated research-loop stages.",
        },
    ]

    summary = [
        {
            "gate": "stage150_precondition",
            "status": "PASS" if stage149_decision == "PASS_STAGE149_H14_R6_EXPLICIT_PROMOTION_POLICY_RECORDED_NOT_DEFAULT" else "FAIL",
            "metric": "stage149_decision",
            "value": stage149_decision,
            "evidence": rel(STAGE149 / "summary.csv"),
            "detail": "Stage150 can refresh final wording only after Stage149 records claim policy.",
            "next_action": "",
        },
        {
            "gate": "stage150_metric_guard",
            "status": "PASS" if metric_ok else "FAIL",
            "metric": "primary_endpoint",
            "value": perf.get("metric", "MISSING"),
            "evidence": rel(STAGE148 / "perf_comparison.csv"),
            "detail": "Final performance wording must use amortized complete-SAB T_bootstrap/r.",
            "next_action": "Do not use raw total time as the main speedup claim.",
        },
        {
            "gate": "stage150_stats_guard",
            "status": "PASS" if perf_status == "PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE" and noise_status == "PASS" and resource_status == "PASS" else "FAIL",
            "metric": "perf;noise;resource",
            "value": f"{perf_status};{noise_status};{resource_status}",
            "evidence": f"{rel(STAGE148 / 'perf_comparison.csv')}; {rel(STAGE148 / 'noise_aggregate.csv')}; {rel(STAGE148 / 'resource_comparison.csv')}",
            "detail": "Performance, final-output noise, and resource overhead are interpreted together.",
            "next_action": "",
        },
        {
            "gate": "stage150_claim_guard",
            "status": "PASS" if policy_ok and default_ok and novelty_ok else "FAIL",
            "metric": "claim_policy",
            "value": f"{policy.get('engineering_claim_policy', '')};{policy.get('default_path_policy', '')};{policy.get('paper_novelty_policy', '')}",
            "evidence": rel(STAGE149 / "claim_policy.csv"),
            "detail": "The final package permits scoped explicit-path engineering wording only.",
            "next_action": "Keep stronger claims in the blocker matrix.",
        },
        {
            "gate": "stage150_decision",
            "status": decision,
            "metric": "final_package_refresh",
            "value": "scoped_explicit_h14_r6" if pass_refresh else "repair_required",
            "evidence": f"{rel(CLAIMS_CSV)}; {rel(EVIDENCE_CSV)}; {rel(BLOCKERS_CSV)}",
            "detail": "Stage150 refreshes the final package without changing scalar/default SAB behavior.",
            "next_action": next_action,
        },
    ]
    return summary, claims, evidence, blockers


def write_docs(
    summary: List[Dict[str, str]],
    claims: List[Dict[str, str]],
    evidence: List[Dict[str, str]],
    blockers: List[Dict[str, str]],
) -> None:
    decision = status_by_gate(summary, "stage150_decision")
    perf = first(read_csv(STAGE148 / "perf_comparison.csv"))
    noise = first(read_csv(STAGE148 / "noise_aggregate.csv"))
    resource = first(read_csv(STAGE148 / "resource_comparison.csv"))

    write_text_lf(PLAN_MD, "\n".join([
        "# Stage150 Final Package Refresh Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Refresh the final PVW/MAT-SAB package so that the current claim boundary matches Stage148/149 evidence.",
        "",
        "## Research Loop",
        "",
        "1. Declare primary endpoint before interpretation: `T_complete_bootstrap(r)/r`.",
        "2. Bind every claim to a source CSV, run stage, backend, parameter set, and policy gate.",
        "3. Preserve negative boundaries: no default-path, novelty, all-parameter, or theoretical-optimality wording.",
        "4. Record blockers so the next implementation stage has a concrete gate instead of a theory loop.",
    ]) + "\n")

    write_text_lf(THEORY_MD, "\n".join([
        "# Stage150 Claim Scope Model",
        "",
        "Date: 2026-07-03",
        "",
        "## Amortized Comparison",
        "",
        "The intended MAT-RLWE/PVW-SAB comparison is not raw runtime. A scalar baseline that processes `r` independent LUT or SAB lanes costs `r * T_scalar` and the MAT-RLWE path costs `T_mat(r)`. The primary endpoint is therefore:",
        "",
        "```text",
        "speedup(r) = T_scalar / (T_mat(r) / r) = r * T_scalar / T_mat(r)",
        "```",
        "",
        "This is the same unit as time per processed plaintext bit or LUT lane.",
        "",
        "## Why The Speedup Is Not Automatically r",
        "",
        "The MAT-RLWE ciphertext has one shared mask and `r` body lanes, so it can share decomposition, selector, and mask-side work across lanes. However the closed dense MAT path still carries row/output interactions, DFT materialization, body updates, memory traffic, key size, and register-pressure costs. Those costs make the practical optimum a measured point on the `T_mat(r)/r` curve, not a free factor-r result.",
        "",
        "## Current Evidence Boundary",
        "",
        f"Stage148 reports r=6 backend mean speedup versus repeated scalar `{perf.get('backend_mean_speedup_vs_scalar', '')}` under `{perf.get('metric', '')}`, with backend-vs-wrapper mean `{perf.get('backend_vs_wrapper_mean_speedup', '')}` and CI low `{perf.get('backend_vs_wrapper_ci95_low', '')}`.",
        f"Noise/resource side conditions are recorded as failures `pvw={noise.get('pvw_failures', '')}, scalar={noise.get('scalar_failures', '')}, pair={noise.get('pair_failures', '')}`, key bytes ratio `{resource.get('key_bytes_ratio', '')}`, and VmHWM ratio `{resource.get('vmhwm_ratio', '')}`.",
        "",
        "Thus the allowed claim is scoped engineering acceleration for an explicit path. Theoretical optimality remains unproved.",
    ]) + "\n")

    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE/PVW-SAB Stage150 Final Scope",
        "",
        "Date: 2026-07-03",
        "",
        "## Algorithm Object",
        "",
        "The current promoted object is not a replacement for scalar `sab_rlwe_bootstrap`. It is an explicit `sab_pvw_*` H14 r=6 path with:",
        "",
        "- `r=6` independent LUT/SAB body lanes packed into one MAT-RLWE/PVW state;",
        "- shared-mask external-product processing;",
        "- active-buffer sparse-schedule state;",
        "- backend FromDFT-add materialization;",
        "- default-false flags and scalar/default isolation.",
        "",
        "## Comparison Unit",
        "",
        "`T_complete_bootstrap(6)/6` is compared against repeated scalar SAB per lane.",
        "",
        "## Current Non-Goals",
        "",
        "Stage150 does not promote default behavior, does not prove an r-body lower bound, and does not claim novelty.",
    ]) + "\n")

    write_text_lf(OUT_MD, "\n".join([
        "# Stage150 Final Package Refresh",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## What This Fixes",
        "",
        "Stage150 refreshes the final package around the actual MAT-RLWE/PVW-SAB metric: complete bootstrapping time divided by the number of processed body lanes. The latest allowed result is a scoped explicit-path engineering claim for H14 r=6, not a default-path or paper-level novelty claim.",
        "",
        "## Summary Gates",
        "",
        table(summary, ["gate", "status", "metric", "value", "detail", "next_action"]),
        "",
        "## Claims",
        "",
        table(claims, CLAIM_FIELDS),
        "",
        "## Evidence Matrix",
        "",
        table(evidence, EVIDENCE_FIELDS),
        "",
        "## Blocker Matrix",
        "",
        table(blockers, BLOCKER_FIELDS),
        "",
        "## Current Numerical Result",
        "",
        f"- Primary endpoint: `{perf.get('metric', '')}`.",
        f"- H14 r=6 backend per-lane speedup over repeated scalar: `{perf.get('backend_mean_speedup_vs_scalar', '')}`.",
        f"- Backend route over wrapper fused reference: mean `{perf.get('backend_vs_wrapper_mean_speedup', '')}`, min `{perf.get('backend_vs_wrapper_min_speedup', '')}`, CI95 low `{perf.get('backend_vs_wrapper_ci95_low', '')}`, CI95 high `{perf.get('backend_vs_wrapper_ci95_high', '')}`.",
        f"- Noise failures: PVW `{noise.get('pvw_failures', '')}`, scalar `{noise.get('scalar_failures', '')}`, paired `{noise.get('pair_failures', '')}`.",
        f"- Resource ratios: key bytes `{resource.get('key_bytes_ratio', '')}`, VmHWM `{resource.get('vmhwm_ratio', '')}`, time max RSS `{resource.get('time_max_rss_ratio', '')}`.",
        "",
        "## Next Implementation Rule",
        "",
        "The next code stage must choose one falsifiable hot-path change and rerun the same correctness, amortized performance, noise/resource, and claim-policy gates. It must not start from a new theory claim unless the claim has a measurable effect on `T_complete_bootstrap(r)/r`.",
    ]) + "\n")


def update_longform(summary: List[Dict[str, str]]) -> None:
    decision = status_by_gate(summary, "stage150_decision")
    perf = first(read_csv(STAGE148 / "perf_comparison.csv"))
    resource = first(read_csv(STAGE148 / "resource_comparison.csv"))
    block = f"""
## Stage 150: Final Package Refresh

Goal:

```text
Refresh the final package around the MAT-RLWE/PVW-SAB amortized endpoint
T_complete_bootstrap(r)/r and the Stage148/149 explicit H14 r=6 evidence.
```

Status:

```text
Completed. Stage150 records {decision}. The current allowed claim is scoped to
the explicit H14 r=6 backend path. It reports backend-versus-repeated-scalar
speedup {perf.get('backend_mean_speedup_vs_scalar', '')} under
T_bootstrap/r, key bytes ratio {resource.get('key_bytes_ratio', '')}, and
VmHWM ratio {resource.get('vmhwm_ratio', '')}. Default-path, all-parameter,
novelty, and theoretical-optimality claims remain blocked.
```
"""
    append_once(ROADMAP_MD, "## Stage 150: Final Package Refresh", block)
    append_once(GOAL_MD, "Stage150 refreshes the final package", f"""
Stage150 refreshes the final package around the correct MAT-RLWE/PVW-SAB
metric: `T_complete_bootstrap(r)/r`, equivalent to time per processed
plaintext bit or LUT/SAB lane. The current scoped explicit H14 r=6 backend
result is {perf.get('backend_mean_speedup_vs_scalar', '')}x versus repeated
scalar SAB per lane under Stage148, with Stage149 keeping default-path,
novelty, and theoretical-optimality claims blocked.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage150 as the final-package refresh gate", f"""
54. Treat Stage150 as the final-package refresh gate:
    `{decision}`. It fixes the comparison dimension to
    `T_complete_bootstrap(r)/r` and records the current scoped H14 r=6
    explicit-path result. The next valid stage must pick a concrete
    implementation candidate and verify it against the same amortized endpoint.
""")
    append_once(STAGE91_MD, "## Stage150 Current-Head Refresh", f"""
## Stage150 Current-Head Refresh

Stage150 supersedes the older r=6 wording with the current Stage148/149
evidence. The primary endpoint is `T_complete_bootstrap(r)/r`, not raw total
runtime. For the explicit H14 r=6 backend path, Stage148 reports
{perf.get('backend_mean_speedup_vs_scalar', '')}x per-lane speedup over
repeated scalar SAB and Stage149 allows only scoped explicit engineering
wording. Default-path, all-parameter, novelty, and theoretical-optimality
claims remain blocked.
""")
    append_once(FINAL_AUDIT_MD, "## Stage150 Current Claim Refresh", f"""
## Stage150 Current Claim Refresh

Stage150 refreshes the current claim ledger after Stage148/149. The scoped
engineering chain remains evidence-backed only for the recorded explicit H14
r=6 path under `T_complete_bootstrap(r)/r`. It does not upgrade default-path,
generalization, novelty, or theoretical-optimality wording.
""")
    append_once(HYPOTHESIS_YAML, "H74_stage150_final_package_refresh", f"""
  - id: H74_stage150_final_package_refresh
    statement: >
      The final PVW/MAT-SAB evidence package must be refreshed around the
      amortized MAT-RLWE endpoint T_complete_bootstrap(r)/r before any further
      implementation or paper claim is promoted.
    mechanism: >
      Stage148 supplies current r=6 repeated performance/noise/resource
      evidence, and Stage149 supplies the explicit-path claim policy. Stage150
      binds these to allowed wording, blocked wording, and next-stage gates.
    status: stage150_final_package_refresh
    evidence: docs/stage150_final_package_refresh.md; experiments/stage150_final_package_refresh_plan.md; theory_checks/stage150_claim_scope_model.md; scripts/build_stage150_final_package_refresh.py; repro/stage150_final_package_refresh/summary.csv; repro/stage150_final_package_refresh/claim_table.csv
    current_decision: >
      {decision}
    failure_criteria:
      - raw total runtime is used as the main speedup metric
      - explicit-path evidence is written as default-path or all-parameter speedup
      - engineering evidence is written as novelty or theoretical optimality
""")


def update_repro(summary: List[Dict[str, str]]) -> None:
    decision = status_by_gate(summary, "stage150_decision")
    existing = read_csv(RUN_LOG)
    run_fields = list(existing[0].keys()) if existing else [
        "run_id", "date", "commit_or_state", "stage", "backend", "command",
        "params", "seed", "status", "summary", "artifacts",
    ]
    base_row = {field: "" for field in run_fields}
    base_row.update({
        "run_id": "stage150-final-package-refresh-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "Stage 150",
        "backend": "package refresh",
        "command": "python scripts/build_stage150_final_package_refresh.py",
        "params": "reads Stage148 repeated/noise/resource and Stage149 claim-policy evidence; primary endpoint T_bootstrap/r",
        "seed": "n/a",
        "status": decision,
        "summary": "Current final package refresh for scoped explicit H14 r=6 MAT-RLWE/PVW-SAB claim.",
        "artifacts": rel(OUT_DIR),
    })
    run_row = {field: base_row.get(field, "") for field in run_fields}
    existing = [
        row for row in existing
        if row.get("run_id") != run_row["run_id"]
        and row.get("stage") != run_row["stage"]
    ]
    existing.append(run_row)
    write_csv(RUN_LOG, existing, run_fields)

    append_once(GLOBAL_MANIFEST, "stage150_final_package_refresh", f"""
- stage150_final_package_refresh: `{decision}`
  - `docs/stage150_final_package_refresh.md`
  - `experiments/stage150_final_package_refresh_plan.md`
  - `theory_checks/stage150_claim_scope_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage150_final_scope.md`
  - `repro/stage150_final_package_refresh/`
""")
    append_once(CHECKLIST_MD, "Stage150 final-package refresh pack", """
- [x] Stage150 final-package refresh pack recorded.
""")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
        else:
            rows.append({
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary, claims, evidence, blockers = build_tables()
    write_csv(SUMMARY_CSV, summary, SUMMARY_FIELDS)
    write_csv(CLAIMS_CSV, claims, CLAIM_FIELDS)
    write_csv(EVIDENCE_CSV, evidence, EVIDENCE_FIELDS)
    write_csv(BLOCKERS_CSV, blockers, BLOCKER_FIELDS)
    write_docs(summary, claims, evidence, blockers)
    update_longform(summary)
    update_repro(summary)
    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD,
        SUMMARY_CSV, CLAIMS_CSV, EVIDENCE_CSV, BLOCKERS_CSV,
        ARTIFACT_INDEX, Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)
    decision = status_by_gate(summary, "stage150_decision")
    print(f"Stage150 final package refresh: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
