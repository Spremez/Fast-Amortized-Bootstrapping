# Stage231 Current-Head Added-Parameter Refresh

Decision: `PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING`.

Stage231 executes a current-head smoke refresh for the added binary parameters
that Stage36 previously covered with higher statistics. The endpoint remains
complete-SAB `T_bootstrap/r`. This stage proves current-head continuity and
parameter-shape selection only; it does not promote added parameters into a
paper-level current-head table because resource and full-stat gates are still
pending.

## Shape Gate

| param | r | observed_h | expected_h | observed_r_prec | expected_r_prec | correctness_status | shape_gate | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 2 | 32 | 32 | 8 | 8 | Pass | PASS | repro/stage231_current_head_added_param_smoke/perf_SET_2_3_4096_r2_runs1/run_0.log |
| SET_2_3_4096 | 4 | 32 | 32 | 8 | 8 | Pass | PASS | repro/stage231_current_head_added_param_smoke/perf_SET_2_3_4096_r4_runs1/run_0.log |
| SET_4_5_2048 | 2 | 42 | 42 | 7 | 7 | Pass | PASS | repro/stage231_current_head_added_param_smoke/perf_SET_4_5_2048_r2_runs1/run_0.log |
| SET_4_5_2048 | 4 | 42 | 42 | 7 | 7 | Pass | PASS | repro/stage231_current_head_added_param_smoke/perf_SET_4_5_2048_r4_runs1/run_0.log |

## Performance Smoke

| param | r | runs | status | metric | pvw_mean_us | scalar_repeated_mean_us | mean_speedup | min_speedup | max_speedup | decision | claim_level | source_csv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 2 | 1 | PASS | T_bootstrap/r | 29319069.000 | 36674366.000 | 1.251 | 1.251 | 1.251 | PASS_SMOKE | current-head smoke only; no CI or promotion | repro/stage231_current_head_added_param_smoke/perf_SET_2_3_4096_r2_runs1/summary.csv |
| SET_2_3_4096 | 4 | 1 | PASS | T_bootstrap/r | 54472629.000 | 72557447.000 | 1.332 | 1.332 | 1.332 | PASS_SMOKE | current-head smoke only; no CI or promotion | repro/stage231_current_head_added_param_smoke/perf_SET_2_3_4096_r4_runs1/summary.csv |
| SET_4_5_2048 | 2 | 1 | PASS | T_bootstrap/r | 16180790.000 | 21592995.000 | 1.334 | 1.334 | 1.334 | PASS_SMOKE | current-head smoke only; no CI or promotion | repro/stage231_current_head_added_param_smoke/perf_SET_4_5_2048_r2_runs1/summary.csv |
| SET_4_5_2048 | 4 | 1 | PASS | T_bootstrap/r | 32633770.000 | 42726514.000 | 1.309 | 1.309 | 1.309 | PASS_SMOKE | current-head smoke only; no CI or promotion | repro/stage231_current_head_added_param_smoke/perf_SET_4_5_2048_r4_runs1/summary.csv |

## Noise Smoke

| param | r | seeds | points | pvw_failures | scalar_failures | pair_failures | avg_pvw_minus_scalar_log2 | status | claim_level | source_csv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_4096 | 2 | 1 | 8192 | 0 | 0 | 0 | -0.015000 | PASS | current-head noise smoke only | repro/stage231_current_head_added_param_smoke/noise_SET_2_3_4096_r2_seeds1/aggregate.csv |
| SET_2_3_4096 | 4 | 1 | 16384 | 0 | 0 | 0 | 0.289000 | PASS | current-head noise smoke only | repro/stage231_current_head_added_param_smoke/noise_SET_2_3_4096_r4_seeds1/aggregate.csv |
| SET_4_5_2048 | 2 | 1 | 4096 | 0 | 0 | 0 | -0.176000 | PASS | current-head noise smoke only | repro/stage231_current_head_added_param_smoke/noise_SET_4_5_2048_r2_seeds1/aggregate.csv |
| SET_4_5_2048 | 4 | 1 | 8192 | 0 | 0 | 0 | 0.049000 | PASS | current-head noise smoke only | repro/stage231_current_head_added_param_smoke/noise_SET_4_5_2048_r4_seeds1/aggregate.csv |

## Promotion Gates

