# Stage189 Closed-State Linear Probe

Decision: `PASS_STAGE189_T2_PUBLIC_CLOSURE_PROBE_DIRECT_SHARED_MASK_REJECTED`.

Stage189 targets the Stage187 `T2_closed_state` obligation with an executable
finite linear-algebra probe. It asks one narrow question:

```text
Can r lane-local compact output masks be publicly projected to one shared
PVW_TMLWE mask while preserving every lane phase, without secret-dependent
correction and without dense re-expansion?
```

The answer is no for the tested r>1 finite systems. The r=1 control passes.
This does not prove every possible compact construction impossible; it rejects
the direct public projection route for the current lane-pair output shape.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage189_inputs | PASS | required_inputs_present | 1 | repro/stage133_lane_state_closure_audit/closure_matrix.csv; repro/stage139_compact_closure_audit/closure.csv; repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv | Stage189 targets T2 using prior lane-pair and nonclosure evidence. | Repair missing inputs before interpreting the probe. |
| stage189_linear_probe | PASS | inconsistent_public_projection_rows_r_gt_1 | 6 | repro/stage189_closed_state_linear_probe/rank_probe.csv | Public one-shared-mask projection is consistent for r=1 control and inconsistent for r>1 finite probes. | Reject direct public closure if no unexpected row exists. |
| stage189_conversion_routes | RECORDED | routes | 5 | repro/stage189_closed_state_linear_probe/conversion_cost_model.csv | Remaining T2 routes require multimask state, secret correction/key switching, dense re-expansion, or a new structured selector proof. | Do not write production compact SAB code. |
| stage189_decision | PASS_STAGE189_T2_PUBLIC_CLOSURE_PROBE_DIRECT_SHARED_MASK_REJECTED | production_compact_sab_permission | 0 | repro/stage189_closed_state_linear_probe/route_decision.csv | Stage189 closes the direct public shared-mask closure route, but does not close T1/T4. | Run isolated T1 distribution or T4 secret-correction/noise probe. |

## Rank Probe

| probe | field | r | N | unknowns | constraints | rank_A | rank_aug | secret_rank_min | consistent | expected | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| public_shared_mask_projection | GF(65537) | 1 | 4 | 16 | 16 | 16 | 16 | 4 | yes | consistent_only_for_r1 | PASS_R1_CONTROL |
| lane_pair_identity_state | GF(65537) | 1 | 4 | 16 | 16 | 16 | 16 | 4 | yes | always_consistent_but_not_one_shared_mask | PASS_INTERNAL_MULTIMASK_STATE |
| public_shared_mask_projection | GF(65537) | 1 | 8 | 64 | 64 | 64 | 64 | 8 | yes | consistent_only_for_r1 | PASS_R1_CONTROL |
| lane_pair_identity_state | GF(65537) | 1 | 8 | 64 | 64 | 64 | 64 | 8 | yes | always_consistent_but_not_one_shared_mask | PASS_INTERNAL_MULTIMASK_STATE |
| public_shared_mask_projection | GF(65537) | 2 | 4 | 32 | 64 | 32 | 33 | 4 | no | consistent_only_for_r1 | EXPECTED_INCONSISTENT |
| lane_pair_identity_state | GF(65537) | 2 | 4 | 64 | 64 | 64 | 64 | 4 | yes | always_consistent_but_not_one_shared_mask | PASS_INTERNAL_MULTIMASK_STATE |
| public_shared_mask_projection | GF(65537) | 2 | 8 | 128 | 256 | 128 | 129 | 8 | no | consistent_only_for_r1 | EXPECTED_INCONSISTENT |
| lane_pair_identity_state | GF(65537) | 2 | 8 | 256 | 256 | 256 | 256 | 8 | yes | always_consistent_but_not_one_shared_mask | PASS_INTERNAL_MULTIMASK_STATE |
| public_shared_mask_projection | GF(65537) | 4 | 4 | 64 | 256 | 64 | 65 | 4 | no | consistent_only_for_r1 | EXPECTED_INCONSISTENT |
| lane_pair_identity_state | GF(65537) | 4 | 4 | 256 | 256 | 256 | 256 | 4 | yes | always_consistent_but_not_one_shared_mask | PASS_INTERNAL_MULTIMASK_STATE |
| public_shared_mask_projection | GF(65537) | 4 | 8 | 256 | 1024 | 256 | 257 | 8 | no | consistent_only_for_r1 | EXPECTED_INCONSISTENT |
| lane_pair_identity_state | GF(65537) | 4 | 8 | 1024 | 1024 | 1024 | 1024 | 8 | yes | always_consistent_but_not_one_shared_mask | PASS_INTERNAL_MULTIMASK_STATE |
| public_shared_mask_projection | GF(65537) | 6 | 4 | 96 | 576 | 96 | 97 | 4 | no | consistent_only_for_r1 | EXPECTED_INCONSISTENT |
| lane_pair_identity_state | GF(65537) | 6 | 4 | 576 | 576 | 576 | 576 | 4 | yes | always_consistent_but_not_one_shared_mask | PASS_INTERNAL_MULTIMASK_STATE |
| public_shared_mask_projection | GF(65537) | 6 | 8 | 384 | 2304 | 384 | 385 | 8 | no | consistent_only_for_r1 | EXPECTED_INCONSISTENT |
| lane_pair_identity_state | GF(65537) | 6 | 8 | 2304 | 2304 | 2304 | 2304 | 8 | yes | always_consistent_but_not_one_shared_mask | PASS_INTERNAL_MULTIMASK_STATE |

