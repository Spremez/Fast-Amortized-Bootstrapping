# Sparse-key entropy / orbit / MITM ceiling computations for 2025/686 keys.
# Deterministic: pure stdlib (math only), runnable under `python -I -S bounds.py`.
# Sources of the transcribed constants (see sparse_key_lambda_bounds.md):
#   [686]  Guimaraes & Pereira, "Fast amortized bootstrapping with small keys and
#          polynomial noise overhead", ACM CCS 2025 / ePrint 2025/686,
#          Tables 3 and 4 (q = 2^64; lambda already adjusted by delta).
#   [279]  Hou, Jiang, Ogilvie, "Careful with the Ring! Concrete Hardness Gaps
#          Between LWE and MLWE", CRYPTO 2026 (ePrint 2026/279), Table 8 rows [42].
# Run: python -I -S bounds.py   (also runs under plain `python bounds.py`)

from math import lgamma, log2, ceil, pi, e

LN2 = log(2) if False else 0.6931471805599453  # not used; keep -I -S import surface minimal


def lbinom(n: int, k: int) -> float:
    """log2 of C(n,k) via lgamma (exact to double precision for n <= 2^20)."""
    if k < 0 or k > n:
        return float("-inf")
    return (lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)) / LN2


def key_entropy(n: int, h: int, w: int) -> float:
    """log2 of the number of fixed-Hamming-weight secrets.
    w = alphabet size per nonzero coefficient (binary {0,1}: w=1; ternary {-1,0,1}: w=2)."""
    return lbinom(n, h) + h * log2(w)


def report_key(name, dist, n, h, sigma_torus_exp, delta, lambda_claimed_686, est_279):
    """One row of the 686-key analysis.
    sigma_torus_exp: exponent c such that torus sigma = 2^-c (686 tables give q/sigma).
    delta: rejection-sampling entropy loss subtracted by 686 (0 if none published).
    est_279: (no_mitm, mitm_h1, mitm_h2) bits from [279] Table 8, or None.
    """
    w = 1 if dist == "binary" else 2
    H = key_entropy(n, h, w)
    orbit = log2(n)                       # rotation-group quotient ceiling (free action)
    H_eff = H - orbit
    tiers = {
        "T1_exhaustive_quotient": H_eff - delta,          # rigorous ceiling (attack = orbit-enumeration)
        "T2_mitm_plain":         (H - delta) / 2,          # May CRYPTO'21, no rotations
        "T3_mitm_rotational":    (H_eff - delta) / 2,      # + 279 Heuristic-2 decomposition
    }
    print(f"{name} ({dist}, n=2^{ceil(log2(n)):.0f}, h={h}, sigma=2^-{sigma_torus_exp}, delta={delta:.2f})")
    print(f"  raw entropy H = log2 C(n,h) + h log2 w      = {H:9.2f} bits")
    print(f"  rotation-orbit loss (ceiling log2 n)        = {orbit:9.2f} bits")
    for k, v in tiers.items():
        print(f"  security ceiling {k:26s}<= {v:9.2f} bits")
    margin = tiers["T3_mitm_rotational"] - lambda_claimed_686
    print(f"  686 claimed lambda (estimator+CHHS19-delta) = {lambda_claimed_686:9.2f} bits")
    print(f"  margin T3-ceiling minus claim              = {margin:9.2f} bits"
          f"  {'(OK)' if margin >= 0 else '(CLAIM EXCEEDS PURE-COMBINATORIAL CEILING)'}")
    if est_279 is not None:
        print(f"  279 RotPrimalHybrid  no-MitM/H1/H2        = "
              f"{est_279[0]:.1f} / {est_279[1]:.1f} / {est_279[2]:.1f} bits")
        print(f"  drop below 686 claim (H2 vs claim)        = {lambda_claimed_686 - est_279[2]:9.2f} bits"
              f"  (orbit ceiling caps rotational part at {orbit:.2f})")
        if delta > 0:
            print(f"  OPEN if 279 ignored 686 delta: H2-delta  = {est_279[2] - delta:9.2f} bits")
    print()


def min_weight_for_lambda(n: int, lam: float, w: int, delta: float, tier: int) -> int:
    """Smallest h such that the given security-ceiling tier reaches lam bits.
    tier 1: exhaustive-on-quotient  (rigorous):      H - log2 n - delta >= lam
    tier 2: plain MITM (May'21):                     (H - delta)/2     >= lam
    tier 3: rotational MITM (279 Heuristic 2):       (H - log2 n - delta)/2 >= lam
    """
    lo, hi = 1, n // 2
    while lo < hi:
        mid = (lo + hi) // 2
        H = key_entropy(n, mid, w)
        val = H - log2(n) - delta if tier == 1 else (
              (H - delta) / 2 if tier == 2 else (H - log2(n) - delta) / 2)
        if val >= lam:
            hi = mid
        else:
            lo = mid + 1
    return lo


