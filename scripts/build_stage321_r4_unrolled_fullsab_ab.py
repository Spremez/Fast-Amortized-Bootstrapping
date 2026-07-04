#!/usr/bin/env python3
"""Build Stage321 full-SAB A/B artifacts for r4-unrolled on direct baseline."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage321_r4_unrolled_fullsab_ab.md"
THEORY = ROOT / "theory_checks" / "stage321_r4_unrolled_direct_fullsab_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage321_r4_unrolled_direct_fullsab.md"
PLAN = ROOT / "experiments" / "stage321_r4_unrolled_fullsab_ab_plan.md"
RUNNER = ROOT / "scripts" / "run_stage321_r4_unrolled_fullsab_ab.sh"
BUILDER = ROOT / "scripts" / "build_stage321_r4_unrolled_fullsab_ab.py"

PERF_SAMPLES = OUT / "perf_samples.csv"
PERF_SUMMARY = OUT / "perf_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage321_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_PASS = "PASS_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED"
DECISION_WEAK = "WEAK_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_POSITIVE_STATS_REVIEW"
DECISION_NEUTRAL = "NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_CORRECTNESS_OR_SAMPLES"

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


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if current and not current.endswith("\n"):
            f.write("\n")
        f.write(text.lstrip())
        if not text.endswith("\n"):
            f.write("\n")


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def ci95(vals: List[float]) -> tuple[float, float]:
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


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def parse_variant(variant: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for outer_idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "variant": variant,
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


def summarize(variant: str, samples: List[Dict[str, object]]) -> Dict[str, object]:
    vals = [fnum(row.get("pvw_lane_us")) for row in samples if row.get("variant") == variant]
    scalars = [fnum(row.get("scalar_lane_us")) for row in samples if row.get("variant") == variant]
    statuses = {str(row.get("correctness", "")) for row in samples if row.get("variant") == variant}
    low, high = ci95(vals)
    return {
        "variant": variant,
        "samples": len(vals),
        "correctness": "Pass" if vals and statuses == {"Pass"} else ",".join(sorted(statuses)) or "MISSING",
        "t_bootstrap_over_r_mean_us": f"{mean(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_stddev_us": f"{pstdev(vals):.3f}" if len(vals) > 1 else "0.000",
        "t_bootstrap_over_r_ci95_low_us": f"{low:.3f}" if vals else "",
        "t_bootstrap_over_r_ci95_high_us": f"{high:.3f}" if vals else "",
        "t_bootstrap_over_r_min_us": f"{min(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_max_us": f"{max(vals):.3f}" if vals else "",
        "scalar_t_bootstrap_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
        "speedup_vs_repeated_scalar_mean": f"{mean(scalars) / mean(vals):.6f}" if vals and scalars else "",
    }


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage321-r4-unrolled-fullsab-ab-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = [
            "run_id", "date", "git_ref", "stage", "backend", "command",
            "config", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 321",
        "backend": "spqlios_avx512-local-wsl",
        "command": "STAGE321_RUNS=5 STAGE321_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage321_r4_unrolled_fullsab_ab.sh",
        "config": "direct baseline vs direct+r4-unrolled complete-SAB T_bootstrap/r A/B",
        "params": "BINARY SET_2_3_2048; r=4; include-zero; direct DFT selected baseline",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage321 refreshes r4-unrolled MAT EP under the current direct PVW/MAT-SAB path.",
        "artifacts": f"{rel(DOC)}; {rel(PERF_SUMMARY)}; {rel(PROOF)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": str(len(data)), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    samples = parse_variant("direct_baseline") + parse_variant("r4_unrolled_direct")
    write_csv(PERF_SAMPLES, samples, [
        "variant", "outer_run", "inner_rep", "correctness", "mode", "r",
        "h", "r_prec", "pvw_us", "pvw_lane_us", "scalar_repeated_us",
        "scalar_lane_us", "speedup_vs_repeated_scalar", "source_log",
    ])

    baseline = summarize("direct_baseline", samples)
    candidate = summarize("r4_unrolled_direct", samples)
    bmean = fnum(baseline.get("t_bootstrap_over_r_mean_us"))
    cmean = fnum(candidate.get("t_bootstrap_over_r_mean_us"))
    r4_speedup = bmean / cmean if bmean and cmean else 0.0
    conservative = fnum(baseline.get("t_bootstrap_over_r_min_us")) / fnum(candidate.get("t_bootstrap_over_r_max_us")) if fnum(candidate.get("t_bootstrap_over_r_max_us")) else 0.0
    ci_separated = fnum(candidate.get("t_bootstrap_over_r_ci95_high_us")) < fnum(baseline.get("t_bootstrap_over_r_ci95_low_us"))
    correctness_ok = baseline.get("correctness") == "Pass" and candidate.get("correctness") == "Pass"
    enough_samples = int(baseline.get("samples", 0)) >= 5 and int(candidate.get("samples", 0)) >= 5
    if not correctness_ok or not enough_samples:
        decision = DECISION_FAIL
    elif r4_speedup >= 1.02 and ci_separated:
        decision = DECISION_PASS
    elif r4_speedup > 1.0:
        decision = DECISION_WEAK
    else:
        decision = DECISION_NEUTRAL

    comparison = {
        "variant": "comparison",
        "samples": min(int(baseline.get("samples", 0)), int(candidate.get("samples", 0))),
        "correctness": "Pass" if correctness_ok else "FAIL",
        "r4_unrolled_vs_direct_baseline_mean": f"{r4_speedup:.6f}",
        "r4_unrolled_ci_separated_from_direct": str(ci_separated).lower(),
        "conservative_direct_min_over_r4_max": f"{conservative:.6f}",
        "decision": decision,
    }
    summary_rows = [baseline, candidate, comparison]
    write_csv(PERF_SUMMARY, summary_rows, [
        "variant", "samples", "correctness", "t_bootstrap_over_r_mean_us",
        "t_bootstrap_over_r_stddev_us", "t_bootstrap_over_r_ci95_low_us",
        "t_bootstrap_over_r_ci95_high_us", "t_bootstrap_over_r_min_us",
        "t_bootstrap_over_r_max_us", "scalar_t_bootstrap_over_r_mean_us",
        "speedup_vs_repeated_scalar_mean",
        "r4_unrolled_vs_direct_baseline_mean",
        "r4_unrolled_ci_separated_from_direct",
        "conservative_direct_min_over_r4_max", "decision",
    ])

    stage320_ok = "PASS_STAGE320_RETURN_TO_MAT_EP_SELECT_R4_UNROLLED_REFRESH" in read_text(
        ROOT / "repro" / "stage320_sab_budget_return" / "stage320_summary.csv"
    )
    proof_rows = [
        {"gate": "G1_stage320_input", "status": "PASS" if stage320_ok else "FAIL", "metric": "Stage320 decision", "value": "r4_unrolled_refresh" if stage320_ok else "missing", "interpretation": "Stage321 must be opened by the Stage320 SAB budget return gate."},
        {"gate": "G2_metric_boundary", "status": "PASS", "metric": "primary endpoint", "value": "complete SAB T_bootstrap/r", "interpretation": "This compares amortized r-body MAT/PVW bootstrapping, not isolated MAT external product."},
        {"gate": "G3_correctness", "status": "PASS" if correctness_ok else "FAIL", "metric": "both variants", "value": f"{baseline.get('correctness')}/{candidate.get('correctness')}", "interpretation": "No timing claim is made if full SAB correctness fails."},
        {"gate": "G4_sample_count", "status": "PASS" if enough_samples else "FAIL", "metric": "samples", "value": str(comparison["samples"]), "interpretation": "Stage321 requires at least five samples per variant before routing."},
        {"gate": "G5_fullsab_effect", "status": "PASS" if r4_speedup >= 1.02 and ci_separated else ("WEAK" if r4_speedup > 1.0 else "NEUTRAL"), "metric": "direct/r4 mean T/r", "value": f"{r4_speedup:.6f}", "interpretation": "Measures the marginal effect of adding r4-unrolled MAT EP to the current direct baseline."},
        {"gate": "G6_scalar_anchor", "status": "PASS" if candidate.get("speedup_vs_repeated_scalar_mean") else "FAIL", "metric": "candidate vs repeated scalar T/r", "value": str(candidate.get("speedup_vs_repeated_scalar_mean", "")), "interpretation": "Records the algorithm-level amortized comparison against repeated scalar SAB."},
        {"gate": "G7_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Positive result opens noise/resource; neutral closes r4-unrolled under current direct baseline."},
    ]
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])

    if decision in {DECISION_PASS, DECISION_WEAK}:
        next_route = "stage322_r4_unrolled_direct_noise_resource_or_highstat"
        next_gate = "Run direct+r4-unrolled noise/resource and, if weak, increase repeated samples before promotion."
    else:
        next_route = "stage322_schedule_attribution_after_r4_unrolled_neutral"
        next_gate = "Close r4-unrolled current-head refresh and return to SAB schedule/profile attribution."
    write_csv(NEXT, [{
        "priority": "P0",
        "route": next_route,
        "entry_condition": decision,
        "gate": next_gate,
        "failure_action": "Do not claim r4-unrolled as a complete-SAB improvement without passing this gate.",
    }], ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_text(COMMANDS, """# Stage321 Reproduction Commands

