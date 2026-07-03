# Stage142 AVX512 FMA-Order Fix Gate

Date: 2026-07-03

## Decision

`PASS_STAGE142_AVX512_FMA_ORDER_FIX_PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN`

Stage142 keeps Stage141 as the recorded failed baseline and adds a minimal code repair: the MAT-aware AVX512 addmul now follows the generic AVX512 FMA order.

## Gates

| gate | status | metric | value | detail |
| --- | --- | --- | --- | --- |
| stage142_avx512_support | PASS | lscpu_avx512f | true | Host exposes AVX512F. |
| stage142_builds | PASS | configs_built | 3 | generic, small-r, and r4-unrolled AVX512 static builds. |
| stage142_compiles | PASS | configs_compiled | 3 | Same target probe compiled for every config. |
| stage142_runs | PASS | configs_run | 3 | Same target probe executed for every config. |
| stage142_correctness | PASS | correctness_rows | 18 | All specialized rows must be exact closed full-MAT DFT equivalents. |
| stage142_comparison | PASS | bench_rows;compare_rows | 270;2 | r=4,T=1,N=1024/2048 same-backend comparison. |
| stage142_decision | PASS_STAGE142_AVX512_FMA_ORDER_FIX_PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN | promotion_policy | 1.176373-1.267909 | FMA-order fix removes Stage141 correctness blocker; r4-unrolled is a kernel-only promotion candidate. |

## Comparison

| r | N | T | Bg_bit | variant | generic_mean_us | smallr_mean_us | r4_unrolled_mean_us | smallr_vs_generic_mean | r4_unrolled_vs_generic_mean | generic_median_us | smallr_median_us | r4_unrolled_median_us | smallr_vs_generic_median | r4_unrolled_vs_generic_median | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | 1024 | 1 | 23 | current_full_mat | 11.670320 | 10.723120 | 9.204380 | 1.088333 | 1.267909 | 11.573750 | 9.919600 | 9.129150 | 1.166756 | 1.267780 | PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN |
| 4 | 2048 | 1 | 23 | current_full_mat | 27.787410 | 27.191870 | 23.621260 | 1.021901 | 1.176373 | 26.121850 | 27.436350 | 23.265550 | 0.952089 | 1.122770 | PROMOTE_R4_UNROLLED_KERNEL_READY_FULL_SAB_RERUN |

## Interpretation

The Stage141 correctness blocker is removed at the closed full-MAT kernel level. The r4-unrolled result is promotable only to full SAB A/B, not to a final bootstrapping speedup claim.
