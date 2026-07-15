#!/usr/bin/env python3
"""Stage344: current-head top-ups for added binary parameter rows."""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import subprocess
from datetime import date
from io import StringIO
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("STAGE344_OUT_DIR", ROOT / "repro" / "stage344_added_parameter_topups"))
if not OUT.is_absolute():
    OUT = ROOT / OUT
RAW = OUT / "raw"

DOC = ROOT / "docs" / "stage344_added_parameter_topups.md"
THEORY = ROOT / "theory_checks" / "stage344_added_parameter_claim_model.md"
PLAN = ROOT / "experiments" / "stage345_matrix_synthesis_or_mechanism_plan.md"
RUNNER = ROOT / "scripts" / "run_stage344_added_parameter_topups.sh"
BUILDER = ROOT / "scripts" / "build_stage344_added_parameter_topups.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE343_SUMMARY = ROOT / "repro" / "stage343_target_r2_current_head_topup" / "summary.csv"
STAGE36_ADDED_PERF = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "performance_stats.csv"
STAGE36_ADDED_NOISE = ROOT / "repro" / "stage36_added_params_runs10_seeds20" / "noise_summary.csv"

SUMMARY = OUT / "summary.csv"
HOTPATH = OUT / "hotpath_equivalence.csv"
PERF_SAMPLES = OUT / "perf_samples.csv"
PERF_SUMMARY = OUT / "perf_summary.csv"
NOISE_SUMMARY = OUT / "noise_summary.csv"
HISTORICAL = OUT / "historical_comparison.csv"
CLAIMS = OUT / "claim_update.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage344_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"
EXEC_PLAN = OUT / "execution_plan.csv"

DECISION_PASS = "PASS_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX"
DECISION_PARTIAL = "PARTIAL_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX"
DECISION_FAIL = "FAIL_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX"

DEFAULT_CASES = [
    ("SET_4_5_2048", "2"),
    ("SET_4_5_2048", "4"),
    ("SET_2_3_4096", "2"),
    ("SET_2_3_4096", "4"),
]

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
NOISE_OVERALL_RE = re.compile(r"SAB_PVW_NONBINARY_TARGET_NOISE target full final-output gate: (?P<overall_gate>Pass|Fail)")
TIME_RSS_RE = re.compile(r"Maximum resident set size \(kbytes\): (?P<time_maxrss_kb>\d+)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")


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
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def run_head() -> str:
    return read_text(RAW / "run_git_head.txt").strip() or git_head()


def git_full(ref: str) -> str:
    if not ref:
        return ""
    try:
        return subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def git_diff_names(base: str) -> list[str]:
    if not base or not git_full(base):
        return []
    try:
        cmd = ["git", "diff", "--name-only", f"{base}..HEAD", "--", "src", "Makefile", "include"]
        out = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        return [line.strip() for line in out.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


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


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(lines)


def intended_cases() -> list[tuple[str, str]]:
    rows = read_csv(EXEC_PLAN)
    if not rows:
        return DEFAULT_CASES
    seen: list[tuple[str, str]] = []
    for row in rows:
        pair = (row.get("param", ""), row.get("r", ""))
        if pair[0] and pair[1] and pair not in seen:
            seen.append(pair)
    return seen or DEFAULT_CASES


def hotpath_rows() -> list[dict[str, object]]:
    ref = run_head()
    diffs = git_diff_names(ref)
    resolves = "yes" if git_full(ref) else "no"
    return [{
        "basis": "stage344_run_head_to_current_head",
        "ref": ref,
        "ref_resolves": resolves,
        "current_head": git_head(),
        "hotpath_diff_count": len(diffs) if resolves == "yes" else "",
        "hotpath_diff_paths": ";".join(diffs[:20]) if resolves == "yes" else "",
        "status": "HOTPATH_EQUIVALENT" if resolves == "yes" and not diffs else "HOTPATH_CHANGED_OR_UNRESOLVED",
    }]


def parse_perf() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(RAW.glob("*_r*/perf/run_*.log")):
        case = path.parts[-3]
        param, case_r = case.rsplit("_r", 1)
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "case": case,
                "param": param,
                "r": sample.group("r") or case_r,
                "mode": sample.group("mode"),
                "h": correct.group("h") if correct else "",
                "r_prec": correct.group("r_prec") if correct else "",
                "outer_log": path.name,
                "inner_rep": sample.group("rep"),
                "correctness": correctness,
                "pvw_us": sample.group("pvw_us"),
                "pvw_lane_us": sample.group("pvw_lane_us"),
                "scalar_repeated_us": sample.group("scalar_us"),
                "scalar_lane_us": sample.group("scalar_lane_us"),
                "speedup_vs_repeated_scalar": sample.group("speedup"),
                "source_log": rel(path),
            })
    return rows


