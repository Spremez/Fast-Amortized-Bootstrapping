#!/usr/bin/env python3
"""Stage332: package the scoped current-head PVW/MAT-SAB result."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage332_paper_result_pack"

DOC = ROOT / "docs" / "stage332_paper_result_pack.md"
CURRENT = ROOT / "docs" / "current_pvw_mat_sab_result.md"
TABLE = ROOT / "doc" / "pvw_mat_sab_scoped_result_table_stage332.md"
THEORY = ROOT / "theory_checks" / "stage332_claim_boundary_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage332_paper_claim_card.md"
PLAN = ROOT / "experiments" / "stage333_literature_novelty_or_compact_security_plan.md"
BUILDER = ROOT / "scripts" / "build_stage332_paper_result_pack.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE331_SUMMARY = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "summary.csv"
STAGE331_PERF = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "perf_summary.csv"
STAGE331_NOISE = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "noise_summary.csv"
STAGE331_CLAIMS = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "claim_boundary.csv"
STAGE329_OBLIGATIONS = ROOT / "repro" / "stage329_formal_compact_selector_checker" / "proof_obligation_matrix.csv"

SUMMARY = OUT / "summary.csv"
RESULT_TABLE = OUT / "paper_result_table.csv"
CLAIM_BOUNDARY = OUT / "claim_boundary.csv"
OPEN_ITEMS = OUT / "open_items.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage332_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE332_SCOPED_PAPER_RESULT_PACK"


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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def first(rows: list[dict[str, str]]) -> dict[str, str]:
    return rows[0] if rows else {}


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log() -> None:
    run_id = "stage332-paper-result-pack-001"
    if run_id in read_text(RUN_LOG):
        return
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as handle:
            fields = list(csv.DictReader(handle).fieldnames or [])
    else:
        fields = []
    if not fields:
        fields = [
            "run_id", "date", "commit_or_state", "stage", "backend", "command",
            "params", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "commit_or_state": git_head(),
        "git_ref": git_head(),
        "stage": "Stage 332",
        "backend": "analysis",
        "command": "python scripts/build_stage332_paper_result_pack.py",
        "params": "BINARY SET_2_3_2048; r=4; include-zero; spqlios_avx512; scoped paper result pack",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Packages Stage331 current-head high-stat PVW/MAT-SAB result with scoped claim boundaries.",
        "artifacts": f"{rel(DOC)}; {rel(TABLE)}; {rel(RESULT_TABLE)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: list[Path]) -> None:
    rows: list[dict[str, object]] = []
    for path in paths:
        if path.exists() and path.is_file():
            data = path.read_bytes()
            rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    stage331 = first(read_csv(STAGE331_SUMMARY))
    perf = first(read_csv(STAGE331_PERF))
    noise = first(read_csv(STAGE331_NOISE))
    stage331_claims = read_csv(STAGE331_CLAIMS)
    obligations = read_csv(STAGE329_OBLIGATIONS)

    r = 4
    pvw_lane_us = fnum(stage331.get("t_bootstrap_over_r_mean_us"))
    scalar_lane_us = fnum(stage331.get("scalar_t_bootstrap_over_r_mean_us"))
    pvw_total_us = pvw_lane_us * r
    scalar_total_us = scalar_lane_us * r
    speedup = fnum(stage331.get("speedup_vs_repeated_scalar_mean"))
    gain_pct = (speedup - 1.0) * 100.0 if speedup else 0.0

    pass_gate = stage331.get("decision") == "PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH"
    result_rows = [{
        "path": "direct_pvw_mat_sab",
        "parameter": "BINARY SET_2_3_2048 include-zero",
        "backend": "spqlios_avx512 WSL",
        "r_body_lanes": r,
        "samples": stage331.get("samples", ""),
        "correctness": stage331.get("correctness", ""),
        "pvw_total_bootstrap_us": f"{pvw_total_us:.3f}",
        "pvw_t_bootstrap_over_r_us": stage331.get("t_bootstrap_over_r_mean_us", ""),
        "pvw_t_bootstrap_over_r_ci95_us": f"{stage331.get('t_bootstrap_over_r_ci95_low_us', '')}..{stage331.get('t_bootstrap_over_r_ci95_high_us', '')}",
        "scalar_repeated_total_us": f"{scalar_total_us:.3f}",
        "scalar_repeated_t_over_r_us": stage331.get("scalar_t_bootstrap_over_r_mean_us", ""),
        "speedup_vs_repeated_scalar": stage331.get("speedup_vs_repeated_scalar_mean", ""),
        "amortized_gain_percent": f"{gain_pct:.3f}",
        "noise_trials": stage331.get("noise_trials", ""),
        "noise_pair_failures": stage331.get("noise_pair_failures", ""),
        "maxrss_kb": stage331.get("time_maxrss_kb", ""),
        "run_head": stage331.get("git_head", ""),
    }]

    summary_rows = [{
        "decision": DECISION if pass_gate else "FAIL_STAGE332_STAGE331_INPUT_NOT_PASS",
        "source_stage": stage331.get("decision", ""),
        "supported_speedup": stage331.get("speedup_vs_repeated_scalar_mean", ""),
        "supported_metric": "complete_sab_T_bootstrap_over_r",
        "samples": stage331.get("samples", ""),
        "noise_pair_failures": f"{stage331.get('noise_pair_failures', '')}/{stage331.get('noise_trials', '')}",
        "claim_scope": "scoped_parameter_backend_path",
        "unsupported": "theoretical_optimality; compact_selector_security; all_parameter_generality; novelty_without_literature",
    }]

    claim_rows = [
        {
            "claim": "main_scoped_systems_result",
            "status": "PASS" if pass_gate else "FAIL",
            "paper_safe_text": f"For BINARY SET_2_3_2048 include-zero on spqlios_avx512, r=4 direct PVW/MAT-SAB achieves {speedup:.6f}x amortized complete-SAB throughput over repeated scalar SAB, measured by T_bootstrap/r.",
            "boundary": "Only this parameter/backend/path; this is not a global optimality claim.",
        },
        {
            "claim": "metric_definition",
            "status": "PASS",
            "paper_safe_text": "The metric is per plaintext bit/lane: complete bootstrapping wall time divided by r MAT/RLWE body lanes.",
            "boundary": "Do not describe the result as single-lane bootstrap latency speedup.",
        },
        {
            "claim": "correctness_noise_resource",
            "status": "PASS" if noise.get("pair_failures") == "0" else "FAIL",
            "paper_safe_text": f"Final-output PVW/scalar pair check has {noise.get('pair_failures', '')}/{noise.get('trials', '')} failures; max RSS is {noise.get('time_maxrss_kb', '')} KB.",
            "boundary": "This is an implementation resource record, not a compact-selector security proof.",
        },
        {
            "claim": "novelty",
            "status": "OPEN_LITERATURE_REQUIRED",
            "paper_safe_text": "Do not claim novelty until Stage333 related-work verification is complete.",
            "boundary": "Related papers must be real and cited with checked support.",
        },
        {
            "claim": "compact_structured_route",
            "status": "OPEN_PROOF_REQUIRED",
            "paper_safe_text": "Compact selector finite algebra passed earlier, but production keygen/security/noise/full-SAB gates remain open.",
            "boundary": "No compact SAB acceleration claim.",
        },
    ]

    open_rows = [
        {
            "item": "related_work_novelty",
            "status": "OPEN",
            "required_before_claim": "Build verified related-work matrix for SAB, PVW/MAT external product, multi-output bootstrapping, and SIMD FHE kernels.",
            "next_action": "Stage333 literature/novelty verification.",
        },
        {
            "item": "compact_keygen_security",
            "status": "OPEN",
            "required_before_claim": "Close production keygen distribution, semantic-zero security, and noise recurrence obligations.",
            "next_action": "Stage333 compact keygen/security preflight if algorithmic improvement is prioritized.",
        },
        {
            "item": "all_parameter_generality",
            "status": "OPEN",
            "required_before_claim": "Repeat high-stat evidence over additional branches/parameter sets.",
            "next_action": "Extend Stage304 matrix only after related-work/paper scope is chosen.",
        },
    ]
    for obligation in obligations:
        if obligation.get("status") != "FINITE_PASS":
            open_rows.append({
                "item": obligation.get("obligation", ""),
                "status": obligation.get("status", ""),
                "required_before_claim": obligation.get("needed_before_code", ""),
                "next_action": "compact route remains blocked",
            })

    proof_rows = [
        {
            "gate": "G1_stage331_pass",
            "status": "PASS" if pass_gate else "FAIL",
            "metric": "Stage331 decision",
            "value": stage331.get("decision", ""),
            "interpretation": "Paper result pack is only allowed after current-head high-stat PASS.",
        },
        {
            "gate": "G2_metric_alignment",
            "status": "PASS",
            "metric": "primary endpoint",
            "value": "complete SAB T_bootstrap/r",
            "interpretation": "The result table uses the user-requested amortized per-bit/lane dimension.",
        },
        {
            "gate": "G3_claim_boundary",
            "status": "PASS",
            "metric": "unsupported claims",
            "value": "optimality/compact/novelty/all-parameter remain open",
            "interpretation": "Stage332 packages only the scoped systems result.",
        },
        {
            "gate": "G4_decision",
            "status": DECISION if pass_gate else "FAIL_STAGE332_STAGE331_INPUT_NOT_PASS",
            "metric": "stage decision",
            "value": DECISION if pass_gate else "blocked",
            "interpretation": "Controls Stage333 literature/novelty or compact security work.",
        },
    ]

    next_rows = [
        {
            "priority": "P0",
            "route": "stage333_literature_novelty_verification",
            "entry_condition": DECISION,
            "gate": "verified real related-work matrix; no unsupported novelty wording",
            "failure_action": "Keep paper text as engineering/scoped systems result only.",
        },
        {
            "priority": "P1",
            "route": "stage333_compact_keygen_security_preflight",
            "entry_condition": "seek algorithmic gain beyond current exact dense/direct path",
            "gate": "keygen distribution, security, noise recurrence, then isolated/full-SAB gates",
            "failure_action": "Keep compact production code blocked.",
        },
    ]

    write_csv(SUMMARY, summary_rows, [
        "decision", "source_stage", "supported_speedup", "supported_metric",
        "samples", "noise_pair_failures", "claim_scope", "unsupported",
    ])
    write_csv(RESULT_TABLE, result_rows, [
        "path", "parameter", "backend", "r_body_lanes", "samples", "correctness",
        "pvw_total_bootstrap_us", "pvw_t_bootstrap_over_r_us",
        "pvw_t_bootstrap_over_r_ci95_us", "scalar_repeated_total_us",
        "scalar_repeated_t_over_r_us", "speedup_vs_repeated_scalar",
        "amortized_gain_percent", "noise_trials", "noise_pair_failures",
        "maxrss_kb", "run_head",
    ])
    write_csv(CLAIM_BOUNDARY, claim_rows, ["claim", "status", "paper_safe_text", "boundary"])
    write_csv(OPEN_ITEMS, open_rows, ["item", "status", "required_before_claim", "next_action"])
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_text(TABLE, f"""# PVW/MAT-SAB Scoped Result Table

