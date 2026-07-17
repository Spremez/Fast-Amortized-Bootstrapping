#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
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
    TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED,
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


def _sha256_json(value: object) -> str:
    return _sha256_bytes(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    )


def _synthetic_terminal_hash(
    classification: str,
    decision: str,
    mechanisms: tuple[MechanismEvaluation, ...],
) -> str:
    return _sha256_json(
        {
            "classification": classification,
            "decision": decision,
            "mechanisms": [asdict(mechanism) for mechanism in mechanisms],
            "schema": "candidate-c-task-5-synthetic-terminal-v1",
        }
    )


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
    c1 = MechanismEvaluation(
        mechanism_id="C1",
        registered=True,
        source_status="PASS",
        equation_status="PASS",
        symbolic_independence_status="PASS_SCOPED_NO_SECURITY_CLAIM",
        phase_status=_status(all(result.phase_identity_passed for result in results)),
        schedule_status="PASS",
        rank_status=_status(all(result.joint_rank_passed for result in results)),
        max_rho=max(result.rho for result in results),
        compression_status=REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
        compression_interval=0,
        b_min=1,
        closed_next_state_consumption=False,
        structural_cost_status=REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
        complete_cost_status=SKIPPED,
        complete_cost=None,
        amdahl_status=SKIPPED,
        amdahl_projection=None,
        fully_evaluated=True,
        failure_reason=terminal.decision,
        object_hashes=tuple(result.result_hash for result in results),
    )
    c2 = MechanismEvaluation(
        mechanism_id="C2",
        registered=False,
        source_status="PASS",
        equation_status="PASS",
        symbolic_independence_status=NO_VERIFIED_TASK3B_RESULT,
        phase_status=NO_VERIFIED_TASK3B_RESULT,
        schedule_status=NO_VERIFIED_TASK3B_RESULT,
        rank_status=NO_VERIFIED_TASK3B_RESULT,
        max_rho=0,
        compression_status=NO_VERIFIED_TASK3B_RESULT,
        compression_interval=0,
        b_min=1,
        closed_next_state_consumption=False,
        structural_cost_status=NO_VERIFIED_TASK3B_RESULT,
        complete_cost_status=SKIPPED,
        complete_cost=None,
        amdahl_status=SKIPPED,
        amdahl_projection=None,
        fully_evaluated=False,
        failure_reason=NO_VERIFIED_TASK3B_RESULT,
        object_hashes=(),
    )
    return (c1, c2)


def _mechanism_passes(mechanism: MechanismEvaluation) -> bool:
    return (
        mechanism.mechanism_id in {"C1", "C2"}
        and mechanism.registered
        and mechanism.source_status == "PASS"
        and mechanism.equation_status == "PASS"
        and mechanism.symbolic_independence_status == "PASS"
        and mechanism.phase_status == "PASS"
        and mechanism.schedule_status == "PASS"
        and mechanism.rank_status == "PASS"
        and mechanism.max_rho <= 2
        and mechanism.compression_status == "PASS"
        and mechanism.compression_interval >= mechanism.b_min
        and mechanism.closed_next_state_consumption
        and mechanism.structural_cost_status == "PASS"
        and mechanism.complete_cost_status == "PASS"
        and mechanism.complete_cost is not None
        and mechanism.complete_cost > 0
        and mechanism.amdahl_status == "PASS"
        and mechanism.amdahl_projection is not None
        and mechanism.amdahl_projection > 1.0
        and mechanism.fully_evaluated
    )


def _validate_terminal_binding(result: GateResult) -> None:
    digest = result.terminal_record_hash
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("terminal record hash is malformed")
    if result.terminal_classification == "REJECT":
        actual = (
            result.terminal_decision
            == REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
            and digest == APPROVED_TASK3C_HASH
        )
        synthetic = (
            result.terminal_decision.startswith("REJECT_C")
            and digest
            == _synthetic_terminal_hash(
                result.terminal_classification,
                result.terminal_decision,
                result.mechanisms,
            )
        )
        valid = actual or synthetic
    elif result.terminal_classification == "INCONCLUSIVE":
        valid = (
            result.terminal_decision
            == TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED
            and digest
            == _synthetic_terminal_hash(
                result.terminal_classification,
                result.terminal_decision,
                result.mechanisms,
            )
        )
    elif result.terminal_classification == "ADMIT":
        valid = (
            result.terminal_decision
            in {
                "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY",
                "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY",
            }
            and digest
            == _synthetic_terminal_hash(
                result.terminal_classification,
                result.terminal_decision,
                result.mechanisms,
            )
        )
    else:
        valid = False
    if not valid:
        raise ValueError("terminal record does not match hash-bound evidence")


