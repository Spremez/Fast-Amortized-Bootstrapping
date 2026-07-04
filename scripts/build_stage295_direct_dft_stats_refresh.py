#!/usr/bin/env python3
"""Stage295: repeated performance plus target-noise refresh for direct DFT."""

from __future__ import annotations

import csv
import hashlib
import math
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage295_direct_dft_stats_refresh"
RAW = OUT / "raw"
DOC = ROOT / "docs" / "stage295_direct_dft_stats_refresh.md"
THEORY = ROOT / "theory_checks" / "stage295_direct_dft_stats_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage295_direct_dft_stats.md"
PLAN = ROOT / "experiments" / "stage295_direct_dft_stats_refresh_plan.md"
RUNNER = ROOT / "scripts" / "run_stage295_direct_dft_stats_refresh.sh"
BUILDER = ROOT / "scripts" / "build_stage295_direct_dft_stats_refresh.py"

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
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage295_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE295_DIRECT_DFT_STATS_REFRESH_HIGHSTAT_PENDING"
DECISION_NEUTRAL = "NEUTRAL_STAGE295_DIRECT_DFT_STATS_REFRESH_NO_PROMOTION"
DECISION_FAIL = "FAIL_STAGE295_DIRECT_DFT_STATS_REFRESH"

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


def ci95(vals: List[float]) -> tuple[float, float]:
    if not vals:
        return 0.0, 0.0
    if len(vals) == 1:
        return vals[0], vals[0]
    t = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262}.get(len(vals), 1.960)
    sd = pstdev(vals)
    half = t * sd / math.sqrt(len(vals))
    return mean(vals) - half, mean(vals) + half


