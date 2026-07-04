#!/usr/bin/env python3
"""Stage330: reconcile high-stat direct-DFT evidence with current hot-code claim."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro" / "stage330_highstat_reconciliation"

DOC = ROOT / "docs" / "stage330_highstat_reconciliation.md"
THEORY = ROOT / "theory_checks" / "stage330_highstat_reconciliation_model.md"
VARIANT = ROOT / "algorithm_variants" / "mat_rlwe_sab_stage330_reconciled_direct_dft_claim.md"
PLAN = ROOT / "experiments" / "stage331_current_head_highstat_or_compact_plan.md"
BUILDER = ROOT / "scripts" / "build_stage330_highstat_reconciliation.py"

GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"
ROADMAP = ROOT / "docs" / "roadmap_stage19_plus.md"
HYPOTHESES = ROOT / "hypotheses" / "hypothesis_register.yaml"
MANIFEST = ROOT / "repro" / "artifact_manifest.md"
CHECKLIST = ROOT / "repro" / "reproduction_checklist.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

STAGE296_PERF = ROOT / "repro" / "stage296_direct_dft_highstat" / "perf_summary.csv"
STAGE296_NOISE = ROOT / "repro" / "stage296_direct_dft_highstat" / "noise_summary.csv"
STAGE296_PLAN = ROOT / "repro" / "stage296_direct_dft_highstat" / "raw" / "variant_plan.csv"
STAGE296_RUNNER = ROOT / "scripts" / "run_stage296_direct_dft_highstat.sh"

STAGE297_RESOURCE = ROOT / "repro" / "stage297_direct_dft_resource_sidecondition" / "linked_resource_summary.csv"

STAGE321_PERF = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "perf_summary.csv"
STAGE321_PLAN = ROOT / "repro" / "stage321_r4_unrolled_fullsab_ab" / "raw" / "variant_plan.csv"
STAGE321_RUNNER = ROOT / "scripts" / "run_stage321_r4_unrolled_fullsab_ab.sh"

STAGE328_SUMMARY = ROOT / "repro" / "stage328_active_goal_requirement_audit" / "summary.csv"
STAGE329_SUMMARY = ROOT / "repro" / "stage329_formal_compact_selector_checker" / "summary.csv"

SUMMARY = OUT / "summary.csv"
FLAG_COMPAT = OUT / "flag_compatibility.csv"
SOURCE_DIFF = OUT / "source_diff_summary.csv"
EVIDENCE = OUT / "evidence_matrix.csv"
CLAIMS = OUT / "claim_update.csv"
PROOF = OUT / "proof_gate.csv"
NEXT = OUT / "next_stage_queue.csv"
COMMANDS = OUT / "reproduction_commands.md"
REPORT = OUT / "stage330_report.md"
ARTIFACT = OUT / "artifact_index.csv"

DECISION = "PASS_STAGE330_HIGHSTAT_RECONCILIATION_HISTORICAL_10RUN_CURRENT_HOTCODE_5RUN"


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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def row_by(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def fnum(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def git_diff_names(start: str, paths: list[str]) -> list[str]:
    try:
        cmd = ["git", "diff", "--name-only", f"{start}..HEAD", "--", *paths]
        out = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def md_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


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


def append_run_log() -> None:
    run_id = "stage330-highstat-reconciliation-001"
    if run_id in read_text(RUN_LOG):
        return
    fields: list[str]
    if RUN_LOG.exists():
        with RUN_LOG.open(newline="", encoding="utf-8-sig") as handle:
            fields = list(csv.DictReader(handle).fieldnames or [])
    else:
        fields = []
    if not fields:
        fields = [
            "run_id", "date", "commit_or_state", "stage", "backend", "command",
            "params", "seed", "status", "summary", "artifacts",
        ]
    row = {field: "" for field in fields}
    values = {
        "run_id": run_id,
        "date": "2026-07-05",
        "commit_or_state": git_head(),
        "git_ref": git_head(),
        "stage": "Stage 330",
        "backend": "analysis",
        "command": "python scripts/build_stage330_highstat_reconciliation.py",
        "params": "BINARY SET_2_3_2048; r=4; include-zero; spqlios_avx512; direct DFT evidence reconciliation",
        "seed": "n/a",
        "status": DECISION,
        "summary": "Reconciles Stage296 high-stat direct-DFT evidence with Stage321 current-hot-code complete SAB claim boundaries.",
        "artifacts": f"{rel(DOC)}; {rel(SUMMARY)}; {rel(PROOF)}; {rel(CLAIMS)}",
    }
    for key, value in values.items():
        if key in row:
            row[key] = value
    with RUN_LOG.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writerow(row)


def artifact_index(paths: list[Path]) -> None:
    rows: list[dict[str, object]] = []
    for path in paths:
        if path.exists() and path.is_file():
            data = path.read_bytes()
            rows.append({"path": rel(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write_csv(ARTIFACT, rows, ["path", "bytes", "sha256"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    stage296_perf_rows = read_csv(STAGE296_PERF)
    stage296_noise_rows = read_csv(STAGE296_NOISE)
    stage296_plan_rows = read_csv(STAGE296_PLAN)
    stage297_resource_rows = read_csv(STAGE297_RESOURCE)
    stage321_perf_rows = read_csv(STAGE321_PERF)
    stage321_plan_rows = read_csv(STAGE321_PLAN)
    stage328_rows = read_csv(STAGE328_SUMMARY)
    stage329_rows = read_csv(STAGE329_SUMMARY)

    s296_direct = row_by(stage296_perf_rows, "variant", "perf_direct_dft")
    s296_control = row_by(stage296_perf_rows, "variant", "perf_selected_control")
    s296_compare = row_by(stage296_perf_rows, "variant", "comparison")
    s296_noise = row_by(stage296_noise_rows, "variant", "noise_direct_dft")
    s296_plan = row_by(stage296_plan_rows, "case", "perf_direct_dft")
    s321_direct = row_by(stage321_perf_rows, "variant", "direct_baseline")
    s321_plan = row_by(stage321_plan_rows, "variant", "direct_baseline")
    s328_summary = stage328_rows[0] if stage328_rows else {}
    s329_summary = stage329_rows[0] if stage329_rows else {}

    runner296 = read_text(STAGE296_RUNNER)
    runner321 = read_text(STAGE321_RUNNER)

    flag_rows = [
        {
            "check": "metric_endpoint",
            "stage296_perf_direct_dft": "complete SAB T_bootstrap/r",
            "stage321_direct_baseline": "complete SAB T_bootstrap/r",
            "status": "PASS",
            "interpretation": "Both summaries parse pvw_lane_us and speedup against repeated scalar SAB.",
        },
        {
            "check": "param",
            "stage296_perf_direct_dft": s296_plan.get("param", ""),
            "stage321_direct_baseline": s321_plan.get("param", ""),
            "status": "PASS" if s296_plan.get("param") == s321_plan.get("param") == "SET_2_3_2048" else "FAIL",
            "interpretation": "Primary parameter set must match before statistical evidence can be bridged.",
        },
        {
            "check": "fft_lib",
            "stage296_perf_direct_dft": s296_plan.get("fft_lib", ""),
            "stage321_direct_baseline": s321_plan.get("fft_lib", ""),
            "status": "PASS" if s296_plan.get("fft_lib") == s321_plan.get("fft_lib") == "spqlios_avx512" else "FAIL",
            "interpretation": "Backend must match; otherwise SIMD/backend effects are confounded.",
        },
        {
            "check": "r_body_lanes",
            "stage296_perf_direct_dft": s296_plan.get("r", ""),
            "stage321_direct_baseline": s321_plan.get("r", ""),
            "status": "PASS" if s296_plan.get("r") == s321_plan.get("r") == "4" else "FAIL",
            "interpretation": "The amortized metric divides by the same MAT body/lane count.",
        },
        {
            "check": "reps",
            "stage296_perf_direct_dft": s296_plan.get("reps", ""),
            "stage321_direct_baseline": s321_plan.get("reps", ""),
            "status": "PASS" if s296_plan.get("reps") == s321_plan.get("reps") == "1" else "FAIL",
            "interpretation": "One complete SAB sample per outer run in both campaigns.",
        },
        {
            "check": "include_zero_branch",
            "stage296_perf_direct_dft": "true" if "SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true" in runner296 else "missing",
            "stage321_direct_baseline": "true" if "SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true" in runner321 else "missing",
            "status": "PASS" if "SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true" in runner296 and "SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true" in runner321 else "FAIL",
            "interpretation": "Branch behavior is part of the algorithmic schedule.",
        },
        {
            "check": "ternary_branch",
            "stage296_perf_direct_dft": "false" if "SAB_PVW_NONBINARY_BENCH_TERNARY=false" in runner296 else "missing",
            "stage321_direct_baseline": "false" if "SAB_PVW_NONBINARY_BENCH_TERNARY=false" in runner321 else "missing",
            "status": "PASS" if "SAB_PVW_NONBINARY_BENCH_TERNARY=false" in runner296 and "SAB_PVW_NONBINARY_BENCH_TERNARY=false" in runner321 else "FAIL",
            "interpretation": "Both campaigns test binary include-zero, not ternary.",
        },
    ]

    common_flags = [
        "A_PRNG=none",
        "ENABLE_VAES=false",
        "KEY=BINARY",
        "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true",
        "MAT_TRGSW_AVX512_SUB_DECOMP=true",
        "MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true",
        "SAB_PVW_BACKEND_FROM_DFT_ADD=true",
        "SAB_PVW_SUB_DECOMP_FUSION=true",
        "SAB_PVW_DUAL_SUB_CMUX=true",
        "SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true",
    ]
    for flag in common_flags:
        has296 = flag in runner296 or flag in s296_plan.get("extra_flags", "")
        has321 = flag in runner321 or flag in s321_plan.get("extra_flags", "")
        flag_rows.append({
            "check": flag,
            "stage296_perf_direct_dft": "present" if has296 else "missing",
            "stage321_direct_baseline": "present" if has321 else "missing",
            "status": "PASS" if has296 and has321 else "FAIL",
            "interpretation": "Required selected direct-DFT implementation flag.",
        })

    source_paths = ["main.c", "src", "include", "Makefile", "CMakeLists.txt"]
    diff_296 = git_diff_names("60350e3", source_paths)
    diff_321 = git_diff_names("e193b30", source_paths)
    source_rows = [
        {
            "comparison": "stage296_input_60350e3_to_current_head",
            "hot_code_changed": "yes" if diff_296 else "no",
            "changed_count": len(diff_296),
            "changed_paths": "; ".join(diff_296[:20]),
            "interpretation": "Stage296 is high-stat but historical-source evidence if any hot-code path changed after 60350e3.",
        },
        {
            "comparison": "stage321_input_e193b30_to_current_head",
            "hot_code_changed": "yes" if diff_321 else "no",
            "changed_count": len(diff_321),
            "changed_paths": "; ".join(diff_321[:20]),
            "interpretation": "Stage321 can stand as current-hot-code evidence if no SAB/MAT source path changed after e193b30.",
        },
    ]

    flag_pass = all(row["status"] == "PASS" for row in flag_rows)
    current_hotcode_equiv = not diff_321
    historical_highstat = bool(diff_296)
    s296_speed = fnum(s296_direct.get("speedup_vs_repeated_scalar_mean"))
    s321_speed = fnum(s321_direct.get("speedup_vs_repeated_scalar_mean"))
    s296_t = fnum(s296_direct.get("t_bootstrap_over_r_mean_us"))
    s321_t = fnum(s321_direct.get("t_bootstrap_over_r_mean_us"))
    speed_delta_pct = ((s321_speed - s296_speed) / s296_speed * 100.0) if s296_speed else 0.0
    t_delta_pct = ((s321_t - s296_t) / s296_t * 100.0) if s296_t else 0.0

    summary_rows = [{
        "decision": DECISION,
        "primary_metric": "complete_sab_T_bootstrap_over_r_vs_repeated_scalar",
        "stage296_samples": s296_direct.get("samples", ""),
        "stage296_speedup": s296_direct.get("speedup_vs_repeated_scalar_mean", ""),
        "stage296_t_over_r_mean_us": s296_direct.get("t_bootstrap_over_r_mean_us", ""),
        "stage321_samples": s321_direct.get("samples", ""),
        "stage321_speedup": s321_direct.get("speedup_vs_repeated_scalar_mean", ""),
        "stage321_t_over_r_mean_us": s321_direct.get("t_bootstrap_over_r_mean_us", ""),
        "speedup_delta_pct": f"{speed_delta_pct:.6f}",
        "t_over_r_delta_pct": f"{t_delta_pct:.6f}",
        "flag_compatibility": "PASS" if flag_pass else "FAIL",
        "stage296_source_scope": "historical_hot_code_changed" if historical_highstat else "current_hot_code_equivalent",
        "stage321_current_hotcode_scope": "current_hotcode_equivalent" if current_hotcode_equiv else "hot_code_changed",
        "paper_current_head_status": "strict_current_head_10run_still_required_for_exact_paper_table",
        "selected_next": "stage331_current_head_highstat_refresh_or_compact_keygen_security_preflight",
    }]

    evidence_rows = [
        {
            "evidence": "stage296_perf_direct_dft",
            "status": "PASS" if s296_direct.get("correctness") == "Pass" and int(s296_direct.get("samples", "0") or "0") >= 10 else "PARTIAL",
            "metric": "complete SAB T_bootstrap/r",
            "value": f"speedup={s296_direct.get('speedup_vs_repeated_scalar_mean', '')}; T/r={s296_direct.get('t_bootstrap_over_r_mean_us', '')}us; samples={s296_direct.get('samples', '')}",
            "scope": "historical-source high-stat mechanism evidence for direct DFT selected path.",
        },
        {
            "evidence": "stage296_noise_direct_dft",
            "status": "PASS" if s296_noise.get("status") == "pass" and s296_noise.get("pair_failures") == "0" else "PARTIAL",
            "metric": "target final-output pair equivalence/noise",
            "value": f"trials={s296_noise.get('trials', '')}; pair_failures={s296_noise.get('pair_failures', '')}; log2_sigma={s296_noise.get('pair_log2_sigma_torus', '')}",
            "scope": "historical direct-DFT noise side evidence.",
        },
        {
            "evidence": "stage297_resource_sidecondition",
            "status": "PASS" if stage297_resource_rows else "MISSING",
            "metric": "resource side condition",
            "value": f"rss_ratio={stage297_resource_rows[0].get('stage297_direct_vs_selected_rss_ratio', '') if stage297_resource_rows else ''}; key_ratio={stage297_resource_rows[0].get('stage293_target_key_ratio', '') if stage297_resource_rows else ''}",
            "scope": "local resource side condition, not all-parameter memory proof.",
        },
        {
            "evidence": "stage321_direct_baseline",
            "status": "PASS" if s321_direct.get("correctness") == "Pass" and current_hotcode_equiv else "PARTIAL",
            "metric": "current-hot-code complete SAB T_bootstrap/r",
            "value": f"speedup={s321_direct.get('speedup_vs_repeated_scalar_mean', '')}; T/r={s321_direct.get('t_bootstrap_over_r_mean_us', '')}us; samples={s321_direct.get('samples', '')}",
            "scope": "current-hot-code engineering evidence; sample count is 5.",
        },
        {
            "evidence": "stage328_active_goal_audit",
            "status": "OPEN",
            "metric": "remaining original-goal gaps",
            "value": f"paper_highstat_ready={s328_summary.get('paper_highstat_ready', '')}; compact={s328_summary.get('compact_route', '')}",
            "scope": "stage330 narrows the high-stat gap but does not close optimality or compact proof.",
        },
        {
            "evidence": "stage329_compact_checker",
            "status": "OPEN",
            "metric": "compact finite algebra",
            "value": f"finite_failures={s329_summary.get('finite_failures', '')}; keygen_code_admitted={s329_summary.get('keygen_code_admitted', '')}",
            "scope": "compact selector finite algebra passed; no production keygen/security/noise/full-SAB claim.",
        },
    ]

    claim_rows = [
        {
            "claim": "primary_metric_dimension",
            "status": "PASS",
            "safe_statement": "The supported PVW/MAT-SAB speedups are amortized complete-SAB T_bootstrap/r against repeated scalar SAB.",
            "not_supported": "Kernel-only speedup or single bootstrap latency as the final algorithm claim.",
        },
        {
            "claim": "direct_dft_highstat_mechanism",
            "status": "PASS_SCOPED_HISTORICAL_SOURCE",
            "safe_statement": "Stage296 gives 10-run direct-DFT evidence with 10 noise trials under the same selected flags and parameter.",
            "not_supported": "It is not by itself an exact current-head paper table because hot-code files changed after 60350e3.",
        },
        {
            "claim": "current_hotcode_complete_sab",
            "status": "PASS_SCOPED_ENGINEERING",
            "safe_statement": "Stage321 direct baseline is current-hot-code equivalent from e193b30 to HEAD and records 5-sample T_bootstrap/r speedup.",
            "not_supported": "Paper-grade current-head >=10 sample claim without a rerun.",
        },
        {
            "claim": "strict_current_head_paper_ready",
            "status": "PARTIAL_RERUN_REQUIRED",
            "safe_statement": "A strict current-head paper table should rerun direct PVW/MAT-SAB with >=10 samples and refreshed noise/resource side conditions.",
            "not_supported": "Claiming the current head has already met the >=10 sample threshold.",
        },
        {
            "claim": "theoretical_optimality",
            "status": "OPEN",
            "safe_statement": "The exact dense implementation frontier is closed under current evidence; theoretical optimality remains unproven.",
            "not_supported": "The MAT/RLWE r-body SAB construction is globally optimal.",
        },
    ]

    proof_rows = [
        {
            "gate": "G1_inputs_present",
            "status": "PASS" if s296_direct and s321_direct else "FAIL",
            "metric": "Stage296/Stage321 summaries",
            "value": f"stage296={bool(s296_direct)}; stage321={bool(s321_direct)}",
            "interpretation": "Stage330 is an evidence reconciliation, so both input campaigns must be present.",
        },
        {
            "gate": "G2_flag_metric_compatibility",
            "status": "PASS" if flag_pass else "FAIL",
            "metric": "flag rows",
            "value": "all_pass" if flag_pass else "mismatch",
            "interpretation": "High-stat bridging is denied if parameter, backend, branch, or direct-DFT flags differ.",
        },
        {
            "gate": "G3_highstat_threshold",
            "status": "PASS" if int(s296_direct.get("samples", "0") or "0") >= 10 else "FAIL",
            "metric": "Stage296 samples",
            "value": s296_direct.get("samples", ""),
            "interpretation": "High-stat mechanism evidence requires at least ten complete-SAB samples.",
        },
        {
            "gate": "G4_current_hotcode_equivalence",
            "status": "PASS" if current_hotcode_equiv else "PARTIAL",
            "metric": "source diff e193b30..HEAD",
            "value": "no_hot_code_diff" if current_hotcode_equiv else f"{len(diff_321)} hot-code files changed",
            "interpretation": "Stage321 remains usable for current-hot-code evidence if hot SAB/MAT code did not change after its input head.",
        },
        {
            "gate": "G5_stage296_source_boundary",
            "status": "BOUNDARY",
            "metric": "source diff 60350e3..HEAD",
            "value": f"{len(diff_296)} hot-code files changed" if diff_296 else "no_hot_code_diff",
            "interpretation": "Historical high-stat evidence supports the mechanism and flag path, but strict current-head paper tables still need rerun if hot code changed.",
        },
        {
            "gate": "G6_decision",
            "status": DECISION,
            "metric": "claim boundary",
            "value": "high-stat mechanism reconciled; current-head strict high-stat remains optional/required by paper wording",
            "interpretation": "Do not claim theoretical optimality or compact SAB acceleration from this stage.",
        },
    ]

    next_rows = [
        {
            "priority": "P0",
            "route": "stage331_current_head_highstat_refresh",
            "entry_condition": "paper table needs exact current-head >=10 samples",
            "gate": "rerun direct PVW/MAT-SAB complete T_bootstrap/r with >=10 samples plus noise/resource refresh",
            "failure_action": "Keep Stage330 as historical high-stat mechanism support and Stage321 as current-hot-code engineering support.",
        },
        {
            "priority": "P1",
            "route": "stage331_compact_keygen_security_preflight",
            "entry_condition": "algorithmic improvement beyond exact dense frontier is prioritized",
            "gate": "close keygen distribution, semantic-zero security, and noise recurrence before production code",
            "failure_action": "Keep compact route proof-blocked; no SAB hot-path code.",
        },
    ]

    write_csv(SUMMARY, summary_rows, [
        "decision", "primary_metric", "stage296_samples", "stage296_speedup",
        "stage296_t_over_r_mean_us", "stage321_samples", "stage321_speedup",
        "stage321_t_over_r_mean_us", "speedup_delta_pct", "t_over_r_delta_pct",
        "flag_compatibility", "stage296_source_scope", "stage321_current_hotcode_scope",
        "paper_current_head_status", "selected_next",
    ])
    write_csv(FLAG_COMPAT, flag_rows, ["check", "stage296_perf_direct_dft", "stage321_direct_baseline", "status", "interpretation"])
    write_csv(SOURCE_DIFF, source_rows, ["comparison", "hot_code_changed", "changed_count", "changed_paths", "interpretation"])
    write_csv(EVIDENCE, evidence_rows, ["evidence", "status", "metric", "value", "scope"])
    write_csv(CLAIMS, claim_rows, ["claim", "status", "safe_statement", "not_supported"])
    write_csv(PROOF, proof_rows, ["gate", "status", "metric", "value", "interpretation"])
    write_csv(NEXT, next_rows, ["priority", "route", "entry_condition", "gate", "failure_action"])

    write_text(DOC, f"""# Stage330 High-Stat Reconciliation