def _derived_decision(result: GateResult) -> str:
    _validate_terminal_binding(result)
    if any(_mechanism_passes(mechanism) for mechanism in result.mechanisms):
        return ADMIT
    if result.terminal_classification == "REJECT" and any(
        mechanism.registered
        and mechanism.fully_evaluated
        and mechanism.failure_reason == result.terminal_decision
        for mechanism in result.mechanisms
    ):
        return REJECT
    if result.terminal_classification == "INCONCLUSIVE":
        return INCONCLUSIVE
    raise GateEvidenceError(
        "Candidate C evidence is neither an admitted mechanism nor a "
        "hash-bound terminal result"
    )


def _primary_mechanism(result: GateResult) -> MechanismEvaluation:
    registered = [
        mechanism for mechanism in result.mechanisms if mechanism.registered
    ]
    if not registered:
        return result.mechanisms[0]
    return registered[0]


def validate_gate_result(result: GateResult) -> None:
    expected = _derived_decision(result)
    if result.decision != expected:
        raise ValueError(
            "decision does not match mechanism and terminal evidence"
        )
    if result.production_hot_path_permission:
        raise ValueError("Candidate C gate cannot enable production code")
    mechanism = _primary_mechanism(result)
    if (
        result.task4_status != mechanism.complete_cost_status
        or result.complete_cost_status != mechanism.complete_cost_status
        or result.complete_cost != mechanism.complete_cost
        or result.amdahl_status != mechanism.amdahl_status
        or result.amdahl_projection != mechanism.amdahl_projection
    ):
        raise ValueError("Task 4 fields do not match the selected mechanism")
    if result.task4_status == SKIPPED and (
        result.complete_cost is not None
        or result.amdahl_projection is not None
    ):
        raise ValueError("skipped Task 4 cannot contain numeric values")
    if expected in {ADMIT} and (
        result.complete_cost_status != "PASS"
        or result.amdahl_status != "PASS"
    ):
        raise ValueError("admission requires numeric Task 4 evidence")


