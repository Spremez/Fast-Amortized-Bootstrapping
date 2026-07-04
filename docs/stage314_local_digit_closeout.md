# Stage314 Local Digit Closeout

Decision: `PASS_STAGE314_LOCAL_DIGIT_MICROVARIANTS_CLOSED_BACKEND_OR_SCHEDULE_NEXT`.

Stage314 closes unsupported local digit microvariants after Stage309-313 and sets an admission rule for future candidates.

## Summary

| decision | stage309_rowbatch_decision | stage312_fullsab_narrow32_vs_direct | stage313_profile_digit_speedup | digit_share_of_body_profile | projected_body_speedup_from_observed_digit_only | route |
| --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE314_LOCAL_DIGIT_MICROVARIANTS_CLOSED_BACKEND_OR_SCHEDULE_NEXT | NEUTRAL_STAGE309_DIGIT_ROWBATCH_NO_PROMOTION | 0.997104 | 1.044719 | 0.172510 | 1.007439 | backend_ifft_or_schedule_level_only_without_new_budget |

## Component Budget

| component | share_of_body_profile | hypothetical_component_reduction | projected_body_profile_speedup |
| --- | --- | --- | --- |
| digit_to_double | 0.172510 | 0.05 | 1.008701 |
| digit_to_double | 0.172510 | 0.10 | 1.017554 |
| digit_to_double | 0.172510 | 0.25 | 1.045071 |
| digit_to_double | 0.172510 | 0.50 | 1.094397 |
| ifft | 0.181943 | 0.05 | 1.009181 |
| ifft | 0.181943 | 0.10 | 1.018531 |
| ifft | 0.181943 | 0.25 | 1.047653 |
| ifft | 0.181943 | 0.50 | 1.100075 |
| dense_from_dec | 0.215408 | 0.05 | 1.010888 |
| dense_from_dec | 0.215408 | 0.10 | 1.022015 |
| dense_from_dec | 0.215408 | 0.25 | 1.056917 |
| dense_from_dec | 0.215408 | 0.50 | 1.120704 |
| mat_ep_total | 0.585042 | 0.05 | 1.030134 |
| mat_ep_total | 0.585042 | 0.10 | 1.062140 |
| mat_ep_total | 0.585042 | 0.25 | 1.171317 |
| mat_ep_total | 0.585042 | 0.50 | 1.413469 |

## Candidate Rules

| candidate_family | status | admission_rule |
| --- | --- | --- |
| local_digit_microvariants | CLOSED_WITHOUT_NEW_BUDGET | Only reopen if projected full-SAB T/r speedup is >=1.02 before implementation. |
| backend_ifft_batch_or_fusion | OPEN_HIGH_RISK | Requires new backend API/model/assembly correctness before SAB integration. |
| schedule_level_reduction | OPEN_ALGORITHMIC | Must reduce call count, materialization count, or schedule lifecycle at SAB level, not only one conversion instruction. |
| dense_mat_avx_rewrite | DEFER | Reopen only if DFT lifecycle ceases to dominate or a concrete assembly/counter hypothesis exists. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_evidence_present | PASS | Stage309-313 files | present | Closeout must be based on recorded experiments. |
| G2_micro_to_full_alignment | PASS | micro positive but full neutral | digit=1.044719; full=0.997104 | Local digit changes are diluted and should not continue without stronger budget. |
| G3_budget_rule | PASS | minimum pre-implementation projected T/r | >=1.02 | New candidates need a predicted full-SAB effect above profile noise. |
| G4_claim_boundary | PASS | scope | route gate only | This is not a new speed claim. |
| G5_decision | PASS_STAGE314_LOCAL_DIGIT_MICROVARIANTS_CLOSED_BACKEND_OR_SCHEDULE_NEXT | stage decision | PASS_STAGE314_LOCAL_DIGIT_MICROVARIANTS_CLOSED_BACKEND_OR_SCHEDULE_NEXT | Controls Stage315 route. |
