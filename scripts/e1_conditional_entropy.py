#!/usr/bin/env python3
"""E1: conditional-entropy audit of the SAB key distributions (2026-09-02).

Facts from the implementation (verified in code):
  * RS_sparse_*_key rejection-samples the support until get_min_prec(key) <= t.
    get_min_prec computes the max downward gap r_max (scan from index N down,
    previous starts at N) and returns int(log2(r_max))+1; acceptance is thus
    r_max <= 2^t - 1 (t=7 -> <= 127).
  * Because rejection discards uniformly, the conditional support distribution
    is uniform on the accepted family, so the entropy loss is EXACTLY
    -log2(p_accept), with p_accept = P(max circular gap <= m) for a uniform
    h-subset of Z_N (m = 2^t - 1).
  * p_accept for a uniform h-subset equals the bounded-composition
    probability (gaps of a uniform h-subset ~ uniform composition of N into
    h positive parts):
      p = (1/C(N-1,h-1)) * sum_j (-1)^j C(h,j) C(N - j*m - 1, h - 1)
        (terms with N - j*m - 1 < h - 1 are zero)
  * ternary keys use ALTERNATING signs (gen_sparse_array: val *= -1):
    sign entropy 1 bit instead of h bits -> loss h-1 bits vs the
    independent-sign model.

Outputs: per-set conditioning loss, corrected T3' for the input-key
combinatorial tier, and the ternary-layer tier comparison.
"""
import math
from math import comb, log2

def p_accept(N: int, h: int, m: int) -> float:
    """P(all circular gaps <= m) for a uniform h-subset of Z_N (exact)."""
    total = comb(N - 1, h - 1)
    if total == 0:
        return 0.0
    s = 0
    for j in range(0, h + 1):
        top = N - j * m - 1
        if top < h - 1:
            break
        s += (-1) ** j * comb(h, j) * comb(top, h - 1)
    return s / total

def log2_binom(n: int, k: int) -> float:
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / math.log(2)

def main():
    import random
    random.seed(7)

    def get_min_prec_mc(positions, N):
        r_max = 0; previous = N
        for j in range(N):
            idx = N - j - 1
            if idx in positions:
                r_diff = previous - idx
                if r_max < r_diff: r_max = r_diff
                previous = idx
        return int(math.log2(r_max)) + 1 if r_max > 0 else 1

    print("=== E1a (impl-semantics MC, 20k samples; delta=7.38 to match recorded T3) ===")
    DELTA = 7.38
    print(f"{'N':>5} {'h':>4} {'t':>3} {'p_accept':>9} {'loss':>6} {'T3prime':>8} {'rho_typ':>7} {'EP cost':>8}")
    for (N, h, t) in [(2048, 39, 7), (2048, 41, 7), (2048, 41, 8), (2048, 42, 7),
                      (2048, 52, 7), (2048, 52, 8), (4096, 32, 8)]:
        acc = 0; tot = 20000; acc_r = []
        for _ in range(tot):
            pos = set(random.sample(range(N), h))
            rp = get_min_prec_mc(pos, N)
            if rp <= t:
                acc += 1; acc_r.append(rp)
        p = acc / tot
        loss = -log2(p) if p > 0 else float("inf")
        H = log2_binom(N, h)
        t3p = (H - loss - log2(N) - DELTA) / 2.0
        rho_typ = (sum(acc_r) / len(acc_r)) if acc_r else float("nan")
        epc = rho_typ * (h + 1) / (7.0 * 40)   # rel to h=39,rho=7 baseline
        print(f"{N:>5} {h:>4} {t:>3} {p:>9.4f} {loss:>6.2f} {t3p:>8.2f} {rho_typ:>7.2f} {epc:>8.2f}x")

    print()
    print("=== E1b: alternating-ternary entropy audit (output key h_out=512/2048) ===")
    N, h = 2048, 512
    H_ind = log2_binom(N, h) + h          # independent signs model
    H_alt = log2_binom(N, h) + 1          # alternating signs (implementation)
    print(f"  combinatorial tier, independent signs: {H_ind:.1f} bit")
    print(f"  combinatorial tier, alternating signs: {H_alt:.1f} bit  (loss {H_ind-H_alt:.1f} = h-1)")
    for (H, tag) in [(H_ind, "independent"), (H_alt, "alternating ")]:
        lam = (H - log2(N)) / 2.0
        print(f"  MITM-style bound ({tag}): lambda ~ {lam:.1f} bit")
    print("  lattice tier of this layer: ~117-128 bit (279 re-estimate) -> binding tier")
    print("  => alternating signs do NOT change the binding tier for h_out=512/2048;")
    print("     they must still be reported as the true distribution (1060 targets ternary).")

if __name__ == "__main__":
    main()

