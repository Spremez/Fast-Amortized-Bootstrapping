#!/usr/bin/env python3
"""Stage331: current-head high-stat complete-SAB refresh for direct PVW/MAT-SAB."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage331_current_head_highstat_refresh"
RAW = OUT / "raw"

DOC = ROOT / "docs" / "stage331_current_head_highstat_refresh.md"
THEORY = ROOT / "theory_checks" / "stage331_current_head_highstat_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage331_current_head_highstat.md"
PLAN = ROOT / "experiments" / "stage332_compact_keygen_security_or_paper_pack_plan.md"
RUNNER = ROOT / "scripts" / "run_stage331_current_head_highstat_refresh.sh"
BUILDER = ROOT / "scripts" / "build_stage331_current_head_highstat_refresh.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE330_SUMMARY = ROOT / "repro" / "stage330_highstat_reconciliation" / "summary.csv"
RUN_GIT_HEAD = RAW / "run_git_head.txt"

PERF_SAMPLES = OUT / "perf_samples.csv"
PERF_SUMMARY = OUT / "perf_summary.csv"
NOISE_SUMMARY = OUT / "noise_summary.csv"
SUMMARY = OUT / "summary.csv"
CLAIMS = OUT / "claim_boundary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage331_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH"
DECISION_PARTIAL = "PARTIAL_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH"
DECISION_FAIL = "FAIL_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH"

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
NOISE_SUMMARY_RE = re.compile(
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
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def run_git_head() -> str:
    env_head = subprocess.os.environ.get("STAGE331_RUN_GIT_HEAD", "").strip()
    if env_head:
        return env_head
    file_head = read_text(RUN_GIT_HEAD).strip()
    return file_head or git_head()


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
    tcrit = {
        2: 12.706,
        3: 4.303,
        4: 3.182,
        5: 2.776,
        6: 2.571,
        7: 2.447,
        8: 2.365,
        9: 2.306,
        10: 2.262,
    }.get(len(vals), 1.960)
    half = tcrit * pstdev(vals) / math.sqrt(len(vals))
    return mean(vals) - half, mean(vals) + half


def parse_perf() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    perf_dir = RAW / "perf_direct_current_head"
    for outer_idx, path in enumerate(sorted(perf_dir.glob("run_*.log"))):
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "variant": "perf_direct_current_head",
                "outer_run": outer_idx,
                "inner_rep": sample.group("rep"),
                "correctness": correctness,
                "mode": sample.group("mode"),
                "r": sample.group("r"),
                "h": correct.group("h") if correct else "",
                "r_prec": correct.group("r_prec") if correct else "",
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
    statuses = {str(row.get("correctness", "")) for row in samples}
    low, high = ci95(vals)
    scalar_low, scalar_high = ci95(scalars)
    return {
        "variant": "perf_direct_current_head",
        "samples": len(vals),
        "correctness": "Pass" if vals and statuses == {"Pass"} else ",".join(sorted(statuses)) or "MISSING",
        "t_bootstrap_over_r_mean_us": f"{mean(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_stddev_us": f"{pstdev(vals):.3f}" if len(vals) > 1 else "0.000",
        "t_bootstrap_over_r_ci95_low_us": f"{low:.3f}" if vals else "",
        "t_bootstrap_over_r_ci95_high_us": f"{high:.3f}" if vals else "",
        "t_bootstrap_over_r_min_us": f"{min(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_max_us": f"{max(vals):.3f}" if vals else "",
        "scalar_t_bootstrap_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
        "scalar_t_bootstrap_over_r_ci95_low_us": f"{scalar_low:.3f}" if scalars else "",
        "scalar_t_bootstrap_over_r_ci95_high_us": f"{scalar_high:.3f}" if scalars else "",
        "speedup_vs_repeated_scalar_mean": f"{mean(scalars) / mean(vals):.6f}" if vals and scalars else "",
    }


def parse_noise() -> dict[str, object]:
    run_log = RAW / "noise_direct_current_head" / "run.log"
    time_log = RAW / "noise_direct_current_head" / "time.log"
    row: dict[str, object] = {
        "variant": "noise_direct_current_head",
        "source_run_log": rel(run_log),
        "source_time_log": rel(time_log),
    }
    match = NOISE_SUMMARY_RE.search(read_text(run_log))
    if match:
        row.update(match.groupdict())
    overall = NOISE_OVERALL_RE.search(read_text(run_log))
    if overall:
        row["overall_gate"] = overall.group("overall_gate")
    time_match = TIME_RSS_RE.search(read_text(time_log))
    if time_match:
        row.update(time_match.groupdict())
    row["status"] = (
        "pass"
        if row.get("gate") == "Pass"
        and row.get("overall_gate") == "Pass"
        and row.get("pair_failures") == "0"
        else "fail"
    )
    return row


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage331-current-head-highstat-refresh-001"
    if run_id in read_text(RUN_LOG):
        return
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as handle:
            fields = list(csv.DictReader(handle).fieldnames or [])
    else:
        fields = []
    if not fields:
        fields = [
            "run_id", "date", "commit_or_state", "stage", "backend", "command",
            "params", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "commit_or_state": git_head(),
        "git_ref": git_head(),
        "stage": "Stage 331",
        "backend": "spqlios_avx512-wsl",
        "command": "STAGE331_PERF_RUNS=10 STAGE331_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage331_current_head_highstat_refresh.sh",
        "params": "BINARY SET_2_3_2048; r=4; include-zero; current-head selected direct DFT",
        "seed": "n/a",
        "status": decision,
        "summary": "Current-head high-stat complete-SAB T_bootstrap/r plus final-output noise/RSS refresh.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(PERF_SUMMARY)}; {rel(NOISE_SUMMARY)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: list[Path]) -> None:
    rows: list[dict[str, object]] = []
    for path in paths:
        if path.exists() and path.is_file():
            data = path.read_bytes()
            rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stage330_rows = read_csv(STAGE330_SUMMARY)
    stage330_decision = stage330_rows[0].get("decision", "") if stage330_rows else ""

    samples = parse_perf()
    perf = summarize_perf(samples)
    noise = parse_noise()

    write_csv(PERF_SAMPLES, samples, [
        "variant", "outer_run", "inner_rep", "correctness", "mode", "r", "h",
        "r_prec", "pvw_us", "pvw_lane_us", "scalar_repeated_us",
        "scalar_lane_us", "speedup_vs_repeated_scalar", "source_log",
    ])
    write_csv(PERF_SUMMARY, [perf], [
        "variant", "samples", "correctness", "t_bootstrap_over_r_mean_us",
        "t_bootstrap_over_r_stddev_us", "t_bootstrap_over_r_ci95_low_us",
        "t_bootstrap_over_r_ci95_high_us", "t_bootstrap_over_r_min_us",
        "t_bootstrap_over_r_max_us", "scalar_t_bootstrap_over_r_mean_us",
        "scalar_t_bootstrap_over_r_ci95_low_us",
        "scalar_t_bootstrap_over_r_ci95_high_us",
        "speedup_vs_repeated_scalar_mean",
    ])
    write_csv(NOISE_SUMMARY, [noise], [
        "variant", "status", "mode", "r", "trials", "points",
        "expected_model_pvw_failures", "expected_model_scalar_failures",
        "pair_failures", "pair_log2_sigma_torus", "pair_log2_max_abs_torus",
        "gate", "overall_gate", "time_maxrss_kb", "source_run_log",
        "source_time_log",
    ])

    samples_n = int(perf.get("samples", 0) or 0)
    noise_trials = int(noise.get("trials", 0) or 0)
    sample_gate = samples_n >= 10
    correctness_gate = perf.get("correctness") == "Pass"
    noise_gate = noise.get("status") == "pass" and noise_trials >= 10
    rss_gate = bool(noise.get("time_maxrss_kb"))
    stage330_gate = stage330_decision.startswith("PASS_STAGE330")

    if stage330_gate and sample_gate and correctness_gate and noise_gate and rss_gate:
        decision = DECISION_PASS
    elif correctness_gate and samples_n > 0:
        decision = DECISION_PARTIAL
    else:
        decision = DECISION_FAIL

    summary_rows = [{
        "decision": decision,
        "git_head": run_git_head(),
        "primary_metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
        "samples": perf.get("samples", ""),
        "correctness": perf.get("correctness", ""),
        "t_bootstrap_over_r_mean_us": perf.get("t_bootstrap_over_r_mean_us", ""),
        "t_bootstrap_over_r_ci95_low_us": perf.get("t_bootstrap_over_r_ci95_low_us", ""),
        "t_bootstrap_over_r_ci95_high_us": perf.get("t_bootstrap_over_r_ci95_high_us", ""),
        "scalar_t_bootstrap_over_r_mean_us": perf.get("scalar_t_bootstrap_over_r_mean_us", ""),
        "speedup_vs_repeated_scalar_mean": perf.get("speedup_vs_repeated_scalar_mean", ""),
        "noise_trials": noise.get("trials", ""),
        "noise_pair_failures": noise.get("pair_failures", ""),
        "time_maxrss_kb": noise.get("time_maxrss_kb", ""),
        "claim_level": "current_head_scoped_highstat" if decision == DECISION_PASS else "not_paper_ready",
    }]

    claim_rows = [
        {
            "claim": "current_head_complete_sab_t_over_r",
            "status": "PASS" if decision == DECISION_PASS else "PARTIAL",
            "supported_statement": f"Current head direct PVW/MAT-SAB has speedup {perf.get('speedup_vs_repeated_scalar_mean', '')}x by complete SAB T_bootstrap/r for BINARY SET_2_3_2048 r=4 include-zero.",
            "not_supported": "All-parameter, compact, or theoretical-optimality claims.",
        },
        {
            "claim": "noise_resource_side_condition",
            "status": "PASS" if noise_gate and rss_gate else "PARTIAL",
            "supported_statement": f"Final-output pair failures={noise.get('pair_failures', '')}/{noise.get('trials', '')}; maxrss={noise.get('time_maxrss_kb', '')} KB.",
            "not_supported": "Full native memory profiling or security proof for compact selector variants.",
        },
        {
            "claim": "paper_grade_scope",
            "status": "PASS_SCOPED" if decision == DECISION_PASS else "NOT_READY",
            "supported_statement": "The result can be written as a scoped systems result for this parameter/backend/path if decision is PASS.",
            "not_supported": "Novelty or optimality without literature/proof closeout.",
        },
    ]

    proof_rows = [
        {
            "gate": "G1_stage330_input",
            "status": "PASS" if stage330_gate else "FAIL",
            "metric": "Stage330 decision",
            "value": stage330_decision,
            "interpretation": "Stage331 is opened by Stage330's high-stat reconciliation.",
        },
        {
            "gate": "G2_sample_count",
            "status": "PASS" if sample_gate else "PARTIAL",
            "metric": "complete-SAB samples",
            "value": str(samples_n),
            "interpretation": "Paper-grade scoped current-head table requires at least ten samples.",
        },
        {
            "gate": "G3_correctness",
            "status": "PASS" if correctness_gate else "FAIL",
            "metric": "full SAB correctness",
            "value": str(perf.get("correctness", "")),
            "interpretation": "No performance claim is allowed if correctness fails.",
        },
        {
            "gate": "G4_noise_trials",
            "status": "PASS" if noise_gate else "PARTIAL",
            "metric": "pair failures/trials",
            "value": f"{noise.get('pair_failures', '')}/{noise.get('trials', '')}",
            "interpretation": "Final-output PVW/scalar pair equivalence should pass over at least ten trials.",
        },
        {
            "gate": "G5_resource_recorded",
            "status": "PASS" if rss_gate else "PARTIAL",
            "metric": "max RSS",
            "value": str(noise.get("time_maxrss_kb", "")),
            "interpretation": "Resource side condition must be recorded with the current-head run.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls whether Stage332 may package the scoped paper result or must rerun.",
        },
    ]

    next_rows = [
        {
            "priority": "P0",
            "route": "stage332_paper_result_pack",
            "entry_condition": DECISION_PASS,
            "gate": "write scoped result table, figures, limitations, and reproducibility pack",
            "failure_action": "If Stage331 is partial/fail, do not claim paper-grade current-head performance.",
        },
        {
            "priority": "P1",
            "route": "stage332_compact_keygen_security_preflight",
            "entry_condition": "compact route is prioritized over paper packing",
            "gate": "keygen distribution and noise/security proof obligations",
            "failure_action": "Keep compact production code blocked.",
        },
    ]

    write_csv(SUMMARY, summary_rows, [
        "decision", "git_head", "primary_metric", "samples", "correctness",
        "t_bootstrap_over_r_mean_us", "t_bootstrap_over_r_ci95_low_us",
        "t_bootstrap_over_r_ci95_high_us", "scalar_t_bootstrap_over_r_mean_us",
        "speedup_vs_repeated_scalar_mean", "noise_trials",
        "noise_pair_failures", "time_maxrss_kb", "claim_level",
    ])
    write_csv(CLAIMS, claim_rows, ["claim", "status", "supported_statement", "not_supported"])
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_text(DOC, f"""# Stage331 Current-Head High-Stat Refresh

