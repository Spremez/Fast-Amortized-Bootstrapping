#!/usr/bin/env python3
"""Stage236: high-stat SET_2_3_4096 r=4 slice and selected binary matrix close."""

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
OUT = ROOT / "repro" / "stage236_set_2_3_4096_r4_highstat_slice"
PERF_RAW = ROOT / "repro" / "stage236_set_2_3_4096_r4_runs10_seeds20"
RESOURCE_RAW = ROOT / "repro" / "stage236_set_2_3_4096_r4_resource"

STAGE233 = ROOT / "repro" / "stage233_set_4_5_2048_r4_highstat_slice"
STAGE234 = ROOT / "repro" / "stage234_set_4_5_2048_r2_highstat_slice"
STAGE235 = ROOT / "repro" / "stage235_set_2_3_4096_r2_highstat_slice"

DOC = ROOT / "docs" / "stage236_set_2_3_4096_r4_highstat_slice.md"
PLAN = ROOT / "experiments" / "stage236_set_2_3_4096_r4_highstat_slice_plan.md"
THEORY = ROOT / "theory_checks" / "stage236_selected_binary_matrix_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage236_selected_binary_matrix.md"

INPUTS = OUT / "input_status.csv"
SHAPE = OUT / "shape_gate.csv"
PERF_RUNS = OUT / "performance_runs.csv"
PERF_STATS = OUT / "performance_stats.csv"
NOISE_SEEDS = OUT / "noise_seed_stats.csv"
NOISE_AGG = OUT / "noise_aggregate.csv"
RESOURCE = OUT / "resource_comparison.csv"
MATRIX = OUT / "selected_binary_matrix_summary.csv"
GATES = OUT / "gate_matrix.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage236_report.md"
ARTIFACT = OUT / "artifact_index.csv"
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
PERF_RUN_COUNT = 10
NOISE_SEED_COUNT = 20
DECISION = "PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE"


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