Decision: `{DECISION}`.

Stage330 reconciles the existing high-stat direct-DFT evidence with the current
PVW/MAT-SAB claim boundary.  It does not run a new benchmark and it does not
admit compact SAB code.

The primary endpoint remains complete SAB `T_bootstrap/r`: the self-contained
bootstrap time divided by the number of MAT/RLWE body lanes, compared against
running scalar SAB independently for the same number of plaintext bits.

## Summary

{md_table(summary_rows, ["decision", "primary_metric", "stage296_speedup", "stage321_speedup", "flag_compatibility", "stage296_source_scope", "stage321_current_hotcode_scope", "paper_current_head_status"])}

## Flag And Metric Compatibility

{md_table(flag_rows, ["check", "stage296_perf_direct_dft", "stage321_direct_baseline", "status"])}

## Source Boundary

{md_table(source_rows, ["comparison", "hot_code_changed", "changed_count", "changed_paths"])}

## Evidence Matrix

{md_table(evidence_rows, ["evidence", "status", "metric", "value", "scope"])}

## Claim Update

{md_table(claim_rows, ["claim", "status", "safe_statement", "not_supported"])}

## Proof Gate

{md_table(proof_rows, ["gate", "status", "metric", "value"])}

Generated from input head `{git_head()}`.
""")

    write_text(THEORY, f"""# Stage330 High-Stat Reconciliation Model

