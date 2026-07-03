# Stage113 r=2 Selector Simulator

Date: 2026-07-03

## Decision

`PASS_STAGE113_R2_LANE_LOCAL_SIM_PHASE_EQUIV_RESOURCE_REQUIRED`

Stage113 runs an algebraic r=2 simulator. It rejects current-format
loop-only off-lane skipping again and shows that a lane-local multimask
new-format candidate can match dense phases in the toy model.

## Gates

| gate | status | metric | value | detail |
|---|---|---|---|---|
| stage113_dense_reference | PASS | dense_phase_equiv | True | Dense reference matches expected r=2 phases. |
| stage113_current_format_drop_offlane | PASS_REJECTED | counterexample | True | Current-format loop-only skipping is rejected. |
| stage113_lane_local_candidate | PASS_PHASE_EQUIV | r2_phase_equiv | True | Lane-local multimask candidate matches dense phases in the r=2 algebraic model. |
| stage113_decision | PASS_STAGE113_R2_LANE_LOCAL_SIM_PHASE_EQUIV_RESOURCE_REQUIRED | next_gate_policy |  | The candidate is phase-plausible but changes ciphertext/key resources. |

## Phase Simulation

| variant | status | phase0 | expected0 | phase1 | expected1 | interpretation |
|---|---|---:|---:|---:|---:|---|
| dense_shared_mask_reference | PASS | 73 | 73 | 121 | 121 | Dense shared-mask row-output products match the expected phases. |
| loop_only_drop_offlane_current_format | FAIL_COUNTEREXAMPLE | -362 | 73 | -224 | 121 | Skipping off-lane bodies while retaining shared masks breaks both lane phases. |
| lane_local_multimask_candidate | PASS_PHASE_EQUIV | 73 | 73 | 121 | 121 | Lane-local masks allow skipping off-lane body rows in this r=2 algebraic model. |

## Product Model

| model | r | products | products/lane | warning |
|---|---:|---:|---:|---|
| current_dense_shared_mask | 2 | 9 | 4.500 | Current valid baseline. |
| lane_local_multimask_target | 2 | 5 | 2.500 | Requires separate lane-local mask/key resource model. |
| raw_product_ratio_dense_over_lane_local | 2 | 1.800 | 1.800 | Arithmetic ratio only; not a complete-SAB speedup claim. |