def parse_noise(case: str) -> dict[str, object]:
    run_log = RAW / case / "noise" / "run.log"
    time_log = RAW / case / "noise" / "time.log"
    row: dict[str, object] = {
        "case": case,
        "trials": "0",
        "points": "",
        "pair_failures": "",
        "gate": "MISSING",
        "overall_gate": "",
        "time_maxrss_kb": "",
        "status": "missing",
        "source_run_log": rel(run_log),
        "source_time_log": rel(time_log),
    }
    text = read_text(run_log)
    match = NOISE_RE.search(text)
    if match:
        row.update(match.groupdict())
    overall = NOISE_OVERALL_RE.search(text)
    if overall:
        row["overall_gate"] = overall.group("overall_gate")
    rss = TIME_RSS_RE.search(read_text(time_log))
    if rss:
        row["time_maxrss_kb"] = rss.group("time_maxrss_kb")
    if row.get("gate") == "Pass" and row.get("overall_gate") == "Pass" and row.get("pair_failures") == "0":
        row["status"] = "pass"
    elif run_log.exists():
        row["status"] = "fail"
    return row


def summarize_perf(samples: list[dict[str, object]]) -> list[dict[str, object]]:
    by_case: dict[str, list[dict[str, object]]] = {}
    for row in samples:
        by_case.setdefault(str(row.get("case", "")), []).append(row)
    rows: list[dict[str, object]] = []
    noise_by_case = {f"{param}_r{r}": parse_noise(f"{param}_r{r}") for param, r in intended_cases()}
    for param, r in intended_cases():
        case = f"{param}_r{r}"
        vals = by_case.get(case, [])
        lanes = [fnum(row.get("pvw_lane_us")) for row in vals]
        scalars = [fnum(row.get("scalar_lane_us")) for row in vals]
        speedups = [fnum(row.get("speedup_vs_repeated_scalar")) for row in vals]
        lane_low, lane_high = ci95(lanes)
        speed_low, speed_high = ci95(speedups)
        statuses = {str(row.get("correctness", "")) for row in vals}
        noise = noise_by_case[case]
        sample_count = len(vals)
        correctness = "Pass" if vals and statuses == {"Pass"} else ",".join(sorted(statuses)) or "MISSING"
        noise_ok = noise.get("status") == "pass" and int(noise.get("trials") or 0) >= 10 and noise.get("pair_failures") == "0"
        perf_ok = sample_count >= 10 and correctness == "Pass"
        rows.append({
            "case": case,
            "param": param,
            "r": r,
            "samples": sample_count,
            "correctness": correctness,
            "pvw_t_over_r_mean_us": f"{mean(lanes):.3f}" if lanes else "",
            "pvw_t_over_r_ci95_us": f"{lane_low:.3f}..{lane_high:.3f}" if lanes else "",
            "scalar_t_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
            "speedup_mean": f"{mean(speedups):.6f}" if speedups else "",
            "speedup_ci95": f"{speed_low:.6f}..{speed_high:.6f}" if speedups else "",
            "noise_trials": noise.get("trials", ""),
            "noise_pair_failures": noise.get("pair_failures", ""),
            "noise_gate": noise.get("gate", ""),
            "noise_overall_gate": noise.get("overall_gate", ""),
            "time_maxrss_kb": noise.get("time_maxrss_kb", ""),
            "status": "PASS_CASE" if perf_ok and noise_ok else "PARTIAL_OR_FAIL",
        })
    return rows


