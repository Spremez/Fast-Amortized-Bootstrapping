# Stage229 Parameter Generalization Matrix

Decision: `PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED`.

Stage229 answers the MAT-RLWE/r-body comparison question by fixing the primary
metric to complete-SAB amortized throughput:

```text
speedup = (time for r scalar SAB bootstraps / r) / (time for one r-body PVW/MAT-SAB bootstrap / r)
        = T_scalar_repeated / T_PVW
```

This is the bootstrap time per processed plaintext lane/bit. The matrix below
does not claim single-output latency improvement, all-parameter coverage,
non-binary PVW support, or theoretical optimality.

## Parameter Definitions

| param | key_mode | in_N | out_N | msg_prec | h | r_prec | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_2048 | BINARY | 2048 | 2048 | 3 | 39 | 7 | target_main | main.c |
| SET_4_5_2048 | BINARY | 2048 | 2048 | 5 | 42 | 7 | added_binary_covered | main.c |
| SET_2_3_4096 | BINARY | 4096 | 2048 | 3 | 32 | 8 | added_binary_covered | main.c |
| TERNARY_or_include_zero | NON_BINARY |  |  |  |  |  | pvw_unsupported_scalar_preserved | docs/stage26_parameter_branch_log.md |

## Evidence Matrix

| scope | param | key_mode | r | metric | runs | speedup_mean | speedup_ci95 | noise_seeds | noise_failures | resource | claim_level | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_head_target | SET_2_3_2048 | BINARY | 2 | T_bootstrap/r | 10 | 1.300000 | 1.276461..1.323539 | 20 | 0/0/0 | key_bytes_ratio=1.013617;rss_ratio=0.990118 | current-head complete-SAB evidence | repro/stage206_current_head_highstat/performance_stats.csv; repro/stage206_current_head_highstat/noise_stats.csv; repro/stage207_current_head_resource_refresh/resource_comparison.csv |
| historical_highstat_target | SET_2_3_2048 | BINARY | 2 | T_bootstrap/r | 10 | 1.191 | 1.075307..1.306693 | 50 | 0/0/0 | key_bytes_ratio_mean=1.014;rss_max=383236.000 | historical high-stat support, not current-head replacement | repro/stage36_target_perf_summary.csv; repro/stage36_target_noise_seeds50/aggregate.csv; repro/stage36_resource_summary.csv |
| current_head_target | SET_2_3_2048 | BINARY | 4 | T_bootstrap/r | 10 | 1.356900 | 1.333331..1.380469 | 20 | 0/0/0 | key_bytes_ratio=1.065349;rss_ratio=0.997138 | current-head complete-SAB evidence | repro/stage206_current_head_highstat/performance_stats.csv; repro/stage206_current_head_highstat/noise_stats.csv; repro/stage207_current_head_resource_refresh/resource_comparison.csv |
| historical_highstat_target | SET_2_3_2048 | BINARY | 4 | T_bootstrap/r | 10 | 1.377 | 1.314893..1.438107 | 50 | 0/0/0 | key_bytes_ratio_mean=1.065;rss_max=769468.000 | historical high-stat support, not current-head replacement | repro/stage36_target_perf_summary.csv; repro/stage36_target_noise_seeds50/aggregate.csv; repro/stage36_resource_summary.csv |
| current_head_exact_r6 | SET_2_3_2048 | BINARY | 6 | T_bootstrap/r | 3 | 1.407333 | not_reported_for_scalar_speedup;backend_vs_wrapper_ci=1.009073..1.038956 | 3 | 0/0/0 | key_bytes_ratio=1.122537;rss_ratio=1.031111 | current exact dense MAT/PVW r=6 support, experimental explicit path | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv; repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv; repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv |
| historical_added_binary | SET_4_5_2048 | BINARY | 2 | T_bootstrap/r | 10 | 1.285700 | 1.255799..1.315601 | 20 | 0/0/0 | not refreshed in added-parameter campaign | binary parameter support only; not all-parameter claim | repro/stage36_added_params_runs10_seeds20/performance_stats.csv; repro/stage36_added_params_runs10_seeds20/noise_summary.csv |
| historical_added_binary | SET_4_5_2048 | BINARY | 4 | T_bootstrap/r | 10 | 1.350700 | 1.329122..1.372278 | 20 | 0/0/0 | not refreshed in added-parameter campaign | binary parameter support only; not all-parameter claim | repro/stage36_added_params_runs10_seeds20/performance_stats.csv; repro/stage36_added_params_runs10_seeds20/noise_summary.csv |
| historical_added_binary | SET_2_3_4096 | BINARY | 2 | T_bootstrap/r | 10 | 1.235100 | 1.210553..1.259647 | 20 | 0/0/0 | not refreshed in added-parameter campaign | binary parameter support only; not all-parameter claim | repro/stage36_added_params_runs10_seeds20/performance_stats.csv; repro/stage36_added_params_runs10_seeds20/noise_summary.csv |
| historical_added_binary | SET_2_3_4096 | BINARY | 4 | T_bootstrap/r | 10 | 1.346200 | 1.285926..1.406474 | 20 | 0/0/0 | not refreshed in added-parameter campaign | binary parameter support only; not all-parameter claim | repro/stage36_added_params_runs10_seeds20/performance_stats.csv; repro/stage36_added_params_runs10_seeds20/noise_summary.csv |

