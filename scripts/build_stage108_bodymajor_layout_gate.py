#!/usr/bin/env python3
"""Build Stage108 body-major layout gate report."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage108_bodymajor_layout_gate"
TILE4_LOG = OUT_DIR / "tile4.log"
FULLTILE_LOG = OUT_DIR / "fulltile.log"
BODYMAJOR_LOG = OUT_DIR / "bodymajor.log"
FULL_TILE4_R6 = OUT_DIR / "full_sab_tile4_r6" / "summary.csv"
FULL_BODY_R6 = OUT_DIR / "full_sab_bodymajor_r6" / "summary.csv"
SUMMARY_CSV = OUT_DIR / "summary.csv"
KERNEL_CSV = OUT_DIR / "kernel_comparison.csv"
FULL_SAB_CSV = OUT_DIR / "full_sab_smoke.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage108_bodymajor_layout_gate.md"
PLAN_MD = ROOT / "experiments" / "stage108_bodymajor_layout_gate_plan.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def fnum(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "") or 0.0)
    except ValueError:
        return 0.0


def token_values(line: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for token in line.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        out[key] = value.rstrip("x")
    return out


def parse_kernel_log(path: Path, variant: str) -> Tuple[bool, List[Dict[str, str]]]:
    if not path.exists():
        return False, []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    correctness = any("MAT_TRGSW/PVW r>4 kernel test: Pass" in line for line in lines)
    rows: List[Dict[str, str]] = []
    for line in lines:
        values = token_values(line)
        if line.startswith("MAT_TRGSW vs scalar"):
            rows.append(
                {
                    "variant": variant,
                    "bench": "dft_output",
                    "r": values.get("r", ""),
                    "scalar_repeated_avg_us": values.get("scalar_repeated_avg_us", ""),
                    "mat_avg_us": values.get("mat_avg_us", ""),
                    "speedup_vs_scalar_repeated": values.get("speedup_vs_scalar_repeated", ""),
                    "source_log": rel(path),
                }
            )
        elif line.startswith("MAT_TRGSW_FULL vs scalar_full"):
            rows.append(
                {
                    "variant": variant,
                    "bench": "full_output",
                    "r": values.get("r", ""),
                    "scalar_repeated_avg_us": values.get("scalar_repeated_avg_us", ""),
                    "mat_avg_us": values.get("mat_avg_us", ""),
                    "speedup_vs_scalar_repeated": values.get("speedup_vs_scalar_repeated", ""),
                    "source_log": rel(path),
                }
            )
    return correctness, rows


def by_key(rows: List[Dict[str, str]], variant: str, bench: str, r: str) -> Dict[str, str]:
    for row in rows:
        if row.get("variant") == variant and row.get("bench") == bench and row.get("r") == r:
            return row
    return {}


def build_kernel_rows(raw_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for bench in ["dft_output", "full_output"]:
        for r in ["6", "8"]:
            tile4 = by_key(raw_rows, "tile4", bench, r)
            fulltile = by_key(raw_rows, "fulltile", bench, r)
            body = by_key(raw_rows, "bodymajor", bench, r)
            tile4_us = fnum(tile4, "mat_avg_us")
            fulltile_us = fnum(fulltile, "mat_avg_us")
            body_us = fnum(body, "mat_avg_us")
            out.append(
                {
                    "bench": bench,
                    "r": r,
                    "tile4_mat_avg_us": f"{tile4_us:.3f}",
                    "fulltile_mat_avg_us": f"{fulltile_us:.3f}",
                    "bodymajor_mat_avg_us": f"{body_us:.3f}",
                    "bodymajor_vs_tile4": f"{tile4_us / body_us:.3f}" if body_us else "0.000",
                    "bodymajor_vs_fulltile": f"{fulltile_us / body_us:.3f}" if body_us else "0.000",
                    "tile4_speedup_vs_scalar": tile4.get("speedup_vs_scalar_repeated", ""),
                    "fulltile_speedup_vs_scalar": fulltile.get("speedup_vs_scalar_repeated", ""),
                    "bodymajor_speedup_vs_scalar": body.get("speedup_vs_scalar_repeated", ""),
                    "tile4_log": tile4.get("source_log", ""),
                    "fulltile_log": fulltile.get("source_log", ""),
                    "bodymajor_log": body.get("source_log", ""),
                }
            )
    return out


def single(path: Path) -> Dict[str, str]:
    rows = read_csv(path)
    return rows[0] if rows else {}


def full_sab_row() -> Dict[str, str]:
    tile4 = single(FULL_TILE4_R6)
    body = single(FULL_BODY_R6)
    tile4_pvw = fnum(tile4, "pvw_avg_us")
    body_pvw = fnum(body, "pvw_avg_us")
    return {
        "r": "6",
        "tile4_status": tile4.get("status", "MISSING"),
        "bodymajor_status": body.get("status", "MISSING"),
        "tile4_pvw_avg_us": f"{tile4_pvw:.3f}",
        "bodymajor_pvw_avg_us": f"{body_pvw:.3f}",
        "bodymajor_vs_tile4": f"{tile4_pvw / body_pvw:.3f}" if body_pvw else "0.000",
        "tile4_speedup_vs_scalar": tile4.get("speedup_vs_scalar_repeated", ""),
        "bodymajor_speedup_vs_scalar": body.get("speedup_vs_scalar_repeated", ""),
        "tile4_evidence": rel(FULL_TILE4_R6) if FULL_TILE4_R6.exists() else "",
        "bodymajor_evidence": rel(FULL_BODY_R6) if FULL_BODY_R6.exists() else "",
    }


def ratio_for(rows: List[Dict[str, str]], bench: str, r: str, key: str) -> float:
    for row in rows:
        if row.get("bench") == bench and row.get("r") == r:
            return fnum(row, key)
    return 0.0


def build_summary(
    tile4_correct: bool,
    fulltile_correct: bool,
    body_correct: bool,
    kernel_rows: List[Dict[str, str]],
    full_row: Dict[str, str],
) -> List[Dict[str, str]]:
    kernel_logs_exist = TILE4_LOG.exists() and FULLTILE_LOG.exists() and BODYMAJOR_LOG.exists()
    body_r6_tile4 = ratio_for(kernel_rows, "full_output", "6", "bodymajor_vs_tile4")
    body_r6_full = ratio_for(kernel_rows, "full_output", "6", "bodymajor_vs_fulltile")
    body_dft_tile4 = ratio_for(kernel_rows, "dft_output", "6", "bodymajor_vs_tile4")
    kernel_positive = body_r6_tile4 > 1.0 and body_r6_full > 1.0 and body_dft_tile4 > 1.0
    full_sab_available = FULL_TILE4_R6.exists() and FULL_BODY_R6.exists()
    full_sab_ratio = fnum(full_row, "bodymajor_vs_tile4")
    full_sab_pass = (
        full_row.get("tile4_status") == "Pass"
        and full_row.get("bodymajor_status") == "Pass"
    )
    rows = [
        {
            "gate": "stage108_inputs_available",
            "status": "PASS" if kernel_logs_exist else "MISSING_KERNEL_LOGS",
            "metric": "tile4;fulltile;bodymajor",
            "value": f"{TILE4_LOG.exists()};{FULLTILE_LOG.exists()};{BODYMAJOR_LOG.exists()}",
            "evidence": f"{rel(TILE4_LOG)}; {rel(FULLTILE_LOG)}; {rel(BODYMAJOR_LOG)}",
            "detail": "All kernel logs are available." if kernel_logs_exist else "One or more kernel logs are missing.",
            "next_action": "Run scripts/run_stage108_bodymajor_layout_gate.sh on the AVX512 performance platform.",
        },
        {
            "gate": "stage108_kernel_correctness",
            "status": "PASS" if tile4_correct and fulltile_correct and body_correct else "FAIL",
            "metric": "tile4;fulltile;bodymajor",
            "value": f"{tile4_correct};{fulltile_correct};{body_correct}",
            "evidence": f"{rel(TILE4_LOG)}; {rel(FULLTILE_LOG)}; {rel(BODYMAJOR_LOG)}",
            "detail": "All r>4 kernel identity gates pass." if tile4_correct and fulltile_correct and body_correct else "A kernel correctness gate failed.",
            "next_action": "Do not interpret timing unless correctness passes.",
        },
        {
            "gate": "stage108_kernel_locality_result",
            "status": "PASS_KERNEL_POSITIVE" if kernel_positive else "NEGATIVE_OR_NEUTRAL_KERNEL",
            "metric": "bodymajor_vs_tile4_full;bodymajor_vs_fulltile_full;bodymajor_vs_tile4_dft",
            "value": f"{body_r6_tile4:.3f};{body_r6_full:.3f};{body_dft_tile4:.3f}",
            "evidence": rel(KERNEL_CSV),
            "detail": "body-major beats tile4/fulltile in kernel microbench." if kernel_positive else "body-major does not beat both existing r=6 kernel layouts.",
            "next_action": "Only run full-SAB promotion gates if kernel-positive or if profile requires a full-SAB sanity check.",
        },
        {
            "gate": "stage108_full_sab_smoke",
            "status": "PASS_FULL_SAB_POSITIVE" if full_sab_available and full_sab_pass and full_sab_ratio > 1.0 else "NEUTRAL_OR_NEGATIVE_FULL_SAB" if full_sab_available and full_sab_pass else "SKIPPED_FULL_SAB",
            "metric": "bodymajor_vs_tile4",
            "value": f"{full_sab_ratio:.3f}",
            "evidence": rel(FULL_SAB_CSV),
            "detail": "body-major complete-SAB smoke beats tile4." if full_sab_available and full_sab_pass and full_sab_ratio > 1.0 else "complete-SAB smoke is missing or not positive.",
            "next_action": "Do not promote without positive complete-SAB T_total/r.",
        },
    ]
    hard_fail = any(row["status"] == "FAIL" for row in rows)
    if hard_fail:
        decision = "FAIL_STAGE108_BODYMAJOR_LAYOUT_GATE"
        detail = "Correctness failed; no performance claim is allowed."
    elif kernel_positive and full_sab_available and full_sab_pass and full_sab_ratio > 1.0:
        decision = "PASS_STAGE108_BODYMAJOR_LAYOUT_POSITIVE_STAGE109_REQUIRED"
        detail = "body-major is a complete-SAB-positive candidate; repeated/noise/resource gates are required."
    elif kernel_positive:
        decision = "PASS_STAGE108_BODYMAJOR_KERNEL_ONLY_NOT_PROMOTED"
        detail = "body-major kernel signal is positive but full-SAB promotion evidence is missing or neutral."
    else:
        decision = "PASS_STAGE108_BODYMAJOR_NEGATIVE_NOT_PROMOTED"
        detail = "body-major layout is correct but not performance-positive versus existing layouts."
    rows.append(
        {
            "gate": "stage108_decision",
            "status": decision,
            "metric": "promotion_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": detail,
            "next_action": "Record this as V106-D evidence and continue with V106-B invariant analysis or another runnable gate.",
        }
    )
    return rows


def write_md(summary: List[Dict[str, str]], kernels: List[Dict[str, str]], full_row: Dict[str, str]) -> None:
    lines = [
        "# Stage108 Body-Major Layout Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage108 implements V106-D as an explicit r=6 body-major MAT external-product",
        "layout experiment behind `MAT_TRGSW_AVX512_R6_BODYMAJOR`. It does not change",
        "scalar/default SAB or the promoted explicit paths.",
        "",
        "## Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['detail']} |")
    lines += [
        "",
        "## Kernel Comparison",
        "",
        "| bench | r | tile4 us | fulltile us | bodymajor us | bodymajor/tile4 | bodymajor/fulltile |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in kernels:
        lines.append(
            f"| {row['bench']} | {row['r']} | {row['tile4_mat_avg_us']} | {row['fulltile_mat_avg_us']} | "
            f"{row['bodymajor_mat_avg_us']} | {row['bodymajor_vs_tile4']} | {row['bodymajor_vs_fulltile']} |"
        )
    lines += [
        "",
        "## Full-SAB Smoke",
        "",
        "| r | tile4 PVW us | bodymajor PVW us | bodymajor/tile4 | tile4 scalar speedup | bodymajor scalar speedup |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {full_row['r']} | {full_row['tile4_pvw_avg_us']} | {full_row['bodymajor_pvw_avg_us']} | "
        f"{full_row['bodymajor_vs_tile4']} | {full_row['tile4_speedup_vs_scalar']} | {full_row['bodymajor_speedup_vs_scalar']} |",
        "",
        "## Interpretation",
        "",
        "This is a falsifiable locality/layout experiment. A kernel-only win is not",
        "enough for a SAB claim; promotion requires complete-SAB `T_total/r`,",
        "correctness/noise, and resource gates.",
        "",
    ]
    OUT_MD.write_bytes("\n".join(lines).encode("utf-8"))


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": rel(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def upsert_run_log(status: str) -> None:
    fields = [
        "run_id",
        "date",
        "commit_or_state",
        "stage",
        "backend",
        "command",
        "params",
        "seed",
        "status",
        "summary",
        "artifacts",
    ]
    rows = [
        row for row in read_csv(RUN_LOG)
        if row.get("run_id") != "stage108-bodymajor-layout-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(ROOT / "scripts" / "run_stage108_bodymajor_layout_gate.sh"),
        rel(ROOT / "scripts" / "build_stage108_bodymajor_layout_gate.py"),
        rel(SUMMARY_CSV),
        rel(KERNEL_CSV),
        rel(FULL_SAB_CSV),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "src" / "mosfhet" / "Makefile.def"),
        rel(ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"),
    ]
    rows.append(
        {
            "run_id": "stage108-bodymajor-layout-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 108",
            "backend": "spqlios_avx512",
            "command": "bash scripts/run_stage108_bodymajor_layout_gate.sh; python scripts/build_stage108_bodymajor_layout_gate.py",
            "params": "MAT_TRGSW_AVX512_R6_BODYMAJOR=true; r=6 layout/locality gate; full-SAB optional",
            "seed": "n/a",
            "status": status,
            "summary": "Stage108 records the V106-D body-major layout experiment behind an explicit flag and compares it with tile4/fulltile under the same r>4 kernel harness.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    tile4_correct, tile4_rows = parse_kernel_log(TILE4_LOG, "tile4")
    fulltile_correct, fulltile_rows = parse_kernel_log(FULLTILE_LOG, "fulltile")
    body_correct, body_rows = parse_kernel_log(BODYMAJOR_LOG, "bodymajor")
    kernel_rows = build_kernel_rows(tile4_rows + fulltile_rows + body_rows)
    full_row = full_sab_row()
    summary = build_summary(tile4_correct, fulltile_correct, body_correct, kernel_rows, full_row)
    write_csv(
        KERNEL_CSV,
        kernel_rows,
        [
            "bench",
            "r",
            "tile4_mat_avg_us",
            "fulltile_mat_avg_us",
            "bodymajor_mat_avg_us",
            "bodymajor_vs_tile4",
            "bodymajor_vs_fulltile",
            "tile4_speedup_vs_scalar",
            "fulltile_speedup_vs_scalar",
            "bodymajor_speedup_vs_scalar",
            "tile4_log",
            "fulltile_log",
            "bodymajor_log",
        ],
    )
    write_csv(
        FULL_SAB_CSV,
        [full_row],
        [
            "r",
            "tile4_status",
            "bodymajor_status",
            "tile4_pvw_avg_us",
            "bodymajor_pvw_avg_us",
            "bodymajor_vs_tile4",
            "tile4_speedup_vs_scalar",
            "bodymajor_speedup_vs_scalar",
            "tile4_evidence",
            "bodymajor_evidence",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_md(summary, kernel_rows, full_row)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                ROOT / "scripts" / "run_stage108_bodymajor_layout_gate.sh",
                ROOT / "scripts" / "build_stage108_bodymajor_layout_gate.py",
                SUMMARY_CSV,
                KERNEL_CSV,
                FULL_SAB_CSV,
                TILE4_LOG,
                FULLTILE_LOG,
                BODYMAJOR_LOG,
                FULL_TILE4_R6,
                FULL_BODY_R6,
                ROOT / "src" / "mosfhet" / "Makefile.def",
                ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    upsert_run_log(summary[-1]["status"])
    print(f"Wrote {rel(SUMMARY_CSV)}")
    print(f"Wrote {rel(KERNEL_CSV)}")
    print(f"Stage108 body-major layout gate: {summary[-1]['status']}")
    return 1 if summary[-1]["status"].startswith("FAIL_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
