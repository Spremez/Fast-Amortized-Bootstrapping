#!/usr/bin/env python3
"""Stage159: repeated/noise/resource gate for sub-decompose fusion."""

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
OUT_DIR = ROOT / "repro" / "stage159_sub_decomp_fusion_repeated_gate"

PERF_RESULTS_CSV = OUT_DIR / "perf_results.csv"
PERF_COMPARISON_CSV = OUT_DIR / "perf_comparison.csv"
NOISE_RESULTS_CSV = OUT_DIR / "noise_results.csv"
NOISE_AGG_CSV = OUT_DIR / "noise_aggregate.csv"
RESOURCE_RESULTS_CSV = OUT_DIR / "resource_results.csv"
RESOURCE_COMPARISON_CSV = OUT_DIR / "resource_comparison.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage159_sub_decomp_fusion_repeated_gate.md"
PLAN_MD = ROOT / "experiments" / "stage159_sub_decomp_fusion_repeated_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage159_sub_decomp_fusion_stat_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_sub_decomp_fusion_repeated.md"

RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"

R_VALUE = int(os.environ.get("STAGE159_R", "6"))
PERF_RUNS = int(os.environ.get("STAGE159_PERF_RUNS", "3"))
BENCH_REPS = int(os.environ.get("SAB_PVW_BENCH_REPS", "1"))
NOISE_SEED_COUNT = int(os.environ.get("STAGE159_NOISE_SEED_COUNT", "3"))
NOISE_START_SEED = int(os.environ.get("STAGE159_NOISE_START_SEED", "6869590"))
NOISE_TRIALS = int(os.environ.get("STAGE159_NOISE_TRIALS", "1"))
RESOURCE_RUNS = int(os.environ.get("STAGE159_RESOURCE_RUNS", "1"))
MAKE_JOBS = os.environ.get("STAGE159_JOBS", "$(nproc)")

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true"
)
CONTROL_FLAGS = (
    f"{BASE_FLAGS} SAB_PVW_BENCH=true SAB_PVW_BENCH_R={R_VALUE} "
    f"SAB_PVW_BENCH_REPS={BENCH_REPS}"
)
FUSION_FLAGS = (
    f"{BASE_FLAGS} SAB_PVW_SUB_DECOMP_FUSION=true "
    f"SAB_PVW_BENCH=true SAB_PVW_BENCH_R={R_VALUE} "
    f"SAB_PVW_BENCH_REPS={BENCH_REPS}"
)

PERF_CONFIGS = [
    {"variant": "control_h14_r6_backend", "flags": CONTROL_FLAGS},
    {"variant": "sub_decomp_fusion_h14_r6_backend", "flags": FUSION_FLAGS},
]

PERF_FIELDS = [
    "variant", "run", "status", "r", "h", "r_prec", "pvw_avg_us",
    "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us",
    "speedup_vs_scalar_repeated", "source_log",
]
PERF_COMPARE_FIELDS = [
    "metric", "runs", "control_mean_pvw_lane_us",
    "fusion_mean_pvw_lane_us", "fusion_over_control_mean_speedup",
    "fusion_over_control_min_speedup", "fusion_over_control_ci95_low",
    "fusion_over_control_ci95_high", "control_mean_speedup_vs_scalar",
    "fusion_mean_speedup_vs_scalar",
    "fusion_incremental_speedup_vs_control_scalar_speedup", "decision",
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
SUMMARY_FIELDS = [
    "gate", "status", "metric", "value", "evidence", "detail",
    "next_action",
]

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
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    clean = "".join(ch if ch in "\n\t" or 32 <= ord(ch) < 127 else "?" for ch in text)
    return "\n".join(line.rstrip() for line in clean.splitlines()).rstrip() + "\n"


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
    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join(["---"] * len(fields)) + " |",
    ]
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
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def wsl_repo() -> str:
    drive = ROOT.drive.rstrip(":").lower()
    rest = ROOT.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{rest}"


