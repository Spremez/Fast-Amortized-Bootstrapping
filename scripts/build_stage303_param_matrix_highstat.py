#!/usr/bin/env python3
"""Stage303: parameter-matrix direct-DFT full-SAB high-stat refresh."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage303_param_matrix_highstat"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage303_param_matrix_highstat.md"
THEORY = ROOT / "theory_checks" / "stage303_param_matrix_highstat_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage303_param_matrix_highstat.md"
PLAN = ROOT / "experiments" / "stage303_param_matrix_highstat_plan.md"
RUNNER = ROOT / "scripts" / "run_stage303_param_matrix_highstat.sh"
BUILDER = ROOT / "scripts" / "build_stage303_param_matrix_highstat.py"

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
REPORT = OUT / "stage303_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE303_PARAM_MATRIX_HIGHSTAT_LOCAL"
DECISION_NEUTRAL = "NEUTRAL_STAGE303_PARAM_MATRIX_HIGHSTAT_CI_OR_EFFECT_WEAK"
DECISION_FAIL = "FAIL_STAGE303_PARAM_MATRIX_HIGHSTAT"

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
NOISE_SUMMARY_RE = re.compile(
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
NOISE_OVERALL_RE = re.compile(r"SAB_PVW_NONBINARY_TARGET_NOISE target full final-output gate: (?P<overall_gate>Pass|Fail)")
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
    tcrit = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}.get(len(vals), 1.960)
    half = tcrit * pstdev(vals) / math.sqrt(len(vals))
    return mean(vals) - half, mean(vals) + half


def parse_perf_variant(variant: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for outer_idx, path in enumerate(sorted((RAW / variant).glob("run_*.log"))):
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "variant": variant,
                "outer_run": outer_idx,
                "inner_rep": sample.group("rep"),
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
    statuses = {str(row.get("correctness", "")) for row in samples if row.get("variant") == variant}
    low, high = ci95(vals)
    scalar_low, scalar_high = ci95(scalars)
    return {
        "variant": variant,
        "samples": len(vals),
        "correctness": "Pass" if vals and statuses == {"Pass"} else ",".join(sorted(statuses)) or "MISSING",
        "t_bootstrap_over_r_mean_us": f"{mean(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_stddev_us": f"{pstdev(vals):.3f}" if len(vals) > 1 else "0.000",
        "t_bootstrap_over_r_ci95_low_us": f"{low:.3f}" if vals else "",
        "t_bootstrap_over_r_ci95_high_us": f"{high:.3f}" if vals else "",
        "t_bootstrap_over_r_min_us": f"{min(vals):.3f}" if vals else "",
        "t_bootstrap_over_r_max_us": f"{max(vals):.3f}" if vals else "",
        "scalar_t_bootstrap_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
        "scalar_t_bootstrap_over_r_ci95_low_us": f"{scalar_low:.3f}" if scalars else "",
        "scalar_t_bootstrap_over_r_ci95_high_us": f"{scalar_high:.3f}" if scalars else "",
        "speedup_vs_repeated_scalar_mean": f"{mean(scalars) / mean(vals):.6f}" if vals and scalars else "",
    }


def parse_noise() -> dict[str, object]:
    run_log = RAW / "noise_direct_dft" / "run.log"
    time_log = RAW / "noise_direct_dft" / "time.log"
    row: dict[str, object] = {"variant": "noise_direct_dft", "source_run_log": rel(run_log), "source_time_log": rel(time_log)}
    match = NOISE_SUMMARY_RE.search(read_text(run_log))
    if match:
        row.update(match.groupdict())
    overall = NOISE_OVERALL_RE.search(read_text(run_log))
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
    samples = parse_perf_variant("perf_selected_control") + parse_perf_variant("perf_direct_dft")
    write_csv(PERF_SAMPLES, [
        "variant", "outer_run", "inner_rep", "correctness", "mode", "r",
        "h", "r_prec", "pvw_us", "pvw_lane_us", "scalar_repeated_us",
        "scalar_lane_us", "speedup_vs_repeated_scalar", "source_log",
    ], samples)

    control = summarize_perf("perf_selected_control", samples)
    direct = summarize_perf("perf_direct_dft", samples)
    control_mean = fnum(control.get("t_bootstrap_over_r_mean_us"))
    direct_mean = fnum(direct.get("t_bootstrap_over_r_mean_us"))
    direct_vs_control = control_mean / direct_mean if control_mean and direct_mean else 0.0
    conservative = fnum(control.get("t_bootstrap_over_r_min_us")) / fnum(direct.get("t_bootstrap_over_r_max_us")) if fnum(direct.get("t_bootstrap_over_r_max_us")) else 0.0
    direct_ci_separated = fnum(direct.get("t_bootstrap_over_r_ci95_high_us")) < fnum(control.get("t_bootstrap_over_r_ci95_low_us"))
    perf_rows = [control, direct, {
        "variant": "comparison",
        "samples": min(int(control.get("samples", 0)), int(direct.get("samples", 0))),
        "correctness": "Pass" if control.get("correctness") == "Pass" and direct.get("correctness") == "Pass" else "FAIL",
        "direct_dft_vs_selected_control_mean": f"{direct_vs_control:.6f}",
        "direct_dft_ci_separated_from_control": "true" if direct_ci_separated else "false",
        "conservative_control_min_over_direct_max": f"{conservative:.6f}",
    }]
    write_csv(PERF_SUMMARY, [
        "variant", "samples", "correctness", "t_bootstrap_over_r_mean_us",
        "t_bootstrap_over_r_stddev_us", "t_bootstrap_over_r_ci95_low_us",
        "t_bootstrap_over_r_ci95_high_us", "t_bootstrap_over_r_min_us",
        "t_bootstrap_over_r_max_us", "scalar_t_bootstrap_over_r_mean_us",
        "scalar_t_bootstrap_over_r_ci95_low_us",
        "scalar_t_bootstrap_over_r_ci95_high_us",
        "speedup_vs_repeated_scalar_mean",
        "direct_dft_vs_selected_control_mean",
        "direct_dft_ci_separated_from_control",
        "conservative_control_min_over_direct_max",
    ], perf_rows)

    noise = parse_noise()
    write_csv(NOISE_SUMMARY, [
        "variant", "status", "mode", "r", "trials", "points",
        "expected_model_pvw_failures", "expected_model_scalar_failures",
        "pair_failures", "pair_log2_sigma_torus",
        "pair_log2_max_abs_torus", "gate", "overall_gate",
        "time_maxrss_kb", "source_run_log", "source_time_log",
    ], [noise])

    stage299_ok = "PASS_STAGE299_DIRECT_DFT_PARAM_PREFLIGHT_LOCAL" in read_text(ROOT / "repro" / "stage299_direct_dft_param_preflight" / "proof_gate.csv")
    perf_ok = (
        control.get("correctness") == "Pass" and direct.get("correctness") == "Pass"
        and int(control.get("samples", 0)) >= 10 and int(direct.get("samples", 0)) >= 10
        and direct_vs_control >= 1.02 and fnum(direct.get("speedup_vs_repeated_scalar_mean")) > 1.0
    )
    noise_ok = noise.get("status") == "pass" and int(noise.get("trials", 0) or 0) >= 10
    if stage299_ok and perf_ok and noise_ok:
        decision = DECISION_PASS
    elif stage299_ok and control.get("correctness") == "Pass" and direct.get("correctness") == "Pass" and noise.get("status") == "pass":
        decision = DECISION_NEUTRAL
    else:
        decision = DECISION_FAIL

    proof_rows = [
        {"gate": "G1_prior_stage299", "status": "PASS" if stage299_ok else "FAIL", "metric": "Stage299 decision", "value": "positive" if stage299_ok else "missing", "interpretation": "Stage303 can only extend a positive Stage299 parameter preflight."},
        {"gate": "G2_sample_count", "status": "PASS" if int(control.get("samples", 0)) >= 10 and int(direct.get("samples", 0)) >= 10 else "FAIL", "metric": "perf samples", "value": f"{control.get('samples', 0)}/{direct.get('samples', 0)}", "interpretation": "Complete SAB A/B must have at least ten samples per variant."},
        {"gate": "G3_repeated_perf_effect", "status": "PASS" if perf_ok else "NEUTRAL_OR_FAIL", "metric": "direct/control mean T/r", "value": f"{direct_vs_control:.6f}", "interpretation": "Primary incremental direct-DFT metric under same backend."},
        {"gate": "G4_ci_separation", "status": "PASS" if direct_ci_separated else "WEAK", "metric": "direct high CI < control low CI", "value": str(direct_ci_separated).lower(), "interpretation": "CI separation upgrades confidence but is not required for a local engineering pass."},
        {"gate": "G5_noise_trials", "status": "PASS" if noise_ok else "FAIL", "metric": "pair failures/trials", "value": f"{noise.get('pair_failures', '')}/{noise.get('trials', '')}", "interpretation": "Target final-output PVW/scalar pair equivalence over ten trials."},
        {"gate": "G6_claim_boundary", "status": "PASS", "metric": "scope", "value": "local 10-run/10-trial campaign", "interpretation": "Still not a universal or literature novelty claim."},
        {"gate": "G7_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls Stage304 route."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    write_csv(CLAIMS, ["claim", "status", "supported_statement", "not_supported"], [
        {"claim": "amortized_complete_sab_speedup", "status": decision, "supported_statement": "direct DFT is compared by complete SAB T_bootstrap/r against repeated scalar and selected PVW control.", "not_supported": "single-output latency or universal optimality."},
        {"claim": "noise_correctness", "status": "PASS" if noise_ok else "FAIL", "supported_statement": "target final-output PVW/scalar pair failures are zero for recorded trials.", "not_supported": "stage-wise noise closure."},
        {"claim": "paper_grade", "status": "not_yet", "supported_statement": "local high-stat evidence may justify next-stage native or multi-parameter expansion.", "not_supported": "novelty or theorem-level optimality."},
    ])
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], [
        {"priority": "P0", "route": "stage304_parameter_claim_update", "entry_condition": decision, "gate": "Integrate SET_4_5_2048 high-stat result with Stage296 target and Stage301 counters.", "failure_action": "Keep broad parameter claim blocked."},
        {"priority": "P1", "route": "stage304_materialization_split_probe", "entry_condition": "need more kernel guidance after parameter matrix", "gate": "Split residual materialization/copy/sub-decomposition cost.", "failure_action": "Do not write a new AVX kernel without a measured component target."},
    ])

    command_text = """# Stage303 Reproduction Commands

