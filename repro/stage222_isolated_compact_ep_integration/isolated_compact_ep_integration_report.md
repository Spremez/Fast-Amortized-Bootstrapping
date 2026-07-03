# Stage222 Isolated Compact EP Integration

Decision: `PASS_STAGE222_ISOLATED_COMPACT_EP_SUBCLASS_OK_COMPLETE_SELECTOR_DENIED`.

Stage222 links the current MOSFHET production compact EP API and verifies its
lane-local arithmetic against a coefficient-domain oracle. The same probe adds
cross-body references as a negative control. This separates a valid compact
subclass from the full 2025/686 SAB selector requirement.

The result is intentionally restrictive: lane-local compact EP is correct, but
the complete selector remains denied because Stage203 contains active neighbor
body equations and Stage139 already showed the direct compact output is not a
closed PVW_TMLWE state.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage222_isolated_compact_ep_integration/input_status.csv | Stage222 consumes Stage221 permission plus Stage203/Stage139/Stage166 boundaries. |
| G2_mosfhet_static_build | PASS | make_static_spqlios | true | repro/stage222_isolated_compact_ep_integration/mosfhet_static_build.log | Probe links against current MOSFHET production compact EP code. |
| G3_probe_compile_run | PASS | compile_ok;run_ok | true;true | repro/stage222_isolated_compact_ep_integration/compile_probe.log; repro/stage222_isolated_compact_ep_integration/run_probe.log | Standalone isolated compact EP probe compiles and runs. |
| G4_lane_local_subclass_correctness | PASS | api_rows;min_cross_body_negative_mismatches | 12;1024 | repro/stage222_isolated_compact_ep_integration/api_results.csv | Current compact EP matches a lane-local oracle and rejects cross-body references. |
| G5_complete_selector_expressiveness | DENY_COMPLETE_SELECTOR_INTEGRATION | stage203_neighbor_rows | 2;4;6 | repro/stage222_isolated_compact_ep_integration/expressiveness_results.csv | Stage203/686 active neighbor equations are outside the current lane-local compact output shape. |
| G6_sab_admission | DENY_SAB_HOTPATH_CODE | missing_before_sab_code | closed_state;neighbor_equation_support;complete_sab_gate | repro/stage222_isolated_compact_ep_integration/proof_gate.csv | Stage222 does not authorize compact EP integration into SAB. |
| G7_stage222_decision | PASS_STAGE222_ISOLATED_COMPACT_EP_SUBCLASS_OK_COMPLETE_SELECTOR_DENIED | decision | PASS_STAGE222_ISOLATED_COMPACT_EP_SUBCLASS_OK_COMPLETE_SELECTOR_DENIED | repro/stage222_isolated_compact_ep_integration/proof_gate.csv | Lane-local compact EP is production-code correct, but complete selector integration is denied. |

## API Results

| backend | r | N | T | Bg_bit | seed | lane_local_component_mismatches | lane_local_phase_mismatches | cross_body_negative_mismatches | max_component_gap | max_phase_gap | max_negative_gap | tolerance | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spqlios | 2 | 512 | 7 | 7 | 0 | 0 | 0 | 1024 | 1068 | 1068 | 18355581447927914460 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 2 | 512 | 7 | 7 | 1 | 0 | 0 | 1024 | 1196 | 1196 | 18422021017524774084 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 2 | 1024 | 7 | 7 | 0 | 0 | 0 | 2048 | 2064 | 2064 | 18398706910616672702 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 2 | 1024 | 7 | 7 | 1 | 0 | 0 | 2048 | 2284 | 2284 | 18328825061032961136 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 4 | 512 | 7 | 7 | 0 | 0 | 0 | 2048 | 1182 | 1128 | 18435328825213795876 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 4 | 512 | 7 | 7 | 1 | 0 | 0 | 2048 | 1294 | 1026 | 18382022420825016916 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 0 | 0 | 4096 | 2452 | 2452 | 18332069718303074352 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 4 | 1024 | 7 | 7 | 1 | 0 | 0 | 4096 | 2576 | 2576 | 18403287289459706564 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 6 | 512 | 7 | 7 | 0 | 0 | 0 | 3072 | 1713 | 1713 | 18393178324805901210 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 6 | 512 | 7 | 7 | 1 | 0 | 0 | 3072 | 1552 | 1552 | 18432605115559727665 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 0 | 0 | 6144 | 2604 | 2604 | 18425245346489215836 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |
| spqlios | 6 | 1024 | 7 | 7 | 1 | 0 | 0 | 6144 | 2592 | 2256 | 18388516007918480690 | 131072 | PASS_LANE_LOCAL_COMPACT_EP_AND_REJECTS_CROSS_BODY |

## Expressiveness Boundary

| r | stage203_neighbor_active_rows | generic_missing_cross_terms | current_kernel_consumes_body_lanes | current_kernel_outputs_body_lanes | complete_selector_status | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 2 | 2 | same-index body lane only | same-index body lane only | DENY_COMPLETE_SELECTOR_INTEGRATION | Stage203 active neighbor rows are outside the current lane-local compact EP state shape. |
| 4 | 4 | 12 | same-index body lane only | same-index body lane only | DENY_COMPLETE_SELECTOR_INTEGRATION | Stage203 active neighbor rows are outside the current lane-local compact EP state shape. |
| 6 | 6 | 30 | same-index body lane only | same-index body lane only | DENY_COMPLETE_SELECTOR_INTEGRATION | Stage203 active neighbor rows are outside the current lane-local compact EP state shape. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage223_compact_route_closeout_or_new_state_design | Stage222 confirms lane-local correctness but complete selector denial. | Choose either a new closed lane-pair/neighbor-capable compact state or return to exact PVW/MAT-SAB optimization. | selected | No compact SAB hot-path code. | repro/stage222_isolated_compact_ep_integration/proof_gate.csv |
| P1 | stage223_exact_pvw_mat_avx_resource_refresh | Compact complete-selector route remains denied. | Continue optimizing valid closed dense MAT path under T_bootstrap/r. | parallel_candidate | Keep previous exact PVW/MAT evidence only. | repro/stage139_compact_closure_audit/summary.csv |
| P2 | no_complete_sab_claim | Any compact state proof is missing. | Report compact route as isolated/subclass only. | fallback | Do not claim compact SAB acceleration. | repro/stage222_isolated_compact_ep_integration/expressiveness_results.csv |
