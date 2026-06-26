#!/usr/bin/env python3
"""Build the Stage70 external-unlock preflight.

Stage70 does not run a SAB benchmark and does not upgrade any claim. It checks
whether the remaining external unlock inputs are present now, and records the
exact route for moving from the scoped engineering package to stronger
native-perf/full-text/novelty evidence when those inputs become available.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
STAGE59 = ROOT / "repro" / "stage59_completion_route_readiness.csv"
STAGE61 = ROOT / "repro" / "stage61_native_perf_unlock_probe" / "summary.csv"
STAGE62 = ROOT / "repro" / "stage62_fulltext_unlock_probe" / "unlock_summary.csv"
STAGE69 = ROOT / "repro" / "stage69_local_variant_feasibility.csv"
OUT_CSV = ROOT / "repro" / "stage70_external_unlock_preflight.csv"
OUT_MD = ROOT / "docs" / "stage70_external_unlock_preflight_log.md"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_key(path: Path, key: str) -> Dict[str, Dict[str, str]]:
    return {row.get(key, ""): row for row in read_csv(path)}


def row(
    gate: str,
    status: str,
    evidence: str,
    detail: str,
    next_action: str,
) -> Dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    }


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["gate", "status", "evidence", "detail", "next_action"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def fulltext_env_status() -> Dict[str, str]:
    raw = os.environ.get("FAB686_FULLTEXT_PATH", "").strip()
    if not raw:
        return {
            "status": "MISSING_ENV",
            "detail": "FAB686_FULLTEXT_PATH is not set in the current process.",
            "path": "",
        }
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    if not path.exists():
        return {
            "status": "PATH_NOT_FOUND",
            "detail": f"FAB686_FULLTEXT_PATH={path} does not exist.",
            "path": str(path),
        }
    if not path.is_file() or path.stat().st_size <= 0:
        return {
            "status": "INVALID_FILE",
            "detail": f"FAB686_FULLTEXT_PATH={path} is not a non-empty file.",
            "path": str(path),
        }
    return {
        "status": "AVAILABLE_UNREVIEWED",
        "detail": f"FAB686_FULLTEXT_PATH={path} exists and must be hashed/reviewed by Stage38.",
        "path": str(path),
    }


def build_rows() -> List[Dict[str, str]]:
    stage59 = by_key(STAGE59, "route_id")
    stage61 = by_key(STAGE61, "probe")
    stage62 = by_key(STAGE62, "gate")
    stage69 = by_key(STAGE69, "gate")
    fulltext_env = fulltext_env_status()

    r3 = stage59.get("S59-R3-NATIVE-PERF", {})
    r4 = stage59.get("S59-R4-FULLTEXT-686", {})
    r5 = stage59.get("S59-R5-NOVELTY-REVIEW", {})
    r6 = stage59.get("S59-R6-OPTIONAL-VARIANTS", {})

    native_gate = stage61.get("hardware_counter_gate", {}).get("status", "MISSING")
    perf_command = stage61.get("perf_command", {}).get("status", "MISSING")
    stage62_decision = stage62.get("stage62_decision", {}).get("status", "MISSING")
    stage69_decision = stage69.get("stage69_decision", {}).get("status", "MISSING")

    rows = [
        row(
            "stage70_route_inputs",
            "PASS" if all([r3, r4, r5, r6]) else "FAIL_ROUTE_MISSING",
            STAGE59.relative_to(ROOT).as_posix(),
            (
                f"R3={r3.get('status', 'MISSING')}; "
                f"R4={r4.get('status', 'MISSING')}; "
                f"R5={r5.get('status', 'MISSING')}; "
                f"R6={r6.get('status', 'MISSING')}"
            ),
            "Regenerate Stage59 if any route row is missing.",
        ),
        row(
            "stage70_native_perf_preflight",
            "WAIT_NATIVE_PERF"
            if native_gate in {"BLOCKED", "READY_FOR_BENCH", "MISSING"}
            else "READY_NATIVE_PERF_REVIEW",
            STAGE61.relative_to(ROOT).as_posix(),
            f"hardware_counter_gate={native_gate}; perf_command={perf_command}",
            "Run STAGE28_RUN_BENCH=1 bash scripts/run_stage28_native_perf_counter_gate.sh on native/perf-enabled Linux.",
        ),
        row(
            "stage70_fulltext_env_preflight",
            fulltext_env["status"],
            "FAB686_FULLTEXT_PATH",
            fulltext_env["detail"],
            "Set FAB686_FULLTEXT_PATH to a recognized 2025/686 full-text PDF and rerun Stage38/62.",
        ),
        row(
            "stage70_fulltext_stage62_preflight",
            "WAIT_FULLTEXT_ARTIFACT"
            if stage62_decision == "WAIT_FULLTEXT_ARTIFACT_MANUAL_REVIEW"
            else "READY_FULLTEXT_REVIEW",
            STAGE62.relative_to(ROOT).as_posix(),
            f"stage62_decision={stage62_decision}",
            "FAB686_FULLTEXT_PATH=/path/to/2025_686.pdf bash scripts/run_stage38_fulltext_review_gate.sh",
        ),
        row(
            "stage70_novelty_preflight",
            "WAIT_FULLTEXT_OR_MANUAL_REVIEW",
            f"{STAGE59.relative_to(ROOT).as_posix()}; {STAGE62.relative_to(ROOT).as_posix()}",
            f"novelty_route={r5.get('status', 'MISSING')}; fulltext={stage62_decision}",
            "After full-text/source anchors are available, rerun related-work and novelty review gates.",
        ),
        row(
            "stage70_local_variant_preflight",
            "NO_LOCAL_VARIANT_READY"
            if stage69_decision == "PASS_LOCAL_VARIANT_FEASIBILITY_AUDIT_STRONGER_CLAIMS_BLOCKED"
            else "REVIEW_LOCAL_VARIANT_ROUTE",
            STAGE69.relative_to(ROOT).as_posix(),
            f"stage69_decision={stage69_decision}",
            "Introduce a new falsifiable hypothesis before starting another local code variant.",
        ),
    ]

    ok = (
        rows[0]["status"] == "PASS"
        and rows[1]["status"] == "WAIT_NATIVE_PERF"
        and rows[2]["status"] in {"MISSING_ENV", "PATH_NOT_FOUND", "INVALID_FILE", "AVAILABLE_UNREVIEWED"}
        and rows[3]["status"] in {"WAIT_FULLTEXT_ARTIFACT", "READY_FULLTEXT_REVIEW"}
        and rows[4]["status"] == "WAIT_FULLTEXT_OR_MANUAL_REVIEW"
        and rows[5]["status"] == "NO_LOCAL_VARIANT_READY"
    )
    rows.append(
        row(
            "stage70_decision",
            "PASS_EXTERNAL_UNLOCK_PREFLIGHT_STRONGER_CLAIMS_BLOCKED"
            if ok
            else "FAIL_EXTERNAL_UNLOCK_PREFLIGHT",
            OUT_CSV.relative_to(ROOT).as_posix(),
            "External unlock route is explicit; current environment still lacks native perf and reviewed 2025/686 full text."
            if ok
            else "External unlock preflight is inconsistent.",
            "Do not mark the full goal complete until native perf/full-text/novelty gates are actually satisfied or scope is explicitly narrowed.",
        )
    )
    return rows


def write_md(rows: List[Dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage70 External Unlock Preflight Log",
        "",
        "Date: 2026-06-26",
        "",
        "## Purpose",
        "",
        "Stage70 records whether the remaining external inputs needed for",
        "stronger PVW/MAT-SAB claims are available now. It does not modify SAB",
        "code, run a benchmark, or upgrade any claim.",
        "",
        "## Official Source Routes",
        "",
        "- 2025/686 ePrint page: https://eprint.iacr.org/2025/686",
        "- DOI route: https://doi.org/10.1145/3719027.3765181",
        "- Public implementation route: https://github.com/antoniocgj/Fast-Amortized-Bootstrapping",
        "",
        "## Gates",
        "",
        "| gate | status | evidence | detail | next_action |",
        "|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            "| {gate} | {status} | {evidence} | {detail} | {next_action} |".format(
                **{k: item[k].replace("|", "\\|") for k in item}
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The scoped engineering evidence chain remains ready, but full goal",
            "completion still requires native performance-counter evidence, a",
            "registered and reviewed 2025/686 full text, and novelty/source-anchor",
            "review if stronger paper claims are desired.",
        ]
    )
    with OUT_MD.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(rows)
    decision = rows[-1]["status"]
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")
    print(f"Wrote {OUT_MD.relative_to(ROOT).as_posix()}")
    print(f"Stage70 external unlock preflight: {decision}")
    return 0 if decision.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