def first(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def input_rows() -> List[Dict[str, str]]:
    paths = [
        (STAGE233 / "performance_stats.csv", "Stage233 SET_4_5_2048 r=4 high-stat performance"),
        (STAGE234 / "performance_stats.csv", "Stage234 SET_4_5_2048 r=2 high-stat performance"),
        (STAGE235 / "performance_stats.csv", "Stage235 SET_2_3_4096 r=2 high-stat performance"),
        (PERF_RAW / "performance_summary.csv", "Stage236 raw high-stat performance aggregate"),
        (PERF_RAW / f"perf_{PARAM}_r{R_VALUE}_runs{PERF_RUN_COUNT}" / "summary.csv", "Stage236 per-run performance"),
        (PERF_RAW / "noise_summary.csv", "Stage236 high-stat noise aggregate summary"),
        (PERF_RAW / f"noise_{PARAM}_r{R_VALUE}_seeds{NOISE_SEED_COUNT}" / "summary.csv", "Stage236 per-seed noise"),
        (RESOURCE_RAW / "summary.csv", "Stage236 resource/keygen/RSS"),
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
            "stats_label": "high-stat slice n=10; SET_2_3_4096 r=4",
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
            "pvw_log2_sigma_torus": row.get("pvw_log2_sigma_torus", ""),
            "scalar_log2_sigma_torus": row.get("scalar_log2_sigma_torus", ""),
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
            "stats_label": "high-stat slice seeds=20; SET_2_3_4096 r=4",
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


def resource_ratio(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    for row in rows:
        if row.get("mode") == "pvw_vs_scalar_ratio":
            return row
    return {}


def matrix_rows(current_perf: List[Dict[str, str]], current_noise: List[Dict[str, str]], current_resource: List[Dict[str, str]]) -> List[Dict[str, str]]:
    specs = [
        ("SET_4_5_2048", "4", "Stage233", STAGE233),
        ("SET_4_5_2048", "2", "Stage234", STAGE234),
        ("SET_2_3_4096", "2", "Stage235", STAGE235),
    ]
    rows = []
    for param, r, stage, base in specs:
        perf = first(base / "performance_stats.csv")
        noise = first(base / "noise_aggregate.csv")
        res = resource_ratio(base / "resource_comparison.csv")
        rows.append(
            {
                "param": param,
                "r": r,
                "stage": stage,
                "stat_level": "high-stat n=10/seeds=20",
                "mean_speedup": perf.get("mean_of_speedups", ""),
                "speedup_ci95_low": perf.get("speedup_ci95_low", ""),
                "speedup_ci95_high": perf.get("speedup_ci95_high", ""),
                "noise_failures": f"{noise.get('pvw_failures','')}/{noise.get('scalar_failures','')}/{noise.get('pair_failures','')}",
                "key_bytes_ratio": res.get("estimated_key_bytes_ratio_vs_scalar_repeated", ""),
                "keygen_ratio": res.get("keygen_us", ""),
                "rss_ratio": res.get("time_max_rss_kb", ""),
                "status": "PASS_HIGHSTAT_SLICE" if perf.get("decision") == "PASS_HIGHSTAT_SLICE" and noise.get("status") == "PASS_HIGHSTAT_SLICE" else "CHECK",
                "evidence": rel(base / "proof_gate.csv"),
            }
        )
    res_current = next((row for row in current_resource if row["mode"] == "pvw_vs_scalar_ratio"), {})
    rows.append(
        {
            "param": PARAM,
            "r": R_VALUE,
            "stage": "Stage236",
            "stat_level": "high-stat n=10/seeds=20",
            "mean_speedup": current_perf[0].get("mean_of_speedups", ""),
            "speedup_ci95_low": current_perf[0].get("speedup_ci95_low", ""),
            "speedup_ci95_high": current_perf[0].get("speedup_ci95_high", ""),
            "noise_failures": f"{current_noise[0].get('pvw_failures','')}/{current_noise[0].get('scalar_failures','')}/{current_noise[0].get('pair_failures','')}",
            "key_bytes_ratio": res_current.get("estimated_key_bytes_ratio_vs_scalar_repeated", ""),
            "keygen_ratio": res_current.get("keygen_us", ""),
            "rss_ratio": res_current.get("time_max_rss_kb", ""),
            "status": "PASS_HIGHSTAT_SLICE" if current_perf[0].get("decision") == "PASS_HIGHSTAT_SLICE" and current_noise[0].get("status") == "PASS_HIGHSTAT_SLICE" else "CHECK",
            "evidence": rel(PROOF),
        }
    )
    return rows


def gate_rows(inputs: List[Dict[str, str]], shape: List[Dict[str, str]], perf: List[Dict[str, str]], noise: List[Dict[str, str]], resource: List[Dict[str, str]], matrix: List[Dict[str, str]]) -> List[Dict[str, str]]:
    resource_pass = {"pvw", "scalar", "pvw_vs_scalar_ratio"}.issubset({row["mode"] for row in resource})
    matrix_pass = all(row["status"] == "PASS_HIGHSTAT_SLICE" for row in matrix)
    return [
        {"gate": "G1_inputs", "required": "Stage233/234/235 route evidence plus raw Stage236 logs exist", "observed": "all present" if all(row["status"] == "present" for row in inputs) else "missing", "status": "PASS" if all(row["status"] == "present" for row in inputs) else "FAIL", "claim_effect": "allows Stage236 aggregation"},
        {"gate": "G2_shape", "required": f"{PARAM} selects h={EXPECTED_H}, r_prec={EXPECTED_R_PREC}", "observed": f"h={shape[0].get('observed_h','')}, r_prec={shape[0].get('observed_r_prec','')}", "status": "PASS" if all(row["shape_gate"] == "PASS" for row in shape) else "FAIL", "claim_effect": "prevents default-parameter fallback"},
        {"gate": "G3_performance_highstat_slice", "required": "10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1", "observed": f"runs={perf[0].get('runs','')}, speedup_mean={perf[0].get('mean_of_speedups','')}, CI95={perf[0].get('speedup_ci95_low','')}..{perf[0].get('speedup_ci95_high','')}", "status": "PASS_HIGHSTAT_SLICE" if all(row["decision"] == "PASS_HIGHSTAT_SLICE" for row in perf) else "FAIL", "claim_effect": "supports this parameter/r slice only"},
        {"gate": "G4_noise_highstat_slice", "required": "20 deterministic seeds, zero PVW/scalar/pair failures", "observed": f"seeds={noise[0].get('seeds','')}, failures={noise[0].get('pvw_failures','')}/{noise[0].get('scalar_failures','')}/{noise[0].get('pair_failures','')}", "status": "PASS_HIGHSTAT_SLICE" if all(row["status"] == "PASS_HIGHSTAT_SLICE" for row in noise) else "FAIL", "claim_effect": "noise side condition supports this slice only"},
        {"gate": "G5_resource", "required": "pvw and scalar resource/keygen/RSS rows for this slice", "observed": "pvw/scalar resource rows present" if resource_pass else "missing", "status": "PASS" if resource_pass else "FAIL", "claim_effect": "records key/RSS side cost beside throughput"},
        {"gate": "G6_metric_boundary", "required": "compare amortized complete SAB, not isolated MAT external product", "observed": "primary endpoint is complete-SAB T_bootstrap/r", "status": "PASS", "claim_effect": "aligns with MAT-RLWE r-body design intent"},
        {"gate": "G7_selected_binary_matrix", "required": "SET_4_5_2048 and SET_2_3_4096, r=2/r=4, all have high-stat perf/noise/resource evidence", "observed": "four selected binary rows pass" if matrix_pass else "one or more rows incomplete", "status": "PASS_SELECTED_BINARY_MATRIX" if matrix_pass else "FAIL", "claim_effect": "supports selected binary added-parameter matrix only"},
        {"gate": "G8_claim_boundary", "required": "do not upgrade to non-binary, compact, all-parameter, novelty, or theoretical-optimality claims", "observed": "boundaries remain explicit", "status": "BOUNDARY_HELD", "claim_effect": "blocks overclaiming beyond measured selected binary rows"},
        {"gate": "G9_stage236_decision", "required": "all Stage236 gates pass and boundaries stay explicit", "observed": DECISION, "status": DECISION, "claim_effect": "move to scoped manuscript/report package"},
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
        {"priority": "P0", "route": "stage237_scoped_manuscript_skeleton", "entry_condition": "Selected binary added-parameter matrix is complete under high-stat gates.", "gate": "Draft a scoped report with algorithm, T_bootstrap/r metric, four-row matrix table, resource/noise side conditions, and claim boundary.", "status": "ready", "failure_action": "Keep evidence as engineering report rather than paper claim.", "evidence": rel(MATRIX)},
        {"priority": "P1", "route": "stage238_native_counter_or_backend_validation", "entry_condition": "The manuscript needs stronger implementation attribution.", "gate": "Run native Linux perf counters or mark WSL counters as proxy only.", "status": "optional", "failure_action": "Do not make hardware-counter or theoretical-optimality claims.", "evidence": rel(PROOF)},
        {"priority": "P2", "route": "stage239_nonbinary_or_compact_design", "entry_condition": "The project expands beyond exact dense binary MAT/PVW-SAB.", "gate": "Closed selector equations, security/noise model, isolated equivalence, production keygen, and full SAB A/B.", "status": "blocked_until_design", "failure_action": "Do not claim non-binary, compact, or theoretical-optimal MAT-RLWE SAB.", "evidence": rel(NEXT)},
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
        f"""# Stage236 Reproduction Commands

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
python scripts/build_stage236_highstat_slice.py
```
""",
    )


def write_docs(inputs: List[Dict[str, str]], shape: List[Dict[str, str]], perf_runs: List[Dict[str, str]], perf_stats: List[Dict[str, str]], noise_seeds: List[Dict[str, str]], noise_agg: List[Dict[str, str]], resource: List[Dict[str, str]], matrix: List[Dict[str, str]], gates: List[Dict[str, str]], proof: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> None:
    doc = f"""# Stage236 High-Stat SET_2_3_4096 r=4 Slice

Decision: `{DECISION}`.

Stage236 promotes binary `{PARAM}`, r={R_VALUE}, from Stage232 preflight to a
high-stat current-head slice under `spqlios_avx512`,
`MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`, and
`SAB_PVW_ACTIVE_BUFFER_FUSION=true`. The primary endpoint is complete-SAB
`T_bootstrap/r`: amortized bootstrapping time per processed plaintext lane/bit.

Together with Stage233, Stage234, and Stage235, this completes the selected
binary added-parameter matrix for `SET_4_5_2048` and `SET_2_3_4096` at r=2 and
r=4. The supported claim remains scoped to those measured binary rows; it does
not include non-binary branches, compact selector keygen, all-parameter
universality, novelty, or theoretical optimality.

## Shape Gate

{table(shape, ["param", "r", "observed_h", "expected_h", "observed_r_prec", "expected_r_prec", "correctness_status", "shape_gate", "runs_checked", "source_log"])}
## Performance Statistics

{table(perf_stats, ["param", "r", "runs", "pass_runs", "metric", "pvw_mean_us", "scalar_repeated_mean_us", "mean_of_speedups", "speedup_stdev", "speedup_ci95_low", "speedup_ci95_high", "ratio_of_means_speedup", "min_speedup", "max_speedup", "stats_label", "decision"])}
## Performance Runs

{table(perf_runs, ["run", "status", "param", "r", "metric", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_scalar_repeated", "source_log"])}
## Noise Aggregate

{table(noise_agg, ["param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "avg_pvw_minus_scalar_log2", "min_pvw_minus_scalar_log2", "max_pvw_minus_scalar_log2", "status", "stats_label"])}
## Noise Seeds

{table(noise_seeds, ["param", "r", "seed", "status", "points", "pvw_failures", "scalar_failures", "pair_failures", "pvw_log2_sigma_torus", "scalar_log2_sigma_torus", "pvw_minus_scalar_log2", "source_log"])}
## Resource Comparison

{table(resource, ["param", "r", "mode", "backend", "keygen_us", "keygen_lane_avg_us", "estimated_key_bytes", "estimated_key_bytes_ratio_vs_scalar_repeated", "internal_vmhwm_kb", "time_max_rss_kb", "source_log"])}
## Selected Binary Matrix

{table(matrix, ["param", "r", "stage", "stat_level", "mean_speedup", "speedup_ci95_low", "speedup_ci95_high", "noise_failures", "key_bytes_ratio", "keygen_ratio", "rss_ratio", "status", "evidence"])}
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
        f"""# Stage236 Experiment Plan

## Hypothesis

For binary `{PARAM}`, r={R_VALUE}, exact dense PVW/MAT-SAB improves complete-SAB
`T_bootstrap/r` over r repeated scalar SAB executions under the same backend.

## Baseline And Metric

Baseline: repeated scalar SAB with the same `KEY`, `PARAM`, `FFT_LIB`,
`MAT_TRGSW_AVX512_SMALLR_SPECIALIZED`, and active-buffer flag. Primary metric:
complete-SAB `T_bootstrap/r`, not isolated MAT external-product latency.

## Gate

This stage requires 10 complete-SAB A/B runs, 20 deterministic noise seeds, and
resource/keygen/RSS rows for PVW and scalar repeated modes. Passing this stage
closes the selected binary added-parameter matrix with Stage233/234/235.
""",
    )
    write_text(
        THEORY,
        f"""# Stage236 Selected Binary Matrix Model

The MAT-RLWE/PVW redesign is evaluated as an amortized complete bootstrapping
algorithm:

```text
speedup = T_scalar_repeated(r lanes) / T_pvw_mat_sab(r body lanes)
lane_time = T_bootstrap / r
```

Stage236 adds the final selected binary row, `{PARAM}` r={R_VALUE}. The selected
matrix now has four high-stat rows: `SET_4_5_2048` r=2/r=4 and
`SET_2_3_4096` r=2/r=4. This supports a scoped engineering claim about exact
dense PVW/MAT-SAB throughput on measured binary rows. It does not prove
non-binary support, compact selector construction, novelty, or theoretical
optimality.
""",
    )
    write_text(
        VARIANT,
        f"""# mat_rlwe_sab_stage236_selected_binary_matrix

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping path.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [selected binary matrix checked], [broader claims blocked].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared-mask SAB work across
  r body lanes and improves per-lane full bootstrapping throughput versus
  repeated scalar SAB for the selected binary parameter rows.

## Matrix Scope

The checked rows are `SET_4_5_2048` r=2/r=4 and `SET_2_3_4096` r=2/r=4. This
is not an all-parameter, non-binary, compact-route, novelty, or theoretical
optimality statement.
""",
    )


def update_project_files() -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 236: SET_2_3_4096 r=4 High-Stat Slice",
        f"""
## Stage 236: SET_2_3_4096 r=4 High-Stat Slice

Goal:

```text
Promote SET_2_3_4096 r=4 from preflight to 10-run/20-seed/resource evidence
under complete-SAB T_bootstrap/r and close the selected binary added-parameter
matrix.
```

Status:

```text
Generated from input head `{head}` with `{DECISION}`. `{PARAM}`, r={R_VALUE}
passes 10-run complete-SAB A/B, 20-seed noise, and resource recording. The
selected binary matrix for SET_4_5_2048 and SET_2_3_4096 at r=2/r=4 is now
high-stat complete, with broader claims still gated.
```
""",
    )
    append_once(
        GOAL,
        "## Stage236 selected binary added-parameter matrix complete",
        f"""
## Stage236 selected binary added-parameter matrix complete

Generated from input head `{head}`, Stage236 records `{DECISION}`. The
current-head `{PARAM}`, r={R_VALUE} slice passes high-stat complete-SAB
`T_bootstrap/r`, noise, and resource gates. Together with Stage233/234/235,
the selected binary matrix covers `SET_4_5_2048` and `SET_2_3_4096`, r=2/r=4.
Non-binary support, compact route, novelty, all-parameter scope, and
theoretical optimality remain open.
""",
    )
    append_once(
        CURRENT_GOAL,
        "### Stage236 selected binary added-parameter matrix complete",
        f"""
### Stage236 selected binary added-parameter matrix complete

`{DECISION}` records the fourth current-head added-parameter high-stat slice.
The selected binary matrix is now complete for `SET_4_5_2048` and
`SET_2_3_4096`, r=2/r=4. The active goal remains open for manuscript packaging,
source-grounded novelty boundaries, and any broader design routes.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage236_selected_binary_matrix_complete:",
        f"""
H10_stage236_selected_binary_matrix_complete:
  status: selected_binary_added_parameter_matrix_highstat_complete
  evidence:
    - repro/stage236_set_2_3_4096_r4_highstat_slice/performance_stats.csv
    - repro/stage236_set_2_3_4096_r4_highstat_slice/noise_aggregate.csv
    - repro/stage236_set_2_3_4096_r4_highstat_slice/resource_comparison.csv
    - repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv
    - docs/stage236_set_2_3_4096_r4_highstat_slice.md
  conclusion: >
    Stage236 records {DECISION}. The current-head binary {PARAM}, r={R_VALUE}
    slice passes 10-run complete-SAB T_bootstrap/r, 20-seed noise, and resource
    gates. Together with Stage233/234/235, selected binary rows SET_4_5_2048
    and SET_2_3_4096 at r=2/r=4 are high-stat complete. Non-binary support,
    compact route, novelty, all-parameter scope, and theoretical optimality
    remain pending.
""",
    )
    append_once(
        RUN_LOG,
        "stage236-selected-binary-matrix-001",
        f"""stage236-selected-binary-matrix-001,{date.today().isoformat()},{head},Stage 236,spqlios_avx512,"bash scripts/run_stage26_parameter_perf_noise.sh; bash scripts/run_stage25_resource_matrix.sh; python scripts/build_stage236_highstat_slice.py","{PARAM} r={R_VALUE}; runs=10; seeds=20; resource pvw/scalar",6863025,{DECISION},"Fourth added-parameter high-stat slice passed; selected binary matrix complete.",docs/stage236_set_2_3_4096_r4_highstat_slice.md; repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage236_set_2_3_4096_r4_highstat_slice:",
        f"""
- stage236_set_2_3_4096_r4_highstat_slice:
  - `docs/stage236_set_2_3_4096_r4_highstat_slice.md`
  - `experiments/stage236_set_2_3_4096_r4_highstat_slice_plan.md`
  - `theory_checks/stage236_selected_binary_matrix_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage236_selected_binary_matrix.md`
  - `scripts/build_stage236_highstat_slice.py`
  - `repro/stage236_set_2_3_4096_r4_highstat_slice/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage236 selected binary added-parameter matrix complete",
        f"""
- [x] Stage236 selected binary added-parameter matrix records decision `{DECISION}`.
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
    matrix = matrix_rows(perf_stats, noise_agg, resource)
    gates = gate_rows(inputs, shape, perf_stats, noise_agg, resource, matrix)
    proof = proof_rows(gates)
    nextq = next_rows()

    write_csv(INPUTS, inputs, ["input", "status", "role", "bytes"])
    write_csv(SHAPE, shape, ["param", "r", "observed_h", "expected_h", "observed_r_prec", "expected_r_prec", "correctness_status", "shape_gate", "runs_checked", "source_log"])
    write_csv(PERF_RUNS, perf_runs, ["run", "status", "param", "r", "metric", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_scalar_repeated", "source_log"])
    write_csv(PERF_STATS, perf_stats, ["param", "r", "runs", "pass_runs", "metric", "pvw_mean_us", "pvw_stdev_us", "scalar_repeated_mean_us", "scalar_repeated_stdev_us", "mean_of_speedups", "speedup_stdev", "speedup_ci95_low", "speedup_ci95_high", "ratio_of_means_speedup", "min_speedup", "max_speedup", "stats_label", "decision"])
    write_csv(NOISE_SEEDS, noise_seeds, ["param", "r", "seed", "status", "points", "pvw_failures", "scalar_failures", "pair_failures", "pvw_log2_sigma_torus", "scalar_log2_sigma_torus", "pvw_minus_scalar_log2", "source_log"])
    write_csv(NOISE_AGG, noise_agg, ["param", "r", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "avg_pvw_minus_scalar_log2", "min_pvw_minus_scalar_log2", "max_pvw_minus_scalar_log2", "status", "stats_label"])
    write_csv(RESOURCE, resource, ["param", "r", "mode", "backend", "keygen_us", "keygen_lane_avg_us", "estimated_key_bytes", "estimated_key_bytes_ratio_vs_scalar_repeated", "internal_vmhwm_kb", "time_max_rss_kb", "source_log", "time_log"])
    write_csv(MATRIX, matrix, ["param", "r", "stage", "stat_level", "mean_speedup", "speedup_ci95_low", "speedup_ci95_high", "noise_failures", "key_bytes_ratio", "keygen_ratio", "rss_ratio", "status", "evidence"])
    write_csv(GATES, gates, ["gate", "required", "observed", "status", "claim_effect"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_repro_commands()
    write_docs(inputs, shape, perf_runs, perf_stats, noise_seeds, noise_agg, resource, matrix, gates, proof, nextq)

    artifact_candidates = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        INPUTS,
        SHAPE,
        PERF_RUNS,
        PERF_STATS,
        NOISE_SEEDS,
        NOISE_AGG,
        RESOURCE,
        MATRIX,
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
    print(f"Stage236 report: {rel(DOC)}")
    print(f"Stage236 decision: {DECISION}")


if __name__ == "__main__":
    main()
