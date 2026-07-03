# Stage216 Post-Counter Frontier

Decision: `PASS_STAGE216_POST_COUNTER_FRONTIER_ROUTE_COMPACT_KEYGEN_PREFLIGHT`.

Stage216 closes the Stage215 counter loop without opening another blind tuning
cycle. The primary endpoint remains complete-SAB `T_bootstrap/r`. Stage215
does not authorize complete-SAB A/B for the multirow DFT wrapper, because its
native integrated `combined_current` path failed the admission threshold.

The only selected next route is a bounded compact selector keygen/security
preflight outside the SAB hot path. This is not a compact SAB implementation
claim; it is the next falsifiable gate needed before any representation-changing
algorithm can be coded.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage216_post_counter_frontier/input_status.csv | All post-counter admission inputs must exist. |
| G2_primary_endpoint_preserved | PASS | min_current_T_bootstrap_over_r_speedup | 1.299817000 | repro/stage216_post_counter_frontier/metric_snapshot.csv | The current accepted comparison dimension remains amortized complete-SAB T_bootstrap/r. |
| G3_stage215_wrapper_reopen | PASS_REJECTED | wrapper_admission | REJECTED_BY_STAGE215 | repro/stage215_native_counter_execution/comparison.csv | Native counter evidence does not reopen the Stage213 wrapper route. |
| G4_non_theory_loop_route | PASS_SELECTED_EXECUTABLE_PREFLIGHT | selected_candidate | C5_compact_selector_keygen_preflight | repro/stage216_post_counter_frontier/next_stage_queue.csv | The next route has finite/prototype gates and no SAB hot-path code permission. |
| G5_stage216_decision | PASS_STAGE216_POST_COUNTER_FRONTIER_ROUTE_COMPACT_KEYGEN_PREFLIGHT | decision | PASS_STAGE216_POST_COUNTER_FRONTIER_ROUTE_COMPACT_KEYGEN_PREFLIGHT | repro/stage216_post_counter_frontier/proof_gate.csv | Post-counter frontier is closed for exact wrapper retuning and routed to bounded compact keygen/security preflight. |

## Input Status

| input | status | evidence | role | bytes |
| --- | --- | --- | --- | --- |
| stage206_current_head_highstat | present | repro/stage206_current_head_highstat/performance_stats.csv | complete-SAB T_bootstrap/r evidence | 877 |
| stage207_resource_refresh | present | repro/stage207_current_head_resource_refresh/resource_comparison.csv | resource cost for current-head path | 900 |
| stage208_profile_attribution | present | repro/stage208_current_head_profile_refresh/component_attribution.csv | current bottleneck and schedule counts | 604 |
| stage200_gap_model | present | repro/stage200_formal_gap_model_with_probe/gap_projection.csv | same-format gap and proof obligations | 676 |
| stage203_selector_equation_probe | present | repro/stage203_production_selector_equation_probe/summary.csv | compact proof-only selector equation status | 1452 |
| stage215_native_counter_comparison | present | repro/stage215_native_counter_execution/comparison.csv | native counter performance admission | 659 |
| stage215_native_counter_summary | present | repro/stage215_native_counter_execution/counter_summary.csv | native load/store/FMA evidence | 995 |
| stage215_proof_gate | present | repro/stage215_native_counter_execution/proof_gate.csv | Stage215 final decision | 1294 |
| stage215_next_queue | present | repro/stage215_native_counter_execution/next_stage_queue.csv | post-counter queue | 472 |

## Metric Snapshot

| r | primary_endpoint | current_head_speedup | ci95_low | ci95_high | key_bytes_ratio | keygen_per_lane_ratio | mat_ep_pct_of_cmux | postproc_tail_pct_max | stage215_combined_wrapper_speedup | stage215_torus_wrapper_speedup | stage215_decision | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | T_bootstrap_over_r | 1.299817 | 1.276461 | 1.323539 | 1.013617 | 1.101017 | 40.879 | 1.218 | 0.991041916 | 0.998751297 | NOT_PROMOTED | repro/stage206_current_head_highstat/performance_stats.csv; repro/stage207_current_head_resource_refresh/resource_comparison.csv; repro/stage208_current_head_profile_refresh/component_attribution.csv; repro/stage215_native_counter_execution/comparison.csv |
| 4 | T_bootstrap_over_r | 1.356445 | 1.333331 | 1.380469 | 1.065349 | 1.197131 | 47.760 | 1.222 | 0.953386388 | 0.999295549 | NOT_PROMOTED | repro/stage206_current_head_highstat/performance_stats.csv; repro/stage207_current_head_resource_refresh/resource_comparison.csv; repro/stage208_current_head_profile_refresh/component_attribution.csv; repro/stage215_native_counter_execution/comparison.csv |
| 2 | native_counter_wrapper_combined_current |  |  |  |  |  |  |  |  |  | loads=36246774;stores=24520014;fp512=34472028 | repro/stage215_native_counter_execution/counter_summary.csv |
| 4 | native_counter_wrapper_combined_current |  |  |  |  |  |  |  |  |  | loads=75077247;stores=42960021;fp512=71675439 | repro/stage215_native_counter_execution/counter_summary.csv |

