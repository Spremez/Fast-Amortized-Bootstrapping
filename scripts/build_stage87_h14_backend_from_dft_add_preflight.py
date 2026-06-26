#!/usr/bin/env python3
"""Build the Stage87 H14 backend FromDFT-add preflight report."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage87_h14_backend_from_dft_add_preflight"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_FULL_SAB = OUT_DIR / "full_sab_smoke.csv"
OUT_MD = ROOT / "docs" / "stage87_h14_backend_from_dft_add_preflight_log.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def has_all(text: str, needles: List[str]) -> bool:
    return all(needle in text for needle in needles)


def parse_bench(log_path: Path, variant: str) -> Dict[str, str]:
    text = read_text(log_path)
    correctness = re.search(
        r"SAB_PVW_BENCH correctness target_full r=(\d+) h=(\d+) r_prec=(\d+): (\w+)",
        text,
    )
    summary = re.search(
        r"SAB_PVW_BENCH summary target_full r=(\d+) reps=(\d+) "
        r"pvw_avg_us=([0-9.]+) pvw_stddev_us=([0-9.]+) "
        r"pvw_lane_avg_us=([0-9.]+) scalar_repeated_avg_us=([0-9.]+) "
        r"scalar_stddev_us=([0-9.]+) scalar_lane_avg_us=([0-9.]+) "
        r"speedup_vs_scalar_repeated=([0-9.]+)x speedup_stddev=([0-9.]+)",
        text,
    )
    row = {
        "variant": variant,
        "r": "",
        "status": "MISSING",
        "reps": "",
        "pvw_avg_us": "",
        "pvw_lane_avg_us": "",
        "scalar_repeated_avg_us": "",
        "scalar_lane_avg_us": "",
        "speedup_vs_scalar_repeated": "",
        "source_log": log_path.relative_to(ROOT).as_posix(),
    }
    if correctness:
        row["r"] = correctness.group(1)
        row["status"] = correctness.group(4)
    if summary:
        row.update(
            {
                "r": summary.group(1),
                "reps": summary.group(2),
                "pvw_avg_us": summary.group(3),
                "pvw_lane_avg_us": summary.group(5),
                "scalar_repeated_avg_us": summary.group(6),
                "scalar_lane_avg_us": summary.group(8),
                "speedup_vs_scalar_repeated": summary.group(9),
            }
        )
    return row


def fnum(row: Dict[str, str], field: str) -> float:
    try:
        return float(row.get(field, ""))
    except ValueError:
        return 0.0


def build_rows(full_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    kernel_text = read_text(OUT_DIR / "kernel_run.log")
    target_text = read_text(OUT_DIR / "target_run.log")
    makefile_text = read_text(ROOT / "src" / "mosfhet" / "Makefile.def")
    pvw_text = read_text(ROOT / "src" / "mosfhet" / "src" / "pvwtmlwe.c")
    polynomial_text = read_text(ROOT / "src" / "mosfhet" / "src" / "polynomial.c")

    wrapper = next((row for row in full_rows if row["variant"] == "wrapper"), {})
    backend = next((row for row in full_rows if row["variant"] == "backend"), {})
    wrapper_pvw = fnum(wrapper, "pvw_avg_us")
    backend_pvw = fnum(backend, "pvw_avg_us")
    backend_vs_wrapper = wrapper_pvw / backend_pvw if backend_pvw > 0 else 0.0

    kernel_pass = has_all(
        kernel_text,
        [
            "SAB_PVW isolated CMUX/NCMUX lane equivalence r=1: Pass",
            "SAB_PVW isolated CMUX/NCMUX lane equivalence r=2: Pass",
            "SAB_PVW isolated CMUX/NCMUX lane equivalence r=4: Pass",
            "SAB_PVW_KERNEL_TEST skip small-N sparse/bootstrap r=4 backend=spqlios_avx512",
            "MAT_TRGSW/PVW staged kernel test: Pass",
        ],
    )
    target_pass = "SAB_PVW target full bootstrap gate: Pass" in target_text
    explicit_flag = has_all(
        makefile_text + "\n" + pvw_text + "\n" + polynomial_text,
        [
            "SAB_PVW_BACKEND_FROM_DFT_ADD",
            "polynomial_DFT_to_torus_add",
            "execute_direct_torus64_add",
        ],
    )
    full_sab_pass = (
        wrapper.get("status") == "Pass"
        and backend.get("status") == "Pass"
        and backend_vs_wrapper > 1.0
    )

    decision = (
        "PASS_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT_PROMOTION_CANDIDATE"
        if explicit_flag and kernel_pass and target_pass and full_sab_pass
        else "FAIL_STAGE87_H14_BACKEND_FROM_DFT_ADD_PREFLIGHT"
    )
    next_action = (
        "Open Stage88 repeated/noise/resource gates before promotion."
        if decision.startswith("PASS")
        else "Fix failed Stage87 gates before running repeated benchmarks."
    )

    return [
        {
            "gate": "stage87_explicit_flag",
            "status": "PASS_EXPLICIT_FLAG" if explicit_flag else "FAIL_MISSING_FLAG",
            "metric": "flag",
            "value": "SAB_PVW_BACKEND_FROM_DFT_ADD",
            "evidence": "src/mosfhet/Makefile.def; src/mosfhet/src/pvwtmlwe.c; src/mosfhet/src/polynomial.c",
            "detail": "Backend FromDFT-add path is behind an explicit opt-in flag.",
            "next_action": "Keep scalar and default PVW paths unchanged.",
        },
        {
            "gate": "stage87_correctness_smoke",
            "status": "PASS" if kernel_pass and target_pass else "FAIL",
            "metric": "kernel;target",
            "value": f"{kernel_pass};{target_pass}",
            "evidence": "repro/stage87_h14_backend_from_dft_add_preflight/kernel_run.log; repro/stage87_h14_backend_from_dft_add_preflight/target_run.log",
            "detail": "Small staged gate and target full-output correctness gate pass."
            if kernel_pass and target_pass
            else "Correctness smoke did not pass.",
            "next_action": "Do not run performance gates until correctness passes.",
        },
        {
            "gate": "stage87_full_sab_smoke",
            "status": "PASS_FULL_SAB_POSITIVE" if full_sab_pass else "FAIL_OR_NEUTRAL",
            "metric": "backend_vs_wrapper_latency",
            "value": f"{backend_vs_wrapper:.6f}",
            "evidence": OUT_FULL_SAB.relative_to(ROOT).as_posix(),
            "detail": (
                f"Backend-add r=6 one-run PVW latency {backend_pvw:.3f} us versus "
                f"wrapper {wrapper_pvw:.3f} us."
            ),
            "next_action": "Treat as one-run smoke only; require repeated A/B, noise, and resource gates.",
        },
        {
            "gate": "stage87_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": OUT_SUMMARY.relative_to(ROOT).as_posix(),
            "detail": "Stage87 records H14-C1 as a promotion candidate, not a promoted/default path."
            if decision.startswith("PASS")
            else "Stage87 did not produce a promotion candidate.",
            "next_action": next_action,
        },
    ]


def write_md(summary_rows: List[Dict[str, str]], full_rows: List[Dict[str, str]]) -> None:
    decision = summary_rows[-1]["status"]
    lines = [
        "# Stage87 H14 Backend FromDFT-Add Preflight Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage87 implements the Stage86-selected H14-C1 backend materialization",
        "preflight behind `SAB_PVW_BACKEND_FROM_DFT_ADD`. It compares the new",
        "backend-level output conversion plus addend path against the existing",
        "wrapper-level `pvmtmlwe_from_DFT_add` path under the same SAB flags.",
        "",
        "## Full SAB Smoke",
        "",
        "| variant | r | status | PVW us | scalar repeated us | speedup vs scalar | source |",
        "|---|---:|---|---:|---:|---:|---|",
    ]
    for item in full_rows:
        lines.append(
            f"| {item['variant']} | {item['r']} | {item['status']} | "
            f"{item['pvw_avg_us']} | {item['scalar_repeated_avg_us']} | "
            f"{item['speedup_vs_scalar_repeated']} | {item['source_log']} |"
        )

    lines.extend(
        [
            "",
            "## Gates",
            "",
            "| gate | status | metric | value | evidence | detail |",
            "|---|---|---|---:|---|---|",
        ]
    )
    for item in summary_rows:
        lines.append(
            f"| {item['gate']} | {item['status']} | {item['metric']} | "
            f"{item['value']} | {item['evidence']} | {item['detail']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{decision}`.",
            "",
            "This is still one-run smoke evidence. It does not promote the flag,",
            "does not change scalar SAB, and does not justify a final bootstrapping",
            "speedup claim until Stage88 repeated/noise/resource gates pass.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    full_rows = [
        parse_bench(OUT_DIR / "full_sab_wrapper_r6" / "run_0.log", "wrapper"),
        parse_bench(OUT_DIR / "full_sab_backend_r6" / "run_0.log", "backend"),
    ]
    summary_rows = build_rows(full_rows)
    write_csv(OUT_FULL_SAB, full_rows)
    write_csv(OUT_SUMMARY, summary_rows)
    write_md(summary_rows, full_rows)
    print(f"Stage87 H14 backend FromDFT-add preflight: {summary_rows[-1]['status']}")


if __name__ == "__main__":
    main()
