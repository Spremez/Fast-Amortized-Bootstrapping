#!/usr/bin/env python3
"""Build Stage328 active-goal requirement audit artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage328_active_goal_requirement_audit"
DOC = ROOT / "docs" / "stage328_active_goal_requirement_audit.md"
THEORY = ROOT / "theory_checks" / "stage328_completion_gap_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage328_next_research_frontier.md"
PLAN = ROOT / "experiments" / "stage329_paper_stat_or_compact_proof_plan.md"
BUILDER = ROOT / "scripts" / "build_stage328_active_goal_requirement_audit.py"

SUMMARY = OUT / "summary.csv"
REQS = OUT / "requirement_matrix.csv"
EVIDENCE = OUT / "evidence_grade.csv"
NEXT = OUT / "next_stage_queue.csv"
GATES = OUT / "proof_gate.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage328_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE106_SUMMARY = ROOT / "repro" / "stage106_mat_rlwe_sab_research_loop" / "summary.csv"
STAGE106_THEORY = ROOT / "repro" / "stage106_mat_rlwe_sab_research_loop" / "theory_bound_matrix.csv"
STAGE200_SUMMARY = ROOT / "repro" / "stage200_formal_gap_model_with_probe" / "summary.csv"
STAGE200_OBLIGATIONS = ROOT / "repro" / "stage200_formal_gap_model_with_probe" / "proof_obligations.csv"
STAGE321_SUMMARY = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "perf_summary.csv"
STAGE325_SUMMARY = ROOT / "repro" / "stage325_selector_transpose_resource_probe" / "summary.csv"
STAGE327_SUMMARY = ROOT / "repro" / "stage327_final_claim_repro_refresh" / "summary.csv"
STAGE327_CLAIMS = ROOT / "repro" / "stage327_final_claim_repro_refresh" / "claim_matrix.csv"
STAGE327_LIMITS = ROOT / "repro" / "stage327_final_claim_repro_refresh" / "limitations.csv"

DECISION = "PASS_STAGE328_ACTIVE_GOAL_AUDIT_GOAL_REMAINS_ACTIVE_SELECT_HIGHSTAT_OR_FORMAL_PROOF"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_csv_one(path: Path) -> Dict[str, str]:
    rows = read_csv_rows(path)
    return rows[0] if rows else {}


def gate_row(path: Path, gate: str) -> Dict[str, str]:
    for row in read_csv_rows(path):
        if row.get("gate") == gate:
            return row
    return {}


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip())
        if not text.endswith("\n"):
            f.write("\n")


def fnum(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": str(len(data)), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def append_run_log() -> None:
    run_id = "stage328-active-goal-requirement-audit-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = [
            "run_id", "date", "git_ref", "stage", "backend", "command",
            "config", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 328",
        "backend": "goal-audit",
        "command": "python scripts/build_stage328_active_goal_requirement_audit.py",
        "config": "active goal requirement-by-requirement audit",
        "params": "PVW/MAT-SAB; r-body MAT-RLWE; T_bootstrap/r",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Stage328 audits the original research goal against current evidence and keeps the goal active.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(REQS)}; {rel(EVIDENCE)}; {rel(GATES)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def direct_baseline() -> Dict[str, str]:
    for row in read_csv_rows(STAGE321_SUMMARY):
        if row.get("variant") == "direct_baseline":
            return row
    return {}


def claim_status(name: str) -> str:
    for row in read_csv_rows(STAGE327_CLAIMS):
        if row.get("claim") == name:
            return row.get("status", "")
    return ""


def limitation_status(name: str) -> str:
    for row in read_csv_rows(STAGE327_LIMITS):
        if row.get("limitation") == name:
            return row.get("status", "")
    return ""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage106_decision = gate_row(STAGE106_SUMMARY, "stage106_decision")
    stage200_decision = gate_row(STAGE200_SUMMARY, "stage200_decision")
    stage327 = read_csv_one(STAGE327_SUMMARY)
    direct = direct_baseline()
    stage325 = read_csv_one(STAGE325_SUMMARY)
    proof_obligations = read_csv_rows(STAGE200_OBLIGATIONS)
    open_obligations = [
        row.get("obligation_id", "")
        for row in proof_obligations
        if row.get("status") in {"OPEN", "BLOCKED"}
    ]
    samples = int(fnum(direct.get("samples")))
    speedup = stage327.get("supported_speedup", "")
    t_over_r = stage327.get("supported_t_bootstrap_over_r_us", "")
    selector_projection = stage325.get("projected_fullsab_speedup_mean", "")

    req_rows = [
        {
            "requirement_id": "R1_algorithm_object",
            "requirement": "Treat PVW/MAT-SAB as an r-body MAT-RLWE ciphertext algorithm, not only a kernel optimization.",
            "status": "PASS_SCOPED",
            "evidence": f"{rel(STAGE106_SUMMARY)}; {rel(STAGE327_SUMMARY)}",
            "gap": "None for current scoped exact route; compact representation remains separate.",
            "next_action": "Preserve r-body state and lane phase invariant in all future variants.",
        },
        {
            "requirement_id": "R2_primary_metric",
            "requirement": "Use T_bootstrap/r as the primary endpoint for processed plaintext bit/lane.",
            "status": "PASS",
            "evidence": f"{rel(STAGE321_SUMMARY)}; {rel(STAGE327_SUMMARY)}",
            "gap": "No gap for current result.",
            "next_action": "Reject future reports that use kernel-only or single-lane latency as final endpoint.",
        },
        {
            "requirement_id": "R3_lower_bound_complexity",
            "requirement": "Provide theory lower-bound and complexity model.",
            "status": "PASS_SCOPED_GLOBAL_OPEN",
            "evidence": f"{rel(STAGE106_THEORY)}; {rel(STAGE200_SUMMARY)}",
            "gap": "Same-format dense lower bound exists; global MAT-RLWE optimality and compact proof remain open.",
            "next_action": "Do not claim optimality; use proof obligations O1-O4 before stronger route.",
        },
        {
            "requirement_id": "R4_candidate_optimal_paths",
            "requirement": "Maintain candidate optimal algorithm paths with falsifiable route status.",
            "status": "PASS_ACTIVE_FRONTIER",
            "evidence": "repro/stage326_exact_dense_route_closeout/frontier_status.csv; repro/stage327_final_claim_repro_refresh/next_stage_queue.csv",
            "gap": "Exact dense local route closed; formal compact selector route has no production proof.",
            "next_action": "Select high-stat confirmation for scoped result or formal compact proof branch.",
        },
        {
            "requirement_id": "R5_falsifiable_experiment_gates",
            "requirement": "Every optimization must have correctness, performance, failure, and repro gates.",
            "status": "PASS_FOR_EXECUTED_BRANCHES",
            "evidence": f"{rel(STAGE321_SUMMARY)}; {rel(STAGE325_SUMMARY)}",
            "gap": "Formal compact branch still needs proof-specific gates before code.",
            "next_action": "For compact route: proof -> finite equivalence -> noise/resource -> full SAB A/B.",
        },
        {
            "requirement_id": "R6_stats_and_repro",
            "requirement": "Provide statistical and reproducibility standards strong enough for paper claims.",
            "status": "PARTIAL_SCOPED_ENGINEERING_ONLY",
            "evidence": f"{rel(STAGE321_SUMMARY)}; {rel(RUN_LOG)}",
            "gap": f"Current formal current-head complete-SAB claim has {samples} samples; paper-level threshold remains >=10 samples plus resource/noise refresh.",
            "next_action": "Run Stage329 high-stat complete-SAB refresh if paper-ready performance wording is needed.",
        },
        {
            "requirement_id": "R7_no_theory_loop",
            "requirement": "Do not remain in pure theory; advance to runnable gates.",
            "status": "PASS_CURRENT_LOOP",
            "evidence": f"{rel(STAGE325_SUMMARY)}; {rel(STAGE327_SUMMARY)}",
            "gap": "Next formal compact work must include an executable finite or production gate.",
            "next_action": "Freeze any theory route after one proof-obligation pass unless it emits a runnable checker.",
        },
        {
            "requirement_id": "R8_completion",
            "requirement": "Only mark the whole active goal complete when every requirement is proven.",
            "status": "NOT_COMPLETE",
            "evidence": f"{rel(STAGE327_LIMITS)}; {rel(STAGE200_OBLIGATIONS)}",
            "gap": f"Open obligations: {','.join(open_obligations) or 'none'}; theoretical optimality status={claim_status('mat_avx512_optimality')}; compact status={limitation_status('compact_route')}.",
            "next_action": "Keep goal active; proceed to high-stat refresh or formal compact proof.",
        },
    ]
    write_csv(REQS, req_rows, [
        "requirement_id", "requirement", "status", "evidence", "gap", "next_action",
    ])

    evidence_rows = [
        {
            "evidence_class": "complete_sab_timing",
            "status": "SUPPORTED_SCOPED",
            "primary_value": f"speedup={speedup}; T/r_us={t_over_r}; samples={samples}",
            "paper_readiness": "needs_highstat_refresh",
            "why": "Complete-SAB endpoint is correct, but sample count is scoped engineering rather than paper-level high-stat.",
        },
        {
            "evidence_class": "isolated_microbench",
            "status": "NEGATIVE_ABLATION_RECORDED",
            "primary_value": f"selector_transpose_projected_fullsab={selector_projection}",
            "paper_readiness": "usable_as_negative_ablation",
            "why": "Useful to reject a candidate, not to support bootstrapping speedup.",
        },
        {
            "evidence_class": "lower_bound_model",
            "status": "SCOPED_MODEL_RECORDED",
            "primary_value": stage200_decision.get("status", ""),
            "paper_readiness": "allowed_as_assumption-scoped_model",
            "why": "Same-format lower bound exists; global optimality remains open.",
        },
        {
            "evidence_class": "formal_compact_route",
            "status": "PROOF_REQUIRED",
            "primary_value": ",".join(open_obligations),
            "paper_readiness": "future_work_only",
            "why": "No production proof, no full SAB timing, no compact claim.",
        },
    ]
    write_csv(EVIDENCE, evidence_rows, [
        "evidence_class", "status", "primary_value", "paper_readiness", "why",
    ])

    gate_rows = [
        {
            "gate": "G1_stage106_research_loop",
            "status": "PASS" if "PASS_STAGE106_RESEARCH_LOOP_FIXED_OPTIMALITY_OPEN" in read_text(STAGE106_SUMMARY) else "FAIL",
            "metric": "algorithm object and endpoint",
            "value": stage106_decision.get("status", ""),
            "interpretation": "The research loop is framed around r-body MAT-RLWE and T_bootstrap/r.",
        },
        {
            "gate": "G2_stage200_lower_bound",
            "status": "PASS_SCOPED" if "PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE" in read_text(STAGE200_SUMMARY) else "FAIL",
            "metric": "lower-bound model",
            "value": stage200_decision.get("status", ""),
            "interpretation": "Lower-bound evidence is scoped to same-format dense representation.",
        },
        {
            "gate": "G3_stage327_final_claim",
            "status": "PASS_SCOPED" if stage327.get("decision") == "PASS_STAGE327_FINAL_CLAIM_REPRO_REFRESH_SCOPED_READY" else "FAIL",
            "metric": "current complete-SAB claim",
            "value": speedup,
            "interpretation": "Current implementation has scoped complete-SAB speedup evidence.",
        },
        {
            "gate": "G4_completion_audit",
            "status": "GOAL_ACTIVE_NOT_COMPLETE",
            "metric": "open gaps",
            "value": ",".join(open_obligations) or "paper_highstat;global_optimality",
            "interpretation": "The full active goal is not proven complete.",
        },
        {
            "gate": "G5_stage328_decision",
            "status": DECISION,
            "metric": "next route",
            "value": "stage329_highstat_or_formal_proof",
            "interpretation": "Concrete next work must either strengthen the scoped result statistically or open a formal compact proof checker.",
        },
    ]
    write_csv(GATES, gate_rows, ["gate", "status", "metric", "value", "interpretation"])

    next_rows = [
        {
            "priority": "P0",
            "route": "stage329_highstat_complete_sab_refresh",
            "entry_condition": "paper-ready scoped performance claim is needed",
            "task": "Rerun current direct PVW/MAT-SAB complete-SAB T_bootstrap/r with >=10 samples and refreshed resource/noise side conditions.",
            "gate": "Correctness pass; >=10 samples; confidence interval reported; no claim widening beyond current parameters.",
            "failure_action": "Keep Stage327 scoped engineering wording only.",
        },
        {
            "priority": "P1",
            "route": "stage329_formal_compact_selector_proof_checker",
            "entry_condition": "algorithmic optimality/product-count route is prioritized",
            "task": "Create executable finite/proof-obligation checker for selector structure before any compact SAB code.",
            "gate": "Distribution/keygen/security/noise obligations must be stated and at least finite checker must pass.",
            "failure_action": "Keep compact route proof-blocked.",
        },
        {
            "priority": "P2",
            "route": "paper_writeup_scoped_systems_result",
            "entry_condition": "no stronger algorithmic route is selected",
            "task": "Write scoped systems report using Stage327 claim matrix and negative ablations.",
            "gate": "Every claim maps to complete-SAB timing, microbench ablation, or proof-blocked limitation.",
            "failure_action": "Do not submit as theoretical-optimality paper.",
        },
    ]
    write_csv(NEXT, next_rows, [
        "priority", "route", "entry_condition", "task", "gate", "failure_action",
    ])

    summary_rows = [{
        "decision": DECISION,
        "goal_status": "active_not_complete",
        "supported_complete_sab_speedup": speedup,
        "supported_samples": samples,
        "paper_highstat_ready": "no" if samples < 10 else "yes",
        "lower_bound_status": "scoped_same_format",
        "exact_dense_frontier": "closed_current_evidence",
        "compact_route": "proof_required",
        "selected_next": "stage329_highstat_complete_sab_refresh_or_formal_compact_proof_checker",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "goal_status", "supported_complete_sab_speedup",
        "supported_samples", "paper_highstat_ready", "lower_bound_status",
        "exact_dense_frontier", "compact_route", "selected_next",
    ])

    write_text(COMMANDS, """# Stage328 Reproduction Commands

