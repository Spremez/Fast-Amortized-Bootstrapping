# Stage183 Addmul Dataflow Screen

Decision: `PASS_STAGE183_ADDMUL_DATAFLOW_SCREEN_NO_CODE_PERMISSION`.

Stage183 checks whether the remaining exact `addmul_from_dec_dft` component
contains a concrete untested dataflow mechanism. It does not. The project
already has MAT-aware AVX512 addmul helpers and r=6 tiled/fulltile/bodymajor
variants. Prior complete-SAB or exact-output gates reject the obvious dataflow
alternatives.

Therefore no new hot-path code is allowed from Stage183. Future work must
either:

- present an assembly/counter-backed addmul mechanism that is not one of the
  rejected layout variants; or
- move to the proof-gated compact/shared-output route; or
- refresh the final scoped claim package without claiming theoretical
  optimality.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage183_inputs | PASS | required_inputs_present | 1 | repro/stage182_exact_path_negative_frontier/summary.csv; src/mosfhet/src/mattrgsw.c | Stage183 consumes Stage182 frontier and current MAT addmul source. | Repair missing inputs before mechanism screening. |
| stage183_source_fact_check | PASS | mat_aware_avx512_variants_present | 1 | repro/stage183_addmul_dataflow_screen/source_facts.csv | Current source already contains tiled, fulltile, and bodymajor MAT-aware AVX512 variants. | Do not describe the project as lacking MAT AVX512 addmul. |
| stage183_projection_check | PASS | required_addmul_speedup_for_3pct_full_sab | 1.151228774 | repro/stage183_addmul_dataflow_screen/projection.csv | The addmul component is large enough only if a real dataflow gain exists. | Reject layout-only retuning without a new proof or counter preflight. |
| stage183_decision | PASS_STAGE183_ADDMUL_DATAFLOW_SCREEN_NO_CODE_PERMISSION | code_permission | denied | repro/stage183_addmul_dataflow_screen/mechanism_screen.csv | No untested exact addmul dataflow mechanism currently meets the code-entry rule. | Route to final exact-frontier closeout or proof-gated compact work. |

## Source Facts

| fact | status | line | evidence | implication |
| --- | --- | --- | --- | --- |
| complex_addmul_uses_avx512_fma | yes | 146 | src/mosfhet/src/mattrgsw.c | The addmul hot loop is already vectorized with AVX512 FMA helpers. |
| rgt4_tiled_kernel_exists | yes | 458 | src/mosfhet/src/mattrgsw.c | Current r=6/r=8 path already reuses each decomposed row across output tiles. |
| r6_fulltile_kernel_exists | yes | 520 | src/mosfhet/src/mattrgsw.c | Register-resident all-output accumulation was implemented as an explicit variant. |
| r6_bodymajor_kernel_exists | yes | 606 | src/mosfhet/src/mattrgsw.c | Output-major dataflow was implemented as an explicit variant. |
| rgt4_dispatch_is_flagged | yes |  | src/mosfhet/Makefile.def | All r>4 MAT variants remain explicit and default-controllable. |

## Projection

| metric | value | unit | interpretation |
| --- | --- | --- | --- |
| r | 6 | lanes | Stage183 screens the current exact r=6 path. |
| dense_complex_products_per_coeff | 49 | complex_vector_products | Closed full-MAT shape has (r+1)^2 products per coefficient block. |
| stage180_addmul_per_call_us | 22.923460937 | us | Measured isolated addmul-from-decomposed-DFT time. |
| addmul_full_sab_share | 0.221723249 | share | Estimated full-SAB share from Stage180 projection. |
| required_addmul_speedup_for_3pct_full_sab | 1.151228774 | x | Minimum local speedup needed before a code branch is worthwhile. |

## Mechanism Screen

| mechanism | decision | evidence | reason | code_permission |
| --- | --- | --- | --- | --- |
| D1_current_tile4_reuse | CURRENT_BASELINE | src/mosfhet/src/mattrgsw.c | The tiled r>4 kernel already loads one decomposed row and updates output tiles for each coefficient. | no_new_code |
| D2_fulltile_register_resident_outputs | REJECT_PRIOR_GATE | repro/stage111_r6_fulltile_repeated_gate/summary.csv | A full-output r=6 path exists; repeated complete-SAB evidence did not promote it. | do_not_reopen_without_new_mechanism |
| D3_bodymajor_output_major | REJECT_PRIOR_GATE | repro/stage154_bodymajor_fullsab_closeout/summary.csv | Complete-SAB `T_bootstrap/r` bodymajor/tile4 result was 0.977892. | do_not_reopen_without_new_mechanism |
| D4_row_streaming_decompose_dft_addmul | REJECT_PRIOR_GATE | repro/stage165_closed_fullmat_streaming_microbench/summary.csv | Streaming reduced scratch lifetime but lost to current all-row tiled AVX in exact-output microbench. | do_not_reopen_without_changed_locality_model |
| D5_more_coefficient_unrolling | DENY_NO_EVIDENCE | repro/stage183_addmul_dataflow_screen/source_facts.csv | Unrolling coefficients duplicates many accumulator registers on top of dec/selector registers; no measured mechanism suggests it beats current tile/fulltile tradeoff. | requires_assembly_counter_preflight_first |
| D6_selector_transposed_key_layout | BLOCK_KEY_FORMAT_CHANGE | repro/stage112_selector_format_gate/summary.csv | Better selector locality likely requires key/selector layout changes, not a loop-only exact-path change. | requires_keygen_resource_noise_gate |
| D7_sparse_selector_skip | BLOCK_SECURITY_FORMAT | repro/stage176_structured_compact_security_api_gate/summary.csv | Encrypted selector rows cannot be skipped as plaintext zeros under the current key format. | proof_branch_only |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 184 | exact-route closeout and paper claim refresh | Stage183 denies new exact addmul code permission. | Update final claim ledger: scoped complete-SAB speedup allowed, theoretical optimality denied. | Do not invent another exact AVX512 variant without new measured mechanism. |
| P1 | 185 | structured compact proof unlock | A proof/literature package for compact shared-mask closure is supplied. | Selector distribution, closed state, noise, resource, and novelty gates must pass before SAB code. | If proof is incomplete, keep compact out of hot path. |
