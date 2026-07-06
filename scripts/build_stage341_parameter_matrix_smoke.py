#!/usr/bin/env python3
"""Stage341: parse a real current-head parameter-matrix smoke run."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("STAGE341_OUT_DIR", ROOT / "repro" / "stage341_parameter_matrix_smoke"))
if not OUT.is_absolute():
    OUT = ROOT / OUT
RAW = OUT / "raw"

DOC = ROOT / "docs" / "stage341_parameter_matrix_smoke.md"
THEORY = ROOT / "theory_checks" / "stage341_smoke_claim_boundary.md"
PLAN = ROOT / "experiments" / "stage342_full_matrix_or_literature_plan.md"
RUNNER = ROOT / "scripts" / "run_stage341_parameter_matrix_smoke.sh"
BUILDER = ROOT / "scripts" / "build_stage341_parameter_matrix_smoke.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE340_SUMMARY = ROOT / "repro" / "stage340_parameter_matrix_current_head_gate" / "summary.csv"
STAGE340_EXECUTION = ROOT / "repro" / "stage340_parameter_matrix_current_head_gate" / "execution_matrix.csv"

SUMMARY = OUT / "summary.csv"
PERF_SAMPLES = OUT / "perf_samples.csv"
PERF_SUMMARY = OUT / "perf_summary.csv"
NOISE_SUMMARY = OUT / "noise_summary.csv"
CLAIMS = OUT / "claim_boundary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage341_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE341_PARAMETER_MATRIX_SMOKE_EXECUTED_NO_MATRIX_CLAIM"
DECISION_FAIL = "FAIL_STAGE341_PARAMETER_MATRIX_SMOKE"

CORRECT_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
SAMPLE_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH sample target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) rep=(?P<rep>\d+) pvw_us=(?P<pvw_us>\d+) "
    r"pvw_lane_us=(?P<pvw_lane_us>[0-9.]+) scalar_repeated_us=(?P<scalar_us>\d+) "
    r"scalar_lane_us=(?P<scalar_lane_us>[0-9.]+) speedup=(?P<speedup>[0-9.]+)x"
)
NOISE_RE = re.compile(
    r"SAB_PVW_NONBINARY_TARGET_NOISE summary target_full mode=(?P<mode>\S+) "
    r"r=(?P<r>\d+) trials=(?P<trials>\d+) points=(?P<points>\d+) "
    r"expected_model_pvw_failures=(?P<expected_model_pvw_failures>\d+) "
    r"expected_model_scalar_failures=(?P<expected_model_scalar_failures>\d+) "
    r"pair_failures=(?P<pair_failures>\d+) "
    r"expected_model_pvw_log2_sigma_torus=(?P<expected_model_pvw_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"expected_model_scalar_log2_sigma_torus=(?P<expected_model_scalar_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_max_abs_torus=(?P<pair_log2_max_abs_torus>-?inf|-?[0-9.]+) "
    r"gate=(?P<gate>Pass|Fail)"
)
NOISE_OVERALL_RE = re.compile(r"SAB_PVW_NONBINARY_TARGET_NOISE target full final-output gate: (?P<overall_gate>Pass|Fail)")
TIME_RSS_RE = re.compile(r"Maximum resident set size \(kbytes\): (?P<time_maxrss_kb>\d+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def run_head() -> str:
    return read_text(RAW / "run_git_head.txt").strip() or git_head()


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def ci95(vals: list[float]) -> tuple[float, float]:
    if not vals:
        return 0.0, 0.0
    if len(vals) == 1:
        return vals[0], vals[0]
    tcrit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}.get(len(vals), 1.960)
    half = tcrit * pstdev(vals) / math.sqrt(len(vals))
    return mean(vals) - half, mean(vals) + half


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def parse_perf() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(RAW.glob("*_r*/perf/run_*.log")):
        case = path.parts[-3]
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "case": case,
                "mode": sample.group("mode"),
                "r": sample.group("r"),
                "h": correct.group("h") if correct else "",
                "r_prec": correct.group("r_prec") if correct else "",
                "outer_log": path.name,
                "inner_rep": sample.group("rep"),
                "correctness": correctness,
                "pvw_us": sample.group("pvw_us"),
                "pvw_lane_us": sample.group("pvw_lane_us"),
                "scalar_repeated_us": sample.group("scalar_us"),
                "scalar_lane_us": sample.group("scalar_lane_us"),
                "speedup_vs_repeated_scalar": sample.group("speedup"),
                "source_log": rel(path),
            })
    return rows


def summarize_perf(samples: list[dict[str, object]]) -> dict[str, object]:
    vals = [fnum(row.get("pvw_lane_us")) for row in samples]
    scalars = [fnum(row.get("scalar_lane_us")) for row in samples]
    speedups = [fnum(row.get("speedup_vs_repeated_scalar")) for row in samples]
    low, high = ci95(vals)
    statuses = {str(row.get("correctness", "")) for row in samples}
    return {
        "case": samples[0].get("case", "") if samples else "",
        "samples": len(samples),
        "correctness": "Pass" if samples and statuses == {"Pass"} else ",".join(sorted(statuses)) or "MISSING",
        "pvw_t_over_r_mean_us": f"{mean(vals):.3f}" if vals else "",
        "pvw_t_over_r_ci95_us": f"{low:.3f}..{high:.3f}" if vals else "",
        "scalar_t_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
        "speedup_mean": f"{mean(speedups):.6f}" if speedups else "",
    }


def parse_noise() -> dict[str, object]:
    run_logs = sorted(RAW.glob("*_r*/noise/run.log"))
    if not run_logs:
        return {"status": "missing"}
    run_log = run_logs[0]
    time_log = run_log.parent / "time.log"
    row: dict[str, object] = {"status": "fail", "source_run_log": rel(run_log), "source_time_log": rel(time_log)}
    match = NOISE_RE.search(read_text(run_log))
    if match:
        row.update(match.groupdict())
    overall = NOISE_OVERALL_RE.search(read_text(run_log))
    if overall:
        row["overall_gate"] = overall.group("overall_gate")
    rss = TIME_RSS_RE.search(read_text(time_log))
    if rss:
        row["time_maxrss_kb"] = rss.group("time_maxrss_kb")
    if row.get("gate") == "Pass" and row.get("overall_gate") == "Pass" and row.get("pair_failures") == "0":
        row["status"] = "pass"
    return row


def append_run_log(decision: str, perf: dict[str, object], noise: dict[str, object]) -> None:
    marker = "stage341-parameter-matrix-smoke-001"
    if marker in read_text(RUN_LOG):
        return
    exists = RUN_LOG.exists()
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        if not exists:
            writer.writerow(["run_id", "date", "git_head", "stage", "backend", "command", "params", "seed", "status", "interpretation", "artifacts"])
        writer.writerow([
            marker,
            "2026-07-06",
            run_head(),
            "Stage 341",
            "spqlios_avx512-wsl-smoke",
            "STAGE341_PERF_RUNS=1 STAGE341_NOISE_TRIALS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 STAGE341_R=2 bash scripts/run_stage341_parameter_matrix_smoke.sh",
            f"{perf.get('case', '')}; samples={perf.get('samples', '')}; noise_trials={noise.get('trials', '')}",
            "n/a",
            decision,
            "Executes one real missing matrix case as a smoke gate; no statistical or broader-parameter claim is promoted.",
            f"{rel(DOC)}; {rel(SUMMARY)}; {rel(PERF_SUMMARY)}; {rel(NOISE_SUMMARY)}; {rel(PROOF)}",
        ])


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def artifact_index(paths: list[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({"artifact": rel(path), "exists": path.exists(), "bytes": file_size(path), "sha256": sha256_file(path)})
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    samples = parse_perf()
    perf = summarize_perf(samples)
    noise = parse_noise()
    stage340 = read_csv(STAGE340_SUMMARY)
    correctness = perf.get("correctness") == "Pass"
    perf_ok = int(perf.get("samples", 0) or 0) >= 1
    noise_ok = noise.get("status") == "pass"
    decision = DECISION_PASS if correctness and perf_ok and noise_ok else DECISION_FAIL
    summary = [{
        "decision": decision,
        "run_head": run_head(),
        "stage340_input": stage340[0].get("decision", "") if stage340 else "",
        "case": perf.get("case", ""),
        "samples": perf.get("samples", ""),
        "correctness": perf.get("correctness", ""),
        "pvw_t_over_r_mean_us": perf.get("pvw_t_over_r_mean_us", ""),
        "scalar_t_over_r_mean_us": perf.get("scalar_t_over_r_mean_us", ""),
        "speedup_mean": perf.get("speedup_mean", ""),
        "noise_trials": noise.get("trials", ""),
        "noise_pair_failures": noise.get("pair_failures", ""),
        "time_maxrss_kb": noise.get("time_maxrss_kb", ""),
        "claim_status": "smoke_only_no_statistical_claim",
    }]
    claim_rows = [
        {
            "claim": "harness_real_execution",
            "status": "PASS" if decision == DECISION_PASS else "FAIL",
            "supported": "One current-head missing matrix case can build, run, and parse.",
            "not_supported": "High-stat performance, full parameter matrix, or broader parameter generality.",
        },
        {
            "claim": "single_run_speedup",
            "status": "SMOKE_ONLY",
            "supported": f"Single smoke speedup field parsed as {perf.get('speedup_mean', '')}.",
            "not_supported": "Paper-grade timing or stable throughput claim.",
        },
    ]
    proof_rows = [
        {
            "gate": "G1_stage340_input",
            "status": "PASS" if stage340 else "MISSING",
            "metric": "Stage340 decision",
            "value": stage340[0].get("decision", "") if stage340 else "",
            "interpretation": "Stage341 follows the executable matrix route.",
        },
        {
            "gate": "G2_perf_smoke",
            "status": "PASS" if correctness and perf_ok else "FAIL",
            "metric": "perf samples/correctness",
            "value": f"{perf.get('samples', '')}/{perf.get('correctness', '')}",
            "interpretation": "Smoke requires at least one parsed complete-SAB sample with correctness Pass.",
        },
        {
            "gate": "G3_noise_smoke",
            "status": "PASS" if noise_ok else "FAIL",
            "metric": "pair failures/trials",
            "value": f"{noise.get('pair_failures', '')}/{noise.get('trials', '')}",
            "interpretation": "Smoke requires final-output pair equivalence for the trial.",
        },
        {
            "gate": "G4_claim_boundary",
            "status": "PASS",
            "metric": "claim level",
            "value": "smoke_only",
            "interpretation": "Do not promote a full matrix or statistical performance claim.",
        },
        {
            "gate": "G5_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls whether Stage342 should run the full matrix or switch route.",
        },
    ]
    next_rows = [
        {
            "priority": "P0",
            "route": "stage342_full_current_head_matrix",
            "entry_condition": DECISION_PASS,
            "command": "STAGE340_EXECUTE=1 STAGE340_PERF_RUNS=10 STAGE340_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage340_parameter_matrix_current_head.sh",
            "gate": "all intended cases pass high-stat complete SAB T_bootstrap/r and noise/RSS",
            "failure_action": "Keep Stage339 scoped claim.",
        },
        {
            "priority": "P1",
            "route": "stage342_literature_or_new_mechanism",
            "entry_condition": "full matrix is not being executed now",
            "command": "verified source audit or mechanism/proof preflight",
            "gate": "source-checked novelty or isolated mechanism/proof gates",
            "failure_action": "No novelty or new algorithm claim.",
        },
    ]
    write_csv(SUMMARY, summary, ["decision", "run_head", "stage340_input", "case", "samples", "correctness", "pvw_t_over_r_mean_us", "scalar_t_over_r_mean_us", "speedup_mean", "noise_trials", "noise_pair_failures", "time_maxrss_kb", "claim_status"])
    write_csv(PERF_SAMPLES, samples, ["case", "mode", "r", "h", "r_prec", "outer_log", "inner_rep", "correctness", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_repeated_scalar", "source_log"])
    write_csv(PERF_SUMMARY, [perf], ["case", "samples", "correctness", "pvw_t_over_r_mean_us", "pvw_t_over_r_ci95_us", "scalar_t_over_r_mean_us", "speedup_mean"])
    write_csv(NOISE_SUMMARY, [noise], ["status", "mode", "r", "trials", "points", "pair_failures", "pair_log2_sigma_torus", "pair_log2_max_abs_torus", "gate", "overall_gate", "time_maxrss_kb", "source_run_log", "source_time_log"])
    write_csv(CLAIMS, claim_rows, ["claim", "status", "supported", "not_supported"])
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "command", "gate", "failure_action"])
    write_text(COMMANDS, """# Stage341 Reproduction Commands

