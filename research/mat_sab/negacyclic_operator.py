"""Ideal-phase scalar SAB and LUT-late-binding operator models over GF(257).

This module implements the exact finite test semantics required by the
Candidate D design (docs/superpowers/specs/2026-07-20-...-operator-sab-design.md
sections 5-7) at the plaintext/phase level:

- the scalar reference: the sparse amortized bootstrapping schedule acting on a
  test-vector-carrying accumulator list (setup rotation, per-slot public
  monomial rotations for ``sub_a``, and the ``r_prec`` RGSW monomial butterfly
  whose per-bit conditional rotations are CMUX on non-wrapped slots and
  NCMUX, i.e. ``-tau_{-1}`` of the wrapped source slot, on wrapped slots);
- the operator state ``U = (U_gamma)`` for ``gamma`` in a channel basis, with
  channel-wise updates, the ``tau_{-1}``-induced channel swap, and the late
  binding ``L_F(U) = sum_gamma gamma(F) * U_gamma``;
- the six registered negative-control corruptions.

Every schedule input is derived from SHA-256 counter PRFs, so execution is
byte-deterministic. Equality here establishes ideal algebraic semantics only;
noise, decomposition error, and decoding margins belong to the D3 gate.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from research.mat_sab.finite_linear import rank

FIELD_PRIME = 257
IDENTITY_LABEL = 0
TAU_MINUS_ONE_LABEL = 1


def prf_int(label: str, counter: int, modulus: int) -> int:
    digest = hashlib.sha256(f"{label}|{counter}".encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big") % modulus


class NegacyclicRing:
    """R = GF(257)[X] / (X^N + 1). Polynomials are coefficient tuples."""

    def __init__(self, n: int) -> None:
        if n not in (8, 16):
            raise ValueError("the D2 contract fixes N in {8, 16}")
        self.n = n

    def zero(self) -> tuple[int, ...]:
        return (0,) * self.n

    def monomial(self, exponent: int) -> tuple[int, ...]:
        poly = [0] * self.n
        poly[exponent % self.n] = 1
        return tuple(poly)

    def add(self, left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
        return tuple((a + b) % FIELD_PRIME for a, b in zip(left, right))

    def sub(self, left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
        return tuple((a - b) % FIELD_PRIME for a, b in zip(left, right))

    def neg(self, value: tuple[int, ...]) -> tuple[int, ...]:
        return tuple((-a) % FIELD_PRIME for a in value)

    def mul(self, left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
        result = [0] * self.n
        for i, a in enumerate(left):
            if a == 0:
                continue
            for j, b in enumerate(right):
                if b == 0:
                    continue
                k = i + j
                factor = a * b
                while k >= self.n:
                    k -= self.n
                    factor = -factor  # X^N = -1
                result[k] = (result[k] + factor) % FIELD_PRIME
        return tuple(result)

    def monomial_mul(self, value: tuple[int, ...], exponent: int) -> tuple[int, ...]:
        return self.mul(value, self.monomial(exponent))

    def tau(self, value: tuple[int, ...]) -> tuple[int, ...]:
        """tau_{-1}: X -> X^{-1}; tau(f)_0 = f_0, tau(f)_{N-j} = -f_j."""
        result = [0] * self.n
        result[0] = value[0]
        for j in range(1, self.n):
            result[self.n - j] = (-value[j]) % FIELD_PRIME
        return tuple(result)

    def state_hash(self, values: list[tuple[int, ...]]) -> str:
        serialized = ";".join(
            ",".join(str(v) for v in value) for value in values
        ).encode("ascii")
        return hashlib.sha256(serialized).hexdigest()


@dataclass(frozen=True)
class ScheduleSpec:
    """One deterministic small-parameter sparse schedule."""

    n: int
    r_prec: int
    h: int
    case: str
    include_zero: bool
    setup_exponents: tuple[int, ...]
    step_exponents: tuple[tuple[int, ...], ...]
    selector_bits: tuple[tuple[int, ...], ...]

    @property
    def selector_summary(self) -> str:
        bits = [b for step in self.selector_bits for b in step]
        if all(b == 0 for b in bits):
            return "0"
        if all(b == 1 for b in bits):
            return "1"
        return "mixed"


def _selector_pattern(case: str, step: int, bit: int, r_prec: int) -> int:
    if case in ("binary_all_zero", "include_zero_mu0"):
        return 0
    if case in ("binary_all_one", "include_zero_mu1", "coeff_one_fast_mu1"):
        return 1
    if case == "binary_alternating":
        return (step + bit) % 2
    if case.startswith("binary_one_hot_"):
        hot = int(case.rsplit("_", 1)[1])
        return 1 if bit == hot else 0
    if case == "binary_source_mixed":
        return prf_int(f"selector|{case}", step * r_prec + bit, 2)
    raise ValueError(f"unknown schedule case: {case}")


def build_schedule(n: int, r_prec: int, h: int, case: str) -> ScheduleSpec:
    """Derive the deterministic schedule for one registered case.

    ``include_zero_*`` cases interleave h extra zero-key steps, matching the
    include-zero schedule shape of the production binary SAB.
    ``coeff_one_fast_mu1`` forces every public sub_a coefficient to one, the
    legitimate precondition of the coeff-one fast path.
    """
    include_zero = case.startswith("include_zero_")
    coeff_one = case.startswith("coeff_one_fast_")
    steps = 2 * h if include_zero else h
    setup = tuple(
        prf_int(f"setup|{case}|{n}", j, 2 * n) - n for j in range(n)
    )
    step_exponents = []
    selectors = []
    for step in range(steps):
        if coeff_one:
            row = tuple(1 for _ in range(n))
        else:
            row = tuple(
                prf_int(f"suba|{case}|{n}", step * n + j, 2 * n) - n
                for j in range(n)
            )
        step_exponents.append(row)
        selectors.append(
            tuple(
                _selector_pattern(case, step, bit, r_prec)
                for bit in range(r_prec)
            )
        )
    return ScheduleSpec(
        n=n,
        r_prec=r_prec,
        h=h,
        case=case,
        include_zero=include_zero,
        setup_exponents=setup,
        step_exponents=tuple(step_exponents),
        selector_bits=tuple(selectors),
    )


@dataclass(frozen=True)
class ControlConfig:
    """Negative-control corruption switches (all False for the honest run)."""

    remove_tau_channel: bool = False
    omit_tau_swap: bool = False
    positive_wrap: bool = False
    skip_sub_a: bool = False
    coeff_one_fast_wrong_guard: bool = False
    wrong_butterfly_source: bool = False


HONEST_CONTROL = ControlConfig()


def scalar_setup(
    ring: NegacyclicRing, spec: ScheduleSpec, test_vector: tuple[int, ...]
) -> list[tuple[int, ...]]:
    return [
        ring.monomial_mul(test_vector, exponent)
        for exponent in spec.setup_exponents
    ]


def scalar_step(
    ring: NegacyclicRing,
    state: list[tuple[int, ...]],
    spec: ScheduleSpec,
    step: int,
) -> list[tuple[int, ...]]:
    """One sparse step: full r_prec butterfly, then the public sub_a rotation."""
    current = list(state)
    for bit in range(spec.r_prec):
        offset = 1 << bit
        selector = spec.selector_bits[step][bit]
        updated = list(current)
        for j in range(spec.n):
            if selector == 0:
                updated[j] = current[j]
                continue
            if j >= offset:
                updated[j] = current[j - offset]
            else:
                source = spec.n - offset + j
                updated[j] = ring.neg(ring.tau(current[source]))
        current = updated
    return [
        ring.monomial_mul(value, -exponent)
        for value, exponent in zip(current, spec.step_exponents[step])
    ]


def scalar_schedule(
    ring: NegacyclicRing, spec: ScheduleSpec, test_vector: tuple[int, ...]
) -> list[tuple[int, ...]]:
    state = scalar_setup(ring, spec, test_vector)
    for step in range(len(spec.selector_bits)):
        state = scalar_step(ring, state, spec, step)
    return state


OperatorSlot = tuple[tuple[int, ...], tuple[int, ...]]


def operator_setup(
    ring: NegacyclicRing, spec: ScheduleSpec
) -> list[OperatorSlot]:
    state: list[OperatorSlot] = []
    for exponent in spec.setup_exponents:
        monomial = ring.monomial(exponent)
        state.append((monomial, ring.zero()))
    return state


def _wrapped_source_transform(
    ring: NegacyclicRing, slot: OperatorSlot, control: ControlConfig
) -> OperatorSlot:
    """-tau_{-1} applied to a wrapped source slot's operator channels.

    tau_{-1} acts on the operator state by swapping the two channels and
    applying tau_{-1} to each; the negacyclic wrap contributes one global
    sign. Negative controls corrupt exactly one of these three ingredients.
    """
    identity_channel, tau_channel = slot
    if control.omit_tau_swap:
        swapped = (ring.tau(identity_channel), ring.tau(tau_channel))
    else:
        swapped = (ring.tau(tau_channel), ring.tau(identity_channel))
    if control.positive_wrap:
        return swapped
    return (ring.neg(swapped[0]), ring.neg(swapped[1]))


def operator_step(
    ring: NegacyclicRing,
    state: list[OperatorSlot],
    spec: ScheduleSpec,
    step: int,
    control: ControlConfig,
) -> list[OperatorSlot]:
    current = list(state)
    for bit in range(spec.r_prec):
        offset = 1 << bit
        selector = spec.selector_bits[step][bit]
        updated = list(current)
        for j in range(spec.n):
            if selector == 0:
                updated[j] = current[j]
                continue
            if control.wrong_butterfly_source:
                offset_source = (j - offset - 1) % spec.n
            else:
                offset_source = j - offset
            if j >= offset:
                updated[j] = current[offset_source]
            else:
                if control.wrong_butterfly_source:
                    source = (spec.n - offset + j - 1) % spec.n
                else:
                    source = spec.n - offset + j
                updated[j] = _wrapped_source_transform(
                    ring, current[source], control
                )
        current = updated
    if control.skip_sub_a:
        return current
    next_state: list[OperatorSlot] = []
    for j, (identity_channel, tau_channel) in enumerate(current):
        exponent = -spec.step_exponents[step][j]
        if control.coeff_one_fast_wrong_guard and spec.step_exponents[step][j] != 1:
            # Mis-applied fast path: the coeff-one shortcut is taken under a
            # guard that does not hold, skipping the public rotation.
            next_state.append((identity_channel, tau_channel))
            continue
        next_state.append(
            (
                ring.monomial_mul(identity_channel, exponent),
                ring.monomial_mul(tau_channel, exponent),
            )
        )
    return next_state


def operator_schedule(
    ring: NegacyclicRing, spec: ScheduleSpec, control: ControlConfig
) -> list[OperatorSlot]:
    state = operator_setup(ring, spec)
    for step in range(len(spec.selector_bits)):
        state = operator_step(ring, state, spec, step, control)
    return state


def bind(
    ring: NegacyclicRing,
    state: list[OperatorSlot],
    test_vector: tuple[int, ...],
    control: ControlConfig,
) -> list[tuple[int, ...]]:
    """Late binding L_F(U) = F * U_id + tau_{-1}(F) * U_tau per slot."""
    tau_vector = ring.tau(test_vector)
    bound: list[tuple[int, ...]] = []
    for identity_channel, tau_channel in state:
        value = ring.mul(identity_channel, test_vector)
        if not control.remove_tau_channel:
            value = ring.add(value, ring.mul(tau_channel, tau_vector))
        bound.append(value)
    return bound


def channel_matrix_rank(
    state: list[OperatorSlot], modulus: int = FIELD_PRIME
) -> int:
    """Column rank of the flattened operator channels (1 or 2 for gamma=2)."""
    identity_column: list[int] = []
    tau_column: list[int] = []
    for identity_channel, tau_channel in state:
        identity_column.extend(identity_channel)
        tau_column.extend(tau_channel)
    return rank([identity_column, tau_column], modulus)


def basis_search_closure(
    ring: NegacyclicRing, spec: ScheduleSpec
) -> tuple[bool, dict[str, object]]:
    """Check whether the single-channel basis Gamma_0 = {identity} closes.

    Returns (closed, evidence) where evidence names the first failing
    basis vector, case, and slot. This provides the mandatory Gamma_0 failure
    record before the single permitted Gamma_1 = {id, tau_{-1}} revision.
    """
    final = operator_schedule(ring, spec, HONEST_CONTROL)
    for basis_index in range(ring.n):
        vector = tuple(
            1 if index == basis_index else 0 for index in range(ring.n)
        )
        scalar_final = scalar_schedule(ring, spec, vector)
        single_channel = [
            ring.mul(identity_channel, vector)
            for identity_channel, _ in final
        ]
        for j, (actual, expected) in enumerate(
            zip(single_channel, scalar_final)
        ):
            if actual != expected:
                return False, {
                    "basis_index": basis_index,
                    "slot": j,
                    "case": spec.case,
                    "n": spec.n,
                }
    return True, {}
