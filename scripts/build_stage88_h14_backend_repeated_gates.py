#!/usr/bin/env python3
"""Build the Stage88 H14 backend repeated/noise/resource gate report."""

from __future__ import annotations

import csv
import glob
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage88_h14_backend_repeated_gates"
FULL_SAB_CSV = OUT_DIR / "full_sab_repeated.csv"
BACKEND_WRAPPER_CSV = OUT_DIR / "backend_vs_wrapper.csv"
NOISE_SUMMARY_CSV = OUT_DIR / "noise_summary.csv"
RESOURCE_SAMPLES_CSV = OUT_DIR / "resource_samples.csv"
RESOURCE_SUMMARY_CSV = OUT_DIR / "resource_summary.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage88_h14_backend_repeated_gates_log.md"

STAGE87_SUMMARY = ROOT / "repro" / "stage87_h14_backend_from_dft_add_preflight" / "summary.csv"
NOISE_AGGREGATE = OUT_DIR / "final_noise" / "aggregate.csv"

MIN_FULL_RUNS = 3
MIN_NOISE_SEEDS = 3
MIN_RESOURCE_RUNS = 1
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


def find_variant_summary(variant: str, r: str = "6") -> Path | None:
    candidates = sorted(
        OUT_DIR.glob(f"full_sab_{variant}_r{r}_runs*/summary.csv"),
        key=lambda p: (len(read_csv(p)), p.as_posix()),
        reverse=True,
    )
    return candidates[0] if candidates else None


def summarize_variant(variant: str, r: str = "6") -> Dict[str, str]:
    path = find_variant_summary(variant, r)
    rows = read_csv(path) if path else []
    speedups = [fnum(row, "speedup_vs_scalar_repeated") for row in rows]
    pvw = [fnum(row, "pvw_avg_us") for row in rows]
    scalar = [fnum(row, "scalar_repeated_avg_us") for row in rows]
    statuses = sorted({row.get("status", "") for row in rows})
    samples = len(rows)
    all_pass = bool(rows) and all(row.get("status") == "Pass" for row in rows)
    speed_mean = mean(speedups) if speedups else 0.0
    speed_min = min(speedups) if speedups else 0.0
    status = "PASS" if all_pass and samples >= MIN_FULL_RUNS and speed_min > 1.0 else "FAIL"
    if all_pass and samples < MIN_FULL_RUNS:
        status = "INSUFFICIENT_REPEATS"
    return {
        "variant": variant,
        "r": r,
        "samples": str(samples),
        "statuses": ";".join(statuses) if statuses else "MISSING",
        "pvw_mean_us": f"{mean(pvw):.3f}" if pvw else "0.000",
        "pvw_min_us": f"{min(pvw):.3f}" if pvw else "0.000",
        "pvw_max_us": f"{max(pvw):.3f}" if pvw else "0.000",
        "scalar_repeated_mean_us": f"{mean(scalar):.3f}" if scalar else "0.000",
        "mean_speedup_vs_scalar": f"{speed_mean:.3f}",
        "min_speedup_vs_scalar": f"{speed_min:.3f}",
        "max_speedup_vs_scalar": f"{max(speedups):.3f}" if speedups else "0.000",
        "stddev_speedup_vs_scalar": f"{stdev(speedups):.6f}" if len(speedups) > 1 else "0.000000",
        "status": status,
        "source": path.relative_to(ROOT).as_posix() if path else "MISSING",
    }


def backend_vs_wrapper_row(r: str = "6") -> Dict[str, str]:
    wrapper_path = find_variant_summary("wrapper", r)
    backend_path = find_variant_summary("backend", r)
    wrapper_rows = {row.get("run"): row for row in read_csv(wrapper_path) if row.get("run") is not None} if wrapper_path else {}
    backend_rows = {row.get("run"): row for row in read_csv(backend_path) if row.get("run") is not None} if backend_path else {}
    paired = sorted(set(wrapper_rows) & set(backend_rows), key=lambda x: int(x))
    ratios = []
    for run in paired:
        backend_pvw = fnum(backend_rows[run], "pvw_avg_us")
        wrapper_pvw = fnum(wrapper_rows[run], "pvw_avg_us")
        if backend_pvw > 0:
            ratios.append(wrapper_pvw / backend_pvw)
    ratio_mean = mean(ratios) if ratios else 0.0
    ratio_min = min(ratios) if ratios else 0.0
    ratio_max = max(ratios) if ratios else 0.0
    if len(paired) < MIN_FULL_RUNS:
        status = "INSUFFICIENT_REPEATS"
    elif ratio_mean > 1.0 and ratio_min > 1.0:
        status = "PASS_BACKEND_FASTER"
    elif ratio_mean > 1.0:
        status = "PASS_MEAN_POSITIVE_REVIEW_MIN"
    elif ratios:
        status = "NEUTRAL_OR_NEGATIVE"
    else:
        status = "MISSING"
    return {
        "r": r,
        "paired_runs": str(len(paired)),
        "backend_vs_wrapper_mean": f"{ratio_mean:.6f}",
        "backend_vs_wrapper_min": f"{ratio_min:.6f}",
        "backend_vs_wrapper_max": f"{ratio_max:.6f}",
        "status": status,
        "wrapper_source": wrapper_path.relative_to(ROOT).as_posix() if wrapper_path else "MISSING",
        "backend_source": backend_path.relative_to(ROOT).as_posix() if backend_path else "MISSING",
    }


