# Stage110 r=6 Fulltile Complete-SAB Gate

Date: 2026-07-03

## Decision

`PASS_STAGE110_R6_FULLTILE_ONERUN_CANDIDATE_NOT_PROMOTED`

Stage110 compares the existing r=6 tile4 and fulltile MAT kernels at the
complete-SAB level under active-buffer PVW/MAT-SAB. This is a routing
gate: a one-run win is not promoted to a final claim.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage110_inputs_available | PASS | tile4_summary;fulltile_summary | True;True | Both complete-SAB summaries are available. |
| stage110_correctness | PASS | all_correct | True | Both variants passed complete-SAB correctness. |
| stage110_fullsab_timing | PASS_POSITIVE | tile4_pvw_mean/fulltile_pvw_mean | 1.026 | Ratio above 1 means fulltile is faster than tile4. |
| stage110_decision | PASS_STAGE110_R6_FULLTILE_ONERUN_CANDIDATE_NOT_PROMOTED | promotion_policy |  | fulltile beats tile4 in this complete-SAB smoke, but run count is below promotion threshold. |

## Comparison

| variant | runs | correct | PVW us mean | PVW lane us mean | speedup vs scalar mean |
|---|---:|---|---:|---:|---:|
| tile4 | 1 | True | 42492394.000 | 7082065.667 | 1.388 |
| fulltile | 1 | True | 41410757.000 | 6901792.833 | 1.397 |
| ratio_fulltile_vs_tile4 | 1 | True | 1.026 | 1.026 | 1.006 |