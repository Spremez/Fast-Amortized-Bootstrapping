#!/usr/bin/env python3
"""Aggregate Stage 36 repeated resource snapshots."""

from __future__ import annotations

import csv
import glob
import statistics
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "repro/stage36_resource_summary.csv"
SAMPLES_CSV = ROOT / "repro/stage36_resource_samples.csv"


def read_samples() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for path_str in sorted(glob.glob(str(ROOT / "repro/stage36_resource_run_*/summary.csv"))):
        path = Path(path_str)
        run_label = path.parent.name
        run_index = run_label.rsplit("_", 1)[-1]
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                item = dict(row)
                item["run_index"] = run_index
                item["run_label"] = run_label
                item["source_csv"] = str(path.relative_to(ROOT)).replace("\\", "/")
                rows.append(item)
    return rows


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fmean(values: List[float]) -> str:
    return f"{statistics.mean(values):.3f}"


def summarize(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    keys = sorted({(row["r"], row["mode"]) for row in rows}, key=lambda x: (int(x[0]), x[1]))
    for r, mode in keys:
        group = [row for row in rows if row["r"] == r and row["mode"] == mode]
        keygen = [float(row["keygen_us"]) for row in group]
        lane = [float(row["keygen_lane_avg_us"]) for row in group]
        ratio = [float(row["estimated_key_bytes_ratio_vs_scalar_repeated"]) for row in group]
        internal = [float(row["internal_vmhwm_kb"]) for row in group]
        rss = [float(row["time_max_rss_kb"]) for row in group]
        key_bytes = sorted({row["estimated_key_bytes"] for row in group})
        source_csvs = ";".join(sorted({row["source_csv"] for row in group}))
        decision = "PASS_RESOURCE_3RUN" if len(group) >= 3 else "INCOMPLETE_RESOURCE"
        out.append(
            {
                "r": r,
                "mode": mode,
                "runs": str(len(group)),
                "keygen_mean_us": fmean(keygen),
                "keygen_min_us": f"{min(keygen):.3f}",
                "keygen_max_us": f"{max(keygen):.3f}",
                "keygen_lane_mean_us": fmean(lane),
                "keygen_lane_min_us": f"{min(lane):.3f}",
                "keygen_lane_max_us": f"{max(lane):.3f}",
                "estimated_key_bytes": "|".join(key_bytes),
                "key_bytes_ratio_mean": fmean(ratio),
                "key_bytes_ratio_min": f"{min(ratio):.6f}",
                "key_bytes_ratio_max": f"{max(ratio):.6f}",
                "internal_vmhwm_mean_kb": fmean(internal),
                "internal_vmhwm_max_kb": f"{max(internal):.3f}",
                "time_max_rss_mean_kb": fmean(rss),
                "time_max_rss_max_kb": f"{max(rss):.3f}",
                "decision": decision,
                "source_csvs": source_csvs,
            }
        )
    return out


def main() -> int:
    samples = read_samples()
    if not samples:
        raise SystemExit("no Stage 36 resource samples found")

    sample_fields = [
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
        "source_csv",
        "notes",
    ]
    write_csv(SAMPLES_CSV, samples, sample_fields)
    write_csv(
        OUT_CSV,
        summarize(samples),
        [
            "r",
            "mode",
            "runs",
            "keygen_mean_us",
            "keygen_min_us",
            "keygen_max_us",
            "keygen_lane_mean_us",
            "keygen_lane_min_us",
            "keygen_lane_max_us",
            "estimated_key_bytes",
            "key_bytes_ratio_mean",
            "key_bytes_ratio_min",
            "key_bytes_ratio_max",
            "internal_vmhwm_mean_kb",
            "internal_vmhwm_max_kb",
            "time_max_rss_mean_kb",
            "time_max_rss_max_kb",
            "decision",
            "source_csvs",
        ],
    )
    print(f"Stage 36 resource samples: {SAMPLES_CSV.relative_to(ROOT)}")
    print(f"Stage 36 resource summary: {OUT_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
