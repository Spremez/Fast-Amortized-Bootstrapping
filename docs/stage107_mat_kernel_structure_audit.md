# Stage107 MAT Kernel Structure Audit

Date: 2026-07-03

## Decision

`PASS_STAGE107_DENSE_KERNEL_AUDIT_NEXT_GATE_SELECTED`

The current MAT external-product implementation contains useful AVX512
specialization and tiling, but the source-level operation structure is
still dense row-output accumulation. For k=1,l=1 it uses `(r+1)`
decomposition rows and `(r+1)` output polynomials, so the hot multiply
structure is `(r+1)^2` complex terms per coefficient vector.

This is not evidence of body-linear or theoretical optimal MAT-RLWE SAB.

## Kernel Structure

| kernel | r | rows | outputs | terms | terms/lane | shape |
|---|---:|---:|---:|---:|---:|---|
| generic_fallback | 2 | 3 | 3 | 9 | 4.500000 | dense_row_output_O_r2 |
| r2_smallr_avx512 | 2 | 3 | 3 | 9 | 4.500000 | dense_row_output_O_r2 |
| r4_smallr_avx512 | 4 | 5 | 5 | 25 | 6.250000 | dense_row_output_O_r2 |
| r4_unrolled_rows | 4 | 5 | 5 | 25 | 6.250000 | dense_row_output_O_r2 |
| r6_rgt4_tiled | 6 | 7 | 7 | 49 | 8.166667 | dense_row_output_O_r2 |
| r6_fulltile | 6 | 7 | 7 | 49 | 8.166667 | dense_row_output_O_r2 |
| r8_rgt4_tiled | 8 | 9 | 9 | 81 | 10.125000 | dense_row_output_O_r2 |

## Next Gates

| priority | gate | variant | required action | stop rule |
|---|---|---|---|---|
| P0 | G107-D | V106-D_body_major_coefficient_blocked_layout | implement or benchmark a layout-only/body-major coefficient-blocked MAT path behind an explicit flag | if kernel wins but complete SAB T_total/r does not, mark neutral and do not promote |
| P1 | G107-B | V106-B_body_linear_mat_external_product | derive selector/key invariants for block/diagonal/body-linear MAT external product before code | if the required selector/key structure changes security assumptions, block until proof review |
| P2 | G107-C | V106-C_dft_lazy_schedule_window | carry DFT/materialized state across a bounded CMUX window | do not repeat Stage23/Stage87 neutral work unless profile shows materialization is dominant |

## Interpretation

Stage108 should not start by claiming a new theorem. It should run a
bounded implementation gate first. The selected immediate gate is V106-D
because it can test body-major/coefficient-blocked locality without
changing selector semantics. V106-B remains the required path for true
body-linear optimality, but it needs a selector/key invariant proof before
code.
