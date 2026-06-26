#!/usr/bin/env python3
"""Build the Stage84 H13 r=6 tile-sweep preflight report."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage84_h13_r6_tile_sweep_preflight"
TILE4_LOG = OUT_DIR / "tile4.log"
FULLTILE_LOG = OUT_DIR / "fulltile.log"
FULL_TILE4_R6 = OUT_DIR / "full_sab_tile4_r6" / "summary.csv"
FULL_FULLTILE_R6 = OUT_DIR / "full_sab_fulltile_r6" / "summary.csv"
STAGE83 = ROOT / "repro" / "stage83_mat_body_design_check" / "decision.csv"
KERNEL_CSV = OUT_DIR / "kernel_comparison.csv"
FULL_SAB_CSV = OUT_DIR / "full_sab_smoke.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage84_h13_r6_tile_sweep_preflight_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fnum(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0.0)
    except ValueError:
        return 0.0


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


def build_kernel_rows(raw_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for bench in ["dft_output", "full_output"]:
        for r in ["6", "8"]:
            tile4 = by_key(raw_rows, "tile4", bench, r)
            fulltile = by_key(raw_rows, "fulltile", bench, r)
            tile4_us = fnum(tile4, "mat_avg_us")
            fulltile_us = fnum(fulltile, "mat_avg_us")
            ratio = tile4_us / fulltile_us if fulltile_us else 0.0
            out.append(
                {
                    "bench": bench,
                    "r": r,
                    "tile4_mat_avg_us": f"{tile4_us:.3f}",
                    "fulltile_mat_avg_us": f"{fulltile_us:.3f}",
                    "fulltile_vs_tile4": f"{ratio:.3f}",
                    "tile4_speedup_vs_scalar": tile4.get("speedup_vs_scalar_repeated", ""),
                    "fulltile_speedup_vs_scalar": fulltile.get("speedup_vs_scalar_repeated", ""),
                    "tile4_log": tile4.get("source_log", ""),
                    "fulltile_log": fulltile.get("source_log", ""),
                }
            )
    return out


def single(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def full_sab_row() -> Dict[str, str]:
    tile4 = single(FULL_TILE4_R6)
    fulltile = single(FULL_FULLTILE_R6)
    tile4_pvw = fnum(tile4, "pvw_avg_us")
    fulltile_pvw = fnum(fulltile, "pvw_avg_us")
    ratio = tile4_pvw / fulltile_pvw if fulltile_pvw else 0.0
    return {
        "r": "6",
        "tile4_status": tile4.get("status", "MISSING"),
        "fulltile_status": fulltile.get("status", "MISSING"),
        "tile4_pvw_avg_us": f"{tile4_pvw:.3f}",
        "fulltile_pvw_avg_us": f"{fulltile_pvw:.3f}",
        "fulltile_vs_tile4": f"{ratio:.3f}",
        "tile4_speedup_vs_scalar": tile4.get("speedup_vs_scalar_repeated", ""),
        "fulltile_speedup_vs_scalar": fulltile.get("speedup_vs_scalar_repeated", ""),
        "tile4_evidence": FULL_TILE4_R6.relative_to(ROOT).as_posix(),
        "fulltile_evidence": FULL_FULLTILE_R6.relative_to(ROOT).as_posix(),
    }


def stage83_status() -> str:
    rows = {row.get("gate"): row for row in read_csv(STAGE83)}
    return rows.get("stage83_decision", {}).get("status", "MISSING")


def row(
    gate: str,
    status: str,
    metric: str,
    value: str,
    evidence: str,
    detail: str,
    next_action: str,
) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "metric": metric,
        "value": value,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def ratio_for(kernel_rows: List[Dict[str, str]], bench: str, r: str) -> float:
    for item in kernel_rows:
        if item.get("bench") == bench and item.get("r") == r:
            return fnum(item, "fulltile_vs_tile4")
    return 0.0


def build_summary(
    tile4_correct: bool,
    fulltile_correct: bool,
    kernel_rows: List[Dict[str, str]],
    full_row: Dict[str, str],
) -> List[Dict[str, str]]:
    stage83_ok = stage83_status() == "PASS_STAGE83_MAT_BODY_DESIGN_CHECK_SELECT_R6_TILE_SWEEP_PREFLIGHT"
    dft_r6 = ratio_for(kernel_rows, "dft_output", "6")
    full_r6 = ratio_for(kernel_rows, "full_output", "6")
    dft_r8 = ratio_for(kernel_rows, "dft_output", "8")
    full_r8 = ratio_for(kernel_rows, "full_output", "8")
    kernel_positive = dft_r6 > 1.0 and full_r6 > 1.0
    full_sab_available = FULL_TILE4_R6.exists() and FULL_FULLTILE_R6.exists()
    full_sab_ratio = fnum(full_row, "fulltile_vs_tile4")
    full_sab_pass = (
        full_row.get("tile4_status") == "Pass"
        and full_row.get("fulltile_status") == "Pass"
    )

    rows = [
        row(
            "stage84_inputs_available",
            "PASS" if stage83_ok and TILE4_LOG.exists() and FULLTILE_LOG.exists() else "FAIL",
            "stage83;tile4_log;fulltile_log",
            f"stage83={stage83_status()}; tile4={TILE4_LOG.exists()}; fulltile={FULLTILE_LOG.exists()}",
            f"{STAGE83.relative_to(ROOT).as_posix()}; {TILE4_LOG.relative_to(ROOT).as_posix()}; {FULLTILE_LOG.relative_to(ROOT).as_posix()}",
            "Stage84 has Stage83 preflight authorization and both kernel logs."
            if stage83_ok and TILE4_LOG.exists() and FULLTILE_LOG.exists()
            else "Stage84 inputs are incomplete.",
            "Restore missing inputs before interpreting Stage84.",
        ),
        row(
            "stage84_kernel_correctness",
            "PASS" if tile4_correct and fulltile_correct else "FAIL",
            "tile4_correct;fulltile_correct",
            f"{tile4_correct};{fulltile_correct}",
            f"{TILE4_LOG.relative_to(ROOT).as_posix()}; {FULLTILE_LOG.relative_to(ROOT).as_posix()}",
            "Both tile4 and fulltile r>4 kernel identity-lane gates pass."
            if tile4_correct and fulltile_correct
            else "A kernel correctness gate failed.",
            "Do not use performance rows if correctness fails.",
        ),
        row(
            "stage84_r6_kernel_comparison",
            "PASS_KERNEL_POSITIVE" if kernel_positive else "NEGATIVE_KERNEL_NOT_PROMOTED",
            "dft_output_ratio;full_output_ratio",
            f"{dft_r6:.3f};{full_r6:.3f}",
            KERNEL_CSV.relative_to(ROOT).as_posix(),
            "r=6 full-output tile beats tile4 in both DFT-output and full-output MAT microbench."
            if kernel_positive
            else "r=6 full-output tile does not beat tile4 in both MAT microbench boundaries.",
            "Run or interpret full-SAB smoke only as preflight; promotion still requires Stage85."
            if kernel_positive
            else "Record as a negative ablation unless a follow-up explains the regression.",
        ),
        row(
            "stage84_r8_guard",
            "RECORDED_DIAGNOSTIC",
            "dft_output_ratio;full_output_ratio",
            f"{dft_r8:.3f};{full_r8:.3f}",
            KERNEL_CSV.relative_to(ROOT).as_posix(),
            "r=8 remains on the existing tile4 dispatch under the fulltile flag; this is a diagnostic guard only.",
            "Do not claim r=8 improvement from the r=6-only flag.",
        ),
        row(
            "stage84_full_sab_smoke",
            "PASS_FULL_SAB_POSITIVE"
            if full_sab_available and full_sab_pass and full_sab_ratio > 1.0
            else "NEUTRAL_OR_NEGATIVE_FULL_SAB"
            if full_sab_available and full_sab_pass
            else "SKIPPED_OR_MISSING_FULL_SAB",
            "fulltile_vs_tile4",
            f"{full_sab_ratio:.3f}",
            FULL_SAB_CSV.relative_to(ROOT).as_posix(),
            "r=6 fulltile complete-SAB smoke passes and beats tile4."
            if full_sab_available and full_sab_pass and full_sab_ratio > 1.0
            else "r=6 complete-SAB smoke is not positive or was not run.",
            "Proceed to Stage85 only if this gate is positive.",
        ),
    ]

    hard_fail = any(item["status"] == "FAIL" for item in rows)
    if hard_fail:
        decision = "FAIL_STAGE84_H13_R6_TILE_SWEEP_PREFLIGHT"
        detail = "Stage84 has missing inputs or correctness failure."
        next_action = "Fix inputs/correctness before continuing."
    elif kernel_positive and full_sab_available and full_sab_pass and full_sab_ratio > 1.0:
        decision = "PASS_STAGE84_H13_R6_TILE_SWEEP_POSITIVE_PREFLIGHT_STAGE85_REQUIRED"
        detail = "Stage84 preflight is positive; Stage85 repeated/noise/resource gates are required before promotion."
        next_action = "Run Stage85 with repeated complete-SAB, final-output noise, and resource gates."
    elif kernel_positive:
        decision = "PASS_STAGE84_H13_R6_TILE_SWEEP_KERNEL_ONLY_NOT_PROMOTED"
        detail = "Stage84 kernel signal is positive but complete-SAB propagation is missing or neutral."
        next_action = "Do not promote; use Stage86 routing unless a stronger full-SAB gate is run."
    else:
        decision = "PASS_STAGE84_H13_R6_TILE_SWEEP_NEGATIVE_NOT_PROMOTED"
        detail = "Stage84 records a correct but non-positive tile-sweep preflight."
        next_action = "Keep the flag experimental and move to Stage86 candidate routing."
    rows.append(
        row(
            "stage84_decision",
            decision,
            "promotion_policy",
            "",
            SUMMARY_CSV.relative_to(ROOT).as_posix(),
            detail,
            next_action,
        )
    )
    return rows


def write_md(
    summary_rows: List[Dict[str, str]],
    kernel_rows: List[Dict[str, str]],
    full_rows: List[Dict[str, str]],
) -> None:
    lines = [
        "# Stage84 H13 R6 Tile-Sweep Preflight Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage84 implements the Stage83-selected H13-C1 r=6 full-output tile",
        "preflight behind `MAT_TRGSW_AVX512_R6_FULLTILE`. It does not change",
        "scalar SAB, default `sab_pvw_*`, key format, or promoted r=2/r=4",
        "behavior.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail | next_action |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in summary_rows:
        lines.append(
            "| {gate} | {status} | {metric} | {value} | {evidence} | {detail} | {next_action} |".format(
                **{k: item[k].replace("|", "\\|") for k in item}
            )
        )
    lines.extend(
        [
            "",
            "## Kernel Comparison",
            "",
            "| bench | r | tile4 us | fulltile us | fulltile/tile4 | tile4 scalar speedup | fulltile scalar speedup |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in kernel_rows:
        lines.append(
            f"| {item['bench']} | {item['r']} | {item['tile4_mat_avg_us']} | {item['fulltile_mat_avg_us']} | {item['fulltile_vs_tile4']} | {item['tile4_speedup_vs_scalar']} | {item['fulltile_speedup_vs_scalar']} |"
        )
    lines.extend(
        [
            "",
            "## Full-SAB Smoke",
            "",
            "| r | tile4 PVW us | fulltile PVW us | fulltile/tile4 | tile4 scalar speedup | fulltile scalar speedup |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in full_rows:
        lines.append(
            f"| {item['r']} | {item['tile4_pvw_avg_us']} | {item['fulltile_pvw_avg_us']} | {item['fulltile_vs_tile4']} | {item['tile4_speedup_vs_scalar']} | {item['fulltile_speedup_vs_scalar']} |"
        )
    decision = summary_rows[-1]["status"] if summary_rows else "MISSING"
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{decision}`",
            "",
            "Stage84 is a preflight result only. A positive result must enter",
            "Stage85 repeated complete-SAB, noise, and resource gates before any",
            "promotion or bootstrapping-speedup claim changes.",
            "",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    tile4_correct, tile4_rows = parse_kernel_log(TILE4_LOG, "tile4")
    fulltile_correct, fulltile_rows = parse_kernel_log(FULLTILE_LOG, "fulltile")
    kernel_rows = build_kernel_rows(tile4_rows + fulltile_rows)
    full_rows = [full_sab_row()]
    summary_rows = build_summary(tile4_correct, fulltile_correct, kernel_rows, full_rows[0])
    write_csv(
        KERNEL_CSV,
        kernel_rows,
        [
            "bench",
            "r",
            "tile4_mat_avg_us",
            "fulltile_mat_avg_us",
            "fulltile_vs_tile4",
            "tile4_speedup_vs_scalar",
            "fulltile_speedup_vs_scalar",
            "tile4_log",
            "fulltile_log",
        ],
    )
    write_csv(
        FULL_SAB_CSV,
        full_rows,
        [
            "r",
            "tile4_status",
            "fulltile_status",
            "tile4_pvw_avg_us",
            "fulltile_pvw_avg_us",
            "fulltile_vs_tile4",
            "tile4_speedup_vs_scalar",
            "fulltile_speedup_vs_scalar",
            "tile4_evidence",
            "fulltile_evidence",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summary_rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_md(summary_rows, kernel_rows, full_rows)
    decision = summary_rows[-1]["status"]
    print(f"Wrote {KERNEL_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {FULL_SAB_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage84 H13 r6 tile-sweep preflight: {decision}")
    return 1 if decision.startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