def parse_perf_variant(variant: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
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


def summarize_perf(variant: str, samples: List[Dict[str, object]]) -> Dict[str, object]:
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


def parse_noise() -> Dict[str, object]:
    run_log = RAW / "noise_direct_dft" / "run.log"
    time_log = RAW / "noise_direct_dft" / "time.log"
    text = read_text(run_log)
    row: Dict[str, object] = {
        "variant": "noise_direct_dft",
        "source_run_log": rel(run_log),
        "source_time_log": rel(time_log),
    }
    match = NOISE_SUMMARY_RE.search(text)
    if match:
        row.update(match.groupdict())
    overall = NOISE_OVERALL_RE.search(text)
    if overall:
        row["overall_gate"] = overall.group("overall_gate")
    time_match = TIME_RSS_RE.search(read_text(time_log))
    if time_match:
        row.update(time_match.groupdict())
    row["status"] = "pass" if row.get("gate") == "Pass" and row.get("overall_gate") == "Pass" and row.get("pair_failures") == "0" else "fail"
    return row


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
    perf_rows = [control, direct, {
        "variant": "comparison",
        "samples": min(int(control.get("samples", 0)), int(direct.get("samples", 0))),
        "correctness": "Pass" if control.get("correctness") == "Pass" and direct.get("correctness") == "Pass" else "FAIL",
        "direct_dft_vs_selected_control_mean": f"{direct_vs_control:.6f}",
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

    stage292_ok = "PASS_STAGE292_DIRECT_DFT_FULLSAB_POSITIVE_NOISE_RESOURCE_REQUIRED" in read_text(ROOT / "repro" / "stage292_fullsab_direct_dft_ab" / "proof_gate.csv")
    stage294_ok = "PASS_STAGE294_DIRECT_DFT_TARGET_NOISE_FINAL_OUTPUT" in read_text(ROOT / "repro" / "stage294_direct_dft_target_noise" / "proof_gate.csv")
    perf_ok = (
        control.get("correctness") == "Pass" and direct.get("correctness") == "Pass"
        and int(control.get("samples", 0)) >= 5 and int(direct.get("samples", 0)) >= 5
        and direct_vs_control >= 1.02 and fnum(direct.get("speedup_vs_repeated_scalar_mean")) > 1.0
    )
    noise_ok = noise.get("status") == "pass" and int(noise.get("trials", 0) or 0) >= 5
    if stage292_ok and stage294_ok and perf_ok and noise_ok:
        decision = DECISION_PASS
    elif stage292_ok and stage294_ok and control.get("correctness") == "Pass" and direct.get("correctness") == "Pass" and noise.get("status") == "pass":
        decision = DECISION_NEUTRAL
    else:
        decision = DECISION_FAIL

    proof_rows = [
        {"gate": "G1_prior_full_sab", "status": "PASS" if stage292_ok else "FAIL", "metric": "Stage292", "value": "positive" if stage292_ok else "missing", "interpretation": "Stage295 refreshes a previously positive full-SAB candidate."},
        {"gate": "G2_prior_noise", "status": "PASS" if stage294_ok else "FAIL", "metric": "Stage294", "value": "target final-output noise" if stage294_ok else "missing", "interpretation": "Stage295 extends, not replaces, the target final-output noise gate."},
        {"gate": "G3_repeated_perf", "status": "PASS" if perf_ok else "NEUTRAL_OR_FAIL", "metric": "direct/control mean T/r", "value": f"{direct_vs_control:.6f}", "interpretation": "Same-backend repeated complete SAB endpoint."},
        {"gate": "G4_noise_trials", "status": "PASS" if noise_ok else "FAIL", "metric": "pair failures/trials", "value": f"{noise.get('pair_failures', '')}/{noise.get('trials', '')}", "interpretation": "Direct DFT final output must remain scalar-equivalent over more trials."},
        {"gate": "G5_claim_boundary", "status": "PASS", "metric": "scope", "value": "5-run/5-trial refresh", "interpretation": "This is stronger than smoke, but still below final paper-grade 10+ run/multi-seed matrix."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Controls whether Stage296 high-stat expansion is justified."},
    ]
    write_csv(PROOF, ["gate", "status", "metric", "value", "interpretation"], proof_rows)
    write_csv(NEXT, ["priority", "route", "entry_condition", "gate", "failure_action"], [
        {"priority": "P0", "route": "stage296_direct_dft_10run_10noise_or_native", "entry_condition": decision, "gate": "Upgrade to 10-run/10+ trial or native counter-supported campaign.", "failure_action": "Keep Stage295 as scoped local refresh."},
        {"priority": "P1", "route": "stage296_stagewise_noise", "entry_condition": "paper claim needs stage-wise noise", "gate": "Target-size stage-wise nonbinary pair noise.", "failure_action": "Limit claims to final-output equivalence/noise."},
    ])

    write_text(COMMANDS, """# Stage295 Reproduction Commands

```bash
STAGE295_PERF_RUNS=5 STAGE295_NOISE_TRIALS=5 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage295_direct_dft_stats_refresh.sh
python3 scripts/build_stage295_direct_dft_stats_refresh.py
```

Primary performance metric: complete SAB `T_bootstrap/r`.
Primary noise metric: target final-output PVW/scalar decoded pair failures.
""")
    report = f"""# Stage295 Direct DFT Stats Refresh

Decision: `{decision}`.

Stage295 refreshes the Stage292 direct-DFT candidate with repeated complete-SAB
`T_bootstrap/r` and target final-output noise trials under the same backend and
target parameter.

## Performance

{md_table(perf_rows, ["variant", "samples", "correctness", "t_bootstrap_over_r_mean_us", "t_bootstrap_over_r_ci95_low_us", "t_bootstrap_over_r_ci95_high_us", "speedup_vs_repeated_scalar_mean", "direct_dft_vs_selected_control_mean"])}

## Noise

{md_table([noise], ["variant", "status", "mode", "r", "trials", "points", "pair_failures", "pair_log2_sigma_torus", "gate", "overall_gate"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value", "interpretation"])}

Generated from input head `{git_head()}`.
"""
    write_text(DOC, report)
    write_text(REPORT, report)
    write_text(THEORY, """# Stage295 Stats Refresh Model

Stage295 keeps the comparison dimension fixed:

```text
complete SAB T_bootstrap / r
```

for selected-control PVW-SAB and the direct-DFT candidate. It also reruns the
target final-output scalar-equivalence noise gate. This separates:

- algorithm-level amortized throughput versus repeated scalar SAB;
- incremental direct-DFT benefit over the selected PVW-SAB control;
- final-output correctness/noise side condition.

The stage is a local statistical refresh, not a universal optimality proof.
""")
    write_text(VARIANT, """# Stage295 Direct DFT Stats Variant

Candidate:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
```

The variant is tested only with the selected PVW-SAB companion flags and
include-zero r=4 target parameters.
""")
    write_text(PLAN, """# Stage295 Experiment Plan

Gates:

- at least five repeated complete-SAB samples per performance variant;
- both variants pass target correctness;
- direct DFT improves selected control mean `T_bootstrap/r` by at least 1.02x;
- direct DFT remains faster than repeated scalar SAB;
- at least five target final-output noise trials with zero pair failures.

If any gate fails, the result is neutral/fail and cannot be promoted.
""")

    append_once(GOAL, "<!-- stage295-direct-dft-stats-refresh -->", f"""<!-- stage295-direct-dft-stats-refresh -->
### Stage295 direct DFT stats refresh

`{decision}` refreshes direct-DFT evidence with repeated complete-SAB
`T_bootstrap/r` and target final-output noise trials. The result remains scoped
to local `spqlios_avx512`, `SET_2_3_2048`, include-zero r=4.
""")
    append_once(ROADMAP, "## Stage 295: Direct DFT Stats Refresh", f"""## Stage 295: Direct DFT Stats Refresh

Goal: strengthen Stage292/294 evidence with repeated performance and noise
refresh.

Status: `{decision}`.
""")
    append_once(HYPOTHESES, "H295_direct_dft_stats_refresh:", f"""H295_direct_dft_stats_refresh:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage295_direct_dft_stats_refresh/perf_summary.csv
    - repro/stage295_direct_dft_stats_refresh/noise_summary.csv
    - repro/stage295_direct_dft_stats_refresh/proof_gate.csv
    - docs/stage295_direct_dft_stats_refresh.md
  conclusion: >
    Stage295 refreshes direct-DFT complete-SAB throughput and target
    final-output noise. It remains scoped and below final paper-grade matrix
    unless Stage296 expands it.
""")
    append_once(MANIFEST, "- stage295_direct_dft_stats_refresh:", """- stage295_direct_dft_stats_refresh:
  - `docs/stage295_direct_dft_stats_refresh.md`
  - `scripts/run_stage295_direct_dft_stats_refresh.sh`
  - `scripts/build_stage295_direct_dft_stats_refresh.py`
  - `repro/stage295_direct_dft_stats_refresh/`
""")
    append_once(CHECKLIST, "<!-- stage295-direct-dft-stats-refresh-checklist -->", f"""<!-- stage295-direct-dft-stats-refresh-checklist -->
- [x] Stage295 records `{decision}` for direct DFT repeated performance plus target final-output noise refresh.
""")
    append_run_log({
        "run_id": "stage295-direct-dft-stats-refresh-001",
        "date": "2026-07-04",
        "git_ref": git_head(),
        "stage": "Stage 295",
        "backend": "spqlios_avx512-local",
        "command": "STAGE295_PERF_RUNS=5 STAGE295_NOISE_TRIALS=5 FFT_LIB=spqlios_avx512 PARAM=SET_2_3_2048 bash scripts/run_stage295_direct_dft_stats_refresh.sh",
        "parameters": "BINARY SET_2_3_2048 r=4 include-zero direct DFT",
        "rng": "n/a",
        "status": decision,
        "notes": "Repeated T_bootstrap/r plus target final-output noise refresh.",
        "artifacts": "docs/stage295_direct_dft_stats_refresh.md; repro/stage295_direct_dft_stats_refresh/proof_gate.csv",
    })

    paths = [DOC, THEORY, VARIANT, PLAN, COMMANDS, REPORT, PERF_SAMPLES, PERF_SUMMARY, NOISE_SUMMARY, PROOF, NEXT, RAW / "variant_plan.csv", RUNNER, BUILDER]
    paths.extend(sorted(RAW.glob("*/*.log")))
    artifact_index(paths)
    print(decision)


if __name__ == "__main__":
    main()
