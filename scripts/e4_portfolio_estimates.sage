#!/usr/bin/env sage
# E4 driver: hybrid-decoding estimates (merged CRYPTO'26 "Careful with the
# Ring!" artifact) on OUR layers.
import sys, time
sys.path.insert(0, '/home/luck/hybrid_attacks_code')
from estimator import estimator as est
import hybrid_decoding as hd

q = 2**64

def run(name, n, h_or_dist, sigma_abs, m):
    alpha = est.alphaf(float(sigma_abs), q, True)
    print(f"=== {name} (alpha={float(alpha):.3e}) ===", flush=True)
    try:
        t0 = time.time()
        res = hd.parameter_search(n, alpha, q, m, h_or_dist, mitm=True)
        print(f"[{name}] {time.time()-t0:.0f}s ->", res, flush=True)
    except Exception as ex:
        print(f"[{name}] ERR:", type(ex).__name__, str(ex)[:300], flush=True)

# input-key layer: sparse binary weight h, sigma = 2^-15 * q = 2^49
for h in [39, 41, 42, 52]:
    run(f"inkey h={h}", 2048, ((0, 1), h), 2.0**49, 2048)
# BSK layer: ternary weight 512, sigma_out sweep (2^-50 -> 2^-39)
run("BSK sigma=2^-50", 2048, ((-1, 1), 512), 2.0**14, 2048)
run("BSK sigma=2^-39", 2048, ((-1, 1), 512), 2.0**25, 2048)
print("E4 DONE", flush=True)
