# Stage146 r4-Unrolled Variance Attribution

Date: 2026-07-03

## Decision

`PASS_STAGE146_VARIANCE_ATTRIBUTED_KEEP_R4_EXPLICIT_ROUTE_TO_SCHEDULE_OR_HIGHER_STAT`

## Summary Gates

| gate | status | metric | value | detail | next_action |
| --- | --- | --- | --- | --- | --- |
| stage146_inputs | PASS | stage144_perf_results | repro/stage144_full_sab_repeated_r4_unrolled_gate/perf_results.csv | Stage146 consumes Stage144 repeated run-level rows. |  |
| stage146_variance | PASS_VARIANCE_OUTLIER_IDENTIFIED | r4_outlier_count | 1 | Outlier rule flags r4-only relative-median deviation. |  |
| stage146_profile | PASS | mat_ep_ratio;body_ratio | 1.110866;1.047740 | One profiled generic/r4 pair attributes body hot-path timing; not a final latency claim. |  |
| stage146_decision | PASS_STAGE146_VARIANCE_ATTRIBUTED_KEEP_R4_EXPLICIT_ROUTE_TO_SCHEDULE_OR_HIGHER_STAT | routing | explicit_r4_unrolled_not_promoted | Stage146 selects the next research route without changing scalar/default behavior. | Do not promote r4-unrolled; use it as a kernel ablation while Stage147 targets full-SAB schedule attribution or stronger repeated stats. |

## Stage144 Robust Variance

| metric | value | detail | status |
| --- | --- | --- | --- |
| stage144_decision | WEAK_STAGE144_PERF_POSITIVE_BUT_CI_CROSSES_ONE | Input repeated gate decision. | PASS |
| paired_runs | 3 | Ordinal generic/r4 Stage144 rows compared. | PASS |
| paired_median_r4_over_generic_speedup | 1.032626 | Median is robust to the slow r4 sample. | PASS |
| paired_mean_without_r4_outlier | 1.038317 | Mean after removing rows flagged by relative-median rule. | PASS_VARIANCE_OUTLIER_IDENTIFIED |
| generic_lane_cv_pct | 0.578544 | Stage144 generic PVW lane coefficient of variation. | PASS |
| r4_lane_cv_pct | 7.464700 | Stage144 r4-unrolled PVW lane coefficient of variation. | PASS_VARIANCE_OUTLIER_IDENTIFIED |
| generic_scalar_lane_cv_pct | 0.481682 | Stage144 scalar lane variation in generic runs. | PASS |
| r4_scalar_lane_cv_pct | 1.519900 | Stage144 scalar lane variation in r4 runs. | PASS |
| r4_outlier_count | 1 | Rows with r4-only deviation >=8% and generic deviation <=3%. | PASS_VARIANCE_OUTLIER_IDENTIFIED |

## Run-Level Attribution

| run | generic_lane_us | r4_lane_us | paired_r4_over_generic_speedup | generic_rel_to_median_pct | r4_rel_to_median_pct | generic_scalar_lane_us | r4_scalar_lane_us | r4_outlier_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 7424115.500 | 7189547.500 | 1.032626 | 0.000000 | 0.000000 | 9693569.250 | 9593246.250 | no |
| 1 | 7488335.000 | 8103267.500 | 0.924113 | 0.865012 | 12.709006 | 9748716.000 | 9813209.000 | yes |
| 2 | 7406579.750 | 7094378.250 | 1.044007 | -0.236200 | -1.323717 | 9655817.000 | 9875675.250 | no |

## Body Profile Rows

| variant | status | lanes | in_N | h | r_prec | bench_pvw_us | bench_pvw_lane_us | body_full_us | mat_ep_calls | mat_ep_us | mat_ep_share | non_mat_body_us | cmux_calls | cmux_us | ncmux_calls | ncmux_us | cmux_sub_us | cmux_from_dft_us | cmux_add_us | ncmux_auto_us | sub_a_calls | sub_a_us | copyback_calls | copyback_us | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| generic_active_profile | PASS | 4 | 2048 | 39 | 7 | 29699091.000 | 7424772.750 | 29405098 | 573440 | 14257427 | 0.484862 | 15147671.000000 | 573440 | 28546752 | 5080 | 434535 | 3884311 | 6321929 | 3989829 | 163596 | 39 | 645107 | 0 | 0 | repro/stage146_r4_unrolled_variance_attribution/profile_generic_active_profile.log |
| r4_unrolled_active_profile | PASS | 4 | 2048 | 39 | 7 | 28333721.000 | 7083430.250 | 28065272 | 573440 | 12834514 | 0.457309 | 15230758.000000 | 573440 | 27221580 | 5080 | 416593 | 3908856 | 6425907 | 3955279 | 162910 | 39 | 629398 | 0 | 0 | repro/stage146_r4_unrolled_variance_attribution/profile_r4_unrolled_active_profile.log |

## Profile Comparison

| metric | generic | r4_unrolled | ratio_or_delta | status | detail |
| --- | --- | --- | --- | --- | --- |
| profile_status | PASS | PASS | 0 | PASS | Correctness and body-profile lines were parsed. |
| bench_pvw_lane_speedup_generic_over_r4 | 7424772.750 | 7083430.250 | 1.048189 | PROFILE_ONLY | One profiled full-SAB run; not a final performance claim. |
| body_full_speedup_generic_over_r4 | 29405098 | 28065272 | 1.047740 | PROFILE_ONLY | Body hot-path timing excludes post-processing. |
| mat_ep_speedup_generic_over_r4 | 14257427 | 12834514 | 1.110866 | PROFILE_ONLY | If >1, the profiled r4-unrolled MAT EP is faster. |
| non_mat_body_speedup_generic_over_r4 | 15147671.000000 | 15230758.000000 | 0.994545 | PROFILE_ONLY | Non-MAT body work includes sub/from_DFT/add/rotation/schedule overhead. |
| mat_ep_share_delta_r4_minus_generic | 0.484862 | 0.457309 | -0.027553 | PROFILE_ONLY | Share delta is diagnostic only because profile instrumentation changes absolute timing. |
| mat_ep_calls_equal | 573440 | 573440 | 1 | PASS | Schedule counts must remain unchanged across kernel variants. |
| copyback_calls_equal_zero | 0 | 0 | 1 | PASS | Active-buffer fusion should keep copyback eliminated. |

## Interpretation

Stage146 is a routing gate. It keeps the r4-unrolled kernel as an explicit ablation unless later repeated full-SAB evidence becomes stable. It does not alter scalar SAB or default PVW/MAT-SAB behavior.
