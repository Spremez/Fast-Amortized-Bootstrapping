# Stage254 Non-Binary Keygen/Noise Preflight

Decision: `PASS_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT_READY_MOSFHET_ISOLATED_PROTOTYPE`.

Stage254 records the keygen/noise/resource obligations that must be satisfied
before non-binary PVW/MAT-SAB can move beyond the finite Stage253 model.

## Source Capability

| capability | source | observed | status | interpretation |
| --- | --- | --- | --- | --- |
| mat_monomial_encrypt_zero_one | src/mosfhet/src/mattrgsw.c; src/mosfhet/include/mosfhet.h | yes | PRESENT | The primitive needed for 0/1 MAT selector encryption exists. |
| mat_to_dft_conversion | src/mosfhet/src/mattrgsw.c; src/mosfhet/include/mosfhet.h | yes | PRESENT | The primitive needed to store selector rows in DFT form exists. |
| current_binary_encrypt_bits_pattern | src/sab_pvw.c | yes | PRESENT | Current binary keygen already loops over MAT monomial bit encryption. |
| production_nonbinary_keygen | src/sab_pvw.c | no | MISSING_BLOCKED | Production non-binary keygen remains absent by design. |


## Selector Keygen Design

| selector_family | plaintext | monomial_exponent | count_per_key | existing_pattern | needed_for_stage255 |
| --- | --- | --- | --- | --- | --- |
| distance_bits | bit_j(r_diff) | 0 | (h + 1) * r_prec | sab_pvw_encrypt_bits | reuse current binary pattern as reference |
| s_coff | c in {0,1} | 0 | h when include_zero | same MAT monomial encryption primitive, new family | allocate/encrypt DFT selector family and verify include-zero sub_a |
| s_sign | s in {0,1} | 0 | h when ternary | same MAT monomial encryption primitive, new family | allocate/encrypt DFT selector family and verify ternary sub_a |


## Cost Projection

| param | branch | in_N | h | r_prec | binary_main_ep_calls | extra_suba_ep_calls | extra_ep_over_binary_main | binary_selector_objects | extra_selector_objects | selector_count_ratio | admission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_2048 | include_zero | 2048 | 39 | 7 | 573440 | 79872 | 0.139286 | 280 | 39 | 1.139286 | single_family_admitted_to_isolated_prototype |
| SET_2_3_2048 | ternary | 2048 | 39 | 7 | 573440 | 79872 | 0.139286 | 280 | 39 | 1.139286 | single_family_admitted_to_isolated_prototype |
| SET_2_3_2048 | include_zero_plus_ternary_stress | 2048 | 39 | 7 | 573440 | 159744 | 0.278571 | 280 | 78 | 1.278571 | stress_only_not_claimed |
| SET_4_5_2048 | include_zero | 2048 | 42 | 7 | 616448 | 86016 | 0.139535 | 301 | 42 | 1.139535 | single_family_admitted_to_isolated_prototype |
| SET_4_5_2048 | ternary | 2048 | 42 | 7 | 616448 | 86016 | 0.139535 | 301 | 42 | 1.139535 | single_family_admitted_to_isolated_prototype |
| SET_4_5_2048 | include_zero_plus_ternary_stress | 2048 | 42 | 7 | 616448 | 172032 | 0.279070 | 301 | 84 | 1.279070 | stress_only_not_claimed |
| SET_2_3_4096 | include_zero | 4096 | 32 | 8 | 1081344 | 131072 | 0.121212 | 264 | 32 | 1.121212 | single_family_admitted_to_isolated_prototype |
| SET_2_3_4096 | ternary | 4096 | 32 | 8 | 1081344 | 131072 | 0.121212 | 264 | 32 | 1.121212 | single_family_admitted_to_isolated_prototype |
| SET_2_3_4096 | include_zero_plus_ternary_stress | 4096 | 32 | 8 | 1081344 | 262144 | 0.242424 | 264 | 64 | 1.242424 | stress_only_not_claimed |


## Noise Obligations

| obligation | status | required_evidence | failure_action |
| --- | --- | --- | --- |
| selector_encryption_noise | pending_stage255 | encrypt MAT s_coff/s_sign selectors and record initial noise distribution | do not integrate non-binary sparse_mul |
| suba_external_product_noise | pending_stage255 | isolated sub_a with encrypted selector DFT and scalar/PVW noise comparison | keep Stage253 finite-only |
| full_sparse_schedule_noise | blocked_until_isolated_passes | multi-step sparse_mul noise recurrence and multi-seed final-output noise | no complete-SAB claim |
| parameter_resource_tradeoff | pending | key size, keygen time, scratch/RSS for non-binary selector families | scope or reject non-binary branch |


## Resource Obligations

