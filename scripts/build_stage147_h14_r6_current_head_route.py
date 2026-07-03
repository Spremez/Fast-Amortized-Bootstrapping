#!/usr/bin/env python3
"""Build Stage147 current-head H14 r=6 backend-route gate."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage147_h14_r6_current_head_route"
STAGE146_SUMMARY = ROOT / "repro" / "stage146_r4_unrolled_variance_attribution" / "summary.csv"
STAGE89_SUMMARY = ROOT / "repro" / "stage89_h14_promotion_policy_integration" / "summary.csv"

VARIANT_RESULTS_CSV = OUT_DIR / "variant_results.csv"
VARIANT_COMPARISON_CSV = OUT_DIR / "variant_comparison.csv"
PRIOR_CSV = OUT_DIR / "prior_route_inputs.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage147_h14_r6_current_head_route.md"
PLAN_MD = ROOT / "experiments" / "stage147_h14_r6_current_head_route_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage147_h14_route_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_h14_r6_backend_route.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

JOBS = int(os.environ.get("JOBS", "8"))
RUN_SMOKE = os.environ.get("STAGE147_RUN_SMOKE", "1") not in {"0", "false", "False"}
R_VALUE = int(os.environ.get("STAGE147_R", "6"))
BENCH_REPS = int(os.environ.get("SAB_PVW_BENCH_REPS", "1"))

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BENCH=true "
    f"SAB_PVW_BENCH_R={R_VALUE} SAB_PVW_BENCH_REPS={BENCH_REPS} "
    "SAB_PVW_BODY_PROFILE=true"
)
VARIANTS = [
    {
        "variant": "wrapper_fused_from_dft_add_r6",
        "flags": f"{BASE_FLAGS} SAB_PVW_FUSED_FROM_DFT_ADD=true",
    },
    {
        "variant": "backend_from_dft_add_r6",
        "flags": f"{BASE_FLAGS} SAB_PVW_BACKEND_FROM_DFT_ADD=true",
    },
]

PRIOR_FIELDS = ["source", "gate", "status", "metric", "value", "evidence", "detail"]
VARIANT_FIELDS = [
    "variant", "status", "r", "h", "r_prec", "lanes", "in_N",
    "bench_pvw_us", "bench_pvw_lane_us", "scalar_repeated_us",
    "scalar_lane_us", "speedup_vs_scalar_repeated", "body_full_us",
    "mat_ep_calls", "mat_ep_us", "mat_ep_share", "cmux_calls", "cmux_us",
    "cmux_sub_us", "cmux_from_dft_us", "cmux_add_us", "ncmux_calls",
    "ncmux_us", "ncmux_auto_us", "sub_a_calls", "sub_a_us",
    "copyback_calls", "copyback_us", "source_log",
]
COMPARE_FIELDS = ["metric", "wrapper", "backend", "backend_over_wrapper", "status", "detail"]
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
PROFILE_KV_RE = re.compile(r"([A-Za-z0-9_]+)=([^ ]+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"


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
        sanitize(proc.stdout).rstrip(),
        "--- stderr ---",
        sanitize(proc.stderr).rstrip(),
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


def collect_prior_inputs() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for source, path in [("Stage146", STAGE146_SUMMARY), ("Stage89", STAGE89_SUMMARY)]:
        found = read_csv(path)
        if not found:
            rows.append({
                "source": source, "gate": "missing", "status": "MISSING",
                "metric": "file", "value": rel(path), "evidence": rel(path),
                "detail": "Prior input not found.",
            })
            continue
        for row in found:
            if row.get("gate", "").endswith("decision") or row.get("gate") in {
                "stage89_performance_policy", "stage89_noise_resource_guard",
            }:
                rows.append({
                    "source": source,
                    "gate": row.get("gate", ""),
                    "status": row.get("status", ""),
                    "metric": row.get("metric", ""),
                    "value": row.get("value", ""),
                    "evidence": row.get("evidence", rel(path)),
                    "detail": row.get("detail", ""),
                })
    return rows


def parse_variant_log(variant: str, log: Path) -> Dict[str, str]:
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    correctness = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    profile_line = ""
    for line in text.splitlines():
        if "SAB_PVW_BODY_PROFILE sample" in line:
            profile_line = line
    kv = dict(PROFILE_KV_RE.findall(profile_line))
    ok = correctness and correctness.group("status") == "Pass" and bench and kv
    status = "PASS" if ok else "FAIL"
    body_full = fnum(kv.get("full_us", "0"))
    mat_ep = fnum(kv.get("mat_ep_us", "0"))
    return {
        "variant": variant,
        "status": status,
        "r": correctness.group("r") if correctness else "",
        "h": correctness.group("h") if correctness else "",
        "r_prec": correctness.group("r_prec") if correctness else "",
        "lanes": kv.get("lanes", ""),
        "in_N": kv.get("in_N", ""),
        "bench_pvw_us": bench.group("pvw_avg_us") if bench else "",
        "bench_pvw_lane_us": bench.group("pvw_lane_avg_us") if bench else "",
        "scalar_repeated_us": bench.group("scalar_repeated_avg_us") if bench else "",
        "scalar_lane_us": bench.group("scalar_lane_avg_us") if bench else "",
        "speedup_vs_scalar_repeated": bench.group("speedup") if bench else "",
        "body_full_us": kv.get("full_us", ""),
        "mat_ep_calls": kv.get("mat_ep_calls", ""),
        "mat_ep_us": kv.get("mat_ep_us", ""),
        "mat_ep_share": fmt(mat_ep / body_full if body_full else 0.0),
        "cmux_calls": kv.get("cmux_calls", ""),
        "cmux_us": kv.get("cmux_us", ""),
        "cmux_sub_us": kv.get("cmux_sub_us", ""),
        "cmux_from_dft_us": kv.get("cmux_from_dft_us", ""),
        "cmux_add_us": kv.get("cmux_add_us", ""),
        "ncmux_calls": kv.get("ncmux_calls", ""),
        "ncmux_us": kv.get("ncmux_us", ""),
        "ncmux_auto_us": kv.get("ncmux_auto_us", ""),
        "sub_a_calls": kv.get("sub_a_calls", ""),
        "sub_a_us": kv.get("sub_a_us", ""),
        "copyback_calls": kv.get("copyback_calls", ""),
        "copyback_us": kv.get("copyback_us", ""),
        "source_log": rel(log),
    }


def run_variants() -> Tuple[bool, List[Dict[str, str]]]:
    if not RUN_SMOKE:
        cached = read_csv(VARIANT_RESULTS_CSV)
        return bool(cached), cached
    rows: List[Dict[str, str]] = []
    ok = True
    for config in VARIANTS:
        variant = config["variant"]
        build_log = OUT_DIR / f"build_{variant}.log"
        build = run_logged(
            f"make clean >/dev/null 2>&1 || true && make {config['flags']} -j{JOBS}",
            build_log,
            timeout=900,
        )
        ok = ok and build.returncode == 0
        run_log = OUT_DIR / f"run_{variant}.log"
        if build.returncode == 0:
            proc = run_logged("./main", run_log, timeout=1500)
            ok = ok and proc.returncode == 0
        else:
            write_text_lf(run_log, "variant run skipped because build failed\n")
            ok = False
        parsed = parse_variant_log(variant, run_log)
        ok = ok and parsed["status"] == "PASS"
        rows.append(parsed)
    run_logged("make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.log", timeout=60)
    return ok, rows


def compare_variants(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    wrapper = next((row for row in rows if row["variant"] == "wrapper_fused_from_dft_add_r6"), None)
    backend = next((row for row in rows if row["variant"] == "backend_from_dft_add_r6"), None)
    if not wrapper or not backend:
        return [{
            "metric": "variant_rows",
            "wrapper": "missing",
            "backend": "missing",
            "backend_over_wrapper": "0",
            "status": "FAIL",
            "detail": "Expected wrapper and backend rows.",
        }]

    def speedup(field: str) -> float:
        denom = fnum(backend.get(field, "0"))
        return fnum(wrapper.get(field, "0")) / denom if denom else 0.0

    def delta(field: str) -> float:
        return fnum(backend.get(field, "0")) - fnum(wrapper.get(field, "0"))

    rows_out = [
        {
            "metric": "correctness",
            "wrapper": wrapper["status"],
            "backend": backend["status"],
            "backend_over_wrapper": "1" if wrapper["status"] == "PASS" and backend["status"] == "PASS" else "0",
            "status": "PASS" if wrapper["status"] == "PASS" and backend["status"] == "PASS" else "FAIL",
            "detail": "Both current-head r=6 explicit variants must pass full-SAB correctness.",
        },
        {
            "metric": "pvw_lane_speedup_backend_over_wrapper",
            "wrapper": wrapper["bench_pvw_lane_us"],
            "backend": backend["bench_pvw_lane_us"],
            "backend_over_wrapper": fmt(speedup("bench_pvw_lane_us")),
            "status": "SMOKE_ONLY",
            "detail": "Primary current-head smoke metric is T_bootstrap/r.",
        },
        {
            "metric": "body_full_speedup_backend_over_wrapper",
            "wrapper": wrapper["body_full_us"],
            "backend": backend["body_full_us"],
            "backend_over_wrapper": fmt(speedup("body_full_us")),
            "status": "PROFILE_ONLY",
            "detail": "Instrumented body hot-path comparison.",
        },
        {
            "metric": "from_dft_speedup_backend_over_wrapper",
            "wrapper": wrapper["cmux_from_dft_us"],
            "backend": backend["cmux_from_dft_us"],
            "backend_over_wrapper": fmt(speedup("cmux_from_dft_us")),
            "status": "PROFILE_ONLY",
            "detail": "Backend callback should reduce inverse DFT materialization/add lifetime.",
        },
        {
            "metric": "mat_ep_speedup_backend_over_wrapper",
            "wrapper": wrapper["mat_ep_us"],
            "backend": backend["mat_ep_us"],
            "backend_over_wrapper": fmt(speedup("mat_ep_us")),
            "status": "PROFILE_ONLY",
            "detail": "MAT EP should be the same algorithmic kernel across these two variants.",
        },
        {
            "metric": "speedup_vs_scalar_wrapper",
            "wrapper": wrapper["speedup_vs_scalar_repeated"],
            "backend": "",
            "backend_over_wrapper": wrapper["speedup_vs_scalar_repeated"],
            "status": "SMOKE_ONLY",
            "detail": "Wrapper variant speedup against repeated scalar SAB.",
        },
        {
            "metric": "speedup_vs_scalar_backend",
            "wrapper": "",
            "backend": backend["speedup_vs_scalar_repeated"],
            "backend_over_wrapper": backend["speedup_vs_scalar_repeated"],
            "status": "SMOKE_ONLY",
            "detail": "Backend variant speedup against repeated scalar SAB.",
        },
        {
            "metric": "mat_ep_calls_equal",
            "wrapper": wrapper["mat_ep_calls"],
            "backend": backend["mat_ep_calls"],
            "backend_over_wrapper": "1" if wrapper["mat_ep_calls"] == backend["mat_ep_calls"] else "0",
            "status": "PASS" if wrapper["mat_ep_calls"] == backend["mat_ep_calls"] else "FAIL",
            "detail": "Backend materialization must not change SAB schedule counts.",
        },
        {
            "metric": "copyback_zero",
            "wrapper": wrapper["copyback_calls"],
            "backend": backend["copyback_calls"],
            "backend_over_wrapper": "1" if wrapper["copyback_calls"] == "0" and backend["copyback_calls"] == "0" else "0",
            "status": "PASS" if wrapper["copyback_calls"] == "0" and backend["copyback_calls"] == "0" else "FAIL",
            "detail": "Active-buffer route should keep copyback eliminated.",
        },
        {
            "metric": "cmux_add_delta_backend_minus_wrapper",
            "wrapper": wrapper["cmux_add_us"],
            "backend": backend["cmux_add_us"],
            "backend_over_wrapper": fmt(delta("cmux_add_us")),
            "status": "PROFILE_ONLY",
            "detail": "Both variants are expected to keep explicit add timing near zero under fused epilogue.",
        },
    ]
    return rows_out


def build_summary(
    prior_rows: List[Dict[str, str]],
    run_ok: bool,
    comparison_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    prior_ok = any(
        row["source"] == "Stage146"
        and row["gate"] == "stage146_decision"
        and row["status"].startswith("PASS_STAGE146")
        for row in prior_rows
    ) and any(
        row["source"] == "Stage89"
        and row["gate"] == "stage89_decision"
        and row["status"].startswith("PASS_STAGE89")
        for row in prior_rows
    )
    correctness_ok = any(row["metric"] == "correctness" and row["status"] == "PASS" for row in comparison_rows)
    count_ok = all(
        row["status"] == "PASS"
        for row in comparison_rows
        if row["metric"] in {"mat_ep_calls_equal", "copyback_zero"}
    )
    lane_ratio = 0.0
    from_dft_ratio = 0.0
    backend_scalar = 0.0
    for row in comparison_rows:
        if row["metric"] == "pvw_lane_speedup_backend_over_wrapper":
            lane_ratio = fnum(row["backend_over_wrapper"])
        elif row["metric"] == "from_dft_speedup_backend_over_wrapper":
            from_dft_ratio = fnum(row["backend_over_wrapper"])
        elif row["metric"] == "speedup_vs_scalar_backend":
            backend_scalar = fnum(row["backend_over_wrapper"])

    if prior_ok and run_ok and correctness_ok and count_ok and lane_ratio > 1.01 and from_dft_ratio > 1.01:
        decision = "PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT"
        next_action = "Run Stage148 repeated/noise/resource refresh for current-head H14 r=6 backend before any stronger claim."
    elif prior_ok and run_ok and correctness_ok and count_ok and backend_scalar > 1.0:
        decision = "WEAK_STAGE147_H14_R6_CURRENT_HEAD_POSITIVE_BUT_BACKEND_EDGE_NOT_CONFIRMED"
        next_action = "Do not rely on backend-over-wrapper; either repeat with higher stats or re-profile materialization."
    elif run_ok and correctness_ok:
        decision = "NEUTRAL_STAGE147_H14_R6_ROUTE_NOT_SELECTED"
        next_action = "Return to candidate generation; current-head H14 r=6 smoke is not sufficient."
    else:
        decision = "FAIL_STAGE147_H14_R6_CURRENT_HEAD_REPAIR_REQUIRED"
        next_action = "Repair current-head wrapper/backend r=6 route before continuing this branch."

    return [
        {
            "gate": "stage147_prior_route",
            "status": "PASS" if prior_ok else "WEAK_OR_MISSING",
            "metric": "stage146;stage89",
            "value": "r4_unrolled_not_promoted;h14_r6_preferred_explicit",
            "evidence": f"{rel(STAGE146_SUMMARY)}; {rel(STAGE89_SUMMARY)}",
            "detail": "Stage147 is justified only because r4-unrolled was not promoted and H14 r=6 was the prior preferred explicit route.",
            "next_action": "",
        },
        {
            "gate": "stage147_current_head_smoke",
            "status": "PASS" if run_ok and correctness_ok else "FAIL",
            "metric": "wrapper;backend",
            "value": "current_head_r6_body_profile_smoke",
            "evidence": rel(VARIANT_RESULTS_CSV),
            "detail": "Current head builds and runs wrapper/backend explicit r=6 full-SAB profile smoke.",
            "next_action": "",
        },
        {
            "gate": "stage147_profile_attribution",
            "status": "PASS" if count_ok else "FAIL",
            "metric": "lane_ratio;from_dft_ratio;backend_scalar",
            "value": f"{fmt(lane_ratio)};{fmt(from_dft_ratio)};{fmt(backend_scalar)}",
            "evidence": rel(VARIANT_COMPARISON_CSV),
            "detail": "Profile smoke attributes current-head backend edge and confirms unchanged schedule counts.",
            "next_action": "",
        },
        {
            "gate": "stage147_decision",
            "status": decision,
            "metric": "route",
            "value": "h14_r6_backend_current_head",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage147 chooses the next research branch without modifying scalar/default behavior.",
            "next_action": next_action,
        },
    ]


def write_docs(
    prior_rows: List[Dict[str, str]],
    variant_rows: List[Dict[str, str]],
    comparison_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    decision = summary_rows[-1]["status"]
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage147 H14 r=6 Current-Head Route Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "After Stage146 keeps r4-unrolled explicit-only, verify whether the prior H14 backend FromDFT-add r=6 route is still the correct next candidate on current head.",
        "",
        "## Gate",
        "",
        "- Compare wrapper fused FromDFT-add and backend FromDFT-add under the same r=6 MAT-RLWE full-SAB shape.",
        "- Use `T_bootstrap/r` as the primary smoke metric.",
        "- Use `SAB_PVW_BODY_PROFILE=true` only for attribution, not final latency claims.",
        "- Keep scalar SAB and default PVW/MAT-SAB behavior unchanged.",
        "",
        "## Promotion Boundary",
        "",
        "A one-run current-head smoke can only route Stage148. It cannot replace Stage88 repeated/noise/resource gates or establish final paper-level speedup.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage147 H14 Route Model",
        "",
        "Date: 2026-07-03",
        "",
        "The r4-unrolled branch improves a local MAT EP but loses stability at complete-SAB `T_bootstrap/r`. Stage147 therefore returns to the stronger prior mechanism: reduce inverse DFT materialization/add lifetime at the backend boundary for r=6, where Stage88/89 already recorded repeated full-SAB evidence.",
        "",
        "This is still a constant-factor implementation route, not a new asymptotic SAB algorithm. The algorithmic object remains MAT-RLWE/r-body SAB, and the endpoint remains amortized per-lane bootstrapping time.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB H14 r=6 Backend Route",
        "",
        "Date: 2026-07-03",
        "",
        "This variant uses r=6 MAT-RLWE/PVW lanes with the existing active-buffer sparse schedule and the backend FromDFT-add materialization callback.",
        "",
        "It is an explicit route behind `SAB_PVW_BACKEND_FROM_DFT_ADD=true` and `MAT_TRGSW_AVX512_RGT4_FUSED=true`. It does not alter scalar `sab_rlwe_bootstrap` or default PVW/MAT-SAB behavior.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage147 H14 r=6 Current-Head Route",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "## Summary Gates",
        "",
        table(summary_rows, ["gate", "status", "metric", "value", "detail", "next_action"]),
        "",
        "## Prior Route Inputs",
        "",
        table(prior_rows, PRIOR_FIELDS),
        "",
        "## Variant Results",
        "",
        table(variant_rows, VARIANT_FIELDS),
        "",
        "## Comparison",
        "",
        table(comparison_rows, COMPARE_FIELDS),
        "",
        "## Interpretation",
        "",
        "Stage147 is a route-selection gate. It can justify a current-head high-stat refresh for H14 r=6 backend, but it does not promote defaults or make a final SAB acceleration claim.",
    ]) + "\n")


def update_longform(summary_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    block = f"""
## Stage 147: H14 r=6 Current-Head Route