```bash
python3 scripts/build_stage328_active_goal_requirement_audit.py
```

Stage328 is a requirement-level audit. It does not run new benchmarks.
""")

    report = f"""# Stage328 Active Goal Requirement Audit

Decision: `{DECISION}`.

Stage328 audits the original PVW/MAT-SAB research objective against the current
worktree. The conclusion is deliberately not "goal complete": the exact dense
implementation branch has a scoped complete-SAB result, but paper-level
statistics and formal compact/optimality proof remain open.

## Summary

{table(summary_rows, ["decision", "goal_status", "supported_complete_sab_speedup", "supported_samples", "paper_highstat_ready", "lower_bound_status", "exact_dense_frontier", "compact_route", "selected_next"])}

## Requirement Matrix

{table(req_rows, ["requirement_id", "status", "gap", "next_action"])}

## Evidence Grade

{table(evidence_rows, ["evidence_class", "status", "primary_value", "paper_readiness", "why"])}

## Proof Gates

{table(gate_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage328 Completion Gap Model

The active goal has two different completion layers:

1. scoped exact-route engineering completion;
2. original research-goal completion.

Stage327 closes layer 1 for the current exact dense/local-layout branch. It
does not close layer 2 because the original goal also asks for stronger
statistics, candidate optimal algorithm paths, and theory/proof boundaries for
MAT-RLWE/r-body SAB.

Current exact-route lower-bound status:

```text
same-format dense lower bound: recorded
global MAT-RLWE optimality: open
compact/structured selector proof: open
```

Therefore the next work must be either a high-stat complete-SAB refresh for a
paper-ready scoped systems claim or an executable formal proof checker for the
compact/structured product-count route.
""")
    write_text(VARIANT, """# Stage328 Next Research Frontier

Current status:

- exact dense/local-layout implementation frontier: closed under current evidence;
- scoped complete-SAB T_bootstrap/r speedup: supported for current path;
- paper-level high-stat claim: not yet ready;
- compact/structured product-count route: proof-required.

Admitted next routes:

1. High-stat complete-SAB refresh for the scoped systems result.
2. Formal compact selector proof checker before any compact SAB code.
3. Scoped paper/report using only Stage327 claim boundaries.

Disallowed next route: another speculative exact dense AVX/layout rewrite
without a new measured mechanism.
""")
    write_text(PLAN, f"""# Stage329 Paper-Stat Or Compact-Proof Plan

Input decision: `{DECISION}`.

Choose one bounded route:

## Route A: High-Stat Complete-SAB Refresh

- run current direct PVW/MAT-SAB complete-SAB `T_bootstrap/r` with at least 10
  samples;
- preserve repeated scalar baseline under the same backend/parameter path;
- report confidence interval, min/max, correctness, and resource/noise side
  conditions;
- keep claim scoped to current r=4 BINARY SET_2_3_2048 path.

## Route B: Formal Compact Selector Proof Checker

- do not write compact SAB hot-path code;
- formalize selector distribution/keygen/security/noise obligations;
- implement a finite checker that can falsify semantic-zero or row-skipping
  claims;
- only after passing proof gates may an isolated compact kernel be reopened.

Failure handling: if neither route is selected, stop optimization work and use
Stage327 as a scoped systems result package.
""")

    append_once(GOAL, "<!-- stage328-active-goal-requirement-audit -->", f"""<!-- stage328-active-goal-requirement-audit -->
### Stage328 active goal requirement audit

`{DECISION}` audits the original goal and records that it remains active: the
exact dense branch is scoped-complete, but high-stat paper readiness and formal
compact/optimality proof remain open.
""")
    append_once(ROADMAP, "## Stage 328: Active Goal Requirement Audit", f"""## Stage 328: Active Goal Requirement Audit

Goal: audit the original PVW/MAT-SAB research objective requirement by
requirement against current evidence.

Status: `{DECISION}`.
""")
    append_once(HYPOTHESES, "H328_active_goal_requirement_audit:", f"""H328_active_goal_requirement_audit:
  status: {DECISION}
  primary_metric: requirement_level_completion_audit
  evidence:
    - repro/stage328_active_goal_requirement_audit/summary.csv
    - repro/stage328_active_goal_requirement_audit/requirement_matrix.csv
    - repro/stage328_active_goal_requirement_audit/evidence_grade.csv
    - repro/stage328_active_goal_requirement_audit/proof_gate.csv
  conclusion: >
    Stage328 verifies that the current exact dense branch is scoped-complete
    but the original active research goal remains open because paper-level
    high-stat evidence and formal compact/optimality proof are not complete.
""")
    append_once(MANIFEST, "- stage328_active_goal_requirement_audit:", """- stage328_active_goal_requirement_audit:
  - `docs/stage328_active_goal_requirement_audit.md`
  - `scripts/build_stage328_active_goal_requirement_audit.py`
  - `repro/stage328_active_goal_requirement_audit/`
""")
    append_once(CHECKLIST, "<!-- stage328-active-goal-requirement-audit-checklist -->", f"""<!-- stage328-active-goal-requirement-audit-checklist -->
- [x] Stage328 records `{DECISION}` and keeps the active goal open with explicit next routes.
""")
    append_run_log()

    paths = [
        DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, REQS, EVIDENCE,
        NEXT, GATES, BUILDER, STAGE106_SUMMARY, STAGE106_THEORY,
        STAGE200_SUMMARY, STAGE200_OBLIGATIONS, STAGE321_SUMMARY,
        STAGE325_SUMMARY, STAGE327_SUMMARY, STAGE327_CLAIMS,
        STAGE327_LIMITS,
    ]
    artifact_index(paths)
    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
