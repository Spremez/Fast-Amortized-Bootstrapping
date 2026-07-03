# Stage108 Body-Major Layout Gate

Date: 2026-07-03

## Decision

`PASS_STAGE108_BODYMAJOR_NEGATIVE_NOT_PROMOTED`

Stage108 implements V106-D as an explicit r=6 body-major MAT external-product
layout experiment behind `MAT_TRGSW_AVX512_R6_BODYMAJOR`. It does not change
scalar/default SAB or the promoted explicit paths.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage108_inputs_available | PASS | tile4;fulltile;bodymajor | True;True;True | All kernel logs are available. |
| stage108_kernel_correctness | PASS | tile4;fulltile;bodymajor | True;True;True | All r>4 kernel identity gates pass. |
| stage108_kernel_locality_result | NEGATIVE_OR_NEUTRAL_KERNEL | bodymajor_vs_tile4_full;bodymajor_vs_fulltile_full;bodymajor_vs_tile4_dft | 1.223;0.922;0.935 | body-major does not beat both existing r=6 kernel layouts. |
| stage108_full_sab_smoke | SKIPPED_FULL_SAB | bodymajor_vs_tile4 | 0.000 | complete-SAB smoke is missing or not positive. |
| stage108_decision | PASS_STAGE108_BODYMAJOR_NEGATIVE_NOT_PROMOTED | promotion_policy |  | body-major layout is correct but not performance-positive versus existing layouts. |

## Kernel Comparison

| bench | r | tile4 us | fulltile us | bodymajor us | bodymajor/tile4 | bodymajor/fulltile |
|---|---:|---:|---:|---:|---:|---:|
| dft_output | 6 | 50.831 | 50.940 | 54.355 | 0.935 | 0.937 |
| dft_output | 8 | 67.478 | 59.703 | 71.158 | 0.948 | 0.839 |
| full_output | 6 | 76.533 | 57.666 | 62.575 | 1.223 | 0.922 |
| full_output | 8 | 86.137 | 83.039 | 85.683 | 1.005 | 0.969 |

## Full-SAB Smoke

| r | tile4 PVW us | bodymajor PVW us | bodymajor/tile4 | tile4 scalar speedup | bodymajor scalar speedup |
|---:|---:|---:|---:|---:|---:|
| 6 | 0.000 | 0.000 | 0.000 |  |  |

## Interpretation

This is a falsifiable locality/layout experiment. A kernel-only win is not
enough for a SAB claim; promotion requires complete-SAB `T_total/r`,
correctness/noise, and resource gates.
