#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GF(257) mechanical verification for r-input batching + Hom-Tr (M-HT.7/8).

Checker obligations (theory_checks/stage396_rinput_homtr_math.md section 9):
  C1  H = {sigma_{1+2d*l}} subgroup-ness; R^H == A (invariants = even support)
  C2  trace extraction  T_H(X^{-lambda} f) = r * m_lambda
  C3  sigma_{-1} action on plain vs negation-symmetric (f-) embeddings
      (plain: lane1 gets -Rev = Y^{-1} J  -- NEGATIVE control;
       f-emb: lane-uniform J              -- the fix)
  C4  full-chain simulation: interleaved pipeline (f-embedding) vs
      2 x scalar oracle pipelines (ring dim d, granularity 2d),
      faithful mirror of the C code semantics (setup / butterfly with
      sigma_{-1} wrapped moves / sub_a / final butterfly), all slots,
      all lane coefficients. Plain embedding arm = expected FAIL control.
  C4-multi  the definitive test with TWO DISTINCT inputs under one key.
  C5  U_a identity  sum_{w in H} P_w sigma_w(Phi_f(m)) = r Phi_f(L_a(m))
  C6  exact per-step division by r (GF(257) inverse) algebra check

All arithmetic in GF(257); polynomials are canonical coefficient lists
(exponents in [0,dim), X^dim = -1 fold). Exponent arithmetic mod 2*dim.
"""
import random
import sys

P = 257
N = 16          # interleaved ring dimension (out ring)
R_LANES = 2     # r
D = N // R_LANES  # 8: per-lane ring dimension
NIN = 8         # in_N: number of accumulator slots / input ring dim
H_PARAM = 3     # sparse key weight
R_PREC = 2      # gap bit-width (gaps < 4)
B_PREC = 3
TWO_N = 2 * N
TWO_D = 2 * D   # per-lane exponent granularity (== scalar oracle 2N')
INV2 = (P + 1) // 2  # 129

# H = {1, 1+N} for r=2 (fixed subgroup, independent of a)
H_GENS = [1, 1 + N]

failures = []


def report(tag, ok, detail=""):
    line = f"[{'PASS' if ok else 'FAIL'}] {tag}" + (f" -- {detail}" if detail else "")
    print(line)
    if not ok:
        failures.append(line)


def fold_exp(e, dim):
    """canonical position + sign for exponent e mod 2*dim (X^dim = -1)."""
    e %= 2 * dim
    if e < dim:
        return e, 1
    return e - dim, -1


def poly_zero(n=N):
    return [0] * n


def poly_rand(rng, n=N):
    return [rng.randrange(P) for _ in range(n)]


def monomial_mul(f, e, n=N):
    """f * X^e in Z_p[X]/(X^n+1); e in [0,2n)."""
    out = poly_zero(n)
    for i in range(n):
        if f[i] == 0:
            continue
        j, s = fold_exp(i + e, n)
        out[j] = (out[j] + s * f[i]) % P
    return out


def automorphism(f, w, n=N):
    """sigma_w: X^i -> X^{w*i mod 2n}."""
    out = poly_zero(n)
    for i in range(n):
        if f[i] == 0:
            continue
        j, s = fold_exp(w * i, n)
        out[j] = (out[j] + s * f[i]) % P
    return out


def poly_add(f, g):
    return [(a + b) % P for a, b in zip(f, g)]


def poly_scale(f, c):
    return [(c * a) % P for a in f]


def poly_mul(f, g, n=N):
    """negacyclic convolution in dim n."""
    out = poly_zero(n)
    for i in range(n):
        if f[i] == 0:
            continue
        for j in range(n):
            k, s = fold_exp(i + j, n)
            out[k] = (out[k] + s * f[i] * g[j]) % P
    return out


def torus2int(c_torus, prec_bits):
    """mirror C torus2int on GF(257) torus: round(c * 2^prec / P) mod 2^prec."""
    v = (c_torus * (1 << prec_bits) + P // 2) // P
    return v % (1 << prec_bits)


def mod_switch(vec, prec_bits, offset_torus=0):
    return [torus2int((c + offset_torus) % P, prec_bits) for c in vec]


def lane_monomial_mul(u, e):
    """Y^e * u inside A = Z[Y]/(Y^d+1) (dim D, exponents mod 2D)."""
    out = poly_zero(D)
    for q in range(D):
        if u[q] == 0:
            continue
        j, s = fold_exp(q + e, D)
        out[j] = (out[j] + s * u[q]) % P
    return out


# ---------------- scalar oracle pipeline (ring dim n_ring, granularity 2n_ring)

def mpmul(p, gap, n_slots, n_ring, r_prec):
    """mirror RGSW_monomial_mul at message level; conditional moves driven by
    gap bits (selector bit=1: move; wrapped sources get sigma_{-1})."""
    two_n = 2 * n_ring
    for i in range(r_prec):
        power = 1 << i
        if (gap >> i) & 1:
            new = [None] * n_slots
            for j in range(power):  # wrapped: p'[j] = sigma_{-1}(p[n-power+j])
                new[j] = automorphism(p[n_slots - power + j], two_n - 1, n_ring)
            for j in range(power, n_slots):  # direct: p'[j] = p[j-power]
                new[j] = p[j - power]
            p = new
    return p


def scalar_pipeline(a_torus, b_torus, tv, gaps, n_slots=NIN, n_ring=D):
    """scalar SAB message path (mirror sparse_amortized_bootstrap.c):
    setup X^{bbar}.TV ; h x (MPMul(gap) ; sub_a X^{+abar}) ; final MPMul."""
    prec_bits = (2 * n_ring).bit_length() - 1
    off = P // (1 << (B_PREC + 1))
    a_bar = mod_switch(a_torus, prec_bits)
    b_bar = mod_switch(b_torus, prec_bits, off)
    acc = [monomial_mul(tv, b_bar[t], n_ring) for t in range(n_slots)]
    for step in range(H_PARAM):
        acc = mpmul(acc, gaps[step], n_slots, n_ring, R_PREC)
        for t in range(n_slots):  # sub_a: X^{+a_bar[t]} (mul_by_xai)
            acc[t] = monomial_mul(acc[t], a_bar[t], n_ring)
    acc = mpmul(acc, gaps[H_PARAM], n_slots, n_ring, R_PREC)
    return acc


# ---------------- interleaved packing helpers

def pack_f(u_lanes, f):
    """Phi_f((u_l)) = sum_l X^{l + r f(l)} u_l(X^r) as dim-N canonical poly."""
    out = poly_zero(N)
    for lam in range(R_LANES):
        for q in range(D):
            if u_lanes[lam][q] == 0:
                continue
            j, s = fold_exp(lam + R_LANES * (q + f[lam]), N)
            out[j] = (out[j] + s * u_lanes[lam][q]) % P
    return out


def unpack_lane(content, lam, f):
    """inverse of pack placement: lane lam's D coefficients."""
    u = [0] * D
    for q in range(D):
        j, s = fold_exp(lam + R_LANES * (q + f[lam]), N)
        u[q] = (s * content[j]) % P
    return u


