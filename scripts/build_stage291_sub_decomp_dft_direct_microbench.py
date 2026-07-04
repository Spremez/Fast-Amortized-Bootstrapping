#!/usr/bin/env python3
"""Stage291 fused sub-decompose-to-DFT direct microbench gate."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage291_sub_decomp_dft_direct_microbench"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage291_sub_decomp_dft_direct_microbench.md"
THEORY = ROOT / "theory_checks" / "stage291_sub_decomp_dft_direct_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage291_sub_decomp_dft_direct.md"
PLAN = ROOT / "experiments" / "stage291_sub_decomp_dft_direct_plan.md"
RUNNER = ROOT / "scripts" / "run_stage291_sub_decomp_dft_direct_microbench.sh"
BUILDER = ROOT / "scripts" / "build_stage291_sub_decomp_dft_direct_microbench.py"

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
REPORT = OUT / "stage291_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_POSITIVE = "PASS_STAGE291_SUB_DECOMP_DFT_DIRECT_MICRO_POSITIVE_FULL_SAB_REQUIRED"
DECISION_NEUTRAL = "NEUTRAL_STAGE291_SUB_DECOMP_DFT_DIRECT_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE291_SUB_DECOMP_DFT_DIRECT_CORRECTNESS"


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


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_log(path: Path, variant: str, run_idx: int) -> Dict[str, object]:
    text = read_text(path)
    correctness = re.search(
        r"MAT_SUB_DFT correctness r=(?P<r>\d+) N=(?P<N>\d+) "
        r"max_abs_diff=(?P<max_abs_diff>\S+) status=(?P<status>\w+)",
        text,
    )
    bench = re.search(
        r"MAT_SUB_DFT bench r=(?P<r>\d+) N=(?P<N>\d+) reps=(?P<reps>\d+) "
        r"separate_avg_us=(?P<separate>\S+) sub_avg_us=(?P<sub>\S+) "
        r"speedup_vs_separate=(?P<speedup>\S+)x checksum=(?P<checksum>\S+)",
        text,
    )
    if correctness is None or bench is None:
        return {"variant": variant, "run": run_idx, "status": "MISSING_OUTPUT", "source_log": rel(path)}
    return {
        "variant": variant,
        "run": run_idx,
        "status": correctness.group("status"),
        "r": correctness.group("r"),
        "N": correctness.group("N"),
        "reps": bench.group("reps"),
        "max_abs_diff": correctness.group("max_abs_diff"),
        "separate_avg_us": bench.group("separate"),
        "sub_avg_us": bench.group("sub"),
        "speedup_vs_separate": bench.group("speedup"),
        "checksum": bench.group("checksum"),
        "source_log": rel(path),
    }


def target_smoke_status() -> str:
    path = RAW / "direct_target_smoke" / "run.log"
    if not path.exists():
        return "MISSING"
    text = read_text(path)
    if "SAB_PVW target full bootstrap gate: Pass" in text:
        return "PASS"
    if "Fail" in text:
        return "FAIL"
    return "UNKNOWN"


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
    run_rows: List[Dict[str, object]] = []
    for variant in ["baseline_sub_decomp", "direct_sub_decomp_dft"]:
        for idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
            run_rows.append(parse_log(path, variant, idx))
    fields = [
        "variant", "run", "status", "r", "N", "reps", "max_abs_diff",
        "separate_avg_us", "sub_avg_us", "speedup_vs_separate", "checksum",
        "source_log",
    ]
    write_csv(RUN_METRICS, fields, run_rows)

    by_variant = {
        variant: [row for row in run_rows if row.get("variant") == variant and row.get("status") == "Pass"]
        for variant in ["baseline_sub_decomp", "direct_sub_decomp_dft"]
    }
    baseline = by_variant["baseline_sub_decomp"]
    direct = by_variant["direct_sub_decomp_dft"]
    all_correct = len(baseline) > 0 and len(baseline) == len(direct)
    baseline_sub = [fnum(row.get("sub_avg_us")) for row in baseline]
    direct_sub = [fnum(row.get("sub_avg_us")) for row in direct]
    paired = [
        baseline_sub[idx] / direct_sub[idx]
        for idx in range(min(len(baseline_sub), len(direct_sub)))
        if direct_sub[idx] > 0.0
    ]
    mean_ratio = mean(paired) if paired else 0.0
    min_ratio = min(paired) if paired else 0.0
    max_ratio = max(paired) if paired else 0.0
    target_status = target_smoke_status()

    decision = DECISION_FAIL
    if all_correct and target_status == "PASS" and min_ratio >= 1.02:
        decision = DECISION_POSITIVE
    elif all_correct:
        decision = DECISION_NEUTRAL

    summary_rows = [{
        "decision": decision,
        "runs_per_variant": len(baseline),
        "target_smoke": target_status,
        "baseline_sub_avg_us_mean": f"{mean(baseline_sub):.6f}" if baseline_sub else "0.000000",
        "direct_sub_avg_us_mean": f"{mean(direct_sub):.6f}" if direct_sub else "0.000000",
        "direct_vs_baseline_speedup_mean": f"{mean_ratio:.6f}",
        "direct_vs_baseline_speedup_min": f"{min_ratio:.6f}",
        "direct_vs_baseline_speedup_max": f"{max_ratio:.6f}",
        "claim": "microbench_and_correctness_only_full_sab_required",
    }]
    write_csv(
        SUMMARY,
        [
            "decision", "runs_per_variant", "target_smoke",
            "baseline_sub_avg_us_mean", "direct_sub_avg_us_mean",
            "direct_vs_baseline_speedup_mean",
            "direct_vs_baseline_speedup_min",
            "direct_vs_baseline_speedup_max", "claim",
        ],
        summary_rows,
    )

    proof_rows = [
        {"gate": "G1_runs", "status": "PASS" if len(baseline) == len(direct) and len(baseline) > 0 else "FAIL", "metric": "paired runs", "value": f"{len(baseline)}/{len(direct)}", "interpretation": "Both variants need paired repeated runs."},
        {"gate": "G2_micro_correctness", "status": "PASS" if all_correct else "FAIL", "metric": "all MAT_SUB_DFT runs", "value": f"baseline={len(baseline)} direct={len(direct)}", "interpretation": "Sub-DTF output must equal separate sub+MAT-EP reference."},
        {"gate": "G3_target_correctness", "status": target_status, "metric": "SAB_PVW target smoke", "value": target_status, "interpretation": "Direct fused path must preserve target full bootstrap correctness before full-SAB A/B."},
        {"gate": "G4_microbench", "status": "PASS" if min_ratio >= 1.02 else "NO_PROMOTION", "metric": "paired min direct/baseline speedup", "value": f"{min_ratio:.6f}", "interpretation": "Every paired run must clear 1.02x before full-SAB A/B."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "claim scope", "value": "microbench only", "interpretation": "Positive Stage291 admits full-SAB A/B; it is not a bootstrap speed claim."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls whether Stage292 full-SAB A/B is opened."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)

    next_task = "Run repeated complete-SAB T_bootstrap/r A/B with MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true." if decision == DECISION_POSITIVE else "Do not run full-SAB A/B; redesign candidate or collect stronger isolated evidence."
    write_csv(
        NEXT,
        ["priority", "stage", "input", "task", "gate"],
        [{
            "priority": "P0",
            "stage": "stage292_sub_decomp_dft_direct_full_sab_ab",
            "input": decision,
            "task": next_task,
            "gate": "same-backend repeated full-SAB correctness/performance; then noise/resource if positive",
        }],
    )

    report = f"""# Stage291 Sub-Decompose Direct-DFT Microbench

