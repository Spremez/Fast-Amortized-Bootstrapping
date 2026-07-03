#!/usr/bin/env python3
"""Build Stage114 lane-local multimask resource model."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage114_lane_local_resource_model"
SUMMARY_CSV = OUT_DIR / "summary.csv"
RESOURCE_CSV = OUT_DIR / "resource_model.csv"
ARTIFACT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage114_lane_local_resource_model.md"
PLAN_MD = ROOT / "experiments" / "stage114_lane_local_resource_model_plan.md"
THEORY_MD = ROOT / "theory_checks" / "stage114_lane_local_resource_model.md"
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


def build_resource_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in [2, 4, 6, 8]:
        current_acc = 1 + r
        lane_acc = 2 * r
        acc_ratio = lane_acc / current_acc
        dense_products = (1 + r) * (1 + r)
        lane_products = 1 + 2 * r
        product_ratio = dense_products / lane_products
        current_selector_polys = (1 + r) * (1 + r)
        lane_selector_polys = 2 * (1 + 2 * r)
        selector_ratio = lane_selector_polys / current_selector_polys
        coarse_net = product_ratio / acc_ratio
        rows.append(
            {
                "r": str(r),
                "current_acc_polys": str(current_acc),
                "lane_local_acc_polys": str(lane_acc),
                "accumulator_poly_ratio": f"{acc_ratio:.3f}",
                "current_dense_products": str(dense_products),
                "lane_local_target_products": str(lane_products),
                "raw_product_ratio": f"{product_ratio:.3f}",
                "current_selector_poly_model": str(current_selector_polys),
                "lane_local_selector_poly_model": str(lane_selector_polys),
                "selector_poly_ratio": f"{selector_ratio:.3f}",
                "coarse_product_over_accumulator_ratio": f"{coarse_net:.3f}",
                "status": "RESOURCE_MODEL_NOT_FATAL" if coarse_net > 1.0 else "RESOURCE_MODEL_NEGATIVE",
            }
        )
    return rows


def build_summary(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    all_not_fatal = all(row["status"] == "RESOURCE_MODEL_NOT_FATAL" for row in rows)
    min_net = min(float(row["coarse_product_over_accumulator_ratio"]) for row in rows)
    decision = (
        "PASS_STAGE114_RESOURCE_MODEL_NOT_FATAL_TOY_C_REQUIRED"
        if all_not_fatal
        else "PASS_STAGE114_RESOURCE_MODEL_NEGATIVE_NOT_IMPLEMENTED"
    )
    return [
        {
            "gate": "stage114_resource_rows",
            "status": "PASS",
            "metric": "r_values",
            "value": "2;4;6;8",
            "evidence": rel(RESOURCE_CSV),
            "detail": "Resource model covers r=2,4,6,8.",
            "next_action": "Use only as a symbolic model, not measured memory evidence.",
        },
        {
            "gate": "stage114_accumulator_overhead",
            "status": "PASS_RECORDED",
            "metric": "lane_local/current_acc_polys",
            "value": ";".join(row["accumulator_poly_ratio"] for row in rows),
            "evidence": rel(RESOURCE_CSV),
            "detail": "Lane-local masks increase accumulator polynomial count.",
            "next_action": "A toy C representation must measure actual allocation/RSS.",
        },
        {
            "gate": "stage114_coarse_tradeoff",
            "status": "PASS_NOT_FATAL" if all_not_fatal else "NEGATIVE",
            "metric": "min_product_over_accumulator_ratio",
            "value": f"{min_net:.3f}",
            "evidence": rel(RESOURCE_CSV),
            "detail": "Raw arithmetic gain remains above accumulator polynomial overhead in this symbolic model.",
            "next_action": "Proceed only to toy representation, not hot-path integration.",
        },
        {
            "gate": "stage114_decision",
            "status": decision,
            "metric": "next_gate_policy",
            "value": "",
            "evidence": rel(SUMMARY_CSV),
            "detail": "Resource model does not immediately kill lane-local multimask, but implementation risk remains high.",
            "next_action": "Stage115 should build a small toy C representation or stop this branch.",
        },
    ]


def write_plan() -> None:
    lines = [
        "# Stage114 Lane-Local Resource Model Plan",
        "",
        "Date: 2026-07-03",
        "",
        "## Objective",
        "",
        "Quantify whether the Stage113 lane-local multimask phase-plausible",
        "candidate is immediately killed by accumulator/key-format resource cost.",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/build_stage114_lane_local_resource_model.py",
        "```",
        "",
        "This is a symbolic resource model, not measured RSS or complete-SAB timing.",
    ]
    PLAN_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_theory(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage114 Lane-Local Multimask Resource Model",
        "",
        "Date: 2026-07-03",
        "",
        "The current shared-mask PVW accumulator has `1+r` polynomial components",
        "for k=1. A lane-local multimask accumulator has roughly `2r` components",
        "because each lane needs its own mask/body pair.",
        "",
        "The current dense external product has `(1+r)^2` product terms for",
        "k=1,l=1. The lane-local body-linear target is modeled as `1+2r` terms.",
        "",
        "This model is only a pre-implementation screen. It ignores allocator",
        "behavior, cache effects, noise growth, key switching, and SAB schedule",
        "integration.",
        "",
        "## Symbolic Rows",
        "",
        "| r | accumulator ratio | product ratio | coarse product/acc ratio |",
        "|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['accumulator_poly_ratio']} | "
            f"{row['raw_product_ratio']} | {row['coarse_product_over_accumulator_ratio']} |"
        )
    THEORY_MD.write_bytes("\n".join(lines).encode("utf-8"))


def write_md(summary: List[Dict[str, str]], rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage114 Lane-Local Resource Model",
        "",
        "Date: 2026-07-03",
        "",
        "## Decision",
        "",
        f"`{summary[-1]['status']}`",
        "",
        "Stage114 screens the lane-local multimask candidate before C work. The",
        "symbolic model says the accumulator grows, but the raw product-count",
        "gain is not immediately erased. This is not measured performance.",
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
        "## Resource Model",
        "",
        "| r | current acc polys | lane-local acc polys | acc ratio | dense products | lane products | product ratio | selector ratio | coarse ratio |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['r']} | {row['current_acc_polys']} | {row['lane_local_acc_polys']} | "
            f"{row['accumulator_poly_ratio']} | {row['current_dense_products']} | "
            f"{row['lane_local_target_products']} | {row['raw_product_ratio']} | "
            f"{row['selector_poly_ratio']} | {row['coarse_product_over_accumulator_ratio']} |"
        )
    OUT_MD.write_bytes("\n".join(lines).encode("utf-8"))


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
        if row.get("run_id") != "stage114-lane-local-resource-model-001"
    ]
    artifacts = [
        rel(OUT_MD),
        rel(PLAN_MD),
        rel(THEORY_MD),
        rel(SUMMARY_CSV),
        rel(RESOURCE_CSV),
        rel(ARTIFACT_INDEX),
        rel(ROOT / "scripts" / "build_stage114_lane_local_resource_model.py"),
    ]
    rows.append(
        {
            "run_id": "stage114-lane-local-resource-model-001",
            "date": "2026-07-03",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 114",
            "backend": "n/a",
            "command": "python scripts/build_stage114_lane_local_resource_model.py",
            "params": "lane-local multimask symbolic resource model r=2,4,6,8",
            "seed": "n/a",
            "status": status,
            "summary": "Stage114 screens lane-local multimask resource overhead and routes only to toy representation, not hot-path implementation.",
            "artifacts": "; ".join(artifacts),
        }
    )
    write_csv(RUN_LOG, rows, fields)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_plan()
    rows = build_resource_rows()
    summary = build_summary(rows)
    write_csv(
        RESOURCE_CSV,
        rows,
        [
            "r",
            "current_acc_polys",
            "lane_local_acc_polys",
            "accumulator_poly_ratio",
            "current_dense_products",
            "lane_local_target_products",
            "raw_product_ratio",
            "current_selector_poly_model",
            "lane_local_selector_poly_model",
            "selector_poly_ratio",
            "coarse_product_over_accumulator_ratio",
            "status",
        ],
    )
    write_csv(
        SUMMARY_CSV,
        summary,
        ["gate", "status", "metric", "value", "evidence", "detail", "next_action"],
    )
    write_theory(rows)
    write_md(summary, rows)
    write_csv(
        ARTIFACT_INDEX,
        artifact_index(
            [
                OUT_MD,
                PLAN_MD,
                THEORY_MD,
                SUMMARY_CSV,
                RESOURCE_CSV,
                ROOT / "scripts" / "build_stage114_lane_local_resource_model.py",
            ]
        ),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    status = summary[-1]["status"]
    upsert_run_log(status)
    print(f"Stage114 lane-local resource model: {status}")
    print(f"Wrote {rel(SUMMARY_CSV)}")
    return 1 if status.startswith("FAIL") else 0


if __name__ == "__main__":
    raise SystemExit(main())
