#!/usr/bin/env python3
"""Build Stage153 dual-sub complete-SAB integration smoke gate."""

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
OUT_DIR = ROOT / "repro" / "stage153_dual_sub_fullsab_gate"

STAGE152_RAW = ROOT / "repro" / "stage152_dual_sub_kernel_gate" / "raw_results.csv"
STAGE151_VARIANTS = ROOT / "repro" / "stage151_h14_r6_fulltile_backend_smoke" / "variant_results.csv"

VARIANT_CSV = OUT_DIR / "variant_results.csv"
PROFILE_CSV = OUT_DIR / "profile_results.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
THEORY_CSV = OUT_DIR / "pair_fraction_model.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
PRIOR_CSV = OUT_DIR / "prior_evidence.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage153_dual_sub_fullsab_gate.md"
PLAN_MD = ROOT / "experiments" / "stage153_dual_sub_fullsab_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage153_dual_sub_pair_fraction_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_dual_sub_fullsab.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

R_VALUE = int(os.environ.get("STAGE153_R", "6"))
N_VALUE = int(os.environ.get("STAGE153_N", "2048"))
H_VALUE = int(os.environ.get("STAGE153_H", "39"))
R_PREC = int(os.environ.get("STAGE153_R_PREC", "7"))
BENCH_REPS = int(os.environ.get("SAB_PVW_BENCH_REPS", "1"))
JOBS = int(os.environ.get("JOBS", "8"))
RUN_SMOKE = os.environ.get("STAGE153_RUN_SMOKE", "1") not in {"0", "false", "False"}
RUN_PROFILE = os.environ.get("STAGE153_RUN_PROFILE", "1") not in {"0", "false", "False"}

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_BENCH=true "
    f"SAB_PVW_BENCH_R={R_VALUE} SAB_PVW_BENCH_REPS={BENCH_REPS}"
)

VARIANTS = [
    {"variant": "control_h14_r6_backend", "flags": BASE_FLAGS, "profile": False},
    {
        "variant": "dual_sub_h14_r6_backend",
        "flags": f"{BASE_FLAGS} SAB_PVW_DUAL_SUB_CMUX=true",
        "profile": False,
    },
    {
        "variant": "dual_sub_h14_r6_profile",
        "flags": f"{BASE_FLAGS} SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_BODY_PROFILE=true",
        "profile": True,
    },
]

VARIANT_FIELDS = [
    "variant", "status", "r", "reps", "correctness", "pvw_avg_us",
    "pvw_lane_avg_us", "scalar_repeated_avg_us", "scalar_lane_avg_us",
    "speedup_vs_scalar_repeated", "source_build_log", "source_run_log",
]
PROFILE_FIELDS = [
    "variant", "status", "lanes", "in_N", "h", "r_prec", "full_us",
    "cmux_calls", "cmux_sub_calls", "dual_sub_pair_calls",
    "expected_pair_calls", "pair_call_fraction", "pair_subop_fraction",
    "dual_sub_pair_us", "cmux_sub_us", "ncmux_calls", "mat_ep_calls",
    "source_run_log",
]
THEORY_FIELDS = [
    "metric", "value", "formula", "detail",
]
COMPARE_FIELDS = ["metric", "control", "dual", "dual_over_control", "status", "detail"]
SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
PRIOR_FIELDS = ["source", "item", "status", "metric", "value", "evidence", "detail"]

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
PROFILE_KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")


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
    stage152 = read_csv(STAGE152_RAW)
    if stage152:
        row = stage152[0]
        rows.append({
            "source": "Stage152",
            "item": "dual_sub_local_kernel",
            "status": row.get("decision", ""),
            "metric": "speedup_mean",
            "value": row.get("speedup_mean", ""),
            "evidence": rel(STAGE152_RAW),
            "detail": "Local dual-sub kernel result before full-SAB pair-fraction correction.",
        })
    variants = read_csv(STAGE151_VARIANTS)
    tile4 = next((row for row in variants if row.get("variant") == "backend_tile4_r6"), {})
    body = fnum(tile4.get("body_full_us", "0"))
    sub = fnum(tile4.get("cmux_sub_us", "0"))
    sub_share = sub / body if body else 0.0
    rows.append({
        "source": "Stage151",
        "item": "current_r6_sub_share",
        "status": "PROFILE_ONLY",
        "metric": "cmux_sub_us/body_full_us",
        "value": fmt(sub_share),
        "evidence": rel(STAGE151_VARIANTS),
        "detail": "Subtraction share must be multiplied by the Stage153 pairable fraction.",
    })
    return rows


