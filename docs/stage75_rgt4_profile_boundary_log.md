# Stage75 R>4 Profile Boundary Log

Date: 2026-06-26

## Purpose

Stage75 diagnoses the Stage74 r>4 lane-scaling boundary with body-profile
evidence. It does not modify scalar SAB, `sab_pvw_*`, the MAT key format,
or the promotion policy.

## Gates

| gate | status | metric | value | evidence | detail |
|---|---|---|---|---|---|
| stage75_r6_body_profile | PASS | status;cmux;mat_ep;ncmux;sub_a;copyback | PASS;573440;573440;5080;39;0 | repro/stage75_rgt4_profile_boundary/body_profile_r6/summary.csv | r=6 profile correctness/count gates pass with CMUX/MAT EP=573440 |
| stage75_r8_body_profile | PASS | status;cmux;mat_ep;ncmux;sub_a;copyback | PASS;573440;573440;5080;39;0 | repro/stage75_rgt4_profile_boundary/body_profile_r8/summary.csv | r=8 profile correctness/count gates pass with CMUX/MAT EP=573440 |
| stage75_schedule_count_invariant | PASS | expected_cmux | 573440 | repro/stage75_rgt4_profile_boundary/body_profile_r6/summary.csv; repro/stage75_rgt4_profile_boundary/body_profile_r8/summary.csv | r=6/r=8 keep the same SAB update count as r=2/r=4; degradation is not caused by extra schedule iterations |
| stage75_rgt4_profile_boundary | NOT_PROMOTED_PROFILE_BOUNDARY | r6_speedup;r8_speedup;r4_ci95_low;mat_ep_share | 1.304;1.189;1.314893;r=6 mat_ep/full=0.549836 r=8 mat_ep/full=0.550237 | repro/stage75_rgt4_profile_boundary/profile_metrics.csv; repro/stage74_r_scaling_boundary/decision.csv; repro/stage36_target_perf_summary.csv | r>4 profile preserves exact SAB counts, while full-SAB speedup remains below or too close to the r=4 promoted boundary; future large-r work needs a dedicated r>4 MAT layout/kernel hypothesis |
| stage75_decision | PASS_RGT4_PROFILE_BOUNDARY_RECORDED_NOT_PROMOTED | promotion_policy |  | repro/stage75_rgt4_profile_boundary/decision.csv | Stage75 attributes direct r>4 underperformance to per-update body/MAT cost under invariant SAB schedule counts; no r>4 promotion |

## Profile Metrics

| r | speedup | pvw_avg_us | mat_ep_us | cmux_us | full_us | mat_ep/full | lane_avg_us |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 1.304 | 42192077.000 | 24402373 | 43122085 | 44381150 | 0.549836 | 7032012.833 |
| 8 | 1.189 | 60069207.000 | 35695370 | 63258000 | 64872771 | 0.550237 | 7508650.875 |

## Interpretation

The r=6 and r=8 profiles preserve the target SAB schedule counts:
`40 * 7 * 2048 = 573440` CMUX/MAT external-product updates,
`5080` NCMUX updates, `39` sub_a calls, and `0` active-buffer
copybacks. Therefore the r>4 boundary is not a schedule-count issue.

The observed larger-r slowdown is consistent with the dense MAT body
cost and generic large-r loop pressure increasing per update. Future
large-r work should start from a dedicated r>4 MAT layout/kernel or
sparse/structured-MAT hypothesis; directly increasing lane count is
not promoted.
