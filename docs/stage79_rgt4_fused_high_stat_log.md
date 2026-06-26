# Stage79 R>4 Fused High-Stat Confirmation Log

Date: 2026-06-26

## Purpose

Stage79 confirms or rejects the Stage78 r=6 fused-MAT promotion
candidate using higher-stat complete-SAB evidence plus expanded
noise and repeated resource gates. It does not change scalar SAB,
the r=2/r=4 explicit path, or defaults.

## Gates

| gate | status | metric | value | evidence | detail |
|---|---|---|---|---|---|
| stage79_stage78_precondition | PASS | stage78_decision | PASS_RGT4_FUSED_REPEATED_GATES_RECORDED_PROMOTION_CANDIDATE | repro/stage78_rgt4_fused_repeated_gates/summary.csv | Stage79 can only confirm a candidate if Stage78 recorded H11 r=6 as a promotion candidate. |
| stage79_r6_high_stat_full_sab | PASS_R4_REGION_NOT_CONFIRMED | samples;mean;ci95_low;min;r4_mean;r4_ci95_low | 10;1.367;1.341302;1.314;1.377;1.314893 | repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/summary.csv | Main high-stat complete-SAB A/B gate for r=6 fused MAT. |
| stage79_r6_final_noise | PASS | seeds;points;failures;avg_gap_log2 | 20;245760;0;-0.107800 | repro/stage79_rgt4_fused_high_stat/final_noise/aggregate.csv | Expanded final-output noise gate for r=6 fused MAT. |
| stage79_r6_resource | PASS | runs;key_ratio_mean;rss_ratio_mean;rss_ratio_max | 3;1.122537;1.030715;1.030764 | repro/stage79_rgt4_fused_high_stat/resource_summary.csv | Repeated resource gate for r=6 fused MAT against repeated scalar. |
| stage79_decision | PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED | promotion_policy |  | repro/stage79_rgt4_fused_high_stat/summary.csv | r=6 fused MAT correctness/noise/resource evidence is usable, but the performance boundary is not strong enough for automatic promotion; Stage80 must keep or reject it explicitly. |

## Complete-SAB A/B

| r | samples | status | PVW mean us | scalar repeated mean us | mean speedup | min | max | stddev | CI95 low | CI95 high | Stage36 r4 mean | Stage36 r4 CI95 low | Stage78 r6 mean | source |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 6 | 10 | PASS_R4_REGION_NOT_CONFIRMED | 43228883.300 | 59042652.200 | 1.367 | 1.314 | 1.457 | 0.040977 | 1.341302 | 1.392098 | 1.377 | 1.314893 | 1.408 | repro/stage79_rgt4_fused_high_stat/full_sab_fused_r6_runs10/summary.csv |

## Noise

| r | seeds | points | failures | min gap | max gap | avg gap | status | source |
|---:|---:|---:|---:|---:|---:|---:|---|---|
| 6 | 20 | 245760 | 0 | -0.417 | 0.478 | -0.107800 | PASS | repro/stage79_rgt4_fused_high_stat/final_noise/aggregate.csv |

## Resource

| r | runs | key ratio mean | keygen ratio mean | RSS ratio mean | RSS ratio max | status | sources |
|---:|---:|---:|---:|---:|---:|---|---|
| 6 | 3 | 1.122537 | 1.287628 | 1.030715 | 1.030764 | PASS | repro/stage79_rgt4_fused_high_stat/resource_run_0/summary.csv;repro/stage79_rgt4_fused_high_stat/resource_run_1/summary.csv;repro/stage79_rgt4_fused_high_stat/resource_run_2/summary.csv |

## Decision

`PASS_RGT4_FUSED_HIGH_STAT_RECORDED_REVIEW_REQUIRED`

r=6 fused MAT correctness/noise/resource evidence is usable, but the performance boundary is not strong enough for automatic promotion; Stage80 must keep or reject it explicitly.
