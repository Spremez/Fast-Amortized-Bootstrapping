"""Concrete finite-ring operator gate for Candidate C Task 3A.

The objects in this module are exact witnesses in GF(257)[X]/(X^8+1).
They do not establish security, production correctness, noise bounds,
performance, novelty, or a complete-SAB speedup.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Sequence

from .candidate_c_schedule import load_binary_target_schedule
from .finite_linear import rank, rref


RING_MODULUS = 257
RING_DEGREE = 8
DEFAULT_GADGET = (1, 16)

ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY = (
    "ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY"
)
ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2 = (
    "ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2"
)
REJECT_C1_PHASE_IDENTITY_TERMINAL = (
    "REJECT_C1_PHASE_IDENTITY_TERMINAL"
)
REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL = (
    "REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL"
)
REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL = (
    "REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL"
)
TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED = (
    "TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED"
)

RELATION_RECORDED_NO_SECURITY_DECISION = (
    "RELATION_RECORDED_NO_SECURITY_DECISION"
)
REGISTERED_SHORT_ERROR_RELATION_FAIL = (
    "REGISTERED_SHORT_ERROR_RELATION_FAIL"
)
NO_RETAINED_MESSAGE_RELATION = "NO_RETAINED_MESSAGE_RELATION"


Polynomial = tuple[int, ...]
Matrix = tuple[tuple[int, ...], ...]
MaskTensor = tuple[
    tuple[tuple[Polynomial, ...], ...],
    ...,
]
BodyTensor = tuple[
    tuple[tuple[Polynomial, ...], ...],
    ...,
]


class SourceBindingError(ValueError):
    """Raised when a required source or artifact boundary is not present."""


@dataclass(frozen=True)
class PhaseProjection:
    public_lambda: Matrix
    secrets: tuple[Polynomial, ...]
    mu: int
    modulus: int
    n: int
    input_components: tuple[str, ...]
    entries: tuple[tuple[Polynomial, ...], ...]


@dataclass(frozen=True)
class OperatorTensor:
    construction: str
    r: int
    rho: int
    d: int
    mu: int
    secrets: tuple[Polynomial, ...]
    gadget: tuple[int, ...]
    n: int
    modulus: int
    public_lambda: Matrix
    input_components: tuple[str, ...]
    mask_polynomials: MaskTensor
    body_polynomials: BodyTensor
    relation_error_distribution: str | None = None
    registered_sigma: float | None = None
    registered_error_bound: float | None = None
    decision_inequality: str | None = None


@dataclass(frozen=True)
class EvaluatorSampleRelation:
    coefficients: tuple[int, ...]
    centered_coefficients: tuple[int, ...]
    l1_norm: int
    l2_norm: float
    retained_messages: tuple[Polynomial, ...]
    retained_centered_message_gap: int
    symbolic_error_multiplier: float
    combined_error_bound: float | None
    decision_inequality: str | None
    decisive: bool


@dataclass(frozen=True)
class EvaluatorSampleRelationAudit:
    mu: int
    sample_rows: int
    mask_columns: int
    left_kernel_dimension: int
    containment_holds: bool
    retained_relation_count: int
    relations: tuple[EvaluatorSampleRelation, ...]
    status: str
    security_decision: bool
    registered_sigma: float | None
    registered_error_bound: float | None
    decision_inequality: str | None
    diagnostic_hash: str


@dataclass(frozen=True)
class EvaluatorCounts:
    selector_objects: int
    mask_roots: int
    body_polynomials: int
    gadget_rows: int
    decomposition_inputs: int
    add_multiplies: int
    transforms: int
    public_mixing_coefficients: int
    bytes: int
    reconstructs_quadratic_body_work: bool


@dataclass(frozen=True)
class SourceBinding:
    name: str
    path: str
    sha256: str
    classification: str
    required_tokens: tuple[str, ...]


@dataclass(frozen=True)
class OperatorGateResult:
    r: int
    rho: int
    modulus: int
    n: int
    gadget: tuple[int, ...]
    public_lambda: Matrix
    tensors: tuple[OperatorTensor, OperatorTensor]
    projections: tuple[PhaseProjection, PhaseProjection]
    relation_audits: tuple[
        EvaluatorSampleRelationAudit,
        EvaluatorSampleRelationAudit,
    ]
    phase_identity_passed: bool
    joint_ranks: tuple[int, int]
    joint_rank_passed: bool
    evaluator_counts: EvaluatorCounts
    dense_counts: EvaluatorCounts
    structural_improvement: bool
    source_bindings: tuple[SourceBinding, ...]
    schedule_hash: str
    seed_hash: str
    decision: str
    result_hash: str


@dataclass(frozen=True)
class _GateEvaluation:
    phase_identity_passed: bool
    joint_ranks: tuple[int, int]
    joint_rank_passed: bool
    relation_audits: tuple[
        EvaluatorSampleRelationAudit,
        EvaluatorSampleRelationAudit,
    ]
    evaluator_counts: EvaluatorCounts
    dense_counts: EvaluatorCounts
    structural_improvement: bool
    decision: str


def _validate_exact_ring(n: int, modulus: int) -> None:
    if type(n) is not int or n != RING_DEGREE:
        raise ValueError("n must equal 8 for the Task 3A exact surrogate")
    if type(modulus) is not int or modulus != RING_MODULUS:
        raise ValueError(
            "modulus must equal 257 for the Task 3A exact surrogate"
        )


def _validate_mu(mu: int) -> None:
    if type(mu) is not int or mu not in (0, 1):
        raise ValueError("mu must be zero or one")


def _normalize_polynomial(
    polynomial: Sequence[int],
    n: int,
    modulus: int,
    *,
    label: str,
) -> Polynomial:
    if len(polynomial) != n:
        raise ValueError(f"{label} must be a length-{n} polynomial")
    if any(type(value) is not int for value in polynomial):
        raise ValueError(f"{label} coefficients must be integers")
    return tuple(value % modulus for value in polynomial)


def _zero(n: int) -> Polynomial:
    return (0,) * n


def _constant(value: int, n: int, modulus: int) -> Polynomial:
    return (value % modulus,) + (0,) * (n - 1)


def _monomial(
    exponent: int,
    coefficient: int,
    n: int,
    modulus: int,
) -> Polynomial:
    wraps, position = divmod(exponent, n)
    value = coefficient if wraps % 2 == 0 else -coefficient
    result = [0] * n
    result[position] = value % modulus
    return tuple(result)


def _poly_add(
    left: Sequence[int],
    right: Sequence[int],
    modulus: int,
) -> Polynomial:
    if len(left) != len(right):
        raise ValueError("polynomial dimensions differ")
    return tuple(
        (left[index] + right[index]) % modulus
        for index in range(len(left))
    )


def _poly_scale(
    scalar: int,
    polynomial: Sequence[int],
    modulus: int,
) -> Polynomial:
    return tuple((scalar * value) % modulus for value in polynomial)


def negacyclic_multiply(
    left: Sequence[int],
    right: Sequence[int],
    modulus: int,
) -> Polynomial:
    """Multiply exact coefficient vectors modulo X^n+1."""

    if not left or len(left) != len(right):
        raise ValueError(
            "negacyclic operands must have the same positive length"
        )
    n = len(left)
    result = [0] * n
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            output = left_index + right_index
            product = left_value * right_value
            if output >= n:
                output -= n
                product = -product
            result[output] = (result[output] + product) % modulus
    return tuple(result)


def _convolution_matrix(
    polynomial: Polynomial,
    modulus: int,
) -> Matrix:
    n = len(polynomial)
    columns = [
        negacyclic_multiply(
            polynomial,
            _monomial(column, 1, n, modulus),
            modulus,
        )
        for column in range(n)
    ]
    return tuple(
        tuple(columns[column][row] for column in range(n))
        for row in range(n)
    )


def _validate_lambda(
    public_lambda: Sequence[Sequence[int]],
    r: int,
    d: int,
    modulus: int,
    *,
    expected_rank: int | None,
) -> Matrix:
    if len(public_lambda) != r or any(
        len(row) != d for row in public_lambda
    ):
        raise ValueError("public Lambda must have shape r x (rho+1)")
    if any(type(value) is not int for row in public_lambda for value in row):
        raise ValueError("public Lambda entries must be integers")
    normalized = tuple(
        tuple(value % modulus for value in row)
        for row in public_lambda
    )
    if any(row[0] != 1 for row in normalized):
        raise ValueError("Lambda[q,0] must equal one")
    if any(normalized[0][column] for column in range(1, d)):
        raise ValueError("Lambda[0,u] must equal zero for u>0")
    differences = tuple(
        tuple(
            (normalized[lane][column] - normalized[0][column])
            % modulus
            for column in range(d)
        )
        for lane in range(1, r)
    )
    actual_rank = rank(differences, modulus)
    if expected_rank is not None and actual_rank != expected_rank:
        raise ValueError(
            "rank((I-1 e_0^T) Lambda) must equal rho"
        )
    return normalized


def _validate_secrets(
    secrets: Sequence[Sequence[int]],
    r: int,
    n: int,
    modulus: int,
) -> tuple[Polynomial, ...]:
    if len(secrets) != r:
        raise ValueError("one secret polynomial is required per lane")
    return tuple(
        _normalize_polynomial(
            secret,
            n,
            modulus,
            label=f"secret s_{lane}",
        )
        for lane, secret in enumerate(secrets)
    )


def _validate_gadget(
    gadget: Sequence[int],
    modulus: int,
) -> tuple[int, ...]:
    if not gadget or any(type(value) is not int for value in gadget):
        raise ValueError("gadget must contain integer levels")
    return tuple(value % modulus for value in gadget)


def _input_components(d: int, r: int) -> tuple[str, ...]:
    return tuple(
        [f"M_{basis}" for basis in range(d)]
        + [f"B_{lane}" for lane in range(r)]
    )


def _validate_polynomial_array(
    value: object,
    dimensions: tuple[int, ...],
    n: int,
    modulus: int,
    *,
    label: str,
) -> None:
    if dimensions:
        if type(value) is not tuple or len(value) != dimensions[0]:
            raise ValueError(f"{label} shape is not canonical")
        for item in value:
            _validate_polynomial_array(
                item,
                dimensions[1:],
                n,
                modulus,
                label=label,
            )
        return
    if (
        type(value) is not tuple
        or len(value) != n
        or any(
            type(coefficient) is not int
            or not 0 <= coefficient < modulus
            for coefficient in value
        )
    ):
        raise ValueError(f"{label} shape is not canonical")


def _validate_tensor_shape(tensor: OperatorTensor) -> None:
    _validate_exact_ring(tensor.n, tensor.modulus)
    _validate_mu(tensor.mu)
    if (
        type(tensor.r) is not int
        or tensor.r not in (2, 4, 6)
        or type(tensor.rho) is not int
        or not 0 <= tensor.rho < tensor.r
        or type(tensor.d) is not int
        or tensor.d <= 0
        or tensor.input_components
        != _input_components(tensor.d, tensor.r)
    ):
        raise ValueError("operator tensor shape is not canonical")
    if (
        _validate_lambda(
            tensor.public_lambda,
            tensor.r,
            tensor.d,
            tensor.modulus,
            expected_rank=None,
        )
        != tensor.public_lambda
        or _validate_secrets(
            tensor.secrets,
            tensor.r,
            tensor.n,
            tensor.modulus,
        )
        != tensor.secrets
        or _validate_gadget(tensor.gadget, tensor.modulus)
        != tensor.gadget
    ):
        raise ValueError("operator tensor shape is not canonical")
    inputs = tensor.d + tensor.r
    levels = len(tensor.gadget)
    _validate_polynomial_array(
        tensor.mask_polynomials,
        (levels, tensor.d, inputs),
        tensor.n,
        tensor.modulus,
        label="mask tensor",
    )
    _validate_polynomial_array(
        tensor.body_polynomials,
        (levels, tensor.r, inputs),
        tensor.n,
        tensor.modulus,
        label="body tensor",
    )


def build_phase_projection(
    public_lambda: Sequence[Sequence[int]],
    secrets: Sequence[Sequence[int]],
    mu: int,
    modulus: int,
) -> PhaseProjection:
    """Build P_Lambda with mask inputs before body inputs."""

    _validate_mu(mu)
    if not public_lambda or not public_lambda[0]:
        raise ValueError("public Lambda must be nonempty")
    r = len(public_lambda)
    d = len(public_lambda[0])
    n = len(secrets[0]) if secrets else 0
    _validate_exact_ring(n, modulus)
    normalized_secrets = _validate_secrets(
        secrets,
        r,
        n,
        modulus,
    )
    normalized_lambda = _validate_lambda(
        public_lambda,
        r,
        d,
        modulus,
        expected_rank=None,
    )
    entries: list[tuple[Polynomial, ...]] = []
    for lane in range(r):
        lane_entries = [
            _poly_scale(
                -normalized_lambda[lane][basis],
                normalized_secrets[lane],
                modulus,
            )
            for basis in range(d)
        ]
        lane_entries.extend(
            _constant(1 if lane == body else 0, n, modulus)
            for body in range(r)
        )
        entries.append(tuple(lane_entries))
    return PhaseProjection(
        public_lambda=normalized_lambda,
        secrets=normalized_secrets,
        mu=mu,
        modulus=modulus,
        n=n,
        input_components=_input_components(d, r),
        entries=tuple(entries),
    )


def _construct_mask_roots(
    d: int,
    r: int,
    gadget: tuple[int, ...],
    n: int,
    modulus: int,
) -> MaskTensor:
    inputs = d + r
    levels: list[tuple[tuple[Polynomial, ...], ...]] = []
    for level in range(len(gadget)):
        basis_rows: list[tuple[Polynomial, ...]] = []
        for basis in range(d):
            components: list[Polynomial] = []
            for component in range(inputs):
                if component < d:
                    active = component == basis
                    exponent = level
                    coefficient = 1
                else:
                    body = component - d
                    active = basis == (body % d)
                    exponent = level + body // d
                    coefficient = body + 2
                components.append(
                    _monomial(
                        exponent,
                        coefficient,
                        n,
                        modulus,
                    )
                    if active
                    else _zero(n)
                )
            basis_rows.append(tuple(components))
        levels.append(tuple(basis_rows))
    return tuple(levels)


def _lane_mask_polynomial(
    mask_polynomials: MaskTensor,
    public_lambda: Matrix,
    level: int,
    lane: int,
    component: int,
    modulus: int,
) -> Polynomial:
    n = len(mask_polynomials[level][0][component])
    result = _zero(n)
    for basis, coefficient in enumerate(public_lambda[lane]):
        result = _poly_add(
            result,
            _poly_scale(
                coefficient,
                mask_polynomials[level][basis][component],
                modulus,
            ),
            modulus,
        )
    return result


def _construct_bodies(
    mask_polynomials: MaskTensor,
    projection: PhaseProjection,
    gadget: tuple[int, ...],
) -> BodyTensor:
    r = len(projection.secrets)
    inputs = len(projection.input_components)
    levels: list[tuple[tuple[Polynomial, ...], ...]] = []
    for level, gadget_value in enumerate(gadget):
        lane_rows: list[tuple[Polynomial, ...]] = []
        for lane in range(r):
            components: list[Polynomial] = []
            for component in range(inputs):
                lane_mask = _lane_mask_polynomial(
                    mask_polynomials,
                    projection.public_lambda,
                    level,
                    lane,
                    component,
                    projection.modulus,
                )
                secret_term = negacyclic_multiply(
                    projection.secrets[lane],
                    lane_mask,
                    projection.modulus,
                )
                message_term = _poly_scale(
                    projection.mu * gadget_value,
                    projection.entries[lane][component],
                    projection.modulus,
                )
                components.append(
                    _poly_add(
                        secret_term,
                        message_term,
                        projection.modulus,
                    )
                )
            lane_rows.append(tuple(components))
        levels.append(tuple(lane_rows))
    return tuple(levels)


def _build_tensor(
    *,
    construction: str,
    r: int,
    rho: int,
    mu: int,
    secrets: Sequence[Sequence[int]],
    gadget: Sequence[int],
    n: int,
    modulus: int,
    public_lambda: Sequence[Sequence[int]],
    mask_polynomials: MaskTensor | None = None,
    enforce_lambda_rank: bool = True,
) -> OperatorTensor:
    _validate_exact_ring(n, modulus)
    _validate_mu(mu)
    if type(r) is not int or r not in (2, 4, 6):
        raise ValueError("r must be one of 2, 4, 6")
    if type(rho) is not int or not 0 <= rho <= r - 1:
        raise ValueError("rho must lie between zero and r-1")
    d = len(public_lambda[0]) if public_lambda else 0
    if d <= 0:
        raise ValueError("public Lambda must have a positive width")
    if enforce_lambda_rank and d != rho + 1:
        raise ValueError("d must equal rho+1")
    normalized_lambda = _validate_lambda(
        public_lambda,
        r,
        d,
        modulus,
        expected_rank=rho if enforce_lambda_rank else None,
    )
    normalized_secrets = _validate_secrets(
        secrets,
        r,
        n,
        modulus,
    )
    normalized_gadget = _validate_gadget(gadget, modulus)
    projection = build_phase_projection(
        normalized_lambda,
        normalized_secrets,
        mu,
        modulus,
    )
    masks = (
        _construct_mask_roots(
            d,
            r,
            normalized_gadget,
            n,
            modulus,
        )
        if mask_polynomials is None
        else mask_polynomials
    )
    expected_inputs = d + r
    if len(masks) != len(normalized_gadget):
        raise ValueError("mask tensor must have one block per gadget level")
    for level in masks:
        if len(level) != d or any(
            len(basis) != expected_inputs for basis in level
        ):
            raise ValueError(
                "mask tensor shape must be ell x d x (d+r)"
            )
        for basis in level:
            for polynomial in basis:
                _normalize_polynomial(
                    polynomial,
                    n,
                    modulus,
                    label="mask entry",
                )
    normalized_masks: MaskTensor = tuple(
        tuple(
            tuple(
                tuple(value % modulus for value in polynomial)
                for polynomial in basis
            )
            for basis in level
        )
        for level in masks
    )
    bodies = _construct_bodies(
        normalized_masks,
        projection,
        normalized_gadget,
    )
    return OperatorTensor(
        construction=construction,
        r=r,
        rho=rho,
        d=d,
        mu=mu,
        secrets=normalized_secrets,
        gadget=normalized_gadget,
        n=n,
        modulus=modulus,
        public_lambda=normalized_lambda,
        input_components=projection.input_components,
        mask_polynomials=normalized_masks,
        body_polynomials=bodies,
    )


def build_dense_control_tensor(
    r: int,
    mu: int,
    secrets: Sequence[Sequence[int]],
    gadget: Sequence[int],
    n: int,
    modulus: int,
) -> OperatorTensor:
    """Build the current shared-mask exact-dense phase control."""

    return _build_tensor(
        construction="EXACT_DENSE_MAT_CONTROL",
        r=r,
        rho=0,
        mu=mu,
        secrets=secrets,
        gadget=gadget,
        n=n,
        modulus=modulus,
        public_lambda=tuple((1,) for _ in range(r)),
    )


def build_rank_bounded_tensor(
    r: int,
    rho: int,
    mu: int,
    secrets: Sequence[Sequence[int]],
    gadget: Sequence[int],
    n: int,
    modulus: int,
    public_lambda: Sequence[Sequence[int]],
) -> OperatorTensor:
    """Build one concrete common-Lambda C1 tensor object."""

    return _build_tensor(
        construction="C1_COMMON_LAMBDA_CONCRETE_TENSOR",
        r=r,
        rho=rho,
        mu=mu,
        secrets=secrets,
        gadget=gadget,
        n=n,
        modulus=modulus,
        public_lambda=public_lambda,
    )


def build_joint_rank_escape_control(
    r: int,
    rho: int,
    mu: int,
    secrets: Sequence[Sequence[int]],
    gadget: Sequence[int],
    n: int,
    modulus: int,
) -> OperatorTensor:
    """Build a control whose levels pass separately but fail jointly."""

    _validate_exact_ring(n, modulus)
    if r != 6 or rho != 2:
        raise ValueError(
            "the registered joint-span control uses r=6 and rho=2"
        )
    normalized_gadget = _validate_gadget(gadget, modulus)
    if len(normalized_gadget) < 2:
        raise ValueError("joint-span control requires at least two levels")
    d = r
    public_lambda = tuple(
        (1,) + tuple(
            1 if column == lane else 0
            for column in range(1, r)
        )
        for lane in range(r)
    )
    inputs = d + r
    levels: list[tuple[tuple[Polynomial, ...], ...]] = []
    active_by_level = ((1, 2), (3, 4))
    for level in range(len(normalized_gadget)):
        active = active_by_level[min(level, 1)]
        basis_rows = []
        for basis in range(d):
            components = []
            for component in range(inputs):
                components.append(
                    _constant(1, n, modulus)
                    if basis in active and component == basis
                    else _zero(n)
                )
            basis_rows.append(tuple(components))
        levels.append(tuple(basis_rows))
    return _build_tensor(
        construction="JOINT_SPAN_ESCAPE_NEGATIVE_CONTROL",
        r=r,
        rho=rho,
        mu=mu,
        secrets=secrets,
        gadget=normalized_gadget,
        n=n,
        modulus=modulus,
        public_lambda=public_lambda,
        mask_polynomials=tuple(levels),
        enforce_lambda_rank=False,
    )


def verify_phase_identity(
    tensor: OperatorTensor,
    projection: PhaseProjection,
) -> bool:
    """Check every (level, lane, component, coefficient) identity."""

    try:
        _validate_tensor_shape(tensor)
    except (TypeError, ValueError):
        return False
    if (
        tensor.public_lambda != projection.public_lambda
        or tensor.secrets != projection.secrets
        or tensor.mu != projection.mu
        or tensor.modulus != projection.modulus
        or tensor.n != projection.n
        or tensor.input_components != projection.input_components
    ):
        return False
    try:
        _validate_polynomial_array(
            projection.entries,
            (tensor.r, tensor.d + tensor.r),
            tensor.n,
            tensor.modulus,
            label="phase projection",
        )
        for level, gadget_value in enumerate(tensor.gadget):
            for lane in range(tensor.r):
                for component in range(tensor.d + tensor.r):
                    lane_mask = _lane_mask_polynomial(
                        tensor.mask_polynomials,
                        tensor.public_lambda,
                        level,
                        lane,
                        component,
                        tensor.modulus,
                    )
                    left = tuple(
                        (
                            tensor.body_polynomials[level][lane][component][
                                coefficient
                            ]
                            - negacyclic_multiply(
                                tensor.secrets[lane],
                                lane_mask,
                                tensor.modulus,
                            )[coefficient]
                        )
                        % tensor.modulus
                        for coefficient in range(tensor.n)
                    )
                    right = _poly_scale(
                        tensor.mu * gadget_value,
                        projection.entries[lane][component],
                        tensor.modulus,
                    )
                    if left != right:
                        return False
    except (IndexError, TypeError, ValueError):
        return False
    return True


def _horizontal_blocks(
    blocks: Sequence[Matrix],
) -> Matrix:
    if not blocks:
        return tuple()
    rows = len(blocks[0])
    if any(len(block) != rows for block in blocks):
        raise ValueError("matrix blocks have different row counts")
    return tuple(
        tuple(
            value
            for block in blocks
            for value in block[row]
        )
        for row in range(rows)
    )


def _basis_expanded_matrix(
    tensor: OperatorTensor,
    levels: Sequence[int],
) -> Matrix:
    blocks: list[Matrix] = []
    for level in levels:
        for component in range(tensor.d + tensor.r):
            convolution_blocks = tuple(
                _convolution_matrix(
                    tensor.mask_polynomials[level][basis][component],
                    tensor.modulus,
                )
                for basis in range(tensor.d)
            )
            blocks.append(
                tuple(
                    row
                    for block in convolution_blocks
                    for row in block
                )
            )
    return _horizontal_blocks(blocks)


def _mix_expanded_basis(
    basis_expanded: Matrix,
    mixing: Matrix,
    n: int,
    modulus: int,
) -> Matrix:
    if not basis_expanded or not mixing:
        return tuple()
    basis_count = len(mixing[0])
    if (
        any(len(row) != basis_count for row in mixing)
        or len(basis_expanded) != basis_count * n
    ):
        raise ValueError("expanded basis and mixing dimensions differ")
    columns = len(basis_expanded[0])
    rows: list[tuple[int, ...]] = []
    for mixing_row in mixing:
        for coefficient in range(n):
            rows.append(
                tuple(
                    sum(
                        mixing_row[basis]
                        * basis_expanded[
                            basis * n + coefficient
                        ][column]
                        for basis in range(basis_count)
                    )
                    % modulus
                    for column in range(columns)
                )
            )
    return tuple(rows)


def _lane_expanded_from_abar(
    tensor: OperatorTensor,
    levels: Sequence[int],
) -> Matrix:
    rows: list[tuple[int, ...]] = []
    for lane in range(tensor.r):
        blocks = []
        for level in levels:
            for component in range(tensor.d + tensor.r):
                blocks.append(
                    _convolution_matrix(
                        _lane_mask_polynomial(
                            tensor.mask_polynomials,
                            tensor.public_lambda,
                            level,
                            lane,
                            component,
                            tensor.modulus,
                        ),
                        tensor.modulus,
                    )
                )
        rows.extend(_horizontal_blocks(blocks))
    return tuple(rows)


def _lane_differences_from_expanded(
    lane_expanded: Matrix,
    r: int,
    n: int,
    modulus: int,
) -> Matrix:
    if not lane_expanded:
        return tuple()
    reference = lane_expanded[:n]
    return tuple(
        tuple(
            (
                lane_expanded[lane * n + coefficient][column]
                - reference[coefficient][column]
            )
            % modulus
            for column in range(len(reference[0]))
        )
        for lane in range(1, r)
        for coefficient in range(n)
    )


def _lambda_differences(
    tensor: OperatorTensor,
) -> Matrix:
    return tuple(
        tuple(
            (
                tensor.public_lambda[lane][basis]
                - tensor.public_lambda[0][basis]
            )
            % tensor.modulus
            for basis in range(tensor.d)
        )
        for lane in range(1, tensor.r)
    )


def _verified_difference_matrix(
    tensor: OperatorTensor,
    levels: Sequence[int],
) -> Matrix:
    basis_expanded = _basis_expanded_matrix(tensor, levels)
    factored = _mix_expanded_basis(
        basis_expanded,
        tensor.public_lambda,
        tensor.n,
        tensor.modulus,
    )
    direct = _lane_expanded_from_abar(tensor, levels)
    if direct != factored:
        raise ValueError("T_mu common-Lambda factorization failed")
    left = _lane_differences_from_expanded(
        direct,
        tensor.r,
        tensor.n,
        tensor.modulus,
    )
    right = _mix_expanded_basis(
        basis_expanded,
        _lambda_differences(tensor),
        tensor.n,
        tensor.modulus,
    )
    if left != right:
        raise ValueError("L-expanded common-Lambda identity failed")
    return left


def verify_joint_rank_factorization(
    tensor: OperatorTensor,
) -> bool:
    """Check T=(Lambda tensor I)R and (L tensor I)T=(L Lambda tensor I)R."""

    try:
        _validate_tensor_shape(tensor)
        _verified_difference_matrix(
            tensor,
            tuple(range(len(tensor.gadget))),
        )
    except (IndexError, TypeError, ValueError):
        return False
    return True


def concatenated_mask_difference_rank(
    tensor: OperatorTensor,
) -> int:
    """Return the joint field-expanded surrogate rank across all levels."""

    _validate_tensor_shape(tensor)
    matrix = _verified_difference_matrix(
        tensor,
        tuple(range(len(tensor.gadget))),
    )
    return rank(matrix, tensor.modulus)


def level_mask_difference_ranks(
    tensor: OperatorTensor,
) -> tuple[int, ...]:
    """Return control ranks before concatenating gadget levels."""

    _validate_tensor_shape(tensor)
    return tuple(
        rank(
            _verified_difference_matrix(tensor, (level,)),
            tensor.modulus,
        )
        for level in range(len(tensor.gadget))
    )


def build_evaluator_sample_matrix(
    tensor: OperatorTensor,
) -> tuple[Matrix, tuple[Matrix, ...]]:
    """Build S_mu by rows and one M_mu,q matrix per secret lane."""

    _validate_tensor_shape(tensor)
    sample_rows: list[tuple[int, ...]] = []
    messages: list[list[tuple[int, ...]]] = [
        [] for _ in range(tensor.r)
    ]
    for level in range(len(tensor.gadget)):
        for component in range(tensor.d + tensor.r):
            sample_rows.append(
                tuple(
                    coefficient
                    for basis in range(tensor.d)
                    for coefficient in tensor.mask_polynomials[level][basis][
                        component
                    ]
                )
            )
            for lane in range(tensor.r):
                lane_mask = _lane_mask_polynomial(
                    tensor.mask_polynomials,
                    tensor.public_lambda,
                    level,
                    lane,
                    component,
                    tensor.modulus,
                )
                secret_term = negacyclic_multiply(
                    tensor.secrets[lane],
                    lane_mask,
                    tensor.modulus,
                )
                messages[lane].append(
                    tuple(
                        (
                            tensor.body_polynomials[level][lane][component][
                                coefficient
                            ]
                            - secret_term[coefficient]
                        )
                        % tensor.modulus
                        for coefficient in range(tensor.n)
                    )
                )
    return tuple(sample_rows), tuple(
        tuple(lane_messages)
        for lane_messages in messages
    )


def _nullspace(
    matrix: Sequence[Sequence[int]],
    modulus: int,
) -> Matrix:
    if not matrix:
        return tuple()
    reduced, pivots = rref(matrix, modulus)
    width = len(matrix[0])
    free_columns = [
        column for column in range(width) if column not in pivots
    ]
    basis: list[tuple[int, ...]] = []
    for free in free_columns:
        vector = [0] * width
        vector[free] = 1
        for row, pivot in enumerate(pivots):
            vector[pivot] = (-reduced[row][free]) % modulus
        basis.append(tuple(vector))
    return tuple(basis)


def _left_kernel_basis(
    sample_matrix: Matrix,
    modulus: int,
) -> Matrix:
    if not sample_matrix:
        return tuple()
    transpose = tuple(
        tuple(
            sample_matrix[row][column]
            for row in range(len(sample_matrix))
        )
        for column in range(len(sample_matrix[0]))
    )
    return _nullspace(transpose, modulus)


def _center(value: int, modulus: int) -> int:
    normalized = value % modulus
    return (
        normalized - modulus
        if normalized > modulus // 2
        else normalized
    )


def _relation_message(
    relation: Sequence[int],
    messages: Matrix,
    modulus: int,
) -> Polynomial:
    if not messages:
        return tuple()
    return tuple(
        sum(
            relation[row] * messages[row][coefficient]
            for row in range(len(messages))
        )
        % modulus
        for coefficient in range(len(messages[0]))
    )


def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def audit_evaluator_sample_relations(
    tensor: OperatorTensor,
    projection: PhaseProjection,
) -> EvaluatorSampleRelationAudit:
    """Audit a basis spanning every exact scalar left-kernel relation."""

    if (
        tensor.mu != projection.mu
        or tensor.public_lambda != projection.public_lambda
        or tensor.secrets != projection.secrets
    ):
        raise ValueError("relation audit projection does not match tensor")
    sample_matrix, messages = build_evaluator_sample_matrix(tensor)
    kernel = _left_kernel_basis(sample_matrix, tensor.modulus)
    diagnostics: list[EvaluatorSampleRelation] = []
    retained_count = 0
    decisive = False
    for relation in kernel:
        centered = tuple(
            _center(value, tensor.modulus)
            for value in relation
        )
        retained = tuple(
            _relation_message(
                relation,
                messages[lane],
                tensor.modulus,
            )
            for lane in range(tensor.r)
        )
        gap = max(
            (
                abs(_center(value, tensor.modulus))
                for polynomial in retained
                for value in polynomial
            ),
            default=0,
        )
        if gap:
            retained_count += 1
        l1_norm = sum(abs(value) for value in centered)
        l2_norm = math.sqrt(
            sum(value * value for value in centered)
        )
        combined_error_bound: float | None = None
        if (
            tensor.relation_error_distribution is not None
            and tensor.decision_inequality
            == "retained_gap > combined_error_bound"
            and tensor.registered_error_bound is not None
        ):
            sigma_term = (
                0.0
                if tensor.registered_sigma is None
                else tensor.registered_sigma * l2_norm
            )
            combined_error_bound = (
                tensor.registered_error_bound * l1_norm
                + sigma_term
            )
        relation_decisive = (
            gap > 0
            and combined_error_bound is not None
            and gap > combined_error_bound
        )
        decisive = decisive or relation_decisive
        diagnostics.append(
            EvaluatorSampleRelation(
                coefficients=relation,
                centered_coefficients=centered,
                l1_norm=l1_norm,
                l2_norm=l2_norm,
                retained_messages=retained,
                retained_centered_message_gap=gap,
                symbolic_error_multiplier=l2_norm,
                combined_error_bound=combined_error_bound,
                decision_inequality=tensor.decision_inequality,
                decisive=relation_decisive,
            )
        )
    if decisive:
        status = REGISTERED_SHORT_ERROR_RELATION_FAIL
    elif retained_count:
        status = RELATION_RECORDED_NO_SECURITY_DECISION
    else:
        status = NO_RETAINED_MESSAGE_RELATION
    payload = {
        "mu": tensor.mu,
        "sample_matrix": sample_matrix,
        "messages": messages,
        "relations": [asdict(item) for item in diagnostics],
        "status": status,
        "error_distribution": tensor.relation_error_distribution,
        "registered_sigma": tensor.registered_sigma,
        "registered_error_bound": tensor.registered_error_bound,
        "decision_inequality": tensor.decision_inequality,
    }
    return EvaluatorSampleRelationAudit(
        mu=tensor.mu,
        sample_rows=len(sample_matrix),
        mask_columns=len(sample_matrix[0]) if sample_matrix else 0,
        left_kernel_dimension=len(kernel),
        containment_holds=retained_count == 0,
        retained_relation_count=retained_count,
        relations=tuple(diagnostics),
        status=status,
        security_decision=decisive,
        registered_sigma=tensor.registered_sigma,
        registered_error_bound=tensor.registered_error_bound,
        decision_inequality=tensor.decision_inequality,
        diagnostic_hash=_sha256_json(payload),
    )


def _counts_for_shape(
    *,
    r: int,
    d: int,
    ell: int,
    n: int,
    public_lambda: Matrix,
) -> EvaluatorCounts:
    inputs = d + r
    outputs = d + r
    selector_objects = 2
    mask_roots = selector_objects * ell * d * inputs
    body_polynomials = selector_objects * ell * r * inputs
    total_polynomials = mask_roots + body_polynomials
    return EvaluatorCounts(
        selector_objects=selector_objects,
        mask_roots=mask_roots,
        body_polynomials=body_polynomials,
        gadget_rows=selector_objects * ell * inputs,
        decomposition_inputs=inputs,
        add_multiplies=ell * inputs * outputs,
        transforms=ell * inputs + outputs,
        public_mixing_coefficients=sum(
            value != 0
            for row in public_lambda
            for value in row
        ),
        bytes=total_polynomials * n * 2,
        reconstructs_quadratic_body_work=(
            body_polynomials >= selector_objects * ell * r * r
        ),
    )


_STAGE203_FIELDS = (
    "r",
    "row",
    "col",
    "equation_class",
    "semantic_role",
    "is_public_row",
    "may_skip_after_proof",
)


def _read_bound_file(root: Path, relative_path: str) -> bytes:
    try:
        return (root / relative_path).read_bytes()
    except OSError as error:
        raise SourceBindingError(
            f"cannot read required binding {relative_path}: {error}"
        ) from error


def _bind_text(
    root: Path,
    *,
    name: str,
    relative_path: str,
    classification: str,
    required_tokens: Sequence[str],
    error_label: str,
) -> SourceBinding:
    content = _read_bound_file(root, relative_path)
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        raise SourceBindingError(
            f"{error_label} is not valid UTF-8"
        ) from error
    missing = [token for token in required_tokens if token not in text]
    if missing:
        raise SourceBindingError(
            f"{error_label} missing required token: {missing[0]}"
        )
    return SourceBinding(
        name=name,
        path=relative_path,
        sha256=hashlib.sha256(content).hexdigest(),
        classification=classification,
        required_tokens=tuple(required_tokens),
    )


def _bind_stage203_support(root: Path) -> SourceBinding:
    relative_path = (
        "repro/stage203_production_selector_equation_probe/"
        "equation_map.csv"
    )
    content = _read_bound_file(root, relative_path)
    try:
        rows = tuple(
            csv.reader(content.decode("utf-8-sig").splitlines())
        )
    except (UnicodeError, csv.Error) as error:
        raise SourceBindingError(
            "Stage203 support-only map cannot be decoded"
        ) from error
    if not rows or tuple(rows[0]) != _STAGE203_FIELDS:
        raise SourceBindingError(
            "Stage203 support-only map cannot provide numeric coefficients"
        )
    if any(len(row) != len(_STAGE203_FIELDS) for row in rows[1:]):
        raise SourceBindingError(
            "Stage203 support-only map has malformed support rows"
        )
    if not any(
        row[3] == "lane_neighbor_body_interaction"
        and row[4] == "active"
        for row in rows[1:]
    ):
        raise SourceBindingError(
            "Stage203 support-only map lost active neighbor support"
        )
    return SourceBinding(
        name="stage203_support_map",
        path=relative_path,
        sha256=hashlib.sha256(content).hexdigest(),
        classification="SUPPORT_ONLY_NO_NUMERIC_COEFFICIENTS",
        required_tokens=_STAGE203_FIELDS,
    )


_TEXT_BINDING_SPECS = (
    (
        "current_mat_keygen_and_operator",
        "src/mosfhet/src/mattrgsw.c",
        "EXACT_SOURCE",
        (
            "return l * (k + r);",
            "MAT_TRGSW_Key mat_trgsw_new_key(",
            "void mat_trgsw_monomial_sample(",
            "pvmtmlwe_sample(out->samples[i], NULL, key->trlwe_key);",
            "static void mat_trgsw_mul_pvmtmlwe_DFT_from_dec(",
            "for (size_t row = 1; row < rows; row++){",
        ),
        "MAT dense source token binding",
    ),
    (
        "candidate_a_phase_solver",
        "research/mat_sab/star_cycle_model.py",
        "EXACT_SOURCE",
        ("def phase_constraints(", "def phase_residual("),
        "Candidate A phase solver binding",
    ),
    (
        "task3_exact_schedule",
        "research/mat_sab/candidate_c_schedule.py",
        "EXACT_SOURCE",
        ("def load_binary_target_schedule(", "selector_applications"),
        "Task 3 schedule binding",
    ),
    (
        "stage222_lane_local_classification",
        "repro/stage222_isolated_compact_ep_integration/proof_gate.csv",
        "EXACT_ARTIFACT",
        (
            "DENY_COMPLETE_SELECTOR_INTEGRATION",
            "PASS_STAGE222_ISOLATED_COMPACT_EP_SUBCLASS_OK_COMPLETE_SELECTOR_DENIED",
        ),
        "Stage222 lane-local artifact binding",
    ),
    (
        "stage345_exact_dense_control",
        "repro/stage345_binary_matrix_synthesis/proof_gate.csv",
        "EXACT_ARTIFACT",
        (
            "PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY",
            "complete SAB T_bootstrap/r vs repeated scalar",
        ),
        "Stage345 exact-dense artifact binding",
    ),
)


def _source_bindings(root: Path) -> tuple[SourceBinding, ...]:
    text_bindings = tuple(
        _bind_text(
            root,
            name=name,
            relative_path=relative_path,
            classification=classification,
            required_tokens=required_tokens,
            error_label=error_label,
        )
        for (
            name,
            relative_path,
            classification,
            required_tokens,
            error_label,
        ) in _TEXT_BINDING_SPECS
    )
    return (
        text_bindings[:3]
        + (_bind_stage203_support(root),)
        + text_bindings[3:]
    )


def _gate_secrets(r: int) -> tuple[Polynomial, ...]:
    return tuple(
        tuple(
            (
                17 * (lane + 1)
                + 11 * coefficient
                + 3
            )
            % RING_MODULUS
            for coefficient in range(RING_DEGREE)
        )
        for lane in range(r)
    )


def _gate_lambda(r: int, rho: int) -> Matrix:
    if rho == 1:
        return ((1, 0), (1, 1))
    return tuple(
        (1, 0, 0)
        if lane == 0
        else (1, lane, lane * lane % RING_MODULUS)
        for lane in range(r)
    )


def _tensor_hash(tensor: OperatorTensor) -> str:
    return _sha256_json(asdict(tensor))


def _schedule_hash(root: Path) -> str:
    schedule = load_binary_target_schedule(root)
    return _sha256_json(asdict(schedule))


def _seed_hash(
    *,
    tensors: Sequence[OperatorTensor],
    bindings: Sequence[SourceBinding],
    schedule_hash: str,
    evaluator_counts: EvaluatorCounts,
) -> str:
    return _sha256_json(
        {
            "tensor_hashes": [_tensor_hash(tensor) for tensor in tensors],
            "source_bindings": [asdict(binding) for binding in bindings],
            "schedule_hash": schedule_hash,
            "evaluator_counts": asdict(evaluator_counts),
            "ring": {
                "modulus": RING_MODULUS,
                "n": RING_DEGREE,
            },
        }
    )


def _derive_decision(
    *,
    phase_identity_passed: bool,
    joint_rank_passed: bool,
    relation_audits: Sequence[EvaluatorSampleRelationAudit],
    structural_improvement: bool,
) -> str:
    if not phase_identity_passed:
        return REJECT_C1_PHASE_IDENTITY_TERMINAL
    if any(
        audit.status == REGISTERED_SHORT_ERROR_RELATION_FAIL
        for audit in relation_audits
    ):
        return REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL
    if not structural_improvement:
        return REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
    if joint_rank_passed:
        return ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY
    return ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2


def _evaluate_gate_material(
    tensors: Sequence[OperatorTensor],
    projections: Sequence[PhaseProjection],
) -> _GateEvaluation:
    if (
        len(tensors) != 2
        or len(projections) != 2
        or tuple(tensor.mu for tensor in tensors) != (0, 1)
        or tuple(projection.mu for projection in projections) != (0, 1)
    ):
        raise ValueError("gate requires separate canonical K_0 and K_1")
    reference = tensors[0]
    shared_fields = (
        "construction",
        "r",
        "rho",
        "d",
        "secrets",
        "gadget",
        "n",
        "modulus",
        "public_lambda",
        "input_components",
    )
    if (
        reference.d != reference.rho + 1
        or any(
            getattr(tensor, field) != getattr(reference, field)
            for tensor in tensors[1:]
            for field in shared_fields
        )
    ):
        raise ValueError("K_0 and K_1 metadata must share d=rho+1")
    phase_identity_passed = all(
        verify_phase_identity(tensor, projection)
        for tensor, projection in zip(tensors, projections)
    )
    joint_ranks_raw = tuple(
        concatenated_mask_difference_rank(tensor)
        for tensor in tensors
    )
    joint_ranks = (joint_ranks_raw[0], joint_ranks_raw[1])
    joint_rank_passed = all(
        value <= reference.rho * reference.n
        for value in joint_ranks
    )
    audits_raw = tuple(
        audit_evaluator_sample_relations(tensor, projection)
        for tensor, projection in zip(tensors, projections)
    )
    audits = (audits_raw[0], audits_raw[1])
    evaluator_counts = _counts_for_shape(
        r=reference.r,
        d=reference.d,
        ell=len(reference.gadget),
        n=reference.n,
        public_lambda=reference.public_lambda,
    )
    dense_counts = _counts_for_shape(
        r=reference.r,
        d=1,
        ell=len(reference.gadget),
        n=reference.n,
        public_lambda=tuple((1,) for _ in range(reference.r)),
    )
    structural_improvement = (
        evaluator_counts.add_multiplies < dense_counts.add_multiplies
        and evaluator_counts.body_polynomials
        < dense_counts.body_polynomials
        and not evaluator_counts.reconstructs_quadratic_body_work
    )
    decision = _derive_decision(
        phase_identity_passed=phase_identity_passed,
        joint_rank_passed=joint_rank_passed,
        relation_audits=audits,
        structural_improvement=structural_improvement,
    )
    return _GateEvaluation(
        phase_identity_passed=phase_identity_passed,
        joint_ranks=joint_ranks,
        joint_rank_passed=joint_rank_passed,
        relation_audits=audits,
        evaluator_counts=evaluator_counts,
        dense_counts=dense_counts,
        structural_improvement=structural_improvement,
        decision=decision,
    )


def _result_payload(result: OperatorGateResult) -> dict[str, object]:
    return {
        "r": result.r,
        "rho": result.rho,
        "modulus": result.modulus,
        "n": result.n,
        "gadget": result.gadget,
        "public_lambda": result.public_lambda,
        "tensor_hashes": [
            _tensor_hash(tensor) for tensor in result.tensors
        ],
        "projection_hashes": [
            _sha256_json(asdict(projection))
            for projection in result.projections
        ],
        "audit_hashes": [
            audit.diagnostic_hash
            for audit in result.relation_audits
        ],
        "phase_identity_passed": result.phase_identity_passed,
        "joint_ranks": result.joint_ranks,
        "joint_rank_passed": result.joint_rank_passed,
        "evaluator_counts": asdict(result.evaluator_counts),
        "dense_counts": asdict(result.dense_counts),
        "structural_improvement": result.structural_improvement,
        "source_bindings": [
            asdict(binding) for binding in result.source_bindings
        ],
        "schedule_hash": result.schedule_hash,
        "seed_hash": result.seed_hash,
        "decision": result.decision,
    }


def run_c1_operator_gate(
    root: Path | str,
    r: int,
    modulus: int,
) -> OperatorGateResult:
    """Build K_0/K_1 and derive exactly one Task 3A decision."""

    _validate_exact_ring(RING_DEGREE, modulus)
    if type(r) is not int or r not in (2, 4, 6):
        raise ValueError("r must be one of 2, 4, 6")
    root_path = Path(root)
    bindings = _source_bindings(root_path)
    schedule_hash = _schedule_hash(root_path)
    rho = min(2, r - 1)
    public_lambda = _gate_lambda(r, rho)
    secrets = _gate_secrets(r)
    tensors = tuple(
        build_rank_bounded_tensor(
            r,
            rho,
            mu,
            secrets,
            DEFAULT_GADGET,
            RING_DEGREE,
            modulus,
            public_lambda,
        )
        for mu in (0, 1)
    )
    projections = tuple(
        build_phase_projection(
            public_lambda,
            secrets,
            mu,
            modulus,
        )
        for mu in (0, 1)
    )
    evaluation = _evaluate_gate_material(tensors, projections)
    seed_hash = _seed_hash(
        tensors=tensors,
        bindings=bindings,
        schedule_hash=schedule_hash,
        evaluator_counts=evaluation.evaluator_counts,
    )
    provisional = OperatorGateResult(
        r=r,
        rho=rho,
        modulus=modulus,
        n=RING_DEGREE,
        gadget=DEFAULT_GADGET,
        public_lambda=public_lambda,
        tensors=(tensors[0], tensors[1]),
        projections=(projections[0], projections[1]),
        relation_audits=evaluation.relation_audits,
        phase_identity_passed=evaluation.phase_identity_passed,
        joint_ranks=evaluation.joint_ranks,
        joint_rank_passed=evaluation.joint_rank_passed,
        evaluator_counts=evaluation.evaluator_counts,
        dense_counts=evaluation.dense_counts,
        structural_improvement=evaluation.structural_improvement,
        source_bindings=bindings,
        schedule_hash=schedule_hash,
        seed_hash=seed_hash,
        decision=evaluation.decision,
        result_hash="",
    )
    return replace(
        provisional,
        result_hash=_sha256_json(_result_payload(provisional)),
    )


def verify_operator_gate_result(
    result: OperatorGateResult,
) -> bool:
    """Recompute all derived fields, including the terminal decision."""

    try:
        reference = result.tensors[0]
        if (
            result.r != reference.r
            or result.rho != reference.rho
            or result.modulus != reference.modulus
            or result.n != reference.n
            or result.gadget != reference.gadget
            or result.public_lambda != reference.public_lambda
        ):
            return False
        evaluation = _evaluate_gate_material(
            result.tensors,
            result.projections,
        )
        seed_hash = _seed_hash(
            tensors=result.tensors,
            bindings=result.source_bindings,
            schedule_hash=result.schedule_hash,
            evaluator_counts=evaluation.evaluator_counts,
        )
        if (
            evaluation.phase_identity_passed
            != result.phase_identity_passed
            or evaluation.joint_ranks != result.joint_ranks
            or evaluation.joint_rank_passed != result.joint_rank_passed
            or evaluation.relation_audits != result.relation_audits
            or evaluation.evaluator_counts != result.evaluator_counts
            or evaluation.dense_counts != result.dense_counts
            or evaluation.structural_improvement
            != result.structural_improvement
            or evaluation.decision != result.decision
            or seed_hash != result.seed_hash
        ):
            return False
        return result.result_hash == _sha256_json(
            _result_payload(result)
        )
    except (IndexError, TypeError, ValueError):
        return False
