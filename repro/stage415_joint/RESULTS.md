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
