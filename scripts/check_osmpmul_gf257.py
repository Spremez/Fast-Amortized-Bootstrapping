#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GF(257) verdict on the ONE-SHOT MONOMIAL MPMUL hypothesis (stage398).

Hypothesis under test: the rho-level bit-decomposed butterfly of 686/Alg1
can be replaced by a single monomial-message move per gap step (selector
encrypts X^{v*unit} directly), removing the rho factor from per-message
cost. VERDICT: REFUTED -- and the correct semantic decomposition of the
butterfly move is established and machine-verified instead.

  M0  relabel + crossing-sigma_{-1} == scalar oracle   PASS (semantic
      theorem S1: the move is a pure relabel plus sigma_{-1} applied to
      contents crossing the array boundary; gap exponents never enter
      the phase -- gaps act by SELECTING which slots' a-values each row
      accumulates; the crossing signs are the negacyclic row signs)
  M1  uniform monomial move                            FAIL (negative
      result: gap moves are secret permutations; single-EP monomial
      messages only work for PUBLIC moves)
  M2  pure relabel (no monomial, no sign)              FAIL (control)

The packed r-input pipeline (interleave + U_a sub_a + bit butterfly with
Psi wrap correction) is verified separately by
scripts/check_rinput_homtr_gf257.py (C4: 2560/2560).
"""
import random
import sys

P = 257
D = 16          # ring dim (scalar oracle ring)
NIN = 8         # slots / input dim n
H_PARAM = 3
R_PREC = 2
B_PREC = 3
TWO_D = 2 * D

failures = []


def report(tag, ok, detail=""):
    line = f"[{'PASS' if ok else 'FAIL'}] {tag}" + (f" -- {detail}" if detail else "")
    print(line)
    if not ok:
        failures.append(line)


def fold_exp(e, dim):
    e %= 2 * dim
    if e < dim:
        return e, 1
    return e - dim, -1


def poly_zero(n):
    return [0] * n


def poly_rand(rng, n):
    return [rng.randrange(P) for _ in range(n)]


def monomial_mul(f, e, n):
    out = poly_zero(n)
    for i in range(n):
        if f[i] == 0:
            continue
        j, s = fold_exp(i + e, n)
        out[j] = (out[j] + s * f[i]) % P
    return out


def automorphism(f, w, n):
    out = poly_zero(n)
    for i in range(n):
        if f[i] == 0:
            continue
        j, s = fold_exp(w * i, n)
        out[j] = (out[j] + s * f[i]) % P
    return out


def torus2int(c_torus, prec_bits):
    v = (c_torus * (1 << prec_bits) + P // 2) // P
    return v % (1 << prec_bits)


def mod_switch(vec, prec_bits, offset_torus=0):
    return [torus2int((c + offset_torus) % P, prec_bits) for c in vec]


# ---------- oracle: bit butterfly (ground truth, mirrors the C code) --------

def mpmul_bits(p, gap, n_slots, n_ring, r_prec):
    two_n = 2 * n_ring
    for i in range(r_prec):
        power = 1 << i
        if (gap >> i) & 1:
            new = [None] * n_slots
            for j in range(power):
                new[j] = automorphism(p[n_slots - power + j], two_n - 1, n_ring)
            for j in range(power, n_slots):
                new[j] = p[j - power]
            p = new
    return p


def scalar_oracle(a_torus, b_torus, tv, gaps):
    prec_bits = TWO_D.bit_length() - 1
    off = P // (1 << (B_PREC + 1))
    a_bar = mod_switch(a_torus, prec_bits)
    b_bar = mod_switch(b_torus, prec_bits, off)
    acc = [monomial_mul(tv, b_bar[t], D) for t in range(NIN)]
    for step in range(H_PARAM):
        acc = mpmul_bits(acc, gaps[step], NIN, D, R_PREC)
        for t in range(NIN):
            acc[t] = monomial_mul(acc[t], a_bar[t], D)
    acc = mpmul_bits(acc, gaps[H_PARAM], NIN, D, R_PREC)
    return acc


# ---------- candidate moves under test --------------------------------------

def os_move_monomial(p, gap, n_slots, n_ring):
    """Hypothesis M1: uniform monomial X^{gap*unit} + relabel."""
    unit = (2 * n_ring) // n_slots
    new = [None] * n_slots
    for j in range(n_slots):
        new[(j + gap) % n_slots] = monomial_mul(
            p[j], (gap * unit) % (2 * n_ring), n_ring)
    return new


def os_move_cross(p, gap, n_slots, n_ring):
    """Semantic truth M0: relabel + sigma_{-1} on boundary crossers.
    NOTE: the crossing set depends on the SECRET gap -- this 'public'
    version is not implementable; the bit butterfly is its efficient
    encrypted implementation (impossibility corollary S2)."""
    two_n = 2 * n_ring
    new = [None] * n_slots
    for j in range(n_slots):
        if j + gap >= n_slots:
            new[(j + gap) % n_slots] = automorphism(p[j], two_n - 1, n_ring)
        else:
            new[(j + gap) % n_slots] = p[j]
    return new


def os_move_relabel(p, gap, n_slots, n_ring):
    """Control M2: pure relabel."""
    return [p[(j - gap) % n_slots] for j in range(n_slots)]


def pipeline(a_torus, b_torus, tv, gaps, move):
    prec_bits = TWO_D.bit_length() - 1
    off = P // (1 << (B_PREC + 1))
    a_bar = mod_switch(a_torus, prec_bits)
    b_bar = mod_switch(b_torus, prec_bits, off)
    acc = [monomial_mul(tv, b_bar[t], D) for t in range(NIN)]
    for step in range(H_PARAM):
        acc = move(acc, gaps[step], NIN, D)
        for t in range(NIN):
            acc[t] = monomial_mul(acc[t], a_bar[t], D)
    acc = move(acc, gaps[H_PARAM], NIN, D)
    return acc


def rand_key_gaps(rng):
    for _ in range(1000):
        pos = sorted(rng.sample(range(NIN), H_PARAM), reverse=True)
        prev, gaps, ok = NIN, [], True
        for c in pos:
            g = prev - c
            if g >= (1 << R_PREC):
                ok = False
                break
            gaps.append(g)
            prev = c
        if ok and 0 < prev < (1 << R_PREC):
            gaps.append(prev)
            if sum(gaps) == NIN:
                return pos, gaps
    raise RuntimeError("no valid key")


def check(move, tag, expect_equal):
    rng = random.Random(21)
    total, mism, first_diag = 0, 0, ""
    for _ in range(30):
        pos, gaps = rand_key_gaps(rng)
        a_t = [poly_rand(rng, 1)[0] for _ in range(NIN)]
        b_t = [poly_rand(rng, 1)[0] for _ in range(NIN)]
        tv = poly_rand(rng, D)
        oracle = scalar_oracle(a_t, b_t, tv, gaps)
        mine = pipeline(a_t, b_t, tv, gaps, move)
        for t in range(NIN):
            total += 1
            if mine[t] != oracle[t]:
                mism += 1
                if not first_diag:
                    first_diag = (f"slot{t} gaps={gaps} "
                                  f"got={mine[t][:4]} want={oracle[t][:4]}")
    equal = (mism == 0)
    good = equal == expect_equal
    report(f"{tag}: {total} cmp, mism {mism}"
           f" ({'equal' if equal else 'differs'})", good, first_diag)


def main():
    print(f"GF(257) OS-MPMUL verdict: n={NIN} d={D} h={H_PARAM} "
          f"r_prec={R_PREC}")
    check(os_move_cross, "M0 relabel+crossing-sigma_{-1} (semantic truth S1)",
          True)
    check(os_move_monomial,
          "M1 uniform monomial move (hypothesis: REFUTED)", False)
    check(os_move_relabel, "M2 pure relabel (control)", False)
    print()
    if failures:
        print(f"VERDICT: FAIL ({len(failures)} unexpected outcomes)")
        for line in failures:
            print("  " + line)
        sys.exit(1)
    print("VERDICT: ALL AS EXPECTED (S1 verified; OS-MPMUL refuted)")
    sys.exit(0)


if __name__ == "__main__":
    main()
