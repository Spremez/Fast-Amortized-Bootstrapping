#!/usr/bin/env python3
"""Apply the verified Candidate D Task 9 decision and bounded ledgers."""

from __future__ import annotations

import argparse
import csv
from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.mat_sab_research_state import (  # noqa: E402
    load_state,
    validate_state,
)
from scripts.run_candidate_d_admission import (  # noqa: E402
    ADMIT,
    BLOCK,
    CURRENT_INPUT_COMMIT,
    REJECT_BINDING_NOISE_SECURITY,
    REJECT_CLOSURE,
    REJECT_COMPLETE_COST,
    REJECT_PRIOR_ART,
    AdmissionEvidenceError,
    AdmissionResult,
    _safe_path,
    verify_candidate_d_artifacts,
)


RUN_MARKER = "candidate-d-admission-001"
HYPOTHESIS_START = "# candidate-d-admission-hypothesis-start"
HYPOTHESIS_END = "# candidate-d-admission-hypothesis-end"
MANIFEST_START = "<!-- candidate-d-admission-manifest-start -->"
MANIFEST_END = "<!-- candidate-d-admission-manifest-end -->"
CHECKLIST_START = "<!-- candidate-d-admission-checklist-start -->"
CHECKLIST_END = "<!-- candidate-d-admission-checklist-end -->"

RUN_FIELDS = (
    "run_id",
    "date",
    "commit_or_state",
    "stage",
    "backend",
    "command",
    "params",
    "seed",
    "status",
    "summary",
    "artifacts",
)
LEDGER_PATHS = (
    "hypotheses/hypothesis_register.yaml",
    "repro/artifact_manifest.md",
    "repro/reproduction_checklist.md",
)
STATE_PATH = "research_state.yaml"
RUN_LOG_PATH = "repro/run_log.csv"
TASK9_PLATFORM = (
    "Windows-NT-10.0.26200.0 CPython-3.12.4; "
    "WSL2-Linux-5.15.167.4-x86_64 cross-check; "
    "formal-performance=native-Linux-required"
)


def _is_resume_result(result: AdmissionResult) -> bool:
    return result.input_commit != CURRENT_INPUT_COMMIT


def _marker_for(result: AdmissionResult, marker: str) -> str:
    if not _is_resume_result(result):
        return marker
    if marker.startswith("<!--") and marker.endswith("-->"):
        return f"{marker[:-3]}-{result.input_commit[:12]} -->"
    return f"{marker}-{result.input_commit[:12]}"


def _run_marker_for(result: AdmissionResult) -> str:
    if not _is_resume_result(result):
        return RUN_MARKER
    return f"candidate-d-admission-{result.input_commit[:12]}"


def _resolved_destination(root: Path, relative: str) -> Path:
    try:
        path = _safe_path(
            root,
            relative,
            f"closeout destination {relative}",
            strict=True,
            require_file=True,
        )
    except AdmissionEvidenceError as error:
        raise ValueError(str(error)) from error
    return path


def _bounded_block(start: str, end: str, content: str) -> bytes:
    return f"{start}\n{content.rstrip()}\n{end}\n".encode("ascii")


def _plan_bounded_append(
    current: bytes,
    start: str,
    end: str,
    content: str,
    label: str,
) -> bytes:
    try:
        text = current.decode("ascii")
    except UnicodeError as error:
        raise ValueError(f"{label} is not ASCII") from error
    lines = text.splitlines()
    if any(
        marker in line and line != marker
        for marker in (start, end)
        for line in lines
    ):
        raise ValueError(f"ledger marker mismatch in {label}: {start}")
    starts = [index for index, line in enumerate(lines) if line == start]
    ends = [index for index, line in enumerate(lines) if line == end]
    expected = _bounded_block(start, end, content).decode("ascii").rstrip("\n")
    if not starts and not ends:
        separator = b"" if not current or current.endswith((b"\n", b"\r")) else b"\n"
        return current + separator + _bounded_block(start, end, content)
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise ValueError(f"ledger marker mismatch in {label}: {start}")
    actual = "\n".join(lines[starts[0] : ends[0] + 1])
    if actual != expected:
        raise ValueError(f"ledger content mismatch in {label}: {start}")
    return current


