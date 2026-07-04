# Stage325 Selector-Transpose Resource Probe

Decision: `NEUTRAL_STAGE325_SELECTOR_TRANSPOSE_MICRO_NO_PROMOTION`.

Stage325 tests the only exact dense route still admitted by Stage324: a
coefficient-blocked selector-transposed layout. The experiment keeps the same
AVX512 complex FMA arithmetic and compares against the current row/poly
selector layout in an isolated r=4, N=2048 dense addmul microbench.

## Summary

| decision | selected_next_stage | runs | correctness | isolated_dense_speedup_mean | required_dense_speedup_for_1pct_fullsab | projected_fullsab_speedup_mean | duplicate_storage_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NEUTRAL_STAGE325_SELECTOR_TRANSPOSE_MICRO_NO_PROMOTION | stage326_exact_dense_route_closeout | 15 | PASS | 1.028925 | 1.048905 | 1.006006 | 2.000000 |

## Resource Projection

| layout | storage_ratio_vs_current | build_avg_ns | build_over_candidate_kernel | interpretation |
| --- | --- | --- | --- | --- |
| current_rowpoly_selector | 1.000000 | 0 | 0 | current production-like row/poly layout |
| replace_with_coeffblocked_transpose | 1.000000 | 16384.618 | 2.560215 | possible future key format; no duplicate selector storage after keygen rewrite |
| duplicate_transposed_view_probe | 2.000000 | 16384.618 | 2.560215 | safe isolated probe shape; unacceptable as hidden production memory unless justified |

## Proof Gates

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage324_input | PASS | Stage324 decision | PASS_STAGE324_SELECT_SELECTOR_TRANSPOSE_RESOURCE_PREFLIGHT_COMPACT_REMAINS_FROZEN | Stage325 is valid only as a bounded selector-transpose probe. |
| G2_microbench_parse | PASS | parsed runs | 15 | All timing conclusions require parsed raw logs. |
| G3_correctness | PASS | max_abs_diff | 0.000000 | Packed selector layout must be bit-exact for the same dense arithmetic order. |
| G4_dense_speed_threshold | FAIL | mean dense speedup | 1.028925 required 1.048905 | Below this threshold, isolated selector locality cannot project 1% full-SAB gain. |
| G5_fullsab_projection | FAIL | projected full-SAB speedup | 1.006006 | Projection uses Stage322/323 dense share and is not a complete-SAB timing claim. |
| G6_resource_visibility | PASS_REPORTED | duplicate storage ratio | 2.000000 | Duplicate transposed view cost is reported separately from replace-format key layout. |
| G7_stage325_decision | NEUTRAL_STAGE325_SELECTOR_TRANSPOSE_MICRO_NO_PROMOTION | selected next | stage326_exact_dense_route_closeout | Only a positive result opens key-view prototype; otherwise close exact dense selector-layout work. |

Generated from input head `e620cf7`.
