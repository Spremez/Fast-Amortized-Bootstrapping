#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mat_sab_research_state import (
    load_state,
    transition_candidate,
    validate_state,
    write_state,
)
from scripts.run_candidate_c_rank_bounded_gate import (
    ADMIT,
    INCONCLUSIVE,
    REJECT,
    SUMMARY_FIELDS,
    canonical_summary_record,
    evaluate_candidate_c,
)

RUN_MARKER = "candidate-c-rank-bounded-gate-001"
HYPOTHESIS_START = "# candidate-c-rank-bounded-gate-hypothesis-start"
HYPOTHESIS_END = "# candidate-c-rank-bounded-gate-hypothesis-end"
MANIFEST_START = "<!-- candidate-c-rank-bounded-gate-manifest-start -->"
MANIFEST_END = "<!-- candidate-c-rank-bounded-gate-manifest-end -->"
CHECKLIST_START = "<!-- candidate-c-rank-bounded-gate-checklist-start -->"
CHECKLIST_END = "<!-- candidate-c-rank-bounded-gate-checklist-end -->"
PREDECESSOR_DECISION = (
    "REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C"
)
TECHGRAPH_DECISION = "CANDIDATE_C_TECHGRAPH_ANCHORED"
EQUATIONS_DECISION = "CANDIDATE_C_EQUATIONS_DEFINED"
DECISIONS = {ADMIT, REJECT, INCONCLUSIVE}


def _resolved_root(root: Path) -> Path:
    resolved = Path(root).resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"root is not a directory: {resolved}")
    return resolved


def _resolved_under_root(
    root: Path,
    path: Path,
    label: str,
    *,
    strict: bool,
) -> Path:
    resolved = Path(path).resolve(strict=strict)
    if not resolved.is_relative_to(root):
        raise ValueError(f"{label} escapes root: {resolved}")
    return resolved


def _read_text(path: Path) -> str:
    return path.read_text(encoding="ascii") if path.exists() else ""


def _bounded_block(start: str, end: str, content: str) -> str:
    return f"{start}\n{content.rstrip()}\n{end}"


def _check_append(path: Path, start: str, end: str, content: str) -> bool:
    current = _read_text(path)
    lines = current.splitlines()
    if any(
        marker in line and line != marker
        for marker in (start, end)
        for line in lines
    ):
        raise ValueError(f"ledger block marker mismatch in {path}: {start}")
    starts = [index for index, line in enumerate(lines) if line == start]
    ends = [index for index, line in enumerate(lines) if line == end]
    if not starts and not ends:
        return True
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise ValueError(f"ledger block marker mismatch in {path}: {start}")
    actual = "\n".join(lines[starts[0] : ends[0] + 1])
    if actual != _bounded_block(start, end, content):
        raise ValueError(f"ledger block/content mismatch in {path}: {start}")
    return False


def _append_once(path: Path, start: str, end: str, content: str) -> None:
    if not _check_append(path, start, end, content):
        return
    current = _read_text(path)
    separator = "" if not current or current.endswith("\n") else "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        current + separator + _bounded_block(start, end, content) + "\n",
        encoding="ascii",
        newline="\n",
    )


def _summary_record(path: Path) -> dict[str, str]:
    try:
        with path.open(newline="", encoding="ascii") as handle:
            records = list(csv.reader(handle, strict=True))
    except (csv.Error, UnicodeError) as error:
        raise ValueError(
            "summary must contain one canonical decision"
        ) from error
    if len(records) != 2:
        raise ValueError("summary must contain one canonical decision")
    fields, row = records
    if (
        tuple(fields) != SUMMARY_FIELDS
        or len(fields) != len(set(fields))
        or len(row) != len(fields)
    ):
        raise ValueError("summary must contain one canonical decision")
    record = dict(zip(fields, row))
    if record["decision"] not in DECISIONS:
        raise ValueError("summary must contain one canonical decision")
    optional_numeric = {"complete_cost", "amdahl_projection"}
    if any(
        value == "" and field not in optional_numeric
        for field, value in record.items()
    ):
        raise ValueError("summary must contain one canonical decision")
    if record["complete_cost"] == "" and (
        record["complete_cost_status"] != "SKIPPED_NO_REGISTERED_OPERATOR"
    ):
        raise ValueError("blank complete cost requires skipped Task 4")
    if record["amdahl_projection"] == "" and (
        record["amdahl_status"] != "SKIPPED_NO_REGISTERED_OPERATOR"
    ):
        raise ValueError("blank Amdahl projection requires skipped Task 4")
    return record


