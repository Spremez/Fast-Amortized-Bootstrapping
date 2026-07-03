#!/usr/bin/env python3
"""Build Stage146 r4-unrolled variance-attribution gate."""

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
STAGE144 = ROOT / "repro" / "stage144_full_sab_repeated_r4_unrolled_gate"
OUT_DIR = ROOT / "repro" / "stage146_r4_unrolled_variance_attribution"

VARIANCE_BY_RUN_CSV = OUT_DIR / "variance_by_run.csv"
VARIANCE_SUMMARY_CSV = OUT_DIR / "variance_summary.csv"
PROFILE_RESULTS_CSV = OUT_DIR / "profile_results.csv"
PROFILE_COMPARISON_CSV = OUT_DIR / "profile_comparison.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage146_r4_unrolled_variance_attribution.md"
PLAN_MD = ROOT / "experiments" / "stage146_r4_unrolled_variance_attribution_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage146_variance_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_r4_unrolled_variance_boundary.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

JOBS = int(os.environ.get("JOBS", "8"))
RUN_PROFILE = os.environ.get("STAGE146_RUN_PROFILE", "1") not in {"0", "false", "False"}

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true KEY=BINARY PARAM=SET_2_3_2048 "
    "SAB_PVW_BENCH=true SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 "
    "SAB_PVW_BODY_PROFILE=true"
)
PROFILE_CONFIGS = [
    {
        "variant": "generic_active_profile",
        "flags": BASE_FLAGS,
    },
    {
        "variant": "r4_unrolled_active_profile",
        "flags": f"{BASE_FLAGS} MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true",
    },
]

VARIANCE_FIELDS = [
    "run", "generic_lane_us", "r4_lane_us", "paired_r4_over_generic_speedup",
    "generic_rel_to_median_pct", "r4_rel_to_median_pct",
    "generic_scalar_lane_us", "r4_scalar_lane_us", "r4_outlier_flag",
]
VARIANCE_SUMMARY_FIELDS = [
    "metric", "value", "detail", "status",
]
PROFILE_FIELDS = [
    "variant", "status", "lanes", "in_N", "h", "r_prec", "bench_pvw_us",
    "bench_pvw_lane_us", "body_full_us", "mat_ep_calls", "mat_ep_us",
    "mat_ep_share", "non_mat_body_us", "cmux_calls", "cmux_us",
    "ncmux_calls", "ncmux_us", "cmux_sub_us", "cmux_from_dft_us",
    "cmux_add_us", "ncmux_auto_us", "sub_a_calls", "sub_a_us",
    "copyback_calls", "copyback_us", "source_log",
]
PROFILE_COMPARE_FIELDS = ["metric", "generic", "r4_unrolled", "ratio_or_delta", "status", "detail"]
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
PROFILE_KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")


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
    write_text_lf(path, text + block.strip() + "\n")


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


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def fmt(value: float) -> str:
    if math.isfinite(value):
        return f"{value:.6f}"
    return str(value)


