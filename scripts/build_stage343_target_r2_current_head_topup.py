#!/usr/bin/env python3
"""Stage343: combine Stage341 r=2 smoke with current-head top-up samples."""

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
OUT = Path(os.environ.get("STAGE343_OUT_DIR", ROOT / "repro" / "stage343_target_r2_current_head_topup"))
if not OUT.is_absolute():
    OUT = ROOT / OUT
RAW = OUT / "raw"

DOC = ROOT / "docs" / "stage343_target_r2_current_head_topup.md"
THEORY = ROOT / "theory_checks" / "stage343_r2_topup_claim_model.md"
PLAN = ROOT / "experiments" / "stage344_added_parameter_topup_plan.md"
RUNNER = ROOT / "scripts" / "run_stage343_target_r2_current_head_topup.sh"
BUILDER = ROOT / "scripts" / "build_stage343_target_r2_current_head_topup.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE341_SUMMARY = ROOT / "repro" / "stage341_parameter_matrix_smoke" / "summary.csv"
STAGE341_PERF = ROOT / "repro" / "stage341_parameter_matrix_smoke" / "perf_samples.csv"
STAGE341_NOISE = ROOT / "repro" / "stage341_parameter_matrix_smoke" / "noise_summary.csv"
STAGE342_SUMMARY = ROOT / "repro" / "stage342_continuity_audit" / "summary.csv"

SUMMARY = OUT / "summary.csv"
HOTPATH = OUT / "hotpath_equivalence.csv"
TOPUP_PERF = OUT / "topup_perf_samples.csv"
COMBINED_PERF = OUT / "combined_perf_samples.csv"
PERF_SUMMARY = OUT / "combined_perf_summary.csv"
TOPUP_NOISE = OUT / "topup_noise_summary.csv"
NOISE_SUMMARY = OUT / "combined_noise_summary.csv"
CLAIMS = OUT / "claim_update.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
REPORT = OUT / "stage343_report.md"
COMMANDS = OUT / "reproduction_commands.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION_PASS = "PASS_STAGE343_TARGET_R2_CURRENT_HEAD_HIGHSTAT_TOPUP"
DECISION_PARTIAL = "PARTIAL_STAGE343_TARGET_R2_CURRENT_HEAD_TOPUP"
DECISION_FAIL = "FAIL_STAGE343_TARGET_R2_CURRENT_HEAD_TOPUP"

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


def hotpath_rows() -> list[dict[str, object]]:
    stage341 = read_csv(STAGE341_SUMMARY)
    stage341_head = stage341[0].get("run_head", "") if stage341 else ""
    topup_head = run_head()
    rows = []
    for label, ref in [("stage341_smoke_to_head", stage341_head), ("stage343_topup_to_head", topup_head)]:
        diffs = git_diff_names(ref)
        resolves = "yes" if git_full(ref) else "no"
        rows.append({
            "basis": label,
            "ref": ref,
            "ref_resolves": resolves,
            "current_head": git_head(),
            "hotpath_diff_count": len(diffs) if resolves == "yes" else "",
            "hotpath_diff_paths": ";".join(diffs[:20]) if resolves == "yes" else "",
            "status": "HOTPATH_EQUIVALENT" if resolves == "yes" and not diffs else "HOTPATH_CHANGED_OR_UNRESOLVED",
        })
    return rows


