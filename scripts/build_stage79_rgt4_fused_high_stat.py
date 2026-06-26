#!/usr/bin/env python3
"""Build the Stage79 r>4 fused-MAT high-stat confirmation report."""

from __future__ import annotations

import csv
import glob
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage79_rgt4_fused_high_stat"
FULL_SAB_CSV = OUT_DIR / "full_sab_high_stat.csv"
NOISE_SUMMARY_CSV = OUT_DIR / "noise_summary.csv"
RESOURCE_SAMPLES_CSV = OUT_DIR / "resource_samples.csv"
RESOURCE_SUMMARY_CSV = OUT_DIR / "resource_summary.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage79_rgt4_fused_high_stat_log.md"

STAGE36_TARGET = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE78_SUMMARY = ROOT / "repro" / "stage78_rgt4_fused_repeated_gates" / "summary.csv"
STAGE78_FULL = ROOT / "repro" / "stage78_rgt4_fused_repeated_gates" / "full_sab_repeated.csv"
NOISE_AGGREGATE = OUT_DIR / "final_noise" / "aggregate.csv"

MIN_FULL_SAMPLES = 10
MIN_NOISE_SEEDS = 20
MIN_RESOURCE_RUNS = 3
RESOURCE_RSS_REVIEW_RATIO = 1.25


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fnum(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, ""))
    except (TypeError, ValueError):
        return default


def stage36_r4_reference() -> Dict[str, str]:
    for row in read_csv(STAGE36_TARGET):
        if row.get("r") == "4":
            return row
    return {}


def stage78_r6_reference() -> Dict[str, str]:
    for row in read_csv(STAGE78_FULL):
        if row.get("r") == "6":
            return row
    return {}


def stage78_precondition_passes() -> bool:
    return any(
        row.get("gate") == "stage78_decision"
        and row.get("status")
        == "PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE"
        for row in read_csv(STAGE78_SUMMARY)
    )


def find_full_summary(r: str = "6") -> Path | None:
    candidates = sorted(
        OUT_DIR.glob(f"full_sab_fused_r{r}_runs*/summary.csv"),
        key=lambda p: (len(read_csv(p)), p.as_posix()),
        reverse=True,
    )
    return candidates[0] if candidates else None