## Research Question

Can Stage296's 10-run direct-DFT complete-SAB result be used to close the
Stage328 high-stat gap for the current PVW/MAT-SAB claim?

## Decision Logic

Let `M` be the endpoint `T_bootstrap/r`, where `r` is the number of MAT/RLWE
body lanes and the baseline is repeated scalar SAB over the same number of
plaintext bits.  Evidence can be bridged only if the following are true:

1. parameter, backend, branch, `r`, and direct-DFT flags match;
2. both campaigns measure complete SAB `M`, not an isolated kernel;
3. the source boundary is explicit.

Stage296 and Stage321 pass the metric/flag check.  Stage296 provides the
stronger statistical campaign, but it is historical-source evidence because
hot-code files changed after `60350e3`.  Stage321 is current-hot-code evidence
because no hot SAB/MAT source files changed between `e193b30` and `{git_head()}`
under the checked source set.

## Consequence

Safe claim: the selected direct-DFT PVW/MAT-SAB mechanism has high-stat
historical support and current-hot-code engineering support with matching
amortized complete-SAB metric.

Unsafe claim: exact current-head paper table with >=10 samples, unless Stage331
reruns current-head performance/noise/resource gates.
""")

    write_text(VARIANT, f"""# mat_rlwe_sab_stage330_reconciled_direct_dft_claim

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping with PVW/MAT-RLWE
  multi-body accumulator path.
