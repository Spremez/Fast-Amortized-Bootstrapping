# Stage326 Exact Dense Route Closeout

Decision: `PASS_STAGE326_EXACT_DENSE_FRONTIER_CLOSED_CLAIM_REFRESH_SELECTED`.

Stage326 closes the current exact dense/local-layout optimization frontier
under the evidence collected through Stage325. This is not a statement of
global theoretical optimality. It means the current key format and local AVX512
routes no longer have an admitted next implementation step without a new
measured mechanism or a formal compact/structured proof.

## Summary

| decision | selected_next_stage | current_direct_speedup_vs_repeated_scalar | dense_share | selector_transpose_dense_speedup | selector_transpose_required_speedup | selector_transpose_projected_fullsab | exact_dense_route_status | compact_route_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE326_EXACT_DENSE_FRONTIER_CLOSED_CLAIM_REFRESH_SELECTED | stage327_final_claim_repro_refresh | 1.748 | 0.212353 | 1.028925 | 1.048905 | 1.006006 | closed_under_current_evidence | frozen_until_formal_proof |

## Evidence Matrix

| evidence | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| current_complete_sab_direct_baseline | SUPPORTED | T_bootstrap/r speedup versus repeated scalar | 1.748 | Current exact PVW/MAT-SAB result remains the supported throughput baseline. |
| r4_unrolled_fullsab_ab | CLOSED_NEUTRAL | decision | NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION | Pointer-hoist/r4-unrolled local AVX512 variant does not improve complete SAB. |
| dense_mat_profile_budget | MEASURED_RESIDUAL | dense_share;mat_ep_share | 0.212353;0.576230 | Dense MAT remains a residual budget, but local exact loop changes need a new mechanism. |
| selector_transpose_microbench | CLOSED_NEUTRAL | isolated_dense_speedup;required;fullsab_projection | 1.028925;1.048905;1.006006 | Selector-transpose locality is correct but below the threshold needed to justify integration. |
| direct_digit | CLOSED_STAGE314 | share | 0.170493 | Local digit variants did not move complete SAB enough. |
| direct_ifft | CLOSED_STAGE319 | share | 0.178357 | Batch5 IFFT intrinsics and assembly failed isolated gates. |
| sub_a_and_copyback | DEFER_LOW_BUDGET | sub_a_share;copyback_share | 0.026891;0.000000 | Current profile does not select sub_a/copyback as first-order optimization targets. |
| compact_structured_route | FROZEN_PROOF_REQUIRED | Stage324 selected route boundary | PASS_STAGE324_SELECT_SELECTOR_TRANSPOSE_RESOURCE_PREFLIGHT_COMPACT_REMAINS_FROZEN | Compact/structured selector is not production-admitted without formal proof and full SAB evidence. |

## Frontier Status

| frontier | status | why | allowed_reopen_condition |
| --- | --- | --- | --- |
| exact_dense_current_key_format | CLOSED_UNDER_CURRENT_EVIDENCE | r4 unrolled and selector-transpose both failed full-SAB or projected full-SAB gates. | new load/store/count mechanism with microbench threshold and full-SAB A/B plan |
| current_supported_claim | KEEP_SCOPED_T_BOOTSTRAP_OVER_R | Current complete SAB evidence supports amortized throughput versus repeated scalar, not theoretical optimality. | Stage327 final claim refresh may package this as scoped systems evidence. |
| structured_compact_algorithmic_route | BLOCKED_PROOF_REQUIRED | Potential product-count reduction changes selector semantics and remains proof-only. | formal distribution/keygen/security proof, noise recurrence, isolated equivalence, and full SAB A/B |
| native_counter_refresh | OPTIONAL_ATTRIBUTION_ONLY | Native counters can improve attribution but cannot rescue a neutral isolated microbench by themselves. | use to support final wording or a new mechanism, not to claim unmeasured speedup |

## Proof Gates

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage325_input | PASS | Stage325 decision | NEUTRAL_STAGE325_SELECTOR_TRANSPOSE_MICRO_NO_PROMOTION | Stage326 closeout requires the selected Stage325 route to be resolved. |
| G2_exact_dense_routes | PASS_CLOSED | closed routes | r4_unrolled;selector_transpose;digit;ifft | Current exact dense/local implementation routes are closed or deferred by measured gates. |
| G3_claim_boundary | PASS_SCOPED | allowed claim | complete-SAB T_bootstrap/r throughput evidence | Do not upgrade to theoretical optimality, compact algorithm, or all-parameter claims. |
| G4_next_stage | PASS_STAGE326_EXACT_DENSE_FRONTIER_CLOSED_CLAIM_REFRESH_SELECTED | selected next | stage327_final_claim_repro_refresh | Refresh final package instead of starting another low-mechanism AVX rewrite. |

Generated from input head `e6c0134`.
