#!/usr/bin/env python3
"""Build Stage151 H14 r=6 backend+fulltile complete-SAB smoke gate."""

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
OUT_DIR = ROOT / "repro" / "stage151_h14_r6_fulltile_backend_smoke"

STAGE150_SUMMARY = ROOT / "repro" / "stage150_final_package_refresh" / "summary.csv"
STAGE111_SUMMARY = ROOT / "repro" / "stage111_r6_fulltile_repeated_gate" / "summary.csv"
STAGE148_PERF = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "perf_comparison.csv"

VARIANT_RESULTS_CSV = OUT_DIR / "variant_results.csv"
COMPARISON_CSV = OUT_DIR / "comparison.csv"
PRIOR_CSV = OUT_DIR / "prior_evidence.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"

OUT_MD = ROOT / "docs" / "stage151_h14_r6_fulltile_backend_smoke.md"
PLAN_MD = ROOT / "experiments" / "stage151_h14_r6_fulltile_backend_smoke_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage151_h14_r6_fulltile_backend_model.md"
VARIANT_MD = ROOT / "algorithm_variants" / "mat_rlwe_sab_h14_r6_fulltile_backend.md"

ROADMAP_MD = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL_MD = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL_MD = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESIS_YAML = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
GLOBAL_MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST_MD = ROOT / "repro" / "reproduction_checklist.md"

R_VALUE = int(os.environ.get("STAGE151_R", "6"))
BENCH_REPS = int(os.environ.get("SAB_PVW_BENCH_REPS", "1"))
JOBS = int(os.environ.get("JOBS", "8"))
RUN_SMOKE = os.environ.get("STAGE151_RUN_SMOKE", "1") not in {"0", "false", "False"}

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true "
    "SAB_PVW_BODY_PROFILE=true "
    "SAB_PVW_BENCH=true "
    f"SAB_PVW_BENCH_R={R_VALUE} SAB_PVW_BENCH_REPS={BENCH_REPS}"
)

VARIANTS = [
    {
        "variant": "backend_tile4_r6",
        "flags": f"{BASE_FLAGS} MAT_TRGSW_AVX512_RGT4_FUSED=true",
    },
    {
        "variant": "backend_fulltile_r6",
        "flags": f"{BASE_FLAGS} MAT_TRGSW_AVX512_R6_FULLTILE=true",
    },
]

VARIANT_FIELDS = [
    "variant", "status", "r", "h", "r_prec", "lanes", "in_N",
    "pvw_avg_us", "pvw_lane_avg_us", "scalar_repeated_avg_us",
    "scalar_lane_avg_us", "speedup_vs_scalar_repeated", "body_full_us",
    "mat_ep_calls", "mat_ep_us", "mat_ep_share", "cmux_calls", "cmux_us",
    "cmux_sub_us", "cmux_from_dft_us", "cmux_add_us", "ncmux_calls",
    "ncmux_us", "ncmux_auto_us", "sub_a_calls", "sub_a_us",
    "copyback_calls", "copyback_us", "source_run_log", "source_build_log",
]
COMPARE_FIELDS = [
    "metric", "tile4", "fulltile", "fulltile_over_tile4", "status", "detail",
]
SUMMARY_FIELDS = ["gate", "status", "metric", "value", "evidence", "detail", "next_action"]
PRIOR_FIELDS = ["source", "gate", "status", "metric", "value", "evidence", "detail"]

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


def status_by_gate(rows: List[Dict[str, str]], gate: str) -> str:
    for row in rows:
        if row.get("gate") == gate:
            return row.get("status", "")
    return "MISSING"


