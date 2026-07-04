#!/usr/bin/env python3
"""Build Stage309 r=4 digit row-batch microbench artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage309_digit_rowbatch_microbench"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage309_digit_rowbatch_microbench.md"
THEORY = ROOT / "theory_checks" / "stage309_digit_rowbatch_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage309_digit_rowbatch.md"
PLAN = ROOT / "experiments" / "stage309_digit_rowbatch_microbench_plan.md"
RUNNER = ROOT / "scripts" / "run_stage309_digit_rowbatch_microbench.sh"
BUILDER = ROOT / "scripts" / "build_stage309_digit_rowbatch_microbench.py"

RUN_METRICS = OUT / "run_metrics.csv"
SUMMARY = OUT / "bench_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage309_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_POSITIVE = "PASS_STAGE309_DIGIT_ROWBATCH_MICRO_POSITIVE_FULLSAB_REQUIRED"
DECISION_NEUTRAL = "NEUTRAL_STAGE309_DIGIT_ROWBATCH_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE309_DIGIT_ROWBATCH_CORRECTNESS"

CORRECT_RE = re.compile(
    r"MAT_SUB_DFT correctness r=(?P<r>\d+) N=(?P<N>\d+) "
    r"max_abs_diff=(?P<max_abs_diff>\S+) status=(?P<status>\w+)"
)
BENCH_RE = re.compile(
    r"MAT_SUB_DFT bench r=(?P<r>\d+) N=(?P<N>\d+) reps=(?P<reps>\d+) "
    r"separate_avg_us=(?P<separate>\S+) sub_avg_us=(?P<sub>\S+) "
    r"speedup_vs_separate=(?P<speedup>\S+)x checksum=(?P<checksum>\S+)"
)
DIRECT_RE = re.compile(r"MAT_TRGSW_DIRECT_DFT_PROFILE sample (?P<direct>.+)")
KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


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


def fmt(value: float) -> str:
    return f"{value:.6f}"


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def parse_log(path: Path, variant: str, run_idx: int) -> Dict[str, object]:
    text = read_text(path)
    correct = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    direct_matches = list(DIRECT_RE.finditer(text))
    direct = dict(KV_RE.findall(direct_matches[-1].group("direct"))) if direct_matches else {}
    if correct is None or bench is None or not direct:
        return {"variant": variant, "run": run_idx, "status": "MISSING_OUTPUT", "source_log": rel(path)}
    return {
        "variant": variant,
        "run": run_idx,
        "status": correct.group("status"),
        "r": correct.group("r"),
        "N": correct.group("N"),
        "reps": bench.group("reps"),
        "max_abs_diff": correct.group("max_abs_diff"),
        "sub_avg_us": bench.group("sub"),
        "speedup_vs_separate": bench.group("speedup"),
        "checksum": bench.group("checksum"),
        "profile_calls": direct.get("calls", ""),
        "profile_rows_sum": direct.get("rows_sum", ""),
        "digit_us": direct.get("digit_us", ""),
        "ifft_us": direct.get("ifft_us", ""),
        "profile_total_us": direct.get("total_us", ""),
        "digit_avg_us_per_call": f"{fnum(direct.get('digit_us')) / fnum(direct.get('calls')):.6f}" if fnum(direct.get("calls")) else "",
        "ifft_avg_us_per_call": f"{fnum(direct.get('ifft_us')) / fnum(direct.get('calls')):.6f}" if fnum(direct.get("calls")) else "",
        "source_log": rel(path),
    }


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def paired_speedups(base_values: List[float], cand_values: List[float]) -> List[float]:
    return [
        base_values[idx] / cand_values[idx]
        for idx in range(min(len(base_values), len(cand_values)))
        if cand_values[idx] > 0.0
    ]


def append_run_log(decision: str) -> None:
    run_id = "stage309-digit-rowbatch-microbench-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: List[str] = []
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
    if not fields:
        fields = ["run_id", "date", "git_ref", "stage", "backend", "command", "config", "seed", "status", "summary", "artifacts"]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "git_ref": git_head(),
        "commit_or_state": git_head(),
        "stage": "Stage 309",
        "backend": "spqlios_avx512-local",
        "command": "STAGE309_RUNS=5 STAGE309_REPS=5000 FFT_LIB=spqlios_avx512 bash scripts/run_stage309_digit_rowbatch_microbench.sh",
        "config": "r=4,N=2048 direct baseline vs row-batched digit materialization microbench",
        "params": "BINARY SET_2_3 microbench; r=4; N=2048",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage309 tests opt-in r=4 row-batched digit materialization before any full-SAB promotion.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(PROOF)}",
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    run_rows: List[Dict[str, object]] = []
    for variant in ["direct_baseline", "rowbatch_digit"]:
        for idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
            run_rows.append(parse_log(path, variant, idx))
    fields = [
        "variant", "run", "status", "r", "N", "reps", "max_abs_diff",
        "sub_avg_us", "speedup_vs_separate", "checksum", "profile_calls",
        "profile_rows_sum", "digit_us", "ifft_us", "profile_total_us",
        "digit_avg_us_per_call", "ifft_avg_us_per_call", "source_log",
    ]
    write_csv(RUN_METRICS, run_rows, fields)

    baseline = [row for row in run_rows if row.get("variant") == "direct_baseline" and row.get("status") == "Pass"]
    candidate = [row for row in run_rows if row.get("variant") == "rowbatch_digit" and row.get("status") == "Pass"]
    all_correct = len(baseline) > 0 and len(baseline) == len(candidate)
    base_digit = [fnum(row.get("digit_us")) for row in baseline]
    cand_digit = [fnum(row.get("digit_us")) for row in candidate]
    base_sub = [fnum(row.get("sub_avg_us")) for row in baseline]
    cand_sub = [fnum(row.get("sub_avg_us")) for row in candidate]
    base_total = [fnum(row.get("profile_total_us")) for row in baseline]
    cand_total = [fnum(row.get("profile_total_us")) for row in candidate]
    digit_speedups = paired_speedups(base_digit, cand_digit)
    sub_speedups = paired_speedups(base_sub, cand_sub)
    total_speedups = paired_speedups(base_total, cand_total)
    digit_min = min(digit_speedups) if digit_speedups else 0.0
    sub_min = min(sub_speedups) if sub_speedups else 0.0
    total_min = min(total_speedups) if total_speedups else 0.0

    decision = DECISION_FAIL
    if all_correct and digit_min >= 1.02 and sub_min >= 1.01:
        decision = DECISION_POSITIVE
    elif all_correct:
        decision = DECISION_NEUTRAL

    summary_rows = [{
        "decision": decision,
        "runs_per_variant": len(baseline),
        "correctness": "PASS" if all_correct else "FAIL",
        "baseline_digit_us_mean": fmt(mean(base_digit)) if base_digit else "0.000000",
        "rowbatch_digit_us_mean": fmt(mean(cand_digit)) if cand_digit else "0.000000",
        "digit_speedup_mean": fmt(mean(digit_speedups)) if digit_speedups else "0.000000",
        "digit_speedup_min": fmt(digit_min),
        "baseline_sub_avg_us_mean": fmt(mean(base_sub)) if base_sub else "0.000000",
        "rowbatch_sub_avg_us_mean": fmt(mean(cand_sub)) if cand_sub else "0.000000",
        "sub_speedup_mean": fmt(mean(sub_speedups)) if sub_speedups else "0.000000",
        "sub_speedup_min": fmt(sub_min),
        "profile_total_speedup_mean": fmt(mean(total_speedups)) if total_speedups else "0.000000",
        "profile_total_speedup_min": fmt(total_min),
        "claim": "microbench_only_full_sab_required",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "runs_per_variant", "correctness",
        "baseline_digit_us_mean", "rowbatch_digit_us_mean",
        "digit_speedup_mean", "digit_speedup_min",
        "baseline_sub_avg_us_mean", "rowbatch_sub_avg_us_mean",
        "sub_speedup_mean", "sub_speedup_min",
        "profile_total_speedup_mean", "profile_total_speedup_min", "claim",
    ])

    proof = [
        {"gate": "G1_runs", "status": "PASS" if len(baseline) == len(candidate) and len(baseline) > 0 else "FAIL", "metric": "paired runs", "value": f"{len(baseline)}/{len(candidate)}", "interpretation": "Both variants need paired repeated runs."},
        {"gate": "G2_correctness", "status": "PASS" if all_correct else "FAIL", "metric": "MAT_SUB_DFT correctness", "value": "PASS" if all_correct else "FAIL", "interpretation": "Row-batched digit materialization must preserve MAT sub-DTF output."},
        {"gate": "G3_digit_component", "status": "PASS" if digit_min >= 1.02 else "NO_PROMOTION", "metric": "paired min digit speedup", "value": fmt(digit_min), "interpretation": "Digit component must improve before full-SAB A/B is justified."},
        {"gate": "G4_sub_latency", "status": "PASS" if sub_min >= 1.01 else "NO_PROMOTION", "metric": "paired min sub-DTF speedup", "value": fmt(sub_min), "interpretation": "Component gain must survive the sub-DTF microbench surface."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "scope", "value": "microbench only", "interpretation": "Stage309 is not a complete-SAB speed claim."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls whether a full-SAB A/B is opened."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    next_task = "Run complete-SAB T_bootstrap/r A/B with rowbatch digit flag enabled." if decision == DECISION_POSITIVE else "Do not promote rowbatch digit; keep direct-DFT path and move to backend IFFT or alternate digit design."
    write_csv(NEXT, [{
        "priority": "P0",
        "stage": "stage310_digit_rowbatch_full_sab_ab" if decision == DECISION_POSITIVE else "stage310_spqlios_batched_ifft_design_or_alt_digit",
        "input": decision,
        "task": next_task,
        "gate": "same-backend full-SAB correctness/performance if positive; otherwise backend/alternate design audit",
    }], ["priority", "stage", "input", "task", "gate"])

    report = (
        "# Stage309 Digit Rowbatch Microbench\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage309 tests an opt-in r=4/k=1/l=1 direct DFT variant that materializes all five digit rows in one coefficient-block loop before running the same per-row SPQLIOS `ifft` calls.\n\n"
        "## Summary\n\n" + table(summary_rows, [
            "decision", "runs_per_variant", "correctness",
            "digit_speedup_mean", "digit_speedup_min",
            "sub_speedup_mean", "sub_speedup_min",
        ]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage309 Digit Rowbatch Model

For k=1, l=1, r=4, direct sub-DTF materializes five gadget rows: the shared
mask row and four body rows. The baseline direct path processes one row at a
time as digit-to-double followed by `ifft`.

The Stage309 candidate computes the five digit rows inside one coefficient
block loop, hoisting common gadget constants and reducing loop/control overhead.
It then calls the same single-row SPQLIOS `ifft` for each row. This does not
change the external-product algebra, selector layout, or scalar SAB path.

The candidate is promoted only if digit_us and sub-DTF microbench latency both
improve; otherwise it remains a negative/neutral ablation.
""")
    write_text(VARIANT, f"""# Stage309 MAT_TRGSW_DIRECT_DFT_R4_ROWBATCH_DIGIT

Flag: `MAT_TRGSW_DIRECT_DFT_R4_ROWBATCH_DIGIT=true`.

Decision: `{decision}`.

This default-off candidate applies only to k=1, l=1, r=4 direct sub-DTF calls.
All other shapes fall back to the existing direct path.
""")
    write_text(PLAN, """# Stage309 Experiment Plan

1. Build direct baseline and rowbatch-digit variants with direct DFT profile.
2. Run paired MAT_SUB_DFT microbench repetitions.
3. Require correctness for every run.
4. Promote only if digit_us and sub-DTF latency improve in every paired run.
5. If neutral, keep the current direct-DFT implementation unchanged.
""")
    write_text(COMMANDS, """# Stage309 Reproduction Commands

```bash
STAGE309_RUNS=5 STAGE309_REPS=5000 FFT_LIB=spqlios_avx512 \\
  bash scripts/run_stage309_digit_rowbatch_microbench.sh
python3 scripts/build_stage309_digit_rowbatch_microbench.py
```
""")

    append_once(ROADMAP, "## Stage 309: Digit Rowbatch Microbench", "\n## Stage 309: Digit Rowbatch Microbench\n\nGoal: test a default-off r=4/k=1/l=1 row-batched digit materialization candidate before full-SAB promotion.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage309-digit-rowbatch-microbench -->", "\n<!-- stage309-digit-rowbatch-microbench -->\n### Stage309 digit rowbatch microbench\n\n" f"`{decision}` tests the default-off `MAT_TRGSW_DIRECT_DFT_R4_ROWBATCH_DIGIT` candidate under isolated microbench gates.\n")
    append_once(HYPOTHESES, "H309_digit_rowbatch_microbench:", "\nH309_digit_rowbatch_microbench:\n" f"  status: {decision}\n  primary_metric: direct_sub_dft_digit_us_and_microbench_latency\n  evidence:\n    - repro/stage309_digit_rowbatch_microbench/run_metrics.csv\n    - repro/stage309_digit_rowbatch_microbench/bench_summary.csv\n    - repro/stage309_digit_rowbatch_microbench/proof_gate.csv\n  conclusion: >\n    Stage309 tests an opt-in r=4 row-batched digit materialization candidate.\n    It can only open full-SAB A/B if both digit component time and sub-DTF\n    microbench latency improve; otherwise it is kept as a neutral ablation.\n")
    append_once(MANIFEST, "- stage309_digit_rowbatch_microbench:", "\n- stage309_digit_rowbatch_microbench:\n  - `docs/stage309_digit_rowbatch_microbench.md`\n  - `theory_checks/stage309_digit_rowbatch_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage309_digit_rowbatch.md`\n  - `experiments/stage309_digit_rowbatch_microbench_plan.md`\n  - `scripts/run_stage309_digit_rowbatch_microbench.sh`\n  - `scripts/build_stage309_digit_rowbatch_microbench.py`\n  - `repro/stage309_digit_rowbatch_microbench/`\n")
    append_once(CHECKLIST, "<!-- stage309-digit-rowbatch-microbench-checklist -->", "\n<!-- stage309-digit-rowbatch-microbench-checklist -->\n" f"- [x] Stage309 records `{decision}` for the rowbatch digit candidate.\n")
    append_run_log(decision)

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, RUN_METRICS, SUMMARY,
        PROOF, NEXT, COMMANDS, REPORT, RAW / "variant_plan.csv",
    ]
    artifacts.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
