# Stage235 High-Stat SET_2_3_4096 r=2 Slice

Decision: `PASS_STAGE235_THIRD_HIGHSTAT_SLICE_SET_2_3_4096_R4_HIGHSTAT_PENDING`.

Stage235 promotes binary `SET_2_3_4096`, r=2, from smoke/preflight evidence
to a high-stat current-head slice under `spqlios_avx512`,
`MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`, and
`SAB_PVW_ACTIVE_BUFFER_FUSION=true`. The primary endpoint is complete-SAB
`T_bootstrap/r`: amortized bootstrapping time per processed plaintext lane/bit.
This is the correct comparison dimension for the MAT-RLWE r-body redesign.

This stage does not complete the added-parameter matrix because `SET_2_3_4096`, r=4,
still has only the Stage232 3-run/3-seed preflight. It also does not prove
non-binary support, compact selector keygen, novelty, or theoretical optimality.

## Shape Gate

| param | r | observed_h | expected_h | observed_r_prec | expected_r_prec | correctness_status | shape_gate | runs_checked | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 2 | 32 | 32 | 8 | 8 | Pass | PASS | 10 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_0.log |

## Performance Runs

| run | status | param | r | metric | pvw_us | pvw_lane_us | scalar_repeated_us | scalar_lane_us | speedup_vs_scalar_repeated | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28623268.000 | 14311634.000 | 35640898.000 | 17820449.000 | 1.245 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_0.log |
| 1 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28767461.000 | 14383730.500 | 35400910.000 | 17700455.000 | 1.231 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_1.log |
| 2 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28818243.000 | 14409121.500 | 35623234.000 | 17811617.000 | 1.236 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_2.log |
| 3 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28773424.000 | 14386712.000 | 35886771.000 | 17943385.500 | 1.247 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_3.log |
| 4 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28784270.000 | 14392135.000 | 36734597.000 | 18367298.500 | 1.276 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_4.log |
| 5 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28670670.000 | 14335335.000 | 36158506.000 | 18079253.000 | 1.261 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_5.log |
| 6 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28935427.000 | 14467713.500 | 35678607.000 | 17839303.500 | 1.233 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_6.log |
| 7 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28366994.000 | 14183497.000 | 35212489.000 | 17606244.500 | 1.241 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_7.log |
| 8 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 30923969.000 | 15461984.500 | 42052605.000 | 21026302.500 | 1.360 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_8.log |
| 9 | Pass | SET_2_3_4096 | 2 | T_bootstrap/r | 28773110.000 | 14386555.000 | 35653019.000 | 17826509.500 | 1.239 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/run_9.log |

## Performance Statistics

| param | r | runs | pass_runs | metric | pvw_mean_us | scalar_repeated_mean_us | mean_of_speedups | speedup_stdev | speedup_ci95_low | speedup_ci95_high | ratio_of_means_speedup | min_speedup | max_speedup | stats_label | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 2 | 10 | 10 | T_bootstrap/r | 28943683.600 | 36404163.600 | 1.256900 | 0.038734 | 1.229193 | 1.284607 | 1.257758 | 1.231000 | 1.360000 | high-stat slice n=10; SET_2_3_4096 r=2 | PASS_HIGHSTAT_SLICE |

## Noise Seeds

