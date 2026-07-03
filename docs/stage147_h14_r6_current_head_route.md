# Stage147 H14 r=6 Current-Head Route

Date: 2026-07-03

## Decision

`PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT`

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage147_prior_route | PASS | stage146;stage89 | r4_unrolled_not_promoted;h14_r6_preferred_explicit | Stage147 is justified only because r4-unrolled was not promoted and H14 r=6 was the prior preferred explicit route. |  |
| stage147_current_head_smoke | PASS | wrapper;backend | current_head_r6_body_profile_smoke | Current head builds and runs wrapper/backend explicit r=6 full-SAB profile smoke. |  |
| stage147_profile_attribution | PASS | lane_ratio;from_dft_ratio;backend_scalar | 1.038546;1.132412;1.417000 | Profile smoke attributes current-head backend edge and confirms unchanged schedule counts. |  |
| stage147_decision | PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT | route | h14_r6_backend_current_head | Stage147 chooses the next research branch without modifying scalar/default behavior. | Run Stage148 repeated/noise/resource refresh for current-head H14 r=6 backend before any stronger claim. |

## Prior Route Inputs

| source | gate | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- | --- |
| Stage146 | stage146_decision | PASS_STAGE146_VARIANCE_ATTRIBUTED_KEEP_R4_EXPLICIT_ROUTE_TO_SCHEDULE_OR_HIGHER_STAT | routing | explicit_r4_unrolled_not_promoted | repro/stage146_r4_unrolled_variance_attribution/summary.csv | Stage146 selects the next research route without changing scalar/default behavior. |
| Stage89 | stage89_performance_policy | PROMOTE_EXPLICIT_PATH_NOT_DEFAULT |  |  | repro/stage88_h14_backend_repeated_gates/backend_vs_wrapper.csv; repro/stage88_h14_backend_repeated_gates/full_sab_repeated.csv; repro/stage36_target_perf_summary.csv | paired=3; backend/wrapper mean=1.035516; min=1.024476; backend/scalar mean=1.437; backend/scalar min=1.435; wrapper/scalar mean=1.384; Stage36 r4 mean=1.377; r4 CI=[1.314893,1.438107] |
| Stage89 | stage89_noise_resource_guard | PASS |  |  | repro/stage88_h14_backend_repeated_gates/noise_summary.csv; repro/stage88_h14_backend_repeated_gates/resource_summary.csv | noise=PASS; seeds=3; resource=PASS; runs=1; key_ratio=1.122537; keygen_ratio=1.301382; rss_ratio=1.030722 |
| Stage89 | stage89_decision | PASS_STAGE89_H14_BACKEND_PROMOTE_EXPLICIT_PATH_NOT_DEFAULT |  |  | repro/stage89_h14_promotion_policy_integration/summary.csv | H14-C1 backend FromDFT-add is promoted as the preferred explicit r=6 local engineering path, while scalar/default paths and paper-level claims remain unchanged. |

## Variant Results

| variant | status | r | h | r_prec | lanes | in_N | bench_pvw_us | bench_pvw_lane_us | scalar_repeated_us | scalar_lane_us | speedup_vs_scalar_repeated | body_full_us | mat_ep_calls | mat_ep_us | mat_ep_share | cmux_calls | cmux_us | cmux_sub_us | cmux_from_dft_us | cmux_add_us | ncmux_calls | ncmux_us | ncmux_auto_us | sub_a_calls | sub_a_us | copyback_calls | copyback_us | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wrapper_fused_from_dft_add_r6 | PASS | 6 | 39 | 7 | 6 | 2048 | 42470475.000 | 7078412.500 | 58869427.000 | 9811571.167 | 1.386 | 42019022 | 573440 | 19619048 | 0.466909 | 573440 | 40671987 | 6138760 | 14854939 | 0 | 5080 | 805166 | 398160 | 39 | 893469 | 0 | 0 | repro/stage147_h14_r6_current_head_route/run_wrapper_fused_from_dft_add_r6.log |
| backend_from_dft_add_r6 | PASS | 6 | 39 | 7 | 6 | 2048 | 40894158.000 | 6815693.000 | 57944617.000 | 9657436.167 | 1.417 | 40420213 | 573440 | 19654922 | 0.486265 | 573440 | 39019746 | 6181128 | 13117963 | 0 | 5080 | 817322 | 427851 | 39 | 909171 | 0 | 0 | repro/stage147_h14_r6_current_head_route/run_backend_from_dft_add_r6.log |

## Comparison

| metric | wrapper | backend | backend_over_wrapper | status | detail |
| --- | --- | --- | --- | --- | --- |
| correctness | PASS | PASS | 1 | PASS | Both current-head r=6 explicit variants must pass full-SAB correctness. |
| pvw_lane_speedup_backend_over_wrapper | 7078412.500 | 6815693.000 | 1.038546 | SMOKE_ONLY | Primary current-head smoke metric is T_bootstrap/r. |
| body_full_speedup_backend_over_wrapper | 42019022 | 40420213 | 1.039555 | PROFILE_ONLY | Instrumented body hot-path comparison. |
| from_dft_speedup_backend_over_wrapper | 14854939 | 13117963 | 1.132412 | PROFILE_ONLY | Backend callback should reduce inverse DFT materialization/add lifetime. |
| mat_ep_speedup_backend_over_wrapper | 19619048 | 19654922 | 0.998175 | PROFILE_ONLY | MAT EP should be the same algorithmic kernel across these two variants. |
| speedup_vs_scalar_wrapper | 1.386 |  | 1.386 | SMOKE_ONLY | Wrapper variant speedup against repeated scalar SAB. |
| speedup_vs_scalar_backend |  | 1.417 | 1.417 | SMOKE_ONLY | Backend variant speedup against repeated scalar SAB. |
| mat_ep_calls_equal | 573440 | 573440 | 1 | PASS | Backend materialization must not change SAB schedule counts. |
| copyback_zero | 0 | 0 | 1 | PASS | Active-buffer route should keep copyback eliminated. |
| cmux_add_delta_backend_minus_wrapper | 0 | 0 | 0.000000 | PROFILE_ONLY | Both variants are expected to keep explicit add timing near zero under fused epilogue. |

## Interpretation

Stage147 is a route-selection gate. It can justify a current-head high-stat refresh for H14 r=6 backend, but it does not promote defaults or make a final SAB acceleration claim.
