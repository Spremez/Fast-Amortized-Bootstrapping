#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay the dell gate's EXACT data (uint64 torus values) through both the
interleaved model and the scalar model in exact unsigned/signed 64-bit
semantics (no GF abstraction): find the first stage where they diverge and
the first C-vs-python divergence (stage-level mirrors of the diag).

Reads repro/rinput_gate_data.txt exported by probe_rinput_diag."""
import sys

M64 = (1 << 64) - 1

def s64(x):
    x &= M64
    return x - (1 << 64) if x >> 63 else x

class Ring:
    def __init__(self, n):
        self.n = n
    def mono(self, f, e):
        n = self.n
        out = [0] * n
        e %= 2 * n
        for i in range(n):
            if f[i] & M64:
                j = i + e
                if j >= 2 * n:
                    j -= 2 * n
                if j >= n:
                    out[j - n] = (out[j - n] - f[i]) & M64
                else:
                    out[j] = (out[j] + f[i]) & M64
        return out
    def auto(self, f, w):
        n = self.n
        out = [0] * n
        for i in range(n):
            if f[i] & M64:
                j = (w * i) % (2 * n)
                if j >= n:
                    out[j - n] = (out[j - n] - f[i]) & M64
                else:
                    out[j] = (out[j] + f[i]) & M64
        return out

def sigma_h(f):
    return [(-c) & M64 if i & 1 else c for i, c in enumerate(f)]

def add(f, g):
    return [(a + b) & M64 for a, b in zip(f, g)]

def rshift(f):
    # (c+1)>>1 unsigned (mirrors sab_rinput_rescale2)
    return [((c + 1) >> 1) & M64 for c in f]

def torus2int(c, prec):
    # mirror mosfhet: round(c * 2^prec / 2^64) mod 2^prec
    v = ((c + (1 << (63 - prec))) >> (64 - prec)) & ((1 << prec) - 1)
    return v

def main():
    lines = open('repro/rinput_gate_data.txt').read().splitlines()
    hdr = lines[0].split()
    N, d, n, h = int(hdr[1]), int(hdr[3]), int(hdr[5]), int(hdr[7])
    rp = int(hdr[9])
    gaps = [int(x) for x in lines[1].split()[1:]]
    vecs = {}
    for ln in lines[2:]:
        tag, vals = ln.split(None, 1)
        vecs[tag] = [int(x) & M64 for x in vals.split()]
    a0, b0, a1, b1 = vecs['a0'], vecs['b0'], vecs['a1'], vecs['b1']
    tv0, tv1 = vecs['tv0'], vecs['tv1']
    print(f"N={N} d={d} n={n} h={h} rp={rp} gaps={gaps}")

    two_d = 2 * d
    two_N = 2 * N
    off = 1 << 60  # b_prec = 3

    RN = Ring(N)
    RD = Ring(d)

    # scalar model (bit butterfly, ring d)
    ab = [torus2int(c, 11) for c in a0]
    bb = [torus2int((c + off) & M64, 11) for c in b0]
    acc_s = [RD.mono(tv0, bb[t]) for t in range(n)]
    # interleaved model (Psi + U_a, ring N)
    ab0 = ab
    ab1 = [torus2int(c, 11) for c in a1]
    bb1 = [torus2int((c + off) & M64, 11) for c in b1]
    acc_i = []
    for t in range(n):
        u0 = RD.mono(tv0, bb[t])
        u1 = RD.mono(tv1, bb1[t])
        packed = [0] * N
        for q in range(d):
            packed[2 * q] = u0[q]
            packed[1 + 2 * q] = u1[q]
        acc_i.append(packed)

    def psi(src):
        t = RN.auto(src, two_N - 1)
        sh = sigma_h(t)
        sp = add(t, sh)
        sm = [(a - b) & M64 for a, b in zip(t, sh)]
        out = sp[:]
        for i in range(N):
            if sm[i]:
                j = i + 2
                if j >= 2 * N:
                    j -= 2 * N
                if j >= N:
                    out[j - N] = (out[j - N] - sm[i]) & M64
                else:
                    out[j] = (out[j] + sm[i]) & M64
        return rshift(out)

    def sub_a(c, x0, x1):
        sh = sigma_h(c)
        sp = add(c, sh)
        sm = [(a - b) & M64 for a, b in zip(c, sh)]
        out = [0] * N
        for i in range(N):
            if sp[i]:
                j = i + 2 * x0
                j %= two_N
                if j >= N:
                    out[j - N] = (out[j - N] - sp[i]) & M64
                else:
                    out[j] = (out[j] + sp[i]) & M64
        for i in range(N):
            if sm[i]:
                j = i + 2 * x1
                j %= two_N
                if j >= N:
                    out[j - N] = (out[j - N] - sm[i]) & M64
                else:
                    out[j] = (out[j] + sm[i]) & M64
        return rshift(out)

    def compare(stage, masked=False):
        bad = 0
        first = None
        for t in range(n):
            for q in range(d):
                iv = acc_i[t][2 * q]     # lane0 coefficient q at even N-pos 2q
                sv = acc_s[t][q]
                if masked:
                    iv &= (1 << 63) - 1
                    sv &= (1 << 63) - 1
                if s64(iv - sv) != 0:
                    # tolerate nothing at plaintext level
                    if first is None:
                        first = (t, q, s64(iv), s64(sv))
                    bad += 1
        print(f"  [{stage}] lane0 mism {bad}/{n*d} (masked={masked})"
              + (f" first {first}" if first else ""))
        return bad

    compare("setup")
    for step in range(h + 1):
        g = gaps[step]
        for i in range(rp):
            pw = 1 << i
            if (g >> i) & 1:
                ns = [None] * n
                for j in range(pw):
                    ns[j] = RD.auto(acc_s[n - pw + j], two_d - 1)
                for j in range(pw, n):
                    ns[j] = acc_s[j - pw]
                acc_s = ns
                ni = [None] * n
                for j in range(pw):
                    ni[j] = psi(acc_i[n - pw + j])
                for j in range(pw, n):
                    ni[j] = acc_i[j - pw]
                acc_i = ni
        compare(f"bfly {step}", masked=True)
        if step < h:
            acc_s = [RD.mono(acc_s[t], ab[t]) for t in range(n)]
            for t in range(n):
                acc_i[t] = sub_a(acc_i[t], ab0[t], ab1[t])
            compare(f"suba {step}", masked=True)
    # final doubling then unmasked verdict
    for t in range(n):
        acc_i[t] = [(2 * c) & M64 for c in acc_i[t]]
    compare("FINAL2x", masked=False)

if __name__ == '__main__':
    main()
