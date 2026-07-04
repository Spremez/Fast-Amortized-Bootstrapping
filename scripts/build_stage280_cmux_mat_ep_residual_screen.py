#!/usr/bin/env python3
"""Build Stage280 CMUX/MAT-EP residual candidate screen artifacts."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage280_cmux_mat_ep_residual_screen"
RAW = OUT_DIR / "raw"
OUT_MD = ROOT / "docs" / "stage280_cmux_mat_ep_residual_screen.md"
RUNNER = ROOT / "scripts" / "run_stage280_cmux_mat_ep_residual_screen.sh"
BUILDER = ROOT / "scripts" / "build_stage280_cmux_mat_ep_residual_screen.py"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

PLAN_CSV = RAW / "variant_plan.csv"
PERF_CSV = OUT_DIR / "performance_results.csv"
COMPARE_CSV = OUT_DIR / "candidate_comparison.csv"
PROFILE_CSV = OUT_DIR / "profile_components.csv"
PROFILE_DELTA_CSV = OUT_DIR / "profile_delta_vs_control.csv"
PROOF_CSV = OUT_DIR / "proof_gate.csv"
QUEUE_CSV = OUT_DIR / "next_stage_queue.csv"
COMMANDS_MD = OUT_DIR / "reproduction_commands.md"
REPORT_COPY = OUT_DIR / "stage280_report.md"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

BENCH_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH summary target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+) pvw_stddev_us=(?P<pvw_stddev_us>[0-9.]+) "
    r"pvw_lane_avg_us=(?P<pvw_lane_avg_us>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+) "
    r"scalar_stddev_us=(?P<scalar_stddev_us>[0-9.]+) "
    r"scalar_lane_avg_us=(?P<scalar_lane_avg_us>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x "
    r"speedup_stddev=(?P<speedup_stddev>[0-9.]+) "
    r"t_bootstrap_over_r_pvw_us=(?P<t_over_r_pvw>[0-9.]+) "
    r"t_bootstrap_over_r_scalar_us=(?P<t_over_r_scalar>[0-9.]+)"
)
CORRECT_RE = re.compile(
    r"SAB_PVW_NONBINARY_BENCH correctness target_full mode=(?P<mode>\w+) "
    r"r=(?P<r>\d+) h=(?P<h>\d+) r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
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
    ("sub_a_rotate", "sub_a_rotate_us", "sub_a_rotate_calls"),
    ("copyback", "copyback_us", "copyback_calls"),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_head() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except Exception:
        return "unknown"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


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


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    sep = "" if current.endswith("\n") or not current else "\n"
    write_text(path, current + sep + text)


def parse_bench_log(path: Path) -> Dict[str, object]:
    text = read_text(path)
    row: Dict[str, object] = {
        "status": "missing_log" if not path.exists() else "missing_summary",
        "correctness": "missing",
        "source_run_log": rel(path),
    }
    correct = CORRECT_RE.search(text)
    if correct:
        row.update({
            "correctness": correct.group("status"),
            "mode": correct.group("mode"),
            "r": correct.group("r"),
            "h": correct.group("h"),
            "r_prec": correct.group("r_prec"),
        })
    bench = BENCH_RE.search(text)
    if bench:
        row.update({
            "status": "pass" if row.get("correctness") == "Pass" else "correctness_failed",
            "mode": bench.group("mode"),
            "r": bench.group("r"),
            "reps": bench.group("reps"),
            "pvw_avg_us": bench.group("pvw_avg_us"),
            "pvw_lane_avg_us": bench.group("pvw_lane_avg_us"),
            "scalar_repeated_avg_us": bench.group("scalar_repeated_avg_us"),
            "scalar_lane_avg_us": bench.group("scalar_lane_avg_us"),
            "speedup_vs_scalar_repeated": bench.group("speedup"),
            "t_bootstrap_over_r_pvw_us": bench.group("t_over_r_pvw"),
            "t_bootstrap_over_r_scalar_us": bench.group("t_over_r_scalar"),
        })
    return row


def parse_profile_log(path: Path, variant: str) -> List[Dict[str, object]]:
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
        calls = int(kv.get(call_key, "0") or "0")
        rows.append({
            "variant": variant,
            "component": component,
            "component_us": f"{component_us:.3f}",
            "calls": calls,
            "share_of_profile_full": f"{component_us / full_us:.6f}" if full_us > 0 else "",
            "full_us": f"{full_us:.3f}" if full_us > 0 else "",
            "source_run_log": rel(path),
        })
    return rows


def artifact_hash(path: Path) -> Dict[str, object]:
    data = path.read_bytes()
    return {"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def build_artifact_index(extra: Iterable[Path]) -> None:
    paths: List[Path] = [
        OUT_MD,
        REPORT_COPY,
        COMMANDS_MD,
        PERF_CSV,
        COMPARE_CSV,
        PROFILE_CSV,
        PROFILE_DELTA_CSV,
        PROOF_CSV,
        QUEUE_CSV,
        PLAN_CSV,
        RUNNER,
        BUILDER,
    ]
    paths.extend(sorted(p for p in RAW.glob("*.log")))
    paths.extend(extra)
    rows = [artifact_hash(path) for path in paths if path.exists()]
    write_csv(ARTIFACT_INDEX, ["path", "bytes", "sha256"], rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plan_rows = read_csv(PLAN_CSV)
    perf_rows: List[Dict[str, object]] = []
    profile_rows: List[Dict[str, object]] = []

    for plan in plan_rows:
        variant = plan["variant"]
        profile = plan["profile"].lower() == "true"
        stem = f"{variant}_profile" if profile else variant
        run_log = RAW / f"{stem}_run.log"
        bench = parse_bench_log(run_log)
        bench.update({
            "variant": variant,
            "profile": str(profile).lower(),
            "extra_flags": plan.get("extra_flags", ""),
            "source_build_log": rel(RAW / f"{stem}_build.log"),
        })
        perf_rows.append(bench)
        if profile:
            profile_rows.extend(parse_profile_log(run_log, variant))

    write_csv(PERF_CSV, [
        "variant", "profile", "status", "correctness", "mode", "r", "h",
        "r_prec", "reps", "pvw_avg_us", "pvw_lane_avg_us",
        "scalar_repeated_avg_us", "scalar_lane_avg_us",
        "speedup_vs_scalar_repeated", "t_bootstrap_over_r_pvw_us",
        "t_bootstrap_over_r_scalar_us", "extra_flags", "source_build_log",
        "source_run_log",
    ], perf_rows)
    write_csv(PROFILE_CSV, [
        "variant", "component", "component_us", "calls",
        "share_of_profile_full", "full_us", "source_run_log",
    ], profile_rows)

    unprofiled = [
        row for row in perf_rows
        if row.get("profile") == "false" and row.get("status") == "pass"
    ]
    control = next((row for row in unprofiled if row["variant"] == "fast_control"), None)
    control_t = float(control["t_bootstrap_over_r_pvw_us"]) if control else 0.0
    compare_rows: List[Dict[str, object]] = []
    for row in unprofiled:
        t_val = float(row["t_bootstrap_over_r_pvw_us"])
        if row["variant"] == "fast_control":
            rel_speed = 1.0
            status = "control"
        else:
            rel_speed = control_t / t_val if control_t > 0 and t_val > 0 else 0.0
            status = "positive_screen" if rel_speed >= 1.01 else "neutral_or_negative_screen"
        compare_rows.append({
            "variant": row["variant"],
            "t_bootstrap_over_r_pvw_us": f"{t_val:.3f}",
            "speedup_vs_fast_control": f"{rel_speed:.6f}",
            "speedup_vs_scalar_repeated": row.get("speedup_vs_scalar_repeated", ""),
            "status": status,
            "extra_flags": row.get("extra_flags", ""),
        })
    write_csv(COMPARE_CSV, [
        "variant", "t_bootstrap_over_r_pvw_us", "speedup_vs_fast_control",
        "speedup_vs_scalar_repeated", "status", "extra_flags",
    ], compare_rows)

    best = max(
        (row for row in compare_rows if row["variant"] != "fast_control"),
        key=lambda row: float(row["speedup_vs_fast_control"]),
        default=None,
    )
    best_speed = float(best["speedup_vs_fast_control"]) if best else 0.0
    if not control:
        decision = "FAIL_STAGE280_CONTROL_MISSING"
    elif any(row.get("correctness") != "Pass" for row in perf_rows):
        decision = "FAIL_STAGE280_CORRECTNESS_OR_PARSE"
    elif best_speed >= 1.01:
        decision = "PASS_STAGE280_RESIDUAL_CANDIDATE_SELECTED_REPEAT_REQUIRED"
    else:
        decision = "PASS_STAGE280_NO_POSITIVE_RESIDUAL_CANDIDATE"

    control_components = {
        row["component"]: float(row["component_us"])
        for row in profile_rows
        if row["variant"] == "fast_control"
    }
    delta_rows: List[Dict[str, object]] = []
    for row in profile_rows:
        if row["variant"] == "fast_control":
            continue
        base = control_components.get(row["component"], 0.0)
        cur = float(row["component_us"])
        delta_rows.append({
            "variant": row["variant"],
            "component": row["component"],
            "control_component_us": f"{base:.3f}",
            "variant_component_us": f"{cur:.3f}",
            "control_over_variant": f"{base / cur:.6f}" if base > 0 and cur > 0 else "",
            "status": "reduced" if base > cur else "not_reduced",
        })
    write_csv(PROFILE_DELTA_CSV, [
        "variant", "component", "control_component_us", "variant_component_us",
        "control_over_variant", "status",
    ], delta_rows)

    correctness_passed = sum(1 for row in perf_rows if row.get("correctness") == "Pass")
    all_rows = len(perf_rows)
    proof_rows = [
        {
            "gate": "G1_current_input",
            "status": "PASS",
            "metric": "input commit",
            "value": git_head(),
            "interpretation": "Stage280 starts after Stage279 residual profile.",
        },
        {
            "gate": "G2_correctness",
            "status": "PASS" if correctness_passed == all_rows and all_rows else "FAIL",
            "metric": "correctness rows",
            "value": f"{correctness_passed}/{all_rows}",
            "interpretation": "All screened variants must pass full SAB correctness before timing is interpreted.",
        },
        {
            "gate": "G3_unprofiled_control",
            "status": "PASS" if control else "FAIL",
            "metric": "fast_control T/r",
            "value": f"{control_t:.3f}" if control else "missing",
            "interpretation": "Candidate deltas use unprofiled fast include-zero control.",
        },
        {
            "gate": "G4_best_candidate",
            "status": "PASS" if best else "FAIL",
            "metric": best["variant"] if best else "missing",
            "value": f"{best_speed:.6f}" if best else "missing",
            "interpretation": "Best candidate is selected only for a repeated gate, not final promotion.",
        },
        {
            "gate": "G5_profile_coverage",
            "status": "PASS" if profile_rows else "FAIL",
            "metric": "profile components",
            "value": str(len(profile_rows)),
            "interpretation": "Body-profile attribution is recorded separately from latency claims.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "No final speed claim is made from Stage280 single-screen data.",
        },
    ]
    write_csv(PROOF_CSV, ["gate", "status", "metric", "value", "interpretation"], proof_rows)

    selected = best["variant"] if best else "none"
    queue_rows = [
        {
            "priority": "P0",
            "route": "stage281_cmux_residual_repeated_gate",
            "entry_condition": decision == "PASS_STAGE280_RESIDUAL_CANDIDATE_SELECTED_REPEAT_REQUIRED",
            "candidate": selected,
            "gate": "Run reps>=3 unprofiled full SAB A/B plus one body-profile refresh.",
            "failure_action": "Mark candidate neutral if repeated mean/min do not beat fast_control.",
        },
        {
            "priority": "P1",
            "route": "stage282_native_execution_resolution",
            "entry_condition": "native BatchMode access still missing",
            "candidate": "native_handoff",
            "gate": "Use key-based native access or keep claims local-only.",
            "failure_action": "Do not write native or paper-grade performance claims.",
        },
    ]
    write_csv(QUEUE_CSV, [
        "priority", "route", "entry_condition", "candidate", "gate",
        "failure_action",
    ], queue_rows)

    write_text(COMMANDS_MD, """# Stage280 Reproduction Commands

