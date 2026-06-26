# Stage77 R>4 Fused MAT Kernel Log

Date: 2026-06-26

## Purpose

Stage77 implements the H11 r>4 fused MAT external-product hypothesis
behind `MAT_TRGSW_AVX512_RGT4_FUSED`. It keeps scalar SAB and the
default promoted r=2/r=4 path unchanged. The stage is a smoke gate:
positive results can only justify repeated Stage78 gates, not immediate
promotion.

## Gates

| gate | status | metric | value | evidence | detail |
|---|---|---|---|---|---|
| stage77_generic_kernel_correctness | PASS | identity_lane_r6_r8 | Pass | repro/stage77_rgt4_fused_mat_kernel/generic.log | generic r=6/r=8 kernel smoke passes |
| stage77_fused_kernel_correctness | PASS | identity_lane_r6_r8 | Pass | repro/stage77_rgt4_fused_mat_kernel/fused.log | fused r=6/r=8 kernel smoke passes |
| stage77_kernel_fused_vs_generic | PASS | dft_ratios;full_ratios | 1.582;1.431|1.510;1.370 | repro/stage77_rgt4_fused_mat_kernel/kernel_comparison.csv | fused tiled kernel beats current generic r>4 kernel in DFT-output and full-output microbench |
| stage77_fused_dft_vs_scalar | PARTIAL_R6_ONLY | r6;r8 | 1.266;0.951 | repro/stage77_rgt4_fused_mat_kernel/kernel_comparison.csv | r=6 DFT-output beats repeated scalar, but r=8 remains below repeated scalar |
| stage77_full_sab_smoke | PASS | fused_vs_generic_r6_r8 | 1.120;1.102 | repro/stage77_rgt4_fused_mat_kernel/full_sab_smoke.csv | fused r=6/r=8 full-SAB one-run smokes pass and beat same-stage generic r>4 |
| stage77_r4_boundary | REPEATED_GATES_REQUIRED | fused_r6;fused_r8;r4_mean;r4_ci95_low | 1.385;1.290;1.377;1.314893 | repro/stage77_rgt4_fused_mat_kernel/full_sab_smoke.csv; repro/stage36_target_perf_summary.csv | r=6 one-run fused smoke reaches the r=4 reference region, but promotion requires repeated full-SAB/noise/resource gates; r=8 remains below the r=4 reference |
| stage77_decision | PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED | promotion_policy |  | repro/stage77_rgt4_fused_mat_kernel/summary.csv | Stage77 promotes H11 from theory to a positive smoke candidate only; no default/full promotion until repeated full-SAB, noise, and resource gates pass |

## Kernel Comparison

| bench | r | generic us | fused us | fused/generic | generic scalar speedup | fused scalar speedup |
|---|---:|---:|---:|---:|---:|---:|
| dft_output | 6 | 52.088 | 32.933 | 1.582 | 0.852 | 1.266 |
| dft_output | 8 | 79.644 | 55.650 | 1.431 | 0.915 | 0.951 |
| full_output | 6 | 68.358 | 45.273 | 1.510 | 1.233 | 1.479 |
| full_output | 8 | 90.819 | 66.307 | 1.370 | 1.199 | 1.271 |

## Full-SAB Smoke

| r | generic PVW us | fused PVW us | fused/generic | generic scalar speedup | fused scalar speedup |
|---:|---:|---:|---:|---:|---:|
| 6 | 43981711.000 | 39254282.000 | 1.120 | 1.266 | 1.385 |
| 8 | 59835924.000 | 54292313.000 | 1.102 | 1.208 | 1.290 |

## Interpretation

The tiled fused r>4 kernel improves the current generic r>4 MAT kernel
in this smoke run: DFT-output fused/generic is `1.582x` for r=6 and
`1.431x` for r=8; full-output fused/generic is `1.510x` and
`1.370x`. Complete SAB one-run smokes also improve over same-stage
generic: r=6 `1.120x` and r=8 `1.102x` fused/generic.

This is not a final promotion. r=8 DFT-output remains below repeated
scalar (`0.951x`), r=8 full-SAB speedup remains below the current r=4
reference, and all full-SAB evidence is one-run smoke. The next stage
must repeat the full-SAB/noise/resource gates, with r=6 as the main
candidate and r=8 as a diagnostic stress case.
