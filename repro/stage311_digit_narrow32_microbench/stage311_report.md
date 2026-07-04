# Stage311 Digit Narrow32 Microbench

Decision: `PASS_STAGE311_DIGIT_NARROW32_MICRO_POSITIVE_FULLSAB_REQUIRED`.

Stage311 tests an opt-in digit conversion variant that narrows signed gadget digits to int32 before converting to double. It is valid only when the gadget digit range fits int32.

## Summary

| decision | runs_per_variant | correctness | digit_speedup_mean | digit_speedup_min | sub_speedup_mean | sub_speedup_min |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE311_DIGIT_NARROW32_MICRO_POSITIVE_FULLSAB_REQUIRED | 5 | PASS | 1.113323 | 1.046913 | 1.099270 | 1.034697 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_runs | PASS | paired runs | 5/5 | Both variants need paired repeated runs. |
| G2_correctness | PASS | MAT_SUB_DFT correctness | PASS | Narrow32 digit conversion must preserve MAT sub-DTF output. |
| G3_digit_component | PASS | paired min digit speedup | 1.046913 | Digit component must improve before full-SAB A/B is justified. |
| G4_sub_latency | PASS | paired min sub-DTF speedup | 1.034697 | Component gain must survive the sub-DTF microbench surface. |
| G5_claim_boundary | PASS | scope | microbench only | Stage311 is not a complete-SAB speed claim. |
| G6_decision | PASS_STAGE311_DIGIT_NARROW32_MICRO_POSITIVE_FULLSAB_REQUIRED | stage decision | PASS_STAGE311_DIGIT_NARROW32_MICRO_POSITIVE_FULLSAB_REQUIRED | Controls whether a full-SAB A/B is opened. |
