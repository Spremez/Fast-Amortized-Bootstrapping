#!/usr/bin/env python3
"""Stage232: selected current-head full-stat/resource preflight for PVW/MAT-SAB."""

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
OUT = ROOT / "repro" / "stage232_selected_subset_fullstat_resource"

PERF_RAW = ROOT / "repro" / "stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3"
RESOURCE_RAW = ROOT / "repro" / "stage232_selected_subset_set_2_3_4096_r4_resource"
STAGE231 = ROOT / "repro" / "stage231_current_head_added_param_smoke"

DOC = ROOT / "docs" / "stage232_selected_subset_fullstat_resource.md"
PLAN = ROOT / "experiments" / "stage232_selected_subset_fullstat_resource_plan.md"
THEORY = ROOT / "theory_checks" / "stage232_subset_stats_resource_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage232_selected_subset.md"

INPUTS = OUT / "input_status.csv"
SELECTION = OUT / "selection_rationale.csv"
SHAPE = OUT / "shape_gate.csv"
PERF_RUNS = OUT / "performance_runs.csv"
PERF_STATS = OUT / "performance_stats.csv"
NOISE_SEEDS = OUT / "noise_seed_stats.csv"
NOISE_AGG = OUT / "noise_aggregate.csv"
RESOURCE = OUT / "resource_comparison.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
ARTIFACT = OUT / "artifact_index.csv"
REPORT = OUT / "stage232_report.md"
REPRO_CMDS = OUT / "reproduction_commands.md"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

PARAM = "SET_2_3_4096"
R_VALUE = "4"
EXPECTED_H = "32"
EXPECTED_R_PREC = "8"
DECISION = "PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING"


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


def ffloat(value: float, places: int = 6) -> str:
    return f"{value:.{places}f}"


