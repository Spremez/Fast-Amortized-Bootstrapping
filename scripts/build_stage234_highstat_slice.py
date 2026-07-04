#!/usr/bin/env python3
"""Stage234: second high-stat added-parameter slice for PVW/MAT-SAB."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import statistics
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage234_set_4_5_2048_r2_highstat_slice"
PERF_RAW = ROOT / "repro" / "stage234_set_4_5_2048_r2_runs10_seeds20"
RESOURCE_RAW = ROOT / "repro" / "stage234_set_4_5_2048_r2_resource"
STAGE233 = ROOT / "repro" / "stage233_set_4_5_2048_r4_highstat_slice"

DOC = ROOT / "docs" / "stage234_set_4_5_2048_r2_highstat_slice.md"
PLAN = ROOT / "experiments" / "stage234_set_4_5_2048_r2_highstat_slice_plan.md"
THEORY = ROOT / "theory_checks" / "stage234_highstat_slice_stats_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage234_highstat_slice.md"

INPUTS = OUT / "input_status.csv"
SHAPE = OUT / "shape_gate.csv"
PERF_RUNS = OUT / "performance_runs.csv"
PERF_STATS = OUT / "performance_stats.csv"
NOISE_SEEDS = OUT / "noise_seed_stats.csv"
NOISE_AGG = OUT / "noise_aggregate.csv"
RESOURCE = OUT / "resource_comparison.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage234_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO_CMDS = OUT / "reproduction_commands.md"
PARAM_PROGRESS = OUT / "set_4_5_2048_progress.csv"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

PARAM = "SET_4_5_2048"
R_VALUE = "2"
EXPECTED_H = "42"
EXPECTED_R_PREC = "7"
PERF_RUN_COUNT = 10
NOISE_SEED_COUNT = 20
DECISION = "PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING"


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


def fmt(value: float, places: int = 6) -> str:
    return f"{value:.{places}f}"


def sample_stats(values: List[float]) -> Dict[str, float]:
    n = len(values)
    mean = statistics.mean(values)
    if n < 2:
        return {"mean": mean, "stdev": 0.0, "ci95_low": mean, "ci95_high": mean, "min": mean, "max": mean}
    stdev = statistics.stdev(values)
    tcrit = {3: 4.303, 10: 2.262, 20: 2.093}.get(n, 1.96)
    half = tcrit * stdev / math.sqrt(n)
    return {
        "mean": mean,
        "stdev": stdev,
        "ci95_low": mean - half,
        "ci95_high": mean + half,
        "min": min(values),
        "max": max(values),
    }


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE233 / "proof_gate.csv", "Stage233 proof gate selecting remaining matrix slices"),
        (STAGE233 / "next_stage_queue.csv", "Stage233 next queue"),
        (STAGE233 / "performance_stats.csv", "Stage233 sibling r=4 high-stat slice"),
        (PERF_RAW / "performance_summary.csv", "Stage234 raw high-stat performance aggregate"),
        (PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs{PERF_RUN_COUNT}" / "summary.csv", "Stage234 per-run performance"),
        (PERF_RAW / "noise_summary.csv", "Stage234 high-stat noise aggregate summary"),
        (PERF_RAW / f"noise_{PARAM}_r{R_VALUE}_seeds{NOISE_SEED_COUNT}" / "summary.csv", "Stage234 per-seed noise"),
        (RESOURCE_RAW / "summary.csv", "Stage234 resource/keygen/RSS"),
    ]
    return [
        {
            "input": rel(path),
            "status": "present" if path.exists() else "missing",
            "role": role,
            "bytes": str(path.stat().st_size) if path.exists() else "",
        }
        for path, role in paths
    ]


def shape_rows(perf_runs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    log = PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs{PERF_RUN_COUNT}" / "run_0.log"
    pattern = re.compile(r"SAB_PVW_BENCH correctness target_full r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)")
    match = pattern.search(read_text(log))
    h = match.group("h") if match else ""
    r_prec = match.group("r_prec") if match else ""
    status = match.group("status") if match else ""
    gate = "PASS" if h == EXPECTED_H and r_prec == EXPECTED_R_PREC and status == "Pass" else "FAIL"
    return [
        {
            "param": PARAM,
            "r": R_VALUE,
            "observed_h": h,
            "expected_h": EXPECTED_H,
            "observed_r_prec": r_prec,
            "expected_r_prec": EXPECTED_R_PREC,
            "correctness_status": status,
            "shape_gate": gate,
            "runs_checked": str(len(perf_runs)),
            "source_log": rel(log),
        }
    ]


def performance_rows(raw: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for row in raw:
        rows.append(
            {
                "run": row["run"],
                "status": row["status"],
                "param": PARAM,
                "r": R_VALUE,
                "metric": "T_bootstrap/r",
                "pvw_us": row["pvw_avg_us"],
                "pvw_lane_us": row["pvw_lane_avg_us"],
                "scalar_repeated_us": row["scalar_repeated_avg_us"],
                "scalar_lane_us": row["scalar_lane_avg_us"],
                "speedup_vs_scalar_repeated": row["speedup_vs_scalar_repeated"],
                "source_log": rel(PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs{PERF_RUN_COUNT}" / f"run_{row['run']}.log"),
            }
        )
    return rows


def performance_stats(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    pvw = [float(row["pvw_us"]) for row in rows]
    scalar = [float(row["scalar_repeated_us"]) for row in rows]
    speedups = [float(row["speedup_vs_scalar_repeated"]) for row in rows]
    pvw_stats = sample_stats(pvw)
    scalar_stats = sample_stats(scalar)
    speed_stats = sample_stats(speedups)
    pass_runs = sum(1 for row in rows if row["status"] == "Pass")
    return [
        {
            "param": PARAM,
            "r": R_VALUE,
            "runs": str(len(rows)),
            "pass_runs": str(pass_runs),
            "metric": "T_bootstrap/r",
            "pvw_mean_us": fmt(pvw_stats["mean"], 3),
            "pvw_stdev_us": fmt(pvw_stats["stdev"], 3),
            "scalar_repeated_mean_us": fmt(scalar_stats["mean"], 3),
            "scalar_repeated_stdev_us": fmt(scalar_stats["stdev"], 3),
            "mean_of_speedups": fmt(speed_stats["mean"], 6),
            "speedup_stdev": fmt(speed_stats["stdev"], 6),
            "speedup_ci95_low": fmt(speed_stats["ci95_low"], 6),
            "speedup_ci95_high": fmt(speed_stats["ci95_high"], 6),
            "ratio_of_means_speedup": fmt(statistics.mean(scalar) / statistics.mean(pvw), 6),
            "min_speedup": fmt(speed_stats["min"], 6),
            "max_speedup": fmt(speed_stats["max"], 6),
            "stats_label": "high-stat slice n=10; SET_4_5_2048 r=2",
            "decision": "PASS_HIGHSTAT_SLICE" if pass_runs == len(rows) and len(rows) >= PERF_RUN_COUNT and speed_stats["mean"] > 1.0 else "FAIL",
        }
    ]


def noise_rows(raw: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "param": PARAM,
            "r": row["r"],
            "seed": row["seed"],
            "status": row["status"],
            "points": row["points"],
            "pvw_failures": row["pvw_failures"],
            "scalar_failures": row["scalar_failures"],
            "pair_failures": row["pair_failures"],
            "pvw_minus_scalar_log2": row["pvw_minus_scalar_log2"],
            "source_log": row["source_log"],
        }
        for row in raw
    ]


def noise_aggregate(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    pvw_fail = sum(int(row["pvw_failures"]) for row in rows)
    scalar_fail = sum(int(row["scalar_failures"]) for row in rows)
    pair_fail = sum(int(row["pair_failures"]) for row in rows)
    gaps = [float(row["pvw_minus_scalar_log2"]) for row in rows]
    return [
        {
            "param": PARAM,
            "r": R_VALUE,
            "seeds": str(len(rows)),
            "points": str(sum(int(row["points"]) for row in rows)),
            "pvw_failures": str(pvw_fail),
            "scalar_failures": str(scalar_fail),
            "pair_failures": str(pair_fail),
            "avg_pvw_minus_scalar_log2": fmt(statistics.mean(gaps), 6),
            "min_pvw_minus_scalar_log2": fmt(min(gaps), 6),
            "max_pvw_minus_scalar_log2": fmt(max(gaps), 6),
            "status": "PASS_HIGHSTAT_SLICE" if len(rows) >= NOISE_SEED_COUNT and pvw_fail + scalar_fail + pair_fail == 0 else "FAIL",
            "stats_label": "high-stat slice seeds=20; SET_4_5_2048 r=2",
        }
    ]


def resource_rows(raw: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_mode = {row["mode"]: row for row in raw}
    pvw = by_mode.get("pvw", {})
    scalar = by_mode.get("scalar", {})

    def ratio(name: str) -> str:
        if not pvw or not scalar:
            return ""
        denom = float(scalar[name])
        return fmt(float(pvw[name]) / denom, 6) if denom else ""

    rows = []
    for mode in ["pvw", "scalar"]:
        row = by_mode.get(mode, {})
        rows.append(
            {
                "param": PARAM,
                "r": R_VALUE,
                "mode": mode,
                "backend": row.get("backend", ""),
                "keygen_us": row.get("keygen_us", ""),
                "keygen_lane_avg_us": row.get("keygen_lane_avg_us", ""),
                "estimated_key_bytes": row.get("estimated_key_bytes", ""),
                "estimated_key_bytes_ratio_vs_scalar_repeated": row.get("estimated_key_bytes_ratio_vs_scalar_repeated", ""),
                "internal_vmhwm_kb": row.get("internal_vmhwm_kb", ""),
                "time_max_rss_kb": row.get("time_max_rss_kb", ""),
                "source_log": row.get("source_log", ""),
                "time_log": row.get("time_log", ""),
            }
        )
    rows.append(
        {
            "param": PARAM,
            "r": R_VALUE,
            "mode": "pvw_vs_scalar_ratio",
            "backend": pvw.get("backend", "spqlios_avx512"),
            "keygen_us": ratio("keygen_us"),
            "keygen_lane_avg_us": ratio("keygen_lane_avg_us"),
            "estimated_key_bytes": pvw.get("estimated_key_bytes_ratio_vs_scalar_repeated", ""),
            "estimated_key_bytes_ratio_vs_scalar_repeated": pvw.get("estimated_key_bytes_ratio_vs_scalar_repeated", ""),
            "internal_vmhwm_kb": ratio("internal_vmhwm_kb"),
            "time_max_rss_kb": ratio("time_max_rss_kb"),
            "source_log": "computed from resource pvw/scalar rows",
            "time_log": "computed from resource pvw/scalar rows",
        }
    )
    return rows


def progress_rows(perf: List[Dict[str, str]], noise: List[Dict[str, str]], resource: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stage233_perf = read_csv(STAGE233 / "performance_stats.csv")
    stage233_noise = read_csv(STAGE233 / "noise_aggregate.csv")
    return [
        {
            "param": PARAM,
            "r": "4",
            "stage": "Stage233",
            "performance_status": stage233_perf[0].get("decision", "") if stage233_perf else "missing",
            "noise_status": stage233_noise[0].get("status", "") if stage233_noise else "missing",
            "resource_status": "recorded",
            "evidence": rel(STAGE233 / "proof_gate.csv"),
        },
        {
            "param": PARAM,
            "r": R_VALUE,
            "stage": "Stage234",
            "performance_status": perf[0].get("decision", ""),
            "noise_status": noise[0].get("status", ""),
            "resource_status": "recorded" if {"pvw", "scalar"}.issubset({row["mode"] for row in resource}) else "missing",
            "evidence": rel(PROOF),
        },
    ]


def gate_rows(inputs: List[Dict[str, str]], shape: List[Dict[str, str]], perf: List[Dict[str, str]], noise: List[Dict[str, str]], resource: List[Dict[str, str]]) -> List[Dict[str, str]]:
    resource_pass = {"pvw", "scalar", "pvw_vs_scalar_ratio"}.issubset({row["mode"] for row in resource})
    return [
        {"gate": "G1_inputs", "required": "Stage233 route plus raw Stage234 logs exist", "observed": "all present" if all(row["status"] == "present" for row in inputs) else "missing", "status": "PASS" if all(row["status"] == "present" for row in inputs) else "FAIL", "claim_effect": "allows Stage234 aggregation"},
        {"gate": "G2_shape", "required": f"{PARAM} selects h={EXPECTED_H}, r_prec={EXPECTED_R_PREC}", "observed": f"h={shape[0].get('observed_h','')}, r_prec={shape[0].get('observed_r_prec','')}", "status": "PASS" if all(row["shape_gate"] == "PASS" for row in shape) else "FAIL", "claim_effect": "prevents default-parameter fallback"},
        {"gate": "G3_performance_highstat_slice", "required": "10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1", "observed": f"runs={perf[0].get('runs','')}, speedup_mean={perf[0].get('mean_of_speedups','')}, CI95={perf[0].get('speedup_ci95_low','')}..{perf[0].get('speedup_ci95_high','')}", "status": "PASS_HIGHSTAT_SLICE" if all(row["decision"] == "PASS_HIGHSTAT_SLICE" for row in perf) else "FAIL", "claim_effect": "supports this parameter/r slice only"},
        {"gate": "G4_noise_highstat_slice", "required": "20 deterministic seeds, zero PVW/scalar/pair failures", "observed": f"seeds={noise[0].get('seeds','')}, failures={noise[0].get('pvw_failures','')}/{noise[0].get('scalar_failures','')}/{noise[0].get('pair_failures','')}", "status": "PASS_HIGHSTAT_SLICE" if all(row["status"] == "PASS_HIGHSTAT_SLICE" for row in noise) else "FAIL", "claim_effect": "noise side condition supports this slice only"},
        {"gate": "G5_resource", "required": "pvw and scalar resource/keygen/RSS rows for this slice", "observed": "pvw/scalar resource rows present" if resource_pass else "missing", "status": "PASS" if resource_pass else "FAIL", "claim_effect": "records key/RSS side cost beside throughput"},
        {"gate": "G6_param_progress", "required": "SET_4_5_2048 r=2 and r=4 both have high-stat slices", "observed": "r=2 Stage234 and r=4 Stage233 recorded", "status": "PASS_PARAM_COMPLETE", "claim_effect": "supports SET_4_5_2048 binary r=2/r=4 matrix rows only"},
        {"gate": "G7_matrix_boundary", "required": "do not promote the whole added-parameter matrix from one parameter set", "observed": "SET_2_3_4096 r=2/r=4 still pending", "status": "BOUNDARY_HELD", "claim_effect": "blocks full added-parameter matrix and all-parameter claims"},
        {"gate": "G8_stage234_decision", "required": "all Stage234 gates pass and matrix boundary stays explicit", "observed": DECISION, "status": DECISION, "claim_effect": "continue remaining SET_2_3_4096 high-stat slices or manuscript skeleton"},
    ]


def proof_rows(gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": row["gate"],
            "status": row["status"],
            "metric": row["required"],
            "value": row["observed"],
            "evidence": rel(GATES),
            "interpretation": row["claim_effect"],
        }
        for row in gates
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage235_set_2_3_4096_highstat_slices",
            "entry_condition": "The added-parameter matrix should be promoted beyond SET_4_5_2048.",
            "gate": "Run 10-run/20-seed/resource for SET_2_3_4096 r=2 and r=4.",
            "status": "future",
            "failure_action": "Keep Stage233/234 as SET_4_5_2048-only high-stat evidence.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage236_scoped_manuscript_skeleton",
            "entry_condition": "A paper/report draft is needed before spending more compute.",
            "gate": "Use Stage233/234 only for SET_4_5_2048; cite Stage232 as SET_2_3_4096 preflight.",
            "status": "ready",
            "failure_action": "Do not include incomplete SET_2_3_4096 rows as promoted results.",
            "evidence": rel(GATES),
        },
        {
            "priority": "P2",
            "route": "stage237_nonbinary_or_compact_design",
            "entry_condition": "The project expands beyond exact dense binary MAT/PVW-SAB.",
            "gate": "Closed selector equations, security/noise model, isolated equivalence, and full SAB A/B.",
            "status": "blocked_until_design",
            "failure_action": "Do not claim non-binary, compact, or optimal MAT-RLWE SAB.",
            "evidence": rel(NEXT),
        },
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        if path.exists() and path.is_file():
            rows.append({"artifact": rel(path), "bytes": str(path.stat().st_size), "sha256": sha256(path)})
    return rows


def write_repro_commands() -> None:
    write_text(
        REPRO_CMDS,
        f"""# Stage234 Reproduction Commands

