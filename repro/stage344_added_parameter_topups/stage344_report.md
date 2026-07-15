# Stage344 Added-Parameter Current-Head Top-Ups

Decision: `PASS_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX`.

Stage344 executes the added binary parameter rows that were still historical
after Stage343. The endpoint remains complete SAB `T_bootstrap/r` against
repeated scalar SAB under the same backend.

## Summary

| decision | intended_cases | passed_cases | speedup_min | speedup_max | speedup_mean_across_cases | max_rss_kb | claim_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX | 4 | 4 | 1.612100 | 1.738200 | 1.675150 | 4618504 | binary_added_parameter_current_head_matrix |

## Per-Case Results

| case | samples | correctness | pvw_t_over_r_mean_us | scalar_t_over_r_mean_us | speedup_mean | speedup_ci95 | noise_trials | noise_pair_failures | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_4_5_2048_r2 | 10 | Pass | 7117983.900 | 12165024.000 | 1.709700 | 1.673443..1.745957 | 10 | 0 | PASS_CASE |
| SET_4_5_2048_r4 | 10 | Pass | 8121233.000 | 14132476.475 | 1.738200 | 1.712133..1.764267 | 10 | 0 | PASS_CASE |
| SET_2_3_4096_r2 | 10 | Pass | 13561017.550 | 21864209.800 | 1.612100 | 1.601707..1.622493 | 10 | 0 | PASS_CASE |
| SET_2_3_4096_r4 | 10 | Pass | 11753773.550 | 19235637.400 | 1.640600 | 1.578981..1.702219 | 10 | 0 | PASS_CASE |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_stage343_input | PASS | Stage343 summary | PASS_STAGE343_TARGET_R2_CURRENT_HEAD_HIGHSTAT_TOPUP |
| G2_hotpath_equivalence | PASS | Stage344 run head to HEAD | stage344_run_head_to_current_head=HOTPATH_EQUIVALENT |
| G3_added_parameter_coverage | PASS | passed/intended rows | 4/4 |
| G4_metric_alignment | PASS | primary endpoint | complete SAB T_bootstrap/r vs repeated scalar |
| G5_claim_boundary | PASS | claim level | binary added parameters only |
| G6_decision | PASS_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX | stage decision | PASS_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX |

## Claim Boundary

| claim | status | safe_statement | blocked_statement |
| --- | --- | --- | --- |
| binary_added_parameter_matrix | ALLOW_SCOPED | Current-head binary added-parameter rows have 10-sample T_bootstrap/r and 10-trial noise evidence. | Non-binary, all-parameter, novelty, or theoretical-optimality wording. |
| full_binary_matrix_with_target | READY_FOR_SYNTHESIS | Stage343 target rows plus Stage344 added rows can be synthesized if all gates pass. | Do not synthesize if either Stage343 or Stage344 gate is missing. |
