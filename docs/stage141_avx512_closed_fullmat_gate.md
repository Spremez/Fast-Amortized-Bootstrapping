# Stage141 AVX512 Closed Full-MAT Gate

Date: 2026-07-03

## Decision

`FAIL_STAGE141_AVX512_CLOSED_FULLMAT_GATE`

Stage141 compares generic, small-r, and r4-unrolled AVX512 variants under the same backend for the valid closed full-MAT target shape.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage141_avx512_support | PASS | lscpu_avx512f | true | Host exposes AVX512F to WSL. |
| stage141_builds | PASS | configs_built | 3 | generic, small-r, and r4-unrolled AVX512 static builds. |
| stage141_compiles | PASS | configs_compiled | 3 | Same target probe compiled for every config. |
| stage141_runs | PASS | configs_run | 3 | Same target probe executed for every config. |
| stage141_correctness | FAIL | correctness_rows | 18 | Checks closed split equivalence for every AVX512 config. |
| stage141_comparison | PASS | bench_rows;compare_rows | 270;2 | r=4,T=1,N=1024/2048 same-backend comparison. |
| stage141_decision | FAIL_STAGE141_AVX512_CLOSED_FULLMAT_GATE | promotion_policy |  | Stage141 decides whether existing AVX512 closed full-MAT specialization should be promoted to SAB rerun. |

## Comparison

| r | N | T | Bg_bit | variant | generic_us | smallr_us | r4_unrolled_us | smallr_vs_generic | r4_unrolled_vs_generic | r4_unrolled_vs_smallr | decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 1024 | 1 | 23 | current_full_mat | 12.571560 | 8.031480 | 9.155230 | 1.565286 | 1.373156 | 0.877256 | CORRECTNESS_BLOCKED_SPEED_ONLY |
| 4 | 2048 | 1 | 23 | current_full_mat | 24.798600 | 22.025830 | 22.681200 | 1.125887 | 1.093355 | 0.971105 | CORRECTNESS_BLOCKED_SPEED_ONLY |