def _run_row(decision: str) -> dict[str, str]:
    return {
        "run_id": RUN_MARKER,
        "date": "2026-07-17",
        "commit_or_state": "candidate-c-rank-bounded-mechanism-gate",
        "stage": "Candidate C mechanism gate",
        "backend": "exact-finite-ring-symbolic",
        "command": "python scripts/run_candidate_c_rank_bounded_gate.py",
        "params": "C1/C2;r=2/4/6;rho<=2;Task4=registered-only",
        "seed": "deterministic",
        "status": decision,
        "summary": (
            "Hash-bound source, equation, symbolic, phase, schedule, rank, "
            "compression, complete-cost, and Amdahl gates close Candidate C."
        ),
        "artifacts": "repro/candidate_c_rank_bounded_gate/",
    }


def _run_log_plan(
    root: Path,
    decision: str,
) -> tuple[Path, list[str], bool]:
    path = _resolved_under_root(
        root,
        root / "repro/run_log.csv",
        "run-log destination",
        strict=True,
    )
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            records = list(csv.reader(handle, strict=True))
    except (csv.Error, UnicodeError) as error:
        raise ValueError("run log header must match canonical schema") from error
    fields = records[0] if records else []
    expected = list(_run_row(decision))
    if fields != expected or len(fields) != len(set(fields)):
        raise ValueError("run log header must match canonical schema")
    rows = []
    for physical in records[1:]:
        marker_positions = [
            index for index, value in enumerate(physical)
            if value == RUN_MARKER
        ]
        if len(physical) == len(fields):
            if any(index != 0 for index in marker_positions):
                raise ValueError("run log rows must match canonical schema")
            rows.append(dict(zip(fields, physical)))
        elif marker_positions:
            raise ValueError("run log rows must match canonical schema")
    matches = [row for row in rows if row["run_id"] == RUN_MARKER]
    if len(matches) > 1:
        raise ValueError(f"duplicate run-log marker: {RUN_MARKER}")
    if matches:
        expected_row = _run_row(decision)
        if matches[0] != expected_row:
            raise ValueError(f"run-log marker/content mismatch: {RUN_MARKER}")
        return path, fields, False
    return path, fields, True


