#!/usr/bin/env python3
"""Build Stage106 MAT-RLWE SAB research-loop artifacts.

Stage106 reframes the PVW/MAT-SAB objective around amortized bootstrap
latency per processed lane/bit, and records finite theory/experiment gates
for the r-body MAT-RLWE optimality program.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage106_mat_rlwe_sab_research_loop"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_AMORTIZED = OUT_DIR / "amortized_metric_table.csv"
OUT_GATES = OUT_DIR / "research_gate_matrix.csv"
OUT_THEORY = OUT_DIR / "theory_bound_matrix.csv"
OUT_VARIANTS = OUT_DIR / "candidate_variant_matrix.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage106_mat_rlwe_sab_research_loop.md"

STAGE36_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE88_FULL_SAB = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "full_sab_repeated.csv"
STAGE88_NOISE = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "noise_summary.csv"
STAGE88_RESOURCE = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "resource_summary.csv"
STAGE101_COUNTERS = ROOT / "repro" / "stage101_cb5_remote_native_perf" / "counter_metrics.csv"
STAGE105 = ROOT / "repro" / "stage105_goal_completion_audit" / "summary.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STATIC_ARTIFACTS = [
    ROOT / "docs" / "stage106_mat_rlwe_sab_research_loop.md",
    ROOT / "experiments" / "stage106_mat_rlwe_sab_research_plan.md",
    ROOT / "theory_checks" / "mat_rlwe_sab_amortized_optimality.md",
    ROOT / "algorithm_variants" / "mat_rlwe_sab_rbody_optimal_path.md",
    ROOT / "literature" / "mat_rlwe_sab_literature_axes.csv",
    ROOT / "scripts" / "build_stage106_mat_rlwe_sab_research_loop.py",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
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


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
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


def stage105_pass() -> bool:
    rows = {row.get("gate"): row for row in read_csv(STAGE105)}
    return (
        rows.get("stage105_decision", {}).get("status")
        == "PASS_STAGE105_SCOPED_GOAL_COMPLETE_STRONGER_CLAIMS_BLOCKED"
    )


def build_amortized_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for row in read_csv(STAGE36_PERF):
        r = int(row["r"])
        pvw = float(row["pvw_mean_us"])
        scalar = float(row["scalar_repeated_mean_us"])
        rows.append(
            {
                "source": f"stage36_target_r{r}_10run",
                "variant": "active_buffer_pvw_mat_sab",
                "param": "SET_2_3_2048",
                "backend": "spqlios_avx512",
                "r": str(r),
                "samples": row["samples"],
                "evidence_level": "10_run_complete_sab",
                "pvw_total_us": f"{pvw:.3f}",
                "scalar_repeated_total_us": f"{scalar:.3f}",
                "pvw_per_lane_us": f"{pvw / r:.3f}",
                "scalar_per_lane_us": f"{scalar / r:.3f}",
                "amortized_speedup": row["mean_speedup"],
                "ci95_low": row.get("ci95_low", ""),
                "status": row.get("decision", ""),
                "interpretation": "same-r total-time speedup equals per-lane amortized speedup",
            }
        )
    for row in read_csv(STAGE88_FULL_SAB):
        if row.get("variant") != "backend":
            continue
        r = int(row["r"])
        pvw = float(row["pvw_mean_us"])
        scalar = float(row["scalar_repeated_mean_us"])
        rows.append(
            {
                "source": "stage88_h14_backend_r6_3run",
                "variant": "h14_backend_from_dft_add_explicit",
                "param": "SET_2_3_2048",
                "backend": "spqlios_avx512",
                "r": str(r),
                "samples": row["samples"],
                "evidence_level": "3_run_complete_sab_candidate",
                "pvw_total_us": f"{pvw:.3f}",
                "scalar_repeated_total_us": f"{scalar:.3f}",
                "pvw_per_lane_us": f"{pvw / r:.3f}",
                "scalar_per_lane_us": f"{scalar / r:.3f}",
                "amortized_speedup": row["mean_speedup_vs_scalar"],
                "ci95_low": "",
                "status": "CANDIDATE_EXPLICIT_NOT_DEFAULT",
                "interpretation": "amortized candidate evidence; not high-stat or paper-level",
            }
        )
    return rows


def build_theory_rows() -> List[Dict[str, str]]:
    h = 39
    rho = 7
    n = 2048
    cmux_per_scalar = (h + 1) * rho * n
    return [
        {
            "model_id": "M1",
            "object": "scalar repeated SAB",
            "formula": "T_scalar_repeat(r)=r*((h+1)*rho*N*C_scalar_cmux+T_tail_scalar)",
            "instantiated_count": f"r*{cmux_per_scalar} CMUX/NCMUX-equivalent scalar updates",
            "status": "FORMAL_MODEL_BASELINE",
            "next_required_check": "keep same backend and same processed lane count for every comparison",
        },
        {
            "model_id": "M2",
            "object": "MAT-RLWE SAB schedule",
            "formula": "T_mat(r)=(h+1)*rho*N*C_mat_cmux(r)+T_tail_mat(r)",
            "instantiated_count": f"{cmux_per_scalar} MAT CMUX/NCMUX schedule steps updating r bodies",
            "status": "FORMAL_MODEL_TO_REFINE",
            "next_required_check": "measure C_mat_cmux(r) decomposition into DFT/FMA/load/store/fromDFT/body-add",
        },
        {
            "model_id": "M3",
            "object": "amortized primary endpoint",
            "formula": "A_mat(r)=T_mat(r)/r; improvement=A_scalar_repeat(r)/A_mat(r)",
            "instantiated_count": "reported stage speedups are valid only because both sides process r lanes",
            "status": "PRIMARY_ENDPOINT_FIXED",
            "next_required_check": "all future tables must report total time and per-lane time",
        },
        {
            "model_id": "M4",
            "object": "optimality lower-bound gap",
            "formula": "gap(r)=A_impl(r)/A_lower_bound(r), where bound separates shared schedule and unavoidable body work",
            "instantiated_count": "not yet numerically closed",
            "status": "THEORY_GAP_OPEN_NOT_A_RESULT",
            "next_required_check": "derive lower bound from memory/FMA counts and validate with assembly/perf counters",
        },
        {
            "model_id": "M5",
            "object": "dense MAT risk",
            "formula": "if C_mat_cmux(r) grows like r^2, A_mat(r) can stop improving despite schedule sharing",
            "instantiated_count": "observed r=6 candidate improves but needs model-gap attribution",
            "status": "RISK_TO_TEST",
            "next_required_check": "compare body-linear, tiled, and dense MAT kernels under same SAB schedule",
        },
    ]


def build_gate_rows(amortized_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    r2_ok = any(
        row["r"] == "2"
        and row["status"] == "PASS_TARGET_PERF_10RUN"
        and float(row["ci95_low"]) > 1.0
        for row in amortized_rows
    )
    r4_ok = any(
        row["r"] == "4"
        and row["status"] == "PASS_TARGET_PERF_10RUN"
        and float(row["ci95_low"]) > 1.0
        for row in amortized_rows
    )
    r6_candidate = any(row["r"] == "6" for row in amortized_rows)
    stage88_noise = {
        row.get("r"): row for row in read_csv(STAGE88_NOISE)
    }.get("6", {})
    stage88_resource = {
        row.get("r"): row for row in read_csv(STAGE88_RESOURCE)
    }.get("6", {})
    counter_metrics = {row.get("metric"): row for row in read_csv(STAGE101_COUNTERS)}
    counters_ok = all(
        metric in counter_metrics
        for metric in [
            "mem_inst_retired.all_loads",
            "mem_inst_retired.all_stores",
            "fp_arith_inst_retired.512b_packed_double",
        ]
    )
    return [
        {
            "gate": "G1_primary_metric_reframed",
            "status": "PASS",
            "evidence": rel(OUT_AMORTIZED),
            "decision": "Use T_total/r as the primary endpoint for MAT-RLWE SAB.",
            "failure_or_stop_rule": "Reject any future speedup table that omits per-lane time.",
        },
        {
            "gate": "G2_existing_r2_r4_amortized_support",
            "status": "PASS" if r2_ok and r4_ok else "FAIL",
            "evidence": rel(STAGE36_PERF),
            "decision": "Existing complete-SAB data supports amortized improvement for r=2/r=4.",
            "failure_or_stop_rule": "Rerun Stage36 if target parameters, backend, or benchmark harness changes.",
        },
        {
            "gate": "G3_r6_candidate_support",
            "status": "CANDIDATE_ONLY" if r6_candidate else "MISSING",
            "evidence": rel(STAGE88_FULL_SAB),
            "decision": "H14 r=6 backend path is a candidate, not a high-stat optimality result.",
            "failure_or_stop_rule": "Do not promote r=6 to paper-level optimality without 10+ runs and model-gap analysis.",
        },
        {
            "gate": "G4_correctness_noise_resource_guard",
            "status": "PASS_CANDIDATE_GUARD"
            if stage88_noise.get("status") == "PASS" and stage88_resource.get("status") == "PASS"
            else "MISSING_OR_FAILING",
            "evidence": f"{rel(STAGE88_NOISE)}; {rel(STAGE88_RESOURCE)}",
            "decision": "r=6 candidate has smoke-scale noise/resource support only.",
            "failure_or_stop_rule": "Any new variant needs deterministic equivalence, multi-seed noise, and resource tables before speedup claims.",
        },
        {
            "gate": "G5_counter_model_not_optimality",
            "status": "PASS_ATTRIBUTION_ONLY" if counters_ok else "MISSING_COUNTERS",
            "evidence": rel(STAGE101_COUNTERS),
            "decision": "Hardware counters exist for attribution but do not close theoretical optimality.",
            "failure_or_stop_rule": "Stop theoretical-optimality wording until load/store/FMA lower bound and assembly audit are recorded.",
        },
        {
            "gate": "G6_no_theory_loop_rule",
            "status": "PASS_PROCESS_GATE",
            "evidence": rel(OUT_GATES),
            "decision": "Every theory item must name the next experiment or be demoted to background.",
            "failure_or_stop_rule": "After two theory-only iterations without a runnable gate, freeze the hypothesis and run measurement.",
        },
        {
            "gate": "G7_stage105_precondition",
            "status": "PASS" if stage105_pass() else "FAIL",
            "evidence": rel(STAGE105),
            "decision": "Stage106 starts from the closed scoped package and reopens only the optimality research question.",
            "failure_or_stop_rule": "Do not reinterpret old evidence if Stage105 is not passing.",
        },
    ]


def build_variant_rows() -> List[Dict[str, str]]:
    return [
        {
            "variant_id": "V106-A",
            "name": "current_active_buffer_pvw_mat_sab",
            "status": "BASELINE_FOR_NEW_RESEARCH_LOOP",
            "main_delta": "r-body shared-mask accumulator plus active-buffer copyback fusion",
            "primary_metric": "T_total/r",
            "required_next_experiment": "keep as baseline for all future MAT-RLWE optimality variants",
        },
        {
            "variant_id": "V106-B",
            "name": "body_linear_mat_external_product",
            "status": "HYPOTHESIS_THEORY_AND_KERNEL_GATE_REQUIRED",
            "main_delta": "avoid dense r^2 body interaction when SAB lanes are independent",
            "primary_metric": "C_mat_cmux(r)/r and full SAB T_total/r",
            "required_next_experiment": "microbench r=2/4/6/8 plus full SAB A/B under same schedule",
        },
        {
            "variant_id": "V106-C",
            "name": "dfT_lazy_schedule_window",
            "status": "HYPOTHESIS_SCHEDULE_GATE_REQUIRED",
            "main_delta": "carry DFT or partially materialized state across CMUX windows",
            "primary_metric": "fromDFT/add/store traffic per lane",
            "required_next_experiment": "single-window equivalence, then full sparse_mul correctness and profile",
        },
        {
            "variant_id": "V106-D",
            "name": "body_major_coefficient_blocked_layout",
            "status": "HYPOTHESIS_LAYOUT_GATE_REQUIRED",
            "main_delta": "re-layout r bodies to improve AVX512 load/store locality",
            "primary_metric": "load/store counters and T_total/r",
            "required_next_experiment": "layout-only kernel microbench; do not change key format until positive",
        },
        {
            "variant_id": "V106-E",
            "name": "r_adaptive_tile_policy",
            "status": "HYPOTHESIS_POLICY_GATE_REQUIRED",
            "main_delta": "select small-r, r=6, and r>6 tiles from measured model gaps",
            "primary_metric": "best validated A_mat(r) under resource limits",
            "required_next_experiment": "r sweep with the same gates and resource thresholds",
        },
    ]


def build_summary(gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    blocking = [
        row for row in gates
        if row["status"] in {"FAIL", "MISSING", "MISSING_OR_FAILING", "MISSING_COUNTERS"}
    ]
    decision = (
        "PASS_STAGE106_RESEARCH_LOOP_FIXED_OPTIMALITY_OPEN"
        if not blocking
        else "FAIL_STAGE106_RESEARCH_LOOP"
    )
    return [
        {
            "gate": "stage106_primary_endpoint",
            "status": "PASS",
            "evidence": rel(OUT_AMORTIZED),
            "detail": "Primary endpoint is amortized complete-SAB latency per processed lane/bit: T_total/r.",
            "next_action": "All future benchmarks must report total and per-lane latency.",
        },
        {
            "gate": "stage106_existing_evidence_reinterpreted",
            "status": "PASS",
            "evidence": rel(OUT_AMORTIZED),
            "detail": "Existing r=2/r=4 speedups are same-r total-time speedups and therefore equal per-lane amortized speedups.",
            "next_action": "Use Stage36 as the current high-stat baseline for r=2/r=4.",
        },
        {
            "gate": "stage106_theoretical_optimality_boundary",
            "status": "OPEN_NOT_PROVEN",
            "evidence": rel(OUT_THEORY),
            "detail": "The MAT-RLWE SAB optimality claim remains open until lower-bound gap and implementation counters are closed.",
            "next_action": "Run bounded model-gap stages instead of theory-only discussion.",
        },
        {
            "gate": "stage106_decision",
            "status": decision,
            "evidence": rel(OUT_GATES),
            "detail": "Research loop is fixed; existing evidence is usable for amortized improvement, but theoretical optimality is not yet proven.",
            "next_action": "Start the next runnable gate with V106-B or V106-D before any stronger claim.",
        },
    ]


def write_md(
    summary: List[Dict[str, str]],
    amortized: List[Dict[str, str]],
    theory: List[Dict[str, str]],
    gates: List[Dict[str, str]],
    variants: List[Dict[str, str]],
) -> None:
    lines = [
        "# Stage106 MAT-RLWE SAB Research Loop",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage106 reframes PVW/MAT-SAB as an algorithmic MAT-RLWE SAB",
        "research program. The primary endpoint is complete-SAB latency",
        "amortized over processed lanes/bits:",
        "",
        "```text",
        "A_mat(r) = T_mat_complete_bootstrap(r) / r",
        "```",
        "",
        "The existing r=2/r=4 complete-SAB speedups remain valid under this",
        "endpoint because the compared runs process the same number of lanes.",
        "Theoretical optimality is explicitly left open.",
        "",
        "## Summary",
        "",
        "| gate | status | detail |",
        "|---|---|---|",
    ]
    for row in summary:
        lines.append(f"| {row['gate']} | {row['status']} | {row['detail']} |")
    lines += [
        "",
        "## Amortized Evidence",
        "",
        "| source | r | samples | PVW total s | scalar total s | PVW per lane s | scalar per lane s | speedup | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in amortized:
        lines.append(
            "| {source} | {r} | {samples} | {pvw_total:.6f} | {scalar_total:.6f} | "
            "{pvw_lane:.6f} | {scalar_lane:.6f} | {speedup} | {status} |".format(
                source=row["source"],
                r=row["r"],
                samples=row["samples"],
                pvw_total=float(row["pvw_total_us"]) / 1_000_000,
                scalar_total=float(row["scalar_repeated_total_us"]) / 1_000_000,
                pvw_lane=float(row["pvw_per_lane_us"]) / 1_000_000,
                scalar_lane=float(row["scalar_per_lane_us"]) / 1_000_000,
                speedup=row["amortized_speedup"],
                status=row["status"],
            )
        )
    lines += [
        "",
        "## Theory Model",
        "",
        "| id | object | formula | status | next check |",
        "|---|---|---|---|---|",
    ]
    for row in theory:
        lines.append(
            f"| {row['model_id']} | {row['object']} | `{row['formula']}` | "
            f"{row['status']} | {row['next_required_check']} |"
        )
    lines += [
        "",
        "## Research Gates",
        "",
        "| gate | status | decision | stop rule |",
        "|---|---|---|---|",
    ]
    for row in gates:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['decision']} | {row['failure_or_stop_rule']} |"
        )
    lines += [
        "",
        "## Candidate Variants",
        "",
        "| id | name | status | next experiment |",
        "|---|---|---|---|",
    ]
    for row in variants:
        lines.append(
            f"| {row['variant_id']} | {row['name']} | {row['status']} | {row['required_next_experiment']} |"
        )
    lines += [
        "",
        "## Non-Drift Rule",
        "",
        "Do not promote a theory claim unless it has a named experiment and a",
        "recorded result. After two theory-only iterations without a runnable gate,",
        "freeze the hypothesis and run the closest microbench or complete-SAB A/B.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def upsert_run_log(status_value: str) -> None:
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
    rows = [
        row for row in rows
        if row.get("run_id") != "stage106-mat-rlwe-sab-research-loop-001"
    ]
    rows.append(
        {
            "run_id": "stage106-mat-rlwe-sab-research-loop-001",
            "date": "2026-07-03",
            "commit_or_state": git_head(),
            "stage": "Stage 106",
            "backend": "n/a",
            "command": "python scripts/build_stage106_mat_rlwe_sab_research_loop.py",
            "params": "MAT-RLWE SAB research loop; primary endpoint T_total/r; no heavy benchmark rerun",
            "seed": "n/a",
            "status": status_value,
            "summary": (
                "Stage106 fixes the amortized per-lane/bit endpoint for MAT-RLWE "
                "SAB, reinterprets existing same-r complete-SAB speedups under "
                "that endpoint, and records finite theory/experiment gates for "
                "optimality research without claiming optimality."
            ),
            "artifacts": "; ".join(
                [
                    rel(OUT_MD),
                    rel(ROOT / "experiments" / "stage106_mat_rlwe_sab_research_plan.md"),
                    rel(ROOT / "theory_checks" / "mat_rlwe_sab_amortized_optimality.md"),
                    rel(ROOT / "algorithm_variants" / "mat_rlwe_sab_rbody_optimal_path.md"),
                    rel(ROOT / "literature" / "mat_rlwe_sab_literature_axes.csv"),
                    rel(OUT_SUMMARY),
                    rel(OUT_AMORTIZED),
                    rel(OUT_GATES),
                    rel(OUT_THEORY),
                    rel(OUT_VARIANTS),
                    rel(OUT_INDEX),
                ]
            ),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> None:
    amortized = build_amortized_rows()
    theory = build_theory_rows()
    gates = build_gate_rows(amortized)
    variants = build_variant_rows()
    summary = build_summary(gates)
    write_csv(
        OUT_AMORTIZED,
        amortized,
        [
            "source",
            "variant",
            "param",
            "backend",
            "r",
            "samples",
            "evidence_level",
            "pvw_total_us",
            "scalar_repeated_total_us",
            "pvw_per_lane_us",
            "scalar_per_lane_us",
            "amortized_speedup",
            "ci95_low",
            "status",
            "interpretation",
        ],
    )
    write_csv(
        OUT_THEORY,
        theory,
        [
            "model_id",
            "object",
            "formula",
            "instantiated_count",
            "status",
            "next_required_check",
        ],
    )
    write_csv(
        OUT_GATES,
        gates,
        ["gate", "status", "evidence", "decision", "failure_or_stop_rule"],
    )
    write_csv(
        OUT_VARIANTS,
        variants,
        [
            "variant_id",
            "name",
            "status",
            "main_delta",
            "primary_metric",
            "required_next_experiment",
        ],
    )
    write_csv(
        OUT_SUMMARY,
        summary,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_md(summary, amortized, theory, gates, variants)
    write_csv(
        OUT_INDEX,
        artifact_index(
            [
                *STATIC_ARTIFACTS,
                OUT_SUMMARY,
                OUT_AMORTIZED,
                OUT_GATES,
                OUT_THEORY,
                OUT_VARIANTS,
                OUT_INDEX,
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    upsert_run_log(summary[-1]["status"])
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_AMORTIZED)}")
    print(f"Wrote {rel(OUT_GATES)}")
    print(f"Stage106 research loop: {summary[-1]['status']}")


if __name__ == "__main__":
    main()