## Conversion Routes

| route | t2_result | extra_state | secret_dependent_work | performance_status | evidence | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| direct_public_projection_to_one_shared_mask | REJECTED | one shared mask only | none | no production benchmark because algebra gate fails | repro/stage189_closed_state_linear_probe/rank_probe.csv | Do not implement this route. |
| keep_lane_pair_or_multimask_state | CLOSED_AS_INTERNAL_STATE_NOT_STANDARD_PVW | r masks plus r bodies instead of one mask plus r bodies | none | Stage134 generalized input full signal 0.910791;1.101122 | repro/stage133_lane_state_closure_audit/closure_matrix.csv; repro/stage134_generalized_lane_pair_input_ep_gate/summary.csv | Only revisit if a decompose/DFT reuse mechanism changes Stage134 economics. |
| secret_correction_or_keyswitch_to_shared_mask | ALGEBRAICALLY_POSSIBLE_BUT_NOT_PUBLIC | one shared mask after correction | body_q += (a_shared - a_q) * s_q or equivalent key switch | unmeasured; must include noise/key/materialization overhead | repro/stage176_structured_compact_security_api_gate/api_options.csv | Requires T1/T4 security-noise proof before any SAB code. |
| dense_full_mat_reexpansion | CLOSED_REFERENCE | standard PVW_TMLWE | covered by existing dense encrypted selector rows | implemented exact full-MAT path; not compact | repro/stage176_structured_compact_security_api_gate/api_options.csv | Keep as current exact baseline, not a compact proof route. |
| new_structured_equal_mask_selector | OPEN_PROOF_ROUTE | one shared mask if selector distribution forces equal output masks | depends on new key distribution/proof | no implementation permission | repro/stage187_compact_proof_obligation_draft/theorem_matrix.csv; repro/stage176_structured_compact_security_api_gate/api_options.csv | Target T1 key-distribution proof before code. |

## Route Decision

| decision | status | reason | allowed_next |
| --- | --- | --- | --- |
| direct_public_shared_mask_closure | DENY | finite linear system is inconsistent for r>1 under full-rank monomial secret multiplication | none |
| production_compact_sab_code | DENY | T2 direct closure is rejected and T1/T4 remain unproven for secret-correction or structured selector routes | isolated T1 distribution probe or T4 noise/key-switch probe |
| lane_pair_multimask_route | DEFER | algebraically closed as internal state but Stage134 performance is neutral/negative for r=4/r=6 unless decompose/DFT economics change | only a new decompose/DFT reuse mechanism with projected complete-SAB impact |
| paper_claim | SCOPED_ONLY | Stage189 strengthens a negative/blocked T2 boundary; it does not implement compact SAB | state as limitation or proof obligation, not as speedup |