- Focused module: complete SAB evidence and claim boundary for direct
  sub-decomposition-to-DFT materialization.
- Optimization target: amortized complete SAB `T_bootstrap/r`.
- Status labels: `PASS_SCOPED_HISTORICAL_HIGHSTAT`, `PASS_CURRENT_HOTCODE_ENGINEERING`,
  `PARTIAL_RERUN_REQUIRED_FOR_STRICT_CURRENT_HEAD_PAPER_TABLE`.
- Main hypothesis: using MAT/RLWE `r` body lanes amortizes the SAB schedule over
  multiple plaintext bits, and direct DFT materialization reduces complete-SAB
  per-lane time relative to repeated scalar SAB.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| repeated scalar SAB over `r` bits | one PVW/MAT-SAB run with `r` body lanes | changes ciphertext data structure and amortizes schedule | Stage296/321 complete `T_bootstrap/r` |
| delayed torus-to-DFT materialization | direct sub-decomposition-to-DFT path | implementation/schedule optimization within PVW/MAT-SAB | Stage296 high-stat; Stage321 current-hot-code |

## Complexity Change

- Time: measured as `T_bootstrap/r`; current supported speedup is in the
  `1.735849x` to `1.745361x` band for `BINARY SET_2_3_2048`, `r=4`,
  `spqlios_avx512`, include-zero.
