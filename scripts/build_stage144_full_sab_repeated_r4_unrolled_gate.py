#!/usr/bin/env python3
"""Build Stage144 repeated full-SAB r=4 r4-unrolled gate."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage144_full_sab_repeated_r4_unrolled_gate"

PERF_RESULTS_CSV = OUT_DIR / "perf_results.csv"
PERF_COMPARISON_CSV = OUT_DIR / "perf_comparison.csv"
NOISE_RESULTS_CSV = OUT_DIR / "noise_results.csv"
NOISE_AGG_CSV = OUT_DIR / "noise_aggregate.csv"
RESOURCE_RESULTS_CSV = OUT_DIR / "resource_results.csv"
RESOURCE_COMPARISON_CSV = OUT_DIR / "resource_comparison.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage144_full_sab_repeated_r4_unrolled_gate.md"
PLAN_MD = ROOT / "experiments" / "stage144_full_sab_repeated_r4_unrolled_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage144_repeated_full_sab_stat_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_r4_unrolled_repeated_gate.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

PERF_RUNS = int(os.environ.get("STAGE144_PERF_RUNS", "3"))
BENCH_REPS = int(os.environ.get("SAB_PVW_BENCH_REPS", "1"))
NOISE_SEED_COUNT = int(os.environ.get("STAGE144_NOISE_SEED_COUNT", "3"))
NOISE_START_SEED = int(os.environ.get("STAGE144_NOISE_START_SEED", "6869440"))
NOISE_TRIALS = int(os.environ.get("STAGE144_NOISE_TRIALS", "1"))
RESOURCE_RUNS = int(os.environ.get("STAGE144_RESOURCE_RUNS", "1"))
JOBS = int(os.environ.get("JOBS", "8"))

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true KEY=BINARY PARAM=SET_2_3_2048"
)
PERF_CONFIGS = [
    {
        "variant": "generic_active",
        "flags": f"{BASE_FLAGS} SAB_PVW_BENCH=true SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS={BENCH_REPS}",
    },
    {
        "variant": "r4_unrolled_active",
        "flags": f"{BASE_FLAGS} MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true SAB_PVW_BENCH=true SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS={BENCH_REPS}",
    },
]

PERF_FIELDS = [
    "variant", "run", "status", "r", "h", "r_prec", "pvw_avg_us",
    "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us",
    "speedup_vs_scalar_repeated", "source_log",
]
PERF_COMPARE_FIELDS = [
    "metric", "runs", "generic_mean_pvw_lane_us",
    "r4_mean_pvw_lane_us", "r4_vs_generic_mean_speedup",
    "r4_vs_generic_min_speedup", "r4_vs_generic_ci95_low",
    "r4_vs_generic_ci95_high", "generic_mean_speedup_vs_scalar",
    "r4_mean_speedup_vs_scalar", "r4_incremental_speedup_vs_generic_scalar_speedup",
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
    "vmhwm_ratio", "status",
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


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def parse_float(text: str) -> float:
    if text in {"inf", "+inf"}:
        return math.inf
    if text == "-inf":
        return -math.inf
    return float(text)


def mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def stdev(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def ci95(values: List[float]) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (values[0], values[0])
    tcrit = {
        2: 12.706,
        3: 4.303,
        4: 3.182,
        5: 2.776,
        6: 2.571,
        7: 2.447,
        8: 2.365,
        9: 2.306,
        10: 2.262,
    }.get(len(values), 1.96)
    half = tcrit * stdev(values) / math.sqrt(len(values))
    avg = mean(values)
    return avg - half, avg + half


def extract_field(line: str, name: str) -> str:
    for token in line.split():
        if token.startswith(name + "="):
            return token.split("=", 1)[1].rstrip("x")
    return ""


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
            proc = run_logged("./main", log, timeout=900)
            ok = ok and proc.returncode == 0
            rows.append(parse_perf_log(variant, run_idx, log))
    return ok, rows


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


def build_perf_comparison(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    generic = {int(row["run"]): row for row in rows if row["variant"] == "generic_active" and row["status"] == "PASS"}
    r4 = {int(row["run"]): row for row in rows if row["variant"] == "r4_unrolled_active" and row["status"] == "PASS"}
    paired_runs = sorted(set(generic).intersection(r4))
    paired_speedups = [
        float(generic[idx]["pvw_lane_avg_us"]) / float(r4[idx]["pvw_lane_avg_us"])
        for idx in paired_runs
    ]
    generic_lane = [float(generic[idx]["pvw_lane_avg_us"]) for idx in paired_runs]
    r4_lane = [float(r4[idx]["pvw_lane_avg_us"]) for idx in paired_runs]
    generic_vs_scalar = [float(generic[idx]["speedup_vs_scalar_repeated"]) for idx in paired_runs]
    r4_vs_scalar = [float(r4[idx]["speedup_vs_scalar_repeated"]) for idx in paired_runs]
    low, high = ci95(paired_speedups)
    avg_speed = mean(paired_speedups)
    scalar_speed_ratio = mean(r4_vs_scalar) / mean(generic_vs_scalar) if mean(generic_vs_scalar) else 0.0
    if len(paired_runs) < PERF_RUNS:
        decision = "FAIL_STAGE144_PERF_MISSING_PAIRED_RUNS"
    elif low > 1.0 and avg_speed >= 1.01:
        decision = "PASS_STAGE144_PERF_REPEATED_R4_UNROLLED_PROMOTION_CANDIDATE"
    elif avg_speed > 1.0:
        decision = "WEAK_STAGE144_PERF_POSITIVE_BUT_CI_CROSSES_ONE"
    else:
        decision = "NEUTRAL_STAGE144_PERF_R4_UNROLLED_NOT_STABLE"
    return [{
        "metric": "T_bootstrap_per_lane",
        "runs": str(len(paired_runs)),
        "generic_mean_pvw_lane_us": f"{mean(generic_lane):.3f}",
        "r4_mean_pvw_lane_us": f"{mean(r4_lane):.3f}",
        "r4_vs_generic_mean_speedup": f"{avg_speed:.6f}",
        "r4_vs_generic_min_speedup": f"{min(paired_speedups) if paired_speedups else 0.0:.6f}",
        "r4_vs_generic_ci95_low": f"{low:.6f}",
        "r4_vs_generic_ci95_high": f"{high:.6f}",
        "generic_mean_speedup_vs_scalar": f"{mean(generic_vs_scalar):.6f}",
        "r4_mean_speedup_vs_scalar": f"{mean(r4_vs_scalar):.6f}",
        "r4_incremental_speedup_vs_generic_scalar_speedup": f"{scalar_speed_ratio:.6f}",
        "decision": decision,
    }]


def run_noise() -> tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    flags = (
        f"{BASE_FLAGS} MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true "
        "MOSFHET_DETERMINISTIC_RNG=true "
        f"SAB_PVW_NOISE_TEST=true SAB_PVW_NOISE_R=4 "
        f"SAB_PVW_NOISE_TRIALS={NOISE_TRIALS} SAB_PVW_NOISE_MAX_LOG2_GAP=4.0"
    )
    build = run_logged(
        f"make clean >/dev/null 2>&1 || true && make {flags} -j{JOBS}",
        OUT_DIR / "noise_build_r4_unrolled.log",
        timeout=900,
    )
    ok = build.returncode == 0
    if build.returncode == 0:
        for idx in range(NOISE_SEED_COUNT):
            seed = NOISE_START_SEED + idx
            log = OUT_DIR / f"noise_r4_unrolled_seed_{seed}.log"
            proc = run_logged(f"MOSFHET_TEST_RNG_SEED={seed} ./main", log, timeout=1200)
            ok = ok and proc.returncode == 0
            rows.append(parse_noise_log(seed, log))
    agg = aggregate_noise(rows)
    return ok and all(row.get("status") == "Pass" for row in rows), rows, agg


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
        return {"r": "4", "seed": str(seed), "status": "MISSING_LINES", "source_log": rel(log)}
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
        "r": "4",
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


def run_resource() -> tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    flags = (
        f"{BASE_FLAGS} MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true "
        "SAB_PVW_RESOURCE_TEST=true SAB_PVW_RESOURCE_R=4"
    )
    build = run_logged(
        f"make clean >/dev/null 2>&1 || true && make {flags} -j{JOBS}",
        OUT_DIR / "resource_build_r4_unrolled.log",
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
                    timeout=1200,
                )
                ok = ok and proc.returncode == 0
                rows.append(parse_resource_log(mode, run_idx, log))
    comparison = compare_resource(rows)
    return ok and comparison and comparison[0]["status"] == "PASS", rows, comparison


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
        lane_keygen = f"{float(keygen) / 4.0:.3f}" if keygen else ""
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
    pvw_rows = [row for row in rows if row["mode"] == "pvw" and row["status"] == "PASS"]
    scalar_rows = [row for row in rows if row["mode"] == "scalar" and row["status"] == "PASS"]
    if not pvw_rows or not scalar_rows:
        return [{"runs": "0", "status": "FAIL"}]
    pvw_keygen = mean([float(row["keygen_lane_avg_us"]) for row in pvw_rows])
    scalar_keygen = mean([float(row["keygen_lane_avg_us"]) for row in scalar_rows])
    pvw_hwm = mean([float(row["internal_vmhwm_kb"]) for row in pvw_rows])
    scalar_hwm = mean([float(row["internal_vmhwm_kb"]) for row in scalar_rows])
    return [{
        "runs": str(min(len(pvw_rows), len(scalar_rows))),
        "pvw_key_bytes": pvw_rows[-1]["estimated_key_bytes"],
        "scalar_key_bytes": scalar_rows[-1]["estimated_key_bytes"],
        "key_bytes_ratio": pvw_rows[-1]["estimated_key_bytes_ratio_vs_scalar_repeated"],
        "pvw_keygen_lane_avg_us": f"{pvw_keygen:.3f}",
        "scalar_keygen_lane_avg_us": f"{scalar_keygen:.3f}",
        "keygen_lane_ratio": f"{pvw_keygen / scalar_keygen if scalar_keygen else 0.0:.6f}",
        "pvw_vmhwm_kb": f"{pvw_hwm:.3f}",
        "scalar_vmhwm_kb": f"{scalar_hwm:.3f}",
        "vmhwm_ratio": f"{pvw_hwm / scalar_hwm if scalar_hwm else 0.0:.6f}",
        "status": "PASS",
    }]


def build_summary(perf_ok: bool, perf_cmp: List[Dict[str, str]],
    noise_ok: bool, noise_agg: List[Dict[str, str]],
    resource_ok: bool, resource_cmp: List[Dict[str, str]]) -> List[Dict[str, str]]:
    perf_decision = perf_cmp[0]["decision"] if perf_cmp else "FAIL_STAGE144_PERF_MISSING"
    if perf_decision.startswith("PASS_") and noise_ok and resource_ok:
        final = "PASS_STAGE144_R4_UNROLLED_REPEATED_NOISE_RESOURCE_PROMOTION_CANDIDATE"
    elif perf_decision.startswith("WEAK_") and noise_ok and resource_ok:
        final = "WEAK_STAGE144_R4_UNROLLED_POSITIVE_STATS_REVIEW_REQUIRED"
    elif perf_decision.startswith("NEUTRAL_") and noise_ok and resource_ok:
        final = "NEUTRAL_STAGE144_R4_UNROLLED_NOT_PROMOTED"
    else:
        final = "FAIL_STAGE144_R4_UNROLLED_GATE"
    return [
        {"gate": "stage144_perf", "status": perf_decision, "metric": "T_bootstrap/r", "value": perf_cmp[0].get("r4_vs_generic_mean_speedup", "") if perf_cmp else "", "evidence": f"{rel(PERF_RESULTS_CSV)}; {rel(PERF_COMPARISON_CSV)}", "detail": f"Repeated full SAB A/B with {PERF_RUNS} paired runs.", "next_action": "Do not promote if this is not PASS or WEAK."},
        {"gate": "stage144_noise", "status": "PASS" if noise_ok else "FAIL", "metric": "seeds;failures", "value": f"{noise_agg[0].get('seeds', '')};{noise_agg[0].get('pvw_failures', '')}/{noise_agg[0].get('scalar_failures', '')}/{noise_agg[0].get('pair_failures', '')}" if noise_agg else "", "evidence": f"{rel(NOISE_RESULTS_CSV)}; {rel(NOISE_AGG_CSV)}", "detail": "Final-output noise for r4-unrolled candidate against scalar repeated outputs.", "next_action": "Do not promote if failures are nonzero."},
        {"gate": "stage144_resource", "status": "PASS" if resource_ok else "FAIL", "metric": "key_bytes_ratio;vmhwm_ratio", "value": f"{resource_cmp[0].get('key_bytes_ratio', '')};{resource_cmp[0].get('vmhwm_ratio', '')}" if resource_cmp else "", "evidence": f"{rel(RESOURCE_RESULTS_CSV)}; {rel(RESOURCE_COMPARISON_CSV)}", "detail": "Resource/key snapshot for r4-unrolled candidate.", "next_action": "Report resource cost with any speed claim."},
        {"gate": "stage144_decision", "status": final, "metric": "promotion_policy", "value": "", "evidence": rel(SUMMARY_CSV), "detail": "Stage144 converts Stage143 smoke into repeated/noise/resource evidence.", "next_action": "Stage145 should decide explicit-flag promotion policy and update final claim package."},
    ]


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip() + "\n")


def write_docs(summary_rows: List[Dict[str, str]], perf_cmp: List[Dict[str, str]],
    noise_agg: List[Dict[str, str]], resource_cmp: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage144 Full SAB Repeated r4-Unrolled Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Turn Stage143 one-run smoke into a repeated complete-SAB A/B gate for the r=4 r4-unrolled AVX512 path.",
        "",
        "## Primary Endpoint",
        "",
        "`T_bootstrap/r`, measured as `pvw_lane_avg_us` for generic active PVW and r4-unrolled active PVW.",
        "",
        "## Gates",
        "",
        "- repeated full-SAB correctness and timing;",
        "- r4-unrolled final-output noise with multiple deterministic seeds;",
        "- resource/key snapshot against repeated scalar SAB;",
        "- promote only if speed, noise, and resource gates are all acceptable.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage144 Repeated Full-SAB Statistical Model",
        "",
        "Date: 2026-07-03",
        "",
        "The tested claim is scoped to implementation-level MAT-aware AVX512 improvement inside the already valid PVW/MAT-SAB full bootstrapping path.",
        "",
        "For each paired run index `i`:",
        "",
        "```text",
        "S_i = T_lane(generic_active, i) / T_lane(r4_unrolled_active, i)",
        "T_lane = T_complete_bootstrap(PVW/MAT-SAB, r=4) / 4",
        "```",
        "",
        "Stage144 reports mean/min and a t-based 95% interval over paired `S_i`. The interval is descriptive because the run count is still small; it is adequate for promote-candidate routing, not for paper-final claims.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# V144: r4-Unrolled Repeated Full-SAB Candidate",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB.",
        "- Focused module: complete r=4 SAB bootstrapping with active-buffer schedule and r4-unrolled MAT external product.",
        "- Optimization target: amortized `T_bootstrap/r`.",
        "- Status labels: `[repeated gate]`, `[noise/resource checked]`, `[promotion policy pending]`.",
        "- Main hypothesis: the Stage142 r4-unrolled closed full-MAT kernel yields a stable complete-SAB per-lane benefit over generic active PVW without correctness, noise, or resource regressions that would invalidate the path.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage144 Full SAB Repeated r4-Unrolled Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Gates",
        "",
        table(summary_rows, ["gate", "status", "metric", "value", "detail"]),
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
        "Stage144 uses the correct MAT-RLWE amortized endpoint. It still remains an explicit-flag candidate until a separate promotion-policy step updates defaults or final claim wording.",
    ]) + "\n")


def update_longform_docs(summary_rows: List[Dict[str, str]], perf_cmp: List[Dict[str, str]],
    noise_agg: List[Dict[str, str]], resource_cmp: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    perf = perf_cmp[0]
    noise = noise_agg[0]
    resource = resource_cmp[0]
    stage_block = f"""
