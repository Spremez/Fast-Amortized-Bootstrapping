"""Registered Candidate C replay and terminal routing for Task 3C.

The current repository has no registered Candidate C operator: every
recomputed Task 3A gate ends in the same scoped C1 rejection.  This module
binds that result without manufacturing C1 admission or C2 material.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .candidate_c_operator_tensor import (
    ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
    RING_MODULUS,
    ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2,
    TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED,
    OperatorGateResult,
    run_c1_operator_gate,
    verify_operator_gate_result,
)
from .candidate_c_schedule import (
    ScheduleEvent,
    iter_binary_schedule_events,
    load_binary_target_schedule,
)


SKIPPED_NO_REGISTERED_OPERATOR = "SKIPPED_NO_REGISTERED_OPERATOR"
_EXPECTED_R_VALUES = (2, 4, 6)
_EXPECTED_COUNTS = {
    "h": 39,
    "monomial_calls": 40,
    "r_prec": 7,
    "in_N": 2048,
    "selector_events": 573440,
    "ncmux_events": 5080,
    "cmux_events": 568360,
    "butterfly_boundaries": 280,
    "monomial_boundaries": 40,
    "sub_a_boundaries": 39,
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sentinel_digest(kind: str) -> str:
    return _sha256(
        {
            "kind": kind,
            "status": SKIPPED_NO_REGISTERED_OPERATOR,
            "task3b_registered": False,
        }
    )


NO_REGISTERED_CONVERSION_BOUNDARY_DIGEST = _sentinel_digest(
    "C2_CONVERSION_BOUNDARIES"
)
NO_REGISTERED_CONVERSION_KEY_IDENTITY_DIGEST = _sentinel_digest(
    "C2_CONVERSION_KEY_IDENTITIES"
)


class NoRegisteredCandidateCOperator(RuntimeError):
    """Raised when Task 4 requests an operator from a terminal Task 3 route."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class _ScheduleBinding:
    schedule_hash: str
    schedule_event_digest: str
    state_edge_digest: str
    h: int
    monomial_calls: int
    r_prec: int
    in_N: int
    selector_events: int
    ncmux_events: int
    cmux_events: int
    butterfly_boundaries: int
    monomial_boundaries: int
    sub_a_boundaries: int


@dataclass(frozen=True)
class RegisteredScheduleTrace:
    r: int
    operator_result_hash: str
    schedule_hash: str
    schedule_event_digest: str
    state_edge_digest: str
    state_identity_digest: str
    selector_events: int
    ncmux_events: int
    cmux_events: int
    butterfly_boundaries: int
    monomial_boundaries: int
    sub_a_boundaries: int
    phase_checks: int
    rank_checks: int
    accumulator_state_identities: int
    max_rho: int
    status: str
    trace_hash: str

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(asdict(self))


@dataclass(frozen=True)
class RegisteredOperatorArtifact:
    operator_results: tuple[OperatorGateResult, ...]
    traces: tuple[RegisteredScheduleTrace, ...]
    conversion_result: None
    decision: str
    artifact_hash: str

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(asdict(self))

    def verify(self, root: Path | str) -> bool:
        try:
            expected = registered_operator_for_task4(root)
        except (NoRegisteredCandidateCOperator, TypeError, ValueError):
            return False
        return self == expected


@dataclass(frozen=True)
class CandidateCTerminalRecord:
    schema: str
    classification: str
    decision: str
    replay_status: str
    task4_status: str
    r_values: tuple[int, ...]
    operator_results: tuple[OperatorGateResult, ...]
    schedule_hash: str
    schedule_event_digest: str
    state_edge_digest: str
    conversion_boundary_digest: str
    conversion_key_identity_digest: str
    h: int
    monomial_calls: int
    r_prec: int
    in_N: int
    selector_events: int
    ncmux_events: int
    cmux_events: int
    butterfly_boundaries: int
    monomial_boundaries: int
    sub_a_boundaries: int
    record_hash: str

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(asdict(self))

    def validate(self, root: Path | str) -> None:
        _validate_terminal_record(self, root)

    def verify(self, root: Path | str) -> bool:
        try:
            self.validate(root)
        except (TypeError, ValueError):
            return False
        return True