def J_action(u):
    """J(u)(Y) = u(Y^{-1}) in A: J(u)_0 = u_0, J(u)_q = -u_{d-q} (1<=q<d)."""
    out = [u[0] % P] + [(-u[D - q]) % P for q in range(1, D)]
    return out


def homtr_weights(a_lanes, f):
    """P_w = sum_lam X^{(lam + r f(lam))(1-w) + r*a_lam} for w in H."""
    ws = []
    for w in H_GENS:
        p_w = poly_zero(N)
        for lam in range(R_LANES):
            e = ((lam + R_LANES * f[lam]) * (1 - w) + R_LANES * a_lanes[lam]) % TWO_N
            p_w = poly_add(p_w, monomial_mul([1] + [0] * (N - 1), e, N))
        ws.append(p_w)
    return ws


def sub_a_homtr_interleaved(content, a_lanes, f):
    """U_a = sum_{w in H} P_w sigma_w(content), then exact /r in GF(257).
    Target: lane lam -> Y^{+a_lam} u_lam (matches scalar mul_by_xai(+a))."""
    total = poly_zero(N)
    for w, p_w in zip(H_GENS, homtr_weights(a_lanes, f)):
        total = poly_add(total, poly_mul(p_w, automorphism(content, w, N), N))
    return poly_scale(total, INV2)


def wrap_microcorrect(content, f):
    """Psi = U_(0,+1) o sigma_{-1}: the wrapped-source correction that makes
    the induced action lane-uniform J (parity obstruction: sigma_{-1} alone
    twists lane 1 by Y^{-(2f+1)}, always odd; the micro-Hom-Tr multiplies
    lane 1 back by Y^{+1}). Reuses the SAME sigma_{1+N} KS key as sub_a."""
    return sub_a_homtr_interleaved(automorphism(content, TWO_N - 1, N),
                                   [0, 1], f)


