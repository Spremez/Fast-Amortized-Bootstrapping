"""Fail-closed Candidate C replay registration and terminal routing.

Task 3A currently rejects every registered rank.  Task 3B has no verified
result, and Task 3C has no per-event tensor executor.  Consequently this
module emits only the deterministic Task 5 terminal record.  Trace, artifact,
and conversion-envelope types define strict validation boundaries but can
never authorize Task 4.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from pathlib import Path
from typing import Any

from .candidate_c_operator_tensor import (
    ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
    REJECT_C1_PHASE_IDENTITY_TERMINAL,
    REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL,
    RING_MODULUS,
    ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2,
    TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED,
    OperatorGateResult,
    run_c1_operator_gate,
    verify_operator_gate_result,
)
from .candidate_c_schedule import (
    BinaryTargetSchedule,
    ScheduleEvent,
    iter_binary_schedule_events,
    load_binary_target_schedule,
)


CANONICAL_VERSION = "candidate-c-typed-canonical-v2"
TRACE_SCHEMA = "candidate-c-task-3c-trace-v2"
TRACE_DOMAIN = "candidate-c/registered-schedule-trace"
ARTIFACT_SCHEMA = "candidate-c-task-3c-artifact-v2"
ARTIFACT_DOMAIN = "candidate-c/registered-operator-artifact"
CONVERSION_SCHEMA = "candidate-c-task-3c-rejected-conversion-v1"
CONVERSION_DOMAIN = "candidate-c/rejected-conversion-envelope"
TERMINAL_SCHEMA = "candidate-c-task-3c-terminal-v2"
TERMINAL_DOMAIN = "candidate-c/terminal-record"

SKIPPED_NO_REGISTERED_OPERATOR = "SKIPPED_NO_REGISTERED_OPERATOR"
NO_VERIFIED_TASK3B_RESULT = "NO_VERIFIED_TASK3B_RESULT"
NO_VERIFIED_ARTIFACT_NO_PER_EVENT_TENSOR_EXECUTOR = (
    "NO_VERIFIED_ARTIFACT_NO_PER_EVENT_TENSOR_EXECUTOR"
)
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
_C1_REJECTION_DECISIONS = frozenset(
    {
        REJECT_C1_PHASE_IDENTITY_TERMINAL,
        REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
        REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL,
    }
)
_C1_NONADMITTED_DECISIONS = _C1_REJECTION_DECISIONS | {
    TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED,
}

_EVENT_DOMAIN = "candidate-c/task3-schedule-event"
_STATE_EDGE_DOMAIN = "candidate-c/task3-state-edge"
_TRACE_HASH_DOMAIN = "candidate-c/registered-schedule-trace/hash"
_TRACE_BYTES_DOMAIN = "candidate-c/registered-schedule-trace/bytes"
_ARTIFACT_HASH_DOMAIN = "candidate-c/registered-operator-artifact/hash"
_ARTIFACT_BYTES_DOMAIN = "candidate-c/registered-operator-artifact/bytes"
_CONVERSION_BOUNDARY_DOMAIN = "candidate-c/conversion-boundaries"
_CONVERSION_KEY_DOMAIN = "candidate-c/conversion-key-identities"
_CONVERSION_HASH_DOMAIN = "candidate-c/rejected-conversion-envelope/hash"
_CONVERSION_BYTES_DOMAIN = "candidate-c/rejected-conversion-envelope/bytes"
_TERMINAL_HASH_DOMAIN = "candidate-c/terminal-record/hash"
_TERMINAL_BYTES_DOMAIN = "candidate-c/terminal-record/bytes"


def _typed_value(value: Any) -> dict[str, Any]:
    """Encode supported values without erasing their Python type."""

    if value is None:
        return {"type": "none"}
    if type(value) is bool:
        return {"type": "bool", "value": value}
    if type(value) is int:
        return {"type": "int", "value": str(value)}
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("canonical floats must be finite")
        return {"type": "float", "value": value.hex()}
    if type(value) is str:
        return {"type": "str", "value": value}
    if type(value) is tuple:
        return {
            "type": "tuple",
            "items": [_typed_value(item) for item in value],
        }
    if type(value) is list:
        return {
            "type": "list",
            "items": [_typed_value(item) for item in value],
        }
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("canonical dictionary keys must be str")
        return {
            "type": "dict",
            "items": [
                {
                    "key": key,
                    "value": _typed_value(value[key]),
                }
                for key in sorted(value)
            ],
        }
    if is_dataclass(value) and not isinstance(value, type):
        value_type = type(value)
        return {
            "type": "dataclass",
            "class": (
                f"{value_type.__module__}.{value_type.__qualname__}"
            ),
            "fields": [
                {
                    "name": field.name,
                    "value": _typed_value(getattr(value, field.name)),
                }
                for field in fields(value)
            ],
        }
    raise TypeError(
        f"unsupported canonical type: {type(value).__qualname__}"
    )


def _canonical_bytes(domain: str, value: Any) -> bytes:
    if type(domain) is not str or not domain:
        raise TypeError("canonical domain must be nonempty str")
    envelope = {
        "canonical_version": CANONICAL_VERSION,
        "domain": domain,
        "payload": _typed_value(value),
    }
    return json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(domain: str, value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(domain, value)).hexdigest()


def _legacy_json_bytes(value: Any) -> bytes:
    """Match Task 3A's existing source-bound schedule hash exactly."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _task3a_schedule_hash(schedule: BinaryTargetSchedule) -> str:
    payload = {
        field.name: getattr(schedule, field.name)
        for field in fields(schedule)
    }
    return hashlib.sha256(_legacy_json_bytes(payload)).hexdigest()


