# Stage148 H14 r=6 Repeated Refresh

Date: 2026-07-03

## Decision

`PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE`

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage148_precondition | PASS | stage147_decision | PASS_STAGE147_H14_R6_CURRENT_HEAD_ROUTE_CONFIRMED_HIGH_STAT_REFRESH_NEXT | Stage148 refresh is valid only after Stage147 routes to current-head H14 r=6 backend. |  |
| stage148_perf | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE | T_bootstrap/r | 1.042309 | Repeated current-head wrapper/backend A/B using amortized per-lane full-SAB time. | Do not promote if backend-vs-wrapper is not stable. |
| stage148_noise | PASS | seeds;failures | 3;0/0/0 | Final-output noise/correctness for current-head H14 backend against scalar repeated outputs. | Do not promote if any failure is nonzero. |
| stage148_resource | PASS | key_bytes_ratio;vmhwm_ratio | 1.122537;1.030966 | Resource/key snapshot for current-head H14 backend versus repeated scalar. | Report resource cost with any speed claim. |
| stage148_decision | PASS_STAGE148_H14_R6_REPEATED_REFRESH_PROMOTION_CANDIDATE | policy_boundary | explicit_h14_r6_backend | Stage148 records current-head repeated evidence; it does not change scalar/default behavior. | Proceed to Stage149 claim-boundary/final-package update; defaults still require a separate policy gate. |

## Performance

| metric | runs | wrapper_mean_pvw_lane_us | backend_mean_pvw_lane_us | backend_vs_wrapper_mean_speedup | backend_vs_wrapper_min_speedup | backend_vs_wrapper_ci95_low | backend_vs_wrapper_ci95_high | wrapper_mean_speedup_vs_scalar | backend_mean_speedup_vs_scalar | backend_incremental_speedup_vs_wrapper_scalar_speedup | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T_bootstrap_per_lane | 3 | 7127306.611 | 6838040.111 | 1.042309 | 1.037274 | 1.035361 | 1.049257 | 1.371000 | 1.432667 | 1.044979 | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE |

## Noise

| r | seeds | points | pvw_failures | scalar_failures | pair_failures | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | avg_pvw_minus_scalar_log2 | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 3 | 36864 | 0 | 0 | 0 | -0.161 | 0.403 | 0.176333 | PASS |

## Resource

| runs | pvw_key_bytes | scalar_key_bytes | key_bytes_ratio | pvw_keygen_lane_avg_us | scalar_keygen_lane_avg_us | keygen_lane_ratio | pvw_vmhwm_kb | scalar_vmhwm_kb | vmhwm_ratio | pvw_time_max_rss_kb | scalar_time_max_rss_kb | time_max_rss_ratio | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1032871032 | 920121648 | 1.122537 | 754248.167 | 609593.833 | 1.237296 | 1191632.000 | 1155840.000 | 1.030966 | 1191692.000 | 1156148.000 | 1.030743 | PASS |

## Interpretation

Stage148 is a repeated evidence refresh for the explicit H14 r=6 backend path. It does not modify scalar/default behavior and does not by itself establish a final paper-level claim.
