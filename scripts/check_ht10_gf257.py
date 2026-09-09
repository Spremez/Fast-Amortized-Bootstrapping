#!/usr/bin/env python3
"""check_ht10_gf257.py -- I-5: machine adjudication of the HT-10
orthogonality theorem (r1-input x r2-LUT), built as a thin extension of
the PROVEN checker check_rinput_homtr_gf257 (imports its primitives).

Joint model (r2=2 bodies over the interleaved ring, per stage407 HT-10):
  - shared secret structure: same gaps, same input ciphertexts (a/b
    torus per input lane) across bodies -- the HT-10 setting (same
    inputs drive all LUTs);
  - per-body interleaved pipeline (plain embedding + Psi-corrected
    wraps + U_a with input-lane exponents, body-blind: identical ring
    maps on every body at the message level);
  - oracles: r1 x r2 = 4 independent scalar pipelines (input l, TV_j).
Layering note (recorded in stage412): the message-level joint check
adjudicates (S); the ciphertext-level body independence (shared mask,
block-diagonal selectors) is adjudicated by the C-level M1 gates
(r in {1..8}, 0-mismatch, six-row matrix + r-input gates).

Negative control: bare sigma_-1 wraps -> lane-1 mismatch expected.
"""
import random
import sys

sys.path.insert(0, "scripts")
from check_rinput_homtr_gf257 import (  # proven primitives
    N, D, NIN, H_PARAM, R_PREC, R_LANES, P,
    poly_rand, rand_key_gaps, scalar_pipeline, interleaved_pipeline,
    unpack_lane,
)

R2 = 2  # LUT/body lanes


def run_joint(seed, correct_wrap=True):
    rng = random.Random(seed)
    pos, gaps = rand_key_gaps(rng)
    inputs = [([poly_rand(rng, 1)[0] for _ in range(NIN)],
               [poly_rand(rng, 1)[0] for _ in range(NIN)])
              for _ in range(R_LANES)]
    tvs = [[poly_rand(rng, D) for _ in range(R2)] for _ in range(R_LANES)]
    f_emb = {0: 0, 1: 0}

    # oracles: (input lane l, LUT j)
    scalar = {(l, j): scalar_pipeline(inputs[l][0], inputs[l][1],
                                      tvs[l][j], gaps)
              for l in range(R_LANES) for j in range(R2)}

    # joint: per-body interleaved pipeline, shared gaps + inputs
    joint = [interleaved_pipeline(
                 [inputs[l][0] for l in range(R_LANES)],
                 [inputs[l][1] for l in range(R_LANES)],
                 [tvs[l][j] for l in range(R_LANES)],
                 gaps, f_emb, correct_wrap)
             for j in range(R2)]

    total = mism = 0
    first = ""
    for t in range(NIN):
        for l in range(R_LANES):
            for j in range(R2):
                got = unpack_lane(joint[j][t], l, f_emb)
                for q in range(D):
                    total += 1
                    if got[q] != scalar[(l, j)][t][q]:
                        mism += 1
                        if not first:
                            first = (f"slot{t} lane{l} body{j} coef{q}: "
                                     f"got {got[q]} want "
                                     f"{scalar[(l, j)][t][q]}")
    return total, mism, first


def main():
    print(f"HT-10 joint checker (GF(257)): N={N} r1={R_LANES} r2={R2} "
          f"d={D} in_N={NIN} h={H_PARAM} r_prec={R_PREC}")
    ok = True
    tot_all = mism_all = 0
    for seed in range(20):
        total, mism, _ = run_joint(seed, correct_wrap=True)
        tot_all += total
        mism_all += mism
        if mism:
            print(f"  seed {seed}: {mism}/{total} MISMATCH")
            ok = False
    print(f"C-JOINT (Psi): {tot_all - mism_all}/{tot_all} equal "
          f"{'PASS' if ok else 'FAIL'}")
    neg = any(run_joint(s, correct_wrap=False)[1] > 0 for s in range(5))
    print(f"C-JOINT-NEG (bare sigma_-1): fires = {neg} (expected True)")
    if not ok or not neg:
        print("HT10 CHECK: FAIL")
        return 1
    print("HT10 CHECK: ALL PASS -- joint r1 x r2 pipeline equals "
          "4 independent scalar oracles (all slots, all coefficients); "
          "negative control fires.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
