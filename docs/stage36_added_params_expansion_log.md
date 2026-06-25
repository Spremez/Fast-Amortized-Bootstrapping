# Stage 36 Added-Parameter Expansion Log

Date: 2026-06-26

## Purpose

This log summarizes the optional Stage 36 added-binary parameter
campaign. It extends the Stage 26 added-parameter evidence from
5-run/5-seed support to the pre-registered 10-run/20-seed budget for
`SET_4_5_2048` and `SET_2_3_4096`, r=2/4.

The result does not change scalar SAB or `sab_pvw_*` code and does not
upgrade non-binary, all-parameter, novelty, theorem-level citation, or
hardware-counter claims.

## Decision

`PASS_ADDED_PARAM_10RUN_20SEED`

## Performance Summary

| param | r | runs | status | pvw_mean_us | scalar_repeated_mean_us | mean_speedup | min_speedup | max_speedup | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 2 | 10 | PASS | 14446172.200 | 18568382.800 | 1.285700 | 1.209000 | 1.346000 | PASS_ADDED_PARAM_10RUN |
| SET_4_5_2048 | 4 | 10 | PASS | 27062846.900 | 36533500.500 | 1.350700 | 1.314000 | 1.397000 | PASS_ADDED_PARAM_10RUN |
| SET_2_3_4096 | 2 | 10 | PASS | 25280021.400 | 31197761.300 | 1.235100 | 1.156000 | 1.286000 | PASS_ADDED_PARAM_10RUN |
| SET_2_3_4096 | 4 | 10 | PASS | 55536748.700 | 74704036.600 | 1.346200 | 1.264000 | 1.569000 | PASS_ADDED_PARAM_10RUN |

## Performance Statistics

| param | r | runs | mean_speedup | stddev_speedup | ci95_low_t | ci95_high_t | decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 2 | 10 | 1.285700 | 0.041801 | 1.255799 | 1.315601 | PASS_ADDED_PARAM_10RUN |
| SET_4_5_2048 | 4 | 10 | 1.350700 | 0.030166 | 1.329122 | 1.372278 | PASS_ADDED_PARAM_10RUN |
| SET_2_3_4096 | 2 | 10 | 1.235100 | 0.034317 | 1.210553 | 1.259647 | PASS_ADDED_PARAM_10RUN |
| SET_2_3_4096 | 4 | 10 | 1.346200 | 0.084263 | 1.285926 | 1.406474 | PASS_ADDED_PARAM_10RUN |

## Supplemental Performance Samples

| param | r | sample_id | speedup_vs_scalar_repeated | decision |
| --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | perf_SET_2_3_4096_r4_runs9_topup:run_7 | 1.318 | SUPPLEMENTAL_NOT_IN_PRIMARY_10RUN |
| SET_2_3_4096 | 4 | perf_SET_2_3_4096_r4_runs9_topup:run_8 | 1.328 | SUPPLEMENTAL_NOT_IN_PRIMARY_10RUN |

## Noise Summary

| param | r | seeds | points | pvw_failures | scalar_failures | pair_failures | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | avg_pvw_minus_scalar_log2 | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 2 | 20 | 81920 | 0 | 0 | 0 | -0.348 | 0.464 | -0.047700 | PASS_ADDED_PARAM_20SEED |
| SET_4_5_2048 | 4 | 20 | 163840 | 0 | 0 | 0 | -0.478 | 0.365 | -0.077350 | PASS_ADDED_PARAM_20SEED |
| SET_2_3_4096 | 2 | 20 | 163840 | 0 | 0 | 0 | -0.562 | 0.665 | -0.041350 | PASS_ADDED_PARAM_20SEED |
| SET_2_3_4096 | 4 | 20 | 327680 | 0 | 0 | 0 | -0.299 | 0.584 | 0.029600 | PASS_ADDED_PARAM_20SEED |

## Interpretation

The added binary parameters now have local 10-run complete-SAB
performance evidence and 20-seed final-output noise evidence for
r=2 and r=4 under `spqlios_avx512` with the promoted active-buffer
PVW/MAT-SAB path. This strengthens binary parameter-generalization
evidence, but it is still not a claim for non-binary branches or all
possible parameter sets.