## Stage 144: Full SAB Repeated r4-Unrolled Gate

Goal:

```text
Promote Stage143 from one-run smoke to repeated complete-SAB A/B with
correctness, final-output noise, and resource evidence for the explicit
r4-unrolled AVX512 candidate.
```

Status:

```text
Completed. Stage144 records {decision}. The primary endpoint is
T_bootstrap/r. r4-unrolled versus generic active PVW has mean paired speedup
{perf['r4_vs_generic_mean_speedup']}, min {perf['r4_vs_generic_min_speedup']},
and CI95 [{perf['r4_vs_generic_ci95_low']}, {perf['r4_vs_generic_ci95_high']}].
Noise status is {noise['status']} across {noise['seeds']} seeds. Resource
key/RSS ratios are {resource['key_bytes_ratio']} and {resource['vmhwm_ratio']}.
```
"""
    append_once(ROADMAP_MD, "## Stage 144: Full SAB Repeated r4-Unrolled Gate", stage_block)
    goal_block = f"""
Stage144 upgrades the r4-unrolled AVX512 path from smoke evidence to repeated
complete-SAB/noise/resource evidence under the amortized `T_bootstrap/r`
metric. It does not change scalar/default behavior.
"""
    append_once(GOAL_MD, "Stage144 upgrades the r4-unrolled AVX512 path", goal_block)
    current_block = f"""
