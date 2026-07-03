# Stage144 Full SAB Repeated r4-Unrolled Gate

Date: 2026-07-03

## Decision

`WEAK_STAGE144_R4_UNROLLED_POSITIVE_STATS_REVIEW_REQUIRED`

## Gates

| gate | status | metric | value | detail |
| --- | --- | --- | --- | --- |
| stage144_perf | WEAK_STAGE144_PERF_POSITIVE_BUT_CI_CROSSES_ONE | T_bootstrap/r | 1.000249 | Repeated full SAB A/B with 3 paired runs. |
| stage144_noise | PASS | seeds;failures | 3;0/0/0 | Final-output noise for r4-unrolled candidate against scalar repeated outputs. |
| stage144_resource | PASS | key_bytes_ratio;vmhwm_ratio | 1.065349;0.997049 | Resource/key snapshot for r4-unrolled candidate. |
| stage144_decision | WEAK_STAGE144_R4_UNROLLED_POSITIVE_STATS_REVIEW_REQUIRED | promotion_policy |  | Stage144 converts Stage143 smoke into repeated/noise/resource evidence. |

## Performance

| metric | runs | generic_mean_pvw_lane_us | r4_mean_pvw_lane_us | r4_vs_generic_mean_speedup | r4_vs_generic_min_speedup | r4_vs_generic_ci95_low | r4_vs_generic_ci95_high | generic_mean_speedup_vs_scalar | r4_mean_speedup_vs_scalar | r4_incremental_speedup_vs_generic_scalar_speedup | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T_bootstrap_per_lane | 3 | 7439676.750 | 7462397.750 | 1.000249 | 0.924113 | 0.835834 | 1.164664 | 1.304000 | 1.312333 | 1.006391 | WEAK_STAGE144_PERF_POSITIVE_BUT_CI_CROSSES_ONE |

## Noise

| r | seeds | points | pvw_failures | scalar_failures | pair_failures | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | avg_pvw_minus_scalar_log2 | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 3 | 24576 | 0 | 0 | 0 | -0.668 | 0.115 | -0.314333 | PASS |

## Resource

| runs | pvw_key_bytes | scalar_key_bytes | key_bytes_ratio | pvw_keygen_lane_avg_us | scalar_keygen_lane_avg_us | keygen_lane_ratio | pvw_vmhwm_kb | scalar_vmhwm_kb | vmhwm_ratio | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 653500424 | 613414432 | 1.065349 | 796147.000 | 672311.500 | 1.184194 | 769112.000 | 771388.000 | 0.997049 | PASS |

## Interpretation

Stage144 uses the correct MAT-RLWE amortized endpoint. It still remains an explicit-flag candidate until a separate promotion-policy step updates defaults or final claim wording.
