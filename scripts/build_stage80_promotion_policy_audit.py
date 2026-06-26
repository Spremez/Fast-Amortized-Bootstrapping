#!/usr/bin/env python3
"""Build the Stage80 r>4 fused-MAT promotion policy audit."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage80_promotion_policy_audit"
OUT_CSV = OUT_DIR / "summary.csv"
OUT_MD = ROOT / "docs" / "stage80_promotion_policy_audit_log.md"

STAGE79_SUMMARY = ROOT / "repro" / "stage79_rgt4_fused_high_stat" / "summary.csv"
STAGE79_FULL = ROOT / "repro" / "stage79_rgt4_fused_high_stat" / "full_sab_high_stat.csv"
STAGE79_NOISE = ROOT / "repro" / "stage79_rgt4_fused_high_stat" / "noise_summary.csv"
STAGE79_RESOURCE = ROOT / "repro" / "stage79_rgt4_fused_high_stat" / "resource_summary.csv"
CURRENT_SMOKE = OUT_DIR / "current_smoke" / "summary.csv"
MAKEFILE_DEF = ROOT / "src" / "mosfhet" / "Makefile.def"
MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
STAGE79_RUNNER = ROOT / "scripts" / "run_stage79_rgt4_fused_high_stat.sh"


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


def default_path_guard() -> Dict[str, str]:
    make_text = MAKEFILE_DEF.read_text(encoding="utf-8") if MAKEFILE_DEF.exists() else ""
    mat_text = MATTRGSW_C.read_text(encoding="utf-8") if MATTRGSW_C.exists() else ""
    runner_text = STAGE79_RUNNER.read_text(encoding="utf-8") if STAGE79_RUNNER.exists() else ""
    checks = {
        "makefile_default_false": "MAT_TRGSW_AVX512_RGT4_FUSED ?= false" in make_text,
        "source_guarded": "#if defined(MAT_TRGSW_AVX512_RGT4_FUSED)" in mat_text,
        "runner_explicit_flag": "MAT_TRGSW_AVX512_RGT4_FUSED=true" in runner_text,
    }
    missing = [name for name, ok in checks.items() if not ok]
    status = "PASS" if not missing else "FAIL_DEFAULT_GUARD"
    return row(
        "stage80_default_path_guard",
        status,
        f"{MAKEFILE_DEF.relative_to(ROOT).as_posix()}; {MATTRGSW_C.relative_to(ROOT).as_posix()}; {STAGE79_RUNNER.relative_to(ROOT).as_posix()}",
        "r>4 fused MAT remains an explicit opt-in flag and is not the default"
        if not missing
        else f"missing_checks={missing}",
        "Do not promote or expose r>4 fused MAT by default unless this guard is intentionally revised with full current-head gates.",
    )


def current_smoke_guard() -> Dict[str, str]:
    rows = by_key(CURRENT_SMOKE, "step")
    expected = ["scalar_binary_full_run", "pvw_target_full_gate", "scalar_ternary_build"]
    missing_or_failed = [
        step for step in expected if rows.get(step, {}).get("status") != "PASS"
    ]
    if not rows:
        status = "MISSING_CURRENT_SMOKE"
        detail = "Stage80 current-head smoke was not run."
    elif missing_or_failed:
        status = "FAIL_CURRENT_SMOKE"
        detail = f"missing_or_failed={missing_or_failed}"
    else:
        status = "PASS"
        detail = "scalar binary full run, explicit PVW target gate, and scalar ternary build pass under current head"
    return row(
        "stage80_current_head_smoke",
        status,
        CURRENT_SMOKE.relative_to(ROOT).as_posix(),
        detail,
        "Run bash scripts/run_stage80_promotion_policy_audit.sh with STAGE80_RUN_CURRENT_SMOKE=1 before relying on Stage80.",
    )


def build_rows() -> List[Dict[str, str]]:
    stage79 = by_key(STAGE79_SUMMARY, "gate")
    full_rows = read_csv(STAGE79_FULL)
    full = full_rows[0] if full_rows else {}
    noise_rows = read_csv(STAGE79_NOISE)
    noise = noise_rows[0] if noise_rows else {}
    resource_rows = read_csv(STAGE79_RESOURCE)
    resource = resource_rows[0] if resource_rows else {}

    stage79_decision = stage79.get("stage79_decision", {}).get("status", "MISSING")
    full_status = stage79.get("stage79_r6_high_stat_full_sab", {}).get("status", "MISSING")
    noise_status = stage79.get("stage79_r6_final_noise", {}).get("status", "MISSING")
    resource_status = stage79.get("stage79_r6_resource", {}).get("status", "MISSING")

    mean_speedup = fnum(full, "mean_speedup")
    r4_mean = fnum(full, "stage36_r4_mean_reference")
    ci_low = fnum(full, "ci95_low")
    r4_ci_low = fnum(full, "stage36_r4_ci95_low_reference")
    samples = int(fnum(full, "samples"))

    performance_policy = (
        "KEEP_EXPERIMENTAL_NOT_PROMOTED"
        if full_status == "PASS_R4_REGION_NOT_CONFIRMED"
        and samples >= 10
        and ci_low >= r4_ci_low
        and mean_speedup < r4_mean
        else "REVIEW_REQUIRED"
    )

    rows = [
        row(
            "stage80_stage79_precondition",
            "PASS"
            if stage79_decision == "PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED"
            else "FAIL_STAGE79_PRECONDITION",
            STAGE79_SUMMARY.relative_to(ROOT).as_posix(),
            f"stage79_decision={stage79_decision}",
            "Rerun Stage79 before Stage80 if this precondition is missing or failed.",
        ),
        row(
            "stage80_performance_policy",
            performance_policy,
            STAGE79_FULL.relative_to(ROOT).as_posix(),
            (
                f"samples={samples}; mean={mean_speedup:.3f}; "
                f"ci95_low={ci_low:.6f}; r4_mean={r4_mean:.3f}; "
                f"r4_ci95_low={r4_ci_low:.6f}; full_status={full_status}"
            ),
            "Keep r=6 fused behind an explicit experimental flag; do not make it default or promoted.",
        ),
        row(
            "stage80_noise_resource_guard",
            "PASS"
            if noise_status == "PASS" and resource_status == "PASS"
            else "FAIL_NOISE_OR_RESOURCE",
            f"{STAGE79_NOISE.relative_to(ROOT).as_posix()}; {STAGE79_RESOURCE.relative_to(ROOT).as_posix()}",
            (
                f"noise={noise_status}; seeds={noise.get('seeds', '0')}; "
                f"resource={resource_status}; runs={resource.get('runs', '0')}; "
                f"key_ratio={resource.get('key_ratio_mean', '0')}; "
                f"rss_ratio={resource.get('rss_ratio_mean', '0')}"
            ),
            "Do not keep even the experimental path if future noise/resource gates fail.",
        ),
        default_path_guard(),
        current_smoke_guard(),
    ]

    ok = (
        rows[0]["status"] == "PASS"
        and rows[1]["status"] == "KEEP_EXPERIMENTAL_NOT_PROMOTED"
        and rows[2]["status"] == "PASS"
        and rows[3]["status"] == "PASS"
        and rows[4]["status"] == "PASS"
    )
    rows.append(
        row(
            "stage80_decision",
            "PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED"
            if ok
            else "FAIL_RGT4_FUSED_POLICY_AUDIT",
            OUT_CSV.relative_to(ROOT).as_posix(),
            "H11 r=6 fused MAT remains available only as an explicit experimental flag; it is not promoted and does not change scalar/default paths."
            if ok
            else "Stage80 cannot make a keep/reject policy decision from the current evidence.",
            "Proceed to Stage81 variant triage; do not upgrade claims or defaults for r=6 fused MAT.",
        )
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = rows[-1]
    lines = [
        "# Stage80 Promotion Policy Audit Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage80 converts the Stage79 r=6 fused-MAT review-required result into",
        "an explicit policy decision. It does not modify scalar SAB, does not",
        "change `sab_pvw_*` defaults, and does not promote the r=6 fused path.",
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
            "The r=6 fused MAT kernel remains useful experimental evidence for",
            "future large-r work, but Stage79 did not beat the r=4 reference",
            "strongly enough to justify a default-path or promoted-line change.",
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
    print(f"Stage80 promotion policy audit: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
