#!/usr/bin/env python3
"""Build Stage100 2025/686 full-text anchor prefill artifacts.

The script intentionally does not store extracted full text. It uses pdftotext
as a temporary local parser and writes only page/keyword metadata plus
review-required candidate anchors for the Stage38 manual review checklist.
"""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_EVIDENCE = ROOT / "repro" / "external_evidence_intake" / "summary.csv"
STAGE38_CHECKLIST = ROOT / "repro" / "stage38_fulltext_review_gate" / "review_checklist.csv"
STAGE99_SUMMARY = ROOT / "repro" / "stage99_external_blocker_reprobe" / "summary.csv"
OUT_DIR = ROOT / "repro" / "stage100_fulltext_anchor_prefill"
OUT_SUMMARY = OUT_DIR / "summary.csv"
OUT_HITS = OUT_DIR / "page_keyword_hits.csv"
OUT_ANCHORS = OUT_DIR / "anchor_candidates.csv"
OUT_INDEX = OUT_DIR / "artifact_index.csv"
OUT_MD = ROOT / "docs" / "stage100_fulltext_anchor_prefill_log.md"


QUERY_SETS: Dict[str, List[str]] = {
    "FAB_PROTOCOL_STAGES": [
        "Algorithm 1",
        "Algorithm 2",
        "Algorithm 3",
        "Algorithm 4",
        "Algorithm 6",
        "MPmul",
        "test vectors",
        "external product",
        "CMUX",
        "extraction",
        "key switching",
        "sparse amortized bootstrapping",
    ],
    "FAB_COMPLEXITY_MODEL": [
        "complexity",
        "amortized complexity",
        "h log B",
        "N h",
        "Lemma 6.1",
        "Corollary 6.2",
        "Algorithm 6 runs",
        "external product",
    ],
    "FAB_CORRECTNESS_NOISE": [
        "correctness",
        "noise",
        "Lemma 3.1",
        "Lemma 4.2",
        "Lemma 6.1",
        "probability of failure",
        "negligible",
    ],
    "FAB_PARAMETER_SECURITY": [
        "parameter selection",
        "security",
        "sparse secrets",
        "binary",
        "ternary",
        "arbitrary sparse secrets",
        "Table",
    ],
    "PVW_SAB_DELTA": [
        "external product",
        "CMUX",
        "matrix",
        "multi",
        "packing",
        "key switching",
        "amortized functional bootstrapping",
    ],
    "NOVELTY_BOUNDARY": [
        "related work",
        "comparison with other works",
        "contributions",
        "techniques",
        "practical results",
        "References",
    ],
}

HEADING_RE = re.compile(
    r"^(?:\d+(?:\.\d+)*\s+.+|Algorithm\s+\d+:.*|Lemma\s+\d+(?:\.\d+)?.*|Corollary\s+\d+(?:\.\d+)?.*|References|Appendix.*)$",
    re.I,
)


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


def row_by(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_pdf_path(path_text: str) -> Path:
    direct = Path(path_text)
    if direct.exists():
        return direct
    if path_text.startswith("/mnt/") and len(path_text) > 6:
        drive = path_text[5].upper() + ":"
        return Path(drive + path_text[6:].replace("/", "\\"))
    return direct


def extract_pages(pdf_path: Path) -> List[str]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), str(tmp_path)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        text = tmp_path.read_text(encoding="utf-8", errors="replace")
        return text.split("\f")
    finally:
        tmp_path.unlink(missing_ok=True)


def page_headings(page_text: str) -> str:
    headings: List[str] = []
    for raw in page_text.splitlines():
        line = " ".join(raw.strip().split())
        if not line or len(line) > 110:
            continue
        if HEADING_RE.match(line):
            headings.append(line)
        if len(headings) >= 4:
            break
    return "; ".join(headings)


def count_term(page_text: str, term: str) -> int:
    return len(re.findall(re.escape(term), page_text, flags=re.I))


