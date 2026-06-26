#!/usr/bin/env python3
"""Build the Stage78 r>4 fused-MAT repeated-gates report."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage78_rgt4_fused_repeated_gates"
FULL_SAB_CSV = OUT_DIR / "full_sab_repeated.csv"
NOISE_SUMMARY_CSV = OUT_DIR / "noise_summary.csv"
RESOURCE_SUMMARY_CSV = OUT_DIR / "resource_summary.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage78_rgt4_fused_repeated_gates_log.md"

STAGE36_TARGET = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE77_FULL = ROOT / "repro" / "stage77_rgt4_fused_mat_kernel" / "full_sab_smoke.csv"
STAGE77_SUMMARY = ROOT / "repro" / "stage77_rgt4_fused_mat_kernel" / "summary.csv"
NOISE_AGGREGATE = OUT_DIR / "final_noise" / "aggregate.csv"
RESOURCE_RAW = OUT_DIR / "resource" / "summary.csv"


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
    except ValueError:
        return default


def stage36_r4_reference() -> Dict[str, str]:
    for row in read_csv(STAGE36_TARGET):
        if row.get("r") == "4":
            return row
    return {}


def stage77_full_row(r: str) -> Dict[str, str]:
    for row in read_csv(STAGE77_FULL):
        if row.get("r") == r:
            return row
    return {}


def find_full_summary(r: str) -> Path | None:
    candidates = sorted(
        OUT_DIR.glob(f"full_sab_fused_r{r}_runs*/summary.csv"),
        key=lambda p: (len(read_csv(p)), p.as_posix()),
        reverse=True,
    )
    return candidates[0] if candidates else None


def summarize_full_sab() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    r4 = stage36_r4_reference()
    r4_mean = fnum(r4, "mean_speedup")
    r4_ci_low = fnum(r4, "ci95_low")
    for r in ["6", "8"]:
        path = find_full_summary(r)
        rows = read_csv(path) if path else []
        speedups = [fnum(row, "speedup_vs_scalar_repeated") for row in rows]
        pvw = [fnum(row, "pvw_avg_us") for row in rows]
        scalar = [fnum(row, "scalar_repeated_avg_us") for row in rows]
        statuses = sorted({row.get("status", "") for row in rows})
        samples = len(rows)
        all_pass = bool(rows) and all(row.get("status") == "Pass" for row in rows)
        speedup_mean = mean(speedups) if speedups else 0.0
        speedup_min = min(speedups) if speedups else 0.0
        speedup_max = max(speedups) if speedups else 0.0
        speedup_stddev = stdev(speedups) if len(speedups) > 1 else 0.0
        stage77 = stage77_full_row(r)
        stage77_speedup = fnum(stage77, "fused_speedup_vs_scalar")
        status = "PASS" if all_pass and speedup_min > 1.0 else "FAIL"
        if r == "6" and samples < 3:
            status = "INSUFFICIENT_REPEATS"
        elif r == "8" and samples < 1:
            status = "INSUFFICIENT_STRESS_REPEATS"
        if status == "PASS" and r == "6" and speedup_mean < r4_ci_low:
            status = "PASS_BELOW_R4_CI_LOW"
        elif status == "PASS" and r == "6" and speedup_mean < r4_mean:
            status = "PASS_R4_REGION_HIGH_STAT_REQUIRED"
        out.append(
            {
                "r": r,
                "samples": str(samples),
                "statuses": ";".join(statuses) if statuses else "MISSING",
                "pvw_mean_us": f"{mean(pvw):.3f}" if pvw else "0.000",
                "scalar_repeated_mean_us": f"{mean(scalar):.3f}" if scalar else "0.000",
                "mean_speedup": f"{speedup_mean:.3f}",
                "min_speedup": f"{speedup_min:.3f}",
                "max_speedup": f"{speedup_max:.3f}",
                "stddev_speedup": f"{speedup_stddev:.6f}",
                "stage77_one_run_speedup": f"{stage77_speedup:.3f}",
                "r4_mean_reference": f"{r4_mean:.3f}",
                "r4_ci95_low_reference": f"{r4_ci_low:.6f}",
                "status": status,
                "source": path.relative_to(ROOT).as_posix() if path else "MISSING",
            }
        )
    return out


def summarize_noise() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    rows = {row.get("r"): row for row in read_csv(NOISE_AGGREGATE)}
    for r in ["6", "8"]:
        row = rows.get(r, {})
        status = row.get("status", "MISSING")
        failures = (
            int(float(row.get("pvw_failures", "0") or 0))
            + int(float(row.get("scalar_failures", "0") or 0))
            + int(float(row.get("pair_failures", "0") or 0))
        )
        seeds = int(float(row.get("seeds", "0") or 0)) if row else 0
        if status == "PASS" and failures == 0 and seeds >= 3:
            gate = "PASS"
        elif status == "PASS" and failures == 0:
            gate = "PASS_LOW_SEED"
        else:
            gate = "FAIL" if row else "MISSING"
        out.append(
            {
                "r": r,
                "seeds": row.get("seeds", "0"),
                "points": row.get("points", "0"),
                "pvw_failures": row.get("pvw_failures", "0"),
                "scalar_failures": row.get("scalar_failures", "0"),
                "pair_failures": row.get("pair_failures", "0"),
                "avg_pvw_minus_scalar_log2": row.get("avg_pvw_minus_scalar_log2", "0"),
                "status": gate,
                "source": NOISE_AGGREGATE.relative_to(ROOT).as_posix()
                if NOISE_AGGREGATE.exists()
                else "MISSING",
            }
        )
    return out


def summarize_resource() -> List[Dict[str, str]]:
    raw = read_csv(RESOURCE_RAW)
    by_key = {(row.get("r"), row.get("mode")): row for row in raw}
    out: List[Dict[str, str]] = []
    for r in ["6", "8"]:
        pvw = by_key.get((r, "pvw"), {})
        scalar = by_key.get((r, "scalar"), {})
        pvw_rss = fnum(pvw, "time_max_rss_kb")
        scalar_rss = fnum(scalar, "time_max_rss_kb")
        rss_ratio = pvw_rss / scalar_rss if scalar_rss else 0.0
        key_ratio = fnum(pvw, "estimated_key_bytes_ratio_vs_scalar_repeated")
        keygen_ratio = (
            fnum(pvw, "keygen_us") / fnum(scalar, "keygen_us")
            if fnum(scalar, "keygen_us")
            else 0.0
        )
        status = "PASS" if pvw and scalar and key_ratio > 0 and rss_ratio > 0 else "MISSING"
        if status == "PASS" and (not math.isfinite(rss_ratio) or rss_ratio > 1.25):
            status = "REVIEW_RESOURCE_OVERHEAD"
        out.append(
            {
                "r": r,
                "key_ratio_vs_scalar_repeated": f"{key_ratio:.6f}",
                "keygen_ratio_vs_scalar_repeated": f"{keygen_ratio:.6f}",
                "pvw_time_max_rss_kb": f"{pvw_rss:.0f}",
                "scalar_time_max_rss_kb": f"{scalar_rss:.0f}",
                "rss_ratio_vs_scalar_repeated": f"{rss_ratio:.6f}",
                "status": status,
                "source": RESOURCE_RAW.relative_to(ROOT).as_posix()
                if RESOURCE_RAW.exists()
                else "MISSING",
            }
        )
    return out


def row(
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
    full_rows: List[Dict[str, str]],
    noise_rows: List[Dict[str, str]],
    resource_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    full = {r["r"]: r for r in full_rows}
    noise = {r["r"]: r for r in noise_rows}
    resource = {r["r"]: r for r in resource_rows}
    r6_full = full.get("6", {})
    r8_full = full.get("8", {})
    r6_noise = noise.get("6", {})
    r8_noise = noise.get("8", {})
    r6_resource = resource.get("6", {})
    r8_resource = resource.get("8", {})

    r6_full_status = r6_full.get("status", "MISSING")
    r8_full_status = r8_full.get("status", "MISSING")
    r6_noise_status = r6_noise.get("status", "MISSING")
    r8_noise_status = r8_noise.get("status", "MISSING")
    r6_resource_status = r6_resource.get("status", "MISSING")
    r8_resource_status = r8_resource.get("status", "MISSING")
    r6_speed = fnum(r6_full, "mean_speedup")
    r4_mean = fnum(r6_full, "r4_mean_reference")
    r4_ci_low = fnum(r6_full, "r4_ci95_low_reference")

    rows = [
        row(
            "stage78_stage77_precondition",
            "PASS"
            if any(
                r.get("gate") == "stage77_decision"
                and r.get("status")
                == "PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED"
                for r in read_csv(STAGE77_SUMMARY)
            )
            else "FAIL",
            "stage77_decision",
            "PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED",
            STAGE77_SUMMARY.relative_to(ROOT).as_posix(),
            "Stage77 recorded H11 as positive smoke and explicitly requires Stage78 repeated gates.",
        ),
        row(
            "stage78_r6_repeated_full_sab",
            r6_full_status,
            "samples;mean_speedup;min_speedup;r4_mean;r4_ci95_low",
            (
                f"{r6_full.get('samples', '0')};{r6_full.get('mean_speedup', '0')};"
                f"{r6_full.get('min_speedup', '0')};{r4_mean:.3f};{r4_ci_low:.6f}"
            ),
            r6_full.get("source", "MISSING"),
            "r=6 fused full-SAB repeated gate is the main Stage78 promotion screen.",
        ),
        row(
            "stage78_r8_stress_full_sab",
            r8_full_status,
            "samples;mean_speedup;min_speedup",
            (
                f"{r8_full.get('samples', '0')};{r8_full.get('mean_speedup', '0')};"
                f"{r8_full.get('min_speedup', '0')}"
            ),
            r8_full.get("source", "MISSING"),
            "r=8 fused full-SAB is kept as a stress case, not the primary promotion target.",
        ),
        row(
            "stage78_r6_noise",
            r6_noise_status,
            "seeds;failures;avg_gap_log2",
            (
                f"{r6_noise.get('seeds', '0')};"
                f"{int(float(r6_noise.get('pvw_failures', '0') or 0)) + int(float(r6_noise.get('scalar_failures', '0') or 0)) + int(float(r6_noise.get('pair_failures', '0') or 0))};"
                f"{r6_noise.get('avg_pvw_minus_scalar_log2', '0')}"
            ),
            r6_noise.get("source", "MISSING"),
            "r=6 final-output noise/correctness gate must have zero PVW/scalar/pair failures.",
        ),
        row(
            "stage78_r8_noise",
            r8_noise_status,
            "seeds;failures;avg_gap_log2",
            (
                f"{r8_noise.get('seeds', '0')};"
                f"{int(float(r8_noise.get('pvw_failures', '0') or 0)) + int(float(r8_noise.get('scalar_failures', '0') or 0)) + int(float(r8_noise.get('pair_failures', '0') or 0))};"
                f"{r8_noise.get('avg_pvw_minus_scalar_log2', '0')}"
            ),
            r8_noise.get("source", "MISSING"),
            "r=8 final-output noise/correctness gate is diagnostic for large-r stress.",
        ),
        row(
            "stage78_resource",
            "PASS"
            if r6_resource_status == "PASS" and r8_resource_status in {"PASS", "REVIEW_RESOURCE_OVERHEAD"}
            else "FAIL",
            "r6_key_ratio;r6_rss_ratio;r8_key_ratio;r8_rss_ratio",
            (
                f"{r6_resource.get('key_ratio_vs_scalar_repeated', '0')};"
                f"{r6_resource.get('rss_ratio_vs_scalar_repeated', '0')};"
                f"{r8_resource.get('key_ratio_vs_scalar_repeated', '0')};"
                f"{r8_resource.get('rss_ratio_vs_scalar_repeated', '0')}"
            ),
            RESOURCE_SUMMARY_CSV.relative_to(ROOT).as_posix(),
            "Resource rows exist for PVW and repeated scalar; ratios are recorded with the speedup evidence.",
        ),
    ]

    r6_ok = r6_full_status in {"PASS", "PASS_R4_REGION_HIGH_STAT_REQUIRED"} and r6_noise_status == "PASS" and r6_resource_status == "PASS"
    if r6_ok and r6_speed >= r4_mean:
        decision = "PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE"
        detail = "r=6 fused repeated full-SAB/noise/resource gates pass and mean speedup reaches or exceeds the r=4 reference mean; run a high-stat confirmation before changing defaults."
    elif r6_ok and r6_speed >= r4_ci_low:
        decision = "PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_HIGH_STAT_REQUIRED"
        detail = "r=6 fused gates pass and land in the r=4 reference region, but the mean does not exceed the r=4 reference mean; keep as a candidate pending higher-stat evidence."
    elif r6_full_status.startswith("PASS") or r6_full_status == "PASS_BELOW_R4_CI_LOW":
        decision = "PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_NOT_PROMOTED"
        detail = "Stage78 records repeated evidence, but the r=6 fused candidate does not clear the r=4 promotion boundary under this gate."
    else:
        decision = "FAIL_RGT4_FUSED_REPEATED_GATES"
        detail = "Stage78 repeated/full-SAB/noise/resource evidence is incomplete or failed; do not promote H11."
    rows.append(
        row(
            "stage78_decision",
            decision,
            "promotion_policy",
            "",
            SUMMARY_CSV.relative_to(ROOT).as_posix(),
            detail,
        )
    )
    return rows


def write_md(
    summary_rows: List[Dict[str, str]],
    full_rows: List[Dict[str, str]],
    noise_rows: List[Dict[str, str]],
    resource_rows: List[Dict[str, str]],
) -> None:
    decision = summary_rows[-1]
    lines = [
        "# Stage78 R>4 Fused Repeated Gates Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage78 is the repeated-gate follow-up to the Stage77 H11 fused",
        "`MAT_TRGSW_AVX512_RGT4_FUSED` smoke. It keeps the scalar SAB path and",
        "the default r=2/r=4 PVW path unchanged. The main candidate is r=6;",
        "r=8 is retained as a diagnostic stress case.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail |",
        "|---|---|---|---|---|---|",
    ]
    for row_data in summary_rows:
        lines.append(
            f"| {row_data['gate']} | {row_data['status']} | {row_data['metric']} | {row_data['value']} | {row_data['evidence']} | {row_data['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Full-SAB Repeated",
            "",
            "| r | samples | status | PVW mean us | scalar repeated mean us | mean speedup | min | max | stddev | Stage77 one-run | r4 mean | r4 CI95 low | source |",
            "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row_data in full_rows:
        lines.append(
            f"| {row_data['r']} | {row_data['samples']} | {row_data['status']} | {row_data['pvw_mean_us']} | {row_data['scalar_repeated_mean_us']} | {row_data['mean_speedup']} | {row_data['min_speedup']} | {row_data['max_speedup']} | {row_data['stddev_speedup']} | {row_data['stage77_one_run_speedup']} | {row_data['r4_mean_reference']} | {row_data['r4_ci95_low_reference']} | {row_data['source']} |"
        )
    lines.extend(
        [
            "",
            "## Noise",
            "",
            "| r | seeds | points | failures | avg PVW-minus-scalar log2 | status | source |",
            "|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row_data in noise_rows:
        failures = (
            int(float(row_data["pvw_failures"] or 0))
            + int(float(row_data["scalar_failures"] or 0))
            + int(float(row_data["pair_failures"] or 0))
        )
        lines.append(
            f"| {row_data['r']} | {row_data['seeds']} | {row_data['points']} | {failures} | {row_data['avg_pvw_minus_scalar_log2']} | {row_data['status']} | {row_data['source']} |"
        )
    lines.extend(
        [
            "",
            "## Resource",
            "",
            "| r | key ratio | keygen ratio | PVW RSS KB | scalar RSS KB | RSS ratio | status | source |",
            "|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row_data in resource_rows:
        lines.append(
            f"| {row_data['r']} | {row_data['key_ratio_vs_scalar_repeated']} | {row_data['keygen_ratio_vs_scalar_repeated']} | {row_data['pvw_time_max_rss_kb']} | {row_data['scalar_time_max_rss_kb']} | {row_data['rss_ratio_vs_scalar_repeated']} | {row_data['status']} | {row_data['source']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{decision['status']}`",
            "",
            decision["detail"],
            "",
            "This stage does not change defaults. Any promotion requires the",
            "decision row to identify a promotion candidate and a follow-up",
            "high-stat confirmation before the claim package or default path is",
            "changed.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    full_rows = summarize_full_sab()
    noise_rows = summarize_noise()
    resource_rows = summarize_resource()
    summary_rows = build_summary(full_rows, noise_rows, resource_rows)
    write_csv(
        FULL_SAB_CSV,
        full_rows,
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
            "stage77_one_run_speedup",
            "r4_mean_reference",
            "r4_ci95_low_reference",
            "status",
            "source",
        ],
    )
    write_csv(
        NOISE_SUMMARY_CSV,
        noise_rows,
        [
            "r",
            "seeds",
            "points",
            "pvw_failures",
            "scalar_failures",
            "pair_failures",
            "avg_pvw_minus_scalar_log2",
            "status",
            "source",
        ],
    )
    write_csv(
        RESOURCE_SUMMARY_CSV,
        resource_rows,
        [
            "r",
            "key_ratio_vs_scalar_repeated",
            "keygen_ratio_vs_scalar_repeated",
            "pvw_time_max_rss_kb",
            "scalar_time_max_rss_kb",
            "rss_ratio_vs_scalar_repeated",
            "status",
            "source",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail"],
    )
    write_md(summary_rows, full_rows, noise_rows, resource_rows)
    decision = summary_rows[-1]["status"]
    print(f"Wrote {FULL_SAB_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {NOISE_SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {RESOURCE_SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage78 r>4 fused repeated gates: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
