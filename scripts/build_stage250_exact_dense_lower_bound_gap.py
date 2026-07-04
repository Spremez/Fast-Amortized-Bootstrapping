"""Stage250: exact dense lower-bound gap refresh.

This stage refreshes the lower-bound/optimality boundary for the supported exact
dense PVW/MAT-SAB route.  It consumes existing complete-SAB timing, profile,
split, and native counter evidence.  It records which parts are measured and
which are still open, without claiming theoretical optimality.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage250_exact_dense_lower_bound_gap"

INPUTS = {
    "stage249_proof_gate": ROOT / "repro" / "stage249_structured_compact_distribution_security" / "proof_gate.csv",
    "stage236_selected_binary": ROOT / "repro" / "stage236_set_2_3_4096_r4_highstat_slice" / "selected_binary_matrix_summary.csv",
    "stage224_perf_refresh": ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "perf_comparison.csv",
    "stage208_profile": ROOT / "repro" / "stage208_current_head_profile_refresh" / "component_attribution.csv",
    "stage209_split": ROOT / "repro" / "stage209_current_head_mat_ep_split" / "split_projection.csv",
    "stage226_attribution": ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "attribution_summary.csv",
    "stage226_counters": ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "counter_summary.csv",
    "stage166_term_model": ROOT / "repro" / "stage166_shared_output_compact_algebra_gate" / "term_model.csv",
    "optimality_model": ROOT / "theory_checks" / "mat_rlwe_sab_amortized_optimality.md",
}

DOC = ROOT / "docs" / "stage250_exact_dense_lower_bound_gap.md"
PLAN = ROOT / "experiments" / "stage250_exact_dense_lower_bound_gap_plan.md"
THEORY = ROOT / "theory_checks" / "stage250_exact_dense_lower_bound_gap_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage250_exact_dense_lower_bound_gap.md"

INPUT_STATUS = OUT / "input_status.csv"
PERFORMANCE = OUT / "performance_endpoint_matrix.csv"
LOWER_BOUND = OUT / "lower_bound_component_matrix.csv"
COUNTER = OUT / "counter_gap_matrix.csv"
CLAIM = OUT / "claim_boundary.csv"
GATES = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage250_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE250_EXACT_DENSE_GAP_REFRESH_OPTIMALITY_OPEN"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip() + "\n")


def append_once(path: Path, marker: str, text: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip("\n").rstrip() + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table(rows: list[dict[str, object]], fields: list[str]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines) + "\n"


def input_rows() -> list[dict[str, object]]:
    return [
        {
            "input_id": key,
            "path": rel(path),
            "status": "present" if path.exists() else "missing",
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for key, path in INPUTS.items()
    ]


def performance_rows() -> list[dict[str, object]]:
    rows = []
    for row in read_csv(INPUTS["stage236_selected_binary"]):
        rows.append({
            "source": row.get("stage", ""),
            "param": row.get("param", ""),
            "r": row.get("r", ""),
            "endpoint": "complete-SAB T_bootstrap/r",
            "mean_speedup": row.get("mean_speedup", ""),
            "ci95_low": row.get("speedup_ci95_low", ""),
            "ci95_high": row.get("speedup_ci95_high", ""),
            "noise_failures": row.get("noise_failures", ""),
            "status": row.get("status", ""),
            "claim_use": "selected_binary_timing_evidence_not_optimality",
        })
    for row in read_csv(INPUTS["stage224_perf_refresh"]):
        rows.append({
            "source": "Stage224 r6 exact refresh",
            "param": "explicit_r6_route",
            "r": "6",
            "endpoint": "complete-SAB T_bootstrap/r",
            "mean_speedup": row.get("backend_mean_speedup_vs_scalar", ""),
            "ci95_low": "not_highstat_3run",
            "ci95_high": "not_highstat_3run",
            "noise_failures": "inherited Stage148 side condition",
            "status": row.get("decision", ""),
            "claim_use": "engineering_refresh_not_highstat_optimality",
        })
    return rows


def lower_bound_rows() -> list[dict[str, object]]:
    rows = [
        {
            "component": "schedule_count",
            "measured_or_model": "S=(h+1)*rho*N; target binary S=573440",
            "evidence": "theory_checks/mat_rlwe_sab_amortized_optimality.md; repro/stage208_current_head_profile_refresh/component_attribution.csv",
            "closed_status": "measured_for_target_schedule",
            "gap_effect": "schedule count is fixed; optimization must reduce per-call cost or tail",
            "next_action": "preserve same schedule count in all A/B tests",
        },
        {
            "component": "mat_ep_primary_share",
            "measured_or_model": "Stage208 MAT EP is 40.879% of CMUX for r=2 and 47.760% for r=4",
            "evidence": "repro/stage208_current_head_profile_refresh/component_attribution.csv",
            "closed_status": "profile_attribution_only",
            "gap_effect": "MAT EP remains the largest measurable body-path term",
            "next_action": "do not optimize postproc first; require split/counter-backed MAT EP mechanism",
        },
        {
            "component": "postproc_tail",
            "measured_or_model": "Stage208 tail max is below 2%",
            "evidence": "repro/stage208_current_head_profile_refresh/component_attribution.csv",
            "closed_status": "defer",
            "gap_effect": "tail cannot explain multi-fold remaining gap today",
            "next_action": "reopen only after body-path change",
        },
        {
            "component": "body_linear_proxy",
            "measured_or_model": "Stage166 shared-output compact term proxy is smaller than dense",
            "evidence": "repro/stage166_shared_output_compact_algebra_gate/term_model.csv; repro/stage249_structured_compact_distribution_security/proof_gate.csv",
            "closed_status": "not_admissible_as_lower_bound",
            "gap_effect": "compact/body-linear proxy is blocked by distribution/security gates",
            "next_action": "do not use compact proxy as optimality proof",
        },
        {
            "component": "split_microbench_projection",
            "measured_or_model": "Stage209 split projection identifies DFT rows/sub-decompose/addmul shares",
            "evidence": "repro/stage209_current_head_mat_ep_split/split_projection.csv",
            "closed_status": "preflight_only",
            "gap_effect": "specific subcomponents are measurable, but no code permission or full-SAB gain yet",
            "next_action": "new exact code requires a counter-backed mechanism and full-SAB A/B",
        },
    ]
    for row in read_csv(INPUTS["stage166_term_model"]):
        rows.append({
            "component": f"term_model_r{row.get('r', '')}",
            "measured_or_model": f"dense={row.get('dense_terms_per_level', '')}; compact_proxy={row.get('shared_output_lane_local_terms', '')}; missing_cross={row.get('missing_cross_body_terms', '')}",
            "evidence": "repro/stage166_shared_output_compact_algebra_gate/term_model.csv",
            "closed_status": "model_only_compact_blocked",
            "gap_effect": "shows dense MAT risk but not an admissible implementation lower bound",
            "next_action": "cite as risk/model only",
        })
    return rows


def counter_rows() -> list[dict[str, object]]:
    attr = {row["metric"]: row for row in read_csv(INPUTS["stage226_attribution"])}
    rows = [
        {
            "metric": "backend_vs_wrapper_complete_sab_speedup",
            "value": attr.get("stage224_backend_vs_wrapper_mean_speedup", {}).get("value", ""),
            "status": "timing_refresh",
            "interpretation": "backend direct path is measurably better than wrapper in Stage224 repeated complete-SAB timing",
            "evidence": "repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv",
        },
        {
            "metric": "cycles_wrapper_over_backend",
            "value": attr.get("stage226_cycles_wrapper_over_backend", {}).get("value", ""),
            "status": "counter_attribution_only",
            "interpretation": "native counters support direction, not lower-bound tightness",
            "evidence": "repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv",
        },
        {
            "metric": "loads_wrapper_over_backend",
            "value": attr.get("stage226_loads_wrapper_over_backend", {}).get("value", ""),
            "status": "counter_attribution_only",
            "interpretation": "load reduction is small and does not prove theoretical optimum",
            "evidence": "repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv",
        },
        {
            "metric": "stores_wrapper_over_backend",
            "value": attr.get("stage226_stores_wrapper_over_backend", {}).get("value", ""),
            "status": "counter_attribution_only",
            "interpretation": "store reduction is small and does not prove theoretical optimum",
            "evidence": "repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv",
        },
        {
            "metric": "optimality_gap_numeric",
            "value": "not_closed",
            "status": "blocked",
            "interpretation": "no validated lower-bound denominator exists for A_impl/A_lower",
            "evidence": "theory_checks/stage250_exact_dense_lower_bound_gap_model.md",
        },
    ]
    return rows


def claim_rows() -> list[dict[str, object]]:
    return [
        {
            "claim": "exact_dense_speedup",
            "status": "supported_scoped",
            "allowed_wording": "Selected binary exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r under recorded gates.",
            "forbidden_wording": "This proves all-parameter or non-binary speedup.",
            "evidence": rel(PERFORMANCE),
        },
        {
            "claim": "exact_dense_optimality",
            "status": "blocked",
            "allowed_wording": "The lower-bound gap remains open; counters are attribution-only.",
            "forbidden_wording": "The exact dense implementation is theoretically optimal.",
            "evidence": rel(LOWER_BOUND),
        },
        {
            "claim": "compact_lower_bound",
            "status": "denied",
            "allowed_wording": "Compact/body-linear term models are risks or blocked proxies.",
            "forbidden_wording": "Use compact term counts as a lower bound for exact dense optimality.",
            "evidence": "repro/stage249_structured_compact_distribution_security/proof_gate.csv",
        },
        {
            "claim": "next_code_permission",
            "status": "denied_without_new_mechanism",
            "allowed_wording": "New exact hot-path code requires a counter-backed mechanism and full-SAB A/B gate.",
            "forbidden_wording": "Implement speculative AVX/MAT rewrites from current lower-bound tables.",
            "evidence": "repro/stage228_counter_driven_backend_kernel_search/proof_gate.csv",
        },
    ]


def gate_rows(inputs, perf, lower, counters, claims) -> list[dict[str, object]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    perf_ok = len(perf) >= 5 and all(row["endpoint"] == "complete-SAB T_bootstrap/r" for row in perf)
    lower_ok = any(row["component"] == "body_linear_proxy" and row["closed_status"] == "not_admissible_as_lower_bound" for row in lower)
    counter_ok = any(row["metric"] == "optimality_gap_numeric" and row["status"] == "blocked" for row in counters)
    claim_ok = any(row["claim"] == "exact_dense_optimality" and row["status"] == "blocked" for row in claims)
    decision_ok = inputs_ok and perf_ok and lower_ok and counter_ok and claim_ok
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "required inputs",
            "value": "all present" if inputs_ok else "missing",
            "evidence": rel(INPUT_STATUS),
            "interpretation": "Stage250 consumes compact freeze, selected timing, profile, split, and counters.",
        },
        {
            "gate": "G2_endpoint",
            "status": "PASS" if perf_ok else "FAIL",
            "metric": "performance rows use complete-SAB T_bootstrap/r",
            "value": len(perf),
            "evidence": rel(PERFORMANCE),
            "interpretation": "Performance evidence remains aligned with the MAT-RLWE/r-body metric.",
        },
        {
            "gate": "G3_lower_bound_boundary",
            "status": "PASS_GAP_OPEN" if lower_ok else "FAIL",
            "metric": "body-linear/compact proxy",
            "value": "not admissible",
            "evidence": rel(LOWER_BOUND),
            "interpretation": "Compact/body-linear models are not valid lower-bound proof for exact dense optimality.",
        },
        {
            "gate": "G4_counter_boundary",
            "status": "PASS_ATTRIBUTION_ONLY" if counter_ok else "FAIL",
            "metric": "numeric optimality gap",
            "value": "not closed",
            "evidence": rel(COUNTER),
            "interpretation": "Stage226 counters support implementation direction only.",
        },
        {
            "gate": "G5_claim_boundary",
            "status": "PASS_NO_OPTIMALITY_CLAIM" if claim_ok else "FAIL",
            "metric": "exact dense optimality",
            "value": "blocked",
            "evidence": rel(CLAIM),
            "interpretation": "No theoretical optimality claim is permitted.",
        },
        {
            "gate": "G6_stage250_decision",
            "status": DECISION if decision_ok else "FAIL_STAGE250_LOWER_BOUND_GAP",
            "metric": "decision",
            "value": DECISION if decision_ok else "FAIL_STAGE250_LOWER_BOUND_GAP",
            "evidence": rel(GATES),
            "interpretation": "Proceed to non-binary semantics or a new counter-backed exact mechanism, not speculative code.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage251_nonbinary_selector_semantics_preflight",
            "entry_condition": "Compact is frozen and exact dense optimality gap remains open without code permission.",
            "gate": "define ternary/include-zero PVW selector semantics and staged equivalence before implementation",
            "status": "selected_next",
            "failure_action": "keep non-binary PVW unsupported",
            "evidence": "repro/stage229_parameter_generalization_matrix/coverage_gaps.csv",
        },
        {
            "priority": "P1",
            "route": "new_exact_dense_counter_backed_mechanism",
            "entry_condition": "A concrete MAT EP/fromDFT/addmul mechanism with predicted full-SAB effect is proposed.",
            "gate": "isolated equivalence, native counters, complete-SAB T_bootstrap/r A/B, noise/resource",
            "status": "conditional",
            "failure_action": "do not edit hot path",
            "evidence": "repro/stage209_current_head_mat_ep_split/split_projection.csv",
        },
        {
            "priority": "P2",
            "route": "paper_claim_boundary_refresh",
            "entry_condition": "No new implementation route is selected.",
            "gate": "state scoped engineering result; optimality and compact/non-binary claims blocked",
            "status": "future_packaging",
            "failure_action": "remove unsupported optimality wording",
            "evidence": rel(CLAIM),
        },
    ]


def artifact_rows(paths: list[Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256(path) if path.exists() and path.is_file() else "",
            "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        })
    return rows


def write_docs(inputs, perf, lower, counters, claims, gates, nextq, head: str) -> None:
    write_text(DOC, f"""# Stage250 Exact Dense Lower-Bound Gap