def _event_bytes(event: ScheduleEvent) -> bytes:
    return _canonical_bytes(asdict(event))


def _schedule_binding(root: Path | str) -> _ScheduleBinding:
    schedule = load_binary_target_schedule(root)
    event_hasher = hashlib.sha256()
    edge_hasher = hashlib.sha256()
    counts: Counter[str] = Counter()
    previous: dict[str, Any] | None = None

    for event in iter_binary_schedule_events(schedule):
        event_dict = asdict(event)
        event_hasher.update(_event_bytes(event))
        event_hasher.update(b"\n")
        edge_hasher.update(
            _canonical_bytes(
                {
                    "previous": previous,
                    "current": event_dict,
                }
            )
        )
        edge_hasher.update(b"\n")
        counts[event.kind] += 1
        previous = event_dict

    binding = _ScheduleBinding(
        schedule_hash=_sha256(asdict(schedule)),
        schedule_event_digest=event_hasher.hexdigest(),
        state_edge_digest=edge_hasher.hexdigest(),
        h=schedule.h,
        monomial_calls=schedule.monomial_calls,
        r_prec=schedule.r_prec,
        in_N=schedule.in_N,
        selector_events=counts["ncmux"] + counts["cmux"],
        ncmux_events=counts["ncmux"],
        cmux_events=counts["cmux"],
        butterfly_boundaries=counts["butterfly_boundary"],
        monomial_boundaries=counts["monomial_boundary"],
        sub_a_boundaries=counts["sub_a_boundary"],
    )
    for field, expected in _EXPECTED_COUNTS.items():
        if getattr(binding, field) != expected:
            raise ValueError(
                f"Task 3 schedule {field} changed: "
                f"{getattr(binding, field)} != {expected}"
            )
    return binding


def _presented_evidence_error(operator_result: Any) -> str:
    if isinstance(operator_result, (str, Path)):
        marker = str(operator_result).upper()
        if "STAGE203" in marker:
            return "Stage203 support-only rows presented as an operator"
        if "STAGE329" in marker:
            return "Stage329 random witness matrices presented as an operator"
    if isinstance(operator_result, Mapping):
        marker = " ".join(
            str(operator_result.get(key, ""))
            for key in ("source", "stage", "classification", "kind")
        ).upper()
        if "STAGE203" in marker or "SUPPORT_ONLY" in marker:
            return "Stage203 support-only rows presented as an operator"
        if "STAGE329" in marker or "RANDOM_WITNESS" in marker:
            return "Stage329 random witness matrices presented as an operator"
    if isinstance(operator_result, (tuple, list)):
        return "Stage329 random witness matrices presented as an operator"
    return "unregistered object presented as a Candidate C operator"


def _recomputed_operator_result(
    root: Path | str,
    operator_result: Any,
) -> OperatorGateResult:
    if not isinstance(operator_result, OperatorGateResult):
        raise ValueError(_presented_evidence_error(operator_result))
    if (
        type(operator_result.r) is not int
        or operator_result.r not in _EXPECTED_R_VALUES
    ):
        raise ValueError("unregistered Candidate C rank")
    if type(operator_result.modulus) is not int:
        raise ValueError("unregistered Candidate C modulus")

    recomputed = run_c1_operator_gate(
        root,
        operator_result.r,
        operator_result.modulus,
    )
    if operator_result.schedule_hash != recomputed.schedule_hash:
        raise ValueError("C1 state/schedule edge mutation")
    if operator_result.decision != recomputed.decision:
        raise ValueError("fabricated C1 admission or changed C1 decision")
    if operator_result.tensors != recomputed.tensors:
        raise ValueError("C1 tensor coefficient mutation")
    if not verify_operator_gate_result(operator_result):
        raise ValueError("Task 3A operator gate result failed recomputation")
    if operator_result != recomputed:
        raise ValueError("Task 3A operator gate result changed")
    return recomputed


def _trace_payload(trace: RegisteredScheduleTrace) -> dict[str, Any]:
    payload = asdict(trace)
    payload.pop("trace_hash")
    return payload


