# Stage328 Active Goal Requirement Audit

Decision: `PASS_STAGE328_ACTIVE_GOAL_AUDIT_GOAL_REMAINS_ACTIVE_SELECT_HIGHSTAT_OR_FORMAL_PROOF`.

Stage328 audits the original PVW/MAT-SAB research objective against the current
worktree. The conclusion is deliberately not "goal complete": the exact dense
implementation branch has a scoped complete-SAB result, but paper-level
statistics and formal compact/optimality proof remain open.

## Summary

| decision | goal_status | supported_complete_sab_speedup | supported_samples | paper_highstat_ready | lower_bound_status | exact_dense_frontier | compact_route | selected_next |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE328_ACTIVE_GOAL_AUDIT_GOAL_REMAINS_ACTIVE_SELECT_HIGHSTAT_OR_FORMAL_PROOF | active_not_complete | 1.745361 | 5 | no | scoped_same_format | closed_current_evidence | proof_required | stage329_highstat_complete_sab_refresh_or_formal_compact_proof_checker |

## Requirement Matrix

| requirement_id | status | gap | next_action |
| --- | --- | --- | --- |
| R1_algorithm_object | PASS_SCOPED | None for current scoped exact route; compact representation remains separate. | Preserve r-body state and lane phase invariant in all future variants. |
| R2_primary_metric | PASS | No gap for current result. | Reject future reports that use kernel-only or single-lane latency as final endpoint. |
| R3_lower_bound_complexity | PASS_SCOPED_GLOBAL_OPEN | Same-format dense lower bound exists; global MAT-RLWE optimality and compact proof remain open. | Do not claim optimality; use proof obligations O1-O4 before stronger route. |
| R4_candidate_optimal_paths | PASS_ACTIVE_FRONTIER | Exact dense local route closed; formal compact selector route has no production proof. | Select high-stat confirmation for scoped result or formal compact proof branch. |
| R5_falsifiable_experiment_gates | PASS_FOR_EXECUTED_BRANCHES | Formal compact branch still needs proof-specific gates before code. | For compact route: proof -> finite equivalence -> noise/resource -> full SAB A/B. |
| R6_stats_and_repro | PARTIAL_SCOPED_ENGINEERING_ONLY | Current formal current-head complete-SAB claim has 5 samples; paper-level threshold remains >=10 samples plus resource/noise refresh. | Run Stage329 high-stat complete-SAB refresh if paper-ready performance wording is needed. |
| R7_no_theory_loop | PASS_CURRENT_LOOP | Next formal compact work must include an executable finite or production gate. | Freeze any theory route after one proof-obligation pass unless it emits a runnable checker. |
| R8_completion | NOT_COMPLETE | Open obligations: O2_selector_structure,O4_source_anchor; theoretical optimality status=NOT_PROVEN; compact status=blocked. | Keep goal active; proceed to high-stat refresh or formal compact proof. |

## Evidence Grade

| evidence_class | status | primary_value | paper_readiness | why |
| --- | --- | --- | --- | --- |
| complete_sab_timing | SUPPORTED_SCOPED | speedup=1.745361; T/r_us=6118505.950; samples=5 | needs_highstat_refresh | Complete-SAB endpoint is correct, but sample count is scoped engineering rather than paper-level high-stat. |
| isolated_microbench | NEGATIVE_ABLATION_RECORDED | selector_transpose_projected_fullsab=1.006006 | usable_as_negative_ablation | Useful to reject a candidate, not to support bootstrapping speedup. |
| lower_bound_model | SCOPED_MODEL_RECORDED | PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE_RECORDED_GOAL_ACTIVE | allowed_as_assumption-scoped_model | Same-format lower bound exists; global optimality remains open. |
| formal_compact_route | PROOF_REQUIRED | O2_selector_structure,O4_source_anchor | future_work_only | No production proof, no full SAB timing, no compact claim. |

## Proof Gates

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage106_research_loop | PASS | algorithm object and endpoint | PASS_STAGE106_RESEARCH_LOOP_FIXED_OPTIMALITY_OPEN | The research loop is framed around r-body MAT-RLWE and T_bootstrap/r. |
| G2_stage200_lower_bound | PASS_SCOPED | lower-bound model | PASS_STAGE200_FORMAL_GAP_MODEL_WITH_PROBE_RECORDED_GOAL_ACTIVE | Lower-bound evidence is scoped to same-format dense representation. |
| G3_stage327_final_claim | PASS_SCOPED | current complete-SAB claim | 1.745361 | Current implementation has scoped complete-SAB speedup evidence. |
| G4_completion_audit | GOAL_ACTIVE_NOT_COMPLETE | open gaps | O2_selector_structure,O4_source_anchor | The full active goal is not proven complete. |
| G5_stage328_decision | PASS_STAGE328_ACTIVE_GOAL_AUDIT_GOAL_REMAINS_ACTIVE_SELECT_HIGHSTAT_OR_FORMAL_PROOF | next route | stage329_highstat_or_formal_proof | Concrete next work must either strengthen the scoped result statistically or open a formal compact proof checker. |

Generated from input head `d341525`.