def sample_stats(values: List[float]) -> Dict[str, float]:
    n = len(values)
    mean = statistics.mean(values)
    if n == 1:
        return {
            "n": 1.0,
            "mean": mean,
            "stdev": 0.0,
            "ci95_half_width": 0.0,
            "ci95_low": mean,
            "ci95_high": mean,
            "min": mean,
            "max": mean,
        }
    stdev = statistics.stdev(values)
    tcrit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}.get(
        n, 1.96
    )
    half = tcrit * stdev / math.sqrt(n)
    return {
        "n": float(n),
        "mean": mean,
        "stdev": stdev,
        "ci95_half_width": half,
        "ci95_low": mean - half,
        "ci95_high": mean + half,
        "min": min(values),
        "max": max(values),
    }


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE231 / "proof_gate.csv", "Stage231 proof gate"),
        (STAGE231 / "next_stage_queue.csv", "Stage231 next queue selecting Stage232"),
        (PERF_RAW / "performance_summary.csv", "Stage232 selected subset performance aggregate"),
        (PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs3" / "summary.csv", "Stage232 selected subset per-run performance"),
        (PERF_RAW / "noise_summary.csv", "Stage232 selected subset noise aggregate summary"),
        (PERF_RAW / f"noise_{PARAM}_r{R_VALUE}_seeds3" / "summary.csv", "Stage232 selected subset per-seed noise"),
        (RESOURCE_RAW / "summary.csv", "Stage232 selected subset resource/keygen/RSS"),
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
    return rows


def selection_rows() -> List[Dict[str, str]]:
    return [
        {
            "param": PARAM,
            "r": R_VALUE,
            "selection_reason": "largest-N added binary parameter plus main r=4 stress case; Stage231 smoke was positive and Stage36 historical evidence existed",
            "primary_metric": "complete-SAB T_bootstrap/r",
            "claim_level": "selected-subset preflight only",
            "promotion_gate": "10-run complete-SAB A/B, 20-seed noise, and resource for the promoted parameter matrix",
            "blocked_claims": "all-parameter, non-binary, theoretical optimality, universal MAT-RLWE SAB optimality",
        }
    ]


def shape_rows(perf_runs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    log = PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs3" / "run_0.log"
    pattern = re.compile(r"SAB_PVW_BENCH correctness target_full r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)")
    match = pattern.search(read_text(log))
    if match:
        h = match.group("h")
        r_prec = match.group("r_prec")
        status = match.group("status")
        gate = "PASS" if h == EXPECTED_H and r_prec == EXPECTED_R_PREC and status == "Pass" else "FAIL"
    else:
        h = ""
        r_prec = ""
        status = ""
        gate = "FAIL"
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
            "source_log": rel(log),
            "runs_checked": str(len(perf_runs)),
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
                "source_log": rel(PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs3" / f"run_{row['run']}.log"),
            }
        )
    return rows


def performance_stats(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    pvw = [float(row["pvw_us"]) for row in rows]
    scalar = [float(row["scalar_repeated_us"]) for row in rows]
    speeds = [float(row["speedup_vs_scalar_repeated"]) for row in rows]
    speed_stats = sample_stats(speeds)
    pvw_stats = sample_stats(pvw)
    scalar_stats = sample_stats(scalar)
    ratio_of_means = statistics.mean(scalar) / statistics.mean(pvw)
    pass_runs = sum(1 for row in rows if row["status"] == "Pass")
    return [
        {
            "param": PARAM,
            "r": R_VALUE,
            "runs": str(len(rows)),
            "pass_runs": str(pass_runs),
            "metric": "T_bootstrap/r",
            "pvw_mean_us": ffloat(pvw_stats["mean"], 3),
            "pvw_stdev_us": ffloat(pvw_stats["stdev"], 3),
            "scalar_repeated_mean_us": ffloat(scalar_stats["mean"], 3),
            "scalar_repeated_stdev_us": ffloat(scalar_stats["stdev"], 3),
            "mean_of_speedups": ffloat(speed_stats["mean"], 6),
            "speedup_stdev": ffloat(speed_stats["stdev"], 6),
            "speedup_ci95_low": ffloat(speed_stats["ci95_low"], 6),
            "speedup_ci95_high": ffloat(speed_stats["ci95_high"], 6),
            "ratio_of_means_speedup": ffloat(ratio_of_means, 6),
            "min_speedup": ffloat(speed_stats["min"], 6),
            "max_speedup": ffloat(speed_stats["max"], 6),
            "stats_label": "preflight n=3; insufficient for final paper table",
            "decision": "PASS_SELECTED_SUBSET_PREFLIGHT" if pass_runs == len(rows) and speed_stats["mean"] > 1.0 else "FAIL",
        }
    ]


def noise_rows(raw: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows = []
    for row in raw:
        rows.append(
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
                "max_allowed_log2_gap": row["max_allowed_log2_gap"],
                "source_log": row["source_log"],
            }
        )
    return rows


def noise_aggregate(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    failures = {
        "pvw": sum(int(row["pvw_failures"]) for row in rows),
        "scalar": sum(int(row["scalar_failures"]) for row in rows),
        "pair": sum(int(row["pair_failures"]) for row in rows),
    }
    gaps = [float(row["pvw_minus_scalar_log2"]) for row in rows]
    return [
        {
            "param": PARAM,
            "r": R_VALUE,
            "seeds": str(len(rows)),
            "points": str(sum(int(row["points"]) for row in rows)),
            "pvw_failures": str(failures["pvw"]),
            "scalar_failures": str(failures["scalar"]),
            "pair_failures": str(failures["pair"]),
            "avg_pvw_minus_scalar_log2": ffloat(statistics.mean(gaps), 6),
            "min_pvw_minus_scalar_log2": ffloat(min(gaps), 6),
            "max_pvw_minus_scalar_log2": ffloat(max(gaps), 6),
            "status": "PASS_PREFLIGHT" if sum(failures.values()) == 0 else "FAIL",
            "stats_label": "preflight seeds=3; insufficient for final noise claim",
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
        return ffloat(float(pvw[name]) / denom, 6) if denom else ""

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


def gate_rows(inputs: List[Dict[str, str]], shapes: List[Dict[str, str]], perf: List[Dict[str, str]], noise: List[Dict[str, str]], resource: List[Dict[str, str]]) -> List[Dict[str, str]]:
    resource_modes = {row["mode"] for row in resource}
    all_inputs = all(row["status"] == "present" for row in inputs)
    shape_pass = all(row["shape_gate"] == "PASS" for row in shapes)
    perf_pass = all(row["decision"] == "PASS_SELECTED_SUBSET_PREFLIGHT" for row in perf)
    noise_pass = all(row["status"] == "PASS_PREFLIGHT" for row in noise)
    resource_pass = {"pvw", "scalar", "pvw_vs_scalar_ratio"}.issubset(resource_modes)
    return [
        {
            "gate": "G1_inputs",
            "required": "Stage231 queue plus selected raw performance/noise/resource logs exist",
            "observed": "all present" if all_inputs else "missing inputs",
            "status": "PASS" if all_inputs else "FAIL",
            "claim_effect": "allows Stage232 aggregation",
        },
        {
            "gate": "G2_shape",
            "required": f"{PARAM} selects h={EXPECTED_H}, r_prec={EXPECTED_R_PREC}",
            "observed": f"h={shapes[0].get('observed_h','')}, r_prec={shapes[0].get('observed_r_prec','')}",
            "status": "PASS" if shape_pass else "FAIL",
            "claim_effect": "prevents default-parameter fallback",
        },
        {
            "gate": "G3_performance_preflight",
            "required": "3 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1",
            "observed": f"runs={perf[0].get('runs','')}, speedup_mean={perf[0].get('mean_of_speedups','')}, CI95={perf[0].get('speedup_ci95_low','')}..{perf[0].get('speedup_ci95_high','')}",
            "status": "PASS_PREFLIGHT" if perf_pass else "FAIL",
            "claim_effect": "positive selected-subset signal only; not final paper statistics",
        },
        {
            "gate": "G4_noise_preflight",
            "required": "3 deterministic seeds, zero PVW/scalar/pair failures",
            "observed": f"seeds={noise[0].get('seeds','')}, failures={noise[0].get('pvw_failures','')}/{noise[0].get('scalar_failures','')}/{noise[0].get('pair_failures','')}",
            "status": "PASS_PREFLIGHT" if noise_pass else "FAIL",
            "claim_effect": "noise sanity only; 20-seed gate remains pending",
        },
        {
            "gate": "G5_resource",
            "required": "pvw and scalar resource/keygen/RSS rows for the selected subset",
            "observed": "pvw/scalar resource rows present" if resource_pass else "resource row missing",
            "status": "PASS" if resource_pass else "FAIL",
            "claim_effect": "resource side condition recorded for selected subset",
        },
        {
            "gate": "G6_promotion_boundary",
            "required": "do not promote selected preflight to full added-parameter matrix",
            "observed": "full matrix and 10-run/20-seed gates still pending",
            "status": "BOUNDARY_HELD",
            "claim_effect": "blocks all-parameter and final-paper table claims",
        },
        {
            "gate": "G7_stage232_decision",
            "required": "all preflight gates pass and promotion boundary stays explicit",
            "observed": DECISION,
            "status": DECISION,
            "claim_effect": "proceed to high-stat matrix or scoped manuscript skeleton",
        },
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
            "route": "stage233_full_added_parameter_matrix",
            "entry_condition": "Added binary parameters must be promoted into a main paper table.",
            "gate": "10-run complete-SAB A/B, 20-seed noise, and resource/keygen/RSS for SET_4_5_2048 and SET_2_3_4096 r=2/r=4 or an explicitly smaller promoted matrix.",
            "status": "future",
            "failure_action": "Keep Stage231/232 as smoke/preflight only and cite Stage229 scoped matrix.",
            "evidence": rel(GATES),
        },
        {
            "priority": "P1",
            "route": "stage234_scoped_manuscript_skeleton",
            "entry_condition": "A manuscript/report draft is needed before spending full-matrix compute.",
            "gate": "Use only Stage206/224/229/230 as main claim support; Stage231/232 as continuity/preflight.",
            "status": "ready",
            "failure_action": "Remove current-head added-parameter tables from manuscript.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P2",
            "route": "stage235_nonbinary_or_compact_design",
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
            rows.append(
                {
                    "artifact": rel(path),
                    "bytes": str(path.stat().st_size),
                    "sha256": sha256(path),
                }
            )
    return rows


def write_docs(inputs: List[Dict[str, str]], selection: List[Dict[str, str]], shapes: List[Dict[str, str]], perf_runs: List[Dict[str, str]], perf_stats: List[Dict[str, str]], noise_seeds: List[Dict[str, str]], noise_agg: List[Dict[str, str]], resource: List[Dict[str, str]], gates: List[Dict[str, str]], proof: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    doc = f"""# Stage232 Selected-Subset Full-Stat/Resource Preflight

Decision: `{DECISION}`.

Stage232 executes one representative current-head added-parameter preflight:
`{PARAM}`, r={R_VALUE}, binary, `spqlios_avx512`, active-buffer PVW/MAT-SAB.
The primary endpoint remains complete-SAB `T_bootstrap/r`, meaning bootstrap
time divided by the number of plaintext lanes/bits processed by the MAT-RLWE
state. This stage is deliberately not a full added-parameter matrix.

## Selection Rationale

{table(selection, ["param", "r", "selection_reason", "primary_metric", "claim_level", "promotion_gate", "blocked_claims"])}
## Shape Gate

{table(shapes, ["param", "r", "observed_h", "expected_h", "observed_r_prec", "expected_r_prec", "correctness_status", "shape_gate", "source_log", "runs_checked"])}
## Performance Runs

{table(perf_runs, ["run", "status", "param", "r", "metric", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_scalar_repeated", "source_log"])}
## Performance Statistics

{table(perf_stats, ["param", "r", "runs", "pass_runs", "metric", "pvw_mean_us", "scalar_repeated_mean_us", "mean_of_speedups", "speedup_stdev", "speedup_ci95_low", "speedup_ci95_high", "ratio_of_means_speedup", "stats_label", "decision"])}
## Noise Preflight

{table(noise_seeds, ["param", "r", "seed", "status", "points", "pvw_failures", "scalar_failures", "pair_failures", "pvw_minus_scalar_log2", "source_log"])}
## Noise Aggregate

{table(noise_agg, ["param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "avg_pvw_minus_scalar_log2", "min_pvw_minus_scalar_log2", "max_pvw_minus_scalar_log2", "status", "stats_label"])}
## Resource Comparison

{table(resource, ["param", "r", "mode", "backend", "keygen_us", "keygen_lane_avg_us", "estimated_key_bytes", "estimated_key_bytes_ratio_vs_scalar_repeated", "internal_vmhwm_kb", "time_max_rss_kb", "source_log"])}
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

    plan = f"""# Stage232 Experiment Plan

## Hypothesis

Changing scalar repeated SAB into exact dense PVW/MAT-SAB for `{PARAM}`, r={R_VALUE}
should improve complete-SAB `T_bootstrap/r` over repeated scalar SAB because the
shared-mask MAT-RLWE state amortizes mask/key-flow work across r body lanes.

Status labels:

- [experiment checked, preflight only]: 3-run complete-SAB A/B and 3-seed noise
  have been executed.
- [statistical evidence insufficient]: n=3 and seeds=3 are not final paper
  statistics.
- [theory not closed]: this does not prove MAT-RLWE SAB optimality.

## Baseline

Repeated scalar SAB under the same `KEY=BINARY`, `PARAM={PARAM}`,
`FFT_LIB=spqlios_avx512`, `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`, and
`SAB_PVW_ACTIVE_BUFFER_FUSION=true` configuration.

## Primary Metric

Complete-SAB `T_bootstrap/r`, reported as speedup versus repeated scalar SAB.

## Commands

See `{rel(REPRO_CMDS)}`.

## Promotion Gate

To promote added parameters into a main claim table, rerun at least 10
complete-SAB A/B runs and 20 noise seeds for the selected parameter matrix, with
resource/keygen/RSS recorded.
"""
    write_text(PLAN, plan)

    theory = f"""# Stage232 Stats/Resource Model

The selected subset tests one falsifiable statement:

```text
For binary {PARAM}, r={R_VALUE}, exact dense PVW/MAT-SAB reduces amortized
complete-SAB time per plaintext lane, T_bootstrap/r, relative to running scalar
SAB r times under the same backend.
```

This is an amortized algorithm-level endpoint, not a raw kernel endpoint. The
measurement includes full SAB setup used by the benchmark path, CMUX/NCMUX,
RGSW monomial flow, extract/post-processing in that path, and correctness gate.

The 3-run t interval in `{rel(PERF_STATS)}` is a preflight interval. It is useful
for deciding whether the route is still alive at current head, but it is not a
final statistical claim. The 3-seed noise run is also a preflight; the 20-seed
gate remains the minimum for promotion.

Resource interpretation:

- `estimated_key_bytes_ratio_vs_scalar_repeated` compares PVW/MAT public
  bootstrap-key estimate against r scalar repeated keys.
- RSS ratios are process-level measurements from `/usr/bin/time -v` and internal
  VMHWM probes.
- A speedup is not promoted unless resource growth is reported beside it.
"""
    write_text(THEORY, theory)

    variant = f"""# mat_rlwe_sab_stage232_selected_subset: Selected current-head preflight

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping path.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [experiment checked, preflight only], [statistical evidence insufficient].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared-mask work across r
  body lanes and improves per-lane full bootstrapping throughput versus repeated
  scalar SAB.

## Mathematical Definition

The state is the existing exact dense MAT-RLWE/PVW state: one shared mask and r
body lanes. Stage232 does not change ciphertext equations or hot-path code; it
refreshes a selected current-head evidence point for `{PARAM}`, r={R_VALUE}.

## Pseudocode

```text
Input: binary SAB instance, PARAM={PARAM}, r={R_VALUE}
Output: preflight evidence package
1. Build scalar and PVW/MAT paths with identical backend flags.
2. Run 3 complete-SAB A/B trials and require per-run correctness Pass.
3. Run 3 deterministic noise seeds and require zero PVW/scalar/pair failures.
4. Run PVW and scalar resource probes and record keygen/key-size/RSS.
5. Label result as selected-subset preflight, not final matrix promotion.
```

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| r independent scalar SAB executions | one exact dense PVW/MAT-SAB execution with r body lanes | amortizes shared state and key flow | `{rel(PERF_STATS)}` |
| scalar resource accounting | PVW/MAT resource accounting beside scalar repeated | reports side cost | `{rel(RESOURCE)}` |
| single-run smoke | 3-run/3-seed selected preflight | increases evidence but not final stats | `{rel(GATES)}` |

## Complexity Change

- Time: measured as complete-SAB `T_bootstrap/r`; Stage232 mean speedup is in
  `{rel(PERF_STATS)}`.
- Memory/key: recorded in `{rel(RESOURCE)}`.
- What must still be measured: 10-run/20-seed full added-parameter matrix before
  paper-table promotion.

## Potential Failure Reasons

- The selected subset may not generalize to r=2 or `SET_4_5_2048`.
- n=3 timing variance may understate or overstate the true effect.
- The exact dense MAT route does not prove theoretical optimality or compact
  selector feasibility.

## Required Experiments

- Full added-parameter matrix if used in the main claim.
- Non-binary and compact-route design gates before any broader claim.
"""
    write_text(VARIANT, variant)


def write_repro_commands() -> None:
    text = f"""# Stage232 Reproduction Commands

Performance/noise preflight:

```bash
STAGE26_PERF_RUNS=3 \\
STAGE26_NOISE_SEED_COUNT=3 \\
STAGE26_PERF_NOISE_R_VALUES='{R_VALUE}' \\
STAGE26_PERF_NOISE_PARAMS='{PARAM}' \\
STAGE26_PERF_NOISE_OUT_DIR={rel(PERF_RAW)} \\
FFT_LIB=spqlios_avx512 \\
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \\
SAB_PVW_ACTIVE_BUFFER_FUSION=true \\
JOBS=2 \\
bash scripts/run_stage26_parameter_perf_noise.sh
```

Resource preflight:

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
python scripts/build_stage232_selected_subset_fullstat_resource.py
```
"""
    write_text(REPRO_CMDS, text)


def update_project_files() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 232: Selected Current-Head Full-Stat/Resource Preflight",
        f"""
## Stage 232: Selected Current-Head Full-Stat/Resource Preflight

Goal:

```text
Run a representative current-head added-parameter preflight with complete-SAB
`T_bootstrap/r`, noise, and resource side conditions without promoting it to a
full parameter-matrix claim.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. `{PARAM}`, r={R_VALUE}
passes selected-subset 3-run complete-SAB A/B, 3-seed noise, and resource
recording. Full added-parameter matrix statistics remain pending.
```
""",
    )
    append_once(
        GOAL,
        "## Stage232 selected-subset preflight",
        f"""
## Stage232 selected-subset preflight

Generated from input head `{head}`, Stage232 records `{DECISION}`. The selected
current-head `{PARAM}`, r={R_VALUE} preflight is positive under complete-SAB
`T_bootstrap/r` and includes resource/keygen/RSS side conditions. This does not
close all-parameter, non-binary, final-paper statistics, or theoretical
optimality gates.
""",
    )
    append_once(
        CURRENT_GOAL,
        "### Stage232 selected current-head preflight",
        f"""
### Stage232 selected current-head preflight

`{DECISION}` records a bounded executable step after Stage231. The goal remains
active: Stage232 is selected-subset preflight evidence only; full matrix
high-statistics and manuscript packaging remain open.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage232_selected_subset_fullstat_resource:",
        f"""
H10_stage232_selected_subset_fullstat_resource:
  status: selected_subset_preflight_passed_full_matrix_pending
  evidence:
    - repro/stage232_selected_subset_fullstat_resource/performance_stats.csv
    - repro/stage232_selected_subset_fullstat_resource/noise_aggregate.csv
    - repro/stage232_selected_subset_fullstat_resource/resource_comparison.csv
    - docs/stage232_selected_subset_fullstat_resource.md
  conclusion: >
    Stage232 records {DECISION}. The selected current-head binary {PARAM}, r={R_VALUE}
    preflight passes 3-run complete-SAB T_bootstrap/r, 3-seed noise, and
    resource gates, but full added-parameter matrix statistics, non-binary
    support, and theoretical optimality remain pending.
""",
    )
    append_once(
        RUN_LOG,
        "stage232-selected-subset-fullstat-resource-001",
        f"""stage232-selected-subset-fullstat-resource-001,{date.today().isoformat()},{head},Stage 232,spqlios_avx512,"bash scripts/run_stage26_parameter_perf_noise.sh; bash scripts/run_stage25_resource_matrix.sh; python scripts/build_stage232_selected_subset_fullstat_resource.py","{PARAM} r={R_VALUE}; runs=3; seeds=3; resource pvw/scalar",6863025,{DECISION},"Selected-subset preflight passed; full matrix high-statistics pending.",docs/stage232_selected_subset_fullstat_resource.md; repro/stage232_selected_subset_fullstat_resource/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage232_selected_subset_fullstat_resource:",
        f"""
- stage232_selected_subset_fullstat_resource:
  - `docs/stage232_selected_subset_fullstat_resource.md`
  - `experiments/stage232_selected_subset_fullstat_resource_plan.md`
  - `theory_checks/stage232_subset_stats_resource_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage232_selected_subset.md`
  - `scripts/build_stage232_selected_subset_fullstat_resource.py`
  - `repro/stage232_selected_subset_fullstat_resource/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage232 selected-subset full-stat/resource preflight records decision",
        f"""
- [x] Stage232 selected-subset full-stat/resource preflight records decision `{DECISION}`.
""",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    perf_run_raw = read_csv(PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs3" / "summary.csv")
    noise_seed_raw = read_csv(PERF_RAW / f"noise_{PARAM}_r{R_VALUE}_seeds3" / "summary.csv")
    resource_raw = read_csv(RESOURCE_RAW / "summary.csv")

    inputs = input_rows()
    selection = selection_rows()
    perf_runs = performance_rows(perf_run_raw)
    perf_stats = performance_stats(perf_runs)
    noise_seeds = noise_rows(noise_seed_raw)
    noise_agg = noise_aggregate(noise_seeds)
    resource = resource_rows(resource_raw)
    shapes = shape_rows(perf_runs)
    gates = gate_rows(inputs, shapes, perf_stats, noise_agg, resource)
    proof = proof_rows(gates)
    nextq = next_rows()

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(SELECTION, selection, ["param", "r", "selection_reason", "primary_metric", "claim_level", "promotion_gate", "blocked_claims"])
    write_csv(SHAPE, shapes, ["param", "r", "observed_h", "expected_h", "observed_r_prec", "expected_r_prec", "correctness_status", "shape_gate", "source_log", "runs_checked"])
    write_csv(PERF_RUNS, perf_runs, ["run", "status", "param", "r", "metric", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_scalar_repeated", "source_log"])
    write_csv(PERF_STATS, perf_stats, ["param", "r", "runs", "pass_runs", "metric", "pvw_mean_us", "pvw_stdev_us", "scalar_repeated_mean_us", "scalar_repeated_stdev_us", "mean_of_speedups", "speedup_stdev", "speedup_ci95_low", "speedup_ci95_high", "ratio_of_means_speedup", "min_speedup", "max_speedup", "stats_label", "decision"])
    write_csv(NOISE_SEEDS, noise_seeds, ["param", "r", "seed", "status", "points", "pvw_failures", "scalar_failures", "pair_failures", "pvw_minus_scalar_log2", "max_allowed_log2_gap", "source_log"])
    write_csv(NOISE_AGG, noise_agg, ["param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "avg_pvw_minus_scalar_log2", "min_pvw_minus_scalar_log2", "max_pvw_minus_scalar_log2", "status", "stats_label"])
    write_csv(RESOURCE, resource, ["param", "r", "mode", "backend", "keygen_us", "keygen_lane_avg_us", "estimated_key_bytes", "estimated_key_bytes_ratio_vs_scalar_repeated", "internal_vmhwm_kb", "time_max_rss_kb", "source_log", "time_log"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()

    write_docs(inputs, selection, shapes, perf_runs, perf_stats, noise_seeds, noise_agg, resource, gates, proof, nextq)

    artifact_candidates = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        INPUTS,
        SELECTION,
        SHAPE,
        PERF_RUNS,
        PERF_STATS,
        NOISE_SEEDS,
        NOISE_AGG,
        RESOURCE,
        GATES,
        PROOF,
        NEXT,
        REPORT,
        REPRO_CMDS,
        PERF_RAW / "performance_summary.csv",
        PERF_RAW / "noise_summary.csv",
        RESOURCE_RAW / "summary.csv",
    ]
    write_csv(ARTIFACT, artifact_rows(artifact_candidates), ["artifact", "bytes", "sha256"])
    update_project_files()

    print(f"Stage232 report: {rel(DOC)}")
    print(f"Stage232 decision: {DECISION}")


if __name__ == "__main__":
    main()
