#!/usr/bin/env python3
"""Stage224: exact PVW/MAT AVX/resource refresh after compact-route denial."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh"

DOC = ROOT / "docs" / "stage224_exact_pvw_mat_avx_resource_refresh.md"
PLAN = ROOT / "experiments" / "stage224_exact_pvw_mat_avx_resource_refresh_plan.md"
THEORY = ROOT / "theory_checks" / "stage224_exact_pvw_mat_avx_resource_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage224_exact_refresh.md"

INPUTS = OUT / "input_status.csv"
PERF = OUT / "perf_results.csv"
PERF_CMP = OUT / "perf_comparison.csv"
SIDE = OUT / "side_conditions.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "exact_pvw_mat_avx_resource_refresh_report.md"
ARTIFACT = OUT / "artifact_index.csv"
REPRO = OUT / "reproduction_commands.md"
CLEANUP = OUT / "cleanup.log"

ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
GOAL = ROOT / "docs" / "goal_sab_max_acceleration.md"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
RUN_LOG = ROOT / "repro" / "run_log.csv"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"

STAGE223_PROOF = ROOT / "repro" / "stage223_route_selection" / "proof_gate.csv"
STAGE223_NEXT = ROOT / "repro" / "stage223_route_selection" / "next_stage_queue.csv"
STAGE148_PERF = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "perf_comparison.csv"
STAGE148_NOISE = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "noise_aggregate.csv"
STAGE148_RESOURCE = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "resource_comparison.csv"
STAGE150_MODEL = ROOT / "theory_checks" / "stage150_claim_scope_model.md"

R_VALUE = int(os.environ.get("STAGE224_R", "6"))
PERF_RUNS = int(os.environ.get("STAGE224_PERF_RUNS", "3"))
BENCH_REPS = int(os.environ.get("SAB_PVW_BENCH_REPS", "1"))
JOBS = int(os.environ.get("JOBS", "8"))

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true"
)
PERF_CONFIGS = [
    {
        "variant": "wrapper_fused_from_dft_add",
        "flags": (
            f"{BASE_FLAGS} SAB_PVW_FUSED_FROM_DFT_ADD=true "
            f"SAB_PVW_BENCH=true SAB_PVW_BENCH_R={R_VALUE} "
            f"SAB_PVW_BENCH_REPS={BENCH_REPS}"
        ),
    },
    {
        "variant": "backend_from_dft_add",
        "flags": (
            f"{BASE_FLAGS} SAB_PVW_BACKEND_FROM_DFT_ADD=true "
            f"SAB_PVW_BENCH=true SAB_PVW_BENCH_R={R_VALUE} "
            f"SAB_PVW_BENCH_REPS={BENCH_REPS}"
        ),
    },
]

DECISION_POSITIVE = "PASS_STAGE224_EXACT_PVW_MAT_AVX_REFRESH_POSITIVE"
DECISION_NEUTRAL = "NEUTRAL_STAGE224_EXACT_PVW_MAT_AVX_REFRESH_KEEP_STAGE148"
DECISION_FAIL = "FAIL_STAGE224_EXACT_PVW_MAT_AVX_REFRESH"

INPUT_FIELDS = ["input", "status", "evidence", "role", "bytes"]
PERF_FIELDS = [
    "variant",
    "run",
    "status",
    "r",
    "h",
    "r_prec",
    "pvw_avg_us",
    "pvw_lane_avg_us",
    "scalar_repeated_avg_us",
    "scalar_lane_avg_us",
    "speedup_vs_scalar_repeated",
    "source_log",
]
PERF_CMP_FIELDS = [
    "metric",
    "runs",
    "wrapper_mean_pvw_lane_us",
    "backend_mean_pvw_lane_us",
    "backend_vs_wrapper_mean_speedup",
    "backend_vs_wrapper_min_speedup",
    "backend_vs_wrapper_ci95_low",
    "backend_vs_wrapper_ci95_high",
    "wrapper_mean_speedup_vs_scalar",
    "backend_mean_speedup_vs_scalar",
    "stage148_backend_speedup_vs_scalar",
    "refresh_vs_stage148_backend_speedup",
    "decision",
]
SIDE_FIELDS = ["source", "status", "metric", "value", "evidence", "interpretation"]

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
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.rstrip() + "\n").encode("utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [{field: row.get(field, "") for field in fields} for row in rows]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)


def append_once(path: Path, marker: str, text: str) -> None:
    current = read_text(path)
    if marker in current:
        return
    if current and not current.endswith("\n"):
        current += "\n"
    write_text(path, current + text.lstrip("\n"))


def table(rows: List[Dict[str, str]], fields: List[str]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    out = [
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(cell(row.get(field, "")) for field in fields) + " |")
    return "\n".join(out) + "\n"


def sha256_file(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def sanitize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"


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
    write_text(
        log,
        "\n".join(
            [
                f"command: {command}",
                f"returncode: {proc.returncode}",
                "--- stdout ---",
                sanitize(proc.stdout).rstrip(),
                "--- stderr ---",
                sanitize(proc.stderr).rstrip(),
            ]
        ),
    )
    return proc


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def stdev(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def ci95(values: List[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    m = mean(values)
    return m - 1.96 * stdev(values) / math.sqrt(len(values)), m + 1.96 * stdev(values) / math.sqrt(len(values))


def build_inputs() -> List[Dict[str, str]]:
    inputs = [
        ("stage223_proof_gate", STAGE223_PROOF, "permission for exact PVW/MAT refresh"),
        ("stage223_next_queue", STAGE223_NEXT, "selected Stage224 route"),
        ("stage148_perf_comparison", STAGE148_PERF, "previous best exact PVW/MAT full-SAB evidence"),
        ("stage148_noise_aggregate", STAGE148_NOISE, "previous noise side condition"),
        ("stage148_resource_comparison", STAGE148_RESOURCE, "previous resource side condition"),
        ("stage150_claim_scope", STAGE150_MODEL, "T_bootstrap/r metric boundary"),
    ]
    rows = []
    for name, path, role in inputs:
        rows.append(
            {
                "input": name,
                "status": "present" if path.exists() else "missing",
                "evidence": rel(path),
                "role": role,
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    return rows


def stage223_selects_stage224() -> bool:
    return any(row.get("route") == "stage224_exact_pvw_mat_avx_resource_refresh" and row.get("status") == "selected" for row in read_csv(STAGE223_NEXT))


def parse_perf_log(variant: str, run_idx: int, log: Path) -> Dict[str, str]:
    text = read_text(log)
    correct = None
    summary = None
    for line in text.splitlines():
        m = CORRECT_RE.search(line)
        if m:
            correct = m.groupdict()
        m = BENCH_RE.search(line)
        if m:
            summary = m.groupdict()
    if correct is None or summary is None:
        return {"variant": variant, "run": str(run_idx), "status": "MISSING_LINES", "source_log": rel(log)}
    return {
        "variant": variant,
        "run": str(run_idx),
        "status": "PASS" if correct["status"] == "Pass" else "FAIL",
        "r": correct["r"],
        "h": correct["h"],
        "r_prec": correct["r_prec"],
        "pvw_avg_us": summary["pvw_avg_us"],
        "pvw_lane_avg_us": summary["pvw_lane_avg_us"],
        "scalar_repeated_avg_us": summary["scalar_repeated_avg_us"],
        "scalar_lane_avg_us": summary["scalar_lane_avg_us"],
        "speedup_vs_scalar_repeated": summary["speedup"],
        "source_log": rel(log),
    }


def run_perf() -> tuple[bool, List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    ok = True
    for config in PERF_CONFIGS:
        variant = config["variant"]
        build_log = OUT / f"perf_build_{variant}.log"
        build = run_logged(
            f"make clean >/dev/null 2>&1 || true && make {config['flags']} -j{JOBS}",
            build_log,
            timeout=1200,
        )
        ok = ok and build.returncode == 0
        if build.returncode != 0:
            continue
        for run_idx in range(PERF_RUNS):
            log = OUT / f"perf_{variant}_run_{run_idx}.log"
            proc = run_logged("./main", log, timeout=1800)
            ok = ok and proc.returncode == 0
            rows.append(parse_perf_log(variant, run_idx, log))
    cleanup = run_logged("make clean >/dev/null 2>&1 || true", CLEANUP, timeout=300)
    ok = ok and cleanup.returncode == 0
    return ok, rows


def stage148_speedup() -> float:
    rows = read_csv(STAGE148_PERF)
    if not rows:
        return 0.0
    return fnum(rows[0].get("backend_mean_speedup_vs_scalar", "0"))


def build_perf_comparison(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    wrapper = {int(row["run"]): row for row in rows if row.get("variant") == "wrapper_fused_from_dft_add" and row.get("status") == "PASS"}
    backend = {int(row["run"]): row for row in rows if row.get("variant") == "backend_from_dft_add" and row.get("status") == "PASS"}
    paired_runs = sorted(set(wrapper).intersection(backend))
    paired_speedups = [fnum(wrapper[i]["pvw_lane_avg_us"]) / fnum(backend[i]["pvw_lane_avg_us"]) for i in paired_runs]
    wrapper_lane = [fnum(wrapper[i]["pvw_lane_avg_us"]) for i in paired_runs]
    backend_lane = [fnum(backend[i]["pvw_lane_avg_us"]) for i in paired_runs]
    wrapper_vs_scalar = [fnum(wrapper[i]["speedup_vs_scalar_repeated"]) for i in paired_runs]
    backend_vs_scalar = [fnum(backend[i]["speedup_vs_scalar_repeated"]) for i in paired_runs]
    low, high = ci95(paired_speedups)
    avg_speed = mean(paired_speedups)
    prev = stage148_speedup()
    current_backend_vs_scalar = mean(backend_vs_scalar)
    if len(paired_runs) < PERF_RUNS:
        decision = "FAIL_STAGE224_PERF_MISSING_PAIRED_RUNS"
    elif low > 1.0 and min(paired_speedups) > 1.0 and avg_speed >= 1.01 and current_backend_vs_scalar > 1.0:
        decision = "PASS_STAGE224_PERF_REFRESH_POSITIVE"
    elif current_backend_vs_scalar > 1.0:
        decision = "WEAK_STAGE224_PERF_REFRESH_POSITIVE_VS_SCALAR_ONLY"
    else:
        decision = "NEUTRAL_STAGE224_PERF_REFRESH_NOT_POSITIVE"
    return [
        {
            "metric": "T_bootstrap_per_lane",
            "runs": str(len(paired_runs)),
            "wrapper_mean_pvw_lane_us": f"{mean(wrapper_lane):.3f}",
            "backend_mean_pvw_lane_us": f"{mean(backend_lane):.3f}",
            "backend_vs_wrapper_mean_speedup": f"{avg_speed:.6f}",
            "backend_vs_wrapper_min_speedup": f"{min(paired_speedups) if paired_speedups else 0.0:.6f}",
            "backend_vs_wrapper_ci95_low": f"{low:.6f}",
            "backend_vs_wrapper_ci95_high": f"{high:.6f}",
            "wrapper_mean_speedup_vs_scalar": f"{mean(wrapper_vs_scalar):.6f}",
            "backend_mean_speedup_vs_scalar": f"{current_backend_vs_scalar:.6f}",
            "stage148_backend_speedup_vs_scalar": f"{prev:.6f}",
            "refresh_vs_stage148_backend_speedup": f"{current_backend_vs_scalar / prev if prev else 0.0:.6f}",
            "decision": decision,
        }
    ]


def build_side_conditions() -> List[Dict[str, str]]:
    noise = read_csv(STAGE148_NOISE)
    resource = read_csv(STAGE148_RESOURCE)
    noise_row = noise[0] if noise else {}
    resource_row = resource[0] if resource else {}
    source_head = subprocess.check_output(["git", "log", "-1", "--format=%h", "--", "src", "src/mosfhet", "Makefile"], cwd=ROOT, text=True).strip()
    return [
        {
            "source": "Stage148 noise",
            "status": noise_row.get("status", "MISSING"),
            "metric": "seeds;failures;avg_pvw_minus_scalar_log2",
            "value": (
                f"{noise_row.get('seeds', '')};"
                f"{noise_row.get('pvw_failures', '')}/"
                f"{noise_row.get('scalar_failures', '')}/"
                f"{noise_row.get('pair_failures', '')};"
                f"{noise_row.get('avg_pvw_minus_scalar_log2', '')}"
            ),
            "evidence": rel(STAGE148_NOISE),
            "interpretation": "Inherited side condition; Stage224 refreshes performance and records source-head boundary.",
        },
        {
            "source": "Stage148 resource",
            "status": resource_row.get("status", "MISSING"),
            "metric": "key_bytes_ratio;vmhwm_ratio;time_max_rss_ratio",
            "value": (
                f"{resource_row.get('key_bytes_ratio', '')};"
                f"{resource_row.get('vmhwm_ratio', '')};"
                f"{resource_row.get('time_max_rss_ratio', '')}"
            ),
            "evidence": rel(STAGE148_RESOURCE),
            "interpretation": "Inherited side condition; rerun resource if Stage224 performance materially changes or before final claim.",
        },
        {
            "source": "source-head",
            "status": "RECORDED",
            "metric": "latest_src_touching_commit",
            "value": source_head,
            "evidence": "git log -1 --format=%h -- src src/mosfhet Makefile",
            "interpretation": "Bounds reuse of Stage148 side conditions; Stage224 does not alter production source.",
        },
    ]


def build_proof(inputs: List[Dict[str, str]], perf_ok: bool, perf_cmp: List[Dict[str, str]], side_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    stage223_ok = stage223_selects_stage224()
    perf_decision = perf_cmp[0]["decision"] if perf_cmp else "MISSING"
    perf_positive = perf_ok and perf_decision == "PASS_STAGE224_PERF_REFRESH_POSITIVE"
    perf_completed = perf_ok and perf_cmp and perf_decision.startswith(("PASS_", "WEAK_", "NEUTRAL_"))
    noise_ok = any(row["source"] == "Stage148 noise" and row["status"] == "PASS" for row in side_rows)
    resource_ok = any(row["source"] == "Stage148 resource" and row["status"] in {"PASS", "REVIEW_RESOURCE_OVERHEAD"} for row in side_rows)
    if not missing and stage223_ok and perf_positive and noise_ok and resource_ok:
        decision = DECISION_POSITIVE
    elif not missing and stage223_ok and perf_completed:
        decision = DECISION_NEUTRAL
    else:
        decision = DECISION_FAIL
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage224 consumes Stage223 route selection and Stage148 side-condition evidence.",
        },
        {
            "gate": "G2_stage223_admission",
            "status": "PASS" if stage223_ok else "FAIL",
            "metric": "stage224_selected",
            "value": str(stage223_ok).lower(),
            "evidence": rel(STAGE223_NEXT),
            "interpretation": "Exact PVW/MAT refresh is only valid after compact complete-SAB route is denied.",
        },
        {
            "gate": "G3_full_sab_perf_refresh",
            "status": perf_decision,
            "metric": "backend_vs_wrapper;backend_vs_scalar",
            "value": (
                f"{perf_cmp[0].get('backend_vs_wrapper_mean_speedup', '')};"
                f"{perf_cmp[0].get('backend_mean_speedup_vs_scalar', '')}"
            ) if perf_cmp else "",
            "evidence": f"{rel(PERF)}; {rel(PERF_CMP)}",
            "interpretation": "Fresh complete-SAB A/B under T_bootstrap/r.",
        },
        {
            "gate": "G4_noise_resource_side_conditions",
            "status": "PASS_INHERITED_SIDE_CONDITIONS" if noise_ok and resource_ok else "REVIEW_SIDE_CONDITIONS",
            "metric": "noise_pass;resource_pass",
            "value": f"{str(noise_ok).lower()};{str(resource_ok).lower()}",
            "evidence": rel(SIDE),
            "interpretation": "Stage224 records inherited noise/resource; rerun before final promotion if source or path changes.",
        },
        {
            "gate": "G5_claim_boundary",
            "status": "PASS_ENGINEERING_REFRESH_ONLY",
            "metric": "claim_boundary",
            "value": "no_compact_complete_sab_claim;no_theoretical_optimality",
            "evidence": rel(DOC),
            "interpretation": "Stage224 is exact PVW/MAT evidence, not compact complete-SAB or optimality proof.",
        },
        {
            "gate": "G6_stage224_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(PROOF),
            "interpretation": "Positive refresh can update the evidence package; neutral refresh keeps Stage148 as current best.",
        },
    ]


def build_next(decision: str) -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage225_exact_refresh_resource_noise_rerun",
            "entry_condition": "Stage224 perf refresh is positive and final claim needs fresh side conditions.",
            "gate": "Rerun noise/resource on the same executable path if promoting Stage224 over Stage148.",
            "status": "selected" if decision == DECISION_POSITIVE else "deferred",
            "failure_action": "Keep Stage148 side conditions and mark Stage224 performance-only refresh.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "stage225_exact_mat_avx_counter_attribution",
            "entry_condition": "Native perf counters are available.",
            "gate": "Attribute backend-vs-wrapper gain to load/store/FMA/cycles rather than backend noise.",
            "status": "future",
            "failure_action": "Use timing-only claim boundary.",
            "evidence": rel(PERF_CMP),
        },
        {
            "priority": "P2",
            "route": "paper_claim_boundary_update",
            "entry_condition": "After Stage224/225 evidence is stable.",
            "gate": "Separate exact MAT/PVW engineering acceleration from blocked compact route.",
            "status": "future",
            "failure_action": "No novelty/optimality claim.",
            "evidence": rel(STAGE150_MODEL),
        },
    ]


def write_docs(inputs: List[Dict[str, str]], perf_rows: List[Dict[str, str]], perf_cmp: List[Dict[str, str]], side_rows: List[Dict[str, str]], proof_rows: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    decision = proof_rows[-1]["status"]
    doc = f"""# Stage224 Exact PVW/MAT AVX Resource Refresh