def collect_prior() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for source, path, gates in [
        ("Stage150", STAGE150_SUMMARY, {"stage150_decision"}),
        ("Stage111", STAGE111_SUMMARY, {"stage111_decision", "stage111_fullsab_timing"}),
    ]:
        csv_rows = read_csv(path)
        if not csv_rows:
            rows.append({
                "source": source,
                "gate": "missing",
                "status": "MISSING",
                "metric": "file",
                "value": rel(path),
                "evidence": rel(path),
                "detail": "Required prior evidence file is missing.",
            })
            continue
        for row in csv_rows:
            if row.get("gate") in gates:
                rows.append({
                    "source": source,
                    "gate": row.get("gate", ""),
                    "status": row.get("status", ""),
                    "metric": row.get("metric", ""),
                    "value": row.get("value", ""),
                    "evidence": row.get("evidence", rel(path)),
                    "detail": row.get("detail", ""),
                })
    perf = read_csv(STAGE148_PERF)
    if perf:
        row = perf[0]
        rows.append({
            "source": "Stage148",
            "gate": "stage148_perf_baseline",
            "status": row.get("decision", ""),
            "metric": row.get("metric", ""),
            "value": row.get("backend_mean_speedup_vs_scalar", ""),
            "evidence": rel(STAGE148_PERF),
            "detail": "Current H14 backend tile4 evidence before Stage151 layout composition.",
        })
    return rows


def parse_variant(variant: str, build_log: Path, run_log: Path) -> Dict[str, str]:
    text = run_log.read_text(encoding="utf-8", errors="replace") if run_log.exists() else ""
    correctness = CORRECT_RE.search(text)
    bench = BENCH_RE.search(text)
    profile_line = ""
    for line in text.splitlines():
        if "SAB_PVW_BODY_PROFILE sample" in line:
            profile_line = line
    kv = dict(PROFILE_KV_RE.findall(profile_line))
    ok = correctness and correctness.group("status") == "Pass" and bench and kv
    body_full = fnum(kv.get("full_us", "0"))
    mat_ep = fnum(kv.get("mat_ep_us", "0"))
    return {
        "variant": variant,
        "status": "PASS" if ok else "FAIL",
        "r": correctness.group("r") if correctness else "",
        "h": correctness.group("h") if correctness else "",
        "r_prec": correctness.group("r_prec") if correctness else "",
        "lanes": kv.get("lanes", ""),
        "in_N": kv.get("in_N", ""),
        "pvw_avg_us": bench.group("pvw_avg_us") if bench else "",
        "pvw_lane_avg_us": bench.group("pvw_lane_avg_us") if bench else "",
        "scalar_repeated_avg_us": bench.group("scalar_repeated_avg_us") if bench else "",
        "scalar_lane_avg_us": bench.group("scalar_lane_avg_us") if bench else "",
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
        "source_run_log": rel(run_log),
        "source_build_log": rel(build_log),
    }


def run_variants() -> Tuple[bool, List[Dict[str, str]]]:
    if not RUN_SMOKE:
        cached = read_csv(VARIANT_RESULTS_CSV)
        return bool(cached), cached
    rows: List[Dict[str, str]] = []
    ok = True
    for config in VARIANTS:
        variant = config["variant"]
        build_log = OUT_DIR / f"build_{variant}.txt"
        run_log = OUT_DIR / f"run_{variant}.txt"
        build = run_logged(
            f"make clean >/dev/null 2>&1 || true && make {config['flags']} -j{JOBS}",
            build_log,
            timeout=900,
        )
        ok = ok and build.returncode == 0
        if build.returncode == 0:
            proc = run_logged("./main", run_log, timeout=1500)
            ok = ok and proc.returncode == 0
        else:
            write_text_lf(run_log, "variant run skipped because build failed\n")
        parsed = parse_variant(variant, build_log, run_log)
        ok = ok and parsed["status"] == "PASS"
        rows.append(parsed)
    run_logged("make clean >/dev/null 2>&1 || true", OUT_DIR / "cleanup.txt", timeout=60)
    return ok, rows


