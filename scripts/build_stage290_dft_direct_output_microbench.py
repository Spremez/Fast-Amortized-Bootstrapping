#!/usr/bin/env python3
"""Stage290 direct-output torus-to-DFT array microbench gate."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage290_dft_direct_output_microbench"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage290_dft_direct_output_microbench.md"
THEORY = ROOT / "theory_checks" / "stage290_direct_output_dft_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage290_dft_direct_output.md"
PLAN = ROOT / "experiments" / "stage290_dft_direct_output_microbench_plan.md"
RUNNER = ROOT / "scripts" / "run_stage290_dft_direct_output_microbench.sh"
BUILDER = ROOT / "scripts" / "build_stage290_dft_direct_output_microbench.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

RUN_METRICS = OUT / "run_metrics.csv"
SUMMARY = OUT / "bench_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage290_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_POSITIVE = "PASS_STAGE290_DFT_DIRECT_OUTPUT_MICRO_POSITIVE_FULL_SAB_REQUIRED"
DECISION_NEUTRAL = "NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE290_DFT_DIRECT_OUTPUT_CORRECTNESS"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.rstrip().split("\n"))
    path.write_text(normalized + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_list = list(fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in field_list})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def append_run_log(row: Dict[str, str]) -> None:
    existing = read_text(RUN_LOG)
    if row["run_id"] in existing:
        return
    with RUN_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "run_id", "date", "git_ref", "stage", "backend", "command",
                "parameters", "rng", "status", "notes", "artifacts",
            ],
            lineterminator="\n",
        )
        writer.writerow(row)


def parse_log(path: Path, run_idx: int) -> Dict[str, object]:
    text = read_text(path)
    correctness = re.search(
        r"MAT_DFT_ARRAY correctness rows=(?P<rows>\d+) N=(?P<N>\d+) "
        r"max_abs_diff=(?P<max_abs_diff>\S+) diff_count=(?P<diff_count>\d+) "
        r"status=(?P<status>\w+)",
        text,
    )
    bench = re.search(
        r"MAT_DFT_ARRAY bench rows=(?P<rows>\d+) N=(?P<N>\d+) reps=(?P<reps>\d+) "
        r"scalar_loop_avg_us=(?P<scalar>\S+) array_avg_us=(?P<array>\S+) "
        r"scalar_per_row_us=(?P<scalar_row>\S+) array_per_row_us=(?P<array_row>\S+) "
        r"speedup_vs_scalar_loop=(?P<speedup>\S+)x checksum=(?P<checksum>\S+)",
        text,
    )
    if correctness is None or bench is None:
        return {"run": run_idx, "status": "MISSING_OUTPUT", "source_log": rel(path)}
    return {
        "run": run_idx,
        "status": correctness.group("status"),
        "rows": correctness.group("rows"),
        "N": correctness.group("N"),
        "reps": bench.group("reps"),
        "max_abs_diff": correctness.group("max_abs_diff"),
        "diff_count": correctness.group("diff_count"),
        "scalar_loop_avg_us": bench.group("scalar"),
        "array_avg_us": bench.group("array"),
        "scalar_per_row_us": bench.group("scalar_row"),
        "array_per_row_us": bench.group("array_row"),
        "speedup_vs_scalar_loop": bench.group("speedup"),
        "checksum": bench.group("checksum"),
        "source_log": rel(path),
    }


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if not path.exists():
            continue
        data = path.read_bytes()
        rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, ["path", "bytes", "sha256"], rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logs = sorted(RAW.glob("run_*.log"))
    run_rows = [parse_log(path, idx) for idx, path in enumerate(logs)]
    fields = [
        "run", "status", "rows", "N", "reps", "max_abs_diff", "diff_count",
        "scalar_loop_avg_us", "array_avg_us", "scalar_per_row_us",
        "array_per_row_us", "speedup_vs_scalar_loop", "checksum", "source_log",
    ]
    write_csv(RUN_METRICS, fields, run_rows)

    valid = [row for row in run_rows if row.get("status") == "Pass"]
    all_correct = len(valid) == len(run_rows) and len(valid) > 0
    speeds = [fnum(row.get("speedup_vs_scalar_loop")) for row in valid]
    scalar = [fnum(row.get("scalar_loop_avg_us")) for row in valid]
    array = [fnum(row.get("array_avg_us")) for row in valid]
    speed_mean = mean(speeds) if speeds else 0.0
    speed_min = min(speeds) if speeds else 0.0
    speed_max = max(speeds) if speeds else 0.0
    decision = DECISION_FAIL
    if all_correct and speed_min >= 1.02:
        decision = DECISION_POSITIVE
    elif all_correct:
        decision = DECISION_NEUTRAL

    summary = [{
        "decision": decision,
        "runs": len(run_rows),
        "correct_runs": len(valid),
        "rows": valid[0].get("rows", "") if valid else "",
        "N": valid[0].get("N", "") if valid else "",
        "reps": valid[0].get("reps", "") if valid else "",
        "scalar_loop_avg_us_mean": f"{mean(scalar):.6f}" if scalar else "0.000000",
        "direct_array_avg_us_mean": f"{mean(array):.6f}" if array else "0.000000",
        "speedup_vs_scalar_loop_mean": f"{speed_mean:.6f}",
        "speedup_vs_scalar_loop_min": f"{speed_min:.6f}",
        "speedup_vs_scalar_loop_max": f"{speed_max:.6f}",
        "claim": "microbench_only_full_sab_required",
    }]
    write_csv(
        SUMMARY,
        [
            "decision", "runs", "correct_runs", "rows", "N", "reps",
            "scalar_loop_avg_us_mean", "direct_array_avg_us_mean",
            "speedup_vs_scalar_loop_mean", "speedup_vs_scalar_loop_min",
            "speedup_vs_scalar_loop_max", "claim",
        ],
        summary,
    )

    proof = [
        {"gate": "G1_logs", "status": "PASS" if logs else "FAIL", "metric": "raw run logs", "value": str(len(logs)), "interpretation": "Repeated isolated logs exist."},
        {"gate": "G2_correctness", "status": "PASS" if all_correct else "FAIL", "metric": "all runs status", "value": f"{len(valid)}/{len(run_rows)}", "interpretation": "Direct-output array DFT must equal scalar-loop DFT output."},
        {"gate": "G3_microbench", "status": "PASS" if decision == DECISION_POSITIVE else "NO_PROMOTION", "metric": "min speedup", "value": f"{speed_min:.6f}", "interpretation": "Every run must clear 1.02x before full-SAB A/B."},
        {"gate": "G4_claim_boundary", "status": "PASS", "metric": "claim scope", "value": "isolated direct-output DFT only", "interpretation": "No complete-SAB speedup claim is made here."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Positive result admits full-SAB A/B only."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof)

    next_task = "Run complete-SAB T_bootstrap/r A/B with direct-output DFT enabled." if decision == DECISION_POSITIVE else "Return to DFT lifecycle design; do not run full-SAB A/B for this candidate."
    next_rows = [
        {
            "priority": "P0",
            "stage": "stage291_direct_output_full_sab_ab",
            "input": decision,
            "task": next_task,
            "gate": "same-backend repeated full-SAB correctness/performance, then noise/resource if positive",
        }
    ]
    write_csv(NEXT, ["priority", "stage", "input", "task", "gate"], next_rows)

    report = f"""# Stage290 DFT Direct-Output Microbench