def _generator_command(result: AdmissionResult) -> str:
    return (
        "python scripts/run_candidate_d_admission.py --input-commit "
        + result.input_commit
    )


def _apply_command(result: AdmissionResult) -> str:
    return (
        "python scripts/apply_candidate_d_admission.py --input-commit "
        + result.input_commit
    )


def _route_conclusion(result: AdmissionResult) -> str:
    if result.decision == ADMIT:
        return (
            "All D0-D3 admission inputs pass. Candidate D advances to an "
            "isolated opt-in D4 experiment; scalar defaults remain unchanged."
        )
    if result.decision == REJECT_PRIOR_ART:
        return (
            "The D1 source review subsumes Candidate D. D is rejected and "
            "Candidate E enters security/novelty preflight."
        )
    if result.decision == REJECT_CLOSURE:
        return (
            "The D2 closure, gamma, or negative-control gate rejects Candidate "
            "D. Candidate E enters security/novelty preflight."
        )
    if result.decision == REJECT_BINDING_NOISE_SECURITY:
        return (
            "The D3 binding, standard-object, or absolute noise/decode gate "
            "rejects Candidate D. Candidate E enters security/novelty preflight."
        )
    if result.decision == REJECT_COMPLETE_COST:
        return (
            "The D3 pessimistic complete-cost or resource gate rejects Candidate "
            "D. Candidate E enters security/novelty preflight."
        )
    if result.d1_status == "BLOCK":
        return (
            "D0 passes and D1 awaits the latest second revision of IACR ePrint "
            "2026/068 and a hash-bound claim review. D remains at D0, E remains "
            "reserved, and production permission is false."
        )
    if result.d2_status == "BLOCK":
        return (
            "D0-D1 pass and D2 source evidence is incomplete. D remains at D1, "
            "E remains reserved, and production permission is false."
        )
    return (
        "D0-D2 pass and D3 source evidence is incomplete. D remains at D2, E "
        "remains reserved, and production permission is false."
    )


def _ledger_contents(
    result: AdmissionResult,
) -> tuple[tuple[str, str, str, str], ...]:
    resume = json.dumps(result.resume_condition, ensure_ascii=True)
    last_gate = _expected_last_reached(result)
    conclusion = _route_conclusion(result)
    hypothesis = f"""H_candidate_d_lut_late_binding_admission:
  status: {result.decision}
  primary_metric: complete_sab_T_bootstrap_div_rN_active
  last_valid_gate: {last_gate}
  evidence:
    - docs/candidate_d_admission_report.md
    - repro/candidate_d_admission/summary.csv
    - repro/candidate_d_admission/proof_gate.csv
    - repro/candidate_d_admission/decision_evidence.json
    - repro/candidate_d_admission/artifact_index.csv
  resume_condition: {resume}
  conclusion: >
    {conclusion}
"""
    manifest = """- candidate_d_admission:
  - `scripts/run_candidate_d_admission.py`
  - `scripts/apply_candidate_d_admission.py`
  - `scripts/mat_sab_research_state.py`
  - `tests/research/test_candidate_d_gate.py`
  - `tests/research/test_candidate_d_closeout.py`
  - `tests/research/test_research_state.py`
  - `docs/candidate_d_d0_baseline.md`
  - `docs/candidate_d_d1_novelty_audit.md`
  - `docs/candidate_d_admission_report.md`
  - `repro/candidate_d_admission/`
"""
    resume_item = ""
    if result.decision == BLOCK:
        resume_item = f"""- [ ] Resume condition: {result.resume_condition}
"""
    checklist = f"""- [x] Candidate D records `{result.decision}` from the complete
  source-derived D0-D3 priority chain. {conclusion} Reproduce with
  `{_generator_command(result)}` followed by `{_apply_command(result)}`.
{resume_item}"""
    return (
        (
            "hypotheses/hypothesis_register.yaml",
            _marker_for(result, HYPOTHESIS_START),
            _marker_for(result, HYPOTHESIS_END),
            hypothesis,
        ),
        (
            "repro/artifact_manifest.md",
            _marker_for(result, MANIFEST_START),
            _marker_for(result, MANIFEST_END),
            manifest,
        ),
        (
            "repro/reproduction_checklist.md",
            _marker_for(result, CHECKLIST_START),
            _marker_for(result, CHECKLIST_END),
            checklist,
        ),
    )