## Coverage Gaps

| gap | status | reason | required_next_evidence | evidence |
| --- | --- | --- | --- | --- |
| non_binary_pvw_sab | blocked | Stage26 explicitly rejects PVW target harness for non-binary key modes while scalar ternary remains preserved. | Separate selector/key-format design for sign/coefficient semantics, isolated equivalence, full SAB A/B, noise/resource. | docs/stage26_parameter_branch_log.md |
| all_parameter_generalization | not_claimed | Evidence covers target binary plus two added binary parameters; other SET_* definitions are not in the repeated matrix. | Pre-register each parameter family and run same-backend complete-SAB A/B plus multi-seed noise. | repro/stage229_parameter_generalization_matrix/parameter_definitions.csv; repro/stage229_parameter_generalization_matrix/parameter_matrix.csv |
| small_parameter_proxy | not_claimed | The recent PARAM=SET_2_3 probe still used default SET_2_3_2048 target shape in the harness output. | Add or identify a true small-parameter harness and prove it prints distinct h/r_prec/in_N before timing. | main.c |
| mat_rlwe_theoretical_optimality | open | Current exact route is dense row-output MAT/PVW. It optimizes T_bootstrap/r empirically but does not prove optimal r-body MAT-RLWE SAB. | Formal lower/upper cost model plus counter-backed kernel evidence and complete-SAB ablation. | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv |
| paper_novelty | blocked_until_source_verified | Engineering speedup evidence is available, but novelty wording requires verified related work and real 2025/686 source anchors. | Source-verified literature/novelty matrix; no fabricated references. | repro/stage229_parameter_generalization_matrix/next_stage_queue.csv |

