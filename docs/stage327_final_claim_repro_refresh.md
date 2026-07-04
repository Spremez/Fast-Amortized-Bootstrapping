# Stage327 Final Claim/Repro Refresh

Decision: `PASS_STAGE327_FINAL_CLAIM_REPRO_REFRESH_SCOPED_READY`.

The current research loop is closed for exact dense/local-layout optimization.
The supported result is a scoped complete-SAB amortized throughput claim in
`T_bootstrap/r` terms. Selector-transpose and r4-unrolled variants remain
negative/neutral ablations, and compact/structured selector remains blocked by
formal proof requirements.

## Summary

| decision | supported_metric | supported_speedup | supported_t_bootstrap_over_r_us | exact_dense_frontier | compact_route | claim_level |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE327_FINAL_CLAIM_REPRO_REFRESH_SCOPED_READY | complete_sab_T_bootstrap_over_r_vs_repeated_scalar | 1.745361 | 6118505.950 | closed_under_current_evidence | frozen_until_formal_proof | scoped_systems_engineering_current_parameters |

## Claim Matrix

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| complete_sab_amortized_throughput | SUPPORTED_SCOPED | On the current r=4 target path, exact PVW/MAT-SAB improves complete SAB amortized throughput by about 1.745361x in T_bootstrap/r versus repeated scalar SAB under the recorded backend. | PVW/MAT-SAB is theoretically optimal or universally faster. |
| selector_transpose_layout | NEGATIVE_OR_NEUTRAL_ABLATION | Coefficient-blocked selector-transpose is bit-exact but only reached 1.028925x isolated dense speedup and 1.006006x projected full-SAB speedup. | Selector-transpose should be integrated into SAB. |
| mat_avx512_optimality | NOT_PROVEN | Current r=4 dense MAT loop already has the main row-reuse/output-store properties tested locally. | The AVX512 MAT external product is theoretically optimal. |
| structured_compact_sab_algorithm | BLOCKED_PROOF_REQUIRED | Structured/compact selector remains a proof route with no production SAB claim. | Compact selector accelerates SAB bootstrapping. |
| paper_level_novelty | SCOPED_ONLY | The current evidence supports a scoped systems/engineering optimization claim for this implementation and parameter path. | This is a broad new asymptotic bootstrapping algorithm without additional proof and literature review. |

## Limitations

| limitation | status | detail |
| --- | --- | --- |
| parameter_scope | scoped | Primary current-head claim is for the recorded r=4 BINARY SET_2_3_2048 path and backend evidence. |
| metric_scope | scoped | Speedup dimension is T_bootstrap/r versus repeated scalar SAB, not single-lane latency versus one scalar bootstrap. |
| exact_dense_frontier | closed_current_evidence | Current local exact dense AVX/layout routes are closed, but new mechanisms may reopen with gates. |
| compact_route | blocked | Structured/compact product-count reduction requires formal proof and full SAB evidence. |
| theoretical_optimality | not_proven | No global theoretical optimality claim is supported. |

## Gates

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage326_input | PASS | Stage326 decision | PASS_STAGE326_EXACT_DENSE_FRONTIER_CLOSED_CLAIM_REFRESH_SELECTED | Final refresh requires exact dense frontier closeout. |
| G2_fullsab_claim | PASS_SCOPED | supported speedup | 1.745361 | Claim uses complete-SAB T_bootstrap/r evidence only. |
| G3_negative_ablation | PASS_RECORDED | selector transpose projection | 1.006006 | Neutral/negative results are preserved and not promoted. |
| G4_limitations | PASS_RECORDED | limitations | parameter;metric;optimality;compact | Unsupported stronger claims are explicitly blocked. |
| G5_stage327_decision | PASS_STAGE327_FINAL_CLAIM_REPRO_REFRESH_SCOPED_READY | final current-head package | scoped ready | Current research loop is closed until a new proof-backed or measured mechanism is supplied. |

Generated from input head `acd7112`.
