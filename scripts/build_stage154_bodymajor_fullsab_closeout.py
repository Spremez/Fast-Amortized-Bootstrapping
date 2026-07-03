#!/usr/bin/env python3
"""Build Stage154 r=6 body-major complete-SAB closeout gate."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage154_bodymajor_fullsab_closeout"

STAGE108_SUMMARY = ROOT / "repro" / "stage108_bodymajor_layout_gate" / "summary.csv"
STAGE108_KERNEL = ROOT / "repro" / "stage108_bodymajor_layout_gate" / "kernel_comparison.csv"
STAGE153_SUMMARY = ROOT / "repro" / "stage153_dual_sub_fullsab_gate" / "summary.csv"

VARIANT_CSV = OUT_DIR / "variant_results.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
PRIOR_CSV = OUT_DIR / "prior_evidence.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage154_bodymajor_fullsab_closeout.md"
PLAN_MD = ROOT / "experiments" / "stage154_bodymajor_fullsab_closeout_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage154_bodymajor_fullsab_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_bodymajor_fullsab_closeout.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

R_VALUE = int(os.environ.get("STAGE154_R", "6"))
BENCH_REPS = int(os.environ.get("SAB_PVW_BENCH_REPS", "1"))
JOBS = int(os.environ.get("JOBS", "8"))
RUN_SMOKE = os.environ.get("STAGE154_RUN_SMOKE", "1") not in {"0", "false", "False"}

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_BENCH=true "
    f"SAB_PVW_BENCH_R={R_VALUE} SAB_PVW_BENCH_REPS={BENCH_REPS}"
)

VARIANTS = [
    {
        "variant": "tile4_h14_r6_backend",
        "flags": f"{BASE_FLAGS} MAT_TRGSW_AVX512_RGT4_FUSED=true",
    },
    {
        "variant": "bodymajor_h14_r6_backend",
        "flags": f"{BASE_FLAGS} MAT_TRGSW_AVX512_R6_BODYMAJOR=true",
    },
]

PRIOR_FIELDS = ["source", "gate", "status", "metric", "value", "evidence", "detail"]
VARIANT_FIELDS = [
    "variant", "status", "r", "reps", "correctness", "pvw_avg_us",
    "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us",
    "speedup_vs_scalar_repeated", "source_build_log", "source_run_log",
]
COMPARE_FIELDS = ["metric", "tile4", "bodymajor", "bodymajor_over_tile4", "status", "detail"]
SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]

CORRECT_RE = re.compile(
    r"SAB_PVW_BENCH correctness target_full r=(?P<r>\d+) h=(?P<h>\d+) "
    r"r_prec=(?P<r_prec>\d+): (?P<status>\w+)"
)
BENCH_RE = re.compile(
    r"SAB_PVW_BENCH summary target_full r=(?P<r>\d+) reps=(?P<reps>\d+) "
    r"pvw_avg_us=(?P<pvw_avg_us>[0-9.]+) pvw_stddev_us=(?P<pvw_stddev_us>[0-9.]+) "
    r"pvw_lane_avg_us=(?P<pvw_lane_avg_us>[0-9.]+) "
    r"scalar_repeated_avg_us=(?P<scalar_repeated_avg_us>[0-9.]+) "
    r"scalar_stddev_us=(?P<scalar_stddev_us>[0-9.]+) "
    r"scalar_lane_avg_us=(?P<scalar_lane_avg_us>[0-9.]+) "
    r"speedup_vs_scalar_repeated=(?P<speedup>[0-9.]+)x "
    r"speedup_stddev=(?P<speedup_stddev>[0-9.]+)"
)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = []
    for ch in text:
        code = ord(ch)
        if ch == "\n" or ch == "\t" or 32 <= code <= 126:
            cleaned.append(ch)
        else:
            cleaned.append("?")
    return "\n".join(line.rstrip() for line in "".join(cleaned).splitlines()).rstrip()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(row.get(field, "") for field in fields) + " |")
    return "\n".join(out)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def append_once(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + block.strip("\n") + "\n")


def upsert_stage_section(path: Path, heading: str, block: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    replacement = block.strip("\n") + "\n"
    pattern = re.compile(
        rf"^{re.escape(heading)}\n.*?(?=^## Stage [0-9]+:|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if pattern.search(text):
        write_text_lf(path, pattern.sub(replacement, text, count=1))
        return
    if text and not text.endswith("\n"):
        text += "\n"
    write_text_lf(path, text + replacement)


def bash(command: str, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def run_logged(command: str, log: Path, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    proc = bash(command, timeout=timeout)
    write_text_lf(log, "\n".join([
        f"command: {command}",
        f"returncode: {proc.returncode}",
        "--- stdout ---",
        sanitize(proc.stdout),
        "--- stderr ---",
        sanitize(proc.stderr),
    ]).rstrip() + "\n")
    return proc


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def fmt(value: float) -> str:
    if math.isfinite(value):
        return f"{value:.6f}"
    return str(value)


def status_by_gate(rows: List[Dict[str, str]], gate: str) -> str:
    for row in rows:
        if row.get("gate") == gate:
            return row.get("status", "")
    return "MISSING"


def collect_prior() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    stage108 = read_csv(STAGE108_SUMMARY)
    rows.append({
        "source": "Stage108",
        "gate": "stage108_decision",
        "status": status_by_gate(stage108, "stage108_decision"),
        "metric": "bodymajor_kernel_gate",
        "value": status_by_gate(stage108, "stage108_kernel_locality_result"),
        "evidence": rel(STAGE108_SUMMARY),
        "detail": "Stage108 tested bodymajor at kernel level but skipped complete-SAB timing.",
    })
    kernels = read_csv(STAGE108_KERNEL)
    full_r6 = next((row for row in kernels if row.get("bench") == "full_output" and row.get("r") == "6"), {})
    rows.append({
        "source": "Stage108",
        "gate": "stage108_kernel_full_output_r6",
        "status": "PROFILE_ONLY",
        "metric": "bodymajor_vs_tile4;bodymajor_vs_fulltile",
        "value": f"{full_r6.get('bodymajor_vs_tile4', '')};{full_r6.get('bodymajor_vs_fulltile', '')}",
        "evidence": rel(STAGE108_KERNEL),
        "detail": "Kernel evidence alone cannot decide complete SAB.",
    })
    stage153 = read_csv(STAGE153_SUMMARY)
    rows.append({
        "source": "Stage153",
        "gate": "stage153_decision",
        "status": status_by_gate(stage153, "stage153_decision"),
        "metric": "next_route",
        "value": "avoid_pair_fraction_limited_dual_sub",
        "evidence": rel(STAGE153_SUMMARY),
        "detail": "After H14-C3 neutral, close broader MAT layout evidence before selecting another route.",
    })
    return rows


def run_variant(variant: Dict[str, str]) -> Dict[str, str]:
    name = variant["variant"]
    flags = variant["flags"]
    vdir = OUT_DIR / name
    vdir.mkdir(parents=True, exist_ok=True)
    clean_log = vdir / "clean.log"
    build_log = vdir / "build.log"
    run_log = vdir / "run.log"
    if RUN_SMOKE:
        clean = run_logged("make clean", clean_log, timeout=300)
        if clean.returncode != 0:
            return {"variant": name, "status": "BUILD_FAIL", "source_build_log": rel(build_log), "source_run_log": rel(run_log)}
        build = run_logged(f"make {flags} -j{JOBS}", build_log, timeout=600)
        if build.returncode != 0:
            return {"variant": name, "status": "BUILD_FAIL", "source_build_log": rel(build_log), "source_run_log": rel(run_log)}
        run = run_logged("./main", run_log, timeout=1200)
        if run.returncode != 0:
            return {"variant": name, "status": "RUN_FAIL", "source_build_log": rel(build_log), "source_run_log": rel(run_log)}
    text = run_log.read_text(encoding="utf-8", errors="replace") if run_log.exists() else ""
    correctness = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    return {
        "variant": name,
        "status": "PASS" if correctness and bench and correctness.group("status") == "Pass" else "MISSING_OR_FAIL",
        "r": bench.group("r") if bench else "",
        "reps": bench.group("reps") if bench else "",
        "correctness": correctness.group("status") if correctness else "",
        "pvw_avg_us": bench.group("pvw_avg_us") if bench else "",
        "pvw_lane_avg_us": bench.group("pvw_lane_avg_us") if bench else "",
        "scalar_repeated_avg_us": bench.group("scalar_repeated_avg_us") if bench else "",
        "scalar_lane_avg_us": bench.group("scalar_lane_avg_us") if bench else "",
        "speedup_vs_scalar_repeated": bench.group("speedup") if bench else "",
        "source_build_log": rel(build_log),
        "source_run_log": rel(run_log),
    }


def compare(variants: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tile = next((row for row in variants if row.get("variant") == "tile4_h14_r6_backend"), {})
    body = next((row for row in variants if row.get("variant") == "bodymajor_h14_r6_backend"), {})
    tile_us = fnum(tile.get("pvw_avg_us", "0"))
    body_us = fnum(body.get("pvw_avg_us", "0"))
    full_speed = tile_us / body_us if tile_us and body_us else 0.0
    tile_lane = fnum(tile.get("pvw_lane_avg_us", "0"))
    body_lane = fnum(body.get("pvw_lane_avg_us", "0"))
    lane_speed = tile_lane / body_lane if tile_lane and body_lane else 0.0
    return [
        {
            "metric": "full_sab_pvw_us",
            "tile4": tile.get("pvw_avg_us", ""),
            "bodymajor": body.get("pvw_avg_us", ""),
            "bodymajor_over_tile4": fmt(full_speed),
            "status": "PROMOTE" if full_speed >= 1.02 else ("NEUTRAL" if full_speed >= 0.99 else "REJECT"),
            "detail": "Complete SAB wall-clock smoke; repeated gate required for any promotion.",
        },
        {
            "metric": "amortized_T_bootstrap_per_lane_us",
            "tile4": tile.get("pvw_lane_avg_us", ""),
            "bodymajor": body.get("pvw_lane_avg_us", ""),
            "bodymajor_over_tile4": fmt(lane_speed),
            "status": "PROMOTE" if lane_speed >= 1.02 else ("NEUTRAL" if lane_speed >= 0.99 else "REJECT"),
            "detail": "Primary MAT-RLWE SAB endpoint.",
        },
        {
            "metric": "speedup_vs_scalar_repeated",
            "tile4": tile.get("speedup_vs_scalar_repeated", ""),
            "bodymajor": body.get("speedup_vs_scalar_repeated", ""),
            "bodymajor_over_tile4": "",
            "status": "INFO",
            "detail": "Reported only as context; the gate is bodymajor versus same-backend tile4.",
        },
    ]


def decide(variants: List[Dict[str, str]], comparison: List[Dict[str, str]]) -> str:
    if any(row.get("status") != "PASS" for row in variants):
        return "FAIL_STAGE154_BODYMAJOR_FULLSAB_CORRECTNESS_OR_BUILD"
    speed = fnum(next((row.get("bodymajor_over_tile4", "0") for row in comparison if row.get("metric") == "amortized_T_bootstrap_per_lane_us"), "0"))
    if speed >= 1.02:
        return "SMOKE_STAGE154_BODYMAJOR_FULLSAB_POSITIVE_REPEATED_REQUIRED"
    if speed >= 0.99:
        return "NEUTRAL_STAGE154_BODYMAJOR_FULLSAB_NO_PROMOTION"
    return "REJECT_STAGE154_BODYMAJOR_FULLSAB_SLOWER"


def write_outputs(prior: List[Dict[str, str]], variants: List[Dict[str, str]],
    comparison: List[Dict[str, str]], decision: str) -> None:
    write_csv(PRIOR_CSV, prior, PRIOR_FIELDS)
    write_csv(VARIANT_CSV, variants, VARIANT_FIELDS)
    write_csv(COMPARISON_CSV, comparison, COMPARE_FIELDS)
    speed = next((row.get("bodymajor_over_tile4", "") for row in comparison if row.get("metric") == "amortized_T_bootstrap_per_lane_us"), "")
    summary = [
        {
            "gate": "stage154_precondition",
            "status": "PASS",
            "metric": "stage108;stage153",
            "value": ";".join([prior[0].get("status", ""), prior[-1].get("status", "")]),
            "evidence": rel(PRIOR_CSV),
            "detail": "Stage154 follows a skipped Stage108 complete-SAB gate and Stage153's dual-sub neutral result.",
            "next_action": "",
        },
        {
            "gate": "stage154_correctness",
            "status": "PASS" if all(row.get("status") == "PASS" for row in variants) else "FAIL",
            "metric": "tile4;bodymajor",
            "value": ";".join(row.get("correctness", "") for row in variants),
            "evidence": rel(VARIANT_CSV),
            "detail": "Both complete-SAB variants must pass target_full correctness.",
            "next_action": "Do not interpret timings if correctness fails.",
        },
        {
            "gate": "stage154_fullsab_smoke",
            "status": next((row.get("status", "") for row in comparison if row.get("metric") == "amortized_T_bootstrap_per_lane_us"), ""),
            "metric": "bodymajor_over_tile4_T_bootstrap_per_lane",
            "value": speed,
            "evidence": rel(COMPARISON_CSV),
            "detail": "Same backend, same r=6, same primary endpoint.",
            "next_action": "",
        },
        {
            "gate": "stage154_decision",
            "status": decision,
            "metric": "candidate_route",
            "value": "r6_bodymajor_fullsab_closeout",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Close or promote the bodymajor layout branch at complete-SAB level.",
            "next_action": "If neutral/rejected, route away from blind r=6 layout tuning.",
        },
    ]
    write_csv(SUMMARY_CSV, summary, SUMMARY_FIELDS)

    write_text_lf(PLAN_MD, """# Stage154 Bodymajor Full-SAB Closeout Plan

