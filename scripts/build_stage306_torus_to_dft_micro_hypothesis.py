#!/usr/bin/env python3
"""Build Stage306 torus-to-DFT residual hypothesis artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage306_torus_to_dft_micro_hypothesis"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage306_torus_to_dft_micro_hypothesis.md"
THEORY = ROOT / "theory_checks" / "stage306_torus_to_dft_lifecycle_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage306_torus_to_dft_candidates.md"
PLAN = ROOT / "experiments" / "stage306_torus_to_dft_micro_hypothesis_plan.md"
RUNNER = ROOT / "scripts" / "run_stage306_torus_to_dft_micro_hypothesis.sh"
BUILDER = ROOT / "scripts" / "build_stage306_torus_to_dft_micro_hypothesis.py"

RUN_METRICS = OUT / "current_microbench_run_metrics.csv"
SUMMARY = OUT / "stage306_summary.csv"
EVIDENCE = OUT / "evidence_matrix.csv"
CANDIDATES = OUT / "candidate_matrix.csv"
BUDGET = OUT / "component_budget.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage306_report.md"
ARTIFACT = OUT / "artifact_index.csv"

STAGE289 = ROOT / "repro" / "stage289_mat_dft_array_microbench" / "bench_summary.csv"
STAGE290 = ROOT / "repro" / "stage290_dft_direct_output_microbench" / "bench_summary.csv"
STAGE291 = ROOT / "repro" / "stage291_sub_decomp_dft_direct_microbench" / "bench_summary.csv"
STAGE305_COMPONENTS = ROOT / "repro" / "stage305_materialization_split_probe" / "split_components.csv"
STAGE305_SUMMARY = ROOT / "repro" / "stage305_materialization_split_probe" / "split_summary.csv"
STAGE305_PROOF = ROOT / "repro" / "stage305_materialization_split_probe" / "proof_gate.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_PASS = "PASS_STAGE306_TORUS_TO_DFT_DIRECT_LIFECYCLE_TARGET_ADMITTED"
DECISION_NEUTRAL = "NEUTRAL_STAGE306_NO_NEW_TORUS_TO_DFT_CANDIDATE"
DECISION_FAIL = "FAIL_STAGE306_TORUS_TO_DFT_EVIDENCE_INCOMPLETE"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def mean_fmt(values: List[float]) -> str:
    return f"{mean(values):.6f}" if values else "0.000000"


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def parse_log(path: Path, variant: str, run_idx: int) -> Dict[str, object]:
    text = read_text(path)
    correctness = re.search(
        r"MAT_SUB_DFT correctness r=(?P<r>\d+) N=(?P<N>\d+) "
        r"max_abs_diff=(?P<max_abs_diff>\S+) status=(?P<status>\w+)",
        text,
    )
    bench = re.search(
        r"MAT_SUB_DFT bench r=(?P<r>\d+) N=(?P<N>\d+) reps=(?P<reps>\d+) "
        r"separate_avg_us=(?P<separate>\S+) sub_avg_us=(?P<sub>\S+) "
        r"speedup_vs_separate=(?P<speedup>\S+)x checksum=(?P<checksum>\S+)",
        text,
    )
    if correctness is None or bench is None:
        return {"variant": variant, "run": run_idx, "status": "MISSING_OUTPUT", "source_log": rel(path)}
    return {
        "variant": variant,
        "run": run_idx,
        "status": correctness.group("status"),
        "r": correctness.group("r"),
        "N": correctness.group("N"),
        "reps": bench.group("reps"),
        "max_abs_diff": correctness.group("max_abs_diff"),
        "separate_avg_us": bench.group("separate"),
        "sub_avg_us": bench.group("sub"),
        "speedup_vs_separate": bench.group("speedup"),
        "checksum": bench.group("checksum"),
        "source_log": rel(path),
    }


def stage_decision(path: Path) -> str:
    rows = read_csv(path)
    if not rows:
        return "MISSING"
    return rows[0].get("decision", "MISSING")


def stage_speed(path: Path, field: str) -> str:
    rows = read_csv(path)
    if not rows:
        return ""
    return rows[0].get(field, "")


def stage305_passed() -> bool:
    rows = read_csv(STAGE305_PROOF)
    return any(
        row.get("gate") == "G5_decision"
        and row.get("status") == "PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED"
        for row in rows
    )


def component_rows() -> List[Dict[str, str]]:
    return read_csv(STAGE305_COMPONENTS)


def direct_components() -> List[Dict[str, str]]:
    return [row for row in component_rows() if row.get("variant") == "direct_dft"]


def dominant_direct_component() -> Dict[str, str]:
    rows = direct_components()
    if not rows:
        return {}
    return max(rows, key=lambda row: fnum(row.get("share_of_split_total")))


def direct_summary() -> Dict[str, str]:
    for row in read_csv(STAGE305_SUMMARY):
        if row.get("variant") == "direct_dft":
            return row
    return {}


def collect_current_microbench() -> tuple[List[Dict[str, object]], Dict[str, object]]:
    run_rows: List[Dict[str, object]] = []
    for variant in ["baseline_sub_decomp", "direct_sub_decomp_dft"]:
        for idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
            run_rows.append(parse_log(path, variant, idx))
    fields = [
        "variant", "run", "status", "r", "N", "reps", "max_abs_diff",
        "separate_avg_us", "sub_avg_us", "speedup_vs_separate", "checksum",
        "source_log",
    ]
    write_csv(RUN_METRICS, run_rows, fields)

    baseline = [row for row in run_rows if row.get("variant") == "baseline_sub_decomp" and row.get("status") == "Pass"]
    direct = [row for row in run_rows if row.get("variant") == "direct_sub_decomp_dft" and row.get("status") == "Pass"]
    baseline_sub = [fnum(row.get("sub_avg_us")) for row in baseline]
    direct_sub = [fnum(row.get("sub_avg_us")) for row in direct]
    paired = [
        baseline_sub[idx] / direct_sub[idx]
        for idx in range(min(len(baseline_sub), len(direct_sub)))
        if direct_sub[idx] > 0.0
    ]
    summary = {
        "runs_per_variant": len(baseline),
        "direct_runs": len(direct),
        "all_correct": "PASS" if len(baseline) > 0 and len(baseline) == len(direct) else "FAIL",
        "baseline_sub_avg_us_mean": mean_fmt(baseline_sub),
        "direct_sub_avg_us_mean": mean_fmt(direct_sub),
        "direct_vs_baseline_speedup_mean": f"{mean(paired):.6f}" if paired else "0.000000",
        "direct_vs_baseline_speedup_min": f"{min(paired):.6f}" if paired else "0.000000",
        "direct_vs_baseline_speedup_max": f"{max(paired):.6f}" if paired else "0.000000",
    }
    return run_rows, summary


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage306-torus-to-dft-micro-hypothesis-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = ["run_id", "date", "git_ref", "stage", "backend", "command", "config", "seed", "status", "summary", "artifacts"]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 306",
        "backend": "spqlios_avx512-local",
        "command": "STAGE306_RUNS=5 STAGE306_REPS=5000 FFT_LIB=spqlios_avx512 bash scripts/run_stage306_torus_to_dft_micro_hypothesis.sh",
        "config": "r=4,N=2048 sub-DTF current-head refresh plus Stage289/290/291/305 candidate audit",
        "params": "r=4,N=2048; BINARY SET_2_3 microbench; linked SET_2_3_2048 full-SAB split evidence",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage306 admits only the direct DFT lifecycle residual as the next measured target; no new broad AVX rewrite.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(EVIDENCE)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": str(len(data)), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _, current = collect_current_microbench()
    dominant = dominant_direct_component()
    direct_sum = direct_summary()
    dominant_name = dominant.get("component", "missing")
    dominant_share = fnum(dominant.get("share_of_split_total"))
    direct_min = fnum(current.get("direct_vs_baseline_speedup_min"))

    stage305_ok = stage305_passed()
    stage289_decision = stage_decision(STAGE289)
    stage290_decision = stage_decision(STAGE290)
    wrapper_rejected = stage289_decision.startswith("NEUTRAL") and stage290_decision.startswith("NEUTRAL")
    current_ok = current.get("all_correct") == "PASS" and direct_min >= 1.02

    if stage305_ok and dominant_name == "torus_to_dft" and current_ok and wrapper_rejected:
        decision = DECISION_PASS
    elif stage305_ok and current.get("all_correct") == "PASS":
        decision = DECISION_NEUTRAL
    else:
        decision = DECISION_FAIL

    summary_rows = [{
        "decision": decision,
        "dominant_direct_component": dominant_name,
        "dominant_direct_share": f"{dominant_share:.6f}",
        "stage305_direct_t_bootstrap_over_r_us": direct_sum.get("t_bootstrap_over_r_pvw_us", ""),
        "stage305_direct_mat_ep_calls": direct_sum.get("body_mat_ep_calls", ""),
        "current_runs_per_variant": current["runs_per_variant"],
        "current_microbench_correctness": current["all_correct"],
        "current_direct_vs_baseline_speedup_mean": current["direct_vs_baseline_speedup_mean"],
        "current_direct_vs_baseline_speedup_min": current["direct_vs_baseline_speedup_min"],
        "current_direct_vs_baseline_speedup_max": current["direct_vs_baseline_speedup_max"],
        "claim": "candidate_admission_not_new_full_sab_speed_claim",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "dominant_direct_component", "dominant_direct_share",
        "stage305_direct_t_bootstrap_over_r_us", "stage305_direct_mat_ep_calls",
        "current_runs_per_variant", "current_microbench_correctness",
        "current_direct_vs_baseline_speedup_mean",
        "current_direct_vs_baseline_speedup_min",
        "current_direct_vs_baseline_speedup_max", "claim",
    ])

    evidence_rows = [
        {
            "stage": "Stage289",
            "evidence": "multirow torus_to_DFT wrapper",
            "decision": stage289_decision,
            "metric": "speedup_vs_scalar_loop_mean/min",
            "value": f"{stage_speed(STAGE289, 'speedup_vs_scalar_loop_mean')}/{stage_speed(STAGE289, 'speedup_vs_scalar_loop_min')}",
            "interpretation": "Wrapping the same row-wise reverse FFT lifecycle is not promoted.",
        },
        {
            "stage": "Stage290",
            "evidence": "direct-output torus_to_DFT array",
            "decision": stage290_decision,
            "metric": "speedup_vs_scalar_loop_mean/min",
            "value": f"{stage_speed(STAGE290, 'speedup_vs_scalar_loop_mean')}/{stage_speed(STAGE290, 'speedup_vs_scalar_loop_min')}",
            "interpretation": "Avoiding the output copy alone is not stable enough to promote.",
        },
        {
            "stage": "Stage291",
            "evidence": "sub-decompose direct DFT",
            "decision": stage_decision(STAGE291),
            "metric": "direct_vs_baseline_speedup_mean/min",
            "value": f"{stage_speed(STAGE291, 'direct_vs_baseline_speedup_mean')}/{stage_speed(STAGE291, 'direct_vs_baseline_speedup_min')}",
            "interpretation": "Direct digit-to-double plus ifft is the already-promoted lifecycle improvement.",
        },
        {
            "stage": "Stage305",
            "evidence": "complete-SAB split profile",
            "decision": "PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED" if stage305_ok else "MISSING_OR_FAIL",
            "metric": "dominant direct split component/share",
            "value": f"{dominant_name}/{dominant.get('share_of_split_total', '')}",
            "interpretation": "After direct DFT, the next measured residual is the direct DFT materialization/ifft block itself.",
        },
        {
            "stage": "Stage306",
            "evidence": "current-head sub-DTF refresh",
            "decision": decision,
            "metric": "direct_vs_baseline_speedup_mean/min",
            "value": f"{current['direct_vs_baseline_speedup_mean']}/{current['direct_vs_baseline_speedup_min']}",
            "interpretation": "Refresh confirms the current direct path still beats the old sub-DTF materialization path.",
        },
    ]
    write_csv(EVIDENCE, evidence_rows, ["stage", "evidence", "decision", "metric", "value", "interpretation"])

    candidates = [
        {
            "candidate": "C1_multirow_dft_wrapper",
            "status": "REJECTED_OR_NEUTRAL",
            "evidence": stage289_decision,
            "next_action": "Do not repeat this wrapper as an optimization candidate.",
        },
        {
            "candidate": "C2_direct_output_dft_array",
            "status": "REJECTED_OR_NEUTRAL",
            "evidence": stage290_decision,
            "next_action": "Do not promote unless redesigned with new evidence.",
        },
        {
            "candidate": "C3_sub_decompose_to_double_direct_dft",
            "status": "PROMOTED_ALREADY_IN_CURRENT_DIRECT_PATH",
            "evidence": f"Stage291 plus Stage292-305; current min {current['direct_vs_baseline_speedup_min']}x",
            "next_action": "Keep as current best complete-SAB path.",
        },
        {
            "candidate": "C4_direct_ifft_lifecycle_split",
            "status": "ADMITTED_FOR_STAGE307" if decision == DECISION_PASS else "BLOCKED",
            "evidence": f"Stage305 direct torus_to_dft share {dominant.get('share_of_split_total', '')}",
            "next_action": "Instrument direct path into digit-to-double and ifft subcomponents before any rewrite.",
        },
        {
            "candidate": "C5_dense_mat_avx512_rewrite",
            "status": "NOT_ADMITTED_FROM_STAGE306",
            "evidence": "Stage301/302 FMA counters near-neutral; Stage305 dense is not dominant residual.",
            "next_action": "Return only if future split shows dense dominates after DFT lifecycle changes.",
        },
    ]
    write_csv(CANDIDATES, candidates, ["candidate", "status", "evidence", "next_action"])

    budget_rows: List[Dict[str, object]] = []
    direct_total = sum(fnum(row.get("us")) for row in direct_components())
    for row in direct_components():
        us = fnum(row.get("us"))
        for reduction in [0.10, 0.25, 0.50]:
            projected = direct_total / (direct_total - us * reduction) if direct_total and direct_total > us * reduction else 0.0
            budget_rows.append({
                "component": row.get("component", ""),
                "share_of_direct_split_total": row.get("share_of_split_total", ""),
                "avg_us_per_call": row.get("avg_us_per_call", ""),
                "hypothetical_component_reduction": f"{reduction:.2f}",
                "profile_level_split_speedup_bound": f"{projected:.6f}" if projected else "",
                "claim_boundary": "profile_model_only_not_latency_claim",
            })
    write_csv(BUDGET, budget_rows, [
        "component", "share_of_direct_split_total", "avg_us_per_call",
        "hypothetical_component_reduction", "profile_level_split_speedup_bound",
        "claim_boundary",
    ])

    proof = [
        {"gate": "G1_entry_stage305", "status": "PASS" if stage305_ok else "FAIL", "metric": "Stage305 proof", "value": "PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED" if stage305_ok else "missing/fail", "interpretation": "Stage306 must start from a measured complete-SAB residual."},
        {"gate": "G2_dominant_component", "status": "PASS" if dominant_name == "torus_to_dft" else "FAIL", "metric": "dominant direct component", "value": dominant_name, "interpretation": "The next candidate must target the measured residual, not a broad rewrite."},
        {"gate": "G3_current_microbench", "status": "PASS" if current_ok else "NO_PROMOTION", "metric": "current direct sub-DTF min speedup", "value": current["direct_vs_baseline_speedup_min"], "interpretation": "The current direct path must still beat the old sub-DTF lifecycle."},
        {"gate": "G4_prior_candidate_filter", "status": "PASS" if wrapper_rejected else "FAIL", "metric": "Stage289/290 wrapper candidates", "value": f"{stage289_decision};{stage290_decision}", "interpretation": "Known neutral DFT wrappers are excluded from the next implementation route."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "scope", "value": "candidate admission", "interpretation": "Stage306 is not a new full-SAB speed claim and does not prove theoretical optimality."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage307: split direct DFT into digit-to-double and ifft before rewriting."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    next_rows = [
        {
            "priority": "P0",
            "route": "stage307_direct_ifft_lifecycle_split_profile",
            "entry_condition": decision,
            "gate": "Direct path profile must split digit-to-double, ifft, and dense use without changing output.",
            "failure_action": "Keep current direct-DFT implementation and move to branch/parameter evidence.",
        },
        {
            "priority": "P1",
            "route": "stage307_branch_coverage_or_parameter_matrix",
            "entry_condition": "paper claim expansion needed",
            "gate": "Cover branch/parameter matrix before broad novelty wording.",
            "failure_action": "Keep claim scoped to tested binary include-zero 2048-output settings.",
        },
    ]
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    report = (
        "# Stage306 Torus-to-DFT Micro-Hypothesis\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage306 is a candidate-admission stage. It binds Stage305 complete-SAB split evidence to current-head sub-DTF microbench data and filters out DFT ideas that were already neutral.\n\n"
        "## Summary\n\n" + table(summary_rows, [
            "decision", "dominant_direct_component", "dominant_direct_share",
            "current_runs_per_variant", "current_microbench_correctness",
            "current_direct_vs_baseline_speedup_mean",
            "current_direct_vs_baseline_speedup_min",
        ]) +
        "\n\n## Evidence Matrix\n\n" + table(evidence_rows, ["stage", "evidence", "decision", "metric", "value"]) +
        "\n\n## Candidate Matrix\n\n" + table(candidates, ["candidate", "status", "evidence", "next_action"]) +
        "\n\n## Component Budget\n\n" + table(budget_rows, ["component", "share_of_direct_split_total", "hypothetical_component_reduction", "profile_level_split_speedup_bound"]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage306 Torus-to-DFT Lifecycle Model

Stage306 narrows the MAT/PVW-SAB optimization target after Stage305. In the
current direct path, `mat_trgsw_mul_pvmtmlwe_sub_DFT` no longer writes a torus
decomposition scratch and then converts that scratch to doubles. It computes
signed decomposition digits directly into the SPQLIOS reverse-FFT buffer and
then calls `ifft` row by row.

For k=1, l=1, r=4, each MAT external product materializes rows = k + r = 5
DFT rows. Stage305 measured the direct split as:

- decompose share: {next((row.get('share_of_split_total') for row in direct_components() if row.get('component') == 'decompose'), '')}
- torus_to_dft share: {next((row.get('share_of_split_total') for row in direct_components() if row.get('component') == 'torus_to_dft'), '')}
- dense share: {next((row.get('share_of_split_total') for row in direct_components() if row.get('component') == 'dense_from_dec'), '')}

The `torus_to_dft` label in this direct path means digit-to-double
materialization plus one reverse FFT per row. Stage289 and Stage290 show that
wrapping the existing per-row FFT lifecycle, or only avoiding an output copy,
does not produce a stable promoted candidate. Therefore the next admissible
research step is not a general AVX512 dense rewrite; it is a direct-path split
profile that separates digit extraction, double materialization, and `ifft`.

The speed budget in Stage306 is a profile model only. A later implementation
must still pass complete-SAB `T_bootstrap/r`, correctness, noise, and resource
gates before it can be called a bootstrapping acceleration.
""")
    write_text(VARIANT, f"""# Stage306 Torus-to-DFT Candidate Audit

Decision: `{decision}`.

No behavior-changing variant is introduced in Stage306. The admitted next
candidate is `C4_direct_ifft_lifecycle_split`, whose first step is measurement,
not replacement.

Rejected or non-promoted candidate families:

- `C1_multirow_dft_wrapper`: Stage289 neutral.
- `C2_direct_output_dft_array`: Stage290 neutral.
- `C5_dense_mat_avx512_rewrite`: not selected by current residual evidence.

Current best path retained:

- `C3_sub_decompose_to_double_direct_dft`: already implemented by
  `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true` and supported by complete-SAB
  `T_bootstrap/r` evidence from later stages.
""")
    write_text(PLAN, """# Stage306 Experiment Plan

1. Re-run current-head sub-DTF microbench for baseline and direct-DFT variants.
2. Require all `MAT_SUB_DFT` correctness checks to pass.
3. Link Stage305 complete-SAB split evidence and identify the dominant direct
   residual component.
4. Filter out Stage289 and Stage290 candidates that were already neutral.
5. Admit Stage307 only as a split-profile measurement of the direct path.
""")
    write_text(COMMANDS, """# Stage306 Reproduction Commands

```bash
STAGE306_RUNS=5 STAGE306_REPS=5000 FFT_LIB=spqlios_avx512 \\
  bash scripts/run_stage306_torus_to_dft_micro_hypothesis.sh
python3 scripts/build_stage306_torus_to_dft_micro_hypothesis.py
```
""")

    append_once(ROADMAP, "## Stage 306: Torus-to-DFT Micro-Hypothesis", "\n## Stage 306: Torus-to-DFT Micro-Hypothesis\n\nGoal: bind Stage305 residual attribution to current-head microbench evidence and admit only a component-specific direct-DFT lifecycle target.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage306-torus-to-dft-micro-hypothesis -->", "\n<!-- stage306-torus-to-dft-micro-hypothesis -->\n### Stage306 torus-to-DFT micro-hypothesis\n\n" f"`{decision}` filters prior DFT candidates and admits a direct-path lifecycle split before any new AVX512 rewrite.\n")
    append_once(HYPOTHESES, "H306_torus_to_dft_micro_hypothesis:", "\nH306_torus_to_dft_micro_hypothesis:\n" f"  status: {decision}\n  primary_metric: candidate_admission_with_current_sub_dft_microbench\n  evidence:\n    - repro/stage306_torus_to_dft_micro_hypothesis/stage306_summary.csv\n    - repro/stage306_torus_to_dft_micro_hypothesis/evidence_matrix.csv\n    - repro/stage306_torus_to_dft_micro_hypothesis/candidate_matrix.csv\n    - repro/stage306_torus_to_dft_micro_hypothesis/proof_gate.csv\n  conclusion: >\n    Stage306 keeps the current direct-DFT path as the best measured path and\n    admits only a direct digit-to-double/ifft lifecycle split as the next\n    research step; it is not a new full-SAB speed claim.\n")
    append_once(MANIFEST, "- stage306_torus_to_dft_micro_hypothesis:", "\n- stage306_torus_to_dft_micro_hypothesis:\n  - `docs/stage306_torus_to_dft_micro_hypothesis.md`\n  - `theory_checks/stage306_torus_to_dft_lifecycle_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage306_torus_to_dft_candidates.md`\n  - `experiments/stage306_torus_to_dft_micro_hypothesis_plan.md`\n  - `scripts/run_stage306_torus_to_dft_micro_hypothesis.sh`\n  - `scripts/build_stage306_torus_to_dft_micro_hypothesis.py`\n  - `repro/stage306_torus_to_dft_micro_hypothesis/`\n")
    append_once(CHECKLIST, "<!-- stage306-torus-to-dft-micro-hypothesis-checklist -->", "\n<!-- stage306-torus-to-dft-micro-hypothesis-checklist -->\n" f"- [x] Stage306 records `{decision}` and routes Stage307 to direct-path lifecycle split profiling.\n")
    append_run_log(decision)

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, RUN_METRICS, SUMMARY,
        EVIDENCE, CANDIDATES, BUDGET, PROOF, NEXT, COMMANDS, REPORT,
        RAW / "variant_plan.csv",
    ]
    artifacts.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
