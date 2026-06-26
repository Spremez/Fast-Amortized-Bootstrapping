#!/usr/bin/env python3
"""Build the Stage99 external blocker reprobe summary."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro" / "stage99_external_blocker_reprobe"
OUT_MD = ROOT / "docs" / "stage99_external_blocker_reprobe_log.md"
STAGE98 = ROOT / "repro" / "stage98_current_smoke_refresh" / "summary.csv"
CURRENT_GOAL = ROOT / "docs" / "current_codex_goal_sab_completion.md"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: Sequence[str]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def summary_row(gate: str, status: str, evidence: str, detail: str, next_action: str) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def native_status(out_dir: Path) -> Dict[str, str]:
    rows = by_key(out_dir / "native_perf_probe" / "summary.csv", "probe")
    gate = rows.get("hardware_counter_gate", {})
    status = gate.get("status", "MISSING")
    detail = gate.get("detail", "native perf summary missing")
    if status == "PASS":
        mapped = "PASS_NATIVE_PERF_COUNTERS_AVAILABLE"
        action = "Run the manual MAT-AVX512 counter attribution review before upgrading theory wording."
    elif status == "READY_FOR_BENCH":
        mapped = "RECORDED_NATIVE_PERF_SMOKE_READY_BENCH_REQUIRED"
        action = "Rerun Stage28 with STAGE28_RUN_BENCH=1 before hardware-counter attribution."
    else:
        mapped = "RECORDED_WAIT_NATIVE_PERF"
        action = "Rerun on native Linux/perf or install usable perf tools before claiming MAT-AVX512 load/store attribution."
    return {
        "status": mapped,
        "detail": f"stage28_hardware_counter_gate={status}; {detail}",
        "evidence": rel(out_dir / "native_perf_probe" / "summary.csv"),
        "next_action": action,
    }


def route_matrix(out_dir: Path) -> List[Dict[str, str]]:
    access = read_csv(out_dir / "citation_probe" / "access_probe.csv")
    rows: List[Dict[str, str]] = []
    for item in access:
        route_status = item.get("status", "MISSING")
        if route_status == "PDF_ACCESSIBLE":
            effect = "route-visible; save/register full text and run Stage38 before theorem-level citation"
        elif route_status == "METADATA_OR_HTML_ONLY":
            effect = "metadata/html only; does not unlock CB7"
        elif route_status.startswith("BLOCKED") or route_status.startswith("HTTP_"):
            effect = "blocked/unavailable direct route; CB7 remains waiting"
        else:
            effect = "diagnostic route status only"
        rows.append(
            {
                "route_id": item.get("id", ""),
                "url": item.get("url", ""),
                "http_code": item.get("http_code", ""),
                "content_type": item.get("content_type", ""),
                "size_download": item.get("size_download", ""),
                "effective_url": item.get("effective_url", ""),
                "status": route_status,
                "claim_effect": effect,
            }
        )
    return rows


def fulltext_status(out_dir: Path) -> Dict[str, str]:
    citation = by_key(out_dir / "citation_probe" / "summary.csv", "gate")
    direct_pdf = citation.get("direct_pdf_access", {})
    direct_pdf_status = direct_pdf.get("status", "MISSING")
    direct_pdf_detail = direct_pdf.get("detail", "")

    local_rows = read_csv(out_dir / "local_fulltext_search.csv")
    found = [
        row for row in local_rows
        if row.get("status", "").startswith("FOUND_")
    ]
    if found:
        mapped = "RECORDED_FULLTEXT_CANDIDATE_REVIEW_REQUIRED"
        detail = f"local_candidate_count={len(found)}; direct_pdf_access={direct_pdf_status}; {direct_pdf_detail}"
        action = "Run Stage38 with FAB686_FULLTEXT_PATH pointing at the intended artifact, then perform source-anchor review."
    elif direct_pdf_status == "PASS":
        mapped = "RECORDED_PDF_ROUTE_AVAILABLE_FULLTEXT_REVIEW_REQUIRED"
        detail = f"direct_pdf_access={direct_pdf_status}; {direct_pdf_detail}; no local reviewed artifact registered by Stage99"
        action = "Save/register the allowed full-text artifact and run Stage38 before theorem-level citations."
    else:
        mapped = "RECORDED_WAIT_EXTERNAL_FULLTEXT"
        detail = f"direct_pdf_access={direct_pdf_status}; {direct_pdf_detail}; no local candidate found"
        action = "Provide FAB686_FULLTEXT_PATH or rerun public-source/full-text probes later."
    return {
        "status": mapped,
        "detail": detail,
        "evidence": f"{rel(out_dir / 'citation_probe' / 'summary.csv')}; {rel(out_dir / 'local_fulltext_search.csv')}",
        "next_action": action,
    }


def build_summary(out_dir: Path) -> List[Dict[str, str]]:
    stage98 = by_key(STAGE98, "gate")
    stage98_status = stage98.get("stage98_decision", {}).get("status", "MISSING")
    stage98_ok = stage98_status == "PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH"
    native = native_status(out_dir)
    fulltext = fulltext_status(out_dir)
    routes = route_matrix(out_dir)
    route_count = len(routes)
    pdf_routes = [r for r in routes if r.get("status") == "PDF_ACCESSIBLE"]
    has_fulltext_candidate = fulltext["status"] in {
        "RECORDED_FULLTEXT_CANDIDATE_REVIEW_REQUIRED",
        "RECORDED_PDF_ROUTE_AVAILABLE_FULLTEXT_REVIEW_REQUIRED",
    }

    rows = [
        summary_row(
            "stage99_stage98_precondition",
            "PASS" if stage98_ok else "FAIL_STAGE98_PRECONDITION",
            rel(STAGE98),
            f"stage98_decision={stage98_status}",
            "Refresh Stage98 before interpreting external blocker state.",
        ),
        summary_row(
            "stage99_native_perf_reprobe",
            native["status"],
            native["evidence"],
            native["detail"],
            native["next_action"],
        ),
        summary_row(
            "stage99_fulltext_reprobe",
            fulltext["status"],
            fulltext["evidence"],
            fulltext["detail"],
            fulltext["next_action"],
        ),
        summary_row(
            "stage99_public_route_matrix",
            "PASS_PUBLIC_ROUTES_RECORDED" if route_count else "REVIEW_PUBLIC_ROUTES_MISSING",
            rel(out_dir / "route_matrix.csv"),
            f"route_count={route_count}; pdf_route_count={len(pdf_routes)}",
            "Treat route visibility as access context only; run Stage38/manual review before source claims.",
        ),
        summary_row(
            "stage99_novelty_review_gate",
            "RECORDED_WAIT_NOVELTY_REVIEW",
            rel(CURRENT_GOAL),
            "Novelty/related-work distinction still requires manual full-text source-anchor review.",
            "Run related-work/source review after full text and references are available.",
        ),
        summary_row(
            "stage99_claim_guard",
            "PASS_STRONGER_CLAIMS_BLOCKED_UNTIL_EXTERNAL_REVIEW",
            rel(CURRENT_GOAL),
            "Stage99 is an external-blocker reprobe only; it does not upgrade speedup, theorem-level, novelty, or MAT-AVX512 optimality claims.",
            "Keep final status scoped unless CB5/CB6/CB7 are explicitly resolved.",
        ),
    ]
    ok = stage98_ok and route_count > 0
    if ok and has_fulltext_candidate:
        decision = "PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_REVIEW_REQUIRED"
        detail = "Stage99 found a route or local candidate that still requires Stage38/manual review before claim upgrade."
    elif ok:
        decision = "PASS_STAGE99_EXTERNAL_BLOCKERS_REPROBED_STRONGER_CLAIMS_BLOCKED"
        detail = "Stage99 records the post-Stage98 external blocker state; native perf/full-text/novelty claims remain blocked."
    else:
        decision = "REVIEW_STAGE99_EXTERNAL_BLOCKER_REPROBE"
        detail = "Stage99 preconditions or route probes are incomplete."
    rows.append(
        summary_row(
            "stage99_decision",
            decision,
            rel(out_dir / "summary.csv"),
            detail,
            "Use Stage99 as the latest external-blocker reprobe after Stage98.",
        )
    )
    return rows


def artifact_rows(out_dir: Path) -> List[Dict[str, str]]:
    artifacts = [
        (CURRENT_GOAL, "Current Codex goal and completion route"),
        (ROOT / "experiments" / "stage99_external_blocker_reprobe_plan.md", "Stage99 experiment plan"),
        (ROOT / "scripts" / "run_stage99_external_blocker_reprobe.sh", "Stage99 runner"),
        (ROOT / "scripts" / "build_stage99_external_blocker_reprobe.py", "Stage99 summary builder"),
        (OUT_MD, "Human-readable Stage99 log"),
        (out_dir / "summary.csv", "Stage99 gate summary"),
        (out_dir / "route_matrix.csv", "Public route matrix distilled from Stage27"),
        (out_dir / "local_fulltext_search.csv", "Local full-text candidate search"),
        (out_dir / "artifact_index.csv", "Stage99 artifact index"),
        (out_dir / "stage99_run.log", "Stage99 wrapper log"),
        (out_dir / "native_perf_probe.log", "Native perf probe wrapper log"),
        (out_dir / "citation_probe.log", "Citation/source probe wrapper log"),
        (out_dir / "native_perf_probe" / "summary.csv", "Stage28 native perf summary under Stage99"),
        (out_dir / "native_perf_probe" / "environment.log", "Stage99 native perf environment"),
        (out_dir / "native_perf_probe" / "perf_smoke.log", "Stage99 native perf smoke log"),
        (out_dir / "citation_probe" / "summary.csv", "Stage27 citation summary under Stage99"),
        (out_dir / "citation_probe" / "access_probe.csv", "Stage27 access probe under Stage99"),
    ]
    return [
        {
            "artifact": rel(path),
            "purpose": purpose,
            "producer": "scripts/build_stage99_external_blocker_reprobe.py"
            if "summary" in purpose.lower() or path == OUT_MD or path.name in {"artifact_index.csv", "route_matrix.csv"}
            else "scripts/run_stage99_external_blocker_reprobe.sh",
        }
        for path, purpose in artifacts
    ]


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_md(summary: List[Dict[str, str]]) -> None:
    decision = summary[-1]
    lines = [
        "# Stage99 External Blocker Reprobe Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "Stage99 refreshes external blocker state after the Stage98 current-head",
        "smoke gate. It does not change SAB code, does not run a complete-SAB",
        "benchmark, and does not upgrade speedup, novelty, theorem-level, or",
        "MAT-AVX512 optimality claims.",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next action |",
        "|---|---|---|---|---|",
    ]
    for row in summary:
        lines.append(
            f"| {row['gate']} | {row['status']} | {esc(row['evidence'])} | {esc(row['detail'])} | {esc(row['next_action'])} |"
        )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
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

    routes = route_matrix(out_dir)
    write_csv(
        out_dir / "route_matrix.csv",
        routes,
        ["route_id", "url", "http_code", "content_type", "size_download", "effective_url", "status", "claim_effect"],
    )
    summary = build_summary(out_dir)
    write_csv(
        out_dir / "summary.csv",
        summary,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_csv(out_dir / "artifact_index.csv", artifact_rows(out_dir), ["artifact", "purpose", "producer"])
    write_md(summary)
    decision = summary[-1]["status"]
    print(f"Wrote {rel(out_dir / 'summary.csv')}")
    print(f"Wrote {rel(out_dir / 'route_matrix.csv')}")
    print(f"Wrote {rel(out_dir / 'artifact_index.csv')}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage99 external blocker reprobe: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