def compare_variants(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    tile4 = next((row for row in rows if row.get("variant") == "backend_tile4_r6"), None)
    fulltile = next((row for row in rows if row.get("variant") == "backend_fulltile_r6"), None)
    if not tile4 or not fulltile:
        return [{
            "metric": "variant_rows",
            "tile4": "missing",
            "fulltile": "missing",
            "fulltile_over_tile4": "0",
            "status": "FAIL",
            "detail": "Expected backend_tile4_r6 and backend_fulltile_r6 rows.",
        }]

    def ratio(field: str) -> float:
        denom = fnum(fulltile.get(field, "0"))
        return fnum(tile4.get(field, "0")) / denom if denom else 0.0

    rows_out = [
        {
            "metric": "correctness",
            "tile4": tile4["status"],
            "fulltile": fulltile["status"],
            "fulltile_over_tile4": "1" if tile4["status"] == "PASS" and fulltile["status"] == "PASS" else "0",
            "status": "PASS" if tile4["status"] == "PASS" and fulltile["status"] == "PASS" else "FAIL",
            "detail": "Both layout variants must pass full-SAB correctness before timing is interpreted.",
        },
        {
            "metric": "T_bootstrap_per_lane_fulltile_over_tile4",
            "tile4": tile4["pvw_lane_avg_us"],
            "fulltile": fulltile["pvw_lane_avg_us"],
            "fulltile_over_tile4": fmt(ratio("pvw_lane_avg_us")),
            "status": "SMOKE_ONLY",
            "detail": "Primary endpoint; ratio above one means fulltile is faster.",
        },
        {
            "metric": "T_bootstrap_total_fulltile_over_tile4",
            "tile4": tile4["pvw_avg_us"],
            "fulltile": fulltile["pvw_avg_us"],
            "fulltile_over_tile4": fmt(ratio("pvw_avg_us")),
            "status": "SMOKE_ONLY",
            "detail": "Total time check; final interpretation remains per lane.",
        },
        {
            "metric": "mat_ep_speedup_fulltile_over_tile4",
            "tile4": tile4["mat_ep_us"],
            "fulltile": fulltile["mat_ep_us"],
            "fulltile_over_tile4": fmt(ratio("mat_ep_us")),
            "status": "PROFILE_ONLY",
            "detail": "MAT external-product body-profile attribution.",
        },
        {
            "metric": "from_dft_speedup_fulltile_over_tile4",
            "tile4": tile4["cmux_from_dft_us"],
            "fulltile": fulltile["cmux_from_dft_us"],
            "fulltile_over_tile4": fmt(ratio("cmux_from_dft_us")),
            "status": "PROFILE_ONLY",
            "detail": "The backend FromDFT-add route is held fixed; this should not be the source of a fulltile gain.",
        },
        {
            "metric": "speedup_vs_scalar_tile4",
            "tile4": tile4["speedup_vs_scalar_repeated"],
            "fulltile": "",
            "fulltile_over_tile4": tile4["speedup_vs_scalar_repeated"],
            "status": "SMOKE_ONLY",
            "detail": "Current tile4 backend path versus repeated scalar SAB.",
        },
        {
            "metric": "speedup_vs_scalar_fulltile",
            "tile4": "",
            "fulltile": fulltile["speedup_vs_scalar_repeated"],
            "fulltile_over_tile4": fulltile["speedup_vs_scalar_repeated"],
            "status": "SMOKE_ONLY",
            "detail": "Current fulltile backend path versus repeated scalar SAB.",
        },
        {
            "metric": "mat_ep_calls_equal",
            "tile4": tile4["mat_ep_calls"],
            "fulltile": fulltile["mat_ep_calls"],
            "fulltile_over_tile4": "1" if tile4["mat_ep_calls"] == fulltile["mat_ep_calls"] else "0",
            "status": "PASS" if tile4["mat_ep_calls"] == fulltile["mat_ep_calls"] else "FAIL",
            "detail": "Layout change must not alter SAB schedule counts.",
        },
        {
            "metric": "copyback_zero",
            "tile4": tile4["copyback_calls"],
            "fulltile": fulltile["copyback_calls"],
            "fulltile_over_tile4": "1" if tile4["copyback_calls"] == "0" and fulltile["copyback_calls"] == "0" else "0",
            "status": "PASS" if tile4["copyback_calls"] == "0" and fulltile["copyback_calls"] == "0" else "FAIL",
            "detail": "Active-buffer invariant must remain intact.",
        },
    ]
    return rows_out


def build_summary(
    prior_rows: List[Dict[str, str]],
    run_ok: bool,
    comparison_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    stage150_ok = any(
        row.get("source") == "Stage150"
        and row.get("gate") == "stage150_decision"
        and row.get("status") == "PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED"
        for row in prior_rows
    )
    correctness_ok = any(row["metric"] == "correctness" and row["status"] == "PASS" for row in comparison_rows)
    invariant_ok = all(
        row["status"] == "PASS"
        for row in comparison_rows
        if row["metric"] in {"mat_ep_calls_equal", "copyback_zero"}
    )
    lane_ratio = 0.0
    mat_ep_ratio = 0.0
    fulltile_scalar = 0.0
    for row in comparison_rows:
        if row["metric"] == "T_bootstrap_per_lane_fulltile_over_tile4":
            lane_ratio = fnum(row["fulltile_over_tile4"])
        elif row["metric"] == "mat_ep_speedup_fulltile_over_tile4":
            mat_ep_ratio = fnum(row["fulltile_over_tile4"])
        elif row["metric"] == "speedup_vs_scalar_fulltile":
            fulltile_scalar = fnum(row["fulltile_over_tile4"])

    if not stage150_ok:
        decision = "FAIL_STAGE151_PRECONDITION_STAGE150_MISSING"
        next_action = "Repair or rerun Stage150 before selecting the next implementation candidate."
    elif not run_ok or not correctness_ok or not invariant_ok:
        decision = "FAIL_STAGE151_H14_R6_FULLTILE_BACKEND_REPAIR_REQUIRED"
        next_action = "Repair build/correctness/schedule invariants before interpreting timing."
    elif lane_ratio >= 1.01 and mat_ep_ratio >= 1.01:
        decision = "PASS_STAGE151_H14_R6_FULLTILE_BACKEND_SMOKE_POSITIVE_REPEAT_NEXT"
        next_action = "Run Stage152 repeated/noise/resource gate for backend+fulltile before any promotion wording."
    elif lane_ratio > 1.0:
        decision = "WEAK_STAGE151_H14_R6_FULLTILE_BACKEND_TINY_POSITIVE_REPEAT_OPTIONAL"
        next_action = "Repeat only if profile variance or mat_ep attribution justifies the cost; do not promote from smoke."
    elif fulltile_scalar > 1.0:
        decision = "NEUTRAL_STAGE151_H14_R6_FULLTILE_BACKEND_NOT_SELECTED"
        next_action = "Keep fulltile as negative/neutral ablation and select a different Stage152 hot-path candidate."
    else:
        decision = "FAIL_STAGE151_H14_R6_FULLTILE_BACKEND_NO_SPEEDUP"
        next_action = "Reject this composition route and choose a different implementation candidate."

    return [
        {
            "gate": "stage151_precondition",
            "status": "PASS" if stage150_ok else "FAIL",
            "metric": "stage150_decision",
            "value": "PASS_STAGE150_FINAL_PACKAGE_REFRESH_SCOPED_EXPLICIT_H14_R6_RECORDED",
            "evidence": rel(STAGE150_SUMMARY),
            "detail": "Stage151 starts only after Stage150 fixes the amortized claim ledger.",
            "next_action": "",
        },
        {
            "gate": "stage151_correctness_smoke",
            "status": "PASS" if run_ok and correctness_ok else "FAIL",
            "metric": "tile4;fulltile",
            "value": "full_sab_correctness",
            "evidence": rel(VARIANT_RESULTS_CSV),
            "detail": "Both H14 backend layout variants must run complete SAB and pass correctness.",
            "next_action": "Do not interpret timing if correctness fails.",
        },
        {
            "gate": "stage151_schedule_invariant",
            "status": "PASS" if invariant_ok else "FAIL",
            "metric": "mat_ep_calls_equal;copyback_zero",
            "value": "573440;0" if invariant_ok else "see comparison",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Fulltile changes only MAT layout, not sparse schedule or active-buffer invariants.",
            "next_action": "",
        },
        {
            "gate": "stage151_timing_smoke",
            "status": "PASS_POSITIVE" if lane_ratio >= 1.01 else ("WEAK_POSITIVE" if lane_ratio > 1.0 else "NEGATIVE_OR_NEUTRAL"),
            "metric": "T_bootstrap/r;mat_ep",
            "value": f"{fmt(lane_ratio)};{fmt(mat_ep_ratio)}",
            "evidence": rel(COMPARISON_CSV),
            "detail": "Smoke timing asks whether backend+fulltile beats backend+tile4 under the primary amortized endpoint.",
            "next_action": "Promotion requires a repeated gate; smoke is only routing evidence.",
        },
        {
            "gate": "stage151_decision",
            "status": decision,
            "metric": "candidate_route",
            "value": "h14_r6_backend_fulltile",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Stage151 selects or rejects the backend+fulltile implementation candidate without changing defaults.",
            "next_action": next_action,
        },
    ]


def write_docs(
    prior_rows: List[Dict[str, str]],
    variant_rows: List[Dict[str, str]],
    comparison_rows: List[Dict[str, str]],
    summary_rows: List[Dict[str, str]],
) -> None:
    decision = status_by_gate(summary_rows, "stage151_decision")
    write_text_lf(PLAN_MD, "\n".join([
        "# Stage151 H14 r=6 Fulltile Backend Smoke Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Test one concrete post-Stage150 implementation candidate: compose the Stage148 H14 backend FromDFT-add path with the r=6 fulltile MAT external-product layout.",
        "",
        "## Hypothesis",
        "",
        "Holding scalar/default behavior, active-buffer fusion, backend FromDFT-add, parameter set, and backend fixed, replacing the r>4 tile4 MAT layout with r=6 fulltile should improve complete SAB `T_bootstrap/r` only if its MAT EP locality gain survives the full SAB schedule.",
        "",
        "## Gate",
        "",
        "- correctness: both backend tile4 and backend fulltile full-SAB smoke pass;",
        "- schedule: MAT EP call count remains 573440 and copyback remains zero;",
        "- performance: `T_bootstrap/r` ratio above one is routing evidence; at least 1.01 plus MAT EP improvement is required to open a repeated Stage152 gate;",
        "- claim policy: no default-path or paper-level wording from this smoke.",
    ]) + "\n")
    write_text_lf(THEORY_MD, "\n".join([
        "# Stage151 H14 r=6 Fulltile Backend Model",
        "",
        "Date: 2026-07-03",
        "",
        "## Candidate Delta",
        "",
        "The baseline is the current explicit H14 r=6 backend path from Stage148: r>4 tile4 MAT layout, backend FromDFT-add, active-buffer fusion, and complete binary `SET_2_3_2048` SAB. Stage151 changes only the MAT external-product layout flag from `MAT_TRGSW_AVX512_RGT4_FUSED=true` to `MAT_TRGSW_AVX512_R6_FULLTILE=true`.",
        "",
        "## Complexity And Lower-Bound Relation",
        "",
        "Both variants have the same closed dense full-MAT arithmetic shape for k=1, l=1, r=6: seven decomposed input rows and seven output polynomials per external product. The fulltile path does not reduce the asymptotic external-product count:",
        "",
        "```text",
        "(h + 1) * r_prec * N = 40 * 7 * 2048 = 573440 MAT EP calls",
        "```",
        "",
        "It is therefore a locality/SIMD scheduling candidate, not a new lower-bound proof. It can be promoted only if the measured `T_bootstrap/r` and MAT EP profile both improve under the same backend.",
        "",
        "## Failure Mode",
        "",
        "Stage111 showed fulltile can be kernel-plausible but complete-SAB negative without backend composition. Stage151 explicitly checks whether the H14 backend path changes that conclusion. A neutral result closes this candidate as another negative ablation.",
    ]) + "\n")
    write_text_lf(VARIANT_MD, "\n".join([
        "# MAT-RLWE SAB H14 r=6 Backend Fulltile Candidate",
        "",
        "Date: 2026-07-03",
        "",
        "## Definition",
        "",
        "Candidate `H75`: explicit `sab_pvw_*` full bootstrapping with:",
        "",
        "- r=6 independent MAT-RLWE/PVW body lanes;",
        "- binary `SET_2_3_2048`;",
        "- active-buffer sparse schedule;",
        "- backend FromDFT-add;",
        "- r=6 fulltile MAT external-product AVX512 layout;",
        "- scalar/default SAB unchanged.",
        "",
        "## Baseline",
        "",
        "The direct baseline is the same explicit backend path with the existing r>4 tile4 layout. The paper-level scalar baseline remains repeated scalar SAB measured per lane.",
    ]) + "\n")
    write_text_lf(OUT_MD, "\n".join([
        "# Stage151 H14 r=6 Fulltile Backend Smoke",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "Stage151 tests a single implementation candidate after Stage150: whether r=6 fulltile becomes useful when composed with the H14 backend FromDFT-add route. It is a smoke/routing gate, not a final promotion claim.",
        "",
        "## Summary Gates",
        "",
        table(summary_rows, ["gate", "status", "metric", "value", "detail", "next_action"]),
        "",
        "## Prior Evidence",
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
        "A positive Stage151 result only opens a repeated Stage152 gate. A neutral or negative result keeps fulltile as an ablation and routes the research loop to a different hot-path candidate.",
    ]) + "\n")


def update_longform(summary_rows: List[Dict[str, str]]) -> None:
    decision = status_by_gate(summary_rows, "stage151_decision")
    timing = next((row for row in summary_rows if row["gate"] == "stage151_timing_smoke"), {})
    block = f"""
## Stage 151: H14 r=6 Fulltile Backend Smoke

Goal:

```text
Test whether composing the Stage148 H14 backend FromDFT-add route with the
r=6 fulltile MAT external-product layout improves complete SAB T_bootstrap/r.
```

Status:

```text
Completed. Stage151 records {decision}. The timing smoke value is
{timing.get('value', '')} for `T_bootstrap/r;mat_ep`. This is routing evidence
only; default-path and final-paper claims remain blocked.
```
"""
    append_once(ROADMAP_MD, "## Stage 151: H14 r=6 Fulltile Backend Smoke", block)
    append_once(GOAL_MD, "Stage151 tests H14 r=6 fulltile backend composition", f"""
Stage151 tests H14 r=6 fulltile backend composition after Stage150 fixes the
amortized endpoint. It changes only the r=6 MAT layout under the explicit
backend path and evaluates complete SAB `T_bootstrap/r`; the decision is
`{decision}`.
""")
    append_once(CURRENT_GOAL_MD, "Treat Stage151 as the H14 r=6 fulltile backend smoke gate", f"""
55. Treat Stage151 as the H14 r=6 fulltile backend smoke gate:
    `{decision}`. It is a concrete implementation-candidate gate, not a final
    claim. If it is not positive, fulltile remains an ablation and the next
    stage must choose a different hot-path candidate.
""")
    append_once(HYPOTHESIS_YAML, "H75_h14_r6_fulltile_backend_smoke", f"""
  - id: H75_h14_r6_fulltile_backend_smoke
    statement: >
      Composing the H14 backend FromDFT-add route with the r=6 fulltile MAT
      external-product layout may improve complete SAB T_bootstrap/r if the
      fulltile MAT EP locality gain survives the full sparse schedule.
    mechanism: >
      The backend route already reduces inverse DFT/add materialization; the
      fulltile layout changes only the r=6 MAT output tiling while preserving
      MAT EP count and active-buffer copyback invariants.
    status: stage151_h14_r6_fulltile_backend_smoke
    evidence: docs/stage151_h14_r6_fulltile_backend_smoke.md; experiments/stage151_h14_r6_fulltile_backend_smoke_plan.md; theory_checks/stage151_h14_r6_fulltile_backend_model.md; scripts/build_stage151_h14_r6_fulltile_backend_smoke.py; repro/stage151_h14_r6_fulltile_backend_smoke/summary.csv; repro/stage151_h14_r6_fulltile_backend_smoke/comparison.csv
    current_decision: >
      {decision}
    failure_criteria:
      - fulltile correctness fails under complete SAB
      - MAT EP calls or copyback invariants change
      - T_bootstrap/r does not beat backend tile4 under the same backend
""")


def update_repro(summary_rows: List[Dict[str, str]]) -> None:
    decision = status_by_gate(summary_rows, "stage151_decision")
    existing = read_csv(RUN_LOG)
    run_fields = list(existing[0].keys()) if existing else [
        "run_id", "date", "commit_or_state", "stage", "backend", "command",
        "params", "seed", "status", "summary", "artifacts",
    ]
    base_row = {field: "" for field in run_fields}
    base_row.update({
        "run_id": "stage151-h14-r6-fulltile-backend-smoke-001",
        "date": "2026-07-03",
        "commit_or_state": git_head(),
        "stage": "Stage 151",
        "backend": "spqlios_avx512",
        "command": "python scripts/build_stage151_h14_r6_fulltile_backend_smoke.py",
        "params": "BINARY SET_2_3_2048; r=6; active-buffer; backend FromDFT-add; tile4 vs fulltile; reps=1",
        "seed": "default-rng",
        "status": decision,
        "summary": "H14 r=6 backend+fulltile implementation-candidate complete-SAB smoke gate.",
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
    append_once(GLOBAL_MANIFEST, "stage151_h14_r6_fulltile_backend_smoke", f"""
- stage151_h14_r6_fulltile_backend_smoke: `{decision}`
  - `docs/stage151_h14_r6_fulltile_backend_smoke.md`
  - `experiments/stage151_h14_r6_fulltile_backend_smoke_plan.md`
  - `theory_checks/stage151_h14_r6_fulltile_backend_model.md`
  - `algorithm_variants/mat_rlwe_sab_h14_r6_fulltile_backend.md`
  - `repro/stage151_h14_r6_fulltile_backend_smoke/`
""")
    append_once(CHECKLIST_MD, "Stage151 H14 r=6 fulltile backend smoke pack", """
- [x] Stage151 H14 r=6 fulltile backend smoke pack recorded.
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
    prior_rows = collect_prior()
    run_ok, variant_rows = run_variants()
    comparison_rows = compare_variants(variant_rows)
    summary_rows = build_summary(prior_rows, run_ok, comparison_rows)

    write_csv(PRIOR_CSV, prior_rows, PRIOR_FIELDS)
    write_csv(VARIANT_RESULTS_CSV, variant_rows, VARIANT_FIELDS)
    write_csv(COMPARISON_CSV, comparison_rows, COMPARE_FIELDS)
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    write_docs(prior_rows, variant_rows, comparison_rows, summary_rows)
    update_longform(summary_rows)
    update_repro(summary_rows)
    artifacts = [
        OUT_MD, PLAN_MD, THEORY_MD, VARIANT_MD,
        PRIOR_CSV, VARIANT_RESULTS_CSV, COMPARISON_CSV, SUMMARY_CSV,
        OUT_DIR / "build_backend_tile4_r6.txt",
        OUT_DIR / "run_backend_tile4_r6.txt",
        OUT_DIR / "build_backend_fulltile_r6.txt",
        OUT_DIR / "run_backend_fulltile_r6.txt",
        OUT_DIR / "cleanup.txt",
        ARTIFACT_INDEX, Path(__file__).resolve(),
    ]
    write_artifact_index(artifacts)

    decision = status_by_gate(summary_rows, "stage151_decision")
    print(f"Stage151 H14 r=6 fulltile backend smoke: {decision}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 0 if decision.startswith(("PASS_", "WEAK_", "NEUTRAL_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
