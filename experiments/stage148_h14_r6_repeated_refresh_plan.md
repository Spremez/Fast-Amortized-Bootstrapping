# Stage148 H14 r=6 Repeated Refresh Plan

Date: 2026-07-03

## Objective

Refresh the preferred explicit H14 r=6 backend route on current head with repeated complete-SAB, final-output noise, and resource evidence.

## Metrics

- Primary latency metric: `T_bootstrap/r` from `pvw_lane_avg_us`.
- Same-backend comparison: backend FromDFT-add versus wrapper fused FromDFT-add.
- Baseline comparison: backend complete-SAB speedup against repeated scalar SAB.
- Correctness/noise: final-output multi-seed failure counts and noise gap.
- Resource: key bytes, keygen lane time, internal VmHWM, and `/usr/bin/time` max RSS.

## Boundary

Stage148 can support a promotion-policy review for the explicit H14 r=6 backend path. It cannot change defaults or establish paper-level novelty by itself.
