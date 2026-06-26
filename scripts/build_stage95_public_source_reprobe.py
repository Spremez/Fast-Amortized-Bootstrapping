#!/usr/bin/env python3
"""Build the Stage95 public-source reprobe summary."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro" / "stage95_public_source_reprobe"
OUT_MD = ROOT / "docs" / "stage95_public_source_reprobe_log.md"

STAGE72_SUMMARY = ROOT / "repro" / "stage72_external_source_refresh" / "summary.csv"
STAGE72_ACCESS = ROOT / "repro" / "stage72_external_source_refresh" / "access_probe.csv"
STAGE91_CLAIMS = ROOT / "repro" / "stage91_final_package" / "claim_boundary.csv"
STAGE93 = ROOT / "repro" / "stage93_external_lane_attempt" / "summary.csv"
STAGE94 = ROOT / "repro" / "stage94_local_frontier_audit" / "summary.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def row(gate: str, status: str, evidence: str, detail: str, next_action: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def status_of(rows: Dict[str, Dict[str, str]], key: str) -> str:
    return rows.get(key, {}).get("status", "MISSING")


def build_route_rows() -> List[Dict[str, str]]:
    access = by_key(STAGE72_ACCESS, "source_id")
    routes = [
        "FAB686_EPRINT_PDF",
        "FAB686_EPRINT_PAGE",
        "FAB686_ACM_PDF",
        "FAB686_ACM_DOI_PAGE",
        "FAB686_AUTHOR_PAGE",
        "FAB686_AUTHOR_BIBTEX",
        "FAB686_AUTHOR_GUESSED_PDF",
        "FAB686_GITHUB_REPO",
    ]
    rows = []
    for source_id in routes:
        item = access.get(source_id, {})
        rows.append(
            {
                "source_id": source_id,
                "role": item.get("role", "MISSING"),
                "url": item.get("url", ""),
                "status": item.get("status", "MISSING"),
                "http_status": item.get("http_status", ""),
                "content_type": item.get("content_type", ""),
                "marker_present": item.get("marker_present", ""),
                "detail": item.get("detail", ""),
            }
        )
    return rows


def build_summary(out_dir: Path, route_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    stage72 = by_key(STAGE72_SUMMARY, "gate")
    stage91_claims = by_key(STAGE91_CLAIMS, "claim_id")
    stage93 = by_key(STAGE93, "gate")
    stage94 = by_key(STAGE94, "gate")

    stage94_ok = (
        status_of(stage94, "stage94_decision")
        == "PASS_STAGE94_LOCAL_FRONTIER_AUDIT_NO_NEW_HOTPATH"
    )
    stage72_ok = (
        status_of(stage72, "stage72_decision")
        == "PASS_EXTERNAL_SOURCE_REFRESH_STRONGER_CLAIMS_BLOCKED"
    )
    metadata_ok = (
        status_of(stage72, "stage72_author_metadata_route") == "PASS"
        and status_of(stage72, "stage72_doi_metadata_route") == "PASS"
        and status_of(stage72, "stage72_code_route") == "PASS"
    )
    fulltext_status = status_of(stage72, "stage72_official_fulltext_routes")
    pdf_accessible = any(
        r["source_id"] in {"FAB686_EPRINT_PDF", "FAB686_ACM_PDF"}
        and r["status"] == "PDF_ACCESSIBLE"
        for r in route_rows
    )
    stage93_ok = (
        status_of(stage93, "stage93_decision")
        == "PASS_STAGE93_EXTERNAL_LANE_ATTEMPT_RECORDED_STRONGER_CLAIMS_BLOCKED"
    )
    claim_statuses = [
        stage91_claims.get("C3", {}).get("status", "MISSING"),
        stage91_claims.get("C4", {}).get("status", "MISSING"),
        stage91_claims.get("C5", {}).get("status", "MISSING"),
    ]
    claims_blocked = all("BLOCKED" in item or "MISSING_OPTIONAL" in item for item in claim_statuses)

    rows = [
        row(
            "stage95_stage94_precondition",
            "PASS" if stage94_ok else "FAIL_STAGE94_PRECONDITION",
            rel(STAGE94),
            f"stage94_decision={status_of(stage94, 'stage94_decision')}",
            "Rerun Stage94 before relying on Stage95 if this gate fails.",
        ),
        row(
            "stage95_stage72_refresh",
            "PASS" if stage72_ok else "FAIL_STAGE72_REFRESH",
            rel(STAGE72_SUMMARY),
            f"stage72_decision={status_of(stage72, 'stage72_decision')}",
            "Rerun scripts/build_stage72_external_source_refresh.py before Stage95.",
        ),
        row(
            "stage95_public_metadata_routes",
            "PASS_METADATA_CODE_VISIBLE" if metadata_ok else "FAIL_METADATA_CODE_ROUTES",
            rel(STAGE72_SUMMARY),
            "author metadata, DOI metadata, and code routes are visible"
            if metadata_ok else "one or more public metadata/code routes failed",
            "Metadata/code routes are useful context but not theorem-level full text.",
        ),
        row(
            "stage95_direct_fulltext_routes",
            "FULLTEXT_AVAILABLE_REVIEW_REQUIRED" if pdf_accessible else "WAIT_FULLTEXT_ARTIFACT",
            rel(out_dir / "route_matrix.csv"),
            f"stage72_official_fulltext_routes={fulltext_status}",
            "Save and hash the accessible PDF, then run Stage38 with FAB686_FULLTEXT_PATH."
            if pdf_accessible else "Keep CB7 blocked until a PDF/text artifact is available locally.",
        ),
        row(
            "stage95_stage93_consistency",
            "PASS" if stage93_ok else "FAIL_STAGE93_CONSISTENCY",
            rel(STAGE93),
            f"stage93_decision={status_of(stage93, 'stage93_decision')}",
            "Rerun Stage93 if local full-text artifacts or native perf availability changed.",
        ),
        row(
            "stage95_claim_guard",
            "PASS_STRONGER_CLAIMS_BLOCKED" if claims_blocked and not pdf_accessible else "REVIEW_CLAIMS_REQUIRED",
            rel(STAGE91_CLAIMS),
            "C3/C4/C5 remain blocked under Stage91 claim boundary"
            if claims_blocked and not pdf_accessible else f"claim_statuses={claim_statuses}; pdf_accessible={pdf_accessible}",
            "Do not upgrade theorem-level, novelty, or hardware-counter claims before Stage38/manual review/native perf gates pass.",
        ),
    ]
    ok = all(item["status"].startswith("PASS") or item["status"] == "WAIT_FULLTEXT_ARTIFACT" for item in rows)
    rows.append(
        row(
            "stage95_decision",
            "PASS_STAGE95_PUBLIC_SOURCE_REPROBE_STRONGER_CLAIMS_BLOCKED"
            if ok and not pdf_accessible
            else "REVIEW_STAGE95_PUBLIC_SOURCE_REPROBE",
            rel(out_dir / "summary.csv"),
            "Public metadata/code routes are refreshed; direct full-text routes still do not provide a reviewed artifact, so stronger claims remain blocked."
            if ok and not pdf_accessible else "Inspect Stage95 route matrix and claim gates before changing blockers.",
            "Supply a local full-text artifact or native perf evidence to unlock stronger claims.",
        )
    )
    return rows


def artifact_rows(out_dir: Path) -> List[Dict[str, str]]:
    return [
        {"artifact": rel(out_dir / "summary.csv"), "purpose": "Stage95 gate summary", "producer": "scripts/build_stage95_public_source_reprobe.py"},
        {"artifact": rel(out_dir / "route_matrix.csv"), "purpose": "Public source route matrix", "producer": "scripts/build_stage95_public_source_reprobe.py"},
        {"artifact": rel(out_dir / "artifact_index.csv"), "purpose": "Stage95 artifact index", "producer": "scripts/build_stage95_public_source_reprobe.py"},
        {"artifact": rel(OUT_MD), "purpose": "Human-readable Stage95 log", "producer": "scripts/build_stage95_public_source_reprobe.py"},
    ]


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_md(out_dir: Path, summary: List[Dict[str, str]], routes: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    decision = summary[-1]
    lines = [
        "# Stage95 Public Source Reprobe Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "Stage95 reruns the public-source refresh and records whether public",
        "metadata or direct full-text routes can unlock CB7/CB6. Metadata/code",
        "visibility is not treated as reviewed full text.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next action |",
        "|---|---|---|---|---|",
    ]
    for item in summary:
        lines.append(
            f"| {item['gate']} | {item['status']} | {esc(item['evidence'])} | {esc(item['detail'])} | {esc(item['next_action'])} |"
        )
    lines.extend([
        "",
        "## Route Matrix",
        "",
        "| source | role | http | status | url |",
        "|---|---|---:|---|---|",
    ])
    for item in routes:
        lines.append(
            f"| {item['source_id']} | {item['role']} | {item['http_status']} | {item['status']} | {item['url']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    routes = build_route_rows()
    summary = build_summary(out_dir, routes)
    index = artifact_rows(out_dir)
    write_csv(out_dir / "route_matrix.csv", routes, [
        "source_id",
        "role",
        "url",
        "status",
        "http_status",
        "content_type",
        "marker_present",
        "detail",
    ])
    write_csv(out_dir / "summary.csv", summary, ["gate", "status", "evidence", "detail", "next_action"])
    write_csv(out_dir / "artifact_index.csv", index, ["artifact", "purpose", "producer"])
    write_md(out_dir, summary, routes)
    decision = summary[-1]["status"]
    print(f"Wrote {rel(out_dir / 'summary.csv')}")
    print(f"Wrote {rel(out_dir / 'route_matrix.csv')}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage95 public source reprobe: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