def noise_row(r: str = "6") -> Dict[str, str]:
    rows = {row.get("r"): row for row in read_csv(NOISE_AGGREGATE)}
    row = rows.get(r, {})
    seeds = int(float(row.get("seeds", "0") or 0)) if row else 0
    failures = (
        int(float(row.get("pvw_failures", "0") or 0))
        + int(float(row.get("scalar_failures", "0") or 0))
        + int(float(row.get("pair_failures", "0") or 0))
    )
    if row.get("status") == "PASS" and failures == 0 and seeds >= MIN_NOISE_SEEDS:
        status = "PASS"
    elif row.get("status") == "PASS" and failures == 0:
        status = "PASS_INSUFFICIENT_SEEDS"
    elif row:
        status = "FAIL"
    else:
        status = "MISSING"
    return {
        "r": r,
        "seeds": row.get("seeds", "0"),
        "points": row.get("points", "0"),
        "pvw_failures": row.get("pvw_failures", "0"),
        "scalar_failures": row.get("scalar_failures", "0"),
        "pair_failures": row.get("pair_failures", "0"),
        "min_pvw_minus_scalar_log2": row.get("min_pvw_minus_scalar_log2", "0"),
        "max_pvw_minus_scalar_log2": row.get("max_pvw_minus_scalar_log2", "0"),
        "avg_pvw_minus_scalar_log2": row.get("avg_pvw_minus_scalar_log2", "0"),
        "status": status,
        "source": NOISE_AGGREGATE.relative_to(ROOT).as_posix()
        if NOISE_AGGREGATE.exists()
        else "MISSING",
    }


def resource_samples(r: str = "6") -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path_str in sorted(glob.glob(str(OUT_DIR / "resource_run_*" / "summary.csv"))):
        path = Path(path_str)
        run_label = path.parent.name
        run_index = run_label.rsplit("_", 1)[-1]
        for row in read_csv(path):
            if row.get("r") != r:
                continue
            item = dict(row)
            item["run_index"] = run_index
            item["run_label"] = run_label
            item["source_csv"] = path.relative_to(ROOT).as_posix()
            rows.append(item)
    return rows


def resource_summary(samples: List[Dict[str, str]], r: str = "6") -> Dict[str, str]:
    pvw = [row for row in samples if row.get("mode") == "pvw"]
    scalar = [row for row in samples if row.get("mode") == "scalar"]
    pvw_by_run = {row.get("run_label"): row for row in pvw}
    scalar_by_run = {row.get("run_label"): row for row in scalar}
    paired_runs = sorted(set(pvw_by_run) & set(scalar_by_run))
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
    status = "PASS" if len(paired_runs) >= MIN_RESOURCE_RUNS and key_ratios and rss_ratios else "INCOMPLETE_RESOURCE"
    if status == "PASS" and (not math.isfinite(max(rss_ratios)) or max(rss_ratios) > RESOURCE_RSS_REVIEW_RATIO):
        status = "REVIEW_RESOURCE_OVERHEAD"
    return {
        "r": r,
        "runs": str(len(paired_runs)),
        "key_ratio_mean": f"{mean(key_ratios):.6f}" if key_ratios else "0.000000",
        "keygen_ratio_mean": f"{mean(keygen_ratios):.6f}" if keygen_ratios else "0.000000",
        "rss_ratio_mean": f"{mean(rss_ratios):.6f}" if rss_ratios else "0.000000",
        "rss_ratio_max": f"{max(rss_ratios):.6f}" if rss_ratios else "0.000000",
        "status": status,
        "source_csvs": ";".join(sorted({row.get("source_csv", "") for row in samples if row.get("source_csv")})) or "MISSING",
    }


def stage87_precondition_passes() -> bool:
    return any(
        row.get("gate") == "stage87_decision"
        and row.get("status")
        == "PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE"
        for row in read_csv(STAGE87_SUMMARY)
    )