def run_wsl(command: str, log: Path, timeout: int = 1800) -> int:
    bash_cmd = f"cd {wsl_repo()} && {command}"
    print(f"[stage159] {command}", flush=True)
    proc = subprocess.run(
        ["wsl", "bash", "-lc", bash_cmd],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    output = proc.stdout.decode("utf-8", errors="ignore")
    write_text_lf(log, sanitize("\n".join([
        f"command: {command}",
        f"returncode: {proc.returncode}",
        "--- output ---",
        output,
    ])))
    return proc.returncode


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


def mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def stdev(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def ci95(values: List[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    m = mean(values)
    return m - 1.96 * stdev(values) / math.sqrt(len(values)), m + 1.96 * stdev(values) / math.sqrt(len(values))


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
        return {
            "variant": variant,
            "run": str(run_idx),
            "status": "MISSING_LINES",
            "source_log": rel(log),
        }
    return {
        "variant": variant,
        "run": str(run_idx),
        "status": "PASS" if correct["status"] == "Pass" else "FAIL",
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


def run_perf() -> Tuple[bool, List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    ok = True
    for config in PERF_CONFIGS:
        variant = config["variant"]
        vdir = OUT_DIR / variant
        build_log = vdir / "build.log"
        build_rc = run_wsl(
            f"make clean >/dev/null 2>&1 || true && make {config['flags']} -j{MAKE_JOBS}",
            build_log,
            timeout=1200,
        )
        ok = ok and build_rc == 0
        if build_rc != 0:
            continue
        for run_idx in range(PERF_RUNS):
            log = vdir / f"run_{run_idx}.log"
            rc = run_wsl("stdbuf -o0 ./main", log, timeout=1800)
            ok = ok and rc == 0
            rows.append(parse_perf_log(variant, run_idx, log))
    return ok, rows


def build_perf_comparison(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    control = {
        int(row["run"]): row
        for row in rows
        if row.get("variant") == "control_h14_r6_backend" and row.get("status") == "PASS"
    }
    fusion = {
        int(row["run"]): row
        for row in rows
        if row.get("variant") == "sub_decomp_fusion_h14_r6_backend" and row.get("status") == "PASS"
    }
    paired_runs = sorted(set(control).intersection(fusion))
    paired_speedups = [
        float(control[idx]["pvw_lane_avg_us"]) / float(fusion[idx]["pvw_lane_avg_us"])
        for idx in paired_runs
    ]
    control_lane = [float(control[idx]["pvw_lane_avg_us"]) for idx in paired_runs]
    fusion_lane = [float(fusion[idx]["pvw_lane_avg_us"]) for idx in paired_runs]
    control_vs_scalar = [float(control[idx]["speedup_vs_scalar_repeated"]) for idx in paired_runs]
    fusion_vs_scalar = [float(fusion[idx]["speedup_vs_scalar_repeated"]) for idx in paired_runs]
    low, high = ci95(paired_speedups)
    avg_speed = mean(paired_speedups)
    min_speed = min(paired_speedups) if paired_speedups else 0.0
    scalar_speed_ratio = mean(fusion_vs_scalar) / mean(control_vs_scalar) if mean(control_vs_scalar) else 0.0

    if len(paired_runs) < PERF_RUNS:
        decision = "FAIL_STAGE159_PERF_MISSING_PAIRED_RUNS"
    elif min_speed > 1.0 and avg_speed >= 1.02:
        decision = "PASS_STAGE159_PERF_SUB_DECOMP_FUSION_REPEATED_POSITIVE"
    elif avg_speed > 1.0:
        decision = "WEAK_STAGE159_PERF_POSITIVE_MIN_OR_MAGNITUDE_REVIEW"
    else:
        decision = "NEUTRAL_STAGE159_PERF_SUB_DECOMP_FUSION_NOT_STABLE"

    return [{
        "metric": "T_bootstrap_per_lane",
        "runs": str(len(paired_runs)),
        "control_mean_pvw_lane_us": f"{mean(control_lane):.3f}",
        "fusion_mean_pvw_lane_us": f"{mean(fusion_lane):.3f}",
        "fusion_over_control_mean_speedup": f"{avg_speed:.6f}",
        "fusion_over_control_min_speedup": f"{min_speed:.6f}",
        "fusion_over_control_ci95_low": f"{low:.6f}",
        "fusion_over_control_ci95_high": f"{high:.6f}",
        "control_mean_speedup_vs_scalar": f"{mean(control_vs_scalar):.6f}",
        "fusion_mean_speedup_vs_scalar": f"{mean(fusion_vs_scalar):.6f}",
        "fusion_incremental_speedup_vs_control_scalar_speedup": f"{scalar_speed_ratio:.6f}",
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
        return {
            "r": str(R_VALUE),
            "seed": str(seed),
            "status": "MISSING_LINES",
            "source_log": rel(log),
        }
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
    pass_rows = [row for row in rows if row.get("status") == "Pass"]
    gaps = [parse_float(row["pvw_minus_scalar_log2"]) for row in pass_rows]
    pvw_fail = sum(int(row.get("pvw_failures", "0")) for row in rows if row.get("pvw_failures"))
    scalar_fail = sum(int(row.get("scalar_failures", "0")) for row in rows if row.get("scalar_failures"))
    pair_fail = sum(int(row.get("pair_failures", "0")) for row in rows if row.get("pair_failures"))
    points = sum(int(row.get("points", "0")) for row in rows if row.get("points"))
    status = "PASS" if len(pass_rows) == NOISE_SEED_COUNT and pvw_fail == 0 and scalar_fail == 0 and pair_fail == 0 else "FAIL"
    return [{
        "r": str(R_VALUE),
        "seeds": str(len(pass_rows)),
        "points": str(points),
        "pvw_failures": str(pvw_fail),
        "scalar_failures": str(scalar_fail),
        "pair_failures": str(pair_fail),
        "min_pvw_minus_scalar_log2": f"{min(gaps) if gaps else 0.0:.3f}",
        "max_pvw_minus_scalar_log2": f"{max(gaps) if gaps else 0.0:.3f}",
        "avg_pvw_minus_scalar_log2": f"{mean(gaps):.6f}",
        "status": status,
    }]


def run_noise() -> Tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    flags = (
        f"{BASE_FLAGS} SAB_PVW_SUB_DECOMP_FUSION=true "
        "MOSFHET_DETERMINISTIC_RNG=true "
        f"SAB_PVW_NOISE_TEST=true SAB_PVW_NOISE_R={R_VALUE} "
        f"SAB_PVW_NOISE_TRIALS={NOISE_TRIALS} SAB_PVW_NOISE_MAX_LOG2_GAP=4.0"
    )
    build_rc = run_wsl(
        f"make clean >/dev/null 2>&1 || true && make {flags} -j{MAKE_JOBS}",
        OUT_DIR / "noise" / "build.log",
        timeout=1200,
    )
    ok = build_rc == 0
    if build_rc == 0:
        for idx in range(NOISE_SEED_COUNT):
            seed = NOISE_START_SEED + idx
            log = OUT_DIR / "noise" / f"seed_{seed}.log"
            rc = run_wsl(f"env MOSFHET_TEST_RNG_SEED={seed} stdbuf -o0 ./main", log, timeout=1800)
            ok = ok and rc == 0
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
        return {
            "run": str(run_idx),
            "mode": mode,
            "status": "MISSING_LINES",
            "source_log": rel(log),
        }
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
    if scalar_hwm and pvw_hwm / scalar_hwm > 1.25:
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


def run_resource() -> Tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    flags = (
        f"{BASE_FLAGS} SAB_PVW_SUB_DECOMP_FUSION=true "
        f"SAB_PVW_RESOURCE_TEST=true SAB_PVW_RESOURCE_R={R_VALUE}"
    )
    build_rc = run_wsl(
        f"make clean >/dev/null 2>&1 || true && make {flags} -j{MAKE_JOBS}",
        OUT_DIR / "resource" / "build.log",
        timeout=1200,
    )
    ok = build_rc == 0
    if build_rc == 0:
        for run_idx in range(RESOURCE_RUNS):
            for mode in ["pvw", "scalar"]:
                log = OUT_DIR / "resource" / f"{mode}_run_{run_idx}.log"
                rc = run_wsl(
                    f"/usr/bin/time -v env SAB_PVW_RESOURCE_MODE={mode} stdbuf -o0 ./main",
                    log,
                    timeout=1800,
                )
                ok = ok and rc == 0
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
    perf_decision = perf_cmp[0]["decision"] if perf_cmp else "MISSING"
    noise_status = noise_agg[0]["status"] if noise_agg else "MISSING"
    resource_status = resource_cmp[0]["status"] if resource_cmp else "MISSING"
    perf_pass = perf_ok and perf_decision.startswith("PASS_STAGE159_PERF")
    perf_weak = perf_ok and perf_decision.startswith("WEAK_STAGE159_PERF")
    perf_neutral = perf_ok and perf_decision.startswith("NEUTRAL_STAGE159_PERF")
    noise_pass = noise_ok and noise_status == "PASS"
    resource_pass = resource_ok and resource_status in {"PASS", "REVIEW_RESOURCE_OVERHEAD"}

    if perf_pass and noise_pass and resource_status == "PASS":
        decision = "PASS_STAGE159_SUB_DECOMP_FUSION_REPEATED_PROMOTION_CANDIDATE"
        next_action = "Proceed to a policy/default gate or next representation-changing optimization; keep the flag explicit until then."
    elif perf_pass and noise_pass and resource_pass:
        decision = "PASS_STAGE159_SUB_DECOMP_FUSION_REPEATED_RESOURCE_REVIEW"
        next_action = "Review resource overhead before promotion."
    elif perf_weak and noise_pass and resource_pass:
        decision = "WEAK_STAGE159_SUB_DECOMP_FUSION_REPEATED_REVIEW_REQUIRED"
        next_action = "Do not promote; inspect run variance and consider more repeats."
    elif perf_neutral and noise_pass and resource_pass:
        decision = "NEUTRAL_STAGE159_SUB_DECOMP_FUSION_REPEATED_NOT_PROMOTED"
        next_action = "Keep as neutral ablation; move to next hypothesis."
    else:
        decision = "FAIL_STAGE159_SUB_DECOMP_FUSION_REPEATED_GATE"
        next_action = "Repair correctness/noise/resource or reject this candidate."

    return [
        {
            "gate": "stage159_perf",
            "status": perf_decision,
            "metric": "T_bootstrap/r",
            "value": perf_cmp[0].get("fusion_over_control_mean_speedup", "") if perf_cmp else "",
            "evidence": f"{rel(PERF_RESULTS_CSV)}; {rel(PERF_COMPARISON_CSV)}",
            "detail": "Repeated complete-SAB A/B for sub-decompose fusion versus same H14 backend control.",
            "next_action": "Promotion requires stable positive amortized per-lane timing.",
        },
        {
            "gate": "stage159_noise",
            "status": noise_status,
            "metric": "seeds;failures",
            "value": (
                f"{noise_agg[0].get('seeds', '')};"
                f"{noise_agg[0].get('pvw_failures', '')}/"
                f"{noise_agg[0].get('scalar_failures', '')}/"
                f"{noise_agg[0].get('pair_failures', '')}"
            ) if noise_agg else "",
            "evidence": f"{rel(NOISE_RESULTS_CSV)}; {rel(NOISE_AGG_CSV)}",
            "detail": "Final-output correctness/noise for the fusion path against scalar repeated outputs.",
            "next_action": "Any nonzero failure blocks promotion.",
        },
        {
            "gate": "stage159_resource",
            "status": resource_status,
            "metric": "key_bytes_ratio;vmhwm_ratio",
            "value": (
                f"{resource_cmp[0].get('key_bytes_ratio', '')};"
                f"{resource_cmp[0].get('vmhwm_ratio', '')}"
            ) if resource_cmp else "",
            "evidence": f"{rel(RESOURCE_RESULTS_CSV)}; {rel(RESOURCE_COMPARISON_CSV)}",
            "detail": "Resource/key snapshot for the fusion path versus repeated scalar.",
            "next_action": "Report key/memory cost with any timing claim.",
        },
        {
            "gate": "stage159_decision",
            "status": decision,
            "metric": "promotion_boundary",
            "value": "sub_decomp_fusion_explicit_flag",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage159 decides whether Stage158's smoke candidate survives research gates.",
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
        "# Stage159 Sub-Decompose Fusion Repeated Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Upgrade the Stage158 one-run complete-SAB smoke into a strict research gate: repeated performance, final-output noise/correctness, and resource evidence.",
        "",
        "## Primary Metric",
        "",
        "`T_bootstrap/r`, implemented as `pvw_lane_avg_us`, is the primary amortized MAT-RLWE/SAB throughput metric.",
        "",
        "## Variants",
        "",
        "- Control: H14 r=6 backend path with active-buffer and backend FromDFT-add.",
        "- Candidate: same flags plus `SAB_PVW_SUB_DECOMP_FUSION=true`.",
        "",
        "## Gates",
        "",
        "- Performance: paired repeated full-SAB A/B.",
        "- Correctness/noise: deterministic multi-seed final-output comparison.",
        "- Resource: key bytes, keygen per lane, internal VmHWM, and `/usr/bin/time` max RSS.",
        "",
        "No default-path or paper-level claim is upgraded by this stage alone.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage159 Sub-Decompose Fusion Statistical Model",
        "",
        "Date: 2026-07-03",
        "",
        "The candidate changes a local CMUX lifecycle:",
        "",
        "```text",
        "control: sub PVW_TMLWE -> decompose -> MAT external product",
        "fusion:  direct decompose(in2 - in1) -> MAT external product",
        "```",
        "",
        "The SAB sparse schedule count is unchanged: no CMUX, NCMUX, sub_a, RGSW monomial, extract, or key-switch count is reduced. Therefore the only admissible speed claim is an implementation-level lifecycle improvement inside the existing MAT-RLWE/SAB algorithm, measured on complete SAB as `T_bootstrap/r`.",
        "",
        "Promotion rule:",
        "",
        "```text",
        "speedup = mean(T_lane(control) / T_lane(fusion))",
        "positive if paired runs are complete, min speedup > 1.0, and mean speedup >= 1.02",
        "```",
        "",
        "Noise/resource gates are conjunctive. A faster but noisy or resource-unstated variant remains non-promotable.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB Sub-Decompose Fusion Repeated Variant",
        "",
        "Date: 2026-07-03",
        "",
        "Flag:",
        "",
        "```text",
        "SAB_PVW_SUB_DECOMP_FUSION=true",
        "```",
        "",
        "Boundary:",
        "",
        "- Explicit path only.",
        "- Scalar SAB default path unchanged.",
        "- Same key format and same sparse schedule as Stage158.",
        "- Evidence endpoint is complete-SAB amortized throughput, not a standalone kernel microbench.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage159 Sub-Decompose Fusion Repeated Gate",
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
        "Stage159 keeps the research loop finite: Stage158's positive smoke either becomes a promotion candidate, a weak/neutral ablation, or a failed candidate based on complete-SAB repeated evidence plus correctness/noise/resource gates.",
    ]) + "\n")


def update_longform(summary_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    append_once(ROADMAP_MD, "## Stage 159: Sub-Decompose Fusion Repeated Gate", f"""
## Stage 159: Sub-Decompose Fusion Repeated Gate

Goal:

```text
Upgrade Stage158 sub-decompose fusion from one-run full-SAB smoke to repeated
T_bootstrap/r, final-output noise, and resource gates.
```

Status:

```text
Completed. Stage159 records {decision}. Scalar/default paths remain unchanged.
```
""")
    append_once(GOAL_MD, "Stage159 upgrades sub-decompose fusion to a strict repeated gate", f"""
Stage159 upgrades sub-decompose fusion from Stage158 smoke to repeated
complete-SAB performance plus final-output noise/resource evidence. It uses
`T_bootstrap/r` as the endpoint and keeps `SAB_PVW_SUB_DECOMP_FUSION` explicit.
Decision: `{decision}`.
""")
    append_once(CURRENT_GOAL_MD, "63. Treat Stage159 as the sub-decompose fusion repeated gate", f"""
63. Treat Stage159 as the sub-decompose fusion repeated gate:
    `{decision}`. This stage decides whether the Stage158 candidate is a
    promotion candidate, weak/neutral ablation, or failed path under strict
    complete-SAB research gates.
""")
    append_once(HYPOTHESIS_YAML, "H83_sub_decomp_fusion_repeated_gate", f"""
  - id: H83_sub_decomp_fusion_repeated_gate
    statement: >
      The Stage158 sub-decompose fusion candidate should retain stable
      complete-SAB T_bootstrap/r improvement over the same H14 backend control
      and pass final-output noise/resource gates.
    mechanism: >
      Directly decomposing the in2-in1 CMUX difference removes an intermediate
      PVW_TMLWE write/read without changing key format or the sparse SAB
      schedule.
    status: stage159_sub_decomp_fusion_repeated_gate
    evidence: docs/stage159_sub_decomp_fusion_repeated_gate.md; experiments/stage159_sub_decomp_fusion_repeated_gate_plan.md; theory_checks/stage159_sub_decomp_fusion_stat_model.md; algorithm_variants/mat_rlwe_sab_sub_decomp_fusion_repeated.md; scripts/build_stage159_sub_decomp_fusion_repeated_gate.py; repro/stage159_sub_decomp_fusion_repeated_gate/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - paired repeated T_bootstrap/r does not improve over same-backend control
      - final-output noise has nonzero failures
      - resource/key overhead is not reported
""")


def update_repro(summary_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    append_once(
        RUN_LOG,
        "stage159-sub-decomp-fusion-repeated-gate-001",
        "stage159-sub-decomp-fusion-repeated-gate-001,"
        f"2026-07-03,{git_head()},Stage 159,spqlios_avx512,"
        "python scripts/build_stage159_sub_decomp_fusion_repeated_gate.py,"
        f"r={R_VALUE}; perf_runs={PERF_RUNS}; bench_reps={BENCH_REPS}; "
        f"noise_seeds={NOISE_SEED_COUNT}; resource_runs={RESOURCE_RUNS}; "
        f"sub_decomp_fusion,{NOISE_START_SEED},{decision},"
        "Sub-decompose fusion repeated full-SAB performance/noise/resource gate.,"
        f"{rel(OUT_DIR)}\n",
    )

    append_once(GLOBAL_MANIFEST, "stage159_sub_decomp_fusion_repeated_gate", f"""
- stage159_sub_decomp_fusion_repeated_gate: `{decision}`
  - `docs/stage159_sub_decomp_fusion_repeated_gate.md`
  - `experiments/stage159_sub_decomp_fusion_repeated_gate_plan.md`
  - `theory_checks/stage159_sub_decomp_fusion_stat_model.md`
  - `algorithm_variants/mat_rlwe_sab_sub_decomp_fusion_repeated.md`
  - `repro/stage159_sub_decomp_fusion_repeated_gate/`
""")
    append_once(CHECKLIST_MD, "Stage159 sub-decompose fusion repeated gate pack", """
- [x] Stage159 sub-decompose fusion repeated/noise/resource gate pack recorded.
""")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({
                "artifact": rel(path),
                "exists": "self",
                "sha256": "",
                "size_bytes": "",
            })
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
        raise SystemExit("STAGE159_PERF_RUNS must be >= 2")
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

    run_wsl("make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=300)

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
        OUT_DIR / "control_h14_r6_backend" / "build.log",
        OUT_DIR / "sub_decomp_fusion_h14_r6_backend" / "build.log",
        OUT_DIR / "noise" / "build.log",
        OUT_DIR / "resource" / "build.log",
        OUT_DIR / "cleanup.log",
        ARTIFACT_INDEX,
        Path(__file__).resolve(),
    ]
    for config in PERF_CONFIGS:
        for run_idx in range(PERF_RUNS):
            artifacts.append(OUT_DIR / config["variant"] / f"run_{run_idx}.log")
    for idx in range(NOISE_SEED_COUNT):
        artifacts.append(OUT_DIR / "noise" / f"seed_{NOISE_START_SEED + idx}.log")
    for run_idx in range(RESOURCE_RUNS):
        for mode in ["pvw", "scalar"]:
            artifacts.append(OUT_DIR / "resource" / f"{mode}_run_{run_idx}.log")
    write_artifact_index(artifacts)

    decision = summary_rows[-1]["status"]
    print(f"Stage159 sub-decomp fusion repeated gate: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if decision.startswith(("PASS_", "WEAK_", "NEUTRAL_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
