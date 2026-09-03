#!/usr/bin/env sage
# E4 v5a2: NEW lattice-estimator ONLY, fixed API (E.nd.* + Xs=/Xe=; no OLD path on sys.path)
import sys, time, logging
logging.disable(logging.WARNING)
sys.path.insert(0, "/home/delld/spz/dell-final-bench/lattice-estimator")
import estimator as E
from estimator import LWE
def P(l): print(l, flush=True)
P("loaded new estimator from " + E.__file__)

def try_sd(cands):
    for name, mk in cands:
        try:
            return name, mk()
        except Exception:
            continue
    return None, None

t_start = time.time()
def fmt(r):
    parts = []
    for k, v in r.items():
        if isinstance(v, dict) and "rop" in v and v["rop"] is not None:
            try:
                parts.append("%s=2^%.1f" % (k, float(v["rop"].log(2))))
            except Exception:
                pass
    return "; ".join(parts)

def run(name, cands, sigma_abs):
    sname, s = try_sd(cands)
    if s is None:
        P(name + " ERR no secret dist"); return
    try:
        params = LWE.Parameters(n=2048, q=2**64, Xs=s, Xe=E.nd.DiscreteGaussian(float(sigma_abs)))
    except Exception as ex:
        P("%s ERR params %s %s" % (name, type(ex).__name__, str(ex)[:120])); return
    try:
        t0 = time.time(); r = LWE.estimate.rough(params)
        P("%s[%s] rough: %s [%ds]" % (name, sname, fmt(r), time.time()-t0))
    except Exception as ex:
        P("%s rough ERR %s %s" % (name, type(ex).__name__, str(ex)[:120]))
    for alg, tag in [(LWE.primal_usvp, "usvp"), (LWE.dual_hybrid, "dual-hybrid")]:
        if tag == "dual-hybrid" and time.time() - t_start > 2700:
            P(name + " dual-hybrid SKIPPED (time budget)"); continue
        try:
            t0 = time.time(); r = alg(params)
            P("%s[%s] %s=2^%.1f [%ds]" % (name, sname, tag, float(r["rop"].log(2)), time.time()-t0))
        except Exception as ex:
            P("%s %s ERR %s %s" % (name, tag, type(ex).__name__, str(ex)[:120]))

for h in [39, 41, 42, 52]:
    run("inkey h=%d" % h, [("SparseBinary", lambda h=h: E.nd.SparseBinary(h))], 2.0**49)
for sx, sig in [("BSK 2^-50", 2.0**14), ("BSK 2^-39", 2.0**25)]:
    run(sx, [("SparseTernary256+256", lambda: E.nd.SparseTernary(256, 256)),
             ("SparseTernary512", lambda: E.nd.SparseTernary(512)),
             ("Ternary", lambda: E.nd.Ternary)], sig)
P("=== V5A2 DONE ===")
