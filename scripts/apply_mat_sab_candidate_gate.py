#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mat_sab_research_state import (
    load_state,
    transition_candidate,
    validate_state,
    write_state,
)
from scripts.run_candidate_a_star_cycle_gate import ADMIT, REJECT


HYPOTHESIS_MARKER = "H_candidate_a_star_cycle_mechanism:"
RUN_MARKER = "candidate-a-star-cycle-gate-001"
MANIFEST_MARKER = "<!-- candidate-a-star-cycle-gate-manifest -->"
CHECKLIST_MARKER = "<!-- candidate-a-star-cycle-gate-checklist -->"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def _check_append(path: Path, marker: str, content: str) -> bool:
    current = _read_text(path)
    count = current.count(marker)
    if count > 1:
        raise ValueError(f"duplicate ledger marker in {path}: {marker}")
    if count == 1:
        if content.rstrip() not in current:
            raise ValueError(f"ledger marker/content mismatch in {path}: {marker}")
        return False
    return True


def _append_once(path: Path, marker: str, content: str) -> None:
    if not _check_append(path, marker, content):
        return
    current = _read_text(path)
    separator = "" if not current or current.endswith("\n") else "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        current + separator + content.rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _decision(summary_path: Path) -> str:
    with summary_path.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1 or rows[0].get("decision") not in {ADMIT, REJECT}:
        raise ValueError("summary must contain one recognized decision")
    return rows[0]["decision"]


def _run_row(decision: str) -> dict[str, str]:
    return {
        "run_id": RUN_MARKER,
        "date": "2026-07-17",
        "commit_or_state": "candidate-a-mechanism-gate",
        "stage": "Candidate A mechanism gate",
        "backend": "finite-field-standard-library",
        "command": "python scripts/run_candidate_a_star_cycle_gate.py",
        "params": "r=2/4/6; mu=0/1; prime=257",
        "seed": "deterministic",
        "status": decision,
        "summary": (
            "Phase equations and standard PVW randomization decide "
            "Candidate A routing."
        ),
        "artifacts": "repro/candidate_a_star_cycle_gate/",
    }


def _run_log_plan(root: Path, decision: str) -> tuple[Path, list[str], bool]:
    path = root / "repro/run_log.csv"
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    required = set(_run_row(decision))
    if not fields or not required.issubset(fields):
        raise ValueError("run log is missing required columns")
    matches = [row for row in rows if row.get("run_id") == RUN_MARKER]
    if len(matches) > 1:
        raise ValueError(f"duplicate run-log marker: {RUN_MARKER}")
    if matches:
        expected = _run_row(decision)
        if any(matches[0].get(field) != value for field, value in expected.items()):
            raise ValueError(f"run-log marker/content mismatch: {RUN_MARKER}")
        return path, fields, False
    return path, fields, True


def _append_run(path: Path, fields: list[str], decision: str, needed: bool) -> None:
    if not needed:
        return
    row = _run_row(decision)
    with path.open("a", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writerow({field: row.get(field, "") for field in fields})


def _ledger_entries(decision: str) -> tuple[tuple[str, str, str], ...]:
    hypothesis = f"""H_candidate_a_star_cycle_mechanism:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/candidate_a_star_cycle_gate/summary.csv
    - repro/candidate_a_star_cycle_gate/phase_constraints.csv
    - repro/candidate_a_star_cycle_gate/randomization_dimension.csv
    - theory_checks/candidate_a_star_cycle_production_equations.md
  conclusion: >
    Candidate A is decided by the source-anchored phase and standard-PVW
    randomization gate. The finite-field checker makes no security, noise,
    production-readiness, or performance claim.
"""
    manifest = """<!-- candidate-a-star-cycle-gate-manifest -->
- candidate_a_star_cycle_gate:
  - `research/mat_sab/`
  - `theory_checks/candidate_a_star_cycle_production_equations.md`
  - `docs/candidate_a_star_cycle_mechanism_gate.md`
  - `scripts/run_candidate_a_star_cycle_gate.py`
  - `scripts/apply_mat_sab_candidate_gate.py`
  - `repro/candidate_a_star_cycle_gate/`
"""
    checklist = f"""<!-- candidate-a-star-cycle-gate-checklist -->
- [x] Candidate A records `{decision}` from source, phase, dense-control,
  negative-control, and standard-PVW randomization gates; production hot-path
  permission remains false. Reproduce with
  `python scripts/run_candidate_a_star_cycle_gate.py` followed by
  `python scripts/apply_mat_sab_candidate_gate.py`.
"""
    return (
        ("hypotheses/hypothesis_register.yaml", HYPOTHESIS_MARKER, hypothesis),
        ("repro/artifact_manifest.md", MANIFEST_MARKER, manifest),
        ("repro/reproduction_checklist.md", CHECKLIST_MARKER, checklist),
    )


def _validate_pre_state(state: dict[str, object]) -> None:
    candidates = state["candidates"]
    expected = (
        state["goal_status"] == "ACTIVE"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state["active_candidate"] == "A"
        and candidates["A"]["status"] == "EQUATIONS_DEFINED"
        and candidates["B"]["status"] == "QUEUED"
        and candidates["C"]["status"] == "QUEUED"
    )
    if not expected:
        raise ValueError("state is not at the Candidate A mechanism gate")


def _validate_applied_state(state: dict[str, object], decision: str) -> None:
    candidates = state["candidates"]
    common = (
        state["goal_status"] == "ACTIVE"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state.get("last_decision") == decision
        and candidates["C"]["status"] == "QUEUED"
    )
    if decision == ADMIT:
        branch = (
            state["active_candidate"] == "A"
            and candidates["A"]["status"] == "ADVERSARIAL_CHECKER_PASS"
            and candidates["B"]["status"] == "QUEUED"
        )
    else:
        branch = (
            state["active_candidate"] == "B"
            and candidates["A"]["status"] == "REJECTED"
            and candidates["B"]["status"] == "INTAKE"
        )
    if not common or not branch:
        raise ValueError(
            f"state/decision mismatch: {candidates['A']['status']} and {decision}"
        )
    validate_state(state)


def apply_gate(root: Path, state_path: Path, summary_path: Path) -> str:
    decision = _decision(summary_path)
    state = load_state(state_path)
    target = "ADVERSARIAL_CHECKER_PASS" if decision == ADMIT else "REJECTED"
    current = state["candidates"]["A"]["status"]

    entries = _ledger_entries(decision)
    for relative, marker, content in entries:
        _check_append(root / relative, marker, content)
    run_path, run_fields, append_run = _run_log_plan(root, decision)

    if current == "EQUATIONS_DEFINED":
        _validate_pre_state(state)
        state = transition_candidate(state, "A", target, decision)
        _validate_applied_state(state, decision)
        write_state(state_path, state)
    else:
        _validate_applied_state(state, decision)

    for relative, marker, content in entries:
        _append_once(root / relative, marker, content)
    _append_run(run_path, run_fields, decision, append_run)
    return decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    state = args.state or args.root / "research_state.yaml"
    summary = (
        args.summary
        or args.root / "repro/candidate_a_star_cycle_gate/summary.csv"
    )
    print(apply_gate(args.root, state, summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