def _require_str(value: Any, name: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{name} must be str")


def _require_int(value: Any, name: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be int")


def _require_tuple(value: Any, name: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{name} must be tuple")


def _require_digest(value: Any, name: str) -> None:
    _require_str(value, name)
    if len(value) != 64 or any(
        character not in "0123456789abcdef"
        for character in value
    ):
        raise ValueError(f"{name} must be lowercase SHA-256")


class AdmittedReplayNotImplemented(RuntimeError):
    """No admitted trace can exist before a real per-event tensor executor."""


class NoRegisteredCandidateCOperator(RuntimeError):
    """Raised when Task 4 requests an operator from a terminal Task 3 route."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class UnsupportedC2Material(ValueError):
    """Task 3B supplied no verified conversion result."""


class ConversionBoundaryMutation(ValueError):
    """An unverified C2 claim changed its typed boundary sequence."""


class ConversionKeyIdentityMutation(ValueError):
    """An unverified C2 claim changed its typed conversion-key sequence."""


class StateEdgeMutation(ValueError):
    """The source-derived Task 3 state/event edge binding changed."""


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
class RejectedConversionEnvelope:
    """Typed self-integrity envelope for C2 material that remains unsupported."""

    schema: str
    canonical_version: str
    canonical_domain: str
    claimed_decision: str
    boundaries: tuple[str, ...]
    conversion_key_identities: tuple[str, ...]
    boundary_digest: str
    key_identity_digest: str
    envelope_hash: str

    @classmethod
    def from_unverified_claim(
        cls,
        *,
        claimed_decision: str,
        boundaries: tuple[str, ...],
        conversion_key_identities: tuple[str, ...],
    ) -> RejectedConversionEnvelope:
        _require_str(claimed_decision, "claimed_decision")
        _validate_string_tuple(boundaries, "boundaries")
        _validate_string_tuple(
            conversion_key_identities,
            "conversion_key_identities",
        )
        provisional = cls(
            schema=CONVERSION_SCHEMA,
            canonical_version=CANONICAL_VERSION,
            canonical_domain=CONVERSION_DOMAIN,
            claimed_decision=claimed_decision,
            boundaries=boundaries,
            conversion_key_identities=conversion_key_identities,
            boundary_digest=_sha256(
                _CONVERSION_BOUNDARY_DOMAIN,
                boundaries,
            ),
            key_identity_digest=_sha256(
                _CONVERSION_KEY_DOMAIN,
                conversion_key_identities,
            ),
            envelope_hash="",
        )
        return replace(
            provisional,
            envelope_hash=provisional.recomputed_hash(),
        )

    def recomputed_hash(self) -> str:
        _validate_conversion_types(self, require_hash=False)
        return _sha256(
            _CONVERSION_HASH_DOMAIN,
            _conversion_payload(self),
        )

    def canonical_bytes(self) -> bytes:
        _validate_conversion_types(self, require_hash=True)
        return _canonical_bytes(_CONVERSION_BYTES_DOMAIN, self)


@dataclass(frozen=True)
class RegisteredScheduleTrace:
    """Untrusted trace claim whose validator always fails closed."""

    schema: str
    canonical_version: str
    canonical_domain: str
    r: int
    operator_result_hash: str
    schedule_hash: str
    schedule_event_digest: str
    state_edge_digest: str
    state_identity_digest: str
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
    phase_checks: int
    rank_checks: int
    accumulator_state_identities: int
    max_rho: int
    status: str
    trace_hash: str

    def recomputed_hash(self) -> str:
        _validate_trace_types(self, require_hash=False)
        return _sha256(_TRACE_HASH_DOMAIN, _trace_payload(self))

    def canonical_bytes(self) -> bytes:
        _validate_trace_types(self, require_hash=True)
        return _canonical_bytes(_TRACE_BYTES_DOMAIN, self)

    def validate(self, root: Path | str) -> None:
        _validate_trace(self, root)

    def verify(self, root: Path | str) -> bool:
        try:
            self.validate(root)
        except (
            AdmittedReplayNotImplemented,
            TypeError,
            ValueError,
        ):
            return False
        return False


@dataclass(frozen=True)
class RegisteredOperatorArtifact:
    """Untrusted artifact claim; this implementation never emits one."""

    schema: str
    canonical_version: str
    canonical_domain: str
    operator_results: tuple[OperatorGateResult, ...]
    traces: tuple[RegisteredScheduleTrace, ...]
    conversion_result: None
    decision: str
    artifact_hash: str

    def recomputed_hash(self) -> str:
        _validate_artifact_types(self, require_hash=False)
        return _sha256(
            _ARTIFACT_HASH_DOMAIN,
            _artifact_payload(self),
        )

    def canonical_bytes(self) -> bytes:
        _validate_artifact_types(self, require_hash=True)
        return _canonical_bytes(_ARTIFACT_BYTES_DOMAIN, self)

    def validate(self, root: Path | str) -> None:
        _validate_artifact_types(self, require_hash=True)
        if self.artifact_hash != self.recomputed_hash():
            raise ValueError("registered artifact hash changed")
        raise AdmittedReplayNotImplemented(
            "registered artifacts require a genuine per-event tensor executor"
        )

    def verify(self, root: Path | str) -> bool:
        try:
            self.validate(root)
        except (
            AdmittedReplayNotImplemented,
            TypeError,
            ValueError,
        ):
            return False
        return False


@dataclass(frozen=True)
class CandidateCTerminalRecord:
    schema: str
    canonical_version: str
    canonical_domain: str
    classification: str
    decision: str
    replay_status: str
    task4_status: str
    conversion_status: str
    r_values: tuple[int, ...]
    operator_results: tuple[OperatorGateResult, ...]
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
    record_hash: str

    def recomputed_hash(self) -> str:
        _validate_terminal_types(self, require_hash=False)
        return _sha256(
            _TERMINAL_HASH_DOMAIN,
            _terminal_payload(self),
        )

    def canonical_bytes(self) -> bytes:
        _validate_terminal_types(self, require_hash=True)
        return _canonical_bytes(_TERMINAL_BYTES_DOMAIN, self)

    def validate(self, root: Path | str) -> None:
        _validate_terminal_record(self, root)

    def verify(self, root: Path | str) -> bool:
        try:
            self.validate(root)
        except (TypeError, ValueError):
            return False
        return True


def _validate_string_tuple(value: Any, name: str) -> None:
    _require_tuple(value, name)
    if any(type(item) is not str for item in value):
        raise TypeError(f"{name} entries must be str")


def _validate_conversion_types(
    envelope: RejectedConversionEnvelope,
    *,
    require_hash: bool,
) -> None:
    if type(envelope) is not RejectedConversionEnvelope:
        raise TypeError("conversion envelope type changed")
    for name in (
        "schema",
        "canonical_version",
        "canonical_domain",
        "claimed_decision",
        "boundary_digest",
        "key_identity_digest",
        "envelope_hash",
    ):
        _require_str(getattr(envelope, name), name)
    _validate_string_tuple(envelope.boundaries, "boundaries")
    _validate_string_tuple(
        envelope.conversion_key_identities,
        "conversion_key_identities",
    )
    _require_digest(envelope.boundary_digest, "boundary_digest")
    _require_digest(envelope.key_identity_digest, "key_identity_digest")
    if require_hash:
        _require_digest(envelope.envelope_hash, "envelope_hash")


def _conversion_payload(
    envelope: RejectedConversionEnvelope,
) -> dict[str, Any]:
    return {
        "schema": envelope.schema,
        "canonical_version": envelope.canonical_version,
        "canonical_domain": envelope.canonical_domain,
        "claimed_decision": envelope.claimed_decision,
        "boundaries": envelope.boundaries,
        "conversion_key_identities": (
            envelope.conversion_key_identities
        ),
        "boundary_digest": envelope.boundary_digest,
        "key_identity_digest": envelope.key_identity_digest,
    }


def _reject_conversion_input(conversion_result: Any) -> None:
    if type(conversion_result) is not RejectedConversionEnvelope:
        raise UnsupportedC2Material(
            "C2 input requires the typed rejection-only conversion envelope"
        )
    envelope = conversion_result
    try:
        _require_digest(envelope.boundary_digest, "boundary_digest")
    except (TypeError, ValueError) as exc:
        raise ConversionBoundaryMutation(
            "C2 conversion boundary mutation"
        ) from exc
    try:
        _require_digest(envelope.key_identity_digest, "key_identity_digest")
    except (TypeError, ValueError) as exc:
        raise ConversionKeyIdentityMutation(
            "C2 conversion-key identity mutation"
        ) from exc
    _validate_conversion_types(envelope, require_hash=True)
    if (
        envelope.schema != CONVERSION_SCHEMA
        or envelope.canonical_version != CANONICAL_VERSION
        or envelope.canonical_domain != CONVERSION_DOMAIN
    ):
        raise UnsupportedC2Material(
            "unsupported C2 rejection-envelope contract"
        )
    if envelope.boundary_digest != _sha256(
        _CONVERSION_BOUNDARY_DOMAIN,
        envelope.boundaries,
    ):
        raise ConversionBoundaryMutation(
            "C2 conversion boundary mutation"
        )
    if envelope.key_identity_digest != _sha256(
        _CONVERSION_KEY_DOMAIN,
        envelope.conversion_key_identities,
    ):
        raise ConversionKeyIdentityMutation(
            "C2 conversion-key identity mutation"
        )
    if envelope.envelope_hash != envelope.recomputed_hash():
        raise UnsupportedC2Material("C2 rejection envelope hash changed")
    raise UnsupportedC2Material(
        "C2 material is unsupported: no verified Task 3B result"
    )


def _event_bytes(event: ScheduleEvent) -> bytes:
    if type(event) is not ScheduleEvent:
        raise TypeError("schedule event type changed")
    return _canonical_bytes(_EVENT_DOMAIN, event)


def _schedule_binding(root: Path | str) -> _ScheduleBinding:
    schedule = load_binary_target_schedule(root)
    if type(schedule) is not BinaryTargetSchedule:
        raise TypeError("binary schedule type changed")
    event_hasher = hashlib.sha256()
    edge_hasher = hashlib.sha256()
    counts: Counter[str] = Counter()
    previous: ScheduleEvent | None = None

    for event in iter_binary_schedule_events(schedule):
        event_hasher.update(_event_bytes(event))
        event_hasher.update(b"\n")
        edge_hasher.update(
            _canonical_bytes(
                _STATE_EDGE_DOMAIN,
                {
                    "previous": previous,
                    "current": event,
                },
            )
        )
        edge_hasher.update(b"\n")
        counts[event.kind] += 1
        previous = event

    binding = _ScheduleBinding(
        schedule_hash=_task3a_schedule_hash(schedule),
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
    if type(operator_result) is not OperatorGateResult:
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
    if type(recomputed) is not OperatorGateResult:
        raise TypeError("recomputed Task 3A result type changed")
    if operator_result.schedule_hash != recomputed.schedule_hash:
        raise StateEdgeMutation("C1 state/schedule edge mutation")
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
    return {
        field.name: getattr(trace, field.name)
        for field in fields(trace)
        if field.name != "trace_hash"
    }


def _validate_trace_types(
    trace: RegisteredScheduleTrace,
    *,
    require_hash: bool,
) -> None:
    if type(trace) is not RegisteredScheduleTrace:
        raise TypeError("registered trace type changed")
    for name in (
        "schema",
        "canonical_version",
        "canonical_domain",
        "operator_result_hash",
        "schedule_hash",
        "schedule_event_digest",
        "state_edge_digest",
        "state_identity_digest",
        "status",
        "trace_hash",
    ):
        _require_str(getattr(trace, name), name)
    for name in (
        "r",
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
        "phase_checks",
        "rank_checks",
        "accumulator_state_identities",
        "max_rho",
    ):
        _require_int(getattr(trace, name), name)
    for name in (
        "operator_result_hash",
        "schedule_hash",
        "schedule_event_digest",
        "state_edge_digest",
        "state_identity_digest",
    ):
        _require_digest(getattr(trace, name), name)
    if require_hash:
        _require_digest(trace.trace_hash, "trace_hash")


def _validate_trace(
    trace: RegisteredScheduleTrace,
    root: Path | str,
) -> None:
    _validate_trace_types(trace, require_hash=True)
    if (
        trace.schema != TRACE_SCHEMA
        or trace.canonical_version != CANONICAL_VERSION
        or trace.canonical_domain != TRACE_DOMAIN
    ):
        raise ValueError("registered trace canonical contract changed")
    if trace.status != "UNVERIFIED_REPLAY_CLAIM":
        raise ValueError("registered trace status is not fail-closed")
    if trace.trace_hash != trace.recomputed_hash():
        raise ValueError("registered trace hash changed")

    schedule = _schedule_binding(root)
    if trace.state_edge_digest != schedule.state_edge_digest:
        raise StateEdgeMutation("C1 state/schedule edge mutation")
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
        getattr(trace, field) != getattr(schedule, field)
        for field in schedule_fields
    ):
        raise ValueError("registered trace schedule binding changed")
    if (
        trace.phase_checks != trace.selector_events
        or trace.rank_checks != trace.selector_events
        or trace.accumulator_state_identities
        != trace.monomial_calls * trace.in_N
    ):
        raise ValueError("registered trace replay counts changed")

    result = run_c1_operator_gate(root, trace.r, RING_MODULUS)
    if not verify_operator_gate_result(result):
        raise ValueError("fresh Task 3A result failed verification")
    if trace.operator_result_hash != result.result_hash:
        raise ValueError("registered trace operator binding changed")
    if trace.max_rho != result.rho:
        raise ValueError("registered trace rank binding changed")
    raise AdmittedReplayNotImplemented(
        "registered traces require a genuine per-event tensor executor"
    )


def _artifact_payload(
    artifact: RegisteredOperatorArtifact,
) -> dict[str, Any]:
    return {
        field.name: getattr(artifact, field.name)
        for field in fields(artifact)
        if field.name != "artifact_hash"
    }


def _validate_artifact_types(
    artifact: RegisteredOperatorArtifact,
    *,
    require_hash: bool,
) -> None:
    if type(artifact) is not RegisteredOperatorArtifact:
        raise TypeError("registered artifact type changed")
    for name in (
        "schema",
        "canonical_version",
        "canonical_domain",
        "decision",
        "artifact_hash",
    ):
        _require_str(getattr(artifact, name), name)
    _require_tuple(artifact.operator_results, "operator_results")
    _require_tuple(artifact.traces, "traces")
    if any(
        type(result) is not OperatorGateResult
        for result in artifact.operator_results
    ):
        raise TypeError("operator_results entries must be OperatorGateResult")
    if any(
        type(trace) is not RegisteredScheduleTrace
        for trace in artifact.traces
    ):
        raise TypeError("traces entries must be RegisteredScheduleTrace")
    if artifact.conversion_result is not None:
        raise TypeError("registered artifact conversion_result must be None")
    if require_hash:
        _require_digest(artifact.artifact_hash, "artifact_hash")


def replay_registered_operator(
    root: Path | str,
    operator_result: Any,
    conversion_result: Any | None = None,
) -> RegisteredScheduleTrace | None:
    """Return no trace unless a future real executor replaces this boundary."""

    if type(operator_result) is not OperatorGateResult:
        raise ValueError(_presented_evidence_error(operator_result))
    if conversion_result is not None:
        _reject_conversion_input(conversion_result)
    recomputed = _recomputed_operator_result(root, operator_result)
    if recomputed.decision in _C1_NONADMITTED_DECISIONS:
        return None
    if recomputed.decision in {
        ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY,
        ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2,
    }:
        raise AdmittedReplayNotImplemented(
            "admitted Candidate C replay requires a genuine per-event "
            "tensor executor"
        )
    raise ValueError("unregistered Task 3A terminal decision")


def registered_operator_for_task4(
    root: Path | str,
) -> RegisteredOperatorArtifact:
    """Always block Task 4; no Task 3C executor can emit an artifact."""

    results = tuple(
        run_c1_operator_gate(root, r, RING_MODULUS)
        for r in _EXPECTED_R_VALUES
    )
    if any(type(result) is not OperatorGateResult for result in results):
        raise TypeError("recomputed Task 3A result type changed")
    if not all(verify_operator_gate_result(result) for result in results):
        raise ValueError("recomputed Task 3A result failed verification")
    decisions = tuple(result.decision for result in results)
    if len(set(decisions)) == 1 and decisions[0] in _C1_NONADMITTED_DECISIONS:
        raise NoRegisteredCandidateCOperator(decisions[0])
    raise NoRegisteredCandidateCOperator(
        NO_VERIFIED_ARTIFACT_NO_PER_EVENT_TENSOR_EXECUTOR
    )


def _terminal_payload(
    record: CandidateCTerminalRecord,
) -> dict[str, Any]:
    return {
        field.name: getattr(record, field.name)
        for field in fields(record)
        if field.name != "record_hash"
    }


def _validate_terminal_types(
    record: CandidateCTerminalRecord,
    *,
    require_hash: bool,
) -> None:
    if type(record) is not CandidateCTerminalRecord:
        raise TypeError("terminal record type changed")
    for name in (
        "schema",
        "canonical_version",
        "canonical_domain",
        "classification",
        "decision",
        "replay_status",
        "task4_status",
        "conversion_status",
        "schedule_hash",
        "schedule_event_digest",
        "state_edge_digest",
        "record_hash",
    ):
        _require_str(getattr(record, name), name)
    _require_tuple(record.r_values, "r_values")
    if any(type(value) is not int for value in record.r_values):
        raise TypeError("r_values entries must be int")
    _require_tuple(record.operator_results, "operator_results")
    if any(
        type(result) is not OperatorGateResult
        for result in record.operator_results
    ):
        raise TypeError("operator_results entries must be OperatorGateResult")
    for name in (
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
    ):
        _require_int(getattr(record, name), name)
    for name in (
        "schedule_hash",
        "schedule_event_digest",
        "state_edge_digest",
    ):
        _require_digest(getattr(record, name), name)
    if require_hash:
        _require_digest(record.record_hash, "record_hash")


def _terminal_classification(decision: str) -> str:
    if decision == TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED:
        return "INCONCLUSIVE"
    if decision in _C1_REJECTION_DECISIONS:
        return "REJECT"
    raise ValueError("Task 3A decision does not route to Task 5")


def _build_terminal_record(root: Path | str) -> CandidateCTerminalRecord:
    results = tuple(
        run_c1_operator_gate(root, r, RING_MODULUS)
        for r in _EXPECTED_R_VALUES
    )
    if any(type(result) is not OperatorGateResult for result in results):
        raise TypeError("recomputed Task 3A result type changed")
    if not all(verify_operator_gate_result(result) for result in results):
        raise ValueError("recomputed Task 3A result failed verification")
    decisions = tuple(result.decision for result in results)
    if len(set(decisions)) != 1:
        raise ValueError("Task 3A terminal decisions differ across r")
    decision = decisions[0]
    classification = _terminal_classification(decision)
    schedule = _schedule_binding(root)
    if any(result.schedule_hash != schedule.schedule_hash for result in results):
        raise StateEdgeMutation(
            "Task 3A and Task 3 state/schedule edge binding changed"
        )

    provisional = CandidateCTerminalRecord(
        schema=TERMINAL_SCHEMA,
        canonical_version=CANONICAL_VERSION,
        canonical_domain=TERMINAL_DOMAIN,
        classification=classification,
        decision=decision,
        replay_status=SKIPPED_NO_REGISTERED_OPERATOR,
        task4_status=SKIPPED_NO_REGISTERED_OPERATOR,
        conversion_status=NO_VERIFIED_TASK3B_RESULT,
        r_values=_EXPECTED_R_VALUES,
        operator_results=results,
        schedule_hash=schedule.schedule_hash,
        schedule_event_digest=schedule.schedule_event_digest,
        state_edge_digest=schedule.state_edge_digest,
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
        record_hash=provisional.recomputed_hash(),
    )


def _validate_terminal_record(
    record: CandidateCTerminalRecord,
    root: Path | str,
) -> None:
    _validate_terminal_types(record, require_hash=True)
    if (
        record.schema != TERMINAL_SCHEMA
        or record.canonical_version != CANONICAL_VERSION
        or record.canonical_domain != TERMINAL_DOMAIN
    ):
        raise ValueError("terminal canonical contract changed")
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
    if record.conversion_status != NO_VERIFIED_TASK3B_RESULT:
        raise ValueError("terminal conversion status changed")
    if record.r_values != _EXPECTED_R_VALUES:
        raise ValueError("registered Task 3A ranks changed")

    schedule = _schedule_binding(root)
    if record.state_edge_digest != schedule.state_edge_digest:
        raise StateEdgeMutation("C1 state/schedule edge mutation")
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
        raise StateEdgeMutation("Task 3A schedule edge binding changed")
    decisions = {result.decision for result in record.operator_results}
    if decisions != {record.decision}:
        raise ValueError("terminal decision changed")
    if record.record_hash != record.recomputed_hash():
        raise ValueError("terminal record hash changed")


def terminal_record_for_task5(
    root: Path | str,
) -> CandidateCTerminalRecord:
    """Return the canonical scoped terminal record for Candidate C Task 5."""

    return _build_terminal_record(root)
