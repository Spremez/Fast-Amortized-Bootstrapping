#!/usr/bin/env python3
"""Build Stage110 r=6 fulltile complete-SAB gate report."""

from __future__ import annotations

import csv
import hashlib
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage110_r6_fulltile_fullsab_gate"
TILE4_SUMMARY = OUT_DIR / "tile4" / "summary.csv"
FULLTILE_SUMMARY = OUT_DIR / "fulltile" / "summary.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage110_r6_fulltile_fullsab_gate.md"
PLAN_MD = ROOT / "experiments" / "stage110_r6_fulltile_fullsab_gate_plan.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def fnum(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0.0)
    except ValueError:
        return 0.0


def mean_field(rows: List[Dict[str, str]], field: str) -> float:
    vals = [fnum(row, field) for row in rows if row.get(field, "")]
    return statistics.mean(vals) if vals else 0.0


def all_pass(rows: List[Dict[str, str]]) -> bool:
    return bool(rows) and all(row.get("status") == "Pass" for row in rows)


def run_logs() -> List[Path]:
    return (
        sorted((OUT_DIR / "tile4").glob("run_*.log"))
        + sorted((OUT_DIR / "fulltile").glob("run_*.log"))
    )


def build_comparison() -> List[Dict[str, str]]:
    tile4 = read_csv(TILE4_SUMMARY)
    fulltile = read_csv(FULLTILE_SUMMARY)
    tile4_pvw = mean_field(tile4, "pvw_avg_us")
    fulltile_pvw = mean_field(fulltile, "pvw_avg_us")
    tile4_lane = mean_field(tile4, "pvw_lane_avg_us")
    fulltile_lane = mean_field(fulltile, "pvw_lane_avg_us")
    tile4_speed = mean_field(tile4, "speedup_vs_scalar_repeated")
    fulltile_speed = mean_field(fulltile, "speedup_vs_scalar_repeated")
    return [
        {
            "variant": "tile4",
            "runs": str(len(tile4)),
            "all_correct": str(all_pass(tile4)),
            "pvw_avg_us_mean": f"{tile4_pvw:.3f}",
            "pvw_lane_avg_us_mean": f"{tile4_lane:.3f}",
            "speedup_vs_scalar_mean": f"{tile4_speed:.3f}",
            "summary": rel(TILE4_SUMMARY) if TILE4_SUMMARY.exists() else "",
        },
        {
            "variant": "fulltile",
            "runs": str(len(fulltile)),
            "all_correct": str(all_pass(fulltile)),
            "pvw_avg_us_mean": f"{fulltile_pvw:.3f}",
            "pvw_lane_avg_us_mean": f"{fulltile_lane:.3f}",
            "speedup_vs_scalar_mean": f"{fulltile_speed:.3f}",
            "summary": rel(FULLTILE_SUMMARY) if FULLTILE_SUMMARY.exists() else "",
        },
        {
            "variant": "ratio_fulltile_vs_tile4",
            "runs": str(min(len(tile4), len(fulltile))),
            "all_correct": str(all_pass(tile4) and all_pass(fulltile)),
            "pvw_avg_us_mean": f"{tile4_pvw / fulltile_pvw:.3f}" if fulltile_pvw else "0.000",
            "pvw_lane_avg_us_mean": f"{tile4_lane / fulltile_lane:.3f}" if fulltile_lane else "0.000",
            "speedup_vs_scalar_mean": f"{fulltile_speed / tile4_speed:.3f}" if tile4_speed else "0.000",
            "summary": f"{rel(TILE4_SUMMARY)}; {rel(FULLTILE_SUMMARY)}",
        },
    ]