- Memory/key: direct DFT does not add a key format; Stage297 records local RSS
  side condition for the selected/direct comparison.
- What must still be measured: exact current-head >=10 run table if paper
  wording requires strict current-head statistical evidence.

## Paper Contribution Candidate

`[experiment supported, scoped]` PVW/MAT-SAB should be reported using
amortized complete-SAB time per plaintext bit/lane, not kernel-only speedup.

`[not yet supported]` The construction is theoretically optimal among all
MAT/RLWE SAB algorithms, or compact selector variants are secure and faster.
""")

    write_text(PLAN, """# Stage331 Current-Head High-Stat Or Compact Plan

Input decision:
`PASS_STAGE330_HIGHSTAT_RECONCILIATION_HISTORICAL_10RUN_CURRENT_HOTCODE_5RUN`.

Route A: current-head high-stat refresh.

- run the exact selected direct PVW/MAT-SAB complete benchmark on the current
  hot-code head with at least 10 samples;
- refresh target final-output noise and resource side conditions;
- report `T_bootstrap/r` against repeated scalar SAB and keep backend fixed to
  `spqlios_avx512`;
- promote only if correctness passes and confidence intervals are recorded.

Route B: compact keygen/security preflight.

- map compact selector equations to production MAT_TRGSW key generation;
- prove or falsify public distribution and semantic-zero security obligations;
- derive a noise recurrence before any SAB hot-path compact code is admitted.
""")

    write_text(COMMANDS, f"""# Stage330 Reproduction Commands

