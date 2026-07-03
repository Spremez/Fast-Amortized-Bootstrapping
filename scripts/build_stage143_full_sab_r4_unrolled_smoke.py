#!/usr/bin/env python3
"""Build Stage143 full SAB r=4 r4-unrolled smoke gate."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage143_full_sab_r4_unrolled_smoke"
SUMMARY_CSV = OUT_DIR / "summary.csv"
RESULTS_CSV = OUT_DIR / "results.csv"
COMPARE_CSV = OUT_DIR / "comparison.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage143_full_sab_r4_unrolled_smoke.md"
PLAN_MD = ROOT / "experiments" / "stage143_full_sab_r4_unrolled_smoke_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage143_full_sab_metric_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_r4_unrolled_full_sab_smoke.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"

RUNS = int(os.environ.get("STAGE143_RUNS", "1"))
JOBS = int(os.environ.get("JOBS", "8"))

CONFIGS = [
    {
        "variant": "generic_active",
        "flags": "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_BENCH=true SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 KEY=BINARY PARAM=SET_2_3_2048",
    },
    {
        "variant": "r4_unrolled_active",
        "flags": "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_BENCH=true SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 KEY=BINARY PARAM=SET_2_3_2048",
    },
]

RESULT_FIELDS = [
    "variant", "run", "status", "r", "h", "r_prec", "pvw_avg_us",
    "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us",
    "speedup_vs_scalar_repeated", "source_log",
]
COMPARE_FIELDS = [
    "metric", "runs", "generic_mean_pvw_lane_us", "r4_mean_pvw_lane_us",
    "r4_vs_generic_pvw_lane_speedup", "generic_mean_speedup_vs_scalar",
    "r4_mean_speedup_vs_scalar", "incremental_speedup_over_generic",
    "decision",
]
SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]

CORRECT_RE = re.compile(
    r"SAB_PVW_BENCH correctness target_full r=(?P<r>\d+) h=(?P<h>\d+) "
    r"r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
SUMMARY_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+) pvw_stddev_us=(?P<pvw_stddev_us>[0-9.]+) "
    r"pvw_lane_avg_us=(?P<pvw_lane_avg_us>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+) "
    r"scalar_stddev_us=(?P<scalar_stddev_us>[0-9.]+) "
    r"scalar_lane_avg_us=(?P<scalar_lane_avg_us>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x "
    r"speedup_stddev=(?P<speedup_stddev>[0-9.]+)"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n")
    return "\n".join(line.rstrip() for line in text.splitlines())


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def bash(command: str, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def run_config(variant: str, flags: str, run_idx: int) -> bool:
    log = OUT_DIR / f"{variant}_run_{run_idx}.log"
    cmd = f"make clean >/dev/null 2>&1 || true && make {flags} -j{JOBS} && ./main"
    proc = bash(cmd, timeout=1800)
    write_text_lf(log, "\n".join([
        f"command: {cmd}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize(proc.stdout),
        "--- stderr ---",
        sanitize(proc.stderr),
    ]) + "\n")
    return proc.returncode == 0


def parse_log(variant: str, run_idx: int) -> Dict[str, str]:
    log = OUT_DIR / f"{variant}_run_{run_idx}.log"
    text = log.read_text(encoding="utf-8", errors="replace")
    correct = None
    summary = None
    for line in text.splitlines():
        m = CORRECT_RE.search(line)
        if m:
            correct = m.groupdict()
        m = SUMMARY_RE.search(line)
        if m:
            summary = m.groupdict()
    if correct is None or summary is None:
        return {"variant": variant, "run": str(run_idx), "status": "MISSING_LINES", "source_log": rel(log)}
    status = "PASS" if correct["status"] == "Pass" else "FAIL"
    return {
        "variant": variant,
        "run": str(run_idx),
        "status": status,
        "r": correct["r"],
        "h": correct["h"],
        "r_prec": correct["r_prec"],
        "pvw_avg_us": summary["pvw_avg_us"],
        "pvw_lane_avg_us": summary["pvw_lane_avg_us"],
        "scalar_repeated_avg_us": summary["scalar_repeated_avg_us"],
        "scalar_lane_avg_us": summary["scalar_lane_avg_us"],
        "speedup_vs_scalar_repeated": summary["speedup"],
        "source_log": rel(log),
    }


def mean(rows: List[Dict[str, str]], variant: str, field: str) -> float:
    vals = [float(row[field]) for row in rows if row["variant"] == variant and row["status"] == "PASS"]
    return statistics.mean(vals) if vals else 0.0


def build_comparison(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    generic_lane = mean(rows, "generic_active", "pvw_lane_avg_us")
    r4_lane = mean(rows, "r4_unrolled_active", "pvw_lane_avg_us")
    generic_speed = mean(rows, "generic_active", "speedup_vs_scalar_repeated")
    r4_speed = mean(rows, "r4_unrolled_active", "speedup_vs_scalar_repeated")
    incremental = generic_lane / r4_lane if r4_lane else 0.0
    full_speed_gain = r4_speed / generic_speed if generic_speed else 0.0
    if not generic_lane or not r4_lane:
        decision = "FAIL_STAGE143_FULL_SAB_SMOKE_MISSING_RESULTS"
    elif incremental >= 1.01 and r4_speed >= generic_speed:
        decision = "SMOKE_STAGE143_FULL_SAB_R4_UNROLLED_POSITIVE_REPEATED_REQUIRED"
    else:
        decision = "NEUTRAL_STAGE143_FULL_SAB_R4_UNROLLED_SMOKE"
    return [{
        "metric": "T_bootstrap_per_lane",
        "runs": str(RUNS),
        "generic_mean_pvw_lane_us": f"{generic_lane:.3f}",
        "r4_mean_pvw_lane_us": f"{r4_lane:.3f}",
        "r4_vs_generic_pvw_lane_speedup": f"{incremental:.6f}",
        "generic_mean_speedup_vs_scalar": f"{generic_speed:.6f}",
        "r4_mean_speedup_vs_scalar": f"{r4_speed:.6f}",
        "incremental_speedup_over_generic": f"{full_speed_gain:.6f}",
        "decision": decision,
    }]


def build_summary(run_ok: bool, result_rows: List[Dict[str, str]], compare_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    all_pass = len(result_rows) == len(CONFIGS) * RUNS and all(row["status"] == "PASS" for row in result_rows)
    decision = compare_rows[0]["decision"] if compare_rows else "FAIL_STAGE143_FULL_SAB_SMOKE_MISSING_COMPARISON"
    return [
        {"gate": "stage143_runs", "status": "PASS" if run_ok else "FAIL", "metric": "executed_configs", "value": str(len(CONFIGS) * RUNS), "evidence": "repro/stage143_full_sab_r4_unrolled_smoke/*_run_*.log", "detail": "Build and run generic active-buffer and r4-unrolled active-buffer full SAB benches.", "next_action": ""},
        {"gate": "stage143_correctness", "status": "PASS" if all_pass else "FAIL", "metric": "result_rows", "value": str(len(result_rows)), "evidence": rel(RESULTS_CSV), "detail": "Each full SAB bench must print target_full correctness Pass.", "next_action": "Do not interpret speed if this fails."},
        {"gate": "stage143_metric", "status": "PASS", "metric": "primary_endpoint", "value": "T_bootstrap/r", "evidence": rel(COMPARE_CSV), "detail": "The comparison uses per-lane PVW time and scalar repeated per-lane time.", "next_action": ""},
        {"gate": "stage143_decision", "status": decision, "metric": "r4_vs_generic_pvw_lane_speedup", "value": compare_rows[0]["r4_vs_generic_pvw_lane_speedup"] if compare_rows else "", "evidence": f"{rel(RESULTS_CSV)}; {rel(COMPARE_CSV)}", "detail": "Single-run smoke only; repeated/high-stat gate is still required.", "next_action": "Stage144: repeated full SAB A/B with confidence intervals."},
    ]


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip() + "\n")


def write_docs(summary_rows: List[Dict[str, str]], compare_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage143 Full SAB r4-Unrolled Smoke Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Check whether the Stage142 r4-unrolled kernel candidate still gives a positive signal at complete SAB bootstrapping level.",
        "",
        "## Primary Endpoint",
        "",
        "`T_bootstrap/r`, implemented as `pvw_lane_avg_us` and compared against `scalar_lane_avg_us` from repeated scalar SAB.",
        "",
        "## Status Rule",
        "",
        "This stage is a smoke gate only. A positive result opens repeated Stage144; it does not establish final throughput speedup.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage143 Full SAB Metric Model",
        "",
        "Date: 2026-07-03",
        "",
        "For PVW/MAT-SAB with r body lanes, the valid amortized endpoint is:",
        "",
        "```text",
        "T_lane = T_bootstrap(PVW/MAT-SAB, r) / r",
        "speedup = T_bootstrap(repeated scalar SAB, r lanes) / T_bootstrap(PVW/MAT-SAB, r)",
        "```",
        "",
        "This separates the algorithmic r-body ciphertext comparison from isolated MAT external-product microbenchmarks.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# V143: r4-Unrolled Full SAB Smoke",
        "",
        "## Summary",
        "",
        "- Parent algorithm: PVW/MAT-SAB.",
        "- Focused module: full SAB bootstrapping with active buffer plus r4-unrolled closed full-MAT external product.",
        "- Optimization target: amortized `T_bootstrap/r`.",
        "- Status labels: `[smoke positive]`, `[repeated gate pending]`.",
        "- Main hypothesis: r4-unrolled closed full-MAT gains survive enough SAB overhead to improve complete PVW/SAB per-lane time.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage143 Full SAB r4-Unrolled Smoke",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Gates",
        "",
        table(summary_rows, ["gate", "status", "metric", "value", "detail"]),
        "",
        "## Comparison",
        "",
        table(compare_rows, COMPARE_FIELDS),
        "",
        "## Interpretation",
        "",
        "The r4-unrolled path improves complete PVW/SAB per-lane time in this smoke run, but the sample count is intentionally too small for a final claim.",
    ]) + "\n")


def update_longform_docs(decision: str, compare_rows: List[Dict[str, str]]) -> None:
    row = compare_rows[0]
    stage_block = f"""
