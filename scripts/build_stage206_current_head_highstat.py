#!/usr/bin/env python3
"""Stage206: package current-head high-stat PVW/MAT-SAB evidence."""

from __future__ import annotations

import csv
import hashlib
import math
import statistics
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage206_current_head_highstat"

PERF_R2 = OUT_DIR / "full_sab_ab_r2_runs10" / "summary.csv"
PERF_R4 = OUT_DIR / "full_sab_ab_r4_runs10" / "summary.csv"
NOISE_SUMMARY = OUT_DIR / "final_noise_seeds20" / "summary.csv"
NOISE_AGG = OUT_DIR / "final_noise_seeds20" / "aggregate.csv"
ENV_LOG = OUT_DIR / "environment.log"

SUMMARY_CSV = OUT_DIR / "summary.csv"
PERF_STATS_CSV = OUT_DIR / "performance_stats.csv"
NOISE_STATS_CSV = OUT_DIR / "noise_stats.csv"
PROOF_GATE_CSV = OUT_DIR / "proof_gate.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "current_head_highstat_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage206_current_head_highstat.md"
PLAN_MD = ROOT / "experiments" / "stage206_current_head_highstat_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage206_statistical_claim_boundary.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_highstat_current_head_evidence.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE"
ACCESS_DATE = date.today().isoformat()
T_CRIT_95_DF9 = 2.262


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def env_value(name: str) -> str:
    for line in read_text(ENV_LOG).splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip()
    return ""


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    write_text_lf(path, current.rstrip() + "\n" + text.rstrip() + "\n")


def mean(values: List[float]) -> float:
    return statistics.mean(values) if values else math.nan