def cv_pct(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = statistics.mean(values)
    if m == 0:
        return 0.0
    return statistics.stdev(values) / m * 100.0


def stage144_variance() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    rows = read_csv(STAGE144 / "perf_results.csv")
    generic = {int(row["run"]): row for row in rows if row.get("variant") == "generic_active"}
    r4 = {int(row["run"]): row for row in rows if row.get("variant") == "r4_unrolled_active"}
    runs = sorted(set(generic) & set(r4))
    if not runs:
        return [], [{
            "metric": "stage144_runs_available",
            "value": "0",
            "detail": "No paired generic/r4 rows found.",
            "status": "FAIL",
        }]

    generic_lanes = [fnum(generic[idx]["pvw_lane_avg_us"]) for idx in runs]
    r4_lanes = [fnum(r4[idx]["pvw_lane_avg_us"]) for idx in runs]
    generic_scalar = [fnum(generic[idx]["scalar_lane_avg_us"]) for idx in runs]
    r4_scalar = [fnum(r4[idx]["scalar_lane_avg_us"]) for idx in runs]
    generic_median = statistics.median(generic_lanes)
    r4_median = statistics.median(r4_lanes)

    by_run: List[Dict[str, str]] = []
    outliers = 0
    paired_speedups: List[float] = []
    for idx in runs:
        g_lane = fnum(generic[idx]["pvw_lane_avg_us"])
        r_lane = fnum(r4[idx]["pvw_lane_avg_us"])
        g_scalar = fnum(generic[idx]["scalar_lane_avg_us"])
        r_scalar = fnum(r4[idx]["scalar_lane_avg_us"])
        speedup = g_lane / r_lane if r_lane else 0.0
        paired_speedups.append(speedup)
        g_rel = (g_lane / generic_median - 1.0) * 100.0 if generic_median else 0.0
        r_rel = (r_lane / r4_median - 1.0) * 100.0 if r4_median else 0.0
        outlier = abs(r_rel) >= 8.0 and abs(g_rel) <= 3.0
        if outlier:
            outliers += 1
        by_run.append({
            "run": str(idx),
            "generic_lane_us": f"{g_lane:.3f}",
            "r4_lane_us": f"{r_lane:.3f}",
            "paired_r4_over_generic_speedup": fmt(speedup),
            "generic_rel_to_median_pct": fmt(g_rel),
            "r4_rel_to_median_pct": fmt(r_rel),
            "generic_scalar_lane_us": f"{g_scalar:.3f}",
            "r4_scalar_lane_us": f"{r_scalar:.3f}",
            "r4_outlier_flag": "yes" if outlier else "no",
        })

    perf_cmp = read_csv(STAGE144 / "perf_comparison.csv")
    stage144_decision = perf_cmp[0].get("decision", "MISSING") if perf_cmp else "MISSING"
    median_speedup = statistics.median(paired_speedups)
    leave_outlier = [fnum(row["paired_r4_over_generic_speedup"]) for row in by_run if row["r4_outlier_flag"] == "no"]
    leave_outlier_mean = statistics.mean(leave_outlier) if leave_outlier else 0.0
    status = "PASS_VARIANCE_OUTLIER_IDENTIFIED" if outliers else "NO_SINGLE_OUTLIER_IDENTIFIED"
    summary = [
        {"metric": "stage144_decision", "value": stage144_decision, "detail": "Input repeated gate decision.", "status": "PASS"},
        {"metric": "paired_runs", "value": str(len(runs)), "detail": "Ordinal generic/r4 Stage144 rows compared.", "status": "PASS"},
        {"metric": "paired_median_r4_over_generic_speedup", "value": fmt(median_speedup), "detail": "Median is robust to the slow r4 sample.", "status": "PASS"},
        {"metric": "paired_mean_without_r4_outlier", "value": fmt(leave_outlier_mean), "detail": "Mean after removing rows flagged by relative-median rule.", "status": status},
        {"metric": "generic_lane_cv_pct", "value": fmt(cv_pct(generic_lanes)), "detail": "Stage144 generic PVW lane coefficient of variation.", "status": "PASS"},
        {"metric": "r4_lane_cv_pct", "value": fmt(cv_pct(r4_lanes)), "detail": "Stage144 r4-unrolled PVW lane coefficient of variation.", "status": status},
        {"metric": "generic_scalar_lane_cv_pct", "value": fmt(cv_pct(generic_scalar)), "detail": "Stage144 scalar lane variation in generic runs.", "status": "PASS"},
        {"metric": "r4_scalar_lane_cv_pct", "value": fmt(cv_pct(r4_scalar)), "detail": "Stage144 scalar lane variation in r4 runs.", "status": "PASS"},
        {"metric": "r4_outlier_count", "value": str(outliers), "detail": "Rows with r4-only deviation >=8% and generic deviation <=3%.", "status": status},
    ]
    return by_run, summary


def parse_profile_log(variant: str, log: Path) -> Dict[str, str]:
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    correctness = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    profile_line = ""
    for line in text.splitlines():
        if "SAB_PVW_BODY_PROFILE sample" in line:
            profile_line = line
    kv = dict(PROFILE_KV_RE.findall(profile_line))
    status = "PASS" if correctness and correctness.group("status") == "Pass" and bench and kv else "FAIL"
    mat_ep_us = fnum(kv.get("mat_ep_us", "0"))
    body_full_us = fnum(kv.get("full_us", "0"))
    non_mat = body_full_us - mat_ep_us
    share = mat_ep_us / body_full_us if body_full_us else 0.0
    return {
        "variant": variant,
        "status": status,
        "lanes": kv.get("lanes", ""),
        "in_N": kv.get("in_N", ""),
        "h": kv.get("h", ""),
        "r_prec": kv.get("r_prec", ""),
        "bench_pvw_us": bench.group("pvw_avg_us") if bench else "",
        "bench_pvw_lane_us": bench.group("pvw_lane_avg_us") if bench else "",
        "body_full_us": kv.get("full_us", ""),
        "mat_ep_calls": kv.get("mat_ep_calls", ""),
        "mat_ep_us": kv.get("mat_ep_us", ""),
        "mat_ep_share": fmt(share),
        "non_mat_body_us": fmt(non_mat),
        "cmux_calls": kv.get("cmux_calls", ""),
        "cmux_us": kv.get("cmux_us", ""),
        "ncmux_calls": kv.get("ncmux_calls", ""),
        "ncmux_us": kv.get("ncmux_us", ""),
        "cmux_sub_us": kv.get("cmux_sub_us", ""),
        "cmux_from_dft_us": kv.get("cmux_from_dft_us", ""),
        "cmux_add_us": kv.get("cmux_add_us", ""),
        "ncmux_auto_us": kv.get("ncmux_auto_us", ""),
        "sub_a_calls": kv.get("sub_a_calls", ""),
        "sub_a_us": kv.get("sub_a_us", ""),
        "copyback_calls": kv.get("copyback_calls", ""),
        "copyback_us": kv.get("copyback_us", ""),
        "source_log": rel(log),
    }


def run_profiles() -> Tuple[bool, List[Dict[str, str]]]:
    if not RUN_PROFILE:
        cached = read_csv(PROFILE_RESULTS_CSV)
        return bool(cached), cached
    rows: List[Dict[str, str]] = []
    ok = True
    for config in PROFILE_CONFIGS:
        variant = config["variant"]
        build_log = OUT_DIR / f"profile_build_{variant}.log"
        build = run_logged(
            f"make clean >/dev/null 2>&1 || true && make {config['flags']} -j{JOBS}",
            build_log,
            timeout=900,
        )
        ok = ok and build.returncode == 0
        run_log = OUT_DIR / f"profile_{variant}.log"
        if build.returncode == 0:
            proc = run_logged("./main", run_log, timeout=1200)
            ok = ok and proc.returncode == 0
        else:
            write_text_lf(run_log, "profile run skipped because build failed\n")
            ok = False
        parsed = parse_profile_log(variant, run_log)
        ok = ok and parsed.get("status") == "PASS"
        rows.append(parsed)
    run_logged("make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=60)
    return ok, rows


def compare_profiles(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(rows) < 2:
        return [{
            "metric": "profile_available",
            "generic": "0",
            "r4_unrolled": "0",
            "ratio_or_delta": "0",
            "status": "SKIPPED",
            "detail": "No profile run was requested or completed.",
        }]
    generic = next((row for row in rows if row["variant"] == "generic_active_profile"), None)
    r4 = next((row for row in rows if row["variant"] == "r4_unrolled_active_profile"), None)
    if not generic or not r4:
        return [{
            "metric": "profile_available",
            "generic": "missing",
            "r4_unrolled": "missing",
            "ratio_or_delta": "0",
            "status": "FAIL",
            "detail": "Expected generic and r4 profile rows.",
        }]

    def ratio(field: str) -> float:
        denom = fnum(r4.get(field, "0"))
        return fnum(generic.get(field, "0")) / denom if denom else 0.0

    comparisons = [
        {
            "metric": "profile_status",
            "generic": generic["status"],
            "r4_unrolled": r4["status"],
            "ratio_or_delta": "0",
            "status": "PASS" if generic["status"] == "PASS" and r4["status"] == "PASS" else "FAIL",
            "detail": "Correctness and body-profile lines were parsed.",
        },
        {
            "metric": "bench_pvw_lane_speedup_generic_over_r4",
            "generic": generic["bench_pvw_lane_us"],
            "r4_unrolled": r4["bench_pvw_lane_us"],
            "ratio_or_delta": fmt(ratio("bench_pvw_lane_us")),
            "status": "PROFILE_ONLY",
            "detail": "One profiled full-SAB run; not a final performance claim.",
        },
        {
            "metric": "body_full_speedup_generic_over_r4",
            "generic": generic["body_full_us"],
            "r4_unrolled": r4["body_full_us"],
            "ratio_or_delta": fmt(ratio("body_full_us")),
            "status": "PROFILE_ONLY",
            "detail": "Body hot-path timing excludes post-processing.",
        },
        {
            "metric": "mat_ep_speedup_generic_over_r4",
            "generic": generic["mat_ep_us"],
            "r4_unrolled": r4["mat_ep_us"],
            "ratio_or_delta": fmt(ratio("mat_ep_us")),
            "status": "PROFILE_ONLY",
            "detail": "If >1, the profiled r4-unrolled MAT EP is faster.",
        },
        {
            "metric": "non_mat_body_speedup_generic_over_r4",
            "generic": generic["non_mat_body_us"],
            "r4_unrolled": r4["non_mat_body_us"],
            "ratio_or_delta": fmt(ratio("non_mat_body_us")),
            "status": "PROFILE_ONLY",
            "detail": "Non-MAT body work includes sub/from_DFT/add/rotation/schedule overhead.",
        },
        {
            "metric": "mat_ep_share_delta_r4_minus_generic",
            "generic": generic["mat_ep_share"],
            "r4_unrolled": r4["mat_ep_share"],
            "ratio_or_delta": fmt(fnum(r4["mat_ep_share"]) - fnum(generic["mat_ep_share"])),
            "status": "PROFILE_ONLY",
            "detail": "Share delta is diagnostic only because profile instrumentation changes absolute timing.",
        },
        {
            "metric": "mat_ep_calls_equal",
            "generic": generic["mat_ep_calls"],
            "r4_unrolled": r4["mat_ep_calls"],
            "ratio_or_delta": "1" if generic["mat_ep_calls"] == r4["mat_ep_calls"] else "0",
            "status": "PASS" if generic["mat_ep_calls"] == r4["mat_ep_calls"] else "FAIL",
            "detail": "Schedule counts must remain unchanged across kernel variants.",
        },
        {
            "metric": "copyback_calls_equal_zero",
            "generic": generic["copyback_calls"],
            "r4_unrolled": r4["copyback_calls"],
            "ratio_or_delta": "1" if generic["copyback_calls"] == "0" and r4["copyback_calls"] == "0" else "0",
            "status": "PASS" if generic["copyback_calls"] == "0" and r4["copyback_calls"] == "0" else "FAIL",
            "detail": "Active-buffer fusion should keep copyback eliminated.",
        },
    ]
    return comparisons


def build_summary(
    variance_summary: List[Dict[str, str]],
    profile_ok: bool,
    profile_cmp: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    outlier_count = 0
    for row in variance_summary:
        if row["metric"] == "r4_outlier_count":
            outlier_count = int(float(row["value"]))
    profile_pass = profile_ok and any(row["metric"] == "profile_status" and row["status"] == "PASS" for row in profile_cmp)
    mat_ep_ratio = 0.0
    body_ratio = 0.0
    for row in profile_cmp:
        if row["metric"] == "mat_ep_speedup_generic_over_r4":
            mat_ep_ratio = fnum(row["ratio_or_delta"])
        if row["metric"] == "body_full_speedup_generic_over_r4":
            body_ratio = fnum(row["ratio_or_delta"])

    if outlier_count and profile_pass and mat_ep_ratio > 1.02:
        decision = "PASS_STAGE146_VARIANCE_ATTRIBUTED_KEEP_R4_EXPLICIT_ROUTE_TO_SCHEDULE_OR_HIGHER_STAT"
        next_action = "Do not promote r4-unrolled; use it as a kernel ablation while Stage147 targets full-SAB schedule attribution or stronger repeated stats."
    elif outlier_count and profile_pass:
        decision = "WEAK_STAGE146_VARIANCE_PROFILE_NO_KERNEL_EDGE_ROUTE_TO_KERNEL_REPAIR"
        next_action = "Do not promote r4-unrolled; repair or replace kernel candidate before more full-SAB repeats."
    elif profile_pass:
        decision = "WEAK_STAGE146_NO_OUTLIER_PROFILE_ONLY_MORE_STATS_REQUIRED"
        next_action = "Run higher-stat paired complete-SAB before changing policy."
    else:
        decision = "FAIL_STAGE146_PROFILE_ATTRIBUTION_INCOMPLETE"
        next_action = "Repair profile gate before using Stage146 for routing."

    return [
        {
            "gate": "stage146_inputs",
            "status": "PASS" if variance_summary else "FAIL",
            "metric": "stage144_perf_results",
            "value": rel(STAGE144 / "perf_results.csv"),
            "evidence": rel(STAGE144 / "perf_results.csv"),
            "detail": "Stage146 consumes Stage144 repeated run-level rows.",
            "next_action": "",
        },
        {
            "gate": "stage146_variance",
            "status": "PASS_VARIANCE_OUTLIER_IDENTIFIED" if outlier_count else "NO_SINGLE_OUTLIER_IDENTIFIED",
            "metric": "r4_outlier_count",
            "value": str(outlier_count),
            "evidence": f"{rel(VARIANCE_BY_RUN_CSV)}; {rel(VARIANCE_SUMMARY_CSV)}",
            "detail": "Outlier rule flags r4-only relative-median deviation.",
            "next_action": "",
        },
        {
            "gate": "stage146_profile",
            "status": "PASS" if profile_pass else "FAIL_OR_SKIPPED",
            "metric": "mat_ep_ratio;body_ratio",
            "value": f"{fmt(mat_ep_ratio)};{fmt(body_ratio)}",
            "evidence": f"{rel(PROFILE_RESULTS_CSV)}; {rel(PROFILE_COMPARISON_CSV)}",
            "detail": "One profiled generic/r4 pair attributes body hot-path timing; not a final latency claim.",
            "next_action": "",
        },
        {
            "gate": "stage146_decision",
            "status": decision,
            "metric": "routing",
            "value": "explicit_r4_unrolled_not_promoted",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage146 selects the next research route without changing scalar/default behavior.",
            "next_action": next_action,
        },
    ]


def write_docs(
    variance_rows: List[Dict[str, str]],
    variance_summary: List[Dict[str, str]],
    profile_rows: List[Dict[str, str]],
    profile_cmp: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    decision = summary_rows[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage146 r4-Unrolled Variance Attribution Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Explain why Stage144 produced weak repeated complete-SAB evidence for the r4-unrolled AVX512 path.",
        "",
        "## Procedure",
        "",
        "1. Reuse Stage144 repeated run rows and compute robust paired statistics.",
        "2. Flag r4-only slow samples by relative-median deviation.",
        "3. Run one diagnostic `SAB_PVW_BODY_PROFILE` pair for generic active and r4-unrolled active.",
        "4. Route the next stage without changing scalar/default behavior.",
        "",
        "## Boundary",
        "",
        "Profile timings are attribution evidence only. Final speedup still requires repeated complete-SAB `T_bootstrap/r` gates.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage146 Variance Model",
        "",
        "Date: 2026-07-03",
        "",
        "The MAT-RLWE comparison endpoint is amortized `T_bootstrap/r`. A single run with a faster MAT EP does not prove a faster complete bootstrapping algorithm if run-to-run variance crosses one.",
        "",
        "Stage146 separates three quantities:",
        "",
        "- robust repeated evidence from Stage144;",
        "- diagnostic body-profile attribution for MAT EP versus non-MAT work;",
        "- promotion policy, which remains controlled by repeated complete-SAB gates.",
        "",
        "A r4-only slow sample indicates that more kernel work is not automatically justified. The next stage must either reduce full-SAB variance, increase paired statistics, or target schedule-level work that appears in the profile.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB r4-Unrolled Variance Boundary",
        "",
        "Date: 2026-07-03",
        "",
        "The r4-unrolled AVX512 path is a local MAT external-product kernel variant. It does not change the SAB schedule, ciphertext semantics, key format, noise model, or scalar/default route.",
        "",
        "Stage146 keeps this variant behind an explicit flag unless repeated complete-SAB evidence becomes stable under `T_bootstrap/r`.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage146 r4-Unrolled Variance Attribution",
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
        "## Stage144 Robust Variance",
        "",
        table(variance_summary, VARIANCE_SUMMARY_FIELDS),
        "",
        "## Run-Level Attribution",
        "",
        table(variance_rows, VARIANCE_FIELDS),
        "",
        "## Body Profile Rows",
        "",
        table(profile_rows, PROFILE_FIELDS),
        "",
        "## Profile Comparison",
        "",
        table(profile_cmp, PROFILE_COMPARE_FIELDS),
        "",
        "## Interpretation",
        "",
        "Stage146 is a routing gate. It keeps the r4-unrolled kernel as an explicit ablation unless later repeated full-SAB evidence becomes stable. It does not alter scalar SAB or default PVW/MAT-SAB behavior.",
    ]) + "\n")


def update_longform(summary_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    block = f"""
## Stage 146: r4-Unrolled Variance Attribution

Goal:

```text
Explain the Stage144 weak repeated result and decide whether r4-unrolled AVX512
deserves more full-SAB work or should remain only an explicit ablation.
```

Status:

```text
Completed. Stage146 records {decision}. It consumes Stage144 repeated
rows, runs one body-profile diagnostic pair, and keeps scalar/default behavior
unchanged.
```
"""
    append_once(ROADMAP_MD, "## Stage 146: r4-Unrolled Variance Attribution", block)
    append_once(GOAL_MD, "Stage146 records r4-unrolled variance attribution", f"""
Stage146 records r4-unrolled variance attribution after Stage145. It treats
Stage144 run-level spread as a routing input, not as a reason to promote the
r4-unrolled AVX512 path. All final acceleration wording remains bound to
repeated complete-SAB `T_bootstrap/r` gates.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage146 as the r4-unrolled variance-attribution gate", f"""
50. Treat Stage146 as the r4-unrolled variance-attribution gate:
    `{decision}`. This stage may guide the next research route, but it does not
    promote the r4-unrolled path or modify scalar/default SAB behavior.
""")
    append_once(HYPOTHESIS_YAML, "H70_r4_unrolled_variance_attribution", f"""
  - id: H70_r4_unrolled_variance_attribution
    statement: >
      The Stage144 weak r4-unrolled complete-SAB result is dominated by
      run-level variance or non-promotable local effects, so r4-unrolled must
      remain explicit-only until a later repeated full-SAB gate stabilizes.
    mechanism: >
      Stage146 combines robust Stage144 run-level analysis with one body-profile
      diagnostic pair to separate MAT EP attribution from final complete-SAB
      claim strength.
    status: stage146_r4_unrolled_variance_attribution
    evidence: docs/stage146_r4_unrolled_variance_attribution.md; experiments/stage146_r4_unrolled_variance_attribution_plan.md; theory_checks/stage146_variance_model.md; scripts/build_stage146_r4_unrolled_variance_attribution.py; repro/stage146_r4_unrolled_variance_attribution/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - profile or repeated rows are used as final speedup proof without a repeated complete-SAB gate
      - scalar/default SAB behavior changes during variance attribution
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
        "run_id": "stage146-r4-unrolled-variance-attribution-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "stage146_r4_unrolled_variance_attribution",
        "backend": "spqlios_avx512",
        "command": "python scripts/build_stage146_r4_unrolled_variance_attribution.py",
        "params": "BINARY SET_2_3_2048; r=4; active-buffer; generic vs MAT_TRGSW_AVX512_R4_UNROLLED_ROWS; profile pair",
        "seed": "default-rng",
        "status": decision,
        "summary": "r4-unrolled variance attribution and profile routing gate",
        "artifacts": rel(OUT_DIR),
    })
    run_row = {field: base_row.get(field, "") for field in run_fields}
    existing = [
        row for row in existing
        if row.get("run_id") != run_row.get("run_id")
        and row.get("stage") != run_row.get("stage")
    ]
    existing.append(run_row)
    write_csv(RUN_LOG, existing, run_fields)

    append_once(GLOBAL_MANIFEST, "stage146_r4_unrolled_variance_attribution", f"""
- stage146_r4_unrolled_variance_attribution: `{decision}`
  - `docs/stage146_r4_unrolled_variance_attribution.md`
  - `experiments/stage146_r4_unrolled_variance_attribution_plan.md`
  - `theory_checks/stage146_variance_model.md`
  - `repro/stage146_r4_unrolled_variance_attribution/`
""")
    append_once(CHECKLIST_MD, "Stage146 r4-unrolled variance-attribution pack", """
- [x] Stage146 r4-unrolled variance-attribution pack recorded.
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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    variance_rows, variance_summary = stage144_variance()
    write_csv(VARIANCE_BY_RUN_CSV, variance_rows, VARIANCE_FIELDS)
    write_csv(VARIANCE_SUMMARY_CSV, variance_summary, VARIANCE_SUMMARY_FIELDS)

    profile_ok, profile_rows = run_profiles()
    profile_cmp = compare_profiles(profile_rows)
    summary_rows = build_summary(variance_summary, profile_ok, profile_cmp)

    write_csv(PROFILE_RESULTS_CSV, profile_rows, PROFILE_FIELDS)
    write_csv(PROFILE_COMPARISON_CSV, profile_cmp, PROFILE_COMPARE_FIELDS)
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)

    write_docs(variance_rows, variance_summary, profile_rows, profile_cmp, summary_rows)
    update_longform(summary_rows)
    update_repro(summary_rows)

    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD,
        VARIANCE_BY_RUN_CSV, VARIANCE_SUMMARY_CSV,
        PROFILE_RESULTS_CSV, PROFILE_COMPARISON_CSV, SUMMARY_CSV,
        OUT_DIR / "profile_build_generic_active_profile.log",
        OUT_DIR / "profile_generic_active_profile.log",
        OUT_DIR / "profile_build_r4_unrolled_active_profile.log",
        OUT_DIR / "profile_r4_unrolled_active_profile.log",
        OUT_DIR / "cleanup.log",
        ARTIFACT_INDEX,
        Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)
    print(f"Stage146 r4-unrolled variance attribution: {summary_rows[-1]['status']}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
