# Stage194 Exact DFT/Conversion Preflight

Decision: `PASS_STAGE194_EXACT_DFT_PREFLIGHT_NO_CODE_ROUTE_SCOPED_REFRESH`.

Stage194 executes the DFT/conversion route selected by Stage193. It performs a
source/prior-gate/budget audit before any implementation.

Result: no local DFT/conversion code candidate is authorized. Same-format call
count reduction is closed, backend batching and direct-scale candidates were
neutral, batched decompose-to-DFT missed its target, and lazy DFT state is not
closed. Only an external backend primitive route remains possible, and it must
restart with equivalence and complete-SAB gates.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage194_inputs | PASS | required_inputs_present | 1 | src/mosfhet/src/polynomial.c; repro/stage180_mat_ep_split_probe/derived_projection.csv; repro/stage174_from_dft_direct_scale_gate/summary.csv; repro/stage163_from_dft_batching_microbench/summary.csv | Stage194 consumes DFT/conversion source, Stage180 budgets, and prior DFT/backend gates. | Repair missing inputs before interpreting preflight. |
| stage194_source_prior_audit | PASS_RECORDED | source_facts;prior_gates | 5;6 | repro/stage194_exact_dft_conversion_preflight/source_facts.csv; repro/stage194_exact_dft_conversion_preflight/prior_gate_matrix.csv | Current path already uses backend fused add and cached FFT processors; prior backend batching/direct-scale candidates were neutral. | Screen only new mechanisms. |
| stage194_component_budget | PASS_RECORDED | torus_to_dft_required_speedup | 1.208076492 | repro/stage194_exact_dft_conversion_preflight/component_budget.csv | DFT conversion can matter only if a new mechanism exceeds the complete-SAB projection threshold. | Deny local code if no candidate reaches the threshold. |
| stage194_code_permission | DENY_NO_LOCAL_DFT_CODE_CANDIDATE | promoted_candidates;external_only_candidates | 0;1 | repro/stage194_exact_dft_conversion_preflight/mechanism_candidates.csv | All local DFT/conversion candidates are rejected, neutral, or proof-blocked; only external backend primitive work remains optional. | Route to Stage195 scoped paper/repro refresh. |
| stage194_decision | PASS_STAGE194_EXACT_DFT_PREFLIGHT_NO_CODE_ROUTE_SCOPED_REFRESH | next_stage | Stage195 | repro/stage194_exact_dft_conversion_preflight/next_stage_queue.csv | The local implementation frontier is exhausted under current gates; consolidate report/repro rather than speculate. | Proceed to Stage195. |

## Source Facts

| fact | status | line | evidence | implication |
| --- | --- | --- | --- | --- |
| dft_to_torus_uses_backend_direct | yes | 352 | src/mosfhet/src/polynomial.c | Same-format materialization is delegated to backend FFT; local arithmetic changes must beat the backend primitive. |
| dft_to_torus_add_uses_backend_fused_add | yes | 368 | src/mosfhet/src/polynomial.c | The current add path already uses fused backend materialize+add for TORUS64. |
| pvw_from_dft_add_has_backend_flag | yes | 765 | src/mosfhet/src/pvwtmlwe.c | Stage174 tested this explicit backend/SIMD candidate and did not promote it. |
| mat_sub_dft_converts_every_decomposed_row | yes | 741 | src/mosfhet/src/mattrgsw.c | Exact torus-input MAT EP still needs one torus_to_DFT per decomposed row before addmul. |
| fft_processor_cached_per_thread_and_N | yes | 335 | src/mosfhet/src/polynomial.c | Processor construction is already cached; optimization must target conversion work, not init overhead. |

## Prior Gate Matrix

| gate | route | status | quantitative_result | evidence | consequence |
| --- | --- | --- | --- | --- | --- |
| Stage162 | same_format_materialization_count_reduction | CLOSED | reducible_calls_without_representation_change=0 | repro/stage162_materialization_count_feasibility/summary.csv | Do not claim fewer from_DFT calls under current torus-input API. |
| Stage163 | component_major_from_DFT_batching | NEUTRAL_NOT_PROMOTED | component_major_over_backend_current_mean=0.972807930 | repro/stage163_from_dft_batching_microbench/summary.csv | Do not repeat backend batching without a new mechanism. |
| Stage174 | direct_scale_backend_from_DFT_add | NEUTRAL_OR_REJECT | baseline/direct_scale=0.990754925;0.949781500 | repro/stage174_from_dft_direct_scale_gate/summary.csv | Do not implement direct-scale/fused-add variants as full-SAB candidates. |
| Stage136 | batched_decompose_to_DFT | NEUTRAL_OR_NEGATIVE | r4 speedup_current_over_batched=0.739827 | repro/stage136_batched_decomp_dft_gate/summary.csv | Do not reopen this batched decomp/DFT variant. |
| Stage156 | naive_lazy_DFT_accumulator | REJECTED_NONCLOSED | decomposition nonlinearity counterexamples found | repro/stage156_lazy_dft_closure_gate/summary.csv | Do not keep only DFT accumulator state without a new exact decomposition API. |
| Stage164 | representation_change | PROOF_OR_NEW_API_REQUIRED | same-format closed; representation route must prove closure/noise | repro/stage164_representation_closure_route/summary.csv | Representation changes are not local DFT tuning. |

