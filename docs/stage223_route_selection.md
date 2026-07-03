# Stage223 Route Selection

Decision: `PASS_STAGE223_ROUTE_EXACT_PVW_MAT_REFRESH_SELECTED_COMPACT_COMPLETE_DENIED`.

Stage223 closes the current compact-production route for complete SAB: the
lane-local compact EP subclass remains valid, but Stage222 denies complete
selector integration. The executable mainline is therefore the already valid
closed dense MAT/PVW path, measured by `T_bootstrap/r`.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage223_route_selection/input_status.csv | Stage223 route selection consumes compact denial and exact full-SAB evidence. |
| G2_compact_complete_route | DENY_COMPACT_COMPLETE_SAB_ROUTE | stage222_complete_selector | DENY_COMPLETE_SELECTOR_INTEGRATION | repro/stage223_route_selection/evidence_summary.csv | Current compact route cannot be connected to SAB without a new closed state/proof. |
| G3_exact_mat_route | SELECT_EXACT_PVW_MAT_MAINLINE | best_current_complete_sab_speedup_per_lane | 1.432667 | repro/stage223_route_selection/route_matrix.csv | The valid executable route is exact closed dense MAT/PVW optimization under T_bootstrap/r. |
| G4_claim_boundary | PASS_ENGINEERING_SCOPE_ONLY | paper_claim_boundary | no_theoretical_optimality;no_compact_complete_sab_claim | docs/stage223_route_selection.md | Stage223 prevents unsupported compact algorithm or optimality claims. |
| G5_stage223_decision | PASS_STAGE223_ROUTE_EXACT_PVW_MAT_REFRESH_SELECTED_COMPACT_COMPLETE_DENIED | decision | PASS_STAGE223_ROUTE_EXACT_PVW_MAT_REFRESH_SELECTED_COMPACT_COMPLETE_DENIED | repro/stage223_route_selection/proof_gate.csv | Proceed to exact PVW/MAT AVX/resource refresh; keep compact complete-SAB blocked. |

## Evidence Summary

| source | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| Stage222 | PASS_STAGE222_ISOLATED_COMPACT_EP_SUBCLASS_OK_COMPLETE_SELECTOR_DENIED | complete_selector_status | DENY_COMPLETE_SELECTOR_INTEGRATION | repro/stage222_isolated_compact_ep_integration/proof_gate.csv | Production compact EP is lane-local correct but cannot cover current Stage203/SAB selector. |
| Stage134 | NEUTRAL_OR_NEGATIVE | min_full_speedup_r4_r6;max_full_speedup_all | 0.910791;1.101122 | repro/stage134_generalized_lane_pair_input_ep_gate/ratio_summary.csv | Closure-capable generalized compact EP is correct but not a stable r=4/r=6 performance route. |
| Stage139/166 | COMPACT_DIRECT_ROUTE_BLOCKED | closure;generic_exactness | not_pvw_closed;cross_body_missing | repro/stage139_compact_closure_audit/summary.csv; repro/stage166_shared_output_compact_algebra_gate/summary.csv | Direct compact output and generic compact exactness are both denied without a new state/proof. |
| Stage144 | WEAK_STAGE144_PERF_POSITIVE_BUT_CI_CROSSES_ONE | r4_T_bootstrap_per_lane_speedup_vs_scalar | 1.312333 | repro/stage144_full_sab_repeated_r4_unrolled_gate/perf_comparison.csv | r=4 exact MAT/PVW full-SAB evidence is weak-positive but CI crosses one for incremental kernel change. |
| Stage148 | PASS_STAGE148_PERF_BACKEND_REPEATED_POSITIVE | r6_T_bootstrap_per_lane_speedup_vs_scalar;key_bytes_ratio;vmhwm_ratio | 1.432667;1.122537;1.030966 | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv; repro/stage148_h14_r6_repeated_refresh/summary.csv | r=6 exact MAT/PVW backend has the strongest complete-SAB T_bootstrap/r evidence so far. |

## Route Matrix

| route | status | reason | evidence | next_action |
| --- | --- | --- | --- | --- |
| compact_lane_local_current_api | KEEP_AS_ISOLATED_SUBCLASS_ONLY | Stage222 lane-local oracle passes but cross-body negative control rejects complete selector. | repro/stage222_isolated_compact_ep_integration/proof_gate.csv | Do not connect to SAB hot path. |
| new_closed_neighbor_capable_compact_state | PROOF_ONLY_HIGH_RISK | Would need a state shape that consumes/writes neighbor body equations while remaining closed and secure. | repro/stage222_isolated_compact_ep_integration/expressiveness_results.csv; repro/stage166_shared_output_compact_algebra_gate/summary.csv | Only start if explicitly choosing a new algebra/proof research branch. |
| exact_closed_dense_mat_pvw | SELECT_EXECUTABLE_MAINLINE | Already valid for complete SAB and has r=6 per-lane full-SAB speedup evidence. | repro/stage148_h14_r6_repeated_refresh/perf_comparison.csv; theory_checks/stage150_claim_scope_model.md | Run Stage224 exact PVW/MAT AVX resource refresh under T_bootstrap/r. |
| paper_claim | ENGINEERING_CLAIM_ONLY_FOR_NOW | No compact complete-SAB algorithm is admitted; theoretical optimality remains unproved. | theory_checks/stage150_claim_scope_model.md | Report exact MAT/PVW acceleration with resource/noise side conditions; keep compact as negative/blocked result. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage224_exact_pvw_mat_avx_resource_refresh | Stage223 selects exact closed dense MAT/PVW as executable mainline. | Rerun full-SAB T_bootstrap/r, AVX/backend attribution, resource/noise side conditions. | selected | Keep Stage148 as current best evidence and do not claim further gains. | repro/stage223_route_selection/proof_gate.csv |
| P1 | stage225_neighbor_capable_compact_state_proof | User explicitly chooses a new compact algebra/proof branch. | Define and falsify a closed neighbor-capable compact state before any code. | proof_only_deferred | Do not touch SAB hot path. | repro/stage222_isolated_compact_ep_integration/expressiveness_results.csv |
| P2 | paper_claim_boundary_update | After Stage224 refresh or if native platform remains unavailable. | Separate exact MAT/PVW engineering claim from blocked compact route. | future | No novelty/optimality claim. | theory_checks/stage150_claim_scope_model.md |
