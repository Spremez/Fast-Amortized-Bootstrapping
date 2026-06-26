#!/usr/bin/env python3
"""Probe 2025/686 external paper metadata and full-text availability.

This stage records source availability for the base 2025/686 paper. It does
not unlock theorem-level claims by itself: a registered full-text artifact and
manual claim-to-source review are still required before any paper/novelty
wording can be upgraded.
"""

from __future__ import annotations

import argparse
import csv
import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "repro" / "stage55_external_paper_probe"
DOC = ROOT / "docs" / "stage55_external_paper_probe_log.md"

CROSSREF_URL = "https://api.crossref.org/works/10.1145/3719027.3765181"


@dataclass(frozen=True)
class ProbeSource:
    source_id: str
    role: str
    url: str
    expected_kind: str
    notes: str


SOURCES = [
    ProbeSource(
        "FAB686_EPRINT_PDF",
        "base_fulltext_candidate",
        "https://eprint.iacr.org/2025/686.pdf",
        "pdf",
        "IACR ePrint PDF route for theorem-level 2025/686 review.",
    ),
    ProbeSource(
        "FAB686_EPRINT_PAGE",
        "base_metadata_candidate",
        "https://eprint.iacr.org/2025/686",
        "html",
        "IACR ePrint landing page route.",
    ),
    ProbeSource(
        "FAB686_ACM_PDF",
        "base_fulltext_candidate",
        "https://dl.acm.org/doi/pdf/10.1145/3719027.3765181",
        "pdf",
        "ACM DOI PDF route for the published CCS 2025 version.",
    ),
    ProbeSource(
        "FAB686_ACM_DOI_PAGE",
        "base_metadata_candidate",
        "https://dl.acm.org/doi/10.1145/3719027.3765181",
        "html",
        "ACM DOI landing page route.",
    ),
    ProbeSource(
        "FAB686_AUTHOR_PAGE",
        "base_author_metadata",
        "https://antonioguimaraes.org/publication/guimaraes-fast-2025/",
        "html",
        "Author publication page containing base-paper metadata and links.",
    ),
    ProbeSource(
        "FAB686_GITHUB",
        "base_code_metadata",
        "https://github.com/antoniocgj/Fast-Amortized-Bootstrapping",
        "html",
        "Public implementation repository for the 2025/686 code base.",
    ),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def classify_response(
    http_status: str,
    content_type: str,
    sample: bytes,
    expected_kind: str,
    error: str,
) -> str:
    haystack = sample[:4096].lower()
    if "HTTP Error 403" in error or http_status == "403":
        return "BLOCKED_403"
    if error:
        return "FETCH_ERROR"
    if b"enable javascript and cookies" in haystack or b"cf-chl" in haystack:
        return "BLOCKED_CLOUDFLARE_CHALLENGE"
    if expected_kind == "pdf" and (
        sample.startswith(b"%PDF-") or content_type.lower().startswith("application/pdf")
    ):
        return "PDF_ACCESSIBLE"
    if http_status in {"200", "202"}:
        return "METADATA_OR_HTML_ONLY"
    if http_status:
        return f"HTTP_{http_status}"
    return "MISSING"


def fetch_url(source: ProbeSource, timeout_s: float, user_agent: str) -> Dict[str, str]:
    request = urllib.request.Request(source.url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as resp:
            sample = resp.read(4096)
            content_type = resp.headers.get("content-type", "")
            http_status = str(resp.status)
            effective_url = resp.geturl()
            error = ""
    except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as exc:
        sample = b""
        content_type = ""
        http_status = str(getattr(exc, "code", "") or "")
        effective_url = ""
        error = str(exc)

    return {
        "source_id": source.source_id,
        "role": source.role,
        "url": source.url,
        "expected_kind": source.expected_kind,
        "http_status": http_status,
        "content_type": content_type,
        "sample_bytes": str(len(sample)),
        "effective_url": effective_url,
        "status": classify_response(
            http_status, content_type, sample, source.expected_kind, error
        ),
        "detail": source.notes if not error else f"{source.notes} error={error}",
    }


def fetch_crossref(out_dir: Path, timeout_s: float, user_agent: str) -> Dict[str, str]:
    request = urllib.request.Request(CROSSREF_URL, headers={"User-Agent": user_agent})
    out_json = out_dir / "crossref_metadata.json"
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            message = payload.get("message", {})
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
    except Exception as exc:  # noqa: BLE001 - probe must preserve failure detail.
        return {
            "metadata_id": "crossref_doi_metadata",
            "status": "FETCH_ERROR",
            "evidence": "",
            "title": "",
            "authors": "",
            "year": "",
            "venue": "",
            "doi": "10.1145/3719027.3765181",
            "page": "",
            "references_count": "",
            "detail": str(exc),
        }

    authors = [
        " ".join(filter(None, [a.get("given", ""), a.get("family", "")]))
        for a in message.get("author", [])
    ]
    title = "; ".join(message.get("title", []))
    venue = "; ".join(message.get("container-title", []))
    issued = message.get("issued", {}).get("date-parts", [[]])[0]
    year = str(issued[0]) if issued else ""
    return {
        "metadata_id": "crossref_doi_metadata",
        "status": "PASS",
        "evidence": rel(out_json),
        "title": title,
        "authors": "; ".join(authors),
        "year": year,
        "venue": venue,
        "doi": message.get("DOI", ""),
        "page": message.get("page", ""),
        "references_count": str(message.get("references-count", "")),
        "detail": "Crossref DOI metadata is available, but it is not theorem-level full text.",
    }


def build_summary(
    access_rows: List[Dict[str, str]],
    metadata_row: Dict[str, str],
    out_dir: Path,
) -> List[Dict[str, str]]:
    fulltext_rows = [r for r in access_rows if r["role"] == "base_fulltext_candidate"]
    metadata_rows = [r for r in access_rows if "metadata" in r["role"]]
    fulltext_accessible = any(r["status"] == "PDF_ACCESSIBLE" for r in fulltext_rows)
    metadata_available = metadata_row["status"] == "PASS" or any(
        r["status"] == "METADATA_OR_HTML_ONLY" for r in metadata_rows
    )
    cf_blocks = [
        f"{r['source_id']}={r['status']}"
        for r in access_rows
        if r["status"] in {"BLOCKED_CLOUDFLARE_CHALLENGE", "BLOCKED_403"}
    ]

    decision = (
        "FULLTEXT_AVAILABLE_REVIEW_REQUIRED"
        if fulltext_accessible
        else "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW"
    )
    policy = (
        "A local PDF/text artifact and manual claim-to-source review are still required "
        "before theorem, algorithm, table, figure, or experiment-number claims from "
        "2025/686 are allowed."
    )

    return [
        {
            "gate": "crossref_doi_metadata",
            "status": metadata_row["status"],
            "evidence": metadata_row.get("evidence", ""),
            "detail": metadata_row.get("detail", ""),
        },
        {
            "gate": "official_metadata_visibility",
            "status": "PASS" if metadata_available else "MISSING",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": "; ".join(
                f"{r['source_id']}={r['status']}" for r in metadata_rows
            ),
        },
        {
            "gate": "official_fulltext_pdf_access",
            "status": "PASS" if fulltext_accessible else "BLOCKED",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": "; ".join(
                f"{r['source_id']}={r['status']}" for r in fulltext_rows
            ),
        },
        {
            "gate": "cloudflare_block_recorded",
            "status": "PASS" if cf_blocks else "NOT_OBSERVED",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": "; ".join(cf_blocks) if cf_blocks else "No Cloudflare/403 block recorded.",
        },
        {
            "gate": "stage55_decision",
            "status": decision,
            "evidence": rel(out_dir / "summary.csv"),
            "detail": policy,
        },
    ]