def mpmul_interleaved(p, gap, f, correct_wrap):
    """butterfly for the interleaved accumulator (dim N). Wrapped sources get
    Psi (with correction) or bare sigma_{-1} (negative control)."""
    new = list(p)
    for i in range(R_PREC):
        power = 1 << i
        if (gap >> i) & 1:
            new = [None] * NIN
            for j in range(power):
                src = p[NIN - power + j]
                new[j] = wrap_microcorrect(src, f) if correct_wrap \
                    else automorphism(src, TWO_N - 1, N)
            for j in range(power, NIN):
                new[j] = p[j - power]
            p = new
    return new


def interleaved_pipeline(a_torus_lanes, b_torus_lanes, tvs, gaps, f,
                         correct_wrap=True):
    """interleaved message path: setup Phi_f, h x (shared MPMul-with-Psi ;
    Hom-Tr sub_a), final MPMul; dim-N ring."""
    prec_bits = TWO_D.bit_length() - 1
    off = P // (1 << (B_PREC + 1))
    a_bars = [mod_switch(a, prec_bits) for a in a_torus_lanes]
    b_bars = [mod_switch(b, prec_bits, off) for b in b_torus_lanes]
    acc = []
    for t in range(NIN):
        u_lanes = [lane_monomial_mul(tvs[lam], b_bars[lam][t])
                   for lam in range(R_LANES)]
        acc.append(pack_f(u_lanes, f))
    for step in range(H_PARAM):
        acc = mpmul_interleaved(acc, gaps[step], f, correct_wrap)
        for t in range(NIN):
            acc[t] = sub_a_homtr_interleaved(
                acc[t], [a_bars[lam][t] for lam in range(R_LANES)], f)
    acc = mpmul_interleaved(acc, gaps[H_PARAM], f, correct_wrap)
    return acc


# ---------------- key generation (gap constraints like C keygen)

def rand_key_gaps(rng):
    """descending positions with gaps in [1,2^R_PREC), final gap < 2^R_PREC."""
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


# ---------------- checks

def check_c1():
    hs = {(1 + 2 * D * l) % TWO_N for l in range(R_LANES)}
    closed = all(((w1 * w2) % TWO_N) in hs for w1 in hs for w2 in hs)
    report("C1a H closed under multiplication mod 2N",
           closed and len(hs) == R_LANES)
    rng = random.Random(1)
    ok = True
    for _ in range(50):
        fpoly = poly_rand(rng)
        inv = all(automorphism(fpoly, w) == fpoly for w in hs)
        odd_zero = all(fpoly[i] == 0 for i in range(1, N, 2))
        if inv != odd_zero:
            ok = False
            break
    report("C1b R^H == A (invariants = even support)", ok)


def check_c2():
    rng = random.Random(2)
    ok = True
    for _ in range(50):
        fpoly = poly_rand(rng)
        lanes = [[fpoly[lam + R_LANES * q] for q in range(D)]
                 for lam in range(R_LANES)]
        for lam in range(R_LANES):
            tr = poly_zero(N)
            for w in H_GENS:
                tr = poly_add(tr,
                              automorphism(monomial_mul(fpoly, TWO_N - lam, N), w, N))
            exp = poly_zero(N)
            for q in range(D):
                j, s = fold_exp(R_LANES * q, N)  # m_lam(X^r) support
                exp[j] = (exp[j] + s * R_LANES * lanes[lam][q]) % P
            if tr != exp:
                ok = False
                break
        if not ok:
            break
    report("C2 trace extraction T_H(X^{-lam} f) = r*m_lam", ok)


def check_c3():
    rng = random.Random(3)
    ok_plain_neg, ok_psi = True, True
    f_plain = {0: 0, 1: 0}
    for _ in range(50):
        us = [poly_rand(rng, D) for _ in range(R_LANES)]
        # negative fact: bare sigma_{-1} on plain embedding = (J, -Rev)
        lhs_p = automorphism(pack_f(us, f_plain), TWO_N - 1, N)
        rev1 = [(-us[1][D - 1 - q]) % P for q in range(D)]  # -Rev(u_1)
        rhs_p = pack_f([J_action(us[0]), rev1], f_plain)
        if lhs_p != rhs_p:
            ok_plain_neg = False
        # corrected lemma: Psi = U_(0,1) o sigma_{-1} = lane-uniform J
        lhs = wrap_microcorrect(pack_f(us, f_plain), f_plain)
        rhs = pack_f([J_action(u) for u in us], f_plain)
        if lhs != rhs:
            ok_psi = False
    report("C3b plain embedding: sigma_{-1} = (J, -Rev)  [negative fact]",
           ok_plain_neg)
    report("C3c Psi = U_(0,1) o sigma_{-1} = lane-uniform J  [the fix]",
           ok_psi)


