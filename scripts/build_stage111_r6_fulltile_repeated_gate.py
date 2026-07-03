#!/usr/bin/env python3
"""Build Stage111 r=6 fulltile repeated complete-SAB gate report."""

from __future__ import annotations

import csv
import hashlib
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage111_r6_fulltile_repeated_gate"
TILE4_SUMMARY = OUT_DIR / "tile4" / "summary.csv"
FULLTILE_SUMMARY = OUT_DIR / "fulltile" / "summary.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage111_r6_fulltile_repeated_gate.md"
PLAN_MD = ROOT / "experiments" / "stage111_r6_fulltile_repeated_gate_plan.md"
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


def values(rows: List[Dict[str, str]], field: str) -> List[float]:
    return [fnum(row, field) for row in rows if row.get(field, "")]


def mean(vals: List[float]) -> float:
    return statistics.mean(vals) if vals else 0.0


def stdev(vals: List[float]) -> float:
    return statistics.stdev(vals) if len(vals) > 1 else 0.0


def all_pass(rows: List[Dict[str, str]]) -> bool:
    return bool(rows) and all(row.get("status") == "Pass" for row in rows)


def run_logs() -> List[Path]:
    return (
        sorted((OUT_DIR / "tile4").glob("run_*.log"))
        + sorted((OUT_DIR / "fulltile").glob("run_*.log"))
    )


def variant_stats(name: str, path: Path, rows: List[Dict[str, str]]) -> Dict[str, str]:
    pvw = values(rows, "pvw_avg_us")
    lane = values(rows, "pvw_lane_avg_us")
    scalar = values(rows, "scalar_repeated_avg_us")
    speed = values(rows, "speedup_vs_scalar_repeated")
    return {
        "variant": name,
        "runs": str(len(rows)),
        "all_correct": str(all_pass(rows)),
        "pvw_avg_us_mean": f"{mean(pvw):.3f}",
        "pvw_avg_us_stddev": f"{stdev(pvw):.3f}",
        "pvw_avg_us_min": f"{min(pvw):.3f}" if pvw else "0.000",
        "pvw_avg_us_max": f"{max(pvw):.3f}" if pvw else "0.000",
        "pvw_lane_avg_us_mean": f"{mean(lane):.3f}",
        "pvw_lane_avg_us_stddev": f"{stdev(lane):.3f}",
        "scalar_repeated_avg_us_mean": f"{mean(scalar):.3f}",
        "speedup_vs_scalar_mean": f"{mean(speed):.3f}",
        "speedup_vs_scalar_stddev": f"{stdev(speed):.3f}",
        "summary": rel(path) if path.exists() else "",
    }


def ratio_row(tile4: Dict[str, str], fulltile: Dict[str, str]) -> Dict[str, str]:
    tile4_pvw = float(tile4["pvw_avg_us_mean"])
    fulltile_pvw = float(fulltile["pvw_avg_us_mean"])
    tile4_lane = float(tile4["pvw_lane_avg_us_mean"])
    fulltile_lane = float(fulltile["pvw_lane_avg_us_mean"])
    tile4_speed = float(tile4["speedup_vs_scalar_mean"])
    fulltile_speed = float(fulltile["speedup_vs_scalar_mean"])
    return {
        "variant": "ratio_fulltile_vs_tile4",
        "runs": str(min(int(tile4["runs"]), int(fulltile["runs"]))),
        "all_correct": str(tile4["all_correct"] == "True" and fulltile["all_correct"] == "True"),
        "pvw_avg_us_mean": f"{tile4_pvw / fulltile_pvw:.3f}" if fulltile_pvw else "0.000",
        "pvw_avg_us_stddev": "",
        "pvw_avg_us_min": "",
        "pvw_avg_us_max": "",
        "pvw_lane_avg_us_mean": f"{tile4_lane / fulltile_lane:.3f}" if fulltile_lane else "0.000",
        "pvw_lane_avg_us_stddev": "",
        "scalar_repeated_avg_us_mean": "",
        "speedup_vs_scalar_mean": f"{fulltile_speed / tile4_speed:.3f}" if tile4_speed else "0.000",
        "speedup_vs_scalar_stddev": "",
        "summary": f"{tile4['summary']}; {fulltile['summary']}",
    }


def build_comparison() -> List[Dict[str, str]]:
    tile4 = variant_stats("tile4", TILE4_SUMMARY, read_csv(TILE4_SUMMARY))
    fulltile = variant_stats("fulltile", FULLTILE_SUMMARY, read_csv(FULLTILE_SUMMARY))
    return [tile4, fulltile, ratio_row(tile4, fulltile)]


