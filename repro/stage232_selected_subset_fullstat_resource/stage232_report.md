# Stage232 Selected-Subset Full-Stat/Resource Preflight

Decision: `PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING`.

Stage232 executes one representative current-head added-parameter preflight:
`SET_2_3_4096`, r=4, binary, `spqlios_avx512`, active-buffer PVW/MAT-SAB.
The primary endpoint remains complete-SAB `T_bootstrap/r`, meaning bootstrap
time divided by the number of plaintext lanes/bits processed by the MAT-RLWE
state. This stage is deliberately not a full added-parameter matrix.

## Selection Rationale

| param | r | selection_reason | primary_metric | claim_level | promotion_gate | blocked_claims |
| --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | largest-N added binary parameter plus main r=4 stress case; Stage231 smoke was positive and Stage36 historical evidence existed | complete-SAB T_bootstrap/r | selected-subset preflight only | 10-run complete-SAB A/B, 20-seed noise, and resource for the promoted parameter matrix | all-parameter, non-binary, theoretical optimality, universal MAT-RLWE SAB optimality |

## Shape Gate

| param | r | observed_h | expected_h | observed_r_prec | expected_r_prec | correctness_status | shape_gate | source_log | runs_checked |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | 32 | 32 | 8 | 8 | Pass | PASS | repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/perf_SET_2_3_4096_r4_runs3/run_0.log | 3 |

## Performance Runs

| run | status | param | r | metric | pvw_us | pvw_lane_us | scalar_repeated_us | scalar_lane_us | speedup_vs_scalar_repeated | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 53299569.000 | 13324892.250 | 71733422.000 | 17933355.500 | 1.346 | repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/perf_SET_2_3_4096_r4_runs3/run_0.log |
| 1 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 53878476.000 | 13469619.000 | 72043189.000 | 18010797.250 | 1.337 | repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/perf_SET_2_3_4096_r4_runs3/run_1.log |
| 2 | Pass | SET_2_3_4096 | 4 | T_bootstrap/r | 54046023.000 | 13511505.750 | 72034269.000 | 18008567.250 | 1.333 | repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/perf_SET_2_3_4096_r4_runs3/run_2.log |

## Performance Statistics

| param | r | runs | pass_runs | metric | pvw_mean_us | scalar_repeated_mean_us | mean_of_speedups | speedup_stdev | speedup_ci95_low | speedup_ci95_high | ratio_of_means_speedup | stats_label | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | 3 | 3 | T_bootstrap/r | 53741356.000 | 71936960.000 | 1.338667 | 0.006658 | 1.322125 | 1.355208 | 1.338577 | preflight n=3; insufficient for final paper table | PASS_SELECTED_SUBSET_PREFLIGHT |

## Noise Preflight

| param | r | seed | status | points | pvw_failures | scalar_failures | pair_failures | pvw_minus_scalar_log2 | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | 6863025 | Pass | 16384 | 0 | 0 | 0 | 0.289 | repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/noise_SET_2_3_4096_r4_seeds3/r4/seed_6863025.log |
| SET_2_3_4096 | 4 | 6863026 | Pass | 16384 | 0 | 0 | 0 | -0.125 | repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/noise_SET_2_3_4096_r4_seeds3/r4/seed_6863026.log |
| SET_2_3_4096 | 4 | 6863027 | Pass | 16384 | 0 | 0 | 0 | 0.087 | repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/noise_SET_2_3_4096_r4_seeds3/r4/seed_6863027.log |

## Noise Aggregate

| param | r | seeds | points | pvw_failures | scalar_failures | pair_failures | avg_pvw_minus_scalar_log2 | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | status | stats_label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | 3 | 49152 | 0 | 0 | 0 | 0.083667 | -0.125000 | 0.289000 | PASS_PREFLIGHT | preflight seeds=3; insufficient for final noise claim |

## Resource Comparison

| param | r | mode | backend | keygen_us | keygen_lane_avg_us | estimated_key_bytes | estimated_key_bytes_ratio_vs_scalar_repeated | internal_vmhwm_kb | time_max_rss_kb | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 4 | pvw | spqlios_avx512 | 6150681 | 1537670.250 | 1184198352 | 1.031844 | 1412768 | 1412996 | repro/stage232_selected_subset_set_2_3_4096_r4_resource/r4/pvw.log |
| SET_2_3_4096 | 4 | scalar | spqlios_avx512 | 4676652 | 1169163.000 | 1147652928 | 1.000000 | 1459248 | 1459624 | repro/stage232_selected_subset_set_2_3_4096_r4_resource/r4/scalar.log |
| SET_2_3_4096 | 4 | pvw_vs_scalar_ratio | spqlios_avx512 | 1.315189 | 1.315189 | 1.031844 | 1.031844 | 0.968148 | 0.968055 | computed from resource pvw/scalar rows |

## Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| G1_inputs | Stage231 queue plus selected raw performance/noise/resource logs exist | all present | PASS | allows Stage232 aggregation |
| G2_shape | SET_2_3_4096 selects h=32, r_prec=8 | h=32, r_prec=8 | PASS | prevents default-parameter fallback |
| G3_performance_preflight | 3 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=3, speedup_mean=1.338667, CI95=1.322125..1.355208 | PASS_PREFLIGHT | positive selected-subset signal only; not final paper statistics |
| G4_noise_preflight | 3 deterministic seeds, zero PVW/scalar/pair failures | seeds=3, failures=0/0/0 | PASS_PREFLIGHT | noise sanity only; 20-seed gate remains pending |
| G5_resource | pvw and scalar resource/keygen/RSS rows for the selected subset | pvw/scalar resource rows present | PASS | resource side condition recorded for selected subset |
| G6_promotion_boundary | do not promote selected preflight to full added-parameter matrix | full matrix and 10-run/20-seed gates still pending | BOUNDARY_HELD | blocks all-parameter and final-paper table claims |
| G7_stage232_decision | all preflight gates pass and promotion boundary stays explicit | PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING | PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING | proceed to high-stat matrix or scoped manuscript skeleton |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | Stage231 queue plus selected raw performance/noise/resource logs exist | all present | repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv | allows Stage232 aggregation |
| G2_shape | PASS | SET_2_3_4096 selects h=32, r_prec=8 | h=32, r_prec=8 | repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv | prevents default-parameter fallback |
| G3_performance_preflight | PASS_PREFLIGHT | 3 complete-SAB A/B runs, all correctness Pass, mean T_bootstrap/r speedup > 1 | runs=3, speedup_mean=1.338667, CI95=1.322125..1.355208 | repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv | positive selected-subset signal only; not final paper statistics |
| G4_noise_preflight | PASS_PREFLIGHT | 3 deterministic seeds, zero PVW/scalar/pair failures | seeds=3, failures=0/0/0 | repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv | noise sanity only; 20-seed gate remains pending |
| G5_resource | PASS | pvw and scalar resource/keygen/RSS rows for the selected subset | pvw/scalar resource rows present | repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv | resource side condition recorded for selected subset |
| G6_promotion_boundary | BOUNDARY_HELD | do not promote selected preflight to full added-parameter matrix | full matrix and 10-run/20-seed gates still pending | repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv | blocks all-parameter and final-paper table claims |
| G7_stage232_decision | PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING | all preflight gates pass and promotion boundary stays explicit | PASS_STAGE232_SELECTED_SUBSET_PREFLIGHT_RESOURCE_RECORDED_FULL_MATRIX_PENDING | repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv | proceed to high-stat matrix or scoped manuscript skeleton |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage233_full_added_parameter_matrix | Added binary parameters must be promoted into a main paper table. | 10-run complete-SAB A/B, 20-seed noise, and resource/keygen/RSS for SET_4_5_2048 and SET_2_3_4096 r=2/r=4 or an explicitly smaller promoted matrix. | future | Keep Stage231/232 as smoke/preflight only and cite Stage229 scoped matrix. | repro/stage232_selected_subset_fullstat_resource/gate_matrix.csv |
| P1 | stage234_scoped_manuscript_skeleton | A manuscript/report draft is needed before spending full-matrix compute. | Use only Stage206/224/229/230 as main claim support; Stage231/232 as continuity/preflight. | ready | Remove current-head added-parameter tables from manuscript. | repro/stage232_selected_subset_fullstat_resource/proof_gate.csv |
| P2 | stage235_nonbinary_or_compact_design | The project expands beyond exact dense binary MAT/PVW-SAB. | Closed selector equations, security/noise model, isolated equivalence, and full SAB A/B. | blocked_until_design | Do not claim non-binary, compact, or optimal MAT-RLWE SAB. | repro/stage232_selected_subset_fullstat_resource/next_stage_queue.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage231_current_head_added_param_smoke/proof_gate.csv | present | Stage231 proof gate | 1373 |
| repro/stage231_current_head_added_param_smoke/next_stage_queue.csv | present | Stage231 next queue selecting Stage232 | 1100 |
| repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/performance_summary.csv | present | Stage232 selected subset performance aggregate | 300 |
| repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/perf_SET_2_3_4096_r4_runs3/summary.csv | present | Stage232 selected subset per-run performance | 402 |
| repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/noise_summary.csv | present | Stage232 selected subset noise aggregate summary | 321 |
| repro/stage232_selected_subset_set_2_3_4096_r4_runs3_seeds3/noise_SET_2_3_4096_r4_seeds3/summary.csv | present | Stage232 selected subset per-seed noise | 693 |
| repro/stage232_selected_subset_set_2_3_4096_r4_resource/summary.csv | present | Stage232 selected subset resource/keygen/RSS | 744 |