def _run_row(result: AdmissionResult) -> dict[str, str]:
    params = (
        f"D0={result.d0_status};D1={result.d1_status};D2={result.d2_status};"
        f"gamma={result.gamma_count if result.gamma_count is not None else 'none'};"
        f"negative_controls={result.negative_controls_status};"
        f"binding={result.binding_status};security={result.security_status};"
        f"noise={result.noise_status};cost={result.complete_cost_status};"
        f"resource={result.resource_status};"
        f"pessimistic_projection={result.pessimistic_projection or 'none'};"
        f"pre_permission={'yes' if result.pre_application_permission else 'no'};"
        f"execution_platform={TASK9_PLATFORM}"
    )
    return {
        "run_id": _run_marker_for(result),
        "date": "2026-07-21",
        "commit_or_state": result.input_commit,
        "stage": "Candidate D atomic D0-D3 admission closeout",
        "backend": "python-stdlib-evidence-controller",
        "command": _generator_command(result) + " && " + _apply_command(result),
        "params": params,
        "seed": "deterministic",
        "status": result.decision,
        "summary": _route_conclusion(result),
        "artifacts": (
            "docs/candidate_d_admission_report.md; "
            "repro/candidate_d_admission/summary.csv; "
            "repro/candidate_d_admission/proof_gate.csv; "
            "repro/candidate_d_admission/decision_evidence.json; "
            "repro/candidate_d_admission/artifact_index.csv"
        ),
    }


def _serialized_run_row(row: Mapping[str, str]) -> bytes:
    stream = StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=RUN_FIELDS,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writerow(row)
    return stream.getvalue().encode("ascii")


def _plan_run_log(current: bytes, result: AdmissionResult) -> bytes:
    try:
        text = current.decode("ascii")
        records = list(csv.reader(StringIO(text, newline=""), strict=True))
    except (UnicodeError, csv.Error) as error:
        raise ValueError("run log is malformed") from error
    if (
        not records
        or tuple(records[0]) != RUN_FIELDS
    ):
        raise ValueError("run log header changed")
    marker = _run_marker_for(result)
    for row in records[1:]:
        for index, value in enumerate(row):
            if marker in value and (
                value != marker or index != 0 or len(row) != len(RUN_FIELDS)
            ):
                raise ValueError(
                    f"run-log marker is outside its canonical row: {marker}"
                )
    matches = [
        row
        for row in records[1:]
        if len(row) == len(RUN_FIELDS) and row[0] == marker
    ]
    expected = _run_row(result)
    if len(matches) > 1:
        raise ValueError(f"duplicate run-log marker: {marker}")
    if matches:
        if dict(zip(RUN_FIELDS, matches[0])) != expected:
            raise ValueError(f"run-log marker/content mismatch: {marker}")
        return current
    separator = b"" if current.endswith((b"\n", b"\r")) else b"\n"
    return current + separator + _serialized_run_row(expected)


def _expected_last_reached(result: AdmissionResult) -> str:
    if result.d0_status != "PASS":
        return "PLAN_APPROVED"
    if result.d1_status != "PASS":
        return "D0_BASELINE_FROZEN"
    if result.d2_status != "PASS":
        return "D1_NOVELTY_AUDIT_PASS"
    return "D2_OPERATOR_CLOSURE_PASS"


def _validate_pre_state(state: dict[str, object], result: AdmissionResult) -> None:
    validate_state(state)
    candidates = state["candidates"]
    expected_last = _expected_last_reached(result)
    expected_decisions = {
        "PLAN_APPROVED": "CANDIDATE_D_WRITTEN_SPEC_AND_IMPLEMENTATION_PLAN_APPROVED",
        "D0_BASELINE_FROZEN": "PASS_D0_CANDIDATE_D_BASELINES_FROZEN",
        "D1_NOVELTY_AUDIT_PASS": (
            "PASS_D1_DISTINCT_SAB_OPERATOR_CLAIM_REMAINS_TESTABLE"
        ),
        "D2_OPERATOR_CLOSURE_PASS": "PASS_D2_OPERATOR_CLOSURE_G_LE_4",
    }
    expected_sources = {
        "PLAN_APPROVED": "DESIGN_APPROVED_PENDING_WRITTEN_SPEC_REVIEW",
        "D0_BASELINE_FROZEN": "PLAN_APPROVED",
        "D1_NOVELTY_AUDIT_PASS": "D0_BASELINE_FROZEN",
        "D2_OPERATOR_CLOSURE_PASS": "D1_NOVELTY_AUDIT_PASS",
    }
    if not (
        state["goal_status"] == "ACTIVE"
        and state["active_candidate"] == "D"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and candidates["D"]["status"] == expected_last
        and candidates["D"]["last_reached_status"] == expected_last
        and candidates["E"]["status"] == "RESERVED_FALLBACK_NOT_STARTED"
        and candidates["E"]["last_reached_status"]
        == "RESERVED_FALLBACK_NOT_STARTED"
        and state["last_decision"] == expected_decisions[expected_last]
        and state["last_decision_source_status"]
        == expected_sources[expected_last]
    ):
        raise ValueError("state is not at the last valid Candidate D gate")