def build_summary(comparison: List[Dict[str, str]]) -> List[Dict[str, str]]:
    ratio = comparison[-1]
    correctness = ratio.get("all_correct") == "True"
    ratio_total = fnum(ratio, "pvw_avg_us_mean")
    runs = int(ratio.get("runs", "0") or 0)
    positive = correctness and ratio_total > 1.0
    high_stat = runs >= 3
    if not correctness:
        decision = "FAIL_STAGE110_R6_FULLTILE_CORRECTNESS"
        detail = "A complete-SAB correctness gate failed or summaries are missing."
    elif positive and high_stat:
        decision = "PASS_STAGE110_R6_FULLTILE_FULLSAB_POSITIVE_REVIEW_REQUIRED"
        detail = "fulltile beats tile4 in repeated complete-SAB smoke; noise/resource review required."
    elif positive:
        decision = "PASS_STAGE110_R6_FULLTILE_ONERUN_CANDIDATE_NOT_PROMOTED"
        detail = "fulltile beats tile4 in this complete-SAB smoke, but run count is below promotion threshold."
    else:
        decision = "PASS_STAGE110_R6_FULLTILE_NEGATIVE_NOT_PROMOTED"
        detail = "fulltile does not beat tile4 at complete-SAB level."
    return [
        {
            "gate": "stage110_inputs_available",
            "status": "PASS" if TILE4_SUMMARY.exists() and FULLTILE_SUMMARY.exists() else "MISSING",
            "metric": "tile4_summary;fulltile_summary",
            "value": f"{TILE4_SUMMARY.exists()};{FULLTILE_SUMMARY.exists()}",
            "evidence": f"{rel(TILE4_SUMMARY)}; {rel(FULLTILE_SUMMARY)}",
            "detail": "Both complete-SAB summaries are available.",
            "next_action": "Run scripts/run_stage110_r6_fulltile_fullsab_gate.sh if missing.",
        },
        {
            "gate": "stage110_correctness",
            "status": "PASS" if correctness else "FAIL",
            "metric": "all_correct",
            "value": str(correctness),
            "evidence": rel(COMPARISON_CSV),
            "detail": "Both variants passed complete-SAB correctness." if correctness else "Correctness failed or evidence missing.",
            "next_action": "Do not interpret timing unless correctness passes.",
        },
        {
            "gate": "stage110_fullsab_timing",
            "status": "PASS_POSITIVE" if positive else "NEGATIVE_OR_NEUTRAL",
            "metric": "tile4_pvw_mean/fulltile_pvw_mean",
            "value": f"{ratio_total:.3f}",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Ratio above 1 means fulltile is faster than tile4.",
            "next_action": "Promotion requires repeated runs plus noise/resource gates.",
        },
        {
            "gate": "stage110_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": detail,
            "next_action": "Use this as empirical routing evidence, not a paper-level claim.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage110 r=6 Fulltile Complete-SAB Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Test whether the r=6 fulltile kernel advantage observed in Stage108",
        "translates to complete SAB `T_total/r` under the current active-buffer",
        "PVW/MAT-SAB path.",
        "",
        "## Command",
        "",
        "```bash",
        "bash scripts/run_stage110_r6_fulltile_fullsab_gate.sh",
        "```",
        "",
        "Use `STAGE110_RUNS=3` or higher before promotion wording.",
    ]
    PLAN_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_md(summary: List[Dict[str, str]], comparison: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage110 r=6 Fulltile Complete-SAB Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage110 compares the existing r=6 tile4 and fulltile MAT kernels at the",
        "complete-SAB level under active-buffer PVW/MAT-SAB. This is a routing",
        "gate: a one-run win is not promoted to a final claim.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['detail']} |")
    lines += [
        "",
        "## Comparison",
        "",
        "| variant | runs | correct | PVW us mean | PVW lane us mean | speedup vs scalar mean |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in comparison:
        lines.append(
            f"| {row['variant']} | {row['runs']} | {row['all_correct']} | "
            f"{row['pvw_avg_us_mean']} | {row['pvw_lane_avg_us_mean']} | "
            f"{row['speedup_vs_scalar_mean']} |"
        )
    OUT_MD.write_bytes("\n".join(lines).encode("utf-8"))


def artifact_index(paths: Iterable[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def upsert_run_log(status: str) -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = [
        row for row in read_csv(RUN_LOG)
        if row.get("run_id") != "stage110-r6-fulltile-fullsab-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(SUMMARY_CSV),
        rel(COMPARISON_CSV),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "run_stage110_r6_fulltile_fullsab_gate.sh"),
        rel(ROOT / "scripts" / "build_stage110_r6_fulltile_fullsab_gate.py"),
        *[rel(path) for path in run_logs()],
    ]
    rows.append(
        {
            "run_id": "stage110-r6-fulltile-fullsab-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 110",
            "backend": "spqlios_avx512",
            "command": "bash scripts/run_stage110_r6_fulltile_fullsab_gate.sh; python scripts/build_stage110_r6_fulltile_fullsab_gate.py",
            "params": "BINARY SET_2_3_2048; r=6; active-buffer; tile4 vs fulltile",
            "seed": "default-rng",
            "status": status,
            "summary": "Stage110 checks whether r=6 fulltile kernel evidence transfers to complete SAB latency per lane.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    comparison = build_comparison()
    summary = build_summary(comparison)
    write_csv(
        COMPARISON_CSV,
        comparison,
        [
            "variant",
            "runs",
            "all_correct",
            "pvw_avg_us_mean",
            "pvw_lane_avg_us_mean",
            "speedup_vs_scalar_mean",
            "summary",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_md(summary, comparison)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                SUMMARY_CSV,
                COMPARISON_CSV,
                ROOT / "scripts" / "run_stage110_r6_fulltile_fullsab_gate.sh",
                ROOT / "scripts" / "build_stage110_r6_fulltile_fullsab_gate.py",
                TILE4_SUMMARY,
                FULLTILE_SUMMARY,
                *run_logs(),
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage110 r=6 fulltile complete-SAB gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") else 0


if __name__ == "__main__":
    raise SystemExit(main())