Goal:

```text
After the r4-unrolled branch remains explicit-only, verify whether the
previously preferred H14 backend FromDFT-add r=6 path is still the right
current-head candidate branch.
```

Status:

```text
Completed. Stage147 records {decision}. It runs a current-head wrapper/backend
r=6 full-SAB profile smoke and preserves scalar/default behavior.
```
"""
    append_once(ROADMAP_MD, "## Stage 147: H14 r=6 Current-Head Route", block)
    append_once(GOAL_MD, "Stage147 returns to the H14 r=6 backend route", f"""
Stage147 returns to the H14 r=6 backend route after Stage146 rejects promotion
for r4-unrolled. It uses current-head `T_bootstrap/r` smoke and body-profile
attribution only to route the next high-stat refresh; it does not change
scalar/default behavior or final claim policy.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage147 as the H14 r=6 current-head route gate", f"""
51. Treat Stage147 as the H14 r=6 current-head route gate:
    `{decision}`. This stage confirms or rejects the next branch after
    r4-unrolled remains explicit-only; it is not a final speedup claim.
""")
    append_once(HYPOTHESIS_YAML, "H71_h14_r6_current_head_route", f"""
  - id: H71_h14_r6_current_head_route
    statement: >
      After r4-unrolled remains explicit-only, the H14 backend FromDFT-add r=6
      route should be the next current-head branch if it still beats the wrapper
      fused reference under T_bootstrap/r smoke and preserves schedule counts.
    mechanism: >
      Backend FromDFT-add reduces inverse DFT materialization/add lifetime
      without changing MAT EP call counts or scalar SAB behavior.
    status: stage147_h14_r6_current_head_route
    evidence: docs/stage147_h14_r6_current_head_route.md; experiments/stage147_h14_r6_current_head_route_plan.md; theory_checks/stage147_h14_route_model.md; scripts/build_stage147_h14_r6_current_head_route.py; repro/stage147_h14_r6_current_head_route/summary.csv
    current_decision: >
      {decision}
    failure_criteria:
      - current-head wrapper/backend r=6 correctness fails
      - backend route changes MAT EP schedule counts or copyback invariants
      - one-run smoke is used as a final speedup claim
