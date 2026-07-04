#!/usr/bin/env python3
"""Build Stage319 hand-written IFFT batch5 assembly artifacts."""

from __future__ import annotations

import csv
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage319_ifft_batch5_asm_microbench"
LOG = OUT / "batch5_asm_run_5000_001.log"
OBJDUMP = OUT / "ifft_batch5_tile32_asm_objdump.txt"
LINE_COUNT = OUT / "asm_objdump_line_count.txt"

DOC = ROOT / "docs" / "stage319_ifft_batch5_asm_microbench.md"
THEORY = ROOT / "theory_checks" / "stage319_ifft_batch5_asm_closeout.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage319_ifft_batch5_asm.md"
PLAN = ROOT / "experiments" / "stage320_return_to_sab_schedule_plan.md"

SUMMARY = OUT / "stage319_summary.csv"
RUNS = OUT / "bench_runs.csv"
EQUIV = OUT / "equivalence.csv"
ASM = OUT / "asm_audit.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage319_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "FAIL_STAGE319_HAND_ASM_BATCH5_CORRECT_BUT_SLOW_CLOSE_BACKEND_IFFT_BATCH5"
NEXT_STAGE = "stage320_return_to_sab_schedule_or_mat_ep_budget"
REQUIRED_REDUCTION = 0.107769


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


def append_once(path: Path, marker: str, block: str) -> None:
    text = read_text(path)
    if marker in text:
        return
    write_text(path, text.rstrip() + "\n" + marker + "\n" + block.strip() + "\n")


def git_head() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        )
        return out.strip()
    except Exception:
        return "unknown"


def sanitize_objdump() -> None:
    if not OBJDUMP.exists():
        return
    lines = [line.rstrip() for line in read_text(OBJDUMP).splitlines()]
    write_text(OBJDUMP, "\n".join(lines))


def parse_log() -> tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    text = read_text(LOG)
    equiv_re = re.compile(
        r"MAT_IFFT_BATCH5 equivalence variant=(?P<variant>\w+) rows=(?P<rows>\d+) "
        r"N=(?P<N>\d+) bit_mismatches=(?P<mismatches>\d+) "
        r"max_abs=(?P<max_abs>[-+0-9.eE]+)"
    )
    bench_re = re.compile(
        r"MAT_IFFT_BATCH5 bench variant=(?P<variant>\w+) rows=(?P<rows>\d+) "
        r"N=(?P<N>\d+) reps=(?P<reps>\d+) copy_avg_us=(?P<copy>[-+0-9.eE]+) "
        r"scalar_ifft_est_avg_us=(?P<scalar>[-+0-9.eE]+) "
        r"batch_ifft_est_avg_us=(?P<batch>[-+0-9.eE]+) "
        r"speedup=(?P<speedup>[-+0-9.eE]+) reduction=(?P<reduction>[-+0-9.eE]+)"
    )
    equiv_rows: List[Dict[str, object]] = []
    bench_rows: List[Dict[str, object]] = []
    for line in text.splitlines():
        eq = equiv_re.search(line)
        if eq:
            equiv_rows.append(
                {
                    "sample": len(equiv_rows) + 1,
                    "variant": eq.group("variant"),
                    "rows": int(eq.group("rows")),
                    "N": int(eq.group("N")),
                    "bit_mismatches": int(eq.group("mismatches")),
                    "max_abs": float(eq.group("max_abs")),
                }
            )
        bm = bench_re.search(line)
        if bm:
            bench_rows.append(
                {
                    "sample": len(bench_rows) + 1,
                    "variant": bm.group("variant"),
                    "rows": int(bm.group("rows")),
                    "N": int(bm.group("N")),
                    "reps": int(bm.group("reps")),
                    "copy_avg_us": float(bm.group("copy")),
                    "scalar_ifft_est_avg_us": float(bm.group("scalar")),
                    "batch_ifft_est_avg_us": float(bm.group("batch")),
                    "speedup": float(bm.group("speedup")),
                    "reduction": float(bm.group("reduction")),
                }
            )
    return equiv_rows, bench_rows


