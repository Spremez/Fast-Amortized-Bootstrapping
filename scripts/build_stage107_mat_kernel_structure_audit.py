#!/usr/bin/env python3
"""Build Stage107 MAT kernel structure audit.

This stage prevents theory drift by grounding the next MAT-RLWE SAB step in
the current source structure. It records whether existing AVX512 MAT paths are
body-linear or dense row-output kernels, and chooses the first runnable gate.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage107_mat_kernel_structure_audit"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_KERNELS = OUT_DIR / "kernel_structure.csv"
OUT_NEXT = OUT_DIR / "next_gate.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage107_mat_kernel_structure_audit.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"
SOURCE = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"


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


def source_has(token: str) -> bool:
    return token in SOURCE.read_text(encoding="utf-8")


def dense_terms(r: int) -> int:
    rows = r + 1
    outputs = r + 1
    return rows * outputs


def build_kernel_rows() -> List[Dict[str, str]]:
    configs = [
        ("generic_fallback", "generic", 2, "no flag", "generic row/output loops"),
        ("r2_smallr_avx512", "avx512_smallr", 2, "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED", "manual r=2 specialization"),
        ("r4_smallr_avx512", "avx512_smallr", 4, "MAT_TRGSW_AVX512_SMALLR_SPECIALIZED", "manual r=4 specialization"),
        ("r4_unrolled_rows", "avx512_unrolled", 4, "MAT_TRGSW_AVX512_R4_UNROLLED_ROWS", "row pointers unrolled"),
        ("r6_rgt4_tiled", "avx512_tiled", 6, "MAT_TRGSW_AVX512_RGT4_FUSED", "tile outputs by four"),
        ("r6_fulltile", "avx512_fulltile", 6, "MAT_TRGSW_AVX512_R6_FULLTILE", "full output tile"),
        ("r8_rgt4_tiled", "avx512_tiled", 8, "MAT_TRGSW_AVX512_RGT4_FUSED", "tile outputs by four"),
    ]
    rows: List[Dict[str, str]] = []
    for kernel_id, kind, r, flag, note in configs:
        terms = dense_terms(r)
        token_status = "SOURCE_TOKEN_PRESENT"
        if flag != "no flag" and not source_has(flag):
            token_status = "SOURCE_TOKEN_MISSING"
        rows.append(
            {
                "kernel_id": kernel_id,
                "kind": kind,
                "r": str(r),
                "rows": str(r + 1),
                "outputs": str(r + 1),
                "complex_terms_per_coeff_vector": str(terms),
                "terms_per_lane": f"{terms / r:.6f}",
                "asymptotic_shape": "dense_row_output_O_r2",
                "body_linear": "no",
                "source_flag": flag,
                "source_status": token_status,
                "interpretation": note,
            }
        )
    return rows


def build_next_gate_rows() -> List[Dict[str, str]]:
    return [
        {
            "priority": "P0",
            "gate_id": "G107-D",
            "variant": "V106-D_body_major_coefficient_blocked_layout",
            "why_first": "runnable without changing selector semantics or key format; directly tests load/store locality and T_total/r",
            "required_action": "implement or benchmark a layout-only/body-major coefficient-blocked MAT path behind an explicit flag",
            "correctness_gate": "SAB_PVW_KERNEL_TEST and target full bootstrap equivalence",
            "performance_gate": "kernel C_mat_cmux(r)/r plus complete-SAB T_total/r for r=2/4/6 where available",
            "stop_rule": "if kernel wins but complete SAB T_total/r does not, mark neutral and do not promote",
        },
        {
            "priority": "P1",
            "gate_id": "G107-B",
            "variant": "V106-B_body_linear_mat_external_product",
            "why_first": "needed for theoretical optimality because current kernels remain dense O(r^2)",
            "required_action": "derive selector/key invariants for block/diagonal/body-linear MAT external product before code",
            "correctness_gate": "lane phase equivalence after CMUX, RGSW monomial, sparse_mul, and full bootstrap",
            "performance_gate": "show C_mat_cmux(r)/r improves versus dense kernels and complete SAB improves",
            "stop_rule": "if the required selector/key structure changes security assumptions, block until proof review",
        },
        {
            "priority": "P2",
            "gate_id": "G107-C",
            "variant": "V106-C_dft_lazy_schedule_window",
            "why_first": "secondary schedule/materialization target after the dense-kernel gap is measured",
            "required_action": "carry DFT/materialized state across a bounded CMUX window",
            "correctness_gate": "single-window equivalence before full sparse_mul",
            "performance_gate": "fromDFT/store traffic reduction plus complete-SAB T_total/r",
            "stop_rule": "do not repeat Stage23/Stage87 neutral work unless profile shows materialization is dominant",
        },
    ]


def build_summary(kernel_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    all_dense = all(row["asymptotic_shape"] == "dense_row_output_O_r2" for row in kernel_rows)
    return [
        {
            "gate": "stage107_source_structure_audit",
            "status": "PASS" if all_dense else "REVIEW_REQUIRED",
            "evidence": rel(OUT_KERNELS),
            "detail": "Current MAT kernels are AVX512-specialized/tiled but still dense row-output accumulations.",
            "next_action": "Do not claim body-linear optimality from current kernels.",
        },
        {
            "gate": "stage107_first_runnable_gate",
            "status": "SELECT_V106_D_FIRST_AND_V106_B_THEORY_PARALLEL",
            "evidence": rel(OUT_NEXT),
            "detail": "Run layout/locality gate first because it is runnable without key-format changes; keep body-linear external product as the required optimality path.",
            "next_action": "Start Stage108 with V106-D measurement or code behind an explicit flag.",
        },
        {
            "gate": "stage107_decision",
            "status": "PASS_STAGE107_DENSE_KERNEL_AUDIT_NEXT_GATE_SELECTED",
            "evidence": rel(OUT_SUMMARY),
            "detail": "The current implementation is not theoretical-optimality evidence; next work is a bounded runnable gate.",
            "next_action": "Implement and measure Stage108 V106-D; derive V106-B invariants before code.",
        },
    ]


def write_md(summary: List[Dict[str, str]], kernels: List[Dict[str, str]], next_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage107 MAT Kernel Structure Audit",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "The current MAT external-product implementation contains useful AVX512",
        "specialization and tiling, but the source-level operation structure is",
        "still dense row-output accumulation. For k=1,l=1 it uses `(r+1)`",
        "decomposition rows and `(r+1)` output polynomials, so the hot multiply",
        "structure is `(r+1)^2` complex terms per coefficient vector.",
        "",
        "This is not evidence of body-linear or theoretical optimal MAT-RLWE SAB.",
        "",
        "## Kernel Structure",
        "",
        "| kernel | r | rows | outputs | terms | terms/lane | shape |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in kernels:
        lines.append(
            f"| {row['kernel_id']} | {row['r']} | {row['rows']} | {row['outputs']} | "
            f"{row['complex_terms_per_coeff_vector']} | {row['terms_per_lane']} | "
            f"{row['asymptotic_shape']} |"
        )
    lines += [
        "",
        "## Next Gates",
        "",
        "| priority | gate | variant | required action | stop rule |",
        "|---|---|---|---|---|",
    ]
    for row in next_rows:
        lines.append(
            f"| {row['priority']} | {row['gate_id']} | {row['variant']} | "
            f"{row['required_action']} | {row['stop_rule']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "Stage108 should not start by claiming a new theorem. It should run a",
        "bounded implementation gate first. The selected immediate gate is V106-D",
        "because it can test body-major/coefficient-blocked locality without",
        "changing selector semantics. V106-B remains the required path for true",
        "body-linear optimality, but it needs a selector/key invariant proof before",
        "code.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


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
        if row.get("run_id") != "stage107-mat-kernel-structure-audit-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(OUT_SUMMARY),
        rel(OUT_KERNELS),
        rel(OUT_NEXT),
        rel(OUT_INDEX),
        rel(SOURCE),
    ]
    rows.append(
        {
            "run_id": "stage107-mat-kernel-structure-audit-001",
            "date": "2026-07-03",
            "commit_or_state": git_head(),
            "stage": "Stage 107",
            "backend": "n/a",
            "command": "python scripts/build_stage107_mat_kernel_structure_audit.py",
            "params": "source-level MAT kernel structure audit; no benchmark rerun",
            "seed": "n/a",
            "status": status,
            "summary": "Stage107 records that current MAT AVX512 kernels remain dense row-output accumulations and selects V106-D as the first runnable gate while keeping V106-B as the optimality path.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> None:
    kernels = build_kernel_rows()
    next_rows = build_next_gate_rows()
    summary = build_summary(kernels)
    write_csv(
        OUT_KERNELS,
        kernels,
        [
            "kernel_id",
            "kind",
            "r",
            "rows",
            "outputs",
            "complex_terms_per_coeff_vector",
            "terms_per_lane",
            "asymptotic_shape",
            "body_linear",
            "source_flag",
            "source_status",
            "interpretation",
        ],
    )
    write_csv(
        OUT_NEXT,
        next_rows,
        [
            "priority",
            "gate_id",
            "variant",
            "why_first",
            "required_action",
            "correctness_gate",
            "performance_gate",
            "stop_rule",
        ],
    )
    write_csv(
        OUT_SUMMARY,
        summary,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_md(summary, kernels, next_rows)
    write_csv(
        OUT_INDEX,
        artifact_index(
            [
                OUT_MD,
                OUT_SUMMARY,
                OUT_KERNELS,
                OUT_NEXT,
                OUT_INDEX,
                ROOT / "scripts" / "build_stage107_mat_kernel_structure_audit.py",
                SOURCE,
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    upsert_run_log(summary[-1]["status"])
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_KERNELS)}")
    print(f"Stage107 kernel audit: {summary[-1]['status']}")


if __name__ == "__main__":
    main()
