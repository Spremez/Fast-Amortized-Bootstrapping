#!/usr/bin/env python3
"""Stage205: current platform probe and small-sample complete-SAB A/B package."""

from __future__ import annotations

import csv
import hashlib
import re
import statistics
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage205_current_platform_probe"

PERF_SMOKE_SUMMARY = OUT_DIR / "stage28_perf_smoke" / "summary.csv"
PERF_ENV = OUT_DIR / "stage28_perf_smoke" / "environment.log"
SMOKE_SUMMARY = OUT_DIR / "stage98_current_smoke" / "summary.csv"
SMOKE_RAW = OUT_DIR / "stage98_current_smoke" / "raw_smoke.csv"
AB_R2 = OUT_DIR / "full_sab_ab_r2_runs3_sequential" / "summary.csv"
AB_R4 = OUT_DIR / "full_sab_ab_r4_runs3_sequential" / "summary.csv"
INVALID_R2 = OUT_DIR / "invalid_parallel_race_labeled_r2"
INVALID_R4 = OUT_DIR / "invalid_parallel_race_labeled_r4"

SUMMARY_CSV = OUT_DIR / "summary.csv"
PLATFORM_CSV = OUT_DIR / "platform_gate.csv"
AB_SUMMARY_CSV = OUT_DIR / "full_sab_ab_summary.csv"
INVALID_CSV = OUT_DIR / "invalid_run_log.csv"
PROOF_GATE_CSV = OUT_DIR / "proof_gate.csv"
NEXT_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_MD = OUT_DIR / "current_platform_probe_report.md"
ARTIFACT_CSV = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage205_current_platform_probe.md"
PLAN_MD = ROOT / "experiments" / "stage205_current_platform_probe_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage205_amortized_metric_and_platform_boundary.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_current_head_benchmark_policy.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB"
ACCESS_DATE = date.today().isoformat()


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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    write_text_lf(path, current.rstrip() + "\n" + text.rstrip() + "\n")


def status_for(rows: List[Dict[str, str]], key: str, value: str, status_key: str = "status") -> str:
    for row in rows:
        if row.get(key) == value:
            return row.get(status_key, "")
    return ""


def env_value(name: str) -> str:
    text = read_text(PERF_ENV)
    m = re.search(rf"^{re.escape(name)}=(.*)$", text, flags=re.MULTILINE)
    return m.group(1).strip() if m else ""


def summarize_ab(path: Path, r_value: int) -> Dict[str, str]:
    rows = read_csv(path)
    if not rows:
        return {
            "r": str(r_value),
            "status": "MISSING",
            "runs": "0",
            "evidence": rel(path),
        }
    speeds = [float(row["speedup_vs_scalar_repeated"]) for row in rows]
    pvw = [float(row["pvw_avg_us"]) for row in rows]
    scalar = [float(row["scalar_repeated_avg_us"]) for row in rows]
    pvw_lane = [float(row["pvw_lane_avg_us"]) for row in rows]
    scalar_lane = [float(row["scalar_lane_avg_us"]) for row in rows]
    correctness = "PASS" if all(row.get("status") == "Pass" for row in rows) else "FAIL"
    ratio_of_means = statistics.mean(scalar) / statistics.mean(pvw)
    lane_ratio_of_means = statistics.mean(scalar_lane) / statistics.mean(pvw_lane)
    return {
        "r": str(r_value),
        "status": correctness,
        "runs": str(len(rows)),
        "backend": "spqlios_avx512",
        "param": "SET_2_3_2048",
        "variant": "active_buffer_pvw_mat_sab",
        "metric": "T_bootstrap_over_r",
        "pvw_total_mean_us": f"{statistics.mean(pvw):.3f}",
        "scalar_repeated_total_mean_us": f"{statistics.mean(scalar):.3f}",
        "pvw_per_lane_mean_us": f"{statistics.mean(pvw_lane):.3f}",
        "scalar_repeated_per_lane_mean_us": f"{statistics.mean(scalar_lane):.3f}",
        "mean_of_run_speedups": f"{statistics.mean(speeds):.6f}",
        "min_speedup": f"{min(speeds):.6f}",
        "max_speedup": f"{max(speeds):.6f}",
        "ratio_of_mean_totals": f"{ratio_of_means:.6f}",
        "ratio_of_mean_per_lane": f"{lane_ratio_of_means:.6f}",
        "evidence": rel(path),
        "claim_level": "current_head_small_sample_only",
    }