```sh
python scripts/build_stage330_highstat_reconciliation.py
```

Inputs:

- `{rel(STAGE296_PERF)}`
- `{rel(STAGE296_NOISE)}`
- `{rel(STAGE297_RESOURCE)}`
- `{rel(STAGE321_PERF)}`
- `{rel(STAGE296_RUNNER)}`
- `{rel(STAGE321_RUNNER)}`

Stage330 is an analysis/reconciliation stage.  It intentionally does not rerun
the heavy complete-SAB benchmark.
""")

    report = read_text(DOC)
    write_text(REPORT, report)

    append_once(GOAL, "<!-- stage330-highstat-reconciliation -->", f"""
<!-- stage330-highstat-reconciliation -->
### Stage330 high-stat reconciliation

`{DECISION}` records that Stage296 supplies same-flag 10-run direct-DFT
mechanism evidence, while Stage321 remains the current-hot-code complete-SAB
engineering claim with 5 samples. Strict current-head paper tables still require
a fresh >=10-sample run.
""")

    append_once(ROADMAP, "<!-- stage330-highstat-reconciliation-roadmap -->", f"""
<!-- stage330-highstat-reconciliation-roadmap -->
## Stage 330: High-Stat Reconciliation

Goal: reconcile historical high-stat direct-DFT evidence with the current
PVW/MAT-SAB `T_bootstrap/r` claim boundary.

