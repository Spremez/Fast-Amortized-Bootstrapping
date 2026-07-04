# Stage246 Broader Algorithm Admission Gate

Decision: `PASS_STAGE246_BROADER_ALGORITHM_GATE_RECORDED_PROOF_PROTOTYPES_ONLY`.

Stage246 takes the PVW/MAT-SAB research loop beyond the selected binary exact
dense result and classifies broader routes. It does not promote new
bootstrapping claims. Its output is an admission decision for future
implementation work.

## Candidate Algorithms

| candidate_id | name | algorithm_object | status | admission | primary_metric | key_theory_risk | required_next_gate | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V246-A | selected_binary_exact_dense_baseline | r-body MAT-RLWE exact dense PVW/MAT-SAB for selected binary parameter rows | BASELINE_SUPPORTED_SCOPED | keep_as_baseline_for_future_variants | complete-SAB T_bootstrap/r | not an optimality theorem; dense MAT can scale poorly with r | rerun full-SAB A/B if executable hot path or benchmark semantics change | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv; repro/stage245_current_head_counter_bridge/proof_gate.csv |
| V246-B | nonbinary_exact_pvw_sab | ternary/include-zero PVW/MAT-SAB exact route | BLOCKED_NO_SELECTOR_SEMANTICS | do_not_implement_hot_path | not applicable until phase invariant exists | scalar ternary branches do not imply PVW selector/key semantics | selector semantics preflight: define sign/coefficient mapping, staged phase invariant, noise/resource plan | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv |
| V246-C | generic_shared_output_compact_mat | drop dense MAT rows/off-lane terms with the existing key distribution | REJECT_GENERIC_COMPACT | rejected_as_algorithm_candidate | not admissible | finite-field counterexamples show random dense selectors are not representable by lane-local shared-output compact structure | none for generic route; replace with structured keygen design | repro/stage166_shared_output_compact_algebra_gate/summary.csv; repro/stage112_selector_format_gate/summary.csv |
| V246-D | structured_compact_keygen_noise_route | new selector/key distribution that makes compact shared-output/state exact | ADMIT_PROOF_PROTOTYPE_ONLY | allow_stage248_finite_algebra_and_toy_noise_probe | proof prototype first; later full-SAB T_bootstrap/r if admitted | new key distribution may break security/noise assumptions or fail phase equivalence | finite r=2 algebra simulator plus toy phase/noise recurrence; no production SAB edits | repro/stage166_shared_output_compact_algebra_gate/next_stage_queue.csv |
| V246-E | mat_rlwe_optimality_lower_bound_route | lower-bound and gap model for exact/compact r-body MAT-RLWE SAB | ADMIT_MODEL_AND_COUNTER_GAP_ONLY | analysis_plus_counter_refresh_only | gap(r)=A_impl(r)/A_lower(r), with A_impl=T_bootstrap/r | counter attribution does not prove lower-bound tightness | derive measurable lower-bound rows and attach native counter/assembly evidence | theory_checks/mat_rlwe_sab_amortized_optimality.md; repro/stage245_current_head_counter_bridge/claim_boundary.csv |


## Admission Decision

| candidate_id | decision | production_permission | next_action | claim_status |
| --- | --- | --- | --- | --- |
| V246-A | retain_as_baseline | already_existing_scoped_path | rerun full-SAB A/B if executable hot path or benchmark semantics change | BASELINE_SUPPORTED_SCOPED |
| V246-B | block_until_preflight | no | selector semantics preflight: define sign/coefficient mapping, staged phase invariant, noise/resource plan | BLOCKED_NO_SELECTOR_SEMANTICS |
| V246-C | reject | no | none for generic route; replace with structured keygen design | REJECT_GENERIC_COMPACT |
| V246-D | admit_proof_prototype | no_hot_path_edits | finite r=2 algebra simulator plus toy phase/noise recurrence; no production SAB edits | ADMIT_PROOF_PROTOTYPE_ONLY |
| V246-E | admit_analysis_only | no_speedup_claim | derive measurable lower-bound rows and attach native counter/assembly evidence | ADMIT_MODEL_AND_COUNTER_GAP_ONLY |


## Proof Obligations

| obligation_id | applies_to | required_statement | current_status | evidence_or_gap | failure_action |
| --- | --- | --- | --- | --- | --- |
| P246-1 | all promoted variants | For every checked SAB step and lane q, phase(body_q(acc_mat)) equals the scalar reference phase. | satisfied_only_for_selected_binary_exact_dense_tests | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv | variant cannot enter full-SAB benchmark |
| P246-2 | nonbinary_exact_pvw_sab | Define selector/key semantics for ternary/include-zero sub_a, sign, coefficient, and noise behavior. | missing | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv | keep non-binary PVW claim unsupported |
| P246-3 | generic_shared_output_compact_mat | Represent dense selector action with compact shared-output terms under current key distribution. | contradicted_by_counterexamples | repro/stage166_shared_output_compact_algebra_gate/finite_field_counterexamples.csv | reject generic compact route |
| P246-4 | structured_compact_keygen_noise_route | Prove a constrained selector/key distribution removes off-lane terms while preserving security/noise and phase equivalence. | open_proof_prototype_admitted | repro/stage166_shared_output_compact_algebra_gate/next_stage_queue.csv | do not integrate compact SAB hot path |
| P246-5 | mat_rlwe_optimality_lower_bound_route | Separate schedule, selector stream, unavoidable body work, memory traffic, and tail lower bounds. | model_open_not_proven | theory_checks/mat_rlwe_sab_amortized_optimality.md | do not claim theoretical optimality |


