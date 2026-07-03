# Stage190 Selector Distribution Distinguisher

Decision: `PASS_STAGE190_T1_SELECTOR_DISTRIBUTION_DISTINGUISHERS_RECORDED_IMPLEMENTATION_STILL_DENIED`.

Stage190 targets the Stage187 `T1_key_distribution` obligation. It does not
prove compact selectors insecure. It records a narrower result: the usual
shortcuts needed by compact/shared-output selector layouts cannot be described
as indistinguishable from the current dense MAT_TRGSW public key distribution
without a new proof or assumption.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage190_inputs | PASS | required_inputs_present | 1 | repro/stage124_mosfhet_type_api_skeleton/layout_results.csv; repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv; repro/stage189_closed_state_linear_probe/summary.csv | Stage190 targets T1 after Stage189 rejects direct public closure. | Repair missing inputs before interpreting distribution results. |
| stage190_distribution_probe | PASS_DISTINGUISHERS_RECORDED | distinguisher_rows | 9 | repro/stage190_selector_distribution_distinguisher/distribution_probe.csv | Row deletion, deterministic zero rows, and forced equal masks are publicly distinguishable in the finite probe. | Do not claim standard dense-key equivalence for compact selectors. |
| stage190_route_policy | DENY_PRODUCTION_COMPACT_CODE | proof_only_routes | 1 | repro/stage190_selector_distribution_distinguisher/distribution_route.csv | Only a declared new structured selector distribution remains open, and it is proof-only. | Run a formal assumption/reduction draft or T4 noise probe before code. |
| stage190_decision | PASS_STAGE190_T1_SELECTOR_DISTRIBUTION_DISTINGUISHERS_RECORDED_IMPLEMENTATION_STILL_DENIED | production_compact_sab_permission | 0 | repro/stage190_selector_distribution_distinguisher/summary.csv | T1 is not proven; standard-distribution shortcuts are rejected. | Proceed only to isolated proof/noise probes or scoped manuscript updates. |

## Distribution Probe

| candidate | r | mask_N | trials | dense_observation | structured_observation | distinguisher | successes | status | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| delete_body_cross_rows | 2 | 16 | 1 | 63 | 56 | public_row_count | 1 | DISTINGUISHER_FOUND | 7 public selector rows are missing versus dense format. |
| force_equal_output_masks | 2 | 16 | 64 | 0 | 64 | mask_equality_relation | 64 | DISTINGUISHER_FOUND | Forced shared/equal masks create a public equality relation absent from independent dense rows in the probe. |
| deterministic_zero_cross_rows | 2 | 16 | 64 | 0 | 64 | zero_mask_relation | 64 | DISTINGUISHER_FOUND | Replacing omitted rows with deterministic zero rows is publicly detectable. |
| delete_body_cross_rows | 4 | 16 | 1 | 175 | 112 | public_row_count | 1 | DISTINGUISHER_FOUND | 63 public selector rows are missing versus dense format. |
| force_equal_output_masks | 4 | 16 | 64 | 0 | 64 | mask_equality_relation | 64 | DISTINGUISHER_FOUND | Forced shared/equal masks create a public equality relation absent from independent dense rows in the probe. |
| deterministic_zero_cross_rows | 4 | 16 | 64 | 0 | 64 | zero_mask_relation | 64 | DISTINGUISHER_FOUND | Replacing omitted rows with deterministic zero rows is publicly detectable. |
| delete_body_cross_rows | 6 | 16 | 1 | 343 | 168 | public_row_count | 1 | DISTINGUISHER_FOUND | 175 public selector rows are missing versus dense format. |
| force_equal_output_masks | 6 | 16 | 64 | 0 | 64 | mask_equality_relation | 64 | DISTINGUISHER_FOUND | Forced shared/equal masks create a public equality relation absent from independent dense rows in the probe. |
| deterministic_zero_cross_rows | 6 | 16 | 64 | 0 | 64 | zero_mask_relation | 64 | DISTINGUISHER_FOUND | Replacing omitted rows with deterministic zero rows is publicly detectable. |

## Route Policy

| route | t1_status | public_difference | security_consequence | implementation_permission |
| --- | --- | --- | --- | --- |
| current_dense_mat_trgsw_distribution | AVAILABLE_REFERENCE | none versus current implementation | standard current route remains the baseline | YES_FOR_EXACT_FULL_MAT_ONLY |
| delete_body_cross_rows_and_claim_dense_equivalence | REJECTED | key row count/key size changes | not indistinguishable from dense public key format | NO |
| deterministic_zero_cross_rows | REJECTED | zero-mask relation is directly testable | cannot be justified as standard RLWE encryption of zero | NO |
| force_equal_or_shared_output_masks | REJECTED_AS_STANDARD_DISTRIBUTION | mask equality relation is directly testable | requires a new structured-key assumption or reduction | NO_UNTIL_PROOF |
| new_structured_selector_distribution | OPEN_PROOF_ONLY | must be declared as a new public key distribution | needs hybrid/simulation proof and leakage analysis | PROOF_ONLY |

## Claim Boundary

| claim | status | safe_replacement | evidence |
| --- | --- | --- | --- |
| compact_selector_is_standard_dense_key | DENY | compact selector variants change the public distribution unless a new proof is supplied | repro/stage190_selector_distribution_distinguisher/distribution_probe.csv |
| row_deletion_is_free | DENY | row deletion is a key-format change with an immediate public size distinguisher | repro/stage190_selector_distribution_distinguisher/distribution_probe.csv |
| equal_shared_masks_are_indistinguishable | DENY | equal/shared masks create a public relation in this finite probe | repro/stage190_selector_distribution_distinguisher/distribution_probe.csv |
| new_structured_key_may_be_studied | ALLOW_PROOF_ONLY | state an explicit structured-key assumption/reduction target before implementation | repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv; repro/stage176_structured_compact_security_api_gate/api_options.csv |
