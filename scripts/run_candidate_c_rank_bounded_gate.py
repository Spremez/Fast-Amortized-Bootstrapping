#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import os
import platform
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.mat_sab.candidate_c_operator_tensor import (
    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
)
from research.mat_sab.candidate_c_registered_replay import (
    NO_VERIFIED_TASK3B_RESULT,
    SKIPPED_NO_REGISTERED_OPERATOR,
    CandidateCTerminalRecord,
    terminal_record_for_task5,
)

OUT = Path("repro/candidate_c_rank_bounded_gate")
ADMIT = "ADMIT_CANDIDATE_C_KEY_SECURITY_NOISE_PREFLIGHT"
REJECT = "REJECT_CANDIDATE_C_RANK_BOUNDED_STATE_CAMPAIGN_EXHAUSTED"
INCONCLUSIVE = "INCONCLUSIVE_CANDIDATE_C_EVIDENCE_EXHAUSTED"
SKIPPED = SKIPPED_NO_REGISTERED_OPERATOR
APPROVED_TASK3C_HASH = (
    "8ad876708aa4a736c0f0f9adae33bab766272f411e90fbc23a5ac23e10a73cb6"
)
SUMMARY_FIELDS = (
    "decision",
    "source_status",
    "equation_status",
    "symbolic_independence_status",
    "phase_status",
    "schedule_status",
    "rank_status",
    "compression_status",
    "complete_cost_status",
    "complete_cost",
    "amdahl_status",
    "amdahl_projection",
    "task4_status",
    "mechanism_id",
    "max_rho",
    "compression_interval",
    "b_min",
    "closed_next_state_consumption",
    "terminal_classification",
    "terminal_decision",
    "terminal_record_hash",
    "production_hot_path_permission",
)
REQUIRED_PACK_FILES = (
    "summary.csv",
    "source_mapping.csv",
    "schedule_trace.csv",
    "operator_tensor.csv",
    "evaluator_sample_relations.csv",
    "conversion_material.csv",
    "registered_object_hash.csv",
    "terminal_record.csv",
    "rank_growth.csv",
    "compression_gate.csv",
    "complete_cost.csv",
    "amdahl_projection.csv",
    "mechanism_matrix.csv",
    "proof_gate.csv",
    "input_manifest.csv",
    "environment.csv",
    "artifact_index.csv",
    "reproduction_commands.md",
)
COMPUTATIONAL_INPUTS = (
    "main.c",
    "paper_techgraphs/candidate_c_rank_bounded_state.yaml",
    "repro/stage203_production_selector_equation_probe/equation_map.csv",
    "repro/stage222_isolated_compact_ep_integration/proof_gate.csv",
    "repro/stage345_binary_matrix_synthesis/proof_gate.csv",
    "research/mat_sab/candidate_c_operator_tensor.py",
    "research/mat_sab/candidate_c_registered_replay.py",
    "research/mat_sab/candidate_c_schedule.py",
    "research/mat_sab/finite_linear.py",
    "research/mat_sab/rank_bounded_state_model.py",
    "research/mat_sab/star_cycle_model.py",
    "scripts/run_candidate_c_rank_bounded_gate.py",
    "src/mosfhet/Makefile.def",
    "src/mosfhet/src/mattrgsw.c",
    "src/sab_pvw.c",
    "src/sparse_amortized_bootstrap.c",
    "theory_checks/candidate_c_rank_bounded_state_model.md",
)
GENERATED_DOCUMENTS = (
    "docs/candidate_c_rank_bounded_mechanism_gate.md",
    "algorithm_variants/candidate_c_rank_bounded_state.md",
    "experiments/candidate_c_rank_bounded_gate_plan.md",
)


class GateEvidenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class MechanismEvaluation:
    mechanism_id: str
    registered: bool
    source_status: str
    equation_status: str
    symbolic_independence_status: str
    phase_status: str
    schedule_status: str
    rank_status: str
    max_rho: int
    compression_status: str
    compression_interval: int
    b_min: int
    closed_next_state_consumption: bool
    structural_cost_status: str
    complete_cost_status: str
    complete_cost: float | None
    amdahl_status: str
    amdahl_projection: float | None
    fully_evaluated: bool
    failure_reason: str
    object_hashes: tuple[str, ...]


