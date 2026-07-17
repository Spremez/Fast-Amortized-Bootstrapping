"""Exact GF(p) mechanism controls for Candidate C.

These finite-field witnesses test rank and phase identities only. They are not
security, noise, polynomial-module, or production-performance evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import count
from typing import Hashable, NamedTuple, Sequence

from .finite_linear import rank, rref, solve_affine


Matrix = tuple[tuple[int, ...], ...]
_SYMBOL_SEQUENCE = count(1)


@dataclass(frozen=True)
class _RootIdentity:
    token: int
    provenance: Hashable
    value: int


@dataclass(frozen=True)
class _LinearIdentity:
    modulus: int
    terms: tuple[tuple[_RootIdentity, int], ...]


def _root_identity(
    provenance: Hashable,
    value: int,
    modulus: int,
) -> _LinearIdentity:
    root = _RootIdentity(
        token=next(_SYMBOL_SEQUENCE),
        provenance=provenance,
        value=value % modulus,
    )
    return _LinearIdentity(modulus, ((root, 1),))


def _combine_identities(
    coefficients: Sequence[int],
    identities: Sequence[_LinearIdentity],
    modulus: int,
) -> _LinearIdentity:
    combined: dict[_RootIdentity, int] = {}
    for coefficient, identity in zip(coefficients, identities):
        coefficient %= modulus
        for root, root_coefficient in identity.terms:
            combined[root] = (
                combined.get(root, 0)
                + coefficient * root_coefficient
            ) % modulus
    return _LinearIdentity(
        modulus,
        tuple(
            (root, combined[root])
            for root in sorted(combined, key=lambda item: item.token)
            if combined[root]
        ),
    )


def _identity_value(identity: _LinearIdentity) -> int:
    return sum(
        root.value * coefficient
        for root, coefficient in identity.terms
    ) % identity.modulus


def _public_identity(identity: _LinearIdentity) -> Hashable:
    terms = tuple(
        (coefficient, root.provenance)
        for root, coefficient in identity.terms
    )
    if len(terms) == 1 and terms[0][0] == 1:
        return terms[0][1]
    return ("root-linear-image", identity.modulus, terms)


def _fresh_symbol(
    modulus: int,
    symbol_index: int,
) -> tuple[Hashable, int, _LinearIdentity]:
    token = next(_SYMBOL_SEQUENCE)
    value = 1 + (symbol_index % (modulus - 1))
    provenance = ("independent-mask", token)
    root = _RootIdentity(token, provenance, value)
    return provenance, value, _LinearIdentity(modulus, ((root, 1),))


def _validate_modulus(modulus: int) -> None:
    if type(modulus) is not int or modulus <= 1:
        raise ValueError("modulus must be a positive prime")
    divisor = 2
    while divisor * divisor <= modulus:
        if modulus % divisor == 0:
            raise ValueError("modulus must be a positive prime")
        divisor += 1


def _matrix_shape(
    matrix: Sequence[Sequence[int]],
    *,
    label: str,
    allow_zero_columns: bool = False,
) -> tuple[int, int]:
    if not matrix:
        raise ValueError(f"{label} must contain at least one row")
    columns = len(matrix[0])
    if (columns == 0 and not allow_zero_columns) or any(
        len(row) != columns for row in matrix
    ):
        raise ValueError(f"{label} must be rectangular")
    return len(matrix), columns


@dataclass(frozen=True)
class MaskSpanState:
    lane_coefficients: Matrix
    body_constants: tuple[int, ...]
    mask_symbols: tuple[int, ...]
    provenance: tuple[Hashable, ...]
    modulus: int
    _provenance_tokens: tuple[_LinearIdentity, ...] = field(
        default=(),
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        _validate_modulus(self.modulus)
        lanes, symbols = _matrix_shape(
            self.lane_coefficients,
            label="lane coefficients",
            allow_zero_columns=True,
        )
        if len(self.body_constants) != lanes:
            raise ValueError("one body constant is required per lane")
        if len(self.mask_symbols) != symbols:
            raise ValueError("one mask symbol is required per coefficient column")
        if len(self.provenance) != symbols:
            raise ValueError("one provenance identifier is required per mask symbol")
        if self._provenance_tokens and len(self._provenance_tokens) != symbols:
            raise ValueError("one provenance token is required per mask symbol")
        if any(value % self.modulus for value in self.lane_coefficients[0]):
            raise ValueError("lambda[0,*] must be normalized to zero")
        try:
            distinct_provenance = len(set(self.provenance))
        except TypeError as error:
            raise ValueError("provenance identifiers must be hashable") from error
        if distinct_provenance != symbols:
            raise ValueError("provenance identifiers must be unique within a state")
        object.__setattr__(
            self,
            "lane_coefficients",
            tuple(
                tuple(value % self.modulus for value in row)
                for row in self.lane_coefficients
            ),
        )
        object.__setattr__(
            self,
            "body_constants",
            tuple(value % self.modulus for value in self.body_constants),
        )
        normalized_symbols = tuple(
            value % self.modulus for value in self.mask_symbols
        )
        object.__setattr__(
            self,
            "mask_symbols",
            normalized_symbols,
        )
        if not self._provenance_tokens:
            object.__setattr__(
                self,
                "_provenance_tokens",
                tuple(
                    _root_identity(provenance, value, self.modulus)
                    for provenance, value in zip(
                        self.provenance,
                        normalized_symbols,
                    )
                ),
            )
        elif any(
            not isinstance(identity, _LinearIdentity)
            or identity.modulus != self.modulus
            or _identity_value(identity) != value
            for identity, value in zip(
                self._provenance_tokens,
                normalized_symbols,
            )
        ):
            raise ValueError(
                "provenance identities must match their mask symbols"
            )


class CompressionResult(NamedTuple):
    compressed_state: MaskSpanState
    phase_preserved: bool
    discarded_directions: int
    online_product_count: int
    key_component_count: int


def shared_state(r: int, modulus: int) -> MaskSpanState:
    _validate_modulus(modulus)
    if type(r) is not int or r <= 0:
        raise ValueError("r must be positive")
    return MaskSpanState(
        lane_coefficients=tuple(() for _ in range(r)),
        body_constants=tuple(0 for _ in range(r)),
        mask_symbols=(),
        provenance=(),
        modulus=modulus,
    )


def _roots_for_identities(
    identities: Sequence[_LinearIdentity],
) -> tuple[_RootIdentity, ...]:
    roots: dict[int, _RootIdentity] = {}
    for identity in identities:
        for root, _ in identity.terms:
            previous = roots.get(root.token)
            if previous is not None and previous != root:
                raise ValueError("immutable root identity collision")
            roots[root.token] = root
    return tuple(roots[token] for token in sorted(roots))


def _effective_root_matrix(
    state: MaskSpanState,
    roots: Sequence[_RootIdentity],
) -> Matrix:
    root_index = {
        root: column
        for column, root in enumerate(roots)
    }
    rows: list[tuple[int, ...]] = []
    for lane_coefficients in state.lane_coefficients:
        effective = [0] * len(roots)
        for coefficient, identity in zip(
            lane_coefficients,
            state._provenance_tokens,
        ):
            for root, root_coefficient in identity.terms:
                column = root_index[root]
                effective[column] = (
                    effective[column]
                    + coefficient * root_coefficient
                ) % state.modulus
        rows.append(tuple(effective))
    return tuple(rows)


def _state_from_effective_root_matrix(
    effective: Matrix,
    body_constants: Sequence[int],
    roots: Sequence[_RootIdentity],
    modulus: int,
) -> MaskSpanState:
    reduced, pivots = rref(effective, modulus)
    source_rank = len(pivots)
    if source_rank == 0:
        return MaskSpanState(
            lane_coefficients=tuple(() for _ in body_constants),
            body_constants=tuple(body_constants),
            mask_symbols=(),
            provenance=(),
            modulus=modulus,
        )

    basis = tuple(
        tuple(reduced[row])
        for row in range(source_rank)
    )
    transposed_basis = tuple(
        tuple(
            basis[component][root]
            for component in range(source_rank)
        )
        for root in range(len(roots))
    )
    lane_coefficients: list[tuple[int, ...]] = []
    for lane_effective in effective:
        factorization = solve_affine(
            transposed_basis,
            lane_effective,
            modulus,
        )
        if not factorization.consistent:
            raise AssertionError("canonical source basis lost a lane equation")
        lane_coefficients.append(factorization.particular)

    identities = tuple(
        _LinearIdentity(
            modulus,
            tuple(
                (root, coefficient)
                for root, coefficient in zip(roots, basis_row)
                if coefficient
            ),
        )
        for basis_row in basis
    )
    return MaskSpanState(
        lane_coefficients=tuple(lane_coefficients),
        body_constants=tuple(body_constants),
        mask_symbols=tuple(
            _identity_value(identity)
            for identity in identities
        ),
        provenance=tuple(
            _public_identity(identity)
            for identity in identities
        ),
        modulus=modulus,
        _provenance_tokens=identities,
    )


def _canonicalize_state(state: MaskSpanState) -> MaskSpanState:
    roots = _roots_for_identities(state._provenance_tokens)
    effective = _effective_root_matrix(state, roots)
    return _state_from_effective_root_matrix(
        effective,
        state.body_constants,
        roots,
        state.modulus,
    )


def lane_difference_matrix(
    state: MaskSpanState,
    reference_lane: int = 0,
) -> Matrix:
    if (
        type(reference_lane) is not int
        or not 0 <= reference_lane < len(state.lane_coefficients)
    ):
        raise ValueError("reference lane is out of range")
    reference = state.lane_coefficients[reference_lane]
    return tuple(
        tuple(
            (value - reference[column]) % state.modulus
            for column, value in enumerate(row)
        )
        for lane, row in enumerate(state.lane_coefficients)
        if lane != reference_lane
    )


def excess_rank(state: MaskSpanState) -> int:
    return rank(lane_difference_matrix(state), state.modulus)


def append_mask_directions(
    state: MaskSpanState,
    lane_coefficients: Sequence[Sequence[int]],
) -> MaskSpanState:
    lanes, symbols = _matrix_shape(
        lane_coefficients,
        label="appended lane coefficients",
    )
    if lanes != len(state.lane_coefficients):
        raise ValueError("appended directions must have one row per lane")
    if any(value % state.modulus for value in lane_coefficients[0]):
        raise ValueError("appended lambda[0,*] must be normalized to zero")
    fresh = tuple(
        _fresh_symbol(
            state.modulus,
            len(state.mask_symbols) + symbol,
        )
        for symbol in range(symbols)
    )
    return MaskSpanState(
        lane_coefficients=tuple(
            tuple(current) + tuple(appended)
            for current, appended in zip(
                state.lane_coefficients,
                lane_coefficients,
            )
        ),
        body_constants=state.body_constants,
        mask_symbols=state.mask_symbols + tuple(item[1] for item in fresh),
        provenance=state.provenance + tuple(item[0] for item in fresh),
        modulus=state.modulus,
        _provenance_tokens=state._provenance_tokens
        + tuple(item[2] for item in fresh),
    )


def linear_combine_states(
    lhs: MaskSpanState,
    rhs: MaskSpanState,
    lhs_scale: int,
    rhs_scale: int,
) -> MaskSpanState:
    if lhs.modulus != rhs.modulus:
        raise ValueError("combined states must use the same modulus")
    if len(lhs.lane_coefficients) != len(rhs.lane_coefficients):
        raise ValueError("combined states must have the same lane count")
    if type(lhs_scale) is not int or type(rhs_scale) is not int:
        raise ValueError("combination scales must be integers")

    modulus = lhs.modulus
    columns: list[list[int]] = []
    symbols: list[int] = []
    provenances: list[Hashable] = []
    tokens: list[_LinearIdentity] = []
    provenance_index: dict[Hashable, int] = {}

    for operand, scale in ((lhs, lhs_scale), (rhs, rhs_scale)):
        scale %= modulus
        if scale == 0:
            continue
        for column, provenance in enumerate(operand.provenance):
            if provenance in provenance_index:
                output_column = provenance_index[provenance]
                if (
                    tokens[output_column]
                    != operand._provenance_tokens[column]
                    or symbols[output_column] != operand.mask_symbols[column]
                ):
                    raise ValueError(
                        "independent provenance identifiers must remain disjoint"
                    )
                for lane in range(len(columns[output_column])):
                    columns[output_column][lane] = (
                        columns[output_column][lane]
                        + scale * operand.lane_coefficients[lane][column]
                    ) % modulus
                continue

            provenance_index[provenance] = len(columns)
            columns.append(
                [
                    scale * operand.lane_coefficients[lane][column] % modulus
                    for lane in range(len(operand.lane_coefficients))
                ]
            )
            symbols.append(operand.mask_symbols[column])
            provenances.append(provenance)
            tokens.append(operand._provenance_tokens[column])

    active = [
        column
        for column, values in enumerate(columns)
        if any(values)
    ]
    combined = MaskSpanState(
        lane_coefficients=tuple(
            tuple(columns[column][lane] for column in active)
            for lane in range(len(lhs.lane_coefficients))
        ),
        body_constants=tuple(
            (lhs_scale * left + rhs_scale * right) % modulus
            for left, right in zip(lhs.body_constants, rhs.body_constants)
        ),
        mask_symbols=tuple(symbols[column] for column in active),
        provenance=tuple(provenances[column] for column in active),
        modulus=modulus,
        _provenance_tokens=tuple(tokens[column] for column in active),
    )
    return _canonicalize_state(combined)


def rotate_state(state: MaskSpanState, exponent: int) -> MaskSpanState:
    if type(exponent) is not int:
        raise ValueError("rotation exponent must be an integer")
    factor = 1 if exponent % 2 == 0 else (-1) % state.modulus
    if factor == 1:
        return state
    return MaskSpanState(
        lane_coefficients=tuple(
            tuple(
                factor * value % state.modulus
                for value in row
            )
            for row in state.lane_coefficients
        ),
        body_constants=tuple(
            factor * value % state.modulus
            for value in state.body_constants
        ),
        mask_symbols=state.mask_symbols,
        provenance=state.provenance,
        modulus=state.modulus,
        _provenance_tokens=state._provenance_tokens,
    )


def phase_vector(
    state: MaskSpanState,
    secrets: Sequence[int],
    modulus: int,
) -> tuple[int, ...]:
    _validate_modulus(modulus)
    if modulus != state.modulus:
        raise ValueError("phase modulus must match the state modulus")
    if len(secrets) != len(state.body_constants):
        raise ValueError("one secret is required per body")
    return tuple(
        (
            body
            - secret
            * sum(
                symbol * coefficient
                for symbol, coefficient in zip(
                    state.mask_symbols,
                    state.lane_coefficients[lane],
                )
            )
        )
        % modulus
        for lane, (body, secret) in enumerate(
            zip(state.body_constants, secrets)
        )
    )


def compress_state(
    state: MaskSpanState,
    projection: Matrix,
) -> CompressionResult:
    if not isinstance(projection, tuple) or any(
        not isinstance(row, tuple) for row in projection
    ):
        raise ValueError("projection must be an immutable public matrix")
    if not projection:
        if any(
            value
            for row in state.lane_coefficients
            for value in row
        ):
            raise ValueError(
                "public projection would discard a phase-active direction"
            )
        compressed = MaskSpanState(
            lane_coefficients=tuple(
                () for _ in state.lane_coefficients
            ),
            body_constants=state.body_constants,
            mask_symbols=(),
            provenance=(),
            modulus=state.modulus,
        )
        return CompressionResult(
            compressed_state=compressed,
            phase_preserved=True,
            discarded_directions=len(state.provenance),
            online_product_count=0,
            key_component_count=0,
        )
    components, columns = _matrix_shape(projection, label="projection")
    if columns != len(state.provenance):
        raise ValueError("projection width must match the state symbol count")
    normalized_projection = tuple(
        tuple(value % state.modulus for value in row)
        for row in projection
    )
    projection_rank = rank(normalized_projection, state.modulus)
    if projection_rank != components:
        raise ValueError("public projection rows must be independent")

    transposed_projection = tuple(
        tuple(
            normalized_projection[component][symbol]
            for component in range(components)
        )
        for symbol in range(columns)
    )
    compressed_coefficients: list[tuple[int, ...]] = []
    for lane_coefficients in state.lane_coefficients:
        factorization = solve_affine(
            transposed_projection,
            lane_coefficients,
            state.modulus,
        )
        if not factorization.consistent:
            raise ValueError(
                "public projection would discard a phase-active direction"
            )
        compressed_coefficients.append(factorization.particular)

    reconstructed = tuple(
        tuple(
            sum(
                compressed_coefficients[lane][component]
                * normalized_projection[component][symbol]
                for component in range(components)
            )
            % state.modulus
            for symbol in range(columns)
        )
        for lane in range(len(state.lane_coefficients))
    )
    if reconstructed != state.lane_coefficients:
        raise ValueError(
            "public projection would discard a phase-active direction"
        )

    projected_tokens = tuple(
        _combine_identities(
            normalized_projection[component],
            state._provenance_tokens,
            state.modulus,
        )
        for component in range(components)
    )
    projected_provenance = tuple(
        _public_identity(identity)
        for identity in projected_tokens
    )
    projected_symbols = tuple(
        _identity_value(identity)
        for identity in projected_tokens
    )
    projected = MaskSpanState(
        lane_coefficients=tuple(compressed_coefficients),
        body_constants=state.body_constants,
        mask_symbols=projected_symbols,
        provenance=projected_provenance,
        modulus=state.modulus,
        _provenance_tokens=projected_tokens,
    )
    compressed = _canonicalize_state(projected)
    return CompressionResult(
        compressed_state=compressed,
        phase_preserved=True,
        discarded_directions=(
            columns - len(compressed.provenance)
        ),
        online_product_count=sum(
            value != 0
            for row in compressed.lane_coefficients
            for value in row
        ),
        key_component_count=len(compressed.provenance),
    )


def schedule_step(
    state: MaskSpanState,
    step: Mapping[str, object],
) -> MaskSpanState:
    if not isinstance(step, Mapping):
        raise ValueError("schedule step must be a public operation mapping")
    operation = step.get("operation")
    if operation == "append_mask_directions":
        coefficients = step.get("lane_coefficients")
        if not isinstance(coefficients, Sequence):
            raise ValueError("append step requires lane coefficients")
        return append_mask_directions(state, coefficients)
    if operation == "rotate":
        exponent = step.get("exponent")
        if type(exponent) is not int:
            raise ValueError("rotate step requires an integer exponent")
        return rotate_state(state, exponent)
    raise ValueError(f"unknown schedule operation: {operation!r}")