def _transition_state(
    state: dict[str, object], result: AdmissionResult
) -> dict[str, object]:
    _validate_pre_state(state, result)
    changed = json.loads(json.dumps(state))
    candidates = changed["candidates"]
    source = _expected_last_reached(result)
    changed["paper_gate"] = "BLOCKED"
    changed["production_hot_path_permission"] = False
    changed["last_decision"] = result.decision
    changed["last_decision_source_status"] = source
    if result.decision == ADMIT:
        candidates["D"]["status"] = "D3_ADMISSION_PASS"
        candidates["D"]["last_reached_status"] = "D3_ADMISSION_PASS"
        changed["last_decision_source_status"] = "D2_OPERATOR_CLOSURE_PASS"
        changed["active_candidate"] = "D"
        changed["goal_status"] = "ACTIVE"
        changed["production_hot_path_permission"] = True
    elif result.decision in {
        REJECT_PRIOR_ART,
        REJECT_CLOSURE,
        REJECT_BINDING_NOISE_SECURITY,
        REJECT_COMPLETE_COST,
    }:
        candidates["D"]["status"] = "REJECTED"
        candidates["D"]["last_reached_status"] = source
        candidates["E"]["status"] = "SECURITY_NOVELTY_PREFLIGHT"
        candidates["E"]["last_reached_status"] = "SECURITY_NOVELTY_PREFLIGHT"
        changed["active_candidate"] = "E"
        changed["goal_status"] = "ACTIVE"
    elif result.decision == BLOCK:
        changed["active_candidate"] = "D"
        changed["goal_status"] = "EXTERNAL_BLOCKED"
    else:
        raise ValueError("unknown Candidate D decision")
    validate_state(changed)
    return changed


def _validate_resume_base_state(state: dict[str, object]) -> None:
    validate_state(state)
    candidates = state["candidates"]
    if not (
        state["goal_status"] == "EXTERNAL_BLOCKED"
        and state["active_candidate"] == "D"
        and state["paper_gate"] == "BLOCKED"
        and state["production_hot_path_permission"] is False
        and state["last_decision"] == BLOCK
        and candidates["D"]["status"]
        in {
            "PLAN_APPROVED",
            "D0_BASELINE_FROZEN",
            "D1_NOVELTY_AUDIT_PASS",
            "D2_OPERATOR_CLOSURE_PASS",
        }
        and candidates["D"]["last_reached_status"]
        == candidates["D"]["status"]
        and state["last_decision_source_status"]
        == candidates["D"]["status"]
        and candidates["E"]["status"] == "RESERVED_FALLBACK_NOT_STARTED"
        and candidates["E"]["last_reached_status"]
        == "RESERVED_FALLBACK_NOT_STARTED"
    ):
        raise ValueError("state is not an exact Candidate D external BLOCK")


