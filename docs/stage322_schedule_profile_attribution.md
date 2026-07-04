# Stage322 Schedule/Profile Attribution

Decision: `PASS_STAGE322_PROFILE_SELECT_DENSE_MAT_LAYOUT_COUNTER_PREFLIGHT`.

Stage322 profiles the current selected direct PVW/MAT-SAB path after Stage321
closed the exact r4-unrolled refresh. The goal is to pick the next executable
route by measured complete-SAB budget rather than reopen failed local routes.

## Summary

| decision | selected_next_stage | correctness | t_bootstrap_over_r_us | speedup_vs_repeated_scalar | mat_ep_share | dense_share | sub_a_share | copyback_share | direct_ifft_share | direct_digit_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE322_PROFILE_SELECT_DENSE_MAT_LAYOUT_COUNTER_PREFLIGHT | stage323_dense_mat_layout_counter_preflight | Pass | 6191943.500 | 1.748 | 0.576230 | 0.212353 | 0.026891 | 0.000000 | 0.178357 | 0.170493 |

## Component Budget

| component | share_of_profile_full | calls | status | interpretation |
| --- | --- | --- | --- | --- |
| mat_ep_lifecycle | 0.576230 | 1146880 | DOMINANT_BUT_R4_UNROLLED_CLOSED | MAT EP remains dominant; Stage321 closes only the r4-unrolled implementation, not all MAT layout work. |
| cmux_from_dft | 0.380787 | 1146880 | MATERIALIZATION_RESIDUAL | Materializing MAT EP output remains large, but backend-from-DFT-add is already active. |
| dense_from_dec | 0.212353 | 1146880 | SELECTABLE_UNCLOSED | Largest unclosed MAT subcomponent after digit/IFFT/r4 routes are closed. |
| direct_ifft | 0.178357 | 1126560 | CLOSED_STAGE319 | Batch5 IFFT intrinsics and assembly failed isolated gates. |
| direct_digit | 0.170493 | 1126560 | CLOSED_STAGE314 | Local digit variants did not move complete SAB enough. |
| sub_a_total | 0.026891 | 78 | LOW_SHARE_DEFER | Sub_a is below the schedule-preflight threshold in this profile. |
| sub_a_rotate | 0.021737 | 159744 | LOW_SHARE_DEFER | Rotation is the main sub_a cost but still too small for the next first candidate. |
| sub_a_copy | 0.004989 | 159744 | LOW_SHARE_DEFER | Copy inside sub_a is measurable but below the materiality threshold. |
| ncmux_auto | 0.007716 | 10160 | LOW_SHARE_DEFER | Automorphism work is not the largest remaining budget. |
| dual_sub_pair | 0.002413 | 10160 | LOW_SHARE_DEFER | Dual-sub pair overhead is already small. |
| copyback | 0.000000 |  | NO_CURRENT_BUDGET | Active/direct path reports zero copyback calls; copyback fusion is not a valid next target. |

## Candidate Ranking

| rank | candidate | status | profile_share | reason |
| --- | --- | --- | --- | --- |
| P0 | dense_mat_layout_counter_preflight | SELECT_STAGE323 | 0.212353 | Dense MAT addmul is the largest unclosed measured component after digit, IFFT, and r4-unrolled routes are closed. |
| P1 | sub_a_rotation_copy_preflight | DEFER_LOW_SHARE | 0.026891 | Schedule-level sub_a work is measurable but below the 5% materiality threshold in current profile. |
| P2 | copyback_fusion_refresh | CLOSED_NO_BUDGET | 0.000000 | Current active/direct path reports no copyback calls. |
| CLOSED | r4_unrolled_current_direct | CLOSED_STAGE321_NEUTRAL | 0.576230 | Stage321 complete-SAB A/B was neutral, so this exact r4-unrolled route is closed. |
| CLOSED | batch5_ifft | CLOSED_STAGE319 | 0.178357 | Both intrinsics and hand-assembly batch5 IFFT were correct but slower. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage321_input | PASS | Stage321 decision | r4-neutral | Stage322 opens only after r4-unrolled is closed under current direct baseline. |
| G2_correctness | PASS | target correctness | Pass | Profile attribution is invalid if complete SAB correctness fails. |
| G3_schedule_count | PASS | mat_ep calls | 1146880/573440x2 | Confirms the expected 40*7*2048 external-product call surface per profile sample. |
| G4_closed_routes | PASS | deny list | digit;ifft;r4_unrolled | Closed routes are not reopened without a new mechanism. |
| G5_candidate_selection | PASS_STAGE322_PROFILE_SELECT_DENSE_MAT_LAYOUT_COUNTER_PREFLIGHT | selected next | stage323_dense_mat_layout_counter_preflight | Selects the next route by measured share and closure status, not by theoretical preference. |

Generated from input head `0490061`.