Use this table only with the stated scope and boundaries.

{md_table(result_rows, ["path", "parameter", "backend", "r_body_lanes", "samples", "pvw_t_bootstrap_over_r_us", "scalar_repeated_t_over_r_us", "speedup_vs_repeated_scalar", "noise_pair_failures", "maxrss_kb", "run_head"])}

Safe wording:

> For `BINARY SET_2_3_2048` include-zero on `spqlios_avx512`, `r=4` direct
> PVW/MAT-SAB achieves `{speedup:.6f}x` amortized complete-SAB throughput over
> repeated scalar SAB, measured by `T_bootstrap/r`.

Do not use this table to claim theoretical optimality, compact selector
security, all-parameter generality, or novelty.
""")

    write_text(DOC, f"""# Stage332 Paper Result Pack

Decision: `{DECISION if pass_gate else 'FAIL_STAGE332_STAGE331_INPUT_NOT_PASS'}`.

Stage332 packages the Stage331 current-head high-stat result into a scoped
paper/report result.  It does not add a new benchmark and it does not broaden
the claim beyond the measured parameter/backend/path.

## Summary

{md_table(summary_rows, ["decision", "supported_speedup", "supported_metric", "samples", "noise_pair_failures", "claim_scope", "unsupported"])}

## Result Table

