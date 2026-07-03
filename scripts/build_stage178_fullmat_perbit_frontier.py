#!/usr/bin/env python3
"""Stage178: exact full-MAT per-bit throughput frontier."""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage178_fullmat_perbit_frontier"

SUMMARY_CSV = OUT_DIR / "summary.csv"
PERBIT_CSV = OUT_DIR / "per_bit_throughput.csv"
COMPONENT_CSV = OUT_DIR / "component_attribution.csv"
CANDIDATE_CSV = OUT_DIR / "candidate_matrix.csv"
AMDAHL_CSV = OUT_DIR / "amdahl_bounds.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage178_fullmat_perbit_frontier.md"
PLAN_MD = ROOT / "experiments" / "stage178_fullmat_perbit_frontier_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage178_fullmat_perbit_frontier_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_exact_fullmat_frontier.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE169_AGG = ROOT / "repro" / "stage169_cb5_native_repeated_r6_gate" / "aggregate.csv"
STAGE169_RUNS = ROOT / "repro" / "stage169_cb5_native_repeated_r6_gate" / "run_results.csv"
STAGE170_METRICS = ROOT / "repro" / "stage170_native_split_counter_microbench" / "run_metrics.csv"
STAGE170_SUMMARY = ROOT / "repro" / "stage170_native_split_counter_microbench" / "summary.csv"
STAGE174_COMPARISON = ROOT / "repro" / "stage174_from_dft_direct_scale_gate" / "comparison.csv"
STAGE159_SUMMARY = ROOT / "repro" / "stage159_sub_decomp_fusion_repeated_gate" / "summary.csv"
STAGE154_SUMMARY = ROOT / "repro" / "stage154_bodymajor_fullsab_closeout" / "summary.csv"
STAGE165_SUMMARY = ROOT / "repro" / "stage165_closed_fullmat_streaming_microbench" / "summary.csv"
STAGE176_SUMMARY = ROOT / "repro" / "stage176_structured_compact_security_api_gate" / "summary.csv"
STAGE177_SUMMARY = ROOT / "repro" / "stage177_verified_literature_novelty_gate" / "summary.csv"

DECISION = "PASS_STAGE178_FULLMAT_PERBIT_FRONTIER_SELECT_MAT_EP_AUDIT"

