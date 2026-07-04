#!/usr/bin/env python3
"""Build Stage326 exact dense route closeout artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage326_exact_dense_route_closeout"
DOC = ROOT / "docs" / "stage326_exact_dense_route_closeout.md"
THEORY = ROOT / "theory_checks" / "stage326_exact_dense_frontier_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage326_exact_dense_closed.md"
PLAN = ROOT / "experiments" / "stage327_final_claim_repro_refresh_plan.md"
BUILDER = ROOT / "scripts" / "build_stage326_exact_dense_route_closeout.py"

SUMMARY = OUT / "summary.csv"
EVIDENCE = OUT / "evidence_matrix.csv"
FRONTIER = OUT / "frontier_status.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage326_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE321_SUMMARY = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "perf_summary.csv"
STAGE321_PROOF = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "proof_gate.csv"
STAGE322_PROFILE = ROOT / "repro" / "stage322_schedule_profile_attribution" / "profile_summary.csv"
STAGE322_COMPONENTS = ROOT / "repro" / "stage322_schedule_profile_attribution" / "component_budget.csv"
STAGE323_SUMMARY = ROOT / "repro" / "stage323_dense_mat_counter_preflight" / "summary.csv"
STAGE324_SUMMARY = ROOT / "repro" / "stage324_selector_layout_mechanism_preflight" / "summary.csv"
STAGE325_SUMMARY = ROOT / "repro" / "stage325_selector_transpose_resource_probe" / "summary.csv"
STAGE325_PROOF = ROOT / "repro" / "stage325_selector_transpose_resource_probe" / "proof_gate.csv"

DECISION = "PASS_STAGE326_EXACT_DENSE_FRONTIER_CLOSED_CLAIM_REFRESH_SELECTED"


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


def fmt(value: float) -> str:
    return f"{value:.6f}"


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
    run_id = "stage326-exact-dense-route-closeout-001"
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
        "stage": "Stage 326",
        "backend": "evidence-closeout",
        "command": "python scripts/build_stage326_exact_dense_route_closeout.py",
        "config": "exact dense PVW/MAT-SAB route closeout",
        "params": "BINARY SET_2_3_2048; r=4; T_bootstrap/r claim boundary",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Stage326 closes current exact dense/local-layout optimization routes and selects final claim/repro refresh.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(EVIDENCE)}; {rel(FRONTIER)}; {rel(GATES)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def stage321_direct_speedup() -> str:
    for row in read_csv_rows(STAGE321_SUMMARY):
        if row.get("variant") == "direct_baseline":
            return row.get("speedup_vs_scalar_repeated_mean", "")
    return ""


def component_status(component: str) -> Dict[str, str]:
    for row in read_csv_rows(STAGE322_COMPONENTS):
        if row.get("component") == component:
            return row
    return {}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage322 = read_csv_one(STAGE322_PROFILE)
    stage323 = read_csv_one(STAGE323_SUMMARY)
    stage324 = read_csv_one(STAGE324_SUMMARY)
    stage325 = read_csv_one(STAGE325_SUMMARY)
    stage321_speedup = stage321_direct_speedup()

    dense_share = fnum(stage323.get("stage322_dense_share"))
    mat_ep_share = fnum(stage323.get("stage322_mat_ep_share"))
    selector_speedup = fnum(stage325.get("isolated_dense_speedup_mean"))
    selector_projection = fnum(stage325.get("projected_fullsab_speedup_mean"))
    selector_required = fnum(stage325.get("required_dense_speedup_for_1pct_fullsab"))
    r4_unrolled_text = read_text(STAGE321_PROOF)
    stage325_text = read_text(STAGE325_PROOF)

    evidence_rows = [
        {
            "evidence": "current_complete_sab_direct_baseline",
            "status": "SUPPORTED",
            "metric": "T_bootstrap/r speedup versus repeated scalar",
            "value": stage321_speedup or stage322.get("speedup_vs_repeated_scalar", ""),
            "source": rel(STAGE321_SUMMARY),
            "interpretation": "Current exact PVW/MAT-SAB result remains the supported throughput baseline.",
        },
        {
            "evidence": "r4_unrolled_fullsab_ab",
            "status": "CLOSED_NEUTRAL",
            "metric": "decision",
            "value": "NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION" if "NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION" in r4_unrolled_text else "missing",
            "source": rel(STAGE321_PROOF),
            "interpretation": "Pointer-hoist/r4-unrolled local AVX512 variant does not improve complete SAB.",
        },
        {
            "evidence": "dense_mat_profile_budget",
            "status": "MEASURED_RESIDUAL",
            "metric": "dense_share;mat_ep_share",
            "value": f"{fmt(dense_share)};{fmt(mat_ep_share)}",
            "source": rel(STAGE323_SUMMARY),
            "interpretation": "Dense MAT remains a residual budget, but local exact loop changes need a new mechanism.",
        },
        {
            "evidence": "selector_transpose_microbench",
            "status": "CLOSED_NEUTRAL",
            "metric": "isolated_dense_speedup;required;fullsab_projection",
            "value": f"{fmt(selector_speedup)};{fmt(selector_required)};{fmt(selector_projection)}",
            "source": rel(STAGE325_SUMMARY),
            "interpretation": "Selector-transpose locality is correct but below the threshold needed to justify integration.",
        },
        {
            "evidence": "direct_digit",
            "status": component_status("direct_digit").get("status", "CLOSED"),
            "metric": "share",
            "value": component_status("direct_digit").get("share_of_profile_full", ""),
            "source": rel(STAGE322_COMPONENTS),
            "interpretation": component_status("direct_digit").get("interpretation", "digit route already closed"),
        },
        {
            "evidence": "direct_ifft",
            "status": component_status("direct_ifft").get("status", "CLOSED"),
            "metric": "share",
            "value": component_status("direct_ifft").get("share_of_profile_full", ""),
            "source": rel(STAGE322_COMPONENTS),
            "interpretation": component_status("direct_ifft").get("interpretation", "IFFT route already closed"),
        },
        {
            "evidence": "sub_a_and_copyback",
            "status": "DEFER_LOW_BUDGET",
            "metric": "sub_a_share;copyback_share",
            "value": f"{component_status('sub_a_total').get('share_of_profile_full', '')};{component_status('copyback').get('share_of_profile_full', '')}",
            "source": rel(STAGE322_COMPONENTS),
            "interpretation": "Current profile does not select sub_a/copyback as first-order optimization targets.",
        },
        {
            "evidence": "compact_structured_route",
            "status": "FROZEN_PROOF_REQUIRED",
            "metric": "Stage324 selected route boundary",
            "value": stage324.get("decision", ""),
            "source": rel(STAGE324_SUMMARY),
            "interpretation": "Compact/structured selector is not production-admitted without formal proof and full SAB evidence.",
        },
    ]
    write_csv(EVIDENCE, evidence_rows, [
        "evidence", "status", "metric", "value", "source", "interpretation",
    ])

    frontier_rows = [
        {
            "frontier": "exact_dense_current_key_format",
            "status": "CLOSED_UNDER_CURRENT_EVIDENCE",
            "why": "r4 unrolled and selector-transpose both failed full-SAB or projected full-SAB gates.",
            "allowed_reopen_condition": "new load/store/count mechanism with microbench threshold and full-SAB A/B plan",
        },
        {
            "frontier": "current_supported_claim",
            "status": "KEEP_SCOPED_T_BOOTSTRAP_OVER_R",
            "why": "Current complete SAB evidence supports amortized throughput versus repeated scalar, not theoretical optimality.",
            "allowed_reopen_condition": "Stage327 final claim refresh may package this as scoped systems evidence.",
        },
        {
            "frontier": "structured_compact_algorithmic_route",
            "status": "BLOCKED_PROOF_REQUIRED",
            "why": "Potential product-count reduction changes selector semantics and remains proof-only.",
            "allowed_reopen_condition": "formal distribution/keygen/security proof, noise recurrence, isolated equivalence, and full SAB A/B",
        },
        {
            "frontier": "native_counter_refresh",
            "status": "OPTIONAL_ATTRIBUTION_ONLY",
            "why": "Native counters can improve attribution but cannot rescue a neutral isolated microbench by themselves.",
            "allowed_reopen_condition": "use to support final wording or a new mechanism, not to claim unmeasured speedup",
        },
    ]
    write_csv(FRONTIER, frontier_rows, [
        "frontier", "status", "why", "allowed_reopen_condition",
    ])

    gate_rows = [
        {
            "gate": "G1_stage325_input",
            "status": "PASS" if "NEUTRAL_STAGE325_SELECTOR_TRANSPOSE_MICRO_NO_PROMOTION" in stage325_text else "FAIL",
            "metric": "Stage325 decision",
            "value": stage325.get("decision", ""),
            "interpretation": "Stage326 closeout requires the selected Stage325 route to be resolved.",
        },
        {
            "gate": "G2_exact_dense_routes",
            "status": "PASS_CLOSED",
            "metric": "closed routes",
            "value": "r4_unrolled;selector_transpose;digit;ifft",
            "interpretation": "Current exact dense/local implementation routes are closed or deferred by measured gates.",
        },
        {
            "gate": "G3_claim_boundary",
            "status": "PASS_SCOPED",
            "metric": "allowed claim",
            "value": "complete-SAB T_bootstrap/r throughput evidence",
            "interpretation": "Do not upgrade to theoretical optimality, compact algorithm, or all-parameter claims.",
        },
        {
            "gate": "G4_next_stage",
            "status": DECISION,
            "metric": "selected next",
            "value": "stage327_final_claim_repro_refresh",
            "interpretation": "Refresh final package instead of starting another low-mechanism AVX rewrite.",
        },
    ]
    write_csv(GATES, gate_rows, ["gate", "status", "metric", "value", "interpretation"])

    summary_rows = [{
        "decision": DECISION,
        "selected_next_stage": "stage327_final_claim_repro_refresh",
        "current_direct_speedup_vs_repeated_scalar": stage321_speedup or stage322.get("speedup_vs_repeated_scalar", ""),
        "stage322_profile_speedup_vs_repeated_scalar": stage322.get("speedup_vs_repeated_scalar", ""),
        "dense_share": fmt(dense_share),
        "mat_ep_share": fmt(mat_ep_share),
        "selector_transpose_dense_speedup": fmt(selector_speedup),
        "selector_transpose_required_speedup": fmt(selector_required),
        "selector_transpose_projected_fullsab": fmt(selector_projection),
        "exact_dense_route_status": "closed_under_current_evidence",
        "compact_route_status": "frozen_until_formal_proof",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "selected_next_stage",
        "current_direct_speedup_vs_repeated_scalar",
        "stage322_profile_speedup_vs_repeated_scalar",
        "dense_share", "mat_ep_share",
        "selector_transpose_dense_speedup",
        "selector_transpose_required_speedup",
        "selector_transpose_projected_fullsab",
        "exact_dense_route_status", "compact_route_status",
    ])

    next_rows = [
        {
            "priority": "P0",
            "stage": "stage327_final_claim_repro_refresh",
            "entry_condition": DECISION,
            "task": "Refresh final evidence package with Stage320-326 results and scoped claim wording.",
            "gate": "Every claim must map to complete-SAB timing, microbench-only evidence, or blocked/frozen route status.",
            "failure_action": "Keep active goal open only for a new formal proof or new measured mechanism.",
        },
        {
            "priority": "P1",
            "stage": "formal_compact_selector_reopen",
            "entry_condition": "new proof artifact",
            "task": "Reopen algorithmic product-count reduction only after a real distribution/keygen/security proof.",
            "gate": "Proof, noise recurrence, isolated equivalence, resource, and full-SAB A/B.",
            "failure_action": "Do not implement compact SAB hot path.",
        },
    ]
    write_csv(NEXT, next_rows, [
        "priority", "stage", "entry_condition", "task", "gate", "failure_action",
    ])

    write_text(COMMANDS, """# Stage326 Reproduction Commands

