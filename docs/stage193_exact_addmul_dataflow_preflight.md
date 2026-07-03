# Stage193 Exact Addmul Dataflow Preflight

Decision: `PASS_STAGE193_EXACT_ADDMUL_PREFLIGHT_NO_CODE_ROUTE_DFT_MECHANISM`.

Stage193 executes the non-theory route selected by Stage192. It audits the
exact full-MAT addmul path before code. The result is no-code: every candidate
is already rejected, requires a key-format gate, or fails the projected
complete-SAB `T_bootstrap/r` promotion threshold.

The only new local mechanism identified is caching decomposed DFT rows across
the r=6 output tiles. Its optimistic memory-op upper bound is below the
Stage180 component speedup required for a 3% complete-SAB gain.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage193_inputs | PASS | required_inputs_present | 1 | src/mosfhet/src/mattrgsw.c; repro/stage180_mat_ep_split_probe/derived_projection.csv; repro/stage183_addmul_dataflow_screen/mechanism_screen.csv | Stage193 consumes source facts, Stage180 counters, and prior rejected mechanism ledgers. | Repair missing inputs before interpreting preflight. |
| stage193_source_counter_audit | PASS_RECORDED | source_facts;counter_rows | 5;1 | repro/stage193_exact_addmul_dataflow_preflight/source_facts.csv; repro/stage193_exact_addmul_dataflow_preflight/counter_summary.csv | Current exact addmul is already AVX512 FMA and prior r6 dataflow families exist as explicit flags. | Screen only genuinely new mechanisms. |
| stage193_dec_cache_projection | REJECT_BELOW_COMPLETE_SAB_GATE | r6_full_sab_speedup_bound | 1.022675 | repro/stage193_exact_addmul_dataflow_preflight/projection_bounds.csv | The only local duplicate-load mechanism has an optimistic r=6 bound below the 3pct complete-SAB promotion threshold. | Do not implement dec-cache tile variant. |
| stage193_code_permission | DENY_NO_ADDMUL_CODE_CANDIDATE | promoted_candidates | 0 | repro/stage193_exact_addmul_dataflow_preflight/dataflow_candidates.csv | All addmul candidates are prior-rejected, key-format-blocked, or below the projected complete-SAB gate. | Route to Stage194 DFT conversion mechanism preflight. |
| stage193_decision | PASS_STAGE193_EXACT_ADDMUL_PREFLIGHT_NO_CODE_ROUTE_DFT_MECHANISM | next_stage | Stage194 | repro/stage193_exact_addmul_dataflow_preflight/next_stage_queue.csv | Exact addmul preflight avoids speculative implementation and routes to the secondary DFT mechanism. | Proceed to Stage194. |

## Source Facts

| fact | status | line | evidence | implication |
| --- | --- | --- | --- | --- |
| complex_addmul_uses_avx512_fma | yes | 146 | src/mosfhet/src/mattrgsw.c | The exact addmul hot loop is already vectorized; Stage193 must find dataflow savings, not basic AVX512 enablement. |
| rgt4_tiled_kernel_reuses_dec_per_output_tile | yes | 458 | src/mosfhet/src/mattrgsw.c | For r=6, dec rows are loaded once per output tile; this is the only local duplicate-load opportunity. |
| r6_fulltile_exists | yes | 520 | src/mosfhet/src/mattrgsw.c | All-output register-resident accumulation was already implemented and rejected by prior gates. |
| r6_bodymajor_exists | yes | 606 | src/mosfhet/src/mattrgsw.c | Output-major dataflow was already implemented and rejected by prior gates. |
| sub_decomp_avx512_exists_default_off | yes | 15 | src/mosfhet/Makefile.def | Sub-decompose vectorization remains an explicit negative ablation, not a promoted path. |

## Counter Summary

| variant | per_call_us | loads | stores | fp512 | cache_miss_rate | ipc | evidence | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| addmul_from_dec_dft | 22.923460937 | 64970716 | 32210397 | 70084809 | 0.047610 | 1.335007 | repro/stage180_mat_ep_split_probe/counter_metrics.csv | Low cache-miss rate and heavy FP512 mean prefetch-only is weak; only real load/store reduction or fewer FMA-equivalent ops can matter. |

## Projection Bounds

| candidate | r | tile_outputs | selector_loads_per_coeff | dec_loads_current_per_coeff | dec_loads_cached_per_coeff | duplicate_dec_load_fraction | upper_component_speedup | required_component_speedup_for_3pct_full_sab | full_sab_speedup_bound | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dec_register_cache_across_tiles | 6 | 4 | 98 | 28 | 14 | 0.100000 | 1.111111 | 1.151228774 | 1.022675 | REJECT_TARGET_R6_BELOW_3PCT_GATE |
| dec_register_cache_across_tiles | 8 | 4 | 162 | 54 | 18 | 0.153846 | 1.181818 | 1.151228774 | 1.035316 | NON_TARGET_R8_REQUIRES_FULL_SAB_CONTEXT |

## Dataflow Candidates

| candidate | new_mechanism | prior_status | static_or_counter_result | risk | code_permission |
| --- | --- | --- | --- | --- | --- |
| dec_register_cache_across_tiles | yes | not directly tested; adjacent fulltile exists | r6 upper component speedup 1.111111 below required 1.151228774 | requires keeping 14 dec registers plus tile accumulators; may spill and lose the static upper bound | DENY_BELOW_FULL_SAB_GATE |
| all_outputs_fulltile | no | rejected | Stage111/151 did not promote fulltile under complete-SAB gates | register pressure and variance already observed | DENY_PRIOR_REJECTED |
| bodymajor_output_major | no | rejected | Stage154 bodymajor/tile4 complete-SAB result was slower | worse complete-SAB T_bootstrap/r | DENY_PRIOR_REJECTED |
| row_streaming_decompose_dft_addmul | no | rejected | Stage165 streaming lost to current tiled AVX | decomposition/DFT locality did not translate to speed | DENY_PRIOR_REJECTED |
| selector_transposed_key_layout | yes | blocked | could improve selector locality but changes key format | requires keygen/resource/noise gates, not a local addmul edit | DENY_KEY_FORMAT_GATE_REQUIRED |
| prefetch_only_selector_rows | weak | not promoted | Stage180 addmul cache miss rate is low; no arithmetic/load-count reduction | implementation-only tweak unlikely to reach complete-SAB threshold | DENY_NO_PROJECTED_3PCT |

## Next Stage Queue

| stage | title | status | goal | required_inputs | correctness_gate | performance_gate | failure_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Stage194 | Exact DFT Conversion Mechanism Preflight | NEXT | screen a genuinely new torus_to_DFT/from_DFT mechanism after addmul preflight found no code candidate | repro/stage180_mat_ep_split_probe/derived_projection.csv; repro/stage174_from_dft_direct_scale_gate/summary.csv; src/mosfhet/src/polynomial.c | no source changes; specify exact DFT/conversion equivalence first | component speedup must exceed Stage180 3pct full-SAB requirement | route to scoped paper/repro package rather than speculative implementation |
| Stage195 | Scoped Paper/Repro Refresh | CONDITIONAL | if Stage194 finds no code candidate, freeze engineering result and limitations | repro/stage188_scoped_manuscript_skeleton/summary.csv; repro/stage192_compact_admission_route_selection/summary.csv; repro/stage193_exact_addmul_dataflow_preflight/summary.csv | claim guard forbids compact/optimality overclaim | no new speedup claim without complete-SAB benchmark | repair claim ledger |