Decision: `{gates[-1]["status"]}`.

Stage250 refreshes the exact dense PVW/MAT-SAB lower-bound boundary after the
compact route was frozen. It keeps the primary endpoint as complete-SAB
`T_bootstrap/r` and records that theoretical optimality remains open.

## Performance Endpoint Matrix

{table(perf, ["source", "param", "r", "endpoint", "mean_speedup", "ci95_low", "ci95_high", "noise_failures", "status", "claim_use"])}

## Lower-Bound Component Matrix

{table(lower, ["component", "measured_or_model", "evidence", "closed_status", "gap_effect", "next_action"])}

## Counter Gap Matrix

{table(counters, ["metric", "value", "status", "interpretation", "evidence"])}

## Claim Boundary

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}

## Inputs

{table(inputs, ["input_id", "path", "status", "bytes"])}

Generated from head `{head}`.
""")
    write_text(REPORT, f"""# Stage250 Report

Decision: `{gates[-1]["status"]}`.

Exact dense PVW/MAT-SAB has scoped complete-SAB `T_bootstrap/r` timing evidence
and counter attribution, but the numeric lower-bound gap is not closed.
Compact/body-linear term models cannot be used as lower bounds because compact
production was frozen by Stage249. No speculative exact hot-path code is
admitted without a new counter-backed mechanism.
""")
    write_text(PLAN, """# Stage250 Exact Dense Lower-Bound Gap Plan

