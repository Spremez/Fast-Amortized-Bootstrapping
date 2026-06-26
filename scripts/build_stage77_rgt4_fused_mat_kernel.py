#!/usr/bin/env python3
"""Build the Stage77 r>4 fused-MAT kernel smoke report."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage77_rgt4_fused_mat_kernel"
GENERIC_LOG = OUT_DIR / "generic.log"
FUSED_LOG = OUT_DIR / "fused.log"
FULL_GENERIC_R6 = OUT_DIR / "full_sab_generic_r6" / "summary.csv"
FULL_GENERIC_R8 = OUT_DIR / "full_sab_generic_r8" / "summary.csv"
FULL_FUSED_R6 = OUT_DIR / "full_sab_fused_r6" / "summary.csv"
FULL_FUSED_R8 = OUT_DIR / "full_sab_fused_r8" / "summary.csv"
STAGE36_TARGET = ROOT / "repro" / "stage36_target_perf_summary.csv"
KERNEL_CSV = OUT_DIR / "kernel_comparison.csv"
FULL_SAB_CSV = OUT_DIR / "full_sab_smoke.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage77_rgt4_fused_mat_kernel_log.md"


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


def token_values(line: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for token in line.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        out[key] = value.rstrip("x")
    return out


def parse_kernel_log(path: Path, variant: str) -> Tuple[bool, List[Dict[str, str]]]:
    if not path.exists():
        return False, []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    correctness = any("MAT_TRGSW/PVW r>4 kernel test: Pass" in line for line in lines)
    rows: List[Dict[str, str]] = []
    for line in lines:
        values = token_values(line)
        if line.startswith("MAT_TRGSW vs scalar"):
            rows.append(
                {
                    "variant": variant,
                    "bench": "dft_output",
                    "r": values.get("r", ""),
                    "scalar_repeated_avg_us": values.get("scalar_repeated_avg_us", ""),
                    "mat_avg_us": values.get("mat_avg_us", ""),
                    "speedup_vs_scalar_repeated": values.get("speedup_vs_scalar_repeated", ""),
                    "source_log": path.relative_to(ROOT).as_posix(),
                }
            )
        elif line.startswith("MAT_TRGSW_FULL vs scalar_full"):
            rows.append(
                {
                    "variant": variant,
                    "bench": "full_output",
                    "r": values.get("r", ""),
                    "scalar_repeated_avg_us": values.get("scalar_repeated_avg_us", ""),
                    "mat_avg_us": values.get("mat_avg_us", ""),
                    "speedup_vs_scalar_repeated": values.get("speedup_vs_scalar_repeated", ""),
                    "source_log": path.relative_to(ROOT).as_posix(),
                }
            )
    return correctness, rows


def by_key(rows: List[Dict[str, str]], variant: str, bench: str, r: str) -> Dict[str, str]:
    for row in rows:
        if row.get("variant") == variant and row.get("bench") == bench and row.get("r") == r:
            return row
    return {}


def build_kernel_rows(kernel_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for bench in ["dft_output", "full_output"]:
        for r in ["6", "8"]:
            generic = by_key(kernel_rows, "generic", bench, r)
            fused = by_key(kernel_rows, "fused", bench, r)
            generic_mat = fnum(generic, "mat_avg_us")
            fused_mat = fnum(fused, "mat_avg_us")
            fused_vs_generic = generic_mat / fused_mat if fused_mat else 0.0
            out.append(
                {
                    "bench": bench,
                    "r": r,
                    "generic_mat_avg_us": f"{generic_mat:.3f}",
                    "fused_mat_avg_us": f"{fused_mat:.3f}",
                    "fused_vs_generic": f"{fused_vs_generic:.3f}",
                    "generic_speedup_vs_scalar": generic.get("speedup_vs_scalar_repeated", ""),
                    "fused_speedup_vs_scalar": fused.get("speedup_vs_scalar_repeated", ""),
                    "generic_log": generic.get("source_log", ""),
                    "fused_log": fused.get("source_log", ""),
                }
            )
    return out


def single(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def full_sab_row(r: str, generic_path: Path, fused_path: Path) -> Dict[str, str]:
    generic = single(generic_path)
    fused = single(fused_path)
    generic_pvw = fnum(generic, "pvw_avg_us")
    fused_pvw = fnum(fused, "pvw_avg_us")
    fused_vs_generic = generic_pvw / fused_pvw if fused_pvw else 0.0
    return {
        "r": r,
        "generic_status": generic.get("status", "MISSING"),
        "fused_status": fused.get("status", "MISSING"),
        "generic_pvw_avg_us": f"{generic_pvw:.3f}",
        "fused_pvw_avg_us": f"{fused_pvw:.3f}",
        "fused_vs_generic": f"{fused_vs_generic:.3f}",
        "generic_speedup_vs_scalar": generic.get("speedup_vs_scalar_repeated", ""),
        "fused_speedup_vs_scalar": fused.get("speedup_vs_scalar_repeated", ""),
        "generic_evidence": generic_path.relative_to(ROOT).as_posix(),
        "fused_evidence": fused_path.relative_to(ROOT).as_posix(),
    }


def stage36_r4_reference() -> Dict[str, str]:
    for row in read_csv(STAGE36_TARGET):
        if row.get("r") == "4":
            return row
    return {}


def build_summary_rows(
    generic_correct: bool,
    fused_correct: bool,
    kernel_rows: List[Dict[str, str]],
    full_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = [
        {
            "gate": "stage77_generic_kernel_correctness",
            "status": "PASS" if generic_correct else "FAIL",
            "metric": "identity_lane_r6_r8",
            "value": "Pass" if generic_correct else "Fail",
            "evidence": GENERIC_LOG.relative_to(ROOT).as_posix(),
            "detail": "generic r=6/r=8 kernel smoke passes"
            if generic_correct
            else "generic r>4 kernel smoke failed or log missing",
        },
        {
            "gate": "stage77_fused_kernel_correctness",
            "status": "PASS" if fused_correct else "FAIL",
            "metric": "identity_lane_r6_r8",
            "value": "Pass" if fused_correct else "Fail",
            "evidence": FUSED_LOG.relative_to(ROOT).as_posix(),
            "detail": "fused r=6/r=8 kernel smoke passes"
            if fused_correct
            else "fused r>4 kernel smoke failed or log missing",
        },
    ]
    dft_ratios = [
        fnum(row, "fused_vs_generic")
        for row in kernel_rows
        if row.get("bench") == "dft_output"
    ]
    full_ratios = [
        fnum(row, "fused_vs_generic")
        for row in kernel_rows
        if row.get("bench") == "full_output"
    ]
    dft_ok = all(value > 1.0 for value in dft_ratios)
    full_ok = all(value > 1.0 for value in full_ratios)
    rows.append(
        {
            "gate": "stage77_kernel_fused_vs_generic",
            "status": "PASS" if dft_ok and full_ok else "FAIL",
            "metric": "dft_ratios;full_ratios",
            "value": ";".join(f"{v:.3f}" for v in dft_ratios)
            + "|"
            + ";".join(f"{v:.3f}" for v in full_ratios),
            "evidence": KERNEL_CSV.relative_to(ROOT).as_posix(),
            "detail": "fused tiled kernel beats current generic r>4 kernel in DFT-output and full-output microbench"
            if dft_ok and full_ok
            else "fused tiled kernel does not consistently beat generic r>4 kernel",
        }
    )
    fused_dft = {
        row.get("r"): fnum(row, "fused_speedup_vs_scalar")
        for row in kernel_rows
        if row.get("bench") == "dft_output"
    }
    dft_scalar_status = (
        "PARTIAL_R6_ONLY"
        if fused_dft.get("6", 0.0) > 1.0 and fused_dft.get("8", 0.0) < 1.0
        else "PASS"
        if all(v > 1.0 for v in fused_dft.values())
        else "FAIL"
    )
    rows.append(
        {
            "gate": "stage77_fused_dft_vs_scalar",
            "status": dft_scalar_status,
            "metric": "r6;r8",
            "value": f"{fused_dft.get('6', 0.0):.3f};{fused_dft.get('8', 0.0):.3f}",
            "evidence": KERNEL_CSV.relative_to(ROOT).as_posix(),
            "detail": "r=6 DFT-output beats repeated scalar, but r=8 remains below repeated scalar"
            if dft_scalar_status == "PARTIAL_R6_ONLY"
            else "fused DFT-output scalar comparison needs review",
        }
    )
    full_ok = all(
        row.get("generic_status") == "Pass"
        and row.get("fused_status") == "Pass"
        and fnum(row, "fused_vs_generic") > 1.0
        for row in full_rows
    )
    rows.append(
        {
            "gate": "stage77_full_sab_smoke",
            "status": "PASS" if full_ok else "FAIL",
            "metric": "fused_vs_generic_r6_r8",
            "value": ";".join(f"{fnum(row, 'fused_vs_generic'):.3f}" for row in full_rows),
            "evidence": FULL_SAB_CSV.relative_to(ROOT).as_posix(),
            "detail": "fused r=6/r=8 full-SAB one-run smokes pass and beat same-stage generic r>4"
            if full_ok
            else "fused full-SAB smoke does not consistently beat generic or correctness failed",
        }
    )
    r4 = stage36_r4_reference()
    r4_mean = fnum(r4, "mean_speedup")
    r4_ci_low = fnum(r4, "ci95_low")
    fused_full = {row.get("r"): fnum(row, "fused_speedup_vs_scalar") for row in full_rows}
    boundary_status = "REPEATED_GATES_REQUIRED"
    if fused_full.get("6", 0.0) <= r4_ci_low and fused_full.get("8", 0.0) <= r4_ci_low:
        boundary_status = "BELOW_R4_REFERENCE"
    rows.append(
        {
            "gate": "stage77_r4_boundary",
            "status": boundary_status,
            "metric": "fused_r6;fused_r8;r4_mean;r4_ci95_low",
            "value": (
                f"{fused_full.get('6', 0.0):.3f};{fused_full.get('8', 0.0):.3f};"
                f"{r4_mean:.3f};{r4_ci_low:.6f}"
            ),
            "evidence": f"{FULL_SAB_CSV.relative_to(ROOT).as_posix()}; {STAGE36_TARGET.relative_to(ROOT).as_posix()}",
            "detail": "r=6 one-run fused smoke reaches the r=4 reference region, but promotion requires repeated full-SAB/noise/resource gates; r=8 remains below the r=4 reference"
            if boundary_status == "REPEATED_GATES_REQUIRED"
            else "fused r>4 one-run smokes remain below the r=4 reference",
        }
    )
    decision_ok = generic_correct and fused_correct and dft_ok and full_ok
    rows.append(
        {
            "gate": "stage77_decision",
            "status": "PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED"
            if decision_ok
            else "FAIL_RGT4_FUSED_SMOKE",
            "metric": "promotion_policy",
            "value": "",
            "evidence": SUMMARY_CSV.relative_to(ROOT).as_posix(),
            "detail": "Stage77 promotes H11 from theory to a positive smoke candidate only; no default/full promotion until repeated full-SAB, noise, and resource gates pass"
            if decision_ok
            else "Stage77 fused kernel smoke failed; do not continue promotion gates",
        }
    )
    return rows


def write_md(
    summary_rows: List[Dict[str, str]],
    kernel_rows: List[Dict[str, str]],
    full_rows: List[Dict[str, str]],
) -> None:
    lines = [
        "# Stage77 R>4 Fused MAT Kernel Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage77 implements the H11 r>4 fused MAT external-product hypothesis",
        "behind `MAT_TRGSW_AVX512_RGT4_FUSED`. It keeps scalar SAB and the",
        "default promoted r=2/r=4 path unchanged. The stage is a smoke gate:",
        "positive results can only justify repeated Stage78 gates, not immediate",
        "promotion.",
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
            "## Kernel Comparison",
            "",
            "| bench | r | generic us | fused us | fused/generic | generic scalar speedup | fused scalar speedup |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in kernel_rows:
        lines.append(
            f"| {row['bench']} | {row['r']} | {row['generic_mat_avg_us']} | {row['fused_mat_avg_us']} | {row['fused_vs_generic']} | {row['generic_speedup_vs_scalar']} | {row['fused_speedup_vs_scalar']} |"
        )
    lines.extend(
        [
            "",
            "## Full-SAB Smoke",
            "",
            "| r | generic PVW us | fused PVW us | fused/generic | generic scalar speedup | fused scalar speedup |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in full_rows:
        lines.append(
            f"| {row['r']} | {row['generic_pvw_avg_us']} | {row['fused_pvw_avg_us']} | {row['fused_vs_generic']} | {row['generic_speedup_vs_scalar']} | {row['fused_speedup_vs_scalar']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The tiled fused r>4 kernel improves the current generic r>4 MAT kernel",
            "in this smoke run: DFT-output fused/generic is `1.582x` for r=6 and",
            "`1.431x` for r=8; full-output fused/generic is `1.510x` and",
            "`1.370x`. Complete SAB one-run smokes also improve over same-stage",
            "generic: r=6 `1.120x` and r=8 `1.102x` fused/generic.",
            "",
            "This is not a final promotion. r=8 DFT-output remains below repeated",
            "scalar (`0.951x`), r=8 full-SAB speedup remains below the current r=4",
            "reference, and all full-SAB evidence is one-run smoke. The next stage",
            "must repeat the full-SAB/noise/resource gates, with r=6 as the main",
            "candidate and r=8 as a diagnostic stress case.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    generic_correct, generic_rows = parse_kernel_log(GENERIC_LOG, "generic")
    fused_correct, fused_rows = parse_kernel_log(FUSED_LOG, "fused")
    kernel_rows = build_kernel_rows(generic_rows + fused_rows)
    full_rows = [
        full_sab_row("6", FULL_GENERIC_R6, FULL_FUSED_R6),
        full_sab_row("8", FULL_GENERIC_R8, FULL_FUSED_R8),
    ]
    summary_rows = build_summary_rows(generic_correct, fused_correct, kernel_rows, full_rows)
    write_csv(
        KERNEL_CSV,
        kernel_rows,
        [
            "bench",
            "r",
            "generic_mat_avg_us",
            "fused_mat_avg_us",
            "fused_vs_generic",
            "generic_speedup_vs_scalar",
            "fused_speedup_vs_scalar",
            "generic_log",
            "fused_log",
        ],
    )
    write_csv(
        FULL_SAB_CSV,
        full_rows,
        [
            "r",
            "generic_status",
            "fused_status",
            "generic_pvw_avg_us",
            "fused_pvw_avg_us",
            "fused_vs_generic",
            "generic_speedup_vs_scalar",
            "fused_speedup_vs_scalar",
            "generic_evidence",
            "fused_evidence",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail"],
    )
    write_md(summary_rows, kernel_rows, full_rows)
    decision = summary_rows[-1]["status"]
    print(f"Wrote {KERNEL_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {FULL_SAB_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage77 r>4 fused MAT kernel: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