Decision: `{decision}`.

Stage290 tests `MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT`, an explicit opt-in path
that converts torus rows directly into the DFT output buffer and runs `ifft`
there, avoiding the extra scratch-to-output copy in the Stage289 wrapper.

| metric | value |
|---|---:|
| runs | {len(run_rows)} |
| correct runs | {len(valid)} |
| scalar loop mean us | {summary[0]['scalar_loop_avg_us_mean']} |
| direct array mean us | {summary[0]['direct_array_avg_us_mean']} |
| speedup mean | {summary[0]['speedup_vs_scalar_loop_mean']}x |
| speedup min | {summary[0]['speedup_vs_scalar_loop_min']}x |
| speedup max | {summary[0]['speedup_vs_scalar_loop_max']}x |

This is still a microbench-only result. A positive decision only admits Stage291
complete-SAB A/B; it does not prove bootstrapping acceleration by itself.

## Proof Gate

| gate | status | value |
|---|---|---|
"""
    for row in proof:
        report += f"| {row['gate']} | {row['status']} | {row['value']} |\n"
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage290 Direct-Output DFT Model

Baseline `polynomial_torus_to_DFT` converts torus coefficients into the
FFT processor reverse buffer, runs an in-place reverse FFT, and copies the
double buffer into the destination DFT polynomial. Stage289's array wrapper
kept the same arithmetic and added a scratch-to-output copy.

`MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT` writes converted doubles into
`out[i]->coeffs` and calls `ifft` in place on that destination. The arithmetic
count is unchanged, but one N-double copy per converted row is removed. The
candidate is therefore expected to help only when the removed copy is visible
relative to the reverse FFT cost.
""")
    write_text(VARIANT, f"""# Stage290 DFT Direct-Output Variant

Flag: `MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT=true`.

Decision: `{decision}`.

The path is explicit and default-off. It changes only the multi-row DFT array
implementation used by MAT external-product experiments. It must pass full-SAB
`T_bootstrap/r` A/B before becoming a SAB optimization claim.
""")
    write_text(PLAN, """# Stage290 DFT Direct-Output Microbench Plan

1. Build with `MAT_TRGSW_DFT_ARRAY_BENCH=true` and
   `MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT=true`.
2. Compare direct-output array DFT against scalar per-row DFT on rows=5/N=2048.
3. Require exact DFT-output equality and repeated min speedup >= 1.02x.
4. If positive, run Stage291 complete-SAB A/B with the same explicit flag.
""")
    write_text(COMMANDS, """# Stage290 Reproduction Commands

```bash
STAGE290_RUNS=3 STAGE290_REPS=5000 FFT_LIB=spqlios_avx512 \\
  bash scripts/run_stage290_dft_direct_output_microbench.sh
python3 scripts/build_stage290_dft_direct_output_microbench.py
```
""")

    append_once(GOAL, "<!-- stage290-dft-direct-output-microbench -->", f"""
<!-- stage290-dft-direct-output-microbench -->
### Stage290 DFT direct-output microbench

`{decision}` tests direct-output torus-to-DFT conversion for the MAT-SAB r=4
rows=5/N=2048 shape. The result is isolated microbench evidence only; a
positive gate admits complete-SAB `T_bootstrap/r` A/B but is not itself a
bootstrapping speed claim.
""")
    append_once(HYPOTHESES, "H10_stage290_dft_direct_output_microbench:", f"""
H10_stage290_dft_direct_output_microbench:
  status: {decision}
  evidence:
    - repro/stage290_dft_direct_output_microbench/run_metrics.csv
    - repro/stage290_dft_direct_output_microbench/bench_summary.csv
    - repro/stage290_dft_direct_output_microbench/proof_gate.csv
    - docs/stage290_dft_direct_output_microbench.md
  conclusion: >
    Stage290 implements a default-off direct-output DFT array path. It may
    proceed to complete-SAB A/B only when the isolated repeated microbench is
    positive; otherwise it remains a rejected DFT lifecycle candidate.
""")
    append_once(MANIFEST, "- stage290_dft_direct_output_microbench:", """
- stage290_dft_direct_output_microbench:
  - `docs/stage290_dft_direct_output_microbench.md`
  - `theory_checks/stage290_direct_output_dft_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage290_dft_direct_output.md`
  - `experiments/stage290_dft_direct_output_microbench_plan.md`
  - `scripts/run_stage290_dft_direct_output_microbench.sh`
  - `scripts/build_stage290_dft_direct_output_microbench.py`
  - `repro/stage290_dft_direct_output_microbench/`
""")
    append_once(CHECKLIST, "<!-- stage290-dft-direct-output-microbench-checklist -->", f"""
<!-- stage290-dft-direct-output-microbench-checklist -->
- [x] Stage290 records `{decision}` for the direct-output DFT array microbench.
""")
    append_run_log({
        "run_id": "stage290-dft-direct-output-microbench-001",
        "date": "2026-07-04",
        "git_ref": git_head(),
        "stage": "Stage290",
        "backend": "spqlios_avx512",
        "command": "STAGE290_RUNS=3 STAGE290_REPS=5000 FFT_LIB=spqlios_avx512 bash scripts/run_stage290_dft_direct_output_microbench.sh",
        "parameters": "rows=5; N=2048; direct-output torus_to_DFT array",
        "rng": "default-rng",
        "status": decision,
        "notes": "Microbench-only; full-SAB A/B required for any bootstrap speed claim.",
        "artifacts": "docs/stage290_dft_direct_output_microbench.md; repro/stage290_dft_direct_output_microbench/",
    })

    artifact_index([
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, RUN_METRICS, SUMMARY,
        PROOF, NEXT, COMMANDS, REPORT, RAW / "variant_plan.csv",
        *sorted(RAW.glob("*.log")),
    ])
    print(decision)


if __name__ == "__main__":
    main()