## Objective

Refresh the exact dense optimality boundary after compact production is frozen.

## Gates

- Performance rows must use complete-SAB `T_bootstrap/r`.
- Compact/body-linear proxies must not be treated as admissible lower bounds.
- Native counters remain attribution-only unless tied to a formal lower bound.
- New code requires a concrete mechanism plus full-SAB A/B and noise/resource.
""")
    write_text(THEORY, """# Stage250 Exact Dense Lower-Bound Gap Model

The exact dense route currently has:

- measured complete-SAB amortized speedup on selected binary rows;
- profile evidence that MAT external product remains the largest CMUX term;
- native counter attribution for a backend-vs-wrapper implementation choice.

It does not have:

- a validated `A_lower(r)` denominator for `gap(r)=A_impl(r)/A_lower(r)`;
- an admissible compact/body-linear lower bound, because compact production is
  blocked by distribution/security gates;
- code permission for speculative AVX/MAT rewrites.

Therefore exact dense optimality remains open. Future lower-bound work must
produce measurable lower-bound components and tie them to counters/assembly and
complete-SAB A/B.
""")
    write_text(VARIANT, """# MAT-RLWE SAB Stage250 Exact Dense Gap Refresh

## Summary

- Parent algorithm: exact dense PVW/MAT-SAB.
- Focused module: lower-bound/optimality boundary.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: `scoped_speedup_supported`, `optimality_open`,
  `no_speculative_hotpath_code`.
