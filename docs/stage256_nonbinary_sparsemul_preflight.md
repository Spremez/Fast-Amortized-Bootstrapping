# Stage256 Non-Binary Sparse_Mul Preflight

Decision: `PASS_STAGE256_NONBINARY_SPARSEMUL_PREFLIGHT_READY_EXPLICIT_IMPLEMENTATION`.

Stage256 lifts the non-binary route from isolated `sub_a` selector updates to
the `sparse_mul` integration boundary. It does not implement production code.

## Source Boundary

| boundary | source_fact | observed | required_delta | production_edit_allowed_now |
| --- | --- | --- | --- | --- |
| current_binary_key_object | SAB_PVW_Key contains only MAT_TRGSW_DFT *** s | yes | new explicit non-binary key object or sidecar with s_coff/s_sign | no |
| current_sparse_mul | sab_pvw_sparse_mul_binary consumes sab->s and sab_pvw_sub_a_binary | yes | new sab_pvw_nonbinary_sparse_mul path consuming active state and selector families | only_after_stage257 |
| binary_guard | PVW constructor rejects coeff != 1 | yes | do not remove guard; add explicit non-binary constructor | no |
| scalar_reference | scalar sub_a has include_zero and ternary branches | yes | use scalar equations as reference for Stage257 tests | not_applicable |
| source_isolation_sab_pvw.h | include/sab_pvw.h | unchanged | Stage256 must not modify production source | no |
| source_isolation_sab_pvw.c | src/sab_pvw.c | unchanged | Stage256 must not modify production source | no |
| source_isolation_sparse_amortized_bootstrap.c | src/sparse_amortized_bootstrap.c | unchanged | Stage256 must not modify production source | no |


## Integration Design

| component | required_shape | consumer | invariant | stage257_task |
| --- | --- | --- | --- | --- |
| nonbinary_key_object | distance bit selectors plus optional MAT s_coff/s_sign families | nonbinary sparse_mul/sub_a only | binary SAB_PVW_Key and sab_pvw_sparse_mul_binary remain unchanged | define explicit sidecar or new key type |
| rgsw_monomial_step | reuse existing sab_pvw_RGSW_monomial_mul_state for distance-bit schedule | same active buffer state as binary path | CMUX count remains (h+1)*r_prec*in_N | call existing state primitive, no non-binary change |
| include_zero_sub_a | p <- p + s_coff*((X^a - 1)p) | MAT s_coff selector for every sparse step | one extra selector external product per accumulator index per step | implement isolated function behind explicit flag/path |
| ternary_sub_a | p1 <- X^a p; p <- p1 + s_sign*((X^-2a - 1)p1) | MAT s_sign selector for every sparse step | one extra selector external product per accumulator index per step | implement isolated function behind explicit flag/path |
| final_rgsw | same final RGSW monomial multiplication as binary path | distance-bit selectors only | no sub_a after final RGSW | preserve binary schedule order |


## Schedule Count Projection

| param | branch | in_N | h | r_prec | binary_main_ep_calls | extra_suba_ep_calls | total_ep_class_calls | extra_over_binary_main | total_over_binary_main | claim_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_2048 | include_zero | 2048 | 39 | 7 | 573440 | 79872 | 653312 | 0.139286 | 1.139286 | single_branch_preflight |
| SET_2_3_2048 | ternary | 2048 | 39 | 7 | 573440 | 79872 | 653312 | 0.139286 | 1.139286 | single_branch_preflight |
| SET_2_3_2048 | stress_both | 2048 | 39 | 7 | 573440 | 159744 | 733184 | 0.278571 | 1.278571 | stress_only |
| SET_4_5_2048 | include_zero | 2048 | 42 | 7 | 616448 | 86016 | 702464 | 0.139535 | 1.139535 | single_branch_preflight |
| SET_4_5_2048 | ternary | 2048 | 42 | 7 | 616448 | 86016 | 702464 | 0.139535 | 1.139535 | single_branch_preflight |
| SET_4_5_2048 | stress_both | 2048 | 42 | 7 | 616448 | 172032 | 788480 | 0.279070 | 1.279070 | stress_only |
| SET_2_3_4096 | include_zero | 4096 | 32 | 8 | 1081344 | 131072 | 1212416 | 0.121212 | 1.121212 | single_branch_preflight |
| SET_2_3_4096 | ternary | 4096 | 32 | 8 | 1081344 | 131072 | 1212416 | 0.121212 | 1.121212 | single_branch_preflight |
| SET_2_3_4096 | stress_both | 4096 | 32 | 8 | 1081344 | 262144 | 1343488 | 0.242424 | 1.242424 | stress_only |