def _replay_admitted_c1(
    root: Path | str,
    result: OperatorGateResult,
) -> RegisteredScheduleTrace:
    schedule = load_binary_target_schedule(root)
    if _sha256(asdict(schedule)) != result.schedule_hash:
        raise ValueError("C1 state/schedule edge mutation")

    event_hasher = hashlib.sha256()
    edge_hasher = hashlib.sha256()
    previous_event: dict[str, Any] | None = None
    counts: Counter[str] = Counter()
    states: dict[tuple[int, int], str] = {}
    seen_at_bit: set[int] = set()
    active_boundary: tuple[int, int] | None = None
    phase_checks = 0
    rank_checks = 0

    for event in iter_binary_schedule_events(schedule):
        event_dict = asdict(event)
        event_hasher.update(_event_bytes(event))
        event_hasher.update(b"\n")
        edge_hasher.update(
            _canonical_bytes(
                {
                    "previous": previous_event,
                    "current": event_dict,
                }
            )
        )
        edge_hasher.update(b"\n")
        previous_event = event_dict
        counts[event.kind] += 1

        if event.kind in {"ncmux", "cmux"}:
            if event.bit is None or event.index is None:
                raise ValueError("selector event lost its state identity")
            boundary = (event.monomial, event.bit)
            if active_boundary is None:
                active_boundary = boundary
            if boundary != active_boundary:
                raise ValueError("selector crossed an unregistered boundary")
            if event.index in seen_at_bit:
                raise ValueError("selector repeated an accumulator state")
            seen_at_bit.add(event.index)
            state_key = (event.monomial, event.index)
            prior_state = states.get(
                state_key,
                _sha256(
                    {
                        "kind": "CANDIDATE_C_ACCUMULATOR_INPUT",
                        "monomial": event.monomial,
                        "index": event.index,
                    }
                ),
            )
            states[state_key] = _sha256(
                {
                    "prior_state": prior_state,
                    "event": event_dict,
                    "operator_result_hash": result.result_hash,
                }
            )
            phase_checks += 1
            rank_checks += 1
            if not result.phase_identity_passed:
                raise ValueError("registered operator failed per-state phase")
            if not result.joint_rank_passed:
                raise ValueError("registered operator failed per-state rank")
        elif event.kind == "butterfly_boundary":
            if (
                active_boundary != (event.monomial, event.bit)
                or seen_at_bit != set(range(schedule.in_N))
            ):
                raise ValueError("C1 state/schedule edge mutation")
            active_boundary = None
            seen_at_bit.clear()

    binding = _ScheduleBinding(
        schedule_hash=result.schedule_hash,
        schedule_event_digest=event_hasher.hexdigest(),
        state_edge_digest=edge_hasher.hexdigest(),
        h=schedule.h,
        monomial_calls=schedule.monomial_calls,
        r_prec=schedule.r_prec,
        in_N=schedule.in_N,
        selector_events=counts["ncmux"] + counts["cmux"],
        ncmux_events=counts["ncmux"],
        cmux_events=counts["cmux"],
        butterfly_boundaries=counts["butterfly_boundary"],
        monomial_boundaries=counts["monomial_boundary"],
        sub_a_boundaries=counts["sub_a_boundary"],
    )
    for field, expected in _EXPECTED_COUNTS.items():
        if getattr(binding, field) != expected:
            raise ValueError(f"Task 3 schedule {field} changed")

    provisional = RegisteredScheduleTrace(
        r=result.r,
        operator_result_hash=result.result_hash,
        schedule_hash=binding.schedule_hash,
        schedule_event_digest=binding.schedule_event_digest,
        state_edge_digest=binding.state_edge_digest,
        state_identity_digest=_sha256(
            [
                {
                    "monomial": key[0],
                    "index": key[1],
                    "state_hash": value,
                }
                for key, value in sorted(states.items())
            ]
        ),
        selector_events=binding.selector_events,
        ncmux_events=binding.ncmux_events,
        cmux_events=binding.cmux_events,
        butterfly_boundaries=binding.butterfly_boundaries,
        monomial_boundaries=binding.monomial_boundaries,
        sub_a_boundaries=binding.sub_a_boundaries,
        phase_checks=phase_checks,
        rank_checks=rank_checks,
        accumulator_state_identities=len(states),
        max_rho=result.rho,
        status="REPLAYED_REGISTERED_C1_OPERATOR",
        trace_hash="",
    )
    return replace(
        provisional,
        trace_hash=_sha256(_trace_payload(provisional)),
    )