| gate | required | observed | status | claim_effect |
| --- | --- | --- | --- | --- |
| shape_gate | observed h/r_prec equals selected PARAM definition for all param/r cases | see shape_gate.csv | PASS | Allows current-head smoke interpretation only. |
| performance_smoke | one complete-SAB A/B run per param/r with correctness Pass and speedup > 1 | 4/4 | PASS | Does not provide CI; cannot replace 10-run Stage36 evidence. |
| noise_smoke | one deterministic seed per param/r with zero PVW/scalar/pair failures | 4/4 | PASS | Noise sanity only; cannot replace 20-seed Stage36 evidence. |
| resource_refresh | current-head resource/keygen/RSS for added parameters | not run in Stage231 smoke | PENDING | Blocks current-head paper-table promotion. |
| full_statistics | at least 10 complete-SAB A/B runs and 20 noise seeds if added parameters enter a paper table | 1 run and 1 seed | PENDING | Blocks statistical claim; current result is smoke only. |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | inputs_present | true | repro/stage231_current_head_added_param_smoke/input_status.csv | Stage231 consumes Stage230 policy and raw current-head smoke logs. |
| G2_shape_gate | PASS | shape_rows | 4/4 | repro/stage231_current_head_added_param_smoke/shape_gate.csv | PARAM selection changed the actual SAB target shape; this is not default SET_2_3_2048 fallback. |
| G3_performance_smoke | PASS | positive_smoke_rows | 4/4 | repro/stage231_current_head_added_param_smoke/performance_smoke.csv | Every added param/r case has one passing complete-SAB T_bootstrap/r smoke run. |
| G4_noise_smoke | PASS | zero_failure_rows | 4/4 | repro/stage231_current_head_added_param_smoke/noise_smoke.csv | Every added param/r case has one deterministic zero-failure final-output noise smoke. |
| G5_promotion_boundary | PASS_SMOKE_ONLY_RESOURCE_AND_FULL_STATS_PENDING | pending_promotion_gates | 2 | repro/stage231_current_head_added_param_smoke/promotion_gate.csv | The current-head smoke refresh cannot be used as a paper-level added-parameter table. |
| G6_stage231_decision | PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING | decision | PASS_STAGE231_CURRENT_HEAD_ADDED_PARAM_SMOKE_FULL_STATS_RESOURCE_PENDING | repro/stage231_current_head_added_param_smoke/proof_gate.csv | Proceed to full-stat/resource refresh if added parameters are needed in the main claim. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage232_current_head_added_param_full_stats_resource | Added binary parameters must appear in a paper/main table. | 10-run complete-SAB A/B, 20-seed noise, and resource/keygen/RSS for selected param/r cases. | selected_if_added_param_table_needed | Keep Stage231 as current-head smoke and Stage36 as historical high-stat support. | repro/stage231_current_head_added_param_smoke/promotion_gate.csv |
| P1 | stage233_scoped_manuscript_skeleton | User wants a report draft before broader parameter promotion. | Use Stage231 only as smoke continuity; use Stage229/230 claim policy for wording. | future | Remove added-parameter current-head table claims. | repro/stage231_current_head_added_param_smoke/proof_gate.csv |
| P2 | stage234_nonbinary_or_compact_design | Algorithm scope expands beyond exact dense binary PVW/MAT-SAB. | Selector/key equations, security/noise model, isolated equivalence, then full SAB A/B. | blocked_until_design | Do not claim non-binary, compact, or optimal MAT-RLWE SAB. | repro/stage231_current_head_added_param_smoke/promotion_gate.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage230_source_verified_literature_novelty_audit/proof_gate.csv | present | Stage230 proof gate | 1187 |
| repro/stage230_source_verified_literature_novelty_audit/next_stage_queue.csv | present | Stage230 next queue | 1150 |
| repro/stage230_source_verified_literature_novelty_audit/claim_policy.csv | present | Stage230 claim policy | 824 |
| repro/stage231_current_head_added_param_smoke/performance_summary.csv | present | Stage231 raw performance smoke summary | 766 |
| repro/stage231_current_head_added_param_smoke/noise_summary.csv | present | Stage231 raw noise smoke summary | 744 |
| stage230_next_contains_stage231 | present | Stage230 routes current-head added-parameter refresh when a broader table is needed. |  |
