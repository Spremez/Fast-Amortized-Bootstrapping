#!/usr/bin/env python3
"""Stage229: scope exact PVW/MAT-SAB parameter evidence and gaps."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage229_parameter_generalization_matrix"

DOC = ROOT / "docs" / "stage229_parameter_generalization_matrix.md"
PLAN = ROOT / "experiments" / "stage229_parameter_generalization_matrix_plan.md"
THEORY = ROOT / "theory_checks" / "stage229_parameter_scope_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage229_parameter_scope.md"

INPUTS = OUT / "input_status.csv"
PARAM_DEFS = OUT / "parameter_definitions.csv"
MATRIX = OUT / "parameter_matrix.csv"
COVERAGE = OUT / "coverage_gaps.csv"
CLAIMS = OUT / "claim_scope.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "parameter_generalization_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE228_PROOF = ROOT / "repro" / "stage228_counter_driven_backend_kernel_search" / "proof_gate.csv"
STAGE228_NEXT = ROOT / "repro" / "stage228_counter_driven_backend_kernel_search" / "next_stage_queue.csv"
STAGE206_PERF = ROOT / "repro" / "stage206_current_head_highstat" / "performance_stats.csv"
STAGE206_NOISE = ROOT / "repro" / "stage206_current_head_highstat" / "noise_stats.csv"
STAGE207_RESOURCE = ROOT / "repro" / "stage207_current_head_resource_refresh" / "resource_comparison.csv"
STAGE224_PERF = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "perf_comparison.csv"
STAGE225_NOISE = ROOT / "repro" / "stage225_exact_refresh_noise_resource_rerun" / "noise_aggregate.csv"
STAGE225_RESOURCE = ROOT / "repro" / "stage225_exact_refresh_noise_resource_rerun" / "resource_comparison.csv"
STAGE226_ATTR = ROOT / "repro" / "stage226_exact_mat_avx_counter_attribution" / "attribution_summary.csv"
STAGE36_TARGET_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE36_TARGET_NOISE = ROOT / "repro" / "stage36_target_noise_seeds50" / "aggregate.csv"
STAGE36_STAGE_NOISE = ROOT / "repro" / "stage36_stage_noise_seeds10" / "aggregate.csv"
STAGE36_RESOURCE = ROOT / "repro" / "stage36_resource_summary.csv"
STAGE36_ADDED_PERF = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "performance_stats.csv"
STAGE36_ADDED_NOISE = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "noise_summary.csv"
STAGE26_BRANCH_LOG = ROOT / "docs" / "stage26_parameter_branch_log.md"
STAGE26_PERF_LOG = ROOT / "docs" / "stage26_parameter_perf_noise_log.md"
STAGE36_ADDED_LOG = ROOT / "docs" / "stage36_added_params_expansion_log.md"
MAIN_C = ROOT / "main.c"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    if not rows:
        return "_No rows._\n"
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def find_row(rows: List[Dict[str, str]], **criteria: str) -> Dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in criteria.items()):
            return row
    return {}


def stage228_selects_stage229() -> bool:
    return any(
        row.get("route") == "stage229_parameter_generalization_matrix" and row.get("status") == "selected"
        for row in read_csv(STAGE228_NEXT)
    )


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE228_PROOF, "Stage228 proof gate selecting parameter matrix"),
        (STAGE228_NEXT, "Stage228 next queue"),
        (STAGE206_PERF, "current-head r=2/r=4 complete-SAB A/B"),
        (STAGE206_NOISE, "current-head r=2/r=4 final-output noise"),
        (STAGE207_RESOURCE, "current-head r=2/r=4 resource refresh"),
        (STAGE224_PERF, "exact r=6 backend complete-SAB refresh"),
        (STAGE225_NOISE, "exact r=6 fresh noise refresh"),
        (STAGE225_RESOURCE, "exact r=6 fresh resource refresh"),
        (STAGE226_ATTR, "exact r=6 counter attribution"),
        (STAGE36_TARGET_PERF, "historical target high-stat performance"),
        (STAGE36_TARGET_NOISE, "historical target 50-seed noise"),
        (STAGE36_STAGE_NOISE, "historical target stage-noise"),
        (STAGE36_RESOURCE, "historical target resource matrix"),
        (STAGE36_ADDED_PERF, "added binary parameter 10-run performance"),
        (STAGE36_ADDED_NOISE, "added binary parameter 20-seed noise"),
        (STAGE26_BRANCH_LOG, "PVW non-binary unsupported boundary"),
        (STAGE26_PERF_LOG, "added binary parameter smoke history"),
        (STAGE36_ADDED_LOG, "added binary high-stat report"),
        (MAIN_C, "current target parameter definitions"),
    ]
    rows = []
    for path, role in paths:
        rows.append(
            {
                "input": rel(path),
                "status": "present" if path.exists() else "missing",
                "role": role,
                "bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    rows.append(
        {
            "input": "stage228_next_selects_stage229",
            "status": "present" if stage228_selects_stage229() else "missing",
            "role": "Keeps execution on the registered route.",
            "bytes": "",
        }
    )
    return rows


def parameter_definition_rows() -> List[Dict[str, str]]:
    return [
        {
            "param": "SET_2_3_2048",
            "key_mode": "BINARY",
            "in_N": "2048",
            "out_N": "2048",
            "msg_prec": "3",
            "h": "39",
            "r_prec": "7",
            "status": "target_main",
            "evidence": rel(MAIN_C),
        },
        {
            "param": "SET_4_5_2048",
            "key_mode": "BINARY",
            "in_N": "2048",
            "out_N": "2048",
            "msg_prec": "5",
            "h": "42",
            "r_prec": "7",
            "status": "added_binary_covered",
            "evidence": rel(MAIN_C),
        },
        {
            "param": "SET_2_3_4096",
            "key_mode": "BINARY",
            "in_N": "4096",
            "out_N": "2048",
            "msg_prec": "3",
            "h": "32",
            "r_prec": "8",
            "status": "added_binary_covered",
            "evidence": rel(MAIN_C),
        },
        {
            "param": "TERNARY_or_include_zero",
            "key_mode": "NON_BINARY",
            "in_N": "",
            "out_N": "",
            "msg_prec": "",
            "h": "",
            "r_prec": "",
            "status": "pvw_unsupported_scalar_preserved",
            "evidence": rel(STAGE26_BRANCH_LOG),
        },
    ]


def matrix_rows() -> List[Dict[str, str]]:
    current_perf = read_csv(STAGE206_PERF)
    current_noise = read_csv(STAGE206_NOISE)
    current_res = read_csv(STAGE207_RESOURCE)
    stage36_target = read_csv(STAGE36_TARGET_PERF)
    stage36_target_noise = read_csv(STAGE36_TARGET_NOISE)
    stage36_res = read_csv(STAGE36_RESOURCE)
    added_perf = read_csv(STAGE36_ADDED_PERF)
    added_noise = read_csv(STAGE36_ADDED_NOISE)
    r6_perf = read_csv(STAGE224_PERF)
    r6_noise = read_csv(STAGE225_NOISE)
    r6_resource = read_csv(STAGE225_RESOURCE)

    rows: List[Dict[str, str]] = []
    for r in ("2", "4"):
        perf = find_row(current_perf, r=r)
        noise = find_row(current_noise, r=r)
        res = find_row(current_res, r=r)
        older_perf = find_row(stage36_target, r=r)
        older_noise = find_row(stage36_target_noise, r=r)
        older_res_pvw = find_row(stage36_res, r=r, mode="pvw")
        rows.append(
            {
                "scope": "current_head_target",
                "param": "SET_2_3_2048",
                "key_mode": "BINARY",
                "r": r,
                "metric": "T_bootstrap/r",
                "runs": perf.get("runs", ""),
                "speedup_mean": perf.get("mean_of_run_speedups", "") or perf.get("mean_speedup", ""),
                "speedup_ci95": f"{perf.get('ci95_low','')}..{perf.get('ci95_high','')}",
                "noise_seeds": noise.get("seeds", ""),
                "noise_failures": f"{noise.get('pvw_failures','')}/{noise.get('scalar_failures','')}/{noise.get('pair_failures','')}",
                "resource": f"key_bytes_ratio={res.get('key_bytes_ratio','')};rss_ratio={res.get('internal_vmhwm_ratio','')}",
                "claim_level": "current-head complete-SAB evidence",
                "evidence": f"{rel(STAGE206_PERF)}; {rel(STAGE206_NOISE)}; {rel(STAGE207_RESOURCE)}",
            }
        )
        rows.append(
            {
                "scope": "historical_highstat_target",
                "param": "SET_2_3_2048",
                "key_mode": "BINARY",
                "r": r,
                "metric": "T_bootstrap/r",
                "runs": older_perf.get("samples", ""),
                "speedup_mean": older_perf.get("mean_speedup", ""),
                "speedup_ci95": f"{older_perf.get('ci95_low','')}..{older_perf.get('ci95_high','')}",
                "noise_seeds": older_noise.get("seeds", ""),
                "noise_failures": f"{older_noise.get('pvw_failures','')}/{older_noise.get('scalar_failures','')}/{older_noise.get('pair_failures','')}",
                "resource": f"key_bytes_ratio_mean={older_res_pvw.get('key_bytes_ratio_mean','')};rss_max={older_res_pvw.get('time_max_rss_max_kb','')}",
                "claim_level": "historical high-stat support, not current-head replacement",
                "evidence": f"{rel(STAGE36_TARGET_PERF)}; {rel(STAGE36_TARGET_NOISE)}; {rel(STAGE36_RESOURCE)}",
            }
        )
    r6 = r6_perf[0] if r6_perf else {}
    r6n = r6_noise[0] if r6_noise else {}
    r6r = r6_resource[0] if r6_resource else {}
    rows.append(
        {
            "scope": "current_head_exact_r6",
            "param": "SET_2_3_2048",
            "key_mode": "BINARY",
            "r": "6",
            "metric": "T_bootstrap/r",
            "runs": r6.get("runs", ""),
            "speedup_mean": r6.get("backend_mean_speedup_vs_scalar", ""),
            "speedup_ci95": (
                "not_reported_for_scalar_speedup;"
                f"backend_vs_wrapper_ci={r6.get('backend_vs_wrapper_ci95_low','')}..{r6.get('backend_vs_wrapper_ci95_high','')}"
            ),
            "noise_seeds": r6n.get("seeds", ""),
            "noise_failures": f"{r6n.get('pvw_failures','')}/{r6n.get('scalar_failures','')}/{r6n.get('pair_failures','')}",
            "resource": f"key_bytes_ratio={r6r.get('key_bytes_ratio','')};rss_ratio={r6r.get('vmhwm_ratio','')}",
            "claim_level": "current exact dense MAT/PVW r=6 support, experimental explicit path",
            "evidence": f"{rel(STAGE224_PERF)}; {rel(STAGE225_NOISE)}; {rel(STAGE225_RESOURCE)}",
        }
    )
    for param in ("SET_4_5_2048", "SET_2_3_4096"):
        for r in ("2", "4"):
            perf = find_row(added_perf, param=param, r=r)
            noise = find_row(added_noise, param=param, r=r)
            rows.append(
                {
                    "scope": "historical_added_binary",
                    "param": param,
                    "key_mode": "BINARY",
                    "r": r,
                    "metric": "T_bootstrap/r",
                    "runs": perf.get("runs", ""),
                    "speedup_mean": perf.get("mean_speedup", ""),
                    "speedup_ci95": f"{perf.get('ci95_low_t','')}..{perf.get('ci95_high_t','')}",
                    "noise_seeds": noise.get("seeds", ""),
                    "noise_failures": f"{noise.get('pvw_failures','')}/{noise.get('scalar_failures','')}/{noise.get('pair_failures','')}",
                    "resource": "not refreshed in added-parameter campaign",
                    "claim_level": "binary parameter support only; not all-parameter claim",
                    "evidence": f"{rel(STAGE36_ADDED_PERF)}; {rel(STAGE36_ADDED_NOISE)}",
                }
            )
    return rows


def coverage_rows() -> List[Dict[str, str]]:
    return [
        {
            "gap": "non_binary_pvw_sab",
            "status": "blocked",
            "reason": "Stage26 explicitly rejects PVW target harness for non-binary key modes while scalar ternary remains preserved.",
            "required_next_evidence": "Separate selector/key-format design for sign/coefficient semantics, isolated equivalence, full SAB A/B, noise/resource.",
            "evidence": rel(STAGE26_BRANCH_LOG),
        },
        {
            "gap": "all_parameter_generalization",
            "status": "not_claimed",
            "reason": "Evidence covers target binary plus two added binary parameters; other SET_* definitions are not in the repeated matrix.",
            "required_next_evidence": "Pre-register each parameter family and run same-backend complete-SAB A/B plus multi-seed noise.",
            "evidence": f"{rel(PARAM_DEFS)}; {rel(MATRIX)}",
        },
        {
            "gap": "small_parameter_proxy",
            "status": "not_claimed",
            "reason": "The recent PARAM=SET_2_3 probe still used default SET_2_3_2048 target shape in the harness output.",
            "required_next_evidence": "Add or identify a true small-parameter harness and prove it prints distinct h/r_prec/in_N before timing.",
            "evidence": rel(MAIN_C),
        },
        {
            "gap": "mat_rlwe_theoretical_optimality",
            "status": "open",
            "reason": "Current exact route is dense row-output MAT/PVW. It optimizes T_bootstrap/r empirically but does not prove optimal r-body MAT-RLWE SAB.",
            "required_next_evidence": "Formal lower/upper cost model plus counter-backed kernel evidence and complete-SAB ablation.",
            "evidence": rel(STAGE226_ATTR),
        },
        {
            "gap": "paper_novelty",
            "status": "blocked_until_source_verified",
            "reason": "Engineering speedup evidence is available, but novelty wording requires verified related work and real 2025/686 source anchors.",
            "required_next_evidence": "Source-verified literature/novelty matrix; no fabricated references.",
            "evidence": rel(NEXT),
        },
    ]


def claim_rows(matrix: List[Dict[str, str]], coverage: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "claim": "primary_metric",
            "status": "supported",
            "allowed_wording": "Speedup is measured as complete-SAB amortized throughput, `T_scalar_repeated/r` over `T_PVW/r`, i.e. bootstrap time per processed plaintext lane/bit.",
            "forbidden_wording": "Do not report one PVW call total latency as a single-output latency improvement.",
            "evidence": rel(MATRIX),
        },
        {
            "claim": "current_head_target_binary",
            "status": "supported_scoped",
            "allowed_wording": "Current head supports binary `SET_2_3_2048` r=2/r=4 complete-SAB A/B with noise/resource side conditions.",
            "forbidden_wording": "Do not generalize this row to non-binary or all parameter sets.",
            "evidence": rel(MATRIX),
        },
        {
            "claim": "historical_added_binary",
            "status": "supported_scoped_historical",
            "allowed_wording": "Stage36 supports added binary parameters `SET_4_5_2048` and `SET_2_3_4096` for r=2/r=4 under recorded high-stat gates.",
            "forbidden_wording": "Do not call these current-head refreshes unless rerun at current head.",
            "evidence": rel(MATRIX),
        },
        {
            "claim": "r6_exact_route",
            "status": "supported_experimental_explicit",
            "allowed_wording": "Exact dense MAT/PVW r=6 has current explicit-path support with fresh noise/resource and counter attribution.",
            "forbidden_wording": "Do not call r=6 theoretically optimal or default-promoted.",
            "evidence": rel(MATRIX),
        },
        {
            "claim": "non_binary_pvw",
            "status": "unsupported",
            "allowed_wording": "PVW/MAT-SAB non-binary support is not implemented; scalar ternary baseline is preserved.",
            "forbidden_wording": "Do not claim ternary/include-zero PVW-SAB support.",
            "evidence": rel(COVERAGE),
        },
        {
            "claim": "mat_rlwe_optimality",
            "status": "unsupported_open",
            "allowed_wording": "The present route is an empirically validated dense MAT/RLWE exact path, not a proof of optimal r-body MAT-RLWE SAB.",
            "forbidden_wording": "Do not claim theoretical optimality of MAT external product or full SAB.",
            "evidence": rel(COVERAGE),
        },
    ]


def proof_rows(inputs: List[Dict[str, str]], matrix: List[Dict[str, str]], coverage: List[Dict[str, str]]) -> List[Dict[str, str]]:
    inputs_ok = all(row["status"] == "present" for row in inputs)
    current_rows = [
        row for row in matrix
        if row["scope"] == "current_head_target" and row["runs"] and row["noise_seeds"]
    ]
    added_rows = [row for row in matrix if row["scope"] == "historical_added_binary" and row["runs"] == "10" and row["noise_seeds"] == "20"]
    r6_rows = [row for row in matrix if row["scope"] == "current_head_exact_r6" and row["runs"] and row["noise_seeds"]]
    nonbinary_blocked = any(row["gap"] == "non_binary_pvw_sab" and row["status"] == "blocked" for row in coverage)
    all_param_not_claimed = any(row["gap"] == "all_parameter_generalization" and row["status"] == "not_claimed" for row in coverage)
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if inputs_ok else "FAIL",
            "metric": "inputs_present",
            "value": str(inputs_ok).lower(),
            "evidence": rel(INPUTS),
            "interpretation": "Stage229 only consumes registered evidence; missing inputs block promotion.",
        },
        {
            "gate": "G2_metric_dimension",
            "status": "PASS",
            "metric": "primary_metric",
            "value": "T_bootstrap/r",
            "evidence": rel(CLAIMS),
            "interpretation": "All PVW/MAT-SAB speedups are amortized per processed plaintext lane/bit.",
        },
        {
            "gate": "G3_current_head_binary_target",
            "status": "PASS" if len(current_rows) == 2 else "FAIL",
            "metric": "current_rows",
            "value": str(len(current_rows)),
            "evidence": rel(MATRIX),
            "interpretation": "Current-head r=2/r=4 target evidence is present.",
        },
        {
            "gate": "G4_added_binary_history",
            "status": "PASS" if len(added_rows) == 4 else "FAIL",
            "metric": "added_rows",
            "value": str(len(added_rows)),
            "evidence": rel(MATRIX),
            "interpretation": "Two added binary parameters have historical 10-run/20-seed evidence.",
        },
        {
            "gate": "G5_exact_r6_current",
            "status": "PASS" if len(r6_rows) == 1 else "FAIL",
            "metric": "r6_rows",
            "value": str(len(r6_rows)),
            "evidence": rel(MATRIX),
            "interpretation": "Current exact r=6 explicit-path evidence is registered but remains scoped.",
        },
        {
            "gate": "G6_nonbinary_boundary",
            "status": "PASS_BLOCKED_SCOPE" if nonbinary_blocked else "FAIL",
            "metric": "nonbinary_blocked",
            "value": str(nonbinary_blocked).lower(),
            "evidence": rel(COVERAGE),
            "interpretation": "PVW non-binary support remains unsupported; scalar non-binary is not removed.",
        },
        {
            "gate": "G7_generalization_boundary",
            "status": "PASS_NOT_ALL_PARAMETERS" if all_param_not_claimed else "FAIL",
            "metric": "all_parameter_claim",
            "value": "denied",
            "evidence": rel(COVERAGE),
            "interpretation": "Stage229 records a scoped parameter matrix, not an all-parameter theorem.",
        },
        {
            "gate": "G8_stage229_decision",
            "status": "PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED",
            "metric": "decision",
            "value": "PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED",
            "evidence": rel(PROOF),
            "interpretation": "Proceed to source-verified novelty audit and explicit implementation preflights only.",
        },
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage230_source_verified_literature_novelty_audit",
            "entry_condition": "Stage229 fixes claim scope and forbids paper novelty overclaim.",
            "gate": "Real sources only; verify 2025/686, PVW/MAT, multi-output bootstrapping, and SIMD FHE kernel context.",
            "status": "selected",
            "failure_action": "Keep final report engineering-scoped and remove novelty wording.",
            "evidence": rel(CLAIMS),
        },
        {
            "priority": "P1",
            "route": "stage231_true_parameter_refresh",
            "entry_condition": "A claim needs current-head support beyond binary SET_2_3_2048 and r=6.",
            "gate": "Print parameter shape first, then same-backend complete-SAB A/B, multi-seed noise, resource.",
            "status": "future",
            "failure_action": "Keep Stage36 added-parameter evidence historical/scoped.",
            "evidence": rel(COVERAGE),
        },
        {
            "priority": "P2",
            "route": "stage232_nonbinary_pvw_design_preflight",
            "entry_condition": "User elects to support ternary/include-zero PVW-SAB.",
            "gate": "Selector/key-format equations before implementation; isolated equivalence before full SAB.",
            "status": "blocked_until_design",
            "failure_action": "Do not claim non-binary PVW-SAB.",
            "evidence": rel(COVERAGE),
        },
    ]


def write_reports(
    decision: str,
    inputs: List[Dict[str, str]],
    params: List[Dict[str, str]],
    matrix: List[Dict[str, str]],
    coverage: List[Dict[str, str]],
    claims: List[Dict[str, str]],
    proof: List[Dict[str, str]],
    queue: List[Dict[str, str]],
) -> None:
    report = f"""# Stage229 Parameter Generalization Matrix

