# Stage154 Bodymajor Full-SAB Closeout

Date: 2026-07-03

## Decision

`REJECT_STAGE154_BODYMAJOR_FULLSAB_SLOWER`

## Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage154_precondition | PASS | stage108;stage153 | PASS_STAGE108_BODYMAJOR_NEGATIVE_NOT_PROMOTED;NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED | repro/stage154_bodymajor_fullsab_closeout/prior_evidence.csv | Stage154 follows a skipped Stage108 complete-SAB gate and Stage153's dual-sub neutral result. |  |
| stage154_correctness | PASS | tile4;bodymajor | Pass;Pass | repro/stage154_bodymajor_fullsab_closeout/variant_results.csv | Both complete-SAB variants must pass target_full correctness. | Do not interpret timings if correctness fails. |
| stage154_fullsab_smoke | REJECT | bodymajor_over_tile4_T_bootstrap_per_lane | 0.977892 | repro/stage154_bodymajor_fullsab_closeout/comparison.csv | Same backend, same r=6, same primary endpoint. |  |
| stage154_decision | REJECT_STAGE154_BODYMAJOR_FULLSAB_SLOWER | candidate_route | r6_bodymajor_fullsab_closeout | repro/stage154_bodymajor_fullsab_closeout/summary.csv | Close or promote the bodymajor layout branch at complete-SAB level. | If neutral/rejected, route away from blind r=6 layout tuning. |

## Prior Evidence

| source | gate | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- | --- |
| Stage108 | stage108_decision | PASS_STAGE108_BODYMAJOR_NEGATIVE_NOT_PROMOTED | bodymajor_kernel_gate | NEGATIVE_OR_NEUTRAL_KERNEL | repro/stage108_bodymajor_layout_gate/summary.csv | Stage108 tested bodymajor at kernel level but skipped complete-SAB timing. |
| Stage108 | stage108_kernel_full_output_r6 | PROFILE_ONLY | bodymajor_vs_tile4;bodymajor_vs_fulltile | 1.223;0.922 | repro/stage108_bodymajor_layout_gate/kernel_comparison.csv | Kernel evidence alone cannot decide complete SAB. |
| Stage153 | stage153_decision | NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED | next_route | avoid_pair_fraction_limited_dual_sub | repro/stage153_dual_sub_fullsab_gate/summary.csv | After H14-C3 neutral, close broader MAT layout evidence before selecting another route. |

## Variant Results

| variant | status | r | reps | correctness | pvw_avg_us | pvw_lane_avg_us | scalar_repeated_avg_us | scalar_lane_avg_us | speedup_vs_scalar_repeated | source_build_log | source_run_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tile4_h14_r6_backend | PASS | 6 | 1 | Pass | 40748543.000 | 6791423.833 | 58689790.000 | 9781631.667 | 1.440 | repro/stage154_bodymajor_fullsab_closeout/tile4_h14_r6_backend/build.log | repro/stage154_bodymajor_fullsab_closeout/tile4_h14_r6_backend/run.log |
| bodymajor_h14_r6_backend | PASS | 6 | 1 | Pass | 41669763.000 | 6944960.500 | 59114815.000 | 9852469.167 | 1.419 | repro/stage154_bodymajor_fullsab_closeout/bodymajor_h14_r6_backend/build.log | repro/stage154_bodymajor_fullsab_closeout/bodymajor_h14_r6_backend/run.log |

## Comparison

| metric | tile4 | bodymajor | bodymajor_over_tile4 | status | detail |
| --- | --- | --- | --- | --- | --- |
| full_sab_pvw_us | 40748543.000 | 41669763.000 | 0.977892 | REJECT | Complete SAB wall-clock smoke; repeated gate required for any promotion. |
| amortized_T_bootstrap_per_lane_us | 6791423.833 | 6944960.500 | 0.977892 | REJECT | Primary MAT-RLWE SAB endpoint. |
| speedup_vs_scalar_repeated | 1.440 | 1.419 |  | INFO | Reported only as context; the gate is bodymajor versus same-backend tile4. |

## Interpretation

The complete-SAB smoke bodymajor/tile4 result on `T_bootstrap/r` is `0.977892`.
This closes the Stage108 full-SAB evidence gap for the body-major layout branch.
