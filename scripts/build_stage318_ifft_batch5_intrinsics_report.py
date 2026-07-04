#!/usr/bin/env python3
"""Build Stage318 IFFT batch5 intrinsics microbench artifacts."""

from __future__ import annotations

import csv
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage318_ifft_batch5_intrinsics_microbench"
LOG = OUT / "batch5_run_5000_001.log"
OBJDUMP = OUT / "ifft_batch5_tile32_objdump.txt"
LINE_COUNT = OUT / "objdump_line_count.txt"

DOC = ROOT / "docs" / "stage318_ifft_batch5_intrinsics_microbench.md"
THEORY = ROOT / "theory_checks" / "stage318_ifft_batch5_intrinsics_gap.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage318_ifft_batch5_intrinsics.md"
PLAN = ROOT / "experiments" / "stage318_ifft_batch5_intrinsics_plan.md"

SUMMARY = OUT / "stage318_summary.csv"
RUNS = OUT / "bench_runs.csv"
EQUIV = OUT / "equivalence.csv"
ASM = OUT / "asm_audit.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage318_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION = "FAIL_STAGE318_INTRINSIC_BATCH5_CORRECT_BUT_SLOW_BLOCK_SAB_INTEGRATION"
NEXT_STAGE = "stage319_handwritten_ifft_batch5_tile32_asm_or_close_backend"
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


def parse_log() -> tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    text = read_text(LOG)
    equiv_re = re.compile(
        r"MAT_IFFT_BATCH5 equivalence rows=(?P<rows>\d+) N=(?P<N>\d+) "
        r"bit_mismatches=(?P<mismatches>\d+) max_abs=(?P<max_abs>[-+0-9.eE]+)"
    )
    bench_re = re.compile(
        r"MAT_IFFT_BATCH5 bench rows=(?P<rows>\d+) N=(?P<N>\d+) "
        r"reps=(?P<reps>\d+) copy_avg_us=(?P<copy>[-+0-9.eE]+) "
        r"scalar_ifft_est_avg_us=(?P<scalar>[-+0-9.eE]+) "
        r"batch_ifft_est_avg_us=(?P<batch>[-+0-9.eE]+) "
        r"speedup=(?P<speedup>[-+0-9.eE]+) reduction=(?P<reduction>[-+0-9.eE]+)"
    )
    equiv_rows: List[Dict[str, object]] = []
    bench_rows: List[Dict[str, object]] = []
    equiv_idx = 0
    bench_idx = 0
    for line in text.splitlines():
        eq = equiv_re.search(line)
        if eq:
            equiv_idx += 1
            equiv_rows.append(
                {
                    "sample": equiv_idx,
                    "rows": int(eq.group("rows")),
                    "N": int(eq.group("N")),
                    "bit_mismatches": int(eq.group("mismatches")),
                    "max_abs": float(eq.group("max_abs")),
                }
            )
        bm = bench_re.search(line)
        if bm:
            bench_idx += 1
            scalar = float(bm.group("scalar"))
            batch = float(bm.group("batch"))
            bench_rows.append(
                {
                    "sample": bench_idx,
                    "rows": int(bm.group("rows")),
                    "N": int(bm.group("N")),
                    "reps": int(bm.group("reps")),
                    "copy_avg_us": float(bm.group("copy")),
                    "scalar_ifft_est_avg_us": scalar,
                    "batch_ifft_est_avg_us": batch,
                    "speedup": float(bm.group("speedup")),
                    "reduction": float(bm.group("reduction")),
                }
            )
    return equiv_rows, bench_rows


def asm_audit_rows() -> List[Dict[str, object]]:
    text = read_text(OBJDUMP)
    line_count_text = read_text(LINE_COUNT).strip()
    try:
        line_count = int(line_count_text.splitlines()[0])
    except Exception:
        line_count = len(text.splitlines())
    rsp_refs = len(re.findall(r"\[rsp|\[rbp", text))
    high_zmm_refs = len(re.findall(r"zmm(?:1[6-9]|2[0-9]|3[0-1])", text))
    vzeroall_refs = len(re.findall(r"\bvzeroall\b", text))
    vzeroupper_refs = len(re.findall(r"\bvzeroupper\b", text))
    call_refs = len(re.findall(r"\bcall", text))
    return [
        {
            "artifact": rel(OBJDUMP),
            "line_count": line_count,
            "rsp_or_rbp_refs": rsp_refs,
            "high_zmm16_31_refs": high_zmm_refs,
            "vzeroall_refs": vzeroall_refs,
            "vzeroupper_refs": vzeroupper_refs,
            "call_refs": call_refs,
            "interpretation": (
                "Compiler-generated intrinsics code is long, uses stack loop "
                "state, and does not use zmm16-zmm31; hand assembly remains "
                "required for the Stage317 tile32 model."
            ),
        }
    ]


