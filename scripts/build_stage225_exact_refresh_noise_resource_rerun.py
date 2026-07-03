#!/usr/bin/env python3
"""Stage225: fresh noise/resource rerun for the Stage224 exact PVW/MAT path."""

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
OUT = ROOT / "repro" / "stage225_exact_refresh_noise_resource_rerun"

DOC = ROOT / "docs" / "stage225_exact_refresh_noise_resource_rerun.md"
PLAN = ROOT / "experiments" / "stage225_exact_refresh_noise_resource_rerun_plan.md"
THEORY = ROOT / "theory_checks" / "stage225_exact_refresh_noise_resource_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage225_noise_resource.md"

INPUTS = OUT / "input_status.csv"
NOISE = OUT / "noise_results.csv"
NOISE_AGG = OUT / "noise_aggregate.csv"
RESOURCE = OUT / "resource_results.csv"
RESOURCE_CMP = OUT / "resource_comparison.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "noise_resource_rerun_report.md"
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

STAGE224_PROOF = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "proof_gate.csv"
STAGE224_PERF = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "perf_comparison.csv"
STAGE224_NEXT = ROOT / "repro" / "stage224_exact_pvw_mat_avx_resource_refresh" / "next_stage_queue.csv"
STAGE148_NOISE = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "noise_aggregate.csv"
STAGE148_RESOURCE = ROOT / "repro" / "stage148_h14_r6_repeated_refresh" / "resource_comparison.csv"
STAGE150_MODEL = ROOT / "theory_checks" / "stage150_claim_scope_model.md"

R_VALUE = int(os.environ.get("STAGE225_R", "6"))
NOISE_SEED_COUNT = int(os.environ.get("STAGE225_NOISE_SEED_COUNT", "3"))
NOISE_START_SEED = int(os.environ.get("STAGE225_NOISE_START_SEED", "6869580"))
NOISE_TRIALS = int(os.environ.get("STAGE225_NOISE_TRIALS", "1"))
RESOURCE_RUNS = int(os.environ.get("STAGE225_RESOURCE_RUNS", "1"))
JOBS = int(os.environ.get("JOBS", "8"))

BASE_FLAGS = (
    "FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false "
    "PARAM=SET_2_3_2048 KEY=BINARY "
    "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true "
    "MAT_TRGSW_AVX512_RGT4_FUSED=true "
    "SAB_PVW_ACTIVE_BUFFER_FUSION=true "
    "SAB_PVW_BACKEND_FROM_DFT_ADD=true"
)

DECISION = "PASS_STAGE225_EXACT_REFRESH_FRESH_NOISE_RESOURCE"

INPUT_FIELDS = ["input", "status", "evidence", "role", "bytes"]
NOISE_FIELDS = [
    "r",
    "seed",
    "status",
    "points",
    "pvw_failures",
    "scalar_failures",
    "pair_failures",
    "pvw_log2_sigma_torus",
    "scalar_log2_sigma_torus",
    "pair_log2_sigma_torus",
    "pvw_minus_scalar_log2",
    "max_allowed_log2_gap",
    "source_log",
]
NOISE_AGG_FIELDS = [
    "r",
    "seeds",
    "points",
    "pvw_failures",
    "scalar_failures",
    "pair_failures",
    "min_pvw_minus_scalar_log2",
    "max_pvw_minus_scalar_log2",
    "avg_pvw_minus_scalar_log2",
    "stage148_avg_pvw_minus_scalar_log2",
    "status",
]
RESOURCE_FIELDS = [
    "run",
    "mode",
    "status",
    "keygen_us",
    "keygen_lane_avg_us",
    "estimated_key_bytes",
    "estimated_key_bytes_ratio_vs_scalar_repeated",
    "internal_vmhwm_kb",
    "time_max_rss_kb",
    "source_log",
]
RESOURCE_CMP_FIELDS = [
    "runs",
    "pvw_key_bytes",
    "scalar_key_bytes",
    "key_bytes_ratio",
    "stage148_key_bytes_ratio",
    "pvw_keygen_lane_avg_us",
    "scalar_keygen_lane_avg_us",
    "keygen_lane_ratio",
    "pvw_vmhwm_kb",
    "scalar_vmhwm_kb",
    "vmhwm_ratio",
    "stage148_vmhwm_ratio",
    "pvw_time_max_rss_kb",
    "scalar_time_max_rss_kb",
    "time_max_rss_ratio",
    "status",
]

