# Stage111 r=6 Fulltile Repeated Gate

Date: 2026-07-03

## Decision

`PASS_STAGE111_R6_FULLTILE_REPEATED_NEGATIVE_NOT_PROMOTED`

Stage111 repeats the r=6 tile4/fulltile complete-SAB comparison. It is a
routing gate, not a final paper claim.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage111_inputs_available | PASS | tile4_summary;fulltile_summary | True;True | Both repeated complete-SAB summaries are available. |
| stage111_correctness | PASS | all_correct | True | All repeated runs passed correctness. |
| stage111_repetition_count | PASS | runs_per_variant | 3 | At least 3 runs are required for this routing gate. |
| stage111_fullsab_timing | NEGATIVE_OR_NEUTRAL | tile4_pvw_mean/fulltile_pvw_mean;speedup_ratio | 0.974;1.019 | Ratio above 1 means fulltile is faster than tile4. |
| stage111_decision | PASS_STAGE111_R6_FULLTILE_REPEATED_NEGATIVE_NOT_PROMOTED | promotion_policy |  | fulltile does not beat tile4 in repeated complete-SAB means. |

## Comparison

| variant | runs | correct | PVW mean us | PVW stddev us | PVW lane mean us | speedup mean | speedup stddev |
|---|---:|---|---:|---:|---:|---:|---:|
| tile4 | 3 | True | 42219780.667 | 231381.658 | 7036630.111 | 1.376 | 0.013 |
| fulltile | 3 | True | 43336939.000 | 1646101.902 | 7222823.167 | 1.402 | 0.041 |
| ratio_fulltile_vs_tile4 | 3 | True | 0.974 |  | 0.974 | 1.019 |  |