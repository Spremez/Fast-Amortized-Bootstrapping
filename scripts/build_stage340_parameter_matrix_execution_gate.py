#!/usr/bin/env python3
"""Stage340: current-head parameter-matrix execution gate."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import subprocess
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get(
    "STAGE340_OUT_DIR",
    ROOT / "repro" / "stage340_parameter_matrix_current_head_gate",
))
if not OUT.is_absolute():
    OUT = ROOT / OUT
RAW = OUT / "raw"

DOC = ROOT / "docs" / "stage340_parameter_matrix_current_head_gate.md"
THEORY = ROOT / "theory_checks" / "stage340_parameter_matrix_model.md"
PLAN = ROOT / "experiments" / "stage341_parameter_matrix_execution_or_literature_plan.md"
RUNNER = ROOT / "scripts" / "run_stage340_parameter_matrix_current_head.sh"
BUILDER = ROOT / "scripts" / "build_stage340_parameter_matrix_execution_gate.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE339_SUMMARY = ROOT / "repro" / "stage339_scoped_paper_package_refresh" / "summary.csv"
STAGE339_PARAM = ROOT / "repro" / "stage339_scoped_paper_package_refresh" / "parameter_coverage.csv"
STAGE331_SUMMARY = ROOT / "repro" / "stage331_current_head_highstat_refresh" / "summary.csv"
STAGE36_TARGET_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE36_TARGET_NOISE = ROOT / "repro" / "stage36_target_noise_seeds50" / "aggregate.csv"
STAGE36_ADDED_PERF = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "performance_stats.csv"
STAGE36_ADDED_NOISE = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "noise_summary.csv"

SUMMARY = OUT / "summary.csv"
HOTCODE = OUT / "hotcode_equivalence.csv"
PLATFORM = OUT / "platform_gate.csv"
EXECUTION = OUT / "execution_matrix.csv"
HISTORICAL = OUT / "historical_evidence_map.csv"
PARSED_PERF = OUT / "parsed_perf_samples.csv"
PARSED_SUMMARY = OUT / "parsed_result_summary.csv"
CLAIMS = OUT / "claim_update.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage340_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"
EXEC_PLAN = OUT / "execution_plan.csv"
DRY_COMMANDS = OUT / "dry_run_commands.sh"

DECISION_READY = "READY_STAGE340_CURRENT_HEAD_MATRIX_HARNESS_NO_NEW_PERFORMANCE_CLAIM"
DECISION_PASS = "PASS_STAGE340_CURRENT_HEAD_PARAMETER_MATRIX_REFRESH"
DECISION_PARTIAL = "PARTIAL_STAGE340_CURRENT_HEAD_PARAMETER_MATRIX_REFRESH"

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
NOISE_RE = re.compile(
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
NOISE_OVERALL_RE = re.compile(
    r"SAB_PVW_NONBINARY_TARGET_NOISE target full final-output gate: (?P<overall_gate>Pass|Fail)"
)
TIME_RSS_RE = re.compile(r"Maximum resident set size \(kbytes\): (?P<time_maxrss_kb>\d+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return (
        path.read_text(encoding="utf-8", errors="replace")
        .replace("\x00", "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if current and not current.endswith("\n"):
            handle.write("\n")
        handle.write(text.lstrip())
        if not text.endswith("\n"):
            handle.write("\n")


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def git_diff_names(base: str, paths: list[str]) -> list[str]:
    if not base or base == "unknown":
        return []
    try:
        cmd = ["git", "diff", "--name-only", f"{base}..HEAD", "--", *paths]
        out = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        return [line.strip() for line in out.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def cmd_status(cmd: list[str]) -> tuple[str, str]:
    try:
        out = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.STDOUT, timeout=10)
        return "PRESENT", out.strip().splitlines()[0] if out.strip() else ""
    except Exception as exc:  # noqa: BLE001 - probe diagnostics only
        return "MISSING", str(exc).splitlines()[0]


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


def first_row(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def hotcode_rows() -> list[dict[str, object]]:
    stage331 = first_row(STAGE331_SUMMARY)
    base = stage331.get("git_head", "")
    hot_diff = git_diff_names(base, ["src", "Makefile", "include"])
    broader_diff = git_diff_names(base, ["src", "Makefile", "include", "scripts/run_stage331_current_head_highstat_refresh.sh"])
    return [
        {
            "basis": "stage331_primary_run_head_to_current_head",
            "stage331_head": base,
            "current_head": git_head(),
            "hotcode_paths_checked": "src;Makefile;include",
            "hotcode_diff_count": len(hot_diff),
            "hotcode_diff_paths": ";".join(hot_diff),
            "runner_diff_count": len(broader_diff) - len(hot_diff),
            "status": "HOTCODE_EQUIVALENT" if base and not hot_diff else "HOTCODE_CHANGED_RERUN_REQUIRED",
        }
    ]


def platform_rows() -> list[dict[str, object]]:
    bash_status, bash_detail = cmd_status(["bash", "--version"])
    uname_status, uname_detail = cmd_status(["uname", "-a"])
    proc_version = read_text(Path("/proc/version")) if Path("/proc/version").exists() else ""
    runtime_kind = "WSL_OR_LINUX"
    if "microsoft" in proc_version.lower() or "wsl" in proc_version.lower():
        runtime_kind = "WSL"
    elif uname_status != "PRESENT":
        runtime_kind = "UNKNOWN"
    return [
        {
            "probe": "bash",
            "status": bash_status,
            "detail": bash_detail,
            "interpretation": "Can run dry-run/harness scripts." if bash_status == "PRESENT" else "Bash unavailable.",
        },
        {
            "probe": "linux_runtime",
            "status": uname_status,
            "detail": uname_detail,
            "interpretation": f"Runtime kind={runtime_kind}; performance claims still require executed logs.",
        },
        {
            "probe": "performance_execution",
            "status": "NOT_EXECUTED_THIS_STAGE",
            "detail": "Stage340 harness defaults to dry-run.",
            "interpretation": "No new performance claim is created by the gate itself.",
        },
    ]


def historical_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    stage331 = first_row(STAGE331_SUMMARY)
    rows.append({
        "parameter": "SET_2_3_2048 include-zero",
        "r": "4",
        "evidence_class": "current_head_primary",
        "perf_speedup": stage331.get("speedup_vs_repeated_scalar_mean", ""),
        "perf_samples": stage331.get("samples", ""),
        "noise_status": f"{stage331.get('noise_pair_failures', '')}/{stage331.get('noise_trials', '')}",
        "source": rel(STAGE331_SUMMARY),
        "claim_use": "main scoped claim if hotcode-equivalent",
    })
    target_noise = {row.get("r", ""): row for row in read_csv(STAGE36_TARGET_NOISE)}
    for row in read_csv(STAGE36_TARGET_PERF):
        noise = target_noise.get(row.get("r", ""), {})
        rows.append({
            "parameter": "SET_2_3_2048",
            "r": row.get("r", ""),
            "evidence_class": "historical_target_matrix",
            "perf_speedup": row.get("mean_speedup", ""),
            "perf_samples": row.get("samples", ""),
            "noise_status": f"{noise.get('pair_failures', '')}/{noise.get('seeds', '')}",
            "source": rel(STAGE36_TARGET_PERF),
            "claim_use": "supporting only; rerun for current-head broader claim",
        })
    added_noise = {(row.get("param", ""), row.get("r", "")): row for row in read_csv(STAGE36_ADDED_NOISE)}
    for row in read_csv(STAGE36_ADDED_PERF):
        noise = added_noise.get((row.get("param", ""), row.get("r", "")), {})
        rows.append({
            "parameter": row.get("param", ""),
            "r": row.get("r", ""),
            "evidence_class": "historical_added_binary_matrix",
            "perf_speedup": row.get("mean_speedup", ""),
            "perf_samples": row.get("runs", ""),
            "noise_status": f"{noise.get('pair_failures', '')}/{noise.get('seeds', '')}",
            "source": rel(STAGE36_ADDED_PERF),
            "claim_use": "supporting only; rerun for current-head broader claim",
        })
    return rows


def execution_rows(hot_status: str) -> list[dict[str, object]]:
    plan = read_csv(EXEC_PLAN)
    plan_cmd = {(row.get("param", ""), row.get("r", ""), row.get("kind", "")): row.get("command", "") for row in plan}
    params = ["SET_2_3_2048", "SET_4_5_2048", "SET_2_3_4096"]
    rows: list[dict[str, object]] = []
    for param in params:
        for r in ["2", "4"]:
            case = f"{param}_r{r}"
            perf_logs = sorted((RAW / case / "perf").glob("run_*.log"))
            noise_log = RAW / case / "noise" / "run.log"
            if perf_logs and noise_log.exists():
                status = "RESULT_LOGS_PRESENT_PARSE_GATE"
            elif param == "SET_2_3_2048" and r == "4" and hot_status == "HOTCODE_EQUIVALENT":
                status = "SATISFIED_BY_STAGE331_HOTCODE_EQUIVALENT_PRIMARY"
            else:
                status = "NEEDS_CURRENT_HEAD_EXECUTION"
            rows.append({
                "case": case,
                "parameter": param,
                "r": r,
                "status": status,
                "perf_command": plan_cmd.get((param, r, "perf"), ""),
                "noise_command": plan_cmd.get((param, r, "noise"), ""),
                "gate": "complete SAB T_bootstrap/r A/B plus noise/RSS; same backend; no claim if missing logs",
            })
    return rows


def parse_perf_logs() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(RAW.glob("*_r*/perf/run_*.log")):
        case = path.parts[-3]
        parts = case.rsplit("_r", 1)
        param = parts[0]
        case_r = parts[1] if len(parts) > 1 else ""
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "case": case,
                "parameter": param,
                "r": sample.group("r") or case_r,
                "outer_log": path.name,
                "inner_rep": sample.group("rep"),
                "correctness": correctness,
                "pvw_lane_us": sample.group("pvw_lane_us"),
                "scalar_lane_us": sample.group("scalar_lane_us"),
                "speedup_vs_repeated_scalar": sample.group("speedup"),
                "source_log": rel(path),
            })
    return rows


def parse_noise(case: str) -> dict[str, object]:
    noise_dir = RAW / case / "noise"
    run_log = noise_dir / "run.log"
    time_log = noise_dir / "time.log"
    row: dict[str, object] = {
        "case": case,
        "noise_trials": "",
        "noise_pair_failures": "",
        "noise_gate": "MISSING",
        "time_maxrss_kb": "",
    }
    text = read_text(run_log)
    match = NOISE_RE.search(text)
    if match:
        row["noise_trials"] = match.group("trials")
        row["noise_pair_failures"] = match.group("pair_failures")
        row["noise_gate"] = match.group("gate")
    overall = NOISE_OVERALL_RE.search(text)
    if overall:
        row["noise_overall_gate"] = overall.group("overall_gate")
    rss = TIME_RSS_RE.search(read_text(time_log))
    if rss:
        row["time_maxrss_kb"] = rss.group("time_maxrss_kb")
    return row


def result_summary_rows(samples: list[dict[str, object]]) -> list[dict[str, object]]:
    by_case: dict[str, list[dict[str, object]]] = {}
    for row in samples:
        by_case.setdefault(str(row.get("case", "")), []).append(row)
    rows: list[dict[str, object]] = []
    for case, vals in sorted(by_case.items()):
        lanes = [fnum(row.get("pvw_lane_us")) for row in vals]
        scalars = [fnum(row.get("scalar_lane_us")) for row in vals]
        speedups = [fnum(row.get("speedup_vs_repeated_scalar")) for row in vals]
        low, high = ci95(lanes)
        noise = parse_noise(case)
        rows.append({
            "case": case,
            "parameter": vals[0].get("parameter", ""),
            "r": vals[0].get("r", ""),
            "samples": len(vals),
            "correctness": "Pass" if {row.get("correctness") for row in vals} == {"Pass"} else "MIXED_OR_MISSING",
            "pvw_t_over_r_mean_us": f"{mean(lanes):.3f}" if lanes else "",
            "pvw_t_over_r_ci95_us": f"{low:.3f}..{high:.3f}" if lanes else "",
            "scalar_t_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
            "speedup_mean": f"{mean(speedups):.6f}" if speedups else "",
            "noise_trials": noise.get("noise_trials", ""),
            "noise_pair_failures": noise.get("noise_pair_failures", ""),
            "noise_gate": noise.get("noise_gate", ""),
            "time_maxrss_kb": noise.get("time_maxrss_kb", ""),
            "status": "PASS_EXECUTED_CASE" if len(vals) >= 10 and noise.get("noise_pair_failures") == "0" else "PARTIAL_OR_MISSING_GATE",
        })
    return rows


def claim_rows(decision: str, hot_status: str, result_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    executed = len(result_rows)
    return [
        {
            "claim": "primary_r4_SET_2_3_2048",
            "status": "UNCHANGED_SUPPORTED" if hot_status == "HOTCODE_EQUIVALENT" else "RERUN_REQUIRED",
            "statement": "Stage331 primary r=4 result remains hot-code current if no src/Makefile/include changes occurred.",
            "evidence": f"{rel(STAGE331_SUMMARY)}; {rel(HOTCODE)}",
        },
        {
            "claim": "current_head_parameter_matrix",
            "status": "PASS" if decision == DECISION_PASS else "NOT_PROMOTED",
            "statement": f"Executed current-head matrix cases parsed: {executed}.",
            "evidence": rel(PARSED_SUMMARY),
        },
        {
            "claim": "broader_parameter_generality",
            "status": "BLOCK_UNTIL_STAGE340_EXECUTED",
            "statement": "Historical parameter rows remain supporting evidence only until current-head matrix logs pass.",
            "evidence": rel(HISTORICAL),
        },
        {
            "claim": "new_performance_speedup",
            "status": "NO_NEW_CLAIM_THIS_STAGE" if decision == DECISION_READY else "SEE_PARSED_RESULTS",
            "statement": "The harness gate itself does not create a new performance result.",
            "evidence": rel(PROOF),
        },
    ]


def proof_rows(
    hot_status: str,
    exec_rows: list[dict[str, object]],
    result_rows: list[dict[str, object]],
    decision: str,
) -> list[dict[str, object]]:
    stage339 = first_row(STAGE339_SUMMARY)
    missing = [row for row in exec_rows if row.get("status") == "NEEDS_CURRENT_HEAD_EXECUTION"]
    passed = [row for row in result_rows if row.get("status") == "PASS_EXECUTED_CASE"]
    return [
        {
            "gate": "G1_stage339_route",
            "status": "PASS" if stage339.get("decision") else "MISSING",
            "metric": "Stage339 decision",
            "value": stage339.get("decision", ""),
            "interpretation": "Stage340 follows the parameter-matrix route.",
        },
        {
            "gate": "G2_hotcode_equivalence",
            "status": "PASS" if hot_status == "HOTCODE_EQUIVALENT" else "RERUN_REQUIRED",
            "metric": "src/Makefile/include diff since Stage331",
            "value": hot_status,
            "interpretation": "Primary r=4 result remains hot-code current only if this passes.",
        },
        {
            "gate": "G3_harness_ready",
            "status": "PASS",
            "metric": "runner and builder",
            "value": f"{rel(RUNNER)}; {rel(BUILDER)}",
            "interpretation": "The matrix can be executed with STAGE340_EXECUTE=1 on WSL/Linux.",
        },
        {
            "gate": "G4_current_head_matrix_coverage",
            "status": "PASS" if not missing else "PARTIAL",
            "metric": "missing current-head cases",
            "value": str(len(missing)),
            "interpretation": "Broader parameter claims require every intended case to pass.",
        },
        {
            "gate": "G5_executed_result_cases",
            "status": "PASS" if passed and len(missing) == 0 else "NOT_EXECUTED_OR_PARTIAL",
            "metric": "passed executed cases",
            "value": str(len(passed)),
            "interpretation": "No new speedup claim is allowed if no executed cases are parsed.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls whether Stage341 runs the matrix, verifies literature, or admits a new mechanism/proof.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage341_execute_current_head_parameter_matrix",
            "entry_condition": "Broader parameter wording is desired and WSL/Linux performance platform is available.",
            "command": "STAGE340_EXECUTE=1 STAGE340_PERF_RUNS=10 STAGE340_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage340_parameter_matrix_current_head.sh",
            "gate": "all intended parameter/r cases pass correctness, T_bootstrap/r A/B, noise, and RSS gates",
            "failure_action": "Keep Stage339 scoped primary claim only.",
        },
        {
            "priority": "P1",
            "route": "stage341_verified_related_work_matrix",
            "entry_condition": "Novelty wording is needed before paper drafting.",
            "command": "source-verified literature audit with real DOI/ePrint/TCHES/ICALP sources",
            "gate": "no citation or novelty claim without fulltext/source support",
            "failure_action": "Write scoped systems result without novelty overclaim.",
        },
        {
            "priority": "P2",
            "route": "stage341_new_mechanism_or_formal_proof",
            "entry_condition": "A concrete new mechanism or closed compact-state proof appears.",
            "command": "mechanism/proof preflight before SAB hot-path code",
            "gate": "isolated equivalence and microbench, or formal keygen/security/noise proof",
            "failure_action": "Reject before production integration.",
        },
    ]


def append_run_log(decision: str) -> None:
    marker = "stage340-parameter-matrix-gate-001"
    if marker in read_text(RUN_LOG):
        return
    exists = RUN_LOG.exists()
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        if not exists:
            writer.writerow(["run_id", "date", "git_head", "stage", "backend", "command", "params", "seed", "status", "interpretation", "artifacts"])
        writer.writerow([
            marker,
            "2026-07-06",
            git_head(),
            "Stage 340",
            "harness-gate",
            "STAGE340_EXECUTE=0 bash scripts/run_stage340_parameter_matrix_current_head.sh",
            "SET_2_3_2048/SET_4_5_2048/SET_2_3_4096; r=2/4; dry-run gate",
            "n/a",
            decision,
            "Adds current-head parameter-matrix harness and keeps broader speedup claims blocked until executed WSL/Linux logs pass.",
            f"{rel(DOC)}; {rel(EXECUTION)}; {rel(HOTCODE)}; {rel(PROOF)}",
        ])


def artifact_index(paths: list[Path]) -> None:
    rows = []
    for path in paths:
        rows.append({
            "artifact": rel(path),
            "exists": path.exists(),
            "bytes": file_size(path),
            "sha256": sha256_file(path),
        })
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    hot = hotcode_rows()
    hot_status = str(hot[0].get("status", ""))
    platform = platform_rows()
    historical = historical_rows()
    exec_rows = execution_rows(hot_status)
    samples = parse_perf_logs()
    result_rows = result_summary_rows(samples)
    missing = [row for row in exec_rows if row.get("status") == "NEEDS_CURRENT_HEAD_EXECUTION"]
    pass_cases = [row for row in result_rows if row.get("status") == "PASS_EXECUTED_CASE"]
    if pass_cases and not missing:
        decision = DECISION_PASS
    elif samples:
        decision = DECISION_PARTIAL
    else:
        decision = DECISION_READY
    claims = claim_rows(decision, hot_status, result_rows)
    proof = proof_rows(hot_status, exec_rows, result_rows, decision)
    nextq = next_rows()
    summary = [{
        "decision": decision,
        "current_head": git_head(),
        "stage331_head": first_row(STAGE331_SUMMARY).get("git_head", ""),
        "hotcode_status": hot_status,
        "primary_supported_speedup": first_row(STAGE331_SUMMARY).get("speedup_vs_repeated_scalar_mean", ""),
        "executed_case_count": len(result_rows),
        "missing_current_head_cases": len(missing),
        "claim_status": "no_new_performance_claim" if decision == DECISION_READY else "see_parsed_results",
        "next_required": "execute Stage340 matrix on WSL/Linux or switch to verified literature/new mechanism/proof route",
    }]

    write_csv(SUMMARY, summary, ["decision", "current_head", "stage331_head", "hotcode_status", "primary_supported_speedup", "executed_case_count", "missing_current_head_cases", "claim_status", "next_required"])
    write_csv(HOTCODE, hot, ["basis", "stage331_head", "current_head", "hotcode_paths_checked", "hotcode_diff_count", "hotcode_diff_paths", "runner_diff_count", "status"])
    write_csv(PLATFORM, platform, ["probe", "status", "detail", "interpretation"])
    write_csv(EXECUTION, exec_rows, ["case", "parameter", "r", "status", "perf_command", "noise_command", "gate"])
    write_csv(HISTORICAL, historical, ["parameter", "r", "evidence_class", "perf_speedup", "perf_samples", "noise_status", "source", "claim_use"])
    write_csv(PARSED_PERF, samples, ["case", "parameter", "r", "outer_log", "inner_rep", "correctness", "pvw_lane_us", "scalar_lane_us", "speedup_vs_repeated_scalar", "source_log"])
    write_csv(PARSED_SUMMARY, result_rows, ["case", "parameter", "r", "samples", "correctness", "pvw_t_over_r_mean_us", "pvw_t_over_r_ci95_us", "scalar_t_over_r_mean_us", "speedup_mean", "noise_trials", "noise_pair_failures", "noise_gate", "time_maxrss_kb", "status"])
    write_csv(CLAIMS, claims, ["claim", "status", "statement", "evidence"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "command", "gate", "failure_action"])
    write_text(COMMANDS, """# Stage340 Reproduction Commands

