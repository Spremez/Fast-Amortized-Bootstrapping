# Stage340 Parameter Matrix Current-Head Gate

Decision: `READY_STAGE340_CURRENT_HEAD_MATRIX_HARNESS_NO_NEW_PERFORMANCE_CLAIM`.

The Stage339 result remains scoped unless this matrix is executed on the
performance platform and all intended parameter/r cases pass. Stage340 provides
the harness, hot-code equivalence check, execution matrix, and parser.

## Current Status

| decision | hotcode_status | primary_supported_speedup | executed_case_count | missing_current_head_cases | claim_status |
| --- | --- | --- | --- | --- | --- |
| READY_STAGE340_CURRENT_HEAD_MATRIX_HARNESS_NO_NEW_PERFORMANCE_CLAIM | HOTCODE_EQUIVALENT | 1.747647 | 0 | 5 | no_new_performance_claim |

## Next Routes

| priority | route | command | gate | failure_action |
| --- | --- | --- | --- | --- |
| P0 | stage341_execute_current_head_parameter_matrix | STAGE340_EXECUTE=1 STAGE340_PERF_RUNS=10 STAGE340_NOISE_TRIALS=10 FFT_LIB=spqlios_avx512 bash scripts/run_stage340_parameter_matrix_current_head.sh | all intended parameter/r cases pass correctness, T_bootstrap/r A/B, noise, and RSS gates | Keep Stage339 scoped primary claim only. |
| P1 | stage341_verified_related_work_matrix | source-verified literature audit with real DOI/ePrint/TCHES/ICALP sources | no citation or novelty claim without fulltext/source support | Write scoped systems result without novelty overclaim. |
| P2 | stage341_new_mechanism_or_formal_proof | mechanism/proof preflight before SAB hot-path code | isolated equivalence and microbench, or formal keygen/security/noise proof | Reject before production integration. |