Decision: `{decision}`.

Stage224 is a fresh complete-SAB performance refresh for the exact closed dense
MAT/PVW route selected by Stage223. The primary metric is still
`T_bootstrap/r`, not raw bootstrap runtime. Compact complete-SAB integration
remains denied.

## Proof Gates

{table(proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Performance Comparison

{table(perf_cmp, PERF_CMP_FIELDS)}
## Performance Runs

{table(perf_rows, PERF_FIELDS)}
## Side Conditions

{table(side_rows, SIDE_FIELDS)}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        THEORY,
        """# Stage224 Exact PVW/MAT AVX Resource Model

The exact PVW/MAT path is the only currently admitted complete-SAB route. Stage224
therefore measures the explicit r=6 backend path by

```text
T_lane = T_bootstrap / r
speedup_vs_scalar = T_scalar_repeated / T_pvw_batch
```

The backend-vs-wrapper comparison isolates the AVX/materialization path within
the same exact MAT/PVW algorithm. Noise/resource are side conditions, not part
of the latency numerator.
""",
    )
    write_text(
        PLAN,
        """# Stage224 Experiment Plan

1. Build and run wrapper fused FromDFT-add full-SAB benchmark.
2. Build and run backend FromDFT-add full-SAB benchmark.
3. Pair runs by index and compare `T_bootstrap/r`.
4. Record Stage148 noise/resource side conditions and the latest source-touching
   commit.
5. Do not claim compact complete-SAB acceleration or theoretical optimality.
""",
    )
    write_text(
        VARIANT,
        """# MAT-RLWE SAB Stage224 Exact Refresh

This variant continues the exact closed dense MAT/PVW route. It is not a compact
selector route. The active candidate is r=6 with `SAB_PVW_BACKEND_FROM_DFT_ADD`
and `MAT_TRGSW_AVX512_RGT4_FUSED`, evaluated by complete-SAB `T_bootstrap/r`.
""",
    )
    write_text(
        REPRO,
        f"""# Stage224 Reproduction Commands

```powershell
python scripts\\build_stage224_exact_pvw_mat_avx_resource_refresh.py
Get-Content {rel(PROOF)}
Get-Content {rel(PERF_CMP)}
```

Optional controls:

```powershell
$env:STAGE224_PERF_RUNS='3'
$env:SAB_PVW_BENCH_REPS='1'
```
""",
    )


def update_tracking(status: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 224: Exact PVW/MAT AVX Resource Refresh",
        f"""
## Stage 224: Exact PVW/MAT AVX Resource Refresh

Goal:

```text
Rerun complete-SAB T_bootstrap/r performance for the exact closed dense MAT/PVW
mainline selected after compact complete-SAB denial.
```

Status:

```text
Completed. Stage224 records {status}. It refreshes exact PVW/MAT full-SAB
performance and preserves the compact complete-SAB denial boundary.
```
""",
    )
    append_once(
        GOAL,
        "Stage224 exact PVW/MAT AVX refresh",
        f"""
- Stage224 exact PVW/MAT AVX refresh: `{status}`. This is a complete-SAB
  `T_bootstrap/r` performance refresh for the valid exact route, not a compact
  complete-SAB claim.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage224 exact PVW/MAT AVX refresh",
        f"""
- Stage224 exact PVW/MAT AVX refresh completed with `{status}`. Continue with
  fresh noise/resource rerun only if this refresh is promoted beyond Stage148.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage224_exact_pvw_mat_avx_refresh",
        f"""
H10_stage224_exact_pvw_mat_avx_refresh:
  status: exact_pvw_mat_full_sab_refresh_recorded
  evidence:
    - repro/stage224_exact_pvw_mat_avx_resource_refresh/proof_gate.csv
    - repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv
    - docs/stage224_exact_pvw_mat_avx_resource_refresh.md
  conclusion: >
    Stage224 records {status}. The valid exact closed dense MAT/PVW route is
    refreshed under T_bootstrap/r; compact complete-SAB integration remains
    denied.
""",
    )
    append_once(
        RUN_LOG,
        "stage224-exact-pvw-mat-avx-refresh-001",
        f"""stage224-exact-pvw-mat-avx-refresh-001,2026-07-04,{head},Stage 224,spqlios_avx512,python scripts/build_stage224_exact_pvw_mat_avx_resource_refresh.py,Stage223 route selection,complete SAB T_bootstrap/r,{status},"Exact PVW/MAT AVX refresh; compact complete-SAB denied.",docs/stage224_exact_pvw_mat_avx_resource_refresh.md; repro/stage224_exact_pvw_mat_avx_resource_refresh/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage224_exact_pvw_mat_avx_resource_refresh:",
        """
- stage224_exact_pvw_mat_avx_resource_refresh:
  - `docs/stage224_exact_pvw_mat_avx_resource_refresh.md`
  - `experiments/stage224_exact_pvw_mat_avx_resource_refresh_plan.md`
  - `theory_checks/stage224_exact_pvw_mat_avx_resource_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage224_exact_refresh.md`
  - `scripts/build_stage224_exact_pvw_mat_avx_resource_refresh.py`
  - `repro/stage224_exact_pvw_mat_avx_resource_refresh/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage224 exact PVW/MAT AVX refresh recorded",
        """
- [x] Stage224 exact PVW/MAT AVX refresh recorded.
""",
    )


def write_artifacts(paths: Iterable[Path]) -> None:
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path),
                "bytes": str(path.stat().st_size) if path.exists() else "0",
            }
        )
    write_csv(ARTIFACT, rows, ["path", "exists", "sha256", "bytes"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = build_inputs()
    perf_ok, perf_rows = run_perf()
    perf_cmp = build_perf_comparison(perf_rows)
    side_rows = build_side_conditions()
    proof_rows = build_proof(inputs, perf_ok, perf_cmp, side_rows)
    next_rows = build_next(proof_rows[-1]["status"])
    write_csv(INPUTS, inputs, INPUT_FIELDS)
    write_csv(PERF, perf_rows, PERF_FIELDS)
    write_csv(PERF_CMP, perf_cmp, PERF_CMP_FIELDS)
    write_csv(SIDE, side_rows, SIDE_FIELDS)
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, perf_rows, perf_cmp, side_rows, proof_rows, next_rows)
    status = proof_rows[-1]["status"]
    update_tracking(status)
    artifact_paths = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        INPUTS,
        PERF,
        PERF_CMP,
        SIDE,
        PROOF,
        NEXT,
        REPORT,
        REPRO,
        CLEANUP,
        Path(__file__),
    ]
    artifact_paths += sorted(OUT.glob("perf_build_*.log"))
    artifact_paths += sorted(OUT.glob("perf_*_run_*.log"))
    write_artifacts(artifact_paths)
    print(status)
    return 0 if status in {DECISION_POSITIVE, DECISION_NEUTRAL} else 1


if __name__ == "__main__":
    raise SystemExit(main())