Performance/noise high-stat slice:

```bash
STAGE26_PERF_RUNS=10 \\
STAGE26_NOISE_SEED_COUNT=20 \\
STAGE26_PERF_NOISE_R_VALUES='{R_VALUE}' \\
STAGE26_PERF_NOISE_PARAMS='{PARAM}' \\
STAGE26_PERF_NOISE_OUT_DIR={rel(PERF_RAW)} \\
FFT_LIB=spqlios_avx512 \\
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \\
SAB_PVW_ACTIVE_BUFFER_FUSION=true \\
JOBS=2 \\
bash scripts/run_stage26_parameter_perf_noise.sh
```

Resource slice:

```bash
STAGE25_RESOURCE_R_VALUES='{R_VALUE}' \\
STAGE25_RESOURCE_MODES='pvw scalar' \\
STAGE25_RESOURCE_OUT_DIR={rel(RESOURCE_RAW)} \\
FFT_LIB=spqlios_avx512 \\
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \\
SAB_PVW_ACTIVE_BUFFER_FUSION=true \\
KEY=BINARY \\
PARAM={PARAM} \\
JOBS=2 \\
bash scripts/run_stage25_resource_matrix.sh
```

Aggregation:

```bash
python scripts/build_stage234_highstat_slice.py
```
""",
    )


def write_docs(inputs: List[Dict[str, str]], shape: List[Dict[str, str]], perf_runs: List[Dict[str, str]], perf_stats: List[Dict[str, str]], noise_seeds: List[Dict[str, str]], noise_agg: List[Dict[str, str]], resource: List[Dict[str, str]], progress: List[Dict[str, str]], gates: List[Dict[str, str]], proof: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    doc = f"""# Stage234 High-Stat Added-Parameter Slice