Decision: `{decision}`.

Stage291 tests `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT`, a default-off path that fuses
the dominant SAB `mat_trgsw_mul_pvmtmlwe_sub_DFT` lifecycle:
`sub_decompose -> torus scratch -> torus_to_double -> ifft` becomes
`sub_decompose_to_double -> ifft` for each MAT row.

| metric | value |
|---|---:|
| paired runs | {len(baseline)} |
| target smoke | {target_status} |
| baseline sub avg us | {summary_rows[0]['baseline_sub_avg_us_mean']} |
| direct sub avg us | {summary_rows[0]['direct_sub_avg_us_mean']} |
| direct/baseline speedup mean | {summary_rows[0]['direct_vs_baseline_speedup_mean']}x |
| direct/baseline speedup min | {summary_rows[0]['direct_vs_baseline_speedup_min']}x |
| direct/baseline speedup max | {summary_rows[0]['direct_vs_baseline_speedup_max']}x |

This is not a full-SAB speed claim. A positive decision only opens Stage292
complete bootstrapping A/B under the primary endpoint `T_bootstrap/r`.

## Proof Gate

| gate | status | value |
|---|---|---|
"""
    for row in proof_rows:
        report += f"| {row['gate']} | {row['status']} | {row['value']} |\n"
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage291 Sub-Decompose Direct-DFT Model

Stage288 measured MAT EP split time dominated by `torus_to_dft` and dense
multiply, with decompose still material. The selected SAB path has many more
`sub` MAT EP calls than normal calls. The direct-DFT candidate targets only
`mat_trgsw_mul_pvmtmlwe_sub_DFT`.

For each row, the old path writes a TorusPolynomial decomposition and then
reads it back to convert to the SPQLIOS reverse-FFT double buffer. The new path
computes the same signed decomposition digits directly as doubles and applies
`ifft` in place. It preserves the external-product algebra and should reduce
one torus write/read lifecycle per row. The FFT arithmetic and dense MAT
multiply are unchanged, so any benefit is bounded by the decompose+conversion
share of sub-DTF calls.
""")
    write_text(VARIANT, f"""# Stage291 MAT_TRGSW_SUB_DECOMP_DFT_DIRECT

Flag: `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true`.

Decision: `{decision}`.

This is a default-off implementation candidate for the SAB sub-DTF hot path.
It does not change scalar SAB and does not alter selector semantics. It may
enter a full-SAB `T_bootstrap/r` benchmark only after this isolated gate passes.
""")
    write_text(PLAN, """# Stage291 Sub-Decompose Direct-DFT Plan

1. Compare baseline `mat_trgsw_mul_pvmtmlwe_sub_DFT` with direct-DFT variant.
2. For every run, verify equality against separate `pvmtmlwe_sub` plus normal
   MAT external product.
3. Require target full-bootstrap correctness smoke for the direct variant.
4. Promote to Stage292 only if paired min direct/baseline speedup is >= 1.02x.
""")
    write_text(COMMANDS, """# Stage291 Reproduction Commands

```bash
STAGE291_RUNS=5 STAGE291_REPS=5000 FFT_LIB=spqlios_avx512 \\
  bash scripts/run_stage291_sub_decomp_dft_direct_microbench.sh
python3 scripts/build_stage291_sub_decomp_dft_direct_microbench.py
```
""")

    append_once(GOAL, "<!-- stage291-sub-decomp-dft-direct-microbench -->", f"""
<!-- stage291-sub-decomp-dft-direct-microbench -->
### Stage291 sub-decompose direct-DFT microbench

`{decision}` tests a default-off fused `sub_decompose_to_double -> ifft` path
for the dominant MAT-SAB sub-DTF calls. It records paired isolated microbench
evidence and target correctness smoke; full SAB `T_bootstrap/r` claims remain
gated behind Stage292.
""")
    append_once(HYPOTHESES, "H10_stage291_sub_decomp_dft_direct_microbench:", f"""
H10_stage291_sub_decomp_dft_direct_microbench:
  status: {decision}
  evidence:
    - repro/stage291_sub_decomp_dft_direct_microbench/run_metrics.csv
    - repro/stage291_sub_decomp_dft_direct_microbench/bench_summary.csv
    - repro/stage291_sub_decomp_dft_direct_microbench/proof_gate.csv
    - docs/stage291_sub_decomp_dft_direct_microbench.md
  conclusion: >
    Stage291 implements and tests a default-off direct DFT path for
    sub-decompose MAT external products. It can only open a full-SAB A/B gate;
    it is not by itself a complete bootstrapping speedup claim.
""")
    append_once(MANIFEST, "- stage291_sub_decomp_dft_direct_microbench:", """
- stage291_sub_decomp_dft_direct_microbench:
  - `docs/stage291_sub_decomp_dft_direct_microbench.md`
  - `theory_checks/stage291_sub_decomp_dft_direct_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage291_sub_decomp_dft_direct.md`
  - `experiments/stage291_sub_decomp_dft_direct_plan.md`
  - `scripts/run_stage291_sub_decomp_dft_direct_microbench.sh`
  - `scripts/build_stage291_sub_decomp_dft_direct_microbench.py`
  - `repro/stage291_sub_decomp_dft_direct_microbench/`
""")
    append_once(CHECKLIST, "<!-- stage291-sub-decomp-dft-direct-microbench-checklist -->", f"""
<!-- stage291-sub-decomp-dft-direct-microbench-checklist -->
- [x] Stage291 records `{decision}` for the sub-decompose direct-DFT candidate.
""")
    append_run_log({
        "run_id": "stage291-sub-decomp-dft-direct-microbench-001",
        "date": "2026-07-04",
        "git_ref": git_head(),
        "stage": "Stage291",
        "backend": "spqlios_avx512",
        "command": "STAGE291_RUNS=5 STAGE291_REPS=5000 FFT_LIB=spqlios_avx512 bash scripts/run_stage291_sub_decomp_dft_direct_microbench.sh",
        "parameters": "r=4; N=2048; sub_decompose direct DFT; target correctness smoke",
        "rng": "default-rng",
        "status": decision,
        "notes": "Microbench plus correctness only; full-SAB A/B required for bootstrap speed claim.",
        "artifacts": "docs/stage291_sub_decomp_dft_direct_microbench.md; repro/stage291_sub_decomp_dft_direct_microbench/",
    })

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, RUNNER, BUILDER, RUN_METRICS, SUMMARY,
        PROOF, NEXT, COMMANDS, REPORT, RAW / "variant_plan.csv",
    ]
    artifacts.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(artifacts)
    print(decision)


if __name__ == "__main__":
    main()
