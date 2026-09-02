#!/usr/bin/env sage
# E4 v3: full portfolio on dell (~/spz/dell-final-bench). Fixes:
#  - inkey format bug bypassed by sweeping hybrid_decoding_attack directly
#    (parameter_search's dual_scale pre-pass only sets m/beta_max and is what
#    raised the success_probability domain error on sparse-binary secrets)
#  - adds uSVP and dual tiers via the old estimator's top-level functions
import sys, time, logging
logging.disable(logging.WARNING)
sys.path.insert(0, '/home/delld/spz/dell-final-bench/hybrid_attacks_code')
from estimator import estimator as est
import hybrid_decoding as hd

q = 2**64
out = []

def hd_grid(name, n, sd, sigma_abs, m=2048):
    alpha = est.alphaf(float(sigma_abs), q, True)
    best = None
    t0 = time.time()
    for beta in range(100, 451, 25):
        for tau in range(50, 401, 25):
            try:
                r = hd.hybrid_decoding_attack(n=n, alpha=alpha, q=q, m=m,
                                              secret_distribution=sd,
                                              beta=beta, tau=tau, mitm=True)
                rop = float(r["rop"].log(2))
                if best is None or rop < best[0]:
                    best = (rop, beta, tau, r)
            except Exception:
                pass
    line = f"{name}: hybrid_decoding rop=2^{best[0]:.1f} beta={best[1]} tau={best[2]}" if best else f"{name}: HD FAILED"
    print(line, flush=True); out.append(line)
    print(f"  [{time.time()-t0:.0f}s]", flush=True)

def simple(name, fn, n, sd, sigma_abs, m=2048):
    alpha = est.alphaf(float(sigma_abs), q, True)
    t0 = time.time()
    try:
        r = fn(n, alpha, q, m=m, secret_distribution=sd)
        keys = {k: (f"2^{float(v.log(2)):.1f}" if hasattr(v, 'log') else v) for k, v in r.items() if k in ("rop", "beta", "d", "m")}
        line = f"{name}: {keys}"
    except Exception as ex:
        line = f"{name}: ERR {type(ex).__name__} {str(ex)[:120]}"
    print(line, f"[{time.time()-t0:.0f}s]", flush=True); out.append(line)

for h in [39, 41, 42, 52]:
    hd_grid(f"inkey h={h}", 2048, ((0, 1), h), 2.0**49)
for h in [39, 41, 42, 52]:
    simple(f"inkey h={h} usvp", est.usvp, 2048, ((0, 1), h), 2.0**49)
    simple(f"inkey h={h} dual", est.dual, 2048, ((0, 1), h), 2.0**49)
for sx, sig in [("2^-50", 2.0**14), ("2^-39", 2.0**25)]:
    simple(f"BSK sigma={sx} usvp", est.usvp, 2048, ((-1, 1), 512), sig)
    simple(f"BSK sigma={sx} dual", est.dual, 2048, ((-1, 1), 512), sig)
print("=== E4V3 DONE ===", flush=True)
print("\n".join(out), flush=True)
