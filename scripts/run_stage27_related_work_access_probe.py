#!/usr/bin/env python3
"""Probe related-work source access for the Stage 27 novelty gate.

This is a source-access probe, not a citation-support verifier. It records
which related-work sources are currently reachable from this environment and
keeps novelty/theorem-level claims blocked until full texts are manually
reviewed.
"""

from __future__ import annotations

import argparse
import csv
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "repro" / "stage27_related_work_access_probe"
DOC = ROOT / "docs" / "stage27_related_work_access_probe_log.md"


@dataclass(frozen=True)
class Source:
    source_id: str
    work: str
    role: str
    url: str
    notes: str


SOURCES = [
    Source(
        "FAB686_AUTHOR_PUBLICATION",
        "Fast amortized bootstrapping with small keys and polynomial noise overhead",
        "base_metadata",
        "https://antonioguimaraes.org/publication/guimaraes-fast-2025/",
        "Base paper author metadata page.",
    ),
    Source(
        "FAB686_GITHUB",
        "Fast-Amortized-Bootstrapping repository",
        "base_code_metadata",
        "https://github.com/antoniocgj/Fast-Amortized-Bootstrapping",
        "Base implementation repository and parameter/backend context.",
    ),
    Source(
        "FAB686_EPRINT_PDF",
        "IACR ePrint 2025/686",
        "base_fulltext_candidate",
        "https://eprint.iacr.org/2025/686.pdf",
        "Base-paper full-text candidate; required for theorem-level citations.",
    ),
    Source(
        "FAB686_ACM_PDF",
        "ACM DOI PDF for 2025/686",
        "base_fulltext_candidate",
        "https://dl.acm.org/doi/pdf/10.1145/3719027.3765181",
        "Publisher full-text candidate; required for theorem-level citations.",
    ),
    Source(
        "CM2112_ASKCRYPTO",
        "Sharing the Mask: TFHE Bootstrapping on Packed Messages",
        "shared_mask_prior_art_metadata",
        "https://askcryp.to/t/resource-topic-2025-2112-sharing-the-mask-tfhe-bootstrapping-on-packed-messages/25443",
        "Public metadata/topic page for common-mask multi-body TFHE work.",
    ),
    Source(
        "CM2112_DBLP",
        "Sharing the Mask bibliographic record",
        "shared_mask_prior_art_metadata",
        "https://dblp.org/rec/journals/iacr/BergeratBCOPT25.html",
        "Bibliographic metadata for TCHES/ePrint source identity.",
    ),
    Source(
        "CM2112_EPRINT_PDF",
        "Sharing the Mask ePrint PDF",
        "shared_mask_prior_art_fulltext_candidate",
        "https://eprint.iacr.org/2025/2112.pdf",
        "Full-text candidate for prior-art manual review.",
    ),
    Source(
        "INTT696_USP_PDF",
        "Faster amortized bootstrapping using the incomplete NTT for free",
        "adjacent_acceleration_fulltext",
        "https://repositorio.usp.br/directbitstream/69b0ba87-a92a-40e3-94ed-ecdb8ee395ec/Faster_amortized_bootstrapping_using_the_incomplete_NTT_for_free.pdf",
        "Public PDF for adjacent incomplete-NTT amortized bootstrapping.",
    ),
    Source(
        "INTT696_GITHUB",
        "incomplete_ntt_amortized_bt repository",
        "adjacent_acceleration_code",
        "https://github.com/thalespaiva/incomplete_ntt_amortized_bt",
        "Code/reproducibility context for adjacent incomplete-NTT work.",
    ),
    Source(
        "GPVL23_COSIC_PDF",
        "Amortized Bootstrapping Revisited",
        "amortized_bs_lineage_fulltext",
        "https://www.esat.kuleuven.be/cosic/publications/article-3610.pdf",
        "Public PDF for earlier amortized bootstrapping lineage.",
    ),
    Source(
        "BOOT_SURVEY_2026_RG",
        "Bootstrapping in FHEW-like cryptosystems: A survey",
        "secondary_survey_candidate",
        "https://www.researchgate.net/publication/390905714_Bootstrapping_in_FHEW-like_cryptosystems_A_survey",
        "Secondary survey context only; not primary novelty evidence.",
    ),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def classify(http_status: str, content_type: str, sample: bytes, error: str) -> str:
    if error:
        if "HTTP Error 403" in error:
            return "BLOCKED_403"
        if "HTTP Error 404" in error:
            return "HTTP_404"
        if "timed out" in error.lower():
            return "TIMEOUT"
        return "FETCH_ERROR"
    if http_status == "200" and (
        content_type.lower().startswith("application/pdf") or sample.startswith(b"%PDF")
    ):
        return "PDF_ACCESSIBLE"
    if http_status in {"200", "202"}:
        return "METADATA_OR_HTML_ONLY"
    if http_status == "403":
        return "BLOCKED_403"
    if http_status:
        return f"HTTP_{http_status}"
    return "MISSING"


def probe(source: Source, agent: str, timeout_s: float, retries: int) -> Dict[str, str]:
    req = urllib.request.Request(source.url, headers={"User-Agent": agent})
    last_error = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                sample = resp.read(4096)
                content_type = resp.headers.get("content-type", "")
                http_status = str(resp.status)
                effective_url = resp.geturl()
                return {
                    "source_id": source.source_id,
                    "work": source.work,
                    "role": source.role,
                    "url": source.url,
                    "http_status": http_status,
                    "content_type": content_type,
                    "sample_bytes": str(len(sample)),
                    "effective_url": effective_url,
                    "status": classify(http_status, content_type, sample, ""),
                    "notes": source.notes,
                }
        except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout) as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(1 + attempt)

    return {
        "source_id": source.source_id,
        "work": source.work,
        "role": source.role,
        "url": source.url,
        "http_status": "",
        "content_type": "",
        "sample_bytes": "0",
        "effective_url": "",
        "status": classify("", "", b"", last_error),
        "notes": f"{source.notes} fetch_error={last_error}",
    }