def replay_registered_operator(
    root: Path | str,
    operator_result: Any,
    conversion_result: Any | None = None,
) -> RegisteredScheduleTrace | None:
    """Replay only a freshly recomputed admitted Task 3A result.

    Task 3B is absent on the current route, so every C2 claim is unregistered.
    A verified terminal C1 result returns ``None`` before schedule iteration.
    """

    if not isinstance(operator_result, OperatorGateResult):
        raise ValueError(_presented_evidence_error(operator_result))
    if conversion_result is not None:
        raise ValueError(
            "C2 admission without a verified Task 3B result and complete "
            "conversion data"
        )
    recomputed = _recomputed_operator_result(root, operator_result)
    if recomputed.decision in {
        REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
        TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED,
    }:
        return None
    if recomputed.decision == ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2:
        raise ValueError(
            "C2 admission without a verified Task 3B result and complete "
            "conversion data"
        )
    if recomputed.decision != ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY:
        raise ValueError("unregistered Task 3A terminal decision")
    return _replay_admitted_c1(root, recomputed)


def _artifact_payload(
    artifact: RegisteredOperatorArtifact,
) -> dict[str, Any]:
    payload = asdict(artifact)
    payload.pop("artifact_hash")
    return payload


def registered_operator_for_task4(
    root: Path | str,
) -> RegisteredOperatorArtifact:
    """Return one all-r admitted artifact or prove Task 4 unreachable."""

    results = tuple(
        run_c1_operator_gate(root, r, RING_MODULUS)
        for r in _EXPECTED_R_VALUES
    )
    if not all(verify_operator_gate_result(result) for result in results):
        raise ValueError("recomputed Task 3A result failed verification")
    decisions = tuple(result.decision for result in results)
    if (
        len(set(decisions)) == 1
        and decisions[0] != ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY
    ):
        raise NoRegisteredCandidateCOperator(decisions[0])
    if any(
        decision != ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY
        for decision in decisions
    ):
        raise NoRegisteredCandidateCOperator(
            "MIXED_TASK3A_RESULTS_NO_REGISTERED_OPERATOR"
        )

    traces = tuple(
        replay_registered_operator(root, result, None)
        for result in results
    )
    if any(trace is None for trace in traces):
        raise NoRegisteredCandidateCOperator(
            "TASK3A_REPLAY_DID_NOT_PRODUCE_REGISTERED_TRACE"
        )
    admitted_traces = tuple(trace for trace in traces if trace is not None)
    provisional = RegisteredOperatorArtifact(
        operator_results=results,
        traces=admitted_traces,
        conversion_result=None,
        decision=ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
        artifact_hash="",
    )
    return replace(
        provisional,
        artifact_hash=_sha256(_artifact_payload(provisional)),
    )


def _terminal_payload(
    record: CandidateCTerminalRecord,
) -> dict[str, Any]:
    payload = asdict(record)
    payload.pop("record_hash")
    return payload


def _terminal_classification(decision: str) -> str:
    if decision == TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED:
        return "INCONCLUSIVE"
    if decision == REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL:
        return "REJECT"
    raise ValueError("Task 3A decision does not route to Task 5")


