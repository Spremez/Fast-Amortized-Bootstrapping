#!/usr/bin/env python3
"""Build the Stage 65 r=4 unrolled AVX512 variant log."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / os.environ.get(
    "STAGE65_OUT_DIR", "repro/stage65_r4_unrolled_avx512"
)
KERNEL_CSV = OUT_DIR / "kernel_microbench.csv"
FULL_CSV = OUT_DIR / "full_sab_smoke.csv"
INSTR_CSV = OUT_DIR / "instruction_counts.csv"
DEFAULT_SCALAR_SMOKE_LOG = OUT_DIR / "default_scalar_ffnt_smoke.log"
SUMMARY_CSV = OUT_DIR / "summary.csv"
DOC_MD = ROOT / "docs" / "stage65_r4_unrolled_avx512_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
      return []
    with path.open(newline="", encoding="utf-8") as f:
      return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["gate", "status", "metric", "value", "evidence", "detail"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fmean(rows: Iterable[Dict[str, str]], field: str) -> float | None:
    values = []
    for row in rows:
        raw = row.get(field, "")
        if raw:
            values.append(float(raw))
    return mean(values) if values else None


def ratio_status(ratio: float | None) -> str:
    if ratio is None:
        return "MISSING"
    if ratio >= 1.01:
        return "SMOKE_POSITIVE"
    if ratio >= 0.99:
        return "NEUTRAL"
    return "NEGATIVE"


def ratio_detail(label: str, baseline: float | None, variant: float | None) -> str:
    if baseline is None or variant is None:
        return f"{label}: missing baseline or variant rows"
    return (
        f"{label}: specialized_mean_us={baseline:.3f}; "
        f"r4_unrolled_mean_us={variant:.3f}; ratio={baseline / variant:.6f}x"
    )


def build_rows() -> List[Dict[str, str]]:
    kernel_rows = read_csv(KERNEL_CSV)
    full_rows = read_csv(FULL_CSV)
    instr_rows = read_csv(INSTR_CSV)
    rows: List[Dict[str, str]] = []

    variants = {row.get("variant") for row in kernel_rows}
    required_variants = {"specialized", "r4_unrolled"}
    full_statuses = [row.get("status") for row in full_rows]
    correctness_ok = required_variants.issubset(variants) and all(
        status == "Pass" for status in full_statuses
    )
    rows.append(
        {
            "gate": "stage65_correctness",
            "status": "PASS" if correctness_ok else "FAIL",
            "metric": "kernel_variants;full_sab_statuses",
            "value": f"variants={sorted(v for v in variants if v)}; full={full_statuses}",
            "evidence": (
                f"{KERNEL_CSV.relative_to(ROOT).as_posix()}; "
                f"{FULL_CSV.relative_to(ROOT).as_posix()}"
            ),
            "detail": "staged kernel rows exist and full-SAB smoke rows pass when present",
        }
    )

    for kind in ("dft_output", "full_output"):
        base = [
            row
            for row in kernel_rows
            if row.get("variant") == "specialized"
            and row.get("kind") == kind
            and row.get("r") == "4"
        ]
        variant = [
            row
            for row in kernel_rows
            if row.get("variant") == "r4_unrolled"
            and row.get("kind") == kind
            and row.get("r") == "4"
        ]
        base_mean = fmean(base, "mat_avg_us")
        variant_mean = fmean(variant, "mat_avg_us")
        ratio = base_mean / variant_mean if base_mean and variant_mean else None
        rows.append(
            {
                "gate": f"stage65_kernel_{kind}",
                "status": ratio_status(ratio),
                "metric": "specialized_mat_avg_us / r4_unrolled_mat_avg_us",
                "value": "" if ratio is None else f"{ratio:.6f}",
                "evidence": KERNEL_CSV.relative_to(ROOT).as_posix(),
                "detail": ratio_detail(kind, base_mean, variant_mean),
            }
        )

    base_full = [row for row in full_rows if row.get("variant") == "specialized"]
    variant_full = [row for row in full_rows if row.get("variant") == "r4_unrolled"]
    base_full_mean = fmean(base_full, "pvw_avg_us")
    variant_full_mean = fmean(variant_full, "pvw_avg_us")
    full_ratio = (
        base_full_mean / variant_full_mean
        if base_full_mean and variant_full_mean
        else None
    )
    full_status = "NOT_RUN" if not full_rows else ratio_status(full_ratio)
    rows.append(
        {
            "gate": "stage65_full_sab_r4",
            "status": full_status,
            "metric": "specialized_pvw_avg_us / r4_unrolled_pvw_avg_us",
            "value": "" if full_ratio is None else f"{full_ratio:.6f}",
            "evidence": FULL_CSV.relative_to(ROOT).as_posix(),
            "detail": ratio_detail("full_sab_r4", base_full_mean, variant_full_mean),
        }
    )

    instr_detail = "instruction rows missing"
    if instr_rows:
        instr_detail = "; ".join(
            f"{row.get('variant')}: zmm={row.get('zmm_refs')} "
            f"vfmadd={row.get('vfmadd')} vfnmadd={row.get('vfnmadd')} "
            f"vfmsub={row.get('vfmsub')} vmovapd={row.get('vmovapd')} "
            f"vmovupd={row.get('vmovupd')}"
            for row in instr_rows
        )
    rows.append(
        {
            "gate": "stage65_instruction_proxy",
            "status": "RECORDED" if instr_rows else "MISSING",
            "metric": "objdump instruction proxy",
            "value": str(len(instr_rows)),
            "evidence": INSTR_CSV.relative_to(ROOT).as_posix(),
            "detail": instr_detail,
        }
    )

    scalar_text = (
        DEFAULT_SCALAR_SMOKE_LOG.read_text(encoding="utf-8", errors="replace")
        if DEFAULT_SCALAR_SMOKE_LOG.exists()
        else ""
    )
    scalar_pass = "Pass" in scalar_text and "Sparse bootstrapping with binary keys" in scalar_text
    rows.append(
        {
            "gate": "stage65_scalar_baseline_smoke",
            "status": "PASS" if scalar_pass else "MISSING_OR_FAIL",
            "metric": "default scalar ffnt smoke",
            "value": "Pass" if scalar_pass else "",
            "evidence": DEFAULT_SCALAR_SMOKE_LOG.relative_to(ROOT).as_posix(),
            "detail": (
                "default scalar SAB builds and runs without PVW or Stage65 flags"
                if scalar_pass
                else "run default scalar FFNT smoke before relying on baseline invariant"
            ),
        }
    )

    if not correctness_ok:
        decision = "REJECT_CORRECTNESS_OR_MISSING_ROWS"
    elif not full_rows:
        decision = "KERNEL_ONLY_PENDING_FULL_SAB"
    elif full_ratio is not None and full_ratio >= 1.01:
        decision = "SMOKE_POSITIVE_PENDING_REPEATED_NOISE_RESOURCE"
    elif full_ratio is not None and full_ratio >= 0.99:
        decision = "NEUTRAL_NOT_PROMOTED"
    else:
        decision = "NEGATIVE_NOT_PROMOTED"

    rows.append(
        {
            "gate": "stage65_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": (
                f"{KERNEL_CSV.relative_to(ROOT).as_posix()}; "
                f"{FULL_CSV.relative_to(ROOT).as_posix()}"
            ),
            "detail": (
                "Stage65A does not change the default promoted path; full repeated "
                "A/B plus noise/resource gates are required before any promotion."
            ),
        }
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    DOC_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage 65A R4 Unrolled AVX512 Variant Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage65A evaluates a reversible r=4 MAT external-product variant,",
        "`MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true`. The variant is limited to",
        "`k=1,l=1,r=4` AVX512 MAT/PVW external product code and does not alter",
        "scalar SAB, default PVW behavior, or the MAT_TRGSW key format.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | evidence | detail |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {gate} | {status} | {metric} | {value} | {evidence} | {detail} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Decision Policy",
            "",
            "A positive kernel result is not a bootstrapping acceleration claim.",
            "The variant can only be promoted after repeated complete-SAB A/B,",
            "correctness/noise, resource, and Stage42 closure gates pass.",
        ]
    )
    with DOC_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    rows = build_rows()
    write_csv(SUMMARY_CSV, rows)
    write_md(rows)
    decision = next(row for row in rows if row["gate"] == "stage65_decision")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"Wrote {DOC_MD.relative_to(ROOT)}")
    print(f"Stage65A decision: {decision['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
