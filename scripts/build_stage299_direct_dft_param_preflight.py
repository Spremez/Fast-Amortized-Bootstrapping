#!/usr/bin/env python3
"""Stage299: added-parameter preflight for direct DFT."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage299_direct_dft_param_preflight"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage299_direct_dft_param_preflight.md"
THEORY = ROOT / "theory_checks" / "stage299_direct_dft_param_preflight_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage299_direct_dft_param_preflight.md"
PLAN = ROOT / "experiments" / "stage299_direct_dft_param_preflight_plan.md"
RUNNER = ROOT / "scripts" / "run_stage299_direct_dft_param_preflight.sh"
BUILDER = ROOT / "scripts" / "build_stage299_direct_dft_param_preflight.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

PERF_SAMPLES = OUT / "perf_samples.csv"
PERF_SUMMARY = OUT / "perf_summary.csv"
NOISE_SUMMARY = OUT / "noise_summary.csv"
PROOF = OUT / "proof_gate.csv"
CLAIMS = OUT / "claim_boundary.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage299_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT_LOCAL"
DECISION_NEUTRAL = "NEUTRAL_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT"
DECISION_FAIL = "FAIL_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT"

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
NOISE_RE = re.compile(
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
OVERALL_RE = re.compile(r"SAB_PVW_NONBINARY_TARGET_NOISE target full final-output gate: (?P<overall_gate>Pass|Fail)")
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


def ci95(vals: list[float]) -> tuple[float, float]:
    if not vals:
        return 0.0, 0.0
    if len(vals) == 1:
        return vals[0], vals[0]
    tcrit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776}.get(len(vals), 1.960)
    half = tcrit * pstdev(vals) / math.sqrt(len(vals))
    return mean(vals) - half, mean(vals) + half


def parse_perf(variant: str) -> list[dict[str, object]]:
    rows = []
    for outer_idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "variant": variant,
                "outer_run": outer_idx,
                "correctness": correctness,
                "mode": sample.group("mode"),
                "r": sample.group("r"),
                "h": correct.group("h") if correct else "",
                "r_prec": correct.group("r_prec") if correct else "",
                "pvw_us": sample.group("pvw_us"),
                "pvw_lane_us": sample.group("pvw_lane_us"),
                "scalar_repeated_us": sample.group("scalar_us"),
                "scalar_lane_us": sample.group("scalar_lane_us"),
                "speedup_vs_repeated_scalar": sample.group("speedup"),
                "source_log": rel(path),
            })
    return rows


def summarize_perf(variant: str, samples: list[dict[str, object]]) -> dict[str, object]:
    vals = [fnum(row.get("pvw_lane_us")) for row in samples if row.get("variant") == variant]
    scalars = [fnum(row.get("scalar_lane_us")) for row in samples if row.get("variant") == variant]
    statuses = {row.get("correctness") for row in samples if row.get("variant") == variant}
    low, high = ci95(vals)
    return {
        "variant": variant,
        "samples": len(vals),
        "correctness": "Pass" if vals and statuses == {"Pass"} else ",".join(sorted(str(s) for s in statuses)) or "MISSING",
        "t_bootstrap_over_r_mean_us": f"{mean(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_ci95_low_us": f"{low:.3f}" if vals else "",
        "t_bootstrap_over_r_ci95_high_us": f"{high:.3f}" if vals else "",
        "t_bootstrap_over_r_min_us": f"{min(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_max_us": f"{max(vals):.3f}" if vals else "",
        "scalar_t_bootstrap_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
        "speedup_vs_repeated_scalar_mean": f"{mean(scalars) / mean(vals):.6f}" if vals and scalars else "",
    }


def parse_noise() -> dict[str, object]:
    run_log = RAW / "noise_direct_dft" / "run.log"
    time_log = RAW / "noise_direct_dft" / "time.log"
    text = read_text(run_log)
    row: dict[str, object] = {"variant": "noise_direct_dft", "source_run_log": rel(run_log), "source_time_log": rel(time_log)}
    match = NOISE_RE.search(text)
    if match:
        row.update(match.groupdict())
    overall = OVERALL_RE.search(text)
    if overall:
        row["overall_gate"] = overall.group("overall_gate")
    time_match = TIME_RSS_RE.search(read_text(time_log))
    if time_match:
        row.update(time_match.groupdict())
    row["status"] = "pass" if row.get("gate") == "Pass" and row.get("overall_gate") == "Pass" and row.get("pair_failures") == "0" else "fail"
    return row


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
    samples = parse_perf("perf_selected_control") + parse_perf("perf_direct_dft")
    write_csv(PERF_SAMPLES, [
        "variant", "outer_run", "correctness", "mode", "r", "h", "r_prec",
        "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us",
        "speedup_vs_repeated_scalar", "source_log",
    ], samples)
    control = summarize_perf("perf_selected_control", samples)
    direct = summarize_perf("perf_direct_dft", samples)
    direct_vs_control = fnum(control.get("t_bootstrap_over_r_mean_us")) / fnum(direct.get("t_bootstrap_over_r_mean_us")) if fnum(direct.get("t_bootstrap_over_r_mean_us")) else 0.0
    perf_rows = [control, direct, {
        "variant": "comparison",
        "samples": min(int(control.get("samples", 0)), int(direct.get("samples", 0))),
        "correctness": "Pass" if control.get("correctness") == "Pass" and direct.get("correctness") == "Pass" else "FAIL",
        "direct_dft_vs_selected_control_mean": f"{direct_vs_control:.6f}",
    }]
    write_csv(PERF_SUMMARY, [
        "variant", "samples", "correctness", "t_bootstrap_over_r_mean_us",
        "t_bootstrap_over_r_ci95_low_us", "t_bootstrap_over_r_ci95_high_us",
        "t_bootstrap_over_r_min_us", "t_bootstrap_over_r_max_us",
        "scalar_t_bootstrap_over_r_mean_us",
        "speedup_vs_repeated_scalar_mean",
        "direct_dft_vs_selected_control_mean",
    ], perf_rows)

    noise = parse_noise()
    write_csv(NOISE_SUMMARY, [
        "variant", "status", "mode", "r", "trials", "points",
        "expected_model_pvw_failures", "expected_model_scalar_failures",
        "pair_failures", "pair_log2_sigma_torus", "pair_log2_max_abs_torus",
        "gate", "overall_gate", "time_maxrss_kb", "source_run_log", "source_time_log",
    ], [noise])

    stage298_ok = "PASS_STAGE298_DIRECT_DFT_TARGET_STAGE_NOISE_LOCAL" in read_text(ROOT / "repro" / "stage298_direct_dft_target_stage_noise" / "proof_gate.csv")
    perf_base_ok = control.get("correctness") == "Pass" and direct.get("correctness") == "Pass" and int(control.get("samples", 0)) >= 3 and int(direct.get("samples", 0)) >= 3
    direct_positive = direct_vs_control >= 1.01 and fnum(direct.get("speedup_vs_repeated_scalar_mean")) > 1.0
    noise_ok = noise.get("status") == "pass" and int(noise.get("trials", 0) or 0) >= 3
    if stage298_ok and perf_base_ok and direct_positive and noise_ok:
        decision = DECISION_PASS
    elif stage298_ok and perf_base_ok and noise_ok:
        decision = DECISION_NEUTRAL
    else:
        decision = DECISION_FAIL

    proof_rows = [
        {"gate": "G1_prior_stage298", "status": "PASS" if stage298_ok else "FAIL", "metric": "Stage298 decision", "value": "positive" if stage298_ok else "missing", "interpretation": "Added-parameter preflight follows target stage-wise evidence."},
        {"gate": "G2_perf_samples", "status": "PASS" if perf_base_ok else "FAIL", "metric": "samples", "value": f"{control.get('samples', 0)}/{direct.get('samples', 0)}", "interpretation": "At least three complete-SAB samples per variant."},
        {"gate": "G3_direct_effect", "status": "PASS" if direct_positive else "NEUTRAL", "metric": "direct/control mean T/r", "value": f"{direct_vs_control:.6f}", "interpretation": "Preflight effect threshold is 1.01x over selected control."},
        {"gate": "G4_noise", "status": "PASS" if noise_ok else "FAIL", "metric": "pair failures/trials", "value": f"{noise.get('pair_failures', '')}/{noise.get('trials', '')}", "interpretation": "Final-output pair equivalence for the added parameter."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "scope", "value": "SET_4_5_2048 preflight", "interpretation": "This is a preflight, not a full parameter-generalization matrix."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage300 route."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    write_csv(CLAIMS, ["claim", "status", "supported_statement", "not_supported"], [
        {"claim": "added_parameter_preflight", "status": decision, "supported_statement": "Direct-DFT was tested on SET_4_5_2048 with complete-SAB T/r and final-output noise.", "not_supported": "full all-parameter generalization."},
        {"claim": "direct_dft_universal_gain", "status": "not_yet", "supported_statement": "A positive preflight broadens evidence beyond SET_2_3_2048.", "not_supported": "universal optimality or all branch coverage."},
    ])
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], [
        {"priority": "P0", "route": "stage300_native_counter_or_second_param", "entry_condition": decision, "gate": "Native counter attribution or repeat on SET_2_3_4096.", "failure_action": "Keep Stage299 as preflight only."},
        {"priority": "P1", "route": "stage300_report_claim_matrix", "entry_condition": decision, "gate": "Update contribution claim matrix with pass/neutral/fail labels.", "failure_action": "Do not broaden parameter claim."},
    ])

    write_text(COMMANDS, """# Stage299 Reproduction Commands

