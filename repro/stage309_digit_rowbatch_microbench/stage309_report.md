# Stage309 Digit Rowbatch Microbench

Decision: `NEUTRAL_STAGE309_DIGIT_ROWBATCH_NO_PROMOTION`.

Stage309 tests an opt-in r=4/k=1/l=1 direct DFT variant that materializes all five digit rows in one coefficient-block loop before running the same per-row SPQLIOS `ifft` calls.

## Summary

| decision | runs_per_variant | correctness | digit_speedup_mean | digit_speedup_min | sub_speedup_mean | sub_speedup_min |
| --- | --- | --- | --- | --- | --- | --- |
| NEUTRAL_STAGE309_DIGIT_ROWBATCH_NO_PROMOTION | 5 | PASS | 1.057960 | 0.899814 | 0.978751 | 0.870218 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_runs | PASS | paired runs | 5/5 | Both variants need paired repeated runs. |
| G2_correctness | PASS | MAT_SUB_DFT correctness | PASS | Row-batched digit materialization must preserve MAT sub-DTF output. |
| G3_digit_component | NO_PROMOTION | paired min digit speedup | 0.899814 | Digit component must improve before full-SAB A/B is justified. |
| G4_sub_latency | NO_PROMOTION | paired min sub-DTF speedup | 0.870218 | Component gain must survive the sub-DTF microbench surface. |
| G5_claim_boundary | PASS | scope | microbench only | Stage309 is not a complete-SAB speed claim. |
| G6_decision | NEUTRAL_STAGE309_DIGIT_ROWBATCH_NO_PROMOTION | stage decision | NEUTRAL_STAGE309_DIGIT_ROWBATCH_NO_PROMOTION | Controls whether a full-SAB A/B is opened. |