def _validate_historical_block_ledgers(current: dict[str, bytes]) -> None:
    marker_specs = (
        ("hypotheses/hypothesis_register.yaml", HYPOTHESIS_START, HYPOTHESIS_END),
        ("repro/artifact_manifest.md", MANIFEST_START, MANIFEST_END),
        ("repro/reproduction_checklist.md", CHECKLIST_START, CHECKLIST_END),
    )
    for relative, start, end in marker_specs:
        try:
            lines = current[relative].decode("ascii").splitlines()
        except UnicodeError as error:
            raise ValueError("historical Candidate D ledger is not ASCII") from error
        starts = [index for index, line in enumerate(lines) if line == start]
        ends = [index for index, line in enumerate(lines) if line == end]
        if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
            raise ValueError("historical Candidate D BLOCK marker is missing")
        body = "\n".join(lines[starts[0] + 1 : ends[0]])
        if relative.endswith("hypothesis_register.yaml") and (
            BLOCK not in body or "production permission is false" not in body
        ):
            raise ValueError("historical Candidate D BLOCK hypothesis changed")
        if relative.endswith("reproduction_checklist.md") and (
            BLOCK not in body or CURRENT_INPUT_COMMIT not in body
        ):
            raise ValueError("historical Candidate D BLOCK checklist changed")
        if relative.endswith("artifact_manifest.md") and (
            "scripts/run_candidate_d_admission.py" not in body
            or "repro/candidate_d_admission/" not in body
        ):
            raise ValueError("historical Candidate D BLOCK manifest changed")

    try:
        rows = list(
            csv.DictReader(
                StringIO(current[RUN_LOG_PATH].decode("ascii"), newline=""),
                strict=True,
            )
        )
    except (UnicodeError, csv.Error) as error:
        raise ValueError("historical Candidate D run log is malformed") from error
    matches = [row for row in rows if row.get("run_id") == RUN_MARKER]
    if len(matches) != 1 or not (
        matches[0].get("commit_or_state") == CURRENT_INPUT_COMMIT
        and matches[0].get("status") == BLOCK
        and CURRENT_INPUT_COMMIT in matches[0].get("command", "")
    ):
        raise ValueError("historical Candidate D BLOCK run record changed")


def _transition_resumed_state(
    state: dict[str, object], result: AdmissionResult
) -> dict[str, object]:
    _validate_resume_base_state(state)
    changed = json.loads(json.dumps(state))
    candidates = changed["candidates"]
    source = _expected_last_reached(result)
    changed["paper_gate"] = "BLOCKED"
    changed["production_hot_path_permission"] = False
    changed["last_decision"] = result.decision
    changed["last_decision_source_status"] = source
    if result.decision == ADMIT:
        candidates["D"]["status"] = "D3_ADMISSION_PASS"
        candidates["D"]["last_reached_status"] = "D3_ADMISSION_PASS"
        changed["active_candidate"] = "D"
        changed["goal_status"] = "ACTIVE"
        changed["production_hot_path_permission"] = True
    elif result.decision in {
        REJECT_PRIOR_ART,
        REJECT_CLOSURE,
        REJECT_BINDING_NOISE_SECURITY,
        REJECT_COMPLETE_COST,
    }:
        candidates["D"]["status"] = "REJECTED"
        candidates["D"]["last_reached_status"] = source
        candidates["E"]["status"] = "SECURITY_NOVELTY_PREFLIGHT"
        candidates["E"]["last_reached_status"] = "SECURITY_NOVELTY_PREFLIGHT"
        changed["active_candidate"] = "E"
        changed["goal_status"] = "ACTIVE"
    elif result.decision == BLOCK:
        candidates["D"]["status"] = source
        candidates["D"]["last_reached_status"] = source
        changed["active_candidate"] = "D"
        changed["goal_status"] = "EXTERNAL_BLOCKED"
    else:
        raise ValueError("unknown Candidate D resume decision")
    validate_state(changed)
    return changed


def _validate_applied_state(
    state: dict[str, object], result: AdmissionResult
) -> None:
    validate_state(state)
    candidates = state["candidates"]
    source = _expected_last_reached(result)
    common = (
        state["last_decision"] == result.decision
        and state["paper_gate"] == "BLOCKED"
        and state["last_decision_source_status"] == source
    )
    if result.decision == BLOCK:
        branch = (
            state["goal_status"] == "EXTERNAL_BLOCKED"
            and state["active_candidate"] == "D"
            and state["production_hot_path_permission"] is False
            and candidates["D"]["status"] == source
            and candidates["D"]["last_reached_status"] == source
            and candidates["E"]["status"] == "RESERVED_FALLBACK_NOT_STARTED"
        )
    elif result.decision == ADMIT:
        branch = (
            state["goal_status"] == "ACTIVE"
            and state["active_candidate"] == "D"
            and state["production_hot_path_permission"] is True
            and candidates["D"]["status"] == "D3_ADMISSION_PASS"
        )
    else:
        branch = (
            state["goal_status"] == "ACTIVE"
            and state["active_candidate"] == "E"
            and state["production_hot_path_permission"] is False
            and candidates["D"]["status"] == "REJECTED"
            and candidates["D"]["last_reached_status"] == source
            and candidates["E"]["status"] == "SECURITY_NOVELTY_PREFLIGHT"
        )
    if not common or not branch:
        raise ValueError("state contains a different Candidate D closeout")


