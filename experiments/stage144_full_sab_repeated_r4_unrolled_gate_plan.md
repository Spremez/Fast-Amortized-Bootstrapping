# Stage144 Full SAB Repeated r4-Unrolled Gate Plan

Date: 2026-07-03

## Objective

Turn Stage143 one-run smoke into a repeated complete-SAB A/B gate for the r=4 r4-unrolled AVX512 path.

## Primary Endpoint

`T_bootstrap/r`, measured as `pvw_lane_avg_us` for generic active PVW and r4-unrolled active PVW.

## Gates

- repeated full-SAB correctness and timing;
- r4-unrolled final-output noise with multiple deterministic seeds;
- resource/key snapshot against repeated scalar SAB;
- promote only if speed, noise, and resource gates are all acceptable.