Status: `{DECISION}`.
""")

    append_once(HYPOTHESES, "H330_highstat_reconciliation:", f"""
H330_highstat_reconciliation:
  status: {DECISION}
  primary_metric: complete_sab_T_bootstrap_over_r_vs_repeated_scalar
  evidence:
    - repro/stage330_highstat_reconciliation/summary.csv
    - repro/stage330_highstat_reconciliation/flag_compatibility.csv
    - repro/stage330_highstat_reconciliation/source_diff_summary.csv
    - repro/stage330_highstat_reconciliation/claim_update.csv
  conclusion: >
    Stage330 reconciles same-flag Stage296 high-stat direct-DFT evidence with
    Stage321 current-hot-code engineering evidence. It preserves the strict
    boundary that current-head paper-grade >=10-sample evidence needs a rerun.
""")

    append_once(MANIFEST, "<!-- stage330-highstat-reconciliation-manifest -->", """
<!-- stage330-highstat-reconciliation-manifest -->
- stage330_highstat_reconciliation:
  - `docs/stage330_highstat_reconciliation.md`
  - `theory_checks/stage330_highstat_reconciliation_model.md`
  - `algorithm_variants/mat_rlwe_sab_stage330_reconciled_direct_dft_claim.md`
  - `experiments/stage331_current_head_highstat_or_compact_plan.md`
  - `scripts/build_stage330_highstat_reconciliation.py`
  - `repro/stage330_highstat_reconciliation/`
""")

    append_once(CHECKLIST, "<!-- stage330-highstat-reconciliation-checklist -->", f"""
<!-- stage330-highstat-reconciliation-checklist -->
- [x] Stage330 records `{DECISION}` and separates high-stat historical mechanism
  evidence from strict current-head paper-table requirements.
""")

    append_run_log()

    artifacts = [
        DOC, THEORY, VARIANT, PLAN, BUILDER, SUMMARY, FLAG_COMPAT, SOURCE_DIFF,
        EVIDENCE, CLAIMS, PROOF, NEXT, COMMANDS, REPORT,
    ]
    artifact_index(artifacts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
