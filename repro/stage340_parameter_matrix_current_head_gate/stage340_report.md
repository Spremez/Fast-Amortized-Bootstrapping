# Stage340 Parameter Matrix Current-Head Gate

Decision: `READY_STAGE340_CURRENT_HEAD_MATRIX_HARNESS_NO_NEW_PERFORMANCE_CLAIM`.

Stage340 adds the executable gate for broadening the parameter claim. It does
not create a new speedup result unless `STAGE340_EXECUTE=1` logs are present and
parse successfully.

## Summary

| decision | current_head | stage331_head | hotcode_status | primary_supported_speedup | executed_case_count | missing_current_head_cases | claim_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| READY_STAGE340_CURRENT_HEAD_MATRIX_HARNESS_NO_NEW_PERFORMANCE_CLAIM | e0b7560 | 6a5f113 | HOTCODE_EQUIVALENT | 1.747647 | 0 | 5 | no_new_performance_claim |

## Hot-Code Equivalence

| stage331_head | current_head | hotcode_diff_count | hotcode_diff_paths | status |
| --- | --- | --- | --- | --- |
| 6a5f113 | e0b7560 | 0 |  | HOTCODE_EQUIVALENT |

## Execution Matrix

| case | status | gate |
| --- | --- | --- |
| SET_2_3_2048_r2 | NEEDS_CURRENT_HEAD_EXECUTION | complete SAB T_bootstrap/r A/B plus noise/RSS; same backend; no claim if missing logs |
| SET_2_3_2048_r4 | SATISFIED_BY_STAGE331_HOTCODE_EQUIVALENT_PRIMARY | complete SAB T_bootstrap/r A/B plus noise/RSS; same backend; no claim if missing logs |
| SET_4_5_2048_r2 | NEEDS_CURRENT_HEAD_EXECUTION | complete SAB T_bootstrap/r A/B plus noise/RSS; same backend; no claim if missing logs |
| SET_4_5_2048_r4 | NEEDS_CURRENT_HEAD_EXECUTION | complete SAB T_bootstrap/r A/B plus noise/RSS; same backend; no claim if missing logs |
| SET_2_3_4096_r2 | NEEDS_CURRENT_HEAD_EXECUTION | complete SAB T_bootstrap/r A/B plus noise/RSS; same backend; no claim if missing logs |
| SET_2_3_4096_r4 | NEEDS_CURRENT_HEAD_EXECUTION | complete SAB T_bootstrap/r A/B plus noise/RSS; same backend; no claim if missing logs |

## Historical Evidence Map

| parameter | r | evidence_class | perf_speedup | perf_samples | noise_status | claim_use |
| --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_2048 include-zero | 4 | current_head_primary | 1.747647 | 10 | 0/10 | main scoped claim if hotcode-equivalent |
| SET_2_3_2048 | 2 | historical_target_matrix | 1.191 | 10 | 0/50 | supporting only; rerun for current-head broader claim |
| SET_2_3_2048 | 4 | historical_target_matrix | 1.377 | 10 | 0/50 | supporting only; rerun for current-head broader claim |
| SET_4_5_2048 | 2 | historical_added_binary_matrix | 1.285700 | 10 | 0/20 | supporting only; rerun for current-head broader claim |
| SET_4_5_2048 | 4 | historical_added_binary_matrix | 1.350700 | 10 | 0/20 | supporting only; rerun for current-head broader claim |
| SET_2_3_4096 | 2 | historical_added_binary_matrix | 1.235100 | 10 | 0/20 | supporting only; rerun for current-head broader claim |
| SET_2_3_4096 | 4 | historical_added_binary_matrix | 1.346200 | 10 | 0/20 | supporting only; rerun for current-head broader claim |

## Claim Update

| claim | status | statement |
| --- | --- | --- |
| primary_r4_SET_2_3_2048 | UNCHANGED_SUPPORTED | Stage331 primary r=4 result remains hot-code current if no src/Makefile/include changes occurred. |
| current_head_parameter_matrix | NOT_PROMOTED | Executed current-head matrix cases parsed: 0. |
| broader_parameter_generality | BLOCK_UNTIL_STAGE340_EXECUTED | Historical parameter rows remain supporting evidence only until current-head matrix logs pass. |
| new_performance_speedup | NO_NEW_CLAIM_THIS_STAGE | The harness gate itself does not create a new performance result. |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_stage339_route | PASS | Stage339 decision | PASS_STAGE339_SCOPED_PACKAGE_REFRESH_NO_STRONGER_CLAIM |
| G2_hotcode_equivalence | PASS | src/Makefile/include diff since Stage331 | HOTCODE_EQUIVALENT |
| G3_harness_ready | PASS | runner and builder | scripts/run_stage340_parameter_matrix_current_head.sh; scripts/build_stage340_parameter_matrix_execution_gate.py |
| G4_current_head_matrix_coverage | PARTIAL | missing current-head cases | 5 |
| G5_executed_result_cases | NOT_EXECUTED_OR_PARTIAL | passed executed cases | 0 |
| G6_decision | READY_STAGE340_CURRENT_HEAD_MATRIX_HARNESS_NO_NEW_PERFORMANCE_CLAIM | stage decision | READY_STAGE340_CURRENT_HEAD_MATRIX_HARNESS_NO_NEW_PERFORMANCE_CLAIM |
