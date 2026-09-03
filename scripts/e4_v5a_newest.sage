#!/usr/bin/env sage
# E4 v5a: NEW lattice-estimator ONLY (own process; the old artifact's package
# shares the name 'estimator' and cannot coexist).
import sys, time, logging
logging.disable(logging.WARNING)
sys.path.insert(0, '/home/delld/spz/dell-final-bench/lattice-estimator')
import estimator as E
names = [n for n in dir(E) if not n.startswith('_')]
print("names:", ",".join(names)[:300], flush=True)
from estimator import LWE
out = []
def P(l): print(l, flush=True); out.append(l)

def sd(h, binary):
    tries = []
    if binary:
        tries += [("SparseBinary", lambda: E.LDistribution.SparseBinary(h))]
    tries += [("SparseTernary", lambda: E.LDistribution.SparseTernary(h)),
              ("Ternary", lambda: E.LDistribution.Ternary)]
    for name, mk in tries:
        try: return name, mk()
        except Exception: continue
    raise RuntimeError("no secret dist")

def run(name, h, sigma_abs, binary=True):
    try:
        sname, s = sd(h, binary)
        params = LWE.Parameters(n=2048, q=2**64,
                                alpha=E.alphaf(float(sigma_abs), 2**64, True),
                                secret=s)
        t0 = time.time()
        r = LWE.estimate.rough(params)
        P(f"{name}[{sname}] rough: " + "; ".join(
            f"{k}=2^{float(v['rop'].log(2)):.1f}" for k, v in r.items() if isinstance(v, dict) and 'rop' in v)
          + f" [{time.time()-t0:.0f}s]")
        t0 = time.time()
        try:
            r2 = LWE.estimate(params, deny_list=("arora-gb", "bkw"))
            P(f"{name}[{sname}] full: " + "; ".join(
                f"{k}=2^{float(v['rop'].log(2)):.1f}" for k, v in r2.items() if isinstance(v, dict) and 'rop' in v)
              + f" [{time.time()-t0:.0f}s]")
        except Exception as ex:
            P(f"{name} full ERR {type(ex).__name__} {str(ex)[:120]}")
    except Exception as ex:
        P(f"{name} ERR {type(ex).__name__} {str(ex)[:150]}")

for h in [39, 41, 42, 52]:
    run(f"inkey h={h}", h, 2.0**49, binary=True)
for sx, sig in [("BSK 2^-50", 2.0**14), ("BSK 2^-39", 2.0**25)]:
    run(sx, 512, sig, binary=False)
P("=== V5A DONE ===")