## Experiment Gates

| gate_id | candidate_id | experiment | baseline | metric | success | failure | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E246-1 | V246-A | full-SAB A/B after code changes | repeated scalar SAB same backend and same lane count | T_bootstrap/r, noise failures, key size, keygen, RSS | positive mean speedup with CI lower bound above 1 and no worse failure rate | speedup <= 1, correctness/noise regression, or unreported resource side cost | not_needed_until_code_delta |
| E246-2 | V246-B | non-binary selector semantics staged equivalence | scalar ternary/include-zero SAB branch | per-step phase equivalence and final-output correctness | r=1/2/4 staged phase equivalence plus full-SAB deterministic pass | any undefined selector semantics or phase mismatch | blocked_before_experiment |
| E246-3 | V246-C | generic compact exactness probe | dense MAT selector finite-field action | mismatch count | zero mismatches for required selector family | existing counterexamples remain | rejected_by_existing_counterexamples |
| E246-4 | V246-D | finite r=2 structured compact keygen/noise prototype | dense MAT finite algebra reference | phase equivalence, off-lane zero proof rows, toy noise recurrence | proof-prototype passes before production code | cannot satisfy off-lane zero/security/noise obligations | selected_next_executable_gate |
| E246-5 | V246-E | lower-bound gap table with counter/assembly rows | current exact dense implementation | A_impl/A_lower plus cycles/load/store/FMA attribution | gap terms measurable and conservative; no unsupported optimality claim | lower bound too loose or counters not tied to implementation | analysis_gate |


## Stats And Repro Gates

| check_id | topic | requirement | status | evidence |
| --- | --- | --- | --- | --- |
| S246-1 | primary endpoint | Every performance claim reports complete-SAB T_bootstrap/r and same-r scalar repeated baseline. | enforced | repro/stage240_scoped_latex_draft/claim_audit.csv |
| S246-2 | statistics | Paper-level performance promotion needs repeated runs and uncertainty; single perf-stat runs are attribution only. | enforced | repro/stage245_current_head_counter_bridge/claim_boundary.csv |
| S246-3 | ablation | Any new implementation must isolate representation, kernel, schedule, post-processing, and backend effects. | required_for_future_variants | experiments/stage246_broader_algorithm_admission_gate_plan.md |
| S246-4 | reproducibility | Each future variant must record commit, command, backend, CPU flags, seeds, raw logs, and artifact hashes. | required_for_future_variants | repro/stage246_broader_algorithm_admission_gate/reproduction_commands.md |
| S246-5 | negative results | Rejected and blocked candidates remain in the matrix and are not deleted from the research record. | enforced | repro/stage246_broader_algorithm_admission_gate/candidate_algorithm_matrix.csv |


## Claim Boundary

| claim_id | stage246_status | safe_wording | blocked_wording | evidence |
| --- | --- | --- | --- | --- |
| C1_selected_binary_throughput | ALLOW_SCOPED_REPORT | Exact dense PVW/MAT-SAB improves complete-SAB T_bootstrap/r over repeated scalar SAB on the selected binary rows. | Do not claim all-parameter speedup, non-binary support, novelty, or theoretical optimality. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C2_correctness_noise_side_condition | ALLOW_SCOPED_REPORT | The four selected binary rows have zero PVW/scalar/pair final-output failures under 20 deterministic seeds each. | Do not use sampled noise evidence as a universal correctness theorem. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C3_resource_side_costs | ALLOW_SCOPED_REPORT | Throughput gains are reported with key-size, keygen, and RSS side costs. | Do not report throughput alone as final efficiency. | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv |
| C4_novelty | SCOPED_ONLY_NOT_FINAL | The current draft can describe a scoped systems/engineering study of PVW/MAT-SAB for 2025/686-style SAB. | Do not claim first shared-mask batching, first PVW packing, or first TFHE external product. | repro/stage230_source_verified_literature_novelty_audit/novelty_risk_map.csv |
| C5_optimality | DENY | The current complexity model identifies measured lower-bound-style constraints and candidate paths, but no formal optimality theorem is complete. | Do not state theoretically optimal, universally optimal, or lower-bound tight. | repro/stage227_exact_route_claim_boundary_update/claim_matrix.csv |
| C6_broader_algorithm_admission | DENY_PRODUCTION_PROMOTION_NOW | Broader routes are separated into proof prototypes and blocked claims. | Do not claim non-binary PVW-SAB, compact PVW-SAB, all-parameter support, or theoretical optimality. | repro/stage246_broader_algorithm_admission_gate/candidate_algorithm_matrix.csv |
| C7_next_executable_gate | ALLOW_PROOF_PROTOTYPE_ONLY | The next executable route is a finite/toy structured-compact proof prototype, not SAB hot-path integration. | Do not edit production SAB for compact/non-binary support before the proof-prototype gate passes. | repro/stage246_broader_algorithm_admission_gate/next_stage_queue.csv |


## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | required input files | all present | repro/stage246_broader_algorithm_admission_gate/input_status.csv | Stage246 consumes existing selected-binary, compact, non-binary, and counter-boundary evidence. |
| G2_claim_boundary | PASS_NO_BROADER_PRODUCTION_PROMOTION | broader claims | denied for production | repro/stage246_broader_algorithm_admission_gate/active_claim_boundary.csv | Selected binary exact dense claim is preserved; broader claims stay gated. |
| G3_candidate_classification | PASS | candidate_count | 5 | repro/stage246_broader_algorithm_admission_gate/candidate_algorithm_matrix.csv | Baseline, non-binary, generic compact, structured compact, and optimality routes are separated. |
| G4_generic_compact_guard | PASS_REJECT_GENERIC_COMPACT | existing compact counterexamples | generic route rejected | repro/stage166_shared_output_compact_algebra_gate/summary.csv | Counterexamples prevent loop-only/shared-output compact hot-path implementation. |
| G5_next_executable_gate | PASS_PROOF_PROTOTYPE_SELECTED | structured compact route | finite/toy proof prototype only | repro/stage246_broader_algorithm_admission_gate/experiment_gate_matrix.csv | The next executable work is a proof prototype, not production SAB integration. |
| G6_stats_repro | PASS | stats/repro constraints | enforced | repro/stage246_broader_algorithm_admission_gate/stats_repro_gate.csv | Future speedup claims require repeated complete-SAB timing and reproducible logs. |
| G7_stage246_decision | PASS_STAGE246_BROADER_ALGORITHM_GATE_RECORDED_PROOF_PROTOTYPES_ONLY | decision | PASS_STAGE246_BROADER_ALGORITHM_GATE_RECORDED_PROOF_PROTOTYPES_ONLY | repro/stage246_broader_algorithm_admission_gate/proof_gate.csv | Proceed to Stage248 proof prototype; do not expand paper claims now. |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage248_structured_compact_keygen_finite_probe | Stage246 admits V246-D proof prototype only. | finite r=2 algebra simulator, off-lane zero constraints, toy noise recurrence, dense-reference equivalence | selected_next_executable | freeze compact route and keep exact dense as scoped contribution | repro/stage246_broader_algorithm_admission_gate/experiment_gate_matrix.csv |
| P1 | stage249_nonbinary_selector_semantics_preflight | A non-binary PVW claim is needed. | selector/key semantics for ternary/include-zero, staged phase equivalence, scalar branch preservation | blocked_until_semantics_design | keep non-binary PVW unsupported | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv |
| P2 | stage250_exact_dense_lower_bound_gap_refresh | Optimality wording is desired. | measurable lower-bound components plus native counter/assembly tie-in | analysis_gate | state measured engineering improvement only | theory_checks/mat_rlwe_sab_amortized_optimality.md |
| P3 | stage247_batchboot_monitor_rerun | Before final submission or after citation metadata changes. | official source route only | future_monitor | leave BatchBoot TODO | repro/stage244_batchboot_bibtex_monitor/remaining_todo.csv |


## Inputs

| input_id | path | status | bytes |
| --- | --- | --- | --- |
| stage240_claim_audit | repro/stage240_scoped_latex_draft/claim_audit.csv | present | 1643 |
| stage245_counter_bridge | repro/stage245_current_head_counter_bridge/proof_gate.csv | present | 1141 |
| stage229_coverage_gaps | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv | present | 1641 |
| stage229_claim_scope | repro/stage229_parameter_generalization_matrix/claim_scope.csv | present | 1783 |
| stage236_selected_binary | repro/stage236_set_2_3_4096_r4_highstat_slice/selected_binary_matrix_summary.csv | present | 899 |
| stage166_compact_gate | repro/stage166_shared_output_compact_algebra_gate/summary.csv | present | 1054 |
| stage112_selector_gate | repro/stage112_selector_format_gate/summary.csv | present | 887 |
| optimality_model | theory_checks/mat_rlwe_sab_amortized_optimality.md | present | 3177 |
| complexity_model | theory_checks/pvw_sab_complexity_model.md | present | 1802 |


Generated from head `e2b3595`.
