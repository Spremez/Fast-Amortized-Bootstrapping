#!/usr/bin/env python3
"""Stage292: full-SAB A/B for direct sub-decompose-to-DFT."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage292_fullsab_direct_dft_ab"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage292_fullsab_direct_dft_ab.md"
THEORY = ROOT / "theory_checks" / "stage292_fullsab_direct_dft_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage292_direct_dft_fullsab.md"
PLAN = ROOT / "experiments" / "stage292_fullsab_direct_dft_ab_plan.md"
RUNNER = ROOT / "scripts" / "run_stage292_fullsab_direct_dft_ab.sh"
BUILDER = ROOT / "scripts" / "build_stage292_fullsab_direct_dft_ab.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

SAMPLES = OUT / "latency_samples.csv"
SUMMARY = OUT / "latency_summary.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage292_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_POSITIVE = "PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED"
DECISION_NEUTRAL = "NEUTRAL_STAGE292_DIRECT_DFT_FULLSAB_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE292_DIRECT_DFT_FULLSAB_CORRECTNESS_OR_OUTPUT"

CORRECT_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
SAMPLE_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH sample target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) rep=(?P<rep>\d+) pvw_us=(?P<pvw_us>\d+) "
    r"pvw_lane_us=(?P<pvw_lane_us>[0-9.]+) scalar_repeated_us=(?P<scalar_us>\d+) "
    r"scalar_lane_us=(?P<scalar_lane_us>[0-9.]+) speedup=(?P<speedup>[0-9.]+)x"
)
SUMMARY_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH summary target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) reps=(?P<reps>\d+) .*?"
    r"t_bootstrap_over_r_pvw_us=(?P<pvw_over_r>[0-9.]+) "
    r"t_bootstrap_over_r_scalar_us=(?P<scalar_over_r>[0-9.]+)"
)


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
    cleaned = "\n".join(line.rstrip() for line in text.strip().splitlines())
    path.write_text(cleaned + "\n", encoding="utf-8", newline="\n")


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
    current = read_text(RUN_LOG)
    if row["run_id"] in current:
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


def parse_log(path: Path, variant: str, run_idx: int) -> List[Dict[str, object]]:
    text = read_text(path)
    correct = CORRECT_RE.search(text)
    summary = SUMMARY_RE.search(text)
    correctness = correct.group("status") if correct else "MISSING"
    mode = correct.group("mode") if correct else (summary.group("mode") if summary else "")
    r = correct.group("r") if correct else (summary.group("r") if summary else "")
    h = correct.group("h") if correct else ""
    r_prec = correct.group("r_prec") if correct else ""
    rows: List[Dict[str, object]] = []
    for sample in SAMPLE_RE.finditer(text):
        rows.append({
            "variant": variant,
            "outer_run": run_idx,
            "inner_rep": sample.group("rep"),
            "correctness": correctness,
            "mode": mode or sample.group("mode"),
            "r": r or sample.group("r"),
            "h": h,
            "r_prec": r_prec,
            "pvw_us": sample.group("pvw_us"),
            "pvw_lane_us": sample.group("pvw_lane_us"),
            "scalar_repeated_us": sample.group("scalar_us"),
            "scalar_lane_us": sample.group("scalar_lane_us"),
            "speedup_vs_repeated_scalar": sample.group("speedup"),
            "summary_pvw_over_r_us": summary.group("pvw_over_r") if summary else "",
            "summary_scalar_over_r_us": summary.group("scalar_over_r") if summary else "",
            "source_log": rel(path),
        })
    if not rows:
        rows.append({
            "variant": variant,
            "outer_run": run_idx,
            "inner_rep": "",
            "correctness": correctness,
            "mode": mode,
            "r": r,
            "h": h,
            "r_prec": r_prec,
            "source_log": rel(path),
        })
    return rows


def summarize(variant: str, rows: List[Dict[str, object]]) -> Dict[str, object]:
    vals = [fnum(row.get("pvw_lane_us")) for row in rows if row.get("variant") == variant and fnum(row.get("pvw_lane_us")) > 0]
    scalar_vals = [fnum(row.get("scalar_lane_us")) for row in rows if row.get("variant") == variant and fnum(row.get("scalar_lane_us")) > 0]
    statuses = {str(row.get("correctness", "")) for row in rows if row.get("variant") == variant}
    correctness = "Pass" if vals and statuses == {"Pass"} else ",".join(sorted(statuses)) or "MISSING"
    return {
        "variant": variant,
        "samples": len(vals),
        "correctness": correctness,
        "t_bootstrap_over_r_mean_us": f"{mean(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_stddev_us": f"{pstdev(vals):.3f}" if len(vals) > 1 else "0.000",
        "t_bootstrap_over_r_min_us": f"{min(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_max_us": f"{max(vals):.3f}" if vals else "",
        "scalar_t_bootstrap_over_r_mean_us": f"{mean(scalar_vals):.3f}" if scalar_vals else "",
        "speedup_vs_repeated_scalar_mean": f"{mean(scalar_vals) / mean(vals):.6f}" if vals and scalar_vals else "",
    }


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
    sample_rows: List[Dict[str, object]] = []
    for variant in ["selected_control", "direct_dft_candidate"]:
        for idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
            sample_rows.extend(parse_log(path, variant, idx))

    sample_fields = [
        "variant", "outer_run", "inner_rep", "correctness", "mode", "r", "h",
        "r_prec", "pvw_us", "pvw_lane_us", "scalar_repeated_us",
        "scalar_lane_us", "speedup_vs_repeated_scalar",
        "summary_pvw_over_r_us", "summary_scalar_over_r_us", "source_log",
    ]
    write_csv(SAMPLES, sample_fields, sample_rows)

    control = summarize("selected_control", sample_rows)
    candidate = summarize("direct_dft_candidate", sample_rows)
    c_mean = fnum(control.get("t_bootstrap_over_r_mean_us"))
    d_mean = fnum(candidate.get("t_bootstrap_over_r_mean_us"))
    c_min = fnum(control.get("t_bootstrap_over_r_min_us"))
    d_max = fnum(candidate.get("t_bootstrap_over_r_max_us"))
    direct_vs_control = c_mean / d_mean if c_mean > 0 and d_mean > 0 else 0.0
    conservative = c_min / d_max if c_min > 0 and d_max > 0 else 0.0
    correctness_ok = control.get("correctness") == "Pass" and candidate.get("correctness") == "Pass"
    enough_samples = int(control.get("samples", 0)) >= 2 and int(candidate.get("samples", 0)) >= 2
    if correctness_ok and enough_samples and direct_vs_control >= 1.02:
        decision = DECISION_POSITIVE
    elif correctness_ok and enough_samples:
        decision = DECISION_NEUTRAL
    else:
        decision = DECISION_FAIL

    summary_rows = [
        control,
        candidate,
        {
            "variant": "comparison",
            "samples": min(int(control.get("samples", 0)), int(candidate.get("samples", 0))),
            "correctness": "Pass" if correctness_ok else "FAIL",
            "direct_dft_vs_selected_control_mean": f"{direct_vs_control:.6f}",
            "conservative_control_min_over_direct_max": f"{conservative:.6f}",
            "decision": decision,
        },
    ]
    write_csv(
        SUMMARY,
        [
            "variant", "samples", "correctness", "t_bootstrap_over_r_mean_us",
            "t_bootstrap_over_r_stddev_us", "t_bootstrap_over_r_min_us",
            "t_bootstrap_over_r_max_us", "scalar_t_bootstrap_over_r_mean_us",
            "speedup_vs_repeated_scalar_mean",
            "direct_dft_vs_selected_control_mean",
            "conservative_control_min_over_direct_max", "decision",
        ],
        summary_rows,
    )

    stage291 = read_text(ROOT / "repro" / "stage291_sub_decomp_dft_direct_microbench" / "bench_summary.csv")
    stage291_ok = "PASS_STAGE291_SUB_DECOMP_DFT_DIRECT_MICRO_POSITIVE_FULL_SAB_REQUIRED" in stage291
    proof_rows = [
        {"gate": "G1_stage291_input", "status": "PASS" if stage291_ok else "WARN", "metric": "Stage291 decision", "value": "positive_microbench" if stage291_ok else "missing_or_not_positive", "interpretation": "Stage292 is opened only as a full-SAB validation of Stage291."},
        {"gate": "G2_correctness", "status": "PASS" if correctness_ok else "FAIL", "metric": "both variants", "value": f"{control.get('correctness')}/{candidate.get('correctness')}", "interpretation": "No timing claim is made if scalar/PVW output equivalence fails."},
        {"gate": "G3_samples", "status": "PASS" if enough_samples else "FAIL", "metric": "samples per variant", "value": f"{control.get('samples')}/{candidate.get('samples')}", "interpretation": "This is a repeated local A/B, not a high-stat final campaign."},
        {"gate": "G4_full_sab_increment", "status": "PASS" if direct_vs_control >= 1.02 else "NEUTRAL", "metric": "selected control T/r over direct T/r", "value": f"{direct_vs_control:.6f}", "interpretation": "Measures the direct-DFT change inside complete SAB."},
        {"gate": "G5_algorithm_endpoint", "status": "PASS" if candidate.get("speedup_vs_repeated_scalar_mean") else "FAIL", "metric": "candidate vs repeated scalar T/r", "value": str(candidate.get("speedup_vs_repeated_scalar_mean", "")), "interpretation": "This is the main MAT-RLWE/PVW-SAB comparison dimension."},
        {"gate": "G6_claim_boundary", "status": "PASS", "metric": "claim scope", "value": "full_sab_local_ab_not_noise_resource", "interpretation": "Noise/resource/high-stat/paper claims remain separate gates."},
        {"gate": "G7_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Positive result opens noise/resource; neutral result records an ablation."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)

    queue_rows = [
        {"priority": "P0", "route": "stage293_direct_dft_noise_resource", "entry_condition": decision, "gate": "Only if Stage292 is positive: run correctness/noise/resource for direct DFT.", "failure_action": "Do not promote direct DFT if noise/resource regresses or full-SAB effect vanishes."},
        {"priority": "P1", "route": "stage293b_counter_attribution", "entry_condition": "optional after positive or neutral Stage292", "gate": "Native counters/assembly to explain memory-op effect.", "failure_action": "Keep as proxy if native counters are unavailable."},
    ]
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], queue_rows)

    write_text(COMMANDS, f"""# Stage292 Reproduction Commands