## Finite Schedule Probe

| branch | r | seed | in_N | poly_N | h | r_prec | round_mismatches | final_mismatches | negative_controls_checked | copyback_count | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 0 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 1 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 2 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 3 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 4 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 5 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 6 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 7 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 8 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 1 | 9 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 0 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 1 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 2 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 3 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 4 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 5 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 6 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 7 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 8 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 2 | 9 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 0 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 1 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 2 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 3 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 4 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 5 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 6 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 7 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 8 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| include_zero | 4 | 9 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 0 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 1 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 2 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 3 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 4 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 5 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 6 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 7 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 8 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 1 | 9 | 16 | 64 | 5 | 3 | 0 | 0 | 40 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 0 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 1 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 2 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 3 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 4 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 5 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 6 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 7 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 8 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 2 | 9 | 16 | 64 | 5 | 3 | 0 | 0 | 80 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 0 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 1 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 2 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 3 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 4 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 5 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 6 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 7 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 8 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |
| ternary | 4 | 9 | 16 | 64 | 5 | 3 | 0 | 0 | 160 | 0 | PASS_SPARSEMUL_PREFLIGHT |


## Negative Controls

| branch | r | seed | negative_controls_checked | negative_control_naive_matches | negative_control_expected_failures | status |
| --- | --- | --- | --- | --- | --- | --- |
| include_zero | 1 | 0 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 1 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 2 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 3 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 4 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 5 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 6 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 7 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 8 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 1 | 9 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 0 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 1 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 2 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 3 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 4 | 80 | 2 | 78 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 5 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 6 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 7 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 8 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 2 | 9 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 0 | 160 | 0 | 160 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 1 | 160 | 1 | 159 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 2 | 160 | 0 | 160 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 3 | 160 | 2 | 158 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 4 | 160 | 2 | 158 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 5 | 160 | 0 | 160 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 6 | 160 | 0 | 160 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 7 | 160 | 0 | 160 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 8 | 160 | 0 | 160 | PASS_NEGATIVE_CONTROL |
| include_zero | 4 | 9 | 160 | 0 | 160 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 0 | 40 | 2 | 38 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 1 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 2 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 3 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 4 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 5 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 6 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 7 | 40 | 1 | 39 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 8 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| ternary | 1 | 9 | 40 | 0 | 40 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 0 | 80 | 4 | 76 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 1 | 80 | 1 | 79 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 2 | 80 | 1 | 79 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 3 | 80 | 3 | 77 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 4 | 80 | 1 | 79 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 5 | 80 | 3 | 77 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 6 | 80 | 1 | 79 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 7 | 80 | 3 | 77 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 8 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| ternary | 2 | 9 | 80 | 0 | 80 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 0 | 160 | 4 | 156 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 1 | 160 | 3 | 157 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 2 | 160 | 3 | 157 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 3 | 160 | 5 | 155 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 4 | 160 | 3 | 157 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 5 | 160 | 6 | 154 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 6 | 160 | 2 | 158 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 7 | 160 | 3 | 157 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 8 | 160 | 1 | 159 | PASS_NEGATIVE_CONTROL |
| ternary | 4 | 9 | 160 | 1 | 159 | PASS_NEGATIVE_CONTROL |


## Noise/Resource Recurrence

| item | model | target_value | status | failure_action |
| --- | --- | --- | --- | --- |
| selector_ep_noise | each non-binary sub_a consumes one additional MAT selector EP per accumulator index | h * in_N = 79872 for SET_2_3_2048 | needs_stage257_measurement | do not integrate full SAB |
| active_buffer_lifecycle | reuse existing active buffer state; normalize only at API boundary | no semantic copyback in finite preflight except final normalization | preflight_pass_required | disable active-buffer non-binary path |
| key_size_growth | one additional MAT selector family adds h selector objects | 39 extra selector objects at target h=39 | needs_stage257_resource_measurement | scope or reject non-binary branch |
| complete_sab_noise | not inferred from isolated or finite schedule probes | multi-seed final-output noise after full integration | blocked_until_stage258 | no speedup/noise claim |
| count_pressure_gate | single non-binary branch extra EP-class calls remain under 0.20 of binary main path | max_single_branch_extra=0.139535 | pass_preflight | do not implement sparse_mul |


## Admission

