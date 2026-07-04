#!/usr/bin/env python3
"""Stage294: target-size nonbinary final-output noise for direct DFT."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage294_direct_dft_target_noise"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage294_direct_dft_target_noise.md"
THEORY = ROOT / "theory_checks" / "stage294_direct_dft_target_noise_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage294_direct_dft_target_noise.md"
PLAN = ROOT / "experiments" / "stage294_direct_dft_target_noise_plan.md"
RUNNER = ROOT / "scripts" / "run_stage294_direct_dft_target_noise.sh"
BUILDER = ROOT / "scripts" / "build_stage294_direct_dft_target_noise.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SUMMARY = OUT / "target_noise_summary.csv"
LANES = OUT / "target_noise_lanes.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage294_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE294_DIRECT_DFT_TARGET_NOISE_FINAL_OUTPUT"
DECISION_FAIL = "FAIL_STAGE294_DIRECT_DFT_TARGET_NOISE"

SUMMARY_RE = re.compile(
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
LANE_RE = re.compile(
    r"SAB_PVW_NONBINARY_TARGET_NOISE lane target_full mode=(?P<mode>\S+) "
    r"r=(?P<r>\d+) lane=(?P<lane>\d+) trials=(?P<trials>\d+) "
    r"expected_model_pvw_failures=(?P<expected_model_pvw_failures>\d+) "
    r"expected_model_scalar_failures=(?P<expected_model_scalar_failures>\d+) "
    r"pair_failures=(?P<pair_failures>\d+) "
    r"expected_model_pvw_log2_sigma_torus=(?P<expected_model_pvw_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"expected_model_scalar_log2_sigma_torus=(?P<expected_model_scalar_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>-?inf|-?[0-9.]+)"
)
OVERALL_GATE_RE = re.compile(r"SAB_PVW_NONBINARY_TARGET_NOISE target full final-output gate: (?P<overall_gate>Pass|Fail)")
TIME_RSS_RE = re.compile(r"Maximum resident set size \(kbytes\): (?P<time_maxrss_kb>\d+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in text.strip().splitlines()) + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def append_run_log(row: Dict[str, str]) -> None:
    current = read_text(RUN_LOG)
    if row["run_id"] in current:
        return
    with RUN_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["run_id", "date", "git_ref", "stage", "backend", "command", "parameters", "rng", "status", "notes", "artifacts"],
            lineterminator="\n",
        )
        writer.writerow(row)


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def md_table(rows: List[Dict[str, object]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


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
    run_log = RAW / "direct_dft_target_noise" / "run.log"
    time_log = RAW / "direct_dft_target_noise" / "time.log"
    text = read_text(run_log)
    time_text = read_text(time_log)

    summary_match = SUMMARY_RE.search(text)
    overall_match = OVERALL_GATE_RE.search(text)
    summary: Dict[str, object] = {
        "variant": "direct_dft_target_noise",
        "source_run_log": rel(run_log),
        "source_time_log": rel(time_log),
    }
    if summary_match:
        summary.update(summary_match.groupdict())
    if overall_match:
        summary["overall_gate"] = overall_match.group("overall_gate")
    time_match = TIME_RSS_RE.search(time_text)
    if time_match:
        summary.update(time_match.groupdict())

    lane_rows = []
    for lane_match in LANE_RE.finditer(text):
        row = lane_match.groupdict()
        row["source_run_log"] = rel(run_log)
        lane_rows.append(row)

    failures = int(summary.get("pair_failures", "1") or "1")
    stage292_ok = "PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED" in read_text(
        ROOT / "repro" / "stage292_fullsab_direct_dft_ab" / "proof_gate.csv"
    )
    stage293_ok = "PASS_STAGE293_DIRECT_DFT_TARGET_CORRECT_RESOURCE_SMOKE_NOISE_PENDING" in read_text(
        ROOT / "repro" / "stage293_direct_dft_noise_resource" / "proof_gate.csv"
    )
    pass_gate = summary.get("gate") == "Pass" and summary.get("overall_gate") == "Pass" and failures == 0
    decision = DECISION_PASS if stage292_ok and stage293_ok and pass_gate else DECISION_FAIL
    summary["decision"] = decision
    summary["stage292_input"] = "PASS" if stage292_ok else "FAIL"
    summary["stage293_input"] = "PASS" if stage293_ok else "FAIL"

    write_csv(SUMMARY, [
        "variant", "mode", "r", "trials", "points",
        "expected_model_pvw_failures", "expected_model_scalar_failures",
        "pair_failures", "expected_model_pvw_log2_sigma_torus",
        "expected_model_scalar_log2_sigma_torus", "pair_log2_sigma_torus",
        "pair_log2_max_abs_torus", "gate",
        "overall_gate", "time_maxrss_kb", "stage292_input",
        "stage293_input", "decision", "source_run_log", "source_time_log",
    ], [summary])
    write_csv(LANES, [
        "mode", "r", "lane", "trials", "expected_model_pvw_failures",
        "expected_model_scalar_failures",
        "pair_failures", "expected_model_pvw_log2_sigma_torus",
        "expected_model_scalar_log2_sigma_torus", "pair_log2_sigma_torus",
        "source_run_log",
    ], lane_rows)

    proof_rows = [
        {"gate": "G1_stage292_full_sab", "status": "PASS" if stage292_ok else "FAIL", "metric": "Stage292 full-SAB T/r", "value": "positive" if stage292_ok else "missing", "interpretation": "Noise gate follows a full-SAB positive candidate."},
        {"gate": "G2_stage293_resource", "status": "PASS" if stage293_ok else "FAIL", "metric": "Stage293 target correctness/resource", "value": "pass" if stage293_ok else "missing", "interpretation": "Target correctness/resource smoke must precede stronger noise evidence."},
        {"gate": "G3_pair_failures", "status": "PASS" if failures == 0 else "FAIL", "metric": "PVW/scalar decoded pair failures", "value": str(failures), "interpretation": "Direct DFT output must decode identically to repeated scalar SAB."},
        {"gate": "G4_expected_model_boundary", "status": "INFO", "metric": "expected-model mismatches", "value": f"pvw={summary.get('expected_model_pvw_failures', '')};scalar={summary.get('expected_model_scalar_failures', '')}", "interpretation": "The hand-written LUT model is diagnostic only for nonbinary packing; scalar reference equivalence is the gate."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "scope", "value": "target final-output noise", "interpretation": "This is not stage-wise noise, all-parameter noise, or paper-grade high-stat closure."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Pass supports high-stat refresh and stage-wise repair next."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], [
        {"priority": "P0", "route": "stage295_direct_dft_highstat_perf_noise", "entry_condition": decision, "gate": "Increase repeated T/r and target-noise trials/seeds.", "failure_action": "Keep Stage294 as final-output smoke only."},
        {"priority": "P1", "route": "stage295_stagewise_noise_repair", "entry_condition": decision, "gate": "Add target-size stage-wise nonbinary noise if needed for paper claims.", "failure_action": "Limit claim to final-output noise."},
    ])

    write_text(COMMANDS, """# Stage294 Reproduction Commands

