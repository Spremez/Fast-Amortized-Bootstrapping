# Stage250 Exact Dense Lower-Bound Gap

Decision: `PASS_STAGE250_EXACT_DENSE_GAP_REFRESH_OPTIMALITY_OPEN`.

Stage250 refreshes the exact dense PVW/MAT-SAB lower-bound boundary after the
compact route was frozen. It keeps the primary endpoint as complete-SAB
`T_bootstrap/r` and records that theoretical optimality remains open.

## Performance Endpoint Matrix

| source | param | r | endpoint | mean_speedup | ci95_low | ci95_high | noise_failures | status | claim_use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stage233 | SET_4_5_2048 | 4 | complete-SAB T_bootstrap/r | 1.357500 | 1.344091 | 1.370909 | 0/0/0 | PASS_HIGHSTAT_SLICE | selected_binary_timing_evidence_not_optimality |
| Stage234 | SET_4_5_2048 | 2 | complete-SAB T_bootstrap/r | 1.264700 | 1.255514 | 1.273886 | 0/0/0 | PASS_HIGHSTAT_SLICE | selected_binary_timing_evidence_not_optimality |
| Stage235 | SET_2_3_4096 | 2 | complete-SAB T_bootstrap/r | 1.256900 | 1.229193 | 1.284607 | 0/0/0 | PASS_HIGHSTAT_SLICE | selected_binary_timing_evidence_not_optimality |
| Stage236 | SET_2_3_4096 | 4 | complete-SAB T_bootstrap/r | 1.329600 | 1.317739 | 1.341461 | 0/0/0 | PASS_HIGHSTAT_SLICE | selected_binary_timing_evidence_not_optimality |
| Stage224 r6 exact refresh | explicit_r6_route | 6 | complete-SAB T_bootstrap/r | 1.407333 | not_highstat_3run | not_highstat_3run | inherited Stage148 side condition | PASS_STAGE224_PERF_REFRESH_POSITIVE | engineering_refresh_not_highstat_optimality |


## Lower-Bound Component Matrix

| component | measured_or_model | evidence | closed_status | gap_effect | next_action |
| --- | --- | --- | --- | --- | --- |
| schedule_count | S=(h+1)*rho*N; target binary S=573440 | theory_checks/mat_rlwe_sab_amortized_optimality.md; repro/stage208_current_head_profile_refresh/component_attribution.csv | measured_for_target_schedule | schedule count is fixed; optimization must reduce per-call cost or tail | preserve same schedule count in all A/B tests |
| mat_ep_primary_share | Stage208 MAT EP is 40.879% of CMUX for r=2 and 47.760% for r=4 | repro/stage208_current_head_profile_refresh/component_attribution.csv | profile_attribution_only | MAT EP remains the largest measurable body-path term | do not optimize postproc first; require split/counter-backed MAT EP mechanism |
| postproc_tail | Stage208 tail max is below 2% | repro/stage208_current_head_profile_refresh/component_attribution.csv | defer | tail cannot explain multi-fold remaining gap today | reopen only after body-path change |
| body_linear_proxy | Stage166 shared-output compact term proxy is smaller than dense | repro/stage166_shared_output_compact_algebra_gate/term_model.csv; repro/stage249_structured_compact_distribution_security/proof_gate.csv | not_admissible_as_lower_bound | compact/body-linear proxy is blocked by distribution/security gates | do not use compact proxy as optimality proof |
| split_microbench_projection | Stage209 split projection identifies DFT rows/sub-decompose/addmul shares | repro/stage209_current_head_mat_ep_split/split_projection.csv | preflight_only | specific subcomponents are measurable, but no code permission or full-SAB gain yet | new exact code requires a counter-backed mechanism and full-SAB A/B |
| term_model_r2 | dense=9; compact_proxy=7; missing_cross=2 | repro/stage166_shared_output_compact_algebra_gate/term_model.csv | model_only_compact_blocked | shows dense MAT risk but not an admissible implementation lower bound | cite as risk/model only |
| term_model_r4 | dense=25; compact_proxy=13; missing_cross=12 | repro/stage166_shared_output_compact_algebra_gate/term_model.csv | model_only_compact_blocked | shows dense MAT risk but not an admissible implementation lower bound | cite as risk/model only |
| term_model_r6 | dense=49; compact_proxy=19; missing_cross=30 | repro/stage166_shared_output_compact_algebra_gate/term_model.csv | model_only_compact_blocked | shows dense MAT risk but not an admissible implementation lower bound | cite as risk/model only |
| term_model_r8 | dense=81; compact_proxy=25; missing_cross=56 | repro/stage166_shared_output_compact_algebra_gate/term_model.csv | model_only_compact_blocked | shows dense MAT risk but not an admissible implementation lower bound | cite as risk/model only |


## Counter Gap Matrix