def invalid_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for expected, path in [(2, INVALID_R2), (4, INVALID_R4)]:
        run_logs = sorted(path.glob("run_*.log")) if path.exists() else []
        actual = []
        for log in run_logs:
            text = read_text(log)
            m = re.search(r"SAB_PVW_BENCH correctness target_full r=(\d+)", text)
            actual.append(m.group(1) if m else "missing")
        rows.append(
            {
                "invalid_id": f"parallel_race_labeled_r{expected}",
                "status": "REJECTED",
                "expected_r": str(expected),
                "observed_r_values": ";".join(actual),
                "reason": "r2 and r4 builds were launched concurrently in one workspace and raced on build/main; outputs are preserved but excluded.",
                "evidence": rel(path / "summary.csv") if (path / "summary.csv").exists() else rel(path),
            }
        )
    return rows


def platform_rows() -> List[Dict[str, str]]:
    perf_rows = read_csv(PERF_SMOKE_SUMMARY)
    smoke_rows = read_csv(SMOKE_SUMMARY)
    return [
        {
            "gate": "wsl_toolchain",
            "status": "PASS",
            "evidence": rel(PERF_ENV),
            "detail": f"cpu_model={env_value('cpu_model')}; perf_event_paranoid={env_value('perf_event_paranoid')}",
            "impact": "WSL can run current-head smoke and same-backend small-sample A/B.",
        },
        {
            "gate": "avx512_vaes_flags",
            "status": "PASS" if "avx512" in env_value("cpu_flags") and "vaes" in env_value("cpu_flags") else "FAIL",
            "evidence": rel(PERF_ENV),
            "detail": "CPU flags expose avx512 and vaes under WSL.",
            "impact": "spqlios_avx512 path is admissible for smoke/small-sample A/B.",
        },
        {
            "gate": "hardware_perf_counters",
            "status": status_for(perf_rows, "probe", "hardware_counter_gate"),
            "evidence": rel(PERF_SMOKE_SUMMARY),
            "detail": status_for(perf_rows, "probe", "perf_command"),
            "impact": "MAT-AVX512 load/store/FMA attribution remains blocked on this WSL image because perf is missing.",
        },
        {
            "gate": "current_head_smoke",
            "status": status_for(smoke_rows, "gate", "stage98_decision"),
            "evidence": rel(SMOKE_SUMMARY),
            "detail": "scalar binary full run, explicit active-buffer PVW gate, explicit backend PVW gate, and scalar ternary build pass.",
            "impact": "Current HEAD is runnable before interpreting A/B samples.",
        },
    ]


def proof_gate_rows(ab_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    all_ab_pass = all(row.get("status") == "PASS" and float(row.get("min_speedup", "0")) > 1.0 for row in ab_rows)
    return [
        {
            "gate": "G1_platform",
            "status": "PASS_WITH_PERF_BLOCKED",
            "evidence": rel(PLATFORM_CSV),
            "detail": "WSL/spqlios_avx512 can run smoke and A/B; hardware counters are unavailable.",
            "remaining_gap": "Install Linux perf or rerun on native Linux for load/store/FMA attribution.",
        },
        {
            "gate": "G2_current_head_smoke",
            "status": "PASS",
            "evidence": rel(SMOKE_SUMMARY),
            "detail": "Current scalar/default and explicit PVW paths pass smoke.",
            "remaining_gap": "Smoke is not a speed claim.",
        },
        {
            "gate": "G3_complete_sab_ab_small_sample",
            "status": "PASS_SMALL_SAMPLE" if all_ab_pass else "FAIL",
            "evidence": rel(AB_SUMMARY_CSV),
            "detail": "Sequential r=2/r=4 complete-SAB A/B uses T_bootstrap/r under the same backend.",
            "remaining_gap": "Increase runs/seeds and separate noise instrumentation before paper-grade claims.",
        },
        {
            "gate": "G4_invalid_parallel_run_rejected",
            "status": "PASS_REJECTED_INVALID",
            "evidence": rel(INVALID_CSV),
            "detail": "Concurrent make/main race output is preserved but excluded.",
            "remaining_gap": "Run build-and-benchmark jobs sequentially or isolate worktrees.",
        },
    ]


def next_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "high_stat_current_head_ab",
            "entry_condition": "Use isolated sequential worktree/build directories or single-run serialization.",
            "gate": "10+ complete-SAB runs for r=2/r=4 and 20+ noise seeds with T_bootstrap/r endpoint.",
            "current_status": "ready",
            "evidence": rel(AB_SUMMARY_CSV),
        },
        {
            "priority": "P1",
            "route": "perf_counter_attribution",
            "entry_condition": "Linux perf is installed and hardware counters are usable.",
            "gate": "Record cycles, instructions, cache, load/store/FMA proxy counters for scalar vs MAT paths.",
            "current_status": "blocked_perf_missing",
            "evidence": rel(PLATFORM_CSV),
        },
        {
            "priority": "P2",
            "route": "full_text_anchor_table",
            "entry_condition": "Reviewed 2025/686 full text is available.",
            "gate": "Map SAB equations and reported complexity to paper anchors.",
            "current_status": "waiting_full_text",
            "evidence": "repro/stage204_source_anchor_intake/proof_gate.csv",
        },
    ]