def summary_row(gate: str, status: str, metric: str, value: str, evidence: str, detail: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "metric": metric,
        "value": value,
        "evidence": evidence,
        "detail": detail,
    }


def build_summary(
    wrapper: Dict[str, str],
    backend: Dict[str, str],
    comparison: Dict[str, str],
    noise: Dict[str, str],
    resource: Dict[str, str],
) -> List[Dict[str, str]]:
    precondition = stage87_precondition_passes()
    repeated_positive = comparison["status"] == "PASS_BACKEND_FASTER"
    repeated_review = comparison["status"] == "PASS_MEAN_POSITIVE_REVIEW_MIN"
    backend_scalar_pass = backend["status"] == "PASS"
    wrapper_pass = wrapper["status"] == "PASS"
    noise_pass = noise["status"] == "PASS"
    resource_pass = resource["status"] == "PASS"
    resource_review = resource["status"] == "REVIEW_RESOURCE_OVERHEAD"

    rows = [
        summary_row(
            "stage88_stage87_precondition",
            "PASS" if precondition else "FAIL",
            "stage87_decision",
            "PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE",
            STAGE87_SUMMARY.relative_to(ROOT).as_posix(),
            "Stage88 is valid only after Stage87 records H14-C1 as a promotion candidate.",
        ),
        summary_row(
            "stage88_repeated_full_sab",
            comparison["status"],
            "paired_runs;backend_vs_wrapper_mean;min;backend_speedup_mean",
            (
                f"{comparison['paired_runs']};{comparison['backend_vs_wrapper_mean']};"
                f"{comparison['backend_vs_wrapper_min']};{backend['mean_speedup_vs_scalar']}"
            ),
            BACKEND_WRAPPER_CSV.relative_to(ROOT).as_posix(),
            "Repeated complete-SAB gate compares backend FromDFT-add against wrapper fused FromDFT-add.",
        ),
        summary_row(
            "stage88_backend_vs_scalar",
            backend["status"],
            "samples;mean_speedup;min_speedup",
            f"{backend['samples']};{backend['mean_speedup_vs_scalar']};{backend['min_speedup_vs_scalar']}",
            backend["source"],
            "Backend complete-SAB must remain faster than repeated scalar SAB.",
        ),
        summary_row(
            "stage88_wrapper_reference",
            wrapper["status"],
            "samples;mean_speedup;min_speedup",
            f"{wrapper['samples']};{wrapper['mean_speedup_vs_scalar']};{wrapper['min_speedup_vs_scalar']}",
            wrapper["source"],
            "Wrapper fused FromDFT-add is the same-backend reference for H14-C1.",
        ),
        summary_row(
            "stage88_final_noise",
            noise["status"],
            "seeds;points;failures;avg_gap_log2",
            (
                f"{noise['seeds']};{noise['points']};"
                f"{int(float(noise['pvw_failures'] or 0)) + int(float(noise['scalar_failures'] or 0)) + int(float(noise['pair_failures'] or 0))};"
                f"{noise['avg_pvw_minus_scalar_log2']}"
            ),
            noise["source"],
            "Backend final-output correctness/noise gate must have zero PVW/scalar/pair failures.",
        ),
        summary_row(
            "stage88_resource",
            resource["status"],
            "runs;key_ratio_mean;keygen_ratio_mean;rss_ratio_mean;rss_ratio_max",
            (
                f"{resource['runs']};{resource['key_ratio_mean']};"
                f"{resource['keygen_ratio_mean']};{resource['rss_ratio_mean']};"
                f"{resource['rss_ratio_max']}"
            ),
            RESOURCE_SUMMARY_CSV.relative_to(ROOT).as_posix(),
            "Resource gate records backend key size, keygen time, and RSS against repeated scalar.",
        ),
    ]

    if precondition and repeated_positive and backend_scalar_pass and wrapper_pass and noise_pass and resource_pass:
        decision = "PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE"
        detail = "H14-C1 backend FromDFT-add passes repeated complete-SAB, final noise, and resource gates; proceed to promotion-policy integration rather than changing defaults immediately."
    elif precondition and (repeated_positive or repeated_review) and backend_scalar_pass and noise_pass and (resource_pass or resource_review):
        decision = "PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_REVIEW_REQUIRED"
        detail = "H14-C1 has usable repeated/noise/resource evidence, but min-run or resource overhead requires review before promotion."
    elif precondition and backend_scalar_pass and wrapper_pass and noise_pass:
        decision = "PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_NOT_PROMOTED"
        detail = "Stage88 evidence is valid, but backend-vs-wrapper or resource evidence does not justify promotion."
    else:
        decision = "FAIL_STAGE88_H14_BACKEND_REPEATED_GATES"
        detail = "Stage88 evidence is incomplete or failed; keep H14-C1 experimental and do not promote."
    rows.append(summary_row("stage88_decision", decision, "promotion_policy", "", SUMMARY_CSV.relative_to(ROOT).as_posix(), detail))
    return rows