""")


def update_repro(summary_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    existing = read_csv(RUN_LOG)
    run_fields = list(existing[0].keys()) if existing else [
        "run_id", "date", "commit_or_state", "stage", "backend", "command",
        "params", "seed", "status", "summary", "artifacts",
    ]
    base_row = {field: "" for field in run_fields}
    base_row.update({
        "run_id": "stage147-h14-r6-current-head-route-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "Stage 147",
        "backend": "spqlios_avx512",
        "command": "python scripts/build_stage147_h14_r6_current_head_route.py",
        "params": f"r={R_VALUE}; reps={BENCH_REPS}; wrapper fused FromDFT-add vs backend FromDFT-add; body profile smoke",
        "seed": "default-rng",
        "status": decision,
        "summary": "Current-head H14 r=6 backend route smoke/profile gate.",
        "artifacts": rel(OUT_DIR),
    })
    run_row = {field: base_row.get(field, "") for field in run_fields}
    existing = [
        row for row in existing
        if row.get("run_id") != run_row["run_id"]
        and row.get("stage") != run_row["stage"]
    ]
    existing.append(run_row)
    write_csv(RUN_LOG, existing, run_fields)

    append_once(GLOBAL_MANIFEST, "stage147_h14_r6_current_head_route", f"""
- stage147_h14_r6_current_head_route: `{decision}`
  - `docs/stage147_h14_r6_current_head_route.md`
  - `experiments/stage147_h14_r6_current_head_route_plan.md`
  - `theory_checks/stage147_h14_route_model.md`
  - `repro/stage147_h14_r6_current_head_route/`
