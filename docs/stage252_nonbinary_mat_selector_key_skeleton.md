# Stage252 Non-Binary MAT Selector Key Skeleton

Decision: `PASS_STAGE252_NONBINARY_MAT_SELECTOR_KEY_SKELETON_READY_ISOLATED_EQUIVALENCE`.

Stage252 defines a non-production key skeleton for extending binary
PVW/MAT-SAB to include-zero and ternary selector semantics. It adds no
production source and makes no speed claim.

## Skeleton Design

| component | selector_family | role | count_per_key | mat_object | source_delta | production_status |
| --- | --- | --- | --- | --- | --- | --- |
| distance_bits | s | binary sparse distance bits shared across r body lanes | (h + 1) * r_prec | MAT_TRGSW_DFT | matches current SAB_PVW_Key::s | existing_binary_only |
| include_zero_presence | s_coff | presence selector c in {0,1}: p + c((X^a - 1)p) | h if include_zero | MAT_TRGSW_DFT | new non-production skeleton family | not_implemented |
| ternary_sign | s_sign | sign selector s in {0,1}: choose X^a or X^-a | h if ternary | MAT_TRGSW_DFT | new non-production skeleton family | not_implemented |
| selector_api_boundary | stage252_key | own optional selector families without changing SAB_PVW_Key | distance + optional s_coff + optional s_sign | metadata-only C skeleton in repro | no production header/source edit | isolated_preflight_only |


## Layout Projection

| param | branch | h | r_prec | distance_count | coff_count | sign_count | total_selector_objects | count_ratio_vs_binary | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target_SET_2_3_2048 | binary | 39 | 7 | 280 | 0 | 0 | 280 | 1.000000 | selector-object count only; not byte, noise, or speed evidence |
| target_SET_2_3_2048 | include_zero | 39 | 7 | 280 | 39 | 0 | 319 | 1.139286 | selector-object count only; not byte, noise, or speed evidence |
| target_SET_2_3_2048 | ternary | 39 | 7 | 280 | 0 | 39 | 319 | 1.139286 | selector-object count only; not byte, noise, or speed evidence |
| target_SET_2_3_2048 | include_zero_plus_ternary_stress | 39 | 7 | 280 | 39 | 39 | 358 | 1.278571 | selector-object count only; not byte, noise, or speed evidence |
| added_SET_4_5_2048 | binary | 42 | 7 | 301 | 0 | 0 | 301 | 1.000000 | selector-object count only; not byte, noise, or speed evidence |
| added_SET_4_5_2048 | include_zero | 42 | 7 | 301 | 42 | 0 | 343 | 1.139535 | selector-object count only; not byte, noise, or speed evidence |
| added_SET_4_5_2048 | ternary | 42 | 7 | 301 | 0 | 42 | 343 | 1.139535 | selector-object count only; not byte, noise, or speed evidence |
| added_SET_4_5_2048 | include_zero_plus_ternary_stress | 42 | 7 | 301 | 42 | 42 | 385 | 1.279070 | selector-object count only; not byte, noise, or speed evidence |
| added_SET_2_3_4096 | binary | 32 | 8 | 264 | 0 | 0 | 264 | 1.000000 | selector-object count only; not byte, noise, or speed evidence |
| added_SET_2_3_4096 | include_zero | 32 | 8 | 264 | 32 | 0 | 296 | 1.121212 | selector-object count only; not byte, noise, or speed evidence |
| added_SET_2_3_4096 | ternary | 32 | 8 | 264 | 0 | 32 | 296 | 1.121212 | selector-object count only; not byte, noise, or speed evidence |
| added_SET_2_3_4096 | include_zero_plus_ternary_stress | 32 | 8 | 264 | 32 | 32 | 328 | 1.242424 | selector-object count only; not byte, noise, or speed evidence |


## API Contract

| api | inputs | positive_contract | negative_contract | hot_path_status |
| --- | --- | --- | --- | --- |
| stage252_key_alloc | r, h, r_prec, include_zero, ternary | allocates distance bits plus requested optional selector families | rejects r<=0, h<=0, r_prec<=0 | non_production |
| stage252_selector_at | family, step, bit | returns distance/coff/sign selector metadata in range | rejects missing family and out-of-range indices | non_production |
| stage252_hot_scan | key object | counts selector families without allocation | detects role/count mismatches | no hot allocation in probe |
| stage253_entry_requirement | skeleton plus scalar equation target | may proceed to isolated sub_a equivalence only | does not authorize full SAB or production keygen | blocked |


## C Probe

| case | r | h | r_prec | include_zero | ternary | distance_count | coff_count | sign_count | total_count | expected_total | role_mismatches | guard_failures | hot_alloc_delta | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| binary_target | 4 | 39 | 7 | 0 | 0 | 280 | 0 | 0 | 280 | 280 | 0 | 0 | 0 | PASS_STAGE252_KEY_SKELETON |
| include_zero_target | 4 | 39 | 7 | 1 | 0 | 280 | 39 | 0 | 319 | 319 | 0 | 0 | 0 | PASS_STAGE252_KEY_SKELETON |
| ternary_target | 4 | 39 | 7 | 0 | 1 | 280 | 0 | 39 | 319 | 319 | 0 | 0 | 0 | PASS_STAGE252_KEY_SKELETON |
| include_zero_ternary_stress | 4 | 39 | 7 | 1 | 1 | 280 | 39 | 39 | 358 | 358 | 0 | 0 | 0 | PASS_STAGE252_KEY_SKELETON |
| include_zero_r2 | 2 | 39 | 7 | 1 | 0 | 280 | 39 | 0 | 319 | 319 | 0 | 0 | 0 | PASS_STAGE252_KEY_SKELETON |
| ternary_r2 | 2 | 39 | 7 | 0 | 1 | 280 | 0 | 39 | 319 | 319 | 0 | 0 | 0 | PASS_STAGE252_KEY_SKELETON |
| added_2048_r4 | 4 | 42 | 7 | 1 | 1 | 301 | 42 | 42 | 385 | 385 | 0 | 0 | 0 | PASS_STAGE252_KEY_SKELETON |
| added_4096_r4 | 4 | 32 | 8 | 1 | 1 | 264 | 32 | 32 | 328 | 328 | 0 | 0 | 0 | PASS_STAGE252_KEY_SKELETON |