def ci95(values: List[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    sd = stdev(values)
    half = 1.96 * sd / math.sqrt(len(values))
    return mean(values) - half, mean(values) + half


def full_sab_row() -> Dict[str, str]:
    path = find_full_summary("6")
    rows = read_csv(path) if path else []
    speedups = [fnum(row, "speedup_vs_scalar_repeated") for row in rows]
    pvw = [fnum(row, "pvw_avg_us") for row in rows]
    scalar = [fnum(row, "scalar_repeated_avg_us") for row in rows]
    statuses = sorted({row.get("status", "") for row in rows})
    samples = len(rows)
    all_pass = bool(rows) and all(row.get("status") == "Pass" for row in rows)
    speed_mean = mean(speedups) if speedups else 0.0
    speed_min = min(speedups) if speedups else 0.0
    speed_max = max(speedups) if speedups else 0.0
    speed_stddev = stdev(speedups) if len(speedups) > 1 else 0.0
    low, high = ci95(speedups)
    r4 = stage36_r4_reference()
    r4_mean = fnum(r4, "mean_speedup")
    r4_low = fnum(r4, "ci95_low")
    r4_high = fnum(r4, "ci95_high")
    stage78 = stage78_r6_reference()
    stage78_mean = fnum(stage78, "mean_speedup")
    stage78_min = fnum(stage78, "min_speedup")

    status = "PASS"
    if not all_pass:
        status = "FAIL"
    elif samples < MIN_FULL_SAMPLES:
        status = "INSUFFICIENT_SAMPLES"
    elif speed_min <= 1.0:
        status = "FAIL_MIN_SPEEDUP"
    elif speed_mean >= r4_mean and low >= r4_low:
        status = "PASS_PROMOTION_BOUNDARY_CONFIRMED"
    elif speed_mean >= r4_mean:
        status = "PASS_MEAN_CONFIRMED_CI_REVIEW"
    elif speed_mean >= r4_low:
        status = "PASS_R4_REGION_NOT_CONFIRMED"
    else:
        status = "PASS_BELOW_R4_REFERENCE"

    return {
        "r": "6",
        "samples": str(samples),
        "statuses": ";".join(statuses) if statuses else "MISSING",
        "pvw_mean_us": f"{mean(pvw):.3f}" if pvw else "0.000",
        "scalar_repeated_mean_us": f"{mean(scalar):.3f}" if scalar else "0.000",
        "mean_speedup": f"{speed_mean:.3f}",
        "min_speedup": f"{speed_min:.3f}",
        "max_speedup": f"{speed_max:.3f}",
        "stddev_speedup": f"{speed_stddev:.6f}",
        "ci95_low": f"{low:.6f}",
        "ci95_high": f"{high:.6f}",
        "stage36_r4_mean_reference": f"{r4_mean:.3f}",
        "stage36_r4_ci95_low_reference": f"{r4_low:.6f}",
        "stage36_r4_ci95_high_reference": f"{r4_high:.6f}",
        "stage78_r6_mean_reference": f"{stage78_mean:.3f}",
        "stage78_r6_min_reference": f"{stage78_min:.3f}",
        "status": status,
        "source": path.relative_to(ROOT).as_posix() if path else "MISSING",
    }


def noise_rows() -> List[Dict[str, str]]:
    rows = {row.get("r"): row for row in read_csv(NOISE_AGGREGATE)}
    row = rows.get("6", {})
    seeds = int(float(row.get("seeds", "0") or 0)) if row else 0
    failures = (
        int(float(row.get("pvw_failures", "0") or 0))
        + int(float(row.get("scalar_failures", "0") or 0))
        + int(float(row.get("pair_failures", "0") or 0))
    )
    if row.get("status") == "PASS" and failures == 0 and seeds >= MIN_NOISE_SEEDS:
        gate = "PASS"
    elif row.get("status") == "PASS" and failures == 0:
        gate = "PASS_INSUFFICIENT_SEEDS"
    elif row:
        gate = "FAIL"
    else:
        gate = "MISSING"
    return [
        {
            "r": "6",
            "seeds": row.get("seeds", "0"),
            "points": row.get("points", "0"),
            "pvw_failures": row.get("pvw_failures", "0"),
            "scalar_failures": row.get("scalar_failures", "0"),
            "pair_failures": row.get("pair_failures", "0"),
            "min_pvw_minus_scalar_log2": row.get("min_pvw_minus_scalar_log2", "0"),
            "max_pvw_minus_scalar_log2": row.get("max_pvw_minus_scalar_log2", "0"),
            "avg_pvw_minus_scalar_log2": row.get("avg_pvw_minus_scalar_log2", "0"),
            "status": gate,
            "source": NOISE_AGGREGATE.relative_to(ROOT).as_posix()
            if NOISE_AGGREGATE.exists()
            else "MISSING",
        }
    ]


def resource_samples() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    pattern = str(OUT_DIR / "resource_run_*" / "summary.csv")
    for path_str in sorted(glob.glob(pattern)):
        path = Path(path_str)
        run_label = path.parent.name
        run_index = run_label.rsplit("_", 1)[-1]
        for row in read_csv(path):
            if row.get("r") != "6":
                continue
            item = dict(row)
            item["run_index"] = run_index
            item["run_label"] = run_label
            item["source_csv"] = path.relative_to(ROOT).as_posix()
            rows.append(item)
    return rows


def resource_summary(samples: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    pvw = [row for row in samples if row.get("mode") == "pvw"]
    scalar = [row for row in samples if row.get("mode") == "scalar"]
    scalar_by_run = {row.get("run_label"): row for row in scalar}
    pvw_by_run = {row.get("run_label"): row for row in pvw}
    paired_runs = sorted(set(scalar_by_run) & set(pvw_by_run))
    key_ratios = [fnum(pvw_by_run[run], "estimated_key_bytes_ratio_vs_scalar_repeated") for run in paired_runs]
    keygen_ratios = [
        fnum(pvw_by_run[run], "keygen_us") / fnum(scalar_by_run[run], "keygen_us")
        for run in paired_runs
        if fnum(scalar_by_run[run], "keygen_us")
    ]
    rss_ratios = [
        fnum(pvw_by_run[run], "time_max_rss_kb") / fnum(scalar_by_run[run], "time_max_rss_kb")
        for run in paired_runs
        if fnum(scalar_by_run[run], "time_max_rss_kb")
    ]
    pvw_rss = [fnum(row, "time_max_rss_kb") for row in pvw]
    scalar_rss = [fnum(row, "time_max_rss_kb") for row in scalar]
    source_csvs = ";".join(sorted({row.get("source_csv", "") for row in samples if row.get("source_csv")}))

    runs = len(paired_runs)
    status = "PASS" if runs >= MIN_RESOURCE_RUNS and key_ratios and rss_ratios else "INCOMPLETE_RESOURCE"
    if status == "PASS" and max(rss_ratios) > RESOURCE_RSS_REVIEW_RATIO:
        status = "REVIEW_RESOURCE_OVERHEAD"
    out.append(
        {
            "r": "6",
            "runs": str(runs),
            "key_ratio_mean": f"{mean(key_ratios):.6f}" if key_ratios else "0.000000",
            "key_ratio_min": f"{min(key_ratios):.6f}" if key_ratios else "0.000000",
            "key_ratio_max": f"{max(key_ratios):.6f}" if key_ratios else "0.000000",
            "keygen_ratio_mean": f"{mean(keygen_ratios):.6f}" if keygen_ratios else "0.000000",
            "rss_ratio_mean": f"{mean(rss_ratios):.6f}" if rss_ratios else "0.000000",
            "rss_ratio_min": f"{min(rss_ratios):.6f}" if rss_ratios else "0.000000",
            "rss_ratio_max": f"{max(rss_ratios):.6f}" if rss_ratios else "0.000000",
            "pvw_rss_mean_kb": f"{mean(pvw_rss):.3f}" if pvw_rss else "0.000",
            "scalar_rss_mean_kb": f"{mean(scalar_rss):.3f}" if scalar_rss else "0.000",
            "status": status,
            "source_csvs": source_csvs if source_csvs else "MISSING",
        }
    )
    return out


def summary_row(
    gate: str,
    status: str,
    metric: str,
    value: str,
    evidence: str,
    detail: str,
) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "metric": metric,
        "value": value,
        "evidence": evidence,
        "detail": detail,
    }


def build_summary(
    full: Dict[str, str],
    noise: Dict[str, str],
    resource: Dict[str, str],
) -> List[Dict[str, str]]:
    precondition = stage78_precondition_passes()
    full_status = full.get("status", "MISSING")
    noise_status = noise.get("status", "MISSING")
    resource_status = resource.get("status", "MISSING")
    rows = [
        summary_row(
            "stage79_stage78_precondition",
            "PASS" if precondition else "FAIL",
            "stage78_decision",
            "PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE",
            STAGE78_SUMMARY.relative_to(ROOT).as_posix(),
            "Stage79 can only confirm a candidate if Stage78 recorded H11 r=6 as a promotion candidate.",
        ),
        summary_row(
            "stage79_r6_high_stat_full_sab",
            full_status,
            "samples;mean;ci95_low;min;r4_mean;r4_ci95_low",
            (
                f"{full.get('samples', '0')};{full.get('mean_speedup', '0')};"
                f"{full.get('ci95_low', '0')};{full.get('min_speedup', '0')};"
                f"{full.get('stage36_r4_mean_reference', '0')};"
                f"{full.get('stage36_r4_ci95_low_reference', '0')}"
            ),
            full.get("source", "MISSING"),
            "Main high-stat complete-SAB A/B gate for r=6 fused MAT.",
        ),
        summary_row(
            "stage79_r6_final_noise",
            noise_status,
            "seeds;points;failures;avg_gap_log2",
            (
                f"{noise.get('seeds', '0')};{noise.get('points', '0')};"
                f"{int(float(noise.get('pvw_failures', '0') or 0)) + int(float(noise.get('scalar_failures', '0') or 0)) + int(float(noise.get('pair_failures', '0') or 0))};"
                f"{noise.get('avg_pvw_minus_scalar_log2', '0')}"
            ),
            noise.get("source", "MISSING"),
            "Expanded final-output noise gate for r=6 fused MAT.",
        ),
        summary_row(
            "stage79_r6_resource",
            resource_status,
            "runs;key_ratio_mean;rss_ratio_mean;rss_ratio_max",
            (
                f"{resource.get('runs', '0')};{resource.get('key_ratio_mean', '0')};"
                f"{resource.get('rss_ratio_mean', '0')};{resource.get('rss_ratio_max', '0')}"
            ),
            RESOURCE_SUMMARY_CSV.relative_to(ROOT).as_posix(),
            "Repeated resource gate for r=6 fused MAT against repeated scalar.",
        ),
    ]

    strong_full = full_status == "PASS_PROMOTION_BOUNDARY_CONFIRMED"
    acceptable_noise = noise_status == "PASS"
    acceptable_resource = resource_status in {"PASS", "REVIEW_RESOURCE_OVERHEAD"}
    if precondition and strong_full and acceptable_noise and resource_status == "PASS":
        decision = "PASS_RGT4_FUSED_HIGH_STAT_CONFIRMED_PROMOTION_CANDIDATE"
        detail = "r=6 fused MAT passes high-stat complete-SAB, noise, and resource gates and clears the r=4 reference boundary; proceed to Stage80 explicit-policy integration audit."
    elif precondition and full_status.startswith("PASS") and acceptable_noise and acceptable_resource:
        decision = "PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED"
        detail = "r=6 fused MAT correctness/noise/resource evidence is usable, but the performance boundary is not strong enough for automatic promotion; Stage80 must keep or reject it explicitly."
    elif precondition and full_status.startswith("PASS"):
        decision = "PASS_RGT4_FUSED_HIGH_STAT_RECORDED_NOT_PROMOTED"
        detail = "The high-stat performance row is recorded, but noise or resource evidence is incomplete; do not promote H11."
    else:
        decision = "FAIL_RGT4_FUSED_HIGH_STAT_CONFIRMATION"
        detail = "Stage79 evidence is missing or failed; do not promote H11."
    rows.append(
        summary_row(
            "stage79_decision",
            decision,
            "promotion_policy",
            "",
            SUMMARY_CSV.relative_to(ROOT).as_posix(),
            detail,
        )
    )
    return rows


def write_md(
    summary: List[Dict[str, str]],
    full: Dict[str, str],
    noise_rows_data: List[Dict[str, str]],
    resource_rows_data: List[Dict[str, str]],
) -> None:
    decision = summary[-1]
    lines = [
        "# Stage79 R>4 Fused High-Stat Confirmation Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage79 confirms or rejects the Stage78 r=6 fused-MAT promotion",
        "candidate using higher-stat complete-SAB evidence plus expanded",
        "noise and repeated resource gates. It does not change scalar SAB,",
        "the r=2/r=4 explicit path, or defaults.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail |",
        "|---|---|---|---|---|---|",
    ]
    for item in summary:
        lines.append(
            f"| {item['gate']} | {item['status']} | {item['metric']} | {item['value']} | {item['evidence']} | {item['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Complete-SAB A/B",
            "",
            "| r | samples | status | PVW mean us | scalar repeated mean us | mean speedup | min | max | stddev | CI95 low | CI95 high | Stage36 r4 mean | Stage36 r4 CI95 low | Stage78 r6 mean | source |",
            "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
            (
                f"| {full['r']} | {full['samples']} | {full['status']} | {full['pvw_mean_us']} | "
                f"{full['scalar_repeated_mean_us']} | {full['mean_speedup']} | {full['min_speedup']} | "
                f"{full['max_speedup']} | {full['stddev_speedup']} | {full['ci95_low']} | "
                f"{full['ci95_high']} | {full['stage36_r4_mean_reference']} | "
                f"{full['stage36_r4_ci95_low_reference']} | {full['stage78_r6_mean_reference']} | {full['source']} |"
            ),
            "",
            "## Noise",
            "",
            "| r | seeds | points | failures | min gap | max gap | avg gap | status | source |",
            "|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in noise_rows_data:
        failures = (
            int(float(item["pvw_failures"] or 0))
            + int(float(item["scalar_failures"] or 0))
            + int(float(item["pair_failures"] or 0))
        )
        lines.append(
            f"| {item['r']} | {item['seeds']} | {item['points']} | {failures} | "
            f"{item['min_pvw_minus_scalar_log2']} | {item['max_pvw_minus_scalar_log2']} | "
            f"{item['avg_pvw_minus_scalar_log2']} | {item['status']} | {item['source']} |"
        )
    lines.extend(
        [
            "",
            "## Resource",
            "",
            "| r | runs | key ratio mean | keygen ratio mean | RSS ratio mean | RSS ratio max | status | sources |",
            "|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in resource_rows_data:
        lines.append(
            f"| {item['r']} | {item['runs']} | {item['key_ratio_mean']} | "
            f"{item['keygen_ratio_mean']} | {item['rss_ratio_mean']} | "
            f"{item['rss_ratio_max']} | {item['status']} | {item['source_csvs']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{decision['status']}`",
            "",
            decision["detail"],
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    full = full_sab_row()
    noise = noise_rows()
    samples = resource_samples()
    resource = resource_summary(samples)
    summary = build_summary(full, noise[0], resource[0])

    write_csv(
        FULL_SAB_CSV,
        [full],
        [
            "r",
            "samples",
            "statuses",
            "pvw_mean_us",
            "scalar_repeated_mean_us",
            "mean_speedup",
            "min_speedup",
            "max_speedup",
            "stddev_speedup",
            "ci95_low",
            "ci95_high",
            "stage36_r4_mean_reference",
            "stage36_r4_ci95_low_reference",
            "stage36_r4_ci95_high_reference",
            "stage78_r6_mean_reference",
            "stage78_r6_min_reference",
            "status",
            "source",
        ],
    )
    write_csv(
        NOISE_SUMMARY_CSV,
        noise,
        [
            "r",
            "seeds",
            "points",
            "pvw_failures",
            "scalar_failures",
            "pair_failures",
            "min_pvw_minus_scalar_log2",
            "max_pvw_minus_scalar_log2",
            "avg_pvw_minus_scalar_log2",
            "status",
            "source",
        ],
    )
    write_csv(
        RESOURCE_SAMPLES_CSV,
        samples,
        [
            "run_index",
            "run_label",
            "backend",
            "r",
            "mode",
            "keygen_us",
            "keygen_lane_avg_us",
            "estimated_key_bytes",
            "estimated_key_bytes_ratio_vs_scalar_repeated",
            "internal_vmhwm_kb",
            "time_max_rss_kb",
            "source_log",
            "time_log",
            "notes",
            "source_csv",
        ],
    )
    write_csv(
        RESOURCE_SUMMARY_CSV,
        resource,
        [
            "r",
            "runs",
            "key_ratio_mean",
            "key_ratio_min",
            "key_ratio_max",
            "keygen_ratio_mean",
            "rss_ratio_mean",
            "rss_ratio_min",
            "rss_ratio_max",
            "pvw_rss_mean_kb",
            "scalar_rss_mean_kb",
            "status",
            "source_csvs",
        ],
    )
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail"])
    write_md(summary, full, noise, resource)

    decision = summary[-1]["status"]
    print(f"Wrote {FULL_SAB_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {NOISE_SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {RESOURCE_SAMPLES_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {RESOURCE_SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage79 r>4 fused high-stat confirmation: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