| param | r | seed | status | points | pvw_failures | scalar_failures | pair_failures | pvw_log2_sigma_torus | scalar_log2_sigma_torus | pvw_minus_scalar_log2 | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 2 | 6863025 | Pass | 8192 | 0 | 0 | 0 | -7.703 | -7.688 | -0.015 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863025.log |
| SET_2_3_4096 | 2 | 6863026 | Pass | 8192 | 0 | 0 | 0 | -7.878 | -7.745 | -0.133 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863026.log |
| SET_2_3_4096 | 2 | 6863027 | Pass | 8192 | 0 | 0 | 0 | -7.826 | -7.660 | -0.166 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863027.log |
| SET_2_3_4096 | 2 | 6863028 | Pass | 8192 | 0 | 0 | 0 | -7.834 | -7.555 | -0.279 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863028.log |
| SET_2_3_4096 | 2 | 6863029 | Pass | 8192 | 0 | 0 | 0 | -7.752 | -7.447 | -0.305 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863029.log |
| SET_2_3_4096 | 2 | 6863030 | Pass | 8192 | 0 | 0 | 0 | -7.620 | -7.584 | -0.037 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863030.log |
| SET_2_3_4096 | 2 | 6863031 | Pass | 8192 | 0 | 0 | 0 | -7.332 | -7.886 | 0.554 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863031.log |
| SET_2_3_4096 | 2 | 6863032 | Pass | 8192 | 0 | 0 | 0 | -7.696 | -7.884 | 0.188 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863032.log |
| SET_2_3_4096 | 2 | 6863033 | Pass | 8192 | 0 | 0 | 0 | -7.212 | -7.472 | 0.260 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863033.log |
| SET_2_3_4096 | 2 | 6863034 | Pass | 8192 | 0 | 0 | 0 | -8.017 | -7.791 | -0.226 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863034.log |
| SET_2_3_4096 | 2 | 6863035 | Pass | 8192 | 0 | 0 | 0 | -7.196 | -7.418 | 0.223 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863035.log |
| SET_2_3_4096 | 2 | 6863036 | Pass | 8192 | 0 | 0 | 0 | -7.499 | -7.487 | -0.013 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863036.log |
| SET_2_3_4096 | 2 | 6863037 | Pass | 8192 | 0 | 0 | 0 | -8.006 | -7.896 | -0.110 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863037.log |
| SET_2_3_4096 | 2 | 6863038 | Pass | 8192 | 0 | 0 | 0 | -7.807 | -7.416 | -0.391 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863038.log |
| SET_2_3_4096 | 2 | 6863039 | Pass | 8192 | 0 | 0 | 0 | -7.748 | -7.612 | -0.136 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863039.log |
| SET_2_3_4096 | 2 | 6863040 | Pass | 8192 | 0 | 0 | 0 | -7.945 | -7.412 | -0.533 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863040.log |
| SET_2_3_4096 | 2 | 6863041 | Pass | 8192 | 0 | 0 | 0 | -7.102 | -7.771 | 0.669 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863041.log |
| SET_2_3_4096 | 2 | 6863042 | Pass | 8192 | 0 | 0 | 0 | -7.934 | -7.502 | -0.432 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863042.log |
| SET_2_3_4096 | 2 | 6863043 | Pass | 8192 | 0 | 0 | 0 | -7.801 | -7.562 | -0.239 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863043.log |
| SET_2_3_4096 | 2 | 6863044 | Pass | 8192 | 0 | 0 | 0 | -7.679 | -7.916 | 0.236 | repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/r2/seed_6863044.log |

## Noise Aggregate

| param | r | seeds | points | pvw_failures | scalar_failures | pair_failures | avg_pvw_minus_scalar_log2 | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | status | stats_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 2 | 20 | 163840 | 0 | 0 | 0 | -0.044250 | -0.533000 | 0.669000 | PASS_HIGHSTAT_SLICE | high-stat slice seeds=20; SET_2_3_4096 r=2 |

## Resource Comparison

| param | r | mode | backend | keygen_us | keygen_lane_avg_us | estimated_key_bytes | estimated_key_bytes_ratio_vs_scalar_repeated | internal_vmhwm_kb | time_max_rss_kb | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 2 | pvw | spqlios_avx512 | 2378608 | 1189304.000 | 577347680 | 1.006136 | 718368 | 718708 | repro/stage235_set_2_3_4096_r2_resource/r2/pvw.log |
| SET_2_3_4096 | 2 | scalar | spqlios_avx512 | 2158155 | 1079077.500 | 573826464 | 1.000000 | 731528 | 731740 | repro/stage235_set_2_3_4096_r2_resource/r2/scalar.log |
| SET_2_3_4096 | 2 | pvw_vs_scalar_ratio | spqlios_avx512 | 1.102149 | 1.102149 | 1.006136 | 1.006136 | 0.982010 | 0.982190 | computed from resource pvw/scalar rows |

## Added-Parameter Matrix Progress

