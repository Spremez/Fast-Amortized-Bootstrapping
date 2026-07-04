#!/usr/bin/env python3
"""Build Stage311 narrow32 digit-conversion microbench artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage311_digit_narrow32_microbench"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage311_digit_narrow32_microbench.md"
THEORY = ROOT / "theory_checks" / "stage311_digit_narrow32_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage311_digit_narrow32.md"
PLAN = ROOT / "experiments" / "stage311_digit_narrow32_microbench_plan.md"
RUNNER = ROOT / "scripts" / "run_stage311_digit_narrow32_microbench.sh"
BUILDER = ROOT / "scripts" / "build_stage311_digit_narrow32_microbench.py"

RUN_METRICS = OUT / "run_metrics.csv"
SUMMARY = OUT / "bench_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage311_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_POSITIVE = "PASS_STAGE311_DIGIT_NARROW32_MICRO_POSITIVE_FULLSAB_REQUIRED"
DECISION_NEUTRAL = "NEUTRAL_STAGE311_DIGIT_NARROW32_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE311_DIGIT_NARROW32_CORRECTNESS"

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
        "source_log": rel(path),
    }


def paired_speedups(base_values: List[float], cand_values: List[float]) -> List[float]:
    return [
        base_values[idx] / cand_values[idx]
        for idx in range(min(len(base_values), len(cand_values)))
        if cand_values[idx] > 0.0
    ]


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage311-digit-narrow32-microbench-001"
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
        "stage": "Stage 311",
        "backend": "spqlios_avx512-local",
        "command": "STAGE311_RUNS=5 STAGE311_REPS=5000 FFT_LIB=spqlios_avx512 bash scripts/run_stage311_digit_narrow32_microbench.sh",
        "config": "r=4,N=2048 direct baseline vs narrow32 digit conversion microbench",
        "params": "BINARY SET_2_3 microbench; r=4; N=2048",
        "seed": "n/a",
        "status": decision,
        "summary": "Stage311 tests opt-in int64->int32->double digit conversion before any full-SAB promotion.",
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
    for variant in ["direct_baseline", "narrow32_digit"]:
        for idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
            run_rows.append(parse_log(path, variant, idx))
    fields = [
        "variant", "run", "status", "r", "N", "reps", "max_abs_diff",
        "sub_avg_us", "speedup_vs_separate", "checksum", "profile_calls",
        "profile_rows_sum", "digit_us", "ifft_us", "profile_total_us",
        "digit_avg_us_per_call", "source_log",
    ]
    write_csv(RUN_METRICS, run_rows, fields)

    baseline = [row for row in run_rows if row.get("variant") == "direct_baseline" and row.get("status") == "Pass"]
    candidate = [row for row in run_rows if row.get("variant") == "narrow32_digit" and row.get("status") == "Pass"]
    all_correct = len(baseline) > 0 and len(baseline) == len(candidate)
    base_digit = [fnum(row.get("digit_us")) for row in baseline]
    cand_digit = [fnum(row.get("digit_us")) for row in candidate]
    base_sub = [fnum(row.get("sub_avg_us")) for row in baseline]
    cand_sub = [fnum(row.get("sub_avg_us")) for row in candidate]
    digit_speedups = paired_speedups(base_digit, cand_digit)
    sub_speedups = paired_speedups(base_sub, cand_sub)
    digit_min = min(digit_speedups) if digit_speedups else 0.0
    sub_min = min(sub_speedups) if sub_speedups else 0.0

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
        "narrow32_digit_us_mean": fmt(mean(cand_digit)) if cand_digit else "0.000000",
        "digit_speedup_mean": fmt(mean(digit_speedups)) if digit_speedups else "0.000000",
        "digit_speedup_min": fmt(digit_min),
        "baseline_sub_avg_us_mean": fmt(mean(base_sub)) if base_sub else "0.000000",
        "narrow32_sub_avg_us_mean": fmt(mean(cand_sub)) if cand_sub else "0.000000",
        "sub_speedup_mean": fmt(mean(sub_speedups)) if sub_speedups else "0.000000",
        "sub_speedup_min": fmt(sub_min),
        "claim": "microbench_only_full_sab_required",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "runs_per_variant", "correctness",
        "baseline_digit_us_mean", "narrow32_digit_us_mean",
        "digit_speedup_mean", "digit_speedup_min",
        "baseline_sub_avg_us_mean", "narrow32_sub_avg_us_mean",
        "sub_speedup_mean", "sub_speedup_min", "claim",
    ])

    proof = [
        {"gate": "G1_runs", "status": "PASS" if len(baseline) == len(candidate) and len(baseline) > 0 else "FAIL", "metric": "paired runs", "value": f"{len(baseline)}/{len(candidate)}", "interpretation": "Both variants need paired repeated runs."},
        {"gate": "G2_correctness", "status": "PASS" if all_correct else "FAIL", "metric": "MAT_SUB_DFT correctness", "value": "PASS" if all_correct else "FAIL", "interpretation": "Narrow32 digit conversion must preserve MAT sub-DTF output."},
        {"gate": "G3_digit_component", "status": "PASS" if digit_min >= 1.02 else "NO_PROMOTION", "metric": "paired min digit speedup", "value": fmt(digit_min), "interpretation": "Digit component must improve before full-SAB A/B is justified."},
        {"gate": "G4_sub_latency", "status": "PASS" if sub_min >= 1.01 else "NO_PROMOTION", "metric": "paired min sub-DTF speedup", "value": fmt(sub_min), "interpretation": "Component gain must survive the sub-DTF microbench surface."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "scope", "value": "microbench only", "interpretation": "Stage311 is not a complete-SAB speed claim."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls whether a full-SAB A/B is opened."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    next_stage = "stage312_digit_narrow32_full_sab_ab" if decision == DECISION_POSITIVE else "stage312_backend_ifft_or_stop_digit_microvariants"
    next_task = "Run complete-SAB T_bootstrap/r A/B with narrow32 digit flag enabled." if decision == DECISION_POSITIVE else "Do not promote narrow32; continue only with backend IFFT or a new justified digit microvariant."
    write_csv(NEXT, [{
        "priority": "P0",
        "stage": next_stage,
        "input": decision,
        "task": next_task,
        "gate": "same-backend full-SAB correctness/performance if positive; otherwise no full-SAB A/B",
    }], ["priority", "stage", "input", "task", "gate"])

    report = (
        "# Stage311 Digit Narrow32 Microbench\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage311 tests an opt-in digit conversion variant that narrows signed gadget digits to int32 before converting to double. It is valid only when the gadget digit range fits int32.\n\n"
        "## Summary\n\n" + table(summary_rows, [
            "decision", "runs_per_variant", "correctness",
            "digit_speedup_mean", "digit_speedup_min",
            "sub_speedup_mean", "sub_speedup_min",
        ]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage311 Digit Narrow32 Model

For the tested SAB parameters, Bg_bit=23 and signed gadget digits fit in int32.
The baseline direct digit path converts signed int64 lanes directly to double.
The Stage311 candidate converts int64 digits to int32 lanes first, then uses
the AVX512 int32-to-double conversion.

The algebra is unchanged if and only if the signed digit range fits in int32.
The implementation therefore keeps a runtime guard and falls back to the
baseline int64-to-double conversion for larger gadget bases.

Promotion requires both the profiled digit component and the sub-DTF microbench
surface to improve in every paired run.
""")
    write_text(VARIANT, f"""# Stage311 MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32

Flag: `MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32=true`.

Decision: `{decision}`.

This default-off candidate changes only digit materialization in the direct
sub-DTF path. It does not change key format, ciphertext algebra, selector
layout, scalar SAB, or default PVW/MAT-SAB behavior.
""")
    write_text(PLAN, """# Stage311 Experiment Plan

1. Build direct baseline and narrow32 variants with direct DFT profile.
2. Run paired MAT_SUB_DFT microbench repetitions.
3. Require correctness for every run.
4. Promote only if digit_us and sub-DTF latency improve in every paired run.
5. If neutral, keep the current direct-DFT implementation unchanged.
""")
    write_text(COMMANDS, """# Stage311 Reproduction Commands

```bash
STAGE311_RUNS=5 STAGE311_REPS=5000 FFT_LIB=spqlios_avx512 \\
  bash scripts/run_stage311_digit_narrow32_microbench.sh
python3 scripts/build_stage311_digit_narrow32_microbench.py
```
""")

    append_once(ROADMAP, "## Stage 311: Digit Narrow32 Microbench", "\n## Stage 311: Digit Narrow32 Microbench\n\nGoal: test an opt-in int64-to-int32-to-double digit materialization candidate before full-SAB promotion.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage311-digit-narrow32-microbench -->", "\n<!-- stage311-digit-narrow32-microbench -->\n### Stage311 digit narrow32 microbench\n\n" f"`{decision}` tests the default-off `MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32` candidate under isolated microbench gates.\n")
    append_once(HYPOTHESES, "H311_digit_narrow32_microbench:", "\nH311_digit_narrow32_microbench:\n" f"  status: {decision}\n  primary_metric: direct_sub_dft_digit_us_and_microbench_latency\n  evidence:\n    - repro/stage311_digit_narrow32_microbench/run_metrics.csv\n    - repro/stage311_digit_narrow32_microbench/bench_summary.csv\n    - repro/stage311_digit_narrow32_microbench/proof_gate.csv\n  conclusion: >\n    Stage311 tests an opt-in narrow32 digit materialization candidate. It can\n    only open full-SAB A/B if both digit component time and sub-DTF microbench\n    latency improve; otherwise it is a neutral/negative ablation.\n")
    append_once(MANIFEST, "- stage311_digit_narrow32_microbench:", "\n- stage311_digit_narrow32_microbench:\n  - `docs/stage311_digit_narrow32_microbench.md`\n  - `theory_checks/stage311_digit_narrow32_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage311_digit_narrow32.md`\n  - `experiments/stage311_digit_narrow32_microbench_plan.md`\n  - `scripts/run_stage311_digit_narrow32_microbench.sh`\n  - `scripts/build_stage311_digit_narrow32_microbench.py`\n  - `repro/stage311_digit_narrow32_microbench/`\n")
    append_once(CHECKLIST, "<!-- stage311-digit-narrow32-microbench-checklist -->", "\n<!-- stage311-digit-narrow32-microbench-checklist -->\n" f"- [x] Stage311 records `{decision}` for the narrow32 digit candidate.\n")
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