@dataclass(frozen=True)
class GateResult:
    terminal_record: CandidateCTerminalRecord
    decision: str
    terminal_classification: str
    terminal_decision: str
    terminal_record_hash: str
    task4_status: str
    complete_cost_status: str
    complete_cost: float | None
    amdahl_status: str
    amdahl_projection: float | None
    production_hot_path_permission: bool
    mechanisms: tuple[MechanismEvaluation, ...]
    source_rows: tuple[dict[str, object], ...]
    schedule_rows: tuple[dict[str, object], ...]
    operator_rows: tuple[dict[str, object], ...]
    relation_rows: tuple[dict[str, object], ...]
    conversion_rows: tuple[dict[str, object], ...]
    hash_rows: tuple[dict[str, object], ...]
    terminal_rows: tuple[dict[str, object], ...]
    rank_rows: tuple[dict[str, object], ...]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _status(value: bool) -> str:
    return "PASS" if value else "FAIL"


def _source_rows(
    terminal: CandidateCTerminalRecord,
) -> tuple[dict[str, object], ...]:
    by_key = {}
    for result in terminal.operator_results:
        for binding in result.source_bindings:
            key = (binding.name, binding.path, binding.sha256)
            by_key[key] = {
                "source_id": binding.name,
                "path": binding.path,
                "sha256": binding.sha256,
                "classification": binding.classification,
                "required_tokens": ";".join(binding.required_tokens),
                "status": "PASS",
            }
    return tuple(by_key[key] for key in sorted(by_key))


def _schedule_rows(
    terminal: CandidateCTerminalRecord,
) -> tuple[dict[str, object], ...]:
    return (
        {
            "schedule_hash": terminal.schedule_hash,
            "schedule_event_digest": terminal.schedule_event_digest,
            "state_edge_digest": terminal.state_edge_digest,
            "h": terminal.h,
            "monomial_calls": terminal.monomial_calls,
            "r_prec": terminal.r_prec,
            "in_N": terminal.in_N,
            "selector_events": terminal.selector_events,
            "ncmux_events": terminal.ncmux_events,
            "cmux_events": terminal.cmux_events,
            "butterfly_boundaries": terminal.butterfly_boundaries,
            "monomial_boundaries": terminal.monomial_boundaries,
            "sub_a_boundaries": terminal.sub_a_boundaries,
            "status": "PASS",
        },
    )


def _operator_rows(
    terminal: CandidateCTerminalRecord,
) -> tuple[dict[str, object], ...]:
    rows = []
    for result in terminal.operator_results:
        rows.append(
            {
                "mechanism_id": "C1",
                "r": result.r,
                "rho": result.rho,
                "modulus": result.modulus,
                "ring_degree": result.n,
                "gadget": ";".join(str(value) for value in result.gadget),
                "phase_identity_status": _status(result.phase_identity_passed),
                "joint_rank_status": _status(result.joint_rank_passed),
                "structural_cost_status": (
                    "PASS" if result.structural_improvement
                    else REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
                ),
                "decision": result.decision,
                "seed_hash": result.seed_hash,
                "result_hash": result.result_hash,
            }
        )
    return tuple(rows)


def _relation_rows(
    terminal: CandidateCTerminalRecord,
) -> tuple[dict[str, object], ...]:
    rows = []
    for result in terminal.operator_results:
        for mu, audit in enumerate(result.relation_audits):
            rows.append(
                {
                    "mechanism_id": "C1",
                    "r": result.r,
                    "mu": mu,
                    "status": audit.status,
                    "security_decision": (
                        "yes" if audit.security_decision else "no"
                    ),
                    "registered_sigma": (
                        "" if audit.registered_sigma is None
                        else audit.registered_sigma
                    ),
                    "registered_error_bound": (
                        "" if audit.registered_error_bound is None
                        else audit.registered_error_bound
                    ),
                    "decision_inequality": audit.decision_inequality or "",
                    "diagnostic_hash": audit.diagnostic_hash,
                }
            )
    return tuple(rows)


def _rank_rows(
    terminal: CandidateCTerminalRecord,
) -> tuple[dict[str, object], ...]:
    rows = []
    for result in terminal.operator_results:
        for mu, observed in enumerate(result.joint_ranks):
            rows.append(
                {
                    "mechanism_id": "C1",
                    "r": result.r,
                    "mu": mu,
                    "rho": result.rho,
                    "rank_bound": result.rho * result.n,
                    "observed_joint_rank": observed,
                    "status": _status(observed <= result.rho * result.n),
                }
            )
    return tuple(rows)


