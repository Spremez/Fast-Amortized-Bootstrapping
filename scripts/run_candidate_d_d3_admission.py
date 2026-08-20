#!/usr/bin/env python3
"""Deterministic Candidate D D3 admission stage runner.

Implements the Tasks 7-8 D3 replay contract registered in
``scripts/run_candidate_d_admission.py``. Reads only committed sources under
``--root`` and writes exactly the nine canonical outputs plus the stage
replay manifest under ``--output-root``. No clocks, no platform data.
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

from research.mat_sab.candidate_d_admission import run_d3_admission  # noqa: E402

REPLAY_MANIFEST_SCHEMA = "candidate-d-stage-replay-v1"

D3_SUMMARY_FIELDS = (
    "decision",
    "binding_status",
    "security_status",
    "noise_status",
    "complete_cost_status",
    "resource_status",
    "pessimistic_projection",
)
D3_BINDING_FIELDS = (
    "plaintext_bits",
    "delta_integer",
    "delta_torus",
    "coefficient_min",
    "coefficient_max",
    "checker_min",
    "checker_max",
    "binder_operation",
    "status",
)
D3_SECURITY_FIELDS = ("object", "realization", "assumption", "status")
D3_NOISE_FIELDS = ("case", "value", "limit", "source_anchor", "status")
D3_STRUCTURAL_FIELDS = (
    "variant",
    "r",
    "g",
    "selector_events",
    "products_per_event",
    "selector_ring_products",
    "materialized_components",
    "late_binding_products",
    "ncmux_events",
    "sub_a_calls",
    "status",
)
D3_AMDAHL_FIELDS = (
    "scenario",
    "complete_ratio_vs_b1",
    "speedup_vs_b1",
    "ep_ratio",
    "materialization_ratio",
    "automorphism_ratio",
    "late_binding_us",
    "status",
)
D3_RESOURCE_FIELDS = (
    "variant",
    "selector_key_bytes",
    "automorphism_key_bytes",
    "operator_state_bytes",
    "scratch_bytes",
    "output_bytes",
    "rerandomization_bytes",
    "keygen_work",
    "late_binding_transforms",
    "status",
)

CANONICAL_OUTPUTS = (
    "theory_checks/candidate_d_security_noise.md",
    "theory_checks/candidate_d_complete_cost.md",
    "repro/candidate_d_admission/binding_domain.csv",
    "repro/candidate_d_admission/security_object_map.csv",
    "repro/candidate_d_admission/noise_bound.csv",
    "repro/candidate_d_admission/structural_cost.csv",
    "repro/candidate_d_admission/amdahl_projection.csv",
    "repro/candidate_d_admission/resource_projection.csv",
    "repro/candidate_d_admission/d3_summary.csv",
)


def _csv_bytes(fields, rows) -> bytes:
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

    result = run_d3_admission(checkout)
    summary_row = {
        "decision": result.decision,
        "binding_status": result.binding_status,
        "security_status": result.security_status,
        "noise_status": result.noise_status,
        "complete_cost_status": result.complete_cost_status,
        "resource_status": result.resource_status,
        "pessimistic_projection": result.pessimistic_projection,
    }
    _write_output(
        output_root,
        "theory_checks/candidate_d_security_noise.md",
        result.security_noise_markdown.encode("utf-8"),
    )
    _write_output(
        output_root,
        "theory_checks/candidate_d_complete_cost.md",
        result.complete_cost_markdown.encode("utf-8"),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/binding_domain.csv",
        _csv_bytes(D3_BINDING_FIELDS, result.binding_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/security_object_map.csv",
        _csv_bytes(D3_SECURITY_FIELDS, result.security_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/noise_bound.csv",
        _csv_bytes(D3_NOISE_FIELDS, result.noise_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/structural_cost.csv",
        _csv_bytes(D3_STRUCTURAL_FIELDS, result.structural_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/amdahl_projection.csv",
        _csv_bytes(D3_AMDAHL_FIELDS, result.amdahl_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/resource_projection.csv",
        _csv_bytes(D3_RESOURCE_FIELDS, result.resource_rows),
    )
    _write_output(
        output_root,
        "repro/candidate_d_admission/d3_summary.csv",
        _csv_bytes(D3_SUMMARY_FIELDS, (summary_row,)),
    )
    manifest = {
        "schema": REPLAY_MANIFEST_SCHEMA,
        "stage": "D3",
        "input_commit": arguments.input_commit,
        "controller_commit": arguments.controller_commit,
        "decision": result.decision,
        "canonical_outputs": list(CANONICAL_OUTPUTS),
        "scientific_authority": True,
    }
    _write_output(
        output_root,
        "candidate_d_stage_replay.json",
        (
            json.dumps(manifest, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("ascii"),
    )
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
