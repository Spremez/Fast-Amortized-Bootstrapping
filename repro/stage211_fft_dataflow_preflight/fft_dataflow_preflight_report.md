# Stage211 FFT/DFT Dataflow Preflight

Decision: `PASS_STAGE211_DFT_DATAFLOW_PREFLIGHT_DENY_HOTPATH_CODE`.

Stage211 checks whether the current codebase has a new DFT/FFT dataflow
mechanism that is concrete enough for production SAB hot-path implementation.
It does not add a new kernel. The audit finds that the current MOSFHET wrapper
and SPQLIOS backend expose single-polynomial reverse DFT calls, while prior
same-format batching and direct-scale routes are already neutral, rejected, or
proof-blocked.

The current-head Stage209 budget still matters: `torus_to_dft_rows` reaches a
maximum estimated complete-SAB share of `0.241408`, and a 3% complete-SAB
gain would require at least `1.137206x` component speedup in the best current
projection. Stage211 therefore keeps DFT/dataflow as a valid research target
but denies local hot-path edits until a new primitive or proof exists.

## API Surface

| fact | status | evidence | detail | implication |
| --- | --- | --- | --- | --- |
| polynomial_torus_to_DFT_signature | single_poly_api | src/mosfhet/src/polynomial.c:373 | The MOSFHET wrapper accepts one output DFT polynomial and one input torus polynomial. | MAT rows are converted by repeated scalar-row calls under the current API. |
| spqlios_reverse_torus64_signature | single_row_backend_api | src/mosfhet/src/fft/spqlios/spqlios-fft.h:43 | The public backend primitive exposes one output double buffer and one input torus buffer. | No existing source-level multirow reverse DFT primitive is available to call. |
| spqlios_processor_scratch | one_reverse_scratch_buffer | src/mosfhet/src/fft/spqlios/spqlios-fft.h:31 | The processor owns one reverse scratch buffer in the current structure. | A true multirow primitive needs backend API and scratch-layout changes, not only SAB call-site edits. |
| current_exact_mat_ep_row_loops | row_loop_present | src/mosfhet/src/mattrgsw.c:741; src/mosfhet/src/mattrgsw.c:837 | Found 2 exact MAT-EP runtime row-loop call sites over scratch->dec_dft[i]. | The measured Stage209 torus_to_dft_rows component is this repeated conversion boundary. |
| compact_path_runtime_dft_calls | single_poly_calls_present | src/mosfhet/src/mattrgsw.c:963; src/mosfhet/src/mattrgsw.c:968 | Found 2 compact-path runtime scratch conversion call sites. | The compact path also relies on single-poly DFT calls. |
| compact_key_setup_dft_calls | single_poly_calls_present | src/mosfhet/src/mattrgsw.c:919-922 | Found 4 compact key-row conversion call sites. | Key setup DFT materialization does not create a runtime multirow primitive. |
| multirow_dft_api_search | not_present | src/mosfhet/src/polynomial.c; src/mosfhet/src/fft/spqlios/spqlios-fft.h; src/mosfhet/src/fft/spqlios/fft_processor_spqlios.c | Regex search found 0 reverse-torus batch/rows/multi API names. | Stage211 cannot honestly route to production code through an existing multirow DFT API. |

## Prior Gates

| source | route | status | quantitative_result | evidence | stage211_consequence |
| --- | --- | --- | --- | --- | --- |
| Stage162 | same_format_materialization_count_reduction | CLOSED | reducible_calls_without_representation_change=0 | repro/stage162_materialization_count_feasibility/summary.csv | Do not claim fewer from_DFT calls under current torus-input API. |
| Stage163 | component_major_from_DFT_batching | NEUTRAL_NOT_PROMOTED | component_major_over_backend_current_mean=0.972807930 | repro/stage163_from_dft_batching_microbench/summary.csv | Do not repeat backend batching without a new mechanism. |
| Stage174 | direct_scale_backend_from_DFT_add | NEUTRAL_OR_REJECT | baseline/direct_scale=0.990754925;0.949781500 | repro/stage174_from_dft_direct_scale_gate/summary.csv | Do not implement direct-scale/fused-add variants as full-SAB candidates. |
| Stage136 | batched_decompose_to_DFT | NEUTRAL_OR_NEGATIVE | r4 speedup_current_over_batched=0.739827 | repro/stage136_batched_decomp_dft_gate/summary.csv | Do not reopen this batched decomp/DFT variant. |
| Stage156 | naive_lazy_DFT_accumulator | REJECTED_NONCLOSED | decomposition nonlinearity counterexamples found | repro/stage156_lazy_dft_closure_gate/summary.csv | Do not keep only DFT accumulator state without a new exact decomposition API. |
| Stage164 | representation_change | PROOF_OR_NEW_API_REQUIRED | same-format closed; representation route must prove closure/noise | repro/stage164_representation_closure_route/summary.csv | Representation changes are not local DFT tuning. |
| same_format_call_count_reduction | algorithmic_count | REJECTED | reducible_calls_without_representation_change=0 | repro/stage162_materialization_count_feasibility/materialization_lower_bound.csv | do not reopen without representation change |
| backend_component_major_batching | backend_wall_time | NEUTRAL | component_major_batch_over_backend_current_mean=0.972807930 | repro/stage163_from_dft_batching_microbench/comparison.csv | do not integrate into full SAB |
| direct_scale_or_fused_add_variant | backend_wall_time | NEUTRAL_OR_REJECT | baseline/direct_scale mean ratio=0.990754925 | repro/stage174_from_dft_direct_scale_gate/comparison.csv | do not keep tuning direct-scale |
| batched_decompose_to_DFT | decomp_dft_dataflow | REJECTED | r4 speedup_current_over_batched=0.739827 at N=1024 and 0.671246 at N=512 | repro/stage136_batched_decomp_dft_gate/ratio_summary.csv | do not reopen this batching shape |
| new_torus_to_DFT_backend_kernel | backend_primitive | OPEN_ONLY_EXTERNALLY | must beat component speedup 1.208076492; no local MOSFHET code path identified | repro/stage194_exact_dft_conversion_preflight/component_budget.csv | requires backend-library kernel work or external perf evidence, not local SAB code |
| lazy_DFT_or_DFT_state_accumulator | representation_change | REJECTED_OR_PROOF_BLOCKED | naive lazy DFT rejected; representation change needs closure/noise proof | repro/stage156_lazy_dft_closure_gate/summary.csv; repro/stage164_representation_closure_route/summary.csv | keep as proof route only |

