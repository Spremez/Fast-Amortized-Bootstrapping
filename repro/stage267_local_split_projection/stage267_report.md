# Stage267 Local Split Projection

Decision: `PASS_STAGE267_LOCAL_SPLIT_PROJECTION_SELECT_STAGE268_BACKEND_SMOKE`.

Stage267 is the local fallback after Stage266 could not record native counters.
It does not measure a new speedup. It converts the current Stage263 non-binary
profile into Amdahl ceilings and selects the next bounded experiment.

## r=4 Component Aggregate

| component | share_body_min | share_body_max | share_pvw_min | share_pvw_max |
| --- | --- | --- | --- | --- |
| mat_ep | 0.415161 | 0.418790 | 0.411629 | 0.414869 |
| materialization_lifecycle | 0.449993 | 0.464893 | 0.445780 | 0.460938 |
| postproc_residual | 0.008581 | 0.009450 | 0.008508 | 0.009362 |
| sub_a | 0.110166 | 0.121316 | 0.109229 | 0.120180 |

## Candidate Selection

| candidate | target | r4_share_pvw_max | status | next_gate | failure_action |
| --- | --- | --- | --- | --- | --- |
| stage268_nonbinary_backend_from_dft_add_smoke | materialization_lifecycle | 0.460938 | selected | One-run r=4 include-zero/ternary backend-vs-default T_bootstrap/r smoke; then repeated/noise/resource only if positive. | Record neutral/negative and do not reopen direct-scale from_DFT work without a new mechanism. |
| mat_ep_kernel_layout_change | mat_ep | 0.414869 | blocked_until_counter_or_new_mechanism | Microbench plus full SAB A/B, same backend. | Do not repeat row-unroll-only negative path. |
| nonbinary_sub_a_rotation_path | sub_a | 0.120180 | deferred | Mode-specific sub_a profile and isolated equivalence before code. | Do not optimize sub_a before larger materialization candidate is screened. |

## Source Capability

| check | status | interpretation |
| --- | --- | --- |
| backend_from_dft_add_flag | PASS | Existing explicit flag can be tested without new hot-path code. |
| backend_flag_enables_fused_wrapper | PASS | Existing explicit flag can be tested without new hot-path code. |
| pvw_cmux_uses_from_dft_add | PASS | Existing explicit flag can be tested without new hot-path code. |
| backend_impl_guard | PASS | Existing explicit flag can be tested without new hot-path code. |
| nonbinary_bench_flag | PASS | Existing explicit flag can be tested without new hot-path code. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_inputs | PASS | Stage263 profile and Stage266 handoff | profile_rows=4 | Projection starts from current profile and no-native-counter boundary. |
| G2_materialization_share | PASS | r4 materialization_lifecycle share_pvw_max | 0.460938 | from_DFT+add+sub is large enough to screen an existing backend materialization flag. |
| G3_mat_ep_share | PASS | r4 mat_ep share_pvw_max | 0.414869 | MAT EP remains important but source-only AVX tuning needs native counters or a new mechanism. |
| G4_candidate_selection | selected | selected candidate | stage268_nonbinary_backend_from_dft_add_smoke | Select an existing explicit flag before writing new hot-path code. |
| G5_claim_boundary | PASS_PROJECTION_ONLY | no speedup claim | projection_not_measurement | Stage267 does not itself prove performance. |
| G6_decision | PASS_STAGE267_LOCAL_SPLIT_PROJECTION_SELECT_STAGE268_BACKEND_SMOKE | stage decision | PASS_STAGE267_LOCAL_SPLIT_PROJECTION_SELECT_STAGE268_BACKEND_SMOKE | Proceed to bounded Stage268 smoke only. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| component_priority | supported_projection | Current profile selects materialization_lifecycle as the first local smoke candidate. | Projection proves the candidate is faster. |
| hardware_counter_attribution | not_supported | Stage266 remains handoff-only without native counters. | Stage267 supplies native load/store/FMA attribution. |
| stage268_code_policy | no_new_hotpath_code | Stage268 may test an existing explicit flag. | Implement a new MAT/SAB hot-path variant before the smoke gate. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action |
| --- | --- | --- | --- | --- | --- |
| P0 | stage268_nonbinary_backend_from_dft_add_smoke | Stage267 selected existing explicit backend FromDFT-add flag. | r=4 include-zero/ternary correctness and one-run T_bootstrap/r backend-vs-default smoke. | selected | Record neutral/negative; no promotion. |
| P1 | stage268_repeated_noise_resource | Only if Stage268 smoke is positive for both modes. | repeated T_bootstrap/r, final noise/resource, same backend. | conditional | Do not claim full SAB speedup from smoke. |

Source model rows: `2`. Generated from input head `41f3e62`.
