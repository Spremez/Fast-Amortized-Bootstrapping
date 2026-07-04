# Stage270 Candidate Closeout And Next Selection

Decision: `PASS_STAGE270_FROM_DFT_ADD_CLOSED_SELECT_SUBA_SPLIT_PROFILE`.

Stage270 closes the existing backend FromDFT-add materialization candidate after
Stage269 repeated timing failed to promote it. The research loop now returns to
the remaining candidate queue without changing SAB hot-path behavior.

## Candidate Closeout

| candidate | stage268_smoke_min_speedup | stage269_repeated_min_speedup | decision | rule |
| --- | --- | --- | --- | --- |
| backend_from_dft_add_materialization | 1.014700 | 0.991473 | CLOSE_NEUTRAL_NO_PROMOTION | Do not use Stage268 smoke as final evidence; do not reopen this flag without a new mechanism or changed profile. |

## Next Candidate Selection

| candidate | profile_basis | execution_status | selected | next_gate | reason |
| --- | --- | --- | --- | --- | --- |
| mat_ep_native_counter_or_layout_change | r4 mat_ep share_pvw_max=0.414869 | blocked_auth_or_counter_platform | no | Native current-head counters for load/store/FMA before new layout code. | MAT EP remains largest single component, but source-only tuning cannot prove AVX512 optimality or guide layout safely. |
| nonbinary_sub_a_split_profile | r4 sub_a share_pvw_max=0.120180 | available_local | yes | Stage271 add profile-only split counters for rotation, MAT EP, from_DFT, and add/copy inside non-binary sub_a; run r=4 include-zero/ternary correctness plus body profile. | Materialization flag was neutral on repeated timing; sub_a is the next material local bottleneck with isolated source entry points. |
| postproc_extract_packing | r4 postproc share_pvw_max=0.009362 | deferred_low_share | no | Only revisit if body optimizations raise tail share. | Current tail share is below 1%; high-risk tail work is not justified. |

## Source Capability

| check | status | interpretation |
| --- | --- | --- |
| nonbinary_sub_a_include_zero_exists | PASS | Local sub_a profiling/preflight can be built from current sources. |
| nonbinary_sub_a_ternary_exists | PASS | Local sub_a profiling/preflight can be built from current sources. |
| sub_a_body_profile_counter_exists | PASS | Local sub_a profiling/preflight can be built from current sources. |
| body_profile_flag_exists | PASS | Local sub_a profiling/preflight can be built from current sources. |
| suba_output_fusion_flag_exists | PASS | Local sub_a profiling/preflight can be built from current sources. |

## Auth Probe

| probe | status | returncode |
| --- | --- | --- |
| cb5_batchmode | auth_unavailable | 255 |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_from_dft_add_closeout | PASS | Stage269 repeated result | 0.991473 | The Stage268 smoke candidate did not survive repeated timing. |
| G2_no_smoke_overclaim | PASS | claim boundary | smoke_not_promoted | Stage268 may remain context only, not an optimization claim. |
| G3_native_counter_route | BLOCKED | CB5 batchmode auth | auth_unavailable | MAT EP native counter route remains selected only when authenticated native execution is available. |
| G4_stage266_boundary | PASS | native counter claim boundary | no_current_native_counter_rows | No hardware-counter optimality wording is allowed. |
| G5_next_candidate | PASS | selected local candidate | nonbinary_sub_a_split_profile | Select the next local executable gate rather than writing optimization code directly. |
| G6_decision | PASS_STAGE270_FROM_DFT_ADD_CLOSED_SELECT_SUBA_SPLIT_PROFILE | stage decision | PASS_STAGE270_FROM_DFT_ADD_CLOSED_SELECT_SUBA_SPLIT_PROFILE | Proceed to Stage271 sub_a split profile preflight. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| backend_from_dft_add | closed_neutral | The existing backend FromDFT-add flag had a positive smoke but failed repeated promotion. | Backend FromDFT-add improves full SAB throughput. |
| mat_ep_optimality | blocked_no_native_counter | MAT EP remains the largest single component and needs native counter attribution. | Current MAT AVX512 is theoretically optimal. |
| sub_a_next | selected_preflight_only | sub_a split profiling is the next local executable gate. | sub_a optimization is proven beneficial before split profile and full SAB A/B. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage271_nonbinary_sub_a_split_profile | Stage270 selects local sub_a split profile after FromDFT-add closeout. | profile-only counters, r=4 include-zero/ternary correctness, split attribution; no hot-path claim. | selected | If split counters show no actionable component, close sub_a and return to MAT native counter route. |
| P1 | stage272_sub_a_candidate_smoke | Only if Stage271 identifies a dominant safe subcomponent. | isolated equivalence plus full SAB T_bootstrap/r smoke. | conditional | Record neutral/negative; do not promote. |

Generated from input head `3ef9311`.