## Mechanism Matrix

| mechanism | mechanism_class | estimated_full_sab_share | min_component_speedup_for_3pct | decision | reason | next_gate |
| --- | --- | --- | --- | --- | --- | --- |
| M1_current_row_loop | baseline | 0.241408 | 1.137206 | BASELINE_ONLY | It explains the measured cost but provides no new dataflow or fewer operations. | Use as reference for any future DFT primitive. |
| M2_reopen_same_format_batching | old_backend_loop_order | 0.241408 | 1.137206 | DENY_REOPEN | Stage136 batched decomp-to-DFT was negative and Stage163 backend batching was neutral. | Only reopen with a different API or new counter-backed mechanism. |
| M3_direct_decompose_to_dft_or_lazy_state | representation_change | 0.241408 | 1.137206 | PROOF_BLOCKED | Decomposition uses coefficient-domain subtract, offset, shift, and mask before DFT; bypassing the torus polynomial needs exact closure and noise proof. | Separate proof route only; no production hot path from Stage211. |
| M4_new_multirow_fft_backend_api | new_backend_primitive | 0.241408 | 1.137206 | ADMIT_BACKEND_API_DESIGN_ONLY | A true multirow reverse DFT could target the largest current component, but the source tree has no callable primitive yet. | Stage212 should specify and microbench a standalone backend prototype before SAB integration. |
| M5_native_counter_route | measurement_infrastructure | 0.241408 | 1.137206 | BLOCKED_LOCALLY | Stage209 counter status is blocked_no_perf_binary; local perf_path is empty. | Run on native Linux or a configured remote host before reopening assembly-level claims. |

## Proof Gates

| gate | status | evidence | detail | remaining_gap |
| --- | --- | --- | --- | --- |
| G1_stage210_input | PASS | repro/stage210_candidate_admission/candidate_matrix.csv | Stage210 admits only C2 as preflight-only DFT/FFT dataflow work. | Stage211 must decide whether a concrete mechanism exists now. |
| G2_api_surface | PASS_SINGLE_ROW_DFT_API_ONLY | repro/stage211_fft_dataflow_preflight/api_surface.csv | The current wrapper/backend exposes single-poly reverse DFT and row-loop call sites. | No existing multirow DFT primitive can be integrated directly. |
| G3_prior_route_guard | PASS_OLD_DFT_ROUTES_REJECTED | repro/stage211_fft_dataflow_preflight/prior_gate_matrix.csv | Same-format batching, direct-scale, batched decomp-to-DFT, and naive lazy-state routes are closed or proof-blocked. | Only genuinely new mechanisms may proceed. |
| G4_mechanism_admission | PASS_BACKEND_API_DESIGN_ONLY | repro/stage211_fft_dataflow_preflight/mechanism_matrix.csv | The only admitted route is a future standalone multirow FFT/backend API design, not current SAB hot-path code. | Needs a prototype API and microbench before integration. |
| G5_stage211_decision | PASS_STAGE211_DFT_DATAFLOW_PREFLIGHT_DENY_HOTPATH_CODE | repro/stage211_fft_dataflow_preflight/proof_gate.csv | Stage211 prevents theory drift by denying local production hot-path edits when no current source-level primitive exists. | Proceed to Stage212 backend API sketch/probe or native counter refresh. |

## Next Queue

| priority | route | entry_condition | gate | status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | stage212_multirow_fft_backend_api_probe | Stage211 admits backend/API design only. | Define exact API, scratch layout, correctness oracle, and microbench for row groups before SAB integration. | ready | repro/stage211_fft_dataflow_preflight/mechanism_matrix.csv |
| P1 | native_perf_counter_refresh | Native Linux perf or configured remote host is available. | Collect load/store/FMA/cache/cycle counters for Stage209 split variants. | blocked_locally | repro/stage209_current_head_mat_ep_split/environment.csv |
| P2 | sab_hotpath_integration | Stage212 or native counters promote a concrete mechanism. | Flag-only implementation, staged equivalence, full SAB A/B, noise/resource, and claim audit. | denied_now | repro/stage211_fft_dataflow_preflight/proof_gate.csv |