## Component Budget

| component | full_sab_share | required_component_speedup_for_3pct_full_sab | per_call_us | loads | stores | fp512 | cache_miss_rate | evidence | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| torus_to_dft_rows | 0.169104610 | 1.208076492 | 17.483339844 | 68118974 | 53511995 | 59186396 | 0.139774 | repro/stage180_mat_ep_split_probe/derived_projection.csv; repro/stage180_mat_ep_split_probe/counter_metrics.csv | Large enough to matter only if a new mechanism beats about 1.208x component speedup. |
| sub_decompose | 0.103963271 | 1.389195069 | 10.748525391 | 31961718 | 26882399 | 5909004 |  | repro/stage180_mat_ep_split_probe/derived_projection.csv | Sub-decompose alone requires a much larger speedup and Stage181 already rejected the AVX512 variant. |
| addmul_from_dec_dft | 0.221723249 | 1.151228774 | 22.923460937 | 64970716 | 32210397 | 70084809 |  | repro/stage193_exact_addmul_dataflow_preflight/summary.csv | Closed by Stage193 unless a new nonlocal mechanism appears. |

## Mechanism Candidates

| candidate | mechanism_type | status | best_evidence | quantitative_or_static_result | code_permission | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| same_format_call_count_reduction | algorithmic_count | REJECTED | repro/stage162_materialization_count_feasibility/materialization_lower_bound.csv | reducible_calls_without_representation_change=0 | DENY | do not reopen without representation change |
| backend_component_major_batching | backend_wall_time | NEUTRAL | repro/stage163_from_dft_batching_microbench/comparison.csv | component_major_batch_over_backend_current_mean=0.972807930 | DENY | do not integrate into full SAB |
| direct_scale_or_fused_add_variant | backend_wall_time | NEUTRAL_OR_REJECT | repro/stage174_from_dft_direct_scale_gate/comparison.csv | baseline/direct_scale mean ratio=0.990754925 | DENY | do not keep tuning direct-scale |
| batched_decompose_to_DFT | decomp_dft_dataflow | REJECTED | repro/stage136_batched_decomp_dft_gate/ratio_summary.csv | r4 speedup_current_over_batched=0.739827 at N=1024 and 0.671246 at N=512 | DENY | do not reopen this batching shape |
| new_torus_to_DFT_backend_kernel | backend_primitive | OPEN_ONLY_EXTERNALLY | repro/stage194_exact_dft_conversion_preflight/component_budget.csv | must beat component speedup 1.208076492; no local MOSFHET code path identified | DENY_LOCAL_CODE | requires backend-library kernel work or external perf evidence, not local SAB code |
| lazy_DFT_or_DFT_state_accumulator | representation_change | REJECTED_OR_PROOF_BLOCKED | repro/stage156_lazy_dft_closure_gate/summary.csv; repro/stage164_representation_closure_route/summary.csv | naive lazy DFT rejected; representation change needs closure/noise proof | DENY | keep as proof route only |

## Next Stage Queue

| stage | title | status | goal | required_inputs | correctness_gate | performance_gate | failure_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage195 | Scoped Paper/Repro Refresh | NEXT | freeze the current exact PVW/MAT-SAB engineering result, negative frontiers, and compact proof blockers into a clean report/repro package | repro/stage188_scoped_manuscript_skeleton/summary.csv; repro/stage192_compact_admission_route_selection/summary.csv; repro/stage193_exact_addmul_dataflow_preflight/summary.csv; repro/stage194_exact_dft_conversion_preflight/summary.csv | claim guard forbids compact implementation, theoretical optimality, or unverified novelty | only Stage178/169 complete-SAB T_bootstrap/r evidence may be used as speedup | repair claim ledger and manuscript skeleton |
| Future backend route | External FFT Backend Primitive Work | OPTIONAL_EXTERNAL | only if a new backend torus_to_DFT primitive is available, rerun Stage180/Stage194 budgets | new backend implementation; repro/stage194_exact_dft_conversion_preflight/component_budget.csv | bit-exact conversion equivalence | component speedup above Stage180 requirement and complete-SAB A/B | record neutral backend ablation |
