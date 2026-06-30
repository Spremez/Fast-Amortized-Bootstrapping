#!/usr/bin/env python3
"""Build Stage102 verified source-anchor review for the 2025/686 paper."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage102_686_source_anchor_review"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_MATRIX = OUT_DIR / "review_matrix.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage102_686_source_anchor_review_log.md"
STAGE38_CHECKLIST = ROOT / "repro" / "stage38_fulltext_review_gate" / "review_checklist.csv"
STAGE100 = ROOT / "repro" / "stage100_fulltext_anchor_prefill" / "summary.csv"
EXTERNAL = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"


REVIEW_ROWS: List[Dict[str, str]] = [
    {
        "review_item": "FAB_PROTOCOL_STAGES",
        "status": "REVIEWED_SOURCE_ANCHORS_VERIFIED",
        "paper_anchor": "2025/686 pp.5-6 Sec.1.2 contributions/MPmul; p.10 Sec.2.2 test vectors/extraction; p.12 Algorithm 1 and Lemma 3.1; p.13 Algorithm 2 bin-SAB; pp.14-15 binary proof and Algorithm 3 tern-SAB; pp.16-17 Algorithm 4 general sparse SAB; p.18 Sec.5/Algorithm 5 packing key switching; pp.20-21 Algorithm 6 functional bootstrapping, Lemma 6.1, Corollary 6.2",
        "verified_scope": "Protocol mapping anchors the scalar 2025/686 SAB path used by this project.",
        "claim_limit": "This does not by itself validate PVW/MAT as part of the original paper; PVW/MAT remains the local implementation delta.",
    },
    {
        "review_item": "FAB_COMPLEXITY_MODEL",
        "status": "REVIEWED_SOURCE_ANCHORS_VERIFIED",
        "paper_anchor": "2025/686 p.6 states the external-product complexity form for sparse bootstrapping; p.14 gives bin-SAB/MPmul external-product complexity; p.21 gives Algorithm 6 complexity and amortized per-message form in Corollary 6.2",
        "verified_scope": "The local cost model may map its counted CMUX/external-product calls to the paper's scalar external-product schedule.",
        "claim_limit": "The local PVW/MAT batching changes throughput constants and lane batching, not the paper's asymptotic SAB theorem.",
    },
    {
        "review_item": "FAB_CORRECTNESS_NOISE",
        "status": "REVIEWED_SOURCE_ANCHORS_VERIFIED",
        "paper_anchor": "2025/686 p.12 Lemma 3.1 MPmul noise; p.14 Algorithm 2 correctness/noise proof text; p.21 Lemma 6.1 functional bootstrapping noise and extraction statement; p.33 Appendix B average-case external-product/CMUX noise analysis",
        "verified_scope": "Correctness/noise claims for this project must remain tied to local scalar-vs-PVW gates and seed sweeps, with paper anchors used for the scalar SAB protocol rationale.",
        "claim_limit": "Do not cite these anchors as proving the local PVW/MAT path unless local equivalence/noise evidence is cited alongside them.",
    },
    {
        "review_item": "FAB_PARAMETER_SECURITY",
        "status": "REVIEWED_SOURCE_ANCHORS_VERIFIED",
        "paper_anchor": "2025/686 p.22 Sec.6.2 parameter/security discussion; p.23 Table 3 repacking/bootstrapping parameters and security-level method; p.24 Table 4 binary/ternary parameters with q=2^64 and rejection-sampling adjustment; pp.27-28 arbitrary sparse-secret comparison",
        "verified_scope": "Parameter/security citations are valid for the paper's stated parameterization and supported branches.",
        "claim_limit": "Local experiments currently support binary target and selected added binary parameters; non-binary and all-parameter claims remain separately gated.",
    },
    {
        "review_item": "PVW_SAB_DELTA",
        "status": "REVIEWED_SOURCE_ANCHORS_VERIFIED",
        "paper_anchor": "Base scalar anchors: 2025/686 pp.5-6 external products/MPmul, p.12 Algorithm 1, p.13 Algorithm 2, p.18 CMUX/packing KS, pp.20-21 Algorithm 6/extract. Local delta: `sab_pvw_*` shared-mask MAT/PVW multi-body batching and explicit-lane PVW/MAT external products in this repository.",
        "verified_scope": "The implementation delta is replacing repeated scalar external-product/CMUX work across independent lanes with a shared-mask PVW/MAT multi-body path while preserving the scalar SAB schedule as reference.",
        "claim_limit": "This is a local algorithm-engineering delta over the 2025/686 implementation path, not a statement that 2025/686 originally proposed PVW/MAT batching.",
    },
    {
        "review_item": "NOVELTY_BOUNDARY",
        "status": "REVIEWED_SOURCE_ANCHORS_VERIFIED",
        "paper_anchor": "2025/686 pp.3,5,7,28 contributions/comparison and pp.29-32 references; Stage103 related-work matrix for post-paper and adjacent work.",
        "verified_scope": "The safe contribution boundary is a scoped PVW/MAT-SAB systems optimization with measured complete-SAB throughput gains.",
        "claim_limit": "Broad novelty for shared-mask batching, SIMD bootstrapping, amortized bootstrapping, or new SAB asymptotics is not supported by this review.",
    },
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
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


def status(path: Path, key: str, value: str, field: str = "status") -> str:
    for row in read_csv(path):
        if row.get(key) == value:
            return row.get(field, "MISSING")
    return "MISSING"


def update_stage38_checklist() -> None:
    existing = read_csv(STAGE38_CHECKLIST)
    by_item = {row["review_item"]: row for row in REVIEW_ROWS}
    updated: List[Dict[str, str]] = []
    for row in existing:
        item = row.get("review_item", "")
        review = by_item.get(item)
        if review:
            row["status"] = review["status"]
            row["paper_anchor"] = review["paper_anchor"]
            row["notes"] = (
                f"Stage102 verified source anchors. {review['verified_scope']} Claim limit: {review['claim_limit']}"
            )
        updated.append(row)
    if updated:
        write_csv(
            STAGE38_CHECKLIST,
            updated,
            ["review_item", "required_evidence", "status", "paper_anchor", "notes"],
        )


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
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


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def upsert_run_log() -> None:
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
    rows = read_csv(RUN_LOG)
    rows = [row for row in rows if row.get("run_id") != "stage102-686-source-anchor-review-001"]
    rows.append(
        {
            "run_id": "stage102-686-source-anchor-review-001",
            "date": "2026-06-30",
            "commit_or_state": f"working-tree-after-{git_head()}",
            "stage": "Stage 102",
            "backend": "n/a",
            "command": "python scripts/build_stage102_686_source_anchor_review.py",
            "params": "registered 2025/686 full-text artifact; Stage100 candidate anchors; manual source-anchor review",
            "seed": "source-review",
            "status": "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED",
            "summary": "All six Stage38 2025/686 review rows are replaced with verified page/section anchors and explicit claim limits. The review supports scoped protocol citations but not broad novelty or theorem-level PVW/MAT claims.",
            "artifacts": "docs/stage102_686_source_anchor_review_log.md; experiments/stage102_686_source_anchor_review_plan.md; scripts/build_stage102_686_source_anchor_review.py; repro/stage102_686_source_anchor_review/summary.csv; repro/stage102_686_source_anchor_review/review_matrix.csv; repro/stage102_686_source_anchor_review/artifact_index.csv; repro/stage38_fulltext_review_gate/review_checklist.csv",
        }
    )
    write_csv(RUN_LOG, rows, fields)


def write_md(summary_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage102 2025/686 Source-Anchor Review Log",
        "",
        "Date: 2026-06-30",
        "",
        "## Purpose",
        "",
        "Stage102 turns the Stage100 candidate page hints into reviewed source",
        "anchors for the 2025/686 paper. It records page/section-level anchors",
        "and claim limits without storing full paper text.",
        "",
        "## Summary",
        "",
        "| gate | status | detail |",
        "|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(f"| {row['gate']} | {row['status']} | {row['detail']} |")
    lines.extend(["", "## Reviewed Anchors", "", "| item | status | anchor | claim limit |", "|---|---|---|---|"])
    for row in REVIEW_ROWS:
        lines.append(
            f"| {row['review_item']} | {row['status']} | {row['paper_anchor']} | {row['claim_limit']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "CB7 is resolved for scoped source-anchor use: theorem, algorithm,",
            "complexity, parameter, and protocol citations can be grounded in the",
            "listed paper anchors. Broad novelty and PVW/MAT theorem claims remain",
            "bounded by Stage103 and by local experimental evidence.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    fulltext_status = status(EXTERNAL, "evidence_id", "fab686_fulltext")
    stage100_decision = status(STAGE100, "gate", "stage100_decision")
    all_reviewed = all(row["status"] == "REVIEWED_SOURCE_ANCHORS_VERIFIED" for row in REVIEW_ROWS)

    update_stage38_checklist()
    write_csv(
        OUT_MATRIX,
        REVIEW_ROWS,
        ["review_item", "status", "paper_anchor", "verified_scope", "claim_limit"],
    )

    summary_rows = [
        {
            "gate": "stage102_fulltext_precondition",
            "status": "PASS" if fulltext_status == "AVAILABLE_UNREVIEWED" else "FAIL",
            "evidence": rel(EXTERNAL),
            "detail": f"fab686_fulltext={fulltext_status}",
            "next_action": "Register a valid 2025/686 full text before source-anchor review.",
        },
        {
            "gate": "stage102_candidate_precondition",
            "status": "PASS"
            if stage100_decision == "PASS_STAGE100_FULLTEXT_ANCHOR_PREFILL_REVIEW_REQUIRED"
            else "FAIL",
            "evidence": rel(STAGE100),
            "detail": f"stage100_decision={stage100_decision}",
            "next_action": "Run Stage100 candidate anchor prefill before Stage102.",
        },
        {
            "gate": "stage102_review_matrix",
            "status": "PASS" if all_reviewed else "FAIL",
            "evidence": rel(OUT_MATRIX),
            "detail": f"reviewed_rows={len(REVIEW_ROWS)}",
            "next_action": "Fill any missing reviewed anchors before citing paper-specific details.",
        },
        {
            "gate": "stage102_stage38_update",
            "status": "PASS"
            if all(row.get("status") == "REVIEWED_SOURCE_ANCHORS_VERIFIED" for row in read_csv(STAGE38_CHECKLIST))
            else "FAIL",
            "evidence": rel(STAGE38_CHECKLIST),
            "detail": "Stage38 checklist rows now carry verified source anchors.",
            "next_action": "Do not upgrade CB7 if any checklist row remains candidate-only.",
        },
        {
            "gate": "stage102_decision",
            "status": "PASS_STAGE102_686_SOURCE_ANCHORS_REVIEWED"
            if fulltext_status == "AVAILABLE_UNREVIEWED" and all_reviewed
            else "FAIL_STAGE102_686_SOURCE_ANCHORS",
            "evidence": rel(OUT_SUMMARY),
            "detail": "CB7 source-anchor review is complete for scoped 2025/686 citations.",
            "next_action": "Use Stage103 for novelty boundaries before manuscript-level contribution claims.",
        },
    ]

    write_csv(
        OUT_SUMMARY,
        summary_rows,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_md(summary_rows)
    write_csv(
        OUT_INDEX,
        artifact_index([OUT_SUMMARY, OUT_MATRIX, OUT_MD, STAGE38_CHECKLIST]),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    upsert_run_log()
    decision = summary_rows[-1]["status"]
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_MATRIX)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage102 source-anchor review: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
