# Stage153 Dual-Sub Full-SAB Gate

Date: 2026-07-03

## Decision

`NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED`

## Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage153_build_correctness | PASS | control_and_dual_correctness | Pass;Pass | repro/stage153_dual_sub_fullsab_gate/variant_results.csv | Both control and dual-sub complete SAB smoke must pass target_full correctness. |  |
| stage153_pair_count | PASS | dual_sub_pair_calls/expected | 5080/5080 | repro/stage153_dual_sub_fullsab_gate/profile_results.csv | Dynamic pair count must match (h+1)*(2^r_prec-1). |  |
| stage153_corrected_theory_bound | LIMITED | corrected_body_speedup_bound | 1.000352 | repro/stage153_dual_sub_fullsab_gate/pair_fraction_model.csv | Stage152 local speedup must be multiplied by the actual pairable fraction. | Do not spend more effort on H14-C3 unless a broader pairing schedule is found. |
| stage153_fullsab_smoke | NEUTRAL | dual_over_control_T_bootstrap_per_lane | 1.002283 | repro/stage153_dual_sub_fullsab_gate/comparison.csv | Complete SAB smoke compares dual-sub against the same H14 r=6 backend path. |  |
| stage153_decision | NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED | candidate_route | h14_c3_dual_sub_fullsab | repro/stage153_dual_sub_fullsab_gate/summary.csv | Stage153 either promotes, neutralizes, or rejects the full-SAB dual-sub integration candidate. | Route to a broader schedule-level candidate if neutral or rejected. |

## Prior Evidence

| source | item | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- | --- |
| Stage152 | dual_sub_local_kernel | PASS_STAGE152_DUAL_SUB_LOCAL_POSITIVE_INTEGRATION_CANDIDATE | speedup_mean | 1.150215 | repro/stage152_dual_sub_kernel_gate/raw_results.csv | Local dual-sub kernel result before full-SAB pair-fraction correction. |
| Stage151 | current_r6_sub_share | PROFILE_ONLY | cmux_sub_us/body_full_us | 0.152252 | repro/stage151_h14_r6_fulltile_backend_smoke/variant_results.csv | Subtraction share must be multiplied by the Stage153 pairable fraction. |

## Variant Results

| variant | status | r | reps | correctness | pvw_avg_us | pvw_lane_avg_us | scalar_repeated_avg_us | scalar_lane_avg_us | speedup_vs_scalar_repeated | source_build_log | source_run_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control_h14_r6_backend | PASS | 6 | 1 | Pass | 40937628.000 | 6822938.000 | 58398188.000 | 9733031.333 | 1.427 | repro/stage153_dual_sub_fullsab_gate/control_h14_r6_backend/build.log | repro/stage153_dual_sub_fullsab_gate/control_h14_r6_backend/run.log |
| dual_sub_h14_r6_backend | PASS | 6 | 1 | Pass | 40844399.000 | 6807399.833 | 58937686.000 | 9822947.667 | 1.443 | repro/stage153_dual_sub_fullsab_gate/dual_sub_h14_r6_backend/build.log | repro/stage153_dual_sub_fullsab_gate/dual_sub_h14_r6_backend/run.log |
| dual_sub_h14_r6_profile | PASS | 6 | 1 | Pass | 42012709.000 | 7002118.167 | 58862366.000 | 9810394.333 | 1.401 | repro/stage153_dual_sub_fullsab_gate/dual_sub_h14_r6_profile/build.log | repro/stage153_dual_sub_fullsab_gate/dual_sub_h14_r6_profile/run.log |

## Profile Result

| variant | status | lanes | in_N | h | r_prec | full_us | cmux_calls | cmux_sub_calls | dual_sub_pair_calls | expected_pair_calls | pair_call_fraction | pair_subop_fraction | dual_sub_pair_us | cmux_sub_us | ncmux_calls | mat_ep_calls | source_run_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dual_sub_h14_r6_profile | PASS | 6 | 2048 | 39 | 7 | 41514445 | 573440 | 573440 | 5080 | 5080 | 0.008859 | 0.017718 | 87096 | 6362060 | 5080 | 573440 | repro/stage153_dual_sub_fullsab_gate/dual_sub_h14_r6_profile/run.log |

## Pair-Fraction Model

| metric | value | formula | detail |
| --- | --- | --- | --- |
| pair_calls_per_full_sab | 5080 | (h+1)*(2^r_prec-1) | Expected 5080 for h=39, r_prec=7. |
| pair_subop_fraction | 0.017718 | 2*(2^r_prec-1)/(r_prec*N) | Only this fraction of CMUX/NCMUX subtraction outputs can use the dual-sub shared input. |
| stage152_corrected_body_speedup_bound | 1.000352 | 1/(1-sub_share*pair_subop_fraction*(1-1/local_speedup)) | This corrects Stage152's local Amdahl projection by the actual pairable fraction. |

## Comparison

| metric | control | dual | dual_over_control | status | detail |
| --- | --- | --- | --- | --- | --- |
| full_sab_pvw_us | 40937628.000 | 40844399.000 | 1.002283 | NEUTRAL | Complete SAB wall-clock smoke, not repeated statistics. |
| amortized_T_bootstrap_per_lane_us | 6822938.000 | 6807399.833 | 1.002283 | NEUTRAL | Primary MAT-RLWE endpoint for the integration smoke. |
| corrected_theory_bound | 1.000000 | 1.000352 | 1.000352 | LIMITED | Pairable-fraction corrected bound predicts only a very small body-level opportunity. |

## Interpretation

The full-SAB smoke result is `1.002283` on the primary `T_bootstrap/r` endpoint.
The dynamic pair count confirms `5080`
pair sites, so the Stage152 local kernel win applies to only
`0.017718` of subtraction outputs. This is why
the candidate is not allowed to become a final bootstrapping claim from local
kernel evidence alone.