| param | branch | selector_count_ratio | extra_ep_over_binary_main | status | interpretation |
| --- | --- | --- | --- | --- | --- |
| SET_2_3_2048 | include_zero | 1.139286 | 0.139286 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |
| SET_2_3_2048 | ternary | 1.139286 | 0.139286 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |
| SET_2_3_2048 | include_zero_plus_ternary_stress | 1.278571 | 0.278571 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |
| SET_4_5_2048 | include_zero | 1.139535 | 0.139535 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |
| SET_4_5_2048 | ternary | 1.139535 | 0.139535 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |
| SET_4_5_2048 | include_zero_plus_ternary_stress | 1.279070 | 0.279070 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |
| SET_2_3_4096 | include_zero | 1.121212 | 0.121212 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |
| SET_2_3_4096 | ternary | 1.121212 | 0.121212 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |
| SET_2_3_4096 | include_zero_plus_ternary_stress | 1.242424 | 0.242424 | preflight_only | Counts show cost pressure; actual bytes/time/noise require Stage255+ measurement. |


## Admission

| route | decision | production_permission | reason | next_gate |
| --- | --- | --- | --- | --- |
| stage255_mosfhet_isolated_selector_keygen | ADMIT_ISOLATED_PROTOTYPE | no | single-family extra EP ratio max=0.139535; source primitives present=true | actual MAT selector encryption, isolated sub_a equivalence, noise/resource |
| nonbinary_full_sab | BLOCKED | no | no encrypted selector keygen, noise recurrence, sparse_mul integration, or full SAB A/B yet | Stage255 and later |
| include_zero_plus_ternary_stress | STRESS_ONLY_NOT_CLAIMED | no | scalar code prioritizes include_zero branch before ternary; both-family row is only layout pressure | separate branch semantics if ever claimed |


## Claim Boundary

| claim | status | allowed_wording | forbidden_wording | evidence |
| --- | --- | --- | --- | --- |
| keygen_preflight | supported_preflight | MAT primitives needed for 0/1 selector encryption exist and counts are projected. | Non-binary MAT selector keygen is implemented. | repro/stage254_nonbinary_keygen_noise_preflight/selector_keygen_design.csv |
| nonbinary_cost | count_model_only | Single-family non-binary sub_a adds h*in_N MAT external-product-class updates in the model. | This model proves non-binary speedup or slowdown. | repro/stage254_nonbinary_keygen_noise_preflight/cost_projection.csv |
| noise_security | unsupported_pending | Noise/security remains a required Stage255+ gate. | Non-binary PVW noise is acceptable. | repro/stage254_nonbinary_keygen_noise_preflight/noise_obligation_matrix.csv |


## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs_and_stage253 | PASS | inputs;stage253 | true;true | repro/stage254_nonbinary_keygen_noise_preflight/input_status.csv; repro/stage253_isolated_nonbinary_suba_equivalence/proof_gate.csv | Stage254 is valid only after isolated non-binary equivalence passes. |
| G2_source_capability | PASS | source primitives | present_or_blocked_as_expected | repro/stage254_nonbinary_keygen_noise_preflight/source_capability_matrix.csv | MAT monomial encryption/DFT primitives exist; production non-binary keygen remains absent. |
| G3_cost_pressure | PASS_PREFLIGHT | single-family extra EP ratio | below_0.20 | repro/stage254_nonbinary_keygen_noise_preflight/cost_projection.csv | Single-family non-binary branches are not ruled out by first-order count pressure. |
| G4_noise_obligations | PASS_OBLIGATIONS_RECORDED | noise obligations | pending | repro/stage254_nonbinary_keygen_noise_preflight/noise_obligation_matrix.csv | Noise is not proven; obligations are explicit before any production claim. |
| G5_admission_boundary | PASS_NO_PRODUCTION | production permission | no | repro/stage254_nonbinary_keygen_noise_preflight/implementation_admission.csv | Only MOSFHET-adjacent isolated prototype is admitted. |
| G6_stage254_decision | PASS_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT_READY_MOSFHET_ISOLATED_PROTOTYPE | decision | PASS_STAGE254_NONBINARY_KEYGEN_NOISE_PREFLIGHT_READY_MOSFHET_ISOLATED_PROTOTYPE | repro/stage254_nonbinary_keygen_noise_preflight/proof_gate.csv | Proceed to actual isolated selector keygen/noise prototype, not full SAB. |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage255_mosfhet_isolated_selector_keygen_noise | Stage254 preflight admits isolated prototype only. | actual MAT s_coff/s_sign encryption, isolated sub_a equivalence, noise/resource | selected_next | keep non-binary PVW unsupported | repro/stage254_nonbinary_keygen_noise_preflight/implementation_admission.csv |
| P1 | stage256_nonbinary_sparse_mul_integration | Stage255 passes actual selector keygen/noise/resource | integrate selector families into sparse_mul outside default path | conditional | no production integration | repro/stage254_nonbinary_keygen_noise_preflight/noise_obligation_matrix.csv |
| P2 | stage257_nonbinary_full_sab_ab | Stage256 integration passes correctness and noise | complete-SAB T_bootstrap/r, multi-seed noise/resource, scalar default isolation | future_gated | no non-binary speedup claim | repro/stage254_nonbinary_keygen_noise_preflight/claim_boundary.csv |


Generated from head `26bc1c4`.
