# Active Goal Requirement Report

Decision: `PASS_STAGE199_ACTIVE_GOAL_VERIFIER_RECORDED_GOAL_ACTIVE`.

This verifier checks the active PVW/MAT-SAB research goal against current
evidence. It explicitly prevents treating the scoped paper/repro package as
full goal completion.

## Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage199_inputs | PASS | required_inputs_present | 1 | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv; repro/stage198_metadata_safe_manuscript_refresh/summary.csv | Stage199 verifies the active goal against current evidence, not intent. | Repair missing inputs before using this verifier. |
| stage199_requirement_matrix | PASS_RECORDED | requirements | 8 | repro/stage199_active_goal_requirement_verifier/requirement_matrix.csv | 5 scoped requirements satisfied; 3 remain partial or not complete. | Use gap register for next route selection. |
| stage199_fulltext_boundary | BLOCKED | target_686_fulltext_gate | BLOCKED | repro/stage196_public_source_refresh/citation_gate.csv | The source-anchor route remains outside current evidence if reviewed full text is unavailable. | Use metadata-safe writing or supply full text. |
| stage199_completion_decision | PASS_STAGE199_ACTIVE_GOAL_VERIFIER_RECORDED_GOAL_ACTIVE | goal_status | active | repro/stage199_active_goal_requirement_verifier/summary.csv | The scoped evidence chain is usable, but the full active goal is not proven complete. | Proceed to P0/P1/P2 in the next-action selector. |

## Requirement Matrix

| requirement_id | current_status | objective_requirement | evidence_strength | remaining_gap | evidence |
| --- | --- | --- | --- | --- | --- |
| R1_primary_metric | SATISFIED_SCOPED | Use complete bootstrapping time per processed plaintext bit/lane as the primary endpoint. | complete-SAB T_bootstrap/r recorded and reused in scoped writing | No gap for scoped reporting; broader parameters still need their own gates. | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv; repro/stage198_metadata_safe_manuscript_refresh/manuscript_draft.md |
| R2_algorithm_object | SATISFIED_SCOPED | Treat PVW/MAT-SAB as a MAT-RLWE/r-body ciphertext modification of SAB, not just a kernel benchmark. | support bank and draft use the r-body SAB object and complete-SAB endpoint | A final formal algorithm section still needs source-paper anchors and proof text. | repro/stage197_metadata_safe_citation_bank/sentence_support_bank.csv; repro/stage198_metadata_safe_manuscript_refresh/manuscript_draft.md |
| R3_complexity_lower_bound | PARTIAL | Give a lower-bound or gap model for the r-body MAT-RLWE SAB route. | component shares and required component speedups are recorded for exact full-MAT route selection | Formal lower-bound proof and exact proof assumptions remain incomplete. | repro/stage180_mat_ep_split_probe/derived_projection.csv |
| R4_candidate_paths | SATISFIED_FOR_CURRENT_FRONTIER | Maintain candidate algorithm paths and close or promote them by falsifiable gates. | compact, addmul, and DFT/conversion frontiers are admitted, denied, or routed with explicit conditions | No current new code candidate is open; new mechanisms need fresh admission evidence. | repro/stage192_compact_admission_route_selection/summary.csv; repro/stage193_exact_addmul_dataflow_preflight/summary.csv; repro/stage194_exact_dft_conversion_preflight/summary.csv |
| R5_experiment_gates | SATISFIED_SCOPED | Use correctness, performance, noise/resource, and reproducibility gates before any acceleration claim. | current claim ledger and writing support preserve scoped complete-SAB evidence and blocked frontiers | Any new mechanism still needs a fresh full gate sequence. | repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv; repro/stage197_metadata_safe_citation_bank/summary.csv; repro/stage198_metadata_safe_manuscript_refresh/summary.csv |
| R6_statistics | SATISFIED_SCOPED | Report effect sizes and avoid single-run or kernel-only overclaims. | recorded mean 1.131666667x, min 1.115000000x, CI-low 1.095041982x | Broader parameter/backend statistics require their own matrices before broad claims. | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv; repro/stage195_scoped_paper_repro_refresh/final_claim_ledger.csv |
| R7_literature_citation | PARTIAL_BLOCKED | Use true sources and avoid unsupported novelty or theorem-level paper statements. | metadata-safe citation policy and guarded draft exist | Reviewed 2025/686 full text is still required for theorem, equation, proof, and experiment anchors. | repro/stage196_public_source_refresh/citation_gate.csv; repro/stage197_metadata_safe_citation_bank/sentence_support_bank.csv; repro/stage198_metadata_safe_manuscript_refresh/manuscript_draft.md |
| R8_final_completion | NOT_COMPLETE | Finish the full research goal, including proof/model closure, promoted implementation evidence, literature review, and claim ledger. | this verifier records that scoped evidence is not equal to full objective completion | Formal proof closure, source-anchor review, and any stronger implementation claim remain open. | repro/stage199_active_goal_requirement_verifier/summary.csv |

## Evidence Gaps

| requirement_id | gap | needed_evidence | current_action |
| --- | --- | --- | --- |
| R3_complexity_lower_bound | Formal lower-bound proof and exact proof assumptions remain incomplete. | formal proof note with assumptions, lower-bound statement, and counterexample/falsification checks | prepare a bounded proof-obligation stage only if it includes falsifiable checks |
| R7_literature_citation | Reviewed 2025/686 full text is still required for theorem, equation, proof, and experiment anchors. | local reviewed full text path plus source-anchor extraction | wait for full-text artifact or keep metadata-safe writing |
| R8_final_completion | Formal proof closure, source-anchor review, and any stronger implementation claim remain open. | all partial rows upgraded with direct evidence and no remaining blocked stronger claims | keep goal active |

## Next Action Selector

| priority | route | entry_condition | why_this_moves_goal | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | source_anchor_intake | Reviewed 2025/686 full text is available as a local artifact. | It upgrades metadata-only baseline use to theorem/algorithm/experiment anchor support. | Every source-specific sentence maps to an inspected text anchor. | waiting_external_artifact | repro/stage196_public_source_refresh/citation_gate.csv |
| P1 | formal_gap_model_with_falsification | No new implementation mechanism is available, but a proof stage must include checkable assumptions and counterexamples. | It targets the remaining formal lower-bound/gap-model requirement instead of writing more prose. | Assumption table, proof obligation table, and at least one executable finite counterexample/consistency probe. | candidate_next_research_stage | repro/stage199_active_goal_requirement_verifier/evidence_gap_register.csv |
| P2 | new_mechanism_admission | A concrete addmul, DFT/conversion, compact proof, or backend mechanism is supplied. | It can reopen implementation progress only if projected complete-SAB impact is measurable. | Correctness, noise/resource, complete-SAB T_bootstrap/r, and claim-policy gates. | waiting_new_mechanism | repro/stage193_exact_addmul_dataflow_preflight/summary.csv; repro/stage194_exact_dft_conversion_preflight/summary.csv |
