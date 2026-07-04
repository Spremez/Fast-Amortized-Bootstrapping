# Stage284 Frontier Gap Ledger

Decision: `PASS_STAGE284_FRONTIER_GAP_LEDGER_READY_NATIVE_OR_MAT_EP_SPLIT_NEXT`.

Stage284 aligns the current selected PVW/MAT-SAB path with the original
MAT-RLWE/r-body research objective.  It treats `T_bootstrap/r` as the only
primary speed endpoint, consumes the latest repeated/noise/resource/native
gates, and converts the residual profile into falsifiable next-stage work.

## Frontier Summary

| item | value | status | interpretation |
| --- | --- | --- | --- |
| primary_endpoint | T_bootstrap/r | fixed | All current speed comparisons are amortized per processed lane/bit. |
| fast_control_t_over_r_mean_us | 7058774.917 | Pass | Current same-backend control after include-zero fast path. |
| candidate_t_over_r_mean_us | 6584179.750 | Pass | Current selected backend_sub_decomp_dual path. |
| candidate_vs_fast_control_mean | 1.072081 | local_repeated_positive | Incremental local repeated improvement over the current fast control. |
| candidate_vs_fast_control_conservative | 1.063396 | positive | Conservative min/control over max/candidate guard. |
| candidate_vs_repeated_scalar_mean | 1.596038 | local_repeated_positive | Amortized MAT-RLWE/r-body gain over repeated scalar SAB. |
| noise_resource_gate | pass | pass | Local ffnt proxy; not target AVX512 performance evidence. |
| native_target_gate | native_access_failed_or_missing_auth | failed | Paper-grade native target timing remains disallowed until access succeeds. |

## Residual Gap Ledger

| component | profile_share | component_us_profile_total | calls | projected_t_over_r_if_zero_us | zero_component_upper_bound_vs_candidate | next_gate |
| --- | --- | --- | --- | --- | --- | --- |
| mat_ep | 0.604066 | 15691590.000 | 573440 | 2606900.625 | 2.525673 | P1 native counter plus split microbench before new AVX/layout code |
| cmux_from_dft | 0.358366 | 9309145.000 | 573440 | 4224633.590 | 1.558521 | P2 only with a new mechanism; prior direct-add alone was neutral |
| cmux_sub | 0.002268 | 58925.000 | 573440 | 6569246.830 | 1.002273 | low unless a paired schedule fusion changes its share |
| ncmux_total | 0.017172 | 446063.000 | 5080 | 6471116.215 | 1.017472 | low priority after dual-sub unless profile changes |
| sub_a_total | 0.024975 | 648760.000 | 39 | 6419739.861 | 1.025615 | defer unless a combined schedule variant can move full SAB |
| outside_rgsw_tail | 0.025648 | 666244.000 | n/a | 6415308.708 | 1.026323 | defer while share is small |

## Algorithm Frontier

| candidate_id | priority | status | algorithm_delta | next_gate |
| --- | --- | --- | --- | --- |
| S284-A-current-selected-exact | P0 | local_positive_pending_native | Keep current exact dense backend_sub_decomp_dual path. | Rerun Stage283 on authenticated native target. |
| S284-B-mat-ep-split-avx | P1 | admitted_but_no_hot_path_edit_without_counter_or_split_gate | Reduce MAT EP/sub-decomposition cost without changing selector semantics. | Native counter plus split microbench, then full SAB A/B. |
| S284-C-from-dft-lifecycle | P2 | conditional_new_mechanism_required | Shorten from_DFT/materialization lifetime around CMUX output. | New alias-safe lifecycle design before implementation. |
| S284-D-body-linear-selector-format | P3 | research_route_blocked_for_hot_path | Change selector/key format toward body-linear or compact terms. | Separate distribution/security and noise proof before hot-path code. |
| S284-E-tail-and-sub-a | P4 | deferred | Optimize sub_a/NCMUX/extract residuals. | Reopen only after a new profile shows larger share. |

## Claim Boundary

| claim | status | allowed_wording | forbidden_wording |
| --- | --- | --- | --- |
| current_speedup_dimension | allowed | Speedup is measured as complete SAB T_bootstrap/r, i.e. per processed plaintext lane/bit. | Speedup is raw total time for one r-body ciphertext without amortization. |
| current_candidate_promotion | local_only | The selected candidate is locally repeated-positive and passes local proxy noise/resource. | The candidate is native/paper-grade proven. |
| theoretical_optimality | blocked | The lower-bound gap and admissible body-linear route remain open. | The current exact dense MAT AVX512 path is theoretically optimal. |
| component_projection | projection_only | Amdahl rows prioritize next gates; they are not measured speedups. | A zero-component projection is an achievable implementation result. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_inputs | PASS | required inputs | all present | Stage284 must be derived from current measured evidence. |
| G2_primary_metric | PASS | endpoint | T_bootstrap/r | This stage preserves the r-body per-lane comparison requested for MAT-RLWE SAB. |
| G3_local_repeated_candidate | PASS | candidate/control speedup | mean=1.072081; conservative=1.063396 | Local repeated speed is positive but remains platform-scoped. |
| G4_residual_frontier | PASS | selected candidate MAT EP share | 0.604066 | Next code work must target measured residual share, not an abstract bottleneck. |
| G5_native_boundary | PASS_BOUNDARY_RECORDED | native access | failed | No native/paper-grade target claim is allowed while access is missing. |
| G6_decision | PASS_STAGE284_FRONTIER_GAP_LEDGER_READY_NATIVE_OR_MAT_EP_SPLIT_NEXT | stage decision | PASS_STAGE284_FRONTIER_GAP_LEDGER_READY_NATIVE_OR_MAT_EP_SPLIT_NEXT | Proceed to native rerun or MAT EP split/counter gate; do not claim optimality. |

## Next Queue

| priority | route | entry_condition | gate | failure_action |
| --- | --- | --- | --- | --- |
| P0 | stage285_native_target_rerun | Stage283 native access missing | Rerun selected candidate and fast control on native target with T_bootstrap/r. | Keep all target performance and counter claims local/proxy only. |
| P1 | stage286_mat_ep_split_counter_gate | MAT EP remains largest selected-candidate profile share. | Split MAT EP into decompose/DFT/FMA/load-store attribution and require full SAB A/B before promotion. | Do not edit hot path; record as counter/proxy-only. |
| P2 | stage287_from_dft_lifecycle_design | from_DFT share remains high after selected candidate. | Alias-safe lifecycle design, isolated equivalence, then repeated T_bootstrap/r. | Reject if repeated full SAB is neutral. |
| P3 | stage288_body_linear_selector_proof | pursue theoretical optimum beyond exact dense format. | Distribution/security/noise proof for a new selector/key format before any hot-path code. | Keep dense exact path as scoped engineering route. |

Generated from head `cdfb5bc`.