def _actual_mechanisms(
    terminal: CandidateCTerminalRecord,
) -> tuple[MechanismEvaluation, ...]:
    results = terminal.operator_results
    if not results:
        raise GateEvidenceError("Task 3C terminal record has no Task 3A results")
    structural_failure = all(
        not result.structural_improvement
        and result.decision
        == REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
        for result in results
    )
    if (
        not structural_failure
        or terminal.decision
        != REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
    ):
        raise GateEvidenceError(
            "Task 3C terminal record is not the scoped C1 structural-cost "
            "failure"
        )
    source_passed = all(result.source_bindings for result in results)
    schedule_passed = all(
        result.schedule_hash == terminal.schedule_hash for result in results
    )
    replay_skipped = terminal.replay_status == SKIPPED
    task4_skipped = terminal.task4_status == SKIPPED
    if not replay_skipped or not task4_skipped:
        raise GateEvidenceError(
            "Task 3C terminal record does not preserve the skipped replay/"
            "Task 4 route"
        )
    c1 = MechanismEvaluation(
        mechanism_id="C1",
        registered=True,
        source_status=_status(source_passed),
        equation_status=_status(bool(results)),
        symbolic_independence_status="PASS_SCOPED_NO_SECURITY_CLAIM",
        phase_status=_status(all(result.phase_identity_passed for result in results)),
        schedule_status=_status(schedule_passed),
        rank_status=_status(all(result.joint_rank_passed for result in results)),
        max_rho=max(result.rho for result in results),
        compression_status=terminal.decision,
        compression_interval=0,
        b_min=1,
        closed_next_state_consumption=not replay_skipped,
        structural_cost_status=terminal.decision,
        complete_cost_status=terminal.task4_status,
        complete_cost=None,
        amdahl_status=terminal.task4_status,
        amdahl_projection=None,
        fully_evaluated=structural_failure,
        failure_reason=terminal.decision,
        object_hashes=tuple(result.result_hash for result in results),
    )
    c2 = MechanismEvaluation(
        mechanism_id="C2",
        registered=False,
        source_status="PASS",
        equation_status="PASS",
        symbolic_independence_status=terminal.conversion_status,
        phase_status=terminal.conversion_status,
        schedule_status=terminal.conversion_status,
        rank_status=terminal.conversion_status,
        max_rho=0,
        compression_status=terminal.conversion_status,
        compression_interval=0,
        b_min=1,
        closed_next_state_consumption=False,
        structural_cost_status=terminal.conversion_status,
        complete_cost_status=terminal.task4_status,
        complete_cost=None,
        amdahl_status=terminal.task4_status,
        amdahl_projection=None,
        fully_evaluated=False,
        failure_reason=terminal.conversion_status,
        object_hashes=(),
    )
    return (c1, c2)


def _primary_mechanism(result: GateResult) -> MechanismEvaluation:
    registered = [
        mechanism for mechanism in result.mechanisms if mechanism.registered
    ]
    if not registered:
        return result.mechanisms[0]
    return registered[0]


def _evaluate_verified_terminal(root: Path) -> GateResult:
    try:
        terminal = terminal_record_for_task5(root)
        terminal.validate(root)
    except (OSError, TypeError, ValueError) as error:
        raise GateEvidenceError(
            "Candidate C requires a hash-bound terminal Task 3C record"
        ) from error
    if terminal.record_hash != APPROVED_TASK3C_HASH:
        raise GateEvidenceError(
            "Candidate C terminal Task 3C record is not the approved record"
        )
    if (
        terminal.classification != "REJECT"
        or terminal.decision
        != REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
    ):
        raise GateEvidenceError(
            "Candidate C terminal Task 3C record is not the approved REJECT "
            "route"
        )
    mechanisms = _actual_mechanisms(terminal)
    result = GateResult(
        terminal_record=terminal,
        decision=REJECT,
        terminal_classification=terminal.classification,
        terminal_decision=terminal.decision,
        terminal_record_hash=terminal.record_hash,
        task4_status=terminal.task4_status,
        complete_cost_status=terminal.task4_status,
        complete_cost=None,
        amdahl_status=terminal.task4_status,
        amdahl_projection=None,
        production_hot_path_permission=False,
        mechanisms=mechanisms,
        source_rows=_source_rows(terminal),
        schedule_rows=_schedule_rows(terminal),
        operator_rows=_operator_rows(terminal),
        relation_rows=_relation_rows(terminal),
        conversion_rows=(
            {
                "mechanism_id": "C2",
                "conversion_status": terminal.conversion_status,
                "registered_material": "no",
                "task4_status": terminal.task4_status,
            },
        ),
        hash_rows=(
            {
                "object": "terminal_record",
                "mechanism_id": "C1",
                "sha256": terminal.record_hash,
            },
            *(
                {
                    "object": f"operator_result_r{operator.r}",
                    "mechanism_id": "C1",
                    "sha256": operator.result_hash,
                }
                for operator in terminal.operator_results
            ),
        ),
        terminal_rows=(
            {
                "classification": terminal.classification,
                "decision": terminal.decision,
                "replay_status": terminal.replay_status,
                "task4_status": terminal.task4_status,
                "conversion_status": terminal.conversion_status,
                "r_values": ";".join(str(value) for value in terminal.r_values),
                "schedule_hash": terminal.schedule_hash,
                "record_hash": terminal.record_hash,
            },
        ),
        rank_rows=_rank_rows(terminal),
    )
    mechanism = _primary_mechanism(result)
    if (
        result.production_hot_path_permission
        or result.task4_status != terminal.task4_status
        or result.complete_cost_status != terminal.task4_status
        or result.amdahl_status != terminal.task4_status
        or result.complete_cost is not None
        or result.amdahl_projection is not None
        or mechanism.structural_cost_status != terminal.decision
    ):
        raise GateEvidenceError(
            "Candidate C fields do not derive from the terminal record"
        )
    return result


