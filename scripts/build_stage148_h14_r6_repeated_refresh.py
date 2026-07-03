#!/usr/bin/env python3
"""Build Stage148 current-head H14 r=6 repeated/noise/resource refresh."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage148_h14_r6_repeated_refresh"
STAGE147_SUMMARY = ROOT / "repro" / "stage147_h14_r6_current_head_route" / "summary.csv"

PERF_RESULTS_CSV = OUT_DIR / "perf_results.csv"
PERF_COMPARISON_CSV = OUT_DIR / "perf_comparison.csv"
NOISE_RESULTS_CSV = OUT_DIR / "noise_results.csv"
NOISE_AGG_CSV = OUT_DIR / "noise_aggregate.csv"
RESOURCE_RESULTS_CSV = OUT_DIR / "resource_results.csv"
RESOURCE_COMPARISON_CSV = OUT_DIR / "resource_comparison.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage148_h14_r6_repeated_refresh.md"
PLAN_MD = ROOT / "experiments" / "stage148_h14_r6_repeated_refresh_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage148_h14_repeated_stat_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_h14_r6_repeated_refresh.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

R_VALUE = int(os.environ.get("STAGE148_R", "6"))
PERF_RUNS = int(os.environ.get("STAGE148_PERF_RUNS", "3"))
BENCH_REPS = int(os.environ.get("SAB_PVW_BENCH_REPS", "1"))
NOISE_SEED_COUNT = int(os.environ.get("STAGE148_NOISE_SEED_COUNT", "3"))
NOISE_START_SEED = int(os.environ.get("STAGE148_NOISE_START_SEED", "6869480"))
NOISE_TRIALS = int(os.environ.get("STAGE148_NOISE_TRIALS", "1"))
RESOURCE_RUNS = int(os.environ.get("STAGE148_RESOURCE_RUNS", "1"))
JOBS = int(os.environ.get("JOBS", "8"))

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true"
)
PERF_CONFIGS = [
    {
        "variant": "wrapper_fused_from_dft_add",
        "flags": (
            f"{BASE_FLAGS} SAB_PVW_FUSED_FROM_DFT_ADD=true "
            f"SAB_PVW_BENCH=true SAB_PVW_BENCH_R={R_VALUE} "
            f"SAB_PVW_BENCH_REPS={BENCH_REPS}"
        ),
    },
    {
        "variant": "backend_from_dft_add",
        "flags": (
            f"{BASE_FLAGS} SAB_PVW_BACKEND_FROM_DFT_ADD=true "
            f"SAB_PVW_BENCH=true SAB_PVW_BENCH_R={R_VALUE} "
            f"SAB_PVW_BENCH_REPS={BENCH_REPS}"
        ),
    },
]

PERF_FIELDS = [
    "variant", "run", "status", "r", "h", "r_prec", "pvw_avg_us",
    "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us",
    "speedup_vs_scalar_repeated", "source_log",
]
PERF_COMPARE_FIELDS = [
    "metric", "runs", "wrapper_mean_pvw_lane_us",
    "backend_mean_pvw_lane_us", "backend_vs_wrapper_mean_speedup",
    "backend_vs_wrapper_min_speedup", "backend_vs_wrapper_ci95_low",
    "backend_vs_wrapper_ci95_high", "wrapper_mean_speedup_vs_scalar",
    "backend_mean_speedup_vs_scalar", "backend_incremental_speedup_vs_wrapper_scalar_speedup",
    "decision",
]
NOISE_FIELDS = [
    "r", "seed", "status", "points", "pvw_failures",
    "scalar_failures", "pair_failures", "pvw_log2_sigma_torus",
    "scalar_log2_sigma_torus", "pair_log2_sigma_torus",
    "pvw_minus_scalar_log2", "max_allowed_log2_gap", "source_log",
]
NOISE_AGG_FIELDS = [
    "r", "seeds", "points", "pvw_failures", "scalar_failures",
    "pair_failures", "min_pvw_minus_scalar_log2",
    "max_pvw_minus_scalar_log2", "avg_pvw_minus_scalar_log2", "status",
]
RESOURCE_FIELDS = [
    "run", "mode", "status", "keygen_us", "keygen_lane_avg_us",
    "estimated_key_bytes", "estimated_key_bytes_ratio_vs_scalar_repeated",
    "internal_vmhwm_kb", "time_max_rss_kb", "source_log",
]
RESOURCE_COMPARE_FIELDS = [
    "runs", "pvw_key_bytes", "scalar_key_bytes", "key_bytes_ratio",
    "pvw_keygen_lane_avg_us", "scalar_keygen_lane_avg_us",
    "keygen_lane_ratio", "pvw_vmhwm_kb", "scalar_vmhwm_kb",
    "vmhwm_ratio", "pvw_time_max_rss_kb", "scalar_time_max_rss_kb",
    "time_max_rss_ratio", "status",
]
SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]

CORRECT_RE = re.compile(
    r"SAB_PVW_BENCH correctness target_full r=(?P<r>\d+) h=(?P<h>\d+) "
    r"r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
BENCH_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+) pvw_stddev_us=(?P<pvw_stddev_us>[0-9.]+) "
    r"pvw_lane_avg_us=(?P<pvw_lane_avg_us>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+) "
    r"scalar_stddev_us=(?P<scalar_stddev_us>[0-9.]+) "
    r"scalar_lane_avg_us=(?P<scalar_lane_avg_us>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x "
    r"speedup_stddev=(?P<speedup_stddev>[0-9.]+)"
)
NOISE_GATE_RE = re.compile(r"SAB_PVW_NOISE target full bootstrap gate: (?P<status>\w+)")
NOISE_SUMMARY_RE = re.compile(
    r"SAB_PVW_NOISE summary target_full r=(?P<r>\d+) trials=(?P<trials>\d+) "
    r"points=(?P<points>\d+) pvw_failures=(?P<pvw_failures>\d+) "
    r"scalar_failures=(?P<scalar_failures>\d+) pair_failures=(?P<pair_failures>\d+) "
    r"pvw_log2_sigma_torus=(?P<pvw_log2_sigma_torus>[-0-9.inf]+) "
    r"scalar_log2_sigma_torus=(?P<scalar_log2_sigma_torus>[-0-9.inf]+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>[-0-9.inf]+) "
    r"pvw_minus_scalar_log2=(?P<pvw_minus_scalar_log2>[-0-9.inf]+) "
    r"max_allowed_log2_gap=(?P<max_allowed_log2_gap>[-0-9.]+)"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def bash(command: str, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def run_logged(command: str, log: Path, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    proc = bash(command, timeout=timeout)
    write_text_lf(log, "\n".join([
        f"command: {command}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize(proc.stdout).rstrip(),
        "--- stderr ---",
        sanitize(proc.stderr).rstrip(),
    ]).rstrip() + "\n")
    return proc


def extract_field(line: str, name: str) -> str:
    for token in line.split():
        if token.startswith(name + "="):
            return token.split("=", 1)[1].rstrip("x")
    return ""


def parse_float(text: str) -> float:
    if text in {"inf", "+inf"}:
        return math.inf
    if text == "-inf":
        return -math.inf
    return float(text)


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def stdev(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def ci95(values: List[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    m = mean(values)
    return m - 1.96 * stdev(values) / math.sqrt(len(values)), m + 1.96 * stdev(values) / math.sqrt(len(values))


def stage147_passes() -> bool:
    return any(
        row.get("gate") == "stage147_decision"
        and row.get("status") == "PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT"
        for row in read_csv(STAGE147_SUMMARY)
    )


def parse_perf_log(variant: str, run_idx: int, log: Path) -> Dict[str, str]:
    text = log.read_text(encoding="utf-8", errors="replace")
    correct = None
    summary = None
    for line in text.splitlines():
        m = CORRECT_RE.search(line)
        if m:
            correct = m.groupdict()
        m = BENCH_RE.search(line)
        if m:
            summary = m.groupdict()
    if correct is None or summary is None:
        return {"variant": variant, "run": str(run_idx), "status": "MISSING_LINES", "source_log": rel(log)}
    status = "PASS" if correct["status"] == "Pass" else "FAIL"
    return {
        "variant": variant,
        "run": str(run_idx),
        "status": status,
        "r": correct["r"],
        "h": correct["h"],
        "r_prec": correct["r_prec"],
        "pvw_avg_us": summary["pvw_avg_us"],
        "pvw_lane_avg_us": summary["pvw_lane_avg_us"],
        "scalar_repeated_avg_us": summary["scalar_repeated_avg_us"],
        "scalar_lane_avg_us": summary["scalar_lane_avg_us"],
        "speedup_vs_scalar_repeated": summary["speedup"],
        "source_log": rel(log),
    }


def run_perf() -> tuple[bool, List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    ok = True
    for config in PERF_CONFIGS:
        variant = config["variant"]
        build_log = OUT_DIR / f"perf_build_{variant}.log"
        build = run_logged(
            f"make clean >/dev/null 2>&1 || true && make {config['flags']} -j{JOBS}",
            build_log,
            timeout=900,
        )
        ok = ok and build.returncode == 0
        if build.returncode != 0:
            continue
        for run_idx in range(PERF_RUNS):
            log = OUT_DIR / f"perf_{variant}_run_{run_idx}.log"
            proc = run_logged("./main", log, timeout=1500)
            ok = ok and proc.returncode == 0
            rows.append(parse_perf_log(variant, run_idx, log))
    return ok, rows


def build_perf_comparison(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    wrapper = {int(row["run"]): row for row in rows if row.get("variant") == "wrapper_fused_from_dft_add" and row.get("status") == "PASS"}
    backend = {int(row["run"]): row for row in rows if row.get("variant") == "backend_from_dft_add" and row.get("status") == "PASS"}
    paired_runs = sorted(set(wrapper).intersection(backend))
    paired_speedups = [
        float(wrapper[idx]["pvw_lane_avg_us"]) / float(backend[idx]["pvw_lane_avg_us"])
        for idx in paired_runs
    ]
    wrapper_lane = [float(wrapper[idx]["pvw_lane_avg_us"]) for idx in paired_runs]
    backend_lane = [float(backend[idx]["pvw_lane_avg_us"]) for idx in paired_runs]
    wrapper_vs_scalar = [float(wrapper[idx]["speedup_vs_scalar_repeated"]) for idx in paired_runs]
    backend_vs_scalar = [float(backend[idx]["speedup_vs_scalar_repeated"]) for idx in paired_runs]
    low, high = ci95(paired_speedups)
    avg_speed = mean(paired_speedups)
    scalar_speed_ratio = mean(backend_vs_scalar) / mean(wrapper_vs_scalar) if mean(wrapper_vs_scalar) else 0.0
    if len(paired_runs) < PERF_RUNS:
        decision = "FAIL_STAGE148_PERF_MISSING_PAIRED_RUNS"
    elif low > 1.0 and min(paired_speedups) > 1.0 and avg_speed >= 1.01:
        decision = "PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE"
    elif avg_speed > 1.0 and min(paired_speedups) > 1.0:
        decision = "PASS_STAGE148_PERF_POSITIVE_CI_REVIEW"
    elif avg_speed > 1.0:
        decision = "WEAK_STAGE148_PERF_POSITIVE_MIN_OR_CI_REVIEW"
    else:
        decision = "NEUTRAL_STAGE148_PERF_BACKEND_NOT_STABLE"
    return [{
        "metric": "T_bootstrap_per_lane",
        "runs": str(len(paired_runs)),
        "wrapper_mean_pvw_lane_us": f"{mean(wrapper_lane):.3f}",
        "backend_mean_pvw_lane_us": f"{mean(backend_lane):.3f}",
        "backend_vs_wrapper_mean_speedup": f"{avg_speed:.6f}",
        "backend_vs_wrapper_min_speedup": f"{min(paired_speedups) if paired_speedups else 0.0:.6f}",
        "backend_vs_wrapper_ci95_low": f"{low:.6f}",
        "backend_vs_wrapper_ci95_high": f"{high:.6f}",
        "wrapper_mean_speedup_vs_scalar": f"{mean(wrapper_vs_scalar):.6f}",
        "backend_mean_speedup_vs_scalar": f"{mean(backend_vs_scalar):.6f}",
        "backend_incremental_speedup_vs_wrapper_scalar_speedup": f"{scalar_speed_ratio:.6f}",
        "decision": decision,
    }]


def parse_noise_log(seed: int, log: Path) -> Dict[str, str]:
    text = log.read_text(encoding="utf-8", errors="replace")
    gate_status = None
    summary = None
    for line in text.splitlines():
        m = NOISE_GATE_RE.search(line)
        if m:
            gate_status = m.group("status")
        m = NOISE_SUMMARY_RE.search(line)
        if m:
            summary = m.groupdict()
    if gate_status is None or summary is None:
        return {"r": str(R_VALUE), "seed": str(seed), "status": "MISSING_LINES", "source_log": rel(log)}
    return {
        "r": summary["r"],
        "seed": str(seed),
        "status": gate_status,
        "points": summary["points"],
        "pvw_failures": summary["pvw_failures"],
        "scalar_failures": summary["scalar_failures"],
        "pair_failures": summary["pair_failures"],
        "pvw_log2_sigma_torus": summary["pvw_log2_sigma_torus"],
        "scalar_log2_sigma_torus": summary["scalar_log2_sigma_torus"],
        "pair_log2_sigma_torus": summary["pair_log2_sigma_torus"],
        "pvw_minus_scalar_log2": summary["pvw_minus_scalar_log2"],
        "max_allowed_log2_gap": summary["max_allowed_log2_gap"],
        "source_log": rel(log),
    }


def aggregate_noise(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    gaps = [parse_float(row["pvw_minus_scalar_log2"]) for row in rows if row.get("status") == "Pass"]
    pvw_fail = sum(int(row.get("pvw_failures", "0")) for row in rows if row.get("pvw_failures"))
    scalar_fail = sum(int(row.get("scalar_failures", "0")) for row in rows if row.get("scalar_failures"))
    pair_fail = sum(int(row.get("pair_failures", "0")) for row in rows if row.get("pair_failures"))
    points = sum(int(row.get("points", "0")) for row in rows if row.get("points"))
    status = "PASS" if len(gaps) == NOISE_SEED_COUNT and pvw_fail == 0 and scalar_fail == 0 and pair_fail == 0 else "FAIL"
    return [{
        "r": str(R_VALUE),
        "seeds": str(len(gaps)),
        "points": str(points),
        "pvw_failures": str(pvw_fail),
        "scalar_failures": str(scalar_fail),
        "pair_failures": str(pair_fail),
        "min_pvw_minus_scalar_log2": f"{min(gaps) if gaps else 0.0:.3f}",
        "max_pvw_minus_scalar_log2": f"{max(gaps) if gaps else 0.0:.3f}",
        "avg_pvw_minus_scalar_log2": f"{mean(gaps):.6f}",
        "status": status,
    }]


def run_noise() -> tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    flags = (
        f"{BASE_FLAGS} SAB_PVW_BACKEND_FROM_DFT_ADD=true "
        "MOSFHET_DETERMINISTIC_RNG=true "
        f"SAB_PVW_NOISE_TEST=true SAB_PVW_NOISE_R={R_VALUE} "
        f"SAB_PVW_NOISE_TRIALS={NOISE_TRIALS} SAB_PVW_NOISE_MAX_LOG2_GAP=4.0"
    )
    build = run_logged(
        f"make clean >/dev/null 2>&1 || true && make {flags} -j{JOBS}",
        OUT_DIR / "noise_build_backend.log",
        timeout=900,
    )
    ok = build.returncode == 0
    if build.returncode == 0:
        for idx in range(NOISE_SEED_COUNT):
            seed = NOISE_START_SEED + idx
            log = OUT_DIR / f"noise_backend_seed_{seed}.log"
            proc = run_logged(f"MOSFHET_TEST_RNG_SEED={seed} ./main", log, timeout=1500)
            ok = ok and proc.returncode == 0
            rows.append(parse_noise_log(seed, log))
    agg = aggregate_noise(rows)
    return ok and all(row.get("status") == "Pass" for row in rows), rows, agg


def parse_resource_log(mode: str, run_idx: int, log: Path) -> Dict[str, str]:
    text = log.read_text(encoding="utf-8", errors="replace")
    gate = "Pass" if "SAB_PVW_RESOURCE target_full gate: Pass" in text else "Fail"
    key_line = ""
    keygen_line = ""
    rss_line = ""
    for line in text.splitlines():
        if "SAB_PVW_RESOURCE key_bytes target_full" in line:
            key_line = line
        if mode == "pvw" and "SAB_PVW_RESOURCE keygen target_full" in line and "mode=pvw" in line:
            keygen_line = line
        if mode == "scalar" and "SAB_PVW_RESOURCE keygen target_full" in line and "mode=scalar" in line:
            keygen_line = line
        if mode == "pvw" and "SAB_PVW_RESOURCE rss target_full" in line and "after_pvw_sab_keygen" in line:
            rss_line = line
        if mode == "scalar" and "SAB_PVW_RESOURCE rss target_full" in line and "after_scalar_repeated_sab_keygen" in line:
            rss_line = line
    max_rss = ""
    for line in text.splitlines():
        if "Maximum resident set size" in line:
            max_rss = line.split(":", 1)[1].strip()
            break
    if not key_line or not keygen_line or not rss_line:
        return {"run": str(run_idx), "mode": mode, "status": "MISSING_LINES", "source_log": rel(log)}
    if mode == "pvw":
        keygen = extract_field(keygen_line, "pvw_sab_keygen_us")
        lane_keygen = f"{float(keygen) / float(R_VALUE):.3f}" if keygen else ""
        key_bytes = extract_field(key_line, "pvw_estimated_key_bytes")
        ratio = extract_field(key_line, "pvw_vs_scalar_repeated_ratio")
    else:
        keygen = extract_field(keygen_line, "scalar_repeated_sab_keygen_us")
        lane_keygen = extract_field(keygen_line, "scalar_lane_avg_keygen_us")
        key_bytes = extract_field(key_line, "scalar_repeated_estimated_key_bytes")
        ratio = "1.000000"
    return {
        "run": str(run_idx),
        "mode": mode,
        "status": "PASS" if gate == "Pass" else "FAIL",
        "keygen_us": keygen,
        "keygen_lane_avg_us": lane_keygen,
        "estimated_key_bytes": key_bytes,
        "estimated_key_bytes_ratio_vs_scalar_repeated": ratio,
        "internal_vmhwm_kb": extract_field(rss_line, "vmhwm_kb"),
        "time_max_rss_kb": max_rss,
        "source_log": rel(log),
    }


def compare_resource(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    pvw_rows = [row for row in rows if row.get("mode") == "pvw" and row.get("status") == "PASS"]
    scalar_rows = [row for row in rows if row.get("mode") == "scalar" and row.get("status") == "PASS"]
    if not pvw_rows or not scalar_rows:
        return [{"runs": "0", "status": "FAIL"}]
    pvw_keygen = mean([float(row["keygen_lane_avg_us"]) for row in pvw_rows])
    scalar_keygen = mean([float(row["keygen_lane_avg_us"]) for row in scalar_rows])
    pvw_hwm = mean([float(row["internal_vmhwm_kb"]) for row in pvw_rows])
    scalar_hwm = mean([float(row["internal_vmhwm_kb"]) for row in scalar_rows])
    pvw_time_rss = mean([float(row["time_max_rss_kb"]) for row in pvw_rows if row.get("time_max_rss_kb")])
    scalar_time_rss = mean([float(row["time_max_rss_kb"]) for row in scalar_rows if row.get("time_max_rss_kb")])
    key_ratio = mean([float(row["estimated_key_bytes_ratio_vs_scalar_repeated"]) for row in pvw_rows])
    status = "PASS"
    if pvw_hwm / scalar_hwm > 1.25 if scalar_hwm else True:
        status = "REVIEW_RESOURCE_OVERHEAD"
    return [{
        "runs": str(min(len(pvw_rows), len(scalar_rows))),
        "pvw_key_bytes": pvw_rows[0]["estimated_key_bytes"],
        "scalar_key_bytes": scalar_rows[0]["estimated_key_bytes"],
        "key_bytes_ratio": f"{key_ratio:.6f}",
        "pvw_keygen_lane_avg_us": f"{pvw_keygen:.3f}",
        "scalar_keygen_lane_avg_us": f"{scalar_keygen:.3f}",
        "keygen_lane_ratio": f"{pvw_keygen / scalar_keygen if scalar_keygen else 0.0:.6f}",
        "pvw_vmhwm_kb": f"{pvw_hwm:.3f}",
        "scalar_vmhwm_kb": f"{scalar_hwm:.3f}",
        "vmhwm_ratio": f"{pvw_hwm / scalar_hwm if scalar_hwm else 0.0:.6f}",
        "pvw_time_max_rss_kb": f"{pvw_time_rss:.3f}",
        "scalar_time_max_rss_kb": f"{scalar_time_rss:.3f}",
        "time_max_rss_ratio": f"{pvw_time_rss / scalar_time_rss if scalar_time_rss else 0.0:.6f}",
        "status": status,
    }]


def run_resource() -> tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    flags = f"{BASE_FLAGS} SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_RESOURCE_TEST=true SAB_PVW_RESOURCE_R={R_VALUE}"
    build = run_logged(
        f"make clean >/dev/null 2>&1 || true && make {flags} -j{JOBS}",
        OUT_DIR / "resource_build_backend.log",
        timeout=900,
    )
    ok = build.returncode == 0
    if build.returncode == 0:
        for run_idx in range(RESOURCE_RUNS):
            for mode in ["pvw", "scalar"]:
                log = OUT_DIR / f"resource_{mode}_run_{run_idx}.log"
                proc = run_logged(
                    f"/usr/bin/time -v env SAB_PVW_RESOURCE_MODE={mode} ./main",
                    log,
                    timeout=1500,
                )
                ok = ok and proc.returncode == 0
                rows.append(parse_resource_log(mode, run_idx, log))
    comparison = compare_resource(rows)
    return ok and comparison and comparison[0]["status"] in {"PASS", "REVIEW_RESOURCE_OVERHEAD"}, rows, comparison


def build_summary(
    perf_ok: bool,
    perf_cmp: List[Dict[str, str]],
    noise_ok: bool,
    noise_agg: List[Dict[str, str]],
    resource_ok: bool,
    resource_cmp: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    stage147_ok = stage147_passes()
    perf_decision = perf_cmp[0]["decision"] if perf_cmp else "MISSING"
    noise_status = noise_agg[0]["status"] if noise_agg else "MISSING"
    resource_status = resource_cmp[0]["status"] if resource_cmp else "MISSING"
    perf_pass = perf_ok and perf_decision.startswith("PASS_STAGE148_PERF")
    noise_pass = noise_ok and noise_status == "PASS"
    resource_pass = resource_ok and resource_status in {"PASS", "REVIEW_RESOURCE_OVERHEAD"}

    if stage147_ok and perf_pass and noise_pass and resource_status == "PASS":
        decision = "PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE"
        next_action = "Proceed to Stage149 claim-boundary/final-package update; defaults still require a separate policy gate."
    elif stage147_ok and perf_pass and noise_pass and resource_pass:
        decision = "PASS_STAGE148_H14_R6_REPEATED_REFRESH_RESOURCE_REVIEW"
        next_action = "Review resource overhead before any promotion-policy update."
    elif stage147_ok and perf_cmp and perf_cmp[0]["backend_mean_speedup_vs_scalar"] and float(perf_cmp[0]["backend_mean_speedup_vs_scalar"]) > 1.0 and noise_pass:
        decision = "WEAK_STAGE148_H14_R6_REPEATED_REFRESH_BACKEND_POSITIVE_REVIEW_REQUIRED"
        next_action = "Do not promote; inspect backend-vs-wrapper variance and resource rows."
    else:
        decision = "FAIL_STAGE148_H14_R6_REPEATED_REFRESH"
        next_action = "Repair failed repeated, noise, or resource gate before relying on H14 r=6 current-head route."

    return [
        {
            "gate": "stage148_precondition",
            "status": "PASS" if stage147_ok else "FAIL",
            "metric": "stage147_decision",
            "value": "PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT",
            "evidence": rel(STAGE147_SUMMARY),
            "detail": "Stage148 refresh is valid only after Stage147 routes to current-head H14 r=6 backend.",
            "next_action": "",
        },
        {
            "gate": "stage148_perf",
            "status": perf_decision,
            "metric": "T_bootstrap/r",
            "value": perf_cmp[0]["backend_vs_wrapper_mean_speedup"] if perf_cmp else "",
            "evidence": f"{rel(PERF_RESULTS_CSV)}; {rel(PERF_COMPARISON_CSV)}",
            "detail": "Repeated current-head wrapper/backend A/B using amortized per-lane full-SAB time.",
            "next_action": "Do not promote if backend-vs-wrapper is not stable.",
        },
        {
            "gate": "stage148_noise",
            "status": noise_status,
            "metric": "seeds;failures",
            "value": (
                f"{noise_agg[0].get('seeds', '')};"
                f"{noise_agg[0].get('pvw_failures', '')}/"
                f"{noise_agg[0].get('scalar_failures', '')}/"
                f"{noise_agg[0].get('pair_failures', '')}"
            ) if noise_agg else "",
            "evidence": f"{rel(NOISE_RESULTS_CSV)}; {rel(NOISE_AGG_CSV)}",
            "detail": "Final-output noise/correctness for current-head H14 backend against scalar repeated outputs.",
            "next_action": "Do not promote if any failure is nonzero.",
        },
        {
            "gate": "stage148_resource",
            "status": resource_status,
            "metric": "key_bytes_ratio;vmhwm_ratio",
            "value": (
                f"{resource_cmp[0].get('key_bytes_ratio', '')};"
                f"{resource_cmp[0].get('vmhwm_ratio', '')}"
            ) if resource_cmp else "",
            "evidence": f"{rel(RESOURCE_RESULTS_CSV)}; {rel(RESOURCE_COMPARISON_CSV)}",
            "detail": "Resource/key snapshot for current-head H14 backend versus repeated scalar.",
            "next_action": "Report resource cost with any speed claim.",
        },
        {
            "gate": "stage148_decision",
            "status": decision,
            "metric": "policy_boundary",
            "value": "explicit_h14_r6_backend",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage148 records current-head repeated evidence; it does not change scalar/default behavior.",
            "next_action": next_action,
        },
    ]


def write_docs(
    summary_rows: List[Dict[str, str]],
    perf_cmp: List[Dict[str, str]],
    noise_agg: List[Dict[str, str]],
    resource_cmp: List[Dict[str, str]],
) -> None:
    decision = summary_rows[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage148 H14 r=6 Repeated Refresh Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Refresh the preferred explicit H14 r=6 backend route on current head with repeated complete-SAB, final-output noise, and resource evidence.",
        "",
        "## Metrics",
        "",
        "- Primary latency metric: `T_bootstrap/r` from `pvw_lane_avg_us`.",
        "- Same-backend comparison: backend FromDFT-add versus wrapper fused FromDFT-add.",
        "- Baseline comparison: backend complete-SAB speedup against repeated scalar SAB.",
        "- Correctness/noise: final-output multi-seed failure counts and noise gap.",
        "- Resource: key bytes, keygen lane time, internal VmHWM, and `/usr/bin/time` max RSS.",
        "",
        "## Boundary",
        "",
        "Stage148 can support a promotion-policy review for the explicit H14 r=6 backend path. It cannot change defaults or establish paper-level novelty by itself.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage148 H14 Repeated Statistical Model",
        "",
        "Date: 2026-07-03",
        "",
        "The repeated gate tests whether Stage147's current-head smoke survives process-level variance. The endpoint remains amortized MAT-RLWE/SAB throughput:",
        "",
        "```text",
        "T_lane = T_bootstrap / r",
        "speedup_backend_vs_wrapper = T_lane(wrapper) / T_lane(backend)",
        "speedup_backend_vs_scalar = T_scalar_repeated / T_backend",
        "```",
        "",
        "A backend route is promotable only if repeated full-SAB timing is positive and final-output noise/resource gates pass. A local materialization improvement or one-run smoke remains insufficient.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB H14 r=6 Repeated Refresh",
        "",
        "Date: 2026-07-03",
        "",
        "Focused route: r=6 MAT-RLWE/PVW lanes, active-buffer sparse schedule, r>4 fused MAT kernel, and backend FromDFT-add materialization.",
        "",
        "The path is explicit-only: `SAB_PVW_BACKEND_FROM_DFT_ADD=true` and `MAT_TRGSW_AVX512_RGT4_FUSED=true`. Scalar SAB and default PVW/MAT-SAB behavior remain unchanged.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage148 H14 r=6 Repeated Refresh",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Summary Gates",
        "",
        table(summary_rows, ["gate", "status", "metric", "value", "detail", "next_action"]),
        "",
        "## Performance",
        "",
        table(perf_cmp, PERF_COMPARE_FIELDS),
        "",
        "## Noise",
        "",
        table(noise_agg, NOISE_AGG_FIELDS),
        "",
        "## Resource",
        "",
        table(resource_cmp, RESOURCE_COMPARE_FIELDS),
        "",
        "## Interpretation",
        "",
        "Stage148 is a repeated evidence refresh for the explicit H14 r=6 backend path. It does not modify scalar/default behavior and does not by itself establish a final paper-level claim.",
    ]) + "\n")


def update_longform(summary_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    block = f"""
## Stage 148: H14 r=6 Repeated Refresh