```bash
STAGE292_RUNS=3 STAGE292_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage292_fullsab_direct_dft_ab.sh
python3 scripts/build_stage292_fullsab_direct_dft_ab.py
```

Primary endpoint: complete SAB `T_bootstrap/r` for r-body MAT-RLWE/PVW output.
""")

    report = f"""# Stage292 Full-SAB Direct DFT A/B

Decision: `{decision}`.

Stage292 tests whether Stage291's direct sub-decompose-to-DFT improvement
survives inside complete SAB. The primary metric is `T_bootstrap/r`, i.e. full
bootstrap time divided by the number of processed body lanes/plaintext lanes.

## Summary

{md_table(summary_rows, ["variant", "samples", "correctness", "t_bootstrap_over_r_mean_us", "t_bootstrap_over_r_min_us", "t_bootstrap_over_r_max_us", "speedup_vs_repeated_scalar_mean", "direct_dft_vs_selected_control_mean", "decision"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

## Interpretation

`speedup_vs_repeated_scalar_mean` is the algorithm-level amortized comparison.
`direct_dft_vs_selected_control_mean` is only the incremental value of adding
`MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true` to the already selected PVW-SAB path.

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)

    write_text(THEORY, """# Stage292 Direct DFT Full-SAB Model

The original selected path computes an intermediate PVW_TMLWE difference and
then decomposes that torus polynomial before FFT/DFT conversion:

```text
diff = in2 - in1
digits = decompose(diff)
DFT(digits)
MAT external product
```

The Stage291 candidate removes the materialized torus `diff` rows for the
sub-decompose route and writes signed decomposition digits directly into the
SPQLIOS reverse-transform input:

```text
DFT(decompose(in2 - in1))
MAT external product
```

The sparse SAB schedule, selector semantics, secret-key distribution, and
external-product count are unchanged. The theoretical gain is bounded by the
fraction of full-SAB time spent in this sub-decompose-to-DFT path, so a
positive microbench can still become neutral in complete SAB.
""")
    write_text(VARIANT, """# Stage292 Direct DFT Full-SAB Variant

Flag:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
```

Required companion flags for this gate:

```text
SAB_PVW_SUB_DECOMP_FUSION=true
MAT_TRGSW_AVX512_SUB_DECOMP=true
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
```

Default status: off. Scalar `sab_rlwe_bootstrap` and the selected PVW-SAB
control path remain available as references.
""")
    write_text(PLAN, """# Stage292 Experiment Plan

Goal: validate Stage291 direct sub-decompose-to-DFT inside full SAB.

Comparison:

- selected_control: current selected r=4 include-zero PVW-SAB path.
- direct_dft_candidate: selected_control plus
  `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true`.

Correctness gate: both variants must print
`SAB_PVW_NONBINARY_BENCH correctness ... Pass`.

Performance gate: use complete SAB `T_bootstrap/r`. Promote only if direct DFT
improves the selected control by at least 1.02x in mean repeated local runs.

Failure handling: if neutral or negative, keep Stage291 as a kernel-level
ablation and do not default-enable the flag.
""")

    append_once(GOAL, "<!-- stage292-fullsab-direct-dft-ab -->", f"""<!-- stage292-fullsab-direct-dft-ab -->
### Stage292 full-SAB direct DFT A/B

`{decision}` tests `MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true` inside complete
SAB using `T_bootstrap/r`. The algorithm-level scalar comparison is recorded
separately from the incremental selected-control comparison.
""")
    append_once(ROADMAP, "## Stage 292: Direct DFT Full-SAB A/B", f"""## Stage 292: Direct DFT Full-SAB A/B

Goal: validate Stage291 direct sub-decompose-to-DFT under complete SAB
`T_bootstrap/r`.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H292_direct_dft_fullsab_ab:", f"""H292_direct_dft_fullsab_ab:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage292_fullsab_direct_dft_ab/latency_summary.csv
    - repro/stage292_fullsab_direct_dft_ab/proof_gate.csv
    - docs/stage292_fullsab_direct_dft_ab.md
  conclusion: >
    Stage292 evaluates whether direct sub-decompose-to-DFT survives as a
    complete-SAB improvement. Algorithm-level speedup is reported as
    T_bootstrap/r versus repeated scalar; direct-vs-control is only an
    incremental implementation gate.
""")
    append_once(MANIFEST, "- stage292_fullsab_direct_dft_ab:", """- stage292_fullsab_direct_dft_ab:
  - `docs/stage292_fullsab_direct_dft_ab.md`
  - `scripts/run_stage292_fullsab_direct_dft_ab.sh`
  - `scripts/build_stage292_fullsab_direct_dft_ab.py`
  - `repro/stage292_fullsab_direct_dft_ab/`
""")
    append_once(CHECKLIST, "<!-- stage292-fullsab-direct-dft-ab-checklist -->", f"""<!-- stage292-fullsab-direct-dft-ab-checklist -->
- [x] Stage292 records `{decision}` for direct sub-decompose-to-DFT under complete SAB `T_bootstrap/r`.
""")
    append_run_log({
        "run_id": "stage292-fullsab-direct-dft-ab-001",
        "date": "2026-07-04",
        "git_ref": git_head(),
        "stage": "Stage 292",
        "backend": "spqlios_avx512-local",
        "command": "STAGE292_RUNS=3 STAGE292_REPS=1 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage292_fullsab_direct_dft_ab.sh",
        "parameters": "BINARY SET_2_3_2048 r=4 include-zero",
        "rng": "n/a",
        "status": decision,
        "notes": "Full-SAB T_bootstrap/r A/B; direct DFT is incremental to selected PVW-SAB control.",
        "artifacts": "docs/stage292_fullsab_direct_dft_ab.md; repro/stage292_fullsab_direct_dft_ab/proof_gate.csv",
    })

    paths = [DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, SAMPLES, SUMMARY, PROOF, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)


if __name__ == "__main__":
    main()
