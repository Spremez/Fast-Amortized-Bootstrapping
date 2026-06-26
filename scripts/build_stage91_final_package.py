#!/usr/bin/env python3
"""Build the Stage91 final scoped PVW/MAT-SAB package."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage91_final_package"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage91_final_sab_optimization_package.md"

STAGE36_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
STAGE36_NOISE = ROOT / "repro" / "stage36_target_noise_seeds50" / "aggregate.csv"
STAGE36_RESOURCE = ROOT / "repro" / "stage36_resource_summary.csv"
STAGE50_MATRIX = ROOT / "repro" / "stage50_performance_evidence_matrix.csv"
STAGE88_FULL = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "full_sab_repeated.csv"
STAGE88_BACKEND = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "backend_vs_wrapper.csv"
STAGE88_NOISE = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "noise_summary.csv"
STAGE88_RESOURCE = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "resource_summary.csv"
STAGE89 = ROOT / "repro" / "stage89_h14_promotion_policy_integration" / "summary.csv"
STAGE89_SMOKE = (
    ROOT / "repro" / "stage89_h14_promotion_policy_integration" / "current_smoke" / "summary.csv"
)
STAGE90 = ROOT / "repro" / "stage90_external_claim_unlock" / "summary.csv"
STAGE42 = ROOT / "repro" / "stage42_evidence_closure_audit.csv"
STAGE51 = ROOT / "repro" / "stage51_goal_completion_frontier.csv"
STAGE57 = ROOT / "repro" / "stage57_scope_label_audit.csv"
STAGE59 = ROOT / "repro" / "stage59_completion_route_readiness.csv"
STAGE68 = ROOT / "repro" / "stage68_frontier_closure_consistency.csv"
BLOCKERS = ROOT / "repro" / "remaining_blocker_dashboard.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def row(gate: str, status: str, evidence: str, detail: str, next_action: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def git_output(args: List[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()


def stage89_anchor_commit() -> str:
    try:
        return git_output(
            [
                "git",
                "log",
                "--grep=Add Stage89 H14 promotion policy integration",
                "--format=%H",
                "-n",
                "1",
            ]
        )
    except Exception:
        return ""


def changed_sab_sources_after_stage89(anchor: str) -> List[str]:
    if not anchor:
        return ["MISSING_STAGE89_ANCHOR"]
    try:
        out = git_output(
            [
                "git",
                "diff",
                "--name-only",
                f"{anchor}..HEAD",
                "--",
                "main.c",
                "include",
                "src",
                "Makefile",
                "CMakeLists.txt",
            ]
        )
    except Exception as exc:
        return [f"DIFF_ERROR:{exc}"]
    return [line for line in out.splitlines() if line.strip()]


def stage89_smoke_gate() -> Dict[str, str]:
    rows = by_key(STAGE89_SMOKE, "step")
    expected = [
        "scalar_binary_full_run",
        "backend_pvw_target_full_gate",
        "scalar_ternary_build",
    ]
    missing = [step for step in expected if rows.get(step, {}).get("status") != "PASS"]
    anchor = stage89_anchor_commit()
    changed_sources = changed_sab_sources_after_stage89(anchor)
    ok = not missing and not changed_sources
    detail = (
        f"stage89_smoke=PASS; stage89_anchor={anchor[:7]}; sab_source_changes_after_stage89=none"
        if ok
        else f"missing_or_failed_smoke={missing}; stage89_anchor={anchor[:7] if anchor else 'MISSING'}; sab_source_changes_after_stage89={changed_sources}"
    )
    return row(
        "stage91_smoke_current_code_guard",
        "PASS_CURRENT_SMOKE_INHERITED_SOURCE_UNCHANGED" if ok else "FAIL_CURRENT_SMOKE_OR_SOURCE_GUARD",
        f"{rel(STAGE89_SMOKE)}; git diff {anchor[:7] if anchor else 'MISSING'}..HEAD -- main.c include src",
        detail,
        "Rerun current-head smoke if SAB source files change after Stage89.",
    )


def performance_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for item in read_csv(STAGE36_PERF):
        rows.append(
            {
                "lane": "target_binary_high_stat",
                "param": "SET_2_3_2048",
                "r": item["r"],
                "evidence_level": "10_run_complete_sab",
                "status": item["decision"],
                "mean_speedup": item["mean_speedup"],
                "min_speedup": item["min_speedup"],
                "max_speedup": item["max_speedup"],
                "ci95_low": item["ci95_low"],
                "ci95_high": item["ci95_high"],
                "claim_level": "scoped_engineering_supported",
                "source": rel(STAGE36_PERF),
            }
        )
    stage88_full = by_key(STAGE88_FULL, "variant")
    backend = stage88_full.get("backend", {})
    if backend:
        rows.append(
            {
                "lane": "preferred_explicit_r6_h14_backend",
                "param": "SET_2_3_2048",
                "r": backend.get("r", "6"),
                "evidence_level": "3_run_complete_sab_plus_stage89_policy",
                "status": backend.get("status", "MISSING"),
                "mean_speedup": backend.get("mean_speedup_vs_scalar", ""),
                "min_speedup": backend.get("min_speedup_vs_scalar", ""),
                "max_speedup": backend.get("max_speedup_vs_scalar", ""),
                "ci95_low": "",
                "ci95_high": "",
                "claim_level": "preferred_explicit_engineering_path_not_default",
                "source": rel(STAGE88_FULL),
            }
        )
    return rows


def performance_gate() -> Dict[str, str]:
    perf = {row.get("r"): row for row in read_csv(STAGE36_PERF)}
    stage50 = by_key(STAGE50_MATRIX, "evidence_id")
    stage88 = by_key(STAGE88_BACKEND, "r")
    problems: List[str] = []
    for r_value in ["2", "4"]:
        row_data = perf.get(r_value, {})
        if row_data.get("decision") != "PASS_TARGET_PERF_10RUN":
            problems.append(f"stage36_r{r_value}={row_data.get('decision', 'MISSING')}")
        try:
            if float(row_data.get("ci95_low", "0")) <= 1.0:
                problems.append(f"stage36_r{r_value}_ci_low={row_data.get('ci95_low')}")
        except ValueError:
            problems.append(f"stage36_r{r_value}_ci_low_parse")
        matrix = stage50.get(f"stage36_target_perf_r{r_value}", {})
        if matrix.get("status") != "PASS":
            problems.append(f"stage50_r{r_value}={matrix.get('status', 'MISSING')}")
    r6 = stage88.get("6", {})
    if r6.get("status") != "PASS_BACKEND_FASTER":
        problems.append(f"stage88_r6_backend={r6.get('status', 'MISSING')}")
    return row(
        "stage91_performance_gate",
        "PASS_SCOPED_COMPLETE_SAB_PERFORMANCE" if not problems else "FAIL_PERFORMANCE_GATE",
        f"{rel(STAGE36_PERF)}; {rel(STAGE50_MATRIX)}; {rel(STAGE88_FULL)}; {rel(STAGE88_BACKEND)}",
        "Stage36 r=2/r=4 high-stat complete-SAB performance passes; Stage88 records preferred explicit r=6 H14 backend path."
        if not problems
        else "; ".join(problems),
        "Rerun performance campaigns before changing speedup wording.",
    )


def noise_resource_gate() -> Dict[str, str]:
    noise36 = {row.get("r"): row for row in read_csv(STAGE36_NOISE)}
    resource36 = {(row.get("r"), row.get("mode")): row for row in read_csv(STAGE36_RESOURCE)}
    noise88 = {row.get("r"): row for row in read_csv(STAGE88_NOISE)}
    resource88 = {row.get("r"): row for row in read_csv(STAGE88_RESOURCE)}
    problems: List[str] = []
    for r_value in ["2", "4"]:
        n = noise36.get(r_value, {})
        if n.get("status") != "PASS" or n.get("pvw_failures") != "0" or n.get("pair_failures") != "0":
            problems.append(f"stage36_noise_r{r_value}={n.get('status', 'MISSING')}")
        pvw = resource36.get((r_value, "pvw"), {})
        scalar = resource36.get((r_value, "scalar"), {})
        if pvw.get("decision") != "PASS_RESOURCE_3RUN" or scalar.get("decision") != "PASS_RESOURCE_3RUN":
            problems.append(f"stage36_resource_r{r_value}=MISSING_OR_FAIL")
    n6 = noise88.get("6", {})
    r6 = resource88.get("6", {})
    if n6.get("status") != "PASS" or n6.get("pair_failures") != "0":
        problems.append(f"stage88_noise_r6={n6.get('status', 'MISSING')}")
    if r6.get("status") != "PASS":
        problems.append(f"stage88_resource_r6={r6.get('status', 'MISSING')}")
    return row(
        "stage91_noise_resource_gate",
        "PASS_SCOPED_NOISE_RESOURCE" if not problems else "FAIL_NOISE_RESOURCE_GATE",
        f"{rel(STAGE36_NOISE)}; {rel(STAGE36_RESOURCE)}; {rel(STAGE88_NOISE)}; {rel(STAGE88_RESOURCE)}",
        "Stage36 r=2/r=4 target noise/resource and Stage88 r=6 explicit-path noise/resource gates pass under their recorded scopes."
        if not problems
        else "; ".join(problems),
        "Do not promote any path whose future noise/resource gate fails.",
    )


def stage89_policy_gate() -> Dict[str, str]:
    rows = by_key(STAGE89, "gate")
    decision = rows.get("stage89_decision", {}).get("status", "MISSING")
    return row(
        "stage91_stage89_policy_gate",
        "PASS_EXPLICIT_R6_POLICY_RECORDED"
        if decision == "PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT"
        else "FAIL_STAGE89_POLICY",
        rel(STAGE89),
        f"stage89_decision={decision}",
        "Keep H14 r=6 backend explicit/default-false unless a separate default-promotion gate passes.",
    )


def stage90_claim_gate() -> Dict[str, str]:
    rows = by_key(STAGE90, "gate")
    decision = rows.get("stage90_decision", {}).get("status", "MISSING")
    native = rows.get("stage90_native_perf_unlock", {}).get("status", "MISSING")
    fulltext = rows.get("stage90_fulltext_unlock", {}).get("status", "MISSING")
    novelty = rows.get("stage90_novelty_review_unlock", {}).get("status", "MISSING")
    ok = (
        decision == "PASS_STAGE90_EXTERNAL_CLAIM_UNLOCK_PROBE_RECORDED_STRONGER_CLAIMS_BLOCKED"
        and native == "WAIT_NATIVE_PERF"
        and fulltext == "WAIT_FULLTEXT_ARTIFACT"
        and novelty == "WAIT_FULLTEXT_OR_MANUAL_REVIEW"
    )
    return row(
        "stage91_external_claim_gate",
        "PASS_STRONGER_CLAIMS_BLOCKED" if ok else "FAIL_EXTERNAL_CLAIM_GATE",
        rel(STAGE90),
        f"decision={decision}; native={native}; fulltext={fulltext}; novelty={novelty}",
        "Keep novelty, theorem-level 2025/686 citations, and MAT-AVX512 optimality blocked until external evidence is supplied.",
    )


def closure_gate() -> Dict[str, str]:
    stage42 = by_key(STAGE42, "check_id")
    stage51 = by_key(STAGE51, "frontier_id")
    stage57 = by_key(STAGE57, "audit_id")
    stage59 = by_key(STAGE59, "route_id")
    stage68 = by_key(STAGE68, "gate")
    problems: List[str] = []
    if stage42.get("S42-OVERALL", {}).get("status") != "PASS_SCOPED_EVIDENCE_CLOSURE_STRONGER_CLAIMS_BLOCKED":
        problems.append("stage42_overall")
    if stage51.get("G6", {}).get("status") != "LOCAL_READY":
        problems.append("stage51_g6")
    if any(row.get("status") != "PASS" for row in stage57.values()):
        problems.append("stage57")
    stage59_r7 = stage59.get("S59-R7-FINAL-PAPER-PACKAGE", {}).get("status")
    if stage59_r7 not in {
        "WAIT_STRONGER_UNLOCKS",
        "SCOPED_FINAL_PACKAGE_READY_STRONGER_BLOCKED",
    }:
        problems.append("stage59_r7")
    if stage68.get("stage68_decision", {}).get("status") != "PASS_FRONTIER_CLOSURE_CONSISTENCY":
        problems.append("stage68")
    return row(
        "stage91_existing_closure_gate",
        "PASS_PRE_STAGE91_CLOSURE_READY" if not problems else "FAIL_PRE_STAGE91_CLOSURE",
        f"{rel(STAGE42)}; {rel(STAGE51)}; {rel(STAGE57)}; {rel(STAGE59)}; {rel(STAGE68)}",
        "Pre/post-Stage91 closure/frontier/route consistency is ready."
        if not problems
        else "; ".join(problems),
        "After Stage91 is generated, extend Stage42/verifier and rebuild closure.",
    )


def claim_boundary_rows() -> List[Dict[str, str]]:
    blockers = by_key(BLOCKERS, "blocker_id")
    return [
        {
            "claim_id": "C1",
            "claim": "PVW/MAT-SAB explicit path improves complete SAB throughput over repeated scalar SAB for tested binary target r=2/r=4.",
            "status": "ENGINEERING_SUPPORTED",
            "evidence": rel(STAGE36_PERF),
            "allowed_wording": "Scoped engineering throughput improvement under tested binary parameters and same backend.",
            "blocked_wording": "Universal, all-parameter, novelty, or theoretical-optimality claim.",
        },
        {
            "claim_id": "C2",
            "claim": "H14 backend FromDFT-add is the preferred explicit r=6 engineering path.",
            "status": "ENGINEERING_SUPPORTED_EXPLICIT_NOT_DEFAULT",
            "evidence": f"{rel(STAGE88_FULL)}; {rel(STAGE89)}",
            "allowed_wording": "Preferred explicit r=6 local engineering path with 3-run/noise/resource support.",
            "blocked_wording": "Default path promotion or high-stat/paper-level r=6 claim.",
        },
        {
            "claim_id": "C3",
            "claim": "MAT-AVX512 load/store/FMA theoretical optimality.",
            "status": blockers.get("CB5", {}).get("current_status", "BLOCKED_EXTERNAL"),
            "evidence": blockers.get("CB5", {}).get("evidence", rel(BLOCKERS)),
            "allowed_wording": "Practical implementation evidence only.",
            "blocked_wording": "Theoretical optimality or hardware-counter-backed memory-operation superiority.",
        },
        {
            "claim_id": "C4",
            "claim": "Novelty beyond scoped engineering/systems integration.",
            "status": blockers.get("CB6", {}).get("current_status", "BLOCKED_EXTERNAL_REVIEW"),
            "evidence": blockers.get("CB6", {}).get("evidence", rel(BLOCKERS)),
            "allowed_wording": "Novelty remains unclaimed.",
            "blocked_wording": "New shared-mask/multiple-body batching invention claim.",
        },
        {
            "claim_id": "C5",
            "claim": "Theorem-level 2025/686 protocol, table, figure, or experiment citations.",
            "status": blockers.get("CB7", {}).get("current_status", "BLOCKED_EXTERNAL_FULLTEXT"),
            "evidence": blockers.get("CB7", {}).get("evidence", rel(BLOCKERS)),
            "allowed_wording": "Metadata and implementation context only.",
            "blocked_wording": "Specific theorem/algorithm/table/figure citations from unreviewed full text.",
        },
    ]


def reproduction_rows() -> List[Dict[str, str]]:
    return [
        {
            "artifact": "Stage91 package",
            "command": "bash scripts/run_stage91_final_package.sh",
            "output": "docs/stage91_final_sab_optimization_package.md; repro/stage91_final_package/summary.csv",
        },
        {
            "artifact": "Stage90 external claim probe",
            "command": "bash scripts/run_stage90_external_claim_unlock.sh",
            "output": "docs/stage90_external_claim_unlock_log.md; repro/stage90_external_claim_unlock/summary.csv",
        },
        {
            "artifact": "closure audit",
            "command": "python scripts/build_stage42_evidence_closure_audit.py",
            "output": "docs/stage42_evidence_closure_audit.md; repro/stage42_evidence_closure_audit.csv",
        },
        {
            "artifact": "read-only closure verifier",
            "command": "python scripts/verify_stage42_closure.py --check-only",
            "output": "stdout",
        },
    ]


def write_performance_table(rows: List[Dict[str, str]]) -> None:
    write_csv(
        OUT_DIR / "performance_claims.csv",
        rows,
        [
            "lane",
            "param",
            "r",
            "evidence_level",
            "status",
            "mean_speedup",
            "min_speedup",
            "max_speedup",
            "ci95_low",
            "ci95_high",
            "claim_level",
            "source",
        ],
    )


def write_noise_resource_table() -> None:
    rows: List[Dict[str, str]] = []
    for item in read_csv(STAGE36_NOISE):
        rows.append(
            {
                "lane": "target_binary_noise",
                "r": item.get("r", ""),
                "scope": "50_seed_final_output",
                "status": item.get("status", ""),
                "failures": f"pvw={item.get('pvw_failures')}; scalar={item.get('scalar_failures')}; pair={item.get('pair_failures')}",
                "resource_or_noise": "noise",
                "source": rel(STAGE36_NOISE),
            }
        )
    for item in read_csv(STAGE88_NOISE):
        rows.append(
            {
                "lane": "explicit_r6_h14_noise",
                "r": item.get("r", ""),
                "scope": "3_seed_final_output",
                "status": item.get("status", ""),
                "failures": f"pvw={item.get('pvw_failures')}; scalar={item.get('scalar_failures')}; pair={item.get('pair_failures')}",
                "resource_or_noise": "noise",
                "source": rel(STAGE88_NOISE),
            }
        )
    for item in read_csv(STAGE36_RESOURCE):
        if item.get("mode") == "pvw" and item.get("r") in {"2", "4"}:
            rows.append(
                {
                    "lane": "target_binary_resource",
                    "r": item.get("r", ""),
                    "scope": "3_run_resource",
                    "status": item.get("decision", ""),
                    "failures": f"key_ratio={item.get('key_bytes_ratio_mean')}; rss_max_kb={item.get('time_max_rss_max_kb')}",
                    "resource_or_noise": "resource",
                    "source": rel(STAGE36_RESOURCE),
                }
            )
    for item in read_csv(STAGE88_RESOURCE):
        rows.append(
            {
                "lane": "explicit_r6_h14_resource",
                "r": item.get("r", ""),
                "scope": "1_run_resource",
                "status": item.get("status", ""),
                "failures": f"key_ratio={item.get('key_ratio_mean')}; rss_ratio={item.get('rss_ratio_mean')}; keygen_ratio={item.get('keygen_ratio_mean')}",
                "resource_or_noise": "resource",
                "source": rel(STAGE88_RESOURCE),
            }
        )
    write_csv(
        OUT_DIR / "noise_resource_claims.csv",
        rows,
        ["lane", "r", "scope", "status", "failures", "resource_or_noise", "source"],
    )


def markdown_table(rows: List[Dict[str, str]], columns: List[str]) -> List[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for item in rows:
        lines.append("| " + " | ".join(str(item.get(col, "")).replace("|", "\\|") for col in columns) + " |")
    return lines


def write_doc(summary: List[Dict[str, str]], perf: List[Dict[str, str]], claims: List[Dict[str, str]]) -> None:
    decision = summary[-1]
    lines = [
        "# Stage91 Final SAB Optimization Package",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "## Algorithm Scope",
        "",
        "The final scoped path is an explicit `sab_pvw_*` implementation beside",
        "the scalar `sab_rlwe_bootstrap` baseline. It batches multiple independent",
        "LUT/SAB lanes with PVW/MAT shared-mask multi-body external products.",
        "For the target binary `SET_2_3_2048` schedule, the Stage19 audit fixed",
        "the main external-product-class count at `(h+1)*r_prec*N = 40*7*2048 =",
        "573440`, with NCMUX `5080`; active-buffer fusion keeps copyback at zero",
        "in the promoted body path.",
        "",
        "The package distinguishes two evidence lanes:",
        "",
        "- target `r=2/4` high-stat scoped engineering evidence from Stage36;",
        "- preferred explicit `r=6` H14 backend evidence from Stage88/89, not a",
        "  default-path or paper-level claim.",
        "",
        "## Gates",
        "",
        *markdown_table(summary, ["gate", "status", "detail"]),
        "",
        "## Performance Claims",
        "",
        *markdown_table(
            perf,
            [
                "lane",
                "param",
                "r",
                "evidence_level",
                "mean_speedup",
                "min_speedup",
                "max_speedup",
                "ci95_low",
                "ci95_high",
                "claim_level",
            ],
        ),
        "",
        "## Claim Boundary",
        "",
        *markdown_table(claims, ["claim_id", "status", "allowed_wording", "blocked_wording"]),
        "",
        "## Reproduction",
        "",
        "The reproduction commands are recorded in",
        "`repro/stage91_final_package/reproduction_commands.csv`. The package",
        "does not rerun heavy benchmarks; it freezes the current audited evidence",
        "and requires reruns only when source code, backend, platform, or claim",
        "scope changes.",
        "",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def build_summary() -> List[Dict[str, str]]:
    rows = [
        stage89_smoke_gate(),
        performance_gate(),
        noise_resource_gate(),
        stage89_policy_gate(),
        stage90_claim_gate(),
        closure_gate(),
    ]
    ok = all(item["status"].startswith("PASS") for item in rows)
    decision = (
        "PASS_STAGE91_FINAL_SCOPED_PACKAGE_STRONGER_CLAIMS_BLOCKED"
        if ok
        else "FAIL_STAGE91_FINAL_PACKAGE"
    )
    rows.append(
        row(
            "stage91_decision",
            decision,
            rel(OUT_SUMMARY),
            "Final scoped SAB optimization package is assembled; stronger native-perf/full-text/novelty claims remain blocked."
            if ok
            else "One or more Stage91 gates failed; do not treat the final package as frozen.",
            "Keep the package scoped and rerun Stage90/91 plus closure verification after source, backend, or external-evidence changes.",
        )
    )
    return rows


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_summary()
    perf = performance_rows()
    claims = claim_boundary_rows()
    write_csv(
        OUT_SUMMARY,
        summary,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_performance_table(perf)
    write_noise_resource_table()
    write_csv(
        OUT_DIR / "claim_boundary.csv",
        claims,
        ["claim_id", "claim", "status", "evidence", "allowed_wording", "blocked_wording"],
    )
    write_csv(
        OUT_DIR / "reproduction_commands.csv",
        reproduction_rows(),
        ["artifact", "command", "output"],
    )
    artifact_rows = [
        {"artifact": "summary", "path": rel(OUT_SUMMARY)},
        {"artifact": "performance_claims", "path": rel(OUT_DIR / "performance_claims.csv")},
        {"artifact": "noise_resource_claims", "path": rel(OUT_DIR / "noise_resource_claims.csv")},
        {"artifact": "claim_boundary", "path": rel(OUT_DIR / "claim_boundary.csv")},
        {"artifact": "reproduction_commands", "path": rel(OUT_DIR / "reproduction_commands.csv")},
        {"artifact": "markdown_report", "path": rel(OUT_MD)},
    ]
    write_csv(OUT_DIR / "artifact_index.csv", artifact_rows, ["artifact", "path"])
    write_doc(summary, perf, claims)
    decision = summary[-1]["status"]
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage91 final package: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
