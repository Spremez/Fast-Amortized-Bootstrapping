# Stage159 Sub-Decompose Fusion Repeated Gate

Date: 2026-07-03

## Decision

`PASS_STAGE159_SUB_DECOMP_FUSION_REPEATED_PROMOTION_CANDIDATE`

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage159_perf | PASS_STAGE159_PERF_SUB_DECOMP_FUSION_REPEATED_POSITIVE | T_bootstrap/r | 1.036393 | Repeated complete-SAB A/B for sub-decompose fusion versus same H14 backend control. | Promotion requires stable positive amortized per-lane timing. |
| stage159_noise | PASS | seeds;failures | 3;0/0/0 | Final-output correctness/noise for the fusion path against scalar repeated outputs. | Any nonzero failure blocks promotion. |
| stage159_resource | PASS | key_bytes_ratio;vmhwm_ratio | 1.122537;1.031098 | Resource/key snapshot for the fusion path versus repeated scalar. | Report key/memory cost with any timing claim. |
| stage159_decision | PASS_STAGE159_SUB_DECOMP_FUSION_REPEATED_PROMOTION_CANDIDATE | promotion_boundary | sub_decomp_fusion_explicit_flag | Stage159 decides whether Stage158's smoke candidate survives research gates. | Proceed to a policy/default gate or next representation-changing optimization; keep the flag explicit until then. |

## Performance

| metric | runs | control_mean_pvw_lane_us | fusion_mean_pvw_lane_us | fusion_over_control_mean_speedup | fusion_over_control_min_speedup | fusion_over_control_ci95_low | fusion_over_control_ci95_high | control_mean_speedup_vs_scalar | fusion_mean_speedup_vs_scalar | fusion_incremental_speedup_vs_control_scalar_speedup | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T_bootstrap_per_lane | 3 | 6836220.167 | 6596492.333 | 1.036393 | 1.021281 | 1.019695 | 1.053090 | 1.428667 | 1.478333 | 1.034764 | PASS_STAGE159_PERF_SUB_DECOMP_FUSION_REPEATED_POSITIVE |

## Noise

| r | seeds | points | pvw_failures | scalar_failures | pair_failures | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | avg_pvw_minus_scalar_log2 | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 3 | 36864 | 0 | 0 | 0 | -0.254 | 0.115 | -0.044333 | PASS |

## Resource

| runs | pvw_key_bytes | scalar_key_bytes | key_bytes_ratio | pvw_keygen_lane_avg_us | scalar_keygen_lane_avg_us | keygen_lane_ratio | pvw_vmhwm_kb | scalar_vmhwm_kb | vmhwm_ratio | pvw_time_max_rss_kb | scalar_time_max_rss_kb | time_max_rss_ratio | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1032871032 | 920121648 | 1.122537 | 762900.667 | 604016.333 | 1.263046 | 1191756.000 | 1155812.000 | 1.031098 | 1191788.000 | 1156164.000 | 1.030812 | PASS |

## Interpretation

Stage159 keeps the research loop finite: Stage158's positive smoke either becomes a promotion candidate, a weak/neutral ablation, or a failed candidate based on complete-SAB repeated evidence plus correctness/noise/resource gates.