def _append_run(
    path: Path,
    fields: list[str],
    decision: str,
    needed: bool,
) -> None:
    if not needed:
        return
    if path.stat().st_size:
        with path.open("rb") as handle:
            handle.seek(-1, 2)
            terminated = handle.read(1) in {b"\r", b"\n"}
        if not terminated:
            with path.open("ab") as handle:
                handle.write(b"\n")
    with path.open("a", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writerow(_run_row(decision))


def _ledger_entries(
    decision: str,
) -> tuple[tuple[str, str, str, str], ...]:
    hypothesis = f"""H_candidate_c_rank_bounded_mechanism:
  status: {decision}
  primary_metric: complete_sab_T_bootstrap_over_r
  evidence:
    - repro/candidate_c_rank_bounded_gate/summary.csv
    - repro/candidate_c_rank_bounded_gate/terminal_record.csv
    - repro/candidate_c_rank_bounded_gate/rank_growth.csv
    - repro/candidate_c_rank_bounded_gate/compression_gate.csv
    - repro/candidate_c_rank_bounded_gate/complete_cost.csv
    - repro/candidate_c_rank_bounded_gate/amdahl_projection.csv
  conclusion: >
    Candidate C closes the finite C1/C2 rank-bounded-state campaign. Task 4
    remains SKIPPED_NO_REGISTERED_OPERATOR on the actual route, with no
    fabricated complete-cost or Amdahl values. Production permission is false.
"""
    manifest = """- candidate_c_rank_bounded_gate:
  - `research/mat_sab/candidate_c_operator_tensor.py`
  - `research/mat_sab/candidate_c_registered_replay.py`
  - `scripts/run_candidate_c_rank_bounded_gate.py`
  - `scripts/apply_candidate_c_rank_bounded_gate.py`
  - `docs/candidate_c_rank_bounded_mechanism_gate.md`
  - `algorithm_variants/candidate_c_rank_bounded_state.md`
  - `experiments/candidate_c_rank_bounded_gate_plan.md`
  - `repro/candidate_c_rank_bounded_gate/`
"""
    checklist = f"""- [x] Candidate C records `{decision}` from hash-bound source,
  equation, symbolic-independence, phase, schedule, rank, compression,
  complete-cost, and Amdahl fields. Reproduce with
  `python scripts/run_candidate_c_rank_bounded_gate.py` followed by
  `python scripts/apply_candidate_c_rank_bounded_gate.py`; production hot-path
  permission remains false.
"""
    return (
        (
            "hypotheses/hypothesis_register.yaml",
            HYPOTHESIS_START,
            HYPOTHESIS_END,
            hypothesis,
        ),
        (
            "repro/artifact_manifest.md",
            MANIFEST_START,
            MANIFEST_END,
            manifest,
        ),
        (
            "repro/reproduction_checklist.md",
            CHECKLIST_START,
            CHECKLIST_END,
            checklist,
        ),
    )


def _validate_pre_state(state: dict[str, object]) -> None:
    candidates = state["candidates"]
    if not (
        state["goal_status"] == "ACTIVE"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state["active_candidate"] == "C"
        and state.get("last_decision") == PREDECESSOR_DECISION
        and candidates["A"]["status"] == "REJECTED"
        and candidates["B"]["status"] == "REJECTED"
        and candidates["C"]["status"] == "INTAKE"
    ):
        raise ValueError("state is not at the Candidate C mechanism gate")


def _validate_applied_state(
    state: dict[str, object],
    decision: str,
) -> None:
    candidates = state["candidates"]
    common = (
        state["active_candidate"] == "C"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state.get("last_decision") == decision
        and candidates["A"]["status"] == "REJECTED"
        and candidates["B"]["status"] == "REJECTED"
    )
    if decision == ADMIT:
        branch = (
            candidates["C"]["status"] == "ADVERSARIAL_CHECKER_PASS"
            and state["goal_status"] == "ACTIVE"
        )
    elif decision == REJECT:
        branch = (
            candidates["C"]["status"] == "REJECTED"
            and state["goal_status"] == "RESEARCH_CAMPAIGN_EXHAUSTED"
        )
    elif decision == INCONCLUSIVE:
        branch = (
            candidates["C"]["status"] == "INCONCLUSIVE"
            and state["goal_status"] == "RESEARCH_CAMPAIGN_INCONCLUSIVE"
        )
    else:
        branch = False
    if not common or not branch:
        raise ValueError(
            f"state/decision mismatch: {candidates['C']['status']} and "
            f"{decision}"
        )
    validate_state(state)


def _transition_initial_state(
    state: dict[str, object],
    decision: str,
) -> dict[str, object]:
    _validate_pre_state(state)
    changed = transition_candidate(
        state,
        "C",
        "TECHGRAPH_ANCHORED",
        TECHGRAPH_DECISION,
    )
    changed = transition_candidate(
        changed,
        "C",
        "EQUATIONS_DEFINED",
        EQUATIONS_DECISION,
    )
    targets = {
        ADMIT: "ADVERSARIAL_CHECKER_PASS",
        REJECT: "REJECTED",
        INCONCLUSIVE: "INCONCLUSIVE",
    }
    changed = transition_candidate(
        changed,
        "C",
        targets[decision],
        decision,
    )
    _validate_applied_state(changed, decision)
    return changed


def _snapshot_outputs(
    paths: tuple[Path, ...],
) -> dict[Path, bytes | None]:
    return {
        path: path.read_bytes() if path.exists() else None
        for path in paths
    }


def _restore_outputs(snapshot: dict[Path, bytes | None]) -> None:
    for path, content in snapshot.items():
        if content is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


def apply_gate(
    root: Path,
    state_path: Path,
    summary_path: Path,
    *,
    input_commit: str,
) -> str:
    resolved_root = _resolved_root(root)
    state = _resolved_under_root(
        resolved_root,
        state_path,
        "state path",
        strict=True,
    )
    summary = _resolved_under_root(
        resolved_root,
        summary_path,
        "summary path",
        strict=True,
    )
    summary_record = _summary_record(summary)
    recomputed_result = evaluate_candidate_c(
        resolved_root,
        input_commit=input_commit,
    )
    recomputed = canonical_summary_record(
        recomputed_result,
        root=resolved_root,
        input_commit=input_commit,
    )
    if summary_record != recomputed:
        raise ValueError("summary does not match recomputed gate evidence")
    decision = summary_record["decision"]
    current_state = load_state(state)

    entries = tuple(
        (
            _resolved_under_root(
                resolved_root,
                resolved_root / relative,
                f"ledger destination {relative}",
                strict=False,
            ),
            start,
            end,
            content,
        )
        for relative, start, end, content in _ledger_entries(decision)
    )
    for path, start, end, content in entries:
        _check_append(path, start, end, content)
    run_path, run_fields, append_run = _run_log_plan(
        resolved_root,
        decision,
    )

    current = current_state["candidates"]["C"]["status"]
    if current == "INTAKE":
        changed = _transition_initial_state(current_state, decision)
    elif current in {
        "ADVERSARIAL_CHECKER_PASS",
        "REJECTED",
        "INCONCLUSIVE",
    }:
        _validate_applied_state(current_state, decision)
        changed = None
    else:
        raise ValueError("state is not at the Candidate C mechanism gate")

    outputs = (
        state,
        *(path for path, _start, _end, _content in entries),
        run_path,
    )
    snapshot = _snapshot_outputs(outputs)
    try:
        if changed is not None:
            write_state(state, changed)
        for path, start, end, content in entries:
            _append_once(path, start, end, content)
        _append_run(run_path, run_fields, decision, append_run)
    except Exception:
        _restore_outputs(snapshot)
        raise
    return decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--input-commit", required=True)
    args = parser.parse_args()
    state = args.state or args.root / "research_state.yaml"
    summary = (
        args.summary
        or args.root / "repro/candidate_c_rank_bounded_gate/summary.csv"
    )
    print(
        apply_gate(
            args.root,
            state,
            summary,
            input_commit=args.input_commit,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