```bash
STAGE299_RUNS=3 STAGE299_NOISE_TRIALS=3 PARAM=SET_4_5_2048 FFT_LIB=spqlios_avx512 bash scripts/run_stage299_direct_dft_param_preflight.sh
python3 scripts/build_stage299_direct_dft_param_preflight.py
```

Primary endpoint: complete SAB `T_bootstrap/r`; side condition: final-output
PVW/scalar pair failures.
""")
    report = f"""# Stage299 Direct DFT Parameter Preflight

Decision: `{decision}`.

Stage299 tests whether the direct-DFT PVW/MAT-SAB candidate remains viable on
the added binary parameter `SET_4_5_2048`. This is a preflight, not a final
parameter-generalization matrix.

## Performance

{md_table(perf_rows, ["variant", "samples", "correctness", "t_bootstrap_over_r_mean_us", "t_bootstrap_over_r_ci95_low_us", "t_bootstrap_over_r_ci95_high_us", "speedup_vs_repeated_scalar_mean", "direct_dft_vs_selected_control_mean"])}

## Noise

{md_table([noise], ["variant", "status", "r", "trials", "points", "pair_failures", "pair_log2_sigma_torus", "gate", "overall_gate"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage299 Parameter Preflight Model

The primary metric remains complete SAB `T_bootstrap/r`. Stage299 does not
change the algorithm. It tests whether the direct sub-decompose-to-DFT path,
previously positive on `SET_2_3_2048`, is still viable on `SET_4_5_2048`.

Pass requires a local positive direct/control effect and final-output
PVW/scalar pair equivalence. Neutral records parameter sensitivity without
promoting a broad claim.
""")
    write_text(VARIANT, """# Stage299 Direct DFT Parameter Preflight

Variant:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
PARAM=SET_4_5_2048
```

The selected-control branch uses the same PVW/MAT-SAB flags without the
direct-DFT flag.
""")
    write_text(PLAN, """# Stage299 Experiment Plan

Gates:

- Stage298 target stage-wise noise is positive;
- three complete-SAB samples per performance variant;
- direct-DFT improves selected-control mean `T_bootstrap/r` by at least 1.01x;
- direct-DFT remains faster than repeated scalar SAB;
- three final-output noise trials with zero pair failures.
""")

    append_once(GOAL, "<!-- stage299-direct-dft-param-preflight -->", f"""<!-- stage299-direct-dft-param-preflight -->
### Stage299 direct DFT parameter preflight

`{decision}` tests the direct-DFT candidate on `SET_4_5_2048` with complete-SAB
`T_bootstrap/r` and final-output noise. The result is a preflight only; broad
parameter-generalization still needs a larger matrix.
""")
    append_once(ROADMAP, "## Stage 299: Direct DFT Parameter Preflight", f"""## Stage 299: Direct DFT Parameter Preflight

Goal: test direct-DFT viability beyond `SET_2_3_2048` on one added parameter.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H299_direct_dft_param_preflight:", f"""H299_direct_dft_param_preflight:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage299_direct_dft_param_preflight/perf_summary.csv
    - repro/stage299_direct_dft_param_preflight/noise_summary.csv
    - repro/stage299_direct_dft_param_preflight/proof_gate.csv
    - docs/stage299_direct_dft_param_preflight.md
  conclusion: >
    Stage299 records an added-parameter preflight for the direct-DFT candidate.
    It may broaden evidence if positive but cannot replace a full parameter
    matrix or native attribution.
""")
    append_once(MANIFEST, "- stage299_direct_dft_param_preflight:", """- stage299_direct_dft_param_preflight:
  - `docs/stage299_direct_dft_param_preflight.md`
  - `scripts/run_stage299_direct_dft_param_preflight.sh`
  - `scripts/build_stage299_direct_dft_param_preflight.py`
  - `repro/stage299_direct_dft_param_preflight/`
""")
    append_once(CHECKLIST, "<!-- stage299-direct-dft-param-preflight-checklist -->", f"""<!-- stage299-direct-dft-param-preflight-checklist -->
- [x] Stage299 records `{decision}` for direct DFT added-parameter preflight.
""")
    append_run_log({
        "run_id": "stage299-direct-dft-param-preflight-001",
        "date": "2026-07-05",
        "git_ref": git_head(),
        "stage": "Stage 299",
        "backend": "spqlios_avx512-local",
        "command": "STAGE299_RUNS=3 STAGE299_NOISE_TRIALS=3 PARAM=SET_4_5_2048 FFT_LIB=spqlios_avx512 bash scripts/run_stage299_direct_dft_param_preflight.sh",
        "parameters": "BINARY SET_4_5_2048 r=4 include-zero direct DFT preflight",
        "rng": "n/a",
        "status": decision,
        "notes": "Added-parameter complete-SAB T/r and final-output noise preflight.",
        "artifacts": "docs/stage299_direct_dft_param_preflight.md; repro/stage299_direct_dft_param_preflight/proof_gate.csv",
    })

    paths = [DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, PERF_SAMPLES, PERF_SUMMARY, NOISE_SUMMARY, PROOF, CLAIMS, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)


if __name__ == "__main__":
    main()