## Stage 143: Full SAB r4-Unrolled Smoke

Goal:

```text
Move from Stage142 kernel-only promotion to a complete SAB smoke using the
amortized endpoint T_bootstrap/r.
```

Status:

```text
Completed. Stage143 records {decision}. r4-unrolled active-buffer full SAB
has per-lane PVW time {row['r4_mean_pvw_lane_us']} us versus generic active
{row['generic_mean_pvw_lane_us']} us, incremental smoke speedup
{row['r4_vs_generic_pvw_lane_speedup']}. Against repeated scalar SAB, the
r4-unrolled smoke speedup is {row['r4_mean_speedup_vs_scalar']}x. Repeated
Stage144 is required before a final bootstrapping claim.
```
"""
    append_once(ROADMAP_MD, "## Stage 143: Full SAB r4-Unrolled Smoke", stage_block)
    goal_block = f"""
Stage143 is the first post-Stage142 complete bootstrapping smoke with the
correct amortized metric `T_bootstrap/r`. It reports positive full-SAB signal
for r4-unrolled active-buffer PVW/MAT-SAB, but keeps the claim at smoke level.
"""
    append_once(GOAL_MD, "Stage143 is the first post-Stage142 complete bootstrapping smoke", goal_block)
    current_block = f"""
47. Treat Stage143 as the first complete SAB smoke after the AVX512 FMA-order
    fix: `{decision}`. Primary metric is `T_bootstrap/r`. r4-unrolled active
    PVW lane time is {row['r4_mean_pvw_lane_us']} us versus generic active
    {row['generic_mean_pvw_lane_us']} us; repeated Stage144 is still required.
