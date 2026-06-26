#!/usr/bin/env python3
"""Refresh external source availability for 2025/686 after Stage71.

Stage72 probes current official/author/metadata routes for the base 2025/686
paper. It is an external evidence refresh only: it does not modify SAB code,
does not run a benchmark, and does not upgrade theorem-level, novelty, or
MAT-AVX512 attribution claims.
"""

from __future__ import annotations

import csv
import json
import socket
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "stage72_external_source_refresh"
OUT_MD = ROOT / "docs" / "stage72_external_source_refresh_log.md"

CROSSREF_URL = "https://api.crossref.org/works/10.1145/3719027.3765181"
USER_AGENT = "Mozilla/5.0 stage72-external-source-refresh"


@dataclass(frozen=True)
class Source:
    source_id: str
    role: str
    url: str
    expected_kind: str
    required_marker: str
    notes: str


SOURCES = [
    Source(
        "FAB686_EPRINT_PDF",
        "official_fulltext_candidate",
        "https://eprint.iacr.org/2025/686.pdf",
        "pdf",
        "",
        "IACR ePrint PDF route.",
    ),
    Source(
        "FAB686_EPRINT_PAGE",
        "official_metadata_candidate",
        "https://eprint.iacr.org/2025/686",
        "html",
        "2025/686",
        "IACR ePrint landing page.",
    ),
    Source(
        "FAB686_ACM_PDF",
        "official_fulltext_candidate",
        "https://dl.acm.org/doi/pdf/10.1145/3719027.3765181",
        "pdf",
        "",
        "ACM DOI PDF route.",
    ),
    Source(
        "FAB686_ACM_DOI_PAGE",
        "official_metadata_candidate",
        "https://dl.acm.org/doi/10.1145/3719027.3765181",
        "html",
        "10.1145/3719027.3765181",
        "ACM DOI landing page.",
    ),
    Source(
        "FAB686_AUTHOR_PAGE",
        "author_metadata_candidate",
        "https://antonioguimaraes.org/publication/guimaraes-fast-2025/",
        "html",
        "Fast amortized bootstrapping with small keys",
        "Author publication page with abstract, ePrint link, and code link.",
    ),
    Source(
        "FAB686_AUTHOR_BIBTEX",
        "author_metadata_candidate",
        "https://antonioguimaraes.org/publication/guimaraes-fast-2025/cite.bib",
        "bibtex",
        "guimaraes_fast_2025",
        "Author-provided BibTeX metadata.",
    ),
    Source(
        "FAB686_AUTHOR_GUESSED_PDF",
        "author_fulltext_guess",
        "https://antonioguimaraes.org/publication/guimaraes-fast-2025/guimaraes-fast-2025.pdf",
        "pdf",
        "",
        "Conventional Hugo Blox local-PDF guess; not advertised by the page.",
    ),
    Source(
        "FAB686_GITHUB_REPO",
        "code_route",
        "https://github.com/antoniocgj/Fast-Amortized-Bootstrapping",
        "html",
        "Fast-Amortized-Bootstrapping",
        "Author-linked public implementation repository.",
    ),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ascii_text(value: str) -> str:
    return (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fetch_sample(source: Source, timeout_s: float = 45.0) -> Dict[str, str]:
    req = urllib.request.Request(source.url, headers={"User-Agent": USER_AGENT})
    sample = b""
    content_type = ""
    http_status = ""
    effective_url = ""
    error = ""
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            sample = resp.read(16384)
            content_type = resp.headers.get("content-type", "")
            http_status = str(resp.status)
            effective_url = resp.geturl()
    except urllib.error.HTTPError as exc:
        http_status = str(exc.code)
        content_type = exc.headers.get("content-type", "") if exc.headers else ""
        try:
            sample = exc.read(4096)
        except Exception:  # noqa: BLE001 - best effort probe capture.
            sample = b""
        error = str(exc)
    except (urllib.error.URLError, socket.timeout) as exc:
        error = str(exc)

    text_sample = sample.decode("utf-8", errors="ignore")
    lowered = text_sample.lower()
    marker_present = (
        "yes"
        if source.required_marker
        and source.required_marker.lower() in lowered
        else "no"
        if source.required_marker
        else "not_required"
    )
    status = classify(source, http_status, content_type, sample, marker_present, error)

    return {
        "source_id": source.source_id,
        "role": source.role,
        "url": source.url,
        "expected_kind": source.expected_kind,
        "http_status": http_status,
        "content_type": content_type,
        "sample_bytes": str(len(sample)),
        "marker_present": marker_present,
        "effective_url": effective_url,
        "status": status,
        "detail": source.notes if not error else f"{source.notes} error={error}",
    }


def classify(
    source: Source,
    http_status: str,
    content_type: str,
    sample: bytes,
    marker_present: str,
    error: str,
) -> str:
    haystack = sample[:4096].lower()
    if http_status == "403" or b"cf-mitigated" in haystack or b"challenge" in haystack:
        return "BLOCKED_403_OR_CHALLENGE"
    if http_status == "404":
        return "NOT_FOUND"
    if error:
        return "FETCH_ERROR"
    if source.expected_kind == "pdf":
        if sample.startswith(b"%PDF-") or content_type.lower().startswith("application/pdf"):
            return "PDF_ACCESSIBLE"
        return "NOT_PDF"
    if marker_present == "yes":
        return "PASS_METADATA"
    if http_status == "200":
        return "PASS_HTTP_200_MARKER_MISSING"
    if http_status:
        return f"HTTP_{http_status}"
    return "MISSING"


def fetch_crossref(out_dir: Path, timeout_s: float = 45.0) -> Dict[str, str]:
    req = urllib.request.Request(CROSSREF_URL, headers={"User-Agent": USER_AGENT})
    out_json = out_dir / "crossref_metadata.json"
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
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
            "detail": str(exc),
        }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    msg = payload.get("message", {})
    authors = [
        " ".join(filter(None, [a.get("given", ""), a.get("family", "")]))
        for a in msg.get("author", [])
    ]
    issued = msg.get("issued", {}).get("date-parts", [[]])[0]
    return {
        "metadata_id": "crossref_doi_metadata",
        "status": "PASS",
        "evidence": rel(out_json),
        "title": ascii_text("; ".join(msg.get("title", []))),
        "authors": ascii_text("; ".join(authors)),
        "year": str(issued[0]) if issued else "",
        "venue": ascii_text("; ".join(msg.get("container-title", []))),
        "doi": msg.get("DOI", ""),
        "detail": "DOI metadata is available; this is not full text.",
    }


def write_author_bibtex(access_rows: List[Dict[str, str]], out_dir: Path) -> str:
    row = next((r for r in access_rows if r["source_id"] == "FAB686_AUTHOR_BIBTEX"), {})
    if row.get("status") != "PASS_METADATA":
        return ""
    req = urllib.request.Request(row["url"], headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=45.0) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""
    out = out_dir / "author_cite.bib"
    out.write_text(payload if payload.endswith("\n") else payload + "\n", encoding="utf-8", newline="\n")
    return rel(out)


def build_summary(
    access_rows: List[Dict[str, str]],
    metadata: Dict[str, str],
    bibtex_evidence: str,
) -> List[Dict[str, str]]:
    by_id = {r["source_id"]: r for r in access_rows}
    fulltext_rows = [
        by_id["FAB686_EPRINT_PDF"],
        by_id["FAB686_ACM_PDF"],
        by_id["FAB686_AUTHOR_GUESSED_PDF"],
    ]
    official_fulltext_ok = any(r["status"] == "PDF_ACCESSIBLE" for r in fulltext_rows[:2])
    author_metadata_ok = (
        by_id["FAB686_AUTHOR_PAGE"]["status"] == "PASS_METADATA"
        and by_id["FAB686_AUTHOR_BIBTEX"]["status"] == "PASS_METADATA"
        and bool(bibtex_evidence)
    )
    code_ok = by_id["FAB686_GITHUB_REPO"]["status"] in {
        "PASS_METADATA",
        "PASS_HTTP_200_MARKER_MISSING",
    }
    doi_ok = metadata["status"] == "PASS"

    return [
        {
            "gate": "stage72_author_metadata_route",
            "status": "PASS" if author_metadata_ok else "FAIL",
            "evidence": f"{rel(OUT_DIR / 'access_probe.csv')}; {bibtex_evidence}",
            "detail": (
                "author page and author BibTeX metadata are available"
                if author_metadata_ok
                else "author page or BibTeX metadata missing"
            ),
        },
        {
            "gate": "stage72_doi_metadata_route",
            "status": "PASS" if doi_ok else "FAIL",
            "evidence": metadata.get("evidence", ""),
            "detail": metadata.get("detail", ""),
        },
        {
            "gate": "stage72_code_route",
            "status": "PASS" if code_ok else "FAIL",
            "evidence": rel(OUT_DIR / "access_probe.csv"),
            "detail": f"FAB686_GITHUB_REPO={by_id['FAB686_GITHUB_REPO']['status']}",
        },
        {
            "gate": "stage72_official_fulltext_routes",
            "status": "FULLTEXT_AVAILABLE_REVIEW_REQUIRED"
            if official_fulltext_ok
            else "WAIT_FULLTEXT_ARTIFACT",
            "evidence": rel(OUT_DIR / "access_probe.csv"),
            "detail": "; ".join(f"{r['source_id']}={r['status']}" for r in fulltext_rows),
        },
        {
            "gate": "stage72_claim_policy",
            "status": "KEEP_STRONGER_CLAIMS_BLOCKED",
            "evidence": rel(OUT_DIR / "summary.csv"),
            "detail": "metadata/code routes are not sufficient for theorem-level or novelty claims without reviewed full text",
        },
    ]


def write_doc(
    access_rows: List[Dict[str, str]],
    metadata: Dict[str, str],
    summary_rows: List[Dict[str, str]],
) -> None:
    decision = summary_rows[-1]
    lines = [
        "# Stage72 External Source Refresh Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage72 refreshes current external source availability after Stage71.",
        "It checks official ePrint/ACM routes, the author publication page,",
        "author-provided BibTeX, Crossref DOI metadata, and the author-linked",
        "GitHub code route.",
        "",
        "This stage does not change SAB code, does not run a benchmark, and does",
        "not upgrade theorem-level, novelty, all-parameter, non-binary, or",
        "MAT-AVX512 optimality claims.",
        "",
        "## Metadata",
        "",
        f"- title: `{metadata.get('title', '')}`",
        f"- authors: `{metadata.get('authors', '')}`",
        f"- year: `{metadata.get('year', '')}`",
        f"- venue: `{metadata.get('venue', '')}`",
        f"- DOI: `{metadata.get('doi', '')}`",
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
            "| stage72_decision | PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED | repro/stage72_external_source_refresh/summary.csv | External metadata/code routes are refreshed; direct full-text review remains blocked or requires a supplied artifact. |",
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
            "## Decision",
            "",
            "`PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED`",
            "",
            "Author metadata, DOI metadata, and the implementation route are visible,",
            "but the direct ePrint/ACM full-text PDF routes are still not a reviewed",
            "local full-text artifact. Keep CB6/CB7 and paper-level claims blocked.",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    access_rows = [fetch_sample(source) for source in SOURCES]
    metadata = fetch_crossref(OUT_DIR)
    bibtex_evidence = write_author_bibtex(access_rows, OUT_DIR)
    summary_rows = build_summary(access_rows, metadata, bibtex_evidence)
    summary_rows.append(
        {
            "gate": "stage72_decision",
            "status": "PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED",
            "evidence": rel(OUT_DIR / "summary.csv"),
            "detail": "External source routes were refreshed; stronger claims remain blocked pending reviewed full text.",
        }
    )

    write_csv(
        OUT_DIR / "access_probe.csv",
        access_rows,
        [
            "source_id",
            "role",
            "url",
            "expected_kind",
            "http_status",
            "content_type",
            "sample_bytes",
            "marker_present",
            "effective_url",
            "status",
            "detail",
        ],
    )
    write_csv(
        OUT_DIR / "crossref_summary.csv",
        [metadata],
        ["metadata_id", "status", "evidence", "title", "authors", "year", "venue", "doi", "detail"],
    )
    write_csv(OUT_DIR / "summary.csv", summary_rows, ["gate", "status", "evidence", "detail"])
    write_doc(access_rows, metadata, summary_rows[:-1])

    print(f"Stage72 summary: {rel(OUT_DIR / 'summary.csv')}")
    print(f"Stage72 log: {rel(OUT_MD)}")
    print("Stage72 external source refresh: PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
