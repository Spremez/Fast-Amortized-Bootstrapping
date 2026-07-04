# Stage306 Torus-to-DFT Micro-Hypothesis

Decision: `PASS_STAGE306_TORUS_TO_DFT_DIRECT_LIFECYCLE_TARGET_ADMITTED`.

Stage306 is a candidate-admission stage. It binds Stage305 complete-SAB split evidence to current-head sub-DTF microbench data and filters out DFT ideas that were already neutral.

## Summary

| decision | dominant_direct_component | dominant_direct_share | current_runs_per_variant | current_microbench_correctness | current_direct_vs_baseline_speedup_mean | current_direct_vs_baseline_speedup_min |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE306_TORUS_TO_DFT_DIRECT_LIFECYCLE_TARGET_ADMITTED | torus_to_dft | 0.616652 | 5 | PASS | 1.104602 | 1.045028 |

## Evidence Matrix

| stage | evidence | decision | metric | value |
| --- | --- | --- | --- | --- |
| Stage289 | multirow torus_to_DFT wrapper | NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION | speedup_vs_scalar_loop_mean/min | 0.948000/0.923000 |
| Stage290 | direct-output torus_to_DFT array | NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION | speedup_vs_scalar_loop_mean/min | 1.003200/0.920000 |
| Stage291 | sub-decompose direct DFT | PASS_STAGE291_SUB_DECOMP_DFT_DIRECT_MICRO_POSITIVE_FULL_SAB_REQUIRED | direct_vs_baseline_speedup_mean/min | 1.372118/1.109962 |
| Stage305 | complete-SAB split profile | PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED | dominant direct split component/share | torus_to_dft/0.616652 |
| Stage306 | current-head sub-DTF refresh | PASS_STAGE306_TORUS_TO_DFT_DIRECT_LIFECYCLE_TARGET_ADMITTED | direct_vs_baseline_speedup_mean/min | 1.104602/1.045028 |

## Candidate Matrix

| candidate | status | evidence | next_action |
| --- | --- | --- | --- |
| C1_multirow_dft_wrapper | REJECTED_OR_NEUTRAL | NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION | Do not repeat this wrapper as an optimization candidate. |
| C2_direct_output_dft_array | REJECTED_OR_NEUTRAL | NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION | Do not promote unless redesigned with new evidence. |
| C3_sub_decompose_to_double_direct_dft | PROMOTED_ALREADY_IN_CURRENT_DIRECT_PATH | Stage291 plus Stage292-305; current min 1.045028x | Keep as current best complete-SAB path. |
| C4_direct_ifft_lifecycle_split | ADMITTED_FOR_STAGE307 | Stage305 direct torus_to_dft share 0.616652 | Instrument direct path into digit-to-double and ifft subcomponents before any rewrite. |
| C5_dense_mat_avx512_rewrite | NOT_ADMITTED_FROM_STAGE306 | Stage301/302 FMA counters near-neutral; Stage305 dense is not dominant residual. | Return only if future split shows dense dominates after DFT lifecycle changes. |

## Component Budget

| component | share_of_direct_split_total | hypothetical_component_reduction | profile_level_split_speedup_bound |
| --- | --- | --- | --- |
| decompose | 0.002047 | 0.10 | 1.000205 |
| decompose | 0.002047 | 0.25 | 1.000514 |
| decompose | 0.002047 | 0.50 | 1.001028 |
| torus_to_dft | 0.616652 | 0.10 | 1.065939 |
| torus_to_dft | 0.616652 | 0.25 | 1.182942 |
| torus_to_dft | 0.616652 | 0.50 | 1.447805 |
| dense_from_dec | 0.378154 | 0.10 | 1.039431 |
| dense_from_dec | 0.378154 | 0.25 | 1.104773 |
| dense_from_dec | 0.378154 | 0.50 | 1.234071 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_entry_stage305 | PASS | Stage305 proof | PASS_STAGE305_MATERIALIZATION_SPLIT_PROFILE_RECORDED | Stage306 must start from a measured complete-SAB residual. |
| G2_dominant_component | PASS | dominant direct component | torus_to_dft | The next candidate must target the measured residual, not a broad rewrite. |
| G3_current_microbench | PASS | current direct sub-DTF min speedup | 1.045028 | The current direct path must still beat the old sub-DTF lifecycle. |
| G4_prior_candidate_filter | PASS | Stage289/290 wrapper candidates | NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION;NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION | Known neutral DFT wrappers are excluded from the next implementation route. |
| G5_claim_boundary | PASS | scope | candidate admission | Stage306 is not a new full-SAB speed claim and does not prove theoretical optimality. |
| G6_decision | PASS_STAGE306_TORUS_TO_DFT_DIRECT_LIFECYCLE_TARGET_ADMITTED | stage decision | PASS_STAGE306_TORUS_TO_DFT_DIRECT_LIFECYCLE_TARGET_ADMITTED | Controls Stage307: split direct DFT into digit-to-double and ifft before rewriting. |
