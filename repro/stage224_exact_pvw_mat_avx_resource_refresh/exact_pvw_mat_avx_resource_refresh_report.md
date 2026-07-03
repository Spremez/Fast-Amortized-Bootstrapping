# Stage224 Exact PVW/MAT AVX Resource Refresh

Decision: `PASS_STAGE224_EXACT_PVW_MAT_AVX_REFRESH_POSITIVE`.

Stage224 is a fresh complete-SAB performance refresh for the exact closed dense
MAT/PVW route selected by Stage223. The primary metric is still
`T_bootstrap/r`, not raw bootstrap runtime. Compact complete-SAB integration
remains denied.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage224_exact_pvw_mat_avx_resource_refresh/input_status.csv | Stage224 consumes Stage223 route selection and Stage148 side-condition evidence. |
| G2_stage223_admission | PASS | stage224_selected | true | repro/stage223_route_selection/next_stage_queue.csv | Exact PVW/MAT refresh is only valid after compact complete-SAB route is denied. |
| G3_full_sab_perf_refresh | PASS_STAGE224_PERF_REFRESH_POSITIVE | backend_vs_wrapper;backend_vs_scalar | 1.024015;1.407333 | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_results.csv; repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv | Fresh complete-SAB A/B under T_bootstrap/r. |
| G4_noise_resource_side_conditions | PASS_INHERITED_SIDE_CONDITIONS | noise_pass;resource_pass | true;true | repro/stage224_exact_pvw_mat_avx_resource_refresh/side_conditions.csv | Stage224 records inherited noise/resource; rerun before final promotion if source or path changes. |
| G5_claim_boundary | PASS_ENGINEERING_REFRESH_ONLY | claim_boundary | no_compact_complete_sab_claim;no_theoretical_optimality | docs/stage224_exact_pvw_mat_avx_resource_refresh.md | Stage224 is exact PVW/MAT evidence, not compact complete-SAB or optimality proof. |
| G6_stage224_decision | PASS_STAGE224_EXACT_PVW_MAT_AVX_REFRESH_POSITIVE | decision | PASS_STAGE224_EXACT_PVW_MAT_AVX_REFRESH_POSITIVE | repro/stage224_exact_pvw_mat_avx_resource_refresh/proof_gate.csv | Positive refresh can update the evidence package; neutral refresh keeps Stage148 as current best. |

## Performance Comparison

| metric | runs | wrapper_mean_pvw_lane_us | backend_mean_pvw_lane_us | backend_vs_wrapper_mean_speedup | backend_vs_wrapper_min_speedup | backend_vs_wrapper_ci95_low | backend_vs_wrapper_ci95_high | wrapper_mean_speedup_vs_scalar | backend_mean_speedup_vs_scalar | stage148_backend_speedup_vs_scalar | refresh_vs_stage148_backend_speedup | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T_bootstrap_per_lane | 3 | 7195767.556 | 7027354.944 | 1.024015 | 1.008886 | 1.009073 | 1.038956 | 1.376000 | 1.407333 | 1.432667 | 0.982317 | PASS_STAGE224_PERF_REFRESH_POSITIVE |

## Performance Runs

| variant | run | status | r | h | r_prec | pvw_avg_us | pvw_lane_avg_us | scalar_repeated_avg_us | scalar_lane_avg_us | speedup_vs_scalar_repeated | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wrapper_fused_from_dft_add | 0 | PASS | 6 | 39 | 7 | 42797020.000 | 7132836.667 | 59587483.000 | 9931247.167 | 1.392 | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_wrapper_fused_from_dft_add_run_0.log |
| wrapper_fused_from_dft_add | 1 | PASS | 6 | 39 | 7 | 43297241.000 | 7216206.833 | 59054741.000 | 9842456.833 | 1.364 | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_wrapper_fused_from_dft_add_run_1.log |
| wrapper_fused_from_dft_add | 2 | PASS | 6 | 39 | 7 | 43429555.000 | 7238259.167 | 59592443.000 | 9932073.833 | 1.372 | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_wrapper_fused_from_dft_add_run_2.log |
| backend_from_dft_add | 0 | PASS | 6 | 39 | 7 | 42420083.000 | 7070013.833 | 59027398.000 | 9837899.667 | 1.391 | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_backend_from_dft_add_run_0.log |
| backend_from_dft_add | 1 | PASS | 6 | 39 | 7 | 41905398.000 | 6984233.000 | 59957236.000 | 9992872.667 | 1.431 | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_backend_from_dft_add_run_1.log |
| backend_from_dft_add | 2 | PASS | 6 | 39 | 7 | 42166908.000 | 7027818.000 | 59016282.000 | 9836047.000 | 1.400 | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_backend_from_dft_add_run_2.log |

## Side Conditions

| source | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| Stage148 noise | PASS | seeds;failures;avg_pvw_minus_scalar_log2 | 3;0/0/0;0.176333 | repro/stage148_h14_r6_repeated_refresh/noise_aggregate.csv | Inherited side condition; Stage224 refreshes performance and records source-head boundary. |
| Stage148 resource | PASS | key_bytes_ratio;vmhwm_ratio;time_max_rss_ratio | 1.122537;1.030966;1.030743 | repro/stage148_h14_r6_repeated_refresh/resource_comparison.csv | Inherited side condition; rerun resource if Stage224 performance materially changes or before final claim. |
| source-head | RECORDED | latest_src_touching_commit | d8d56ee | git log -1 --format=%h -- src src/mosfhet Makefile | Bounds reuse of Stage148 side conditions; Stage224 does not alter production source. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage225_exact_refresh_resource_noise_rerun | Stage224 perf refresh is positive and final claim needs fresh side conditions. | Rerun noise/resource on the same executable path if promoting Stage224 over Stage148. | selected | Keep Stage148 side conditions and mark Stage224 performance-only refresh. | repro/stage224_exact_pvw_mat_avx_resource_refresh/proof_gate.csv |
| P1 | stage225_exact_mat_avx_counter_attribution | Native perf counters are available. | Attribute backend-vs-wrapper gain to load/store/FMA/cycles rather than backend noise. | future | Use timing-only claim boundary. | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv |
| P2 | paper_claim_boundary_update | After Stage224/225 evidence is stable. | Separate exact MAT/PVW engineering acceleration from blocked compact route. | future | No novelty/optimality claim. | theory_checks/stage150_claim_scope_model.md |