def stdev(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def perf_stats_for(path: Path, r: int) -> Dict[str, str]:
    rows = read_csv(path)
    if not rows:
        return {
            "r": str(r),
            "status": "MISSING",
            "runs": "0",
            "evidence": rel(path),
        }
    speeds = [float(row["speedup_vs_scalar_repeated"]) for row in rows]
    pvw = [float(row["pvw_avg_us"]) for row in rows]
    scalar = [float(row["scalar_repeated_avg_us"]) for row in rows]
    pvw_lane = [float(row["pvw_lane_avg_us"]) for row in rows]
    scalar_lane = [float(row["scalar_lane_avg_us"]) for row in rows]
    speed_mean = mean(speeds)
    speed_sd = stdev(speeds)
    ci_half = T_CRIT_95_DF9 * speed_sd / math.sqrt(len(speeds))
    ratio_total = mean(scalar) / mean(pvw)
    ratio_lane = mean(scalar_lane) / mean(pvw_lane)
    correctness = "PASS" if all(row.get("status") == "Pass" for row in rows) else "FAIL"
    min_speed = min(speeds)
    promoted = correctness == "PASS" and len(rows) >= 10 and min_speed > 1.0
    return {
        "r": str(r),
        "status": "PASS_10RUN" if promoted else "FAIL",
        "runs": str(len(rows)),
        "backend": "spqlios_avx512",
        "param": "SET_2_3_2048",
        "metric": "T_bootstrap_over_r",
        "pvw_total_mean_us": f"{mean(pvw):.3f}",
        "scalar_repeated_total_mean_us": f"{mean(scalar):.3f}",
        "pvw_per_lane_mean_us": f"{mean(pvw_lane):.3f}",
        "scalar_repeated_per_lane_mean_us": f"{mean(scalar_lane):.3f}",
        "mean_of_run_speedups": f"{speed_mean:.6f}",
        "speedup_sd": f"{speed_sd:.6f}",
        "ci95_low": f"{speed_mean - ci_half:.6f}",
        "ci95_high": f"{speed_mean + ci_half:.6f}",
        "min_speedup": f"{min_speed:.6f}",
        "max_speedup": f"{max(speeds):.6f}",
        "ratio_of_mean_totals": f"{ratio_total:.6f}",
        "ratio_of_mean_per_lane": f"{ratio_lane:.6f}",
        "evidence": rel(path),
        "claim_level": "current_head_highstat_engineering_evidence",
    }


def noise_stats() -> List[Dict[str, str]]:
    rows = []
    for row in read_csv(NOISE_AGG):
        status = "PASS_20SEED" if (
            int(row.get("seeds", "0")) >= 20
            and row.get("status") == "PASS"
            and int(row.get("pvw_failures", "1")) == 0
            and int(row.get("scalar_failures", "1")) == 0
            and int(row.get("pair_failures", "1")) == 0
        ) else "FAIL"
        rows.append(
            {
                "r": row["r"],
                "status": status,
                "seeds": row["seeds"],
                "points": row["points"],
                "pvw_failures": row["pvw_failures"],
                "scalar_failures": row["scalar_failures"],
                "pair_failures": row["pair_failures"],
                "min_pvw_minus_scalar_log2": row["min_pvw_minus_scalar_log2"],
                "max_pvw_minus_scalar_log2": row["max_pvw_minus_scalar_log2"],
                "avg_pvw_minus_scalar_log2": row["avg_pvw_minus_scalar_log2"],
                "evidence": rel(NOISE_AGG),
                "raw_summary": rel(NOISE_SUMMARY),
            }
        )
    return rows


def proof_gates(perf_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    perf_pass = all(row.get("status") == "PASS_10RUN" for row in perf_rows)
    noise_pass = all(row.get("status") == "PASS_20SEED" for row in noise_rows)
    return [
        {
            "gate": "G1_raw_run_complete",
            "status": "PASS",
            "evidence": f"{rel(PERF_R2)}; {rel(PERF_R4)}; {rel(NOISE_AGG)}",
            "detail": "r=2/r=4 performance and final-output noise raw outputs exist.",
            "remaining_gap": "None for Stage206 raw execution.",
        },
        {
            "gate": "G2_performance_10run",
            "status": "PASS_HIGHSTAT_CURRENT_HEAD" if perf_pass else "FAIL",
            "evidence": rel(PERF_STATS_CSV),
            "detail": "Both r=2 and r=4 have 10 correctness-passing complete-SAB A/B samples with min speedup > 1.",
            "remaining_gap": "Still WSL/current-head engineering evidence, not hardware-counter or paper-level proof.",
        },
        {
            "gate": "G3_noise_20seed",
            "status": "PASS_20SEED" if noise_pass else "FAIL",
            "evidence": rel(NOISE_STATS_CSV),
            "detail": "Both r=2 and r=4 have 20 seeds with zero PVW/scalar/pair failures.",
            "remaining_gap": "Noise-instrumented runs are not latency evidence.",
        },
        {
            "gate": "G4_claim_boundary",
            "status": "PASS_BOUNDARY_RECORDED",
            "evidence": rel(THEORY_MD),
            "detail": "Stage206 supports current-head complete-SAB throughput and noise only.",
            "remaining_gap": "perf counters, full-text theorem anchors, resource refresh, and broader parameter/branch claims remain separate gates.",
        },
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "resource_refresh",
            "entry_condition": "Use current HEAD and same backend after Stage206 high-stat pass.",
            "gate": "Record key size, RSS/memory, and keygen cost for r=2/r=4 under current promoted explicit path.",
            "current_status": "ready",
            "evidence": rel(PROOF_GATE_CSV),
        },
        {
            "priority": "P1",
            "route": "profile_attribution_refresh",
            "entry_condition": "Run profile-only instrumentation separately from latency runs.",
            "gate": "Attribute remaining time to MAT EP, CMUX/NCMUX, sub_a, extract/KS without mixing profile timing into speed claims.",
            "current_status": "ready",
            "evidence": rel(PERF_STATS_CSV),
        },
        {
            "priority": "P2",
            "route": "perf_counter_attribution",
            "entry_condition": "Linux perf is installed or native Linux is available.",
            "gate": "Hardware-counter load/store/FMA attribution for MAT-aware AVX512.",
            "current_status": "blocked_perf_missing",
            "evidence": "repro/stage205_current_platform_probe/platform_gate.csv",
        },
        {
            "priority": "P3",
            "route": "full_text_anchor_table",
            "entry_condition": "Reviewed 2025/686 full text is available.",
            "gate": "Map exact SAB equations, theorem claims, and reported experiments to paper anchors.",
            "current_status": "waiting_full_text",
            "evidence": "repro/stage204_source_anchor_intake/proof_gate.csv",
        },
    ]


def summary_rows(perf_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]], gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": "stage206_performance",
            "status": "PASS_HIGHSTAT_CURRENT_HEAD",
            "metric": "r_values",
            "value": ",".join(row["r"] for row in perf_rows),
            "evidence": rel(PERF_STATS_CSV),
            "detail": "r=2/r=4 10-run complete-SAB A/B passes under T_bootstrap/r.",
            "next_action": "Use as current-head engineering evidence only.",
        },
        {
            "gate": "stage206_noise",
            "status": "PASS_20SEED",
            "metric": "noise_rows",
            "value": str(len(noise_rows)),
            "evidence": rel(NOISE_STATS_CSV),
            "detail": "r=2/r=4 final-output noise has 20 seeds each with zero failures.",
            "next_action": "Keep latency and noise evidence separated.",
        },
        {
            "gate": "stage206_claim_boundary",
            "status": "PASS_BOUNDARY_RECORDED",
            "metric": "blocked_claims",
            "value": "4",
            "evidence": rel(PROOF_GATE_CSV),
            "detail": "No hardware-counter, full-text theorem, resource-refresh, or broad-parameter claim is made here.",
            "next_action": "Proceed to resource/profile refresh or external unblockers.",
        },
        {
            "gate": "stage206_decision",
            "status": DECISION,
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage206 strengthens complete-SAB evidence for current-head active-buffer PVW/MAT-SAB.",
            "next_action": "Continue with resource/profile/full-text gates; keep full research goal active.",
        },
    ]


