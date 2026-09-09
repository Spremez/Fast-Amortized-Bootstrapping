#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduce the dell gate's exact parameter SHAPE in GF(257):
n=256 slots, N=2048 interleaved ring, d=1024 lanes, h=6, r_prec=7,
gaps = [30, 57, 36, 24, 18, 5, 86] (the dell key).

If the interleaved(Psi) pipeline != scalar oracle here, the bug is in the
semantics at this shape (multi-bit gaps); if equal, the bug is C-level.
P_w are 2-monomial sums -> all ops O(N) (no general polynomial mult)."""
import random
import sys

P = 257
N = 2048
R_LANES = 2
D = N // R_LANES   # 1024
NIN = 256
H_PARAM = 6
R_PREC = 7
B_PREC = 3
TWO_N = 2 * N
TWO_D = 2 * D
INV2 = (P + 1) // 2
GAPS = [30, 57, 36, 24, 18, 5, 86]


def fold(e, dim):
    e %= 2 * dim
    return (e, 1) if e < dim else (e - dim, -1)


def mono(f, e, dim):
    out = [0] * dim
    for i in range(dim):
        if f[i]:
            j, s = fold(i + e, dim)
            out[j] = (out[j] + s * f[i]) % P
    return out


def auto(f, w, dim):
    out = [0] * dim
    for i in range(dim):
        if f[i]:
            j, s = fold(w * i, dim)
            out[j] = (out[j] + s * f[i]) % P
    return out


def add(f, g):
    return [(a + b) % P for a, b in zip(f, g)]


def sigma_h(f):
    return [(-c) % P if i & 1 else c for i, c in enumerate(f)]


def torus2int(c, prec):
    return ((c * (1 << prec) + P // 2) // P) % (1 << prec)


def scalar_oracle(a_t, b_t, tv):
    prec = TWO_D.bit_length() - 1
    off = P // (1 << (B_PREC + 1))
    ab = [torus2int(c, prec) for c in a_t]
    bb = [torus2int((c + off) % P, prec) for c in b_t]
    acc = [mono(tv, bb[t], D) for t in range(NIN)]
    for step in range(H_PARAM + 1):
        g = GAPS[step]
        for i in range(R_PREC):
            pw = 1 << i
            if (g >> i) & 1:
                new = [None] * NIN
                for j in range(pw):
                    new[j] = auto(acc[NIN - pw + j], TWO_D - 1, D)
                for j in range(pw, NIN):
                    new[j] = acc[j - pw]
                acc = new
        if step < H_PARAM:
            for t in range(NIN):
                acc[t] = mono(acc[t], ab[t], D)
    return acc


def psi(src):
    """Psi = U_(0,1) o sigma_{-1}: (t + sh t) + Y (t - sh t), /2, all O(N)."""
    t = auto(src, TWO_N - 1, N)
    sh = sigma_h(t)
    sp = add(t, sh)
    sm = [(a - b) % P for a, b in zip(t, sh)]
    out = sp[:]
    for i in range(N):
        if sm[i]:
            j, s = fold(i + 2, N)
            out[j] = (out[j] + s * sm[i]) % P
    return [(c * INV2) % P for c in out]


def sub_a(c, a0, a1):
    sh = sigma_h(c)
    sp = add(c, sh)
    sm = [(a - b) % P for a, b in zip(c, sh)]
    out = [0] * N
    for i in range(N):
        if sp[i]:
            j, s = fold(i + 2 * a0, N)
            out[j] = (out[j] + s * sp[i]) % P
    for i in range(N):
        if sm[i]:
            j, s = fold(i + 2 * a1, N)
            out[j] = (out[j] + s * sm[i]) % P
    return [(x * INV2) % P for x in out]


def pack(u0, u1):
    out = [0] * N
    for q in range(D):
        j, s = fold(2 * q, N)
        out[j] = (out[j] + s * u0[q]) % P
        j2, s2 = fold(1 + 2 * q, N)
        out[j2] = (out[j2] + s2 * u1[q]) % P
    return out


def unpack(c, lam):
    u = [0] * D
    for q in range(D):
        j, s = fold(lam + 2 * q, N)
        u[q] = (s * c[j]) % P
    return u


def interleaved(a0t, b0t, a1t, b1t, tv0, tv1):
    prec = TWO_D.bit_length() - 1
    off = P // (1 << (B_PREC + 1))
    ab0 = [torus2int(c, prec) for c in a0t]
    bb0 = [torus2int((c + off) % P, prec) for c in b0t]
    ab1 = [torus2int(c, prec) for c in a1t]
    bb1 = [torus2int((c + off) % P, prec) for c in b1t]
    acc = []
    for t in range(NIN):
        u0 = mono(tv0, bb0[t], D)
        u1 = mono(tv1, bb1[t], D)
        acc.append(pack(u0, u1))
    for step in range(H_PARAM + 1):
        g = GAPS[step]
        for i in range(R_PREC):
            pw = 1 << i
            if (g >> i) & 1:
                new = [None] * NIN
                for j in range(pw):
                    new[j] = psi(acc[NIN - pw + j])
                for j in range(pw, NIN):
                    new[j] = acc[j - pw]
                acc = new
        if step < H_PARAM:
            for t in range(NIN):
                acc[t] = sub_a(acc[t], ab0[t], ab1[t])
    return acc


def main():
    rng = random.Random(99)
    trials = 2
    total = mism = 0
    first = ""
    for _ in range(trials):
        a0 = [rng.randrange(P) for _ in range(NIN)]
        b0 = [rng.randrange(P) for _ in range(NIN)]
        a1 = [rng.randrange(P) for _ in range(NIN)]
        b1 = [rng.randrange(P) for _ in range(NIN)]
        tv0 = [rng.randrange(P) for _ in range(D)]
        tv1 = [rng.randrange(P) for _ in range(D)]
        s0 = scalar_oracle(a0, b0, tv0)
        s1 = scalar_oracle(a1, b1, tv1)
        il = interleaved(a0, b0, a1, b1, tv0, tv1)
        for t in range(NIN):
            g0 = unpack(il[t], 0)
            g1 = unpack(il[t], 1)
            for q in range(D):
                total += 1
                if g0[q] != s0[t][q] or g1[q] != s1[t][q]:
                    mism += 1
                    if not first:
                        first = f"slot{t} lane{0 if g0[q] != s0[t][q] else 1} q{q}"
    print(f"gate-shape repro: {total} cmp, mism {mism}"
          + (f" first {first}" if first else ""))
    print("VERDICT:", "SEMANTIC DIVERGENCE AT GATE SHAPE" if mism else
          "EQUAL AT GATE SHAPE (bug is C-level)")


if __name__ == "__main__":
    main()