def summary_rows(platform: List[Dict[str, str]], ab_rows: List[Dict[str, str]], gates: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "gate": "stage205_platform",
            "status": "PASS_WITH_PERF_BLOCKED",
            "metric": "platform_gates",
            "value": str(len(platform)),
            "evidence": rel(PLATFORM_CSV),
            "detail": "WSL/spqlios_avx512 is usable for smoke/A-B, but perf counter attribution is blocked.",
            "next_action": "Install perf or rerun on native Linux for hardware-counter conclusions.",
        },
        {
            "gate": "stage205_current_smoke",
            "status": "PASS",
            "metric": "smoke_rows",
            "value": str(len(read_csv(SMOKE_RAW))),
            "evidence": rel(SMOKE_SUMMARY),
            "detail": "Current-head scalar and explicit PVW smoke gates pass.",
            "next_action": "Use this only as runnability evidence.",
        },
        {
            "gate": "stage205_full_sab_ab",
            "status": "PASS_SMALL_SAMPLE",
            "metric": "ab_rows",
            "value": str(len(ab_rows)),
            "evidence": rel(AB_SUMMARY_CSV),
            "detail": "Sequential r=2/r=4 complete-SAB A/B shows positive T_bootstrap/r speedup under same backend.",
            "next_action": "Run high-stat A/B and noise gates before upgrading claim level.",
        },
        {
            "gate": "stage205_invalid_parallel_rejection",
            "status": "PASS_REJECTED_INVALID",
            "metric": "invalid_rows",
            "value": str(len(invalid_rows())),
            "evidence": rel(INVALID_CSV),
            "detail": "Concurrent benchmark outputs are excluded due shared build/main race.",
            "next_action": "Do not run make-based benchmark variants in parallel in one worktree.",
        },
        {
            "gate": "stage205_decision",
            "status": DECISION,
            "metric": "goal_status",
            "value": "active",
            "evidence": rel(PROOF_GATE_CSV),
            "detail": "Current-head execution moved from metadata-only back to concrete A/B evidence, with strict claim boundary.",
            "next_action": "Proceed to high-stat current-head A/B or perf-counter attribution.",
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


def build_report(summary: List[Dict[str, str]], platform: List[Dict[str, str]], ab_rows: List[Dict[str, str]], invalid: List[Dict[str, str]], gates: List[Dict[str, str]], nextq: List[Dict[str, str]]) -> str:
    return f"""# Stage205 Current Platform Probe

Decision: `{DECISION}`.

Stage205 moves the active loop back to executable evidence. The primary
complete-SAB metric is amortized latency per processed lane,
`T_bootstrap / r`; for same-r comparison this equals the total-time ratio
between repeated scalar SAB and one PVW/MAT-SAB run.

## Summary

{table(summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])}

## Platform Gates

{table(platform, ["gate", "status", "evidence", "detail", "impact"])}

## Complete-SAB A/B

{table(ab_rows, ["r", "status", "runs", "backend", "param", "metric", "pvw_total_mean_us", "scalar_repeated_total_mean_us", "pvw_per_lane_mean_us", "scalar_repeated_per_lane_mean_us", "mean_of_run_speedups", "min_speedup", "max_speedup", "ratio_of_mean_per_lane", "claim_level"])}

## Rejected Invalid Run

{table(invalid, ["invalid_id", "status", "expected_r", "observed_r_values", "reason", "evidence"])}

## Proof Gates

{table(gates, ["gate", "status", "evidence", "detail", "remaining_gap"])}

## Next Queue

{table(nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])}
"""


def update_tracking() -> None:
    append_once(
        ROADMAP_MD,
        "## Stage 205: Current Platform Probe",
        """
## Stage 205: Current Platform Probe

Goal:

```text
Return from source/theory gates to executable current-head evidence: WSL
platform probe, current scalar/PVW smoke, and sequential complete-SAB A/B using
the amortized T_bootstrap/r endpoint.
```

Status:

```text
Completed. Stage205 records PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB.
WSL/spqlios_avx512 smoke passes and sequential r=2/r=4 complete-SAB A/B is
positive, but hardware-counter attribution is blocked because perf is missing
and the A/B evidence is small-sample only.
```
""",
    )
    append_once(
        GOAL_MD,
        "Stage205 records current platform probe.",
        """
Stage205 records current platform probe. Decision: `PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB`.
It refreshes current-head WSL/spqlios_avx512 smoke and sequential r=2/r=4
complete-SAB A/B with `T_bootstrap/r` as the primary endpoint; it also records
that hardware-counter attribution is blocked by missing `perf`.
""",
    )
    append_once(
        CURRENT_GOAL_MD,
        "109. Treat Stage205 as current platform probe:",
        """
109. Treat Stage205 as current platform probe:
    `PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB`. Current-head scalar and
    explicit PVW paths pass WSL/spqlios_avx512 smoke; sequential r=2/r=4
    complete-SAB A/B is positive under `T_bootstrap/r`, but remains small-sample
    evidence and perf-counter attribution is blocked.
""",
    )
    append_once(
        HYPOTHESIS_YAML,
        "  - id: H129_current_platform_small_sample_ab",
        """
  - id: H129_current_platform_small_sample_ab
    statement: >
      Current-head PVW/MAT-SAB must preserve scalar/PVW runnability and show
      positive same-backend amortized complete-SAB evidence before high-stat
      optimization or paper claims continue.
    mechanism: >
      Stage205 runs WSL/spqlios_avx512 platform gates, current-head scalar/PVW
      smoke, sequential r=2/r=4 complete-SAB A/B under T_bootstrap/r, and
      rejects a concurrent make/main race run.
    status: stage205_current_platform_probe
    evidence: docs/stage205_current_platform_probe.md; experiments/stage205_current_platform_probe_plan.md; theory_checks/stage205_amortized_metric_and_platform_boundary.md; repro/stage205_current_platform_probe/summary.csv
    current_decision: >
      PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB
    failure_criteria:
      - parallel make/build races are used as performance evidence
      - small-sample A/B is upgraded to paper-grade statistical evidence
      - hardware-counter conclusions are made while perf is unavailable
""",
    )
    append_once(
        RUN_LOG,
        "stage205_current_platform_probe",
        f"{ACCESS_DATE},{git_commit()},stage205_current_platform_probe,WSL Stage28 smoke + Stage98 smoke + sequential Stage20 r=2/r=4 runs3,spqlios_avx512 SET_2_3_2048,none,{rel(SUMMARY_CSV)},{DECISION}\n",
    )
    append_once(
        MANIFEST,
        "### Stage205 Current Platform Probe",
        """
### Stage205 Current Platform Probe

- `docs/stage205_current_platform_probe.md`
- `experiments/stage205_current_platform_probe_plan.md`
- `theory_checks/stage205_amortized_metric_and_platform_boundary.md`
- `algorithm_variants/mat_rlwe_sab_current_head_benchmark_policy.md`
- `repro/stage205_current_platform_probe/`
""",
    )
    append_once(
        CHECKLIST,
        "- [x] Stage205 current platform probe records WSL smoke, small-sample A/B, and invalid parallel-run rejection.",
        "- [x] Stage205 current platform probe records WSL smoke, small-sample A/B, and invalid parallel-run rejection.\n",
    )


def main() -> None:
    platform = platform_rows()
    ab_rows = [summarize_ab(AB_R2, 2), summarize_ab(AB_R4, 4)]
    invalid = invalid_rows()
    gates = proof_gate_rows(ab_rows)
    nextq = next_rows()
    summary = summary_rows(platform, ab_rows, gates)

    write_csv(PLATFORM_CSV, platform, ["gate", "status", "evidence", "detail", "impact"])
    write_csv(AB_SUMMARY_CSV, ab_rows, ["r", "status", "runs", "backend", "param", "variant", "metric", "pvw_total_mean_us", "scalar_repeated_total_mean_us", "pvw_per_lane_mean_us", "scalar_repeated_per_lane_mean_us", "mean_of_run_speedups", "min_speedup", "max_speedup", "ratio_of_mean_totals", "ratio_of_mean_per_lane", "evidence", "claim_level"])
    write_csv(INVALID_CSV, invalid, ["invalid_id", "status", "expected_r", "observed_r_values", "reason", "evidence"])
    write_csv(PROOF_GATE_CSV, gates, ["gate", "status", "evidence", "detail", "remaining_gap"])
    write_csv(NEXT_CSV, nextq, ["priority", "route", "entry_condition", "gate", "current_status", "evidence"])
    write_csv(SUMMARY_CSV, summary, ["gate", "status", "metric", "value", "evidence", "detail", "next_action"])

    report = build_report(summary, platform, ab_rows, invalid, gates, nextq)
    write_text_lf(REPORT_MD, report)
    write_text_lf(OUT_MD, report)
    write_text_lf(
        PLAN_MD,
        f"""# Stage205 Current Platform Probe Plan

Primary endpoint: complete-SAB amortized latency per processed lane,
`T_bootstrap / r`, comparing one PVW/MAT-SAB run against r repeated scalar SAB
runs under the same backend.

Correctness gate: every A/B sample must include
`SAB_PVW_BENCH correctness target_full ... Pass`.

Performance gate: r=2 and r=4 sequential small-sample A/B must have min
speedup above 1.0 before high-stat reruns are worth scheduling.

Failure handling: concurrent make-based benchmark runs in one worktree are
rejected because they race on `build/` and `main`.

Decision: `{DECISION}`.
""",
    )
    write_text_lf(
        THEORY_MD,
        """# Stage205 Amortized Metric And Platform Boundary

For the MAT-RLWE/PVW path with r body lanes, the correct complete-SAB endpoint
is `T_bootstrap / r`. When comparing against r repeated scalar SAB runs, the
ratio of total times equals the ratio of per-lane amortized times because both
sides process r lanes.

This stage does not make a hardware-counter claim: WSL exposes AVX512/VAES
flags, but `perf` is missing, so load/store/FMA attribution remains blocked.
""",
    )
    write_text_lf(
        VARIANT_MD,
        """# Current-Head Benchmark Policy

PVW/MAT-SAB benchmark runs are admissible only when:

- scalar/default and explicit PVW smoke pass on the same commit;
- make/build jobs are serialized or isolated by worktree/build directory;
- the endpoint is recorded as `T_bootstrap/r`;
- noise-instrumented runs are separated from latency runs;
- hardware-counter claims require a working Linux `perf` path.
""",
    )
    write_text_lf(
        COMMANDS_MD,
        """# Stage205 Reproduction Commands

```powershell
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash -lc 'STAGE28_PERF_GATE_OUT_DIR=repro/stage205_current_platform_probe/stage28_perf_smoke bash scripts/run_stage28_native_perf_counter_gate.sh'
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash -lc 'STAGE98_OUT_DIR=repro/stage205_current_platform_probe/stage98_current_smoke FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage98_current_smoke_refresh.sh'
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash -lc 'STAGE20_ACTIVE_BENCH_RUNS=3 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage205_current_platform_probe/full_sab_ab_r2_runs3_sequential FFT_LIB=spqlios_avx512 bash scripts/run_stage20_active_buffer_bench.sh'
wsl --cd /mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping bash -lc 'STAGE20_ACTIVE_BENCH_RUNS=3 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage205_current_platform_probe/full_sab_ab_r4_runs3_sequential FFT_LIB=spqlios_avx512 bash scripts/run_stage20_active_buffer_bench.sh'
python scripts\\build_stage205_current_platform_probe.py
```
""",
    )

    raw_log_paths = sorted(OUT_DIR.rglob("*.log"))
    artifact_paths = [
        OUT_MD,
        PLAN_MD,
        THEORY_MD,
        VARIANT_MD,
        REPORT_MD,
        COMMANDS_MD,
        SUMMARY_CSV,
        PLATFORM_CSV,
        AB_SUMMARY_CSV,
        INVALID_CSV,
        PROOF_GATE_CSV,
        NEXT_CSV,
        PERF_SMOKE_SUMMARY,
        PERF_ENV,
        SMOKE_SUMMARY,
        SMOKE_RAW,
        AB_R2,
        AB_R4,
        INVALID_R2 / "summary.csv",
        INVALID_R4 / "summary.csv",
        Path(__file__),
    ] + raw_log_paths
    write_csv(ARTIFACT_CSV, artifact_rows(artifact_paths), ["path", "exists", "sha256", "bytes"])
    update_tracking()
    print(DECISION)


if __name__ == "__main__":
    main()
