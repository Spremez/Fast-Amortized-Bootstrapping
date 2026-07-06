# Stage336 Exact PVW/MAT Frontier Report

Decision: `PASS_STAGE336_CURRENT_HEAD_SMOKE_SELECT_DIRECT_IFFT_FRONTIER`.

Stage336 resumes implementation-facing work after Stage335.  It records a
current-head FFNT smoke guard, keeps `T_bootstrap/r` as the endpoint, and
selects the next closed-path candidate from measured exact PVW/MAT-SAB
evidence.

## Summary

| decision | current_head_smoke | performance_anchor | selected_candidate | selected_next |
| --- | --- | --- | --- | --- |
| PASS_STAGE336_CURRENT_HEAD_SMOKE_SELECT_DIRECT_IFFT_FRONTIER | pass | stage331_current_head_highstat | direct_ifft_lifecycle | stage337_direct_ifft_lifecycle_candidate |

## Smoke

| step | backend | param | status | claim_use |
| --- | --- | --- | --- | --- |
| scalar_binary_full_run | ffnt | SET_2_3 | PASS | current-head correctness/build smoke only; not performance evidence |
| pvw_target_full_gate | ffnt | SET_2_3 | PASS | current-head correctness/build smoke only; not performance evidence |

## Frontier Evidence

| evidence | status | metric | value | claim_use |
| --- | --- | --- | --- | --- |
| stage331_current_head_highstat | PASS_STAGE331_CURRENT_HEAD_HIGHSTAT_REFRESH | complete_sab_T_bootstrap_over_r_vs_repeated_scalar | T/r=6117083.425; speedup=1.747647 | main scoped complete SAB result |
| stage336_current_head_smoke | PASS | current-head FFNT smoke | scalar_binary_and_pvw_target | current commit guard, non-performance |
| stage321_r4_unrolled_fullsab_ab | NEUTRAL_STAGE321_R4_UNROLLED_DIRECT_FULLSAB_NO_PROMOTION | incremental r4_unrolled_vs_direct_baseline | 0.998571 | closes r4-unrolled as current direct-path candidate |
| stage321_direct_baseline | Pass | complete SAB T/r direct baseline | 6118505.950 | sanity anchor for selected direct path |

## Component Frontier

| source_stage | component | share | avg_us | interpretation |
| --- | --- | --- | --- | --- |
| 288 | decompose | 0.271126 | 7.501737 | MAT EP split component; profile-only |
| 288 | torus_to_dft | 0.386764 | 10.701313 | MAT EP split component; profile-only |
| 288 | dense_from_dec | 0.337370 | 9.334637 | MAT EP split component; profile-only |
| 307 | digit_to_double | 0.481687 | 7.533581 | Direct DFT lifecycle subcomponent; profile-only |
| 307 | ifft | 0.504577 | 7.891585 | Direct DFT lifecycle subcomponent; profile-only |
| 307 | accounting_gap | 0.013737 |  | Direct DFT lifecycle subcomponent; profile-only |

## Candidate Selection

| candidate | status | basis | allowed_action | blocked_action |
| --- | --- | --- | --- | --- |
| direct_ifft_lifecycle | SELECT_STAGE337 | Stage288 torus_to_dft share=0.386764; Stage307 ifft share=0.504577 | isolated lifecycle/microbench design and a flag-gated closed-path experiment | claim complete SAB speedup before full A/B |
| digit_to_double_narrow_or_batch | SECONDARY | Stage307 digit_to_double share=0.481687 | microbench only after IFFT route is understood | wide hot-path rewrite without isolated equivalence |
| r4_unrolled_rows | CLOSED_NEUTRAL | Stage321 full SAB A/B ratio=0.998571 | none unless a new mechanism changes the cost model | promote r4-unrolled under current direct baseline |
| compact_selector | DENIED_FOR_COMPLETE_SAB | Stage222 complete selector expressiveness denied; Stage335 route audit | new closed neighbor-capable state proof only | integrate compact selector into SAB hot path |

## Proof Gate

| gate | status | metric | value |
| --- | --- | --- | --- |
| G1_current_head_smoke | PASS | FFNT scalar/PVW smoke | pass |
| G2_primary_metric | PASS | T_bootstrap/r | stage331_highstat |
| G3_compact_boundary | PASS | Stage335 compact route | denied |
| G4_profile_target | PASS | dominant closed-path residual | torus_to_dft/direct_ifft_lifecycle |
| G5_decision | PASS_STAGE336_CURRENT_HEAD_SMOKE_SELECT_DIRECT_IFFT_FRONTIER | stage decision | stage337_direct_ifft_candidate |

Generated from input head `55a0cc4`.
