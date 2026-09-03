#!/usr/bin/env sage
# E4 v5 FINAL: portfolio via the NEW lattice-estimator (dell clone) for
# usvp+dual(+bdd) on both layers, plus the old-code runs with fixed Cost
# printing. This closes the security table.
import sys, time, logging
logging.disable(logging.WARNING)
NEW = '/home/delld/spz/dell-final-bench/lattice-estimator'
OLD = '/home/delld/spz/dell-final-bench/hybrid_attacks_code'
sys.path.insert(0, NEW)
sys.path.insert(0, OLD)
out = []
def P(line):
    print(line, flush=True); out.append(line)

# ---------- new estimator ----------
import estimator as nest   # new API
P("new-estimator names: " + ",".join(n for n in dir(nest) if not n.startswith('_'))[:200])
from estimator import LWE, ND

def secret_dist(h, binary=True):
    cands = []
    if binary:
        cands += [("SparseBinary", lambda: nest.LDistribution.SparseBinary(h))]
    cands += [("SparseTernary", lambda: nest.LDistribution.SparseTernary(h))]
    for name, mk in cands:
        try:
            return name, mk()
        except Exception:
            continue
    raise RuntimeError("no sparse secret dist")

def run_new(name, h, sigma_abs, binary=True):
    try:
        sname, sd = secret_dist(h, binary)
        params = LWE.Parameters(n=2048, q=2**64,
                                alpha=nest.alphaf(float(sigma_abs), 2**64, True),
                                secret=sd)
        t0 = time.time()
        res = LWE.estimate.rough(params)   # usvp + dual(rough) fast pass
        line = f"{name} [new,{sname}] rough: " + "; ".join(
            f"{k}=2^{float(v['rop'].log(2)):.1f}" for k, v in res.items() if 'rop' in v)
        P(line + f" [{time.time()-t0:.0f}s]")
        t0 = time.time()
        try:
            res2 = LWE.estimate(params, deny_list=("arora-gb", "bkw"))
            line2 = f"{name} [new] full: " + "; ".join(
                f"{k}=2^{float(v['rop'].log(2)):.1f}" for k, v in res2.items() if 'rop' in v)
            P(line2 + f" [{time.time()-t0:.0f}s]")
        except Exception as ex:
            P(f"{name} [new] full ERR {type(ex).__name__} {str(ex)[:120]}")
    except Exception as ex:
        P(f"{name} [new] ERR {type(ex).__name__} {str(ex)[:150]}")

# ---------- old code (fixed printing) ----------
from estimator import estimator as oest
import hybrid_decoding as ohd

def run_old_usvp(name, n, sd, sigma_abs, m=2048):
    try:
        alpha = oest.alphaf(float(sigma_abs), 2**64, True)
        r = oest.primal_usvp(n, alpha, 2**64, secret_distribution=sd, m=m,
                             success_probability=0.99)
        P(f"{name} [old] usvp=2^{float(r['rop'].log(2)):.1f} beta={r['beta']}")
    except Exception as ex:
        P(f"{name} [old] usvp ERR {type(ex).__name__} {str(ex)[:100]}")

def run_old_dualdrop(name, n, sd, sigma_abs, m=2048):
    try:
        alpha = oest.alphaf(float(sigma_abs), 2**64, True)
        f = oest.partial(oest.drop_and_solve, oest.dual, postprocess=True, decision=True)
        r = f(n, alpha, 2**64, secret_distribution=sd, m=m)
        P(f"{name} [old] dual-hybrid=2^{float(r['rop'].log(2)):.1f} beta={r['beta']}")
    except Exception as ex:
        P(f"{name} [old] dual-hybrid ERR {type(ex).__name__} {str(ex)[:100]}")

for h in [39, 41, 42, 52]:
    run_new(f"inkey h={h}", h, 2.0**49, binary=True)
    run_old_usvp(f"inkey h={h}", 2048, ((-1, 0), h), 2.0**49)
for sx, sig in [("2^-50", 2.0**14), ("2^-39", 2.0**25)]:
    run_new(f"BSK sigma={sx}", 512, sig, binary=False)  # ternary w=512
    run_old_usvp(f"BSK sigma={sx}", 2048, ((-1, 1), 512), sig)
    run_old_dualdrop(f"BSK sigma={sx}", 2048, ((-1, 1), 512), sig)
P("=== E4V5 DONE ===")
P("\n".join(out))