## Objective

Close the Stage108 gap by testing `MAT_TRGSW_AVX512_R6_BODYMAJOR=true` at
complete SAB level against the same H14 r=6 tile4 backend control.

## Gate

Primary endpoint: complete SAB `T_bootstrap/r`.

This is a smoke gate. A positive result requires repeated/noise/resource gates
before promotion; a neutral or negative result closes blind body-major tuning.
""")
    write_text_lf(THEORY_MD, """# Stage154 Bodymajor Full-SAB Model

Body-major changes MAT external-product loop order and locality only. It does
not change the `(h+1) * r_prec * N` SAB update count, key format, security
argument, or scalar/default SAB path.

Therefore a kernel-level result is insufficient: the only meaningful gate is
whether the full complete-SAB `T_bootstrap/r` endpoint improves over the same
H14 r=6 backend tile4 control.
""")
    write_text_lf(VARIANT_MD, f"""# MAT-RLWE SAB r=6 Bodymajor Full-SAB Closeout

## Delta

Use existing explicit `MAT_TRGSW_AVX512_R6_BODYMAJOR=true` under the current
H14 r=6 backend FromDFT-add path.

## Status

`{decision}`

This stage exists because Stage108 left complete-SAB bodymajor timing missing.
""")
    write_text_lf(OUT_MD, f"""# Stage154 Bodymajor Full-SAB Closeout

