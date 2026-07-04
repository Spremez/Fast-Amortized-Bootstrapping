# Stage234 Experiment Plan

## Hypothesis

For binary `SET_4_5_2048`, r=2, exact dense PVW/MAT-SAB improves complete-SAB
`T_bootstrap/r` over r repeated scalar SAB executions under the same backend.

## Baseline And Metric

Baseline: repeated scalar SAB with the same `KEY`, `PARAM`, `FFT_LIB`, active
buffer flag, and AVX512 specialization flag. Primary metric: complete-SAB
`T_bootstrap/r` speedup.

## Gate

This stage requires 10 complete-SAB A/B runs, 20 deterministic noise seeds, and
resource/keygen/RSS for PVW and scalar repeated modes. Passing this stage
supports `SET_4_5_2048`, r=2, and completes `SET_4_5_2048` r=2/r=4
high-stat coverage only.