Dry-run gate:

```powershell
bash scripts/run_stage340_parameter_matrix_current_head.sh
```

Execute on WSL/Linux performance platform:

```sh
STAGE340_EXECUTE=1 STAGE340_PERF_RUNS=10 STAGE340_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage340_parameter_matrix_current_head.sh
```

Parse existing logs only:

```powershell
python scripts\\build_stage340_parameter_matrix_execution_gate.py
```
""")

    write_text(REPORT, f"""# Stage340 Parameter Matrix Current-Head Gate

Decision: `{decision}`.

Stage340 adds the executable gate for broadening the parameter claim. It does
not create a new speedup result unless `STAGE340_EXECUTE=1` logs are present and
parse successfully.

## Summary

{md_table(summary, ["decision", "current_head", "stage331_head", "hotcode_status", "primary_supported_speedup", "executed_case_count", "missing_current_head_cases", "claim_status"])}

## Hot-Code Equivalence

{md_table(hot, ["stage331_head", "current_head", "hotcode_diff_count", "hotcode_diff_paths", "status"])}

## Execution Matrix

{md_table(exec_rows, ["case", "status", "gate"])}

## Historical Evidence Map

{md_table(historical, ["parameter", "r", "evidence_class", "perf_speedup", "perf_samples", "noise_status", "claim_use"])}