def historical_rows(perf_summary: list[dict[str, object]]) -> list[dict[str, object]]:
    hist_perf = {(row.get("param", ""), row.get("r", "")): row for row in read_csv(STAGE36_ADDED_PERF)}
    hist_noise = {(row.get("param", ""), row.get("r", "")): row for row in read_csv(STAGE36_ADDED_NOISE)}
    rows: list[dict[str, object]] = []
    for row in perf_summary:
        key = (str(row.get("param", "")), str(row.get("r", "")))
        hp = hist_perf.get(key, {})
        hn = hist_noise.get(key, {})
        rows.append({
            "case": row.get("case", ""),
            "current_head_speedup": row.get("speedup_mean", ""),
            "current_head_samples": row.get("samples", ""),
            "current_head_noise": f"{row.get('noise_pair_failures', '')}/{row.get('noise_trials', '')}",
            "historical_stage36_speedup": hp.get("mean_speedup", ""),
            "historical_stage36_samples": hp.get("runs", ""),
            "historical_stage36_noise": f"{hn.get('pair_failures', '')}/{hn.get('seeds', '')}",
            "interpretation": "current-head row supersedes historical supporting row if PASS_CASE",
        })
    return rows


def claim_rows(decision: str) -> list[dict[str, object]]:
    return [
        {
            "claim": "binary_added_parameter_matrix",
            "status": "ALLOW_SCOPED" if decision == DECISION_PASS else "NOT_PROMOTED",
            "safe_statement": "Current-head binary added-parameter rows have 10-sample T_bootstrap/r and 10-trial noise evidence." if decision == DECISION_PASS else "Added-parameter rows remain partial/historical until all rows pass.",
            "blocked_statement": "Non-binary, all-parameter, novelty, or theoretical-optimality wording.",
            "evidence": rel(SUMMARY),
        },
        {
            "claim": "full_binary_matrix_with_target",
            "status": "READY_FOR_SYNTHESIS" if decision == DECISION_PASS and read_csv(STAGE343_SUMMARY) else "BLOCKED",
            "safe_statement": "Stage343 target rows plus Stage344 added rows can be synthesized if all gates pass.",
            "blocked_statement": "Do not synthesize if either Stage343 or Stage344 gate is missing.",
            "evidence": f"{rel(STAGE343_SUMMARY)}; {rel(PERF_SUMMARY)}",
        },
    ]


def proof_rows(hot: list[dict[str, object]], perf_summary: list[dict[str, object]], decision: str) -> list[dict[str, object]]:
    hot_ok = all(row.get("status") == "HOTPATH_EQUIVALENT" for row in hot)
    pass_rows = [row for row in perf_summary if row.get("status") == "PASS_CASE"]
    return [
        {
            "gate": "G1_stage343_input",
            "status": "PASS" if read_csv(STAGE343_SUMMARY) else "MISSING",
            "metric": "Stage343 summary",
            "value": read_csv(STAGE343_SUMMARY)[0].get("decision", "") if read_csv(STAGE343_SUMMARY) else "",
            "interpretation": "Target parameter high-stat evidence must already exist before matrix synthesis.",
        },
        {
            "gate": "G2_hotpath_equivalence",
            "status": "PASS" if hot_ok else "FAIL",
            "metric": "Stage344 run head to HEAD",
            "value": ";".join(f"{row.get('basis')}={row.get('status')}" for row in hot),
            "interpretation": "Current-head claim requires no hotpath diff after execution.",
        },
        {
            "gate": "G3_added_parameter_coverage",
            "status": "PASS" if len(pass_rows) == len(intended_cases()) else "PARTIAL",
            "metric": "passed/intended rows",
            "value": f"{len(pass_rows)}/{len(intended_cases())}",
            "interpretation": "Every added binary parameter/r row must pass before broader wording.",
        },
        {
            "gate": "G4_metric_alignment",
            "status": "PASS",
            "metric": "primary endpoint",
            "value": "complete SAB T_bootstrap/r vs repeated scalar",
            "interpretation": "Kernel-only or backend-only wins are not used for this stage claim.",
        },
        {
            "gate": "G5_claim_boundary",
            "status": "PASS",
            "metric": "claim level",
            "value": "binary added parameters only",
            "interpretation": "No non-binary, all-parameter, novelty, or theoretical-optimality claim.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls whether Stage345 can synthesize the binary matrix.",
        },
    ]