Goal:

```text
Upgrade the Stage147 current-head H14 r=6 backend smoke into repeated
complete-SAB performance, final-output noise, and resource evidence.
```

Status:

```text
Completed. Stage148 records {decision}. It preserves scalar/default behavior
and keeps the endpoint at amortized `T_bootstrap/r`.
```
"""
    append_once(ROADMAP_MD, "## Stage 148: H14 r=6 Repeated Refresh", block)
    append_once(GOAL_MD, "Stage148 upgrades the H14 r=6 backend route", f"""
Stage148 upgrades the H14 r=6 backend route from Stage147 smoke to repeated
current-head performance plus final-output noise/resource evidence. It remains
an explicit-path research gate and does not change scalar/default behavior.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage148 as the H14 r=6 repeated refresh gate", f"""
52. Treat Stage148 as the H14 r=6 repeated refresh gate:
    `{decision}`. This stage records current-head repeated/noise/resource
    evidence for the explicit backend route; it is still not a default-path or
    paper-level novelty claim by itself.
""")
    append_once(HYPOTHESIS_YAML, "H72_h14_r6_repeated_refresh", f"""
  - id: H72_h14_r6_repeated_refresh
    statement: >
      The current-head H14 backend FromDFT-add r=6 route should retain stable
      full-SAB T_bootstrap/r improvement over the wrapper fused reference and
      repeated scalar SAB, while passing final-output noise and resource gates.
    mechanism: >
      Backend materialization reduces inverse DFT/add lifecycle cost without
      changing the sparse SAB schedule or scalar default path.
    status: stage148_h14_r6_repeated_refresh
    evidence: docs/stage148_h14_r6_repeated_refresh.md; experiments/stage148_h14_r6_repeated_refresh_plan.md; theory_checks/stage148_h14_repeated_stat_model.md; scripts/build_stage148_h14_r6_repeated_refresh.py; repro/stage148_h14_r6_repeated_refresh/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - repeated backend-vs-wrapper T_bootstrap/r is not stable
      - final-output noise has nonzero failures
      - resource/key overhead is not reported with performance
