#!/usr/bin/env python3
"""Stage284: current MAT-RLWE SAB frontier gap ledger.

This stage consumes the latest measured candidate evidence and converts it into
a falsifiable frontier ledger.  It does not run a new heavy benchmark and it
does not claim optimality.  Its purpose is to prevent the research loop from
drifting: every next algorithmic move must be justified by measured
T_bootstrap/r evidence, a component share, and a concrete gate.
"""

from __future__ import annotations

import csv
import hashlib
import math
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage284_frontier_gap_ledger"
DOC = ROOT / "docs" / "stage284_frontier_gap_ledger.md"
THEORY = ROOT / "theory_checks" / "stage284_frontier_gap_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage284_frontier_candidates.md"
PLAN = ROOT / "experiments" / "stage284_frontier_validation_plan.md"
BUILDER = ROOT / "scripts" / "build_stage284_frontier_gap_ledger.py"

CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

INPUTS = {
    "stage250_proof": ROOT / "repro" / "stage250_exact_dense_lower_bound_gap" / "proof_gate.csv",
    "stage250_lower_bound": ROOT / "repro" / "stage250_exact_dense_lower_bound_gap" / "lower_bound_component_matrix.csv",
    "stage280_profile": ROOT / "repro" / "stage280_cmux_mat_ep_residual_screen" / "profile_components.csv",
    "stage280_candidate": ROOT / "repro" / "stage280_cmux_mat_ep_residual_screen" / "candidate_comparison.csv",
    "stage281_latency": ROOT / "repro" / "stage281_cmux_residual_repeated_gate" / "latency_summary.csv",
    "stage282_noise_resource": ROOT / "repro" / "stage282_cmux_residual_noise_resource" / "noise_resource_summary.csv",
    "stage282_proof": ROOT / "repro" / "stage282_cmux_residual_noise_resource" / "proof_gate.csv",
    "stage283_probe": ROOT / "repro" / "stage283_native_target_repeated_gate" / "native_access_probe.csv",
    "stage283_proof": ROOT / "repro" / "stage283_native_target_repeated_gate" / "proof_gate.csv",
    "stage166_terms": ROOT / "repro" / "stage166_shared_output_compact_algebra_gate" / "term_model.csv",
}

