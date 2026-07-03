# Stage200 Formal Gap Model with Probe

Decision: `PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE_RECORDED_GOAL_ACTIVE`.

This stage adds a scoped lower-bound/gap model and finite counterexample probes.
It is not a complete proof for every possible MAT-RLWE SAB representation.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage200_inputs | PASS | required_inputs_present | 1 | repro/stage140_closed_fullmat_attribution_gate/attribution.csv; repro/stage162_materialization_count_feasibility/summary.csv; repro/stage199_active_goal_requirement_verifier/evidence_gap_register.csv | Stage200 consumes lower-bound, materialization-count, projection, and active-goal gap evidence. | Repair missing inputs before using the model. |
| stage200_lower_bound_model | PASS_RECORDED | model_rows | 6 | repro/stage200_formal_gap_model_with_probe/lower_bound_model.csv | The model records input DFT lower bound, dense full-MAT terms, and repeated scalar comparison counts. | Do not interpret as a final proof outside the stated assumptions. |
| stage200_finite_probe | PASS | probe_failures | 0 | repro/stage200_formal_gap_model_with_probe/finite_probe.csv | Finite probes reject component omission and toy additive decomposition shortcuts. | If nonzero, inspect finite probe rows before using counterexamples. |
| stage200_counterexample_matrix | PASS_RECORDED | rejected_shortcuts | 3 | repro/stage200_formal_gap_model_with_probe/counterexample_matrix.csv | Shortcut rejections are scoped to the assumptions and do not prove all alternatives impossible. | Use proof obligations before opening compact or lazy-state production work. |
| stage200_decision | PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE_RECORDED_GOAL_ACTIVE | goal_status | active | repro/stage200_formal_gap_model_with_probe/summary.csv | The R3 formal-gap requirement is improved from partial to scoped model plus executable probes, but the full goal remains active. | Proceed only via source-anchor intake, structured selector proof, or new exact mechanism admission. |

## Assumptions

| assumption_id | statement | scope | evidence | falsification |
| --- | --- | --- | --- | --- |
| A1_state_shape | Exact full-MAT state has one shared mask component and r body components, so m=r+1 input components are present. | current exact PVW_TMLWE representation | repro/stage140_closed_fullmat_attribution_gate/attribution.csv | Find a correct production state with fewer than r+1 torus input components under the same API. |
| A2_torus_input_api | The current exact external product consumes torus-domain input before decomposition and DFT multiplication. | same-format production path | repro/stage162_materialization_count_feasibility/summary.csv | Provide a closed decomposed/DFT state that feeds the next SAB step without torus materialization. |
| A3_general_selector_coupling | For a general closed full-MAT selector, each output row may depend on every input component. | dense MAT_TRGSW_DFT model, not compact proof route | repro/stage200_formal_gap_model_with_probe/finite_probe.csv | Show structural zero constraints from key generation that safely remove a component for all inputs. |
| A4_complete_sab_metric | Any acceleration claim must be measured on complete SAB T_bootstrap/r, not only a component count. | claim policy | repro/stage199_active_goal_requirement_verifier/evidence_gap_register.csv | None; this is a reporting invariant from the active goal. |

## Lower-Bound Model