| param | r | stage | stat_level | performance_status | noise_status | resource_status | claim_scope | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | Stage233 | high-stat | PASS_HIGHSTAT_SLICE | PASS_HIGHSTAT_SLICE | recorded | promoted for this binary parameter/r slice | repro/stage233_set_4_5_2048_r4_highstat_slice/proof_gate.csv |
| SET_4_5_2048 | 2 | Stage234 | high-stat | PASS_HIGHSTAT_SLICE | PASS_HIGHSTAT_SLICE | recorded | promoted for this binary parameter/r slice | repro/stage234_set_4_5_2048_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 2 | Stage235 | high-stat | PASS_HIGHSTAT_SLICE | PASS_HIGHSTAT_SLICE | recorded | promoted for this binary parameter/r slice | repro/stage235_set_2_3_4096_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 4 | Stage232 | preflight n=3/seeds=3 | PASS_SELECTED_SUBSET_PREFLIGHT | PASS_PREFLIGHT | recorded | preflight only; high-stat pending | repro/stage232_selected_subset_fullstat_resource/proof_gate.csv |

## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage232/233/234 route evidence plus raw Stage235 logs exist | all present | PASS | allows Stage235 aggregation |
| G2_shape | SET_2_3_4096 selects h=32, r_prec=8 | h=32, r_prec=8 | PASS | prevents default-parameter fallback |
| G3_performance_highstat_slice | 10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=10, speedup_mean=1.256900, CI95=1.229193..1.284607 | PASS_HIGHSTAT_SLICE | supports this parameter/r slice only |
| G4_noise_highstat_slice | 20 deterministic seeds, zero PVW/scalar/pair failures | seeds=20, failures=0/0/0 | PASS_HIGHSTAT_SLICE | noise side condition supports this slice only |
| G5_resource | pvw and scalar resource/keygen/RSS rows for this slice | pvw/scalar resource rows present | PASS | records key/RSS side cost beside throughput |
| G6_metric_boundary | compare amortized complete SAB, not isolated MAT external product | primary endpoint is complete-SAB T_bootstrap/r | PASS | aligns with MAT-RLWE r-body design intent |
| G7_matrix_boundary | do not promote full added-parameter matrix until SET_2_3_4096 r=4 is high-stat | SET_2_3_4096 r=4 remains Stage232 preflight only | BOUNDARY_HELD | blocks all-added-parameter and paper-final matrix claims |
| G8_stage235_decision | all Stage235 gates pass and matrix boundary stays explicit | PASS_STAGE235_THIRD_HIGHSTAT_SLICE_SET_2_3_4096_R4_HIGHSTAT_PENDING | PASS_STAGE235_THIRD_HIGHSTAT_SLICE_SET_2_3_4096_R4_HIGHSTAT_PENDING | continue Stage236 SET_2_3_4096 r=4 high-stat slice |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | Stage232/233/234 route evidence plus raw Stage235 logs exist | all present | repro/stage235_set_2_3_4096_r2_highstat_slice/gate_matrix.csv | allows Stage235 aggregation |
| G2_shape | PASS | SET_2_3_4096 selects h=32, r_prec=8 | h=32, r_prec=8 | repro/stage235_set_2_3_4096_r2_highstat_slice/gate_matrix.csv | prevents default-parameter fallback |
| G3_performance_highstat_slice | PASS_HIGHSTAT_SLICE | 10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=10, speedup_mean=1.256900, CI95=1.229193..1.284607 | repro/stage235_set_2_3_4096_r2_highstat_slice/gate_matrix.csv | supports this parameter/r slice only |
| G4_noise_highstat_slice | PASS_HIGHSTAT_SLICE | 20 deterministic seeds, zero PVW/scalar/pair failures | seeds=20, failures=0/0/0 | repro/stage235_set_2_3_4096_r2_highstat_slice/gate_matrix.csv | noise side condition supports this slice only |
| G5_resource | PASS | pvw and scalar resource/keygen/RSS rows for this slice | pvw/scalar resource rows present | repro/stage235_set_2_3_4096_r2_highstat_slice/gate_matrix.csv | records key/RSS side cost beside throughput |
| G6_metric_boundary | PASS | compare amortized complete SAB, not isolated MAT external product | primary endpoint is complete-SAB T_bootstrap/r | repro/stage235_set_2_3_4096_r2_highstat_slice/gate_matrix.csv | aligns with MAT-RLWE r-body design intent |
| G7_matrix_boundary | BOUNDARY_HELD | do not promote full added-parameter matrix until SET_2_3_4096 r=4 is high-stat | SET_2_3_4096 r=4 remains Stage232 preflight only | repro/stage235_set_2_3_4096_r2_highstat_slice/gate_matrix.csv | blocks all-added-parameter and paper-final matrix claims |
| G8_stage235_decision | PASS_STAGE235_THIRD_HIGHSTAT_SLICE_SET_2_3_4096_R4_HIGHSTAT_PENDING | all Stage235 gates pass and matrix boundary stays explicit | PASS_STAGE235_THIRD_HIGHSTAT_SLICE_SET_2_3_4096_R4_HIGHSTAT_PENDING | repro/stage235_set_2_3_4096_r2_highstat_slice/gate_matrix.csv | continue Stage236 SET_2_3_4096 r=4 high-stat slice |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage236_set_2_3_4096_r4_highstat_slice | Stage235 passes and the added-parameter matrix still lacks SET_2_3_4096 r=4 high-stat evidence. | Run 10 complete-SAB A/B samples, 20 noise seeds, and resource pvw/scalar for SET_2_3_4096 r=4. | ready | Keep SET_2_3_4096 r=4 as preflight-only and block full added-parameter matrix claims. | repro/stage235_set_2_3_4096_r2_highstat_slice/proof_gate.csv |
| P1 | stage237_scoped_manuscript_skeleton | A draft is needed before further code routes. | Use only passed slices as main result rows; keep Stage232 r=4 as preflight until Stage236 completes. | ready_after_stage236_or_as_partial_report | Write a scoped report, not a final full-matrix paper claim. | repro/stage235_set_2_3_4096_r2_highstat_slice/added_parameter_matrix_progress.csv |
| P2 | stage238_nonbinary_or_compact_design | The project expands beyond exact dense binary MAT/PVW-SAB. | Closed selector equations, security/noise model, isolated equivalence, production keygen, and full SAB A/B. | blocked_until_design | Do not claim non-binary, compact, or theoretical-optimal MAT-RLWE SAB. | repro/stage235_set_2_3_4096_r2_highstat_slice/next_stage_queue.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage232_selected_subset_fullstat_resource/performance_stats.csv | present | Stage232 sibling SET_2_3_4096 r=4 preflight | 463 |
| repro/stage232_selected_subset_fullstat_resource/noise_aggregate.csv | present | Stage232 sibling SET_2_3_4096 r=4 preflight noise | 287 |
| repro/stage232_selected_subset_fullstat_resource/resource_comparison.csv | present | Stage232 sibling SET_2_3_4096 r=4 preflight resource | 818 |
| repro/stage233_set_4_5_2048_r4_highstat_slice/performance_stats.csv | present | Stage233 SET_4_5_2048 r=4 high-stat baseline row | 448 |
| repro/stage234_set_4_5_2048_r2_highstat_slice/performance_stats.csv | present | Stage234 SET_4_5_2048 r=2 high-stat baseline row | 443 |
| repro/stage235_set_2_3_4096_r2_runs10_seeds20/performance_summary.csv | present | Stage235 raw high-stat performance aggregate | 286 |
| repro/stage235_set_2_3_4096_r2_runs10_seeds20/perf_SET_2_3_4096_r2_runs10/summary.csv | present | Stage235 per-run performance | 983 |
| repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_summary.csv | present | Stage235 high-stat noise aggregate summary | 309 |
| repro/stage235_set_2_3_4096_r2_runs10_seeds20/noise_SET_2_3_4096_r2_seeds20/summary.csv | present | Stage235 per-seed noise | 3299 |
| repro/stage235_set_2_3_4096_r2_resource/summary.csv | present | Stage235 resource/keygen/RSS | 674 |