| route | decision | production_permission | reason | next_gate |
| --- | --- | --- | --- | --- |
| stage257_explicit_nonbinary_sparsemul_implementation | ADMIT_EXPLICIT_IMPLEMENTATION | explicit_new_path_only | finite schedule lifecycle, negative controls, count pressure, and Stage255 actual selector gate pass | implement explicit sab_pvw_nonbinary_* path without changing binary default |
| default_binary_sab | NO_CHANGE | no_default_change | binary path remains baseline and regression oracle | scalar/binary regression tests after any Stage257 code |
| nonbinary_full_sab_speedup | BLOCKED | no | no full sparse_mul implementation, full SAB correctness, multi-seed noise, or T_bootstrap/r benchmark yet | Stage257+Stage258 |


## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| sparsemul_preflight | supported_preflight | A non-binary sparse_mul integration boundary and finite schedule preflight are ready for explicit implementation. | Non-binary sparse_mul is implemented. | repro/stage256_nonbinary_sparsemul_preflight/finite_sparsemul_schedule_probe.csv |
| count_model | supported_model_only | Single non-binary branch adds h*in_N EP-class updates before measurement. | The count model proves speedup. | repro/stage256_nonbinary_sparsemul_preflight/schedule_count_projection.csv |
| full_sab_speedup | unsupported | No non-binary full-SAB speedup is claimed. | Non-binary PVW/MAT-SAB accelerates bootstrapping. | repro/stage256_nonbinary_sparsemul_preflight/implementation_admission.csv |


## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs_and_stage255 | PASS | inputs;stage255 | true;true | repro/stage256_nonbinary_sparsemul_preflight/input_status.csv; repro/stage255_mosfhet_nonbinary_selector_keygen_noise/proof_gate.csv | Stage256 is valid only after actual isolated selector gate passes. |
| G2_source_boundary | PASS | source boundaries | observed | repro/stage256_nonbinary_sparsemul_preflight/source_boundary_matrix.csv | Current binary source shape and required non-binary deltas are explicit. |
| G3_finite_schedule_probe | PASS | probe_rows;negative_rows | 60;60 | repro/stage256_nonbinary_sparsemul_preflight/finite_sparsemul_schedule_probe.csv; repro/stage256_nonbinary_sparsemul_preflight/negative_control_matrix.csv | Multi-round finite sparse_mul lifecycle preserves lane equivalence and negative controls. |
| G4_count_recurrence | PASS_PREFLIGHT | single branch extra EP ratio | below_0.20 | repro/stage256_nonbinary_sparsemul_preflight/schedule_count_projection.csv; repro/stage256_nonbinary_sparsemul_preflight/noise_resource_recurrence.csv | Count pressure and recurrence obligations are recorded before implementation. |
| G5_admission_boundary | PASS_EXPLICIT_PATH_ONLY | implementation permission | explicit_new_path_only | repro/stage256_nonbinary_sparsemul_preflight/implementation_admission.csv | Stage257 may implement an explicit non-binary path only; default binary remains unchanged. |
| G6_stage256_decision | PASS_STAGE256_NONBINARY_SPARSEMUL_PREFLIGHT_READY_EXPLICIT_IMPLEMENTATION | decision | PASS_STAGE256_NONBINARY_SPARSEMUL_PREFLIGHT_READY_EXPLICIT_IMPLEMENTATION | repro/stage256_nonbinary_sparsemul_preflight/proof_gate.csv | Proceed to explicit non-binary sparse_mul implementation gate, not full SAB. |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage257_explicit_nonbinary_sparsemul_implementation | Stage256 admits explicit implementation only. | add sidecar/new key object and sab_pvw_nonbinary_sparse_mul without changing binary default | selected_next | revert/disable explicit path; keep binary default | repro/stage256_nonbinary_sparsemul_preflight/implementation_admission.csv |
| P1 | stage258_nonbinary_sparsemul_correctness_noise | Stage257 explicit path compiles | actual MOSFHET sparse_mul equivalence, selector noise/resource, binary regression | conditional | do not enter full SAB | repro/stage256_nonbinary_sparsemul_preflight/noise_resource_recurrence.csv |
| P2 | stage259_nonbinary_full_sab_ab | Stage258 sparse_mul gates pass | complete-SAB T_bootstrap/r, multi-seed noise, resource, scalar/default isolation | future_gated | no non-binary bootstrapping speedup claim | repro/stage256_nonbinary_sparsemul_preflight/claim_boundary.csv |


Generated from head `0eecbc5`.