def parse_topup_perf() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(RAW.glob("*_r*/perf/run_*.log")):
        case = path.parts[-3]
        text = read_text(path)
        correct = CORRECT_RE.search(text)
        correctness = correct.group("status") if correct else "MISSING"
        for sample in SAMPLE_RE.finditer(text):
            rows.append({
                "sample_source": "stage343_topup",
                "case": case,
                "mode": sample.group("mode"),
                "r": sample.group("r"),
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


def previous_perf_rows(hot_ok: bool) -> list[dict[str, object]]:
    if not hot_ok:
        return []
    rows = []
    for row in read_csv(STAGE341_PERF):
        rows.append({
            "sample_source": "stage341_smoke_hotpath_equivalent",
            "case": row.get("case", ""),
            "mode": row.get("mode", ""),
            "r": row.get("r", ""),
            "h": row.get("h", ""),
            "r_prec": row.get("r_prec", ""),
            "outer_log": row.get("outer_log", ""),
            "inner_rep": row.get("inner_rep", ""),
            "correctness": row.get("correctness", ""),
            "pvw_us": row.get("pvw_us", ""),
            "pvw_lane_us": row.get("pvw_lane_us", ""),
            "scalar_repeated_us": row.get("scalar_repeated_us", ""),
            "scalar_lane_us": row.get("scalar_lane_us", ""),
            "speedup_vs_repeated_scalar": row.get("speedup_vs_repeated_scalar", ""),
            "source_log": row.get("source_log", ""),
        })
    return rows


def summarize_perf(rows: list[dict[str, object]]) -> dict[str, object]:
    lanes = [fnum(row.get("pvw_lane_us")) for row in rows]
    scalars = [fnum(row.get("scalar_lane_us")) for row in rows]
    speedups = [fnum(row.get("speedup_vs_repeated_scalar")) for row in rows]
    lane_low, lane_high = ci95(lanes)
    speed_low, speed_high = ci95(speedups)
    statuses = {str(row.get("correctness", "")) for row in rows}
    return {
        "case": rows[0].get("case", "") if rows else "",
        "samples": len(rows),
        "stage341_samples_included": sum(1 for row in rows if str(row.get("sample_source", "")).startswith("stage341")),
        "stage343_samples_included": sum(1 for row in rows if row.get("sample_source") == "stage343_topup"),
        "correctness": "Pass" if rows and statuses == {"Pass"} else ",".join(sorted(statuses)) or "MISSING",
        "pvw_t_over_r_mean_us": f"{mean(lanes):.3f}" if lanes else "",
        "pvw_t_over_r_ci95_us": f"{lane_low:.3f}..{lane_high:.3f}" if lanes else "",
        "scalar_t_over_r_mean_us": f"{mean(scalars):.3f}" if scalars else "",
        "speedup_mean": f"{mean(speedups):.6f}" if speedups else "",
        "speedup_ci95": f"{speed_low:.6f}..{speed_high:.6f}" if speedups else "",
    }


def parse_topup_noise() -> dict[str, object]:
    run_logs = sorted(RAW.glob("*_r*/noise/run.log"))
    if not run_logs:
        return {"status": "missing", "trials": "0", "pair_failures": ""}
    run_log = run_logs[0]
    time_log = run_log.parent / "time.log"
    row: dict[str, object] = {"status": "fail", "source_run_log": rel(run_log), "source_time_log": rel(time_log)}
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
    return row


def combined_noise(topup: dict[str, object], include_stage341: bool) -> dict[str, object]:
    prev = read_csv(STAGE341_NOISE)[0] if include_stage341 and read_csv(STAGE341_NOISE) else {}
    prev_trials = int(prev.get("trials") or 0)
    prev_fail = int(prev.get("pair_failures") or 0)
    top_trials = int(topup.get("trials") or 0)
    top_fail = int(topup.get("pair_failures") or 0)
    rss_vals = [int(x) for x in [prev.get("time_maxrss_kb", ""), topup.get("time_maxrss_kb", "")] if str(x).isdigit()]
    return {
        "stage341_trials_included": prev_trials,
        "stage343_trials_included": top_trials,
        "total_trials": prev_trials + top_trials,
        "pair_failures": prev_fail + top_fail,
        "topup_gate": topup.get("gate", ""),
        "topup_overall_gate": topup.get("overall_gate", ""),
        "time_maxrss_kb_max": max(rss_vals) if rss_vals else "",
        "status": "pass" if prev_fail + top_fail == 0 and prev_trials + top_trials >= 10 and topup.get("status") == "pass" else "partial_or_fail",
    }


def claim_rows(decision: str) -> list[dict[str, object]]:
    return [
        {
            "claim": "current_head_target_r2_highstat",
            "status": "ALLOW_SCOPED" if decision == DECISION_PASS else "NOT_PROMOTED",
            "safe_statement": "SET_2_3_2048 r=2 current-head complete-SAB T_bootstrap/r high-stat top-up is available." if decision == DECISION_PASS else "r=2 remains partial/smoke until 10 samples and 10 noise trials pass.",
            "blocked_statement": "Broader added-parameter, non-binary, novelty, or theoretical-optimality wording.",
            "evidence": rel(SUMMARY),
        },
        {
            "claim": "full_parameter_matrix",
            "status": "STILL_BLOCKED",
            "safe_statement": "Target r=2 can be promoted only inside the scoped target parameter if Stage343 passes.",
            "blocked_statement": "SET_4_5_2048 and SET_2_3_4096 still need current-head topups.",
            "evidence": rel(NEXT),
        },
    ]


def proof_rows(hot: list[dict[str, object]], perf: dict[str, object], noise: dict[str, object], decision: str) -> list[dict[str, object]]:
    hot_ok = all(row.get("status") == "HOTPATH_EQUIVALENT" for row in hot)
    perf_ok = perf.get("samples") == 10 and perf.get("correctness") == "Pass"
    noise_ok = noise.get("status") == "pass"
    return [
        {
            "gate": "G1_stage342_route",
            "status": "PASS" if read_csv(STAGE342_SUMMARY) else "MISSING",
            "metric": "Stage342 decision",
            "value": read_csv(STAGE342_SUMMARY)[0].get("decision", "") if read_csv(STAGE342_SUMMARY) else "",
            "interpretation": "Stage343 follows the r=2 current-head top-up route.",
        },
        {
            "gate": "G2_hotpath_equivalence",
            "status": "PASS" if hot_ok else "FAIL",
            "metric": "Stage341/Stage343 run heads to HEAD",
            "value": ";".join(f"{row.get('basis')}={row.get('status')}" for row in hot),
            "interpretation": "Stage341 smoke can be combined only when hotpath-equivalent.",
        },
        {
            "gate": "G3_perf_highstat",
            "status": "PASS" if perf_ok else "PARTIAL",
            "metric": "samples/correctness",
            "value": f"{perf.get('samples', '')}/{perf.get('correctness', '')}",
            "interpretation": "Requires 10 complete-SAB samples with correctness Pass.",
        },
        {
            "gate": "G4_noise_resource",
            "status": "PASS" if noise_ok else "PARTIAL_OR_FAIL",
            "metric": "pair failures/trials",
            "value": f"{noise.get('pair_failures', '')}/{noise.get('total_trials', '')}",
            "interpretation": "Requires zero pair failures over 10 combined trials and RSS recorded.",
        },
        {
            "gate": "G5_claim_boundary",
            "status": "PASS",
            "metric": "claim level",
            "value": "target_r2_only",
            "interpretation": "Do not promote added parameters, novelty, or theoretical optimality.",
        },
        {
            "gate": "G6_decision",
            "status": decision,
            "metric": "stage decision",
            "value": decision,
            "interpretation": "Controls whether r=2 moves from smoke-only to scoped current-head high-stat.",
        },
    ]


def next_rows() -> list[dict[str, object]]:
    return [
        {
            "priority": "P0",
            "route": "stage344_added_parameter_current_head_topups",
            "entry_condition": "Need broader binary parameter wording beyond SET_2_3_2048.",
            "command": "Run current-head topups for SET_4_5_2048 and SET_2_3_4096, r=2/4.",
            "gate": "10 samples and 10 noise trials per claimed case, same backend, T_bootstrap/r.",
            "failure_action": "Keep added-parameter rows historical/supporting only.",
        },
        {
            "priority": "P1",
            "route": "stage344_mechanism_or_source_verified_paper_route",
            "entry_condition": "No further matrix execution or a stronger algorithmic claim is needed.",
            "command": "Admit only a new measured mechanism/proof or verified literature audit.",
            "gate": "No novelty/theoretical-optimality wording without source/proof support.",
            "failure_action": "Publish scoped systems result and negative ablations only.",
        },
    ]


def append_run_log(decision: str, perf: dict[str, object], noise: dict[str, object]) -> None:
    marker = "stage343-target-r2-topup-001"
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
            run_head(),
            "Stage 343",
            "spqlios_avx512-wsl",
            "STAGE343_PERF_RUNS=9 STAGE343_NOISE_TRIALS=9 FFT_LIB=spqlios_avx512 bash scripts/run_stage343_target_r2_current_head_topup.sh",
            f"SET_2_3_2048_r2; combined_samples={perf.get('samples', '')}; combined_noise_trials={noise.get('total_trials', '')}",
            "n/a",
            decision,
            "Top-up Stage341 r=2 smoke to a scoped current-head high-stat target r=2 result if gates pass.",
            f"{rel(DOC)}; {rel(SUMMARY)}; {rel(PERF_SUMMARY)}; {rel(NOISE_SUMMARY)}; {rel(PROOF)}",
        ])


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
    hot_ok = all(row.get("status") == "HOTPATH_EQUIVALENT" for row in hot)
    topup_perf = parse_topup_perf()
    combined_perf = [*previous_perf_rows(hot_ok), *topup_perf]
    perf = summarize_perf(combined_perf)
    topup_noise = parse_topup_noise()
    noise = combined_noise(topup_noise, hot_ok)
    perf_ok = perf.get("samples") == 10 and perf.get("correctness") == "Pass"
    noise_ok = noise.get("status") == "pass"
    if hot_ok and perf_ok and noise_ok:
        decision = DECISION_PASS
    elif combined_perf or int(noise.get("total_trials") or 0) > 0:
        decision = DECISION_PARTIAL
    else:
        decision = DECISION_FAIL
    claims = claim_rows(decision)
    proof = proof_rows(hot, perf, noise, decision)
    nextq = next_rows()
    summary = [{
        "decision": decision,
        "run_head": run_head(),
        "current_head": git_head(),
        "case": perf.get("case", "SET_2_3_2048_r2"),
        "samples": perf.get("samples", ""),
        "correctness": perf.get("correctness", ""),
        "pvw_t_over_r_mean_us": perf.get("pvw_t_over_r_mean_us", ""),
        "pvw_t_over_r_ci95_us": perf.get("pvw_t_over_r_ci95_us", ""),
        "scalar_t_over_r_mean_us": perf.get("scalar_t_over_r_mean_us", ""),
        "speedup_mean": perf.get("speedup_mean", ""),
        "speedup_ci95": perf.get("speedup_ci95", ""),
        "noise_trials": noise.get("total_trials", ""),
        "noise_pair_failures": noise.get("pair_failures", ""),
        "time_maxrss_kb_max": noise.get("time_maxrss_kb_max", ""),
        "claim_status": "target_r2_scoped_highstat" if decision == DECISION_PASS else "not_promoted",
    }]
    fields = ["sample_source", "case", "mode", "r", "h", "r_prec", "outer_log", "inner_rep", "correctness", "pvw_us", "pvw_lane_us", "scalar_repeated_us", "scalar_lane_us", "speedup_vs_repeated_scalar", "source_log"]
    write_csv(SUMMARY, summary, ["decision", "run_head", "current_head", "case", "samples", "correctness", "pvw_t_over_r_mean_us", "pvw_t_over_r_ci95_us", "scalar_t_over_r_mean_us", "speedup_mean", "speedup_ci95", "noise_trials", "noise_pair_failures", "time_maxrss_kb_max", "claim_status"])
    write_csv(HOTPATH, hot, ["basis", "ref", "ref_resolves", "current_head", "hotpath_diff_count", "hotpath_diff_paths", "status"])
    write_csv(TOPUP_PERF, topup_perf, fields)
    write_csv(COMBINED_PERF, combined_perf, fields)
    write_csv(PERF_SUMMARY, [perf], ["case", "samples", "stage341_samples_included", "stage343_samples_included", "correctness", "pvw_t_over_r_mean_us", "pvw_t_over_r_ci95_us", "scalar_t_over_r_mean_us", "speedup_mean", "speedup_ci95"])
    write_csv(TOPUP_NOISE, [topup_noise], ["status", "mode", "r", "trials", "points", "pair_failures", "pair_log2_sigma_torus", "pair_log2_max_abs_torus", "gate", "overall_gate", "time_maxrss_kb", "source_run_log", "source_time_log"])
    write_csv(NOISE_SUMMARY, [noise], ["stage341_trials_included", "stage343_trials_included", "total_trials", "pair_failures", "topup_gate", "topup_overall_gate", "time_maxrss_kb_max", "status"])
    write_csv(CLAIMS, claims, ["claim", "status", "safe_statement", "blocked_statement", "evidence"])
    write_csv(PROOF, proof, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, nextq, ["priority", "route", "entry_condition", "command", "gate", "failure_action"])
    write_text(COMMANDS, """# Stage343 Reproduction Commands

```sh
STAGE343_PERF_RUNS=9 STAGE343_NOISE_TRIALS=9 FFT_LIB=spqlios_avx512 bash scripts/run_stage343_target_r2_current_head_topup.sh
```

Parse existing logs only:

```powershell
python scripts\\build_stage343_target_r2_current_head_topup.py
```
""")
    write_text(REPORT, f"""# Stage343 Target r=2 Current-Head Top-Up

Decision: `{decision}`.

Stage343 tests the next executable gap from Stage342: promote
`SET_2_3_2048 r=2` from smoke-only to a scoped current-head high-stat row by
combining the hotpath-equivalent Stage341 sample with nine new top-up samples.

## Summary

{md_table(summary, ["decision", "case", "samples", "correctness", "pvw_t_over_r_mean_us", "scalar_t_over_r_mean_us", "speedup_mean", "speedup_ci95", "noise_trials", "noise_pair_failures", "claim_status"])}

## Proof Gate

{md_table(proof, ["gate", "status", "metric", "value"])}

## Claim Boundary

{md_table(claims, ["claim", "status", "safe_statement", "blocked_statement"])}
""")
    write_text(DOC, f"""# Stage343 Target r=2 Current-Head Top-Up

Decision: `{decision}`.

This stage is a strict top-up of the target `SET_2_3_2048 r=2` row. It does not
claim added-parameter generality, non-binary support, novelty, or theoretical
optimality.

{md_table(summary, ["case", "samples", "correctness", "speedup_mean", "speedup_ci95", "noise_trials", "noise_pair_failures", "claim_status"])}
""")
    write_text(THEORY, """# Stage343 r=2 Top-Up Claim Model

The valid metric is complete `T_bootstrap/r` against repeated scalar SAB under
the same backend. Stage343 only changes the evidence level for one target row:
`SET_2_3_2048 r=2`.

The Stage341 sample is admissible only because the hotpath audit checks
`src/`, `Makefile`, and `include/` from the Stage341 run head to current HEAD.
If that check fails, the sample is excluded and the result cannot pass the
10-sample high-stat gate.
""")
    write_text(PLAN, """# Stage344 Added-Parameter Top-Up Plan

Only start this route if broader binary-parameter wording is required.

Required cases:

- `SET_4_5_2048 r=2`
- `SET_4_5_2048 r=4`
- `SET_2_3_4096 r=2`
- `SET_2_3_4096 r=4`

Each claimed row needs 10 complete-SAB `T_bootstrap/r` samples, 10 noise trials,
zero pair failures, RSS reporting, and hotpath-equivalent run heads.
""")
    append_once(GOAL, "<!-- stage343-target-r2-topup -->", f"""
<!-- stage343-target-r2-topup -->
- Stage343: `{decision}`. Target r=2 current-head top-up is recorded; only the target-row claim may be promoted if gates pass.
""")
    append_once(ROADMAP, "<!-- stage343-target-r2-topup -->", f"""
<!-- stage343-target-r2-topup -->
## Stage343: Target r=2 Current-Head Top-Up

- Decision: `{decision}`.
- Result: target `SET_2_3_2048 r=2` high-stat top-up route.
- Boundary: no added-parameter, novelty, or theoretical-optimality claim.
""")
    append_once(HYPOTHESES, "H343_target_r2_topup:", f"""
H343_target_r2_topup:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/stage343_target_r2_current_head_topup/summary.csv
    - repro/stage343_target_r2_current_head_topup/combined_perf_summary.csv
    - repro/stage343_target_r2_current_head_topup/combined_noise_summary.csv
    - repro/stage343_target_r2_current_head_topup/proof_gate.csv
  conclusion: >
    Stage343 top-ups the target r=2 row only. It does not alter claims about
    added parameters, non-binary branches, novelty, or theoretical optimality.
""")
    append_once(MANIFEST, "<!-- stage343-target-r2-topup-manifest -->", """
<!-- stage343-target-r2-topup-manifest -->
- stage343_target_r2_current_head_topup:
  - `docs/stage343_target_r2_current_head_topup.md`
  - `theory_checks/stage343_r2_topup_claim_model.md`
  - `experiments/stage344_added_parameter_topup_plan.md`
  - `scripts/run_stage343_target_r2_current_head_topup.sh`
  - `scripts/build_stage343_target_r2_current_head_topup.py`
  - `repro/stage343_target_r2_current_head_topup/`
""")
    append_once(CHECKLIST, "<!-- stage343-target-r2-topup-checklist -->", f"""
<!-- stage343-target-r2-topup-checklist -->
- [x] Stage343 records `{decision}` with target r=2 only claim boundary.
""")
    append_run_log(decision, perf, noise)
    raw_paths = [
        RAW / "run_git_head.txt",
        *sorted(RAW.glob("*_r*/perf/*.log")),
        *sorted(RAW.glob("*_r*/noise/*.log")),
        OUT / "execution_plan.csv",
    ]
    artifact_index([DOC, THEORY, PLAN, RUNNER, BUILDER, SUMMARY, HOTPATH, TOPUP_PERF, COMBINED_PERF, PERF_SUMMARY, TOPUP_NOISE, NOISE_SUMMARY, CLAIMS, PROOF, NEXT, REPORT, COMMANDS, *raw_paths])
    return 0 if decision == DECISION_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
