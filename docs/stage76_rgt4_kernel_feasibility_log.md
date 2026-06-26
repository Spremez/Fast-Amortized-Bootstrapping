# Stage76 R>4 Kernel Feasibility Log

Date: 2026-06-26

## Purpose

Stage76 checks the existing MAT external-product kernel at r=6/r=8
without changing scalar SAB, the default `sab_pvw_*` path, or the MAT
key format. It separates DFT-output kernel evidence from full-output
shared-decomposition/DFT evidence so that a narrow microbenchmark result
cannot be overclaimed as complete SAB acceleration.

## Gates

| gate | status | metric | value | evidence | detail |
|---|---|---|---|---|---|
| stage76_rgt4_kernel_correctness | PASS | identity_lane_r6_r8 | Pass | repro/stage76_rgt4_kernel_feasibility/rgt4_kernel_smoke.log | r=6/r=8 MAT_TRGSW/PVW identity-lane kernel smoke passes |
| stage76_r6_dft_output_kernel | NEGATIVE_DFT_OUTPUT_NOT_PROMOTED | speedup_vs_scalar_repeated | 0.984 | repro/stage76_rgt4_kernel_feasibility/kernel_microbench.csv | r=6 DFT-output MAT path does not beat repeated scalar external products; no direct r>4 kernel promotion |
| stage76_r6_full_output_kernel | SMOKE_POSITIVE_FULL_OUTPUT | speedup_vs_scalar_repeated | 1.168 | repro/stage76_rgt4_kernel_feasibility/kernel_microbench.csv | r=6 full-output smoke is positive but only a kernel-level/shared-DFT signal |
| stage76_r8_dft_output_kernel | NEGATIVE_DFT_OUTPUT_NOT_PROMOTED | speedup_vs_scalar_repeated | 0.912 | repro/stage76_rgt4_kernel_feasibility/kernel_microbench.csv | r=8 DFT-output MAT path does not beat repeated scalar external products; no direct r>4 kernel promotion |
| stage76_r8_full_output_kernel | SMOKE_POSITIVE_LOW_MARGIN_FULL_OUTPUT | speedup_vs_scalar_repeated | 1.044 | repro/stage76_rgt4_kernel_feasibility/kernel_microbench.csv | r=8 full-output smoke is positive but only a kernel-level/shared-DFT signal |
| stage76_mul_share_boundary | PASS | mat_shared_mask_mul_pct_r6_r8 | 55.72;61.20 | repro/stage76_rgt4_kernel_feasibility/ep_breakdown.csv | r>4 MAT shared-mask path is multiply dominated; future work must target fused MAT multiply/layout/register blocking |
| stage76_decision | PASS_RGT4_KERNEL_FEASIBILITY_RECORDED_NO_PROMOTION | promotion_policy |  | repro/stage76_rgt4_kernel_feasibility/summary.csv | Stage76 records r>4 kernel feasibility and rejects direct promotion; next large-r candidate must be a dedicated fused MAT multiply/layout hypothesis |

## Kernel Microbench

| bench | r | scalar repeated us | MAT us | speedup |
|---|---:|---:|---:|---:|
| mat_only | 6 | n/a | 42 | n/a |
| mat_only | 8 | n/a | 63 | n/a |
| dft_output | 6 | 39.955 | 40.595 | 0.984 |
| dft_output | 8 | 55.301 | 60.615 | 0.912 |
| full_output | 6 | 65.522 | 56.080 | 1.168 |
| full_output | 8 | 86.914 | 83.290 | 1.044 |

## External-Product Phase Breakdown

| mode | r | phase us | decompose % | DFT % | mul % |
|---|---:|---:|---:|---:|---:|
| scalar_repeated | 6 | 48.562 | 14.62 | 53.58 | 31.80 |
| mat_shared_mask | 6 | 44.327 | 9.61 | 34.67 | 55.72 |
| scalar_repeated | 8 | 73.015 | 14.91 | 53.76 | 31.33 |
| mat_shared_mask | 8 | 72.031 | 8.70 | 30.10 | 61.20 |

## Interpretation

The r=6/r=8 identity-lane checks pass, so the existing generic r>4
MAT external-product path is functionally usable. Performance does
not justify promotion: DFT-output MAT is `0.984x` for r=6 and
`0.912x` for r=8 versus repeated scalar external products. Full-output
measurements remain slightly positive only because they include shared
decomposition/DFT effects: r=6 reaches `1.168x`, while r=8 reaches
only `1.044x`.

The phase breakdown shows the MAT shared-mask path becomes multiply
dominated at r>4 (`55.72%` for r=6 and `61.20%` for r=8). Therefore
the next large-r optimization must target the dense MAT multiply and
its layout/register/cache behavior, not another direct lane-count
increase or a repeat of the Stage65A row-unrolled r=4 direction.
