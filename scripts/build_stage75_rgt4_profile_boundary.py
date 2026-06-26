#!/usr/bin/env python3
"""Build the Stage75 r>4 profile-boundary diagnosis."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage75_rgt4_profile_boundary"
R6_SUMMARY = OUT_DIR / "body_profile_r6" / "summary.csv"
R8_SUMMARY = OUT_DIR / "body_profile_r8" / "summary.csv"
STAGE74_DECISION = ROOT / "repro" / "stage74_r_scaling_boundary" / "decision.csv"
STAGE36_TARGET = ROOT / "repro" / "stage36_target_perf_summary.csv"
OUT_CSV = OUT_DIR / "decision.csv"
OUT_PROFILE = OUT_DIR / "profile_metrics.csv"
OUT_MD = ROOT / "docs" / "stage75_rgt4_profile_boundary_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fieldnames: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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


def single(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def key_values(line: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for token in line.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        out[key] = value.rstrip("x")
    return out


def profile_from_log(summary_row: Dict[str, str]) -> Dict[str, str]:
    log_ref = summary_row.get("source_log", "")
    log_path = ROOT / log_ref if log_ref else Path()
    profile_line = ""
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "SAB_PVW_BODY_PROFILE sample" in line:
                profile_line = line
    values = key_values(profile_line)
    r = summary_row.get("r", "")
    pvw_avg_us = fnum(summary_row, "pvw_avg_us")
    mat_ep_us = float(values.get("mat_ep_us", "0") or 0)
    cmux_us = float(values.get("cmux_us", "0") or 0)
    full_us = float(values.get("full_us", "0") or 0)
    return {
        "r": r,
        "status": summary_row.get("status", "MISSING"),
        "speedup": summary_row.get("speedup", ""),
        "pvw_avg_us": summary_row.get("pvw_avg_us", ""),
        "scalar_repeated_avg_us": summary_row.get("scalar_repeated_avg_us", ""),
        "full_us": values.get("full_us", ""),
        "sparse_mul_us": values.get("sparse_mul_us", ""),
        "rgsw_monomial_us": values.get("rgsw_monomial_us", ""),
        "cmux_us": values.get("cmux_us", ""),
        "mat_ep_us": values.get("mat_ep_us", ""),
        "cmux_sub_us": values.get("cmux_sub_us", ""),
        "cmux_from_dft_us": values.get("cmux_from_dft_us", ""),
        "cmux_add_us": values.get("cmux_add_us", ""),
        "ncmux_us": values.get("ncmux_us", ""),
        "sub_a_us": values.get("sub_a_us", ""),
        "mat_ep_share_of_cmux": f"{(mat_ep_us / cmux_us):.6f}" if cmux_us else "",
        "mat_ep_share_of_full": f"{(mat_ep_us / full_us):.6f}" if full_us else "",
        "pvw_lane_avg_us": f"{(pvw_avg_us / float(r)):.3f}" if pvw_avg_us and r else "",
        "source_log": log_ref,
    }


def body_gate(r_value: int, path: Path) -> Dict[str, str]:
    row = single(path)
    expected_cmux = inum(row, "expected_cmux")
    ok = (
        row.get("status") == "PASS"
        and inum(row, "cmux_calls") == expected_cmux
        and inum(row, "mat_ep_calls") == expected_cmux
        and inum(row, "ncmux_calls") == inum(row, "expected_ncmux")
        and inum(row, "sub_a_calls") == inum(row, "expected_sub_a")
        and inum(row, "copyback_calls") == inum(row, "expected_active_copyback")
    )
    return {
        "gate": f"stage75_r{r_value}_body_profile",
        "status": "PASS" if ok else "FAIL",
        "metric": "status;cmux;mat_ep;ncmux;sub_a;copyback",
        "value": (
            f"{row.get('status', 'MISSING')};{row.get('cmux_calls', '')};"
            f"{row.get('mat_ep_calls', '')};{row.get('ncmux_calls', '')};"
            f"{row.get('sub_a_calls', '')};{row.get('copyback_calls', '')}"
        ),
        "evidence": path.relative_to(ROOT).as_posix(),
        "detail": (
            f"r={r_value} profile correctness/count gates pass with CMUX/MAT EP={expected_cmux}"
            if ok
            else f"r={r_value} profile mismatch: {row}"
        ),
    }


def schedule_invariant_gate() -> Dict[str, str]:
    r6 = single(R6_SUMMARY)
    r8 = single(R8_SUMMARY)
    expected = 573440
    ok = all(
        inum(row, key) == expected
        for row in [r6, r8]
        for key in ["cmux_calls", "expected_cmux", "mat_ep_calls"]
    )
    return {
        "gate": "stage75_schedule_count_invariant",
        "status": "PASS" if ok else "FAIL",
        "metric": "expected_cmux",
        "value": str(expected),
        "evidence": (
            f"{R6_SUMMARY.relative_to(ROOT).as_posix()}; "
            f"{R8_SUMMARY.relative_to(ROOT).as_posix()}"
        ),
        "detail": (
            "r=6/r=8 keep the same SAB update count as r=2/r=4; degradation is not caused by extra schedule iterations"
            if ok
            else "CMUX/MAT EP count changed; fix schedule understanding before optimizing r>4"
        ),
    }


def boundary_diagnosis_gate(profile_rows: List[Dict[str, str]]) -> Dict[str, str]:
    stage74 = {row.get("gate"): row for row in read_csv(STAGE74_DECISION)}
    stage36 = {row.get("r"): row for row in read_csv(STAGE36_TARGET)}
    r4 = stage36.get("4", {})
    r4_ci_low = fnum(r4, "ci95_low")
    r6 = single(R6_SUMMARY)
    r8 = single(R8_SUMMARY)
    r6_speedup = fnum(r6, "speedup")
    r8_speedup = fnum(r8, "speedup")
    stage74_not_promoted = (
        stage74.get("stage74_decision", {}).get("status")
        == "PASS_R_GT4_BOUNDARY_RECORDED_NOT_PROMOTED"
    )
    below_or_mixed = r6_speedup < r4_ci_low or r8_speedup < r4_ci_low
    counts_ok = all(row.get("status") == "PASS" for row in [r6, r8])
    mat_ep_shares = [
        f"r={row['r']} mat_ep/full={row.get('mat_ep_share_of_full', '')}"
        for row in profile_rows
    ]
    status = (
        "NOT_PROMOTED_PROFILE_BOUNDARY"
        if stage74_not_promoted and below_or_mixed and counts_ok
        else "REVIEW_RGT4_PROFILE_BOUNDARY"
    )
    return {
        "gate": "stage75_rgt4_profile_boundary",
        "status": status,
        "metric": "r6_speedup;r8_speedup;r4_ci95_low;mat_ep_share",
        "value": f"{r6_speedup:.3f};{r8_speedup:.3f};{r4_ci_low:.6f};" + " ".join(mat_ep_shares),
        "evidence": (
            f"{OUT_PROFILE.relative_to(ROOT).as_posix()}; "
            f"{STAGE74_DECISION.relative_to(ROOT).as_posix()}; "
            f"{STAGE36_TARGET.relative_to(ROOT).as_posix()}"
        ),
        "detail": (
            "r>4 profile preserves exact SAB counts, while full-SAB speedup remains below or too close to the r=4 promoted boundary; future large-r work needs a dedicated r>4 MAT layout/kernel hypothesis"
            if status == "NOT_PROMOTED_PROFILE_BOUNDARY"
            else "r>4 profile requires manual review before updating the promotion boundary"
        ),
    }


def build_rows() -> List[Dict[str, str]]:
    profile_rows = [profile_from_log(single(R6_SUMMARY)), profile_from_log(single(R8_SUMMARY))]
    write_csv(
        OUT_PROFILE,
        profile_rows,
        [
            "r",
            "status",
            "speedup",
            "pvw_avg_us",
            "scalar_repeated_avg_us",
            "full_us",
            "sparse_mul_us",
            "rgsw_monomial_us",
            "cmux_us",
            "mat_ep_us",
            "cmux_sub_us",
            "cmux_from_dft_us",
            "cmux_add_us",
            "ncmux_us",
            "sub_a_us",
            "mat_ep_share_of_cmux",
            "mat_ep_share_of_full",
            "pvw_lane_avg_us",
            "source_log",
        ],
    )
    rows = [
        body_gate(6, R6_SUMMARY),
        body_gate(8, R8_SUMMARY),
        schedule_invariant_gate(),
        boundary_diagnosis_gate(profile_rows),
    ]
    failures = [row["gate"] for row in rows if row["status"] == "FAIL"]
    promoted = rows[-1]["status"] != "NOT_PROMOTED_PROFILE_BOUNDARY"
    decision_status = (
        "PASS_RGT4_PROFILE_BOUNDARY_RECORDED_NOT_PROMOTED"
        if not failures and not promoted
        else "PASS_RGT4_PROFILE_REVIEW_REQUIRED"
        if not failures
        else "FAIL_RGT4_PROFILE_BOUNDARY"
    )
    rows.append(
        {
            "gate": "stage75_decision",
            "status": decision_status,
            "metric": "promotion_policy",
            "value": "",
            "evidence": OUT_CSV.relative_to(ROOT).as_posix(),
            "detail": (
                "Stage75 attributes direct r>4 underperformance to per-update body/MAT cost under invariant SAB schedule counts; no r>4 promotion"
                if decision_status == "PASS_RGT4_PROFILE_BOUNDARY_RECORDED_NOT_PROMOTED"
                else f"failed_gates={failures}; promoted_review={promoted}"
            ),
        }
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    profile_rows = read_csv(OUT_PROFILE)
    lines = [
        "# Stage75 R>4 Profile Boundary Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage75 diagnoses the Stage74 r>4 lane-scaling boundary with body-profile",
        "evidence. It does not modify scalar SAB, `sab_pvw_*`, the MAT key format,",
        "or the promotion policy.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['evidence']} | {row['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Profile Metrics",
            "",
            "| r | speedup | pvw_avg_us | mat_ep_us | cmux_us | full_us | mat_ep/full | lane_avg_us |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in profile_rows:
        lines.append(
            "| {r} | {speedup} | {pvw_avg_us} | {mat_ep_us} | {cmux_us} | {full_us} | {mat_ep_share_of_full} | {pvw_lane_avg_us} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The r=6 and r=8 profiles preserve the target SAB schedule counts:",
            "`40 * 7 * 2048 = 573440` CMUX/MAT external-product updates,",
            "`5080` NCMUX updates, `39` sub_a calls, and `0` active-buffer",
            "copybacks. Therefore the r>4 boundary is not a schedule-count issue.",
            "",
            "The observed larger-r slowdown is consistent with the dense MAT body",
            "cost and generic large-r loop pressure increasing per update. Future",
            "large-r work should start from a dedicated r>4 MAT layout/kernel or",
            "sparse/structured-MAT hypothesis; directly increasing lane count is",
            "not promoted.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    rows = build_rows()
    write_csv(
        OUT_CSV,
        rows,
        ["gate", "status", "metric", "value", "evidence", "detail"],
    )
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_PROFILE.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage75 r>4 profile boundary: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