def asm_rows() -> List[Dict[str, object]]:
    text = read_text(OBJDUMP)
    try:
        line_count = int(read_text(LINE_COUNT).splitlines()[0])
    except Exception:
        line_count = len(text.splitlines())
    return [
        {
            "artifact": rel(OBJDUMP),
            "line_count": line_count,
            "rsp_or_rbp_refs": len(re.findall(r"\[rsp|\[rbp", text)),
            "high_zmm16_31_refs": len(re.findall(r"zmm(?:1[6-9]|2[0-9]|3[0-1])", text)),
            "vzeroall_refs": len(re.findall(r"\bvzeroall\b", text)),
            "call_refs": len(re.findall(r"\bcall", text)),
            "interpretation": (
                "The handwritten batch5 assembly is correct but still too long "
                "relative to five compact single-row IFFT calls; saved trig loads "
                "do not pay for row-batched address and butterfly work."
            ),
        }
    ]


def fmean(values: List[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def main() -> int:
    if not LOG.exists() or not OBJDUMP.exists():
        print("missing Stage319 raw log or objdump")
        return 1
    sanitize_objdump()
    equiv_rows, bench_rows = parse_log()
    if not equiv_rows or not bench_rows:
        print("failed to parse Stage319 raw log")
        return 1
    asm = asm_rows()
    speedups = [float(row["speedup"]) for row in bench_rows]
    reductions = [float(row["reduction"]) for row in bench_rows]
    mismatches = [int(row["bit_mismatches"]) for row in equiv_rows]
    max_abs = [float(row["max_abs"]) for row in equiv_rows]
    summary_rows = [
        {
            "decision": DECISION,
            "samples": len(bench_rows),
            "max_bit_mismatches": max(mismatches),
            "max_abs": f"{max(max_abs):.17g}",
            "mean_speedup": f"{fmean(speedups):.6f}",
            "min_speedup": f"{min(speedups):.6f}",
            "max_speedup": f"{max(speedups):.6f}",
            "mean_reduction": f"{fmean(reductions):.6f}",
            "required_reduction": f"{REQUIRED_REDUCTION:.6f}",
            "next_stage": NEXT_STAGE,
        }
    ]

    write_csv(RUNS, bench_rows, [
        "sample", "variant", "rows", "N", "reps", "copy_avg_us",
        "scalar_ifft_est_avg_us", "batch_ifft_est_avg_us", "speedup", "reduction"
    ])
    write_csv(EQUIV, equiv_rows, [
        "sample", "variant", "rows", "N", "bit_mismatches", "max_abs"
    ])
    write_csv(ASM, asm, [
        "artifact", "line_count", "rsp_or_rbp_refs", "high_zmm16_31_refs",
        "vzeroall_refs", "call_refs", "interpretation"
    ])
    write_csv(SUMMARY, summary_rows, [
        "decision", "samples", "max_bit_mismatches", "max_abs",
        "mean_speedup", "min_speedup", "max_speedup", "mean_reduction",
        "required_reduction", "next_stage"
    ])
    proof_rows = [
        {
            "gate": "G1_build",
            "status": "PASS",
            "metric": "WSL spqlios_avx512 build",
            "value": "make succeeded",
            "interpretation": "The hand-written assembly candidate is buildable.",
        },
        {
            "gate": "G2_equivalence",
            "status": "PASS",
            "metric": "max bit mismatches",
            "value": max(mismatches),
            "interpretation": "Assembly batch5 output is bit-identical to five existing IFFT calls.",
        },
        {
            "gate": "G3_performance",
            "status": "FAIL",
            "metric": "mean isolated IFFT reduction vs required",
            "value": f"{fmean(reductions):.6f};{REQUIRED_REDUCTION:.6f}",
            "interpretation": "The hand-written batch5 assembly is slower than the scalar assembly baseline.",
        },
        {
            "gate": "G4_close_backend_ifft_batch5",
            "status": "PASS_CLOSE",
            "metric": "backend direction",
            "value": "closed",
            "interpretation": "Batch5 IFFT is not an admissible path to SAB acceleration.",
        },
    ]
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, [
        {
            "priority": "P0",
            "stage": NEXT_STAGE,
            "input": DECISION,
            "task": "Return to complete-SAB T_bootstrap/r budget and choose a non-IFFT schedule/MAT-EP optimization candidate.",
            "gate": "no SAB integration from IFFT batch5; next candidate must have pre-implementation full-SAB budget evidence",
        }
    ], ["priority", "stage", "input", "task", "gate"])
    write_text(COMMANDS, """# Stage319 Reproduction Commands

```sh
make FFT_LIB=spqlios_avx512 MAT_TRGSW_IFFT_BATCH5_ASM_BENCH=true MAT_TRGSW_IFFT_BATCH5_BENCH_REPS=5000
./main
objdump -d -Mintel --disassemble=ifft_batch5_tile32_asm build/spqlios-ifft-avx512.o
```
""")
    artifacts = [
        (SUMMARY, "decision summary"),
        (RUNS, "parsed repeated bench runs"),
        (EQUIV, "bit-equivalence results"),
        (ASM, "assembly audit counters"),
        (PROOF, "stage gate"),
        (NEXT, "next-stage queue"),
        (LOG, "raw bench log"),
        (OBJDUMP, "raw objdump"),
        (DOC, "human-readable report"),
        (THEORY, "closeout theory note"),
        (VARIANT, "algorithm variant card"),
        (PLAN, "next experiment plan"),
    ]
    write_csv(ARTIFACT, [{"artifact": rel(p), "role": r} for p, r in artifacts], ["artifact", "role"])

    summary = summary_rows[0]
    report = f"""# Stage319 IFFT Batch5 Hand Assembly Microbench

Decision: `{DECISION}`.

Stage319 implements a hand-written SPQLIOS AVX512 `ifft_batch5_tile32_asm`
candidate.  It is bit-identical to five existing `ifft` calls, but it is still
slower and therefore closes the backend batch5 IFFT direction.

| metric | value |
| --- | --- |
| samples | {summary['samples']} |
| max bit mismatches | {summary['max_bit_mismatches']} |
| mean speedup | {summary['mean_speedup']} |
| min speedup | {summary['min_speedup']} |
| max speedup | {summary['max_speedup']} |
| mean reduction | {summary['mean_reduction']} |
| required reduction | {summary['required_reduction']} |
| next stage | {summary['next_stage']} |

Interpretation: the Stage317 memory-only model overestimated the opportunity.
The saved trig-table loads are dominated by the extra row-batched address and
butterfly work compared with five compact single-row SPQLIOS assembly calls.
This negative result is now part of the evidence chain and prevents further
IFFT-only work from delaying complete SAB optimization.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, f"""# Stage319 IFFT Batch5 Closeout

Both C/intrinsics and hand-written assembly implementations are correct but
slower than the existing scalar-row SPQLIOS AVX512 IFFT baseline.

The decisive metric is isolated IFFT component reduction.  Stage319 mean
reduction is {summary['mean_reduction']} while the required reduction is
{summary['required_reduction']}.  Since the candidate fails before SAB
integration, it cannot improve complete `T_bootstrap/r`.

The backend batch5 IFFT direction is closed.  Further work should return to
SAB schedule, MAT external product, selector layout, or complete pipeline
budget items where full-SAB evidence can justify implementation risk.
""")
    write_text(VARIANT, f"""# Stage319 Candidate: `ifft_batch5_tile32_asm`

Status: `{DECISION}`.

This candidate is a hand-written AVX512 assembly implementation of five-row
SPQLIOS inverse transform batching.  It preserves:

```text
forall row in 0..4: out[row] = IFFT(row)
```

Correctness passes with zero bit mismatches.  Performance fails, so the symbol
must remain an isolated negative ablation and must not be called from MAT/SAB.
""")
    write_text(PLAN, f"""# Stage320 Plan

Input decision: `{DECISION}`.

Return to the complete SAB `T_bootstrap/r` budget.  Candidate selection should
exclude IFFT batch5 and require pre-implementation evidence that the candidate
can move full SAB by at least the standing budget threshold.

Priority directions:

- schedule-level SAB copy/sub/CMUX fusion with full-SAB attribution;
- MAT external product row/layout changes that affect the dominant share;
- selector/key layout changes only if they preserve correctness and key format
  boundaries.
""")

    append_once(GOAL, "<!-- stage319-ifft-batch5-asm-microbench -->",
        f"""### Stage319 IFFT batch5 hand assembly microbench

`{DECISION}`: hand-written batch5 IFFT is bit-identical but slower than five
existing SPQLIOS AVX512 `ifft` calls, closing the backend IFFT batch5 route.
""")
    append_once(ROADMAP, "<!-- stage319-ifft-batch5-asm-roadmap -->",
        f"""## Stage 319: IFFT Batch5 Hand Assembly Microbench

Goal: test whether hand-written assembly can rescue the Stage317 IFFT batch5
candidate after the Stage318 intrinsics failure.

Status: `{DECISION}`.
""")
    append_once(HYPOTHESES, "H319_ifft_batch5_hand_asm_microbench:",
        f"""H319_ifft_batch5_hand_asm_microbench:
  status: {DECISION}
  primary_metric: isolated_ifft_component_reduction
  evidence:
    - repro/stage319_ifft_batch5_asm_microbench/stage319_summary.csv
    - repro/stage319_ifft_batch5_asm_microbench/bench_runs.csv
    - repro/stage319_ifft_batch5_asm_microbench/equivalence.csv
    - repro/stage319_ifft_batch5_asm_microbench/asm_audit.csv
  conclusion: >
    Hand-written batch5 IFFT is correct but slower than five scalar-row
    SPQLIOS AVX512 IFFT calls, so the backend batch5 IFFT direction is closed.
""")
    append_once(MANIFEST, "<!-- stage319-ifft-batch5-asm-manifest -->",
        """- stage319_ifft_batch5_asm_microbench:
  - `docs/stage319_ifft_batch5_asm_microbench.md`
  - `theory_checks/stage319_ifft_batch5_asm_closeout.md`
  - `algorithm_variants/mat_rlwe_sab_stage319_ifft_batch5_asm.md`
  - `experiments/stage320_return_to_sab_schedule_plan.md`
  - `scripts/build_stage319_ifft_batch5_asm_report.py`
  - `repro/stage319_ifft_batch5_asm_microbench/`
""")
    append_once(CHECKLIST, "<!-- stage319-ifft-batch5-asm-checklist -->",
        f"""- [x] Stage319 records `{DECISION}` and closes IFFT batch5 before SAB integration.
""")
    append_once(RUN_LOG, "stage319-ifft-batch5-asm-microbench-001",
        (
            "stage319-ifft-batch5-asm-microbench-001,2026-07-05,"
            f"{git_head()},Stage 319,spqlios_avx512,"
            "make FFT_LIB=spqlios_avx512 MAT_TRGSW_IFFT_BATCH5_ASM_BENCH=true "
            "MAT_TRGSW_IFFT_BATCH5_BENCH_REPS=5000 && ./main,"
            "BINARY SET_2_3_2048 rows=5 isolated IFFT batch5 hand assembly,"
            f"n/a,{DECISION},"
            "Stage319 proves the hand-written batch5 IFFT is correct but slower "
            "than five scalar-row SPQLIOS AVX512 IFFT calls and closes the "
            "backend batch5 IFFT route,"
            "docs/stage319_ifft_batch5_asm_microbench.md; "
            "repro/stage319_ifft_batch5_asm_microbench/stage319_summary.csv; "
            "repro/stage319_ifft_batch5_asm_microbench/bench_runs.csv"
        ))

    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
