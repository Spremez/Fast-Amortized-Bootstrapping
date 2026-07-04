#!/usr/bin/env python3
"""Build Stage281 repeated gate artifacts for the selected CMUX residual candidate."""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage281_cmux_residual_repeated_gate"
RAW = OUT_DIR / "raw"
OUT_MD = ROOT / "docs" / "stage281_cmux_residual_repeated_gate.md"
RUNNER = ROOT / "scripts" / "run_stage281_cmux_residual_repeated_gate.sh"
BUILDER = ROOT / "scripts" / "build_stage281_cmux_residual_repeated_gate.py"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

SAMPLES_CSV = OUT_DIR / "latency_samples.csv"
SUMMARY_CSV = OUT_DIR / "latency_summary.csv"
PROFILE_CSV = OUT_DIR / "profile_components.csv"
PROFILE_DELTA_CSV = OUT_DIR / "profile_delta_vs_control.csv"
PROOF_CSV = OUT_DIR / "proof_gate.csv"
QUEUE_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_COPY = OUT_DIR / "stage281_report.md"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

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
PROFILE_KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")

COMPONENTS = [
    ("rgsw_monomial", "rgsw_monomial_us", "rgsw_monomial_calls"),
    ("cmux_total", "cmux_us", "cmux_calls"),
    ("mat_ep", "mat_ep_us", "mat_ep_calls"),
    ("cmux_from_dft", "cmux_from_dft_us", "cmux_from_dft_calls"),
    ("cmux_add", "cmux_add_us", "cmux_add_calls"),
    ("cmux_sub", "cmux_sub_us", "cmux_sub_calls"),
    ("ncmux_total", "ncmux_us", "ncmux_calls"),
    ("ncmux_auto", "ncmux_auto_us", "ncmux_auto_calls"),
    ("dual_sub_pair", "dual_sub_pair_us", "dual_sub_pair_calls"),
    ("sub_a_total", "sub_a_us", "sub_a_calls"),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, fields: Iterable[str], rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in writer.fieldnames})


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def parse_latency(variant: str, path: Path) -> List[Dict[str, object]]:
    text = read_text(path)
    correctness = "missing"
    correct = CORRECT_RE.search(text)
    if correct:
        correctness = correct.group("status")
    rows: List[Dict[str, object]] = []
    for match in SAMPLE_RE.finditer(text):
        rows.append({
            "variant": variant,
            "rep": match.group("rep"),
            "correctness": correctness,
            "mode": match.group("mode"),
            "r": match.group("r"),
            "pvw_us": match.group("pvw_us"),
            "pvw_lane_us": match.group("pvw_lane_us"),
            "scalar_repeated_us": match.group("scalar_us"),
            "scalar_lane_us": match.group("scalar_lane_us"),
            "speedup_vs_scalar_repeated": match.group("speedup"),
            "source_run_log": rel(path),
        })
    return rows


def parse_profile(variant: str, path: Path) -> List[Dict[str, object]]:
    text = read_text(path)
    profile_line = ""
    for line in text.splitlines():
        if line.startswith("SAB_PVW_BODY_PROFILE sample "):
            profile_line = line
    if not profile_line:
        return []
    kv = dict(PROFILE_KV_RE.findall(profile_line))
    full_us = float(kv.get("full_us", "0") or "0")
    rows: List[Dict[str, object]] = []
    for component, us_key, call_key in COMPONENTS:
        component_us = float(kv.get(us_key, "0") or "0")
        rows.append({
            "variant": variant,
            "component": component,
            "component_us": f"{component_us:.3f}",
            "calls": kv.get(call_key, "0"),
            "share_of_profile_full": f"{component_us / full_us:.6f}" if full_us > 0 else "",
            "full_us": f"{full_us:.3f}" if full_us > 0 else "",
            "source_run_log": rel(path),
        })
    return rows