def write_doc(
    out_dir: Path,
    access_rows: List[Dict[str, str]],
    metadata_row: Dict[str, str],
    summary_rows: List[Dict[str, str]],
) -> None:
    decision = next(r for r in summary_rows if r["gate"] == "stage55_decision")
    lines = [
        "# Stage 55 External Paper Probe Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage 55 refreshes the 2025/686 source-acquisition state with a stronger",
        "paper-metadata probe. It records official full-text routes, DOI/Crossref",
        "metadata, Cloudflare/403 blocking, and the claim policy for theorem-level",
        "citation review.",
        "",
        "This stage does not change scalar SAB or `sab_pvw_*` code and does not",
        "upgrade novelty, theorem-level, or protocol-number claims.",
        "",
        "## Summary",
        "",
        f"- decision: `{decision['status']}`",
        f"- title: `{metadata_row.get('title', '')}`",
        f"- DOI: `{metadata_row.get('doi', '')}`",
        f"- authors: `{metadata_row.get('authors', '')}`",
        f"- venue: `{metadata_row.get('venue', '')}`",
        f"- pages: `{metadata_row.get('page', '')}`",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for row in summary_rows:
        lines.append(f"| {row['gate']} | {row['status']} | {row['evidence']} | {row['detail']} |")

    lines.extend(
        [
            "",
            "## Access Matrix",
            "",
            "| source | role | status | url |",
            "|---|---|---|---|",
        ]
    )
    for row in access_rows:
        lines.append(f"| {row['source_id']} | {row['role']} | {row['status']} | {row['url']} |")

    lines.extend(
        [
            "",
            "## Claim Policy",
            "",
            "Crossref metadata is enough to identify the publication, but it is not",
            "enough to cite theorem, algorithm, table, figure, or experiment-number",
            "claims. Those claims remain blocked until a recognized full text is",
            "registered and manually reviewed against concrete anchors.",
            "",
        ]
    )
    DOC.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--agent", default="Mozilla/5.0 stage55-paper-probe")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    access_rows = [fetch_url(source, args.timeout, args.agent) for source in SOURCES]
    metadata_row = fetch_crossref(out_dir, args.timeout, args.agent)
    summary_rows = build_summary(access_rows, metadata_row, out_dir)

    write_csv(
        out_dir / "access_probe.csv",
        access_rows,
        [
            "source_id",
            "role",
            "url",
            "expected_kind",
            "http_status",
            "content_type",
            "sample_bytes",
            "effective_url",
            "status",
            "detail",
        ],
    )
    write_csv(
        out_dir / "crossref_summary.csv",
        [metadata_row],
        [
            "metadata_id",
            "status",
            "evidence",
            "title",
            "authors",
            "year",
            "venue",
            "doi",
            "page",
            "references_count",
            "detail",
        ],
    )
    write_csv(out_dir / "summary.csv", summary_rows, ["gate", "status", "evidence", "detail"])
    write_doc(out_dir, access_rows, metadata_row, summary_rows)

    decision = next(r for r in summary_rows if r["gate"] == "stage55_decision")
    print(f"Stage 55 paper probe summary: {rel(out_dir / 'summary.csv')}")
    print(f"Stage 55 paper probe log: {rel(DOC)}")
    print(f"Decision: {decision['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