def mean(values: List[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def main() -> int:
    if not LOG.exists() or not OBJDUMP.exists():
        print("missing Stage318 raw log or objdump")
        return 1

    equiv_rows, bench_rows = parse_log()
    asm_rows = asm_audit_rows()
    if not equiv_rows or not bench_rows:
        print("failed to parse Stage318 raw log")
        return 1

    speedups = [float(row["speedup"]) for row in bench_rows]
    reductions = [float(row["reduction"]) for row in bench_rows]
    mismatches = [int(row["bit_mismatches"]) for row in equiv_rows]
    max_abs_values = [float(row["max_abs"]) for row in equiv_rows]
    summary_rows = [
        {
            "decision": DECISION,
            "samples": len(bench_rows),
            "max_bit_mismatches": max(mismatches),
            "max_abs": f"{max(max_abs_values):.17g}",
            "mean_speedup": f"{mean(speedups):.6f}",
            "min_speedup": f"{min(speedups):.6f}",
            "max_speedup": f"{max(speedups):.6f}",
            "mean_reduction": f"{mean(reductions):.6f}",
            "required_reduction": f"{REQUIRED_REDUCTION:.6f}",
            "next_stage": NEXT_STAGE,
        }
    ]

    write_csv(
        RUNS,
        bench_rows,
        [
            "sample",
            "rows",
            "N",
            "reps",
            "copy_avg_us",
            "scalar_ifft_est_avg_us",
            "batch_ifft_est_avg_us",
            "speedup",
            "reduction",
        ],
    )
    write_csv(EQUIV, equiv_rows, ["sample", "rows", "N", "bit_mismatches", "max_abs"])
    write_csv(
        ASM,
        asm_rows,
        [
            "artifact",
            "line_count",
            "rsp_or_rbp_refs",
            "high_zmm16_31_refs",
            "vzeroall_refs",
            "vzeroupper_refs",
            "call_refs",
            "interpretation",
        ],
    )
    write_csv(
        SUMMARY,
        summary_rows,
        [
            "decision",
            "samples",
            "max_bit_mismatches",
            "max_abs",
            "mean_speedup",
            "min_speedup",
            "max_speedup",
            "mean_reduction",
            "required_reduction",
            "next_stage",
        ],
    )
    proof_rows = [
        {
            "gate": "G1_build",
            "status": "PASS",
            "metric": "WSL spqlios_avx512 build",
            "value": "make succeeded",
            "interpretation": "The isolated candidate is buildable on the Linux performance platform.",
        },
        {
            "gate": "G2_equivalence",
            "status": "PASS",
            "metric": "max bit mismatches",
            "value": max(mismatches),
            "interpretation": "Batch5 output is bit-identical to five existing IFFT calls.",
        },
        {
            "gate": "G3_performance",
            "status": "FAIL",
            "metric": "mean isolated IFFT reduction vs required",
            "value": f"{mean(reductions):.6f};{REQUIRED_REDUCTION:.6f}",
            "interpretation": "The intrinsics implementation is slower than the scalar assembly baseline.",
        },
        {
            "gate": "G4_no_sab_integration",
            "status": "PASS_BLOCKED",
            "metric": "policy",
            "value": "no SAB hot path integration",
            "interpretation": "The candidate is not promoted to MAT/SAB.",
        },
        {
            "gate": "G5_next",
            "status": DECISION,
            "metric": "stage decision",
            "value": NEXT_STAGE,
            "interpretation": "Only a hand-written tile32 assembly attempt remains admissible for this backend direction.",
        },
    ]
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(
        NEXT,
        [
            {
                "priority": "P0",
                "stage": NEXT_STAGE,
                "input": DECISION,
                "task": "Either implement a hand-written SPQLIOS AVX512 tile3+tile2 ifft_batch5 assembly microbench or close the backend IFFT direction.",
                "gate": "bit-identical rows and >= 0.107769 isolated IFFT reduction before any SAB integration",
            }
        ],
        ["priority", "stage", "input", "task", "gate"],
    )
    write_text(
        COMMANDS,
        """# Stage318 Reproduction Commands

```sh
make FFT_LIB=spqlios_avx512 MAT_TRGSW_IFFT_BATCH5_BENCH=true MAT_TRGSW_IFFT_BATCH5_BENCH_REPS=5000
./main
objdump -d -Mintel --disassemble=ifft_batch5_tile32 build/spqlios-fft-impl-avx512.o
```

Official Stage318 timing evidence uses WSL/Linux.  Windows MinGW AVX512 builds
are treated as unsupported proxy evidence for this stage.
""",
    )
    artifact_rows = [
        {"artifact": rel(path), "role": role}
        for path, role in [
            (SUMMARY, "decision summary"),
            (RUNS, "parsed repeated bench runs"),
            (EQUIV, "bit-equivalence results"),
            (ASM, "assembly audit counters"),
            (PROOF, "stage gate"),
            (NEXT, "next-stage queue"),
            (LOG, "raw bench log"),
            (OBJDUMP, "raw objdump"),
            (DOC, "human-readable stage report"),
            (THEORY, "theory gap note"),
            (VARIANT, "algorithm variant card"),
            (PLAN, "next experiment plan"),
        ]
    ]
    write_csv(ARTIFACT, artifact_rows, ["artifact", "role"])

    summary = summary_rows[0]
    report = f"""# Stage318 IFFT Batch5 Intrinsics Microbench

Decision: `{DECISION}`.

Stage318 implements an isolated AVX512-intrinsics `ifft_batch5_tile32`
candidate and compares it with five calls to the existing hand-written
SPQLIOS AVX512 `ifft`.  The candidate is correct but slower, so it is blocked
from MAT/SAB integration.

## Summary

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

## Interpretation

The mathematical transform is unchanged and bit-identical.  The performance
gate fails because the compiler-generated C/intrinsics schedule does not
match the Stage317 hand-scheduled tile32 model.  It uses stack-resident loop
state and no zmm16-zmm31 registers, while the baseline is a compact
hand-written single-row assembly routine.

This result is useful because it prevents premature SAB integration.  A
complete SAB `T_bootstrap/r` claim still requires an isolated IFFT candidate
that first clears the component gate.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(
        THEORY,
        f"""# Stage318 Intrinsics Gap

Stage317 predicted a possible IFFT component reduction of about 0.120000 in
the trig-loading regions, with a required measured component reduction of
{REQUIRED_REDUCTION:.6f}.  Stage318 shows that simply expressing the tile3+tile2
schedule in C intrinsics is insufficient.

Observed repeated-run mean speedup is {summary['mean_speedup']}, with mean
reduction {summary['mean_reduction']}.  The gap is not mathematical: the output
is bit-identical.  The gap is implementation-level scheduling.  The generated
function has {asm_rows[0]['line_count']} objdump lines, {asm_rows[0]['rsp_or_rbp_refs']}
stack-frame references, and {asm_rows[0]['high_zmm16_31_refs']} references to
zmm16-zmm31.

Conclusion: for this backend direction, the next admissible optimization is
hand-written assembly that explicitly controls register allocation and loop
shape, or the backend IFFT direction should be closed as not worth further
complexity.
""",
    )
    write_text(
        VARIANT,
        f"""# Stage318 Candidate: Intrinsics `ifft_batch5_tile32`

Status: `{DECISION}`.

The candidate computes:

```text
forall row in 0..4: out[row] = IFFT(row)
```

It changes only the backend schedule by batching five independent rows and
sharing trig-table vectors across row tiles.  Correctness passes with zero
bit mismatches, but performance fails against five existing hand-written
SPQLIOS AVX512 `ifft` calls.

Promotion is forbidden.  The candidate remains a negative ablation for the
paper trail: MAT/RLWE row batching is not automatically faster unless the
backend schedule is implemented at assembly quality.
""",
    )
    write_text(
        PLAN,
        f"""# Stage319 Plan

Input decision: `{DECISION}`.

1. Do not connect `ifft_batch5_tile32` to `mat_trgsw_sub_decompose_DFT_direct`.
2. Either implement a hand-written SPQLIOS AVX512 tile3+tile2 batch5 routine
   or close the backend IFFT direction.
3. Required gate remains bit-identical output and >= {REQUIRED_REDUCTION:.6f}
   isolated IFFT component reduction.
4. If Stage319 fails, return to schedule-level SAB/MAT optimizations with
   complete `T_bootstrap/r` as the primary metric.
""",
    )

    append_once(
        GOAL,
        "<!-- stage318-ifft-batch5-intrinsics-microbench -->",
        f"""### Stage318 IFFT batch5 intrinsics microbench

`{DECISION}`: the isolated intrinsics batch5 IFFT is bit-identical but slower
than five existing SPQLIOS AVX512 `ifft` calls, so SAB integration remains
blocked.
""",
    )
    append_once(
        ROADMAP,
        "<!-- stage318-ifft-batch5-intrinsics-roadmap -->",
        f"""## Stage 318: IFFT Batch5 Intrinsics Microbench

Goal: test the Stage317 tile3+tile2 candidate as an isolated AVX512 intrinsics
implementation.

Status: `{DECISION}`.
""",
    )
    append_once(
        HYPOTHESES,
        "H318_ifft_batch5_intrinsics_microbench:",
        f"""H318_ifft_batch5_intrinsics_microbench:
  status: {DECISION}
  primary_metric: isolated_ifft_component_reduction
  evidence:
    - repro/stage318_ifft_batch5_intrinsics_microbench/stage318_summary.csv
    - repro/stage318_ifft_batch5_intrinsics_microbench/bench_runs.csv
    - repro/stage318_ifft_batch5_intrinsics_microbench/equivalence.csv
    - repro/stage318_ifft_batch5_intrinsics_microbench/asm_audit.csv
  conclusion: >
    The intrinsics implementation is bit-identical but slower than the
    existing hand-written scalar-row SPQLIOS AVX512 IFFT, so it is not
    integrated into MAT/SAB.
""",
    )
    append_once(
        MANIFEST,
        "<!-- stage318-ifft-batch5-intrinsics-manifest -->",
        """- stage318_ifft_batch5_intrinsics_microbench:
  - `docs/stage318_ifft_batch5_intrinsics_microbench.md`
  - `theory_checks/stage318_ifft_batch5_intrinsics_gap.md`
  - `algorithm_variants/mat_rlwe_sab_stage318_ifft_batch5_intrinsics.md`
  - `experiments/stage318_ifft_batch5_intrinsics_plan.md`
  - `scripts/build_stage318_ifft_batch5_intrinsics_report.py`
  - `repro/stage318_ifft_batch5_intrinsics_microbench/`
""",
    )
    append_once(
        CHECKLIST,
        "<!-- stage318-ifft-batch5-intrinsics-checklist -->",
        f"""- [x] Stage318 records `{DECISION}` and blocks SAB integration for the
  intrinsics candidate.
""",
    )
    append_once(
        RUN_LOG,
        "stage318-ifft-batch5-intrinsics-microbench-001",
        (
            "stage318-ifft-batch5-intrinsics-microbench-001,2026-07-05,"
            f"{git_head()},Stage 318,spqlios_avx512,"
            "make FFT_LIB=spqlios_avx512 MAT_TRGSW_IFFT_BATCH5_BENCH=true "
            "MAT_TRGSW_IFFT_BATCH5_BENCH_REPS=5000 && ./main,"
            "BINARY SET_2_3_2048 rows=5 isolated IFFT batch5 intrinsics,"
            f"n/a,{DECISION},"
            "Stage318 proves the intrinsics batch5 IFFT is correct but slower "
            "than five scalar-row SPQLIOS AVX512 IFFT calls and must not be "
            "integrated into SAB,"
            "docs/stage318_ifft_batch5_intrinsics_microbench.md; "
            "repro/stage318_ifft_batch5_intrinsics_microbench/stage318_summary.csv; "
            "repro/stage318_ifft_batch5_intrinsics_microbench/bench_runs.csv"
        ),
    )

    print(DECISION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