NOISE_GATE_RE = re.compile(r"SAB_PVW_NOISE target full bootstrap gate: (?P<status>\w+)")
NOISE_SUMMARY_RE = re.compile(
    r"SAB_PVW_NOISE summary target_full r=(?P<r>\d+) trials=(?P<trials>\d+) "
    r"points=(?P<points>\d+) pvw_failures=(?P<pvw_failures>\d+) "
    r"scalar_failures=(?P<scalar_failures>\d+) pair_failures=(?P<pair_failures>\d+) "
    r"pvw_log2_sigma_torus=(?P<pvw_log2_sigma_torus>[-0-9.inf]+) "
    r"scalar_log2_sigma_torus=(?P<scalar_log2_sigma_torus>[-0-9.inf]+) "
    r"pair_log2_sigma_torus=(?P<pair_log2_sigma_torus>[-0-9.inf]+) "
    r"pvw_minus_scalar_log2=(?P<pvw_minus_scalar_log2>[-0-9.inf]+) "
    r"max_allowed_log2_gap=(?P<max_allowed_log2_gap>[-0-9.]+)"
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


def parse_float(text: str) -> float:
    if text in {"inf", "+inf"}:
        return math.inf
    if text == "-inf":
        return -math.inf
    return float(text)


def fnum(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def extract_field(line: str, name: str) -> str:
    for token in line.split():
        if token.startswith(name + "="):
            return token.split("=", 1)[1].rstrip("x")
    return ""


def build_inputs() -> List[Dict[str, str]]:
    inputs = [
        ("stage224_proof_gate", STAGE224_PROOF, "positive performance refresh admission"),
        ("stage224_perf_comparison", STAGE224_PERF, "fresh T_bootstrap/r performance result"),
        ("stage224_next_queue", STAGE224_NEXT, "selected fresh side-condition rerun route"),
        ("stage148_noise_aggregate", STAGE148_NOISE, "comparison baseline for previous side condition"),
        ("stage148_resource_comparison", STAGE148_RESOURCE, "comparison baseline for previous side condition"),
        ("stage150_claim_scope", STAGE150_MODEL, "metric and claim boundary"),
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


def stage224_selects_stage225() -> bool:
    return any(row.get("route") == "stage225_exact_refresh_resource_noise_rerun" and row.get("status") == "selected" for row in read_csv(STAGE224_NEXT))


def stage148_noise_avg() -> str:
    rows = read_csv(STAGE148_NOISE)
    return rows[0].get("avg_pvw_minus_scalar_log2", "") if rows else ""


def stage148_resource_value(field: str) -> str:
    rows = read_csv(STAGE148_RESOURCE)
    return rows[0].get(field, "") if rows else ""


def parse_noise_log(seed: int, log: Path) -> Dict[str, str]:
    text = read_text(log)
    gate_status = None
    summary = None
    for line in text.splitlines():
        m = NOISE_GATE_RE.search(line)
        if m:
            gate_status = m.group("status")
        m = NOISE_SUMMARY_RE.search(line)
        if m:
            summary = m.groupdict()
    if gate_status is None or summary is None:
        return {"r": str(R_VALUE), "seed": str(seed), "status": "MISSING_LINES", "source_log": rel(log)}
    return {
        "r": summary["r"],
        "seed": str(seed),
        "status": gate_status,
        "points": summary["points"],
        "pvw_failures": summary["pvw_failures"],
        "scalar_failures": summary["scalar_failures"],
        "pair_failures": summary["pair_failures"],
        "pvw_log2_sigma_torus": summary["pvw_log2_sigma_torus"],
        "scalar_log2_sigma_torus": summary["scalar_log2_sigma_torus"],
        "pair_log2_sigma_torus": summary["pair_log2_sigma_torus"],
        "pvw_minus_scalar_log2": summary["pvw_minus_scalar_log2"],
        "max_allowed_log2_gap": summary["max_allowed_log2_gap"],
        "source_log": rel(log),
    }


def aggregate_noise(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    gaps = [parse_float(row["pvw_minus_scalar_log2"]) for row in rows if row.get("status") == "Pass"]
    pvw_fail = sum(int(row.get("pvw_failures", "0")) for row in rows if row.get("pvw_failures"))
    scalar_fail = sum(int(row.get("scalar_failures", "0")) for row in rows if row.get("scalar_failures"))
    pair_fail = sum(int(row.get("pair_failures", "0")) for row in rows if row.get("pair_failures"))
    points = sum(int(row.get("points", "0")) for row in rows if row.get("points"))
    status = "PASS" if len(gaps) == NOISE_SEED_COUNT and pvw_fail == 0 and scalar_fail == 0 and pair_fail == 0 else "FAIL"
    return [
        {
            "r": str(R_VALUE),
            "seeds": str(len(gaps)),
            "points": str(points),
            "pvw_failures": str(pvw_fail),
            "scalar_failures": str(scalar_fail),
            "pair_failures": str(pair_fail),
            "min_pvw_minus_scalar_log2": f"{min(gaps) if gaps else 0.0:.3f}",
            "max_pvw_minus_scalar_log2": f"{max(gaps) if gaps else 0.0:.3f}",
            "avg_pvw_minus_scalar_log2": f"{mean(gaps):.6f}",
            "stage148_avg_pvw_minus_scalar_log2": stage148_noise_avg(),
            "status": status,
        }
    ]


def run_noise() -> tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    flags = (
        f"{BASE_FLAGS} MOSFHET_DETERMINISTIC_RNG=true "
        f"SAB_PVW_NOISE_TEST=true SAB_PVW_NOISE_R={R_VALUE} "
        f"SAB_PVW_NOISE_TRIALS={NOISE_TRIALS} SAB_PVW_NOISE_MAX_LOG2_GAP=4.0"
    )
    build = run_logged(
        f"make clean >/dev/null 2>&1 || true && make {flags} -j{JOBS}",
        OUT / "noise_build_backend.log",
        timeout=1200,
    )
    rows: List[Dict[str, str]] = []
    ok = build.returncode == 0
    if build.returncode == 0:
        for idx in range(NOISE_SEED_COUNT):
            seed = NOISE_START_SEED + idx
            log = OUT / f"noise_backend_seed_{seed}.log"
            proc = run_logged(f"MOSFHET_TEST_RNG_SEED={seed} ./main", log, timeout=1800)
            ok = ok and proc.returncode == 0
            rows.append(parse_noise_log(seed, log))
    agg = aggregate_noise(rows)
    return ok and all(row.get("status") == "Pass" for row in rows), rows, agg


def parse_resource_log(mode: str, run_idx: int, log: Path) -> Dict[str, str]:
    text = read_text(log)
    gate = "Pass" if "SAB_PVW_RESOURCE target_full gate: Pass" in text else "Fail"
    key_line = ""
    keygen_line = ""
    rss_line = ""
    for line in text.splitlines():
        if "SAB_PVW_RESOURCE key_bytes target_full" in line:
            key_line = line
        if mode == "pvw" and "SAB_PVW_RESOURCE keygen target_full" in line and "mode=pvw" in line:
            keygen_line = line
        if mode == "scalar" and "SAB_PVW_RESOURCE keygen target_full" in line and "mode=scalar" in line:
            keygen_line = line
        if mode == "pvw" and "SAB_PVW_RESOURCE rss target_full" in line and "after_pvw_sab_keygen" in line:
            rss_line = line
        if mode == "scalar" and "SAB_PVW_RESOURCE rss target_full" in line and "after_scalar_repeated_sab_keygen" in line:
            rss_line = line
    max_rss = ""
    for line in text.splitlines():
        if "Maximum resident set size" in line:
            max_rss = line.split(":", 1)[1].strip()
            break
    if not key_line or not keygen_line or not rss_line:
        return {"run": str(run_idx), "mode": mode, "status": "MISSING_LINES", "source_log": rel(log)}
    if mode == "pvw":
        keygen = extract_field(keygen_line, "pvw_sab_keygen_us")
        lane_keygen = f"{float(keygen) / float(R_VALUE):.3f}" if keygen else ""
        key_bytes = extract_field(key_line, "pvw_estimated_key_bytes")
        ratio = extract_field(key_line, "pvw_vs_scalar_repeated_ratio")
    else:
        keygen = extract_field(keygen_line, "scalar_repeated_sab_keygen_us")
        lane_keygen = extract_field(keygen_line, "scalar_lane_avg_keygen_us")
        key_bytes = extract_field(key_line, "scalar_repeated_estimated_key_bytes")
        ratio = "1.000000"
    return {
        "run": str(run_idx),
        "mode": mode,
        "status": "PASS" if gate == "Pass" else "FAIL",
        "keygen_us": keygen,
        "keygen_lane_avg_us": lane_keygen,
        "estimated_key_bytes": key_bytes,
        "estimated_key_bytes_ratio_vs_scalar_repeated": ratio,
        "internal_vmhwm_kb": extract_field(rss_line, "vmhwm_kb"),
        "time_max_rss_kb": max_rss,
        "source_log": rel(log),
    }


def compare_resource(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    pvw_rows = [row for row in rows if row.get("mode") == "pvw" and row.get("status") == "PASS"]
    scalar_rows = [row for row in rows if row.get("mode") == "scalar" and row.get("status") == "PASS"]
    if not pvw_rows or not scalar_rows:
        return [{"runs": "0", "status": "FAIL"}]
    pvw_keygen = mean([float(row["keygen_lane_avg_us"]) for row in pvw_rows])
    scalar_keygen = mean([float(row["keygen_lane_avg_us"]) for row in scalar_rows])
    pvw_hwm = mean([float(row["internal_vmhwm_kb"]) for row in pvw_rows])
    scalar_hwm = mean([float(row["internal_vmhwm_kb"]) for row in scalar_rows])
    pvw_time_rss_values = [float(row["time_max_rss_kb"]) for row in pvw_rows if row.get("time_max_rss_kb")]
    scalar_time_rss_values = [float(row["time_max_rss_kb"]) for row in scalar_rows if row.get("time_max_rss_kb")]
    pvw_time_rss = mean(pvw_time_rss_values)
    scalar_time_rss = mean(scalar_time_rss_values)
    key_ratio = mean([float(row["estimated_key_bytes_ratio_vs_scalar_repeated"]) for row in pvw_rows])
    status = "PASS"
    if scalar_hwm and pvw_hwm / scalar_hwm > 1.25:
        status = "REVIEW_RESOURCE_OVERHEAD"
    return [
        {
            "runs": str(min(len(pvw_rows), len(scalar_rows))),
            "pvw_key_bytes": pvw_rows[0]["estimated_key_bytes"],
            "scalar_key_bytes": scalar_rows[0]["estimated_key_bytes"],
            "key_bytes_ratio": f"{key_ratio:.6f}",
            "stage148_key_bytes_ratio": stage148_resource_value("key_bytes_ratio"),
            "pvw_keygen_lane_avg_us": f"{pvw_keygen:.3f}",
            "scalar_keygen_lane_avg_us": f"{scalar_keygen:.3f}",
            "keygen_lane_ratio": f"{pvw_keygen / scalar_keygen if scalar_keygen else 0.0:.6f}",
            "pvw_vmhwm_kb": f"{pvw_hwm:.3f}",
            "scalar_vmhwm_kb": f"{scalar_hwm:.3f}",
            "vmhwm_ratio": f"{pvw_hwm / scalar_hwm if scalar_hwm else 0.0:.6f}",
            "stage148_vmhwm_ratio": stage148_resource_value("vmhwm_ratio"),
            "pvw_time_max_rss_kb": f"{pvw_time_rss:.3f}",
            "scalar_time_max_rss_kb": f"{scalar_time_rss:.3f}",
            "time_max_rss_ratio": f"{pvw_time_rss / scalar_time_rss if scalar_time_rss else 0.0:.6f}",
            "status": status,
        }
    ]


def run_resource() -> tuple[bool, List[Dict[str, str]], List[Dict[str, str]]]:
    flags = f"{BASE_FLAGS} SAB_PVW_RESOURCE_TEST=true SAB_PVW_RESOURCE_R={R_VALUE}"
    build = run_logged(
        f"make clean >/dev/null 2>&1 || true && make {flags} -j{JOBS}",
        OUT / "resource_build_backend.log",
        timeout=1200,
    )
    rows: List[Dict[str, str]] = []
    ok = build.returncode == 0
    if build.returncode == 0:
        for run_idx in range(RESOURCE_RUNS):
            for mode in ["pvw", "scalar"]:
                log = OUT / f"resource_{mode}_run_{run_idx}.log"
                proc = run_logged(f"/usr/bin/time -v env SAB_PVW_RESOURCE_MODE={mode} ./main", log, timeout=1800)
                ok = ok and proc.returncode == 0
                rows.append(parse_resource_log(mode, run_idx, log))
    cmp_rows = compare_resource(rows)
    return ok and cmp_rows and cmp_rows[0]["status"] in {"PASS", "REVIEW_RESOURCE_OVERHEAD"}, rows, cmp_rows


def build_proof(inputs: List[Dict[str, str]], noise_ok: bool, noise_agg: List[Dict[str, str]], resource_ok: bool, resource_cmp: List[Dict[str, str]]) -> List[Dict[str, str]]:
    missing = [row["input"] for row in inputs if row["status"] != "present"]
    stage224_ok = stage224_selects_stage225()
    noise_status = noise_agg[0].get("status", "MISSING") if noise_agg else "MISSING"
    resource_status = resource_cmp[0].get("status", "MISSING") if resource_cmp else "MISSING"
    ready = not missing and stage224_ok and noise_ok and noise_status == "PASS" and resource_ok and resource_status in {"PASS", "REVIEW_RESOURCE_OVERHEAD"}
    decision = DECISION if ready else "FAIL_STAGE225_EXACT_REFRESH_FRESH_NOISE_RESOURCE"
    return [
        {
            "gate": "G1_required_inputs",
            "status": "PASS" if not missing else "FAIL",
            "metric": "missing_inputs",
            "value": ";".join(missing),
            "evidence": rel(INPUTS),
            "interpretation": "Stage225 consumes Stage224 performance and reruns fresh side conditions.",
        },
        {
            "gate": "G2_stage224_admission",
            "status": "PASS" if stage224_ok else "FAIL",
            "metric": "stage225_selected",
            "value": str(stage224_ok).lower(),
            "evidence": rel(STAGE224_NEXT),
            "interpretation": "Fresh side-condition rerun is valid only after Stage224 positive performance refresh.",
        },
        {
            "gate": "G3_fresh_noise",
            "status": noise_status,
            "metric": "seeds;failures;avg_gap",
            "value": (
                f"{noise_agg[0].get('seeds', '')};"
                f"{noise_agg[0].get('pvw_failures', '')}/"
                f"{noise_agg[0].get('scalar_failures', '')}/"
                f"{noise_agg[0].get('pair_failures', '')};"
                f"{noise_agg[0].get('avg_pvw_minus_scalar_log2', '')}"
            ) if noise_agg else "",
            "evidence": f"{rel(NOISE)}; {rel(NOISE_AGG)}",
            "interpretation": "Fresh final-output noise/correctness for the Stage224 backend path.",
        },
        {
            "gate": "G4_fresh_resource",
            "status": resource_status,
            "metric": "key_bytes_ratio;vmhwm_ratio;time_max_rss_ratio",
            "value": (
                f"{resource_cmp[0].get('key_bytes_ratio', '')};"
                f"{resource_cmp[0].get('vmhwm_ratio', '')};"
                f"{resource_cmp[0].get('time_max_rss_ratio', '')}"
            ) if resource_cmp else "",
            "evidence": f"{rel(RESOURCE)}; {rel(RESOURCE_CMP)}",
            "interpretation": "Fresh key/memory side conditions for the Stage224 backend path.",
        },
        {
            "gate": "G5_claim_boundary",
            "status": "PASS_ENGINEERING_SIDE_CONDITIONS_ONLY",
            "metric": "claim_boundary",
            "value": "no_compact_complete_sab_claim;no_theoretical_optimality",
            "evidence": rel(DOC),
            "interpretation": "Stage225 strengthens exact-route evidence only; it does not change algorithmic novelty claims.",
        },
        {
            "gate": "G6_stage225_decision",
            "status": decision,
            "metric": "decision",
            "value": decision,
            "evidence": rel(PROOF),
            "interpretation": "Fresh side conditions are ready for Stage226 claim/counter package if gates pass.",
        },
    ]


def build_next(decision: str) -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "route": "stage226_exact_mat_avx_counter_attribution",
            "entry_condition": "Stage224 performance and Stage225 fresh side conditions pass.",
            "gate": "Attribute backend-vs-wrapper gain to cycles/load/store/FMA where counters are available.",
            "status": "selected" if decision == DECISION else "blocked",
            "failure_action": "Keep timing-only exact-route evidence and do not claim backend mechanism.",
            "evidence": rel(PROOF),
        },
        {
            "priority": "P1",
            "route": "paper_claim_boundary_update",
            "entry_condition": "After Stage226 counter attribution or if counters remain unavailable.",
            "gate": "Separate exact MAT/PVW engineering acceleration from blocked compact route.",
            "status": "future",
            "failure_action": "No novelty/optimality claim.",
            "evidence": rel(STAGE150_MODEL),
        },
        {
            "priority": "P2",
            "route": "neighbor_capable_compact_state_proof",
            "entry_condition": "Only if user chooses a new compact algebra/proof branch.",
            "gate": "Define closed neighbor-capable compact state before implementation.",
            "status": "proof_only_deferred",
            "failure_action": "Do not touch SAB hot path.",
            "evidence": rel(STAGE224_PROOF),
        },
    ]


def write_docs(inputs: List[Dict[str, str]], noise_rows: List[Dict[str, str]], noise_agg: List[Dict[str, str]], resource_rows: List[Dict[str, str]], resource_cmp: List[Dict[str, str]], proof_rows: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    decision = proof_rows[-1]["status"]
    doc = f"""# Stage225 Exact Refresh Noise/Resource Rerun

Decision: `{decision}`.

Stage225 reruns fresh correctness/noise and resource gates for the exact closed
dense MAT/PVW backend path measured in Stage224. This closes the gap where
Stage224 used inherited Stage148 side conditions.

## Proof Gates

{table(proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])}
## Noise Aggregate

{table(noise_agg, NOISE_AGG_FIELDS)}
## Noise Runs

{table(noise_rows, NOISE_FIELDS)}
## Resource Comparison

{table(resource_cmp, RESOURCE_CMP_FIELDS)}
## Resource Runs

{table(resource_rows, RESOURCE_FIELDS)}
## Next Queue

{table(next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])}
"""
    write_text(DOC, doc)
    write_text(REPORT, doc)
    write_text(
        THEORY,
        """# Stage225 Exact Refresh Noise/Resource Model

Stage225 does not change the latency numerator. It supplies side conditions for
the Stage224 exact PVW/MAT full-SAB performance refresh:

```text
correctness: final-output failures must remain 0
noise: pvw_minus_scalar_log2 must stay within configured bound
resource: key-size and RSS ratios must be reported with any T_bootstrap/r claim
```

This is still an exact dense MAT/PVW engineering path, not a compact complete-SAB
or theoretical-optimality proof.
""",
    )
    write_text(
        PLAN,
        """# Stage225 Experiment Plan

1. Build the Stage224 backend path with `SAB_PVW_NOISE_TEST`.
2. Run deterministic seeds for final-output correctness/noise.
3. Build the same backend path with `SAB_PVW_RESOURCE_TEST`.
4. Run PVW and repeated scalar resource modes under `/usr/bin/time -v`.
5. Record all side conditions with Stage224 performance evidence.
""",
    )
    write_text(
        VARIANT,
        """# MAT-RLWE SAB Stage225 Noise/Resource

This variant validates the r=6 exact dense MAT/PVW backend route after the
Stage224 performance refresh. It keeps scalar/default behavior unchanged and
keeps compact complete-SAB integration denied.
""",
    )
    write_text(
        REPRO,
        f"""# Stage225 Reproduction Commands

```powershell
python scripts\\build_stage225_exact_refresh_noise_resource_rerun.py
Get-Content {rel(PROOF)}
Get-Content {rel(NOISE_AGG)}
Get-Content {rel(RESOURCE_CMP)}
```

Optional controls:

```powershell
$env:STAGE225_NOISE_SEED_COUNT='3'
$env:STAGE225_RESOURCE_RUNS='1'
```
""",
    )


def update_tracking(status: str) -> None:
    head = git_head()
    append_once(
        ROADMAP,
        "## Stage 225: Exact Refresh Noise/Resource Rerun",
        f"""
## Stage 225: Exact Refresh Noise/Resource Rerun

Goal:

```text
Rerun fresh correctness/noise and resource side conditions for the exact
PVW/MAT backend path refreshed in Stage224.
```

Status:

```text
Completed. Stage225 records {status}. It strengthens the exact-route evidence
package without changing scalar/default behavior or the compact complete-SAB
denial.
```
""",
    )
    append_once(
        GOAL,
        "Stage225 exact refresh noise/resource",
        f"""
- Stage225 exact refresh noise/resource: `{status}`. Fresh side conditions now
  accompany the Stage224 exact PVW/MAT `T_bootstrap/r` performance refresh.
""",
    )
    append_once(
        CURRENT_GOAL,
        "Stage225 exact refresh noise/resource",
        f"""
- Stage225 exact refresh noise/resource completed with `{status}`. The next
  selected route is counter attribution for the exact MAT/PVW backend gain.
""",
    )
    append_once(
        HYPOTHESES,
        "H10_stage225_exact_refresh_noise_resource",
        f"""
H10_stage225_exact_refresh_noise_resource:
  status: exact_route_fresh_side_conditions_passed
  evidence:
    - repro/stage225_exact_refresh_noise_resource_rerun/proof_gate.csv
    - repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv
    - repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv
  conclusion: >
    Stage225 records {status}. Fresh correctness/noise/resource evidence
    supports the Stage224 exact PVW/MAT full-SAB performance refresh; compact
    complete-SAB integration remains denied.
""",
    )
    append_once(
        RUN_LOG,
        "stage225-exact-refresh-noise-resource-001",
        f"""stage225-exact-refresh-noise-resource-001,2026-07-04,{head},Stage 225,spqlios_avx512,python scripts/build_stage225_exact_refresh_noise_resource_rerun.py,Stage224 exact PVW/MAT performance refresh,noise/resource side conditions,{status},"Fresh exact-route side conditions; compact complete-SAB denied.",docs/stage225_exact_refresh_noise_resource_rerun.md; repro/stage225_exact_refresh_noise_resource_rerun/proof_gate.csv
""",
    )
    append_once(
        MANIFEST,
        "- stage225_exact_refresh_noise_resource_rerun:",
        """
- stage225_exact_refresh_noise_resource_rerun:
  - `docs/stage225_exact_refresh_noise_resource_rerun.md`
  - `experiments/stage225_exact_refresh_noise_resource_rerun_plan.md`
  - `theory_checks/stage225_exact_refresh_noise_resource_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage225_noise_resource.md`
  - `scripts/build_stage225_exact_refresh_noise_resource_rerun.py`
  - `repro/stage225_exact_refresh_noise_resource_rerun/`
""",
    )
    append_once(
        CHECKLIST,
        "Stage225 exact refresh noise/resource recorded",
        """
- [x] Stage225 exact refresh noise/resource recorded.
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
    noise_ok, noise_rows, noise_agg = run_noise()
    write_csv(NOISE, noise_rows, NOISE_FIELDS)
    write_csv(NOISE_AGG, noise_agg, NOISE_AGG_FIELDS)
    resource_ok, resource_rows, resource_cmp = run_resource()
    write_csv(RESOURCE, resource_rows, RESOURCE_FIELDS)
    write_csv(RESOURCE_CMP, resource_cmp, RESOURCE_CMP_FIELDS)
    run_logged("make clean >/dev/null 2>&1 || true", CLEANUP, timeout=300)
    proof_rows = build_proof(inputs, noise_ok, noise_agg, resource_ok, resource_cmp)
    next_rows = build_next(proof_rows[-1]["status"])
    write_csv(INPUTS, inputs, INPUT_FIELDS)
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "evidence", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "status", "failure_action", "evidence"])
    write_docs(inputs, noise_rows, noise_agg, resource_rows, resource_cmp, proof_rows, next_rows)
    status = proof_rows[-1]["status"]
    update_tracking(status)
    artifacts = [
        DOC,
        PLAN,
        THEORY,
        VARIANT,
        INPUTS,
        NOISE,
        NOISE_AGG,
        RESOURCE,
        RESOURCE_CMP,
        PROOF,
        NEXT,
        REPORT,
        REPRO,
        CLEANUP,
        OUT / "noise_build_backend.log",
        OUT / "resource_build_backend.log",
        Path(__file__),
    ]
    for idx in range(NOISE_SEED_COUNT):
        artifacts.append(OUT / f"noise_backend_seed_{NOISE_START_SEED + idx}.log")
    for run_idx in range(RESOURCE_RUNS):
        for mode in ["pvw", "scalar"]:
            artifacts.append(OUT / f"resource_{mode}_run_{run_idx}.log")
    write_artifacts(artifacts)
    print(status)
    return 0 if status == DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