48. Treat Stage144 as the repeated complete-SAB gate for the r=4 r4-unrolled
    candidate: `{decision}`. Primary endpoint `T_bootstrap/r` gives mean paired
    r4/generic speedup {perf['r4_vs_generic_mean_speedup']} with CI95
    [{perf['r4_vs_generic_ci95_low']}, {perf['r4_vs_generic_ci95_high']}].
    Noise/resource are recorded in the Stage144 repro pack.
"""
    append_once(CURRENT_GOAL_MD, "48. Treat Stage144 as the repeated complete-SAB gate", current_block)


def upsert_hypothesis(summary_rows: List[Dict[str, str]], perf_cmp: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    perf = perf_cmp[0]
    block = f"""  - id: H68_r4_unrolled_repeated_full_sab_gate
    statement: >
      The Stage142 r4-unrolled closed full-MAT AVX512 kernel should provide a
      stable complete-SAB amortized speedup for r=4 over generic active PVW
      when measured as T_bootstrap/r.
    mechanism: >
      The r4-unrolled kernel reduces the closed full-MAT external-product cost
      without changing the PVW_TMLWE state invariant; Stage144 tests whether
      this kernel-level gain survives full SAB schedule overhead.
    status: stage144_full_sab_repeated_r4_unrolled_gate
    evidence: docs/stage144_full_sab_repeated_r4_unrolled_gate.md; experiments/stage144_full_sab_repeated_r4_unrolled_gate_plan.md; theory_checks/stage144_repeated_full_sab_stat_model.md; algorithm_variants/mat_rlwe_sab_r4_unrolled_repeated_gate.md; scripts/build_stage144_full_sab_repeated_r4_unrolled_gate.py; repro/stage144_full_sab_repeated_r4_unrolled_gate/summary.csv; repro/stage144_full_sab_repeated_r4_unrolled_gate/perf_comparison.csv; repro/stage144_full_sab_repeated_r4_unrolled_gate/noise_aggregate.csv; repro/stage144_full_sab_repeated_r4_unrolled_gate/resource_comparison.csv; repro/stage144_full_sab_repeated_r4_unrolled_gate/artifact_index.csv
    current_decision: >
      Stage144 records {decision}. Mean paired r4/generic complete-SAB
      per-lane speedup is {perf['r4_vs_generic_mean_speedup']} with CI95
      [{perf['r4_vs_generic_ci95_low']}, {perf['r4_vs_generic_ci95_high']}].
    failure_criteria:
      - complete SAB correctness fails in any run
      - paired speedup is not stable
      - final-output noise has nonzero failures
      - resource overhead is not reported with speed
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8") if HYPOTHESIS_YAML.exists() else "hypotheses:\n"
    marker = "  - id: H68_r4_unrolled_repeated_full_sab_gate"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def upsert_run_log(summary_rows: List[Dict[str, str]]) -> None:
    fields = ["run_id", "date", "commit_or_state", "stage", "backend", "command", "params", "seed", "status", "summary", "artifacts"]
    run_id = "stage144-full-sab-r4-unrolled-repeated-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = stage_artifacts()
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 144",
        "backend": "MOSFHET FFT_LIB=spqlios_avx512",
        "command": "python scripts/build_stage144_full_sab_repeated_r4_unrolled_gate.py",
        "params": f"PERF_RUNS={PERF_RUNS}; BENCH_REPS={BENCH_REPS}; NOISE_SEED_COUNT={NOISE_SEED_COUNT}; NOISE_TRIALS={NOISE_TRIALS}; RESOURCE_RUNS={RESOURCE_RUNS}; r=4; active_buffer=true; r4_unrolled=true",
        "seed": f"noise_start={NOISE_START_SEED}",
        "status": summary_rows[-1]["status"],
        "summary": "Repeated full-SAB A/B plus final-output noise and resource gates for r4-unrolled candidate.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 144 Full SAB Repeated r4-Unrolled Gate

