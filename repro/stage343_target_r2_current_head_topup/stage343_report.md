# Stage343 Target r=2 Current-Head Top-Up

Decision: `PASS_STAGE343_TARGET_R2_CURRENT_HEAD_HIGHSTAT_TOPUP`.

Stage343 tests the next executable gap from Stage342: promote
`SET_2_3_2048 r=2` from smoke-only to a scoped current-head high-stat row by
combining the hotpath-equivalent Stage341 sample with nine new top-up samples.

## Summary

| decision | case | samples | correctness | pvw_t_over_r_mean_us | scalar_t_over_r_mean_us | speedup_mean | speedup_ci95 | noise_trials | noise_pair_failures | claim_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE343_TARGET_R2_CURRENT_HEAD_HIGHSTAT_TOPUP | SET_2_3_2048_r2 | 10 | Pass | 6612564.550 | 11056987.250 | 1.672200 | 1.651056..1.693344 | 10 | 0 | target_r2_scoped_highstat |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_stage342_route | PASS | Stage342 decision | PASS_STAGE342_CONTINUITY_AUDIT_SCOPED_BRIDGE_NO_FULL_MATRIX_CLAIM |
| G2_hotpath_equivalence | PASS | Stage341/Stage343 run heads to HEAD | stage341_smoke_to_head=HOTPATH_EQUIVALENT;stage343_topup_to_head=HOTPATH_EQUIVALENT |
| G3_perf_highstat | PASS | samples/correctness | 10/Pass |
| G4_noise_resource | PASS | pair failures/trials | 0/10 |
| G5_claim_boundary | PASS | claim level | target_r2_only |
| G6_decision | PASS_STAGE343_TARGET_R2_CURRENT_HEAD_HIGHSTAT_TOPUP | stage decision | PASS_STAGE343_TARGET_R2_CURRENT_HEAD_HIGHSTAT_TOPUP |

## Claim Boundary

| claim | status | safe_statement | blocked_statement |
| --- | --- | --- | --- |
| current_head_target_r2_highstat | ALLOW_SCOPED | SET_2_3_2048 r=2 current-head complete-SAB T_bootstrap/r high-stat top-up is available. | Broader added-parameter, non-binary, novelty, or theoretical-optimality wording. |
| full_parameter_matrix | STILL_BLOCKED | Target r=2 can be promoted only inside the scoped target parameter if Stage343 passes. | SET_4_5_2048 and SET_2_3_4096 still need current-head topups. |
