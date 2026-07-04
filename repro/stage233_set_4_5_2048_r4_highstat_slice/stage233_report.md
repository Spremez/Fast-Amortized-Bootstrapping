# Stage233 High-Stat Added-Parameter Slice

Decision: `PASS_STAGE233_FIRST_HIGHSTAT_SLICE_RESOURCE_RECORDED_MATRIX_PENDING`.

Stage233 runs the first current-head high-stat added-parameter slice:
`SET_4_5_2048`, r=4, binary, `spqlios_avx512`, active-buffer PVW/MAT-SAB.
The endpoint is complete-SAB `T_bootstrap/r`, the amortized bootstrapping time
per processed plaintext lane/bit. This promotes only this parameter/r slice; it
does not complete the full added-parameter matrix.

## Shape Gate

| param | r | observed_h | expected_h | observed_r_prec | expected_r_prec | correctness_status | shape_gate | runs_checked | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | 42 | 42 | 7 | 7 | Pass | PASS | 10 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_0.log |

## Performance Runs

| run | status | param | r | metric | pvw_us | pvw_lane_us | scalar_repeated_us | scalar_lane_us | speedup_vs_scalar_repeated | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 33411925.000 | 8352981.250 | 46485118.000 | 11621279.500 | 1.391 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_0.log |
| 1 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 30379305.000 | 7594826.250 | 41416153.000 | 10354038.250 | 1.363 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_1.log |
| 2 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 30979418.000 | 7744854.500 | 42361901.000 | 10590475.250 | 1.367 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_2.log |
| 3 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 30881561.000 | 7720390.250 | 42452369.000 | 10613092.250 | 1.375 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_3.log |
| 4 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 31070802.000 | 7767700.500 | 41391957.000 | 10347989.250 | 1.332 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_4.log |
| 5 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 31102944.000 | 7775736.000 | 41470122.000 | 10367530.500 | 1.333 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_5.log |
| 6 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 30850675.000 | 7712668.750 | 41746811.000 | 10436702.750 | 1.353 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_6.log |
| 7 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 30822018.000 | 7705504.500 | 41403644.000 | 10350911.000 | 1.343 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_7.log |
| 8 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 31352315.000 | 7838078.750 | 42343733.000 | 10585933.250 | 1.351 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_8.log |
| 9 | Pass | SET_4_5_2048 | 4 | T_bootstrap/r | 30836959.000 | 7709239.750 | 42163649.000 | 10540912.250 | 1.367 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/run_9.log |

## Performance Statistics

| param | r | runs | pass_runs | metric | pvw_mean_us | scalar_repeated_mean_us | mean_of_speedups | speedup_stdev | speedup_ci95_low | speedup_ci95_high | ratio_of_means_speedup | stats_label | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | 10 | 10 | T_bootstrap/r | 31168792.200 | 42323545.700 | 1.357500 | 0.018745 | 1.344091 | 1.370909 | 1.357882 | high-stat slice n=10; one parameter/r only | PASS_HIGHSTAT_SLICE |

## Noise Seeds

