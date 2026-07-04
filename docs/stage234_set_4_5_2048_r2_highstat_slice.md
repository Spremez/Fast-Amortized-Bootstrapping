# Stage234 High-Stat Added-Parameter Slice

Decision: `PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING`.

Stage234 runs the second current-head high-stat added-parameter slice:
`SET_4_5_2048`, r=2, binary, `spqlios_avx512`, active-buffer PVW/MAT-SAB.
The endpoint is complete-SAB `T_bootstrap/r`, the amortized bootstrapping time
per processed plaintext lane/bit. Together with Stage233, this completes
current-head high-stat evidence for `SET_4_5_2048` at r=2 and r=4, but not the
full added-parameter matrix.

## Shape Gate

| param | r | observed_h | expected_h | observed_r_prec | expected_r_prec | correctness_status | shape_gate | runs_checked | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 2 | 42 | 42 | 7 | 7 | Pass | PASS | 10 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_0.log |

## Performance Runs

| run | status | param | r | metric | pvw_us | pvw_lane_us | scalar_repeated_us | scalar_lane_us | speedup_vs_scalar_repeated | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16494285.000 | 8247142.500 | 20916679.000 | 10458339.500 | 1.268 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_0.log |
| 1 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16437060.000 | 8218530.000 | 20892855.000 | 10446427.500 | 1.271 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_1.log |
| 2 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16561307.000 | 8280653.500 | 21163918.000 | 10581959.000 | 1.278 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_2.log |
| 3 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16762402.000 | 8381201.000 | 20906015.000 | 10453007.500 | 1.247 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_3.log |
| 4 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16493423.000 | 8246711.500 | 20887525.000 | 10443762.500 | 1.266 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_4.log |
| 5 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16660889.000 | 8330444.500 | 20862584.000 | 10431292.000 | 1.252 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_5.log |
| 6 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16563845.000 | 8281922.500 | 20788389.000 | 10394194.500 | 1.255 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_6.log |
| 7 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16672364.000 | 8336182.000 | 21110147.000 | 10555073.500 | 1.266 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_7.log |
| 8 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16282042.000 | 8141021.000 | 20988507.000 | 10494253.500 | 1.289 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_8.log |
| 9 | Pass | SET_4_5_2048 | 2 | T_bootstrap/r | 16709191.000 | 8354595.500 | 20971594.000 | 10485797.000 | 1.255 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/run_9.log |

## Performance Statistics

| param | r | runs | pass_runs | metric | pvw_mean_us | scalar_repeated_mean_us | mean_of_speedups | speedup_stdev | speedup_ci95_low | speedup_ci95_high | ratio_of_means_speedup | stats_label | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 2 | 10 | 10 | T_bootstrap/r | 16563680.800 | 20948821.300 | 1.264700 | 0.012841 | 1.255514 | 1.273886 | 1.264744 | high-stat slice n=10; SET_4_5_2048 r=2 | PASS_HIGHSTAT_SLICE |

## Noise Seeds

| param | r | seed | status | points | pvw_failures | scalar_failures | pair_failures | pvw_minus_scalar_log2 | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 2 | 6863025 | Pass | 4096 | 0 | 0 | 0 | -0.176 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863025.log |
| SET_4_5_2048 | 2 | 6863026 | Pass | 4096 | 0 | 0 | 0 | -0.164 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863026.log |
| SET_4_5_2048 | 2 | 6863027 | Pass | 4096 | 0 | 0 | 0 | 0.470 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863027.log |
| SET_4_5_2048 | 2 | 6863028 | Pass | 4096 | 0 | 0 | 0 | 0.201 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863028.log |
| SET_4_5_2048 | 2 | 6863029 | Pass | 4096 | 0 | 0 | 0 | -0.195 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863029.log |
| SET_4_5_2048 | 2 | 6863030 | Pass | 4096 | 0 | 0 | 0 | -0.005 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863030.log |
| SET_4_5_2048 | 2 | 6863031 | Pass | 4096 | 0 | 0 | 0 | 0.242 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863031.log |
| SET_4_5_2048 | 2 | 6863032 | Pass | 4096 | 0 | 0 | 0 | -0.261 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863032.log |
| SET_4_5_2048 | 2 | 6863033 | Pass | 4096 | 0 | 0 | 0 | -0.194 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863033.log |
| SET_4_5_2048 | 2 | 6863034 | Pass | 4096 | 0 | 0 | 0 | -0.012 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863034.log |
| SET_4_5_2048 | 2 | 6863035 | Pass | 4096 | 0 | 0 | 0 | -0.044 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863035.log |
| SET_4_5_2048 | 2 | 6863036 | Pass | 4096 | 0 | 0 | 0 | 0.136 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863036.log |
| SET_4_5_2048 | 2 | 6863037 | Pass | 4096 | 0 | 0 | 0 | 0.166 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863037.log |
| SET_4_5_2048 | 2 | 6863038 | Pass | 4096 | 0 | 0 | 0 | -0.228 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863038.log |
| SET_4_5_2048 | 2 | 6863039 | Pass | 4096 | 0 | 0 | 0 | 0.095 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863039.log |
| SET_4_5_2048 | 2 | 6863040 | Pass | 4096 | 0 | 0 | 0 | -0.114 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863040.log |
| SET_4_5_2048 | 2 | 6863041 | Pass | 4096 | 0 | 0 | 0 | -0.368 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863041.log |
| SET_4_5_2048 | 2 | 6863042 | Pass | 4096 | 0 | 0 | 0 | -0.329 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863042.log |
| SET_4_5_2048 | 2 | 6863043 | Pass | 4096 | 0 | 0 | 0 | 0.092 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863043.log |
| SET_4_5_2048 | 2 | 6863044 | Pass | 4096 | 0 | 0 | 0 | -0.224 | repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/r2/seed_6863044.log |

