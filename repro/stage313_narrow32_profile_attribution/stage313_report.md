# Stage313 Narrow32 Profile Attribution

Decision: `PASS_STAGE313_NARROW32_PROFILE_ATTRIBUTION_RECORDED`.

Stage313 profiles direct baseline and narrow32 under the complete SAB target path to explain why the Stage311 microbench gain did not promote in Stage312.

## Summary

| variant | correctness | t_bootstrap_over_r_us | body_mat_ep_us_sum | digit_us | ifft_us | direct_over_narrow32_T_over_r_speedup | direct_over_narrow32_digit_speedup | direct_over_narrow32_mat_ep_speedup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| direct_profile | Pass | 6212113.750 | 28790362.000 | 8489325 | 8953547 |  |  |  |
| narrow32_profile | Pass | 6345664.750 | 28604279.000 | 8125944 | 8957938 |  |  |  |
| comparison | Pass |  |  |  |  | 0.978954 | 1.044719 | 1.006505 |

## Lifecycle Comparison

| component | direct | narrow32 | direct_over_narrow32 | interpretation |
| --- | --- | --- | --- | --- |
| T_over_r | 6212113.750 | 6345664.750 | 0.978954 | instrumented profile latency only |
| body_full | 49210765.000 | 49831639.000 | 0.987541 | sum of body profiles |
| mat_ep | 28790362.000 | 28604279.000 | 1.006505 | MAT EP inclusive profile |
| digit_to_double | 8489325 | 8125944 | 1.044719 | direct DFT digit component |
| ifft | 8953547 | 8957938 | 0.999510 | direct DFT reverse FFT component |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_correctness | PASS | profile target correctness | Pass | Both profiled variants must preserve complete SAB correctness. |
| G2_profile_consistency | PASS | direct rows | 5632800/5632800 | Both variants must profile the same direct sub-DTF surface. |
| G3_digit_effect | RECORDED_POSITIVE | direct/narrow32 digit speedup | 1.044719 | Whether the microbench digit effect is visible in full-SAB profile mode. |
| G4_fullsab_context | NO_PROMOTION_CONFIRMED | direct/narrow32 T/r speedup | 0.978954 | Narrow32 remains unpromoted unless full-SAB T/r improves. |
| G5_claim_boundary | PASS_PROFILE_ONLY | scope | instrumented one-run profile | Do not use Stage313 latency as final speed evidence. |
| G6_decision | PASS_STAGE313_NARROW32_PROFILE_ATTRIBUTION_RECORDED | stage decision | PASS_STAGE313_NARROW32_PROFILE_ATTRIBUTION_RECORDED | Controls Stage314 route. |
