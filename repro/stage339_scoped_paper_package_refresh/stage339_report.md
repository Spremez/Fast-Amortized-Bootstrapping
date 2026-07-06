# Stage339 Scoped Paper Package Refresh

Decision: `PASS_STAGE339_SCOPED_PACKAGE_REFRESH_NO_STRONGER_CLAIM`.

Stage339 executes the Stage338 P0 route. It refreshes the scoped paper/package
state without introducing a stronger performance claim. The current supported
speedup remains `1.747647x`, measured as
complete SAB `T_bootstrap/r` for the current-head r=4
`BINARY SET_2_3_2048` include-zero path.

## Summary

| decision | primary_metric | primary_scope | supported_speedup | samples | noise_pair_failures | parameter_claim_status |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE339_SCOPED_PACKAGE_REFRESH_NO_STRONGER_CLAIM | complete_sab_T_bootstrap_over_r | current_head_r4_SET_2_3_2048_include_zero_spqlios_avx512 | 1.747647 | 10 | 0/10 | scoped_current_head_plus_historical_matrix_needs_refresh |

## Claim Matrix

| claim_id | status | paper_safe_statement | blocked_statement |
| --- | --- | --- | --- |
| C1_metric | PASS | The primary endpoint is complete bootstrapping wall time divided by r processed MAT/RLWE body lanes. | Single-lane latency speedup over one scalar bootstrap. |
| C2_current_head_r4_speedup | PASS_SCOPED | For the measured r=4 BINARY SET_2_3_2048 include-zero path, direct PVW/MAT-SAB reaches 1.747647x T_bootstrap/r speedup over repeated scalar SAB. | Universal PVW/MAT-SAB speedup or all-parameter generality. |
| C3_correctness_noise_resource | PASS_SCOPED | Current-head output equivalence has 0/10 pair failures and max RSS 2415796 KB. | Security proof for compact selector variants. |
| C4_algorithmic_metric_vs_backend | PASS_SCOPED | The primary comparison is same-backend repeated scalar SAB versus r-body PVW/MAT-SAB by T_bootstrap/r. | Attributing the full speedup to AVX512 instructions alone or to backend changes. |
| C5_mat_rlwe_theoretical_optimality | BLOCK | Current exact dense MAT/RLWE route is closed under recorded local evidence. | The current MAT/RLWE SAB implementation is theoretically optimal. |
| C6_compact_or_structured_sab | BLOCK | Compact/structured selector remains a proof-gated future route. | Compact selector has complete SAB acceleration or production security. |
| C7_parameter_generalization | PARTIAL_HISTORICAL_NEEDS_CURRENT_HEAD_REFRESH | Historical r=2/r=4 and added binary parameter evidence exists, but the current-head primary claim remains r=4 SET_2_3_2048. | Current-head all-parameter claim. |
| C8_novelty | BLOCK_UNTIL_CITATION_VERIFIED | Novelty wording must wait for real, source-checked related-work support. | Novel shared-mask/common-mask or multi-output bootstrapping claim without verified sources. |

## Negative Ablations

| candidate | status | reason | reopen_condition |
| --- | --- | --- | --- |
| direct_ifft_batch5_intrinsics | CLOSED_SLOW | Correct but slower isolated batch5 intrinsics; do not integrate. | Different backend primitive with isolated speedup and equivalence. |
| direct_ifft_batch5_asm | CLOSED_SLOW | Correct but slower hand assembly; closes batch5 IFFT family. | New SPQLIOS primitive or native evidence not equivalent to Stage319. |
| digit_narrow32 | CLOSED_FULLSAB_NEUTRAL | Microbench positive but complete SAB A/B neutral. | New digit mechanism with full-SAB positive A/B. |
| r4_unrolled_rows | CLOSED_FULLSAB_NEUTRAL | Current direct baseline comparison ratio=0.998571. | New load/store count mechanism beyond pointer hoisting. |
| selector_transpose | CLOSED_MICRO_NEUTRAL | Isolated dense speedup below threshold for 1% full-SAB projection. | Different key layout with resource proof and stronger isolated speedup. |
| compact_selector_current_state | DENIED_COMPLETE_SAB | Current compact/lane-local state does not support complete selector integration. | Formal neighbor-capable closed state plus keygen/security/noise gates. |