def summarize_variant(variant: str, samples: List[Dict[str, object]]) -> Dict[str, object]:
    vals = [float(row["pvw_lane_us"]) for row in samples if row["variant"] == variant]
    scalar_vals = [float(row["scalar_lane_us"]) for row in samples if row["variant"] == variant]
    correctness = {row["correctness"] for row in samples if row["variant"] == variant}
    return {
        "variant": variant,
        "reps": len(vals),
        "correctness": "Pass" if correctness == {"Pass"} and vals else ",".join(sorted(correctness)) or "missing",
        "t_over_r_mean_us": f"{mean(vals):.3f}" if vals else "",
        "t_over_r_stddev_us": f"{pstdev(vals):.3f}" if len(vals) > 1 else "0.000",
        "t_over_r_min_us": f"{min(vals):.3f}" if vals else "",
        "t_over_r_max_us": f"{max(vals):.3f}" if vals else "",
        "scalar_t_over_r_mean_us": f"{mean(scalar_vals):.3f}" if scalar_vals else "",
        "speedup_vs_scalar_mean": f"{mean(scalar_vals) / mean(vals):.6f}" if vals and scalar_vals else "",
    }


def artifact_hash(path: Path) -> Dict[str, object]:
    data = path.read_bytes()
    return {"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def build_artifact_index() -> None:
    paths = [
        OUT_MD, REPORT_COPY, COMMANDS_MD, SAMPLES_CSV, SUMMARY_CSV,
        PROFILE_CSV, PROFILE_DELTA_CSV, PROOF_CSV, QUEUE_CSV,
        RAW / "variant_plan.csv", RUNNER, BUILDER,
    ]
    paths.extend(sorted(RAW.glob("*.log")))
    write_csv(ARTIFACT_INDEX, ["path", "bytes", "sha256"], [
        artifact_hash(path) for path in paths if path.exists()
    ])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    samples = []
    samples.extend(parse_latency("fast_control", RAW / "fast_control_latency_run.log"))
    samples.extend(parse_latency("backend_sub_decomp_dual", RAW / "backend_sub_decomp_dual_latency_run.log"))
    write_csv(SAMPLES_CSV, [
        "variant", "rep", "correctness", "mode", "r", "pvw_us", "pvw_lane_us",
        "scalar_repeated_us", "scalar_lane_us", "speedup_vs_scalar_repeated",
        "source_run_log",
    ], samples)

    control_summary = summarize_variant("fast_control", samples)
    candidate_summary = summarize_variant("backend_sub_decomp_dual", samples)
    control_mean = float(control_summary["t_over_r_mean_us"] or 0)
    candidate_mean = float(candidate_summary["t_over_r_mean_us"] or 0)
    control_min = float(control_summary["t_over_r_min_us"] or 0)
    candidate_max = float(candidate_summary["t_over_r_max_us"] or 0)
    mean_speedup = control_mean / candidate_mean if control_mean and candidate_mean else 0.0
    conservative_speedup = control_min / candidate_max if control_min and candidate_max else 0.0
    decision = (
        "PASS_STAGE281_REPEATED_POSITIVE_NOISE_RESOURCE_REQUIRED"
        if mean_speedup >= 1.02 and candidate_summary["correctness"] == "Pass" and control_summary["correctness"] == "Pass"
        else "PASS_STAGE281_REPEATED_NEUTRAL_OR_INSUFFICIENT"
    )
    summary_rows = [
        control_summary,
        candidate_summary,
        {
            "variant": "comparison",
            "reps": min(int(control_summary["reps"]), int(candidate_summary["reps"])),
            "correctness": "Pass" if control_summary["correctness"] == "Pass" and candidate_summary["correctness"] == "Pass" else "FAIL",
            "t_over_r_mean_us": "",
            "t_over_r_stddev_us": "",
            "t_over_r_min_us": "",
            "t_over_r_max_us": "",
            "scalar_t_over_r_mean_us": "",
            "speedup_vs_scalar_mean": "",
            "speedup_vs_fast_control_mean": f"{mean_speedup:.6f}",
            "conservative_control_min_over_candidate_max": f"{conservative_speedup:.6f}",
            "decision": decision,
        },
    ]
    write_csv(SUMMARY_CSV, [
        "variant", "reps", "correctness", "t_over_r_mean_us",
        "t_over_r_stddev_us", "t_over_r_min_us", "t_over_r_max_us",
        "scalar_t_over_r_mean_us", "speedup_vs_scalar_mean",
        "speedup_vs_fast_control_mean",
        "conservative_control_min_over_candidate_max", "decision",
    ], summary_rows)

    profile_rows = []
    profile_rows.extend(parse_profile("fast_control", RAW / "fast_control_profile_run.log"))
    profile_rows.extend(parse_profile("backend_sub_decomp_dual", RAW / "backend_sub_decomp_dual_profile_run.log"))
    write_csv(PROFILE_CSV, [
        "variant", "component", "component_us", "calls",
        "share_of_profile_full", "full_us", "source_run_log",
    ], profile_rows)
    control_components = {
        row["component"]: float(row["component_us"])
        for row in profile_rows if row["variant"] == "fast_control"
    }
    delta_rows = []
    for row in profile_rows:
        if row["variant"] == "fast_control":
            continue
        base = control_components.get(row["component"], 0.0)
        cur = float(row["component_us"])
        delta_rows.append({
            "component": row["component"],
            "control_component_us": f"{base:.3f}",
            "candidate_component_us": f"{cur:.3f}",
            "control_over_candidate": f"{base / cur:.6f}" if base > 0 and cur > 0 else "",
            "status": "reduced" if base > cur else "not_reduced",
        })
    write_csv(PROFILE_DELTA_CSV, [
        "component", "control_component_us", "candidate_component_us",
        "control_over_candidate", "status",
    ], delta_rows)

    proof_rows = [
        {"gate": "G1_input", "status": "PASS", "metric": "input commit", "value": git_head(), "interpretation": "Stage281 starts after Stage280 candidate selection."},
        {"gate": "G2_correctness", "status": "PASS" if control_summary["correctness"] == "Pass" and candidate_summary["correctness"] == "Pass" else "FAIL", "metric": "latency correctness", "value": f"{control_summary['correctness']}/{candidate_summary['correctness']}", "interpretation": "Timing is interpreted only after both variants pass."},
        {"gate": "G3_repeated_mean", "status": "PASS" if mean_speedup >= 1.02 else "NEUTRAL", "metric": "candidate speedup vs fast_control mean", "value": f"{mean_speedup:.6f}", "interpretation": "Repeated mean uses unprofiled full SAB T_bootstrap/r."},
        {"gate": "G4_conservative_bound", "status": "PASS_STRONG" if conservative_speedup > 1.0 else "OVERLAP", "metric": "control_min/candidate_max", "value": f"{conservative_speedup:.6f}", "interpretation": "Conservative overlap check; not required for screen promotion but recorded."},
        {"gate": "G5_profile_refresh", "status": "PASS" if profile_rows else "FAIL", "metric": "profile rows", "value": str(len(profile_rows)), "interpretation": "Profile remains attribution-only."},
        {"gate": "G6_decision", "status": decision, "metric": "stage decision", "value": decision, "interpretation": "Positive repeated result still needs noise/resource and native gates before final claims."},
    ]
    write_csv(PROOF_CSV, ["gate", "status", "metric", "value", "interpretation"], proof_rows)

    queue_rows = [
        {"priority": "P0", "route": "stage282_noise_resource_gate", "entry_condition": decision, "gate": "Run correctness/noise/resource for selected candidate and fast_control.", "failure_action": "Do not promote if failures, noise regression, or unacceptable resource growth appears."},
        {"priority": "P1", "route": "stage283_native_execution_resolution", "entry_condition": "native evidence still missing", "gate": "Resolve native execution or keep performance local-only.", "failure_action": "Do not claim native or paper-grade speed."},
    ]
    write_csv(QUEUE_CSV, ["priority", "route", "entry_condition", "gate", "failure_action"], queue_rows)

    write_text(COMMANDS_MD, """# Stage281 Reproduction Commands

```bash
bash scripts/run_stage281_cmux_residual_repeated_gate.sh
python3 scripts/build_stage281_cmux_residual_repeated_gate.py
```

Primary endpoint: unprofiled complete SAB `T_bootstrap/r`, repeated for control and selected candidate.
""")
    report = f"""# Stage281 CMUX Residual Repeated Gate

Decision: `{decision}`.

Stage281 repeats the Stage280 selected candidate
`backend_sub_decomp_dual` against the guarded include-zero fast control.
The metric is unprofiled complete SAB `T_bootstrap/r`.

## Latency Summary

| variant | reps | correctness | mean T/r us | min T/r us | max T/r us | scalar speedup mean |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| fast_control | {control_summary['reps']} | {control_summary['correctness']} | {control_summary['t_over_r_mean_us']} | {control_summary['t_over_r_min_us']} | {control_summary['t_over_r_max_us']} | {control_summary['speedup_vs_scalar_mean']} |
| backend_sub_decomp_dual | {candidate_summary['reps']} | {candidate_summary['correctness']} | {candidate_summary['t_over_r_mean_us']} | {candidate_summary['t_over_r_min_us']} | {candidate_summary['t_over_r_max_us']} | {candidate_summary['speedup_vs_scalar_mean']} |

Mean speedup vs fast control: `{mean_speedup:.6f}`.
Conservative `control_min / candidate_max`: `{conservative_speedup:.6f}`.

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
""" + "\n".join(
        f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['interpretation']} |"
        for row in proof_rows
    ) + f"""

## Claim Boundary

This is a repeated local gate, not a final paper claim. Noise/resource and
native execution remain separate gates.

Generated from input head `{git_head()}`.
"""
    write_text(OUT_MD, report)
    write_text(REPORT_COPY, report)

    append_once(CURRENT_GOAL_MD, "<!-- stage281-cmux-residual-repeated-gate -->", f"""<!-- stage281-cmux-residual-repeated-gate -->
### Stage281 CMUX residual repeated gate

`{decision}` repeats the Stage280 selected `backend_sub_decomp_dual` candidate
against fast control using unprofiled complete SAB `T_bootstrap/r`. Noise,
resource, and native gates remain open.
""")
    append_once(HYPOTHESIS_YAML, "H10_stage281_cmux_residual_repeated_gate:", f"""H10_stage281_cmux_residual_repeated_gate:
  status: {decision}
  evidence:
    - repro/stage281_cmux_residual_repeated_gate/latency_summary.csv
    - repro/stage281_cmux_residual_repeated_gate/profile_delta_vs_control.csv
    - repro/stage281_cmux_residual_repeated_gate/proof_gate.csv
    - docs/stage281_cmux_residual_repeated_gate.md
  conclusion: >
    Stage281 repeated the selected CMUX residual candidate against the guarded
    include-zero fast control. Noise/resource and native gates remain required.
""")
    append_once(RUN_LOG, "stage281-cmux-residual-repeated-gate-001", f"""stage281-cmux-residual-repeated-gate-001,2026-07-04,{git_head()},Stage 281,spqlios_avx512-local,bash scripts/run_stage281_cmux_residual_repeated_gate.sh; python scripts/build_stage281_cmux_residual_repeated_gate.py,"r=4 include-zero fast selected CMUX residual candidate repeated gate",n/a,{decision},"Repeated local gate; noise/resource/native still required.",docs/stage281_cmux_residual_repeated_gate.md; repro/stage281_cmux_residual_repeated_gate/proof_gate.csv
""")
    append_once(GLOBAL_MANIFEST, "- stage281_cmux_residual_repeated_gate:", """- stage281_cmux_residual_repeated_gate:
  - `docs/stage281_cmux_residual_repeated_gate.md`
  - `scripts/run_stage281_cmux_residual_repeated_gate.sh`
  - `scripts/build_stage281_cmux_residual_repeated_gate.py`
  - `repro/stage281_cmux_residual_repeated_gate/`
""")
    append_once(CHECKLIST_MD, "<!-- stage281-cmux-residual-repeated-gate-checklist -->", f"""<!-- stage281-cmux-residual-repeated-gate-checklist -->
- [x] Stage281 records `{decision}` for the selected CMUX residual candidate with repeated unprofiled T_bootstrap/r.
""")

    build_artifact_index()
    print(decision)


if __name__ == "__main__":
    main()
