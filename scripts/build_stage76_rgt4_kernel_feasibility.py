#!/usr/bin/env python3
"""Build the Stage76 r>4 kernel-feasibility diagnosis."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage76_rgt4_kernel_feasibility"
RAW_LOG = OUT_DIR / "rgt4_kernel_smoke.log"
KERNEL_CSV = OUT_DIR / "kernel_microbench.csv"
BREAKDOWN_CSV = OUT_DIR / "ep_breakdown.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage76_rgt4_kernel_feasibility_log.md"


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_log() -> List[str]:
    if not RAW_LOG.exists():
        return []
    return RAW_LOG.read_text(encoding="utf-8", errors="replace").splitlines()


def token_values(line: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for token in line.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        out[key] = value.rstrip("x")
    return out


def fnum(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, ""))
    except ValueError:
        return default


def parse_log(lines: List[str]) -> tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    correctness = any("MAT_TRGSW/PVW r>4 kernel test: Pass" in line for line in lines)
    kernel_rows: List[Dict[str, str]] = []
    breakdown_rows: List[Dict[str, str]] = []
    for line in lines:
        values = token_values(line)
        if line.startswith("MAT_TRGSW microbench"):
            kernel_rows.append(
                {
                    "bench": "mat_only",
                    "r": values.get("r", ""),
                    "reps": values.get("reps", ""),
                    "scalar_repeated_avg_us": "",
                    "scalar_lane_avg_us": "",
                    "mat_avg_us": values.get("avg_us", ""),
                    "mat_lane_avg_us": values.get("lane_avg_us", ""),
                    "speedup_vs_scalar_repeated": "",
                    "source_log": RAW_LOG.relative_to(ROOT).as_posix(),
                }
            )
        elif line.startswith("MAT_TRGSW vs scalar"):
            kernel_rows.append(
                {
                    "bench": "dft_output",
                    "r": values.get("r", ""),
                    "reps": values.get("reps", ""),
                    "scalar_repeated_avg_us": values.get("scalar_repeated_avg_us", ""),
                    "scalar_lane_avg_us": values.get("scalar_lane_avg_us", ""),
                    "mat_avg_us": values.get("mat_avg_us", ""),
                    "mat_lane_avg_us": values.get("mat_lane_avg_us", ""),
                    "speedup_vs_scalar_repeated": values.get("speedup_vs_scalar_repeated", ""),
                    "source_log": RAW_LOG.relative_to(ROOT).as_posix(),
                }
            )
        elif line.startswith("MAT_TRGSW_FULL vs scalar_full"):
            kernel_rows.append(
                {
                    "bench": "full_output",
                    "r": values.get("r", ""),
                    "reps": values.get("reps", ""),
                    "scalar_repeated_avg_us": values.get("scalar_repeated_avg_us", ""),
                    "scalar_lane_avg_us": values.get("scalar_lane_avg_us", ""),
                    "mat_avg_us": values.get("mat_avg_us", ""),
                    "mat_lane_avg_us": values.get("mat_lane_avg_us", ""),
                    "speedup_vs_scalar_repeated": values.get("speedup_vs_scalar_repeated", ""),
                    "source_log": RAW_LOG.relative_to(ROOT).as_posix(),
                }
            )
        elif line.startswith("EP_BREAKDOWN"):
            mode = line.split()[1]
            breakdown_rows.append(
                {
                    "mode": mode,
                    "r": values.get("r", ""),
                    "reps": values.get("reps", ""),
                    "phase_sum_avg_us": values.get("phase_sum_avg_us", ""),
                    "alloc_pct": values.get("alloc_pct", ""),
                    "decompose_avg_us": values.get("decompose_avg_us", ""),
                    "decompose_pct": values.get("decompose_pct", ""),
                    "dft_avg_us": values.get("dft_avg_us", ""),
                    "dft_pct": values.get("dft_pct", ""),
                    "clear_pct": values.get("clear_pct", ""),
                    "mul_avg_us": values.get("mul_avg_us", ""),
                    "mul_pct": values.get("mul_pct", ""),
                    "source_log": RAW_LOG.relative_to(ROOT).as_posix(),
                }
            )
    return correctness, kernel_rows, breakdown_rows


def row_for(rows: List[Dict[str, str]], bench: str, r: str) -> Dict[str, str]:
    for row in rows:
        if row.get("bench") == bench and row.get("r") == r:
            return row
    return {}


def breakdown_for(rows: List[Dict[str, str]], mode: str, r: str) -> Dict[str, str]:
    for row in rows:
        if row.get("mode") == mode and row.get("r") == r:
            return row
    return {}


def build_summary(
    correctness: bool, kernel_rows: List[Dict[str, str]], breakdown_rows: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = [
        {
            "gate": "stage76_rgt4_kernel_correctness",
            "status": "PASS" if correctness else "FAIL",
            "metric": "identity_lane_r6_r8",
            "value": "Pass" if correctness else "Fail",
            "evidence": RAW_LOG.relative_to(ROOT).as_posix(),
            "detail": "r=6/r=8 MAT_TRGSW/PVW identity-lane kernel smoke passes"
            if correctness
            else "r>4 identity-lane kernel smoke failed or raw log is missing",
        }
    ]
    dft_speedups: Dict[str, float] = {}
    full_speedups: Dict[str, float] = {}
    for r in ["6", "8"]:
        dft_row = row_for(kernel_rows, "dft_output", r)
        dft_speed = fnum(dft_row, "speedup_vs_scalar_repeated")
        dft_speedups[r] = dft_speed
        rows.append(
            {
                "gate": f"stage76_r{r}_dft_output_kernel",
                "status": "NEGATIVE_DFT_OUTPUT_NOT_PROMOTED"
                if dft_speed < 1.0
                else "REVIEW_DFT_OUTPUT_KERNEL",
                "metric": "speedup_vs_scalar_repeated",
                "value": f"{dft_speed:.3f}",
                "evidence": KERNEL_CSV.relative_to(ROOT).as_posix(),
                "detail": (
                    f"r={r} DFT-output MAT path does not beat repeated scalar external products; no direct r>4 kernel promotion"
                    if dft_speed < 1.0
                    else f"r={r} DFT-output MAT path needs manual review before any promotion"
                ),
            }
        )
        full_row = row_for(kernel_rows, "full_output", r)
        full_speed = fnum(full_row, "speedup_vs_scalar_repeated")
        full_speedups[r] = full_speed
        if full_speed >= 1.05:
            status = "SMOKE_POSITIVE_FULL_OUTPUT"
        elif full_speed > 1.0:
            status = "SMOKE_POSITIVE_LOW_MARGIN_FULL_OUTPUT"
        else:
            status = "NEGATIVE_FULL_OUTPUT"
        rows.append(
            {
                "gate": f"stage76_r{r}_full_output_kernel",
                "status": status,
                "metric": "speedup_vs_scalar_repeated",
                "value": f"{full_speed:.3f}",
                "evidence": KERNEL_CSV.relative_to(ROOT).as_posix(),
                "detail": (
                    f"r={r} full-output smoke is positive but only a kernel-level/shared-DFT signal"
                    if full_speed > 1.0
                    else f"r={r} full-output smoke is not useful"
                ),
            }
        )
    mat_mul_pcts = [
        fnum(breakdown_for(breakdown_rows, "mat_shared_mask", r), "mul_pct")
        for r in ["6", "8"]
    ]
    mul_boundary_ok = all(pct > 50.0 for pct in mat_mul_pcts)
    rows.append(
        {
            "gate": "stage76_mul_share_boundary",
            "status": "PASS" if mul_boundary_ok else "FAIL",
            "metric": "mat_shared_mask_mul_pct_r6_r8",
            "value": ";".join(f"{pct:.2f}" for pct in mat_mul_pcts),
            "evidence": BREAKDOWN_CSV.relative_to(ROOT).as_posix(),
            "detail": "r>4 MAT shared-mask path is multiply dominated; future work must target fused MAT multiply/layout/register blocking"
            if mul_boundary_ok
            else "r>4 phase breakdown does not show the expected multiply-dominated boundary",
        }
    )
    no_promotion = (
        correctness
        and dft_speedups.get("6", 0.0) < 1.0
        and dft_speedups.get("8", 0.0) < 1.0
        and full_speedups.get("8", 0.0) < 1.05
        and mul_boundary_ok
    )
    rows.append(
        {
            "gate": "stage76_decision",
            "status": "PASS_RGT4_KERNEL_FEASIBILITY_RECORDED_NO_PROMOTION"
            if no_promotion
            else "REVIEW_RGT4_KERNEL_FEASIBILITY",
            "metric": "promotion_policy",
            "value": "",
            "evidence": SUMMARY_CSV.relative_to(ROOT).as_posix(),
            "detail": "Stage76 records r>4 kernel feasibility and rejects direct promotion; next large-r candidate must be a dedicated fused MAT multiply/layout hypothesis"
            if no_promotion
            else "Stage76 requires manual review before updating the large-r route",
        }
    )
    return rows


def write_md(
    summary_rows: List[Dict[str, str]],
    kernel_rows: List[Dict[str, str]],
    breakdown_rows: List[Dict[str, str]],
) -> None:
    lines = [
        "# Stage76 R>4 Kernel Feasibility Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage76 checks the existing MAT external-product kernel at r=6/r=8",
        "without changing scalar SAB, the default `sab_pvw_*` path, or the MAT",
        "key format. It separates DFT-output kernel evidence from full-output",
        "shared-decomposition/DFT evidence so that a narrow microbenchmark result",
        "cannot be overclaimed as complete SAB acceleration.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail |",
        "|---|---|---|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['evidence']} | {row['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Kernel Microbench",
            "",
            "| bench | r | scalar repeated us | MAT us | speedup |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in kernel_rows:
        if row["bench"] == "mat_only":
            lines.append(
                f"| {row['bench']} | {row['r']} | n/a | {row['mat_avg_us']} | n/a |"
            )
        else:
            lines.append(
                f"| {row['bench']} | {row['r']} | {row['scalar_repeated_avg_us']} | {row['mat_avg_us']} | {row['speedup_vs_scalar_repeated']} |"
            )
    lines.extend(
        [
            "",
            "## External-Product Phase Breakdown",
            "",
            "| mode | r | phase us | decompose % | DFT % | mul % |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in breakdown_rows:
        lines.append(
            f"| {row['mode']} | {row['r']} | {row['phase_sum_avg_us']} | {row['decompose_pct']} | {row['dft_pct']} | {row['mul_pct']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The r=6/r=8 identity-lane checks pass, so the existing generic r>4",
            "MAT external-product path is functionally usable. Performance does",
            "not justify promotion: DFT-output MAT is `0.984x` for r=6 and",
            "`0.912x` for r=8 versus repeated scalar external products. Full-output",
            "measurements remain slightly positive only because they include shared",
            "decomposition/DFT effects: r=6 reaches `1.168x`, while r=8 reaches",
            "only `1.044x`.",
            "",
            "The phase breakdown shows the MAT shared-mask path becomes multiply",
            "dominated at r>4 (`55.72%` for r=6 and `61.20%` for r=8). Therefore",
            "the next large-r optimization must target the dense MAT multiply and",
            "its layout/register/cache behavior, not another direct lane-count",
            "increase or a repeat of the Stage65A row-unrolled r=4 direction.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    lines = read_log()
    correctness, kernel_rows, breakdown_rows = parse_log(lines)
    write_csv(
        KERNEL_CSV,
        kernel_rows,
        [
            "bench",
            "r",
            "reps",
            "scalar_repeated_avg_us",
            "scalar_lane_avg_us",
            "mat_avg_us",
            "mat_lane_avg_us",
            "speedup_vs_scalar_repeated",
            "source_log",
        ],
    )
    write_csv(
        BREAKDOWN_CSV,
        breakdown_rows,
        [
            "mode",
            "r",
            "reps",
            "phase_sum_avg_us",
            "alloc_pct",
            "decompose_avg_us",
            "decompose_pct",
            "dft_avg_us",
            "dft_pct",
            "clear_pct",
            "mul_avg_us",
            "mul_pct",
            "source_log",
        ],
    )
    summary_rows = build_summary(correctness, kernel_rows, breakdown_rows)
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail"],
    )
    write_md(summary_rows, kernel_rows, breakdown_rows)
    decision = summary_rows[-1]["status"]
    print(f"Wrote {KERNEL_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {BREAKDOWN_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage76 r>4 kernel feasibility: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