def evaluate_candidate_c(
    root: Path = ROOT,
    *,
    input_commit: str,
) -> GateResult:
    source_root = _resolved_directory(root, "source root")
    _validated_input_rows(
        source_root,
        input_commit,
        COMPUTATIONAL_INPUTS,
    )
    result = _evaluate_verified_terminal(source_root)
    _input_paths(source_root, result)
    return result


def validate_gate_result(
    result: GateResult,
    *,
    root: Path,
    input_commit: str,
) -> None:
    expected = evaluate_candidate_c(root, input_commit=input_commit)
    if result != expected:
        raise ValueError(
            "gate result does not match freshly verified Task 3C/Task 3A "
            "evidence"
        )


def _summary_from_verified_result(result: GateResult) -> dict[str, str]:
    mechanism = _primary_mechanism(result)
    values = {
        "decision": result.decision,
        "source_status": mechanism.source_status,
        "equation_status": mechanism.equation_status,
        "symbolic_independence_status": mechanism.symbolic_independence_status,
        "phase_status": mechanism.phase_status,
        "schedule_status": mechanism.schedule_status,
        "rank_status": mechanism.rank_status,
        "compression_status": mechanism.compression_status,
        "complete_cost_status": result.complete_cost_status,
        "complete_cost": (
            "" if result.complete_cost is None else f"{result.complete_cost:.9f}"
        ),
        "amdahl_status": result.amdahl_status,
        "amdahl_projection": (
            "" if result.amdahl_projection is None
            else f"{result.amdahl_projection:.9f}"
        ),
        "task4_status": result.task4_status,
        "mechanism_id": mechanism.mechanism_id,
        "max_rho": str(mechanism.max_rho),
        "compression_interval": str(mechanism.compression_interval),
        "b_min": str(mechanism.b_min),
        "closed_next_state_consumption": (
            "yes" if mechanism.closed_next_state_consumption else "no"
        ),
        "terminal_classification": result.terminal_classification,
        "terminal_decision": result.terminal_decision,
        "terminal_record_hash": result.terminal_record_hash,
        "production_hot_path_permission": "no",
    }
    return {field: values[field] for field in SUMMARY_FIELDS}


def canonical_summary_record(
    result: GateResult,
    *,
    root: Path,
    input_commit: str,
) -> dict[str, str]:
    validate_gate_result(
        result,
        root=root,
        input_commit=input_commit,
    )
    return _summary_from_verified_result(result)