""")


def update_repro(summary_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    existing = read_csv(RUN_LOG)
    run_fields = list(existing[0].keys()) if existing else [
        "run_id", "date", "commit_or_state", "stage", "backend", "command",
        "params", "seed", "status", "summary", "artifacts",
    ]
    base_row = {field: "" for field in run_fields}
    base_row.update({
        "run_id": "stage148-h14-r6-repeated-refresh-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "Stage 148",
        "backend": "spqlios_avx512",
        "command": "python scripts/build_stage148_h14_r6_repeated_refresh.py",
        "params": f"PERF_RUNS={PERF_RUNS}; r={R_VALUE}; reps={BENCH_REPS}; noise_seeds={NOISE_SEED_COUNT}; resource_runs={RESOURCE_RUNS}; backend FromDFT-add",
        "seed": str(NOISE_START_SEED),
        "status": decision,
        "summary": "Current-head H14 r=6 backend repeated/noise/resource refresh.",
        "artifacts": rel(OUT_DIR),
    })
    run_row = {field: base_row.get(field, "") for field in run_fields}
    existing = [
        row for row in existing
        if row.get("run_id") != run_row["run_id"]
        and row.get("stage") != run_row["stage"]
    ]
    existing.append(run_row)
    write_csv(RUN_LOG, existing, run_fields)

    append_once(GLOBAL_MANIFEST, "stage148_h14_r6_repeated_refresh", f"""
