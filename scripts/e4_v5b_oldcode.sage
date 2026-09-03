#!/usr/bin/env sage
# E4 v5b: OLD merged-paper artifact ONLY (own process): recover the numbers
# lost to the print bug in v4 (BSK usvp/dual-hybrid; inkey usvp for record).
import sys, logging
logging.disable(logging.WARNING)
sys.path.insert(0, '/home/delld/spz/dell-final-bench/hybrid_attacks_code')
from estimator import estimator as est
import hybrid_decoding as hd
q = 2**64
out = []
def P(l): print(l, flush=True); out.append(l)

def usvp(name, n, sdist, sigma_abs, m=2048):
    try:
        alpha = est.alphaf(float(sigma_abs), q, True)
        r = est.primal_usvp(n, alpha, q, secret_distribution=sdist, m=m,
                            success_probability=0.99)
        P(f"{name} usvp=2^{float(r['rop'].log(2)):.1f} beta={r['beta']}")
    except Exception as ex:
        P(f"{name} usvp ERR {type(ex).__name__} {str(ex)[:100]}")

def dualdrop(name, n, sdist, sigma_abs, m=2048):
    try:
        alpha = est.alphaf(float(sigma_abs), q, True)
        f = est.partial(est.drop_and_solve, est.dual, postprocess=True, decision=True)
        r = f(n, alpha, q, secret_distribution=sdist, m=m)
        P(f"{name} dual-hybrid=2^{float(r['rop'].log(2)):.1f} beta={r['beta']}")
    except Exception as ex:
        P(f"{name} dual-hybrid ERR {type(ex).__name__} {str(ex)[:100]}")

for h in [39, 41, 42, 52]:
    usvp(f"inkey h={h}", 2048, ((-1, 0), h), 2.0**49)
for sx, sig in [("BSK 2^-50", 2.0**14), ("BSK 2^-39", 2.0**25)]:
    usvp(sx, 2048, ((-1, 1), 512), sig)
    dualdrop(sx, 2048, ((-1, 1), 512), sig)
P("=== V5B DONE ===")
