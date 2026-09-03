#!/usr/bin/env sage
# E4 v4: portfolio on dell. Fixes vs v3:
#  - input key (binary {0,1} weight h) expressed as the mathematically
#    equivalent centered sparse secret ((-1,0), h): s -> s-1 shifts b by the
#    public A*1, exact same security; the {0,1} form breaks the attack code's
#    centered-lattice assumption (prob=0 -> rop=inf, as seen in v3).
#  - uSVP/dual via the old estimator's real entry points: primal_usvp,
#    dual_scale (drop_and_solve wrapping as in parameter_search).
import sys, time, logging
logging.disable(logging.WARNING)
sys.path.insert(0, '/home/delld/spz/dell-final-bench/hybrid_attacks_code')
from estimator import estimator as est
import hybrid_decoding as hd

q = 2**64
out = []

def hd_grid(name, n, sd, sigma_abs, m=2048):
    alpha = est.alphaf(float(sigma_abs), q, True)
    best = None; fails = 0; total = 0
    t0 = time.time()
    for beta in range(100, 451, 25):
        for tau in range(50, 401, 25):
            total += 1
            try:
                r = hd.hybrid_decoding_attack(n=n, alpha=alpha, q=q, m=m,
                                              secret_distribution=sd,
                                              beta=beta, tau=tau, mitm=True)
                rop = float(r["rop"].log(2)) if r["rop"] != oo else float("inf")
                if rop != float("inf") and (best is None or rop < best[0]):
                    best = (rop, beta, tau)
            except Exception:
                fails += 1
    if best:
        line = f"{name}: HD rop=2^{best[0]:.1f} (beta={best[1]}, tau={best[2]}) [fails {fails}/{total}]"
    else:
        line = f"{name}: HD ALL-FAILED/INF ({fails}/{total} exceptions)"
    print(line, flush=True); out.append(line)
    print(f"  [{time.time()-t0:.0f}s]", flush=True)

def usvp(name, n, sd, sigma_abs, m=2048):
    alpha = est.alphaf(float(sigma_abs), q, True)
    t0 = time.time()
    try:
        r = est.primal_usvp(n, alpha, q, secret_distribution=sd, m=m,
                            success_probability=0.99)
        line = f"{name}: usvp rop=2^{float(r['rop'].log(2)):.1f} beta={r.get('beta')}"
    except Exception as ex:
        line = f"{name}: usvp ERR {type(ex).__name__} {str(ex)[:100]}"
    print(line, f"[{time.time()-t0:.0f}s]", flush=True); out.append(line)

def dualdrop(name, n, sd, sigma_abs, m=2048):
    alpha = est.alphaf(float(sigma_abs), q, True)
    t0 = time.time()
    try:
        f = est.partial(est.drop_and_solve, est.dual, postprocess=True, decision=True)
        r = f(n, alpha, q, secret_distribution=sd, m=m)
        line = f"{name}: dual-hybrid rop=2^{float(r['rop'].log(2)):.1f} beta={r.get('beta')}"
    except Exception as ex:
        line = f"{name}: dual-hybrid ERR {type(ex).__name__} {str(ex)[:100]}"
    print(line, f"[{time.time()-t0:.0f}s]", flush=True); out.append(line)

for h in [39, 41, 42, 52]:
    hd_grid(f"inkey h={h}", 2048, ((-1, 0), h), 2.0**49)
    usvp(f"inkey h={h}", 2048, ((-1, 0), h), 2.0**49)
    dualdrop(f"inkey h={h}", 2048, ((-1, 0), h), 2.0**49)
for sx, sig in [("2^-50", 2.0**14), ("2^-39", 2.0**25)]:
    usvp(f"BSK sigma={sx}", 2048, ((-1, 1), 512), sig)
    dualdrop(f"BSK sigma={sx}", 2048, ((-1, 1), 512), sig)
print("=== E4V4 DONE ===", flush=True)
print("\n".join(out), flush=True)
