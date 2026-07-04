# Stage236 High-Stat SET_2_3_4096 r=4 Slice

Decision: `PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE`.

Stage236 promotes binary `SET_2_3_4096`, r=4, from Stage232 preflight to a
high-stat current-head slice under `spqlios_avx512`,
`MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true`, and
`SAB_PVW_ACTIVE_BUFFER_FUSION=true`. The primary endpoint is complete-SAB
`T_bootstrap/r`: amortized bootstrapping time per processed plaintext lane/bit.

Together with Stage233, Stage234, and Stage235, this completes the selected
binary added-parameter matrix for `SET_4_5_2048` and `SET_2_3_4096` at r=2 and
r=4. The supported claim remains scoped to those measured binary rows; it does
not include non-binary branches, compact selector keygen, all-parameter
universality, novelty, or theoretical optimality.

## Shape Gate

| param | r | observed_h | expected_h | observed_r_prec | expected_r_prec | correctness_status | shape_gate | runs_checked | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | 32 | 32 | 8 | 8 | Pass | PASS | 10 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_0.log |

## Performance Statistics

| param | r | runs | pass_runs | metric | pvw_mean_us | scalar_repeated_mean_us | mean_of_speedups | speedup_stdev | speedup_ci95_low | speedup_ci95_high | ratio_of_means_speedup | min_speedup | max_speedup | stats_label | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | 10 | 10 | T_bootstrap/r | 54756737.600 | 72806932.200 | 1.329600 | 0.016581 | 1.317739 | 1.341461 | 1.329643 | 1.290000 | 1.352000 | high-stat slice n=10; SET_2_3_4096 r=4 | PASS_HIGHSTAT_SLICE |

## Performance Runs

| run | status | param | r | metric | pvw_us | pvw_lane_us | scalar_repeated_us | scalar_lane_us | speedup_vs_scalar_repeated | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 53433272.000 | 13358318.000 | 71230075.000 | 17807518.750 | 1.333 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_0.log |
| 1 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 53800434.000 | 13450108.500 | 71740481.000 | 17935120.250 | 1.333 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_1.log |
| 2 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 53902820.000 | 13475705.000 | 71815313.000 | 17953828.250 | 1.332 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_2.log |
| 3 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 55024876.000 | 13756219.000 | 74411252.000 | 18602813.000 | 1.352 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_3.log |
| 4 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 54914078.000 | 13728519.500 | 73288222.000 | 18322055.500 | 1.335 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_4.log |
| 5 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 55409325.000 | 13852331.250 | 72915446.000 | 18228861.500 | 1.316 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_5.log |
| 6 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 54979632.000 | 13744908.000 | 73164880.000 | 18291220.000 | 1.331 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_6.log |
| 7 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 54614957.000 | 13653739.250 | 73314731.000 | 18328682.750 | 1.342 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_7.log |
| 8 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 55857441.000 | 13964360.250 | 72074366.000 | 18018591.500 | 1.290 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_8.log |
| 9 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 55630541.000 | 13907635.250 | 74114556.000 | 18528639.000 | 1.332 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/run_9.log |

## Noise Aggregate

| param | r | seeds | points | pvw_failures | scalar_failures | pair_failures | avg_pvw_minus_scalar_log2 | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | status | stats_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | 20 | 327680 | 0 | 0 | 0 | 0.028950 | -0.302000 | 0.595000 | PASS_HIGHSTAT_SLICE | high-stat slice seeds=20; SET_2_3_4096 r=4 |

## Noise Seeds