Decision: `{decision}`.

Stage331 reruns the selected direct PVW/MAT-SAB complete bootstrapping path on
the current hot-code head.  The primary endpoint is complete SAB
`T_bootstrap/r`, compared with repeated scalar SAB over the same number of
plaintext bits.

## Summary

{md_table(summary_rows, ["decision", "git_head", "samples", "correctness", "t_bootstrap_over_r_mean_us", "speedup_vs_repeated_scalar_mean", "noise_trials", "noise_pair_failures", "time_maxrss_kb", "claim_level"])}

## Performance

{md_table([perf], ["variant", "samples", "correctness", "t_bootstrap_over_r_mean_us", "t_bootstrap_over_r_ci95_low_us", "t_bootstrap_over_r_ci95_high_us", "scalar_t_bootstrap_over_r_mean_us", "speedup_vs_repeated_scalar_mean"])}

## Noise And Resource

{md_table([noise], ["variant", "status", "r", "trials", "points", "pair_failures", "pair_log2_sigma_torus", "gate", "overall_gate", "time_maxrss_kb"])}

## Claim Boundary

{md_table(claim_rows, ["claim", "status", "supported_statement", "not_supported"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value"])}

Generated from input head `{run_git_head()}`.
""")

    write_text(THEORY, """# Stage331 Current-Head High-Stat Model

Stage331 answers only one question: whether the current hot-code direct
PVW/MAT-SAB path has paper-grade local statistical evidence for complete
`T_bootstrap/r`.

The run is accepted only when:

1. the Stage330 reconciliation gate opened the current-head refresh route;
2. at least ten complete-SAB samples are parsed;
3. full SAB correctness passes for every sample;
4. final-output PVW/scalar pair equivalence has zero pair failures over at
   least ten trials;
5. resource evidence records max RSS.

This does not prove global optimality, compact-selector security, or
all-parameter generality.
""")

    write_text(VARIANT, f"""# mat_rlwe_sab_stage331_current_head_highstat

## Summary

- Parent algorithm: PVW/MAT-RLWE multi-body path for 2025/686 SAB.
- Focused module: current-head complete SAB direct-DFT implementation.
- Optimization target: complete `T_bootstrap/r`.
- Status: `{decision}`.
- Run head: `{run_git_head()}`.

## Result

Current-head selected direct PVW/MAT-SAB:

- samples: `{perf.get('samples', '')}`;
- mean `T_bootstrap/r`: `{perf.get('t_bootstrap_over_r_mean_us', '')}` us;
- repeated scalar mean per lane: `{perf.get('scalar_t_bootstrap_over_r_mean_us', '')}` us;
- speedup: `{perf.get('speedup_vs_repeated_scalar_mean', '')}x`;
- noise pair failures: `{noise.get('pair_failures', '')}/{noise.get('trials', '')}`.

## Paper Boundary

This variant supports a scoped systems claim only when the decision is
`PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH`.  It does not support theoretical
optimality or compact selector claims.
""")

    write_text(PLAN, """# Stage332 Compact Keygen/Security Or Paper Pack Plan

Route A: paper result pack.

- use Stage331 only if the decision is
  `PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH`;
- write the scoped result table using complete `T_bootstrap/r`;
- include correctness, noise, RSS, backend, commit, command, and limitations;
- keep theoretical optimality and compact-selector claims marked open.

Route B: compact keygen/security preflight.

- map compact selector equations to production key generation;
- close public distribution, semantic-zero, and noise recurrence obligations;
- do not admit SAB hot-path compact code before proof gates pass.
""")

    write_text(COMMANDS, """# Stage331 Reproduction Commands

```sh
STAGE331_PERF_RUNS=10 STAGE331_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage331_current_head_highstat_refresh.sh
```

Smoke:

```sh
STAGE331_PERF_RUNS=1 STAGE331_NOISE_TRIALS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage331_current_head_highstat_refresh.sh
```
""")

    write_text(REPORT, read_text(DOC))

    append_once(GOAL, "<!-- stage331-current-head-highstat-refresh -->", f"""
<!-- stage331-current-head-highstat-refresh -->
### Stage331 current-head high-stat refresh

`{decision}` records current-head direct PVW/MAT-SAB complete `T_bootstrap/r`
performance, final-output noise, and RSS evidence. It remains scoped to the
tested parameter/backend/path and does not prove compact security or global
optimality.
""")

    append_once(ROADMAP, "<!-- stage331-current-head-highstat-roadmap -->", f"""
<!-- stage331-current-head-highstat-roadmap -->
## Stage 331: Current-Head High-Stat Refresh

Goal: rerun the selected direct PVW/MAT-SAB path on the current hot-code head
with at least ten complete-SAB samples and refreshed noise/resource evidence.

Status: `{decision}`.
""")

    append_once(HYPOTHESES, "H331_current_head_highstat_refresh:", f"""
H331_current_head_highstat_refresh:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r_vs_repeated_scalar
  evidence:
    - repro/stage331_current_head_highstat_refresh/summary.csv
    - repro/stage331_current_head_highstat_refresh/perf_summary.csv
    - repro/stage331_current_head_highstat_refresh/noise_summary.csv
    - repro/stage331_current_head_highstat_refresh/proof_gate.csv
  conclusion: >
    Stage331 refreshes the current-head direct PVW/MAT-SAB evidence for the
    scoped complete-SAB amortized metric.
""")

    append_once(MANIFEST, "<!-- stage331-current-head-highstat-manifest -->", """
<!-- stage331-current-head-highstat-manifest -->
- stage331_current_head_highstat_refresh:
  - `docs/stage331_current_head_highstat_refresh.md`
  - `theory_checks/stage331_current_head_highstat_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage331_current_head_highstat.md`
  - `experiments/stage332_compact_keygen_security_or_paper_pack_plan.md`
  - `scripts/run_stage331_current_head_highstat_refresh.sh`
  - `scripts/build_stage331_current_head_highstat_refresh.py`
  - `repro/stage331_current_head_highstat_refresh/`
""")

    append_once(CHECKLIST, "<!-- stage331-current-head-highstat-checklist -->", f"""
<!-- stage331-current-head-highstat-checklist -->
- [x] Stage331 records `{decision}` for the current-head selected direct
  PVW/MAT-SAB complete `T_bootstrap/r` refresh.
""")

    append_run_log(decision)

    raw_artifacts = [
        RUN_GIT_HEAD,
        RAW / "perf_direct_current_head" / "clean.log",
        RAW / "perf_direct_current_head" / "build.log",
        RAW / "noise_direct_current_head" / "clean.log",
        RAW / "noise_direct_current_head" / "build.log",
        RAW / "noise_direct_current_head" / "run.log",
        RAW / "noise_direct_current_head" / "time.log",
        OUT / "full_run_driver.stdout.log",
        OUT / "full_run_driver.stderr.log",
    ]
    raw_artifacts.extend(sorted((RAW / "perf_direct_current_head").glob("run_*.log")))

    artifact_index([
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, PERF_SAMPLES, PERF_SUMMARY,
        NOISE_SUMMARY, SUMMARY, CLAIMS, PROOF, NEXT, COMMANDS, REPORT,
        *raw_artifacts,
    ])
    return 0 if decision != DECISION_FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
