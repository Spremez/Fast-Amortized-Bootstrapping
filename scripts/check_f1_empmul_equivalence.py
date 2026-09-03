#!/usr/bin/env python3
"""F1 G1 finite check: delta=2 EMPmul step vs sequential single-bit steps.

Verifies Lemma F1-1 of docs/f1_mat_empmul_theory.md at the exact scalar
level over GF(257)[X]/(X^N+1), N in {8, 16}: the fused four-way selection
step of BatchBoot (USENIX Sec'26, Alg. 2 interval structure, migrated to the
negacyclic-operator semantics verified by the Candidate D D2 checker) equals
the composition of the two sequential single-bit CMUX/NCMUX steps for every
slot, every bit-pair offset, and every selector value in {0,1}^2.

The wrapped-source action is -tau_{-1} (negation composed with the
X -> X^{-1} automorphism), matching research/mat_sab/negacyclic_operator.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Reuse the D2-verified operator/ring implementation from the candidate worktree.
WT = (
    Path(__file__).resolve().parents[1]
    / ".worktrees"
    / "candidate-a-star-cycle-gate"
)
sys.path.insert(0, str(WT))

from research.mat_sab.negacyclic_operator import (  # noqa: E402
    NegacyclicRing,
)

P = 257


def sequential_two_bit(
    ring: NegacyclicRing,
    state: list[tuple[int, ...]],
    a: int,
    b: int,
    v_a: int,
    v_b: int,
) -> list[tuple[int, ...]]:
    """Apply bit offset a then bit offset b, each with wrap = -tau_{-1}."""

    def one_bit(current: list[tuple[int, ...]], offset: int, v: int):
        updated = list(current)
        for j in range(ring.n):
            if v == 0:
                updated[j] = current[j]
            elif j >= offset:
                updated[j] = current[j - offset]
            else:
                updated[j] = ring.neg(ring.tau(current[ring.n - offset + j]))
        return updated

    return one_bit(one_bit(state, a, v_a), b, v_b)


def fused_delta2(
    ring: NegacyclicRing,
    state: list[tuple[int, ...]],
    a: int,
    b: int,
    v_a: int,
    v_b: int,
) -> list[tuple[int, ...]]:
    """BatchBoot Alg. 2 four-way fused step with the three-interval split."""
    n = ring.n

    def wrapped(source: int) -> tuple[int, ...]:
        return ring.neg(ring.tau(state[source % n]))

    result = list(state)
    for j in range(n):
        pick_identity = (v_a, v_b) == (0, 0)
        pick_a = (v_a, v_b) == (1, 0)
        pick_b = (v_a, v_b) == (0, 1)
        pick_ab = (v_a, v_b) == (1, 1)
        if pick_identity:
            result[j] = state[j]
            continue
        if j < a:
            # interval 1: all non-identity sources are wrapped
            if pick_a:
                result[j] = wrapped(n - a + j)
            elif pick_b:
                result[j] = wrapped(n - b + j)
            else:
                result[j] = wrapped(n - a - b + j)
        elif j < b:
            # interval 2: source j-a plain, deeper sources wrapped
            if pick_a:
                result[j] = state[j - a]
            elif pick_b:
                result[j] = wrapped(n - b + j)
            else:
                result[j] = wrapped(n - a - b + j)
        elif j < a + b:
            # interval 3: only the combined source wraps
            if pick_a:
                result[j] = state[j - a]
            elif pick_b:
                result[j] = state[j - b]
            else:
                result[j] = wrapped(n - a - b + j)
        else:
            # interval 4: all sources plain
            if pick_a:
                result[j] = state[j - a]
            elif pick_b:
                result[j] = state[j - b]
            else:
                result[j] = state[j - a - b]
    return result


def main() -> int:
    failures = 0
    checks = 0
    for n, r_prec in ((8, 3), (16, 4)):
        ring = NegacyclicRing(n)
        state = [
            tuple((17 * j + 5 * i + 1) % P for i in range(n))
            for j in range(n)
        ]
        for t in range(r_prec // 2):
            a = 1 << (2 * t)
            b = 1 << (2 * t + 1)
            for v_a in (0, 1):
                for v_b in (0, 1):
                    lhs = sequential_two_bit(ring, state, a, b, v_a, v_b)
                    rhs = fused_delta2(ring, state, a, b, v_a, v_b)
                    for j in range(n):
                        checks += 1
                        if lhs[j] != rhs[j]:
                            failures += 1
                            if failures <= 3:
                                print(
                                    f"MISMATCH N={n} t={t} a={a} b={b} "
                                    f"v=({v_a},{v_b}) slot={j}"
                                )
    print(f"checks={checks} failures={failures}")
    print(
        "F1-1 VERIFIED: fused delta=2 step == sequential two-bit composition"
        if failures == 0
        else "F1-1 FAILED"
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
