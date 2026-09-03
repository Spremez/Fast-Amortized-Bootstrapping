#!/usr/bin/env sage
# E4 v5a3: BSK layer with the HONEST alternating-sign model.
# Alternating ternary h=512 == support choice C(2048,512) + 1 global sign bit,
# same secret norm as binary -> model as SparseBinary(512) (shift is public).
import sys, time, logging
logging.disable(logging.WARNING)
sys.path.insert(0, "/home/delld/spz/dell-final-bench/lattice-estimator")
import estimator as E
from estimator import LWE
def P(l): print(l, flush=True)

for tag, sig in [("BSK-alt 2^-50", 2.0**14), ("BSK-alt 2^-51", 2.0**13), ("BSK-alt 2^-49", 2.0**15)]:
    try:
        params = LWE.Parameters(n=2048, q=2**64, Xs=E.nd.SparseBinary(512), Xe=E.nd.DiscreteGaussian(sig))
    except Exception as ex:
        P("%s ERR params %s %s" % (tag, type(ex).__name__, str(ex)[:120])); continue
    for alg, name in [(LWE.primal_usvp, "usvp"), (LWE.dual_hybrid, "dual-hybrid")]:
        try:
            t0 = time.time(); r = alg(params)
            P("%s [%s] = 2^%.1f [%ds]" % (tag, name, float(r["rop"].log(2)), time.time()-t0))
        except Exception as ex:
            P("%s %s ERR %s %s" % (tag, name, type(ex).__name__, str(ex)[:120]))
P("=== V5A3 DONE ===")
