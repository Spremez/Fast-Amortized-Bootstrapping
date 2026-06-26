#!/usr/bin/env python3
"""Build the Stage89 H14 promotion-policy integration report."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage89_h14_promotion_policy_integration"
OUT_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage89_h14_promotion_policy_integration_log.md"

STAGE88_SUMMARY = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "summary.csv"
STAGE88_BACKEND_WRAPPER = (
    ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "backend_vs_wrapper.csv"
)
STAGE88_FULL_SAB = (
    ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "full_sab_repeated.csv"
)
STAGE88_NOISE = ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "noise_summary.csv"
STAGE88_RESOURCE = (
    ROOT / "repro" / "stage88_h14_backend_repeated_gates" / "resource_summary.csv"
)
STAGE80_SUMMARY = ROOT / "repro" / "stage80_promotion_policy_audit" / "summary.csv"
STAGE36_TARGET_PERF = ROOT / "repro" / "stage36_target_perf_summary.csv"
CURRENT_SMOKE = OUT_DIR / "current_smoke" / "summary.csv"

MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"
PVWTMLWE_C = ROOT / "src" / "mosfhet" / "src" / "pvwtmlwe.c"
RUNNER = ROOT / "scripts" / "run_stage89_h14_promotion_policy_integration.sh"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "status", "evidence", "detail", "next_action"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def fnum(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, ""))
    except (TypeError, ValueError):
        return default


def row(gate: str, status: str, evidence: str, detail: str, next_action: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def stage88_precondition() -> Dict[str, str]:
    summary = by_key(STAGE88_SUMMARY, "gate")
    expected = {
        "stage88_repeated_full_sab": "PASS_BACKEND_FASTER",
        "stage88_backend_vs_scalar": "PASS",
        "stage88_wrapper_reference": "PASS",
        "stage88_final_noise": "PASS",
        "stage88_resource": "PASS",
        "stage88_decision": "PASS_STAGE88_H14_BACKEND_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE",
    }
    mismatches = [
        f"{gate}={summary.get(gate, {}).get('status', 'MISSING')}"
        for gate, expected_status in expected.items()
        if summary.get(gate, {}).get("status") != expected_status
    ]
    return row(
        "stage89_stage88_precondition",
        "PASS" if not mismatches else "FAIL_STAGE88_PRECONDITION",
        STAGE88_SUMMARY.relative_to(ROOT).as_posix(),
        "Stage88 repeated complete-SAB, final-output noise, and resource gates pass."
        if not mismatches
        else "; ".join(mismatches),
        "Rerun or repair Stage88 before making an H14 promotion-policy decision.",
    )


def current_head_smoke() -> Dict[str, str]:
    rows = by_key(CURRENT_SMOKE, "step")
    expected = [
        "scalar_binary_full_run",
        "backend_pvw_target_full_gate",
        "scalar_ternary_build",
    ]
    missing_or_failed = [step for step in expected if rows.get(step, {}).get("status") != "PASS"]
    if not rows:
        status = "MISSING_CURRENT_SMOKE"
        detail = "Stage89 current-head smoke was not run."
    elif missing_or_failed:
        status = "FAIL_CURRENT_SMOKE"
        detail = f"missing_or_failed={missing_or_failed}"
    else:
        status = "PASS"
        detail = (
            "scalar binary full run, explicit backend PVW target gate, "
            "and scalar ternary build pass under current head"
        )
    return row(
        "stage89_current_head_smoke",
        status,
        CURRENT_SMOKE.relative_to(ROOT).as_posix(),
        detail,
        "Run bash scripts/run_stage89_h14_promotion_policy_integration.sh with STAGE89_RUN_CURRENT_SMOKE=1 before relying on Stage89.",
    )


def default_path_guard() -> Dict[str, str]:
    make_text = MAKEFILE_DEF.read_text(encoding="utf-8") if MAKEFILE_DEF.exists() else ""
    pvw_text = PVWTMLWE_C.read_text(encoding="utf-8") if PVWTMLWE_C.exists() else ""
    runner_text = RUNNER.read_text(encoding="utf-8") if RUNNER.exists() else ""
    checks = {
        "makefile_default_false": "SAB_PVW_BACKEND_FROM_DFT_ADD ?= false" in make_text,
        "makefile_explicit_ifeq": "ifeq ($(SAB_PVW_BACKEND_FROM_DFT_ADD),true)" in make_text,
        "source_guarded": "#ifdef SAB_PVW_BACKEND_FROM_DFT_ADD" in pvw_text,
        "runner_explicit_flag": "SAB_PVW_BACKEND_FROM_DFT_ADD=true" in runner_text,
    }
    missing = [name for name, ok in checks.items() if not ok]
    return row(
        "stage89_default_path_guard",
        "PASS" if not missing else "FAIL_DEFAULT_GUARD",
        (
            f"{MAKEFILE_DEF.relative_to(ROOT).as_posix()}; "
            f"{PVWTMLWE_C.relative_to(ROOT).as_posix()}; "
            f"{RUNNER.relative_to(ROOT).as_posix()}"
        ),
        "H14 backend FromDFT-add remains explicit, guarded, and default false."
        if not missing
        else f"missing_checks={missing}",
        "Do not change scalar/default behavior unless a separate default-promotion stage is created and passes full gates.",
    )


def stage80_precedent() -> Dict[str, str]:
    stage80 = by_key(STAGE80_SUMMARY, "gate")
    decision = stage80.get("stage80_decision", {}).get("status", "MISSING")
    return row(
        "stage89_stage80_policy_precedent",
        "PASS" if decision == "PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED" else "FAIL_STAGE80_PRECEDENT",
        STAGE80_SUMMARY.relative_to(ROOT).as_posix(),
        f"Stage80 policy precedent={decision}; H14 must make an explicit-path decision without changing defaults.",
        "If Stage80 precedent changes, rerun Stage89 with the revised promotion policy.",
    )


def performance_policy() -> Dict[str, str]:
    comparison_rows = read_csv(STAGE88_BACKEND_WRAPPER)
    comparison = comparison_rows[0] if comparison_rows else {}
    full = by_key(STAGE88_FULL_SAB, "variant")
    backend = full.get("backend", {})
    wrapper = full.get("wrapper", {})
    stage36 = {row.get("r"): row for row in read_csv(STAGE36_TARGET_PERF)}
    r4 = stage36.get("4", {})

    paired_runs = int(fnum(comparison, "paired_runs"))
    backend_vs_wrapper_mean = fnum(comparison, "backend_vs_wrapper_mean")
    backend_vs_wrapper_min = fnum(comparison, "backend_vs_wrapper_min")
    backend_speedup = fnum(backend, "mean_speedup_vs_scalar")
    backend_min = fnum(backend, "min_speedup_vs_scalar")
    wrapper_speedup = fnum(wrapper, "mean_speedup_vs_scalar")
    r4_mean = fnum(r4, "mean_speedup")
    r4_ci_low = fnum(r4, "ci95_low")
    r4_ci_high = fnum(r4, "ci95_high")

    promote_explicit = (
        paired_runs >= 3
        and backend_vs_wrapper_min > 1.0
        and backend_speedup > r4_mean
        and backend_min > r4_ci_low
        and backend_speedup > wrapper_speedup
    )
    if promote_explicit:
        status = "PROMOTE_EXPLICIT_PATH_NOT_DEFAULT"
        next_action = "Use H14 backend FromDFT-add as the preferred explicit r=6 local engineering path; keep defaults unchanged."
    elif paired_runs >= 3 and backend_vs_wrapper_mean > 1.0 and backend_speedup > 1.0:
        status = "KEEP_EXPERIMENTAL_NOT_PROMOTED"
        next_action = "Keep H14 backend opt-in only and require stronger repeated/high-stat evidence before promotion."
    else:
        status = "REJECT_OR_NEUTRAL"
        next_action = "Do not use H14 backend as the preferred path; return to profile-guided variant search."

    detail = (
        f"paired={paired_runs}; backend/wrapper mean={backend_vs_wrapper_mean:.6f}; "
        f"min={backend_vs_wrapper_min:.6f}; backend/scalar mean={backend_speedup:.3f}; "
        f"backend/scalar min={backend_min:.3f}; wrapper/scalar mean={wrapper_speedup:.3f}; "
        f"Stage36 r4 mean={r4_mean:.3f}; r4 CI=[{r4_ci_low:.6f},{r4_ci_high:.6f}]"
    )
    return row(
        "stage89_performance_policy",
        status,
        (
            f"{STAGE88_BACKEND_WRAPPER.relative_to(ROOT).as_posix()}; "
            f"{STAGE88_FULL_SAB.relative_to(ROOT).as_posix()}; "
            f"{STAGE36_TARGET_PERF.relative_to(ROOT).as_posix()}"
        ),
        detail,
        next_action,
    )


def noise_resource_guard() -> Dict[str, str]:
    noise_rows = read_csv(STAGE88_NOISE)
    resource_rows = read_csv(STAGE88_RESOURCE)
    noise = noise_rows[0] if noise_rows else {}
    resource = resource_rows[0] if resource_rows else {}
    ok = noise.get("status") == "PASS" and resource.get("status") == "PASS"
    return row(
        "stage89_noise_resource_guard",
        "PASS" if ok else "FAIL_NOISE_OR_RESOURCE",
        f"{STAGE88_NOISE.relative_to(ROOT).as_posix()}; {STAGE88_RESOURCE.relative_to(ROOT).as_posix()}",
        (
            f"noise={noise.get('status', 'MISSING')}; seeds={noise.get('seeds', '0')}; "
            f"resource={resource.get('status', 'MISSING')}; runs={resource.get('runs', '0')}; "
            f"key_ratio={resource.get('key_ratio_mean', '0')}; "
            f"keygen_ratio={resource.get('keygen_ratio_mean', '0')}; "
            f"rss_ratio={resource.get('rss_ratio_mean', '0')}"
        ),
        "Do not promote or rely on H14 backend if future noise/resource gates fail.",
    )


def claim_guard() -> Dict[str, str]:
    texts = []
    for path in [
        ROOT / "docs" / "goal_sab_max_acceleration.md",
        ROOT / "docs" / "roadmap_stage19_plus.md",
        ROOT / "algorithm_variants" / "pvw_sab_h14_secondary_cmux_materialization.md",
    ]:
        texts.append(path.read_text(encoding="utf-8") if path.exists() else "")
    haystack = "\n".join(texts)
    required = [
        "scalar/default",
        "paper-level",
        "novelty",
        "explicit",
    ]
    missing = [token for token in required if token not in haystack]
    return row(
        "stage89_claim_guard",
        "PASS" if not missing else "FAIL_CLAIM_GUARD",
        "docs/goal_sab_max_acceleration.md; docs/roadmap_stage19_plus.md; algorithm_variants/pvw_sab_h14_secondary_cmux_materialization.md",
        "Claim wording keeps H14 as explicit engineering evidence, not default or paper-level novelty."
        if not missing
        else f"missing_tokens={missing}",
        "Repair claim scope before relying on Stage89 in paper or final reports.",
    )


def build_rows() -> List[Dict[str, str]]:
    rows = [
        stage88_precondition(),
        current_head_smoke(),
        default_path_guard(),
        stage80_precedent(),
        performance_policy(),
        noise_resource_guard(),
        claim_guard(),
    ]
    statuses = {item["gate"]: item["status"] for item in rows}
    promote = (
        statuses["stage89_stage88_precondition"] == "PASS"
        and statuses["stage89_current_head_smoke"] == "PASS"
        and statuses["stage89_default_path_guard"] == "PASS"
        and statuses["stage89_stage80_policy_precedent"] == "PASS"
        and statuses["stage89_performance_policy"] == "PROMOTE_EXPLICIT_PATH_NOT_DEFAULT"
        and statuses["stage89_noise_resource_guard"] == "PASS"
        and statuses["stage89_claim_guard"] == "PASS"
    )
    keep = (
        statuses["stage89_stage88_precondition"] == "PASS"
        and statuses["stage89_current_head_smoke"] == "PASS"
        and statuses["stage89_default_path_guard"] == "PASS"
        and statuses["stage89_performance_policy"] == "KEEP_EXPERIMENTAL_NOT_PROMOTED"
        and statuses["stage89_noise_resource_guard"] == "PASS"
    )
    if promote:
        decision = "PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT"
        detail = (
            "H14-C1 backend FromDFT-add is promoted as the preferred explicit r=6 "
            "local engineering path, while scalar/default paths and paper-level "
            "claims remain unchanged."
        )
        next_action = "Use this explicit path for follow-up Stage90 external/perf-counter unlocks and any future high-stat/default-promotion review."
    elif keep:
        decision = "PASS_STAGE89_H14_BACKEND_KEEP_EXPERIMENTAL_NOT_PROMOTED"
        detail = "H14-C1 remains opt-in experimental evidence; do not use it as the preferred explicit path yet."
        next_action = "Run stronger policy or high-stat gates before promotion."
    else:
        decision = "FAIL_STAGE89_H14_PROMOTION_POLICY"
        detail = "Stage89 cannot make a valid H14 promotion decision from the current evidence."
        next_action = "Fix failed Stage89 gates before moving to external claim unlocks."

    rows.append(
        row(
            "stage89_decision",
            decision,
            OUT_CSV.relative_to(ROOT).as_posix(),
            detail,
            next_action,
        )
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = rows[-1]
    lines = [
        "# Stage89 H14 Promotion Policy Integration Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage89 converts the Stage88 H14-C1 backend FromDFT-add promotion",
        "candidate into an explicit policy decision. It does not change scalar",
        "SAB, does not change default `sab_pvw_*` behavior, and does not upgrade",
        "paper-level novelty or theory claims.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next_action |",
        "|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            "| {gate} | {status} | {evidence} | {detail} | {next_action} |".format(
                **{k: item[k].replace("|", "\\|") for k in item}
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{decision['status']}`",
            "",
            decision["detail"],
            "",
            "Interpretation: H14-C1 is now the preferred explicit r=6 local",
            "engineering path for continued PVW/MAT-SAB work. This is not a",
            "default-path promotion and not a final paper novelty claim.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage89 H14 promotion policy integration: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