## Mechanism Frontier

| candidate | mechanism_class | admission_status | quantitative_gate | allowed_action | blocked_claim | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| C1_reopen_stage213_multirow_dft_wrapper | same_format_backend_wrapper | REJECTED_BY_STAGE215 | min combined_current speedup=0.953386388; required >=1.010000 | keep flag default-off; do not run full SAB A/B for this wrapper | no complete-SAB speedup or AVX optimality claim | repro/stage215_native_counter_execution/comparison.csv |
| C2_immediate_full_sab_ab_for_wrapper | complete_sab_validation | DENIED_ENTRY_CONDITION_NOT_MET | Stage215 did not promote native integrated wrapper candidate | none | do not spend complete-SAB runs on a failed component admission path | repro/stage215_native_counter_execution/proof_gate.csv |
| C3_same_format_exact_local_retuning | exact_full_mat_local_code | DENIED_WITHOUT_NEW_MECHANISM | DFT requirement=0.169104610;1.208076492; addmul requirement=0.221723249;1.151228774 | only if a new counter-backed dataflow mechanism is specified first | no blind AVX512/layout retuning | repro/stage200_formal_gap_model_with_probe/gap_projection.csv |
| C4_external_backend_primitive | backend_or_library_work | WAIT_EXTERNAL_MECHANISM | must beat Stage200 component threshold and then complete-SAB T_bootstrap/r | prepare preflight only after a real primitive exists | backend speed cannot be reported as algorithmic count reduction | repro/stage200_formal_gap_model_with_probe/gap_projection.csv; repro/stage215_native_counter_execution/counter_summary.csv |
| C5_compact_selector_keygen_preflight | representation_changing_algorithm | SELECT_STAGE217_PREFLIGHT_ONLY | Stage203 status=PASS_STAGE203_PRODUCTION_SELECTOR_EQUATION_PROBE_PROOF_ONLY; production keygen/security/noise still missing | write an executable keygen/security/noise admission probe outside SAB hot path | no compact SAB implementation or speedup claim yet | repro/stage203_production_selector_equation_probe/summary.csv |
| C6_scoped_current_result_reporting | claim_packaging | ALLOWED_SCOPED_ONLY | Stage206/207 current-head evidence remains the speedup/resource basis | report scoped T_bootstrap/r engineering result with limitations | no theoretical optimality, broad novelty, or final algorithm completion | repro/stage206_current_head_highstat/performance_stats.csv; repro/stage207_current_head_resource_refresh/resource_comparison.csv |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage217_compact_keygen_security_preflight | Stage215 rejected exact wrapper reopen and Stage203 compact selector equation is proof-only but alive. | Executable distribution/keygen/noise/resource admission probe outside SAB hot path. | selected | If keygen/security/noise closure fails, compact implementation remains denied and route returns to external mechanism only. | repro/stage203_production_selector_equation_probe/summary.csv; repro/stage216_post_counter_frontier/mechanism_frontier.csv |
| P1 | external_backend_primitive_preflight | A real new FFT/DFT/backend primitive is supplied. | Exact conversion equivalence, component speedup above threshold, then complete-SAB T_bootstrap/r. | waiting_external_mechanism | Record neutral backend ablation; do not update algorithm claim. | repro/stage200_formal_gap_model_with_probe/gap_projection.csv |
| P2 | scoped_report_refresh | No new implementation/proof route is selected or Stage217 fails. | Claim guard: only current exact PVW/MAT-SAB T_bootstrap/r result is reported. | fallback | Repair claim wording and repro pack. | repro/stage206_current_head_highstat/performance_stats.csv |