| metric | value | status | interpretation | evidence |
| --- | --- | --- | --- | --- |
| backend_vs_wrapper_complete_sab_speedup | 1.024015000 | timing_refresh | backend direct path is measurably better than wrapper in Stage224 repeated complete-SAB timing | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv |
| cycles_wrapper_over_backend | 1.017861569 | counter_attribution_only | native counters support direction, not lower-bound tightness | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv |
| loads_wrapper_over_backend | 1.011560486 | counter_attribution_only | load reduction is small and does not prove theoretical optimum | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv |
| stores_wrapper_over_backend | 1.009880546 | counter_attribution_only | store reduction is small and does not prove theoretical optimum | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv |
| optimality_gap_numeric | not_closed | blocked | no validated lower-bound denominator exists for A_impl/A_lower | theory_checks/stage250_exact_dense_lower_bound_gap_model.md |


## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| exact_dense_speedup | supported_scoped | Selected binary exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r under recorded gates. | This proves all-parameter or non-binary speedup. | repro/stage250_exact_dense_lower_bound_gap/performance_endpoint_matrix.csv |
| exact_dense_optimality | blocked | The lower-bound gap remains open; counters are attribution-only. | The exact dense implementation is theoretically optimal. | repro/stage250_exact_dense_lower_bound_gap/lower_bound_component_matrix.csv |
| compact_lower_bound | denied | Compact/body-linear term models are risks or blocked proxies. | Use compact term counts as a lower bound for exact dense optimality. | repro/stage249_structured_compact_distribution_security/proof_gate.csv |
| next_code_permission | denied_without_new_mechanism | New exact hot-path code requires a counter-backed mechanism and full-SAB A/B gate. | Implement speculative AVX/MAT rewrites from current lower-bound tables. | repro/stage228_counter_driven_backend_kernel_search/proof_gate.csv |


## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | required inputs | all present | repro/stage250_exact_dense_lower_bound_gap/input_status.csv | Stage250 consumes compact freeze, selected timing, profile, split, and counters. |
| G2_endpoint | PASS | performance rows use complete-SAB T_bootstrap/r | 5 | repro/stage250_exact_dense_lower_bound_gap/performance_endpoint_matrix.csv | Performance evidence remains aligned with the MAT-RLWE/r-body metric. |
| G3_lower_bound_boundary | PASS_GAP_OPEN | body-linear/compact proxy | not admissible | repro/stage250_exact_dense_lower_bound_gap/lower_bound_component_matrix.csv | Compact/body-linear models are not valid lower-bound proof for exact dense optimality. |
| G4_counter_boundary | PASS_ATTRIBUTION_ONLY | numeric optimality gap | not closed | repro/stage250_exact_dense_lower_bound_gap/counter_gap_matrix.csv | Stage226 counters support implementation direction only. |
| G5_claim_boundary | PASS_NO_OPTIMALITY_CLAIM | exact dense optimality | blocked | repro/stage250_exact_dense_lower_bound_gap/claim_boundary.csv | No theoretical optimality claim is permitted. |
| G6_stage250_decision | PASS_STAGE250_EXACT_DENSE_GAP_REFRESH_OPTIMALITY_OPEN | decision | PASS_STAGE250_EXACT_DENSE_GAP_REFRESH_OPTIMALITY_OPEN | repro/stage250_exact_dense_lower_bound_gap/proof_gate.csv | Proceed to non-binary semantics or a new counter-backed exact mechanism, not speculative code. |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage251_nonbinary_selector_semantics_preflight | Compact is frozen and exact dense optimality gap remains open without code permission. | define ternary/include-zero PVW selector semantics and staged equivalence before implementation | selected_next | keep non-binary PVW unsupported | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv |
| P1 | new_exact_dense_counter_backed_mechanism | A concrete MAT EP/fromDFT/addmul mechanism with predicted full-SAB effect is proposed. | isolated equivalence, native counters, complete-SAB T_bootstrap/r A/B, noise/resource | conditional | do not edit hot path | repro/stage209_current_head_mat_ep_split/split_projection.csv |
| P2 | paper_claim_boundary_refresh | No new implementation route is selected. | state scoped engineering result; optimality and compact/non-binary claims blocked | future_packaging | remove unsupported optimality wording | repro/stage250_exact_dense_lower_bound_gap/claim_boundary.csv |


## Inputs

| input_id | path | status | bytes |
| --- | --- | --- | --- |
| stage249_proof_gate | repro/stage249_structured_compact_distribution_security/proof_gate.csv | present | 1584 |
| stage236_selected_binary | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv | present | 899 |
| stage224_perf_refresh | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv | present | 479 |
| stage208_profile | repro/stage208_current_head_profile_refresh/component_attribution.csv | present | 604 |
| stage209_split | repro/stage209_current_head_mat_ep_split/split_projection.csv | present | 1353 |
| stage226_attribution | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | present | 1607 |
| stage226_counters | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv | present | 493 |
| stage166_term_model | repro/stage166_shared_output_compact_algebra_gate/term_model.csv | present | 571 |
| optimality_model | theory_checks/mat_rlwe_sab_amortized_optimality.md | present | 3177 |


Generated from head `b3dc1e0`.