## Source Isolation

| path | tracked_source | modified_in_stage252 | status | interpretation |
| --- | --- | --- | --- | --- |
| include/sab_pvw.h | yes | no | PASS_UNCHANGED | Stage252 must not change production SAB/PVW source. |
| src/sab_pvw.c | yes | no | PASS_UNCHANGED | Stage252 must not change production SAB/PVW source. |
| include/sab.h | yes | no | PASS_UNCHANGED | Stage252 must not change production SAB/PVW source. |
| src/sparse_amortized_bootstrap.c | yes | no | PASS_UNCHANGED | Stage252 must not change production SAB/PVW source. |


## Admission

| route | decision | production_permission | allowed_next_step | blocked_before |
| --- | --- | --- | --- | --- |
| stage252_key_skeleton | ADMITTED_NON_PRODUCTION | no | Stage253 isolated sub_a equivalence | production keygen; full sparse_mul; full SAB; speed claim |
| include_zero_pvw | SKELETON_ONLY | no | prove p + c((X^a - 1)p) per lane using MAT s_coff | noise/resource/full-SAB evidence |
| ternary_pvw | SKELETON_ONLY | no | prove X^a vs X^-a per lane using MAT s_sign | noise/resource/full-SAB evidence |


## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| nonbinary_selector_key_skeleton | supported_nonproduction | A non-production MAT selector key skeleton for s_coff/s_sign is defined and compile-probed. | Non-binary PVW/MAT-SAB is implemented. | repro/stage252_nonbinary_mat_selector_key_skeleton/toy_key_object_probe.csv |
| nonbinary_speedup | unsupported | No non-binary speedup is claimed. | Ternary/include-zero PVW bootstrapping is faster than scalar. | repro/stage252_nonbinary_mat_selector_key_skeleton/admission_decision.csv |
| source_isolation | supported | Stage252 does not change production SAB/PVW source files. | Stage252 productionizes non-binary support. | repro/stage252_nonbinary_mat_selector_key_skeleton/source_isolation.csv |


## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs_and_stage251 | PASS | inputs;stage251 | true;true | repro/stage252_nonbinary_mat_selector_key_skeleton/input_status.csv; repro/stage251_nonbinary_selector_semantics/proof_gate.csv | Stage252 is valid only after Stage251 blocks current production non-binary PVW. |
| G2_compile_run | PASS | compile;run | true;true | repro/stage252_nonbinary_mat_selector_key_skeleton/compile_probe.log; repro/stage252_nonbinary_mat_selector_key_skeleton/run_probe.log | The skeleton compiles and runs as an isolated C key-object probe. |
| G3_layout_roles | PASS | probe_rows | 8 | repro/stage252_nonbinary_mat_selector_key_skeleton/toy_key_object_probe.csv | Distance, s_coff, and s_sign selector-family counts and guards match the skeleton contract. |
| G4_source_isolation | PASS | production_source_modified | no | repro/stage252_nonbinary_mat_selector_key_skeleton/source_isolation.csv | Stage252 leaves scalar/default and sab_pvw production sources unchanged. |
| G5_admission_boundary | PASS_NO_PRODUCTION | production_permission | no | repro/stage252_nonbinary_mat_selector_key_skeleton/admission_decision.csv | Stage252 admits only Stage253 isolated equivalence. |
| G6_stage252_decision | PASS_STAGE252_NONBINARY_MAT_SELECTOR_KEY_SKELETON_READY_ISOLATED_EQUIVALENCE | decision | PASS_STAGE252_NONBINARY_MAT_SELECTOR_KEY_SKELETON_READY_ISOLATED_EQUIVALENCE | repro/stage252_nonbinary_mat_selector_key_skeleton/proof_gate.csv | Proceed to isolated include-zero/ternary sub_a equivalence, not production SAB integration. |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage253_isolated_nonbinary_pvw_sub_a_equivalence | Stage252 skeleton passes compile/layout/source-isolation gates. | prove include-zero and ternary sub_a equations per lane against scalar reference | selected_next | keep non-binary PVW unsupported | repro/stage252_nonbinary_mat_selector_key_skeleton/toy_key_object_probe.csv |
| P1 | stage254_nonbinary_selector_keygen_noise_preflight | Stage253 isolated equivalence passes. | define encrypted MAT s_coff/s_sign keygen and noise/resource side conditions | conditional | do not integrate full SAB | repro/stage252_nonbinary_mat_selector_key_skeleton/admission_decision.csv |
| P2 | stage255_nonbinary_full_sab | keygen/noise preflight passes and production implementation is explicitly admitted | same-backend complete-SAB T_bootstrap/r, multi-seed correctness/noise, resource | future_gated | no non-binary speedup claim | repro/stage252_nonbinary_mat_selector_key_skeleton/claim_boundary.csv |


Generated from head `c5ed044`.
