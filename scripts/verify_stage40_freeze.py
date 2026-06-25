#!/usr/bin/env python3
"""Verify the Stage 40 scoped freeze package without regenerating it."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
FREEZE_SUMMARY = ROOT / "repro" / "stage40_final_freeze_summary.csv"
FREEZE_MANIFEST = ROOT / "repro" / "stage40_final_freeze_manifest.csv"
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
STAGE35 = ROOT / "repro" / "stage35_completion_blockers.csv"
STAGE39 = ROOT / "repro" / "stage39_variant_triage.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"
OUT_MD = ROOT / "docs" / "stage40_postfreeze_verify_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def row_by(rows: List[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def git_short() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def git_status_short() -> str:
    return subprocess.check_output(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
    )


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "evidence", "detail"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def build_checks(status_before_outputs: str) -> List[Dict[str, str]]:
    freeze = {row.get("item"): row for row in read_csv(FREEZE_SUMMARY)}
    manifest = read_csv(FREEZE_MANIFEST)
    audit = {row.get("item_id"): row for row in read_csv(FINAL_AUDIT)}
    blockers = read_csv(STAGE35)
    triage = {row.get("candidate_id"): row for row in read_csv(STAGE39)}
    run_log = read_csv(RUN_LOG)

    manifest_missing = [
        row.get("artifact", "")
        for row in manifest
        if row.get("exists") != "yes" or not (ROOT / row.get("artifact", "")).exists()
    ]
    external_blockers = [
        row
        for row in blockers
        if row.get("lane") == "external_blocker"
    ]
    stage40_run = any(row.get("run_id") == "stage40-final-freeze-001" for row in run_log)

    checks = [
        {
            "check": "verification_input_commit",
            "status": git_short(),
            "evidence": "git rev-parse --short HEAD",
            "detail": "Commit checked before writing verifier output artifacts.",
        },
        {
            "check": "worktree_clean_before_outputs",
            "status": "PASS" if not status_before_outputs.strip() else "FAIL_DIRTY",
            "evidence": "git status --short --untracked-files=all",
            "detail": status_before_outputs.replace("\n", "; ") if status_before_outputs.strip() else "tracked and untracked worktree was clean before verifier outputs.",
        },
        {
            "check": "stage40_decision",
            "status": "PASS" if freeze.get("stage40_decision", {}).get("status") == "SCOPED_FREEZE_READY_STRONGER_CLAIMS_BLOCKED" else "FAIL",
            "evidence": "repro/stage40_final_freeze_summary.csv",
            "detail": freeze.get("stage40_decision", {}).get("status", "MISSING"),
        },
        {
            "check": "final_audit_A9",
            "status": "PASS" if audit.get("A9", {}).get("status") == "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED" else "FAIL",
            "evidence": "repro/final_goal_completion_audit.csv",
            "detail": audit.get("A9", {}).get("status", "MISSING"),
        },
        {
            "check": "stage39_no_variant_promoted",
            "status": "PASS" if triage.get("S39-OVERALL", {}).get("decision") == "NO_NEW_VARIANT_PROMOTED_CURRENTLY" else "FAIL",
            "evidence": "repro/stage39_variant_triage.csv",
            "detail": triage.get("S39-OVERALL", {}).get("decision", "MISSING"),
        },
        {
            "check": "external_blockers_preserved",
            "status": "PASS" if len(external_blockers) >= 2 else "FAIL",
            "evidence": "repro/stage35_completion_blockers.csv",
            "detail": "; ".join(f"{row.get('item_id')}={row.get('status')}" for row in external_blockers),
        },
        {
            "check": "freeze_manifest_paths",
            "status": "PASS" if manifest and not manifest_missing else "FAIL",
            "evidence": "repro/stage40_final_freeze_manifest.csv",
            "detail": "all manifest paths exist" if not manifest_missing else "; ".join(manifest_missing),
        },
        {
            "check": "stage40_run_log_row",
            "status": "PASS" if stage40_run else "FAIL",
            "evidence": "repro/run_log.csv",
            "detail": "stage40-final-freeze-001 present" if stage40_run else "stage40-final-freeze-001 missing",
        },
    ]

    pass_all = all(row["status"] == "PASS" or row["check"] == "verification_input_commit" for row in checks)
    checks.append(
        {
            "check": "postfreeze_decision",
            "status": "PASS_POSTFREEZE_VERIFY" if pass_all else "FAIL_POSTFREEZE_VERIFY",
            "evidence": "repro/stage40_postfreeze_verify/summary.csv",
            "detail": "Scoped freeze is internally consistent; stronger claims remain blocked." if pass_all else "Inspect failing checks before relying on freeze.",
        }
    )
    return checks


def write_md(rows: List[Dict[str, str]]) -> None:
    lines = [
        "# Stage 40 Post-Freeze Verification Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "This verifier checks the frozen scoped engineering evidence chain "
        "without regenerating the Stage 40 freeze package.",
        "",
        "## Checks",
        "",
        "| check | status | evidence | detail |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['check']} | {row['status']} | {row['evidence']} | {row['detail']} |")
    decision = row_by(rows, "check", "postfreeze_decision")
    lines.extend(["", "## Decision", "", decision.get("detail", "No decision row generated.")])
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default="repro/stage40_postfreeze_verify",
        help="Output directory for the verifier summary CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status_before_outputs = git_status_short()
    rows = build_checks(status_before_outputs)
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    write_csv(out_dir / "summary.csv", rows)
    write_md(rows)
    decision = row_by(rows, "check", "postfreeze_decision")
    print(f"Wrote {(out_dir / 'summary.csv').relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    return 0 if decision.get("status") == "PASS_POSTFREEZE_VERIFY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