```sh
STAGE341_PERF_RUNS=1 STAGE341_NOISE_TRIALS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 STAGE341_R=2 bash scripts/run_stage341_parameter_matrix_smoke.sh
```
""")
    write_text(REPORT, f"""# Stage341 Parameter Matrix Smoke

Decision: `{decision}`.

Stage341 executes one real current-head missing matrix case as a smoke gate. It
does not provide statistical performance evidence and does not broaden the
Stage339 scoped claim.

## Summary

{md_table(summary, ["decision", "run_head", "case", "samples", "correctness", "pvw_t_over_r_mean_us", "scalar_t_over_r_mean_us", "speedup_mean", "noise_trials", "noise_pair_failures", "claim_status"])}

## Claim Boundary

{md_table(claim_rows, ["claim", "status", "supported", "not_supported"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value"])}
""")
    write_text(DOC, f"""# Stage341 Parameter Matrix Smoke

Decision: `{decision}`.

This stage verifies that the Stage340 execution path can run a real missing
current-head case. It remains a smoke gate: one sample and one noise trial are
not sufficient for a paper-grade or broader-parameter claim.

{md_table(summary, ["case", "samples", "correctness", "speedup_mean", "noise_trials", "noise_pair_failures", "claim_status"])}
""")
    write_text(THEORY, """# Stage341 Smoke Claim Boundary

Stage341 is an execution-chain check. It verifies build/run/parse behavior for
one missing current-head matrix case. It deliberately does not change the
primary endpoint, the baseline, or the paper claim level.

A single sample can catch build, flag, parser, and final-output equivalence
problems. It cannot estimate stable throughput, confidence intervals, memory
scaling, or parameter generality.
""")
    write_text(PLAN, """# Stage342 Full Matrix Or Literature Plan

If Stage341 passes and broader parameter wording is still desired, run the full
Stage340 matrix with `STAGE340_EXECUTE=1`, 10 performance runs, and 10 noise
trials per case.

If full matrix execution is deferred, the next useful route is verified
literature/novelty checking or a new mechanism/formal proof preflight. Do not
write stronger claims from the Stage341 smoke alone.
""")
    append_once(GOAL, "<!-- stage341-parameter-matrix-smoke -->", f"""
<!-- stage341-parameter-matrix-smoke -->
- Stage341: `{decision}`. Executed one real current-head parameter-matrix smoke case; result is smoke-only and does not promote broader parameter claims.
""")
    append_once(ROADMAP, "<!-- stage341-parameter-matrix-smoke -->", f"""
<!-- stage341-parameter-matrix-smoke -->
## Stage341: Parameter Matrix Smoke

- Decision: `{decision}`.
- Result: real build/run/parse smoke for one missing current-head case.
- Boundary: no statistical or broader parameter claim.
""")
    append_once(HYPOTHESES, "H341_parameter_matrix_smoke:", f"""
H341_parameter_matrix_smoke:
  status: {decision}
  primary_metric: smoke_complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage341_parameter_matrix_smoke/summary.csv
    - repro/stage341_parameter_matrix_smoke/perf_summary.csv
    - repro/stage341_parameter_matrix_smoke/noise_summary.csv
    - repro/stage341_parameter_matrix_smoke/proof_gate.csv
  conclusion: >
    One current-head missing matrix case executed and parsed as a smoke gate.
    This is not a high-stat matrix or broader parameter result.
""")
    append_once(MANIFEST, "<!-- stage341-parameter-matrix-smoke-manifest -->", """
<!-- stage341-parameter-matrix-smoke-manifest -->
- stage341_parameter_matrix_smoke:
  - `docs/stage341_parameter_matrix_smoke.md`
  - `theory_checks/stage341_smoke_claim_boundary.md`
  - `experiments/stage342_full_matrix_or_literature_plan.md`
  - `scripts/run_stage341_parameter_matrix_smoke.sh`
  - `scripts/build_stage341_parameter_matrix_smoke.py`
  - `repro/stage341_parameter_matrix_smoke/`
""")
    append_once(CHECKLIST, "<!-- stage341-parameter-matrix-smoke-checklist -->", f"""
<!-- stage341-parameter-matrix-smoke-checklist -->
- [x] Stage341 records `{decision}` as a real execution smoke with no broader claim promotion.
""")
    append_run_log(decision, perf, noise)
    raw_paths = [
        RAW / "run_git_head.txt",
        *sorted(RAW.glob("*_r*/perf/*.log")),
        *sorted(RAW.glob("*_r*/noise/*.log")),
        OUT / "execution_plan.csv",
    ]
    artifact_index([DOC, THEORY, PLAN, RUNNER, BUILDER, SUMMARY, PERF_SAMPLES, PERF_SUMMARY, NOISE_SUMMARY, CLAIMS, PROOF, NEXT, REPORT, COMMANDS, *raw_paths])
    return 0 if decision == DECISION_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