- Main hypothesis: exact dense remains useful but not proven optimal.

## Required Experiments Before New Code

- isolated equivalence for any changed MAT EP/fromDFT/addmul mechanism;
- native counter evidence for the changed mechanism;
- repeated complete-SAB A/B with `T_bootstrap/r`;
- noise/resource side conditions.
""")
    write_text(REPRO_CMDS, f"""# Stage250 Reproduction Commands

```text
python scripts/build_stage250_exact_dense_lower_bound_gap.py
python -m py_compile scripts/build_stage250_exact_dense_lower_bound_gap.py
```

Decision: `{gates[-1]["status"]}`.
""")


def update_project_files(head: str, decision: str) -> None:
    append_once(ROADMAP, "## Stage 250: Exact Dense Lower-Bound Gap", f"""
## Stage 250: Exact Dense Lower-Bound Gap

Goal:

```text
Refresh the exact dense PVW/MAT-SAB lower-bound/optimality boundary after the
compact production route is frozen.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. Complete-SAB
`T_bootstrap/r` evidence remains scoped and positive, but exact dense
optimality is still open. Compact/body-linear term models are not admissible
lower bounds, and no speculative hot-path code is permitted without a new
counter-backed mechanism.
```
""")
    append_once(GOAL, "Stage250 exact dense lower-bound gap", f"""