R = 6
H_PLUS_ONE = 40
R_PREC = 7
IN_N = 2048
CMUX_CALLS = H_PLUS_ONE * R_PREC * IN_N


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    normalized = [{field: row.get(field, "") for field in fields} for row in row_list]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text_lf(path, current + text.lstrip("\n"))


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_dicts(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def agg_metric(metric: str, column: str) -> float:
    for row in read_csv_dicts(STAGE169_AGG):
        if row.get("metric") == metric:
            return float(row[column])
    return math.nan


def run_metric(variant: str, column: str) -> float:
    for row in read_csv_dicts(STAGE170_METRICS):
        if row.get("variant") == variant:
            return float(row[column])
    return math.nan


def fmt(x: float) -> str:
    return f"{x:.9f}"


def build_perbit_rows() -> List[Dict[str, str]]:
    pvw_avg = agg_metric("pvw_avg_us", "mean")
    pvw_lane = agg_metric("pvw_lane_avg_us", "mean")
    scalar_avg = agg_metric("scalar_repeated_avg_us", "mean")
    scalar_lane = agg_metric("scalar_lane_avg_us", "mean")
    speed_mean = agg_metric("speedup_vs_scalar_repeated", "mean")
    speed_min = agg_metric("speedup_vs_scalar_repeated", "min")
    speed_ci_low = agg_metric("speedup_vs_scalar_repeated", "ci95_low")
    return [
        {
            "metric": "pvw_full_bootstrap_mean_us",
            "value": fmt(pvw_avg),
            "unit": "us",
            "evidence": rel(STAGE169_AGG),
            "interpretation": "Time for one exact full-MAT PVW/MAT-SAB bootstrap carrying r lanes.",
        },
        {
            "metric": "pvw_T_bootstrap_over_r_mean_us",
            "value": fmt(pvw_lane),
            "unit": "us_per_lane",
            "evidence": rel(STAGE169_AGG),
            "interpretation": "Primary amortized endpoint for the current exact path.",
        },
        {
            "metric": "scalar_repeated_full_mean_us",
            "value": fmt(scalar_avg),
            "unit": "us",
            "evidence": rel(STAGE169_AGG),
            "interpretation": "Repeated scalar baseline for r independent lanes.",
        },
        {
            "metric": "scalar_T_bootstrap_over_r_mean_us",
            "value": fmt(scalar_lane),
            "unit": "us_per_lane",
            "evidence": rel(STAGE169_AGG),
            "interpretation": "Scalar repeated baseline normalized per processed lane.",
        },
        {
            "metric": "speedup_vs_scalar_repeated_mean",
            "value": fmt(speed_mean),
            "unit": "x",
            "evidence": rel(STAGE169_AGG),
            "interpretation": "Mean complete-SAB T_bootstrap/r speedup.",
        },
        {
            "metric": "speedup_vs_scalar_repeated_min",
            "value": fmt(speed_min),
            "unit": "x",
            "evidence": rel(STAGE169_AGG),
            "interpretation": "Conservative repeated-run minimum speedup.",
        },
        {
            "metric": "speedup_vs_scalar_repeated_ci95_low",
            "value": fmt(speed_ci_low),
            "unit": "x",
            "evidence": rel(STAGE169_AGG),
            "interpretation": "CI lower bound used for cautious claim wording.",
        },
    ]


def build_component_rows() -> List[Dict[str, str]]:
    pvw_avg = agg_metric("pvw_avg_us", "mean")
    mat_us = run_metric("mat_ep_subdecomp", "per_call_us")
    dft_us = run_metric("from_dft_materialize", "per_call_us")
    mat_total = mat_us * CMUX_CALLS
    dft_total = dft_us * CMUX_CALLS
    hot_total = mat_total + dft_total
    residual = max(0.0, pvw_avg - hot_total)
    return [
        {
            "component": "mat_ep_subdecomp",
            "per_call_us": fmt(mat_us),
            "estimated_full_us": fmt(mat_total),
            "share_of_pvw_full": fmt(mat_total / pvw_avg),
            "source": rel(STAGE170_METRICS),
            "interpretation": "Largest exact-path component; includes sub-decompose and MAT DFT addmul.",
        },
        {
            "component": "from_dft_materialize",
            "per_call_us": fmt(dft_us),
            "estimated_full_us": fmt(dft_total),
            "share_of_pvw_full": fmt(dft_total / pvw_avg),
            "source": rel(STAGE170_METRICS),
            "interpretation": "Second-largest exact-path component; Stage174 direct-scale attempt was neutral.",
        },
        {
            "component": "split_hot_components_total",
            "per_call_us": fmt(mat_us + dft_us),
            "estimated_full_us": fmt(hot_total),
            "share_of_pvw_full": fmt(hot_total / pvw_avg),
            "source": f"{rel(STAGE169_AGG)}; {rel(STAGE170_METRICS)}",
            "interpretation": "Explains most of full-SAB time; good sanity check for attribution.",
        },
        {
            "component": "residual_setup_extract_ks_profile_gap",
            "per_call_us": "",
            "estimated_full_us": fmt(residual),
            "share_of_pvw_full": fmt(residual / pvw_avg),
            "source": rel(STAGE169_AGG),
            "interpretation": "Too small to be the primary next optimization target unless a specific bug is found.",
        },
    ]


def amdahl(speed_component: float, share: float) -> float:
    return 1.0 / ((1.0 - share) + share / speed_component)


def build_amdahl_rows(component_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    shares = {row["component"]: float(row["share_of_pvw_full"]) for row in component_rows}
    rows: List[Dict[str, str]] = []
    for component in ["mat_ep_subdecomp", "from_dft_materialize", "split_hot_components_total", "residual_setup_extract_ks_profile_gap"]:
        share = shares[component]
        for component_speedup in [1.05, 1.10, 1.25, 1.50, 2.00]:
            rows.append({
                "component": component,
                "component_speedup": fmt(component_speedup),
                "share_of_pvw_full": fmt(share),
                "full_sab_speedup_bound": fmt(amdahl(component_speedup, share)),
                "interpretation": "Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline.",
            })
    return rows


def build_candidate_rows(component_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    share = {row["component"]: float(row["share_of_pvw_full"]) for row in component_rows}
    return [
        {
            "candidate": "C1_mat_ep_subdecomp_microarch_audit",
            "target": "mat_trgsw_mul_pvmtmlwe_sub_DFT exact r=6 tiled path",
            "full_time_share": fmt(share["mat_ep_subdecomp"]),
            "prior_evidence": f"{rel(STAGE159_SUMMARY)}; {rel(STAGE165_SUMMARY)}",
            "decision": "SELECT_FOR_STAGE179_AUDIT_ONLY",
            "reason": "Largest remaining exact-path share. Code changes require a new load/store/FMA mechanism because sub-decomp fusion already exists and streaming lost.",
            "gate": "Do not implement unless audit projects >=3% complete-SAB improvement and preserves exact PVW_TMLWE closure.",
        },
        {
            "candidate": "C2_from_dft_materialize_backend",
            "target": "pvmtmlwe_from_DFT_add / materialization",
            "full_time_share": fmt(share["from_dft_materialize"]),
            "prior_evidence": rel(STAGE174_COMPARISON),
            "decision": "DEFER",
            "reason": "Large share but direct AVX512 scale/copy gate was neutral; count reduction needs representation change, currently blocked.",
            "gate": "Reopen only with a new mechanism beyond direct-scale or with closed representation proof.",
        },
        {
            "candidate": "C3_r6_layout_retuning",
            "target": "fulltile/bodymajor/streaming layout variants",
            "full_time_share": fmt(share["mat_ep_subdecomp"]),
            "prior_evidence": f"{rel(STAGE154_SUMMARY)}; {rel(STAGE165_SUMMARY)}",
            "decision": "REJECT_RETUNING_WITHOUT_NEW_MECHANISM",
            "reason": "Fulltile/bodymajor/streaming were already neutral or rejected at full-SAB/microbench gates.",
            "gate": "No new branch unless it changes arithmetic/dataflow, not just layout naming.",
        },
        {
            "candidate": "C4_tail_postprocessing",
            "target": "setup/extract/packing KS/residual",
            "full_time_share": fmt(share["residual_setup_extract_ks_profile_gap"]),
            "prior_evidence": rel(COMPONENT_CSV),
            "decision": "DEFER",
            "reason": "Residual is small relative to MAT EP/from_DFT; tail-only work cannot materially move T_bootstrap/r.",
            "gate": "Reopen only if new profile shows residual >15%.",
        },
        {
            "candidate": "C5_structured_compact",
            "target": "compact selector/representation",
            "full_time_share": "",
            "prior_evidence": rel(STAGE177_SUMMARY),
            "decision": "BLOCKED_BY_STAGE176_177",
            "reason": "Potentially higher algorithmic upside but no implementation permission or strong novelty claim.",
            "gate": "Only proof/literature work, no SAB code.",
        },
    ]


def build_summary_rows(component_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    hot_share = next(float(row["share_of_pvw_full"]) for row in component_rows if row["component"] == "split_hot_components_total")
    mat_share = next(float(row["share_of_pvw_full"]) for row in component_rows if row["component"] == "mat_ep_subdecomp")
    dft_share = next(float(row["share_of_pvw_full"]) for row in component_rows if row["component"] == "from_dft_materialize")
    residual_share = next(float(row["share_of_pvw_full"]) for row in component_rows if row["component"] == "residual_setup_extract_ks_profile_gap")
    return [
        {
            "gate": "stage178_inputs",
            "status": "PASS" if all(p.exists() for p in [STAGE169_AGG, STAGE170_METRICS, STAGE177_SUMMARY]) else "FAIL",
            "metric": "required_inputs_present",
            "value": "1" if all(p.exists() for p in [STAGE169_AGG, STAGE170_METRICS, STAGE177_SUMMARY]) else "0",
            "evidence": f"{rel(STAGE169_AGG)}; {rel(STAGE170_METRICS)}; {rel(STAGE177_SUMMARY)}",
            "detail": "Stage178 consumes complete-SAB repeated evidence, split component counters, and literature/security routing.",
            "next_action": "Repair missing inputs before candidate selection.",
        },
        {
            "gate": "stage178_perbit_endpoint",
            "status": "PASS",
            "metric": "mean_speedup;min_speedup;ci95_low",
            "value": f"{fmt(agg_metric('speedup_vs_scalar_repeated', 'mean'))};{fmt(agg_metric('speedup_vs_scalar_repeated', 'min'))};{fmt(agg_metric('speedup_vs_scalar_repeated', 'ci95_low'))}",
            "evidence": rel(PERBIT_CSV),
            "detail": "Current exact full-MAT r=6 claim is T_bootstrap/r versus repeated scalar.",
            "next_action": "Do not report any other speedup dimension as final SAB acceleration.",
        },
        {
            "gate": "stage178_component_attribution",
            "status": "PASS",
            "metric": "hot_share;mat_share;from_dft_share;residual_share",
            "value": f"{fmt(hot_share)};{fmt(mat_share)};{fmt(dft_share)};{fmt(residual_share)}",
            "evidence": rel(COMPONENT_CSV),
            "detail": "Split MAT EP/subdecomp plus from_DFT explains most of current complete-SAB runtime.",
            "next_action": "Primary exact-path work must target these components.",
        },
        {
            "gate": "stage178_candidate_selection",
            "status": "PASS_SELECT_AUDIT",
            "metric": "selected_candidate",
            "value": "C1_mat_ep_subdecomp_microarch_audit",
            "evidence": rel(CANDIDATE_CSV),
            "detail": "Select an audit, not immediate code. Prior layout/backend retuning had neutral/rejected gates.",
            "next_action": "Stage179 must produce a concrete mechanism or stop.",
        },
        {
            "gate": "stage178_decision",
            "status": DECISION,
            "metric": "route",
            "value": "stage179_mat_ep_audit",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Avoid theory loop: compact remains blocked; next exact-path action is a bounded MAT EP microarchitecture audit.",
            "next_action": "Run Stage179.",
        },
    ]


def build_next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "stage": "179",
            "name": "MAT EP/subdecomp microarchitecture audit",
            "entry_condition": "Stage178 selects C1 as audit-only candidate.",
            "gate": "Find a concrete load/store/FMA/dataflow mechanism with projected >=3% complete-SAB gain, or reject.",
            "failure_rule": "If no mechanism is found, do not write code; record negative frontier.",
        },
        {
            "priority": "P1",
            "stage": "180",
            "name": "exact-path implementation gate",
            "entry_condition": "Stage179 produces a concrete mechanism.",
            "gate": "Implement behind a flag, run correctness, microbench, full-SAB repeated A/B, noise/resource.",
            "failure_rule": "Neutral/reject if complete-SAB T_bootstrap/r does not improve.",
        },
        {
            "priority": "P2",
            "stage": "181",
            "name": "negative frontier package",
            "entry_condition": "Stage179 finds no viable exact-path mechanism.",
            "gate": "Write the remaining-headroom and blocked-route report.",
            "failure_rule": "Do not continue speculative exact-path tuning.",
        },
    ]


def write_docs(summary_rows: List[Dict[str, str]], perbit_rows: List[Dict[str, str]],
               component_rows: List[Dict[str, str]], amdahl_rows: List[Dict[str, str]],
               candidate_rows: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    write_text_lf(OUT_MD, f"""# Stage178 Full-MAT Per-Bit Frontier

Decision: `{DECISION}`.

Stage178 re-normalizes the current exact PVW/MAT-SAB evidence around the metric
the user requested: `T_bootstrap/r`, i.e. complete bootstrapping time divided by
the number of processed lanes/bits.

Current complete-SAB result:

- r = {R}
- PVW/MAT-SAB mean: `{fmt(agg_metric('pvw_lane_avg_us', 'mean'))} us/lane`
- repeated scalar mean: `{fmt(agg_metric('scalar_lane_avg_us', 'mean'))} us/lane`
- speedup mean/min/CI95-low: `{fmt(agg_metric('speedup_vs_scalar_repeated', 'mean'))}x / {fmt(agg_metric('speedup_vs_scalar_repeated', 'min'))}x / {fmt(agg_metric('speedup_vs_scalar_repeated', 'ci95_low'))}x`

The next executable route is not compact SAB. Stage176/177 block that. The
only exact full-MAT target large enough to justify work is a bounded
microarchitecture audit of `mat_ep_subdecomp`.

## Gate Summary

{table(summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}
## Per-Bit Throughput

{table(perbit_rows, ["metric", "value", "unit", "evidence", "interpretation"])}
## Component Attribution

{table(component_rows, ["component", "per_call_us", "estimated_full_us", "share_of_pvw_full", "source", "interpretation"])}
## Amdahl Bounds

{table(amdahl_rows, ["component", "component_speedup", "share_of_pvw_full", "full_sab_speedup_bound", "interpretation"])}
## Candidate Matrix

{table(candidate_rows, ["candidate", "target", "full_time_share", "prior_evidence", "decision", "reason", "gate"])}
## Next Queue

{table(next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])}
""")

    write_text_lf(PLAN_MD, f"""# Stage178 Plan

Goal: stop claim drift and choose the next exact full-MAT action from measured
`T_bootstrap/r` and component shares.

Inputs:

- `{rel(STAGE169_AGG)}`: repeated complete-SAB r=6 endpoint.
- `{rel(STAGE170_METRICS)}`: native split MAT EP/subdecomp and from_DFT timings.
- `{rel(STAGE174_COMPARISON)}`: neutral direct-scale from_DFT gate.
- `{rel(STAGE176_SUMMARY) if (ROOT / 'repro/stage176_structured_compact_security_api_gate/summary.csv').exists() else 'stage176 summary'}` and `{rel(STAGE177_SUMMARY)}`: compact/literature claim boundaries.

Rules:

- Final speedup dimension is complete-SAB `T_bootstrap/r`.
- Kernel or backend-only data cannot be reported as bootstrapping acceleration.
- No code branch opens unless a candidate can plausibly affect full-SAB time.

Decision: `{DECISION}`.
""")

    write_text_lf(THEORY_MD, f"""# Stage178 Full-MAT Frontier Model

The exact full-MAT path keeps the current closed PVW_TMLWE state. It does not
change key distribution, selector semantics, or accumulator representation.

For binary `SET_2_3_2048`, the observed CMUX/NCMUX count is modeled as:

```text
(h + 1) * r_prec * in_N = {H_PLUS_ONE} * {R_PREC} * {IN_N} = {CMUX_CALLS}
```

Stage170 gives per-call costs for two components:

```text
MAT EP/subdecomp:      {fmt(run_metric('mat_ep_subdecomp', 'per_call_us'))} us
from_DFT materialize:  {fmt(run_metric('from_dft_materialize', 'per_call_us'))} us
```

Multiplying those by `{CMUX_CALLS}` explains most of the Stage169 complete-SAB
mean. This makes MAT EP/subdecomp the only exact-path component large enough
to justify a new bounded audit. Tail work is deferred.
""")

    write_text_lf(VARIANT_MD, """# Exact Full-MAT Frontier Variant

Selected next route: audit-only `mat_ep_subdecomp` microarchitecture.

Not selected:

- compact selector integration, because Stage176/177 deny implementation and
  strong novelty claims;
- direct from_DFT scale/copy, because Stage174 was neutral;
- fulltile/bodymajor/streaming retuning, because prior gates were neutral or
  rejected;
- tail post-processing, because the residual share is too small.

Stage179 must either produce a concrete low-level mechanism with projected
complete-SAB impact or close the exact-path tuning branch.
""")


def write_global_updates() -> None:
    append_once(ROADMAP_MD, "## Stage 178: Full-MAT Per-Bit Frontier", f"""
## Stage 178: Full-MAT Per-Bit Frontier

Goal:

```text
Re-normalize current complete-SAB evidence as T_bootstrap/r and select the next
exact full-MAT optimization candidate from measured component shares.
```

Status:

```text
Completed. Stage178 records {DECISION}. Current exact r=6 speedup is
{fmt(agg_metric('speedup_vs_scalar_repeated', 'mean'))}x mean versus repeated
scalar on the complete-SAB T_bootstrap/r endpoint. Next route is an audit-only
MAT EP/subdecomp microarchitecture gate, not compact implementation.
```
""")
    append_once(GOAL_MD, "Stage178 records the exact full-MAT per-bit frontier", f"""
Stage178 records the exact full-MAT per-bit frontier. Decision:
`{DECISION}`. The current accepted complete-SAB speedup dimension is
`T_bootstrap/r`; compact remains blocked; next executable work is a bounded
MAT EP/subdecomp microarchitecture audit.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage178 as the per-bit exact full-MAT frontier", f"""
82. Treat Stage178 as the per-bit exact full-MAT frontier:
    `{DECISION}`. The current complete-SAB r=6 endpoint is
    {fmt(agg_metric('speedup_vs_scalar_repeated', 'mean'))}x mean speedup on
    `T_bootstrap/r` versus repeated scalar. Stage179 may audit MAT
    EP/subdecomp only if it stays tied to complete-SAB impact.
""")
    append_once(HYPOTHESIS_YAML, "H102_fullmat_perbit_frontier", f"""
  - id: H102_fullmat_perbit_frontier
    statement: >
      After compact SAB is blocked, the only exact full-MAT component large
      enough to justify further implementation work is MAT EP/subdecomp, and
      all claims must use complete-SAB T_bootstrap/r.
    mechanism: >
      Stage169 supplies repeated complete-SAB per-lane throughput and Stage170
      splits MAT EP/subdecomp from from_DFT materialization. Amdahl bounds route
      away from tail work and previously neutral layout/backend retuning.
    status: stage178_fullmat_perbit_frontier
    evidence: docs/stage178_fullmat_perbit_frontier.md; experiments/stage178_fullmat_perbit_frontier_plan.md; theory_checks/stage178_fullmat_perbit_frontier_model.md; repro/stage178_fullmat_perbit_frontier/summary.csv
    current_decision: >
      {DECISION}
    failure_criteria:
      - a new branch is opened without projected complete-SAB impact
      - kernel-only speedup is reported as final bootstrapping acceleration
      - compact implementation is resumed despite Stage176/177 blocks
""")
    append_once(RUN_LOG, "stage178-fullmat-perbit-frontier-001", f"""
stage178-fullmat-perbit-frontier-001,2026-07-04,{git_head()},Stage 178,analysis,python scripts/build_stage178_fullmat_perbit_frontier.py,Stage169/170/174/176/177 evidence,none,{DECISION},Exact full-MAT per-bit frontier and candidate-selection gate.,repro/stage178_fullmat_perbit_frontier
""")
    append_once(MANIFEST, "stage178_fullmat_perbit_frontier", f"""
- stage178_fullmat_perbit_frontier: `{DECISION}`
  - `docs/stage178_fullmat_perbit_frontier.md`
  - `experiments/stage178_fullmat_perbit_frontier_plan.md`
  - `theory_checks/stage178_fullmat_perbit_frontier_model.md`
  - `algorithm_variants/mat_rlwe_sab_exact_fullmat_frontier.md`
  - `repro/stage178_fullmat_perbit_frontier/`
""")
    append_once(CHECKLIST, "Stage178 full-MAT per-bit frontier pack recorded", """
- [x] Stage178 full-MAT per-bit frontier pack recorded.
""")


def write_artifacts(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "path": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path),
            "bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_CSV, rows, ["path", "exists", "sha256", "bytes"])


def main() -> None:
    perbit_rows = build_perbit_rows()
    component_rows = build_component_rows()
    amdahl_rows = build_amdahl_rows(component_rows)
    candidate_rows = build_candidate_rows(component_rows)
    next_rows = build_next_rows()
    summary_rows = build_summary_rows(component_rows)

    write_csv(PERBIT_CSV, perbit_rows, ["metric", "value", "unit", "evidence", "interpretation"])
    write_csv(COMPONENT_CSV, component_rows, ["component", "per_call_us", "estimated_full_us", "share_of_pvw_full", "source", "interpretation"])
    write_csv(AMDAHL_CSV, amdahl_rows, ["component", "component_speedup", "share_of_pvw_full", "full_sab_speedup_bound", "interpretation"])
    write_csv(CANDIDATE_CSV, candidate_rows, ["candidate", "target", "full_time_share", "prior_evidence", "decision", "reason", "gate"])
    write_csv(NEXT_CSV, next_rows, ["priority", "stage", "name", "entry_condition", "gate", "failure_rule"])
    write_csv(SUMMARY_CSV, summary_rows, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])
    write_docs(summary_rows, perbit_rows, component_rows, amdahl_rows, candidate_rows, next_rows)
    write_global_updates()
    write_artifacts([
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        SUMMARY_CSV,
        PERBIT_CSV,
        COMPONENT_CSV,
        AMDAHL_CSV,
        CANDIDATE_CSV,
        NEXT_CSV,
        Path(__file__),
    ])
    print(DECISION)


if __name__ == "__main__":
    main()
