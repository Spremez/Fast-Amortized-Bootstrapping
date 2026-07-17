from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .finite_linear import rank


Matrix = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class FactorCost:
    r: int
    q: int
    dense_products: int
    generic_left_products: int
    generic_right_products: int
    separate_diagonal_products: int
    generic_dense_factor_products: int
    generic_dense_factor_beats_dense: bool
    retained_dense_error_products: int
    retained_dense_error_is_quadratic: bool


def _validate_modulus(modulus: int) -> None:
    if type(modulus) is not int or modulus <= 1:
        raise ValueError("modulus must exceed one")


def torus_normal_from_uniform_pair(
    rnd0: int,
    rnd1: int,
    sigma: float,
    *,
    torus_bits: int = 64,
) -> int:
    limit = 1 << torus_bits
    if (
        type(rnd0) is not int
        or type(rnd1) is not int
        or not 0 <= rnd0 < limit
        or not 0 < rnd1 < limit
    ):
        raise ValueError("uniform words must satisfy 0 <= rnd0 and 0 < rnd1")
    if sigma <= 0 or torus_bits not in (32, 64):
        raise ValueError("sigma and torus width must be valid")
    scale = float(limit)
    sample = (
        math.cos(2.0 * math.pi * (rnd0 / scale))
        * math.sqrt(-2.0 * math.log(rnd1 / scale))
        * sigma
    )
    return int(scale * sample)


def _matrix_shape(
    matrix: Sequence[Sequence[int]],
    *,
    label: str,
) -> tuple[int, int]:
    if not matrix:
        raise ValueError(f"{label} must contain at least one row")
    columns = len(matrix[0])
    if columns == 0 or any(len(row) != columns for row in matrix):
        raise ValueError(f"{label} must be a nonempty rectangular matrix")
    return len(matrix), columns


def _validate_standard_inputs(
    secret: Sequence[int],
    masks: Sequence[int],
    errors: Sequence[Sequence[int]],
) -> tuple[int, int]:
    r = len(secret)
    if r <= 0:
        raise ValueError("secret must contain at least one body")
    size = r + 1
    if len(masks) != size:
        raise ValueError("one mask is required per selector row")
    error_rows, error_columns = _matrix_shape(errors, label="errors")
    if error_rows != size or error_columns != r:
        raise ValueError("errors must have shape (r+1) x r")
    return r, size


def standard_selector(
    secret: Sequence[int],
    mu: int,
    masks: Sequence[int],
    errors: Sequence[Sequence[int]],
    modulus: int,
    *,
    gadget: int = 1,
) -> Matrix:
    _validate_modulus(modulus)
    if mu not in (0, 1):
        raise ValueError("mu must be zero or one")
    r, size = _validate_standard_inputs(secret, masks, errors)
    rows: list[tuple[int, ...]] = []
    for row in range(size):
        values = [
            (
                masks[row]
                + (mu * gadget if row == 0 else 0)
            )
            % modulus
        ]
        for lane in range(r):
            column = lane + 1
            values.append(
                (
                    masks[row] * secret[lane]
                    + errors[row][lane]
                    + (mu * gadget if row == column else 0)
                )
                % modulus
            )
        rows.append(tuple(values))
    return tuple(rows)


def external_product(
    digits: Sequence[int],
    selector: Sequence[Sequence[int]],
    modulus: int,
) -> tuple[int, ...]:
    _validate_modulus(modulus)
    rows, columns = _matrix_shape(selector, label="selector")
    if len(digits) != rows:
        raise ValueError("one digit is required per selector row")
    return tuple(
        sum(digits[row] * selector[row][column] for row in range(rows))
        % modulus
        for column in range(columns)
    )


def phase(
    vector: Sequence[int],
    secret: Sequence[int],
    modulus: int,
) -> tuple[int, ...]:
    _validate_modulus(modulus)
    if len(secret) <= 0 or len(vector) != len(secret) + 1:
        raise ValueError("vector must contain one mask and r bodies")
    return tuple(
        (vector[lane + 1] - vector[0] * secret[lane]) % modulus
        for lane in range(len(secret))
    )