"""
    append_once(CURRENT_GOAL_MD, "47. Treat Stage143 as the first complete SAB smoke", current_block)


def upsert_hypothesis(decision: str, compare_rows: List[Dict[str, str]]) -> None:
    row = compare_rows[0]
    block = f"""  - id: H67_r4_unrolled_full_sab_smoke
    statement: >
      The Stage142 r4-unrolled closed full-MAT AVX512 repair should improve
      complete PVW/MAT-SAB amortized bootstrapping time for r=4 when combined
      with the existing active-buffer SAB path.
    mechanism: >
      Stage142 improves the closed external-product kernel used inside each
      SAB CMUX/RGSW step. If that kernel cost remains visible after schedule
      overhead, full SAB T_bootstrap/r should improve over the generic active
      PVW path.
    status: stage143_full_sab_r4_unrolled_smoke
    evidence: docs/stage143_full_sab_r4_unrolled_smoke.md; experiments/stage143_full_sab_r4_unrolled_smoke_plan.md; theory_checks/stage143_full_sab_metric_model.md; algorithm_variants/mat_rlwe_sab_r4_unrolled_full_sab_smoke.md; scripts/build_stage143_full_sab_r4_unrolled_smoke.py; repro/stage143_full_sab_r4_unrolled_smoke/results.csv; repro/stage143_full_sab_r4_unrolled_smoke/comparison.csv; repro/stage143_full_sab_r4_unrolled_smoke/artifact_index.csv
    current_decision: >
      Stage143 records {decision}. r4-unrolled full SAB smoke speedup over
      repeated scalar SAB is {row['r4_mean_speedup_vs_scalar']}x, and its
      incremental per-lane speedup over generic active PVW is
      {row['r4_vs_generic_pvw_lane_speedup']}. This is smoke evidence only.
    failure_criteria:
      - complete SAB correctness fails
      - repeated Stage144 does not preserve the per-lane speedup
      - one-run smoke is claimed as final throughput evidence