def build_hits(pages: List[str]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    hit_rows: List[Dict[str, str]] = []
    anchor_rows: List[Dict[str, str]] = []
    headings_by_page = {i + 1: page_headings(page) for i, page in enumerate(pages)}

    for review_item, terms in QUERY_SETS.items():
        scored_pages: List[Tuple[int, int, List[str]]] = []
        for page_no, page_text in enumerate(pages, 1):
            matched_terms = []
            score = 0
            for term in terms:
                c = count_term(page_text, term)
                if c:
                    matched_terms.append(term)
                    score += c
            if score:
                scored_pages.append((score, page_no, matched_terms))
                hit_rows.append(
                    {
                        "review_item": review_item,
                        "page": str(page_no),
                        "score": str(score),
                        "matched_terms": "; ".join(matched_terms),
                        "section_hint": headings_by_page.get(page_no, ""),
                    }
                )
        ranked = sorted(scored_pages, key=lambda x: (-x[0], x[1]))[:8]
        candidate_pages = ", ".join(str(page_no) for _, page_no, _ in ranked)
        candidate_terms = "; ".join(
            f"p{page_no}: {', '.join(terms[:5])}" for _, page_no, terms in ranked
        )
        anchor_rows.append(
            {
                "review_item": review_item,
                "status": "CANDIDATE_ANCHORS_GENERATED_REVIEW_REQUIRED"
                if ranked
                else "NO_CANDIDATE_ANCHOR_FOUND_REVIEW_REQUIRED",
                "candidate_pages": candidate_pages,
                "candidate_terms": candidate_terms,
                "review_action": (
                    "Manually inspect the listed pages in the registered PDF and replace this candidate with verified page/section anchors before upgrading claims."
                    if ranked
                    else "Manually inspect the paper; keyword prefill did not locate a candidate anchor."
                ),
            }
        )
    return hit_rows, anchor_rows


def prefill_stage38(anchor_rows: List[Dict[str, str]]) -> None:
    checklist = read_csv(STAGE38_CHECKLIST)
    anchors = {row["review_item"]: row for row in anchor_rows}
    prefill_note = (
        "Stage100 prefill is candidate-only and still requires manual source-anchor review."
    )
    updated: List[Dict[str, str]] = []
    for row in checklist:
        item = row.get("review_item", "")
        anchor = anchors.get(item)
        if anchor:
            row["status"] = anchor["status"]
            row["paper_anchor"] = (
                f"Stage100 candidate pages: {anchor['candidate_pages']}"
                if anchor.get("candidate_pages")
                else "Stage100 found no keyword candidate"
            )
            notes = row.get("notes", "").replace(prefill_note, "").strip()
            row["notes"] = f"{notes} {prefill_note}".strip()
        updated.append(row)
    if updated:
        write_csv(
            STAGE38_CHECKLIST,
            updated,
            ["review_item", "required_evidence", "status", "paper_anchor", "notes"],
        )


def write_md(summary_rows: List[Dict[str, str]], anchor_rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage100 Full-Text Anchor Prefill Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage100 converts the registered 2025/686 PDF into candidate page anchors",
        "for the Stage38 manual source review. It does not store full paper text",
        "and does not upgrade theorem, novelty, or paper-level claims.",
        "",
        "## Summary",
        "",
        "| gate | status | detail |",
        "|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(f"| {row['gate']} | {row['status']} | {row['detail']} |")
    lines.extend(["", "## Anchor Candidates", "", "| review item | status | pages |", "|---|---|---|"])
    for row in anchor_rows:
        lines.append(
            f"| {row['review_item']} | {row['status']} | {row['candidate_pages']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Policy",
            "",
            "All Stage100 anchors are candidate-only. A human source review must",
            "confirm page/section anchors before the checklist can be marked as",
            "reviewed or used to upgrade 2025/686 theorem-level or novelty claims.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def artifact_index(paths: List[Path]) -> List[Dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": path.relative_to(ROOT).as_posix(),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_file(path) if path.exists() else "",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def main() -> int:
    external = {r.get("evidence_id"): r for r in read_csv(EXTERNAL_EVIDENCE)}
    stage99 = {r.get("gate"): r for r in read_csv(STAGE99_SUMMARY)}
    fulltext = external.get("fab686_fulltext", {})
    pdf_status = fulltext.get("status", "MISSING")
    pdf_path_text = fulltext.get("path", "")
    pdf_path = resolve_pdf_path(pdf_path_text) if pdf_path_text else Path()
    stage99_decision = stage99.get("stage99_decision", {}).get("status", "MISSING")

    summary_rows: List[Dict[str, str]] = [
        {
            "gate": "stage100_stage99_precondition",
            "status": "PASS"
            if stage99_decision == "PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_REVIEW_REQUIRED"
            else "FAIL",
            "evidence": "repro/stage99_external_blocker_reprobe/summary.csv",
            "detail": f"stage99_decision={stage99_decision}",
            "next_action": "Refresh Stage99 before running Stage100.",
        },
        {
            "gate": "stage100_fulltext_artifact",
            "status": "PASS"
            if pdf_status == "AVAILABLE_UNREVIEWED" and pdf_path.exists()
            else "FAIL",
            "evidence": "repro/external_evidence_intake/summary.csv",
            "detail": f"status={pdf_status}; path={pdf_path_text}",
            "next_action": "Register a valid 2025/686 full-text artifact before anchor prefill.",
        },
    ]

    if summary_rows[0]["status"] != "PASS" or summary_rows[1]["status"] != "PASS":
        write_csv(
            OUT_SUMMARY,
            summary_rows
            + [
                {
                    "gate": "stage100_decision",
                    "status": "FAIL_STAGE100_FULLTEXT_ANCHOR_PREFILL",
                    "evidence": OUT_SUMMARY.relative_to(ROOT).as_posix(),
                    "detail": "Preconditions failed.",
                    "next_action": "Fix Stage99/fulltext artifact state and rerun Stage100.",
                }
            ],
            ["gate", "status", "evidence", "detail", "next_action"],
        )
        return 1

    pages = extract_pages(pdf_path)
    hit_rows, anchor_rows = build_hits(pages)
    prefill_stage38(anchor_rows)

    write_csv(
        OUT_HITS,
        hit_rows,
        ["review_item", "page", "score", "matched_terms", "section_hint"],
    )
    write_csv(
        OUT_ANCHORS,
        anchor_rows,
        ["review_item", "status", "candidate_pages", "candidate_terms", "review_action"],
    )
    all_candidates = all(
        row["status"] == "CANDIDATE_ANCHORS_GENERATED_REVIEW_REQUIRED"
        for row in anchor_rows
    )
    summary_rows.extend(
        [
            {
                "gate": "stage100_text_extract",
                "status": "PASS",
                "evidence": "temporary pdftotext extraction; full text not persisted",
                "detail": f"pages={len(pages)}; pdf_sha256={fulltext.get('sha256', '')}",
                "next_action": "Use only generated metadata unless manual review requires opening the PDF.",
            },
            {
                "gate": "stage100_anchor_candidates",
                "status": "CANDIDATE_ANCHORS_GENERATED_REVIEW_REQUIRED"
                if all_candidates
                else "PARTIAL_CANDIDATE_ANCHORS_REVIEW_REQUIRED",
                "evidence": OUT_ANCHORS.relative_to(ROOT).as_posix(),
                "detail": f"review_items={len(anchor_rows)}; hit_rows={len(hit_rows)}",
                "next_action": "Manually verify candidate pages and replace candidates with source anchors.",
            },
            {
                "gate": "stage100_stage38_prefill",
                "status": "REVIEW_CHECKLIST_PREFILLED_REVIEW_REQUIRED",
                "evidence": STAGE38_CHECKLIST.relative_to(ROOT).as_posix(),
                "detail": "Stage38 checklist now contains candidate-only page anchors.",
                "next_action": "Do not mark reviewed until each row is manually checked against the PDF.",
            },
            {
                "gate": "stage100_claim_guard",
                "status": "PASS_NO_CLAIM_UPGRADE",
                "evidence": OUT_MD.relative_to(ROOT).as_posix(),
                "detail": "Candidate anchors do not upgrade theorem, novelty, or MAT-AVX512 claims.",
                "next_action": "Keep final audit external-review-required until manual review passes.",
            },
            {
                "gate": "stage100_decision",
                "status": "PASS_STAGE100_FULLTEXT_ANCHOR_PREFILL_REVIEW_REQUIRED",
                "evidence": OUT_SUMMARY.relative_to(ROOT).as_posix(),
                "detail": "2025/686 candidate anchors generated; manual source review remains required.",
                "next_action": "Run manual Stage38 source review using the generated candidate pages.",
            },
        ]
    )
    write_csv(
        OUT_SUMMARY,
        summary_rows,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_md(summary_rows, anchor_rows)
    write_csv(
        OUT_INDEX,
        artifact_index([OUT_SUMMARY, OUT_HITS, OUT_ANCHORS, OUT_MD, STAGE38_CHECKLIST]),
        ["artifact", "exists", "sha256", "size_bytes"],
    )
    print(f"Wrote {OUT_SUMMARY.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_HITS.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_ANCHORS.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print("Stage100 fulltext anchor prefill: PASS_STAGE100_FULLTEXT_ANCHOR_PREFILL_REVIEW_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