def build_summary(comparison: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tile4, fulltile, ratio = comparison
    runs = int(ratio.get("runs", "0") or 0)
    correctness = ratio.get("all_correct") == "True"
    ratio_total = float(ratio.get("pvw_avg_us_mean", "0") or 0.0)
    ratio_speed = float(ratio.get("speedup_vs_scalar_mean", "0") or 0.0)
    enough_runs = runs >= 3
    positive = correctness and enough_runs and ratio_total > 1.0
    practical = positive and ratio_total >= 1.01
    if not correctness:
        decision = "FAIL_STAGE111_R6_FULLTILE_REPEATED_CORRECTNESS"
        detail = "A repeated complete-SAB correctness gate failed or evidence is missing."
    elif not enough_runs:
        decision = "PASS_STAGE111_R6_FULLTILE_INSUFFICIENT_REPETITIONS"
        detail = "Repeated gate has fewer than 3 runs."
    elif practical:
        decision = "PASS_STAGE111_R6_FULLTILE_REPEATED_POSITIVE_NOISE_RESOURCE_REQUIRED"
        detail = "fulltile beats tile4 in repeated complete-SAB means; noise/resource gates are still required."
    elif positive:
        decision = "PASS_STAGE111_R6_FULLTILE_REPEATED_TINY_POSITIVE_NOT_PROMOTED"
        detail = "fulltile is positive but below the practical 1.01x threshold."
    else:
        decision = "PASS_STAGE111_R6_FULLTILE_REPEATED_NEGATIVE_NOT_PROMOTED"
        detail = "fulltile does not beat tile4 in repeated complete-SAB means."
    return [
        {
            "gate": "stage111_inputs_available",
            "status": "PASS" if TILE4_SUMMARY.exists() and FULLTILE_SUMMARY.exists() else "MISSING",
            "metric": "tile4_summary;fulltile_summary",
            "value": f"{TILE4_SUMMARY.exists()};{FULLTILE_SUMMARY.exists()}",
            "evidence": f"{rel(TILE4_SUMMARY)}; {rel(FULLTILE_SUMMARY)}",
            "detail": "Both repeated complete-SAB summaries are available.",
            "next_action": "Run scripts/run_stage111_r6_fulltile_repeated_gate.sh if missing.",
        },
        {
            "gate": "stage111_correctness",
            "status": "PASS" if correctness else "FAIL",
            "metric": "all_correct",
            "value": str(correctness),
            "evidence": rel(COMPARISON_CSV),
            "detail": "All repeated runs passed correctness." if correctness else "Correctness failed or evidence missing.",
            "next_action": "Do not interpret timing unless correctness passes.",
        },
        {
            "gate": "stage111_repetition_count",
            "status": "PASS" if enough_runs else "INSUFFICIENT",
            "metric": "runs_per_variant",
            "value": str(runs),
            "evidence": rel(COMPARISON_CSV),
            "detail": "At least 3 runs are required for this routing gate.",
            "next_action": "Rerun with STAGE111_RUNS=3 or higher if insufficient.",
        },
        {
            "gate": "stage111_fullsab_timing",
            "status": "PASS_POSITIVE" if positive else "NEGATIVE_OR_NEUTRAL",
            "metric": "tile4_pvw_mean/fulltile_pvw_mean;speedup_ratio",
            "value": f"{ratio_total:.3f};{ratio_speed:.3f}",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Ratio above 1 means fulltile is faster than tile4.",
            "next_action": "Promotion requires noise/resource and resource-overhead review.",
        },
        {
            "gate": "stage111_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": detail,
            "next_action": "If positive, open Stage112 noise/resource gate; otherwise keep fulltile as an ablation.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage111 r=6 Fulltile Repeated Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Confirm or reject the Stage110 one-run r=6 fulltile complete-SAB signal",
        "with at least three repeated runs for tile4 and fulltile under the same",
        "active-buffer PVW/MAT-SAB path.",
        "",
        "## Command",
        "",
        "```bash",
        "bash scripts/run_stage111_r6_fulltile_repeated_gate.sh",
        "```",
        "",
        "Promotion wording is still blocked after this stage until noise/resource",
        "gates are run.",
    ]
    PLAN_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_md(summary: List[Dict[str, str]], comparison: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage111 r=6 Fulltile Repeated Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage111 repeats the r=6 tile4/fulltile complete-SAB comparison. It is a",
        "routing gate, not a final paper claim.",
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
        "| variant | runs | correct | PVW mean us | PVW stddev us | PVW lane mean us | speedup mean | speedup stddev |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in comparison:
        lines.append(
            f"| {row['variant']} | {row['runs']} | {row['all_correct']} | "
            f"{row['pvw_avg_us_mean']} | {row['pvw_avg_us_stddev']} | "
            f"{row['pvw_lane_avg_us_mean']} | {row['speedup_vs_scalar_mean']} | "
            f"{row['speedup_vs_scalar_stddev']} |"
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
        if row.get("run_id") != "stage111-r6-fulltile-repeated-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(SUMMARY_CSV),
        rel(COMPARISON_CSV),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "run_stage111_r6_fulltile_repeated_gate.sh"),
        rel(ROOT / "scripts" / "build_stage111_r6_fulltile_repeated_gate.py"),
        *[rel(path) for path in run_logs()],
    ]
    rows.append(
        {
            "run_id": "stage111-r6-fulltile-repeated-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 111",
            "backend": "spqlios_avx512",
            "command": "bash scripts/run_stage111_r6_fulltile_repeated_gate.sh; python scripts/build_stage111_r6_fulltile_repeated_gate.py",
            "params": "BINARY SET_2_3_2048; r=6; active-buffer; tile4 vs fulltile; 3 repeated runs",
            "seed": "default-rng",
            "status": status,
            "summary": "Stage111 repeats the r=6 fulltile complete-SAB gate and keeps promotion blocked until noise/resource review.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    comparison = build_comparison()
    summary = build_summary(comparison)
    fields = [
        "variant",
        "runs",
        "all_correct",
        "pvw_avg_us_mean",
        "pvw_avg_us_stddev",
        "pvw_avg_us_min",
        "pvw_avg_us_max",
        "pvw_lane_avg_us_mean",
        "pvw_lane_avg_us_stddev",
        "scalar_repeated_avg_us_mean",
        "speedup_vs_scalar_mean",
        "speedup_vs_scalar_stddev",
        "summary",
    ]
    write_csv(COMPARISON_CSV, comparison, fields)
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
                ROOT / "scripts" / "run_stage111_r6_fulltile_repeated_gate.sh",
                ROOT / "scripts" / "build_stage111_r6_fulltile_repeated_gate.py",
                TILE4_SUMMARY,
                FULLTILE_SUMMARY,
                *run_logs(),
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage111 r=6 fulltile repeated gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") else 0


if __name__ == "__main__":
    raise SystemExit(main())
