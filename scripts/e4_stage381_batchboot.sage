#!/usr/bin/env sage
# Stage381 A4: re-evaluate BatchBoot (USENIX Sec'26) published parameters under
# our corrected attack portfolio -- new lattice-estimator arms (usvp +
# dual-hybrid) for their BSK layers (Tab 9) and input layers (Tab 10).
# Input-layer binding tier is the conditional-entropy T3' MC (run locally,
# results in repro/stage381_batchboot_reeval/).
import sys, time, logging
logging.disable(logging.WARNING)
sys.path.insert(0, "/home/delld/spz/dell-final-bench/lattice-estimator")
import estimator as E
from estimator import LWE
def P(l): print(l, flush=True)
P("loaded new estimator from " + E.__file__)

def fmt(r):
    parts = []
    for k, v in r.items():
        if isinstance(v, dict) and "rop" in v and v["rop"] is not None:
            try:
                parts.append("%s=2^%.1f" % (k, float(v["rop"].log(2))))
            except Exception:
                pass
    return "; ".join(parts)

def run(name, n, secret_dist, sigma_abs):
    P("== %s (n=%d, sigma=2^%.0f) ==" % (name, n, 64 - sigma_abs.log(2)))
    try:
        params = LWE.Parameters(n=n, q=2**64, Xs=secret_dist,
            Xe=E.nd.DiscreteGaussian(float(sigma_abs)))
    except Exception as ex:
        P("  params ERR %s %s" % (type(ex).__name__, str(ex)[:120])); return
    try:
        r = LWE.estimate.rough(params)
        P("  rough: %s" % fmt(r))
    except Exception as ex:
        P("  rough ERR %s" % str(ex)[:120])
    for alg, tag in [(LWE.primal_usvp, "usvp"), (LWE.dual_hybrid, "dual-hybrid")]:
        try:
            r = alg(params)
            P("  %s = 2^%.1f" % (tag, float(r["rop"].log(2))))
        except Exception as ex:
            P("  %s ERR %s %s" % (tag, type(ex).__name__, str(ex)[:120]))

P("=== BatchBoot BSK layers (Tab 9) ===")
# Boot2/4/6 BSK: h=512 sparse ternary, N=2048, sigma=2^-53
run("Boot2/4/6 BSK SparseTernary(512)", 2048, E.nd.SparseTernary(512), 2.0**11)
run("Boot2/4/6 BSK SparseTernary(256+256)", 2048, E.nd.SparseTernary(256, 256), 2.0**11)
# Boot8 BSK: h=512, N=4096, sigma=2^-56
run("Boot8 BSK SparseTernary(512)", 4096, E.nd.SparseTernary(512), 2.0**8)

P("=== BatchBoot input layers (Tab 9/10; sparse binary h) ===")
# sigma_abs = 2^64 * 2^-15 = 2^49 etc.
for nm, n, h, sexp in [("Boot2 in", 2048, 39, -15), ("Boot4 in", 2048, 42, -17),
                       ("Boot6 in", 4096, 33, -21), ("Boot8 in", 4096, 34, -24)]:
    run(nm, n, E.nd.SparseBinary(h), 2.0**(64 + sexp))

P("=== STAGE381 DONE ===")