## Claim Update

{md_table(claims, ["claim", "status", "statement"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}
""")

    write_text(DOC, f"""# Stage340 Parameter Matrix Current-Head Gate

Decision: `{decision}`.

The Stage339 result remains scoped unless this matrix is executed on the
performance platform and all intended parameter/r cases pass. Stage340 provides
the harness, hot-code equivalence check, execution matrix, and parser.

## Current Status

{md_table(summary, ["decision", "hotcode_status", "primary_supported_speedup", "executed_case_count", "missing_current_head_cases", "claim_status"])}

## Next Routes

{md_table(nextq, ["priority", "route", "command", "gate", "failure_action"])}
""")

    write_text(THEORY, """# Stage340 Parameter Matrix Model

The Stage339 primary claim is scoped to one current-head r=4 row. A broader
parameter claim requires current-head evidence for every claimed parameter and
body-lane count.

Hot-code equivalence is checked separately from the Git commit id. If Stage331's
run head differs from HEAD but `src/`, `Makefile`, and `include/` have not
changed, the primary r=4 performance evidence can remain hot-code current. This
does not promote historical r=2 or added-parameter rows; those still require
fresh current-head logs before broader wording.

The primary metric remains complete `T_bootstrap/r` against repeated scalar SAB
under the same backend. Windows or dry-run output is not performance evidence.
""")

    write_text(PLAN, """# Stage341 Parameter Matrix Execution Or Literature Plan

Stage341 must choose one path.

## Execute Matrix

Run on WSL/Linux performance platform:

```sh
STAGE340_EXECUTE=1 STAGE340_PERF_RUNS=10 STAGE340_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage340_parameter_matrix_current_head.sh
```

Promotion requires every claimed parameter/r case to pass complete SAB
correctness, `T_bootstrap/r` A/B, noise, and RSS gates.

## Verify Literature

Use this route before novelty wording. Every source must be real and checked
against full text or authoritative metadata.

## New Mechanism Or Proof

Use this route only if a concrete load/store/count/backend mechanism or a
closed compact-state proof exists. Isolated gates precede SAB hot-path code.
""")

    append_once(GOAL, "<!-- stage340-parameter-matrix-gate -->", f"""
<!-- stage340-parameter-matrix-gate -->
- Stage340: `{decision}`. Added the current-head parameter-matrix harness and hot-code equivalence gate; broader parameter speedup remains blocked until executed WSL/Linux logs pass.
""")
    append_once(ROADMAP, "<!-- stage340-parameter-matrix-gate -->", f"""
<!-- stage340-parameter-matrix-gate -->
## Stage340: Parameter Matrix Current-Head Gate

- Decision: `{decision}`.
- Result: executable dry-run/execute harness for SET_2_3_2048, SET_4_5_2048, SET_2_3_4096 with r=2/4.
- Boundary: no new performance claim until logs are executed and parsed.
""")
    append_once(HYPOTHESES, "H340_parameter_matrix_current_head_gate:", f"""
H340_parameter_matrix_current_head_gate:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage340_parameter_matrix_current_head_gate/summary.csv
    - repro/stage340_parameter_matrix_current_head_gate/hotcode_equivalence.csv
    - repro/stage340_parameter_matrix_current_head_gate/execution_matrix.csv
    - repro/stage340_parameter_matrix_current_head_gate/proof_gate.csv
  conclusion: >
    Stage340 adds an executable current-head parameter-matrix gate. Historical
    parameter rows are not promoted; broader claims require executed WSL/Linux
    logs that pass the parser and proof gates.
""")
    append_once(MANIFEST, "<!-- stage340-parameter-matrix-gate-manifest -->", """
<!-- stage340-parameter-matrix-gate-manifest -->
- stage340_parameter_matrix_current_head_gate:
  - `docs/stage340_parameter_matrix_current_head_gate.md`
  - `theory_checks/stage340_parameter_matrix_model.md`
  - `experiments/stage341_parameter_matrix_execution_or_literature_plan.md`
  - `scripts/run_stage340_parameter_matrix_current_head.sh`
  - `scripts/build_stage340_parameter_matrix_execution_gate.py`
  - `repro/stage340_parameter_matrix_current_head_gate/`
""")
    append_once(CHECKLIST, "<!-- stage340-parameter-matrix-gate-checklist -->", f"""
<!-- stage340-parameter-matrix-gate-checklist -->
- [x] Stage340 records `{decision}` and provides a current-head parameter-matrix harness without promoting unexecuted results.
""")
    append_run_log(decision)
    artifact_index([
        DOC, THEORY, PLAN, RUNNER, BUILDER, SUMMARY, HOTCODE, PLATFORM, EXECUTION,
        HISTORICAL, PARSED_PERF, PARSED_SUMMARY, CLAIMS, PROOF, NEXT, REPORT,
        COMMANDS, EXEC_PLAN, DRY_COMMANDS,
    ])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