def _write_csv(
    path: Path,
    fields: tuple[str, ...],
    rows: Iterable[Mapping[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="ascii", newline="\n")


def _resolved_directory(path: Path, label: str) -> Path:
    try:
        resolved = Path(path).resolve(strict=True)
    except OSError as error:
        raise GateEvidenceError(f"{label} cannot be resolved") from error
    if not resolved.is_dir():
        raise GateEvidenceError(f"{label} is not a directory: {resolved}")
    return resolved


def _resolve_under_root(
    root: Path,
    path: Path,
    label: str,
    *,
    strict: bool,
) -> Path:
    declared_root = _resolved_directory(root, "declared root")
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = declared_root / candidate
    try:
        resolved = candidate.resolve(strict=strict)
    except OSError as error:
        raise GateEvidenceError(f"{label} cannot be resolved") from error
    if not resolved.is_relative_to(declared_root):
        raise GateEvidenceError(
            f"{label} escapes declared root: {resolved}"
        )
    return resolved


def _resolve_input_commit(root: Path, input_commit: str) -> str:
    if (
        not isinstance(input_commit, str)
        or re.fullmatch(
            r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})",
            input_commit,
        )
        is None
    ):
        raise GateEvidenceError(
            f"invalid implementation-input commit: {input_commit}"
        )
    try:
        resolved = subprocess.run(
            [
                "git",
                "rev-parse",
                "--verify",
                input_commit,
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise GateEvidenceError(
            f"invalid implementation-input commit: {input_commit}"
        ) from error
    try:
        object_type = subprocess.run(
            ["git", "cat-file", "-t", resolved],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise GateEvidenceError(
            f"invalid implementation-input commit: {input_commit}"
        ) from error
    if object_type != "commit":
        raise GateEvidenceError(
            f"invalid implementation-input commit: {input_commit}"
        )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", resolved, "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if ancestor.returncode == 1:
        raise GateEvidenceError(
            f"implementation-input commit is not an ancestor of HEAD: "
            f"{resolved}"
        )
    if ancestor.returncode != 0:
        raise GateEvidenceError(
            "cannot validate implementation-input commit ancestry"
        )
    return resolved


def _git_regular_blob(root: Path, commit: str, relative: str) -> bytes:
    try:
        entry = subprocess.run(
            ["git", "ls-tree", commit, "--", relative],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.rstrip("\n")
    except (OSError, subprocess.CalledProcessError) as error:
        raise GateEvidenceError(
            f"cannot inspect implementation-input blob: {relative}"
        ) from error
    if not entry or "\t" not in entry:
        raise GateEvidenceError(
            f"implementation-input commit has no file: {relative}"
        )
    metadata, recorded_path = entry.split("\t", 1)
    try:
        mode, object_type, object_id = metadata.split()
    except ValueError as error:
        raise GateEvidenceError(
            f"malformed implementation-input tree entry: {relative}"
        ) from error
    if (
        recorded_path != relative
        or object_type != "blob"
        or mode not in {"100644", "100755"}
    ):
        raise GateEvidenceError(
            f"implementation-input path is not a regular file: {relative}"
        )
    try:
        return subprocess.run(
            ["git", "cat-file", "blob", object_id],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise GateEvidenceError(
            f"cannot read implementation-input blob: {relative}"
        ) from error


def _validated_input_rows(
    root: Path,
    input_commit: str,
    paths: Iterable[str],
) -> tuple[str, tuple[dict[str, str], ...]]:
    source_root = _resolved_directory(root, "source root")
    commit = _resolve_input_commit(source_root, input_commit)
    relative_paths = tuple(paths)
    if (
        relative_paths != tuple(sorted(relative_paths))
        or len(relative_paths) != len(set(relative_paths))
    ):
        raise GateEvidenceError(
            "computational input manifest must be unique and sorted"
        )
    rows = []
    for relative in relative_paths:
        if (
            not relative
            or Path(relative).is_absolute()
            or "\\" in relative
            or ".." in Path(relative).parts
        ):
            raise GateEvidenceError(
                f"invalid computational input path: {relative}"
            )
        path = _resolve_under_root(
            source_root,
            source_root / relative,
            f"manifest source {relative}",
            strict=False,
        )
        if not path.is_file():
            raise GateEvidenceError(
                f"missing computational input: {relative}"
            )
        committed = _git_regular_blob(source_root, commit, relative)
        working = path.read_bytes()
        if working != committed:
            raise GateEvidenceError(
                f"computational input does not match implementation-input "
                f"commit: {relative}"
            )
        rows.append(
            {
                "path": relative,
                "sha256": _sha256_bytes(committed),
            }
        )
    return commit, tuple(rows)


def _input_paths(
    root: Path,
    result: GateResult,
) -> tuple[str, ...]:
    del root
    bound_paths = {str(row["path"]) for row in result.source_rows}
    if not bound_paths.issubset(COMPUTATIONAL_INPUTS):
        missing = sorted(bound_paths.difference(COMPUTATIONAL_INPUTS))
        raise GateEvidenceError(
            "terminal record introduced an unmanifested input: "
            + ", ".join(missing)
        )
    return COMPUTATIONAL_INPUTS


def _mechanism_rows(
    mechanisms: tuple[MechanismEvaluation, ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "mechanism_id": mechanism.mechanism_id,
            "registered": "yes" if mechanism.registered else "no",
            "source_status": mechanism.source_status,
            "equation_status": mechanism.equation_status,
            "symbolic_independence_status": mechanism.symbolic_independence_status,
            "phase_status": mechanism.phase_status,
            "schedule_status": mechanism.schedule_status,
            "rank_status": mechanism.rank_status,
            "max_rho": mechanism.max_rho,
            "compression_status": mechanism.compression_status,
            "compression_interval": mechanism.compression_interval,
            "b_min": mechanism.b_min,
            "closed_next_state_consumption": (
                "yes" if mechanism.closed_next_state_consumption else "no"
            ),
            "structural_cost_status": mechanism.structural_cost_status,
            "complete_cost_status": mechanism.complete_cost_status,
            "amdahl_status": mechanism.amdahl_status,
            "fully_evaluated": "yes" if mechanism.fully_evaluated else "no",
            "failure_reason": mechanism.failure_reason,
        }
        for mechanism in mechanisms
    )


def _report(result: GateResult, input_commit: str) -> str:
    summary = _summary_from_verified_result(result)
    return f"""# Candidate C Rank-Bounded Mechanism Gate

## Decision

`{result.decision}`

Candidate C closes on the finite C1/C2 mechanism campaign. The hash-bound
Task 3C terminal record is `{result.terminal_record_hash}` and records
`{result.terminal_decision}`. C2 has `{NO_VERIFIED_TASK3B_RESULT}`.

## Gate Summary

- Source: `{summary["source_status"]}`
- Equations: `{summary["equation_status"]}`
- Symbolic independence: `{summary["symbolic_independence_status"]}`
- Phase: `{summary["phase_status"]}`
- Schedule: `{summary["schedule_status"]}`
- Rank: `{summary["rank_status"]}`
- Compression/structural gate: `{summary["compression_status"]}`
- Complete cost: `{summary["complete_cost_status"]}`
- Amdahl projection: `{summary["amdahl_status"]}`

Task 4 is exactly `{SKIPPED}`. No complete-cost or Amdahl number is inferred.
This is a finite mechanism rejection, not a general impossibility, security,
noise, production, or bootstrapping-speedup claim. The exact-dense PVW/MAT-SAB
implementation and its scoped measured result remain unchanged.

## Reproduction

Implementation-input commit: `{input_commit}`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit {input_commit}
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit {input_commit}
```
"""


def _variant(result: GateResult, input_commit: str) -> str:
    return f"""# Candidate C Rank-Bounded Shared-Mask State

The registered C1 equation uses `rho <= 2`, exact phase projections, the
source-bound binary schedule, and a closed-consumption obligation. Its real
Task 3A records for `r=2,4,6` all end at
`{result.terminal_decision}`. The resulting Task 3C record is
`{result.terminal_record_hash}`.

C2 has no verified Task 3B conversion material. Task 4 therefore remains
`{SKIPPED}` with blank numeric cost and Amdahl fields. Production permission
is false.

Reproduce from implementation-input commit `{input_commit}` with
`python scripts/run_candidate_c_rank_bounded_gate.py --input-commit {input_commit}`.
"""


def _experiment(result: GateResult, input_commit: str) -> str:
    return f"""# Candidate C Rank-Bounded Gate Plan

1. Recompute the C1 operator tensor for `r=2,4,6`.
2. Bind source, equations, symbolic relations, phase, schedule, rank, and
   compression/structural cost in one canonical summary.
3. Preserve `{NO_VERIFIED_TASK3B_RESULT}` for C2.
4. Preserve `{SKIPPED}` for Task 4 without numeric substitution.
5. Apply `{result.decision}` atomically to the research state and ledgers.

This plan closes the finite Candidate C mechanism budget. It does not authorize
production work and does not create Candidate D.

Implementation-input commit: `{input_commit}`. Reproduce with
`python scripts/run_candidate_c_rank_bounded_gate.py --input-commit {input_commit}`.
"""


def _render_gate_artifacts(
    source_root: Path,
    destination: Path,
    result: GateResult,
    *,
    input_commit: str,
    input_rows: tuple[dict[str, str], ...],
) -> tuple[Path, ...]:
    out = destination / OUT
    out.mkdir(parents=True, exist_ok=True)

    summary = _summary_from_verified_result(result)
    _write_csv(out / "summary.csv", SUMMARY_FIELDS, (summary,))
    _write_csv(
        out / "source_mapping.csv",
        (
            "source_id",
            "path",
            "sha256",
            "classification",
            "required_tokens",
            "status",
        ),
        result.source_rows,
    )
    _write_csv(
        out / "schedule_trace.csv",
        tuple(result.schedule_rows[0]),
        result.schedule_rows,
    )
    _write_csv(
        out / "operator_tensor.csv",
        tuple(result.operator_rows[0]),
        result.operator_rows,
    )
    _write_csv(
        out / "evaluator_sample_relations.csv",
        tuple(result.relation_rows[0]),
        result.relation_rows,
    )
    _write_csv(
        out / "conversion_material.csv",
        tuple(result.conversion_rows[0]),
        result.conversion_rows,
    )
    _write_csv(
        out / "registered_object_hash.csv",
        tuple(result.hash_rows[0]),
        result.hash_rows,
    )
    _write_csv(
        out / "terminal_record.csv",
        tuple(result.terminal_rows[0]),
        result.terminal_rows,
    )
    _write_csv(
        out / "rank_growth.csv",
        tuple(result.rank_rows[0]),
        result.rank_rows,
    )
    mechanism_rows = _mechanism_rows(result.mechanisms)
    _write_csv(
        out / "compression_gate.csv",
        (
            "mechanism_id",
            "registered",
            "max_rho",
            "compression_status",
            "compression_interval",
            "b_min",
            "closed_next_state_consumption",
            "structural_cost_status",
            "failure_reason",
        ),
        (
            {
                field: row[field]
                for field in (
                    "mechanism_id",
                    "registered",
                    "max_rho",
                    "compression_status",
                    "compression_interval",
                    "b_min",
                    "closed_next_state_consumption",
                    "structural_cost_status",
                    "failure_reason",
                )
            }
            for row in mechanism_rows
        ),
    )
    _write_csv(
        out / "complete_cost.csv",
        ("mechanism_id", "status", "complete_cost"),
        (
            {
                "mechanism_id": mechanism.mechanism_id,
                "status": mechanism.complete_cost_status,
                "complete_cost": (
                    "" if mechanism.complete_cost is None
                    else f"{mechanism.complete_cost:.9f}"
                ),
            }
            for mechanism in result.mechanisms
        ),
    )
    _write_csv(
        out / "amdahl_projection.csv",
        ("mechanism_id", "status", "central_projection"),
        (
            {
                "mechanism_id": mechanism.mechanism_id,
                "status": mechanism.amdahl_status,
                "central_projection": (
                    "" if mechanism.amdahl_projection is None
                    else f"{mechanism.amdahl_projection:.9f}"
                ),
            }
            for mechanism in result.mechanisms
        ),
    )
    _write_csv(
        out / "mechanism_matrix.csv",
        tuple(mechanism_rows[0]),
        mechanism_rows,
    )
    _write_csv(
        out / "proof_gate.csv",
        (
            "gate",
            "status",
            "classification",
            "evidence",
        ),
        (
            {
                "gate": "task3c_terminal_record",
                "status": "PASS",
                "classification": result.terminal_classification,
                "evidence": result.terminal_record_hash,
            },
            {
                "gate": "task4_complete_cost",
                "status": result.complete_cost_status,
                "classification": "no_numeric_substitution",
                "evidence": "complete_cost.csv",
            },
            {
                "gate": "task4_amdahl_projection",
                "status": result.amdahl_status,
                "classification": "no_numeric_substitution",
                "evidence": "amdahl_projection.csv",
            },
            {
                "gate": "production_hot_path_permission",
                "status": "NO",
                "classification": "completion_boundary",
                "evidence": result.decision,
            },
        ),
    )
    expected_inputs = _input_paths(source_root, result)
    if tuple(row["path"] for row in input_rows) != expected_inputs:
        raise GateEvidenceError(
            "verified computational inputs do not match the manifest"
        )
    _write_csv(
        out / "input_manifest.csv",
        ("path", "sha256"),
        input_rows,
    )
    _write_csv(
        out / "environment.csv",
        ("key", "value"),
        (
            {"key": "input_head", "value": input_commit},
            {"key": "python_version", "value": platform.python_version()},
            {"key": "platform", "value": platform.platform()},
            {"key": "terminal_record_hash", "value": result.terminal_record_hash},
        ),
    )
    _write_text(
        out / "reproduction_commands.md",
        f"""# Candidate C Rank-Bounded Gate Reproduction

Implementation-input commit: `{input_commit}`

```text
python scripts/run_candidate_c_rank_bounded_gate.py --input-commit {input_commit}
python scripts/apply_candidate_c_rank_bounded_gate.py --input-commit {input_commit}
python scripts/build_mat_sab_selector_techgraph.py --input-commit {input_commit}
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
""",
    )

    docs = destination / "docs/candidate_c_rank_bounded_mechanism_gate.md"
    variant = destination / "algorithm_variants/candidate_c_rank_bounded_state.md"
    experiment = destination / "experiments/candidate_c_rank_bounded_gate_plan.md"
    _write_text(docs, _report(result, input_commit))
    _write_text(variant, _variant(result, input_commit))
    _write_text(experiment, _experiment(result, input_commit))

    indexed = tuple(
        sorted(
            (
                *(path for path in out.iterdir() if path.name != "artifact_index.csv"),
                docs,
                variant,
                experiment,
            ),
            key=lambda path: path.relative_to(destination).as_posix(),
        )
    )
    _write_csv(
        out / "artifact_index.csv",
        ("path", "sha256"),
        (
            {
                "path": path.relative_to(destination).as_posix(),
                "sha256": _sha256_bytes(path.read_bytes()),
            }
            for path in indexed
        ),
    )
    paths = tuple(
        sorted(
            (*indexed, out / "artifact_index.csv"),
            key=lambda path: path.relative_to(destination).as_posix(),
        )
    )
    pack_names = {path.name for path in out.iterdir()}
    if pack_names != set(REQUIRED_PACK_FILES):
        raise RuntimeError("Candidate C reproducibility pack is incomplete")
    for path in paths:
        path.read_bytes().decode("ascii")
    return paths


def _preflight_destinations(destination: Path) -> None:
    relative_paths = (
        *(OUT / name for name in REQUIRED_PACK_FILES),
        *(Path(relative) for relative in GENERATED_DOCUMENTS),
    )
    for relative in (OUT, *relative_paths):
        candidate = destination / relative
        resolved = _resolve_under_root(
            destination,
            candidate,
            f"generated destination {relative.as_posix()}",
            strict=False,
        )
        if relative == OUT:
            if candidate.exists() and not resolved.is_dir():
                raise GateEvidenceError(
                    f"pack destination is not a directory: {resolved}"
                )
        elif candidate.exists() and not resolved.is_file():
            raise GateEvidenceError(
                f"generated destination is not a file: {resolved}"
            )


def _restore_file_atomic(path: Path, content: bytes | None) -> None:
    if content is None:
        if os.path.lexists(path):
            path.unlink()
        return
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".candidate-c-restore-",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _publish_staged_outputs(
    destination: Path,
    stage: Path,
) -> tuple[Path, ...]:
    relative_paths = tuple(
        sorted(
            (
                *(OUT / name for name in REQUIRED_PACK_FILES),
                *(Path(relative) for relative in GENERATED_DOCUMENTS),
            ),
            key=lambda path: path.as_posix(),
        )
    )
    pack_destination = destination / OUT
    pack_source = stage / OUT
    pack_backup = stage / ".candidate-c-previous-pack"
    document_relatives = tuple(Path(path) for path in GENERATED_DOCUMENTS)
    document_snapshots = {
        relative: (
            (destination / relative).read_bytes()
            if (destination / relative).is_file()
            else None
        )
        for relative in document_relatives
    }
    previous_pack_moved = False
    staged_pack_published = False
    published_documents: list[Path] = []
    try:
        pack_destination.parent.mkdir(parents=True, exist_ok=True)
        for relative in document_relatives:
            (destination / relative).parent.mkdir(
                parents=True,
                exist_ok=True,
            )
        _preflight_destinations(destination)
        if os.path.lexists(pack_destination):
            os.replace(pack_destination, pack_backup)
            previous_pack_moved = True
        os.replace(pack_source, pack_destination)
        staged_pack_published = True
        for relative in document_relatives:
            os.replace(stage / relative, destination / relative)
            published_documents.append(relative)
    except Exception:
        for relative in reversed(published_documents):
            _restore_file_atomic(
                destination / relative,
                document_snapshots[relative],
            )
        if staged_pack_published and os.path.lexists(pack_destination):
            failed_pack = stage / ".candidate-c-failed-pack"
            os.replace(pack_destination, failed_pack)
        if previous_pack_moved and os.path.lexists(pack_backup):
            os.replace(pack_backup, pack_destination)
        raise
    return tuple(destination / relative for relative in relative_paths)


def write_gate_artifacts(
    root: Path,
    result: GateResult,
    *,
    input_commit: str,
    destination_root: Path | None = None,
) -> tuple[Path, ...]:
    source_root = _resolved_directory(root, "source root")
    expected = evaluate_candidate_c(
        source_root,
        input_commit=input_commit,
    )
    if result != expected:
        raise ValueError(
            "gate result does not match freshly verified Task 3C/Task 3A "
            "evidence"
        )
    resolved_commit, input_rows = _validated_input_rows(
        source_root,
        input_commit,
        _input_paths(source_root, expected),
    )
    destination = _resolved_directory(
        source_root if destination_root is None else destination_root,
        "destination root",
    )
    _preflight_destinations(destination)
    stage = Path(
        tempfile.mkdtemp(
            prefix=".candidate-c-stage-",
            dir=destination,
        )
    )
    _resolve_under_root(
        destination,
        stage,
        "Candidate C staging directory",
        strict=True,
    )
    try:
        _preflight_destinations(stage)
        _render_gate_artifacts(
            source_root,
            stage,
            expected,
            input_commit=resolved_commit,
            input_rows=input_rows,
        )
        return _publish_staged_outputs(destination, stage)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--destination-root", type=Path)
    parser.add_argument("--input-commit", required=True)
    args = parser.parse_args()
    result = evaluate_candidate_c(
        args.root,
        input_commit=args.input_commit,
    )
    write_gate_artifacts(
        args.root,
        result,
        input_commit=args.input_commit,
        destination_root=args.destination_root,
    )
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