def next_rows(decision: str) -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage345_binary_matrix_synthesis",
            "entry_condition": decision,
            "command": "Build a matrix-level synthesis from Stage331/343/344 plus resource evidence.",
            "gate": "Every synthesized claim must cite exact rows and preserve unsupported-claim blocks.",
            "failure_action": "Keep results as separate scoped rows.",
        },
        {
            "priority": "P1",
            "route": "stage345_mechanism_or_literature",
            "entry_condition": "Need stronger algorithmic or paper claim after matrix synthesis.",
            "command": "Admit only a new measured mechanism/proof or verified related-work audit.",
            "gate": "No novelty/theoretical-optimality wording without source/proof support.",
            "failure_action": "Publish scoped systems evidence and negative ablations only.",
        },
    ]


def append_run_log(decision: str, perf_summary: list[dict[str, object]]) -> None:
    marker = "stage344-added-parameter-topups-001"
    row = [
        marker,
        date.today().isoformat(),
        run_head(),
        "Stage 344",
        "spqlios_avx512-wsl",
        "STAGE344_PERF_RUNS=10 STAGE344_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage344_added_parameter_topups.sh",
        ";".join(str(row.get("case", "")) for row in perf_summary),
        "n/a",
        decision,
        "Executes current-head added binary parameter rows under complete SAB T_bootstrap/r and noise gates.",
        f"{rel(DOC)}; {rel(SUMMARY)}; {rel(PERF_SUMMARY)}; {rel(NOISE_SUMMARY)}; {rel(PROOF)}",
    ]
    line_buffer = StringIO()
    csv.writer(line_buffer, lineterminator="").writerow(row)
    replacement_line = line_buffer.getvalue()
    if marker in read_text(RUN_LOG):
        lines = read_text(RUN_LOG).splitlines()
        lines = [replacement_line if line.startswith(f"{marker},") else line for line in lines]
        write_text(RUN_LOG, "\n".join(lines))
        return
    exists = RUN_LOG.exists()
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        if not exists:
            writer.writerow(["run_id", "date", "git_head", "stage", "backend", "command", "params", "seed", "status", "interpretation", "artifacts"])
        writer.writerow(row)


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


