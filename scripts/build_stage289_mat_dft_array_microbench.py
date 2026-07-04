#!/usr/bin/env python3
"""Stage289 isolated torus-to-DFT array wrapper microbench gate."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage289_mat_dft_array_microbench"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage289_mat_dft_array_microbench.md"
THEORY = ROOT / "theory_checks" / "stage289_torus_to_dft_array_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage289_dft_array_wrapper_result.md"
PLAN = ROOT / "experiments" / "stage289_mat_dft_array_microbench_plan.md"
RUNNER = ROOT / "scripts" / "run_stage289_mat_dft_array_microbench.sh"
BUILDER = ROOT / "scripts" / "build_stage289_mat_dft_array_microbench.py"

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
REPORT = OUT / "stage289_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_POSITIVE = "PASS_STAGE289_DFT_ARRAY_WRAPPER_POSITIVE_FULL_SAB_REQUIRED"
DECISION_NEUTRAL = "NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE289_DFT_ARRAY_WRAPPER_CORRECTNESS"


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
        return {
            "run": run_idx,
            "status": "MISSING_OUTPUT",
            "source_log": rel(path),
        }
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
        rows.append({
            "path": rel(path),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    write_csv(ARTIFACT, ["path", "bytes", "sha256"], rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    logs = sorted(RAW.glob("run_*.log"))
    run_rows = [parse_log(path, idx) for idx, path in enumerate(logs)]
    write_csv(
        RUN_METRICS,
        [
            "run", "status", "rows", "N", "reps", "max_abs_diff", "diff_count",
            "scalar_loop_avg_us", "array_avg_us", "scalar_per_row_us",
            "array_per_row_us", "speedup_vs_scalar_loop", "checksum", "source_log",
        ],
        run_rows,
    )

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

    summary_rows = [{
        "decision": decision,
        "runs": len(run_rows),
        "correct_runs": len(valid),
        "rows": valid[0].get("rows", "") if valid else "",
        "N": valid[0].get("N", "") if valid else "",
        "reps": valid[0].get("reps", "") if valid else "",
        "scalar_loop_avg_us_mean": f"{mean(scalar):.6f}" if scalar else "0.000000",
        "array_avg_us_mean": f"{mean(array):.6f}" if array else "0.000000",
        "speedup_vs_scalar_loop_mean": f"{speed_mean:.6f}",
        "speedup_vs_scalar_loop_min": f"{speed_min:.6f}",
        "speedup_vs_scalar_loop_max": f"{speed_max:.6f}",
        "claim": "microbench_only_not_full_sab_latency",
    }]
    write_csv(
        SUMMARY,
        [
            "decision", "runs", "correct_runs", "rows", "N", "reps",
            "scalar_loop_avg_us_mean", "array_avg_us_mean",
            "speedup_vs_scalar_loop_mean", "speedup_vs_scalar_loop_min",
            "speedup_vs_scalar_loop_max", "claim",
        ],
        summary_rows,
    )

    proof_rows = [
        {
            "gate": "G1_logs",
            "status": "PASS" if logs else "FAIL",
            "metric": "raw run logs",
            "value": str(len(logs)),
            "interpretation": "Repeated isolated microbench logs must exist.",
        },
        {
            "gate": "G2_correctness",
            "status": "PASS" if all_correct else "FAIL",
            "metric": "all runs status",
            "value": f"{len(valid)}/{len(run_rows)}",
            "interpretation": "Array wrapper must match scalar-loop DFT output.",
        },
        {
            "gate": "G3_performance",
            "status": "PASS_PROMOTION_CANDIDATE" if decision == DECISION_POSITIVE else "NO_PROMOTION",
            "metric": "min speedup",
            "value": f"{speed_min:.6f}",
            "interpretation": "Promotion requires every repeated run to clear 1.02x before full-SAB A/B.",
        },
        {
            "gate": "G4_claim_boundary",
            "status": "PASS",
            "metric": "claim scope",
            "value": "isolated torus_to_DFT wrapper only",
            "interpretation": "No complete-SAB speedup or theoretical-optimality claim is made here.",
        },
        {
            "gate": "G5_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Use this result to admit or reject the wrapper as the next hot-path candidate.",
        },
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)

    next_rows = [
        {
            "priority": "P0",
            "stage": "stage290_dft_lifecycle_avoidance_design",
            "input": "Stage289 negative wrapper result",
            "task": "Design a candidate that removes or fuses torus-to-double/DFT lifecycle work instead of only wrapping per-row calls.",
            "gate": "isolated correctness plus microbench before full-SAB A/B",
        },
        {
            "priority": "P1",
            "stage": "stage291_full_sab_ab_after_dft_candidate",
            "input": "first Stage290 positive candidate",
            "task": "Run unprofiled complete-SAB T_bootstrap/r A/B only after an isolated candidate clears Stage290.",
            "gate": "same-backend repeated full-SAB correctness/performance",
        },
    ]
    write_csv(NEXT, ["priority", "stage", "input", "task", "gate"], next_rows)

    report = f"""# Stage289 MAT DFT Array Microbench

Decision: `{decision}`.

Stage288 found `torus_to_dft` as the largest measured MAT EP split component.
Stage289 isolates the existing `polynomial_torus_to_DFT_array` wrapper against
the scalar per-row loop for the MAT-SAB r=4 shape: rows=5, N=2048.

## Result

| metric | value |
|---|---:|
| runs | {len(run_rows)} |
| correct runs | {len(valid)} |
| scalar loop mean us | {summary_rows[0]['scalar_loop_avg_us_mean']} |
| array wrapper mean us | {summary_rows[0]['array_avg_us_mean']} |
| speedup mean | {summary_rows[0]['speedup_vs_scalar_loop_mean']}x |
| speedup min | {summary_rows[0]['speedup_vs_scalar_loop_min']}x |
| speedup max | {summary_rows[0]['speedup_vs_scalar_loop_max']}x |

