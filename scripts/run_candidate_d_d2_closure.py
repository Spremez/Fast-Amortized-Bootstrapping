#!/usr/bin/env python3
"""Deterministic Candidate D D2 operator-closure stage runner.

Implements the Tasks 4-6 D2 replay contract registered in
``scripts/run_candidate_d_admission.py``. The runner reads only committed
sources under ``--root`` (inside the Task 9 replay boundary this is the
``--no-local`` checkout of ``--input-commit``) and writes exactly the six
canonical outputs under ``--output-root``:

    theory_checks/candidate_d_operator_closure.md
    repro/candidate_d_admission/d2_summary.csv
    repro/candidate_d_admission/closure_basis.csv
    repro/candidate_d_admission/phase_equivalence.csv
    repro/candidate_d_admission/negative_controls.csv
    repro/candidate_d_admission/schedule_trace.csv

Outputs embed no clocks or platform details: identical inputs and CLI
commits produce byte-identical outputs.
"""

from __future__ import annotations

import argparse
import csv
from io import StringIO
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.mat_sab.candidate_d_operator_closure import (  # noqa: E402
    run_closure_check,
)

REPLAY_MANIFEST_SCHEMA = "candidate-d-stage-replay-v1"

D2_SUMMARY_FIELDS = (
    "decision",
    "gamma_count",
    "phase_status",
    "negative_controls_status",
    "schedule_status",
    "equation_revisions_used",
)
D2_CLOSURE_FIELDS = (
    "basis_index",
    "automorphism_label",
    "gamma_count",
    "equation_revision",
    "search_status",
    "status",
)
D2_PHASE_FIELDS = (
    "N",
    "schedule_case",
    "basis_index",
    "operation",
    "accumulator_index",
    "selector_bit",
    "gamma_count",
    "matrix_rank",
    "expected_hash",
    "actual_hash",
    "status",
)
D2_NEGATIVE_FIELDS = ("control", "failed_invariant", "status")
D2_SCHEDULE_FIELDS = (
    "N",
    "schedule_case",
    "step",
    "operation",
    "accumulator_index",
    "selector_bit",
    "status",
)


def _csv_bytes(
    fields: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> bytes:
    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=fields, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _write_output(root: Path, relative: str, content: bytes) -> None:
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not destination.is_file():
        raise RuntimeError(f"output path is not a regular file: {relative}")
    destination.write_bytes(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--input-commit", required=True)
    parser.add_argument("--controller-commit", required=True)
    arguments = parser.parse_args()

    checkout = Path(arguments.root).resolve()
    output_root = Path(arguments.output_root).resolve()
    if not checkout.is_dir():
        raise SystemExit(f"checkout root is not a directory: {checkout}")
    output_root.mkdir(parents=True, exist_ok=True)
    for existing in output_root.rglob("*"):
        if existing.is_symlink() or not (
            existing.is_file() or existing.is_dir()
        ):
            raise SystemExit(
                "output root must contain only regular files and directories"
            )

    result = run_closure_check(checkout)
    summary_row = {
        "decision": result.decision,
        "gamma_count": str(result.gamma_count),
        "phase_status": result.phase_status,
        "negative_controls_status": result.negative_controls_status,
        "schedule_status": result.schedule_status,
        "equation_revisions_used": str(result.equation_revisions_used),
    }
    provenance = (
        "\n## Provenance\n\n"
        f"- input commit: `{arguments.input_commit}`\n"
        f"- controller commit: `{arguments.controller_commit}`\n"
        "- stage: D2 (exact operator closure)\n"
    )
    _write_output(
        output_root,
        "theory_checks/candidate_d_operator_closure.md",
        (result.report_markdown + provenance).encode("utf-8"),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/d2_summary.csv",
        _csv_bytes(D2_SUMMARY_FIELDS, (summary_row,)),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/closure_basis.csv",
        _csv_bytes(D2_CLOSURE_FIELDS, result.basis_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/phase_equivalence.csv",
        _csv_bytes(D2_PHASE_FIELDS, result.phase_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/negative_controls.csv",
        _csv_bytes(D2_NEGATIVE_FIELDS, result.control_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/schedule_trace.csv",
        _csv_bytes(D2_SCHEDULE_FIELDS, result.trace_rows),
    )
    manifest = {
        "schema": REPLAY_MANIFEST_SCHEMA,
        "stage": "D2",
        "input_commit": arguments.input_commit,
        "controller_commit": arguments.controller_commit,
        "decision": result.decision,
        "canonical_outputs": [
            "theory_checks/candidate_d_operator_closure.md",
            "repro/candidate_d_admission/d2_summary.csv",
            "repro/candidate_d_admission/closure_basis.csv",
            "repro/candidate_d_admission/phase_equivalence.csv",
            "repro/candidate_d_admission/negative_controls.csv",
            "repro/candidate_d_admission/schedule_trace.csv",
        ],
        "scientific_authority": True,
    }
    _write_output(
        output_root,
        "candidate_d_stage_replay.json",
        (
            json.dumps(
                manifest, sort_keys=True, separators=(",", ":"), indent=None
            )
            + "\n"
        ).encode("ascii"),
    )
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