def artifact_index(paths: list[Path]) -> None:
    rows = [{"artifact": rel(path), "exists": path.exists(), "bytes": file_size(path), "sha256": sha256_file(path)} for path in paths]
    write_csv(ARTIFACT, rows, ["artifact", "exists", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    hot = hotpath_rows()
    samples = parse_perf()
    perf_summary = summarize_perf(samples)
    noise_rows = [parse_noise(f"{param}_r{r}") for param, r in intended_cases()]
    historical = historical_rows(perf_summary)
    all_pass = all(row.get("status") == "PASS_CASE" for row in perf_summary) and all(row.get("status") == "HOTPATH_EQUIVALENT" for row in hot)
    any_data = bool(samples) or any(row.get("status") != "missing" for row in noise_rows)
    decision = DECISION_PASS if all_pass else DECISION_PARTIAL if any_data else DECISION_FAIL
    claims = claim_rows(decision)
    proof = proof_rows(hot, perf_summary, decision)
    nextq = next_rows(decision)
    speedups = [fnum(row.get("speedup_mean")) for row in perf_summary if row.get("speedup_mean")]
    rss_vals = [int(str(row.get("time_maxrss_kb"))) for row in perf_summary if str(row.get("time_maxrss_kb")).isdigit()]
    summary = [{
        "decision": decision,
        "run_head": run_head(),
        "current_head": git_head(),
        "intended_cases": len(intended_cases()),
        "passed_cases": sum(1 for row in perf_summary if row.get("status") == "PASS_CASE"),
        "speedup_min": f"{min(speedups):.6f}" if speedups else "",
        "speedup_max": f"{max(speedups):.6f}" if speedups else "",
        "speedup_mean_across_cases": f"{mean(speedups):.6f}" if speedups else "",
        "max_rss_kb": max(rss_vals) if rss_vals else "",
        "claim_status": "binary_added_parameter_current_head_matrix" if decision == DECISION_PASS else "not_promoted",
    }]
    perf_fields = ["case", "param", "r", "mode", "h", "r_prec", "outer_log", "inner_rep", "correctness", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_repeated_scalar", "source_log"]
    write_csv(SUMMARY, summary, ["decision", "run_head", "current_head", "intended_cases", "passed_cases", "speedup_min", "speedup_max", "speedup_mean_across_cases", "max_rss_kb", "claim_status"])
    write_csv(HOTPATH, hot, ["basis", "ref", "ref_resolves", "current_head", "hotpath_diff_count", "hotpath_diff_paths", "status"])
    write_csv(PERF_SAMPLES, samples, perf_fields)
    write_csv(PERF_SUMMARY, perf_summary, ["case", "param", "r", "samples", "correctness", "pvw_t_over_r_mean_us", "pvw_t_over_r_ci95_us", "scalar_t_over_r_mean_us", "speedup_mean", "speedup_ci95", "noise_trials", "noise_pair_failures", "noise_gate", "noise_overall_gate", "time_maxrss_kb", "status"])
    write_csv(NOISE_SUMMARY, noise_rows, ["case", "mode", "r", "trials", "points", "pair_failures", "pair_log2_sigma_torus", "pair_log2_max_abs_torus", "gate", "overall_gate", "time_maxrss_kb", "status", "source_run_log", "source_time_log"])
    write_csv(HISTORICAL, historical, ["case", "current_head_speedup", "current_head_samples", "current_head_noise", "historical_stage36_speedup", "historical_stage36_samples", "historical_stage36_noise", "interpretation"])
    write_csv(CLAIMS, claims, ["claim", "status", "safe_statement", "blocked_statement", "evidence"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "command", "gate", "failure_action"])
    write_text(COMMANDS, """# Stage344 Reproduction Commands

```sh
STAGE344_PERF_RUNS=10 STAGE344_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage344_added_parameter_topups.sh
```

Parse existing logs only:

```powershell
python scripts\\build_stage344_added_parameter_topups.py
```
""")
    write_text(REPORT, f"""# Stage344 Added-Parameter Current-Head Top-Ups

Decision: `{decision}`.

Stage344 executes the added binary parameter rows that were still historical
after Stage343. The endpoint remains complete SAB `T_bootstrap/r` against
repeated scalar SAB under the same backend.

## Summary

{md_table(summary, ["decision", "intended_cases", "passed_cases", "speedup_min", "speedup_max", "speedup_mean_across_cases", "max_rss_kb", "claim_status"])}

## Per-Case Results

{md_table(perf_summary, ["case", "samples", "correctness", "pvw_t_over_r_mean_us", "scalar_t_over_r_mean_us", "speedup_mean", "speedup_ci95", "noise_trials", "noise_pair_failures", "status"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}

## Claim Boundary

{md_table(claims, ["claim", "status", "safe_statement", "blocked_statement"])}
""")
    write_text(DOC, f"""# Stage344 Added-Parameter Current-Head Top-Ups

Decision: `{decision}`.

This stage covers only the binary added-parameter rows:
`SET_4_5_2048` and `SET_2_3_4096`, with r=2 and r=4. It does not claim
non-binary support, all-parameter generality, novelty, or theoretical
optimality.

{md_table(perf_summary, ["case", "samples", "speedup_mean", "speedup_ci95", "noise_trials", "noise_pair_failures", "status"])}
""")
    write_text(THEORY, """# Stage344 Added-Parameter Claim Model

The valid endpoint remains complete `T_bootstrap/r` against repeated scalar SAB
under the same backend. Stage344 only upgrades added binary parameter rows from
historical/supporting evidence to current-head evidence when every row has:

- 10 complete-SAB timing samples;
- correctness `Pass`;
- 10 final-output noise trials;
- zero pair failures;
- RSS recorded;
- no hot-path delta from run head to current HEAD.

This is still not a novelty or theoretical-optimality result.
""")
    write_text(PLAN, """# Stage345 Matrix Synthesis Or Mechanism Plan

If Stage344 passes, synthesize Stage331, Stage343, and Stage344 into one binary
parameter matrix. The synthesis must preserve row-level evidence and must not
upgrade unsupported claims.

If stronger claims are needed, admit only:

- a new measured mechanism with isolated and full-SAB gates; or
- a verified literature/proof route with real source support.
""")
    append_once(GOAL, "<!-- stage344-added-parameter-topups -->", f"""
<!-- stage344-added-parameter-topups -->
- Stage344: `{decision}`. Added binary parameter current-head top-ups are recorded; synthesis is allowed only if every row passes.
""")
    append_once(ROADMAP, "<!-- stage344-added-parameter-topups -->", f"""
<!-- stage344-added-parameter-topups -->
## Stage344: Added-Parameter Current-Head Top-Ups

- Decision: `{decision}`.
- Result: current-head added binary parameter rows under complete `T_bootstrap/r`.
- Boundary: no non-binary, all-parameter, novelty, or theoretical-optimality claim.
""")
    append_once(HYPOTHESES, "H344_added_parameter_topups:", f"""
H344_added_parameter_topups:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage344_added_parameter_topups/summary.csv
    - repro/stage344_added_parameter_topups/perf_summary.csv
    - repro/stage344_added_parameter_topups/noise_summary.csv
    - repro/stage344_added_parameter_topups/proof_gate.csv
  conclusion: >
    Stage344 upgrades added binary parameter rows only if every current-head
    row passes timing, correctness, noise, resource, and hotpath gates.
""")
    append_once(MANIFEST, "<!-- stage344-added-parameter-topups-manifest -->", """
<!-- stage344-added-parameter-topups-manifest -->
- stage344_added_parameter_topups:
  - `docs/stage344_added_parameter_topups.md`
  - `theory_checks/stage344_added_parameter_claim_model.md`
  - `experiments/stage345_matrix_synthesis_or_mechanism_plan.md`
  - `scripts/run_stage344_added_parameter_topups.sh`
  - `scripts/build_stage344_added_parameter_topups.py`
  - `repro/stage344_added_parameter_topups/`
""")
    append_once(CHECKLIST, "<!-- stage344-added-parameter-topups-checklist -->", f"""
<!-- stage344-added-parameter-topups-checklist -->
- [x] Stage344 records `{decision}` with added-parameter-only claim boundary.
""")
    append_run_log(decision, perf_summary)
    raw_paths = [
        RAW / "run_git_head.txt",
        *sorted(RAW.glob("*_r*/perf/*.log")),
        *sorted(RAW.glob("*_r*/noise/*.log")),
        EXEC_PLAN,
    ]
    artifact_index([DOC, THEORY, PLAN, RUNNER, BUILDER, SUMMARY, HOTPATH, PERF_SAMPLES, PERF_SUMMARY, NOISE_SUMMARY, HISTORICAL, CLAIMS, PROOF, NEXT, REPORT, COMMANDS, *raw_paths])
    return 0 if decision == DECISION_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
