#!/usr/bin/env python3
"""Stage298: target-size include-zero stage-wise noise for direct DFT."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage298_direct_dft_target_stage_noise"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage298_direct_dft_target_stage_noise.md"
THEORY = ROOT / "theory_checks" / "stage298_direct_dft_target_stage_noise_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage298_direct_dft_target_stage_noise.md"
PLAN = ROOT / "experiments" / "stage298_direct_dft_target_stage_noise_plan.md"
RUNNER = ROOT / "scripts" / "run_stage298_direct_dft_target_stage_noise.sh"
BUILDER = ROOT / "scripts" / "build_stage298_direct_dft_target_stage_noise.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SUMMARY = OUT / "stage_summary.csv"
LANES = OUT / "lane_summary.csv"
PROOF = OUT / "proof_gate.csv"
CLAIMS = OUT / "claim_boundary.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage298_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE298_DIRECT_DFT_TARGET_STAGE_NOISE_LOCAL"
DECISION_FAIL = "FAIL_STAGE298_DIRECT_DFT_TARGET_STAGE_NOISE"

STAGES = ["blind_rotate_coeff0", "extract", "materialize_tlwe", "packing_ks", "hw_ks"]
SUMMARY_RE = re.compile(
    r"SAB_PVW_NONBINARY_STAGE_NOISE summary mode=(?P<mode>\S+) "
    r"stage=(?P<stage>\S+) r=(?P<r>\d+) trials=(?P<trials>\d+) "
    r"points=(?P<points>\d+) pair_failures=(?P<pair_failures>\d+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_max_abs_torus=(?P<pair_log2_max_abs_torus>-?inf|-?[0-9.]+)"
)
LANE_RE = re.compile(
    r"SAB_PVW_NONBINARY_STAGE_NOISE lane mode=(?P<mode>\S+) "
    r"stage=(?P<stage>\S+) r=(?P<r>\d+) lane=(?P<lane>\d+) "
    r"trials=(?P<trials>\d+) points=(?P<points>\d+) "
    r"pair_failures=(?P<pair_failures>\d+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>-?inf|-?[0-9.]+) "
    r"pair_log2_max_abs_torus=(?P<pair_log2_max_abs_torus>-?inf|-?[0-9.]+)"
)
MODE_GATE_RE = re.compile(r"SAB_PVW_NONBINARY_TARGET_STAGE_NOISE target full bootstrap stage gate mode=(?P<mode>\S+): (?P<mode_gate>Pass|Fail)")
OVERALL_RE = re.compile(r"SAB_PVW_NONBINARY_TARGET_STAGE_NOISE target full stage gate: (?P<overall_gate>Pass|Fail)")
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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def append_run_log(row: dict[str, str]) -> None:
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


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out)


def artifact_index(paths: list[Path]) -> None:
    rows = []
    for path in paths:
        if path.exists():
            data = path.read_bytes()
            rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, ["path", "bytes", "sha256"], rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    run_log = RAW / "direct_dft" / "run.log"
    time_log = RAW / "direct_dft" / "time.log"
    text = read_text(run_log)
    time_text = read_text(time_log)
    time_match = TIME_RSS_RE.search(time_text)
    mode_gate = MODE_GATE_RE.search(text)
    overall = OVERALL_RE.search(text)

    summary_rows = []
    for match in SUMMARY_RE.finditer(text):
        row = match.groupdict()
        row["variant"] = "direct_dft"
        row["status"] = "pass" if row.get("pair_failures") == "0" else "fail"
        row["source_run_log"] = rel(run_log)
        if time_match:
            row["time_maxrss_kb"] = time_match.group("time_maxrss_kb")
        summary_rows.append(row)
    lane_rows = []
    for match in LANE_RE.finditer(text):
        row = match.groupdict()
        row["variant"] = "direct_dft"
        row["status"] = "pass" if row.get("pair_failures") == "0" else "fail"
        row["source_run_log"] = rel(run_log)
        lane_rows.append(row)

    write_csv(SUMMARY, [
        "variant", "status", "mode", "stage", "r", "trials", "points",
        "pair_failures", "pair_log2_sigma_torus",
        "pair_log2_max_abs_torus", "time_maxrss_kb", "source_run_log",
    ], summary_rows)
    write_csv(LANES, [
        "variant", "status", "mode", "stage", "r", "lane", "trials",
        "points", "pair_failures", "pair_log2_sigma_torus",
        "pair_log2_max_abs_torus", "source_run_log",
    ], lane_rows)

    stage_set = {row.get("stage") for row in summary_rows}
    trials = min((int(row.get("trials", 0)) for row in summary_rows), default=0)
    total_failures = sum(int(row.get("pair_failures", 1)) for row in summary_rows)
    min_sigma = min((fnum(row.get("pair_log2_sigma_torus")) for row in summary_rows), default=0.0)
    max_abs = max((fnum(row.get("pair_log2_max_abs_torus")) for row in summary_rows), default=0.0)
    stage296_ok = "PASS_STAGE296_DIRECT_DFT_HIGHSTAT_LOCAL" in read_text(ROOT / "repro" / "stage296_direct_dft_highstat" / "proof_gate.csv")
    stage297_ok = "PASS_STAGE297_DIRECT_DFT_RESOURCE_SIDECONDITION_LOCAL" in read_text(ROOT / "repro" / "stage297_direct_dft_resource_sidecondition" / "proof_gate.csv")
    stage_count_ok = set(STAGES).issubset(stage_set)
    gate_ok = mode_gate and mode_gate.group("mode_gate") == "Pass" and overall and overall.group("overall_gate") == "Pass"
    local_ok = stage296_ok and stage297_ok and stage_count_ok and trials >= 3 and total_failures == 0 and gate_ok
    decision = DECISION_PASS if local_ok else DECISION_FAIL

    proof_rows = [
        {"gate": "G1_prior_stage296", "status": "PASS" if stage296_ok else "FAIL", "metric": "Stage296 decision", "value": "positive" if stage296_ok else "missing", "interpretation": "Stage-wise noise is tied to high-stat direct-DFT throughput."},
        {"gate": "G2_prior_stage297", "status": "PASS" if stage297_ok else "FAIL", "metric": "Stage297 decision", "value": "positive" if stage297_ok else "missing", "interpretation": "Stage-wise noise is interpreted with resource side conditions present."},
        {"gate": "G3_stage_coverage", "status": "PASS" if stage_count_ok else "FAIL", "metric": "stages", "value": ",".join(sorted(stage_set)), "interpretation": "All blind/extract/materialize/packing/HW-KS boundaries must be present."},
        {"gate": "G4_pair_failures", "status": "PASS" if total_failures == 0 else "FAIL", "metric": "summary pair failures", "value": str(total_failures), "interpretation": "Every stage summary must have zero PVW/scalar decoded pair failures."},
        {"gate": "G5_trials", "status": "PASS" if trials >= 3 else "FAIL", "metric": "trials", "value": str(trials), "interpretation": "Stage298 is a local 3-trial target stage-wise gate."},
        {"gate": "G6_mode_gate", "status": "PASS" if gate_ok else "FAIL", "metric": "program gate", "value": mode_gate.group("mode_gate") if mode_gate else "missing", "interpretation": "The executable harness must report Pass."},
        {"gate": "G7_claim_boundary", "status": "PASS", "metric": "scope", "value": "local target include-zero r=4", "interpretation": "This is not native counter attribution or parameter generalization."},
        {"gate": "G8_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage299 route."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    write_csv(CLAIMS, ["claim", "status", "supported_statement", "not_supported"], [
        {"claim": "target_stagewise_noise", "status": decision, "supported_statement": "Direct-DFT include-zero r=4 has zero pair failures at every recorded target stage boundary.", "not_supported": "multi-parameter or native-counter claim."},
        {"claim": "complete_sab_speedup_context", "status": "linked", "supported_statement": "Stage296 remains the throughput evidence; Stage298 is only a correctness/noise side condition.", "not_supported": "new speedup result."},
        {"claim": "paper_grade", "status": "not_yet", "supported_statement": "Stage-wise local evidence is positive.", "not_supported": "literature novelty, parameter generalization, or hardware-counter attribution."},
    ])
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], [
        {"priority": "P0", "route": "stage299_parameter_generalization_direct_dft", "entry_condition": decision, "gate": "Repeat direct-DFT complete-SAB/noise on at least one added parameter or branch.", "failure_action": "Keep claim scoped to SET_2_3_2048 include-zero r=4."},
        {"priority": "P1", "route": "stage299_native_counter_direct_dft", "entry_condition": decision, "gate": "Run native counter attribution for selected-control vs direct-DFT.", "failure_action": "Keep attribution as local timing-only."},
    ])

    write_text(COMMANDS, """# Stage298 Reproduction Commands

