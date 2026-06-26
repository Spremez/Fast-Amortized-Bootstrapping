#!/usr/bin/env python3
"""Build the Stage98 current-head smoke refresh summary."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro" / "stage98_current_smoke_refresh"
OUT_MD = ROOT / "docs" / "stage98_current_smoke_refresh_log.md"
STAGE97 = ROOT / "repro" / "stage97_source_delta_guard" / "summary.csv"

EXPECTED_RAW = {
    "scalar_binary_full_run": "PASS",
    "active_pvw_target_full_gate": "PASS",
    "backend_pvw_target_full_gate": "PASS",
    "scalar_ternary_build": "PASS",
}


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


def log_exists(row: Dict[str, str], field: str) -> bool:
    value = row.get(field, "")
    return not value or (ROOT / value).exists()


def build_summary(out_dir: Path) -> List[Dict[str, str]]:
    stage97 = by_key(STAGE97, "gate")
    stage97_status = stage97.get("stage97_decision", {}).get("status", "MISSING")
    raw_path = out_dir / "raw_smoke.csv"
    raw = {row.get("step", ""): row for row in read_csv(raw_path)}

    raw_problems = []
    for step, expected in EXPECTED_RAW.items():
        got = raw.get(step, {}).get("status", "MISSING")
        if got != expected:
            raw_problems.append(f"{step}:status={got}")
        elif not log_exists(raw[step], "build_log") or not log_exists(raw[step], "run_log"):
            raw_problems.append(f"{step}:missing_log")

    stage97_ok = stage97_status == "PASS_STAGE97_SOURCE_DELTA_GUARD_SCALAR_DEFAULT_SEPARATED"
    scalar_ok = raw.get("scalar_binary_full_run", {}).get("status") == "PASS"
    active_ok = raw.get("active_pvw_target_full_gate", {}).get("status") == "PASS"
    backend_ok = raw.get("backend_pvw_target_full_gate", {}).get("status") == "PASS"
    ternary_ok = raw.get("scalar_ternary_build", {}).get("status") == "PASS"

    rows = [
        summary_row(
            "stage98_stage97_precondition",
            "PASS" if stage97_ok else "FAIL_STAGE97_PRECONDITION",
            rel(STAGE97),
            f"stage97_decision={stage97_status}",
            "Refresh Stage97 before interpreting current-head smoke continuity.",
        ),
        summary_row(
            "stage98_scalar_binary_smoke",
            "PASS_SCALAR_BINARY_FULL_RUN" if scalar_ok else "FAIL_SCALAR_BINARY_FULL_RUN",
            rel(raw_path),
            raw.get("scalar_binary_full_run", {}).get("notes", "missing scalar binary row"),
            "Debug scalar/default SAB before continuing PVW/MAT-SAB optimization.",
        ),
        summary_row(
            "stage98_active_pvw_target_smoke",
            "PASS_ACTIVE_PVW_TARGET_GATE" if active_ok else "FAIL_ACTIVE_PVW_TARGET_GATE",
            rel(raw_path),
            raw.get("active_pvw_target_full_gate", {}).get("notes", "missing active PVW row"),
            "Debug explicit active-buffer PVW path before relying on current-head continuity.",
        ),
        summary_row(
            "stage98_backend_pvw_target_smoke",
            "PASS_BACKEND_PVW_TARGET_GATE" if backend_ok else "FAIL_BACKEND_PVW_TARGET_GATE",
            rel(raw_path),
            raw.get("backend_pvw_target_full_gate", {}).get("notes", "missing backend PVW row"),
            "Debug explicit H14 backend PVW path before relying on current-head continuity.",
        ),
        summary_row(
            "stage98_scalar_ternary_build",
            "PASS_SCALAR_TERNARY_BUILD" if ternary_ok else "FAIL_SCALAR_TERNARY_BUILD",
            rel(raw_path),
            raw.get("scalar_ternary_build", {}).get("notes", "missing scalar ternary row"),
            "Inspect scalar non-binary build independence before changing branch support claims.",
        ),
        summary_row(
            "stage98_raw_log_guard",
            "PASS_RAW_LOGS_PRESENT" if not raw_problems else "FAIL_RAW_LOG_GUARD",
            rel(raw_path),
            "all expected smoke rows and logs are present" if not raw_problems else "; ".join(raw_problems),
            "Keep raw build/run logs with the Stage98 repro package.",
        ),
        summary_row(
            "stage98_claim_guard",
            "PASS_CURRENT_SMOKE_ONLY_NO_SPEEDUP_CLAIM",
            rel(OUT_MD),
            "Stage98 is a current-head smoke refresh only; it does not upgrade speedup, novelty, theorem-level, or hardware-counter claims.",
            "Keep Stage98 out of performance tables except as current-head continuity evidence.",
        ),
    ]
    ok = all(row["status"].startswith("PASS") for row in rows)
    rows.append(
        summary_row(
            "stage98_decision",
            "PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH"
            if ok
            else "REVIEW_STAGE98_CURRENT_HEAD_SMOKE_REFRESH",
            rel(out_dir / "summary.csv"),
            "Current-head scalar/default, active PVW target, backend PVW target, and scalar ternary smoke checks pass."
            if ok
            else "Inspect failed Stage98 gates before claiming current-head continuity.",
            "Use Stage98 as the latest current-head smoke refresh after Stage97.",
        )
    )
    return rows


def artifact_rows(out_dir: Path) -> List[Dict[str, str]]:
    raw_rows = read_csv(out_dir / "raw_smoke.csv")
    rows = [
        {"artifact": rel(out_dir / "summary.csv"), "purpose": "Stage98 gate summary", "producer": "scripts/build_stage98_current_smoke_refresh.py"},
        {"artifact": rel(out_dir / "raw_smoke.csv"), "purpose": "Raw current-head smoke matrix", "producer": "scripts/run_stage98_current_smoke_refresh.sh"},
        {"artifact": rel(out_dir / "stage98_run.log"), "purpose": "Stage98 wrapper log", "producer": "scripts/run_stage98_current_smoke_refresh.sh"},
        {"artifact": rel(out_dir / "artifact_index.csv"), "purpose": "Stage98 artifact index", "producer": "scripts/build_stage98_current_smoke_refresh.py"},
        {"artifact": rel(OUT_MD), "purpose": "Human-readable Stage98 log", "producer": "scripts/build_stage98_current_smoke_refresh.py"},
    ]
    for item in raw_rows:
        for field, purpose in [("build_log", "build log"), ("run_log", "run log")]:
            value = item.get(field, "")
            if value:
                rows.append(
                    {
                        "artifact": value,
                        "purpose": f"{item.get('step', 'unknown')} {purpose}",
                        "producer": "scripts/run_stage98_current_smoke_refresh.sh",
                    }
                )
    return rows


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_md(out_dir: Path, summary: List[Dict[str, str]]) -> None:
    decision = summary[-1]
    lines = [
        "# Stage98 Current-Head Smoke Refresh Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Decision",
        "",
        f"`{decision['status']}`",
        "",
        decision["detail"],
        "",
        "Stage98 is a current-head continuity gate. It does not implement a new",
        "SAB variant, run a performance benchmark, or upgrade speedup, novelty,",
        "theorem-level, or hardware-counter claims.",
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

    summary = build_summary(out_dir)
    index = artifact_rows(out_dir)
    write_csv(
        out_dir / "summary.csv",
        summary,
        ["gate", "status", "evidence", "detail", "next_action"],
    )
    write_csv(out_dir / "artifact_index.csv", index, ["artifact", "purpose", "producer"])
    write_md(out_dir, summary)
    decision = summary[-1]["status"]
    print(f"Wrote {rel(out_dir / 'summary.csv')}")
    print(f"Wrote {rel(out_dir / 'artifact_index.csv')}")
    print(f"Wrote {rel(OUT_MD)}")
    print(f"Stage98 current-head smoke refresh: {decision}")
    return 0 if decision.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