def _state_bytes(state: dict[str, object]) -> bytes:
    return (json.dumps(state, indent=2) + "\n").encode("ascii")


def _plan_closeout(
    root: Path, result: AdmissionResult
) -> dict[Path, bytes]:
    paths = {
        relative: _resolved_destination(root, relative)
        for relative in (*LEDGER_PATHS, STATE_PATH, RUN_LOG_PATH)
    }
    current = {relative: path.read_bytes() for relative, path in paths.items()}
    try:
        state = json.loads(current[STATE_PATH].decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("research state is malformed") from error
    planned: dict[Path, bytes] = {}
    for relative, start, end, content in _ledger_contents(result):
        planned[paths[relative]] = _plan_bounded_append(
            current[relative], start, end, content, relative
        )
    planned[paths[RUN_LOG_PATH]] = _plan_run_log(
        current[RUN_LOG_PATH], result
    )
    candidates = state.get("candidates")
    current_decision = state.get("last_decision")
    applied = False
    try:
        _validate_applied_state(state, result)
        planned[paths[STATE_PATH]] = current[STATE_PATH]
        applied = True
    except ValueError:
        pass
    if applied:
        return planned
    if (
        isinstance(candidates, dict)
        and candidates.get("D", {}).get("status")
        in {
            "PLAN_APPROVED",
            "D0_BASELINE_FROZEN",
            "D1_NOVELTY_AUDIT_PASS",
            "D2_OPERATOR_CLOSURE_PASS",
        }
        and state.get("goal_status") == "ACTIVE"
        and current_decision != result.decision
    ):
        changed = _transition_state(state, result)
        planned[paths[STATE_PATH]] = _state_bytes(changed)
    elif _is_resume_result(result) and state.get("goal_status") == "EXTERNAL_BLOCKED":
        _validate_historical_block_ledgers(current)
        changed = _transition_resumed_state(state, result)
        planned[paths[STATE_PATH]] = _state_bytes(changed)
    else:
        raise ValueError("state cannot apply or replay this Candidate D decision")
    return planned


def _replace_bytes_atomic(path: Path, content: bytes) -> None:
    descriptor, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    _replace_bytes_atomic(path, content)


def _restore_snapshot(snapshot: dict[Path, bytes]) -> None:
    for path, content in snapshot.items():
        _replace_bytes_atomic(path, content)


def check_candidate_d_decision(root: Path, result: AdmissionResult) -> str:
    verified = verify_candidate_d_artifacts(
        root, input_commit=result.input_commit
    )
    if verified != result:
        raise ValueError("requested result differs from verified artifacts")
    _plan_closeout(Path(root).resolve(), result)
    return result.decision


def apply_candidate_d_decision(root: Path, result: AdmissionResult) -> str:
    verified = verify_candidate_d_artifacts(
        root, input_commit=result.input_commit
    )
    if verified != result:
        raise ValueError("requested result differs from verified artifacts")
    resolved_root = Path(root).resolve(strict=True)
    planned = _plan_closeout(resolved_root, result)
    snapshot = {path: path.read_bytes() for path in planned}
    if all(snapshot[path] == content for path, content in planned.items()):
        return result.decision
    try:
        for path, content in planned.items():
            if snapshot[path] != content:
                _write_bytes_atomic(path, content)
    except Exception:
        _restore_snapshot(snapshot)
        raise
    return result.decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input-commit", required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate artifacts and the pending/applied closeout without writing",
    )
    args = parser.parse_args(argv)
    result = verify_candidate_d_artifacts(
        args.root, input_commit=args.input_commit
    )
    if args.check:
        decision = check_candidate_d_decision(args.root, result)
    else:
        decision = apply_candidate_d_decision(args.root, result)
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