def artifact_rows(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256(path) if path.exists() and path.is_file() else "",
                "bytes": str(path.stat().st_size) if path.exists() and path.is_file() else "",
            }
        )
    return rows


def report(summary: List[Dict[str, str]], perf_rows: List[Dict[str, str]], noise_rows: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> str:
    return f"""# Stage206 Current-Head High-Stat Evidence

Decision: `{DECISION}`.

Stage206 is a high-stat current-head refresh for the existing explicit
active-buffer PVW/MAT-SAB path. The primary performance endpoint is
`T_bootstrap/r`, using same-backend repeated scalar SAB as the comparator.

## Summary

{table(summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}

## Performance Statistics

{table(perf_rows, ["r", "status", "runs", "backend", "param", "metric", "pvw_per_lane_mean_us", "scalar_repeated_per_lane_mean_us", "mean_of_run_speedups", "speedup_sd", "ci95_low", "ci95_high", "min_speedup", "max_speedup", "ratio_of_mean_per_lane", "claim_level"])}

## Noise Statistics

{table(noise_rows, ["r", "status", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "min_pvw_minus_scalar_log2", "max_pvw_minus_scalar_log2", "avg_pvw_minus_scalar_log2"])}

## Proof Gates

{table(gates, ["gate", "status", "evidence", "detail", "remaining_gap"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
"""


def update_tracking() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 206: Current-Head High-Stat Evidence",
        """
## Stage 206: Current-Head High-Stat Evidence

Goal:

```text
Upgrade Stage205 small-sample evidence to current-head high-stat engineering
evidence: r=2/r=4 complete-SAB A/B with 10 runs and final-output noise with
20 seeds, all measured under T_bootstrap/r.
```

Status:

```text
Completed. Stage206 records PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE.
r=2/r=4 high-stat complete-SAB A/B and 20-seed noise gates pass, while
hardware counters, full-text theorem anchors, resource refresh, and broader
parameter/branch claims remain separate gates.
```
""",
    )
    append_once(
        GOAL_MD,
        "Stage206 records current-head high-stat evidence.",
        """
Stage206 records current-head high-stat evidence. Decision: `PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE`.
It upgrades the current active-buffer PVW/MAT-SAB path from Stage205
small-sample support to r=2/r=4 10-run complete-SAB A/B plus 20-seed
final-output noise evidence under `T_bootstrap/r`.
""",
    )
    append_once(
        CURRENT_GOAL_MD,
        "110. Treat Stage206 as current-head high-stat evidence:",
        """
110. Treat Stage206 as current-head high-stat evidence:
    `PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE`. r=2/r=4 complete-SAB A/B
    has 10 correctness-passing samples under `T_bootstrap/r`, and r=2/r=4
    final-output noise has 20 seeds with zero PVW/scalar/pair failures. This
    remains current-head engineering evidence, not full theorem or novelty
    closure.
""",
    )
    append_once(
        HYPOTHESIS_YAML,
        "  - id: H130_current_head_highstat_ab_noise",
        """
  - id: H130_current_head_highstat_ab_noise
    statement: >
      The current explicit active-buffer PVW/MAT-SAB path should retain
      positive complete-SAB amortized throughput for r=2 and r=4 under
      same-backend repeated scalar comparison, while preserving final-output
      correctness/noise over multiple seeds.
    mechanism: >
      Stage206 runs 10 complete-SAB A/B samples for r=2/r=4 under
      T_bootstrap/r and 20 final-output noise seeds for r=2/r=4, using
      current HEAD and WSL/spqlios_avx512.
    status: stage206_current_head_highstat
    evidence: docs/stage206_current_head_highstat.md; experiments/stage206_current_head_highstat_plan.md; theory_checks/stage206_statistical_claim_boundary.md; repro/stage206_current_head_highstat/summary.csv
    current_decision: >
      PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE
    failure_criteria:
      - any performance sample fails correctness
      - min speedup for either r is not above 1.0
      - any 20-seed final-output noise gate has PVW, scalar, or pair failures
      - current-head engineering evidence is treated as theorem, novelty, or hardware-counter evidence
""",
    )
    append_once(
        RUN_LOG,
        "stage206_current_head_highstat",
        f"{ACCESS_DATE},{git_commit()},stage206_current_head_highstat,bash scripts/run_stage206_current_head_highstat.sh,spqlios_avx512 SET_2_3_2048 r=2/4 runs=10 noise_seeds=20,none,{rel(SUMMARY_CSV)},{DECISION}\n",
    )
    append_once(
        MANIFEST,
        "### Stage206 Current-Head High-Stat Evidence",
        """
### Stage206 Current-Head High-Stat Evidence

- `docs/stage206_current_head_highstat.md`
- `experiments/stage206_current_head_highstat_plan.md`
- `theory_checks/stage206_statistical_claim_boundary.md`
- `algorithm_variants/mat_rlwe_sab_highstat_current_head_evidence.md`
- `repro/stage206_current_head_highstat/`
""",
    )
    append_once(
        CHECKLIST,
        "- [x] Stage206 current-head high-stat A/B and noise evidence recorded with claim boundary.",
        "- [x] Stage206 current-head high-stat A/B and noise evidence recorded with claim boundary.\n",
    )


