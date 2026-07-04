# Stage280 CMUX/MAT-EP Residual Screen

Decision: `PASS_STAGE280_RESIDUAL_CANDIDATE_SELECTED_REPEAT_REQUIRED`.

Stage280 screens existing explicit CMUX/MAT-EP residual candidates under the
current guarded include-zero fast path. The primary metric is unprofiled full
SAB `T_bootstrap/r`; body-profile data is attribution-only.

## Candidate Comparison

| variant | T_bootstrap/r PVW us | speedup vs fast_control | status |
| --- | ---: | ---: | --- |
| fast_control | 7077472.750 | 1.000000 | control |
| backend_from_dft_add | 6906473.000 | 1.024759 | positive_screen |
| sub_decomp_avx | 6944666.500 | 1.019123 | positive_screen |
| backend_sub_decomp_avx | 6721373.250 | 1.052980 | positive_screen |
| backend_sub_decomp_dual | 6625352.500 | 1.068241 | positive_screen |

Selected candidate for the next repeated gate: `backend_sub_decomp_dual`.

## Profile Components

| variant | component | component us | calls | share of profiled full |
| --- | --- | ---: | ---: | ---: |
| fast_control | rgsw_monomial | 27818471.000 | 40 | 0.976217 |
| fast_control | cmux_total | 27622819.000 | 573440 | 0.969351 |
| fast_control | mat_ep | 13211633.000 | 573440 | 0.463628 |
| fast_control | cmux_from_dft | 6432727.000 | 573440 | 0.225740 |
| fast_control | cmux_add | 3969727.000 | 573440 | 0.139307 |
| fast_control | cmux_sub | 3911424.000 | 573440 | 0.137261 |
| backend_from_dft_add | rgsw_monomial | 26931750.000 | 40 | 0.975285 |
| backend_from_dft_add | cmux_total | 26732865.000 | 573440 | 0.968083 |
| backend_from_dft_add | mat_ep | 12878588.000 | 573440 | 0.466375 |
| backend_from_dft_add | cmux_from_dft | 9450331.000 | 573440 | 0.342227 |
| backend_from_dft_add | cmux_add | 0.000 | 573440 | 0.000000 |
| backend_from_dft_add | cmux_sub | 4330589.000 | 573440 | 0.156825 |
| sub_decomp_avx | rgsw_monomial | 26711243.000 | 40 | 0.975666 |
| sub_decomp_avx | cmux_total | 26514203.000 | 573440 | 0.968469 |
| sub_decomp_avx | mat_ep | 16011274.000 | 573440 | 0.584834 |
| sub_decomp_avx | cmux_from_dft | 6393079.000 | 573440 | 0.233516 |
| sub_decomp_avx | cmux_add | 4022434.000 | 573440 | 0.146925 |
| sub_decomp_avx | cmux_sub | 0.000 | 573440 | 0.000000 |
| backend_sub_decomp_avx | rgsw_monomial | 25739986.000 | 40 | 0.974357 |
| backend_sub_decomp_avx | cmux_total | 25548711.000 | 573440 | 0.967116 |
| backend_sub_decomp_avx | mat_ep | 16068539.000 | 573440 | 0.608255 |
| backend_sub_decomp_avx | cmux_from_dft | 9423998.000 | 573440 | 0.356734 |
| backend_sub_decomp_avx | cmux_add | 0.000 | 573440 | 0.000000 |
| backend_sub_decomp_avx | cmux_sub | 0.000 | 573440 | 0.000000 |
| backend_sub_decomp_dual | rgsw_monomial | 25310370.000 | 40 | 0.974352 |
| backend_sub_decomp_dual | cmux_total | 25056781.000 | 573440 | 0.964590 |
| backend_sub_decomp_dual | mat_ep | 15691590.000 | 573440 | 0.604066 |
| backend_sub_decomp_dual | cmux_from_dft | 9309145.000 | 573440 | 0.358366 |
| backend_sub_decomp_dual | cmux_add | 0.000 | 573440 | 0.000000 |
| backend_sub_decomp_dual | cmux_sub | 58925.000 | 573440 | 0.002268 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_current_input | PASS | input commit | c2feb62 | Stage280 starts after Stage279 residual profile. |
| G2_correctness | PASS | correctness rows | 10/10 | All screened variants must pass full SAB correctness before timing is interpreted. |
| G3_unprofiled_control | PASS | fast_control T/r | 7077472.750 | Candidate deltas use unprofiled fast include-zero control. |
| G4_best_candidate | PASS | backend_sub_decomp_dual | 1.068241 | Best candidate is selected only for a repeated gate, not final promotion. |
| G5_profile_coverage | PASS | profile components | 60 | Body-profile attribution is recorded separately from latency claims. |
| G6_decision | PASS_STAGE280_RESIDUAL_CANDIDATE_SELECTED_REPEAT_REQUIRED | stage decision | PASS_STAGE280_RESIDUAL_CANDIDATE_SELECTED_REPEAT_REQUIRED | No final speed claim is made from Stage280 single-screen data. |

## Claim Boundary

| claim | status |
| --- | --- |
| complete SAB speedup | screen-only; repeated gate required |
| algorithmic improvement | not yet promoted; candidate must survive Stage281 |
| backend/SIMD distinction | same `spqlios_avx512` backend and explicit flags recorded |
| native performance | still gated until native execution is resolved |

Generated from input head `c2feb62`.
