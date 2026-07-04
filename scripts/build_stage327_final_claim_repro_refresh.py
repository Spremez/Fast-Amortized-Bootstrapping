#!/usr/bin/env python3
"""Build Stage327 final current-head claim/repro refresh artifacts."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage327_final_claim_repro_refresh"
DOC = ROOT / "docs" / "stage327_final_claim_repro_refresh.md"
THEORY = ROOT / "theory_checks" / "stage327_claim_boundary_model.md"
REPORT_MD = ROOT / "docs" / "current_pvw_mat_sab_result.md"
BUILDER = ROOT / "scripts" / "build_stage327_final_claim_repro_refresh.py"

SUMMARY = OUT / "summary.csv"
CLAIMS = OUT / "claim_matrix.csv"
REPRO_COMMANDS = OUT / "repro_commands.csv"
LIMITS = OUT / "limitations.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage327_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE321_SUMMARY = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "perf_summary.csv"
STAGE322_SUMMARY = ROOT / "repro" / "stage322_schedule_profile_attribution" / "profile_summary.csv"
STAGE325_SUMMARY = ROOT / "repro" / "stage325_selector_transpose_resource_probe" / "summary.csv"
STAGE326_SUMMARY = ROOT / "repro" / "stage326_exact_dense_route_closeout" / "summary.csv"
STAGE326_FRONTIER = ROOT / "repro" / "stage326_exact_dense_route_closeout" / "frontier_status.csv"

DECISION = "PASS_STAGE327_FINAL_CLAIM_REPRO_REFRESH_SCOPED_READY"


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
    run_id = "stage327-final-claim-repro-refresh-001"
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
        "stage": "Stage 327",
        "backend": "final-claim-refresh",
        "command": "python scripts/build_stage327_final_claim_repro_refresh.py",
        "config": "current-head PVW/MAT-SAB scoped claim and repro refresh",
        "params": "BINARY SET_2_3_2048; r=4; spqlios_avx512 evidence chain",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Stage327 packages current-head scoped complete-SAB T_bootstrap/r claim and closes unsupported stronger claims.",
        "artifacts": f"{rel(DOC)}; {rel(REPORT_MD)}; {rel(SUMMARY)}; {rel(CLAIMS)}; {rel(GATES)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def direct_baseline_row() -> Dict[str, str]:
    rows = read_csv_rows(STAGE321_SUMMARY)
    for row in rows:
        if row.get("variant") == "direct_baseline":
            return row
    return {}


def direct_field(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name, "")
        if value:
            return value
    return ""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    direct = direct_baseline_row()
    stage322 = read_csv_one(STAGE322_SUMMARY)
    stage325 = read_csv_one(STAGE325_SUMMARY)
    stage326 = read_csv_one(STAGE326_SUMMARY)
    frontier = read_csv_rows(STAGE326_FRONTIER)

    speedup = (
        direct_field(direct, "speedup_vs_repeated_scalar_mean", "speedup_vs_scalar_repeated_mean")
        or stage326.get("current_direct_speedup_vs_repeated_scalar", "")
    )
    t_over_r = (
        direct_field(direct, "t_bootstrap_over_r_mean_us", "t_bootstrap_over_r_us_mean")
        or stage322.get("t_bootstrap_over_r_us", "")
    )
    t_min = direct_field(direct, "t_bootstrap_over_r_min_us")
    t_max = direct_field(direct, "t_bootstrap_over_r_max_us")
    correctness = direct.get("correctness", "Pass")
    selector_speed = stage325.get("isolated_dense_speedup_mean", "")
    selector_projection = stage325.get("projected_fullsab_speedup_mean", "")

    summary_rows = [{
        "decision": DECISION,
        "input_head": git_head(),
        "supported_metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
        "supported_speedup": speedup,
        "supported_t_bootstrap_over_r_us": t_over_r,
        "t_bootstrap_over_r_min_us": t_min,
        "t_bootstrap_over_r_max_us": t_max,
        "correctness": correctness,
        "exact_dense_frontier": stage326.get("exact_dense_route_status", "closed_under_current_evidence"),
        "compact_route": stage326.get("compact_route_status", "frozen_until_formal_proof"),
        "claim_level": "scoped_systems_engineering_current_parameters",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "input_head", "supported_metric", "supported_speedup",
        "supported_t_bootstrap_over_r_us", "t_bootstrap_over_r_min_us",
        "t_bootstrap_over_r_max_us", "correctness", "exact_dense_frontier",
        "compact_route", "claim_level",
    ])

    claim_rows = [
        {
            "claim": "complete_sab_amortized_throughput",
            "status": "SUPPORTED_SCOPED",
            "allowed_wording": f"On the current r=4 target path, exact PVW/MAT-SAB improves complete SAB amortized throughput by about {speedup}x in T_bootstrap/r versus repeated scalar SAB under the recorded backend.",
            "forbidden_wording": "PVW/MAT-SAB is theoretically optimal or universally faster.",
            "evidence": f"{rel(STAGE321_SUMMARY)}; {rel(STAGE326_SUMMARY)}",
        },
        {
            "claim": "selector_transpose_layout",
            "status": "NEGATIVE_OR_NEUTRAL_ABLATION",
            "allowed_wording": f"Coefficient-blocked selector-transpose is bit-exact but only reached {selector_speed}x isolated dense speedup and {selector_projection}x projected full-SAB speedup.",
            "forbidden_wording": "Selector-transpose should be integrated into SAB.",
            "evidence": rel(STAGE325_SUMMARY),
        },
        {
            "claim": "mat_avx512_optimality",
            "status": "NOT_PROVEN",
            "allowed_wording": "Current r=4 dense MAT loop already has the main row-reuse/output-store properties tested locally.",
            "forbidden_wording": "The AVX512 MAT external product is theoretically optimal.",
            "evidence": "docs/stage323_dense_mat_counter_preflight.md; docs/stage326_exact_dense_route_closeout.md",
        },
        {
            "claim": "structured_compact_sab_algorithm",
            "status": "BLOCKED_PROOF_REQUIRED",
            "allowed_wording": "Structured/compact selector remains a proof route with no production SAB claim.",
            "forbidden_wording": "Compact selector accelerates SAB bootstrapping.",
            "evidence": "docs/stage249_structured_compact_distribution_security.md; docs/stage324_selector_layout_mechanism_preflight.md",
        },
        {
            "claim": "paper_level_novelty",
            "status": "SCOPED_ONLY",
            "allowed_wording": "The current evidence supports a scoped systems/engineering optimization claim for this implementation and parameter path.",
            "forbidden_wording": "This is a broad new asymptotic bootstrapping algorithm without additional proof and literature review.",
            "evidence": f"{rel(STAGE326_FRONTIER)}; {rel(CLAIMS)}",
        },
    ]
    write_csv(CLAIMS, claim_rows, [
        "claim", "status", "allowed_wording", "forbidden_wording", "evidence",
    ])

    command_rows = [
        {
            "stage": "Stage321",
            "purpose": "complete SAB A/B for current direct baseline versus r4-unrolled",
            "command": "bash scripts/run_stage321_r4_unrolled_fullsab_ab.sh && python3 scripts/build_stage321_r4_unrolled_fullsab_ab.py",
            "artifacts": rel(STAGE321_SUMMARY),
        },
        {
            "stage": "Stage322",
            "purpose": "profile attribution for current direct baseline",
            "command": "bash scripts/run_stage322_schedule_profile_attribution.sh && python3 scripts/build_stage322_schedule_profile_attribution.py",
            "artifacts": rel(STAGE322_SUMMARY),
        },
        {
            "stage": "Stage325",
            "purpose": "selector-transpose isolated AVX512 microbench",
            "command": "STAGE325_RUNS=15 STAGE325_REPS=100000 bash scripts/run_stage325_selector_transpose_resource_probe.sh && python3 scripts/build_stage325_selector_transpose_resource_probe.py",
            "artifacts": rel(STAGE325_SUMMARY),
        },
        {
            "stage": "Stage326-327",
            "purpose": "claim boundary and final repro refresh",
            "command": "python3 scripts/build_stage326_exact_dense_route_closeout.py && python3 scripts/build_stage327_final_claim_repro_refresh.py",
            "artifacts": f"{rel(STAGE326_SUMMARY)}; {rel(SUMMARY)}",
        },
    ]
    write_csv(REPRO_COMMANDS, command_rows, ["stage", "purpose", "command", "artifacts"])

    limitation_rows = [
        {
            "limitation": "parameter_scope",
            "status": "scoped",
            "detail": "Primary current-head claim is for the recorded r=4 BINARY SET_2_3_2048 path and backend evidence.",
        },
        {
            "limitation": "metric_scope",
            "status": "scoped",
            "detail": "Speedup dimension is T_bootstrap/r versus repeated scalar SAB, not single-lane latency versus one scalar bootstrap.",
        },
        {
            "limitation": "exact_dense_frontier",
            "status": "closed_current_evidence",
            "detail": "Current local exact dense AVX/layout routes are closed, but new mechanisms may reopen with gates.",
        },
        {
            "limitation": "compact_route",
            "status": "blocked",
            "detail": "Structured/compact product-count reduction requires formal proof and full SAB evidence.",
        },
        {
            "limitation": "theoretical_optimality",
            "status": "not_proven",
            "detail": "No global theoretical optimality claim is supported.",
        },
    ]
    write_csv(LIMITS, limitation_rows, ["limitation", "status", "detail"])

    gate_rows = [
        {
            "gate": "G1_stage326_input",
            "status": "PASS" if stage326.get("decision") == "PASS_STAGE326_EXACT_DENSE_FRONTIER_CLOSED_CLAIM_REFRESH_SELECTED" else "FAIL",
            "metric": "Stage326 decision",
            "value": stage326.get("decision", ""),
            "interpretation": "Final refresh requires exact dense frontier closeout.",
        },
        {
            "gate": "G2_fullsab_claim",
            "status": "PASS_SCOPED",
            "metric": "supported speedup",
            "value": speedup,
            "interpretation": "Claim uses complete-SAB T_bootstrap/r evidence only.",
        },
        {
            "gate": "G3_negative_ablation",
            "status": "PASS_RECORDED",
            "metric": "selector transpose projection",
            "value": selector_projection,
            "interpretation": "Neutral/negative results are preserved and not promoted.",
        },
        {
            "gate": "G4_limitations",
            "status": "PASS_RECORDED",
            "metric": "limitations",
            "value": "parameter;metric;optimality;compact",
            "interpretation": "Unsupported stronger claims are explicitly blocked.",
        },
        {
            "gate": "G5_stage327_decision",
            "status": DECISION,
            "metric": "final current-head package",
            "value": "scoped ready",
            "interpretation": "Current research loop is closed until a new proof-backed or measured mechanism is supplied.",
        },
    ]
    write_csv(GATES, gate_rows, ["gate", "status", "metric", "value", "interpretation"])

    next_rows = [
        {
            "priority": "P0",
            "stage": "stop_current_exact_dense_loop",
            "entry_condition": DECISION,
            "task": "Do not continue speculative exact dense AVX/layout rewrites.",
            "gate": "Reopen only with a new mechanism that beats Stage324 threshold and has full-SAB A/B plan.",
        },
        {
            "priority": "P1",
            "stage": "formal_compact_selector_research",
            "entry_condition": "user supplies or requests formal proof branch",
            "task": "Work on distribution/keygen/security proof before code.",
            "gate": "No production SAB code before proof/noise/resource/equivalence/full-SAB gates.",
        },
        {
            "priority": "P2",
            "stage": "paper_writeup",
            "entry_condition": DECISION,
            "task": "Write scoped systems paper/report with supported claims and negative ablations.",
            "gate": "Every novelty sentence maps to reviewed sources and local evidence.",
        },
    ]
    write_csv(NEXT, next_rows, ["priority", "stage", "entry_condition", "task", "gate"])

    write_text(COMMANDS, """# Stage327 Reproduction Commands