| r | T | input_components_m | mat_input_dft_lower_bound | repeated_scalar_input_dft | mat_input_dft_over_repeated | dense_mat_addmul_terms | repeated_scalar_dense_terms | dense_terms_over_repeated | interpretation | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1 | 3 | 3 | 4 | 0.750000000 | 9 | 8 | 1.125000000 | MAT shares input conversion work but pays dense row/output interactions under the closed full-MAT selector. | repro/stage140_closed_fullmat_attribution_gate/attribution.csv |
| 2 | 7 | 3 | 21 | 28 | 0.750000000 | 63 | 56 | 1.125000000 | MAT shares input conversion work but pays dense row/output interactions under the closed full-MAT selector. | repro/stage140_closed_fullmat_attribution_gate/attribution.csv |
| 4 | 1 | 5 | 5 | 8 | 0.625000000 | 25 | 16 | 1.562500000 | MAT shares input conversion work but pays dense row/output interactions under the closed full-MAT selector. | repro/stage140_closed_fullmat_attribution_gate/attribution.csv |
| 4 | 7 | 5 | 35 | 56 | 0.625000000 | 175 | 112 | 1.562500000 | MAT shares input conversion work but pays dense row/output interactions under the closed full-MAT selector. | repro/stage140_closed_fullmat_attribution_gate/attribution.csv |
| 6 | 1 | 7 | 7 | 12 | 0.583333333 | 49 | 24 | 2.041666667 | MAT shares input conversion work but pays dense row/output interactions under the closed full-MAT selector. | repro/stage140_closed_fullmat_attribution_gate/attribution.csv |
| 6 | 7 | 7 | 49 | 84 | 0.583333333 | 343 | 168 | 2.041666667 | MAT shares input conversion work but pays dense row/output interactions under the closed full-MAT selector. | repro/stage140_closed_fullmat_attribution_gate/attribution.csv |

## Counterexample Matrix

| candidate_shortcut | expected_if_valid | observed | decision | evidence |
| --- | --- | --- | --- | --- |
| drop_or_skip_any_input_component | No mismatch after omitting a component for all tested dense selectors. | omit probe failures=0; total rows=75 | REJECT_SHORTCUT | repro/stage200_formal_gap_model_with_probe/finite_probe.csv |
| same_format_lazy_decomposed_addition | Toy decomposition would commute with addition in all sampled rows. | non-additivity probe failures=0; total rows=5 | REJECT_SHORTCUT | repro/stage200_formal_gap_model_with_probe/finite_probe.csv |
| reduce_same_format_materialization_count | Observed materialization calls would exceed the same-format lower-bound model. | Stage162 records reducible_calls_without_rep_change=0 and matching 573440 count. | REJECT_SAME_FORMAT_COUNT_REDUCTION | repro/stage162_materialization_count_feasibility/summary.csv |

## Proof Obligations

| obligation_id | statement | status | evidence | needed_before_stronger_claim |
| --- | --- | --- | --- | --- |
| O1_bound_scope | State the lower bound only for exact same-format torus-input full-MAT PVW_TMLWE paths. | RECORDED | repro/stage200_formal_gap_model_with_probe/assumptions.csv; repro/stage200_formal_gap_model_with_probe/lower_bound_model.csv | Separate proof for compact, multimask, or lazy-state representations. |
| O2_selector_structure | Prove any component skipping from keygen-imposed zero structure before implementation. | OPEN | repro/stage200_formal_gap_model_with_probe/counterexample_matrix.csv | Structured selector distribution proof and production keygen/noise gates. |
| O3_complete_sab_endpoint | Convert any component-level win into complete-SAB T_bootstrap/r evidence. | RECORDED_POLICY | repro/stage199_active_goal_requirement_verifier/next_action_selector.csv | Correctness, noise/resource, repeated complete-SAB timing, and claim ledger refresh. |
| O4_source_anchor | Cite 2025/686 algorithm/proof details only after reviewed full text is available. | BLOCKED | repro/stage196_public_source_refresh/citation_gate.csv | Local full-text artifact plus source-anchor extraction. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | source_anchor_intake | Reviewed 2025/686 full text is supplied locally. | Map every source-specific algorithm/proof sentence to inspected text anchors. | waiting_external_artifact | repro/stage196_public_source_refresh/citation_gate.csv |
| P1 | structured_selector_proof_probe | A compact/shared-output selector distribution proof route is proposed. | Show keygen-imposed structure safely removes dense terms without public distribution change, then run finite and production noise gates. | proof_required | repro/stage200_formal_gap_model_with_probe/counterexample_matrix.csv |
| P2 | new_exact_mechanism_admission | A new addmul, DFT, or backend primitive mechanism is supplied. | Projection clears complete-SAB threshold and then correctness/noise/resource/full-SAB gates pass. | waiting_new_mechanism | repro/stage200_formal_gap_model_with_probe/gap_projection.csv |
