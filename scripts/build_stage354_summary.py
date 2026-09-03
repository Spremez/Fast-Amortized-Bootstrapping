#!/usr/bin/env python3
"""Parse Stage354 (E1 binary matrix expansion) raw logs into a summary CSV.

Reads repro/stage354_e1_binary_matrix_expansion/raw/<case>/{perf,noise}/ and
emits repro/stage354_e1_binary_matrix_expansion/stage354_summary.csv with the
same metric family as Stage340-345: complete-SAB T_bootstrap/r versus repeated
scalar, plus correctness/noise gate status and peak RSS. Safe to re-run while
the driver is still working: incomplete cases are reported as PENDING.
"""

from __future__ import annotations

import csv
import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "repro" / "stage354_e1_binary_matrix_expansion" / "raw"
OUT = ROOT / "repro" / "stage354_e1_binary_matrix_expansion" / "stage354_summary.csv"
T975 = 2.262  # two-sided t(9, 0.975)


def _field(text: str, name: str) -> float:
    match = re.search(rf"{name}=([\d.]+)", text)
    if match is None:
        raise ValueError(f"field {name} not found")
    return float(match.group(1))


def parse_case(case_dir: Path) -> dict[str, str] | None:
    perf_dir = case_dir / "perf"
    run_logs = sorted(perf_dir.glob("run_*.log"))
    if not run_logs:
        return None
    pvw: list[float] = []
    scalar: list[float] = []
    speedups: list[float] = []
    correctness = set()
    for log in run_logs:
        text = log.read_text()
        if "correctness" not in text:
            continue
        ok = re.search(r"correctness .*?: (\w+)", text)
        correctness.add(ok.group(1) if ok else "UNKNOWN")
        try:
            pvw.append(_field(text, "pvw_lane_us"))
            scalar.append(_field(text, "scalar_lane_us"))
            speedups.append(_field(text, "speedup"))
        except ValueError:
            continue
    if len(pvw) < 2:
        return None
    row = {
        "case": case_dir.name,
        "samples": str(len(pvw)),
        "correctness": "+".join(sorted(correctness)),
        "pvw_lane_mean_us": f"{statistics.mean(pvw):.3f}",
        "scalar_lane_mean_us": f"{statistics.mean(scalar):.3f}",
        "speedup_mean": f"{statistics.mean(speedups):.6f}",
        "speedup_min": f"{min(speedups):.6f}",
        "speedup_max": f"{max(speedups):.6f}",
    }
    if len(pvw) >= 3:
        h = T975 * statistics.stdev(pvw) / math.sqrt(len(pvw))
        row["pvw_ci95_lo_us"] = f"{statistics.mean(pvw) - h:.3f}"
        row["pvw_ci95_hi_us"] = f"{statistics.mean(pvw) + h:.3f}"
    else:
        row["pvw_ci95_lo_us"] = ""
        row["pvw_ci95_hi_us"] = ""
    noise_log = case_dir / "noise" / "run.log"
    time_log = case_dir / "noise" / "time.log"
    if noise_log.is_file():
        summary = re.search(r"summary .* gate=(\w+)", noise_log.read_text())
        row["noise_gate"] = summary.group(1) if summary else "UNKNOWN"
    else:
        row["noise_gate"] = "PENDING"
    if time_log.is_file():
        rss = re.search(r"Maximum resident set size \(kbytes\): (\d+)", time_log.read_text())
        row["max_rss_kb"] = rss.group(1) if rss else ""
    else:
        row["max_rss_kb"] = ""
    return row


def main() -> int:
    rows = []
    for case_dir in sorted(RAW.iterdir() if RAW.is_dir() else []):
        if not case_dir.is_dir():
            continue
        row = parse_case(case_dir)
        if row is not None:
            rows.append(row)
    if not rows:
        print("no completed cases yet", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(
            f"{row['case']}: n={row['samples']} speedup={row['speedup_mean']} "
            f"(range {row['speedup_min']}..{row['speedup_max']}) "
            f"noise={row['noise_gate']} rss={row['max_rss_kb'] or 'PENDING'}KB"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