| param | r | seed | status | points | pvw_failures | scalar_failures | pair_failures | pvw_minus_scalar_log2 | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | 6863025 | Pass | 8192 | 0 | 0 | 0 | 0.049 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863025.log |
| SET_4_5_2048 | 4 | 6863026 | Pass | 8192 | 0 | 0 | 0 | 0.014 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863026.log |
| SET_4_5_2048 | 4 | 6863027 | Pass | 8192 | 0 | 0 | 0 | -0.087 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863027.log |
| SET_4_5_2048 | 4 | 6863028 | Pass | 8192 | 0 | 0 | 0 | -0.177 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863028.log |
| SET_4_5_2048 | 4 | 6863029 | Pass | 8192 | 0 | 0 | 0 | -0.073 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863029.log |
| SET_4_5_2048 | 4 | 6863030 | Pass | 8192 | 0 | 0 | 0 | -0.077 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863030.log |
| SET_4_5_2048 | 4 | 6863031 | Pass | 8192 | 0 | 0 | 0 | -0.227 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863031.log |
| SET_4_5_2048 | 4 | 6863032 | Pass | 8192 | 0 | 0 | 0 | -0.109 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863032.log |
| SET_4_5_2048 | 4 | 6863033 | Pass | 8192 | 0 | 0 | 0 | -0.478 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863033.log |
| SET_4_5_2048 | 4 | 6863034 | Pass | 8192 | 0 | 0 | 0 | -0.202 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863034.log |
| SET_4_5_2048 | 4 | 6863035 | Pass | 8192 | 0 | 0 | 0 | -0.143 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863035.log |
| SET_4_5_2048 | 4 | 6863036 | Pass | 8192 | 0 | 0 | 0 | -0.079 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863036.log |
| SET_4_5_2048 | 4 | 6863037 | Pass | 8192 | 0 | 0 | 0 | -0.028 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863037.log |
| SET_4_5_2048 | 4 | 6863038 | Pass | 8192 | 0 | 0 | 0 | -0.185 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863038.log |
| SET_4_5_2048 | 4 | 6863039 | Pass | 8192 | 0 | 0 | 0 | 0.064 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863039.log |
| SET_4_5_2048 | 4 | 6863040 | Pass | 8192 | 0 | 0 | 0 | -0.220 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863040.log |
| SET_4_5_2048 | 4 | 6863041 | Pass | 8192 | 0 | 0 | 0 | -0.015 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863041.log |
| SET_4_5_2048 | 4 | 6863042 | Pass | 8192 | 0 | 0 | 0 | 0.126 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863042.log |
| SET_4_5_2048 | 4 | 6863043 | Pass | 8192 | 0 | 0 | 0 | 0.335 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863043.log |
| SET_4_5_2048 | 4 | 6863044 | Pass | 8192 | 0 | 0 | 0 | -0.123 | repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/r4/seed_6863044.log |

## Noise Aggregate

| param | r | seeds | points | pvw_failures | scalar_failures | pair_failures | avg_pvw_minus_scalar_log2 | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | status | stats_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | 20 | 163840 | 0 | 0 | 0 | -0.081750 | -0.478000 | 0.335000 | PASS_HIGHSTAT_SLICE | high-stat slice seeds=20; one parameter/r only |

## Resource Comparison

| param | r | mode | backend | keygen_us | keygen_lane_avg_us | estimated_key_bytes | estimated_key_bytes_ratio_vs_scalar_repeated | internal_vmhwm_kb | time_max_rss_kb | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | pvw | spqlios_avx512 | 3211198 | 802799.500 | 662184192 | 1.069425 | 777700 | 777968 | repro/stage233_set_4_5_2048_r4_resource/r4/pvw.log |
| SET_4_5_2048 | 4 | scalar | spqlios_avx512 | 2398427 | 599606.750 | 619196384 | 1.000000 | 777040 | 777284 | repro/stage233_set_4_5_2048_r4_resource/r4/scalar.log |
| SET_4_5_2048 | 4 | pvw_vs_scalar_ratio | spqlios_avx512 | 1.338877 | 1.338877 | 1.069425 | 1.069425 | 1.000849 | 1.000880 | computed from resource pvw/scalar rows |

## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage232 route plus raw Stage233 logs exist | all present | PASS | allows high-stat slice aggregation |
| G2_shape | SET_4_5_2048 selects h=42, r_prec=7 | h=42, r_prec=7 | PASS | prevents default-parameter fallback |
| G3_performance_highstat_slice | 10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=10, speedup_mean=1.357500, CI95=1.344091..1.370909 | PASS_HIGHSTAT_SLICE | supports this parameter/r slice only |
| G4_noise_highstat_slice | 20 deterministic seeds, zero PVW/scalar/pair failures | seeds=20, failures=0/0/0 | PASS_HIGHSTAT_SLICE | noise side condition supports this slice only |
| G5_resource | pvw and scalar resource/keygen/RSS rows for this slice | pvw/scalar resource rows present | PASS | records key/RSS side cost beside throughput |
| G6_matrix_boundary | do not promote the whole added-parameter matrix from one slice | remaining r/parameter slices pending | BOUNDARY_HELD | blocks full-matrix and all-parameter claims |
| G7_stage233_decision | all high-stat slice gates pass and matrix boundary stays explicit | PASS_STAGE233_FIRST_HIGHSTAT_SLICE_RESOURCE_RECORDED_MATRIX_PENDING | PASS_STAGE233_FIRST_HIGHSTAT_SLICE_RESOURCE_RECORDED_MATRIX_PENDING | continue remaining high-stat matrix slices or manuscript skeleton with scoped wording |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | Stage232 route plus raw Stage233 logs exist | all present | repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv | allows high-stat slice aggregation |
| G2_shape | PASS | SET_4_5_2048 selects h=42, r_prec=7 | h=42, r_prec=7 | repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv | prevents default-parameter fallback |
| G3_performance_highstat_slice | PASS_HIGHSTAT_SLICE | 10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=10, speedup_mean=1.357500, CI95=1.344091..1.370909 | repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv | supports this parameter/r slice only |
| G4_noise_highstat_slice | PASS_HIGHSTAT_SLICE | 20 deterministic seeds, zero PVW/scalar/pair failures | seeds=20, failures=0/0/0 | repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv | noise side condition supports this slice only |
| G5_resource | PASS | pvw and scalar resource/keygen/RSS rows for this slice | pvw/scalar resource rows present | repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv | records key/RSS side cost beside throughput |
| G6_matrix_boundary | BOUNDARY_HELD | do not promote the whole added-parameter matrix from one slice | remaining r/parameter slices pending | repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv | blocks full-matrix and all-parameter claims |
| G7_stage233_decision | PASS_STAGE233_FIRST_HIGHSTAT_SLICE_RESOURCE_RECORDED_MATRIX_PENDING | all high-stat slice gates pass and matrix boundary stays explicit | PASS_STAGE233_FIRST_HIGHSTAT_SLICE_RESOURCE_RECORDED_MATRIX_PENDING | repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv | continue remaining high-stat matrix slices or manuscript skeleton with scoped wording |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage234_remaining_highstat_matrix_slices | The added-parameter matrix should be promoted beyond one r=4 slice. | Run 10-run/20-seed/resource for remaining selected slices: SET_4_5_2048 r=2, SET_2_3_4096 r=2, SET_2_3_4096 r=4. | future | Keep Stage233 as single-slice high-stat evidence only. | repro/stage233_set_4_5_2048_r4_highstat_slice/proof_gate.csv |
| P1 | stage235_scoped_manuscript_skeleton | A paper/report draft is needed before spending more compute. | Use Stage233 only for SET_4_5_2048 r=4; cite Stage232 as preflight and Stage229/230 for boundaries. | ready | Do not include incomplete matrix rows as promoted results. | repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv |
| P2 | stage236_nonbinary_or_compact_design | The project expands beyond exact dense binary MAT/PVW-SAB. | Closed selector equations, security/noise model, isolated equivalence, and full SAB A/B. | blocked_until_design | Do not claim non-binary, compact, or optimal MAT-RLWE SAB. | repro/stage233_set_4_5_2048_r4_highstat_slice/next_stage_queue.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage232_selected_subset_fullstat_resource/proof_gate.csv | present | Stage232 proof gate selecting matrix continuation | 1807 |
| repro/stage232_selected_subset_fullstat_resource/next_stage_queue.csv | present | Stage232 next queue | 1145 |
| repro/stage233_set_4_5_2048_r4_runs10_seeds20/performance_summary.csv | present | Stage233 raw high-stat performance aggregate | 286 |
| repro/stage233_set_4_5_2048_r4_runs10_seeds20/perf_SET_4_5_2048_r4_runs10/summary.csv | present | Stage233 per-run performance | 973 |
| repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_summary.csv | present | Stage233 high-stat noise aggregate summary | 309 |
| repro/stage233_set_4_5_2048_r4_runs10_seeds20/noise_SET_4_5_2048_r4_seeds20/summary.csv | present | Stage233 per-seed noise | 3325 |
| repro/stage233_set_4_5_2048_r4_resource/summary.csv | present | Stage233 resource/keygen/RSS | 672 |
