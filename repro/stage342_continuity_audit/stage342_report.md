# Stage342 Continuity Audit

Decision: `PASS_STAGE342_CONTINUITY_AUDIT_SCOPED_BRIDGE_NO_FULL_MATRIX_CLAIM`.

Stage342 separates historical high-stat evidence from current-head evidence.
It does not run new benchmarks and it does not promote a broader parameter
claim.

## Summary

| decision | current_head | primary_current_head_r4_speedup | r2_current_head_status | r2_smoke_speedup | stage36_hotpath_to_head | full_matrix_status |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE342_CONTINUITY_AUDIT_SCOPED_BRIDGE_NO_FULL_MATRIX_CLAIM | 706ae7c | 1.747647 | smoke_only | 1.695000 | HOTPATH_CHANGED_OR_UNRESOLVED | missing_current_head_highstat_cases |

## Evidence Ladder

| layer | status | metric | value | continuity | claim_use |
| --- | --- | --- | --- | --- | --- |
| current_head_primary_r4 | SUPPORTED_SCOPED | complete_sab_T_bootstrap_over_r | speedup=1.747647; samples=10; noise=0/10 | HOTPATH_EQUIVALENT | main current-head scoped r=4 claim |
| current_head_r2_smoke | SMOKE_ONLY | complete_sab_T_bootstrap_over_r | speedup=1.695000; samples=1; noise=0/1 | HOTPATH_EQUIVALENT | execution-chain evidence only; not statistical performance |
| stage50_stage36_target_perf_r2 | PASS | high_stat_target_performance | r=2; speedup=1.191; runs=10 | REFERENCE_HIGH_STAT | may_support_scoped_engineering_target_performance; not novelty/theory/all-parameter |
| stage50_stage47_current_head_smoke_r2 | PASS | single_run_current_head_smoke | r=2; speedup=1.212; runs=1 | CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95 | current-head smoke only; superseded by Stage49 for continuity |
| stage50_stage49_current_head_repeated_r2 | PASS | repeated_current_head_stability | r=2; speedup=1.265; runs=3 | CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95 | may support post-refactor continuity; Stage36 remains performance claim source |
| stage50_stage36_target_perf_r4 | PASS | high_stat_target_performance | r=4; speedup=1.377; runs=10 | REFERENCE_HIGH_STAT | may_support_scoped_engineering_target_performance; not novelty/theory/all-parameter |
| stage50_stage47_current_head_smoke_r4 | PASS | single_run_current_head_smoke | r=4; speedup=1.353; runs=1 | CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95 | current-head smoke only; superseded by Stage49 for continuity |
| stage50_stage49_current_head_repeated_r4 | PASS | repeated_current_head_stability | r=4; speedup=1.376; runs=3 | CURRENT_HEAD_MEAN_WITHIN_STAGE36_CI95 | may support post-refactor continuity; Stage36 remains performance claim source |
| historical_added_SET_4_5_2048_r2 | PASS_ADDED_PARAM_10RUN | historical_added_binary_highstat | speedup=1.285700; runs=10; ci=1.255799..1.315601 | HOTPATH_CHANGED_OR_UNRESOLVED | supporting historical added-binary evidence; rerun for current-head broader claim |
| historical_added_SET_4_5_2048_r4 | PASS_ADDED_PARAM_10RUN | historical_added_binary_highstat | speedup=1.350700; runs=10; ci=1.329122..1.372278 | HOTPATH_CHANGED_OR_UNRESOLVED | supporting historical added-binary evidence; rerun for current-head broader claim |
| historical_added_SET_2_3_4096_r2 | PASS_ADDED_PARAM_10RUN | historical_added_binary_highstat | speedup=1.235100; runs=10; ci=1.210553..1.259647 | HOTPATH_CHANGED_OR_UNRESOLVED | supporting historical added-binary evidence; rerun for current-head broader claim |
| historical_added_SET_2_3_4096_r4 | PASS_ADDED_PARAM_10RUN | historical_added_binary_highstat | speedup=1.346200; runs=10; ci=1.285926..1.406474 | HOTPATH_CHANGED_OR_UNRESOLVED | supporting historical added-binary evidence; rerun for current-head broader claim |

## Matrix Status

| case | status | samples | speedup | noise | next_needed |
| --- | --- | --- | --- | --- | --- |
| SET_2_3_2048_r4 | CURRENT_HEAD_HIGHSTAT_AVAILABLE | 10 | 1.747647 | 0/10 | none for scoped primary r=4; rerun only after hotpath changes |
| SET_2_3_2048_r2 | CURRENT_HEAD_SMOKE_ONLY | 1 | 1.695000 | 0/1 | run 10-sample current-head target r=2 if target r=2 wording is desired |
| SET_4_5_2048_r2 | HISTORICAL_HIGHSTAT_ONLY | 10 | 1.285700 | 0/20 | rerun current-head case before broader current-head parameter claim |
| SET_4_5_2048_r4 | HISTORICAL_HIGHSTAT_ONLY | 10 | 1.350700 | 0/20 | rerun current-head case before broader current-head parameter claim |
| SET_2_3_4096_r2 | HISTORICAL_HIGHSTAT_ONLY | 10 | 1.235100 | 0/20 | rerun current-head case before broader current-head parameter claim |
| SET_2_3_4096_r4 | HISTORICAL_HIGHSTAT_ONLY | 10 | 1.346200 | 0/20 | rerun current-head case before broader current-head parameter claim |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_inputs | PASS | required artifacts | Stage36;Stage49;Stage50;Stage331;Stage341 |
| G2_stage36_hotpath_delta | PASS_SCOPED | Stage36 -> HEAD hotpath diff | changed |
| G3_current_head_anchor | PASS | Stage331 r4 and Stage341 r2 | r4_highstat;r2_smoke |
| G4_full_matrix | MISSING_CURRENT_HEAD_CASES | cases not current-head high-stat | 5 |
| G5_decision | PASS_STAGE342_CONTINUITY_AUDIT_SCOPED_BRIDGE_NO_FULL_MATRIX_CLAIM | stage decision | PASS_STAGE342_CONTINUITY_AUDIT_SCOPED_BRIDGE_NO_FULL_MATRIX_CLAIM |
