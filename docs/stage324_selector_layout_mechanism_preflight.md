# Stage324 Selector Layout / Mechanism Preflight

Decision: `PASS_STAGE324_SELECT_SELECTOR_TRANSPOSE_RESOURCE_PREFLIGHT_COMPACT_REMAINS_FROZEN`.

Stage324 prevents the research loop from drifting. Stage323 already denied
another local r=4 dense addmul rewrite. The remaining exact route with code
permission is a bounded selector-transpose resource/microbench probe. The
structured/compact route remains frozen because Stage249 records no production
permission and no public row saving for the dummy-padding survivor.

## Summary

| decision | selected_next_stage | stage323_dense_share | compact_r4_skip_potential_proof_only | compact_public_saving_current | required_dense_speedup_for_1pct_fullsab | hot_path_code_permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE324_SELECT_SELECTOR_TRANSPOSE_RESOURCE_PREFLIGHT_COMPACT_REMAINS_FROZEN | stage325_selector_transpose_resource_probe | 0.212353 | 0.360000 | 0.000000 | 1.048905 | no |

## Route Matrix

| route | status | product_count_effect | resource_effect | blocking_gate | next_action |
| --- | --- | --- | --- | --- | --- |
| exact_dense_local_loop | CLOSED | none | none | no new load/store/count mechanism | do not write more r4 addmul loop code |
| selector_transposed_key_layout | SELECT_STAGE325_PREFLIGHT | none; dense 25 products per coeff block for r=4 remains | replace-format: approx 1.0x key bytes; duplicate-view: approx 2.0x key bytes plus build cost | resource, equality, isolated microbench, and projected full-SAB gate | run Stage325 selector-transpose resource probe outside SAB hot path |
| structured_compact_selector | FROZEN_PROOF_REQUIRED | potential active-row skip 0.360000 for r=4 only if proven | current proof-only dummy route public saving 0.000000 | formal distribution/keygen/security proof plus noise recurrence | no code until a new proof artifact is supplied |
| schedule_sub_a_or_copyback | DEFER_LOW_BUDGET | none | low | profile share must rise or a zero-risk patch must appear | do not select now |
| native_counter_refresh | OPTIONAL_PROXY_UPGRADE | none | none | native Linux perf or equivalent counter access | use only to upgrade attribution, not to block Stage325 microbench |

## Value Projection

| candidate | measured_fullsab_dense_share | required_dense_speedup_for_1pct_fullsab | required_dense_speedup_for_2pct_fullsab | resource_floor | claim_permission |
| --- | --- | --- | --- | --- | --- |
| selector_transposed_key_layout | 0.212353 | 1.048905 | 1.101729 | replace-format 1.0x; duplicate probe 2.0x | microbench-only until full SAB A/B |
| structured_compact_selector | 0.212353 | 1.048905 | 1.101729 | public saving 0.000000 under current dummy-padding evidence | frozen; no complete-SAB speedup claim |

## Gates

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage323_input | PASS | Stage323 decision | PASS_STAGE323_DENSE_MAT_PREFLIGHT_DENY_LOOP_CODE_ROUTE_SELECTOR_FORMAT_REQUIRED | Stage324 is valid only after exact local dense-loop code is denied. |
| G2_compact_production_boundary | PASS_FROZEN | Stage249 production permission | frozen | Structured/compact route cannot receive SAB hot-path code without a new proof artifact. |
| G3_selector_transpose_semantics | PASS_PREFLIGHT_ONLY | semantic transform | storage/view only | Selector-transpose may be tested because it does not alter ciphertext equations if equality holds. |
| G4_value_threshold | PASS_THRESHOLD_RECORDED | required dense speedup for 1% full SAB | 1.048905 | Stage325 must beat this threshold in isolated dense addmul to justify more code. |
| G5_stage324_decision | PASS_STAGE324_SELECT_SELECTOR_TRANSPOSE_RESOURCE_PREFLIGHT_COMPACT_REMAINS_FROZEN | selected route | selector_transposed_key_layout | Proceed to a bounded resource/microbench probe; no full SAB code yet. |

Generated from input head `beea291`.