def write_md(
    summary: List[Dict[str, str]],
    full_rows: List[Dict[str, str]],
    comparison: Dict[str, str],
    noise: Dict[str, str],
    resource: Dict[str, str],
) -> None:
    decision = summary[-1]
    lines = [
        "# Stage88 H14 Backend Repeated Gates Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage88 repeats the Stage87 H14-C1 backend FromDFT-add preflight",
        "under complete-SAB conditions. It compares backend materialization",
        "against the wrapper fused FromDFT-add reference, then checks final",
        "noise and resource costs. It does not change scalar SAB or defaults.",
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
            "## Complete-SAB Repeated",
            "",
            "| variant | r | samples | status | PVW mean us | scalar repeated mean us | mean speedup | min speedup | max speedup | source |",
            "|---|---:|---:|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in full_rows:
        lines.append(
            f"| {item['variant']} | {item['r']} | {item['samples']} | {item['status']} | "
            f"{item['pvw_mean_us']} | {item['scalar_repeated_mean_us']} | "
            f"{item['mean_speedup_vs_scalar']} | {item['min_speedup_vs_scalar']} | "
            f"{item['max_speedup_vs_scalar']} | {item['source']} |"
        )
    lines.extend(
        [
            "",
            "## Backend vs Wrapper",
            "",
            "| r | paired runs | mean | min | max | status |",
            "|---:|---:|---:|---:|---:|---|",
            (
                f"| {comparison['r']} | {comparison['paired_runs']} | "
                f"{comparison['backend_vs_wrapper_mean']} | "
                f"{comparison['backend_vs_wrapper_min']} | "
                f"{comparison['backend_vs_wrapper_max']} | {comparison['status']} |"
            ),
            "",
            "## Noise And Resource",
            "",
            "| gate | status | values | source |",
            "|---|---|---|---|",
            (
                f"| noise | {noise['status']} | seeds={noise['seeds']}; "
                f"failures={int(float(noise['pvw_failures'] or 0)) + int(float(noise['scalar_failures'] or 0)) + int(float(noise['pair_failures'] or 0))}; "
                f"avg_gap={noise['avg_pvw_minus_scalar_log2']} | {noise['source']} |"
            ),
            (
                f"| resource | {resource['status']} | runs={resource['runs']}; "
                f"key_ratio={resource['key_ratio_mean']}; "
                f"keygen_ratio={resource['keygen_ratio_mean']}; "
                f"rss_ratio={resource['rss_ratio_mean']} | {resource['source_csvs']} |"
            ),
            "",
            "## Decision",
            "",
            f"`{decision['status']}`",
            "",
            decision["detail"],
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    wrapper = summarize_variant("wrapper")
    backend = summarize_variant("backend")
    comparison = backend_vs_wrapper_row()
    noise = noise_row()
    samples = resource_samples()
    resource = resource_summary(samples)
    full_rows = [wrapper, backend]
    summary = build_summary(wrapper, backend, comparison, noise, resource)

    write_csv(
        FULL_SAB_CSV,
        full_rows,
        [
            "variant",
            "r",
            "samples",
            "statuses",
            "pvw_mean_us",
            "pvw_min_us",
            "pvw_max_us",
            "scalar_repeated_mean_us",
            "mean_speedup_vs_scalar",
            "min_speedup_vs_scalar",
            "max_speedup_vs_scalar",
            "stddev_speedup_vs_scalar",
            "status",
            "source",
        ],
    )
    write_csv(
        BACKEND_WRAPPER_CSV,
        [comparison],
        [
            "r",
            "paired_runs",
            "backend_vs_wrapper_mean",
            "backend_vs_wrapper_min",
            "backend_vs_wrapper_max",
            "status",
            "wrapper_source",
            "backend_source",
        ],
    )
    write_csv(
        NOISE_SUMMARY_CSV,
        [noise],
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
        [resource],
        [
            "r",
            "runs",
            "key_ratio_mean",
            "keygen_ratio_mean",
            "rss_ratio_mean",
            "rss_ratio_max",
            "status",
            "source_csvs",
        ],
    )
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail"])
    write_md(summary, full_rows, comparison, noise, resource)

    decision = summary[-1]["status"]
    print(f"Wrote {FULL_SAB_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {BACKEND_WRAPPER_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {NOISE_SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {RESOURCE_SAMPLES_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {RESOURCE_SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage88 H14 backend repeated gates: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