""")
    append_once(CHECKLIST_MD, "Stage147 H14 r=6 current-head route pack", """
- [x] Stage147 H14 r=6 current-head route pack recorded.
""")


def write_artifact_index(paths: List[Path]) -> None:
    rows = []
    for path in paths:
        if path == ARTIFACT_INDEX:
            rows.append({"artifact": rel(path), "exists": "self", "sha256": "", "size_bytes": ""})
        else:
            rows.append({
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            })
    write_csv(ARTIFACT_INDEX, rows, ["artifact", "exists", "sha256", "size_bytes"])


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prior_rows = collect_prior_inputs()
    write_csv(PRIOR_CSV, prior_rows, PRIOR_FIELDS)
    run_ok, variant_rows = run_variants()
    comparison_rows = compare_variants(variant_rows)
    summary_rows = build_summary(prior_rows, run_ok, comparison_rows)

    write_csv(VARIANT_RESULTS_CSV, variant_rows, VARIANT_FIELDS)
    write_csv(VARIANT_COMPARISON_CSV, comparison_rows, COMPARE_FIELDS)
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)

    write_docs(prior_rows, variant_rows, comparison_rows, summary_rows)
    update_longform(summary_rows)
    update_repro(summary_rows)

    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD,
        PRIOR_CSV, VARIANT_RESULTS_CSV, VARIANT_COMPARISON_CSV, SUMMARY_CSV,
        OUT_DIR / "build_wrapper_fused_from_dft_add_r6.log",
        OUT_DIR / "run_wrapper_fused_from_dft_add_r6.log",
        OUT_DIR / "build_backend_from_dft_add_r6.log",
        OUT_DIR / "run_backend_from_dft_add_r6.log",
        OUT_DIR / "cleanup.log",
        ARTIFACT_INDEX,
        Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)
    print(f"Stage147 H14 r=6 current-head route: {summary_rows[-1]['status']}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
