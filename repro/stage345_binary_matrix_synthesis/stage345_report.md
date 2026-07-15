# Stage345 Binary Matrix Synthesis

Decision: `PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY`.

Stage345 synthesizes current-head binary parameter evidence under the user's
requested amortized endpoint: complete SAB `T_bootstrap/r` versus repeated
scalar SAB. It is not a new kernel, backend, novelty, or theoretical-optimality
claim.

## Summary

| decision | rows | primary_metric | speedup_min | speedup_max | speedup_mean_across_rows | claim_status |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY | 6 | complete_sab_T_bootstrap_over_r_vs_repeated_scalar | 1.612100 | 1.747647 | 1.686741 | scoped_binary_matrix_ready |

## Matrix

| case | samples | correctness | pvw_t_over_r_mean_us | scalar_t_over_r_mean_us | speedup_mean | noise_trials | noise_pair_failures | evidence_stage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SET_2_3_2048_r2 | 10 | Pass | 6612564.550 | 11056987.250 | 1.672200 | 10 | 0 | Stage343 |
| SET_2_3_2048_r4 | 10 | Pass | 6117083.425 | 10690503.200 | 1.747647 | 10 | 0 | Stage331 |
| SET_4_5_2048_r2 | 10 | Pass | 7117983.900 | 12165024.000 | 1.709700 | 10 | 0 | Stage344 |
| SET_4_5_2048_r4 | 10 | Pass | 8121233.000 | 14132476.475 | 1.738200 | 10 | 0 | Stage344 |
| SET_2_3_4096_r2 | 10 | Pass | 13561017.550 | 21864209.800 | 1.612100 | 10 | 0 | Stage344 |
| SET_2_3_4096_r4 | 10 | Pass | 11753773.550 | 19235637.400 | 1.640600 | 10 | 0 | Stage344 |

## Claim Boundary

| claim | status | safe_statement | blocked_statement |
| --- | --- | --- | --- |
| binary_parameter_matrix | ALLOW_SCOPED | For tested binary include-zero parameter rows SET_2_3_2048, SET_4_5_2048, and SET_2_3_4096 with r=2/4, PVW/MAT-SAB improves complete SAB T_bootstrap/r versus repeated scalar SAB under spqlios_avx512. | Do not generalize to all parameters, non-binary branches, or other backends without matching gates. |
| algorithmic_speedup_metric | ALLOW_SCOPED | The comparison dimension is amortized per plaintext bit/lane, T_bootstrap/r, not raw single-call latency. | Do not mix kernel microbench, backend/SIMD gains, or scalar single-call latency into this matrix claim. |
| novelty_or_theoretical_optimality | BLOCKED | No novelty or theoretical-optimality wording is introduced by this synthesis. | Requires verified related-work/full-text support and a separate proof or lower-bound argument. |
| resource_generality | PARTIAL_ONLY | RSS is recorded per row; key size/keygen/resource generality is not fully synthesized here. | Do not claim memory/key-size optimality or full resource dominance from this matrix alone. |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_input_stage_decisions | PASS | Stage331/343/344 decisions | Stage331=PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH;Stage343=PASS_STAGE343_TARGET_R2_CURRENT_HEAD_HIGHSTAT_TOPUP;Stage344=PASS_STAGE344_ADDED_PARAMETER_CURRENT_HEAD_MATRIX |
| G2_matrix_coverage | PASS | observed/expected cases | 6/6 |
| G3_row_quality | PASS | samples/correctness/noise | all rows 10 samples, correctness Pass, noise 0/10 |
| G4_metric_alignment | PASS | primary endpoint | complete SAB T_bootstrap/r vs repeated scalar |
| G5_claim_boundary | PASS | blocked claims | non-binary;all-parameter;novelty;theoretical-optimality;resource-generality |
| G6_decision | PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY | stage decision | PASS_STAGE345_BINARY_MATRIX_SYNTHESIS_SCOPED_READY |
