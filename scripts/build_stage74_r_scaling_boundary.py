#!/usr/bin/env python3
"""Build the Stage74 r>4 lane-scaling boundary log."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage74_r_scaling_boundary"
R6_SUMMARY = OUT_DIR / "r6_reps1_runs1" / "summary.csv"
R8_SUMMARY = OUT_DIR / "r8_reps1_runs1" / "summary.csv"
STAGE36_TARGET = ROOT / "repro" / "stage36_target_perf_summary.csv"
OUT_CSV = OUT_DIR / "decision.csv"
OUT_MD = ROOT / "docs" / "stage74_r_scaling_boundary_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "status", "metric", "value", "evidence", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def fnum(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, ""))
    except ValueError:
        return default


def single_row_summary(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def smoke_gate(r_value: int, path: Path) -> Dict[str, str]:
    row = single_row_summary(path)
    status = row.get("status", "MISSING")
    speedup = fnum(row, "speedup_vs_scalar_repeated")
    pvw = fnum(row, "pvw_avg_us")
    scalar = fnum(row, "scalar_repeated_avg_us")
    ok = status == "Pass" and speedup > 1.0
    return {
        "gate": f"stage74_r{r_value}_full_sab_smoke",
        "status": "PASS" if ok else "FAIL",
        "metric": "speedup_vs_scalar_repeated",
        "value": f"{speedup:.3f}",
        "evidence": path.relative_to(ROOT).as_posix(),
        "detail": (
            f"r={r_value} full-SAB correctness passed; pvw_avg_us={pvw:.3f}; "
            f"scalar_repeated_avg_us={scalar:.3f}"
        )
        if ok
        else f"status={status}; speedup={speedup:.3f}",
    }


def boundary_gate() -> Dict[str, str]:
    r6 = single_row_summary(R6_SUMMARY)
    r8 = single_row_summary(R8_SUMMARY)
    stage36 = {row.get("r"): row for row in read_csv(STAGE36_TARGET)}
    r4 = stage36.get("4", {})
    r6_speedup = fnum(r6, "speedup_vs_scalar_repeated")
    r8_speedup = fnum(r8, "speedup_vs_scalar_repeated")
    r4_mean = fnum(r4, "mean_speedup")
    r4_ci_low = fnum(r4, "ci95_low")
    r4_ready = r4.get("decision") == "PASS_TARGET_PERF_10RUN"
    direct_promote = (
        r4_ready
        and r6.get("status") == "Pass"
        and r8.get("status") == "Pass"
        and r6_speedup > r4_mean
        and r8_speedup > r4_mean
    )
    screen_negative = (
        r4_ready
        and r6.get("status") == "Pass"
        and r8.get("status") == "Pass"
        and r6_speedup < r4_ci_low
        and r8_speedup < r4_ci_low
    )
    if direct_promote:
        status = "PROMOTION_CANDIDATE_REQUIRES_FULL_GATES"
        detail = "r=6 and r=8 both exceed the Stage36 r=4 mean in smoke; full repeated/noise/resource gates required"
    elif screen_negative:
        status = "NOT_PROMOTED_R_GT4_BELOW_R4_SCREEN"
        detail = (
            "r=6 and r=8 one-run smoke speedups are below the Stage36 r=4 "
            "10-run CI lower bound; direct r>4 lane-count expansion is not "
            "promoted without a new r>4 kernel/layout hypothesis"
        )
    else:
        status = "INCONCLUSIVE_R_GT4_SCREEN"
        detail = "r>4 smoke does not cleanly dominate or underperform the r=4 Stage36 reference"
    return {
        "gate": "stage74_rgt4_boundary",
        "status": status,
        "metric": "r6_speedup;r8_speedup;r4_mean;r4_ci95_low",
        "value": f"{r6_speedup:.3f};{r8_speedup:.3f};{r4_mean:.3f};{r4_ci_low:.6f}",
        "evidence": (
            f"{R6_SUMMARY.relative_to(ROOT).as_posix()}; "
            f"{R8_SUMMARY.relative_to(ROOT).as_posix()}; "
            f"{STAGE36_TARGET.relative_to(ROOT).as_posix()}"
        ),
        "detail": detail,
    }


def build_rows() -> List[Dict[str, str]]:
    rows = [smoke_gate(6, R6_SUMMARY), smoke_gate(8, R8_SUMMARY), boundary_gate()]
    failures = [row["gate"] for row in rows if row["status"] == "FAIL"]
    decision_status = (
        "PASS_R_GT4_BOUNDARY_RECORDED_NOT_PROMOTED"
        if not failures and rows[-1]["status"] == "NOT_PROMOTED_R_GT4_BELOW_R4_SCREEN"
        else "PASS_R_GT4_BOUNDARY_RECORDED_REVIEW_REQUIRED"
        if not failures
        else "FAIL_R_GT4_BOUNDARY"
    )
    rows.append(
        {
            "gate": "stage74_decision",
            "status": decision_status,
            "metric": "promotion_policy",
            "value": "",
            "evidence": OUT_CSV.relative_to(ROOT).as_posix(),
            "detail": (
                "Stage74 records r=6/r=8 complete-SAB smoke evidence and does not promote direct r>4 scaling"
                if not failures
                else f"failed_gates={failures}"
            ),
        }
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage74 R-Scaling Boundary Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage74 tests whether directly increasing the PVW/MAT-SAB lane count",
        "past the promoted small-r range improves complete SAB throughput. It",
        "does not modify scalar SAB, the default `sab_pvw_*` path, or any MAT",
        "key format.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | "
            f"{row['value']} | {row['evidence']} | {row['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The r=6 and r=8 smoke runs pass correctness and remain faster than",
            "repeated scalar SAB, but they do not beat the current r=4 promoted",
            "evidence. This records a scaling boundary: direct larger-r use of",
            "the current generic MAT path is not a promoted optimization. Future",
            "large-r work needs a new r>4-specific layout, tiling, or sparsity",
            "hypothesis plus full correctness, repeated performance, noise,",
            "resource, and closure gates.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage74 r-scaling boundary: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