def _build_terminal_record(root: Path | str) -> CandidateCTerminalRecord:
    results = tuple(
        run_c1_operator_gate(root, r, RING_MODULUS)
        for r in _EXPECTED_R_VALUES
    )
    if not all(verify_operator_gate_result(result) for result in results):
        raise ValueError("recomputed Task 3A result failed verification")
    decisions = tuple(result.decision for result in results)
    if len(set(decisions)) != 1:
        raise ValueError("Task 3A terminal decisions differ across r")
    decision = decisions[0]
    classification = _terminal_classification(decision)
    schedule = _schedule_binding(root)
    if any(result.schedule_hash != schedule.schedule_hash for result in results):
        raise ValueError("Task 3A and Task 3 schedule hashes differ")

    provisional = CandidateCTerminalRecord(
        schema="candidate-c-task-3c-terminal-v1",
        classification=classification,
        decision=decision,
        replay_status=SKIPPED_NO_REGISTERED_OPERATOR,
        task4_status=SKIPPED_NO_REGISTERED_OPERATOR,
        r_values=_EXPECTED_R_VALUES,
        operator_results=results,
        schedule_hash=schedule.schedule_hash,
        schedule_event_digest=schedule.schedule_event_digest,
        state_edge_digest=schedule.state_edge_digest,
        conversion_boundary_digest=(
            NO_REGISTERED_CONVERSION_BOUNDARY_DIGEST
        ),
        conversion_key_identity_digest=(
            NO_REGISTERED_CONVERSION_KEY_IDENTITY_DIGEST
        ),
        h=schedule.h,
        monomial_calls=schedule.monomial_calls,
        r_prec=schedule.r_prec,
        in_N=schedule.in_N,
        selector_events=schedule.selector_events,
        ncmux_events=schedule.ncmux_events,
        cmux_events=schedule.cmux_events,
        butterfly_boundaries=schedule.butterfly_boundaries,
        monomial_boundaries=schedule.monomial_boundaries,
        sub_a_boundaries=schedule.sub_a_boundaries,
        record_hash="",
    )
    return replace(
        provisional,
        record_hash=_sha256(_terminal_payload(provisional)),
    )


def _validate_terminal_record(
    record: CandidateCTerminalRecord,
    root: Path | str,
) -> None:
    if record.schema != "candidate-c-task-3c-terminal-v1":
        raise ValueError("terminal schema changed")
    if record.classification not in {"REJECT", "INCONCLUSIVE"}:
        raise ValueError("terminal classification changed")
    expected_classification = _terminal_classification(record.decision)
    if record.classification != expected_classification:
        raise ValueError("terminal classification does not match decision")
    if (
        record.replay_status != SKIPPED_NO_REGISTERED_OPERATOR
        or record.task4_status != SKIPPED_NO_REGISTERED_OPERATOR
    ):
        raise ValueError("Task 4 skipped status changed")
    if (
        record.conversion_boundary_digest
        != NO_REGISTERED_CONVERSION_BOUNDARY_DIGEST
    ):
        raise ValueError("C2 conversion boundary mutation")
    if (
        record.conversion_key_identity_digest
        != NO_REGISTERED_CONVERSION_KEY_IDENTITY_DIGEST
    ):
        raise ValueError("C2 conversion-key identity mutation")
    if record.r_values != _EXPECTED_R_VALUES:
        raise ValueError("registered Task 3A ranks changed")

    schedule = _schedule_binding(root)
    if record.state_edge_digest != schedule.state_edge_digest:
        raise ValueError("C1 state/schedule edge mutation")
    schedule_fields = (
        "schedule_hash",
        "schedule_event_digest",
        "h",
        "monomial_calls",
        "r_prec",
        "in_N",
        "selector_events",
        "ncmux_events",
        "cmux_events",
        "butterfly_boundaries",
        "monomial_boundaries",
        "sub_a_boundaries",
    )
    if any(
        getattr(record, field) != getattr(schedule, field)
        for field in schedule_fields
    ):
        raise ValueError("Task 3 schedule binding changed")

    recomputed_results = tuple(
        run_c1_operator_gate(root, r, RING_MODULUS)
        for r in _EXPECTED_R_VALUES
    )
    if len(record.operator_results) != len(recomputed_results):
        raise ValueError("Task 3A operator gate result count changed")
    if any(
        not verify_operator_gate_result(result)
        for result in record.operator_results
    ):
        raise ValueError("Task 3A operator gate result failed verification")
    if record.operator_results != recomputed_results:
        raise ValueError("Task 3A operator gate result changed")
    if any(
        result.schedule_hash != record.schedule_hash
        for result in record.operator_results
    ):
        raise ValueError("Task 3A schedule hash changed")
    decisions = {result.decision for result in record.operator_results}
    if decisions != {record.decision}:
        raise ValueError("terminal decision changed")
    if record.record_hash != _sha256(_terminal_payload(record)):
        raise ValueError("terminal record hash changed")


def terminal_record_for_task5(
    root: Path | str,
) -> CandidateCTerminalRecord:
    """Return the canonical scoped terminal record for Candidate C Task 5."""

    return _build_terminal_record(root)