def evaluate_candidate_c(root: Path = ROOT) -> GateResult:
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
    mechanisms = _actual_mechanisms(terminal)
    result = GateResult(
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
    validate_gate_result(result)
    return result


def synthetic_gate_result(result: GateResult, decision: str) -> GateResult:
    if decision == ADMIT:
        base = result.mechanisms[0]
        mechanism = replace(
            base,
            symbolic_independence_status="PASS",
            phase_status="PASS",
            schedule_status="PASS",
            rank_status="PASS",
            max_rho=min(2, base.max_rho),
            compression_status="PASS",
            compression_interval=8,
            b_min=4,
            closed_next_state_consumption=True,
            structural_cost_status="PASS",
            complete_cost_status="PASS",
            complete_cost=1.0,
            amdahl_status="PASS",
            amdahl_projection=1.01,
            fully_evaluated=True,
            failure_reason="",
        )
        mechanisms = (mechanism,)
        classification = "ADMIT"
        terminal_decision = "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY"
        terminal_hash = _synthetic_terminal_hash(
            classification,
            terminal_decision,
            mechanisms,
        )
        changed = replace(
            result,
            decision=decision,
            terminal_classification=classification,
            terminal_decision=terminal_decision,
            terminal_record_hash=terminal_hash,
            task4_status="PASS",
            complete_cost_status="PASS",
            complete_cost=mechanism.complete_cost,
            amdahl_status="PASS",
            amdahl_projection=mechanism.amdahl_projection,
            mechanisms=mechanisms,
        )
    elif decision == INCONCLUSIVE:
        mechanism = replace(
            result.mechanisms[0],
            registered=False,
            fully_evaluated=False,
            failure_reason=TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED,
        )
        mechanisms = (mechanism,)
        classification = "INCONCLUSIVE"
        terminal_decision = TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED
        terminal_hash = _synthetic_terminal_hash(
            classification,
            terminal_decision,
            mechanisms,
        )
        changed = replace(
            result,
            decision=decision,
            terminal_classification=classification,
            terminal_decision=terminal_decision,
            terminal_record_hash=terminal_hash,
            mechanisms=mechanisms,
        )
    elif decision == REJECT:
        changed = result
    else:
        raise ValueError("unknown Candidate C decision")
    validate_gate_result(changed)
    return changed


def synthetic_reject_after_cost(result: GateResult) -> GateResult:
    admitted = synthetic_gate_result(result, ADMIT)
    terminal_decision = (
        "REJECT_C1_NONPOSITIVE_AMDAHL_PROJECTION_TERMINAL"
    )
    mechanism = replace(
        admitted.mechanisms[0],
        amdahl_status="FAIL_NONPOSITIVE_CENTRAL_PROJECTION",
        amdahl_projection=0.99,
        failure_reason=terminal_decision,
    )
    mechanisms = (mechanism,)
    terminal_hash = _synthetic_terminal_hash(
        "REJECT",
        terminal_decision,
        mechanisms,
    )
    rejected = replace(
        admitted,
        decision=REJECT,
        terminal_classification="REJECT",
        terminal_decision=terminal_decision,
        terminal_record_hash=terminal_hash,
        amdahl_status=mechanism.amdahl_status,
        amdahl_projection=mechanism.amdahl_projection,
        mechanisms=mechanisms,
    )
    validate_gate_result(rejected)
    return rejected


def canonical_summary_record(result: GateResult) -> dict[str, str]:
    validate_gate_result(result)
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


def _git_head(root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise GateEvidenceError("cannot bind Candidate C evidence to git HEAD") from error


def _input_paths(
    root: Path,
    result: GateResult,
) -> tuple[str, ...]:
    paths = {
        "scripts/run_candidate_c_rank_bounded_gate.py",
        "research/mat_sab/candidate_c_registered_replay.py",
        "research/mat_sab/candidate_c_operator_tensor.py",
        "research/mat_sab/candidate_c_schedule.py",
        "research/mat_sab/rank_bounded_state_model.py",
        "paper_techgraphs/candidate_c_rank_bounded_state.yaml",
        "theory_checks/candidate_c_rank_bounded_state_model.md",
    }
    paths.update(str(row["path"]) for row in result.source_rows)
    for relative in (
        "main.c",
        "src/sparse_amortized_bootstrap.c",
        "src/sab_pvw.c",
        "src/mosfhet/Makefile.def",
    ):
        if (root / relative).is_file():
            paths.add(relative)
    return tuple(sorted(paths))


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


def _report(result: GateResult) -> str:
    summary = canonical_summary_record(result)
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
"""


def _variant(result: GateResult) -> str:
    return f"""# Candidate C Rank-Bounded Shared-Mask State

The registered C1 equation uses `rho <= 2`, exact phase projections, the
source-bound binary schedule, and a closed-consumption obligation. Its real
Task 3A records for `r=2,4,6` all end at
`{result.terminal_decision}`. The resulting Task 3C record is
`{result.terminal_record_hash}`.

C2 has no verified Task 3B conversion material. Task 4 therefore remains
`{SKIPPED}` with blank numeric cost and Amdahl fields. Production permission
is false.
"""


def _experiment(result: GateResult) -> str:
    return f"""# Candidate C Rank-Bounded Gate Plan

1. Recompute the C1 operator tensor for `r=2,4,6`.
2. Bind source, equations, symbolic relations, phase, schedule, rank, and
   compression/structural cost in one canonical summary.
3. Preserve `{NO_VERIFIED_TASK3B_RESULT}` for C2.
4. Preserve `{SKIPPED}` for Task 4 without numeric substitution.
5. Apply `{result.decision}` atomically to the research state and ledgers.

This plan closes the finite Candidate C mechanism budget. It does not authorize
production work and does not create Candidate D.
"""


def write_gate_artifacts(
    root: Path,
    result: GateResult,
    *,
    destination_root: Path | None = None,
) -> tuple[Path, ...]:
    validate_gate_result(result)
    source_root = Path(root).resolve()
    destination = (
        source_root if destination_root is None
        else Path(destination_root).resolve()
    )
    out = destination / OUT
    out.mkdir(parents=True, exist_ok=True)

    summary = canonical_summary_record(result)
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
    input_rows = []
    for relative in _input_paths(source_root, result):
        path = source_root / relative
        if not path.is_file():
            raise GateEvidenceError(f"missing input manifest path: {relative}")
        input_rows.append(
            {"path": relative, "sha256": _sha256_bytes(path.read_bytes())}
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
            {"key": "input_head", "value": _git_head(source_root)},
            {"key": "python_version", "value": platform.python_version()},
            {"key": "platform", "value": platform.platform()},
            {"key": "terminal_record_hash", "value": result.terminal_record_hash},
        ),
    )
    _write_text(
        out / "reproduction_commands.md",
        """# Candidate C Rank-Bounded Gate Reproduction

```text
python scripts/run_candidate_c_rank_bounded_gate.py
python scripts/apply_candidate_c_rank_bounded_gate.py
python -m unittest discover -s tests/research -p "test_*.py" -v
python scripts/mat_sab_research_state.py validate
git diff --check
```
""",
    )

    docs = destination / "docs/candidate_c_rank_bounded_mechanism_gate.md"
    variant = destination / "algorithm_variants/candidate_c_rank_bounded_state.md"
    experiment = destination / "experiments/candidate_c_rank_bounded_gate_plan.md"
    _write_text(docs, _report(result))
    _write_text(variant, _variant(result))
    _write_text(experiment, _experiment(result))

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = evaluate_candidate_c(args.root)
    write_gate_artifacts(args.root, result)
    print(result.decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