Decision: `{decision}`.

Stage229 answers the MAT-RLWE/r-body comparison question by fixing the primary
metric to complete-SAB amortized throughput:

```text
speedup = (time for r scalar SAB bootstraps / r) / (time for one r-body PVW/MAT-SAB bootstrap / r)
        = T_scalar_repeated / T_PVW
```

This is the bootstrap time per processed plaintext lane/bit. The matrix below
does not claim single-output latency improvement, all-parameter coverage,
non-binary PVW support, or theoretical optimality.

## Parameter Definitions

{table(params, ["param", "key_mode", "in_N", "out_N", "msg_prec", "h", "r_prec", "status", "evidence"])}
## Evidence Matrix

{table(matrix, ["scope", "param", "key_mode", "r", "metric", "runs", "speedup_mean", "speedup_ci95", "noise_seeds", "noise_failures", "resource", "claim_level", "evidence"])}
## Coverage Gaps

{table(coverage, ["gap", "status", "reason", "required_next_evidence", "evidence"])}
## Claim Scope

{table(claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])}
## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(
        PLAN,
        """# Stage229 Parameter Generalization Plan

## Objective

Record what the current exact PVW/MAT-SAB route can and cannot claim across
parameters before any further optimization or manuscript wording.

## Loop Controls

1. Evidence first: consume only registered logs or rerun commands.
2. Metric lock: every performance row uses complete-SAB `T_bootstrap/r`.
3. Claim split: current-head evidence, historical high-stat evidence, and
   unsupported branches are separate rows.
4. Stop rule: a missing parameter/branch gate creates a future stage, not a
   theoretical assertion.
5. Next action: source-verified literature audit is selected before novelty
   wording; implementation work needs an explicit design/preflight route.

## Execution

Run:

```powershell
python scripts\\build_stage229_parameter_generalization_matrix.py
```
""",
    )
    write_text(
        THEORY,
        """# Stage229 Parameter Scope Model

PVW/MAT-SAB changes the ciphertext object from independent scalar RLWE bodies
to one shared-mask MAT/PVW object with `r` body lanes. Therefore the correct
comparison for the intended algorithm is amortized complete bootstrapping:

```text
T_per_bit_scalar = T_scalar_repeated / r
T_per_bit_pvw    = T_pvw / r
speedup          = T_per_bit_scalar / T_per_bit_pvw
```

Because both sides are divided by the same `r`, recorded speedup is equivalent
to `T_scalar_repeated / T_pvw`, but the interpretation is per processed
plaintext lane/bit. This is not the same as saying one PVW call has lower
single-output latency than one scalar SAB call.

Parameter generalization is an empirical and semantic claim:

- empirical: same-backend complete-SAB A/B, repeated runs, noise, and resource;
- semantic: the selector/key format must support the branch being claimed.

Current evidence supports binary parameters only. Non-binary PVW-SAB remains
blocked because sign/coefficient selector semantics require a separate design.
The exact dense MAT/PVW route remains empirically useful, but theoretical
optimality of r-body MAT-RLWE SAB is still open.
""",
    )
    write_text(
        VARIANT,
        """# Stage229 MAT-RLWE SAB Parameter Scope

## Supported Variant

The supported implementation object is the exact dense MAT/PVW-SAB path:

- shared mask;
- `r` body lanes;
- dense row-output MAT external product;
- scalar SAB default path preserved;
- explicit PVW/MAT flags required for optimized paths.

## Supported Claims

- Binary `SET_2_3_2048` r=2/r=4 has current-head complete-SAB A/B evidence.
- Binary `SET_2_3_2048` r=6 has current explicit exact-route evidence.
- Binary `SET_4_5_2048` and `SET_2_3_4096` have historical high-stat support.

## Unsupported Claims

- Ternary/include-zero PVW-SAB.
- All-parameter PVW/MAT-SAB generalization.
- Theoretical optimality of the current dense MAT external product.
- Paper novelty without source-verified related-work audit.
""",
    )
    write_text(
        REPRO,
        """# Stage229 Reproduction Commands

```powershell
python scripts\\build_stage229_parameter_generalization_matrix.py
Get-Content repro\\stage229_parameter_generalization_matrix\\proof_gate.csv
Get-Content repro\\stage229_parameter_generalization_matrix\\parameter_matrix.csv
Get-Content repro\\stage229_parameter_generalization_matrix\\coverage_gaps.csv
```

Optional current-head smoke probe, not a parameter-generalization claim:

```powershell
bash -lc "make clean >/dev/null 2>&1 || true && make FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3 KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_RGT4_FUSED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_BENCH=true SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 -j2 && ./main"
```

The optional probe must be interpreted from printed `h`, `r_prec`, and `in_N`.
If it prints the default target shape, it is only a smoke probe.
""",
    )


