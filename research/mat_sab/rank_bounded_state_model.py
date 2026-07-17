"""Exact GF(p) mechanism controls for Candidate C.

These finite-field witnesses test rank and phase identities only. They are not
security, noise, polynomial-module, or production-performance evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import count
from typing import Hashable, NamedTuple, Sequence

from .finite_linear import rank, solve_affine


Matrix = tuple[tuple[int, ...], ...]
_SYMBOL_SEQUENCE = count(1)


def _fresh_symbol(
    modulus: int,
    symbol_index: int,
) -> tuple[Hashable, int, int]:
    token = next(_SYMBOL_SEQUENCE)
    value = 1 + (symbol_index % (modulus - 1))
    return ("independent-mask", token), value, token


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
    _provenance_tokens: tuple[int, ...] = field(
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
        object.__setattr__(
            self,
            "mask_symbols",
            tuple(value % self.modulus for value in self.mask_symbols),
        )
        if not self._provenance_tokens:
            object.__setattr__(
                self,
                "_provenance_tokens",
                tuple(next(_SYMBOL_SEQUENCE) for _ in range(symbols)),
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


def lane_difference_matrix(state: MaskSpanState) -> Matrix:
    reference = state.lane_coefficients[0]
    return tuple(
        tuple(
            (value - reference[column]) % state.modulus
            for column, value in enumerate(row)
        )
        for row in state.lane_coefficients[1:]
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
    tokens: list[int] = []
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
    return MaskSpanState(
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


def rotate_state(state: MaskSpanState, exponent: int) -> MaskSpanState:
    if type(exponent) is not int:
        raise ValueError("rotation exponent must be an integer")
    if exponent == 0:
        return state
    factor = pow(2, exponent, state.modulus)
    return MaskSpanState(
        lane_coefficients=state.lane_coefficients,
        body_constants=tuple(
            factor * value % state.modulus
            for value in state.body_constants
        ),
        mask_symbols=tuple(
            factor * value % state.modulus
            for value in state.mask_symbols
        ),
        provenance=tuple(
            ("rotation", exponent, identifier)
            for identifier in state.provenance
        ),
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

    projected_symbols = tuple(
        sum(
            normalized_projection[component][symbol]
            * state.mask_symbols[symbol]
            for symbol in range(columns)
        )
        % state.modulus
        for component in range(components)
    )
    projected_provenance = tuple(
        (
            "public-projection",
            normalized_projection[component],
            state.provenance,
        )
        for component in range(components)
    )
    projected_tokens = tuple(
        next(_SYMBOL_SEQUENCE) for _ in range(components)
    )
    compressed = MaskSpanState(
        lane_coefficients=tuple(compressed_coefficients),
        body_constants=state.body_constants,
        mask_symbols=projected_symbols,
        provenance=projected_provenance,
        modulus=state.modulus,
        _provenance_tokens=projected_tokens,
    )
    return CompressionResult(
        compressed_state=compressed,
        phase_preserved=True,
        discarded_directions=columns - projection_rank,
        online_product_count=sum(
            value != 0
            for row in normalized_projection
            for value in row
        ),
        key_component_count=components,
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
