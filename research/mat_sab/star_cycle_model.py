from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .finite_linear import rank, solve_affine


Matrix = list[list[int]]
Support = frozenset[tuple[int, int]]


@dataclass(frozen=True)
class SupportAnalysis:
    r: int
    modulus: int
    support_size: int
    consistent: bool
    affine_dimension: int
    column_dimensions: tuple[int, ...]
    full_pvw_randomization: bool
    particular_matrix: tuple[tuple[int, ...], ...]


def phase_matrix(secret: Sequence[int], modulus: int) -> Matrix:
    r = len(secret)
    matrix = [[0] * (r + 1) for _ in range(r)]
    for lane, value in enumerate(secret):
        matrix[lane][0] = (-value) % modulus
        matrix[lane][lane + 1] = 1
    return matrix


def kernel_vector(secret: Sequence[int], modulus: int) -> list[int]:
    return [1] + [value % modulus for value in secret]


def identity(size: int) -> Matrix:
    return [[1 if row == column else 0 for column in range(size)] for row in range(size)]


def outer(left: Sequence[int], right: Sequence[int], modulus: int) -> Matrix:
    return [[(a * b) % modulus for b in right] for a in left]


def matmul(left: Sequence[Sequence[int]], right: Sequence[Sequence[int]], modulus: int) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("incompatible matrix dimensions")
    return [
        [
            sum(left[row][inner] * right[inner][column] for inner in range(len(right))) % modulus
            for column in range(len(right[0]))
        ]
        for row in range(len(left))
    ]


def selector_from_kernel(
    secret: Sequence[int], mu: int, weights: Sequence[int], modulus: int
) -> Matrix:
    size = len(secret) + 1
    if len(weights) != size:
        raise ValueError("one randomization weight is required per input column")
    base = identity(size)
    randomizer = outer(kernel_vector(secret, modulus), weights, modulus)
    return [
        [((mu * base[row][column]) + randomizer[row][column]) % modulus for column in range(size)]
        for row in range(size)
    ]


def dense_support(r: int) -> Support:
    return frozenset((row, column) for row in range(r + 1) for column in range(r + 1))


def star_cycle_support(r: int) -> Support:
    support: set[tuple[int, int]] = set()
    for body in range(1, r + 1):
        support.add((0, body))
        support.add((body, 0))
        support.add((body, body))
        support.add((body, 1 + (body % r)))
    return frozenset(support)


def support_from_stage203(path: Path, r: int) -> Support:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        return frozenset(
            (int(row["row"]), int(row["col"]))
            for row in rows
            if int(row["r"]) == r and row["semantic_role"] == "active"
        )


def phase_constraints(
    secret: Sequence[int], mu: int, support: Iterable[tuple[int, int]], modulus: int
) -> tuple[Matrix, list[int], tuple[tuple[int, int], ...]]:
    p_matrix = phase_matrix(secret, modulus)
    index = tuple(sorted(set(support)))
    size = len(secret) + 1
    coefficients: Matrix = []
    rhs: list[int] = []
    for phase_row in range(len(secret)):
        for input_column in range(size):
            equation = [0] * len(index)
            for variable, (output_row, column) in enumerate(index):
                if column == input_column:
                    equation[variable] = p_matrix[phase_row][output_row]
            coefficients.append(equation)
            rhs.append((mu * p_matrix[phase_row][input_column]) % modulus)
    return coefficients, rhs, index


def _matrix_from_vector(
    values: Sequence[int], index: Sequence[tuple[int, int]], size: int
) -> tuple[tuple[int, ...], ...]:
    matrix = [[0] * size for _ in range(size)]
    for value, (row, column) in zip(values, index):
        matrix[row][column] = value
    return tuple(tuple(row) for row in matrix)


def _column_dimensions(
    secret: Sequence[int], support: Support, modulus: int
) -> tuple[int, ...]:
    p_matrix = phase_matrix(secret, modulus)
    dimensions: list[int] = []
    for column in range(len(secret) + 1):
        outputs = sorted(row for row, input_column in support if input_column == column)
        restricted = [[phase_row[row] for row in outputs] for phase_row in p_matrix]
        dimensions.append(len(outputs) - rank(restricted, modulus))
    return tuple(dimensions)


def analyze_support(
    secret: Sequence[int], mu: int, support: Support, modulus: int
) -> SupportAnalysis:
    coefficients, rhs, index = phase_constraints(secret, mu, support, modulus)
    solution = solve_affine(coefficients, rhs, modulus)
    dimensions = _column_dimensions(secret, support, modulus)
    size = len(secret) + 1
    matrix = _matrix_from_vector(solution.particular, index, size) if solution.consistent else tuple()
    return SupportAnalysis(
        r=len(secret),
        modulus=modulus,
        support_size=len(support),
        consistent=solution.consistent,
        affine_dimension=solution.dimension,
        column_dimensions=dimensions,
        full_pvw_randomization=solution.consistent and all(value >= 1 for value in dimensions),
        particular_matrix=matrix,
    )


def phase_residual(
    secret: Sequence[int], matrix: Sequence[Sequence[int]], mu: int, modulus: int
) -> Matrix:
    p_matrix = phase_matrix(secret, modulus)
    actual = matmul(p_matrix, matrix, modulus)
    expected = [[(mu * value) % modulus for value in row] for row in p_matrix]
    return [
        [(actual[row][column] - expected[row][column]) % modulus for column in range(len(expected[0]))]
        for row in range(len(expected))
    ]