```bash
bash scripts/run_stage280_cmux_mat_ep_residual_screen.sh
python3 scripts/build_stage280_cmux_mat_ep_residual_screen.py
```

Primary endpoint: unprofiled complete SAB `T_bootstrap/r` for r=4 include-zero fast path.
Profile rows are attribution-only.
""")

    top_compare = "\n".join(
        f"| {row['variant']} | {row['t_bootstrap_over_r_pvw_us']} | "
        f"{row['speedup_vs_fast_control']} | {row['status']} |"
        for row in compare_rows
    )
    top_profile = "\n".join(
        f"| {row['variant']} | {row['component']} | {row['component_us']} | "
        f"{row['calls']} | {row['share_of_profile_full']} |"
        for row in profile_rows
        if row["component"] in {"rgsw_monomial", "cmux_total", "mat_ep",
                                "cmux_from_dft", "cmux_add", "cmux_sub"}
    )
    report = f"""# Stage280 CMUX/MAT-EP Residual Screen

Decision: `{decision}`.

Stage280 screens existing explicit CMUX/MAT-EP residual candidates under the
current guarded include-zero fast path. The primary metric is unprofiled full
SAB `T_bootstrap/r`; body-profile data is attribution-only.

## Candidate Comparison

| variant | T_bootstrap/r PVW us | speedup vs fast_control | status |
| --- | ---: | ---: | --- |
{top_compare}