Date: 2026-07-03

## Decision

`{decision}`

## Summary

{table(summary, SUMMARY_FIELDS)}

## Prior Evidence

{table(prior, PRIOR_FIELDS)}

## Variant Results

{table(variants, VARIANT_FIELDS)}

## Comparison

{table(comparison, COMPARE_FIELDS)}

## Interpretation

The complete-SAB smoke bodymajor/tile4 result on `T_bootstrap/r` is `{speed}`.
This closes the Stage108 full-SAB evidence gap for the body-major layout branch.
""")

    block = f"""
## Stage 154: Bodymajor Full-SAB Closeout

Goal:

```text
Close the skipped Stage108 complete-SAB gate for r=6 bodymajor layout under
the current H14 backend FromDFT-add path.
```

Status:

```text
Completed. Stage154 records {decision}. Bodymajor/tile4 on the primary
`T_bootstrap/r` endpoint is {speed}.
```
"""
    upsert_stage_section(ROADMAP_MD, "## Stage 154: Bodymajor Full-SAB Closeout", block)
    append_once(GOAL_MD, "Stage154 closes r=6 bodymajor full-SAB evidence", f"""
Stage154 closes the skipped Stage108 complete-SAB bodymajor gate. Decision:
`{decision}`. The comparison is same-backend r=6 `T_bootstrap/r`.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage154 as the bodymajor full-SAB closeout", f"""
58. Treat Stage154 as the bodymajor full-SAB closeout:
    `{decision}`. It closes the Stage108 missing complete-SAB evidence for
    `MAT_TRGSW_AVX512_R6_BODYMAJOR` under the H14 r=6 backend path.
