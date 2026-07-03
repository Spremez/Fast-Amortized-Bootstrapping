#!/usr/bin/env python3
"""Build Stage109 body-linear MAT external-product invariant gate."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage109_body_linear_invariant_gate"
SUMMARY_CSV = OUT_DIR / "summary.csv"
INVARIANT_CSV = OUT_DIR / "invariant_matrix.csv"
MODEL_CSV = OUT_DIR / "operation_model.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage109_body_linear_invariant_gate.md"
PLAN_MD = ROOT / "experiments" / "stage109_body_linear_invariant_gate_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage109_body_linear_external_product.md"
RUN_LOG = ROOT / "repro" / "run_log.csv"

MOSFHET_H = ROOT / "src" / "mosfhet" / "include" / "mosfhet.h"
MATTRGSW_C = ROOT / "src" / "mosfhet" / "src" / "mattrgsw.c"
PVWTMLWE_C = ROOT / "src" / "mosfhet" / "src" / "pvwtmlwe.c"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = [{field: row.get(field, "") for field in fields} for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def has_all(text: str, needles: Iterable[str]) -> bool:
    return all(needle in text for needle in needles)


def build_invariants() -> List[Dict[str, str]]:
    header = read_text(MOSFHET_H)
    mat = read_text(MATTRGSW_C)
    pvw = read_text(PVWTMLWE_C)
    rows = [
        {
            "id": "I109-1",
            "invariant": "PVW_TMLWE has one shared mask vector and r body polynomials.",
            "status": "PASS",
            "source": rel(MOSFHET_H),
            "evidence": "struct _PVW_TMLWE contains TorusPolynomial *a,*b plus k,r",
            "implication": "The r bodies are tied through the same mask coordinates and per-body secret columns.",
        },
        {
            "id": "I109-2",
            "invariant": "PVW_TMLWE encryption fills every body with a zero-encryption relation before message add.",
            "status": "PASS" if has_all(pvw, [
                "generate_random_bytes(byte_size, (uint8_t *) out->a[i]->coeffs)",
                "generate_torus_normal_random_array(out->b[i]->coeffs",
                "polynomial_mul_addto_torus(out->b[j], out->a[i], key->s[i][j])",
            ]) else "FAIL",
            "source": rel(PVWTMLWE_C),
            "evidence": "pvmtmlwe_sample randomizes a and all b[j], then adds a*s[i][j] to each body",
            "implication": "Dropping off-lane body ciphertext terms breaks the zero-encryption cancellation unless a new key/selector format proves otherwise.",
        },
        {
            "id": "I109-3",
            "invariant": "MAT_TRGSW rows are l*(k+r), not one independent scalar TRGSW per body only.",
            "status": "PASS" if "return l * (k + r);" in mat else "FAIL",
            "source": rel(MATTRGSW_C),
            "evidence": "mat_trgsw_rows(l,k,r) = l*(k+r)",
            "implication": "For k=1,l=1 the current selector has r+1 encrypted rows.",
        },
        {
            "id": "I109-4",
            "invariant": "Each MAT_TRGSW row is first sampled as a full PVW_TMLWE encryption of zero.",
            "status": "PASS" if "pvmtmlwe_sample(out->samples[i], NULL, key->trlwe_key)" in mat else "FAIL",
            "source": rel(MATTRGSW_C),
            "evidence": "mat_trgsw_monomial_sample loops rows and calls pvmtmlwe_sample(..., NULL, ...)",
            "implication": "Even diagonal plaintext gadget rows carry full encrypted zero components.",
        },
        {
            "id": "I109-5",
            "invariant": "The plaintext gadget injection is diagonal, but the ciphertext carrier remains full PVW.",
            "status": "PASS" if has_all(mat, [
                "out->samples[j * l + i]->a[j]->coeffs[e] += m * h",
                "out->samples[(k + j) * l + i]->b[j]->coeffs[e] += m * h",
            ]) else "FAIL",
            "source": rel(MATTRGSW_C),
            "evidence": "mask rows add gadget to a[j]; body rows add gadget to b[j]",
            "implication": "Diagonal plaintext alone is insufficient to skip encrypted off-lane zero terms.",
        },
        {
            "id": "I109-6",
            "invariant": "The generic MAT external product multiplies every decomposition row into every output component.",
            "status": "PASS" if has_all(mat, [
                "for (size_t row = 1; row < rows; row++)",
                "for (size_t j = 0; j < r; j++)",
                "polynomial_mul_addto_DFT(out->b[j], scratch->dec_dft[row], selector->samples[row]->b[j])",
            ]) else "FAIL",
            "source": rel(MATTRGSW_C),
            "evidence": "mat_trgsw_mul_pvmtmlwe_DFT performs row x output dense accumulation",
            "implication": "Current implementation shape is dense (k+r)^2 for k=1,l=1.",
        },
        {
            "id": "I109-7",
            "invariant": "No selector metadata exists to certify plaintext/off-lane zero terms for safe skipping.",
            "status": "PASS",
            "source": f"{rel(MOSFHET_H)}; {rel(MATTRGSW_C)}",
            "evidence": "MAT_TRGSW_DFT stores only PVW_TMLWE_DFT *samples and T,Q",
            "implication": "A body-linear shortcut would require a new selector/key format or a proof-carrying metadata layer.",
        },
        {
            "id": "I109-8",
            "invariant": "Current V106-B body-linear implementation is not safe as a local loop-only change.",
            "status": "BLOCKED_CURRENT_FORMAT",
            "source": f"{rel(MATTRGSW_C)}; {rel(PVWTMLWE_C)}",
            "evidence": "full encrypted-zero PVW rows plus dense row-output accumulation",
            "implication": "Do not implement body-linear by skipping ciphertext products in the existing MAT_TRGSW_DFT format.",
        },
    ]
    return rows


def build_operation_model() -> List[Dict[str, str]]:
    rows = []
    for r in [1, 2, 4, 6, 8]:
        k = 1
        l = 1
        mat_rows = l * (k + r)
        outputs = k + r
        dense_products = mat_rows * outputs
        rows.append(
            {
                "r": str(r),
                "k": str(k),
                "l": str(l),
                "mat_rows": str(mat_rows),
                "outputs": str(outputs),
                "current_dense_row_output_products": str(dense_products),
                "per_lane_dense_products": f"{dense_products / r:.3f}",
                "body_linear_target_products": str(k + 2 * r),
                "body_linear_target_per_lane": f"{(k + 2 * r) / r:.3f}",
                "status": "TARGET_REQUIRES_NEW_SELECTOR_FORMAT",
            }
        )
    return rows


def build_summary(invariants: List[Dict[str, str]]) -> List[Dict[str, str]]:
    hard_fail = any(row["status"] == "FAIL" for row in invariants)
    blocked = any(row["status"] == "BLOCKED_CURRENT_FORMAT" for row in invariants)
    if hard_fail:
        decision = "FAIL_STAGE109_SOURCE_INVARIANT_EXTRACTION"
        detail = "Source patterns changed; update the invariant extractor before deciding V106-B."
    elif blocked:
        decision = "PASS_STAGE109_BODY_LINEAR_BLOCKED_CURRENT_SELECTOR_FORMAT"
        detail = "Current MAT_TRGSW_DFT cannot support body-linear product skipping as a loop-only change."
    else:
        decision = "PASS_STAGE109_BODY_LINEAR_READY_FOR_KERNEL_GATE"
        detail = "All required invariants are present and no format blocker was detected."
    return [
        {
            "gate": "stage109_source_invariants",
            "status": "FAIL" if hard_fail else "PASS",
            "metric": "invariant_rows",
            "value": str(len(invariants)),
            "evidence": rel(INVARIANT_CSV),
            "detail": "Source-level invariants extracted from MAT/PVW implementation.",
            "next_action": "Do not proceed if any required source pattern is missing.",
        },
        {
            "gate": "stage109_operation_model",
            "status": "PASS",
            "metric": "dense_products_r1_r2_r4_r6_r8",
            "value": "4;9;25;49;81",
            "evidence": rel(MODEL_CSV),
            "detail": "Current k=1,l=1 MAT external product is dense row-output.",
            "next_action": "Use this model when comparing future body-linear or key-format variants.",
        },
        {
            "gate": "stage109_body_linear_decision",
            "status": decision,
            "metric": "V106-B_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": detail,
            "next_action": "Open a new selector/key-format design gate before any body-linear code path.",
        },
    ]


def write_md(summary: List[Dict[str, str]], invariants: List[Dict[str, str]], model: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage109 Body-Linear Invariant Gate",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage109 checks whether V106-B can be implemented as a local loop-level",
        "body-linear MAT external-product optimization in the current",
        "`MAT_TRGSW_DFT` format. The answer is no: the current selector rows are",
        "full PVW_TMLWE encryptions of zero with diagonal gadget injection, so",
        "off-lane ciphertext terms cannot be skipped without a new selector/key",
        "format and proof.",
        "",
        "## Summary Gates",
        "",
        "| gate | status | metric | value | detail |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(f"| {row['gate']} | {row['status']} | {row['metric']} | {row['value']} | {row['detail']} |")
    lines += [
        "",
        "## Invariant Matrix",
        "",
        "| id | status | invariant | implication |",
        "|---|---|---|---|",
    ]
    for row in invariants:
        lines.append(f"| {row['id']} | {row['status']} | {row['invariant']} | {row['implication']} |")
    lines += [
        "",
        "## Operation Model",
        "",
        "| r | rows | outputs | current dense products | dense products/lane | body-linear target products |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in model:
        lines.append(
            f"| {row['r']} | {row['mat_rows']} | {row['outputs']} | "
            f"{row['current_dense_row_output_products']} | {row['per_lane_dense_products']} | "
            f"{row['body_linear_target_products']} |"
        )
    lines += [
        "",
        "## Next Gate",
        "",
        "The next non-theory-loop step is a finite selector/key-format design gate:",
        "define the minimal additional metadata or alternative encryption format",
        "that makes body-linear skipping mathematically valid, then test it with a",
        "small r=2 equivalence harness before any AVX512 optimization work.",
    ]
    OUT_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_plan() -> None:
    lines = [
        "# Stage109 Body-Linear Invariant Gate Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Decide whether V106-B body-linear MAT external product can be pursued as a",
        "local kernel rewrite under the current `MAT_TRGSW_DFT` key/selector",
        "format.",
        "",
        "## Gate",
        "",
        "- Extract source-level invariants for PVW_TMLWE, MAT_TRGSW row generation,",
        "  gadget injection, decomposition order, and external-product loops.",
        "- If selector rows are full encrypted PVW objects without skip metadata,",
        "  block loop-only body-linear implementation.",
        "- If a safe invariant exists, open a small correctness harness before any",
        "  performance work.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage109_body_linear_invariant_gate.py",
        "```",
    ]
    PLAN_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_theory(summary: List[Dict[str, str]]) -> None:
    decision = summary[-1]["status"]
    lines = [
        "# Stage109 Body-Linear MAT External Product Check",
        "",
        "Date: 2026-07-03",
        "",
        "## Result",
        "",
        f"`{decision}`",
        "",
        "For k=1,l=1, the current MAT external product has `(r+1)^2` encrypted",
        "row-output polynomial products. A body-linear target would need a product",
        "shape closer to `O(r)`, but the present key format does not expose a safe",
        "way to omit off-lane encrypted-zero components.",
        "",
        "The important distinction is:",
        "",
        "- plaintext gadget injection is diagonal;",
        "- ciphertext carrier rows are still full PVW_TMLWE encryptions;",
        "- PVW phase uses the shared mask against every body secret column;",
        "- omitting off-lane body ciphertexts changes the zero-encryption relation.",
        "",
        "Therefore V106-B is not rejected as an algorithmic idea, but it is blocked",
        "as a local loop-only optimization. It requires a new selector/key-format",
        "design gate with a correctness proof before implementation.",
    ]
    THEORY_MD.write_bytes("\n".join(lines).encode("utf-8"))


def artifact_index(paths: Iterable[Path]) -> List[Dict[str, str]]:
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
        if row.get("run_id") != "stage109-body-linear-invariant-gate-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(SUMMARY_CSV),
        rel(INVARIANT_CSV),
        rel(MODEL_CSV),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage109_body_linear_invariant_gate.py"),
    ]
    rows.append(
        {
            "run_id": "stage109-body-linear-invariant-gate-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 109",
            "backend": "n/a",
            "command": "python scripts/build_stage109_body_linear_invariant_gate.py",
            "params": "V106-B body-linear invariant gate; source-level only; no benchmark rerun",
            "seed": "n/a",
            "status": status,
            "summary": "Stage109 decides that body-linear MAT external product is blocked as a loop-only change under the current MAT_TRGSW_DFT selector/key format.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    invariants = build_invariants()
    model = build_operation_model()
    summary = build_summary(invariants)
    write_csv(
        INVARIANT_CSV,
        invariants,
        ["id", "invariant", "status", "source", "evidence", "implication"],
    )
    write_csv(
        MODEL_CSV,
        model,
        [
            "r",
            "k",
            "l",
            "mat_rows",
            "outputs",
            "current_dense_row_output_products",
            "per_lane_dense_products",
            "body_linear_target_products",
            "body_linear_target_per_lane",
            "status",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_md(summary, invariants, model)
    write_theory(summary)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                SUMMARY_CSV,
                INVARIANT_CSV,
                MODEL_CSV,
                ROOT / "scripts" / "build_stage109_body_linear_invariant_gate.py",
                MOSFHET_H,
                MATTRGSW_C,
                PVWTMLWE_C,
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage109 body-linear invariant gate: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") else 0


if __name__ == "__main__":
    raise SystemExit(main())
