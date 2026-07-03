# Stage138 Shared-Mask Compact Gate

Date: 2026-07-03

## Decision

`PASS_STAGE138_SHARED_MASK_COMPACT_PROMOTED_READY_SAB_INTEGRATION`

Stage138 validates the MAT-RLWE shared-mask interpretation: one `a` polynomial shared by r bodies. The main metric is `kernel_time / r`, matching the user's intended amortized comparison dimension.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage138_mosfhet_static_build | PASS | make_static_spqlios | true | MOSFHET static build for shared-mask compact probe. |
| stage138_probe_compile | PASS | gcc_probe_compile | true | Standalone shared-mask compact probe compiled. |
| stage138_probe_run | PASS | probe_returncode | 0 | Shared-mask compact probe executed. |
| stage138_correctness | PASS | correctness_rows | 6 | Production shared-mask compact output equals repeated lane-pair output. |
| stage138_benchmark_rows | PASS | bench_rows;ratio_rows | 60;6 | Repeated lane-pair and shared-mask compact timings recorded. |
| stage138_r4_per_bit_speedup | RECORDED | min_r4_per_bit_speedup;max_r4_per_bit_speedup | 1.293981;1.491182 | Main metric is amortized per-lane/per-bit kernel time. |
| stage138_decision | PASS_STAGE138_SHARED_MASK_COMPACT_PROMOTED_READY_SAB_INTEGRATION | promotion_policy |  | Stage138 decides whether shared-mask compact EP is a real algorithmic route. |

## Ratios

| backend | r | N | T | Bg_bit | seed | repeated_us | shared_us | total_speedup | repeated_per_lane_us | shared_per_lane_us | per_bit_speedup | repeated_dft_conversions | shared_dft_conversions | dft_conversion_reduction | expected_dft_reduction | decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| spqlios | 2 | 1024 | 7 | 7 | 0 | 54.052910 | 45.971770 | 1.175785 | 27.026455 | 22.985885 | 1.175785 | 28 | 21 | 1.333333 | 1.333333 | PROMOTE_SHARED_MASK_COMPACT |
| spqlios | 2 | 512 | 7 | 7 | 0 | 35.046830 | 25.241840 | 1.388442 | 17.523415 | 12.620920 | 1.388442 | 28 | 21 | 1.333333 | 1.333333 | PROMOTE_SHARED_MASK_COMPACT |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 141.960810 | 95.200210 | 1.491182 | 35.490202 | 23.800052 | 1.491182 | 56 | 35 | 1.600000 | 1.600000 | PROMOTE_SHARED_MASK_COMPACT |
| spqlios | 4 | 512 | 7 | 7 | 0 | 52.381410 | 40.480820 | 1.293981 | 13.095353 | 10.120205 | 1.293981 | 56 | 35 | 1.600000 | 1.600000 | PROMOTE_SHARED_MASK_COMPACT |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 166.776730 | 118.331630 | 1.409401 | 27.796121 | 19.721938 | 1.409401 | 84 | 49 | 1.714286 | 1.714286 | PROMOTE_SHARED_MASK_COMPACT |
| spqlios | 6 | 512 | 7 | 7 | 0 | 79.255430 | 58.457670 | 1.355775 | 13.209238 | 9.742945 | 1.355775 | 84 | 49 | 1.714286 | 1.714286 | PROMOTE_SHARED_MASK_COMPACT |