```bash
STAGE298_TRIALS=3 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage298_direct_dft_target_stage_noise.sh
python3 scripts/build_stage298_direct_dft_target_stage_noise.py
```

Primary endpoint: zero PVW/scalar decoded pair failures at every target
stage boundary for direct-DFT include-zero r=4.
""")
    report = f"""# Stage298 Direct DFT Target Stage Noise

Decision: `{decision}`.

Stage298 adds target-size include-zero stage-wise noise evidence for the
direct-DFT PVW/MAT-SAB candidate. It is a correctness/noise side condition for
the Stage296 complete-SAB `T_bootstrap/r` speedup, not a new performance result.

## Stage Summary

{md_table(summary_rows, ["stage", "trials", "points", "pair_failures", "pair_log2_sigma_torus", "pair_log2_max_abs_torus"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Minimum stage sigma: `{min_sigma:.3f}`. Maximum stage absolute delta log2: `{max_abs:.3f}`.

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage298 Target Stage-Noise Model

The gate compares PVW/MAT-SAB lane phases against repeated scalar SAB lane
phases at five target-size boundaries:

1. blind-rotate accumulator coefficient 0;
2. PVW extraction;
3. materialized TLWE lane;
4. packing key switching;
5. HW key switching.

For this stage the correctness condition is pairwise decoded equality between
PVW and scalar references at each boundary. It deliberately does not use the
hand-written nonbinary expected-LUT model as a pass/fail oracle.
""")
    write_text(VARIANT, """# Stage298 Direct DFT Target Stage-Noise Variant

Variant flags:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
SAB_PVW_NONBINARY_TARGET_STAGE_NOISE_TEST=true
```

The tested branch is include-zero, target `SET_2_3_2048`, `r=4`.
""")
    write_text(PLAN, """# Stage298 Experiment Plan

Gates:

- Stage296 high-stat speed evidence is positive;
- Stage297 local resource side condition is positive;
- all five target stage boundaries are present;
- at least three trials;
- zero pair failures in every stage summary;
- executable harness reports Pass.
""")

    append_once(GOAL, "<!-- stage298-direct-dft-target-stage-noise -->", f"""<!-- stage298-direct-dft-target-stage-noise -->
### Stage298 direct DFT target stage-wise noise

`{decision}` adds target-size include-zero r=4 stage-wise PVW/scalar phase
equivalence for the direct-DFT candidate. The result supports Stage296 as a
local correctness/noise side condition, not as native attribution or
parameter-generalized evidence.
""")
    append_once(ROADMAP, "## Stage 298: Direct DFT Target Stage-Wise Noise", f"""## Stage 298: Direct DFT Target Stage-Wise Noise

Goal: close the target include-zero stage-wise noise side condition for the
direct-DFT candidate.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H298_direct_dft_target_stage_noise:", f"""H298_direct_dft_target_stage_noise:
  status: {decision}
  primary_metric: target_stagewise_pair_failures
  evidence:
    - repro/stage298_direct_dft_target_stage_noise/stage_summary.csv
    - repro/stage298_direct_dft_target_stage_noise/lane_summary.csv
    - repro/stage298_direct_dft_target_stage_noise/proof_gate.csv
    - docs/stage298_direct_dft_target_stage_noise.md
  conclusion: >
    Stage298 records target include-zero r=4 stage-wise pair-equivalence for
    the direct-DFT candidate. It remains local until native counter and
    parameter-generalization gates run.
""")
    append_once(MANIFEST, "- stage298_direct_dft_target_stage_noise:", """- stage298_direct_dft_target_stage_noise:
  - `docs/stage298_direct_dft_target_stage_noise.md`
  - `scripts/run_stage298_direct_dft_target_stage_noise.sh`
  - `scripts/build_stage298_direct_dft_target_stage_noise.py`
  - `repro/stage298_direct_dft_target_stage_noise/`
""")
    append_once(CHECKLIST, "<!-- stage298-direct-dft-target-stage-noise-checklist -->", f"""<!-- stage298-direct-dft-target-stage-noise-checklist -->
- [x] Stage298 records `{decision}` for direct DFT target include-zero stage-wise noise.
""")
    append_run_log({
        "run_id": "stage298-direct-dft-target-stage-noise-001",
        "date": "2026-07-05",
        "git_ref": git_head(),
        "stage": "Stage 298",
        "backend": "spqlios_avx512-local",
        "command": "STAGE298_TRIALS=3 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage298_direct_dft_target_stage_noise.sh",
        "parameters": "BINARY SET_2_3_2048 r=4 include-zero direct DFT target stage-wise noise",
        "rng": "n/a",
        "status": decision,
        "notes": "Target stage-wise pair-equivalence gate for direct-DFT evidence.",
        "artifacts": "docs/stage298_direct_dft_target_stage_noise.md; repro/stage298_direct_dft_target_stage_noise/proof_gate.csv",
    })

    paths = [DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SUMMARY, LANES, PROOF, CLAIMS, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)


if __name__ == "__main__":
    main()