{md_table(result_rows, ["path", "parameter", "backend", "r_body_lanes", "samples", "pvw_t_bootstrap_over_r_us", "scalar_repeated_t_over_r_us", "speedup_vs_repeated_scalar", "noise_pair_failures", "maxrss_kb"])}

## Claim Boundary

{md_table(claim_rows, ["claim", "status", "paper_safe_text", "boundary"])}

## Open Items

{md_table(open_rows, ["item", "status", "required_before_claim", "next_action"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value"])}

Generated from input head `{git_head()}`.
""")

    write_text(CURRENT, f"""# Current PVW/MAT-SAB Result

Input evidence head: `{stage331.get('git_head', '')}`.

Supported scoped claim: direct PVW/MAT-SAB improves complete SAB amortized
throughput by `{stage331.get('speedup_vs_repeated_scalar_mean', '')}x` for
`BINARY SET_2_3_2048`, include-zero, `r=4`, `spqlios_avx512`, measured as
`T_bootstrap/r` versus repeated scalar SAB.

Primary current-head result:

- PVW/MAT-SAB `T_bootstrap/r`: `{stage331.get('t_bootstrap_over_r_mean_us', '')}` us
  with 95% CI `{stage331.get('t_bootstrap_over_r_ci95_low_us', '')}..{stage331.get('t_bootstrap_over_r_ci95_high_us', '')}` us;
- repeated scalar SAB `T_bootstrap/r`: `{stage331.get('scalar_t_bootstrap_over_r_mean_us', '')}` us;
- complete PVW run processes `r=4` lanes, so total PVW time is `{pvw_total_us:.3f}` us
  and repeated scalar total is `{scalar_total_us:.3f}` us;
- correctness: `{stage331.get('correctness', '')}`, samples: `{stage331.get('samples', '')}`;
- final-output noise/equivalence: `{stage331.get('noise_pair_failures', '')}/{stage331.get('noise_trials', '')}` pair failures;
- max RSS: `{stage331.get('time_maxrss_kb', '')}` KB.

Important boundaries:

- metric is per-lane amortized complete bootstrapping throughput, not single
  scalar bootstrap latency;
- exact dense/local-layout routes are closed under current evidence;
- selector-transpose reached only isolated/projection-level neutral evidence
  and is not promoted;
- compact/structured product-count reduction remains proof-blocked;
- no theoretical optimality, novelty, or all-parameter claim is supported yet.

Primary evidence:

- `repro/stage331_current_head_highstat_refresh/summary.csv`
- `repro/stage331_current_head_highstat_refresh/perf_summary.csv`
- `repro/stage331_current_head_highstat_refresh/noise_summary.csv`
- `repro/stage332_paper_result_pack/paper_result_table.csv`
""")

    write_text(THEORY, """# Stage332 Claim Boundary Model

Stage332 separates three claim levels.

1. Supported scoped systems result: complete `T_bootstrap/r` for the measured
   parameter/backend/path, with correctness/noise/resource evidence.
2. Open algorithmic optimality: no proof shows that the current exact dense
   MAT/RLWE path is optimal among all PVW/MAT-SAB schedules.
3. Open novelty/security: compact selector and literature novelty claims remain
   blocked until proof and related-work verification are complete.

The paper-safe statement must use the amortized per-bit/lane metric and must
not cite isolated kernel speedups as final bootstrapping acceleration.
""")

    write_text(VARIANT, f"""# mat_rlwe_sab_stage332_paper_claim_card

## Summary

- Parent algorithm: direct PVW/MAT-SAB for 2025/686 sparse amortized
  bootstrapping.
- Focused module: scoped result packaging.
- Optimization target: complete `T_bootstrap/r`.
- Status: `{DECISION if pass_gate else 'FAIL_STAGE332_STAGE331_INPUT_NOT_PASS'}`.

## Paper-Safe Claim

For `BINARY SET_2_3_2048` include-zero on `spqlios_avx512`, `r=4` direct
PVW/MAT-SAB achieves `{speedup:.6f}x` amortized complete-SAB throughput over
repeated scalar SAB, measured by `T_bootstrap/r`.

## Required Boundaries

- Do not claim single-bootstrap latency speedup.
- Do not claim theoretical optimality.
- Do not claim compact selector security or acceleration.
- Do not claim novelty until Stage333 verifies real related work.
""")

    write_text(PLAN, """# Stage333 Literature/Novelty Or Compact Security Plan

Route A: literature and novelty verification.

- Build a verified related-work matrix for 2025/686 SAB, PVW/MAT external
  products, multi-output bootstrapping, and SIMD FHE kernels.
- Use only real papers and source-checked claims.
- Mark novelty as open until citations support the exact contribution boundary.

Route B: compact keygen/security preflight.

- Map compact selector equations to production key generation.
- Close public distribution, semantic-zero, and noise recurrence obligations.
- Only then admit isolated code; full SAB code requires correctness/noise/RSS
  and `T_bootstrap/r` A/B gates.
""")

    write_text(COMMANDS, """# Stage332 Reproduction Commands

```sh
python scripts/build_stage332_paper_result_pack.py
```

Inputs:

- `repro/stage331_current_head_highstat_refresh/summary.csv`
- `repro/stage331_current_head_highstat_refresh/perf_summary.csv`
- `repro/stage331_current_head_highstat_refresh/noise_summary.csv`
""")

    write_text(REPORT, read_text(DOC))

    append_once(GOAL, "<!-- stage332-paper-result-pack -->", f"""
<!-- stage332-paper-result-pack -->
### Stage332 paper result pack

`{DECISION if pass_gate else 'FAIL_STAGE332_STAGE331_INPUT_NOT_PASS'}` packages
the current scoped systems result: direct PVW/MAT-SAB speedup
`{stage331.get('speedup_vs_repeated_scalar_mean', '')}x` by complete
`T_bootstrap/r`, with correctness/noise/RSS evidence and explicit unsupported
claim boundaries.
""")

    append_once(ROADMAP, "<!-- stage332-paper-result-pack-roadmap -->", f"""
<!-- stage332-paper-result-pack-roadmap -->
## Stage 332: Paper Result Pack

Goal: convert the Stage331 current-head high-stat experiment into a scoped
paper/report result table and claim boundary.

Status: `{DECISION if pass_gate else 'FAIL_STAGE332_STAGE331_INPUT_NOT_PASS'}`.
""")

    append_once(HYPOTHESES, "H332_paper_result_pack:", f"""
H332_paper_result_pack:
  status: {DECISION if pass_gate else 'FAIL_STAGE332_STAGE331_INPUT_NOT_PASS'}
  primary_metric: complete_sab_T_bootstrap_over_r_vs_repeated_scalar
  evidence:
    - repro/stage332_paper_result_pack/summary.csv
    - repro/stage332_paper_result_pack/paper_result_table.csv
    - repro/stage332_paper_result_pack/claim_boundary.csv
    - doc/pvw_mat_sab_scoped_result_table_stage332.md
  conclusion: >
    Stage332 packages the current scoped systems result and keeps novelty,
    theoretical optimality, all-parameter generality, and compact security open.
""")

    append_once(MANIFEST, "<!-- stage332-paper-result-pack-manifest -->", """
<!-- stage332-paper-result-pack-manifest -->
- stage332_paper_result_pack:
  - `docs/stage332_paper_result_pack.md`
  - `docs/current_pvw_mat_sab_result.md`
  - `doc/pvw_mat_sab_scoped_result_table_stage332.md`
  - `theory_checks/stage332_claim_boundary_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage332_paper_claim_card.md`
  - `experiments/stage333_literature_novelty_or_compact_security_plan.md`
  - `scripts/build_stage332_paper_result_pack.py`
  - `repro/stage332_paper_result_pack/`
""")

    append_once(CHECKLIST, "<!-- stage332-paper-result-pack-checklist -->", f"""
<!-- stage332-paper-result-pack-checklist -->
- [x] Stage332 records `{DECISION if pass_gate else 'FAIL_STAGE332_STAGE331_INPUT_NOT_PASS'}` and updates the current PVW/MAT-SAB result table.
""")

    append_run_log()

    artifact_index([
        DOC, CURRENT, TABLE, THEORY, VARIANT, PLAN, BUILDER, SUMMARY,
        RESULT_TABLE, CLAIM_BOUNDARY, OPEN_ITEMS, PROOF, NEXT, COMMANDS, REPORT,
    ])
    return 0 if pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