def any_status(rows: List[Dict[str, str]], roles: set[str], statuses: set[str]) -> bool:
    return any(row["role"] in roles and row["status"] in statuses for row in rows)


def status_list(rows: List[Dict[str, str]], roles: set[str]) -> str:
    return "; ".join(
        f"{row['source_id']}={row['status']}" for row in rows if row["role"] in roles
    )


def build_summary(rows: List[Dict[str, str]], out_dir: Path) -> List[Dict[str, str]]:
    base_fulltext_roles = {"base_fulltext_candidate"}
    base_metadata_roles = {"base_metadata", "base_code_metadata"}
    shared_mask_roles = {
        "shared_mask_prior_art_metadata",
        "shared_mask_prior_art_fulltext_candidate",
    }
    adjacent_roles = {"adjacent_acceleration_fulltext", "adjacent_acceleration_code"}
    lineage_roles = {"amortized_bs_lineage_fulltext"}

    base_fulltext = any_status(rows, base_fulltext_roles, {"PDF_ACCESSIBLE"})
    base_metadata = any_status(rows, base_metadata_roles, {"METADATA_OR_HTML_ONLY", "PDF_ACCESSIBLE"})
    shared_mask_seen = any_status(
        rows,
        shared_mask_roles,
        {"PDF_ACCESSIBLE", "METADATA_OR_HTML_ONLY"},
    )
    adjacent_seen = any_status(rows, adjacent_roles, {"PDF_ACCESSIBLE", "METADATA_OR_HTML_ONLY"})
    lineage_seen = any_status(rows, lineage_roles, {"PDF_ACCESSIBLE", "METADATA_OR_HTML_ONLY"})

    summary = [
        {
            "gate": "base_2025_686_fulltext",
            "status": "PASS_FULLTEXT_AVAILABLE" if base_fulltext else "BLOCKED_FULLTEXT",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": status_list(rows, base_fulltext_roles),
        },
        {
            "gate": "base_2025_686_metadata",
            "status": "PASS_METADATA_AVAILABLE" if base_metadata else "MISSING_METADATA",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": status_list(rows, base_metadata_roles),
        },
        {
            "gate": "shared_mask_prior_art_visibility",
            "status": "PASS_PRIOR_ART_RISK_VISIBLE" if shared_mask_seen else "MISSING_PRIOR_ART_ACCESS",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": status_list(rows, shared_mask_roles),
        },
        {
            "gate": "adjacent_incomplete_ntt_visibility",
            "status": "PASS_ADJACENT_VISIBLE" if adjacent_seen else "MISSING_ADJACENT_ACCESS",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": status_list(rows, adjacent_roles),
        },
        {
            "gate": "amortized_bs_lineage_visibility",
            "status": "PASS_LINEAGE_VISIBLE" if lineage_seen else "MISSING_LINEAGE_ACCESS",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": status_list(rows, lineage_roles),
        },
        {
            "gate": "novelty_claim_gate",
            "status": "BLOCK_NOVELTY_CLAIM_PENDING_MANUAL_REVIEW",
            "evidence": rel(out_dir / "access_probe.csv"),
            "detail": (
                "Shared-mask prior-art visibility is recorded, but manual full-text "
                "claim-to-source review is still required before any novelty upgrade."
            ),
        },
        {
            "gate": "related_work_decision",
            "status": "SCOPED_RELATED_WORK_REFRESHED__NOVELTY_STILL_BLOCKED",
            "evidence": rel(out_dir / "summary.csv"),
            "detail": (
                "Machine source-access refresh completed; base full text remains "
                "blocked in this environment and novelty claims remain blocked."
            ),
        },
    ]
    return summary


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_doc(out_dir: Path, rows: List[Dict[str, str]], summary: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage 27 Related-Work Access Probe Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "This probe refreshes related-work source access for the PVW/MAT-SAB",
        "novelty boundary. It records access state only; it does not perform",
        "manual claim-to-source verification and does not upgrade novelty,",
        "theorem-level 2025/686 citations, or all-parameter claims.",
        "",
        "## Summary",
        "",
        "| gate | status | detail |",
        "|---|---|---|",
    ]
    for row in summary:
        lines.append(f"| {row['gate']} | {row['status']} | {row['detail']} |")

    lines.extend(
        [
            "",
            "## Access Matrix",
            "",
            "| source | role | status | url |",
            "|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(f"| {row['source_id']} | {row['role']} | {row['status']} | {row['url']} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The safe claim remains a scoped engineering/systems claim. The probe",
            "records visible shared-mask prior-art risk and adjacent amortized",
            "bootstrapping sources, while keeping novelty and theorem-level",
            "citation claims blocked until full texts are manually reviewed.",
            "",
        ]
    )
    DOC.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--agent", default="Mozilla/5.0 stage27-related-work-probe")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    rows = [probe(source, args.agent, args.timeout, args.retries) for source in SOURCES]
    summary = build_summary(rows, out_dir)

    write_csv(
        out_dir / "access_probe.csv",
        rows,
        [
            "source_id",
            "work",
            "role",
            "url",
            "http_status",
            "content_type",
            "sample_bytes",
            "effective_url",
            "status",
            "notes",
        ],
    )
    write_csv(out_dir / "summary.csv", summary, ["gate", "status", "evidence", "detail"])
    write_doc(out_dir, rows, summary)

    decision = next(row for row in summary if row["gate"] == "related_work_decision")
    print(f"Stage 27 related-work access probe: {rel(out_dir / 'summary.csv')}")
    print(f"Stage 27 related-work access log: {rel(DOC)}")
    print(f"Decision: {decision['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