def run_variant(variant: Dict[str, object]) -> Dict[str, str]:
    name = str(variant["variant"])
    flags = str(variant["flags"])
    vdir = OUT_DIR / name
    vdir.mkdir(parents=True, exist_ok=True)
    build_log = vdir / "build.log"
    run_log = vdir / "run.log"
    clean_log = vdir / "clean.log"
    if RUN_SMOKE and (not variant.get("profile") or RUN_PROFILE):
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
    row = {
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
    return row


def parse_profile() -> Dict[str, str]:
    name = "dual_sub_h14_r6_profile"
    run_log = OUT_DIR / name / "run.log"
    text = run_log.read_text(encoding="utf-8", errors="replace") if run_log.exists() else ""
    lines = [line for line in text.splitlines() if "SAB_PVW_BODY_PROFILE sample" in line]
    kv = dict(PROFILE_KV_RE.findall(lines[-1])) if lines else {}
    expected_pair_calls = (H_VALUE + 1) * ((1 << R_PREC) - 1)
    cmux_calls = fnum(kv.get("cmux_calls", "0"))
    pair_calls = fnum(kv.get("dual_sub_pair_calls", "0"))
    pair_call_fraction = pair_calls / cmux_calls if cmux_calls else 0.0
    pair_subop_fraction = (2.0 * pair_calls) / cmux_calls if cmux_calls else 0.0
    return {
        "variant": name,
        "status": "PASS" if pair_calls == expected_pair_calls else "MISMATCH",
        "lanes": kv.get("lanes", ""),
        "in_N": kv.get("in_N", ""),
        "h": kv.get("h", ""),
        "r_prec": kv.get("r_prec", ""),
        "full_us": kv.get("full_us", ""),
        "cmux_calls": kv.get("cmux_calls", ""),
        "cmux_sub_calls": kv.get("cmux_sub_calls", ""),
        "dual_sub_pair_calls": kv.get("dual_sub_pair_calls", ""),
        "expected_pair_calls": str(expected_pair_calls),
        "pair_call_fraction": fmt(pair_call_fraction),
        "pair_subop_fraction": fmt(pair_subop_fraction),
        "dual_sub_pair_us": kv.get("dual_sub_pair_us", ""),
        "cmux_sub_us": kv.get("cmux_sub_us", ""),
        "ncmux_calls": kv.get("ncmux_calls", ""),
        "mat_ep_calls": kv.get("mat_ep_calls", ""),
        "source_run_log": rel(run_log),
    }


def build_theory(prior_rows: List[Dict[str, str]], profile: Dict[str, str]) -> List[Dict[str, str]]:
    local_speed = fnum(next((row.get("value", "0") for row in prior_rows if row.get("item") == "dual_sub_local_kernel"), "0"))
    sub_share = fnum(next((row.get("value", "0") for row in prior_rows if row.get("item") == "current_r6_sub_share"), "0"))
    pair_ops_fraction = fnum(profile.get("pair_subop_fraction", "0"))
    saved_fraction = sub_share * pair_ops_fraction * (1.0 - 1.0 / local_speed) if local_speed > 0 else 0.0
    body_bound = 1.0 / (1.0 - saved_fraction) if saved_fraction < 1.0 else float("inf")
    return [
        {
            "metric": "pair_calls_per_full_sab",
            "value": profile.get("dual_sub_pair_calls", ""),
            "formula": "(h+1)*(2^r_prec-1)",
            "detail": f"Expected {(H_VALUE + 1) * ((1 << R_PREC) - 1)} for h={H_VALUE}, r_prec={R_PREC}.",
        },
        {
            "metric": "pair_subop_fraction",
            "value": profile.get("pair_subop_fraction", ""),
            "formula": "2*(2^r_prec-1)/(r_prec*N)",
            "detail": "Only this fraction of CMUX/NCMUX subtraction outputs can use the dual-sub shared input.",
        },
        {
            "metric": "stage152_corrected_body_speedup_bound",
            "value": fmt(body_bound),
            "formula": "1/(1-sub_share*pair_subop_fraction*(1-1/local_speedup))",
            "detail": "This corrects Stage152's local Amdahl projection by the actual pairable fraction.",
        },
    ]


def compare(variants: List[Dict[str, str]], theory: List[Dict[str, str]]) -> List[Dict[str, str]]:
    control = next((row for row in variants if row.get("variant") == "control_h14_r6_backend"), {})
    dual = next((row for row in variants if row.get("variant") == "dual_sub_h14_r6_backend"), {})
    control_us = fnum(control.get("pvw_avg_us", "0"))
    dual_us = fnum(dual.get("pvw_avg_us", "0"))
    full_speed = control_us / dual_us if control_us and dual_us else 0.0
    control_lane = fnum(control.get("pvw_lane_avg_us", "0"))
    dual_lane = fnum(dual.get("pvw_lane_avg_us", "0"))
    lane_speed = control_lane / dual_lane if control_lane and dual_lane else 0.0
    bound = fnum(next((row.get("value", "0") for row in theory if row.get("metric") == "stage152_corrected_body_speedup_bound"), "0"))
    return [
        {
            "metric": "full_sab_pvw_us",
            "control": control.get("pvw_avg_us", ""),
            "dual": dual.get("pvw_avg_us", ""),
            "dual_over_control": fmt(full_speed),
            "status": "PROMOTE" if full_speed >= 1.02 else ("NEUTRAL" if full_speed >= 0.99 else "REJECT"),
            "detail": "Complete SAB wall-clock smoke, not repeated statistics.",
        },
        {
            "metric": "amortized_T_bootstrap_per_lane_us",
            "control": control.get("pvw_lane_avg_us", ""),
            "dual": dual.get("pvw_lane_avg_us", ""),
            "dual_over_control": fmt(lane_speed),
            "status": "PROMOTE" if lane_speed >= 1.02 else ("NEUTRAL" if lane_speed >= 0.99 else "REJECT"),
            "detail": "Primary MAT-RLWE endpoint for the integration smoke.",
        },
        {
            "metric": "corrected_theory_bound",
            "control": "1.000000",
            "dual": fmt(bound),
            "dual_over_control": fmt(bound),
            "status": "LIMITED",
            "detail": "Pairable-fraction corrected bound predicts only a very small body-level opportunity.",
        },
    ]


def decide(summary_inputs: Dict[str, object]) -> str:
    variants: List[Dict[str, str]] = summary_inputs["variants"]  # type: ignore[assignment]
    profile: Dict[str, str] = summary_inputs["profile"]  # type: ignore[assignment]
    comparison: List[Dict[str, str]] = summary_inputs["comparison"]  # type: ignore[assignment]
    correctness_ok = all(row.get("status") == "PASS" for row in variants if row.get("variant") != "dual_sub_h14_r6_profile")
    profile_ok = profile.get("status") == "PASS"
    speed = fnum(next((row.get("dual_over_control", "0") for row in comparison if row.get("metric") == "amortized_T_bootstrap_per_lane_us"), "0"))
    if not correctness_ok:
        return "FAIL_STAGE153_DUAL_SUB_FULLSAB_CORRECTNESS"
    if not profile_ok:
        return "FAIL_STAGE153_DUAL_SUB_PAIR_COUNT_MISMATCH"
    if speed >= 1.02:
        return "SMOKE_STAGE153_DUAL_SUB_FULLSAB_POSITIVE_REPEATED_REQUIRED"
    if speed >= 0.99:
        return "NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED"
    return "REJECT_STAGE153_DUAL_SUB_FULLSAB_SLOWER"


def write_outputs(prior_rows: List[Dict[str, str]], variants: List[Dict[str, str]],
    profile: Dict[str, str], theory: List[Dict[str, str]],
    comparison: List[Dict[str, str]], decision: str) -> None:
    write_csv(PRIOR_CSV, prior_rows, PRIOR_FIELDS)
    write_csv(VARIANT_CSV, variants, VARIANT_FIELDS)
    write_csv(PROFILE_CSV, [profile], PROFILE_FIELDS)
    write_csv(THEORY_CSV, theory, THEORY_FIELDS)
    write_csv(COMPARISON_CSV, comparison, COMPARE_FIELDS)
    speed = next((row.get("dual_over_control", "") for row in comparison if row.get("metric") == "amortized_T_bootstrap_per_lane_us"), "")
    bound = next((row.get("value", "") for row in theory if row.get("metric") == "stage152_corrected_body_speedup_bound"), "")
    summary_rows = [
        {
            "gate": "stage153_build_correctness",
            "status": "PASS" if all(row.get("status") == "PASS" for row in variants if row.get("variant") != "dual_sub_h14_r6_profile") else "FAIL",
            "metric": "control_and_dual_correctness",
            "value": ";".join(row.get("correctness", "") for row in variants if row.get("variant") != "dual_sub_h14_r6_profile"),
            "evidence": rel(VARIANT_CSV),
            "detail": "Both control and dual-sub complete SAB smoke must pass target_full correctness.",
            "next_action": "",
        },
        {
            "gate": "stage153_pair_count",
            "status": profile.get("status", ""),
            "metric": "dual_sub_pair_calls/expected",
            "value": f"{profile.get('dual_sub_pair_calls', '')}/{profile.get('expected_pair_calls', '')}",
            "evidence": rel(PROFILE_CSV),
            "detail": "Dynamic pair count must match (h+1)*(2^r_prec-1).",
            "next_action": "",
        },
        {
            "gate": "stage153_corrected_theory_bound",
            "status": "LIMITED",
            "metric": "corrected_body_speedup_bound",
            "value": bound,
            "evidence": rel(THEORY_CSV),
            "detail": "Stage152 local speedup must be multiplied by the actual pairable fraction.",
            "next_action": "Do not spend more effort on H14-C3 unless a broader pairing schedule is found.",
        },
        {
            "gate": "stage153_fullsab_smoke",
            "status": next((row.get("status", "") for row in comparison if row.get("metric") == "amortized_T_bootstrap_per_lane_us"), ""),
            "metric": "dual_over_control_T_bootstrap_per_lane",
            "value": speed,
            "evidence": rel(COMPARISON_CSV),
            "detail": "Complete SAB smoke compares dual-sub against the same H14 r=6 backend path.",
            "next_action": "",
        },
        {
            "gate": "stage153_decision",
            "status": decision,
            "metric": "candidate_route",
            "value": "h14_c3_dual_sub_fullsab",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage153 either promotes, neutralizes, or rejects the full-SAB dual-sub integration candidate.",
            "next_action": "Route to a broader schedule-level candidate if neutral or rejected.",
        },
    ]
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)

    write_text_lf(PLAN_MD, f"""# Stage153 Dual-Sub Full-SAB Gate Plan

## Objective

Integrate the Stage152 shared-input dual-sub kernel behind `SAB_PVW_DUAL_SUB_CMUX`
and test it at the complete SAB endpoint `T_bootstrap/r`.

## Gates

- Correctness: control and dual-sub complete SAB smoke must pass.
- Pair count: dynamic `dual_sub_pair_calls` must equal `(h+1)*(2^r_prec-1)`.
- Performance: compare dual-sub against the same H14 r=6 backend path.
- Claim boundary: this is a smoke gate; repeated statistics are required for
  any positive promotion.
""")
    write_text_lf(THEORY_MD, f"""# Stage153 Dual-Sub Pair-Fraction Model

The paired butterfly update computes:

```text
d_n = Aut(p[in][N-power+j]) - p[in][j]
d_d = p[in][j] - p[in][j+power]
```

and then runs the same two MAT external products and additions as the original
NCMUX/direct-CMUX pair.

The important correction is that only `sum_bit 2^bit = 2^r_prec-1` positions
per RGSW monomial have this shared-input pairing. The complete binary SAB path
has `(h+1)*r_prec*N` CMUX/NCMUX updates. Therefore the pairable subtraction
output fraction is:

```text
2*(2^r_prec-1)/(r_prec*N)
```

For `N={N_VALUE}` and `r_prec={R_PREC}`, this is
`{next((row.get('value','') for row in theory if row.get('metric') == 'pair_subop_fraction'), '')}`.
This sharply limits the effect of the Stage152 local dual-sub speedup.

{table(theory, THEORY_FIELDS)}
""")
    write_text_lf(VARIANT_MD, f"""# MAT-RLWE SAB Dual-Sub Full-SAB Candidate

## Delta

`SAB_PVW_DUAL_SUB_CMUX=true` pairs the first `power` direct CMUX updates with
the `power` NCMUX updates in each `RGSW_monomial_mul_state` bit. It does not
change the scalar SAB path, selector format, external-product count, output
semantics, or default build.

## Status

`{decision}`

The candidate is now implemented as an explicit flag. Stage153 shows the
pairable fraction is the limiting factor; full promotion requires repeated
`T_bootstrap/r` evidence above the neutral band.
""")
    write_text_lf(OUT_MD, f"""# Stage153 Dual-Sub Full-SAB Gate

Date: 2026-07-03

## Decision

`{decision}`

## Summary

{table(summary_rows, SUMMARY_FIELDS)}

## Prior Evidence

{table(prior_rows, PRIOR_FIELDS)}

## Variant Results

{table(variants, VARIANT_FIELDS)}

## Profile Result

{table([profile], PROFILE_FIELDS)}

## Pair-Fraction Model

{table(theory, THEORY_FIELDS)}

## Comparison

{table(comparison, COMPARE_FIELDS)}

## Interpretation

The full-SAB smoke result is `{speed}` on the primary `T_bootstrap/r` endpoint.
The dynamic pair count confirms `{profile.get('dual_sub_pair_calls', '')}`
pair sites, so the Stage152 local kernel win applies to only
`{profile.get('pair_subop_fraction', '')}` of subtraction outputs. This is why
the candidate is not allowed to become a final bootstrapping claim from local
kernel evidence alone.
""")

    block = f"""
## Stage 153: Dual-Sub Full-SAB Gate

Goal:

```text
Integrate the Stage152 shared-input dual-sub kernel behind an explicit flag and
test complete SAB `T_bootstrap/r` against the same H14 r=6 backend control.
```

Status:

```text
Completed. Stage153 records {decision}. The full-SAB smoke dual/control
speedup on `T_bootstrap/r` is {speed}. Dynamic pair calls are
{profile.get('dual_sub_pair_calls', '')}/{profile.get('expected_pair_calls', '')}, and the corrected body-level
bound is {bound}. The key conclusion is that H14-C3 is pair-fraction limited.
```
"""
    upsert_stage_section(ROADMAP_MD, "## Stage 153: Dual-Sub Full-SAB Gate", block)
    append_once(GOAL_MD, "Stage153 integrates dual-sub as a complete-SAB smoke gate", f"""
Stage153 integrates the Stage152 dual-sub kernel behind `SAB_PVW_DUAL_SUB_CMUX`
and tests complete SAB `T_bootstrap/r`. Decision: `{decision}`. The route is
bounded by the pairable fraction, not by the isolated dual-sub kernel speed.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage153 as the dual-sub full-SAB gate", f"""
57. Treat Stage153 as the dual-sub full-SAB gate:
    `{decision}`. The explicit flag path preserves scalar/default SAB and
    confirms the pairable fraction `(h+1)*(2^r_prec-1)`, but this fraction is
    too small for a strong full-SAB claim unless a broader pairing schedule is
    found.
""")
    append_once(HYPOTHESIS_YAML, "H77_dual_sub_fullsab_pair_fraction", f"""
  - id: H77_dual_sub_fullsab_pair_fraction
    statement: >
      The H14-C3 shared-input dual-subtraction optimization should improve
      complete SAB only if enough butterfly positions can be paired.
    mechanism: >
      The integrated path computes the NCMUX subtraction and the adjacent
      direct-CMUX subtraction in one pass over `p[in][j]`, but only
      `sum_bit 2^bit` positions per RGSW monomial have this exact pairing.
    status: stage153_pair_fraction_limited
    evidence: docs/stage153_dual_sub_fullsab_gate.md; experiments/stage153_dual_sub_fullsab_gate_plan.md; theory_checks/stage153_dual_sub_pair_fraction_model.md; algorithm_variants/mat_rlwe_sab_dual_sub_fullsab.md; repro/stage153_dual_sub_fullsab_gate/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - complete SAB correctness fails
      - dynamic pair count differs from `(h+1)*(2^r_prec-1)`
      - full SAB `T_bootstrap/r` does not improve beyond the neutral band
""")

    existing = read_csv(RUN_LOG)
    run_fields = list(existing[0].keys()) if existing else [
        "run_id", "date", "commit_or_state", "stage", "backend", "command",
        "params", "seed", "status", "summary", "artifacts",
    ]
    row = {field: "" for field in run_fields}
    row.update({
        "run_id": "stage153-dual-sub-fullsab-gate-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "Stage 153",
        "backend": "spqlios_avx512",
        "command": "python scripts/build_stage153_dual_sub_fullsab_gate.py",
        "params": f"r={R_VALUE}; reps={BENCH_REPS}; H14 backend; control vs SAB_PVW_DUAL_SUB_CMUX; profile={RUN_PROFILE}",
        "seed": "default-rng",
        "status": decision,
        "summary": "Dual-sub complete-SAB smoke and pair-fraction correction gate.",
        "artifacts": rel(OUT_DIR),
    })
    existing = [old for old in existing if old.get("run_id") != row["run_id"]]
    existing.append(row)
    write_csv(RUN_LOG, existing, run_fields)

    files = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD, PRIOR_CSV, VARIANT_CSV,
        PROFILE_CSV, THEORY_CSV, COMPARISON_CSV, SUMMARY_CSV,
    ]
    for variant in VARIANTS:
        vdir = OUT_DIR / str(variant["variant"])
        for name in ["clean.log", "build.log", "run.log"]:
            path = vdir / name
            if path.exists():
                files.append(path)
    manifest_rows = []
    for path in files:
        if path.exists():
            manifest_rows.append({
                "artifact": rel(path),
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size),
            })
    write_csv(ARTIFACT_INDEX, manifest_rows, ["artifact", "sha256", "bytes"])
    append_once(GLOBAL_MANIFEST, "stage153_dual_sub_fullsab_gate", f"""
## stage153_dual_sub_fullsab_gate

- stage: Stage 153
- status: `{decision}`
- root: `{rel(OUT_DIR)}`
- index: `{rel(ARTIFACT_INDEX)}`
""")
    append_once(CHECKLIST_MD, "Stage153 dual-sub full-SAB gate pack", """
- [x] Stage153 dual-sub full-SAB gate pack recorded.
""")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prior_rows = collect_prior()
    variants = [run_variant(variant) for variant in VARIANTS if (not variant.get("profile") or RUN_PROFILE)]
    profile = parse_profile() if RUN_PROFILE else {}
    theory = build_theory(prior_rows, profile)
    comparison = compare(variants, theory)
    decision = decide({"variants": variants, "profile": profile, "comparison": comparison})
    write_outputs(prior_rows, variants, profile, theory, comparison, decision)
    print(f"Stage153 dual-sub full-SAB gate: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")


if __name__ == "__main__":
    main()