- `docs/stage144_full_sab_repeated_r4_unrolled_gate.md`
- `experiments/stage144_full_sab_repeated_r4_unrolled_gate_plan.md`
- `theory_checks/stage144_repeated_full_sab_stat_model.md`
- `algorithm_variants/mat_rlwe_sab_r4_unrolled_repeated_gate.md`
- `scripts/build_stage144_full_sab_repeated_r4_unrolled_gate.py`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/summary.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/perf_results.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/perf_comparison.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/noise_results.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/noise_aggregate.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/resource_results.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/resource_comparison.csv`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/*.log`
- `repro/stage144_full_sab_repeated_r4_unrolled_gate/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 144 Full SAB Repeated r4-Unrolled Gate", block)


def update_checklist(summary_rows: List[Dict[str, str]]) -> None:
    text = CHECKLIST_MD.read_text(encoding="utf-8") if CHECKLIST_MD.exists() else ""
    old = "- [ ] Run Stage144 repeated complete-SAB A/B for r=4 generic-active versus r4-unrolled-active with confidence intervals, noise/resource checks, and final promote/neutral/reject decision."
    new = f"- [x] Run Stage144 repeated complete-SAB A/B for r=4 generic-active versus r4-unrolled-active with confidence intervals, noise/resource checks, and decision `{summary_rows[-1]['status']}`."
    if old in text:
        text = text.replace(old, new)
    elif new not in text:
        text += "\n" + new + "\n"
    write_text_lf(CHECKLIST_MD, text)


def stage_artifacts() -> List[Path]:
    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV,
        PERF_RESULTS_CSV, PERF_COMPARISON_CSV, NOISE_RESULTS_CSV,
        NOISE_AGG_CSV, RESOURCE_RESULTS_CSV, RESOURCE_COMPARISON_CSV,
        ARTIFACT_INDEX, Path(__file__).resolve(),
    ]
    artifacts.extend(sorted(OUT_DIR.glob("*.log")))
    return artifacts


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
            continue
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    if PERF_RUNS < 2:
        raise SystemExit("STAGE144_PERF_RUNS must be >= 2")
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

    summary_rows = build_summary(perf_ok, perf_cmp, noise_ok, noise_agg,
        resource_ok, resource_cmp)
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    write_docs(summary_rows, perf_cmp, noise_agg, resource_cmp)
    update_longform_docs(summary_rows, perf_cmp, noise_agg, resource_cmp)
    upsert_hypothesis(summary_rows, perf_cmp)
    upsert_run_log(summary_rows)
    upsert_global_manifest()
    update_checklist(summary_rows)
    write_artifact_index(stage_artifacts())
    print(f"Stage144 full SAB repeated r4-unrolled gate: {summary_rows[-1]['status']}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not summary_rows[-1]["status"].startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