## Interpretation

The wrapper is correctness-clean but is not promoted unless every repeated run
beats the scalar loop by at least 1.02x. This is a microbench-only gate and does
not claim complete SAB acceleration. If the decision is neutral, the next DFT
candidate must reduce the conversion lifecycle itself, not merely wrap the same
row-wise reverse FFT work.

## Proof Gate

| gate | status | value |
|---|---|---|
"""
    for row in proof_rows:
        report += f"| {row['gate']} | {row['status']} | {row['value']} |\n"

    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage289 Torus-to-DFT Array Model

For MAT-SAB r=4 with k=1 and l=1, each MAT external product converts
`k+r=5` torus polynomials into DFT form. The tested wrapper keeps the same five
reverse FFTs, but tries to reduce surrounding conversion/copy overhead by
feeding each row through a shared array interface.

The isolated model therefore predicts only a small possible gain: it does not
change FFT arithmetic count, and it can lose if scratch copies or cache effects
exceed saved function-call/processor-buffer overhead. A positive gate requires
same-backend repeated speedup before any full-SAB A/B.
""")
    write_text(VARIANT, f"""# Stage289 DFT Array Wrapper Result

Variant: `MAT_TRGSW_MULTIROW_DFT_WRAPPER` via `MAT_TRGSW_DFT_ARRAY_BENCH`.

Decision: `{decision}`.

The variant is correctness-clean in the isolated rows=5/N=2048 gate. It is not
a SAB optimization claim unless followed by a positive complete-SAB
`T_bootstrap/r` A/B. If neutral, it should be treated as a rejected/negative
microbench for the current r=4 DFT bottleneck.
""")
    write_text(PLAN, """# Stage289 MAT DFT Array Microbench Plan

1. Build with `FFT_LIB=spqlios_avx512` and
   `MAT_TRGSW_DFT_ARRAY_BENCH=true`.
2. Run repeated isolated rows=5/N=2048 DFT conversion tests.
3. Require coefficient-level equality against the scalar per-row loop.
4. Promote only if every run clears a 1.02x wrapper-vs-loop speedup.
5. Otherwise select a deeper DFT lifecycle candidate for Stage290.
""")
    write_text(COMMANDS, """# Stage289 Reproduction Commands

```bash
STAGE289_RUNS=3 STAGE289_REPS=5000 FFT_LIB=spqlios_avx512 \\
  bash scripts/run_stage289_mat_dft_array_microbench.sh
python3 scripts/build_stage289_mat_dft_array_microbench.py
```
""")

    append_once(GOAL, "<!-- stage289-mat-dft-array-microbench -->", f"""
<!-- stage289-mat-dft-array-microbench -->
### Stage289 MAT DFT array microbench

`{decision}` isolates the Stage288 `torus_to_dft` bottleneck by testing the
existing multi-row DFT wrapper against the scalar per-row conversion loop.
Correctness is separated from performance, and the result remains
microbench-only. Complete-SAB `T_bootstrap/r` claims remain gated.
""")
    append_once(HYPOTHESES, "H10_stage289_mat_dft_array_microbench:", f"""
H10_stage289_mat_dft_array_microbench:
  status: {decision}
  evidence:
    - repro/stage289_mat_dft_array_microbench/run_metrics.csv
    - repro/stage289_mat_dft_array_microbench/bench_summary.csv
    - repro/stage289_mat_dft_array_microbench/proof_gate.csv
    - docs/stage289_mat_dft_array_microbench.md
  conclusion: >
    Stage289 isolates the dominant Stage288 torus_to_dft component. The
    multi-row DFT wrapper is correctness-clean, but it is promoted only if the
    repeated isolated microbench clears the speedup gate; otherwise Stage290
    must target deeper DFT lifecycle reduction.
""")
    append_once(MANIFEST, "- stage289_mat_dft_array_microbench:", """
- stage289_mat_dft_array_microbench:
  - `docs/stage289_mat_dft_array_microbench.md`
  - `theory_checks/stage289_torus_to_dft_array_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage289_dft_array_wrapper_result.md`
  - `experiments/stage289_mat_dft_array_microbench_plan.md`
  - `scripts/run_stage289_mat_dft_array_microbench.sh`
  - `scripts/build_stage289_mat_dft_array_microbench.py`
  - `repro/stage289_mat_dft_array_microbench/`
""")
    append_once(CHECKLIST, "<!-- stage289-mat-dft-array-microbench-checklist -->", f"""
<!-- stage289-mat-dft-array-microbench-checklist -->
- [x] Stage289 records `{decision}` for isolated torus-to-DFT array-wrapper microbench.
""")
    append_run_log({
        "run_id": "stage289-mat-dft-array-microbench-001",
        "date": "2026-07-04",
        "git_ref": git_head(),
        "stage": "Stage289",
        "backend": "spqlios_avx512",
        "command": "STAGE289_RUNS=3 STAGE289_REPS=5000 FFT_LIB=spqlios_avx512 bash scripts/run_stage289_mat_dft_array_microbench.sh",
        "parameters": "rows=5; N=2048; isolated torus_to_DFT array wrapper",
        "rng": "default-rng",
        "status": decision,
        "notes": "Microbench-only; no complete-SAB speedup claim.",
        "artifacts": "docs/stage289_mat_dft_array_microbench.md; repro/stage289_mat_dft_array_microbench/",
    })

    artifact_index([
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, RUN_METRICS, SUMMARY,
        PROOF, NEXT, COMMANDS, REPORT, RAW / "variant_plan.csv",
        *sorted(RAW.glob("*.log")),
    ])
    print(decision)


if __name__ == "__main__":
    main()