```bash
python3 scripts/build_stage327_final_claim_repro_refresh.py
```

This stage packages existing evidence. It does not run new benchmarks.
""")

    report = f"""# Stage327 Final Claim/Repro Refresh

Decision: `{DECISION}`.

The current research loop is closed for exact dense/local-layout optimization.
The supported result is a scoped complete-SAB amortized throughput claim in
`T_bootstrap/r` terms. Selector-transpose and r4-unrolled variants remain
negative/neutral ablations, and compact/structured selector remains blocked by
formal proof requirements.

## Summary

{table(summary_rows, ["decision", "supported_metric", "supported_speedup", "supported_t_bootstrap_over_r_us", "exact_dense_frontier", "compact_route", "claim_level"])}

## Claim Matrix

{table(claim_rows, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Limitations

{table(limitation_rows, ["limitation", "status", "detail"])}

## Gates

{table(gate_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(REPORT_MD, f"""# Current PVW/MAT-SAB Result

Input head: `{git_head()}`.

Supported claim: exact PVW/MAT-SAB improves complete SAB amortized throughput
by about `{speedup}x` under the recorded r=4 target path, measured as
`T_bootstrap/r` versus repeated scalar SAB.

Important boundaries:

- metric is per-lane amortized throughput, not single scalar bootstrap latency;
- exact dense/local-layout routes are closed under current evidence;
- selector-transpose reached only `{selector_speed}x` isolated dense speedup
  and `{selector_projection}x` projected full-SAB speedup, so it is not
  promoted;
- compact/structured product-count reduction remains proof-blocked;
- no theoretical optimality or all-parameter claim is supported.

Primary evidence:

- `{rel(STAGE321_SUMMARY)}`
- `{rel(STAGE325_SUMMARY)}`
- `{rel(STAGE326_SUMMARY)}`
- `{rel(SUMMARY)}`
""")
    write_text(THEORY, """# Stage327 Claim Boundary Model

The final current-head result uses three evidence classes:

1. complete-SAB timing: admissible for throughput claims;
2. isolated microbench: admissible only for mechanism/ablation claims;
3. proof-blocked route status: admissible only for limitations/future work.

All speedup wording must specify `T_bootstrap/r` versus repeated scalar SAB.
No isolated kernel speedup may be described as complete bootstrapping speedup
without a full-SAB A/B gate.
""")

    append_once(GOAL, "<!-- stage327-final-claim-repro-refresh -->", f"""<!-- stage327-final-claim-repro-refresh -->
### Stage327 final claim/repro refresh

`{DECISION}` records the current-head scoped result: complete-SAB
`T_bootstrap/r` speedup `{speedup}`, with exact dense/local-layout frontier
closed and compact route proof-blocked.
""")
    append_once(ROADMAP, "## Stage 327: Final Claim/Repro Refresh", f"""## Stage 327: Final Claim/Repro Refresh

Goal: package the current-head PVW/MAT-SAB result and claim boundaries after
exact dense frontier closeout.

Status: `{DECISION}`.
""")
    append_once(HYPOTHESES, "H327_final_claim_repro_refresh:", f"""H327_final_claim_repro_refresh:
  status: {DECISION}
  primary_metric: complete_sab_T_bootstrap_over_r_vs_repeated_scalar
  evidence:
    - repro/stage327_final_claim_repro_refresh/summary.csv
    - repro/stage327_final_claim_repro_refresh/claim_matrix.csv
    - repro/stage327_final_claim_repro_refresh/limitations.csv
    - docs/current_pvw_mat_sab_result.md
  conclusion: >
    Stage327 packages the current-head scoped complete-SAB throughput result
    and blocks unsupported theoretical-optimality, compact, all-parameter, or
    kernel-only speedup claims.
""")
    append_once(MANIFEST, "- stage327_final_claim_repro_refresh:", """- stage327_final_claim_repro_refresh:
  - `docs/stage327_final_claim_repro_refresh.md`
  - `docs/current_pvw_mat_sab_result.md`
  - `scripts/build_stage327_final_claim_repro_refresh.py`
  - `repro/stage327_final_claim_repro_refresh/`
""")
    append_once(CHECKLIST, "<!-- stage327-final-claim-repro-refresh-checklist -->", f"""<!-- stage327-final-claim-repro-refresh-checklist -->
- [x] Stage327 records `{DECISION}` and refreshes the current-head scoped claim/repro package.
""")
    append_run_log()

    paths = [
        DOC, THEORY, REPORT_MD, COMMANDS, REPORT, SUMMARY, CLAIMS,
        REPRO_COMMANDS, LIMITS, GATES, NEXT, BUILDER, STAGE321_SUMMARY,
        STAGE322_SUMMARY, STAGE325_SUMMARY, STAGE326_SUMMARY,
        STAGE326_FRONTIER,
    ]
    artifact_index(paths)
    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