def asymptotic_check(n: int, h: int) -> float:
    """Entropy-approximation sanity: h*log2(e*n/h) (+ h*log2 w outside)."""
    return h * log2(e * n / h)


def main() -> None:
    print("=" * 78)
    print("A. 686 key instances (Tables 3+4 of [686]; q=2^64; torus sigma)")
    print("=" * 78)
    # name, dist, n, h, sigma exp (torus), delta, lambda_686, (279 no-MitM, H1, H2)|None
    keys = [
        # ---- HW-reducing (input-side) keys, Table 4 [686]; T1..T6 re-estimated in [279] Table 8 [42]
        ("B1", "binary", 2048, 39, 15, 7.37, 128.9, None),
        ("B2", "binary", 2048, 42, 17, 6.16, 129.9, None),
        ("B3", "binary", 4096, 33, 21, 0.66, 128.1, None),
        ("B4", "binary", 8192, 27, 21, 1.30, 127.9, None),
        ("B5", "binary", 4096, 34, 24, 0.58, 129.1, None),
        ("B6", "binary", 8192, 28, 24, 1.15, 130.6, None),
        ("T1", "ternary", 2048, 35, 15, 9.34, 128.3, (133.6, 122.8, 118.4)),
        ("T2", "ternary", 2048, 38, 17, 7.81, 129.9, (134.4, 124.0, 119.7)),
        ("T3", "ternary", 4096, 30, 21, 0.92, 127.8, (138.1, 122.1, 117.3)),
        ("T4", "ternary", 8192, 25, 21, 1.63, 127.9, (148.3, 126.7, 121.2)),
        ("T5", "ternary", 4096, 32, 24, 0.73, 127.9, (138.3, 122.7, 118.1)),
        ("T6", "ternary", 8192, 26, 23, 1.46, 129.8, (149.1, 127.8, 122.4)),
        # ---- repacking + bootstrapping keys, Table 3 [686] (no rejection sampling => delta=0)
        ("RPC1", "ternary", 2048, 256, 44, 0.0, 143.1, None),
        ("RPC2", "ternary", 4096, 256, 44, 0.0, 277.2, None),
        ("RPC3", "ternary", 8192, 256, 44, 0.0, 454.1, None),
        ("FBS1", "ternary", 2048, 512, 50, 0.0, 128.9, None),
        ("FBS2", "ternary", 8192, 512, 51, 0.0, 511.8, None),
    ]
    for k in keys:
        report_key(*k)

    print("=" * 78)
    print("B. Minimum Hamming weight h* for a lambda-bit target (n fixed)")
    print("=" * 78)
    for n in (2048, 4096, 8192, 2 ** 14, 2 ** 17):
        for w, dist in ((1, "binary"), (2, "ternary")):
            row = [n, dist]
            for tier, tname in ((1, "exh.quot"), (2, "MITM"), (3, "MITM+rot")):
                row.append(min_weight_for_lambda(n, 128.0, w, 0.0, tier))
            print(f"n={n:6d} {dist:7s}: h*(lam=128, tier1 rigorous)={row[2]:4d}  "
                  f"h*(tier2 May-MITM)={row[3]:4d}  h*(tier3 279-MITM)={row[4]:4d}")
    print()
    print("Note: tier1 is a proven ceiling (attack exists at 2^(H-log2 n-delta));")
    print("      tiers 2-3 assume collision/MitM decomposition heuristics.")

    print()
    print("=" * 78)
    print("C. Entropy-approximation sanity (h*log2(e*n/h) vs exact, binary)")
    print("=" * 78)
    for n, h in ((2048, 39), (2048, 35), (4096, 33), (8192, 26)):
        exact = lbinom(n, h)
        approx = asymptotic_check(n, h)
        print(f"n={n:5d} h={h:3d}: exact log2 C = {exact:7.2f}  approx h*log2(en/h) = {approx:7.2f}"
              f"  (diff {approx - exact:+5.2f})")

    print()
    print("=" * 78)
    print("D. 686 asymptotic-regime check (their Sec 6.1: h = O(lambda/log lambda))")
    print("=" * 78)
    print("Entropy H(h) = h*log2(e*n*w/h). 686's aggressive regime n=lam*log^k(lam),")
    print("h = c*lam/log2(lam) gives H = c*(k+1)*lam*loglog(lam)/log2(lam) = o(lam),")
    print("hence lambda-bit security FAILS asymptotically for ANY constant c (tier 2/3).")
    for lam in (128, 256):
        for k in (0, 1, 2):
            n = lam * (2 ** k)  # crude n = lam*log^k(lam) stand-in: lam*2^k
            h = 2 * lam / log2(lam)
            H = key_entropy(int(n), int(h), 2)
            print(f"lam={lam} k={k}: h=2lam/log2(lam)={h:5.1f} n={n:6d} -> H={H:7.2f} "
                  f"({'>= 2*lam OK' if H >= 2 * lam else '< 2*lam FAILS tier3'})")


if __name__ == "__main__":
    main()