""")
    append_once(HYPOTHESIS_YAML, "H78_bodymajor_fullsab_closeout", f"""
  - id: H78_bodymajor_fullsab_closeout
    statement: >
      The r=6 body-major MAT external-product layout should only remain a
      candidate if it improves complete SAB `T_bootstrap/r` over the current
      H14 r=6 tile4 backend.
    mechanism: >
      Body-major changes MAT accumulation order and locality without changing
      SAB schedule count or selector/key semantics.
    status: stage154_fullsab_closeout
    evidence: docs/stage154_bodymajor_fullsab_closeout.md; experiments/stage154_bodymajor_fullsab_closeout_plan.md; theory_checks/stage154_bodymajor_fullsab_model.md; algorithm_variants/mat_rlwe_sab_bodymajor_fullsab_closeout.md; repro/stage154_bodymajor_fullsab_closeout/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - complete SAB correctness fails
      - `T_bootstrap/r` does not beat same-backend tile4 beyond the neutral band
""")

    existing = read_csv(RUN_LOG)
    fields = list(existing[0].keys()) if existing else [
        "run_id", "date", "commit_or_state", "stage", "backend", "command",
        "params", "seed", "status", "summary", "artifacts",
    ]
    row = {field: "" for field in fields}
    row.update({
        "run_id": "stage154-bodymajor-fullsab-closeout-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "Stage 154",
        "backend": "spqlios_avx512",
        "command": "python scripts/build_stage154_bodymajor_fullsab_closeout.py",
        "params": f"r={R_VALUE}; reps={BENCH_REPS}; H14 backend; tile4 vs bodymajor",
        "seed": "default-rng",
        "status": decision,
        "summary": "Bodymajor complete-SAB smoke closes Stage108 missing full-SAB evidence.",
        "artifacts": rel(OUT_DIR),
    })
    existing = [old for old in existing if old.get("run_id") != row["run_id"]]
    existing.append(row)
    write_csv(RUN_LOG, existing, fields)

    files = [OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, PRIOR_CSV, VARIANT_CSV, COMPARISON_CSV, SUMMARY_CSV]
    for variant in VARIANTS:
        vdir = OUT_DIR / variant["variant"]
        for name in ["clean.log", "build.log", "run.log"]:
            path = vdir / name
            if path.exists():
                files.append(path)
    manifest = []
    for path in files:
        if path.exists():
            manifest.append({"artifact": rel(path), "sha256": sha256_file(path), "bytes": str(path.stat().st_size)})
    write_csv(ARTIFACT_INDEX, manifest, ["artifact", "sha256", "bytes"])
    append_once(GLOBAL_MANIFEST, "stage154_bodymajor_fullsab_closeout", f"""
## stage154_bodymajor_fullsab_closeout

- stage: Stage 154
- status: `{decision}`
- root: `{rel(OUT_DIR)}`
- index: `{rel(ARTIFACT_INDEX)}`
""")
    append_once(CHECKLIST_MD, "Stage154 bodymajor full-SAB closeout pack", """
- [x] Stage154 bodymajor full-SAB closeout pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prior = collect_prior()
    variants = [run_variant(variant) for variant in VARIANTS]
    comparison = compare(variants)
    decision = decide(variants, comparison)
    write_outputs(prior, variants, comparison, decision)
    print(f"Stage154 bodymajor full-SAB closeout: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")


if __name__ == "__main__":
    main()