def expected_phase(
    digits: Sequence[int],
    errors: Sequence[Sequence[int]],
    secret: Sequence[int],
    mu: int,
    modulus: int,
    *,
    gadget: int = 1,
) -> tuple[int, ...]:
    _validate_modulus(modulus)
    if mu not in (0, 1):
        raise ValueError("mu must be zero or one")
    r, size = _validate_standard_inputs(
        secret,
        tuple(0 for _ in range(len(secret) + 1)),
        errors,
    )
    if len(digits) != size:
        raise ValueError("digits must contain one mask and r bodies")
    input_phase = phase(digits, secret, modulus)
    return tuple(
        (
            mu * gadget * input_phase[lane]
            + sum(
                digits[row] * errors[row][lane]
                for row in range(size)
            )
        )
        % modulus
        for lane in range(r)
    )


def constant_error_homomorphic_image(
    polynomial_matrix: Sequence[Sequence[Sequence[int]]],
) -> Matrix:
    if not polynomial_matrix:
        raise ValueError("polynomial matrix must contain at least one row")
    columns = len(polynomial_matrix[0])
    if columns == 0 or any(
        len(row) != columns
        for row in polynomial_matrix
    ):
        raise ValueError("polynomial matrix must be rectangular")
    if any(
        not polynomial
        for row in polynomial_matrix
        for polynomial in row
    ):
        raise ValueError("every polynomial must contain a coefficient")
    return tuple(
        tuple(sum(polynomial) % 2 for polynomial in row)
        for row in polynomial_matrix
    )


def full_rank_homomorphic_image(r: int) -> Matrix:
    if type(r) is not int or r <= 0:
        raise ValueError("r must be positive")
    return tuple(
        tuple(1 if row == column else 0 for column in range(r))
        for row in range(r + 1)
    )


def _matmul(
    left: Sequence[Sequence[int]],
    right: Sequence[Sequence[int]],
    modulus: int,
) -> Matrix:
    left_rows, inner = _matrix_shape(left, label="left factor")
    right_rows, columns = _matrix_shape(right, label="right factor")
    if inner != right_rows:
        raise ValueError("factor dimensions do not match")
    return tuple(
        tuple(
            sum(left[row][index] * right[index][column] for index in range(inner))
            % modulus
            for column in range(columns)
        )
        for row in range(left_rows)
    )


def low_rank_homomorphic_image_control(r: int, q: int) -> Matrix:
    if type(r) is not int or r <= 1:
        raise ValueError("r must exceed one")
    if type(q) is not int or q <= 0 or q >= r:
        raise ValueError("q must satisfy 1 <= q < r")
    size = r + 1
    left = tuple(
        tuple(
            (
                1
                if row < q and row == inner
                else (row + 1) * (inner + 1)
                if row >= q
                else 0
            )
            % 2
            for inner in range(q)
        )
        for row in range(size)
    )
    right = tuple(
        tuple(
            (
                1
                if column < q and column == inner
                else (inner + 1) * (column + 2)
                if column >= q
                else 0
            )
            % 2
            for column in range(r)
        )
        for inner in range(q)
    )
    return _matmul(left, right, 2)


def homomorphic_image_rank(
    image: Sequence[Sequence[int]],
    *,
    modulus: int = 2,
) -> int:
    if modulus != 2:
        raise ValueError("the parity-evaluation image is defined over GF(2)")
    _matrix_shape(image, label="homomorphic image")
    return rank(image, 2)


def homomorphic_image_fits_inner_dimension(
    image: Sequence[Sequence[int]],
    q: int,
) -> bool:
    if type(q) is not int or q < 0:
        raise ValueError("q must be nonnegative")
    return homomorphic_image_rank(image) <= q


def factor_cost(r: int, q: int) -> FactorCost:
    if type(r) is not int or r <= 0:
        raise ValueError("r must be positive")
    if type(q) is not int or q < 0 or q > r:
        raise ValueError("q must satisfy 0 <= q <= r")
    size = r + 1
    dense = size * size
    left = size * q
    right = q * r
    diagonal = size
    factorized = left + right + diagonal
    dense_error = size * r
    return FactorCost(
        r=r,
        q=q,
        dense_products=dense,
        generic_left_products=left,
        generic_right_products=right,
        separate_diagonal_products=diagonal,
        generic_dense_factor_products=factorized,
        generic_dense_factor_beats_dense=factorized < dense,
        retained_dense_error_products=dense_error,
        retained_dense_error_is_quadratic=True,
    )
