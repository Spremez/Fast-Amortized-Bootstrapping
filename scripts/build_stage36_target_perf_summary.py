#!/usr/bin/env python3
"""Aggregate Stage 36 target full-SAB performance samples."""

from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = ROOT / "repro/stage36_target_perf_samples.csv"
SUMMARY_CSV = ROOT / "repro/stage36_target_perf_summary.csv"
EXCLUSION_CSV = ROOT / "repro/stage36_target_perf_exclusions.csv"
SUPPLEMENTAL_CSV = ROOT / "repro/stage36_target_perf_supplemental.csv"

INPUTS = [
    ("target_r2_runs10", 2, ROOT / "repro/stage36_target_perf_r2_runs10/summary.csv"),
    ("target_r4_runs10_initial", 4, ROOT / "repro/stage36_target_perf_r4_runs10/summary.csv"),
]

SUPPLEMENTAL_INPUTS = [
    ("target_r4_runs2_topup", 4, ROOT / "repro/stage36_target_perf_r4_runs2_topup/summary.csv"),
]

PARTIAL_LOGS = [
    (
        "target_r4_runs10_initial",
        4,
        ROOT / "repro/stage36_target_perf_r4_runs10/run_8.log",
        "tool_timeout_partial_log_no_summary_line",
    )
]

T_CRITICAL_95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def tcrit_95(n: int) -> float:
    df = max(1, n - 1)
    return T_CRITICAL_95.get(df, 1.96)


def read_samples() -> List[Dict[str, str]]:
    samples: List[Dict[str, str]] = []
    for source_label, r, path in INPUTS:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                samples.append(
                    {
                        "sample_id": f"{source_label}_run_{row['run']}",
                        "source_label": source_label,
                        "r": str(r),
                        "local_run": row["run"],
                        "status": row["status"],
                        "pvw_avg_us": row["pvw_avg_us"],
                        "scalar_repeated_avg_us": row["scalar_repeated_avg_us"],
                        "speedup_vs_scalar_repeated": row["speedup_vs_scalar_repeated"],
                        "source_csv": str(path.relative_to(ROOT)).replace("\\", "/"),
                    }
                )
    return samples


def read_supplemental_samples() -> List[Dict[str, str]]:
    samples: List[Dict[str, str]] = []
    for source_label, r, path in SUPPLEMENTAL_INPUTS:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                samples.append(
                    {
                        "sample_id": f"{source_label}_run_{row['run']}",
                        "source_label": source_label,
                        "r": str(r),
                        "local_run": row["run"],
                        "status": row["status"],
                        "pvw_avg_us": row["pvw_avg_us"],
                        "scalar_repeated_avg_us": row["scalar_repeated_avg_us"],
                        "speedup_vs_scalar_repeated": row["speedup_vs_scalar_repeated"],
                        "source_csv": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "decision": "SUPPLEMENTAL_NOT_IN_PRIMARY_10RUN",
                    }
                )
    return samples


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize(samples: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in sorted({sample["r"] for sample in samples}, key=int):
        group = [sample for sample in samples if sample["r"] == r]
        speeds = [float(sample["speedup_vs_scalar_repeated"]) for sample in group]
        pvw = [float(sample["pvw_avg_us"]) for sample in group]
        scalar = [float(sample["scalar_repeated_avg_us"]) for sample in group]
        statuses = sorted({sample["status"] for sample in group})
        n = len(group)
        mean_speedup = statistics.mean(speeds)
        stddev = statistics.stdev(speeds) if n > 1 else 0.0
        margin = tcrit_95(n) * stddev / math.sqrt(n) if n > 1 else 0.0
        source_labels = ";".join(sorted({sample["source_label"] for sample in group}))
        decision = "PASS_TARGET_PERF_10RUN" if n >= 10 and statuses == ["Pass"] and mean_speedup > 1.0 else "INCOMPLETE_OR_FAIL"
        notes = "complete 10 sample aggregate"
        if r == "4":
            notes = "complete initial 10 sample aggregate; command hit tool timeout but artifacts completed"
        rows.append(
            {
                "r": r,
                "samples": str(n),
                "statuses": "+".join(statuses),
                "pvw_mean_us": f"{statistics.mean(pvw):.3f}",
                "scalar_repeated_mean_us": f"{statistics.mean(scalar):.3f}",
                "mean_speedup": f"{mean_speedup:.3f}",
                "min_speedup": f"{min(speeds):.3f}",
                "max_speedup": f"{max(speeds):.3f}",
                "stddev_speedup": f"{stddev:.6f}",
                "ci95_low": f"{mean_speedup - margin:.6f}",
                "ci95_high": f"{mean_speedup + margin:.6f}",
                "decision": decision,
                "source_labels": source_labels,
                "notes": notes,
            }
        )
    return rows


def exclusion_rows() -> List[Dict[str, str]]:
    rows = []
    for source_label, r, path, reason in PARTIAL_LOGS:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            has_summary = "SAB_PVW_BENCH summary target_full" in text
            rows.append(
                {
                    "source_label": source_label,
                    "r": str(r),
                    "log": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "reason": reason,
                    "has_summary_line": "yes" if has_summary else "no",
                    "decision": "EXCLUDE" if not has_summary else "NOT_EXCLUDED_COMPLETED_AFTER_TIMEOUT",
                }
            )
    return rows


def main() -> int:
    samples = read_samples()
    if not samples:
        raise SystemExit("no Stage 36 target performance samples found")

    write_csv(
        SAMPLE_CSV,
        samples,
        [
            "sample_id",
            "source_label",
            "r",
            "local_run",
            "status",
            "pvw_avg_us",
            "scalar_repeated_avg_us",
            "speedup_vs_scalar_repeated",
            "source_csv",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summarize(samples),
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
            "decision",
            "source_labels",
            "notes",
        ],
    )
    write_csv(
        EXCLUSION_CSV,
        exclusion_rows(),
        ["source_label", "r", "log", "reason", "has_summary_line", "decision"],
    )
    write_csv(
        SUPPLEMENTAL_CSV,
        read_supplemental_samples(),
        [
            "sample_id",
            "source_label",
            "r",
            "local_run",
            "status",
            "pvw_avg_us",
            "scalar_repeated_avg_us",
            "speedup_vs_scalar_repeated",
            "source_csv",
            "decision",
        ],
    )
    print(f"Stage 36 target perf samples: {SAMPLE_CSV.relative_to(ROOT)}")
    print(f"Stage 36 target perf summary: {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"Stage 36 target perf exclusions: {EXCLUSION_CSV.relative_to(ROOT)}")
    print(f"Stage 36 target perf supplemental: {SUPPLEMENTAL_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