## Noise Aggregate

| param | r | seeds | points | pvw_failures | scalar_failures | pair_failures | avg_pvw_minus_scalar_log2 | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | status | stats_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 2 | 20 | 81920 | 0 | 0 | 0 | -0.045600 | -0.368000 | 0.470000 | PASS_HIGHSTAT_SLICE | high-stat slice seeds=20; SET_4_5_2048 r=2 |

## Resource Comparison

| param | r | mode | backend | keygen_us | keygen_lane_avg_us | estimated_key_bytes | estimated_key_bytes_ratio_vs_scalar_repeated | internal_vmhwm_kb | time_max_rss_kb | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 2 | pvw | spqlios_avx512 | 1635265 | 817632.500 | 314053072 | 1.014389 | 386128 | 386328 | repro/stage234_set_4_5_2048_r2_resource/r2/pvw.log |
| SET_4_5_2048 | 2 | scalar | spqlios_avx512 | 1295062 | 647531.000 | 309598192 | 1.000000 | 389544 | 389812 | repro/stage234_set_4_5_2048_r2_resource/r2/scalar.log |
| SET_4_5_2048 | 2 | pvw_vs_scalar_ratio | spqlios_avx512 | 1.262692 | 1.262692 | 1.014389 | 1.014389 | 0.991231 | 0.991062 | computed from resource pvw/scalar rows |

## SET_4_5_2048 Progress

| param | r | stage | performance_status | noise_status | resource_status | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | Stage233 | PASS_HIGHSTAT_SLICE | PASS_HIGHSTAT_SLICE | recorded | repro/stage233_set_4_5_2048_r4_highstat_slice/proof_gate.csv |
| SET_4_5_2048 | 2 | Stage234 | PASS_HIGHSTAT_SLICE | PASS_HIGHSTAT_SLICE | recorded | repro/stage234_set_4_5_2048_r2_highstat_slice/proof_gate.csv |

## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage233 route plus raw Stage234 logs exist | all present | PASS | allows Stage234 aggregation |
| G2_shape | SET_4_5_2048 selects h=42, r_prec=7 | h=42, r_prec=7 | PASS | prevents default-parameter fallback |
| G3_performance_highstat_slice | 10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=10, speedup_mean=1.264700, CI95=1.255514..1.273886 | PASS_HIGHSTAT_SLICE | supports this parameter/r slice only |
| G4_noise_highstat_slice | 20 deterministic seeds, zero PVW/scalar/pair failures | seeds=20, failures=0/0/0 | PASS_HIGHSTAT_SLICE | noise side condition supports this slice only |
| G5_resource | pvw and scalar resource/keygen/RSS rows for this slice | pvw/scalar resource rows present | PASS | records key/RSS side cost beside throughput |
| G6_param_progress | SET_4_5_2048 r=2 and r=4 both have high-stat slices | r=2 Stage234 and r=4 Stage233 recorded | PASS_PARAM_COMPLETE | supports SET_4_5_2048 binary r=2/r=4 matrix rows only |
| G7_matrix_boundary | do not promote the whole added-parameter matrix from one parameter set | SET_2_3_4096 r=2/r=4 still pending | BOUNDARY_HELD | blocks full added-parameter matrix and all-parameter claims |
| G8_stage234_decision | all Stage234 gates pass and matrix boundary stays explicit | PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING | PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING | continue remaining SET_2_3_4096 high-stat slices or manuscript skeleton |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | Stage233 route plus raw Stage234 logs exist | all present | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv | allows Stage234 aggregation |
| G2_shape | PASS | SET_4_5_2048 selects h=42, r_prec=7 | h=42, r_prec=7 | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv | prevents default-parameter fallback |
| G3_performance_highstat_slice | PASS_HIGHSTAT_SLICE | 10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=10, speedup_mean=1.264700, CI95=1.255514..1.273886 | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv | supports this parameter/r slice only |
| G4_noise_highstat_slice | PASS_HIGHSTAT_SLICE | 20 deterministic seeds, zero PVW/scalar/pair failures | seeds=20, failures=0/0/0 | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv | noise side condition supports this slice only |
| G5_resource | PASS | pvw and scalar resource/keygen/RSS rows for this slice | pvw/scalar resource rows present | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv | records key/RSS side cost beside throughput |
| G6_param_progress | PASS_PARAM_COMPLETE | SET_4_5_2048 r=2 and r=4 both have high-stat slices | r=2 Stage234 and r=4 Stage233 recorded | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv | supports SET_4_5_2048 binary r=2/r=4 matrix rows only |
| G7_matrix_boundary | BOUNDARY_HELD | do not promote the whole added-parameter matrix from one parameter set | SET_2_3_4096 r=2/r=4 still pending | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv | blocks full added-parameter matrix and all-parameter claims |
| G8_stage234_decision | PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING | all Stage234 gates pass and matrix boundary stays explicit | PASS_STAGE234_SECOND_HIGHSTAT_SLICE_SET_4_5_2048_COMPLETE_MATRIX_PENDING | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv | continue remaining SET_2_3_4096 high-stat slices or manuscript skeleton |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage235_set_2_3_4096_highstat_slices | The added-parameter matrix should be promoted beyond SET_4_5_2048. | Run 10-run/20-seed/resource for SET_2_3_4096 r=2 and r=4. | future | Keep Stage233/234 as SET_4_5_2048-only high-stat evidence. | repro/stage234_set_4_5_2048_r2_highstat_slice/proof_gate.csv |
| P1 | stage236_scoped_manuscript_skeleton | A paper/report draft is needed before spending more compute. | Use Stage233/234 only for SET_4_5_2048; cite Stage232 as SET_2_3_4096 preflight. | ready | Do not include incomplete SET_2_3_4096 rows as promoted results. | repro/stage234_set_4_5_2048_r2_highstat_slice/gate_matrix.csv |
| P2 | stage237_nonbinary_or_compact_design | The project expands beyond exact dense binary MAT/PVW-SAB. | Closed selector equations, security/noise model, isolated equivalence, and full SAB A/B. | blocked_until_design | Do not claim non-binary, compact, or optimal MAT-RLWE SAB. | repro/stage234_set_4_5_2048_r2_highstat_slice/next_stage_queue.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage233_set_4_5_2048_r4_highstat_slice/proof_gate.csv | present | Stage233 proof gate selecting remaining matrix slices | 1728 |
| repro/stage233_set_4_5_2048_r4_highstat_slice/next_stage_queue.csv | present | Stage233 next queue | 1084 |
| repro/stage233_set_4_5_2048_r4_highstat_slice/performance_stats.csv | present | Stage233 sibling r=4 high-stat slice | 448 |
| repro/stage234_set_4_5_2048_r2_runs10_seeds20/performance_summary.csv | present | Stage234 raw high-stat performance aggregate | 286 |
| repro/stage234_set_4_5_2048_r2_runs10_seeds20/perf_SET_4_5_2048_r2_runs10/summary.csv | present | Stage234 per-run performance | 973 |
| repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_summary.csv | present | Stage234 high-stat noise aggregate summary | 308 |
| repro/stage234_set_4_5_2048_r2_runs10_seeds20/noise_SET_4_5_2048_r2_seeds20/summary.csv | present | Stage234 per-seed noise | 3319 |
| repro/stage234_set_4_5_2048_r2_resource/summary.csv | present | Stage234 resource/keygen/RSS | 672 |
