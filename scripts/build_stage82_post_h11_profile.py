#!/usr/bin/env python3
"""Build Stage82 post-H11 fused r=6 profile attribution."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage82_post_h11_profile"
BODY_SUMMARY = OUT_DIR / "body_profile_fused_r6" / "summary.csv"
STAGE75_PROFILE = ROOT / "repro" / "stage75_rgt4_profile_boundary" / "profile_metrics.csv"
STAGE79 = ROOT / "repro" / "stage79_rgt4_fused_high_stat" / "summary.csv"
STAGE80 = ROOT / "repro" / "stage80_promotion_policy_audit" / "summary.csv"
STAGE81 = ROOT / "repro" / "stage81_next_variant_triage.csv"
OUT_DECISION = OUT_DIR / "decision.csv"
OUT_PROFILE = OUT_DIR / "profile_metrics.csv"
OUT_MD = ROOT / "docs" / "stage82_post_h11_profile_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def single(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def fnum(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, ""))
    except ValueError:
        return default


def inum(row: Dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(float(row.get(key, "")))
    except ValueError:
        return default


def kv(line: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for token in line.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        out[key] = value.rstrip("x")
    return out


def profile_line_from_summary(summary_row: Dict[str, str]) -> Dict[str, str]:
    log_ref = summary_row.get("source_log", "")
    log_path = ROOT / log_ref if log_ref else Path()
    profile_line = ""
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "SAB_PVW_BODY_PROFILE sample" in line:
                profile_line = line
    return kv(profile_line)


def row(
    gate: str,
    status: str,
    metric: str,
    value: str,
    evidence: str,
    detail: str,
    next_action: str,
) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "metric": metric,
        "value": value,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def profile_metrics(body: Dict[str, str], values: Dict[str, str]) -> Dict[str, str]:
    full_us = float(values.get("full_us", "0") or 0)
    cmux_us = float(values.get("cmux_us", "0") or 0)
    mat_ep_us = float(values.get("mat_ep_us", "0") or 0)
    from_dft_us = float(values.get("cmux_from_dft_us", "0") or 0)
    cmux_add_us = float(values.get("cmux_add_us", "0") or 0)
    cmux_sub_us = float(values.get("cmux_sub_us", "0") or 0)
    ncmux_us = float(values.get("ncmux_us", "0") or 0)
    sub_a_us = float(values.get("sub_a_us", "0") or 0)
    sparse_mul_us = float(values.get("sparse_mul_us", "0") or 0)
    non_mat_us = max(full_us - mat_ep_us, 0.0)
    return {
        "r": body.get("r", "6"),
        "status": body.get("status", "MISSING"),
        "speedup": body.get("speedup", ""),
        "pvw_avg_us": body.get("pvw_avg_us", ""),
        "scalar_repeated_avg_us": body.get("scalar_repeated_avg_us", ""),
        "full_us": values.get("full_us", ""),
        "sparse_mul_us": values.get("sparse_mul_us", ""),
        "cmux_us": values.get("cmux_us", ""),
        "mat_ep_us": values.get("mat_ep_us", ""),
        "cmux_sub_us": values.get("cmux_sub_us", ""),
        "cmux_from_dft_us": values.get("cmux_from_dft_us", ""),
        "cmux_add_us": values.get("cmux_add_us", ""),
        "ncmux_us": values.get("ncmux_us", ""),
        "sub_a_us": values.get("sub_a_us", ""),
        "mat_ep_share_of_full": f"{mat_ep_us / full_us:.6f}" if full_us else "",
        "mat_ep_share_of_cmux": f"{mat_ep_us / cmux_us:.6f}" if cmux_us else "",
        "from_dft_share_of_full": f"{from_dft_us / full_us:.6f}" if full_us else "",
        "cmux_add_share_of_full": f"{cmux_add_us / full_us:.6f}" if full_us else "",
        "cmux_sub_share_of_full": f"{cmux_sub_us / full_us:.6f}" if full_us else "",
        "ncmux_share_of_full": f"{ncmux_us / full_us:.6f}" if full_us else "",
        "sub_a_share_of_full": f"{sub_a_us / full_us:.6f}" if full_us else "",
        "sparse_mul_share_of_full": f"{sparse_mul_us / full_us:.6f}" if full_us else "",
        "non_mat_share_of_full": f"{non_mat_us / full_us:.6f}" if full_us else "",
        "source_log": body.get("source_log", ""),
    }


def build_rows() -> List[Dict[str, str]]:
    stage81 = by_key(STAGE81, "gate")
    stage80 = by_key(STAGE80, "gate")
    stage79 = by_key(STAGE79, "gate")
    stage75_rows = read_csv(STAGE75_PROFILE)
    body = single(BODY_SUMMARY)
    values = profile_line_from_summary(body)
    metrics = profile_metrics(body, values)

    write_csv(
        OUT_PROFILE,
        [metrics],
        [
            "r",
            "status",
            "speedup",
            "pvw_avg_us",
            "scalar_repeated_avg_us",
            "full_us",
            "sparse_mul_us",
            "cmux_us",
            "mat_ep_us",
            "cmux_sub_us",
            "cmux_from_dft_us",
            "cmux_add_us",
            "ncmux_us",
            "sub_a_us",
            "mat_ep_share_of_full",
            "mat_ep_share_of_cmux",
            "from_dft_share_of_full",
            "cmux_add_share_of_full",
            "cmux_sub_share_of_full",
            "ncmux_share_of_full",
            "sub_a_share_of_full",
            "sparse_mul_share_of_full",
            "non_mat_share_of_full",
            "source_log",
        ],
    )

    required = [STAGE81, STAGE80, STAGE79, STAGE75_PROFILE, BODY_SUMMARY]
    missing = [p.relative_to(ROOT).as_posix() for p in required if not p.exists()]
    stage81_ok = (
        stage81.get("stage81_decision", {}).get("status")
        == "PASS_STAGE81_NEXT_VARIANT_TRIAGE_PROFILE_FIRST_NO_CODE_PROMOTION"
    )
    stage80_ok = (
        stage80.get("stage80_decision", {}).get("status")
        == "PASS_RGT4_FUSED_KEEP_EXPERIMENTAL_NOT_PROMOTED"
    )
    stage79_ok = (
        stage79.get("stage79_r6_high_stat_full_sab", {}).get("status")
        == "PASS_R4_REGION_NOT_CONFIRMED"
    )

    expected_cmux = inum(body, "expected_cmux")
    count_ok = (
        body.get("status") == "PASS"
        and inum(body, "cmux_calls") == expected_cmux == 573440
        and inum(body, "mat_ep_calls") == expected_cmux
        and inum(body, "ncmux_calls") == inum(body, "expected_ncmux") == 5080
        and inum(body, "sub_a_calls") == inum(body, "expected_sub_a") == 39
        and inum(body, "copyback_calls") == inum(body, "expected_active_copyback") == 0
    )

    generic_r6 = next((r for r in stage75_rows if r.get("r") == "6"), {})
    fused_speedup = fnum(metrics, "speedup")
    generic_speedup = fnum(generic_r6, "speedup")
    mat_share = fnum(metrics, "mat_ep_share_of_full")
    from_dft_share = fnum(metrics, "from_dft_share_of_full")
    add_share = fnum(metrics, "cmux_add_share_of_full")
    sub_share = fnum(metrics, "cmux_sub_share_of_full")
    non_mat_share = fnum(metrics, "non_mat_share_of_full")

    if mat_share >= 0.45:
        bottleneck_status = "MAT_BODY_REMAINS_PRIMARY"
        next_direction = "Open a theory/design check for MAT multiply/layout only if it can reduce dense body work without key-format risk."
    elif from_dft_share + add_share + sub_share >= 0.30:
        bottleneck_status = "CMUX_MATERIALIZATION_REVIEW"
        next_direction = "Review CMUX materialization/from_DFT/add/sub lifecycle before another MAT kernel variant."
    else:
        bottleneck_status = "MIXED_PROFILE_REVIEW"
        next_direction = "Do not implement code until the mixed profile is compared against another run or counter source."

    rows = [
        row(
            "stage82_inputs_available",
            "PASS" if not missing and stage81_ok and stage80_ok and stage79_ok else "FAIL",
            "stage81;stage80;stage79;stage75;body_summary",
            f"missing={missing}; stage81={stage81_ok}; stage80={stage80_ok}; stage79={stage79_ok}",
            "; ".join(p.relative_to(ROOT).as_posix() for p in required),
            "Stage82 has the Stage81 profile-first precondition and H11 policy evidence"
            if not missing and stage81_ok and stage80_ok and stage79_ok
            else "Restore missing/precondition evidence before using Stage82",
            "Rerun Stage81/80/79 or Stage82 profile if any precondition is false.",
        ),
        row(
            "stage82_fused_r6_profile_counts",
            "PASS" if count_ok else "FAIL",
            "cmux;mat_ep;ncmux;sub_a;copyback",
            f"{body.get('cmux_calls','')};{body.get('mat_ep_calls','')};{body.get('ncmux_calls','')};{body.get('sub_a_calls','')};{body.get('copyback_calls','')}",
            BODY_SUMMARY.relative_to(ROOT).as_posix(),
            "r=6 fused body profile preserves target schedule counts and active-buffer copyback=0"
            if count_ok
            else f"schedule/count mismatch: {body}",
            "Do not optimize until schedule counts are understood and stable.",
        ),
        row(
            "stage82_fused_vs_generic_profile",
            "PROFILE_ONLY_RECORDED",
            "fused_profile_speedup;stage75_generic_profile_speedup;stage79_high_stat_mean",
            f"{fused_speedup:.3f};{generic_speedup:.3f};1.367",
            f"{OUT_PROFILE.relative_to(ROOT).as_posix()}; {STAGE75_PROFILE.relative_to(ROOT).as_posix()}; {STAGE79.relative_to(ROOT).as_posix()}",
            "Instrumented profile timing is recorded for attribution only and is not a final latency claim.",
            "Use non-instrumented repeated A/B before any speedup claim or promotion.",
        ),
        row(
            "stage82_component_attribution",
            bottleneck_status,
            "mat_ep_share;from_dft_share;add_share;sub_share;non_mat_share",
            f"{mat_share:.6f};{from_dft_share:.6f};{add_share:.6f};{sub_share:.6f};{non_mat_share:.6f}",
            OUT_PROFILE.relative_to(ROOT).as_posix(),
            "Stage82 records the dominant post-H11 fused r=6 body-profile components.",
            next_direction,
        ),
    ]

    failures = [r["gate"] for r in rows if r["status"] == "FAIL"]
    decision_status = (
        "PASS_STAGE82_POST_H11_PROFILE_MAT_BODY_PRIMARY"
        if not failures and bottleneck_status == "MAT_BODY_REMAINS_PRIMARY"
        else "PASS_STAGE82_POST_H11_PROFILE_NONMAT_REVIEW"
        if not failures
        else "FAIL_STAGE82_POST_H11_PROFILE"
    )
    rows.append(
        row(
            "stage82_decision",
            decision_status,
            "profile_policy",
            "",
            OUT_DECISION.relative_to(ROOT).as_posix(),
            "Stage82 completes the profile-first requirement without promoting new code"
            if not failures
            else f"failed_gates={failures}",
            next_direction if not failures else "Fix failed gates and rerun Stage82.",
        )
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    metrics = read_csv(OUT_PROFILE)
    decision = rows[-1]["status"] if rows else "MISSING"
    lines = [
        "# Stage82 Post-H11 Fused R6 Profile Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage82 runs the profile-only attribution required by Stage81. It profiles",
        "the explicit H11 fused r=6 path and does not promote H11 or change scalar",
        "or default SAB behavior.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail | next_action |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            "| {gate} | {status} | {metric} | {value} | {evidence} | {detail} | {next_action} |".format(
                **{k: item[k].replace("|", "\\|") for k in item}
            )
        )
    lines.extend(
        [
            "",
            "## Profile Metrics",
            "",
            "| r | speedup | pvw_avg_us | full_us | mat_ep_us | mat_ep/full | from_DFT/full | add/full | sub/full | non-MAT/full |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in metrics:
        lines.append(
            "| {r} | {speedup} | {pvw_avg_us} | {full_us} | {mat_ep_us} | {mat_ep_share_of_full} | {from_dft_share_of_full} | {cmux_add_share_of_full} | {cmux_sub_share_of_full} | {non_mat_share_of_full} |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{decision}`",
            "",
            "Profile timing is instrumentation evidence only. Any future",
            "implementation or speedup claim still requires a new hypothesis, theory",
            "check, staged correctness, non-instrumented full-SAB A/B, noise/resource",
            "gates, and claim-policy update.",
            "",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(
        OUT_DECISION,
        rows,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_DECISION.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_PROFILE.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage82 post-H11 profile: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
