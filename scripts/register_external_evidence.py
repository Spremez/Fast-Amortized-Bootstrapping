#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "repro" / "external_evidence_intake"
OUT_CSV = OUT_DIR / "summary.csv"


def rel_or_abs(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_kind(path: Path) -> str:
    with path.open("rb") as f:
        head = f.read(8)
    if head.startswith(b"%PDF-"):
        return "pdf"
    if path.suffix.lower() in {".txt", ".md", ".tex"}:
        return "text"
    return "unknown"


def existing_evidence_row(evidence_id: str) -> dict[str, str] | None:
    if not OUT_CSV.exists():
        return None
    with OUT_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("evidence_id") == evidence_id and row.get("status") != "MISSING":
                return dict(row)
    return None


def read_stage28_gate(path: Path) -> str:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    for row in rows:
        if row.get("probe") == "hardware_counter_gate":
            return row.get("status", "MISSING")
    return "MISSING"


def evidence_row(evidence_id: str, input_path: str | None, kind: str) -> dict[str, str]:
    if not input_path:
        existing = existing_evidence_row(evidence_id)
        if existing:
            existing["detail"] = (
                existing.get("detail", "")
                + " Preserved because no replacement path was provided."
            ).strip()
            return existing
        return {
            "evidence_id": evidence_id,
            "status": "MISSING",
            "kind": kind,
            "path": "",
            "sha256": "",
            "size_bytes": "",
            "detail": "No path provided.",
        }

    path = Path(input_path)
    if not path.exists():
        return {
            "evidence_id": evidence_id,
            "status": "MISSING",
            "kind": kind,
            "path": str(path),
            "sha256": "",
            "size_bytes": "",
            "detail": "Provided path does not exist.",
        }

    digest = sha256_file(path)
    size = str(path.stat().st_size)

    if evidence_id == "fab686_fulltext":
        detected = file_kind(path)
        if detected in {"pdf", "text"}:
            status = "AVAILABLE_UNREVIEWED"
            detail = (
                "Full-text artifact registered. Manual theorem/algorithm/citation "
                "review is still required before claim upgrade."
            )
        else:
            status = "UNRECOGNIZED_FILE"
            detail = "Artifact exists but is not a recognized PDF/text source."
        kind = detected
    elif evidence_id == "stage28_native_perf_summary":
        try:
            gate = read_stage28_gate(path)
        except Exception as exc:
            gate = "PARSE_ERROR"
            detail = f"Could not parse Stage 28 summary: {exc}"
        else:
            if gate == "PASS":
                status = "PASS_COUNTER_ATTRIBUTION_AVAILABLE"
                detail = (
                    "Stage 28 hardware-counter summary reports PASS. Interpretation "
                    "with Stage 22 timings and objdump evidence is still required."
                )
            elif gate == "READY_FOR_BENCH":
                status = "COUNTER_SMOKE_ONLY"
                detail = "perf smoke passed, but heavy SAB benchmark counter evidence is missing."
            elif gate == "BLOCKED":
                status = "BLOCKED"
                detail = "Stage 28 summary reports blocked hardware-counter evidence."
            else:
                status = f"UNKNOWN_GATE_{gate}"
                detail = "Stage 28 summary did not report a recognized gate status."
    else:
        status = "AVAILABLE"
        detail = "External artifact registered."

    return {
        "evidence_id": evidence_id,
        "status": status,
        "kind": kind,
        "path": rel_or_abs(path),
        "sha256": digest,
        "size_bytes": size,
        "detail": detail,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register external evidence artifacts without upgrading claims automatically."
    )
    parser.add_argument(
        "--fab686-fulltext",
        default=os.environ.get("FAB686_FULLTEXT_PATH"),
        help="Path to a locally supplied 2025/686 full-text PDF/text artifact.",
    )
    parser.add_argument(
        "--stage28-native-perf-summary",
        default=os.environ.get("STAGE28_NATIVE_PERF_SUMMARY"),
        help="Path to a Stage 28 summary.csv from native/perf-enabled hardware-counter run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = [
        evidence_row("fab686_fulltext", args.fab686_fulltext, "paper_fulltext"),
        evidence_row(
            "stage28_native_perf_summary",
            args.stage28_native_perf_summary,
            "hardware_counter_summary",
        ),
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "evidence_id",
                "status",
                "kind",
                "path",
                "sha256",
                "size_bytes",
                "detail",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT_CSV.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
