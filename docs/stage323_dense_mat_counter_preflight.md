# Stage323 Dense MAT Counter Preflight

Decision: `PASS_STAGE323_DENSE_MAT_PREFLIGHT_DENY_LOOP_CODE_ROUTE_SELECTOR_FORMAT_REQUIRED`.

Stage323 tests whether Stage322's dense MAT residual admits another local
exact-loop optimization. It does not. The current r=4 dense MAT path already
uses AVX512 FMA, loads each decomposed row once per coefficient block, reuses
it across all five outputs, and stores each output once. The explicit
r4-unrolled pointer-hoist variant was neutral in complete SAB at Stage321.

## Summary

| decision | stage322_dense_share | required_dense_reduction_for_1pct_fullsab | perf_counter_available | next_stage |
| --- | --- | --- | --- | --- |
| PASS_STAGE323_DENSE_MAT_PREFLIGHT_DENY_LOOP_CODE_ROUTE_SELECTOR_FORMAT_REQUIRED | 0.212353 | 0.046625 | no | stage324_selector_layout_or_structured_mechanism_preflight |

## Static Model

| model | rows | outputs | complex_products_per_block | dec_zmm_loads_per_block | selector_zmm_loads_per_block | output_zmm_stores_per_block | zmm_fma_per_block | estimated_mem_bytes_per_call | dec_reuse_status | store_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| r4_k1_l1_dense_current | 5 | 5 | 25 | 10 | 50 | 10 | 90 | 573440 | optimal_for_dense_r4_loop | one_store_per_output_component |

## Mechanism Screen

| candidate | status | new_mechanism | code_permission |
| --- | --- | --- | --- |
| r4_pointer_hoist_unrolled_rows | CLOSED_STAGE321_NEUTRAL | no | DENY_PRIOR_FULLSAB_NEUTRAL |
| dec_row_cache_across_outputs | DENY_NO_DUPLICATE_DEC_LOADS | no | DENY_NO_LOAD_REDUCTION |
| more_output_register_tiling | DENY_ALREADY_REGISTER_RESIDENT_R4 | no | DENY_NO_STORE_REDUCTION |
| prefetch_only_selector_rows | DENY_COUNTER_UNAVAILABLE_AND_NO_COUNT_REDUCTION | weak | DENY_UNTIL_COUNTER_BACKED |
| selector_transposed_key_layout | ROUTE_STAGE324_KEY_FORMAT_PREFLIGHT | yes | NO_HOT_PATH_CODE_BEFORE_KEYGEN_RESOURCE_NOISE_GATE |
| structured_or_compact_selector | ROUTE_STAGE324_PROOF_BRANCH_ONLY | yes | NO_HOT_PATH_CODE_BEFORE_PROOF_AND_RESOURCE_GATE |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage322_input | PASS | Stage322 decision | dense selected | Stage323 opens only because dense MAT was the selected unclosed residual. |
| G2_perf_counter_probe | PROXY_ONLY | perf availability | no | No hardware-counter claim is made when perf is unavailable. |
| G3_static_load_model | PASS | r4 dec/output reuse | dec_once;store_once | Current r=4 dense loop already reuses each dec row across all outputs and stores each output once. |
| G4_existing_route_closure | PASS | r4_unrolled | Stage321 neutral | The only local r=4 loop variant already failed complete-SAB A/B. |
| G5_code_permission | PASS_STAGE323_DENSE_MAT_PREFLIGHT_DENY_LOOP_CODE_ROUTE_SELECTOR_FORMAT_REQUIRED | exact dense loop code | denied | Further gains require selector/key-format or structured mechanism gates, not another local loop rewrite. |

Generated from input head `0b4cb2a`.
