from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AffineSolution:
    consistent: bool
    rank: int
    variables: int
    dimension: int
    particular: tuple[int, ...]


def mod_inv(value: int, modulus: int) -> int:
    value %= modulus
    if value == 0:
        raise ZeroDivisionError("zero has no modular inverse")
    return pow(value, -1, modulus)


def rref(matrix: Sequence[Sequence[int]], modulus: int) -> tuple[list[list[int]], list[int]]:
    if modulus <= 1:
        raise ValueError("modulus must exceed one")
    rows = [list(value % modulus for value in row) for row in matrix]
    if not rows:
        return [], []
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("ragged matrix")
    pivots: list[int] = []
    pivot_row = 0
    for column in range(width):
        selected = next((row for row in range(pivot_row, len(rows)) if rows[row][column]), None)
        if selected is None:
            continue
        rows[pivot_row], rows[selected] = rows[selected], rows[pivot_row]
        inverse = mod_inv(rows[pivot_row][column], modulus)
        rows[pivot_row] = [(value * inverse) % modulus for value in rows[pivot_row]]
        for row in range(len(rows)):
            if row == pivot_row or rows[row][column] == 0:
                continue
            factor = rows[row][column]
            rows[row] = [
                (value - factor * pivot) % modulus
                for value, pivot in zip(rows[row], rows[pivot_row])
            ]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return rows, pivots


def rank(matrix: Sequence[Sequence[int]], modulus: int) -> int:
    return len(rref(matrix, modulus)[1])


def solve_affine(
    coefficients: Sequence[Sequence[int]], rhs: Sequence[int], modulus: int
) -> AffineSolution:
    if len(coefficients) != len(rhs):
        raise ValueError("coefficient and rhs row counts differ")
    if not coefficients:
        raise ValueError("at least one equation is required")
    variables = len(coefficients[0])
    if any(len(row) != variables for row in coefficients):
        raise ValueError("ragged coefficient matrix")
    augmented = [list(row) + [value] for row, value in zip(coefficients, rhs)]
    reduced, pivots = rref(augmented, modulus)
    inconsistent = any(
        all(value == 0 for value in row[:variables]) and row[variables] != 0
        for row in reduced
    )
    coefficient_pivots = [pivot for pivot in pivots if pivot < variables]
    if inconsistent:
        return AffineSolution(False, len(coefficient_pivots), variables, -1, ())
    particular = [0] * variables
    for row_index, pivot in enumerate(coefficient_pivots):
        particular[pivot] = reduced[row_index][variables]
    return AffineSolution(
        True,
        len(coefficient_pivots),
        variables,
        variables - len(coefficient_pivots),
        tuple(particular),
    )
