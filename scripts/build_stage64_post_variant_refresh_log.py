#!/usr/bin/env python3
"""Build the Stage 64 post-variant refresh log."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / os.environ.get("STAGE64_OUT_DIR", "repro/stage64_post_variant_refresh")
SMOKE_CSV = OUT_DIR / "current_smoke" / "summary.csv"
NOISE_AGG = OUT_DIR / "final_noise" / "aggregate.csv"
STAGE50_MATRIX = ROOT / "repro" / "stage50_performance_evidence_matrix.csv"
OUT_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage64_post_variant_refresh_log.md"


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
            fieldnames=["gate", "status", "evidence", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def field_float(row: Dict[str, str], name: str) -> float:
    try:
        return float(row.get(name, "0"))
    except ValueError:
        return 0.0


def smoke_row() -> Dict[str, str]:
    rows = read_csv(SMOKE_CSV)
    by_step = {row.get("step"): row for row in rows}
    expected = [
        "scalar_binary_full_run",
        "pvw_target_full_gate",
        "scalar_ternary_build",
    ]
    missing = [step for step in expected if by_step.get(step, {}).get("status") != "PASS"]
    return {
        "gate": "stage64_current_smoke",
        "status": "PASS" if not missing else "FAIL",
        "evidence": SMOKE_CSV.relative_to(ROOT).as_posix(),
        "detail": "scalar binary, PVW target, and scalar ternary gates pass"
        if not missing
        else f"missing_or_failed={missing}",
    }


def full_sab_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in ("2", "4"):
        path = OUT_DIR / f"full_sab_r{r}" / "summary.csv"
        summary = read_csv(path)
        statuses = {row.get("status") for row in summary}
        speedups = [field_float(row, "speedup_vs_scalar_repeated") for row in summary]
        pvw = [field_float(row, "pvw_avg_us") for row in summary]
        scalar = [field_float(row, "scalar_repeated_avg_us") for row in summary]
        ok = len(summary) >= 3 and statuses == {"Pass"} and speedups and min(speedups) > 1.0
        detail = (
            "runs={runs}; pvw_mean_us={pvw_mean:.3f}; scalar_mean_us={scalar_mean:.3f}; "
            "speedup_mean={speedup_mean:.3f}; speedup_min={speedup_min:.3f}; "
            "speedup_max={speedup_max:.3f}; speedup_stddev={speedup_stddev:.3f}"
        ).format(
            runs=len(summary),
            pvw_mean=mean(pvw) if pvw else 0.0,
            scalar_mean=mean(scalar) if scalar else 0.0,
            speedup_mean=mean(speedups) if speedups else 0.0,
            speedup_min=min(speedups) if speedups else 0.0,
            speedup_max=max(speedups) if speedups else 0.0,
            speedup_stddev=stdev(speedups) if len(speedups) > 1 else 0.0,
        )
        rows.append(
            {
                "gate": f"stage64_full_sab_r{r}",
                "status": "PASS" if ok else "FAIL",
                "evidence": path.relative_to(ROOT).as_posix(),
                "detail": detail if summary else "summary missing",
            }
        )
    return rows


def noise_row() -> Dict[str, str]:
    rows = read_csv(NOISE_AGG)
    problems = []
    expected = {"2", "4"}
    seen = {row.get("r") for row in rows}
    if seen != expected:
        problems.append(f"seen_r={sorted(seen)}")
    for row in rows:
        if row.get("status") != "PASS":
            problems.append(f"r{row.get('r')}:status={row.get('status')}")
        for field in ("pvw_failures", "scalar_failures", "pair_failures"):
            if row.get(field) != "0":
                problems.append(f"r{row.get('r')}:{field}={row.get(field)}")
    return {
        "gate": "stage64_final_noise",
        "status": "PASS" if not problems and bool(rows) else "FAIL",
        "evidence": NOISE_AGG.relative_to(ROOT).as_posix(),
        "detail": "r=2/r=4 final-output noise smoke passes with zero failures"
        if not problems and rows
        else "; ".join(problems) or "noise aggregate missing",
    }


def stage50_row() -> Dict[str, str]:
    rows = read_csv(STAGE50_MATRIX)
    failed = [row.get("evidence_id") for row in rows if row.get("status") != "PASS"]
    return {
        "gate": "stage64_stage50_matrix",
        "status": "PASS" if rows and not failed else "FAIL",
        "evidence": STAGE50_MATRIX.relative_to(ROOT).as_posix(),
        "detail": "Stage50 performance evidence matrix still passes"
        if rows and not failed
        else f"failed={failed}" if rows else "Stage50 matrix missing",
    }


def build_rows() -> List[Dict[str, str]]:
    rows = [smoke_row(), *full_sab_rows(), noise_row(), stage50_row()]
    failures = [row["gate"] for row in rows if row["status"] != "PASS"]
    rows.append(
        {
            "gate": "stage64_decision",
            "status": "PASS_POST_VARIANT_REFRESH" if not failures else "FAIL_POST_VARIANT_REFRESH",
            "evidence": OUT_CSV.relative_to(ROOT).as_posix(),
            "detail": "Stage64 post-variant refresh passes; default promoted path remains valid"
            if not failures
            else f"failed_gates={failures}",
        }
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage 64 Post-Variant Refresh Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage64 refreshes current-head evidence after the Stage65A code change.",
        "It checks that the default promoted active-buffer PVW/MAT-SAB path and",
        "the scalar SAB baseline remain valid. It does not promote Stage65A.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['evidence']} | {row['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A passing Stage64 refresh means the repository head remains compatible",
            "with the scoped engineering PVW/MAT-SAB evidence after a local code",
            "variant. It is continuity evidence, not a new high-stat performance",
            "claim and not a novelty claim.",
        ]
    )
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = next(row for row in rows if row["gate"] == "stage64_decision")
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage64 post-variant refresh: {decision['status']}")
    return 0 if decision["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