## Claim Scope

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| primary_metric | supported | Speedup is measured as complete-SAB amortized throughput, `T_scalar_repeated/r` over `T_PVW/r`, i.e. bootstrap time per processed plaintext lane/bit. | Do not report one PVW call total latency as a single-output latency improvement. | repro/stage229_parameter_generalization_matrix/parameter_matrix.csv |
| current_head_target_binary | supported_scoped | Current head supports binary `SET_2_3_2048` r=2/r=4 complete-SAB A/B with noise/resource side conditions. | Do not generalize this row to non-binary or all parameter sets. | repro/stage229_parameter_generalization_matrix/parameter_matrix.csv |
| historical_added_binary | supported_scoped_historical | Stage36 supports added binary parameters `SET_4_5_2048` and `SET_2_3_4096` for r=2/r=4 under recorded high-stat gates. | Do not call these current-head refreshes unless rerun at current head. | repro/stage229_parameter_generalization_matrix/parameter_matrix.csv |
| r6_exact_route | supported_experimental_explicit | Exact dense MAT/PVW r=6 has current explicit-path support with fresh noise/resource and counter attribution. | Do not call r=6 theoretically optimal or default-promoted. | repro/stage229_parameter_generalization_matrix/parameter_matrix.csv |
| non_binary_pvw | unsupported | PVW/MAT-SAB non-binary support is not implemented; scalar ternary baseline is preserved. | Do not claim ternary/include-zero PVW-SAB support. | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv |
| mat_rlwe_optimality | unsupported_open | The present route is an empirically validated dense MAT/RLWE exact path, not a proof of optimal r-body MAT-RLWE SAB. | Do not claim theoretical optimality of MAT external product or full SAB. | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | inputs_present | true | repro/stage229_parameter_generalization_matrix/input_status.csv | Stage229 only consumes registered evidence; missing inputs block promotion. |
| G2_metric_dimension | PASS | primary_metric | T_bootstrap/r | repro/stage229_parameter_generalization_matrix/claim_scope.csv | All PVW/MAT-SAB speedups are amortized per processed plaintext lane/bit. |
| G3_current_head_binary_target | PASS | current_rows | 2 | repro/stage229_parameter_generalization_matrix/parameter_matrix.csv | Current-head r=2/r=4 target evidence is present. |
| G4_added_binary_history | PASS | added_rows | 4 | repro/stage229_parameter_generalization_matrix/parameter_matrix.csv | Two added binary parameters have historical 10-run/20-seed evidence. |
| G5_exact_r6_current | PASS | r6_rows | 1 | repro/stage229_parameter_generalization_matrix/parameter_matrix.csv | Current exact r=6 explicit-path evidence is registered but remains scoped. |
| G6_nonbinary_boundary | PASS_BLOCKED_SCOPE | nonbinary_blocked | true | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv | PVW non-binary support remains unsupported; scalar non-binary is not removed. |
| G7_generalization_boundary | PASS_NOT_ALL_PARAMETERS | all_parameter_claim | denied | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv | Stage229 records a scoped parameter matrix, not an all-parameter theorem. |
| G8_stage229_decision | PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED | decision | PASS_STAGE229_SCOPED_BINARY_MATRIX_RECORDED_NONBINARY_BLOCKED | repro/stage229_parameter_generalization_matrix/proof_gate.csv | Proceed to source-verified novelty audit and explicit implementation preflights only. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage230_source_verified_literature_novelty_audit | Stage229 fixes claim scope and forbids paper novelty overclaim. | Real sources only; verify 2025/686, PVW/MAT, multi-output bootstrapping, and SIMD FHE kernel context. | selected | Keep final report engineering-scoped and remove novelty wording. | repro/stage229_parameter_generalization_matrix/claim_scope.csv |
| P1 | stage231_true_parameter_refresh | A claim needs current-head support beyond binary SET_2_3_2048 and r=6. | Print parameter shape first, then same-backend complete-SAB A/B, multi-seed noise, resource. | future | Keep Stage36 added-parameter evidence historical/scoped. | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv |
| P2 | stage232_nonbinary_pvw_design_preflight | User elects to support ternary/include-zero PVW-SAB. | Selector/key-format equations before implementation; isolated equivalence before full SAB. | blocked_until_design | Do not claim non-binary PVW-SAB. | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage228_counter_driven_backend_kernel_search/proof_gate.csv | present | Stage228 proof gate selecting parameter matrix | 1136 |
| repro/stage228_counter_driven_backend_kernel_search/next_stage_queue.csv | present | Stage228 next queue | 923 |
| repro/stage206_current_head_highstat/performance_stats.csv | present | current-head r=2/r=4 complete-SAB A/B | 877 |
| repro/stage206_current_head_highstat/noise_stats.csv | present | current-head r=2/r=4 final-output noise | 549 |
| repro/stage207_current_head_resource_refresh/resource_comparison.csv | present | current-head r=2/r=4 resource refresh | 900 |
| repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv | present | exact r=6 backend complete-SAB refresh | 479 |
| repro/stage225_exact_refresh_noise_resource_rerun/noise_aggregate.csv | present | exact r=6 fresh noise refresh | 231 |
| repro/stage225_exact_refresh_noise_resource_rerun/resource_comparison.csv | present | exact r=6 fresh resource refresh | 427 |
| repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | present | exact r=6 counter attribution | 1607 |
| repro/stage36_target_perf_summary.csv | present | historical target high-stat performance | 521 |
| repro/stage36_target_noise_seeds50/aggregate.csv | present | historical target 50-seed noise | 235 |
| repro/stage36_stage_noise_seeds10/aggregate.csv | present | historical target stage-noise | 1296 |
| repro/stage36_resource_summary.csv | present | historical target resource matrix | 2083 |
| repro/stage36_added_params_runs10_seeds20/performance_stats.csv | present | added binary parameter 10-run performance | 578 |
| repro/stage36_added_params_runs10_seeds20/noise_summary.csv | present | added binary parameter 20-seed noise | 843 |
| docs/stage26_parameter_branch_log.md | present | PVW non-binary unsupported boundary | 3165 |
| docs/stage26_parameter_perf_noise_log.md | present | added binary parameter smoke history | 7864 |
| docs/stage36_added_params_expansion_log.md | present | added binary high-stat report | 3162 |
| main.c | present | current target parameter definitions | 152574 |
| stage228_next_selects_stage229 | present | Keeps execution on the registered route. |  |