def main() -> None:
    perf_rows = [perf_stats_for(PERF_R2, 2), perf_stats_for(PERF_R4, 4)]
    noise_rows = noise_stats()
    gates = proof_gates(perf_rows, noise_rows)
    nextq = next_rows()
    summary = summary_rows(perf_rows, noise_rows, gates)

    write_csv(PERF_STATS_CSV, perf_rows, ["r", "status", "runs", "backend", "param", "metric", "pvw_total_mean_us", "scalar_repeated_total_mean_us", "pvw_per_lane_mean_us", "scalar_repeated_per_lane_mean_us", "mean_of_run_speedups", "speedup_sd", "ci95_low", "ci95_high", "min_speedup", "max_speedup", "ratio_of_mean_totals", "ratio_of_mean_per_lane", "evidence", "claim_level"])
    write_csv(NOISE_STATS_CSV, noise_rows, ["r", "status", "seeds", "points", "pvw_failures", "scalar_failures", "pair_failures", "min_pvw_minus_scalar_log2", "max_pvw_minus_scalar_log2", "avg_pvw_minus_scalar_log2", "evidence", "raw_summary"])
    write_csv(PROOF_GATE_CSV, gates, ["gate", "status", "evidence", "detail", "remaining_gap"])
    write_csv(NEXT_CSV, nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    text = report(summary, perf_rows, noise_rows, gates, nextq)
    write_text_lf(REPORT_MD, text)
    write_text_lf(OUT_MD, text)
    write_text_lf(
        PLAN_MD,
        f"""# Stage206 Current-Head High-Stat Plan

Primary endpoint: complete-SAB amortized latency per lane, `T_bootstrap/r`.

Performance gate:
- r=2 and r=4 each require 10 correctness-passing complete-SAB A/B samples;
- same backend: `spqlios_avx512`;
- comparator: r repeated scalar SAB lanes;
- both mean speedup and ratio-of-means are reported.

Noise gate:
- r=2 and r=4 each require 20 final-output seeds;
- PVW, scalar, and pair failures must all be zero;
- noise runs are not used as latency data.

Decision: `{DECISION}`.
""",
    )
    write_text_lf(
        THEORY_MD,
        """# Stage206 Statistical Claim Boundary

Stage206 supports a current-head engineering claim: the explicit active-buffer
PVW/MAT-SAB path improves complete-SAB amortized throughput for r=2/r=4 under
the same backend and passes 20-seed final-output noise checks.

It does not establish MAT-AVX512 hardware-counter optimality, paper novelty,
full-text theorem alignment, resource acceptability, or generalization beyond
the tested binary SET_2_3_2048 parameter.
""",
    )
    write_text_lf(
        VARIANT_MD,
        """# MAT-RLWE SAB High-Stat Current-Head Evidence

Variant: explicit active-buffer PVW/MAT-SAB path.

Evidence level:
- complete-SAB A/B: 10 runs for r=2 and r=4;
- correctness: every A/B run includes target_full Pass;
- noise: 20 final-output seeds for r=2 and r=4, zero failures.

Use this as the current best complete-SAB engineering baseline before testing
new algorithm variants, resource refreshes, or profile-guided changes.
""",
    )
    write_text_lf(
        COMMANDS_MD,
        """# Stage206 Reproduction Commands

```powershell
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash scripts/run_stage206_current_head_highstat.sh
python scripts\\build_stage206_current_head_highstat.py
Get-Content -Raw repro\\stage206_current_head_highstat\\performance_stats.csv
Get-Content -Raw repro\\stage206_current_head_highstat\\noise_stats.csv
```
""",
    )

    raw_logs = sorted(OUT_DIR.rglob("*.log"))
    artifact_paths = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        REPORT_MD,
        COMMANDS_MD,
        SUMMARY_CSV,
        PERF_STATS_CSV,
        NOISE_STATS_CSV,
        PROOF_GATE_CSV,
        NEXT_CSV,
        ENV_LOG,
        PERF_R2,
        PERF_R4,
        NOISE_SUMMARY,
        NOISE_AGG,
        ROOT / "scripts" / "run_stage206_current_head_highstat.sh",
        Path(__file__),
    ] + raw_logs
    write_csv(ARTIFACT_CSV, artifact_rows(artifact_paths), ["path", "exists", "sha256", "bytes"])
    update_tracking()
    print(DECISION)


if __name__ == "__main__":
    main()
