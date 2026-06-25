#!/usr/bin/env python3
"""Build the Stage 38 full-text artifact gate and review checklist."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "repro" / "stage38_fulltext_review_gate"


REVIEW_ITEMS = [
    (
        "FAB_PROTOCOL_STAGES",
        "Map setup_tv_xb, blind rotation, sparse_mul/RGSW monomial, external product, extract, and KS to page/section evidence.",
    ),
    (
        "FAB_COMPLEXITY_MODEL",
        "Map the h, r_prec, N, and external-product count formulas to paper equations or algorithm text.",
    ),
    (
        "FAB_CORRECTNESS_NOISE",
        "Map correctness/noise theorem assumptions to the implemented parameter and noise gates.",
    ),
    (
        "FAB_PARAMETER_SECURITY",
        "Map parameter-security assumptions and supported branches to the tested binary parameter scope.",
    ),
    (
        "PVW_SAB_DELTA",
        "Identify exactly where PVW/MAT shared-mask multi-body batching changes the base SAB implementation.",
    ),
    (
        "NOVELTY_BOUNDARY",
        "Check whether SAB-specific integration or schedule changes remain novel after base-paper and related-work review.",
    ),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_kind(path: Path) -> str:
    with path.open("rb") as f:
        head = f.read(8)
    if head.startswith(b"%PDF-"):
        return "pdf"
    if path.suffix.lower() in {".txt", ".md", ".tex"}:
        return "text"
    return "unknown"


def rel_or_abs(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_rows(fulltext_path: str | None) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    if not fulltext_path:
        summary = [
            {
                "item": "fulltext_artifact",
                "status": "MISSING",
                "kind": "paper_fulltext",
                "path": "",
                "sha256": "",
                "size_bytes": "",
                "detail": "FAB686_FULLTEXT_PATH was not provided.",
            },
            {
                "item": "stage38_decision",
                "status": "BLOCKED_FULLTEXT_MISSING",
                "kind": "review_gate",
                "path": "",
                "sha256": "",
                "size_bytes": "",
                "detail": "Theorem-level 2025/686 citation and novelty review remain blocked.",
            },
        ]
        checklist_status = "BLOCKED_FULLTEXT_MISSING"
    else:
        path = Path(fulltext_path)
        if not path.exists():
            summary = [
                {
                    "item": "fulltext_artifact",
                    "status": "MISSING",
                    "kind": "paper_fulltext",
                    "path": str(path),
                    "sha256": "",
                    "size_bytes": "",
                    "detail": "Provided FAB686_FULLTEXT_PATH does not exist.",
                },
                {
                    "item": "stage38_decision",
                    "status": "BLOCKED_FULLTEXT_MISSING",
                    "kind": "review_gate",
                    "path": str(path),
                    "sha256": "",
                    "size_bytes": "",
                    "detail": "Theorem-level 2025/686 citation and novelty review remain blocked.",
                },
            ]
            checklist_status = "BLOCKED_FULLTEXT_MISSING"
        else:
            kind = file_kind(path)
            digest = sha256_file(path)
            size = str(path.stat().st_size)
            if kind in {"pdf", "text"}:
                artifact_status = "AVAILABLE_UNREVIEWED"
                decision = "FULLTEXT_AVAILABLE_REVIEW_REQUIRED"
                detail = "Full-text artifact is available; manual claim-to-source review is still required."
                checklist_status = "PENDING_MANUAL_REVIEW"
            else:
                artifact_status = "UNRECOGNIZED_FILE"
                decision = "BLOCKED_UNRECOGNIZED_FULLTEXT"
                detail = "Artifact exists but is not recognized as PDF or text."
                checklist_status = "BLOCKED_UNRECOGNIZED_FULLTEXT"
            summary = [
                {
                    "item": "fulltext_artifact",
                    "status": artifact_status,
                    "kind": kind,
                    "path": rel_or_abs(path),
                    "sha256": digest,
                    "size_bytes": size,
                    "detail": detail,
                },
                {
                    "item": "stage38_decision",
                    "status": decision,
                    "kind": "review_gate",
                    "path": rel_or_abs(path),
                    "sha256": digest,
                    "size_bytes": size,
                    "detail": detail,
                },
            ]

    checklist = [
        {
            "review_item": item,
            "required_evidence": evidence,
            "status": checklist_status,
            "paper_anchor": "",
            "notes": "No theorem-level or novelty claim may be upgraded until this row has concrete source anchors.",
        }
        for item, evidence in REVIEW_ITEMS
    ]
    return summary, checklist


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fulltext",
        default=os.environ.get("FAB686_FULLTEXT_PATH"),
        help="Path to the 2025/686 full-text PDF/text artifact.",
    )
    parser.add_argument(
        "--out-dir",
        default=os.environ.get("STAGE38_OUT_DIR", str(DEFAULT_OUT_DIR)),
        help="Output directory for Stage 38 gate artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    summary, checklist = build_rows(args.fulltext)
    write_csv(
        out_dir / "summary.csv",
        summary,
        ["item", "status", "kind", "path", "sha256", "size_bytes", "detail"],
    )
    write_csv(
        out_dir / "review_checklist.csv",
        checklist,
        ["review_item", "required_evidence", "status", "paper_anchor", "notes"],
    )
    print(f"Wrote {(out_dir / 'summary.csv').relative_to(ROOT).as_posix()}")
    print(f"Wrote {(out_dir / 'review_checklist.csv').relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
