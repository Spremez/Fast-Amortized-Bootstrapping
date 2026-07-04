#!/usr/bin/env python3
"""Build Stage310 IFFT row-scaling benchmark artifacts."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage310_ifft_rows_scaling_bench"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage310_ifft_rows_scaling_bench.md"
THEORY = ROOT / "theory_checks" / "stage310_ifft_rows_scaling_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage310_batched_ifft_candidate.md"
PLAN = ROOT / "experiments" / "stage310_ifft_rows_scaling_bench_plan.md"
RUNNER = ROOT / "scripts" / "run_stage310_ifft_rows_scaling_bench.sh"
BUILDER = ROOT / "scripts" / "build_stage310_ifft_rows_scaling_bench.py"

RUN_METRICS = OUT / "run_metrics.csv"
SUMMARY = OUT / "bench_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage310_report.md"
ARTIFACT = OUT / "artifact_index.csv"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

DECISION_PASS = "PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED"
DECISION_INVESTIGATE = "PASS_STAGE310_IFFT_ROWS_SCALING_CACHE_EFFECT_INVESTIGATE"
DECISION_FAIL = "FAIL_STAGE310_IFFT_ROWS_SCALING_BENCH"

BENCH_RE = re.compile(
    r"MAT_IFFT_ROWS bench rows=(?P<rows>\d+) N=(?P<N>\d+) reps=(?P<reps>\d+) "
    r"copy_avg_us=(?P<copy>\S+) copy_ifft_avg_us=(?P<copy_ifft>\S+) "
    r"ifft_est_avg_us=(?P<ifft_est>\S+) ifft_est_per_row_us=(?P<per_row>\S+) "
    r"checksum=(?P<checksum>\S+)"
)


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


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def parse_log(path: Path) -> Dict[str, object]:
    text = read_text(path)
    match = BENCH_RE.search(text)
    if match is None:
        return {"rows": path.parent.name.replace("rows_", ""), "status": "MISSING_OUTPUT", "source_log": rel(path)}
    return {
        "rows": match.group("rows"),
        "status": "PASS",
        "N": match.group("N"),
        "reps": match.group("reps"),
        "copy_avg_us": match.group("copy"),
        "copy_ifft_avg_us": match.group("copy_ifft"),
        "ifft_est_avg_us": match.group("ifft_est"),
        "ifft_est_per_row_us": match.group("per_row"),
        "checksum": match.group("checksum"),
        "source_log": rel(path),
    }


def row_by_rows(rows: List[Dict[str, object]], count: int) -> Dict[str, object]:
    for row in rows:
        if int(fnum(row.get("rows"))) == count:
            return row
    return {}


def table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def append_run_log(decision: str) -> None:
    run_id = "stage310-ifft-rows-scaling-bench-001"
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
        "stage": "Stage 310",
        "backend": "spqlios_avx512-local",
        "command": "STAGE310_REPS=5000 FFT_LIB=spqlios_avx512 bash scripts/run_stage310_ifft_rows_scaling_bench.sh",
        "config": "rows=1,5,10 direct SPQLIOS ifft row-scaling bench",
        "params": "N=2048; copy-only subtraction; no SAB path change",
        "seed": "deterministic synthetic DFT buffers",
        "status": decision,
        "summary": "Stage310 quantifies whether existing per-row IFFT loop shows enough natural scaling to justify a C-level wrapper.",
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
    run_rows = []
    for path in sorted(RAW.glob("rows_*/run.log")):
        run_rows.append(parse_log(path))
    run_rows = sorted(run_rows, key=lambda row: int(fnum(row.get("rows"))))
    write_csv(RUN_METRICS, run_rows, [
        "rows", "status", "N", "reps", "copy_avg_us", "copy_ifft_avg_us",
        "ifft_est_avg_us", "ifft_est_per_row_us", "checksum", "source_log",
    ])

    all_pass = len(run_rows) >= 3 and all(row.get("status") == "PASS" for row in run_rows)
    one = row_by_rows(run_rows, 1)
    five = row_by_rows(run_rows, 5)
    ten = row_by_rows(run_rows, 10)
    row1 = fnum(one.get("ifft_est_per_row_us"))
    row5 = fnum(five.get("ifft_est_per_row_us"))
    row10 = fnum(ten.get("ifft_est_per_row_us"))
    speedup_5_vs_1 = row1 / row5 if row5 else 0.0
    speedup_10_vs_1 = row1 / row10 if row10 else 0.0
    copy_ok = all(fnum(row.get("copy_ifft_avg_us")) > fnum(row.get("copy_avg_us")) for row in run_rows)
    strong_scaling = speedup_5_vs_1 >= 1.10 and speedup_10_vs_1 >= 1.10
    decision = DECISION_FAIL
    if all_pass and copy_ok and strong_scaling:
        decision = DECISION_INVESTIGATE
    elif all_pass and copy_ok:
        decision = DECISION_PASS

    summary_rows = [{
        "decision": decision,
        "rows_1_ifft_est_per_row_us": f"{row1:.6f}",
        "rows_5_ifft_est_per_row_us": f"{row5:.6f}",
        "rows_10_ifft_est_per_row_us": f"{row10:.6f}",
        "rows5_vs_rows1_per_row_speedup": f"{speedup_5_vs_1:.6f}",
        "rows10_vs_rows1_per_row_speedup": f"{speedup_10_vs_1:.6f}",
        "strong_existing_loop_scaling": "YES" if strong_scaling else "NO",
        "claim": "microbench_backend_route_only_not_full_sab_claim",
    }]
    write_csv(SUMMARY, summary_rows, [
        "decision", "rows_1_ifft_est_per_row_us",
        "rows_5_ifft_est_per_row_us", "rows_10_ifft_est_per_row_us",
        "rows5_vs_rows1_per_row_speedup", "rows10_vs_rows1_per_row_speedup",
        "strong_existing_loop_scaling", "claim",
    ])

    proof = [
        {"gate": "G1_runs", "status": "PASS" if all_pass else "FAIL", "metric": "rows present", "value": ",".join(str(row.get("rows")) for row in run_rows), "interpretation": "Rows 1/5/10 must all produce bench output."},
        {"gate": "G2_copy_subtraction", "status": "PASS" if copy_ok else "FAIL", "metric": "copy_ifft > copy", "value": "PASS" if copy_ok else "FAIL", "interpretation": "Subtracted IFFT estimate must be positive."},
        {"gate": "G3_existing_loop_scaling", "status": "INVESTIGATE" if strong_scaling else "NO_STRONG_SCALING", "metric": "per-row speedup rows5/rows1; rows10/rows1", "value": f"{speedup_5_vs_1:.6f};{speedup_10_vs_1:.6f}", "interpretation": "Strong scaling would justify cache/layout investigation; otherwise C-level wrappers remain weak."},
        {"gate": "G4_claim_boundary", "status": "PASS", "metric": "scope", "value": "ifft microbench only", "interpretation": "This does not change SAB and is not a complete bootstrapping speed claim."},
        {"gate": "G5_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls backend IFFT route."},
    ]
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])

    next_route = "stage311_spqlios_backend_batch_design" if strong_scaling else "stage311_ifft_backend_abi_design_or_stop"
    next_task = "Design a true backend batch IFFT candidate; C-wrapper-only work is insufficient."
    write_csv(NEXT, [{
        "priority": "P0",
        "stage": next_route,
        "input": decision,
        "task": next_task,
        "gate": "new backend API/model/assembly proof before SAB integration",
    }], ["priority", "stage", "input", "task", "gate"])

    report = (
        "# Stage310 IFFT Rows Scaling Bench\n\n"
        f"Decision: `{decision}`.\n\n"
        "Stage310 measures existing SPQLIOS single-row `ifft` under rows=1/5/10 loops. The benchmark subtracts copy-only time from copy+ifft time to avoid repeated transforms on stale buffers.\n\n"
        "## Summary\n\n" + table(summary_rows, [
            "decision", "rows_1_ifft_est_per_row_us",
            "rows_5_ifft_est_per_row_us", "rows_10_ifft_est_per_row_us",
            "rows5_vs_rows1_per_row_speedup", "rows10_vs_rows1_per_row_speedup",
            "strong_existing_loop_scaling",
        ]) +
        "\n\n## Run Metrics\n\n" + table(run_rows, [
            "rows", "N", "reps", "copy_avg_us", "copy_ifft_avg_us",
            "ifft_est_avg_us", "ifft_est_per_row_us",
        ]) +
        "\n\n## Proof Gate\n\n" + table(proof, ["gate", "status", "metric", "value", "interpretation"]) + "\n"
    )
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage310 IFFT Rows Scaling Model

The current direct DFT residual is almost evenly split between digit
materialization and SPQLIOS reverse FFT. Stage308 found no existing batch IFFT
API, so Stage310 measures whether the existing per-row loop already shows
enough sublinear per-row behavior to justify a C-level wrapper or cache-only
optimization.

The benchmark uses deterministic double buffers and records:

```text
ifft_est = time(copy rows + ifft rows) - time(copy rows)
```

This avoids repeatedly applying `ifft` to already-transformed buffers. A strong
C-level scaling signal would require rows=5 and rows=10 to improve per-row time
by at least 1.10x over rows=1. Without that, meaningful improvement requires a
true backend-level batch IFFT API/model/assembly change rather than another
wrapper around the same single-row entry.
""")
    write_text(VARIANT, f"""# Stage310 Batched IFFT Candidate Card

## Summary

- Parent algorithm: PVW/MAT-SAB direct sub-DTF materialization path.
- Focused module: SPQLIOS reverse FFT after digit-to-double materialization.
- Optimization target: lower `T_bootstrap/r` by reducing direct DFT lifecycle time.
- Status labels: `[experimental gate]`, `[backend ABI required]`.
- Main hypothesis: a true batched IFFT backend could improve the Stage307 IFFT
  residual because multiple rows share FFT tables and schedule structure.

## Mathematical Definition

The ciphertext algebra is unchanged. A batch IFFT candidate would replace
independent maps `IFFT(row_i)` for `i in 0..r` with a backend routine
`BatchIFFT(row_0, ..., row_r)` that returns exactly the same DFT-domain rows.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| per-row `ifft(tables, row)` | backend `BatchIFFT(tables, rows)` | implements same transform | Stage310 admits only if backend proof exists |

## Complexity Change

- Time: asymptotically still `(k+r) * IFFT(N)`; possible constant-factor gain only.
- Memory: no key-format change expected; temporary row pointers or backend scratch may grow.
- What must be measured: isolated FFT correctness, per-row IFFT time, complete SAB `T_bootstrap/r`.

## Theory Dependencies

- Inherited assumptions: all external-product algebra and gadget decomposition remain unchanged.
- Proof steps affected: none if each row output is bitwise/numerically equivalent within existing tolerance.
- New lemmas needed: equivalence of backend batch transform to independent row transforms.
- Current status: `{decision}`.

## Required Experiments

- Baselines: current direct DFT path and scalar repeated SAB.
- Metrics: IFFT per-row microbench, direct lifecycle profile, full SAB `T_bootstrap/r`.
- Success criteria: isolated IFFT correctness; component reduction; full SAB speedup with no correctness/noise regression.
- Failure criteria: wrapper-only implementation, no component reduction, or full SAB neutral result.
""")
    write_text(PLAN, """# Stage310 Experiment Plan

1. Build rows=1/5/10 with `MAT_TRGSW_IFFT_ROWS_BENCH=true`.
2. Record copy-only and copy+ifft time.
3. Estimate IFFT time by subtraction.
4. Treat rows=5 and rows=10 per-row speedups >= 1.10x as a signal for backend cache/layout investigation.
5. Otherwise require a true backend batch API/model/assembly before touching SAB.
""")
    write_text(COMMANDS, """# Stage310 Reproduction Commands

```bash
STAGE310_REPS=5000 FFT_LIB=spqlios_avx512 \\
  bash scripts/run_stage310_ifft_rows_scaling_bench.sh
python3 scripts/build_stage310_ifft_rows_scaling_bench.py
```
""")

    append_once(ROADMAP, "## Stage 310: IFFT Rows Scaling Bench", "\n## Stage 310: IFFT Rows Scaling Bench\n\nGoal: measure whether existing single-row SPQLIOS IFFT loops show enough row-scaling to justify C-level wrapper work.\n\n" f"Status: `{decision}`.\n")
    append_once(GOAL, "<!-- stage310-ifft-rows-scaling-bench -->", "\n<!-- stage310-ifft-rows-scaling-bench -->\n### Stage310 IFFT rows scaling bench\n\n" f"`{decision}` records rows=1/5/10 SPQLIOS IFFT scaling and routes any future IFFT acceleration to backend-level work.\n")
    append_once(HYPOTHESES, "H310_ifft_rows_scaling_bench:", "\nH310_ifft_rows_scaling_bench:\n" f"  status: {decision}\n  primary_metric: isolated_spqlios_ifft_per_row_scaling\n  evidence:\n    - repro/stage310_ifft_rows_scaling_bench/run_metrics.csv\n    - repro/stage310_ifft_rows_scaling_bench/bench_summary.csv\n    - repro/stage310_ifft_rows_scaling_bench/proof_gate.csv\n  conclusion: >\n    Stage310 measures whether existing per-row SPQLIOS IFFT loops have strong\n    row scaling. It is not a SAB speed claim; it determines whether future IFFT\n    work must be backend-level.\n")
    append_once(MANIFEST, "- stage310_ifft_rows_scaling_bench:", "\n- stage310_ifft_rows_scaling_bench:\n  - `docs/stage310_ifft_rows_scaling_bench.md`\n  - `theory_checks/stage310_ifft_rows_scaling_model.md`\n  - `algorithm_variants/mat_rlwe_sab_stage310_batched_ifft_candidate.md`\n  - `experiments/stage310_ifft_rows_scaling_bench_plan.md`\n  - `scripts/run_stage310_ifft_rows_scaling_bench.sh`\n  - `scripts/build_stage310_ifft_rows_scaling_bench.py`\n  - `repro/stage310_ifft_rows_scaling_bench/`\n")
    append_once(CHECKLIST, "<!-- stage310-ifft-rows-scaling-bench-checklist -->", "\n<!-- stage310-ifft-rows-scaling-bench-checklist -->\n" f"- [x] Stage310 records `{decision}` for SPQLIOS IFFT row scaling.\n")
    append_run_log(decision)

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, RUN_METRICS, SUMMARY,
        PROOF, NEXT, COMMANDS, REPORT, RAW / "variant_plan.csv",
    ]
    artifacts.extend(sorted(RAW.glob("rows_*/*.log")))
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
