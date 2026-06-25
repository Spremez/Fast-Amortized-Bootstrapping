#!/usr/bin/env python3
"""Build the Stage 40 final scoped freeze report."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
FINAL_AUDIT = ROOT / "repro" / "final_goal_completion_audit.csv"
STAGE35 = ROOT / "repro" / "stage35_completion_blockers.csv"
STAGE39 = ROOT / "repro" / "stage39_variant_triage.csv"
RUN_LOG = ROOT / "repro" / "run_log.csv"
OUT_SUMMARY = ROOT / "repro" / "stage40_final_freeze_summary.csv"
OUT_MANIFEST = ROOT / "repro" / "stage40_final_freeze_manifest.csv"
OUT_MD = ROOT / "docs" / "stage40_final_freeze_report.md"


REQUIRED_ARTIFACTS = [
    "docs/stage27_final_engineering_report.md",
    "docs/final_goal_completion_audit.md",
    "docs/stage35_completion_blocker_matrix.md",
    "docs/stage36_high_stat_expansion_log.md",
    "docs/stage37_native_perf_counter_log.md",
    "docs/stage38_fulltext_review_log.md",
    "docs/stage39_variant_triage_log.md",
    "repro/final_goal_completion_audit.csv",
    "repro/stage35_completion_blockers.csv",
    "repro/stage36_target_perf_summary.csv",
    "repro/stage36_stage_noise_seeds10/aggregate.csv",
    "repro/stage36_resource_summary.csv",
    "repro/stage37_native_perf_counter_audit/summary.csv",
    "repro/stage38_fulltext_review_gate/summary.csv",
    "repro/stage39_variant_triage.csv",
]


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
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def write_csv(path: Path, rows: Iterable[Dict[str, str]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_manifest() -> List[Dict[str, str]]:
    rows = []
    for rel_path in REQUIRED_ARTIFACTS:
        path = ROOT / rel_path
        rows.append(
            {
                "artifact": rel_path,
                "exists": "yes" if path.exists() else "no",
                "size_bytes": str(path.stat().st_size) if path.exists() else "",
            }
        )
    return rows


def main() -> int:
    audit = read_csv(FINAL_AUDIT)
    blockers = read_csv(STAGE35)
    triage = read_csv(STAGE39)
    run_log = read_csv(RUN_LOG)

    a9 = row_by(audit, "item_id", "A9")
    a8 = row_by(audit, "item_id", "A8")
    a8b = row_by(audit, "item_id", "A8b")
    s39 = row_by(triage, "candidate_id", "S39-OVERALL")
    manifest = build_manifest()
    manifest_ok = all(row["exists"] == "yes" for row in manifest)
    external_blockers = [
        row
        for row in blockers
        if row.get("lane") == "external_blocker"
    ]
    run_log_stage40_exists = any(row.get("run_id") == "stage40-final-freeze-001" for row in run_log)

    scoped_ready = a9.get("status") == "SCOPED_ENGINEERING_CHAIN_READY__STRONGER_CLAIMS_BLOCKED"
    triage_ready = s39.get("decision") == "NO_NEW_VARIANT_PROMOTED_CURRENTLY"
    blockers_preserved = len(external_blockers) >= 2
    decision = (
        "SCOPED_FREEZE_READY_STRONGER_CLAIMS_BLOCKED"
        if scoped_ready and triage_ready and blockers_preserved and manifest_ok
        else "FREEZE_NOT_READY"
    )

    summary = [
        {
            "item": "freeze_input_commit",
            "status": git_short(),
            "evidence": "git rev-parse --short HEAD",
            "detail": (
                "Commit state observed before writing Stage 40 artifacts. "
                "The artifact commit is the git commit that contains these generated files."
            ),
        },
        {
            "item": "final_audit_A9",
            "status": a9.get("status", "MISSING"),
            "evidence": "repro/final_goal_completion_audit.csv",
            "detail": a9.get("scope", ""),
        },
        {
            "item": "stage39_overall",
            "status": s39.get("decision", "MISSING"),
            "evidence": "repro/stage39_variant_triage.csv",
            "detail": s39.get("reason", ""),
        },
        {
            "item": "external_blockers",
            "status": "PRESERVED" if blockers_preserved else "MISSING",
            "evidence": "repro/stage35_completion_blockers.csv",
            "detail": "; ".join(f"{row.get('item_id')}={row.get('status')}" for row in external_blockers),
        },
        {
            "item": "required_artifacts",
            "status": "PASS" if manifest_ok else "MISSING",
            "evidence": "repro/stage40_final_freeze_manifest.csv",
            "detail": "All required freeze artifacts exist." if manifest_ok else "One or more required artifacts are missing.",
        },
        {
            "item": "run_log_registration",
            "status": "PENDING_THIS_COMMIT" if not run_log_stage40_exists else "PRESENT",
            "evidence": "repro/run_log.csv",
            "detail": (
                "Stage40 run_log row is present."
                if run_log_stage40_exists
                else "Stage40 run_log row is expected to be added with these artifacts."
            ),
        },
        {
            "item": "stage40_decision",
            "status": decision,
            "evidence": "repro/stage40_final_freeze_summary.csv",
            "detail": (
                "Freeze scoped engineering package only; stronger claims remain blocked."
                if decision.startswith("SCOPED_FREEZE")
                else "Fix missing evidence before freezing."
            ),
        },
    ]

    write_csv(
        OUT_MANIFEST,
        manifest,
        ["artifact", "exists", "size_bytes"],
    )
    write_csv(
        OUT_SUMMARY,
        summary,
        ["item", "status", "evidence", "detail"],
    )

    lines = [
        "# Stage 40 Final Scoped Freeze Report",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision}`",
        "",
        "The current package is a scoped engineering freeze for the tested "
        "binary PVW/MAT-SAB path. It is not a freeze for stronger novelty, "
        "theoretical-optimality, non-binary, or all-parameter claims.",
        "",
        "## Summary",
        "",
        "| item | status | detail |",
        "|---|---|---|",
    ]
    for row in summary:
        lines.append(f"| {row['item']} | {row['status']} | {row['detail']} |")

    lines.extend(
        [
            "",
            "## Required Artifacts",
            "",
            "| artifact | exists | size bytes |",
            "|---|---|---:|",
        ]
    )
    for row in manifest:
        lines.append(f"| {row['artifact']} | {row['exists']} | {row['size_bytes']} |")

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- MAT-AVX512 counter attribution: `{a8.get('status','MISSING')}`.",
            f"- External full-text/native evidence: `{a8b.get('status','MISSING')}`.",
            "- The scoped engineering SAB acceleration evidence can be reported with "
            "its tested parameters and backend.",
            "- Do not claim theorem-level 2025/686 support, novelty, non-binary support, "
            "all-parameter generality, or theoretical MAT-AVX512 optimality from this freeze.",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {OUT_SUMMARY.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MANIFEST.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
