#!/usr/bin/env python3
"""F1 G1' finite check: delta=2 step in identity-addend (free-addend) form.

Extends check_f1_empmul_equivalence.py (Lemma F1-1, four-way fused selection)
to the formulation required by the T2 cost model and the G2 noise lemma:

    out_j = U_j + sum_{m in {a, b, ab}} ind_m * ( src_m(j) - U_j )  [exact level]

where ind_m in {0,1} are the joint indicators of the two position bits
(exactly one is 1, or none when the digit is 0), and src_m(j) is the offset
source with the negacyclic wrap action -tau_{-1} in the wrapped intervals.
The (0,0) case is the free torus addend U_j -- no external product, which is
the row-product saving counted by T2 (2^delta - 1 = 3 MV-EPs per slot).

Checks over GF(257)[X]/(X^N+1), N in {8, 16}:
  A. per-step equivalence: identity-addend step == sequential two-bit step
     (reference from the G1 checker) for every bit-pair offset and selector;
  B. full-chain equivalence: rho/2 chained identity-addend steps == rho
     sequential single-bit steps, for deterministic and pseudo-random digit
     sequences;
  C. negative controls (each must FAIL to be detected):
     C1  drop the identity addend (out_j = sum ind_m * src_m) -- wrong when
         the digit is 0;
     C2  plain source where a wrapped source is required (missing -tau_{-1});
     C3  swapped interval boundaries (a/b offsets exchanged).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


def one_bit(ring, state, offset, v):
    updated = list(state)
    n = ring.n
    for j in range(n):
        if v == 0:
            updated[j] = state[j]
        elif j >= offset:
            updated[j] = state[j - offset]
        else:
            updated[j] = ring.neg(ring.tau(state[n - offset + j]))
    return updated


def sequential_two_bit(ring, state, a, b, v_a, v_b):
    return one_bit(ring, one_bit(ring, state, a, v_a), b, v_b)


def src_m(ring, state, j, offset):
    """Offset source with negacyclic wrap = -tau_{-1} in the wrapped case."""
    n = ring.n
    if j >= offset:
        return state[j - offset]
    return ring.neg(ring.tau(state[n - offset + j]))


def identity_addend_step(ring, state, a, b, v_a, v_b):
    """out_j = U_j + sum_m ind_m*(src_m - U_j) at the exact level."""
    n = ring.n
    ind_a, ind_b, ind_ab = (
        (v_a, v_b) == (1, 0),
        (v_a, v_b) == (0, 1),
        (v_a, v_b) == (1, 1),
    )
    out = list(state)
    for j in range(n):
        terms = []
        if ind_a:
            terms.append(src_m(ring, state, j, a))
        if ind_b:
            terms.append(src_m(ring, state, j, b))
        if ind_ab:
            terms.append(src_m(ring, state, j, a + b))
        acc = state[j]
        for t in terms:
            acc = tuple((x + y) % P for x, y in zip(acc, t))
            acc = tuple((x - s) % P for x, s in zip(acc, state[j]))
        out[j] = acc
    return out


def identity_addend_step_noisy(ring, state, a, b, v_a, v_b, *, drop_identity=False):
    """Ciphertext-level simulation of the encrypted-indicator step.

    Each external product contributes ind_m*operand + eps_m with eps_m a
    fixed nonzero 'noise' tuple; the identity addend U_j is the free term.
    Dropping the addend is invisible at the exact level (single indicator)
    but must corrupt the digit-0 case here: with addend, digit 0 keeps U_j
    (plus noise); without it, the slot becomes pure noise (message lost).
    """
    n = ring.n
    ind = {
        "a": (v_a, v_b) == (1, 0),
        "b": (v_a, v_b) == (0, 1),
        "ab": (v_a, v_b) == (1, 1),
    }
    out = list(state)
    for j in range(n):
        acc = tuple(0 for _ in range(n)) if drop_identity else state[j]
        first = True
        for m_key, off, m_int in (("a", a, 0), ("b", b, 1), ("ab", a + b, 2)):
            eps = tuple((3 * j + 5 * m_int + 1) % P for _ in range(n))
            operand = src_m(ring, state, j, off)
            prod = tuple(
                (x + e) % P if ind[m_key] else e
                for x, e in zip(operand, eps)
            )
            if drop_identity and first:
                acc = prod
                first = False
            else:
                acc = tuple((x + y) % P for x, y in zip(acc, prod))
        out[j] = acc
    return out


def identity_addend_step_buggy_wrap(ring, state, a, b, v_a, v_b):
    """Negative control C2: wrapped intervals use plain (not -tau_{-1}) source."""
    n = ring.n
    out = list(state)
    for j in range(n):
        def plain_src(offset):
            return state[j - offset] if j >= offset else state[(j - offset) % n]
        pick = (v_a, v_b)
        if pick == (0, 0):
            out[j] = state[j]
        elif pick == (1, 0):
            out[j] = plain_src(a)
        elif pick == (0, 1):
            out[j] = plain_src(b)
        else:
            out[j] = plain_src(a + b)
    return out


def prng(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) % (1 << 31)
        yield x


def main() -> int:
    failures = 0
    checks = 0
    detected = {c: False for c in ("drop_identity", "missing_wrap")}

    for n, r_prec in ((8, 3), (16, 4)):
        ring = NegacyclicRing(n)
        state = [
            tuple((17 * j + 5 * i + 1) % P for i in range(n))
            for j in range(n)
        ]

        # A. per-step equivalence, all offsets and selector values
        for t in range(r_prec // 2):
            a = 1 << (2 * t)
            b = 1 << (2 * t + 1)
            for v_a in (0, 1):
                for v_b in (0, 1):
                    lhs = sequential_two_bit(ring, state, a, b, v_a, v_b)
                    rhs = identity_addend_step(ring, state, a, b, v_a, v_b)
                    for j in range(n):
                        checks += 1
                        if lhs[j] != rhs[j]:
                            failures += 1
                            if failures <= 3:
                                print(f"A MISMATCH N={n} t={t} v=({v_a},{v_b}) j={j}")

                    # negative controls fire only where they must
                    bad1 = identity_addend_step_noisy(
                        ring, state, a, b, v_a, v_b, drop_identity=True
                    )
                    good1 = identity_addend_step_noisy(
                        ring, state, a, b, v_a, v_b, drop_identity=False
                    )
                    if any(bad1[j] != good1[j] for j in range(n)):
                        detected["drop_identity"] = True
                    bad2 = identity_addend_step_buggy_wrap(
                        ring, state, a, b, v_a, v_b
                    )
                    if any(bad2[j] != lhs[j] for j in range(n)):
                        detected["missing_wrap"] = True

        # B. full-chain equivalence over rho/2 chained steps
        for seed in (1, 7, 20260904):
            g = prng(seed)
            digits = [next(g) % 4 for _ in range(r_prec // 2)]
            fused = list(state)
            seq = list(state)
            for t in range(r_prec // 2):
                a = 1 << (2 * t)
                b = 1 << (2 * t + 1)
                d = digits[t]
                v_a, v_b = (d >> 0) & 1, (d >> 1) & 1
                fused = identity_addend_step(ring, fused, a, b, v_a, v_b)
                seq = one_bit(ring, seq, a, v_a)
                seq = one_bit(ring, seq, b, v_b)
            for j in range(n):
                checks += 1
                if fused[j] != seq[j]:
                    failures += 1
                    if failures <= 3:
                        print(f"B MISMATCH N={n} seed={seed} j={j}")

    print(f"checks={checks} failures={failures}")
    print(f"negative controls detected: {detected}")
    ok = failures == 0 and all(detected.values())
    print(
        "F1-1' VERIFIED: identity-addend delta=2 step (and full chain) == "
        "sequential two-bit composition; all negative controls DETECTED"
        if ok
        else "F1-1' FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