def check_c5():
    rng = random.Random(5)
    ok = True
    f_emb = {0: 0, 1: -1}
    for _ in range(50):
        us = [poly_rand(rng, D) for _ in range(R_LANES)]
        a_lanes = [rng.randrange(TWO_D) for _ in range(R_LANES)]
        u_out = sub_a_homtr_interleaved(pack_f(us, f_emb), a_lanes, f_emb)
        exp_lanes = [lane_monomial_mul(us[lam], a_lanes[lam])
                     for lam in range(R_LANES)]
        if u_out != pack_f(exp_lanes, f_emb):
            ok = False
            break
    report("C5 U_a identity (f-embedding, random a)", ok)


def check_c6():
    rng = random.Random(7)
    f_emb = {0: 0, 1: -1}
    c = poly_rand(rng)
    a_lanes = [3, 11]
    total = poly_zero(N)
    for w, p_w in zip(H_GENS, homtr_weights(a_lanes, f_emb)):
        total = poly_add(total, poly_mul(p_w, automorphism(c, w, N), N))
    u = sub_a_homtr_interleaved(c, a_lanes, f_emb)
    ok = poly_scale(u, R_LANES) == total and INV2 * R_LANES % P == 1
    report("C6 exact division by r=2 (U_a = pre-sum * inv2)", ok)


def check_c4(f_emb, tag, expect_pass, correct_wrap=True):
    rng = random.Random(11)
    total_cmp, mism, wrap_seen, first_diag = 0, 0, False, ""
    for _ in range(20):
        pos, gaps = rand_key_gaps(rng)
        for g in gaps:
            for i in range(R_PREC):
                if (g >> i) & 1:
                    wrap_seen = True
        inputs = [([poly_rand(rng, 1)[0] for _ in range(NIN)],
                   [poly_rand(rng, 1)[0] for _ in range(NIN)])
                  for _ in range(R_LANES)]
        tvs = [poly_rand(rng, D) for _ in range(R_LANES)]
        scalar = [scalar_pipeline(inputs[lam][0], inputs[lam][1], tvs[lam], gaps)
                  for lam in range(R_LANES)]
        interleaved = interleaved_pipeline(
            [inputs[lam][0] for lam in range(R_LANES)],
            [inputs[lam][1] for lam in range(R_LANES)],
            tvs, gaps, f_emb, correct_wrap)
        for t in range(NIN):
            for lam in range(R_LANES):
                got = unpack_lane(interleaved[t], lam, f_emb)
                for q in range(D):
                    total_cmp += 1
                    if got[q] != scalar[lam][t][q]:
                        mism += 1
                        if not first_diag:
                            first_diag = (f"trial slot{t} lane{lam} coef{q}: "
                                          f"got {got[q]} want {scalar[lam][t][q]} "
                                          f"gaps={gaps}")
    good = (mism == 0) if expect_pass else (mism > 0)
    report(f"C4[{tag}] interleaved vs scalar oracle, 2 distinct inputs "
           f"[{total_cmp} cmp, mism {mism}, wrapped-moves seen: {wrap_seen}]",
           good, first_diag if mism else
           ("(expected FAIL but zero mismatch)" if not expect_pass else ""))


def main():
    print(f"GF(257) r-input Hom-Tr checker: N={N} r={R_LANES} d={D} "
          f"in_N={NIN} h={H_PARAM} r_prec={R_PREC}")
    check_c1()
    check_c2()
    check_c3()
    check_c5()
    check_c6()
    check_c4({0: 0, 1: 0}, "plain-embedding, bare sigma_{-1} (negative ctrl)",
             expect_pass=False, correct_wrap=False)
    check_c4({0: 0, 1: 0}, "plain-embedding + Psi micro-correction",
             expect_pass=True, correct_wrap=True)
    print()
    if failures:
        print(f"VERDICT: FAIL ({len(failures)} failing items)")
        for line in failures:
            print("  " + line)
        sys.exit(1)
    print("VERDICT: ALL PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