| param | r | seed | status | points | pvw_failures | scalar_failures | pair_failures | pvw_log2_sigma_torus | scalar_log2_sigma_torus | pvw_minus_scalar_log2 | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | 6863025 | Pass | 16384 | 0 | 0 | 0 | -7.581 | -7.870 | 0.289 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863025.log |
| SET_2_3_4096 | 4 | 6863026 | Pass | 16384 | 0 | 0 | 0 | -7.737 | -7.612 | -0.125 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863026.log |
| SET_2_3_4096 | 4 | 6863027 | Pass | 16384 | 0 | 0 | 0 | -7.564 | -7.651 | 0.087 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863027.log |
| SET_2_3_4096 | 4 | 6863028 | Pass | 16384 | 0 | 0 | 0 | -7.838 | -7.535 | -0.302 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863028.log |
| SET_2_3_4096 | 4 | 6863029 | Pass | 16384 | 0 | 0 | 0 | -7.297 | -7.704 | 0.407 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863029.log |
| SET_2_3_4096 | 4 | 6863030 | Pass | 16384 | 0 | 0 | 0 | -7.796 | -7.746 | -0.050 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863030.log |
| SET_2_3_4096 | 4 | 6863031 | Pass | 16384 | 0 | 0 | 0 | -7.573 | -7.710 | 0.138 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863031.log |
| SET_2_3_4096 | 4 | 6863032 | Pass | 16384 | 0 | 0 | 0 | -7.706 | -7.860 | 0.154 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863032.log |
| SET_2_3_4096 | 4 | 6863033 | Pass | 16384 | 0 | 0 | 0 | -7.954 | -7.838 | -0.115 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863033.log |
| SET_2_3_4096 | 4 | 6863034 | Pass | 16384 | 0 | 0 | 0 | -7.637 | -7.609 | -0.029 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863034.log |
| SET_2_3_4096 | 4 | 6863035 | Pass | 16384 | 0 | 0 | 0 | -7.213 | -7.807 | 0.595 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863035.log |
| SET_2_3_4096 | 4 | 6863036 | Pass | 16384 | 0 | 0 | 0 | -7.653 | -7.767 | 0.114 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863036.log |
| SET_2_3_4096 | 4 | 6863037 | Pass | 16384 | 0 | 0 | 0 | -7.860 | -7.601 | -0.259 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863037.log |
| SET_2_3_4096 | 4 | 6863038 | Pass | 16384 | 0 | 0 | 0 | -7.744 | -7.627 | -0.117 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863038.log |
| SET_2_3_4096 | 4 | 6863039 | Pass | 16384 | 0 | 0 | 0 | -7.948 | -7.898 | -0.050 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863039.log |
| SET_2_3_4096 | 4 | 6863040 | Pass | 16384 | 0 | 0 | 0 | -7.644 | -7.685 | 0.040 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863040.log |
| SET_2_3_4096 | 4 | 6863041 | Pass | 16384 | 0 | 0 | 0 | -7.693 | -7.630 | -0.063 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863041.log |
| SET_2_3_4096 | 4 | 6863042 | Pass | 16384 | 0 | 0 | 0 | -8.010 | -7.748 | -0.262 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863042.log |
| SET_2_3_4096 | 4 | 6863043 | Pass | 16384 | 0 | 0 | 0 | -7.822 | -7.771 | -0.051 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863043.log |
| SET_2_3_4096 | 4 | 6863044 | Pass | 16384 | 0 | 0 | 0 | -7.637 | -7.815 | 0.178 | repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/r4/seed_6863044.log |

## Resource Comparison

| param | r | mode | backend | keygen_us | keygen_lane_avg_us | estimated_key_bytes | estimated_key_bytes_ratio_vs_scalar_repeated | internal_vmhwm_kb | time_max_rss_kb | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | pvw | spqlios_avx512 | 6242697 | 1560674.250 | 1184198352 | 1.031844 | 1412908 | 1413048 | repro/stage236_set_2_3_4096_r4_resource/r4/pvw.log |
| SET_2_3_4096 | 4 | scalar | spqlios_avx512 | 4597251 | 1149312.750 | 1147652928 | 1.000000 | 1459220 | 1459500 | repro/stage236_set_2_3_4096_r4_resource/r4/scalar.log |
| SET_2_3_4096 | 4 | pvw_vs_scalar_ratio | spqlios_avx512 | 1.357920 | 1.357920 | 1.031844 | 1.031844 | 0.968262 | 0.968173 | computed from resource pvw/scalar rows |

## Selected Binary Matrix

| param | r | stage | stat_level | mean_speedup | speedup_ci95_low | speedup_ci95_high | noise_failures | key_bytes_ratio | keygen_ratio | rss_ratio | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048 | 4 | Stage233 | high-stat n=10/seeds=20 | 1.357500 | 1.344091 | 1.370909 | 0/0/0 | 1.069425 | 1.338877 | 1.000880 | PASS_HIGHSTAT_SLICE | repro/stage233_set_4_5_2048_r4_highstat_slice/proof_gate.csv |
| SET_4_5_2048 | 2 | Stage234 | high-stat n=10/seeds=20 | 1.264700 | 1.255514 | 1.273886 | 0/0/0 | 1.014389 | 1.262692 | 0.991062 | PASS_HIGHSTAT_SLICE | repro/stage234_set_4_5_2048_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 2 | Stage235 | high-stat n=10/seeds=20 | 1.256900 | 1.229193 | 1.284607 | 0/0/0 | 1.006136 | 1.102149 | 0.982190 | PASS_HIGHSTAT_SLICE | repro/stage235_set_2_3_4096_r2_highstat_slice/proof_gate.csv |
| SET_2_3_4096 | 4 | Stage236 | high-stat n=10/seeds=20 | 1.329600 | 1.317739 | 1.341461 | 0/0/0 | 1.031844 | 1.357920 | 0.968173 | PASS_HIGHSTAT_SLICE | repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv |

## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage233/234/235 route evidence plus raw Stage236 logs exist | all present | PASS | allows Stage236 aggregation |
| G2_shape | SET_2_3_4096 selects h=32, r_prec=8 | h=32, r_prec=8 | PASS | prevents default-parameter fallback |
| G3_performance_highstat_slice | 10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=10, speedup_mean=1.329600, CI95=1.317739..1.341461 | PASS_HIGHSTAT_SLICE | supports this parameter/r slice only |
| G4_noise_highstat_slice | 20 deterministic seeds, zero PVW/scalar/pair failures | seeds=20, failures=0/0/0 | PASS_HIGHSTAT_SLICE | noise side condition supports this slice only |
| G5_resource | pvw and scalar resource/keygen/RSS rows for this slice | pvw/scalar resource rows present | PASS | records key/RSS side cost beside throughput |
| G6_metric_boundary | compare amortized complete SAB, not isolated MAT external product | primary endpoint is complete-SAB T_bootstrap/r | PASS | aligns with MAT-RLWE r-body design intent |
| G7_selected_binary_matrix | SET_4_5_2048 and SET_2_3_4096, r=2/r=4, all have high-stat perf/noise/resource evidence | four selected binary rows pass | PASS_SELECTED_BINARY_MATRIX | supports selected binary added-parameter matrix only |
| G8_claim_boundary | do not upgrade to non-binary, compact, all-parameter, novelty, or theoretical-optimality claims | boundaries remain explicit | BOUNDARY_HELD | blocks overclaiming beyond measured selected binary rows |
| G9_stage236_decision | all Stage236 gates pass and boundaries stay explicit | PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE | PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE | move to scoped manuscript/report package |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | Stage233/234/235 route evidence plus raw Stage236 logs exist | all present | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | allows Stage236 aggregation |
| G2_shape | PASS | SET_2_3_4096 selects h=32, r_prec=8 | h=32, r_prec=8 | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | prevents default-parameter fallback |
| G3_performance_highstat_slice | PASS_HIGHSTAT_SLICE | 10 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=10, speedup_mean=1.329600, CI95=1.317739..1.341461 | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | supports this parameter/r slice only |
| G4_noise_highstat_slice | PASS_HIGHSTAT_SLICE | 20 deterministic seeds, zero PVW/scalar/pair failures | seeds=20, failures=0/0/0 | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | noise side condition supports this slice only |
| G5_resource | PASS | pvw and scalar resource/keygen/RSS rows for this slice | pvw/scalar resource rows present | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | records key/RSS side cost beside throughput |
| G6_metric_boundary | PASS | compare amortized complete SAB, not isolated MAT external product | primary endpoint is complete-SAB T_bootstrap/r | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | aligns with MAT-RLWE r-body design intent |
| G7_selected_binary_matrix | PASS_SELECTED_BINARY_MATRIX | SET_4_5_2048 and SET_2_3_4096, r=2/r=4, all have high-stat perf/noise/resource evidence | four selected binary rows pass | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | supports selected binary added-parameter matrix only |
| G8_claim_boundary | BOUNDARY_HELD | do not upgrade to non-binary, compact, all-parameter, novelty, or theoretical-optimality claims | boundaries remain explicit | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | blocks overclaiming beyond measured selected binary rows |
| G9_stage236_decision | PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE | all Stage236 gates pass and boundaries stay explicit | PASS_STAGE236_SELECTED_BINARY_ADDED_PARAMETER_MATRIX_COMPLETE | repro/stage236_set_2_3_4096_r4_highstat_slice/gate_matrix.csv | move to scoped manuscript/report package |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage237_scoped_manuscript_skeleton | Selected binary added-parameter matrix is complete under high-stat gates. | Draft a scoped report with algorithm, T_bootstrap/r metric, four-row matrix table, resource/noise side conditions, and claim boundary. | ready | Keep evidence as engineering report rather than paper claim. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| P1 | stage238_native_counter_or_backend_validation | The manuscript needs stronger implementation attribution. | Run native Linux perf counters or mark WSL counters as proxy only. | optional | Do not make hardware-counter or theoretical-optimality claims. | repro/stage236_set_2_3_4096_r4_highstat_slice/proof_gate.csv |
| P2 | stage239_nonbinary_or_compact_design | The project expands beyond exact dense binary MAT/PVW-SAB. | Closed selector equations, security/noise model, isolated equivalence, production keygen, and full SAB A/B. | blocked_until_design | Do not claim non-binary, compact, or theoretical-optimal MAT-RLWE SAB. | repro/stage236_set_2_3_4096_r4_highstat_slice/next_stage_queue.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage233_set_4_5_2048_r4_highstat_slice/performance_stats.csv | present | Stage233 SET_4_5_2048 r=4 high-stat performance | 448 |
| repro/stage234_set_4_5_2048_r2_highstat_slice/performance_stats.csv | present | Stage234 SET_4_5_2048 r=2 high-stat performance | 443 |
| repro/stage235_set_2_3_4096_r2_highstat_slice/performance_stats.csv | present | Stage235 SET_2_3_4096 r=2 high-stat performance | 444 |
| repro/stage236_set_2_3_4096_r4_runs10_seeds20/performance_summary.csv | present | Stage236 raw high-stat performance aggregate | 286 |
| repro/stage236_set_2_3_4096_r4_runs10_seeds20/perf_SET_2_3_4096_r4_runs10/summary.csv | present | Stage236 per-run performance | 983 |
| repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_summary.csv | present | Stage236 high-stat noise aggregate summary | 308 |
| repro/stage236_set_2_3_4096_r4_runs10_seeds20/noise_SET_2_3_4096_r4_seeds20/summary.csv | present | Stage236 per-seed noise | 3316 |
| repro/stage236_set_2_3_4096_r4_resource/summary.csv | present | Stage236 resource/keygen/RSS | 680 |