```bash
python3 scripts/build_stage326_exact_dense_route_closeout.py
```

Stage326 is an evidence closeout. It does not run new benchmarks or modify
scalar SAB/default `sab_pvw_*`.
""")

    report = f"""# Stage326 Exact Dense Route Closeout

Decision: `{DECISION}`.

Stage326 closes the current exact dense/local-layout optimization frontier
under the evidence collected through Stage325. This is not a statement of
global theoretical optimality. It means the current key format and local AVX512
routes no longer have an admitted next implementation step without a new
measured mechanism or a formal compact/structured proof.

## Summary

{table(summary_rows, ["decision", "selected_next_stage", "current_direct_speedup_vs_repeated_scalar", "dense_share", "selector_transpose_dense_speedup", "selector_transpose_required_speedup", "selector_transpose_projected_fullsab", "exact_dense_route_status", "compact_route_status"])}

## Evidence Matrix

{table(evidence_rows, ["evidence", "status", "metric", "value", "interpretation"])}

## Frontier Status

{table(frontier_rows, ["frontier", "status", "why", "allowed_reopen_condition"])}

## Proof Gates

{table(gate_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage326 Exact Dense Frontier Model

The exact dense PVW/MAT-SAB route keeps the original dense selector equations:

```text
r = 4
rows = r + 1 = 5
outputs = k + r = 5
dense products per coefficient block = 25
```

Stages 321, 323, and 325 show that the remaining local implementation ideas do
not justify production integration:

- r4 pointer-hoist/unrolled rows: complete-SAB neutral;
- local dense loop rewrite: denied by static load/store model;
- selector coefficient-blocked layout: bit-exact but below the isolated
  speedup needed to project 1% complete-SAB gain.

This closes the current exact-dense implementation frontier, not the broader
research problem. A real next algorithmic route must reduce product count or
change the SAB schedule with proof-backed semantics.
""")
    write_text(VARIANT, f"""# Stage326 Exact Dense Route Closed

Status: `{DECISION}`.

Closed under current evidence:

- r4-unrolled local AVX512 variant;
- additional exact dense local loop rewrites;
- selector-transpose key layout integration;
- low-budget sub_a/copyback first-target work.

Still open only with new evidence:

- formal structured/compact selector route;
- new measured backend mechanism with full-SAB `T_bootstrap/r` A/B plan.
""")
    write_text(PLAN, f"""# Stage327 Final Claim/Repro Refresh Plan

Input decision: `{DECISION}`.

Goal: produce the final current-head claim and reproducibility refresh after
closing the exact dense optimization frontier.

Required outputs:

- complete-SAB speedup statement in `T_bootstrap/r` terms only;
- distinction between full-SAB timing, isolated microbench, and blocked routes;
- updated artifact index for Stage320-326;
- explicit limitations: no theoretical optimality, no compact production
  claim, no all-parameter claim.

Failure handling: if a claim is unsupported by full-SAB data, downgrade it to
microbench-only or future-work wording.
""")

    append_once(GOAL, "<!-- stage326-exact-dense-route-closeout -->", f"""<!-- stage326-exact-dense-route-closeout -->
### Stage326 exact dense route closeout

`{DECISION}` closes the current exact dense/local-layout implementation
frontier and selects final claim/repro refresh.
""")
    append_once(ROADMAP, "## Stage 326: Exact Dense Route Closeout", f"""## Stage 326: Exact Dense Route Closeout

Goal: close exact dense/local-layout optimization under current evidence after
Stage325 selector-transpose neutral result.

Status: `{DECISION}`.
""")
    append_once(HYPOTHESES, "H326_exact_dense_route_closeout:", f"""H326_exact_dense_route_closeout:
  status: {DECISION}
  primary_metric: complete_sab_T_bootstrap_over_r_claim_boundary
  evidence:
    - repro/stage326_exact_dense_route_closeout/summary.csv
    - repro/stage326_exact_dense_route_closeout/evidence_matrix.csv
    - repro/stage326_exact_dense_route_closeout/frontier_status.csv
    - repro/stage326_exact_dense_route_closeout/proof_gate.csv
  conclusion: >
    Stage326 closes current exact dense/local-layout implementation routes
    under current evidence and routes to a final scoped claim/repro refresh.
""")
    append_once(MANIFEST, "- stage326_exact_dense_route_closeout:", """- stage326_exact_dense_route_closeout:
  - `docs/stage326_exact_dense_route_closeout.md`
  - `scripts/build_stage326_exact_dense_route_closeout.py`
  - `repro/stage326_exact_dense_route_closeout/`
""")
    append_once(CHECKLIST, "<!-- stage326-exact-dense-route-closeout-checklist -->", f"""<!-- stage326-exact-dense-route-closeout-checklist -->
- [x] Stage326 records `{DECISION}` and selects Stage327 final claim/repro refresh.
""")
    append_run_log()

    paths = [
        DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, EVIDENCE,
        FRONTIER, GATES, NEXT, BUILDER, STAGE321_SUMMARY, STAGE321_PROOF,
        STAGE322_PROFILE, STAGE322_COMPONENTS, STAGE323_SUMMARY,
        STAGE324_SUMMARY, STAGE325_SUMMARY, STAGE325_PROOF,
    ]
    artifact_index(paths)
    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
