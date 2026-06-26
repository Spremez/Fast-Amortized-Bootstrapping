# Stage78 R>4 Fused Repeated Gates Log

Date: 2026-06-26

## Purpose

Stage78 is the repeated-gate follow-up to the Stage77 H11 fused
`MAT_TRGSW_AVX512_RGT4_FUSED` smoke. It keeps the scalar SAB path and
the default r=2/r=4 PVW path unchanged. The main candidate is r=6;
r=8 is retained as a diagnostic stress case.

## Gates

| gate | status | metric | value | evidence | detail |
|---|---|---|---|---|---|
| stage78_stage77_precondition | PASS | stage77_decision | PASS_RGT4_FUSED_SMOKE_RECORDED_REPEATED_GATES_REQUIRED | repro/stage77_rgt4_fused_mat_kernel/summary.csv | Stage77 recorded H11 as positive smoke and explicitly requires Stage78 repeated gates. |
| stage78_r6_repeated_full_sab | PASS | samples;mean_speedup;min_speedup;r4_mean;r4_ci95_low | 3;1.408;1.361;1.377;1.314893 | repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/summary.csv | r=6 fused full-SAB repeated gate is the main Stage78 promotion screen. |
| stage78_r8_stress_full_sab | PASS | samples;mean_speedup;min_speedup | 1;1.350;1.350 | repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r8_runs1/summary.csv | r=8 fused full-SAB is kept as a stress case, not the primary promotion target. |
| stage78_r6_noise | PASS | seeds;failures;avg_gap_log2 | 3;0;-0.006333 | repro/stage78_rgt4_fused_repeated_gates/final_noise/aggregate.csv | r=6 final-output noise/correctness gate must have zero PVW/scalar/pair failures. |
| stage78_r8_noise | PASS | seeds;failures;avg_gap_log2 | 3;0;-0.064667 | repro/stage78_rgt4_fused_repeated_gates/final_noise/aggregate.csv | r=8 final-output noise/correctness gate is diagnostic for large-r stress. |
| stage78_resource | PASS | r6_key_ratio;r6_rss_ratio;r8_key_ratio;r8_rss_ratio | 1.122537;1.030750;1.181090;1.071251 | repro/stage78_rgt4_fused_repeated_gates/resource_summary.csv | Resource rows exist for PVW and repeated scalar; ratios are recorded with the speedup evidence. |
| stage78_decision | PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE | promotion_policy |  | repro/stage78_rgt4_fused_repeated_gates/summary.csv | r=6 fused repeated full-SAB/noise/resource gates pass and mean speedup reaches or exceeds the r=4 reference mean; run a high-stat confirmation before changing defaults. |

## Full-SAB Repeated

| r | samples | status | PVW mean us | scalar repeated mean us | mean speedup | min | max | stddev | Stage77 one-run | r4 mean | r4 CI95 low | source |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 6 | 3 | PASS | 38992508.667 | 54912575.333 | 1.408 | 1.361 | 1.435 | 0.041102 | 1.385 | 1.377 | 1.314893 | repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r6_runs3/summary.csv |
| 8 | 1 | PASS | 54048221.000 | 72975915.000 | 1.350 | 1.350 | 1.350 | 0.000000 | 1.290 | 1.377 | 1.314893 | repro/stage78_rgt4_fused_repeated_gates/full_sab_fused_r8_runs1/summary.csv |

## Noise

| r | seeds | points | failures | avg PVW-minus-scalar log2 | status | source |
|---:|---:|---:|---:|---:|---|---|
| 6 | 3 | 36864 | 0 | -0.006333 | PASS | repro/stage78_rgt4_fused_repeated_gates/final_noise/aggregate.csv |
| 8 | 3 | 49152 | 0 | -0.064667 | PASS | repro/stage78_rgt4_fused_repeated_gates/final_noise/aggregate.csv |

## Resource

| r | key ratio | keygen ratio | PVW RSS KB | scalar RSS KB | RSS ratio | status | source |
|---:|---:|---:|---:|---:|---:|---|---|
| 6 | 1.122537 | 1.185968 | 1191720 | 1156168 | 1.030750 | PASS | repro/stage78_rgt4_fused_repeated_gates/resource/summary.csv |
| 8 | 1.181090 | 1.361129 | 1650352 | 1540584 | 1.071251 | PASS | repro/stage78_rgt4_fused_repeated_gates/resource/summary.csv |

## Decision

`PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE`

r=6 fused repeated full-SAB/noise/resource gates pass and mean speedup reaches or exceeds the r=4 reference mean; run a high-stat confirmation before changing defaults.

This stage does not change defaults. Any promotion requires the
decision row to identify a promotion candidate and a follow-up
high-stat confirmation before the claim package or default path is
changed.