```bash
STAGE321_RUNS=5 STAGE321_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage321_r4_unrolled_fullsab_ab.sh
```

Primary endpoint: complete SAB `T_bootstrap/r` for r-body MAT-RLWE/PVW output.
""")

    report = f"""# Stage321 r4-Unrolled Direct Full-SAB A/B

Decision: `{decision}`.

Stage321 refreshes the old r=4 unrolled MAT EP candidate under the current
direct PVW/MAT-SAB baseline.  The control includes the selected direct DFT,
backend-from-DFT-add, sub-decomp fusion, dual-sub CMUX, and include-zero fast
paths.  The candidate changes only one flag:
`MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`.

## Performance Summary

{table(summary_rows, ["variant", "samples", "correctness", "t_bootstrap_over_r_mean_us", "t_bootstrap_over_r_ci95_low_us", "t_bootstrap_over_r_ci95_high_us", "speedup_vs_repeated_scalar_mean", "r4_unrolled_vs_direct_baseline_mean", "decision"])}

## Proof Gate

{table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

## Interpretation

`speedup_vs_repeated_scalar_mean` is the algorithm-level amortized comparison.
`r4_unrolled_vs_direct_baseline_mean` is only the incremental value of adding
r4-unrolled MAT EP to the current selected direct path.

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)

    write_text(THEORY, """# Stage321 r4-Unrolled Direct Full-SAB Model

The current selected PVW/MAT-SAB baseline already uses direct
sub-decompose-to-DFT materialization and related schedule/materialization
flags. Stage321 tests only whether r=4 row-unrolled MAT external product still
reduces complete bootstrapping time after those later changes.

```text
control   = direct PVW/MAT-SAB
candidate = direct PVW/MAT-SAB + MAT_TRGSW_AVX512_R4_UNROLLED_ROWS
metric    = T_bootstrap(PVW/MAT-SAB, r=4) / 4
```

The r4-unrolled flag changes the MAT external-product implementation, not the
SAB schedule, selector distribution, ciphertext semantics, or scalar baseline.
Therefore any promotion must be supported by complete-SAB T/r evidence and
then by noise/resource side conditions.
""")
    write_text(VARIANT, """# Stage321 r4-Unrolled Direct Full-SAB Variant

Additional flag:

```text
MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true
```

Inherited selected direct baseline flags:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
SAB_PVW_BACKEND_FROM_DFT_ADD=true
SAB_PVW_SUB_DECOMP_FUSION=true
SAB_PVW_DUAL_SUB_CMUX=true
SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
```

Default status: off. Scalar `sab_rlwe_bootstrap` and the selected direct
PVW/MAT-SAB control remain available as references.
""")
    write_text(PLAN, f"""# Stage321 r=4 Unrolled Full-SAB A/B Plan

Input decision: `PASS_STAGE320_RETURN_TO_MAT_EP_SELECT_R4_UNROLLED_REFRESH`.

## Comparison

- control: current selected direct PVW/MAT-SAB path;
- candidate: control plus `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`;
- endpoint: complete SAB `T_bootstrap/r`;
- parameter: `BINARY SET_2_3_2048`, include-zero mode, r=4.

## Gate

- correctness must pass for both variants;
- at least five local samples per variant;
- promote only if mean speedup is at least 1.02x and the candidate high CI is
  below the control low CI;
- weak-positive results require more statistics before noise/resource;
- neutral results close this r4-unrolled refresh and return to SAB schedule
  attribution.

Current decision: `{decision}`.
""")

    append_once(GOAL, "<!-- stage321-r4-unrolled-fullsab-ab -->", f"""<!-- stage321-r4-unrolled-fullsab-ab -->
### Stage321 r4-unrolled direct full-SAB A/B

`{decision}` refreshes `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true` under the
current direct PVW/MAT-SAB baseline using complete `T_bootstrap/r`.
""")
    append_once(ROADMAP, "## Stage 321: r4-Unrolled Direct Full-SAB A/B", f"""## Stage 321: r4-Unrolled Direct Full-SAB A/B

Goal: test the old r=4 unrolled MAT EP candidate under the current selected
direct PVW/MAT-SAB baseline.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H321_r4_unrolled_direct_fullsab_ab:", f"""H321_r4_unrolled_direct_fullsab_ab:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage321_r4_unrolled_fullsab_ab/perf_summary.csv
    - repro/stage321_r4_unrolled_fullsab_ab/proof_gate.csv
    - docs/stage321_r4_unrolled_fullsab_ab.md
  conclusion: >
    Stage321 evaluates whether r4-unrolled MAT EP still improves complete
    SAB after the direct baseline changes. Algorithm-level speedup is reported
    as T_bootstrap/r versus repeated scalar; r4/direct is only an incremental
    implementation gate.
""")
    append_once(MANIFEST, "- stage321_r4_unrolled_fullsab_ab:", """- stage321_r4_unrolled_fullsab_ab:
  - `docs/stage321_r4_unrolled_fullsab_ab.md`
  - `scripts/run_stage321_r4_unrolled_fullsab_ab.sh`
  - `scripts/build_stage321_r4_unrolled_fullsab_ab.py`
  - `repro/stage321_r4_unrolled_fullsab_ab/`
""")
    append_once(CHECKLIST, "<!-- stage321-r4-unrolled-fullsab-ab-checklist -->", f"""<!-- stage321-r4-unrolled-fullsab-ab-checklist -->
- [x] Stage321 records `{decision}` for r4-unrolled MAT EP under current direct complete SAB `T_bootstrap/r`.
""")
    append_run_log(decision)

    paths = [
        DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, PERF_SAMPLES,
        PERF_SUMMARY, PROOF, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER,
    ]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)
    return 0 if decision != DECISION_FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