Selected candidate for the next repeated gate: `{selected}`.

## Profile Components

| variant | component | component us | calls | share of profiled full |
| --- | --- | ---: | ---: | ---: |
{top_profile}

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
""" + "\n".join(
        f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['interpretation']} |"
        for row in proof_rows
    ) + f"""

## Claim Boundary

| claim | status |
| --- | --- |
| complete SAB speedup | screen-only; repeated gate required |
| algorithmic improvement | not yet promoted; candidate must survive Stage281 |
| backend/SIMD distinction | same `spqlios_avx512` backend and explicit flags recorded |
| native performance | still gated until native execution is resolved |

Generated from input head `{git_head()}`.
"""
    write_text(OUT_MD, report)
    write_text(REPORT_COPY, report)

    append_once(
        CURRENT_GOAL_MD,
        "<!-- stage280-cmux-mat-ep-residual-screen -->",
        f"""<!-- stage280-cmux-mat-ep-residual-screen -->
### Stage280 CMUX/MAT-EP residual screen

`{decision}` screens existing explicit CMUX/MAT-EP residual candidates under the
guarded include-zero fast path. The selected next candidate is `{selected}` and
requires repeated full-SAB A/B before any promotion.
""",
    )
    append_once(
        HYPOTHESIS_YAML,
        "H10_stage280_cmux_mat_ep_residual_screen:",
        f"""H10_stage280_cmux_mat_ep_residual_screen:
  status: {decision}
  evidence:
    - repro/stage280_cmux_mat_ep_residual_screen/performance_results.csv
    - repro/stage280_cmux_mat_ep_residual_screen/candidate_comparison.csv
    - repro/stage280_cmux_mat_ep_residual_screen/profile_components.csv
    - docs/stage280_cmux_mat_ep_residual_screen.md
  conclusion: >
    Stage280 screens CMUX/MAT-EP residual candidates under the current
    include-zero fast path. Selected candidate: {selected}. Repeated full-SAB
    A/B remains required before promotion.
