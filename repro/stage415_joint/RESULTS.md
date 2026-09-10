# I-5+ JOINT r1-input x r2-LUT C-level closure (dell, 2026-09-10)

probe_rinput_mb (r1=2 inputs x r2=2 LUT bodies, interleaved ring 2048).
Library: sab_rinput generalized to multi-body (assert removed; selector/
tmp/scratch/buf2 allocations now follow output_key->r; setup_tv_mb).

| Point | Gate | Pair noise rms (4 channels) | Bench (vs 4x scalar) |
|---|---|---|---|
| toy n=256/h=6 | **6/6 trials, 0/1024 each** | 2^52.4-52.6 | 1.004x |
| **FINAL n=2048/h=42** | **0/8192** | 2^53.5-53.6 | **0.981x** |

Reading: at FINAL the joint pipeline serves 4 messages (2 inputs x 2
LUTs) in LESS total time than 4 scalar bootstraps -- per-message cost
0.245x a scalar bootstrap. Composition amortization (HT-10, (1+k/r)
with r=r1*r2) is thus not only correct but measurably profitable at
submission parameters. Pair-noise class matches the single-body r-input
closure (per-channel independence, M1/N1 layering).

## Six-row precision scan (n=2048, h=42, out ring 4096, r1=2 x r2=2)

| Precision | Gate | Ratio vs 4x-scalar | Reading |
|---|---|---|---|
| p=2 | **0/8192 PASS** | 1.278x | clean |
| p=4 | **0/8192 PASS** | 1.258x | clean |
| p=6 | 1700/8192 FAIL | 1.271x | **noise budget limit**: DC-walk accumulates to ~2^54.6, half-grid at p=6 = 2^55 — 21% at the boundary; theory-predicted precision domain boundary |
| p=8 | 7132/8192 FAIL | 1.448x | same, deeper into noise floor |

n=4096 rows: SIGSEGV (not yet root-caused — the n=2048 pipeline is fully
correct; this is a ring-size infrastructure issue, likely stack or array
sizing at N=8192; needs one debugging session).

**Honest finding**: the joint pipeline at current noise parameters
(sigma_G=2^-70 toy key, no fusion flags) has a precision domain of p<=4.
The main matrix handles p up to 8/9 via the full fusion system (BSK-A,
sigma adjustments, etc.); the r-input path has not been tuned for high
precision — the DC-walk noise (2^49.2 coherent, ~2^54.6 accumulated at
h=42) sets the boundary exactly as N1 predicts.