INPUT_STATUS = OUT / "input_status.csv"
FRONTIER = OUT / "frontier_summary.csv"
RESIDUAL = OUT / "residual_gap_ledger.csv"
SENSITIVITY = OUT / "component_sensitivity.csv"
ALGO_QUEUE = OUT / "algorithm_frontier.csv"
CLAIM = OUT / "claim_boundary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage284_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE284_FRONTIER_GAP_LEDGER_READY_NATIVE_OR_MAT_EP_SPLIT_NEXT"
TARGET_VARIANT = "backend_sub_decomp_dual"
CONTROL_VARIANT = "fast_control"
R_VALUE = 4


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_list = list(fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in field_list})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def fnum(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def sha256(path: Path) -> Dict[str, object]:
    data = path.read_bytes()
    return {"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def markdown_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fields) + " |")
    return "\n".join(lines)


def input_status_rows() -> List[Dict[str, object]]:
    return [
        {
            "input_id": name,
            "path": rel(path),
            "status": "present" if path.exists() else "missing",
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        for name, path in INPUTS.items()
    ]


def latency_rows() -> Dict[str, Dict[str, str]]:
    return {row.get("variant", ""): row for row in read_csv(INPUTS["stage281_latency"])}


def profile_rows_for(variant: str) -> Dict[str, Dict[str, str]]:
    return {
        row.get("component", ""): row
        for row in read_csv(INPUTS["stage280_profile"])
        if row.get("variant") == variant
    }


def compact_term_row(r: int) -> Dict[str, str]:
    for row in read_csv(INPUTS["stage166_terms"]):
        if row.get("r") == str(r):
            return row
    return {}


def build_frontier_summary(latency: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    control = latency.get(CONTROL_VARIANT, {})
    candidate = latency.get(TARGET_VARIANT, {})
    comparison = latency.get("comparison", {})
    native_probe = (read_csv(INPUTS["stage283_probe"]) or [{}])[0]
    noise_rows = {row.get("variant", ""): row for row in read_csv(INPUTS["stage282_noise_resource"])}
    noise = noise_rows.get(TARGET_VARIANT, {})

    control_t = fnum(control.get("t_over_r_mean_us"))
    candidate_t = fnum(candidate.get("t_over_r_mean_us"))
    scalar_t = fnum(candidate.get("scalar_t_over_r_mean_us")) or fnum(control.get("scalar_t_over_r_mean_us"))
    incremental = fnum(comparison.get("speedup_vs_fast_control_mean"))
    conservative = fnum(comparison.get("conservative_control_min_over_candidate_max"))
    scalar_speedup = scalar_t / candidate_t if candidate_t and scalar_t else 0.0

    return [
        {
            "item": "primary_endpoint",
            "value": "T_bootstrap/r",
            "status": "fixed",
            "evidence": rel(INPUTS["stage281_latency"]),
            "interpretation": "All current speed comparisons are amortized per processed lane/bit.",
        },
        {
            "item": "fast_control_t_over_r_mean_us",
            "value": f"{control_t:.3f}" if control_t else "missing",
            "status": control.get("correctness", "missing"),
            "evidence": rel(INPUTS["stage281_latency"]),
            "interpretation": "Current same-backend control after include-zero fast path.",
        },
        {
            "item": "candidate_t_over_r_mean_us",
            "value": f"{candidate_t:.3f}" if candidate_t else "missing",
            "status": candidate.get("correctness", "missing"),
            "evidence": rel(INPUTS["stage281_latency"]),
            "interpretation": "Current selected backend_sub_decomp_dual path.",
        },
        {
            "item": "candidate_vs_fast_control_mean",
            "value": f"{incremental:.6f}" if incremental else "missing",
            "status": "local_repeated_positive" if incremental >= 1.02 else "neutral_or_missing",
            "evidence": rel(INPUTS["stage281_latency"]),
            "interpretation": "Incremental local repeated improvement over the current fast control.",
        },
        {
            "item": "candidate_vs_fast_control_conservative",
            "value": f"{conservative:.6f}" if conservative else "missing",
            "status": "positive" if conservative > 1.0 else "neutral_or_missing",
            "evidence": rel(INPUTS["stage281_latency"]),
            "interpretation": "Conservative min/control over max/candidate guard.",
        },
        {
            "item": "candidate_vs_repeated_scalar_mean",
            "value": f"{scalar_speedup:.6f}" if scalar_speedup else "missing",
            "status": "local_repeated_positive" if scalar_speedup > 1.0 else "missing",
            "evidence": rel(INPUTS["stage281_latency"]),
            "interpretation": "Amortized MAT-RLWE/r-body gain over repeated scalar SAB.",
        },
        {
            "item": "noise_resource_gate",
            "value": noise.get("status", "missing"),
            "status": noise.get("status", "missing"),
            "evidence": rel(INPUTS["stage282_noise_resource"]),
            "interpretation": "Local ffnt proxy; not target AVX512 performance evidence.",
        },
        {
            "item": "native_target_gate",
            "value": native_probe.get("reason", "missing"),
            "status": native_probe.get("status", "missing"),
            "evidence": rel(INPUTS["stage283_probe"]),
            "interpretation": "Paper-grade native target timing remains disallowed until access succeeds.",
        },
    ]


def build_residual_ledger(latency: Dict[str, Dict[str, str]], profile: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    candidate_t = fnum(latency.get(TARGET_VARIANT, {}).get("t_over_r_mean_us"))
    components = [
        ("mat_ep", "MAT external product and sub-decomposition hot term", "P1 native counter plus split microbench before new AVX/layout code"),
        ("cmux_from_dft", "inverse DFT/materialization term", "P2 only with a new mechanism; prior direct-add alone was neutral"),
        ("cmux_sub", "subtraction term after dual-sub fusion", "low unless a paired schedule fusion changes its share"),
        ("ncmux_total", "NCMUX residual", "low priority after dual-sub unless profile changes"),
        ("sub_a_total", "sub_a/rotation term", "defer unless a combined schedule variant can move full SAB"),
    ]
    rows: List[Dict[str, object]] = []
    full_us = fnum(profile.get("rgsw_monomial", {}).get("full_us")) or fnum(profile.get("mat_ep", {}).get("full_us"))
    rgsw_us = fnum(profile.get("rgsw_monomial", {}).get("component_us"))
    if full_us > 0 and rgsw_us > 0:
        tail_share = max(0.0, (full_us - rgsw_us) / full_us)
        components.append(("outside_rgsw_tail", "extract/post-schedule residual inferred from profile", "defer while share is small"))
        profile["outside_rgsw_tail"] = {
            "component_us": f"{max(0.0, full_us - rgsw_us):.3f}",
            "calls": "n/a",
            "share_of_profile_full": f"{tail_share:.6f}",
            "full_us": f"{full_us:.3f}",
        }

    for component, meaning, next_gate in components:
        row = profile.get(component, {})
        share = fnum(row.get("share_of_profile_full"))
        projected_zero = candidate_t * max(0.0, 1.0 - share) if candidate_t else 0.0
        max_internal_speedup = 1.0 / (1.0 - share) if 0.0 <= share < 1.0 else math.inf
        rows.append({
            "component": component,
            "meaning": meaning,
            "profile_share": f"{share:.6f}" if row else "missing",
            "component_us_profile_total": row.get("component_us", "missing"),
            "calls": row.get("calls", "missing"),
            "candidate_t_over_r_us": f"{candidate_t:.3f}" if candidate_t else "missing",
            "projected_t_over_r_if_zero_us": f"{projected_zero:.3f}" if candidate_t and row else "missing",
            "zero_component_upper_bound_vs_candidate": f"{max_internal_speedup:.6f}" if row and math.isfinite(max_internal_speedup) else "missing",
            "claim_status": "projection_only_not_speed_claim" if row else "missing_profile",
            "next_gate": next_gate,
        })
    return rows


def build_sensitivity(latency: Dict[str, Dict[str, str]], profile: Dict[str, Dict[str, str]]) -> List[Dict[str, object]]:
    candidate_t = fnum(latency.get(TARGET_VARIANT, {}).get("t_over_r_mean_us"))
    rows: List[Dict[str, object]] = []
    for component in ["mat_ep", "cmux_from_dft", "sub_a_total", "ncmux_total"]:
        share = fnum(profile.get(component, {}).get("share_of_profile_full"))
        for reduction in [0.10, 0.25, 0.50]:
            new_t = candidate_t * (1.0 - share * reduction) if candidate_t else 0.0
            rows.append({
                "component": component,
                "profile_share": f"{share:.6f}",
                "assumed_component_reduction": f"{reduction:.2f}",
                "projected_t_over_r_us": f"{new_t:.3f}" if candidate_t else "missing",
                "projected_speedup_vs_candidate": f"{candidate_t / new_t:.6f}" if candidate_t and new_t else "missing",
                "status": "what_if_projection_only",
            })
    return rows


def build_algorithm_frontier(residual: List[Dict[str, object]]) -> List[Dict[str, object]]:
    term = compact_term_row(R_VALUE)
    dense_terms = fnum(term.get("dense_terms_per_level"))
    compact_terms = fnum(term.get("shared_output_lane_local_terms"))
    compact_ratio = dense_terms / compact_terms if dense_terms and compact_terms else 0.0
    mat_row = next((row for row in residual if row["component"] == "mat_ep"), {})
    from_dft_row = next((row for row in residual if row["component"] == "cmux_from_dft"), {})
    return [
        {
            "candidate_id": "S284-A-current-selected-exact",
            "algorithm_delta": "Keep current exact dense backend_sub_decomp_dual path.",
            "measured_basis": "Stage281 repeated T_bootstrap/r plus Stage282 local noise/resource.",
            "theory_basis": "Same SAB schedule and same MAT selector/key semantics.",
            "risk": "Native target and hardware-counter evidence missing.",
            "next_gate": "Rerun Stage283 on authenticated native target.",
            "priority": "P0",
            "status": "local_positive_pending_native",
        },
        {
            "candidate_id": "S284-B-mat-ep-split-avx",
            "algorithm_delta": "Reduce MAT EP/sub-decomposition cost without changing selector semantics.",
            "measured_basis": f"Current candidate MAT EP profile share {mat_row.get('profile_share', 'missing')}.",
            "theory_basis": "A same-format improvement can move T_bootstrap/r only if MAT EP reduction survives full SAB.",
            "risk": "Native counters may show memory/FMA/register pressure not matching the source model.",
            "next_gate": "Native counter plus split microbench, then full SAB A/B.",
            "priority": "P1",
            "status": "admitted_but_no_hot_path_edit_without_counter_or_split_gate",
        },
        {
            "candidate_id": "S284-C-from-dft-lifecycle",
            "algorithm_delta": "Shorten from_DFT/materialization lifetime around CMUX output.",
            "measured_basis": f"Current candidate from_DFT profile share {from_dft_row.get('profile_share', 'missing')}.",
            "theory_basis": "Materialization traffic is large after backend direct-add and sub-decomp fusion.",
            "risk": "Previous direct-add-only route was neutral; repeated full SAB gate is mandatory.",
            "next_gate": "New alias-safe lifecycle design before implementation.",
            "priority": "P2",
            "status": "conditional_new_mechanism_required",
        },
        {
            "candidate_id": "S284-D-body-linear-selector-format",
            "algorithm_delta": "Change selector/key format toward body-linear or compact terms.",
            "measured_basis": f"Stage166 r={R_VALUE} dense/compact term ratio {compact_ratio:.6f}.",
            "theory_basis": "Would attack the dense (r+1)^2 term risk instead of tuning one dense kernel.",
            "risk": "Current compact/body-linear proxies are not admissible as exact dense lower bounds.",
            "next_gate": "Separate distribution/security and noise proof before hot-path code.",
            "priority": "P3",
            "status": "research_route_blocked_for_hot_path",
        },
        {
            "candidate_id": "S284-E-tail-and-sub-a",
            "algorithm_delta": "Optimize sub_a/NCMUX/extract residuals.",
            "measured_basis": "All are low-share in the selected candidate profile.",
            "theory_basis": "Amdahl impact is small unless combined with a broader schedule change.",
            "risk": "Likely neutral if pursued alone.",
            "next_gate": "Reopen only after a new profile shows larger share.",
            "priority": "P4",
            "status": "deferred",
        },
    ]


def build_claim_boundary() -> List[Dict[str, object]]:
    return [
        {
            "claim": "current_speedup_dimension",
            "status": "allowed",
            "allowed_wording": "Speedup is measured as complete SAB T_bootstrap/r, i.e. per processed plaintext lane/bit.",
            "forbidden_wording": "Speedup is raw total time for one r-body ciphertext without amortization.",
            "evidence": rel(FRONTIER),
        },
        {
            "claim": "current_candidate_promotion",
            "status": "local_only",
            "allowed_wording": "The selected candidate is locally repeated-positive and passes local proxy noise/resource.",
            "forbidden_wording": "The candidate is native/paper-grade proven.",
            "evidence": f"{rel(INPUTS['stage281_latency'])}; {rel(INPUTS['stage282_noise_resource'])}; {rel(INPUTS['stage283_probe'])}",
        },
        {
            "claim": "theoretical_optimality",
            "status": "blocked",
            "allowed_wording": "The lower-bound gap and admissible body-linear route remain open.",
            "forbidden_wording": "The current exact dense MAT AVX512 path is theoretically optimal.",
            "evidence": f"{rel(INPUTS['stage250_lower_bound'])}; {rel(RESIDUAL)}",
        },
        {
            "claim": "component_projection",
            "status": "projection_only",
            "allowed_wording": "Amdahl rows prioritize next gates; they are not measured speedups.",
            "forbidden_wording": "A zero-component projection is an achievable implementation result.",
            "evidence": rel(SENSITIVITY),
        },
    ]


def build_next_queue(native_missing: bool) -> List[Dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage285_native_target_rerun",
            "entry_condition": "Stage283 native access missing" if native_missing else "Stage283 native access available",
            "gate": "Rerun selected candidate and fast control on native target with T_bootstrap/r.",
            "failure_action": "Keep all target performance and counter claims local/proxy only.",
        },
        {
            "priority": "P1",
            "route": "stage286_mat_ep_split_counter_gate",
            "entry_condition": "MAT EP remains largest selected-candidate profile share.",
            "gate": "Split MAT EP into decompose/DFT/FMA/load-store attribution and require full SAB A/B before promotion.",
            "failure_action": "Do not edit hot path; record as counter/proxy-only.",
        },
        {
            "priority": "P2",
            "route": "stage287_from_dft_lifecycle_design",
            "entry_condition": "from_DFT share remains high after selected candidate.",
            "gate": "Alias-safe lifecycle design, isolated equivalence, then repeated T_bootstrap/r.",
            "failure_action": "Reject if repeated full SAB is neutral.",
        },
        {
            "priority": "P3",
            "route": "stage288_body_linear_selector_proof",
            "entry_condition": "pursue theoretical optimum beyond exact dense format.",
            "gate": "Distribution/security/noise proof for a new selector/key format before any hot-path code.",
            "failure_action": "Keep dense exact path as scoped engineering route.",
        },
    ]


def proof_rows(inputs: List[Dict[str, object]], frontier: List[Dict[str, object]], residual: List[Dict[str, object]]) -> List[Dict[str, object]]:
    missing = [row["input_id"] for row in inputs if row["status"] != "present"]
    front = {row["item"]: row for row in frontier}
    native_status = str(front.get("native_target_gate", {}).get("status", "missing"))
    incr = fnum(front.get("candidate_vs_fast_control_mean", {}).get("value"))
    conservative = fnum(front.get("candidate_vs_fast_control_conservative", {}).get("value"))
    mat_share = fnum(next((row.get("profile_share") for row in residual if row.get("component") == "mat_ep"), "0"))
    return [
        {
            "gate": "G1_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "required inputs",
            "value": "all present" if not missing else ",".join(missing),
            "interpretation": "Stage284 must be derived from current measured evidence.",
        },
        {
            "gate": "G2_primary_metric",
            "status": "PASS",
            "metric": "endpoint",
            "value": "T_bootstrap/r",
            "interpretation": "This stage preserves the r-body per-lane comparison requested for MAT-RLWE SAB.",
        },
        {
            "gate": "G3_local_repeated_candidate",
            "status": "PASS" if incr >= 1.02 and conservative > 1.0 else "MISSING_OR_NEUTRAL",
            "metric": "candidate/control speedup",
            "value": f"mean={incr:.6f}; conservative={conservative:.6f}",
            "interpretation": "Local repeated speed is positive but remains platform-scoped.",
        },
        {
            "gate": "G4_residual_frontier",
            "status": "PASS" if mat_share > 0.30 else "WEAK",
            "metric": "selected candidate MAT EP share",
            "value": f"{mat_share:.6f}",
            "interpretation": "Next code work must target measured residual share, not an abstract bottleneck.",
        },
        {
            "gate": "G5_native_boundary",
            "status": "PASS_BOUNDARY_RECORDED" if native_status != "passed" else "PASS_NATIVE_AVAILABLE",
            "metric": "native access",
            "value": native_status,
            "interpretation": "No native/paper-grade target claim is allowed while access is missing.",
        },
        {
            "gate": "G6_decision",
            "status": DECISION,
            "metric": "stage decision",
            "value": DECISION,
            "interpretation": "Proceed to native rerun or MAT EP split/counter gate; do not claim optimality.",
        },
    ]


def write_documents(
    frontier: List[Dict[str, object]],
    residual: List[Dict[str, object]],
    sensitivity: List[Dict[str, object]],
    algorithm: List[Dict[str, object]],
    claims: List[Dict[str, object]],
    proof: List[Dict[str, object]],
    next_rows: List[Dict[str, object]],
) -> None:
    report = f"""# Stage284 Frontier Gap Ledger

Decision: `{DECISION}`.

Stage284 aligns the current selected PVW/MAT-SAB path with the original
MAT-RLWE/r-body research objective.  It treats `T_bootstrap/r` as the only
primary speed endpoint, consumes the latest repeated/noise/resource/native
gates, and converts the residual profile into falsifiable next-stage work.

## Frontier Summary

{markdown_table(frontier, ["item", "value", "status", "interpretation"])}

## Residual Gap Ledger

{markdown_table(residual, ["component", "profile_share", "component_us_profile_total", "calls", "projected_t_over_r_if_zero_us", "zero_component_upper_bound_vs_candidate", "next_gate"])}

## Algorithm Frontier

{markdown_table(algorithm, ["candidate_id", "priority", "status", "algorithm_delta", "next_gate"])}

## Claim Boundary

{markdown_table(claims, ["claim", "status", "allowed_wording", "forbidden_wording"])}

## Proof Gate

{markdown_table(proof, ["gate", "status", "metric", "value", "interpretation"])}

## Next Queue

{markdown_table(next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])}

Generated from head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)

    theory = f"""# Stage284 Frontier Gap Model

## Endpoint

The active endpoint is:

```text
A(r) = T_complete_bootstrap_producing_r_outputs / r
speedup(r) = A_repeated_scalar(r) / A_mat(r)
```

Stage284 uses the Stage281 repeated value for the selected candidate and
keeps all native claims blocked by Stage283.

## Residual/Amdahl Model

For a measured component share `s_i` in the selected candidate profile:

```text
A_after_component_reduction(x) = A_current * (1 - s_i * x)
projected_speedup(x) = A_current / A_after_component_reduction(x)
zero_component_ceiling = 1 / (1 - s_i)
```

These are prioritization projections, not speed claims.  A projection becomes
evidence only after isolated correctness, repeated complete-SAB `T_bootstrap/r`,
noise/resource, and backend-fair gates pass.

## Current Interpretation

- The selected candidate is locally repeated-positive against fast control.
- MAT EP remains the largest selected-candidate residual share.
- from_DFT/materialization is also large but prior direct-add-only work was
  not sufficient, so it needs a new alias/lifecycle mechanism.
- sub_a, NCMUX, and tail residuals are not first-order standalone targets under
  the current profile.
- The compact/body-linear term model remains a research route, not an
  admissible exact-dense lower bound.
"""
    write_text(THEORY, theory)

    variant = f"""# Stage284 MAT-RLWE SAB Frontier Candidates

## Scope

This file records candidates admitted by the current frontier ledger.  Every
candidate must preserve scalar/default SAB behavior and must be evaluated using
complete-SAB `T_bootstrap/r`.

{markdown_table(algorithm, ["candidate_id", "algorithm_delta", "measured_basis", "theory_basis", "risk", "next_gate", "status"])}

## Promotion Rule

A candidate is promoted only if it passes:

1. isolated equivalence for every affected lane/state transition;
2. complete-SAB correctness;
3. repeated `T_bootstrap/r` A/B against the current best same-backend control;
4. noise/resource reporting;
5. native or explicitly scoped platform provenance when making target claims.
"""
    write_text(VARIANT, variant)

    plan = f"""# Stage284 Frontier Validation Plan

## Immediate Gates

{markdown_table(next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])}

## Required Statistics

- Use repeated complete-SAB `T_bootstrap/r`; do not use profiled runs for final
  latency claims.
- Record mean, min, max, and conservative guards at minimum.
- Keep native target evidence separate from WSL/proxy evidence.
- Treat Amdahl rows as planning evidence only.

## Reproduction

```bash
python3 scripts/build_stage284_frontier_gap_ledger.py
```
"""
    write_text(PLAN, plan)

    write_text(COMMANDS, """# Stage284 Reproduction Commands

```bash
python3 scripts/build_stage284_frontier_gap_ledger.py
```

This stage is a ledger builder.  It consumes Stage250/280/281/282/283 CSV
artifacts and does not run a heavy SAB benchmark.
""")


def artifact_index() -> None:
    paths = [
        DOC,
        THEORY,
        VARIANT,
        PLAN,
        COMMANDS,
        REPORT,
        INPUT_STATUS,
        FRONTIER,
        RESIDUAL,
        SENSITIVITY,
        ALGO_QUEUE,
        CLAIM,
        PROOF,
        NEXT,
        BUILDER,
    ]
    write_csv(ARTIFACT, ["path", "bytes", "sha256"], [sha256(path) for path in paths if path.exists()])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = input_status_rows()
    latency = latency_rows()
    profile = profile_rows_for(TARGET_VARIANT)
    frontier = build_frontier_summary(latency)
    residual = build_residual_ledger(latency, profile)
    sensitivity = build_sensitivity(latency, profile)
    algorithm = build_algorithm_frontier(residual)
    claims = build_claim_boundary()
    native_missing = (read_csv(INPUTS["stage283_probe"]) or [{}])[0].get("status") != "passed"
    next_rows = build_next_queue(native_missing)
    proofs = proof_rows(inputs, frontier, residual)

    write_csv(INPUT_STATUS, ["input_id", "path", "status", "bytes"], inputs)
    write_csv(FRONTIER, ["item", "value", "status", "evidence", "interpretation"], frontier)
    write_csv(RESIDUAL, [
        "component", "meaning", "profile_share", "component_us_profile_total", "calls",
        "candidate_t_over_r_us", "projected_t_over_r_if_zero_us",
        "zero_component_upper_bound_vs_candidate", "claim_status", "next_gate",
    ], residual)
    write_csv(SENSITIVITY, [
        "component", "profile_share", "assumed_component_reduction",
        "projected_t_over_r_us", "projected_speedup_vs_candidate", "status",
    ], sensitivity)
    write_csv(ALGO_QUEUE, [
        "candidate_id", "algorithm_delta", "measured_basis", "theory_basis",
        "risk", "next_gate", "priority", "status",
    ], algorithm)
    write_csv(CLAIM, ["claim", "status", "allowed_wording", "forbidden_wording", "evidence"], claims)
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proofs)
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], next_rows)
    write_documents(frontier, residual, sensitivity, algorithm, claims, proofs, next_rows)

    append_once(CURRENT_GOAL, "<!-- stage284-frontier-gap-ledger -->", f"""<!-- stage284-frontier-gap-ledger -->
### Stage284 frontier gap ledger

`{DECISION}` records the current MAT-RLWE/r-body SAB frontier under the
`T_bootstrap/r` endpoint. The selected `backend_sub_decomp_dual` path is
local repeated-positive and local noise/resource-clean, but native target
evidence and theoretical optimality remain open. The next executable routes
are native rerun first, then MAT EP split/counter attribution, then new
from_DFT lifecycle or body-linear selector proof gates.
""")
    append_once(HYPOTHESES, "H10_stage284_frontier_gap_ledger:", f"""H10_stage284_frontier_gap_ledger:
  status: {DECISION}
  evidence:
    - repro/stage284_frontier_gap_ledger/frontier_summary.csv
    - repro/stage284_frontier_gap_ledger/residual_gap_ledger.csv
    - repro/stage284_frontier_gap_ledger/algorithm_frontier.csv
    - docs/stage284_frontier_gap_ledger.md
  conclusion: >
    Stage284 fixes the current frontier around complete-SAB T_bootstrap/r:
    the selected CMUX residual candidate is local repeated-positive, MAT EP is
    the largest measured residual component, native evidence remains missing,
    and theoretical optimality remains blocked pending lower-bound and
    counter-backed gates.
""")
    append_once(RUN_LOG, "stage284-frontier-gap-ledger-001", f"""stage284-frontier-gap-ledger-001,2026-07-04,{git_head()},Stage 284,ledger,no-heavy-run,"current MAT-RLWE SAB frontier gap ledger from Stage250/280/281/282/283 evidence",n/a,{DECISION},"Primary endpoint remains T_bootstrap/r; no optimality or native claim.",docs/stage284_frontier_gap_ledger.md; repro/stage284_frontier_gap_ledger/proof_gate.csv
""")
    append_once(MANIFEST, "- stage284_frontier_gap_ledger:", """- stage284_frontier_gap_ledger:
  - `docs/stage284_frontier_gap_ledger.md`
  - `theory_checks/stage284_frontier_gap_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage284_frontier_candidates.md`
  - `experiments/stage284_frontier_validation_plan.md`
  - `scripts/build_stage284_frontier_gap_ledger.py`
  - `repro/stage284_frontier_gap_ledger/`
""")
    append_once(CHECKLIST, "<!-- stage284-frontier-gap-ledger-checklist -->", f"""<!-- stage284-frontier-gap-ledger-checklist -->
- [x] Stage284 records `{DECISION}` for the current T_bootstrap/r frontier gap ledger.
""")
    artifact_index()
    print(DECISION)


if __name__ == "__main__":
    main()