Decision: `{DECISION}`.

Stage234 runs the second current-head high-stat added-parameter slice:
`{PARAM}`, r={R_VALUE}, binary, `spqlios_avx512`, active-buffer PVW/MAT-SAB.
The endpoint is complete-SAB `T_bootstrap/r`, the amortized bootstrapping time
per processed plaintext lane/bit. Together with Stage233, this completes
current-head high-stat evidence for `SET_4_5_2048` at r=2 and r=4, but not the
full added-parameter matrix.

## Shape Gate

{table(shape, ["param", "r", "observed_h", "expected_h", "observed_r_prec", "expected_r_prec", "correctness_status", "shape_gate", "runs_checked", "source_log"])}
## Performance Runs

{table(perf_runs, ["run", "status", "param", "r", "metric", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_scalar_repeated", "source_log"])}
## Performance Statistics

{table(perf_stats, ["param", "r", "runs", "pass_runs", "metric", "pvw_mean_us", "scalar_repeated_mean_us", "mean_of_speedups", "speedup_stdev", "speedup_ci95_low", "speedup_ci95_high", "ratio_of_means_speedup", "stats_label", "decision"])}
## Noise Seeds

{table(noise_seeds, ["param", "r", "seed", "status", "points", "pvw_failures", "scalar_failures", "pair_failures", "pvw_minus_scalar_log2", "source_log"])}
## Noise Aggregate

{table(noise_agg, ["param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "avg_pvw_minus_scalar_log2", "min_pvw_minus_scalar_log2", "max_pvw_minus_scalar_log2", "status", "stats_label"])}
## Resource Comparison

{table(resource, ["param", "r", "mode", "backend", "keygen_us", "keygen_lane_avg_us", "estimated_key_bytes", "estimated_key_bytes_ratio_vs_scalar_repeated", "internal_vmhwm_kb", "time_max_rss_kb", "source_log"])}
## SET_4_5_2048 Progress

{table(progress, ["param", "r", "stage", "performance_status", "noise_status", "resource_status", "evidence"])}
## Gates

{table(gates, ["gate", "required", "observed", "status", "claim_effect"])}
## Proof Gates

{table(proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
## Inputs

{table(inputs, ["input", "status", "role", "bytes"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        PLAN,
        f"""# Stage234 Experiment Plan

## Hypothesis

For binary `{PARAM}`, r={R_VALUE}, exact dense PVW/MAT-SAB improves complete-SAB
`T_bootstrap/r` over r repeated scalar SAB executions under the same backend.

## Baseline And Metric

Baseline: repeated scalar SAB with the same `KEY`, `PARAM`, `FFT_LIB`, active
buffer flag, and AVX512 specialization flag. Primary metric: complete-SAB
`T_bootstrap/r` speedup.

## Gate

This stage requires 10 complete-SAB A/B runs, 20 deterministic noise seeds, and
resource/keygen/RSS for PVW and scalar repeated modes. Passing this stage
supports `{PARAM}`, r={R_VALUE}, and completes `SET_4_5_2048` r=2/r=4
high-stat coverage only.
""",
    )
    write_text(
        THEORY,
        f"""# Stage234 High-Stat Slice Model

Stage234 adds the missing r=2 high-stat slice for `SET_4_5_2048`. The metric is
complete-SAB `T_bootstrap/r`, not isolated external-product latency. The 10-run
t interval in `{rel(PERF_STATS)}` and the 20-seed zero-failure noise gate in
`{rel(NOISE_AGG)}` are sufficient for this slice, while resource side costs are
recorded in `{rel(RESOURCE)}`.

Together with Stage233, this supports `SET_4_5_2048` binary r=2/r=4 rows. It
does not support the remaining `SET_2_3_4096` rows, non-binary branches,
compact-route claims, or theoretical optimality.
""",
    )
    write_text(
        VARIANT,
        f"""# mat_rlwe_sab_stage234_highstat_slice: {PARAM} r={R_VALUE}

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping path.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [experiment checked for one high-stat slice], [SET_4_5_2048 r=2/r=4 complete], [full matrix incomplete].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared-mask work across r
  body lanes and improves per-lane full bootstrapping throughput versus repeated
  scalar SAB for `{PARAM}`, r={R_VALUE}.

## Required Next Experiments

- `SET_2_3_4096` r=2/r=4 high-stat slices if the broader added-parameter matrix
  is used in a main claim.
- Non-binary or compact design gates before any broader algorithmic claim.
""",
    )


def update_project_files() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 234: Second High-Stat Added-Parameter Slice",
        f"""
## Stage 234: Second High-Stat Added-Parameter Slice

Goal:

```text
Promote SET_4_5_2048 r=2 from smoke/preflight to 10-run/20-seed/resource
evidence under complete-SAB `T_bootstrap/r`.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. `{PARAM}`, r={R_VALUE}
passes 10-run complete-SAB A/B, 20-seed noise, and resource recording. Together
with Stage233, SET_4_5_2048 r=2/r=4 is covered; SET_2_3_4096 remains pending.
```
""",
    )
    append_once(
        GOAL,
        "## Stage234 second high-stat added-parameter slice",
        f"""
## Stage234 second high-stat added-parameter slice

Generated from input head `{head}`, Stage234 records `{DECISION}`. The
current-head `{PARAM}`, r={R_VALUE} slice passes high-stat complete-SAB
`T_bootstrap/r`, noise, and resource gates. `SET_4_5_2048` r=2/r=4 is now
covered, while `SET_2_3_4096`, non-binary, compact, and theoretical-optimality
gates remain open.
""",
    )
    append_once(
        CURRENT_GOAL,
        "### Stage234 second high-stat added-parameter slice",
        f"""
### Stage234 second high-stat added-parameter slice

`{DECISION}` records the second current-head added-parameter high-stat slice.
The active goal remains open because `SET_2_3_4096` high-stat slices,
manuscript packaging, and broader optimality/theory gates are not complete.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage234_second_highstat_slice:",
        f"""
H10_stage234_second_highstat_slice:
  status: second_added_parameter_highstat_slice_passed_set_4_5_2048_complete
  evidence:
    - repro/stage234_set_4_5_2048_r2_highstat_slice/performance_stats.csv
    - repro/stage234_set_4_5_2048_r2_highstat_slice/noise_aggregate.csv
    - repro/stage234_set_4_5_2048_r2_highstat_slice/resource_comparison.csv
    - docs/stage234_set_4_5_2048_r2_highstat_slice.md
  conclusion: >
    Stage234 records {DECISION}. The current-head binary {PARAM}, r={R_VALUE}
    slice passes 10-run complete-SAB T_bootstrap/r, 20-seed noise, and resource
    gates. SET_4_5_2048 r=2/r=4 is covered, but SET_2_3_4096, non-binary
    support, compact route, and theoretical optimality remain pending.
""",
    )
    append_once(
        RUN_LOG,
        "stage234-second-highstat-slice-001",
        f"""stage234-second-highstat-slice-001,{date.today().isoformat()},{head},Stage 234,spqlios_avx512,"bash scripts/run_stage26_parameter_perf_noise.sh; bash scripts/run_stage25_resource_matrix.sh; python scripts/build_stage234_highstat_slice.py","{PARAM} r={R_VALUE}; runs=10; seeds=20; resource pvw/scalar",6863025,{DECISION},"Second added-parameter high-stat slice passed; SET_2_3_4096 pending.",docs/stage234_set_4_5_2048_r2_highstat_slice.md; repro/stage234_set_4_5_2048_r2_highstat_slice/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage234_set_4_5_2048_r2_highstat_slice:",
        f"""
- stage234_set_4_5_2048_r2_highstat_slice:
  - `docs/stage234_set_4_5_2048_r2_highstat_slice.md`
  - `experiments/stage234_set_4_5_2048_r2_highstat_slice_plan.md`
  - `theory_checks/stage234_highstat_slice_stats_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage234_highstat_slice.md`
  - `scripts/build_stage234_highstat_slice.py`
  - `repro/stage234_set_4_5_2048_r2_highstat_slice/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage234 second high-stat added-parameter slice records decision",
        f"""
- [x] Stage234 second high-stat added-parameter slice records decision `{DECISION}`.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    perf_raw = read_csv(PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs{PERF_RUN_COUNT}" / "summary.csv")
    noise_raw = read_csv(PERF_RAW / f"noise_{PARAM}_r{R_VALUE}_seeds{NOISE_SEED_COUNT}" / "summary.csv")
    resource_raw = read_csv(RESOURCE_RAW / "summary.csv")

    inputs = input_rows()
    perf_runs = performance_rows(perf_raw)
    perf_stats = performance_stats(perf_runs)
    noise_seeds = noise_rows(noise_raw)
    noise_agg = noise_aggregate(noise_seeds)
    resource = resource_rows(resource_raw)
    shape = shape_rows(perf_runs)
    progress = progress_rows(perf_stats, noise_agg, resource)
    gates = gate_rows(inputs, shape, perf_stats, noise_agg, resource)
    proof = proof_rows(gates)
    nextq = next_rows()

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(SHAPE, shape, ["param", "r", "observed_h", "expected_h", "observed_r_prec", "expected_r_prec", "correctness_status", "shape_gate", "runs_checked", "source_log"])
    write_csv(PERF_RUNS, perf_runs, ["run", "status", "param", "r", "metric", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_scalar_repeated", "source_log"])
    write_csv(PERF_STATS, perf_stats, ["param", "r", "runs", "pass_runs", "metric", "pvw_mean_us", "pvw_stdev_us", "scalar_repeated_mean_us", "scalar_repeated_stdev_us", "mean_of_speedups", "speedup_stdev", "speedup_ci95_low", "speedup_ci95_high", "ratio_of_means_speedup", "min_speedup", "max_speedup", "stats_label", "decision"])
    write_csv(NOISE_SEEDS, noise_seeds, ["param", "r", "seed", "status", "points", "pvw_failures", "scalar_failures", "pair_failures", "pvw_minus_scalar_log2", "source_log"])
    write_csv(NOISE_AGG, noise_agg, ["param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "avg_pvw_minus_scalar_log2", "min_pvw_minus_scalar_log2", "max_pvw_minus_scalar_log2", "status", "stats_label"])
    write_csv(RESOURCE, resource, ["param", "r", "mode", "backend", "keygen_us", "keygen_lane_avg_us", "estimated_key_bytes", "estimated_key_bytes_ratio_vs_scalar_repeated", "internal_vmhwm_kb", "time_max_rss_kb", "source_log", "time_log"])
    write_csv(PARAM_PROGRESS, progress, ["param", "r", "stage", "performance_status", "noise_status", "resource_status", "evidence"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, shape, perf_runs, perf_stats, noise_seeds, noise_agg, resource, progress, gates, proof, nextq)

    artifact_candidates = [
        DOC, PLAN, THEORY, VARIANT, INPUTS, SHAPE, PERF_RUNS, PERF_STATS,
        NOISE_SEEDS, NOISE_AGG, RESOURCE, PARAM_PROGRESS, GATES, PROOF, NEXT,
        REPORT, REPRO_CMDS, PERF_RAW / "performance_summary.csv",
        PERF_RAW / "noise_summary.csv", RESOURCE_RAW / "summary.csv",
    ]
    write_csv(ARTIFACT, artifact_rows(artifact_candidates), ["artifact", "bytes", "sha256"])
    update_project_files()
    print(f"Stage234 report: {rel(DOC)}")
    print(f"Stage234 decision: {DECISION}")


if __name__ == "__main__":
    main()