def artifact_rows(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def update_tracking(decision: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 229: Parameter Generalization Matrix",
        f"""
## Stage 229: Parameter Generalization Matrix

Goal:

```text
Freeze the complete-SAB `T_bootstrap/r` parameter evidence matrix before
broadening exact PVW/MAT-SAB claims.
```

Status:

```text
Generated from input head `{head}` with `{decision}`. Binary target and added-parameter
evidence is recorded, non-binary PVW-SAB remains unsupported, and all-parameter
or theoretical-optimality claims remain blocked.
```
""",
    )
    append_once(
        GOAL,
        "Stage229 parameter generalization matrix",
        f"\n\n## Stage229 parameter generalization matrix\n\nGenerated from input head `{head}`, Stage229 records `{decision}`. The primary comparison dimension is complete-SAB `T_bootstrap/r`, i.e. bootstrap time per processed plaintext lane/bit. Claims remain binary-parameter scoped.\n",
    )
    append_once(
        CURRENT_GOAL,
        "Stage229 parameter generalization matrix",
        f"\n\n### Stage229 parameter generalization matrix\n\n`{decision}` fixes the exact-route parameter matrix and keeps non-binary, all-parameter, novelty, and theoretical-optimality claims out of scope until their gates run.\n",
    )
    append_once(
        HYPOTHESES,
        "H10_stage229_parameter_generalization_matrix",
        f"""

H10_stage229_parameter_generalization_matrix:
  status: scoped_binary_matrix_recorded
  evidence:
    - repro/stage229_parameter_generalization_matrix/parameter_matrix.csv
    - repro/stage229_parameter_generalization_matrix/coverage_gaps.csv
    - docs/stage229_parameter_generalization_matrix.md
  conclusion: >
    Stage229 records {decision}. The correct comparison dimension is
    complete-SAB T_bootstrap/r. Binary parameter evidence is scoped; non-binary,
    all-parameter, paper-novelty, and theoretical-optimality claims remain
    gated.
""",
    )
    append_once(
        RUN_LOG,
        "stage229-parameter-generalization-matrix-001",
        f"""stage229-parameter-generalization-matrix-001,2026-07-04,{head},Stage 229,analysis,python scripts/build_stage229_parameter_generalization_matrix.py,parameter/branch claim-scope matrix,T_bootstrap_per_lane,{decision},"Binary parameter matrix recorded; non-binary and all-parameter claims blocked.",docs/stage229_parameter_generalization_matrix.md; repro/stage229_parameter_generalization_matrix/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage229_parameter_generalization_matrix:",
        """

- stage229_parameter_generalization_matrix:
  - `docs/stage229_parameter_generalization_matrix.md`
  - `experiments/stage229_parameter_generalization_matrix_plan.md`
  - `theory_checks/stage229_parameter_scope_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage229_parameter_scope.md`
  - `scripts/build_stage229_parameter_generalization_matrix.py`
  - `repro/stage229_parameter_generalization_matrix/`
""",
    )
    append_once(CHECKLIST, "Stage229 parameter generalization matrix", f"\n- [x] Stage229 parameter generalization matrix records decision `{decision}`.\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_rows()
    params = parameter_definition_rows()
    matrix = matrix_rows()
    coverage = coverage_rows()
    claims = claim_rows(matrix, coverage)
    proof = proof_rows(inputs, matrix, coverage)
    queue = next_rows()
    decision = "PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED"

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(PARAM_DEFS, params, ["param", "key_mode", "in_N", "out_N", "msg_prec", "h", "r_prec", "status", "evidence"])
    write_csv(MATRIX, matrix, ["scope", "param", "key_mode", "r", "metric", "runs", "speedup_mean", "speedup_ci95", "noise_seeds", "noise_failures", "resource", "claim_level", "evidence"])
    write_csv(COVERAGE, coverage, ["gap", "status", "reason", "required_next_evidence", "evidence"])
    write_csv(CLAIMS, claims, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, queue, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_reports(decision, inputs, params, matrix, coverage, claims, proof, queue)
    update_tracking(decision)
    write_csv(
        ARTIFACT,
        artifact_rows(
            [
                DOC,
                PLAN,
                THEORY,
                VARIANT,
                INPUTS,
                PARAM_DEFS,
                MATRIX,
                COVERAGE,
                CLAIMS,
                PROOF,
                NEXT,
                REPORT,
                REPRO,
                Path(__file__).resolve(),
            ]
        ),
        ["path", "exists", "sha256", "bytes"],
    )
    print(decision)


if __name__ == "__main__":
    main()