""",
    )
    append_once(
        RUN_LOG,
        "stage280-cmux-mat-ep-residual-screen-001",
        f"""stage280-cmux-mat-ep-residual-screen-001,2026-07-04,{git_head()},Stage 280,spqlios_avx512-local,bash scripts/run_stage280_cmux_mat_ep_residual_screen.sh; python scripts/build_stage280_cmux_mat_ep_residual_screen.py,"r=4 include-zero fast CMUX/MAT-EP residual candidate screen; primary metric T_bootstrap/r",n/a,{decision},"Screen only; selected candidate requires repeated gate.",docs/stage280_cmux_mat_ep_residual_screen.md; repro/stage280_cmux_mat_ep_residual_screen/proof_gate.csv
""",
    )
    append_once(
        GLOBAL_MANIFEST,
        "- stage280_cmux_mat_ep_residual_screen:",
        """- stage280_cmux_mat_ep_residual_screen:
  - `docs/stage280_cmux_mat_ep_residual_screen.md`
  - `scripts/run_stage280_cmux_mat_ep_residual_screen.sh`
  - `scripts/build_stage280_cmux_mat_ep_residual_screen.py`
  - `repro/stage280_cmux_mat_ep_residual_screen/`
""",
    )
    append_once(
        CHECKLIST_MD,
        "<!-- stage280-cmux-mat-ep-residual-screen-checklist -->",
        f"""<!-- stage280-cmux-mat-ep-residual-screen-checklist -->
- [x] Stage280 records `{decision}` with unprofiled T_bootstrap/r and separate profile attribution.
""",
    )

    build_artifact_index([])
    print(decision)


if __name__ == "__main__":
    main()