## Parameter Coverage

| parameter | r | status | speedup | performance_samples | noise_status | claim_use |
| --- | --- | --- | --- | --- | --- | --- |
| BINARY SET_2_3_2048 include-zero | 4 | CURRENT_HEAD_PRIMARY_PASS | 1.747647 | 10 | 0/10 pair failures | main scoped claim |
| BINARY SET_2_3_2048 | 2 | HISTORICAL_PASS_NEEDS_CURRENT_HEAD_REFRESH | 1.191 | 10 | 0/50 seed failures | supporting historical matrix only |
| BINARY SET_2_3_2048 | 4 | HISTORICAL_PASS_SUPERSEDED_BY_CURRENT_HEAD_R4 | 1.377 | 10 | 0/50 seed failures | supporting historical matrix only |
| BINARY SET_4_5_2048 | 2 | HISTORICAL_ADDED_BINARY_PASS_NEEDS_CURRENT_HEAD_REFRESH | 1.285700 | 10 | 0/20 seed failures | do not use as current-head generality without rerun |
| BINARY SET_4_5_2048 | 4 | HISTORICAL_ADDED_BINARY_PASS_NEEDS_CURRENT_HEAD_REFRESH | 1.350700 | 10 | 0/20 seed failures | do not use as current-head generality without rerun |
| BINARY SET_2_3_4096 | 2 | HISTORICAL_ADDED_BINARY_PASS_NEEDS_CURRENT_HEAD_REFRESH | 1.235100 | 10 | 0/20 seed failures | do not use as current-head generality without rerun |
| BINARY SET_2_3_4096 | 4 | HISTORICAL_ADDED_BINARY_PASS_NEEDS_CURRENT_HEAD_REFRESH | 1.346200 | 10 | 0/20 seed failures | do not use as current-head generality without rerun |
| ternary/include-zero branches beyond recorded binary target | n/a | NOT_COVERED_BY_CURRENT_STAGE339_CLAIM |  |  |  | blocked until measured |

## Reviewer Risks

| risk | severity | mitigation | next_action |
| --- | --- | --- | --- |
| metric_confusion | high | Always report T_bootstrap/r and repeated scalar T/r; include total times only as derivation. | Keep C1 metric gate in every report table. |
| theoretical_optimality_overclaim | high | Use not-proven language; require a formal lower bound or compact proof to strengthen. | Stage340 may open proof route only with a concrete proof object. |
| novelty_prior_art | high | Do not claim novelty until source-verified literature matrix is complete. | Run citation/literature verification before manuscript novelty wording. |
| parameter_generality | medium | Mark historical rows and rerun current-head parameter matrix before broader claims. | Stage340 parameter matrix refresh. |
| resource_cost | medium | Current max RSS is recorded; broader resource matrix should be refreshed with parameter reruns. | Include RSS/key/keygen fields in any Stage340 run. |
| backend_attribution | medium | Same-backend A/B remains primary; perf counters are attribution, not the final speedup metric. | Use native counters only to explain, not replace, complete SAB A/B. |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_stage338_route | PASS | Stage338 decision | PASS_STAGE338_NO_NEW_MECHANISM_SELECT_SCOPED_PACKAGE_OR_EXTERNAL_PROOF |
| G2_current_head_primary | PASS | Stage331 decision | PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH |
| G3_claim_boundary | PASS | blocked stronger claims | 3 |
| G4_parameter_scope | PASS_SCOPED | current-head primary rows | 1 |
| G5_decision | PASS_STAGE339_SCOPED_PACKAGE_REFRESH_NO_STRONGER_CLAIM | stage decision | scoped_package_refreshed |
