#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
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
    REGISTERED_SHORT_ERROR_RELATION_FAIL,
    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
    REJECT_C1_PHASE_IDENTITY_TERMINAL,
    REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL,
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
    "amdahl_pessimistic_projection",
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
    "decision_evidence.json",
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
DECISION_EVIDENCE_SCHEMA = "candidate-c-task5-decision-evidence-v1"
ACTUAL_EVIDENCE = "ACTUAL_TASK3C"
FIXTURE_EVIDENCE = "VERIFIED_FIXTURE"
_FIXTURE_HASH_DOMAIN = "candidate-c/task5/verified-fixture/v1"
REJECT_C1_NEGATIVE_PESSIMISTIC_AMDAHL_PROJECTION_TERMINAL = (
    "REJECT_C1_NEGATIVE_PESSIMISTIC_AMDAHL_PROJECTION_TERMINAL"
)
ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY = (
    "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY"
)
ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY = (
    "ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY"
)
REJECT_C2_CONVERSION_CLOSURE = "REJECT_C2_CONVERSION_CLOSURE"
REJECT_C2_NONPOSITIVE_STRUCTURAL_COST = (
    "REJECT_C2_NONPOSITIVE_STRUCTURAL_COST"
)
_APPROVED_C1_RESULT_HASHES = (
    "41d9629ceab043f9b18b97cafa7edb7c2f84d7d85feac0816c8951a887cadbf8",
    "2dfa7574c3c0a2708c69ec4c918c30ca01a239f119c458c7c4d9d5d5bd817a78",
    "553247432086c35f913b21e1706e620f5978b555c44e8c315a8943750c8ba36d",
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
    amdahl_pessimistic_projection: float | None
    fully_evaluated: bool
    failure_reason: str
    object_hashes: tuple[str, ...]


@dataclass(frozen=True)
class RawDecisionEvidence:
    schema: str
    binding_kind: str
    claimed_decision: str
    terminal_classification: str
    terminal_decision: str
    terminal_record_hash: str
    terminal_evidence_exhausted: bool
    replay_status: str
    task3b_status: str
    task4_status: str
    mechanisms: tuple[MechanismEvaluation, ...]


@dataclass(frozen=True)
class VerifiedDecisionEvidence:
    raw: RawDecisionEvidence
    decision: str
    verification_hash: str


@dataclass(frozen=True)
class GateResult:
    decision_evidence: RawDecisionEvidence
    terminal_record: CandidateCTerminalRecord | None
    decision: str
    terminal_classification: str
    terminal_decision: str
    terminal_record_hash: str
    task4_status: str
    complete_cost_status: str
    complete_cost: float | None
    amdahl_status: str
    amdahl_projection: float | None
    amdahl_pessimistic_projection: float | None
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


def _fixture_hash_payload(raw: RawDecisionEvidence) -> dict[str, object]:
    payload = asdict(raw)
    payload.pop("terminal_record_hash")
    return {
        "domain": _FIXTURE_HASH_DOMAIN,
        "evidence": payload,
    }


def bind_fixture_decision_evidence(
    raw: RawDecisionEvidence,
) -> RawDecisionEvidence:
    if (
        type(raw) is not RawDecisionEvidence
        or raw.schema != DECISION_EVIDENCE_SCHEMA
        or raw.binding_kind != FIXTURE_EVIDENCE
    ):
        raise GateEvidenceError(
            "only typed fixture decision evidence can be fixture-bound"
        )
    return replace(
        raw,
        terminal_record_hash=_sha256_json(_fixture_hash_payload(raw)),
    )


def decision_evidence_json(raw: RawDecisionEvidence) -> str:
    _validate_raw_decision_types(raw)
    return (
        json.dumps(
            asdict(raw),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    )


def _mapping_keys(
    value: object,
    expected: set[str],
    label: str,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise GateEvidenceError(f"{label} has a noncanonical schema")
    return value


def raw_decision_evidence_from_json(
    content: str,
) -> RawDecisionEvidence:
    try:
        decoded = json.loads(content)
    except (json.JSONDecodeError, TypeError) as error:
        raise GateEvidenceError(
            "decision evidence is not canonical JSON"
        ) from error
    raw_fields = set(RawDecisionEvidence.__dataclass_fields__)
    record = _mapping_keys(decoded, raw_fields, "decision evidence")
    mechanisms_value = record["mechanisms"]
    if not isinstance(mechanisms_value, list):
        raise GateEvidenceError("decision mechanisms must be a JSON list")
    mechanism_fields = set(MechanismEvaluation.__dataclass_fields__)
    mechanisms = []
    for index, value in enumerate(mechanisms_value):
        mechanism = dict(
            _mapping_keys(
                value,
                mechanism_fields,
                f"decision mechanism {index}",
            )
        )
        hashes = mechanism["object_hashes"]
        if not isinstance(hashes, list):
            raise GateEvidenceError(
                "decision mechanism object hashes must be a JSON list"
            )
        mechanism["object_hashes"] = tuple(hashes)
        try:
            mechanisms.append(MechanismEvaluation(**mechanism))
        except TypeError as error:
            raise GateEvidenceError(
                f"decision mechanism {index} has invalid fields"
            ) from error
    values = dict(record)
    values["mechanisms"] = tuple(mechanisms)
    try:
        raw = RawDecisionEvidence(**values)
    except TypeError as error:
        raise GateEvidenceError(
            "decision evidence has invalid fields"
        ) from error
    _validate_raw_decision_types(raw)
    return raw


def load_decision_evidence(path: Path) -> RawDecisionEvidence:
    try:
        content = Path(path).read_text(encoding="ascii")
    except (OSError, UnicodeError) as error:
        raise GateEvidenceError("cannot read decision evidence") from error
    return raw_decision_evidence_from_json(content)


def _is_finite_number(value: object) -> bool:
    return (
        type(value) in {int, float}
        and math.isfinite(float(value))
    )


def _validate_digest(value: object, label: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise GateEvidenceError(f"{label} is not a SHA-256 digest")


def _validate_mechanism_types(mechanism: MechanismEvaluation) -> None:
    if type(mechanism) is not MechanismEvaluation:
        raise GateEvidenceError("decision mechanism type changed")
    string_fields = (
        "mechanism_id",
        "source_status",
        "equation_status",
        "symbolic_independence_status",
        "phase_status",
        "schedule_status",
        "rank_status",
        "compression_status",
        "structural_cost_status",
        "complete_cost_status",
        "amdahl_status",
        "failure_reason",
    )
    if any(type(getattr(mechanism, field)) is not str for field in string_fields):
        raise GateEvidenceError("decision mechanism string field changed")
    boolean_fields = (
        "registered",
        "closed_next_state_consumption",
        "fully_evaluated",
    )
    if any(type(getattr(mechanism, field)) is not bool for field in boolean_fields):
        raise GateEvidenceError("decision mechanism boolean field changed")
    integer_fields = (
        "max_rho",
        "compression_interval",
        "b_min",
    )
    if any(type(getattr(mechanism, field)) is not int for field in integer_fields):
        raise GateEvidenceError("decision mechanism integer field changed")
    for field in (
        "complete_cost",
        "amdahl_projection",
        "amdahl_pessimistic_projection",
    ):
        value = getattr(mechanism, field)
        if value is not None and not _is_finite_number(value):
            raise GateEvidenceError(
                f"decision mechanism {field} is not finite"
            )
    if (
        type(mechanism.object_hashes) is not tuple
        or any(type(value) is not str for value in mechanism.object_hashes)
    ):
        raise GateEvidenceError("decision mechanism object hashes changed")
    for digest in mechanism.object_hashes:
        _validate_digest(digest, "decision mechanism object hash")


def _validate_raw_decision_types(raw: RawDecisionEvidence) -> None:
    if type(raw) is not RawDecisionEvidence:
        raise GateEvidenceError("raw decision evidence type changed")
    if raw.schema != DECISION_EVIDENCE_SCHEMA:
        raise GateEvidenceError("decision evidence schema changed")
    string_fields = (
        "binding_kind",
        "claimed_decision",
        "terminal_classification",
        "terminal_decision",
        "terminal_record_hash",
        "replay_status",
        "task3b_status",
        "task4_status",
    )
    if any(type(getattr(raw, field)) is not str for field in string_fields):
        raise GateEvidenceError("decision evidence string field changed")
    if type(raw.terminal_evidence_exhausted) is not bool:
        raise GateEvidenceError(
            "decision terminal exhaustion field changed"
        )
    if (
        type(raw.mechanisms) is not tuple
        or not raw.mechanisms
    ):
        raise GateEvidenceError("decision evidence mechanisms changed")
    for mechanism in raw.mechanisms:
        _validate_mechanism_types(mechanism)
    _validate_digest(raw.terminal_record_hash, "terminal record hash")


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
    structural_passed = all(
        result.structural_improvement for result in results
    )
    source_passed = all(result.source_bindings for result in results)
    schedule_passed = all(
        result.schedule_hash == terminal.schedule_hash for result in results
    )
    replay_skipped = terminal.replay_status == SKIPPED
    structural_status = "PASS" if structural_passed else terminal.decision
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
        compression_status=structural_status,
        compression_interval=1 if structural_passed else 0,
        b_min=1,
        closed_next_state_consumption=not replay_skipped,
        structural_cost_status=structural_status,
        complete_cost_status=terminal.task4_status,
        complete_cost=None,
        amdahl_status=terminal.task4_status,
        amdahl_projection=None,
        amdahl_pessimistic_projection=None,
        fully_evaluated=terminal.classification == "REJECT",
        failure_reason=(
            terminal.decision
            if terminal.classification == "REJECT"
            else ""
        ),
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
        amdahl_pessimistic_projection=None,
        fully_evaluated=False,
        failure_reason=terminal.conversion_status,
        object_hashes=(),
    )
    return (c1, c2)


def _mechanism_admits(mechanism: MechanismEvaluation) -> bool:
    return (
        mechanism.mechanism_id in {"C1", "C2"}
        and mechanism.registered
        and mechanism.source_status == "PASS"
        and mechanism.equation_status == "PASS"
        and mechanism.symbolic_independence_status == "PASS"
        and mechanism.phase_status == "PASS"
        and mechanism.schedule_status == "PASS"
        and mechanism.rank_status == "PASS"
        and 0 <= mechanism.max_rho <= 2
        and mechanism.compression_status == "PASS"
        and mechanism.b_min > 0
        and mechanism.compression_interval >= mechanism.b_min
        and mechanism.closed_next_state_consumption
        and mechanism.structural_cost_status == "PASS"
        and mechanism.complete_cost_status == "PASS"
        and _is_finite_number(mechanism.complete_cost)
        and float(mechanism.complete_cost) >= 0.0
        and mechanism.amdahl_status == "PASS"
        and _is_finite_number(mechanism.amdahl_projection)
        and float(mechanism.amdahl_projection) > 1.0
        and _is_finite_number(
            mechanism.amdahl_pessimistic_projection
        )
        and float(mechanism.amdahl_pessimistic_projection) >= 0.0
        and mechanism.fully_evaluated
        and mechanism.failure_reason == ""
    )


_REGISTERED_ADMIT_RULES = {
    ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY: "C1",
    ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY: "C2",
}
REGISTERED_ADMIT_LABELS = tuple(_REGISTERED_ADMIT_RULES)


def _matches_registered_admit(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    mechanism_id = _REGISTERED_ADMIT_RULES.get(raw.terminal_decision)
    return (
        mechanism_id is not None
        and mechanism.mechanism_id == mechanism_id
        and _mechanism_admits(mechanism)
    )


def _symbolic_gate_passed(mechanism: MechanismEvaluation) -> bool:
    return mechanism.symbolic_independence_status in {
        "PASS",
        "PASS_SCOPED_NO_SECURITY_CLAIM",
    }


def _rank_gate_passed(mechanism: MechanismEvaluation) -> bool:
    return (
        mechanism.rank_status == "PASS"
        and 0 <= mechanism.max_rho <= 2
    )


def _compression_gate_passed(mechanism: MechanismEvaluation) -> bool:
    return (
        mechanism.compression_status == "PASS"
        and mechanism.b_min > 0
        and mechanism.compression_interval >= mechanism.b_min
    )


def _base_registered_failure(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    return (
        mechanism.mechanism_id in {"C1", "C2"}
        and mechanism.registered
        and mechanism.fully_evaluated
        and mechanism.failure_reason == raw.terminal_decision
        and not raw.terminal_evidence_exhausted
        and mechanism.source_status == "PASS"
        and mechanism.equation_status == "PASS"
    )


def _pre_cost_failure_context(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    return (
        _base_registered_failure(raw, mechanism)
        and raw.replay_status == SKIPPED
        and raw.task4_status == SKIPPED
        and mechanism.complete_cost_status == SKIPPED
        and mechanism.amdahl_status == SKIPPED
        and mechanism.complete_cost is None
        and mechanism.amdahl_projection is None
        and mechanism.amdahl_pessimistic_projection is None
    )


def _reject_c1_phase(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    return (
        _pre_cost_failure_context(raw, mechanism)
        and _symbolic_gate_passed(mechanism)
        and mechanism.phase_status == "FAIL"
        and mechanism.schedule_status == "PASS"
        and _rank_gate_passed(mechanism)
        and _compression_gate_passed(mechanism)
        and mechanism.closed_next_state_consumption
        and mechanism.structural_cost_status == "PASS"
    )


def _reject_c1_relation(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    return (
        _pre_cost_failure_context(raw, mechanism)
        and mechanism.symbolic_independence_status
        == REGISTERED_SHORT_ERROR_RELATION_FAIL
        and mechanism.phase_status == "PASS"
        and mechanism.schedule_status == "PASS"
        and _rank_gate_passed(mechanism)
        and _compression_gate_passed(mechanism)
        and mechanism.closed_next_state_consumption
        and mechanism.structural_cost_status == "PASS"
    )


def _reject_c1_structural_cost(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    return (
        _pre_cost_failure_context(raw, mechanism)
        and _symbolic_gate_passed(mechanism)
        and mechanism.phase_status == "PASS"
        and mechanism.schedule_status == "PASS"
        and _rank_gate_passed(mechanism)
        and mechanism.compression_status
        == REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
        and mechanism.b_min > 0
        and mechanism.compression_interval < mechanism.b_min
        and not mechanism.closed_next_state_consumption
        and mechanism.structural_cost_status
        == REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
    )


def _reject_c2_conversion_closure(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    return (
        _pre_cost_failure_context(raw, mechanism)
        and _symbolic_gate_passed(mechanism)
        and mechanism.phase_status == "PASS"
        and mechanism.schedule_status == "PASS"
        and _rank_gate_passed(mechanism)
        and mechanism.compression_status == REJECT_C2_CONVERSION_CLOSURE
        and mechanism.b_min > 0
        and mechanism.compression_interval >= mechanism.b_min
        and not mechanism.closed_next_state_consumption
        and mechanism.structural_cost_status == "PASS"
    )


def _reject_c2_structural_cost(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    return (
        _pre_cost_failure_context(raw, mechanism)
        and _symbolic_gate_passed(mechanism)
        and mechanism.phase_status == "PASS"
        and mechanism.schedule_status == "PASS"
        and _rank_gate_passed(mechanism)
        and mechanism.compression_status
        == REJECT_C2_NONPOSITIVE_STRUCTURAL_COST
        and mechanism.b_min > 0
        and mechanism.compression_interval < mechanism.b_min
        and mechanism.closed_next_state_consumption
        and mechanism.structural_cost_status
        == REJECT_C2_NONPOSITIVE_STRUCTURAL_COST
    )


def _reject_c1_negative_pessimistic_amdahl(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    return (
        _base_registered_failure(raw, mechanism)
        and raw.replay_status == "PASS"
        and raw.task4_status == "PASS"
        and _symbolic_gate_passed(mechanism)
        and mechanism.phase_status == "PASS"
        and mechanism.schedule_status == "PASS"
        and _rank_gate_passed(mechanism)
        and _compression_gate_passed(mechanism)
        and mechanism.closed_next_state_consumption
        and mechanism.structural_cost_status == "PASS"
        and mechanism.complete_cost_status == "PASS"
        and _is_finite_number(mechanism.complete_cost)
        and float(mechanism.complete_cost) >= 0.0
        and mechanism.amdahl_status == "PASS"
        and _is_finite_number(mechanism.amdahl_projection)
        and float(mechanism.amdahl_projection) > 1.0
        and _is_finite_number(mechanism.amdahl_pessimistic_projection)
        and float(mechanism.amdahl_pessimistic_projection) < 0.0
    )


_REGISTERED_REJECTION_RULES = {
    REJECT_C1_PHASE_IDENTITY_TERMINAL: (
        "C1",
        _reject_c1_phase,
    ),
    REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL: (
        "C1",
        _reject_c1_relation,
    ),
    REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL: (
        "C1",
        _reject_c1_structural_cost,
    ),
    REJECT_C1_NEGATIVE_PESSIMISTIC_AMDAHL_PROJECTION_TERMINAL: (
        "C1",
        _reject_c1_negative_pessimistic_amdahl,
    ),
    REJECT_C2_CONVERSION_CLOSURE: (
        "C2",
        _reject_c2_conversion_closure,
    ),
    REJECT_C2_NONPOSITIVE_STRUCTURAL_COST: (
        "C2",
        _reject_c2_structural_cost,
    ),
}
REGISTERED_REJECTION_LABELS = tuple(_REGISTERED_REJECTION_RULES)


def _matches_registered_rejection(
    raw: RawDecisionEvidence,
    mechanism: MechanismEvaluation,
) -> bool:
    rule = _REGISTERED_REJECTION_RULES.get(raw.terminal_decision)
    if rule is None:
        return False
    mechanism_id, predicate = rule
    return (
        mechanism.mechanism_id == mechanism_id
        and predicate(raw, mechanism)
    )


def _derive_decision(raw: RawDecisionEvidence) -> str:
    registered = tuple(
        mechanism
        for mechanism in raw.mechanisms
        if mechanism.registered
    )
    if len(registered) > 1:
        raise GateEvidenceError(
            "decision evidence must contain one unique registered mechanism"
        )
    admissible = tuple(
        mechanism
        for mechanism in raw.mechanisms
        if _mechanism_admits(mechanism)
    )
    admitted = tuple(
        mechanism
        for mechanism in raw.mechanisms
        if _matches_registered_admit(raw, mechanism)
    )
    failed = tuple(
        mechanism
        for mechanism in raw.mechanisms
        if _matches_registered_rejection(raw, mechanism)
    )
    if (
        raw.terminal_classification == "ADMIT"
        and raw.terminal_decision in _REGISTERED_ADMIT_RULES
        and not raw.terminal_evidence_exhausted
        and raw.replay_status == "PASS"
        and raw.task4_status == "PASS"
        and len(registered) == 1
        and admissible == registered
        and admitted == registered
        and not failed
    ):
        return ADMIT
    if (
        raw.terminal_classification == "REJECT"
        and raw.terminal_decision in _REGISTERED_REJECTION_RULES
        and not raw.terminal_evidence_exhausted
        and len(registered) == 1
        and failed == registered
        and not admissible
    ):
        return REJECT
    no_numerics = all(
        mechanism.complete_cost is None
        and mechanism.amdahl_projection is None
        and mechanism.amdahl_pessimistic_projection is None
        for mechanism in raw.mechanisms
    )
    task4_skipped = all(
        mechanism.complete_cost_status == SKIPPED
        and mechanism.amdahl_status == SKIPPED
        for mechanism in raw.mechanisms
    )
    if (
        raw.terminal_classification == "INCONCLUSIVE"
        and raw.terminal_decision
        == TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED
        and raw.terminal_evidence_exhausted
        and raw.replay_status == SKIPPED
        and raw.task4_status == SKIPPED
        and raw.task3b_status
        in {NO_VERIFIED_TASK3B_RESULT, "EVIDENCE_EXHAUSTED"}
        and no_numerics
        and task4_skipped
        and not registered
        and not admissible
        and not failed
    ):
        return INCONCLUSIVE
    raise GateEvidenceError(
        "typed decision evidence does not derive ADMIT, REJECT, or "
        "INCONCLUSIVE"
    )


def _approved_actual_mechanisms(
    terminal: CandidateCTerminalRecord,
) -> tuple[MechanismEvaluation, ...]:
    if (
        terminal.record_hash != APPROVED_TASK3C_HASH
        or terminal.classification != "REJECT"
        or terminal.decision
        != REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
        or terminal.replay_status != SKIPPED
        or terminal.task4_status != SKIPPED
        or terminal.conversion_status != NO_VERIFIED_TASK3B_RESULT
    ):
        raise GateEvidenceError("approved actual Task 3C terminal changed")
    mechanisms = _actual_mechanisms(terminal)
    expected = (
        MechanismEvaluation(
            mechanism_id="C1",
            registered=True,
            source_status="PASS",
            equation_status="PASS",
            symbolic_independence_status="PASS_SCOPED_NO_SECURITY_CLAIM",
            phase_status="PASS",
            schedule_status="PASS",
            rank_status="PASS",
            max_rho=2,
            compression_status=(
                REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
            ),
            compression_interval=0,
            b_min=1,
            closed_next_state_consumption=False,
            structural_cost_status=(
                REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
            ),
            complete_cost_status=SKIPPED,
            complete_cost=None,
            amdahl_status=SKIPPED,
            amdahl_projection=None,
            amdahl_pessimistic_projection=None,
            fully_evaluated=True,
            failure_reason=(
                REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
            ),
            object_hashes=_APPROVED_C1_RESULT_HASHES,
        ),
        MechanismEvaluation(
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
            amdahl_pessimistic_projection=None,
            fully_evaluated=False,
            failure_reason=NO_VERIFIED_TASK3B_RESULT,
            object_hashes=(),
        ),
    )
    operator_facts = tuple(
        (
            result.r,
            result.rho,
            result.phase_identity_passed,
            result.joint_rank_passed,
            result.structural_improvement,
            result.decision,
            result.schedule_hash == terminal.schedule_hash,
        )
        for result in terminal.operator_results
    )
    if (
        terminal.r_values != (2, 4, 6)
        or operator_facts
        != (
            (
                2,
                1,
                True,
                True,
                False,
                REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
                True,
            ),
            (
                4,
                2,
                True,
                True,
                False,
                REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
                True,
            ),
            (
                6,
                2,
                True,
                True,
                False,
                REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL,
                True,
            ),
        )
        or mechanisms != expected
    ):
        raise GateEvidenceError("approved actual mechanism facts changed")
    return mechanisms


def _raw_decision_evidence_from_terminal(
    terminal: CandidateCTerminalRecord,
) -> RawDecisionEvidence:
    mechanisms = _approved_actual_mechanisms(terminal)
    provisional = RawDecisionEvidence(
        schema=DECISION_EVIDENCE_SCHEMA,
        binding_kind=ACTUAL_EVIDENCE,
        claimed_decision="",
        terminal_classification=terminal.classification,
        terminal_decision=terminal.decision,
        terminal_record_hash=terminal.record_hash,
        terminal_evidence_exhausted=(
            terminal.classification == "INCONCLUSIVE"
        ),
        replay_status=terminal.replay_status,
        task3b_status=terminal.conversion_status,
        task4_status=terminal.task4_status,
        mechanisms=mechanisms,
    )
    return replace(
        provisional,
        claimed_decision=_derive_decision(provisional),
    )


def verify_decision_evidence(
    raw: RawDecisionEvidence,
    *,
    root: Path | None = None,
    terminal: CandidateCTerminalRecord | None = None,
    allow_fixture: bool = False,
) -> VerifiedDecisionEvidence:
    _validate_raw_decision_types(raw)
    if raw.binding_kind == ACTUAL_EVIDENCE:
        if root is None:
            raise GateEvidenceError(
                "actual decision evidence requires a source root"
            )
        actual_terminal = (
            terminal
            if terminal is not None
            else terminal_record_for_task5(root)
        )
        try:
            actual_terminal.validate(root)
        except (OSError, TypeError, ValueError) as error:
            raise GateEvidenceError(
                "actual Task 3C decision evidence failed verification"
            ) from error
        expected = _raw_decision_evidence_from_terminal(actual_terminal)
        if raw != expected:
            raise GateEvidenceError(
                "actual decision evidence changed from fresh Task 3A/Task 3C"
            )
        verification_hash = actual_terminal.record_hash
    elif raw.binding_kind == FIXTURE_EVIDENCE:
        if not allow_fixture:
            raise GateEvidenceError(
                "fixture decision evidence is disabled"
            )
        expected_hash = _sha256_json(_fixture_hash_payload(raw))
        if raw.terminal_record_hash != expected_hash:
            raise GateEvidenceError(
                "fixture decision evidence hash changed"
            )
        verification_hash = expected_hash
    else:
        raise GateEvidenceError("decision evidence binding kind changed")
    decision = _derive_decision(raw)
    if raw.claimed_decision != decision:
        raise GateEvidenceError(
            "claimed decision does not match typed evidence derivation"
        )
    return VerifiedDecisionEvidence(
        raw=raw,
        decision=decision,
        verification_hash=verification_hash,
    )


def _decision_mechanism(
    raw: RawDecisionEvidence,
    decision: str,
) -> MechanismEvaluation:
    if decision == ADMIT:
        selected = tuple(
            mechanism
            for mechanism in raw.mechanisms
            if _matches_registered_admit(raw, mechanism)
        )
    elif decision == REJECT:
        selected = tuple(
            mechanism
            for mechanism in raw.mechanisms
            if _matches_registered_rejection(raw, mechanism)
        )
    elif decision == INCONCLUSIVE:
        selected = tuple(
            mechanism
            for mechanism in raw.mechanisms
            if mechanism.registered
        )
        if selected:
            raise GateEvidenceError(
                "inconclusive evidence cannot contain a registered mechanism"
            )
        return raw.mechanisms[0]
    else:
        raise GateEvidenceError("unknown verified Candidate C decision")
    if len(selected) != 1 or not selected[0].registered:
        raise GateEvidenceError(
            "verified decision must select one unique registered mechanism"
        )
    return selected[0]


def _primary_mechanism(result: GateResult) -> MechanismEvaluation:
    return _decision_mechanism(
        result.decision_evidence,
        result.decision,
    )


def _gate_result_from_verified(
    verified: VerifiedDecisionEvidence,
    *,
    terminal: CandidateCTerminalRecord | None,
) -> GateResult:
    raw = verified.raw
    primary = _decision_mechanism(raw, verified.decision)
    result = GateResult(
        decision_evidence=raw,
        terminal_record=terminal,
        decision=verified.decision,
        terminal_classification=raw.terminal_classification,
        terminal_decision=raw.terminal_decision,
        terminal_record_hash=raw.terminal_record_hash,
        task4_status=raw.task4_status,
        complete_cost_status=primary.complete_cost_status,
        complete_cost=primary.complete_cost,
        amdahl_status=primary.amdahl_status,
        amdahl_projection=primary.amdahl_projection,
        amdahl_pessimistic_projection=(
            primary.amdahl_pessimistic_projection
        ),
        production_hot_path_permission=False,
        mechanisms=raw.mechanisms,
        source_rows=() if terminal is None else _source_rows(terminal),
        schedule_rows=() if terminal is None else _schedule_rows(terminal),
        operator_rows=() if terminal is None else _operator_rows(terminal),
        relation_rows=() if terminal is None else _relation_rows(terminal),
        conversion_rows=() if terminal is None else (
            {
                "mechanism_id": "C2",
                "conversion_status": terminal.conversion_status,
                "registered_material": "no",
                "task4_status": terminal.task4_status,
            },
        ),
        hash_rows=() if terminal is None else (
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
        terminal_rows=() if terminal is None else (
            {
                "classification": terminal.classification,
                "decision": terminal.decision,
                "replay_status": terminal.replay_status,
                "task4_status": terminal.task4_status,
                "conversion_status": terminal.conversion_status,
                "r_values": ";".join(
                    str(value) for value in terminal.r_values
                ),
                "schedule_hash": terminal.schedule_hash,
                "record_hash": terminal.record_hash,
            },
        ),
        rank_rows=() if terminal is None else _rank_rows(terminal),
    )
    return result


def gate_result_from_decision_evidence(
    raw: RawDecisionEvidence,
    *,
    allow_fixture: bool = False,
) -> GateResult:
    verified = verify_decision_evidence(
        raw,
        allow_fixture=allow_fixture,
    )
    return _gate_result_from_verified(verified, terminal=None)


def _evaluate_verified_terminal(root: Path) -> GateResult:
    try:
        terminal = terminal_record_for_task5(root)
        terminal.validate(root)
    except (OSError, TypeError, ValueError) as error:
        raise GateEvidenceError(
            "Candidate C requires a hash-bound terminal Task 3C record"
        ) from error
    raw = _raw_decision_evidence_from_terminal(terminal)
    verified = verify_decision_evidence(
        raw,
        root=root,
        terminal=terminal,
    )
    result = _gate_result_from_verified(verified, terminal=terminal)
    if result.production_hot_path_permission:
        raise GateEvidenceError(
            "Candidate C evidence cannot enable production code"
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
    allow_fixture: bool = False,
) -> VerifiedDecisionEvidence:
    if result.decision_evidence.binding_kind == ACTUAL_EVIDENCE:
        expected = evaluate_candidate_c(root, input_commit=input_commit)
        _validate_raw_decision_types(result.decision_evidence)
        derived = _derive_decision(result.decision_evidence)
        if result.decision_evidence.claimed_decision != derived:
            raise GateEvidenceError(
                "claimed decision does not match typed evidence derivation"
            )
        verified = VerifiedDecisionEvidence(
            raw=result.decision_evidence,
            decision=derived,
            verification_hash=result.terminal_record_hash,
        )
    else:
        verified = verify_decision_evidence(
            result.decision_evidence,
            allow_fixture=allow_fixture,
        )
        expected = _gate_result_from_verified(verified, terminal=None)
    if result != expected:
        raise ValueError(
            "gate result does not match freshly verified or rederived typed "
            "decision evidence"
        )
    return verified


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
        "amdahl_pessimistic_projection": (
            "" if result.amdahl_pessimistic_projection is None
            else f"{result.amdahl_pessimistic_projection:.9f}"
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
    allow_fixture: bool = False,
) -> dict[str, str]:
    validate_gate_result(
        result,
        root=root,
        input_commit=input_commit,
        allow_fixture=allow_fixture,
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
            "amdahl_pessimistic_projection": (
                ""
                if mechanism.amdahl_pessimistic_projection is None
                else f"{mechanism.amdahl_pessimistic_projection:.9f}"
            ),
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
        (
            "mechanism_id",
            "status",
            "central_projection",
            "pessimistic_projection",
        ),
        (
            {
                "mechanism_id": mechanism.mechanism_id,
                "status": mechanism.amdahl_status,
                "central_projection": (
                    "" if mechanism.amdahl_projection is None
                    else f"{mechanism.amdahl_projection:.9f}"
                ),
                "pessimistic_projection": (
                    ""
                    if mechanism.amdahl_pessimistic_projection is None
                    else f"{mechanism.amdahl_pessimistic_projection:.9f}"
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
    _write_text(
        out / "decision_evidence.json",
        decision_evidence_json(result.decision_evidence),
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
