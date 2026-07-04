# Stage275 Close S272-A and Select Next Candidate

Decision: `PASS_STAGE275_CLOSE_S272A_SELECT_INCLUDE_ZERO_COEFF_ONE_FAST_PATH`.

Stage275 closes the Stage272/274 in-place fused materialization candidate and
selects the next executable experiment. It does not implement a hot-path change
and does not claim speedup.

## Closed Candidate

| candidate | mode | fused_speedup_vs_backend | stage274_status | decision |
| --- | --- | --- | --- | --- |
| S272-A-sub_a_fused_from_DFT_add | include_zero | 0.751103 | neutral_or_negative | close_no_promotion |
| S272-A-sub_a_fused_from_DFT_add | ternary | 0.804529 | neutral_or_negative | close_no_promotion |

## Source Guard

| fact | status | evidence | interpretation |
| --- | --- | --- | --- |
| pvw_include_zero_rejects_negative_coeff | PASS | src/sab_pvw.c | Current PVW include-zero keygen admits only coefficient-one nonzero entries. |
| pvw_s_coff_encrypts_one | PASS | src/sab_pvw.c | Current PVW include-zero selector family materializes encrypted one for scanned nonzero entries. |
| scalar_include_zero_has_zero_gap_semantics | PASS | src/sparse_amortized_bootstrap.c | Scalar include-zero has a broader zero-selector branch, so a fast path must be guarded to current PVW semantics only. |
| stage274_fused_neutral | PASS | repro/stage274_sub_a_fused_materialization_smoke/proof_gate.csv | The in-place from_DFT_add fused materialization candidate is closed as non-promoted. |

## Candidate Ranking

| candidate | scope | stage271_full_pvw_share_basis | first_gate | risk | priority |
| --- | --- | --- | --- | --- | --- |
| S275-A-include_zero_coeff_one_fast_path | include_zero_only_current_pvw_semantics | 0.108762 | Stage276 explicit flag: staged/full correctness, smoke T_bootstrap/r include-zero only. | Scalar include-zero has broader zero-selector semantics; flag must be guarded and not claimed as general include-zero SAB. | P0 |
| S275-B-selector_mat_ep_kernel_tiling | include_zero_and_ternary | 0.057822 | Stage277 selector MAT-EP microbench/profile with exact selector family and r=4. | Local Amdahl ceiling is small; needs full SAB A/B before any claim. | P1 |
| S272-A-sub_a_fused_from_DFT_add | include_zero_and_ternary |  | closed | In-place direct-add is slower despite correctness. | closed |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage274_closeout | PASS | S272-A closeout rows | 2 | The fused materialization candidate is closed without promotion. |
| G2_source_guard | PASS | current PVW include-zero source facts | 4/4 | The next candidate is allowed only as a guarded current-PVW semantic fast path. |
| G3_candidate_selection | PASS | selected candidate | S275-A-include_zero_coeff_one_fast_path | Select an executable correctness-first include-zero fast path before lower-ceiling selector-kernel work. |
| G4_claim_boundary | PASS_DESIGN_ONLY | no speed claim | selection_gate | Stage275 selects the next experiment; it implements no hot-path optimization. |
| G5_decision | PASS_STAGE275_CLOSE_S272A_SELECT_INCLUDE_ZERO_COEFF_ONE_FAST_PATH | stage decision | PASS_STAGE275_CLOSE_S272A_SELECT_INCLUDE_ZERO_COEFF_ONE_FAST_PATH | Proceed to Stage276 only if the closeout inputs and source guard are complete. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| fused_materialization_candidate | closed_neutral | Stage274 found the fused from_DFT_add sub_a path correct but slower in full SAB smoke. | Fused from_DFT_add accelerates SAB. |
| include_zero_coeff_one_fast_path | selected_unimplemented | Current PVW source supports a guarded include-zero coeff-one fast-path hypothesis. | All include-zero SAB instances can drop s_coff. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage276_include_zero_coeff_one_fast_path | Stage275 source guard and closeout pass. | Explicit flag, include-zero staged/full correctness, full SAB T_bootstrap/r smoke vs default/backend. | selected | If correctness or smoke fails, close as guarded negative result and do not default-enable. |
| P1 | stage277_selector_mat_ep_kernel_tiling | Stage276 neutral/failed or residual profile still dominated by selector_mat_ep. | Selector MAT-EP microbench and full SAB A/B under explicit flag. | conditional | No claim without full SAB A/B. |

Generated from input head `e6b31c6`.