- stage148_h14_r6_repeated_refresh: `{decision}`
  - `docs/stage148_h14_r6_repeated_refresh.md`
  - `experiments/stage148_h14_r6_repeated_refresh_plan.md`
  - `theory_checks/stage148_h14_repeated_stat_model.md`
  - `repro/stage148_h14_r6_repeated_refresh/`
""")
    append_once(CHECKLIST_MD, "Stage148 H14 r=6 repeated refresh pack", """
- [x] Stage148 H14 r=6 repeated/noise/resource refresh pack recorded.
""")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
        else:
            rows.append({
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    if PERF_RUNS < 2:
        raise SystemExit("STAGE148_PERF_RUNS must be >= 2")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    perf_ok, perf_rows = run_perf()
    perf_cmp = build_perf_comparison(perf_rows)
    write_csv(PERF_RESULTS_CSV, perf_rows, PERF_FIELDS)
    write_csv(PERF_COMPARISON_CSV, perf_cmp, PERF_COMPARE_FIELDS)

    noise_ok, noise_rows, noise_agg = run_noise()
    write_csv(NOISE_RESULTS_CSV, noise_rows, NOISE_FIELDS)
    write_csv(NOISE_AGG_CSV, noise_agg, NOISE_AGG_FIELDS)

    resource_ok, resource_rows, resource_cmp = run_resource()
    write_csv(RESOURCE_RESULTS_CSV, resource_rows, RESOURCE_FIELDS)
    write_csv(RESOURCE_COMPARISON_CSV, resource_cmp, RESOURCE_COMPARE_FIELDS)

    run_logged("make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=60)

    summary_rows = build_summary(perf_ok, perf_cmp, noise_ok, noise_agg, resource_ok, resource_cmp)
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    write_docs(summary_rows, perf_cmp, noise_agg, resource_cmp)
    update_longform(summary_rows)
    update_repro(summary_rows)

    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD,
        PERF_RESULTS_CSV, PERF_COMPARISON_CSV,
        NOISE_RESULTS_CSV, NOISE_AGG_CSV,
        RESOURCE_RESULTS_CSV, RESOURCE_COMPARISON_CSV,
        SUMMARY_CSV,
        OUT_DIR / "perf_build_wrapper_fused_from_dft_add.log",
        OUT_DIR / "perf_build_backend_from_dft_add.log",
        OUT_DIR / "noise_build_backend.log",
        OUT_DIR / "resource_build_backend.log",
        OUT_DIR / "cleanup.log",
        ARTIFACT_INDEX,
        Path(__file__).resolve(),
    ]
    for variant in ["wrapper_fused_from_dft_add", "backend_from_dft_add"]:
        for run_idx in range(PERF_RUNS):
            artifacts.append(OUT_DIR / f"perf_{variant}_run_{run_idx}.log")
    for idx in range(NOISE_SEED_COUNT):
        artifacts.append(OUT_DIR / f"noise_backend_seed_{NOISE_START_SEED + idx}.log")
    for run_idx in range(RESOURCE_RUNS):
        for mode in ["pvw", "scalar"]:
            artifacts.append(OUT_DIR / f"resource_{mode}_run_{run_idx}.log")
    write_artifact_index(artifacts)
    print(f"Stage148 H14 r=6 repeated refresh: {summary_rows[-1]['status']}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if summary_rows[-1]["status"].startswith(("PASS_", "WEAK_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