```bash
STAGE303_PERF_RUNS=10 STAGE303_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 PARAM=SET_4_5_2048 bash scripts/run_stage303_param_matrix_highstat.sh
python3 scripts/build_stage303_param_matrix_highstat.py
```

Primary endpoint: complete SAB `T_bootstrap/r`.
Side condition: target final-output PVW/scalar decoded pair failures.
"""
    write_text(COMMANDS, command_text)
    report = f"""# Stage303 Direct DFT High-Stat Campaign

Decision: `{decision}`.

Stage303 expands Stage299 from a 3-run/3-trial parameter preflight to a local
10-run/10-trial complete-SAB campaign. It keeps the comparison dimension fixed as
`T_bootstrap/r`.

## Performance

{md_table(perf_rows, ["variant", "samples", "correctness", "t_bootstrap_over_r_mean_us", "t_bootstrap_over_r_ci95_low_us", "t_bootstrap_over_r_ci95_high_us", "speedup_vs_repeated_scalar_mean", "direct_dft_vs_selected_control_mean", "direct_dft_ci_separated_from_control"])}

## Noise

{md_table([noise], ["variant", "status", "mode", "r", "trials", "points", "pair_failures", "pair_log2_sigma_torus", "gate", "overall_gate", "time_maxrss_kb"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage303 Direct DFT High-Stat Model

The primary endpoint remains:

```text
complete SAB amortized time = T_bootstrap / r
```

Stage303 does not introduce a new algorithmic variant. It checks whether the
Stage299 added-parameter direct-DFT result persists under a larger local sample
count. The required comparison is same-backend:

- selected PVW/MAT-SAB control without direct sub-decompose-to-DFT;
- direct-DFT PVW/MAT-SAB candidate;
- repeated scalar SAB only as the amortized baseline denominator.

The stage can support a local engineering claim, but theory-level optimality
still requires broader parameter generalization and stage-wise noise/resource
accounting.
""")
    write_text(VARIANT, """# Stage303 Direct DFT High-Stat Variant

Variant flag:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
```

This remains the Stage292 direct-DFT candidate. Stage303 only strengthens the
evidence base and does not change scalar SAB or selected-control PVW-SAB.
""")
    write_text(PLAN, """# Stage303 Experiment Plan

Gates:

- 10 complete-SAB performance samples per variant;
- target correctness passes in every performance run;
- direct DFT mean `T_bootstrap/r` improves selected-control mean by at least 1.02x;
- direct DFT remains faster than repeated scalar SAB on `T_bootstrap/r`;
- 10 target final-output noise trials with zero PVW/scalar pair failures;
- CI separation is recorded as confidence evidence but not used as the only
  pass/fail boundary because local WSL timing noise can dominate tails.
""")

    append_once(GOAL, "<!-- stage303-param-matrix-highstat -->", f"""<!-- stage303-param-matrix-highstat -->
### Stage303 parameter matrix high-stat campaign

`{decision}` expands `SET_4_5_2048` from Stage299 preflight to a local
10-run/10-trial complete-SAB campaign. The metric remains `T_bootstrap/r`; the
result strengthens parameter evidence but does not establish universal coverage.
""")
    append_once(ROADMAP, "## Stage 303: Parameter Matrix High-Stat Campaign", f"""## Stage 303: Parameter Matrix High-Stat Campaign

Goal: upgrade Stage299 `SET_4_5_2048` evidence with a 10-run/10-trial
same-backend complete SAB campaign.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H303_param_matrix_highstat:", f"""H303_param_matrix_highstat:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage303_param_matrix_highstat/perf_summary.csv
    - repro/stage303_param_matrix_highstat/noise_summary.csv
    - repro/stage303_param_matrix_highstat/proof_gate.csv
    - docs/stage303_param_matrix_highstat.md
  conclusion: >
    Stage303 tests whether direct-DFT complete-SAB throughput persists on
    SET_4_5_2048 under a 10-run/10-trial local campaign. It strengthens but
    does not complete broad parameter generalization.
""")
    append_once(MANIFEST, "- stage303_param_matrix_highstat:", """- stage303_param_matrix_highstat:
  - `docs/stage303_param_matrix_highstat.md`
  - `scripts/run_stage303_param_matrix_highstat.sh`
  - `scripts/build_stage303_param_matrix_highstat.py`
  - `repro/stage303_param_matrix_highstat/`
""")
    append_once(CHECKLIST, "<!-- stage303-param-matrix-highstat-checklist -->", f"""<!-- stage303-param-matrix-highstat-checklist -->
- [x] Stage303 records `{decision}` for SET_4_5_2048 direct DFT high-stat local complete-SAB evidence.
""")
    append_run_log({
        "run_id": "stage303-param-matrix-highstat-001",
        "date": "2026-07-05",
        "git_ref": git_head(),
        "stage": "Stage 303",
        "backend": "spqlios_avx512-local",
        "command": "STAGE303_PERF_RUNS=10 STAGE303_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 PARAM=SET_4_5_2048 bash scripts/run_stage303_param_matrix_highstat.sh",
        "parameters": "BINARY SET_4_5_2048 r=4 include-zero direct DFT",
        "rng": "n/a",
        "status": decision,
        "notes": "High-stat local T_bootstrap/r plus target final-output noise campaign.",
        "artifacts": "docs/stage303_param_matrix_highstat.md; repro/stage303_param_matrix_highstat/proof_gate.csv",
    })

    paths = [DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, PERF_SAMPLES, PERF_SUMMARY, NOISE_SUMMARY, PROOF, CLAIMS, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)


if __name__ == "__main__":
    main()
