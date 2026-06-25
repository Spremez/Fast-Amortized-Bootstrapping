#!/usr/bin/env python3
"""Summarize the Stage 36 added-parameter 10-run/20-seed campaign."""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "repro" / "stage36_added_params_runs10_seeds20"
OUT_MD = ROOT / "docs" / "stage36_added_params_expansion_log.md"

EXPECTED_KEYS = [
    ("SET_4_5_2048", "2"),
    ("SET_4_5_2048", "4"),
    ("SET_2_3_4096", "2"),
    ("SET_2_3_4096", "4"),
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
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def parse_perf_dir(name: str) -> Tuple[str, str] | None:
    match = re.match(r"^perf_(SET_\d+_\d+_\d+)_r(\d+)_runs\d+(?:_.*)?$", name)
    if not match:
        return None
    return match.group(1), match.group(2)


def parse_noise_dir(name: str) -> Tuple[str, str] | None:
    match = re.match(r"^noise_(SET_\d+_\d+_\d+)_r(\d+)_seeds\d+(?:_.*)?$", name)
    if not match:
        return None
    return match.group(1), match.group(2)


def as_float(row: Dict[str, str], key: str) -> float:
    return float(row.get(key, "nan"))


def as_int(row: Dict[str, str], key: str) -> int:
    return int(float(row.get(key, "0")))


def build_performance(
    out_dir: Path,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    samples_by_key: Dict[Tuple[str, str], List[Dict[str, str]]] = {key: [] for key in EXPECTED_KEYS}
    for summary in sorted(out_dir.glob("perf_*_r*_runs*/summary.csv")):
        parsed = parse_perf_dir(summary.parent.name)
        if parsed is None or parsed not in samples_by_key:
            continue
        rows = read_csv(summary)
        for row in rows:
            sample = {
                "param": parsed[0],
                "r": parsed[1],
                "sample_id": f"{summary.parent.name}:run_{row.get('run', '')}",
                "status": row.get("status", ""),
                "pvw_avg_us": row.get("pvw_avg_us", ""),
                "scalar_repeated_avg_us": row.get("scalar_repeated_avg_us", ""),
                "speedup_vs_scalar_repeated": row.get("speedup_vs_scalar_repeated", ""),
                "source_csv": rel(summary),
            }
            samples_by_key[parsed].append(sample)

    sample_rows: List[Dict[str, str]] = []
    supplemental_rows: List[Dict[str, str]] = []
    summary_rows: List[Dict[str, str]] = []
    stats_rows: List[Dict[str, str]] = []
    for key in EXPECTED_KEYS:
        all_samples = samples_by_key[key]
        samples = all_samples[:10]
        supplemental = all_samples[10:]
        sample_rows.extend(samples)
        for row in supplemental:
            extra = dict(row)
            extra["decision"] = "SUPPLEMENTAL_NOT_IN_PRIMARY_10RUN"
            supplemental_rows.append(extra)
        speeds = [as_float(row, "speedup_vs_scalar_repeated") for row in samples]
        pvw = [as_float(row, "pvw_avg_us") for row in samples]
        scalar = [as_float(row, "scalar_repeated_avg_us") for row in samples]
        statuses = sorted({row.get("status", "") for row in samples})
        status = "PASS" if statuses == ["Pass"] else "+".join(statuses) if statuses else "MISSING"
        runs = len(samples)
        if speeds:
            mean_speedup = statistics.mean(speeds)
            min_speedup = min(speeds)
            max_speedup = max(speeds)
            stddev = statistics.stdev(speeds) if len(speeds) > 1 else 0.0
            sem = stddev / math.sqrt(len(speeds)) if speeds else 0.0
            tcrit = T_CRITICAL_95.get(len(speeds) - 1, 1.96)
            ci_half = tcrit * sem
            decision = (
                "PASS_ADDED_PARAM_10RUN"
                if runs >= 10 and status == "PASS" and mean_speedup > 1.0
                else "PARTIAL_ADDED_PARAM_PERF"
            )
            summary_rows.append(
                {
                    "param": key[0],
                    "r": key[1],
                    "runs": str(runs),
                    "status": status,
                    "pvw_mean_us": f"{statistics.mean(pvw):.3f}",
                    "scalar_repeated_mean_us": f"{statistics.mean(scalar):.3f}",
                    "mean_speedup": f"{mean_speedup:.6f}",
                    "min_speedup": f"{min_speedup:.6f}",
                    "max_speedup": f"{max_speedup:.6f}",
                    "decision": decision,
                }
            )
            stats_rows.append(
                {
                    "param": key[0],
                    "r": key[1],
                    "runs": str(runs),
                    "mean_speedup": f"{mean_speedup:.6f}",
                    "min_speedup": f"{min_speedup:.6f}",
                    "max_speedup": f"{max_speedup:.6f}",
                    "stddev_speedup": f"{stddev:.6f}",
                    "sem_speedup": f"{sem:.6f}",
                    "ci95_halfwidth_t": f"{ci_half:.6f}",
                    "ci95_low_t": f"{mean_speedup - ci_half:.6f}",
                    "ci95_high_t": f"{mean_speedup + ci_half:.6f}",
                    "decision": decision,
                }
            )
        else:
            summary_rows.append(
                {
                    "param": key[0],
                    "r": key[1],
                    "runs": "0",
                    "status": "MISSING",
                    "pvw_mean_us": "",
                    "scalar_repeated_mean_us": "",
                    "mean_speedup": "",
                    "min_speedup": "",
                    "max_speedup": "",
                    "decision": "MISSING_ADDED_PARAM_PERF",
                }
            )
            stats_rows.append(
                {
                    "param": key[0],
                    "r": key[1],
                    "runs": "0",
                    "mean_speedup": "",
                    "min_speedup": "",
                    "max_speedup": "",
                    "stddev_speedup": "",
                    "sem_speedup": "",
                    "ci95_halfwidth_t": "",
                    "ci95_low_t": "",
                    "ci95_high_t": "",
                    "decision": "MISSING_ADDED_PARAM_PERF",
                }
            )
    return sample_rows, supplemental_rows, summary_rows, stats_rows


def build_noise(out_dir: Path) -> List[Dict[str, str]]:
    rows_by_key: Dict[Tuple[str, str], Dict[str, str]] = {}
    for aggregate in sorted(out_dir.glob("noise_*_r*_seeds*/aggregate.csv")):
        parsed = parse_noise_dir(aggregate.parent.name)
        if parsed is None or parsed not in EXPECTED_KEYS:
            continue
        rows = read_csv(aggregate)
        if len(rows) != 1:
            continue
        row = rows[0]
        pass_20 = (
            row.get("status") == "PASS"
            and as_int(row, "seeds") >= 20
            and as_int(row, "pvw_failures") == 0
            and as_int(row, "scalar_failures") == 0
            and as_int(row, "pair_failures") == 0
        )
        rows_by_key[parsed] = {
            "param": parsed[0],
            "r": parsed[1],
            "seeds": row.get("seeds", ""),
            "points": row.get("points", ""),
            "pvw_failures": row.get("pvw_failures", ""),
            "scalar_failures": row.get("scalar_failures", ""),
            "pair_failures": row.get("pair_failures", ""),
            "min_pvw_minus_scalar_log2": row.get("min_pvw_minus_scalar_log2", ""),
            "max_pvw_minus_scalar_log2": row.get("max_pvw_minus_scalar_log2", ""),
            "avg_pvw_minus_scalar_log2": row.get("avg_pvw_minus_scalar_log2", ""),
            "status": row.get("status", ""),
            "decision": "PASS_ADDED_PARAM_20SEED" if pass_20 else "PARTIAL_ADDED_PARAM_NOISE",
            "source_csv": rel(aggregate),
        }

    out: List[Dict[str, str]] = []
    for key in EXPECTED_KEYS:
        out.append(
            rows_by_key.get(
                key,
                {
                    "param": key[0],
                    "r": key[1],
                    "seeds": "0",
                    "points": "0",
                    "pvw_failures": "",
                    "scalar_failures": "",
                    "pair_failures": "",
                    "min_pvw_minus_scalar_log2": "",
                    "max_pvw_minus_scalar_log2": "",
                    "avg_pvw_minus_scalar_log2": "",
                    "status": "MISSING",
                    "decision": "MISSING_ADDED_PARAM_NOISE",
                    "source_csv": "",
                },
            )
        )
    return out


def markdown_table(rows: List[Dict[str, str]], fields: List[str]) -> List[str]:
    lines = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return lines


def write_doc(
    out_dir: Path,
    performance: List[Dict[str, str]],
    stats: List[Dict[str, str]],
    supplemental: List[Dict[str, str]],
    noise: List[Dict[str, str]],
) -> None:
    perf_ok = all(row["decision"] == "PASS_ADDED_PARAM_10RUN" for row in stats)
    noise_ok = all(row["decision"] == "PASS_ADDED_PARAM_20SEED" for row in noise)
    decision = (
        "PASS_ADDED_PARAM_10RUN_20SEED"
        if perf_ok and noise_ok
        else "PARTIAL_ADDED_PARAM_EVIDENCE"
    )
    lines = [
        "# Stage 36 Added-Parameter Expansion Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "This log summarizes the optional Stage 36 added-binary parameter",
        "campaign. It extends the Stage 26 added-parameter evidence from",
        "5-run/5-seed support to the pre-registered 10-run/20-seed budget for",
        "`SET_4_5_2048` and `SET_2_3_4096`, r=2/4.",
        "",
        "The result does not change scalar SAB or `sab_pvw_*` code and does not",
        "upgrade non-binary, all-parameter, novelty, theorem-level citation, or",
        "hardware-counter claims.",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Performance Summary",
        "",
    ]
    lines.extend(
        markdown_table(
            performance,
            [
                "param",
                "r",
                "runs",
                "status",
                "pvw_mean_us",
                "scalar_repeated_mean_us",
                "mean_speedup",
                "min_speedup",
                "max_speedup",
                "decision",
            ],
        )
    )
    lines.extend(["", "## Performance Statistics", ""])
    lines.extend(
        markdown_table(
            stats,
            [
                "param",
                "r",
                "runs",
                "mean_speedup",
                "stddev_speedup",
                "ci95_low_t",
                "ci95_high_t",
                "decision",
            ],
        )
    )
    if supplemental:
        lines.extend(["", "## Supplemental Performance Samples", ""])
        lines.extend(
            markdown_table(
                supplemental,
                [
                    "param",
                    "r",
                    "sample_id",
                    "speedup_vs_scalar_repeated",
                    "decision",
                ],
            )
        )
    lines.extend(["", "## Noise Summary", ""])
    lines.extend(
        markdown_table(
            noise,
            [
                "param",
                "r",
                "seeds",
                "points",
                "pvw_failures",
                "scalar_failures",
                "pair_failures",
                "min_pvw_minus_scalar_log2",
                "max_pvw_minus_scalar_log2",
                "avg_pvw_minus_scalar_log2",
                "decision",
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The added binary parameters now have local 10-run complete-SAB",
            "performance evidence and 20-seed final-output noise evidence for",
            "r=2 and r=4 under `spqlios_avx512` with the promoted active-buffer",
            "PVW/MAT-SAB path. This strengthens binary parameter-generalization",
            "evidence, but it is still not a claim for non-binary branches or all",
            "possible parameter sets.",
            "",
        ]
    )
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Stage 36 added-parameter output directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    samples, supplemental, performance, stats = build_performance(out_dir)
    noise = build_noise(out_dir)
    write_csv(
        out_dir / "performance_samples.csv",
        samples,
        [
            "param",
            "r",
            "sample_id",
            "status",
            "pvw_avg_us",
            "scalar_repeated_avg_us",
            "speedup_vs_scalar_repeated",
            "source_csv",
        ],
    )
    write_csv(
        out_dir / "performance_supplemental.csv",
        supplemental,
        [
            "param",
            "r",
            "sample_id",
            "status",
            "pvw_avg_us",
            "scalar_repeated_avg_us",
            "speedup_vs_scalar_repeated",
            "source_csv",
            "decision",
        ],
    )
    write_csv(
        out_dir / "performance_summary.csv",
        performance,
        [
            "param",
            "r",
            "runs",
            "status",
            "pvw_mean_us",
            "scalar_repeated_mean_us",
            "mean_speedup",
            "min_speedup",
            "max_speedup",
            "decision",
        ],
    )
    write_csv(
        out_dir / "performance_stats.csv",
        stats,
        [
            "param",
            "r",
            "runs",
            "mean_speedup",
            "min_speedup",
            "max_speedup",
            "stddev_speedup",
            "sem_speedup",
            "ci95_halfwidth_t",
            "ci95_low_t",
            "ci95_high_t",
            "decision",
        ],
    )
    write_csv(
        out_dir / "noise_summary.csv",
        noise,
        [
            "param",
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
            "decision",
            "source_csv",
        ],
    )
    write_doc(out_dir, performance, stats, supplemental, noise)
    print(f"Stage36 added-parameter performance summary: {rel(out_dir / 'performance_summary.csv')}")
    print(f"Stage36 added-parameter performance stats: {rel(out_dir / 'performance_stats.csv')}")
    print(f"Stage36 added-parameter noise summary: {rel(out_dir / 'noise_summary.csv')}")
    print(f"Stage36 added-parameter log: {rel(OUT_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