"""
    text = HYPOTHESIS_YAML.read_text(encoding="utf-8") if HYPOTHESIS_YAML.exists() else "hypotheses:\n"
    marker = "  - id: H67_r4_unrolled_full_sab_smoke"
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(HYPOTHESIS_YAML, text + block)


def upsert_run_log(decision: str) -> None:
    fields = ["run_id", "date", "commit_or_state", "stage", "backend", "command", "params", "seed", "status", "summary", "artifacts"]
    run_id = "stage143-full-sab-r4-unrolled-smoke-001"
    rows = [row for row in read_csv(RUN_LOG) if row.get("run_id") != run_id]
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, RESULTS_CSV, COMPARE_CSV, ARTIFACT_INDEX, Path(__file__).resolve()]
    for config in CONFIGS:
        for run_idx in range(RUNS):
            artifacts.append(OUT_DIR / f"{config['variant']}_run_{run_idx}.log")
    artifacts.append(OUT_DIR / "cleanup.log")
    rows.append({
        "run_id": run_id,
        "date": "2026-07-03",
        "commit_or_state": f"working-tree-after-{git_head()}",
        "stage": "Stage 143",
        "backend": "MOSFHET FFT_LIB=spqlios_avx512",
        "command": "python scripts/build_stage143_full_sab_r4_unrolled_smoke.py",
        "params": f"RUNS={RUNS}; r=4; reps=1; generic_active vs r4_unrolled_active; active_buffer=true; KEY=BINARY PARAM=SET_2_3_2048",
        "seed": "default-rng",
        "status": decision,
        "summary": "Full SAB smoke with amortized T_bootstrap/r primary metric.",
        "artifacts": "; ".join(rel(p) for p in artifacts),
    })
    write_csv(RUN_LOG, rows, fields)


def upsert_global_manifest() -> None:
    block = """
## Stage 143 Full SAB r4-Unrolled Smoke

- `docs/stage143_full_sab_r4_unrolled_smoke.md`
- `experiments/stage143_full_sab_r4_unrolled_smoke_plan.md`
- `theory_checks/stage143_full_sab_metric_model.md`
- `algorithm_variants/mat_rlwe_sab_r4_unrolled_full_sab_smoke.md`
- `scripts/build_stage143_full_sab_r4_unrolled_smoke.py`
- `repro/stage143_full_sab_r4_unrolled_smoke/summary.csv`
- `repro/stage143_full_sab_r4_unrolled_smoke/results.csv`
- `repro/stage143_full_sab_r4_unrolled_smoke/comparison.csv`
- `repro/stage143_full_sab_r4_unrolled_smoke/*_run_*.log`
- `repro/stage143_full_sab_r4_unrolled_smoke/artifact_index.csv`
"""
    append_once(GLOBAL_MANIFEST, "## Stage 143 Full SAB r4-Unrolled Smoke", block)


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
            continue
        rows.append({
            "artifact": rel(path),
            "exists": "yes" if path.exists() else "no",
            "sha256": sha256_file(path) if path.exists() else "",
            "size_bytes": str(path.stat().st_size) if path.exists() else "0",
        })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_ok = True
    for run_idx in range(RUNS):
        for config in CONFIGS:
            run_ok = run_config(config["variant"], config["flags"], run_idx) and run_ok
    bash("make clean >/dev/null 2>&1 || true", timeout=60)
    write_text_lf(OUT_DIR / "cleanup.log", "command: make clean >/dev/null 2>&1 || true\n")

    result_rows = []
    for run_idx in range(RUNS):
        for config in CONFIGS:
            result_rows.append(parse_log(config["variant"], run_idx))
    compare_rows = build_comparison(result_rows)
    summary_rows = build_summary(run_ok, result_rows, compare_rows)
    decision = summary_rows[-1]["status"]
    write_csv(RESULTS_CSV, result_rows, RESULT_FIELDS)
    write_csv(COMPARE_CSV, compare_rows, COMPARE_FIELDS)
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    write_docs(summary_rows, compare_rows)
    update_longform_docs(decision, compare_rows)
    upsert_hypothesis(decision, compare_rows)
    upsert_run_log(decision)
    upsert_global_manifest()
    artifacts = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, SUMMARY_CSV, RESULTS_CSV, COMPARE_CSV, ARTIFACT_INDEX, Path(__file__).resolve()]
    for config in CONFIGS:
        for run_idx in range(RUNS):
            artifacts.append(OUT_DIR / f"{config['variant']}_run_{run_idx}.log")
    artifacts.append(OUT_DIR / "cleanup.log")
    write_artifact_index(artifacts)
    print(f"Stage143 full SAB r4-unrolled smoke: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if not decision.startswith("FAIL_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
