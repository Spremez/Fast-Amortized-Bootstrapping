#!/usr/bin/env python3
"""sq_security_preflight_279.py -- stage356 sparse-key security preflight.

Eprint 2026/279 (Ogilvie, "On the Concrete Hardness Gap Between MLWE and
LWE") shows that ring coefficient isometries let hybrid attacks amortize
lattice preprocessing across many guesses, making them strictly stronger
than the MLWE->LWE translation used by standard estimators: gaps of up to
15 bits for sparse-secret RLWE (the FHE regime this repository lives in)
and 2-3 bits for dense ML-KEM-class parameters.

This repository's SAB keys are sparse binary (input) and sparse ternary
(output), so the 279 correction applies to every parameter set. The
scale-quantized SAB (sab_sq, the eprint 2025/1711 squared-gadget external
product) suppresses the key-noise term of the blind rotation by
Q^2/T = 2^(2q-64), which converts a q-lowering below the stock Bg = 23
into sigma-headroom: 2*(23-q) bits of tolerable log2(sigma) uplift at
fixed blind-rotation noise. The stock scalar SAB has no such knob (its
operand scale is pinned to the fixed gadget base 2^23), so under 279 the
stock sets must re-harden via h or N (both slower).

Model contract (deliberately relative, not a re-implementation of the
lattice estimator):
  * Baseline bits default to the 686 design target (128-bit classical)
    for every SET_* family; override with --baseline-bits.
  * The 279 gap is a conservative worst case interpolated by secret
    density: 15 bits at h/n <= 0.05 down to 2 bits at h/n >= 0.5.
  * The sigma elasticity (security bits per log2(sigma)) is exposed as a
    range: s_lo = 0.5 (conservative) and s_hi = 1.0 (optimistic); the
    required log2(sigma) uplift for the gap is gap/s.
  * SQ absorption capacity = 2*(23-q) bits, bounded below by the noise
    floor q >= b_prec + 10 (rounding floor of the rescale chain).

Usage:
  python scripts/sq_security_preflight_279.py \
      [--baseline-bits 128] [--out repro/stage356_sq_scale_sab/security_preflight_279.csv]
"""

import argparse
import csv
import math
import os

# Parameter sets mirroring main.c test_sab / test_sab_tern (binary line).
# (name, in_N, h_in, log2 sigma_in, out_N, h_out, log2 sigma_out, msg_prec)
PARAM_SETS = [
    ("SET_2_3_2048", 2048, 39, -15, 2048, 512, -50, 3),
    ("SET_2_3_4096", 4096, 32, -15, 2048, 512, -50, 3),
    ("SET_2_3_8192", 8192, 25, -15, 2048, 512, -50, 3),
    ("SET_4_5_2048", 2048, 42, -17, 2048, 512, -50, 5),
    ("SET_4_5_4096", 4096, 34, -18, 2048, 512, -50, 5),
    ("SET_4_5_8192", 8192, 26, -18, 2048, 512, -50, 5),
    ("SET_6_7_4096", 4096, 33, -21, 2048, 512, -50, 7),
    ("SET_6_7_8192", 8192, 27, -21, 2048, 512, -50, 7),
    ("SET_8_9_4096", 4096, 34, -24, 8192, 512, -51, 9),
    ("SET_8_9_8192", 8192, 28, -24, 8192, 512, -51, 9),
    ("SET_8_9_HIGH_FR", 8192, 28, -22, 4096, 512, -50, 9),
]

STOCK_BG_BIT = 23      # scalar SAB gadget base (accumulator scale)
S_ELASTIC_LO = 0.5     # conservative bits per log2(sigma)
S_ELASTIC_HI = 1.0     # optimistic bits per log2(sigma)


def gap_279_bits(n: int, h: int) -> float:
    """Conservative 2026/279 isometry-hybrid correction by density."""
    density = h / float(n)
    if density <= 0.05:
        return 15.0
    if density >= 0.5:
        return 2.0
    return 15.0 - (density - 0.05) / 0.45 * 13.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-bits", type=float, default=128.0,
                    help="design security of the SET_* families (686 paper)")
    ap.add_argument("--out", default=os.path.join(
        "repro", "stage356_sq_scale_sab", "security_preflight_279.csv"))
    args = ap.parse_args()

    rows = []
    for (name, in_N, h_in, log_sig_in, out_N, h_out, log_sig_out, b_prec) in PARAM_SETS:
        for side, n, h, log_sig in (
            ("input", in_N, h_in, log_sig_in),
            ("output", out_N, h_out, log_sig_out),
        ):
            gap = gap_279_bits(n, h)
            adj = args.baseline_bits - gap
            uplift_lo = gap / S_ELASTIC_LO   # log2(sigma) needed, conservative
            uplift_hi = gap / S_ELASTIC_HI
            # SQ absorption: q bounded by the blind-rotation rounding floor
            q_floor = b_prec + 10
            max_absorb = 2 * max(0, STOCK_BG_BIT - q_floor)
            full_cons = max_absorb >= uplift_lo
            full_opt = max_absorb >= uplift_hi
            q_choice = max(q_floor, STOCK_BG_BIT - int(math.ceil(uplift_lo / 2.0)))
            rows.append({
                "set": name,
                "side": side,
                "N": n,
                "h": h,
                "density": round(h / float(n), 4),
                "log2_sigma": log_sig,
                "baseline_bits": args.baseline_bits,
                "gap_279_bits": round(gap, 1),
                "adjusted_bits": round(adj, 1),
                "uplift_log2sigma_conservative": round(uplift_lo, 1),
                "uplift_log2sigma_optimistic": round(uplift_hi, 1),
                "sq_q_floor_noise": q_floor,
                "sq_max_absorb_bits": max_absorb,
                "sq_q_recommended": q_choice,
                "sq_absorbs_full_gap": "yes" if full_cons else (
                    "optimistic_only" if full_opt else "NO"),
                "stock_absorbs_full_gap": "NO (fixed Bg=23 operand scale)",
            })

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    hdr = ("set", "side", "N", "h", "dens", "gap279", "adj", "upliftC",
           "absorb", "q_rec", "full?")
    print("%-16s %-6s %5s %4s %5s %6s %6s %6s %6s %5s %s" % hdr)
    for r in rows:
        print("%-16s %-6s %5d %4d %5.2f %6.1f %6.1f %6.1f %6d %5d %s" % (
            r["set"], r["side"], r["N"], r["h"], r["density"],
            r["gap_279_bits"], r["adjusted_bits"],
            r["uplift_log2sigma_conservative"], r["sq_max_absorb_bits"],
            r["sq_q_recommended"], r["sq_absorbs_full_gap"]))
    print("\nwrote %s (baseline %.0f bits, elasticity %.1f..%.1f bits/log2sigma)"
          % (args.out, args.baseline_bits, S_ELASTIC_LO, S_ELASTIC_HI))


if __name__ == "__main__":
    main()
