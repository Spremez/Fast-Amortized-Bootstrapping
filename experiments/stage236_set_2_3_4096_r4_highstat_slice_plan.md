# Stage236 Experiment Plan

## Hypothesis

For binary `SET_2_3_4096`, r=4, exact dense PVW/MAT-SAB improves complete-SAB
`T_bootstrap/r` over r repeated scalar SAB executions under the same backend.

## Baseline And Metric

Baseline: repeated scalar SAB with the same `KEY`, `PARAM`, `FFT_LIB`,
`MAT_TRGSW_AVX512_SMALLR_SPECIALIZED`, and active-buffer flag. Primary metric:
complete-SAB `T_bootstrap/r`, not isolated MAT external-product latency.

## Gate

This stage requires 10 complete-SAB A/B runs, 20 deterministic noise seeds, and
resource/keygen/RSS rows for PVW and scalar repeated modes. Passing this stage
closes the selected binary added-parameter matrix with Stage233/234/235.