- Stage250 exact dense lower-bound gap records `{decision}`: exact dense
  PVW/MAT-SAB keeps scoped complete-SAB `T_bootstrap/r` evidence, but the
  numeric lower-bound gap and theoretical optimality remain open.
""")
    append_once(CURRENT_GOAL, "### Stage250 exact dense lower-bound gap", f"""
### Stage250 exact dense lower-bound gap

`{decision}` records that exact dense optimality is not proven. The active goal
remains open for non-binary selector semantics, any future counter-backed exact
mechanism, and final paper/citation closure.
""")
    append_once(HYPOTHESES, "H10_stage250_exact_dense_lower_bound_gap:", f"""
H10_stage250_exact_dense_lower_bound_gap:
  status: exact_dense_gap_refreshed_optimality_open
  evidence:
    - repro/stage250_exact_dense_lower_bound_gap/performance_endpoint_matrix.csv
    - repro/stage250_exact_dense_lower_bound_gap/lower_bound_component_matrix.csv
    - repro/stage250_exact_dense_lower_bound_gap/counter_gap_matrix.csv
    - repro/stage250_exact_dense_lower_bound_gap/proof_gate.csv
    - docs/stage250_exact_dense_lower_bound_gap.md
  conclusion: >
    Stage250 records {decision}. It preserves scoped exact dense complete-SAB
    speedup evidence while blocking theoretical optimality: no validated
    numeric lower-bound denominator exists, compact/body-linear proxies are not
    admissible after Stage249, and new hot-path code requires a concrete
    counter-backed mechanism.
""")
    append_once(RUN_LOG, "stage250-exact-dense-lower-bound-gap-001", f"""stage250-exact-dense-lower-bound-gap-001,{date.today().isoformat()},{head},Stage 250,lower_bound_gap,"python scripts/build_stage250_exact_dense_lower_bound_gap.py","Stage249 compact freeze + exact dense timing/profile/counters",n/a,{decision},"Exact dense speedup remains scoped; optimality gap remains open.",docs/stage250_exact_dense_lower_bound_gap.md; repro/stage250_exact_dense_lower_bound_gap/proof_gate.csv
""")
    append_once(MANIFEST, "- stage250_exact_dense_lower_bound_gap:", """
- stage250_exact_dense_lower_bound_gap:
  - `docs/stage250_exact_dense_lower_bound_gap.md`
  - `experiments/stage250_exact_dense_lower_bound_gap_plan.md`
  - `theory_checks/stage250_exact_dense_lower_bound_gap_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage250_exact_dense_lower_bound_gap.md`
  - `scripts/build_stage250_exact_dense_lower_bound_gap.py`
  - `repro/stage250_exact_dense_lower_bound_gap/`
""")
    append_once(CHECKLIST, "Stage250 exact dense lower-bound gap keeps optimality open", f"""
- [x] Stage250 exact dense lower-bound gap keeps optimality open `{decision}`.
""")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = run_git(["rev-parse", "--short", "HEAD"])
    inputs = input_rows()
    perf = performance_rows()
    lower = lower_bound_rows()
    counters = counter_rows()
    claims = claim_rows()
    gates = gate_rows(inputs, perf, lower, counters, claims)
    nextq = next_rows()

    write_csv(INPUT_STATUS, inputs, ["input_id", "path", "status", "bytes"])
    write_csv(PERFORMANCE, perf, ["source", "param", "r", "endpoint", "mean_speedup", "ci95_low", "ci95_high", "noise_failures", "status", "claim_use"])
    write_csv(LOWER_BOUND, lower, ["component", "measured_or_model", "evidence", "closed_status", "gap_effect", "next_action"])
    write_csv(COUNTER, counters, ["metric", "value", "status", "interpretation", "evidence"])
    write_csv(CLAIM, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(GATES, gates, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])

    write_docs(inputs, perf, lower, counters, claims, gates, nextq, head)
    artifacts = [DOC, PLAN, THEORY, VARIANT, INPUT_STATUS, PERFORMANCE, LOWER_BOUND, COUNTER, CLAIM, GATES, NEXT, REPORT, REPRO_CMDS]
    write_csv(ARTIFACT, artifact_rows(artifacts), ["artifact", "exists", "sha256", "bytes"])
    update_project_files(head, gates[-1]["status"])
    print(f"Stage250 report: {rel(DOC)}")
    print(f"Stage250 decision: {gates[-1]['status']}")


if __name__ == "__main__":
    main()