```bash
STAGE294_TRIALS=3 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage294_direct_dft_target_noise.sh
python3 scripts/build_stage294_direct_dft_target_noise.py
```

Primary evidence: target-size include-zero final-output noise for the direct
DFT PVW/MAT-SAB candidate.
""")
    report = f"""# Stage294 Direct DFT Target Final-Output Noise

Decision: `{decision}`.

Stage294 adds a target-size nonbinary/include-zero final-output noise harness
for the Stage292 direct-DFT candidate. This avoids the old `N=16` SPQLIOS
full-noise fixture and checks the actual `SET_2_3_2048`, r=4 path.

## Summary

{md_table([summary], ["variant", "mode", "r", "trials", "points", "expected_model_pvw_failures", "expected_model_scalar_failures", "pair_failures", "pair_log2_sigma_torus", "gate", "overall_gate", "decision"])}

## Lanes

{md_table(lane_rows, ["lane", "trials", "expected_model_pvw_failures", "expected_model_scalar_failures", "pair_failures", "expected_model_pvw_log2_sigma_torus", "expected_model_scalar_log2_sigma_torus", "pair_log2_sigma_torus"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage294 Target Noise Model

The direct-DFT optimization changes the sub-decompose representation path but
not the plaintext LUT semantics, selector schedule, or scalar reference. The
target final-output noise gate therefore compares:

```text
PVW/MAT-SAB direct DFT output lane q
vs repeated scalar SAB output q
vs expected LUT(input)
```

for every coefficient and every body lane. The repeated scalar SAB output is
the correctness reference for the nonbinary packed LUT; the hand-written LUT
model is retained only as a diagnostic because nonbinary packing has additional
encoding semantics. Passing this gate supports scalar-equivalent final-output
correctness/noise for the target slice; it does not prove stage-wise noise or
all-parameter behavior.
""")
    write_text(VARIANT, """# Stage294 Direct DFT Target Noise Variant

Flags:

```text
SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
```

The candidate uses the same selected PVW-SAB flags as Stage292 and checks
include-zero r=4 under `SET_2_3_2048`.
""")
    write_text(PLAN, """# Stage294 Experiment Plan

Goal: close the immediate Stage293 noise gap with a target-size final-output
noise gate.

Correctness/noise gate:

- zero PVW/scalar decoded pair failures;
- pair noise statistics recorded;
- raw logs preserved.

Failure handling: if this fails, direct DFT remains a performance-only
candidate and cannot be promoted.
""")

    append_once(GOAL, "<!-- stage294-direct-dft-target-noise -->", f"""<!-- stage294-direct-dft-target-noise -->
### Stage294 direct DFT target final-output noise

`{decision}` adds a target-size include-zero final-output noise gate for the
Stage292 direct-DFT candidate. The claim remains scoped to target final output;
stage-wise and high-stat noise are still later gates.
""")
    append_once(ROADMAP, "## Stage 294: Direct DFT Target Final-Output Noise", f"""## Stage 294: Direct DFT Target Final-Output Noise

Goal: replace the old N=16 SPQLIOS noise fixture with a target-size
include-zero final-output noise gate for direct DFT.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H294_direct_dft_target_noise:", f"""H294_direct_dft_target_noise:
  status: {decision}
  primary_metric: target_final_output_noise
  evidence:
    - repro/stage294_direct_dft_target_noise/target_noise_summary.csv
    - repro/stage294_direct_dft_target_noise/target_noise_lanes.csv
    - repro/stage294_direct_dft_target_noise/proof_gate.csv
    - docs/stage294_direct_dft_target_noise.md
  conclusion: >
    Direct DFT has target final-output noise evidence for include-zero r=4 if
    Stage294 passes. Stage-wise and high-stat claims remain separate.
""")
    append_once(MANIFEST, "- stage294_direct_dft_target_noise:", """- stage294_direct_dft_target_noise:
  - `docs/stage294_direct_dft_target_noise.md`
  - `scripts/run_stage294_direct_dft_target_noise.sh`
  - `scripts/build_stage294_direct_dft_target_noise.py`
  - `repro/stage294_direct_dft_target_noise/`
""")
    append_once(CHECKLIST, "<!-- stage294-direct-dft-target-noise-checklist -->", f"""<!-- stage294-direct-dft-target-noise-checklist -->
- [x] Stage294 records `{decision}` for direct DFT target final-output noise.
""")
    append_run_log({
        "run_id": "stage294-direct-dft-target-noise-001",
        "date": "2026-07-04",
        "git_ref": git_head(),
        "stage": "Stage 294",
        "backend": "spqlios_avx512-local",
        "command": "STAGE294_TRIALS=3 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage294_direct_dft_target_noise.sh",
        "parameters": "BINARY SET_2_3_2048 r=4 include-zero direct DFT",
        "rng": "n/a",
        "status": decision,
        "notes": "Target final-output noise; stage-wise/high-stat closure remains separate.",
        "artifacts": "docs/stage294_direct_dft_target_noise.md; repro/stage294_direct_dft_target_noise/proof_gate.csv",
    })

    paths = [DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, LANES, PROOF, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)


if __name__ == "__main__":
    main()
