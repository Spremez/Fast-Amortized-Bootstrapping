# Stage202 Dummy Padding Semantic Probe

Decision: `PASS_STAGE202_DUMMY_PADDING_SEMANTIC_PROBE_PROOF_ONLY`.

Stage202 narrows the dummy padding proof route. It does not authorize compact
SAB production code.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage202_inputs | PASS | required_inputs_present | 1 | repro/stage201_structured_selector_distribution_probe/summary.csv; repro/stage201_structured_selector_distribution_probe/proof_gate.csv | Stage202 consumes Stage201 public-pattern proof route and Stage200 counterexamples. | Repair missing inputs before using this probe. |
| stage202_semantic_probe | PASS | semantic_failures | 0 | repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv | Finite toy semantics pass for zero-semantic dummy rows and reject random-semantic/dense-general controls. | Do not generalize beyond the toy active set. |
| stage202_resource_gate | WEAK_PUBLIC_SIZE | public_row_saving_vs_dense | 0 | repro/stage202_dummy_padding_semantic_probe/resource_model.csv | Dummy padding retains dense public row count, so key-size value is not demonstrated. | Require complete-SAB value proof before any implementation path. |
| stage202_proof_gate | PROOF_ONLY | blocked_or_weak_gates | 2 | repro/stage202_dummy_padding_semantic_probe/proof_gate.csv | Production selector equations, security/noise, and complete-SAB gates remain missing. | Proceed only with production selector equation probe or new exact mechanism. |
| stage202_decision | PASS_STAGE202_DUMMY_PADDING_SEMANTIC_PROBE_PROOF_ONLY | goal_status | active | repro/stage202_dummy_padding_semantic_probe/summary.csv | Dummy padding semantic route is narrowed to toy proof-only; full goal remains active. | Do not implement compact SAB; continue only through P0/P1/P2. |

## Assumptions

| assumption_id | statement | scope | evidence | falsification |
| --- | --- | --- | --- | --- |
| A1_count_matched_toy | The finite model uses a count-matched active set with 4r semantic rows inside the dense (r+1)^2 shape. | toy functional probe only | repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv | A production selector proof must replace the toy active set with real keygen equations. |
| A2_dummy_rows_public_shape | Dummy padding keeps the dense public row shape but assigns semantic zero to inactive rows. | Stage201 surviving public-pattern route | repro/stage201_structured_selector_distribution_probe/candidate_matrix.csv | If dummy rows carry random semantics, the finite model must mismatch the structured reference. |
| A3_no_code_permission | Finite semantic equivalence is not a production keygen, noise, security, or complete-SAB gate. | claim policy | repro/stage202_dummy_padding_semantic_probe/proof_gate.csv | Production code requires real keygen/noise and complete-SAB evidence. |

## Resource Model

| r | dense_public_rows_per_T | active_semantic_rows_per_T | inactive_dummy_rows_per_T | public_row_saving_vs_dense | semantic_active_fraction | semantic_skip_potential | interpretation | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 9 | 8 | 1 | 0 | 0.888888889 | 0.111111111 | Dummy padding preserves dense public size; any speed value requires evaluator-side semantic skipping plus proof. | repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv |
| 4 | 25 | 16 | 9 | 0 | 0.640000000 | 0.360000000 | Dummy padding preserves dense public size; any speed value requires evaluator-side semantic skipping plus proof. | repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv |
| 6 | 49 | 24 | 25 | 0 | 0.489795918 | 0.510204082 | Dummy padding preserves dense public size; any speed value requires evaluator-side semantic skipping plus proof. | repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv |

## Proof Gates

| gate | status | evidence | detail | missing_before_code |
| --- | --- | --- | --- | --- |
| T2_toy_semantic_equivalence | PASS_TOY_ONLY | repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv | dummy zero semantic failures=0 | Replace toy active set with production selector/keygen equations. |
| T2_negative_control_random_dummy | PASS_COUNTEREXAMPLE | repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv | random dummy counterexample failures=0 | Prove dummy public rows encrypt semantic zero and cannot carry arbitrary semantic terms. |
| T2_negative_control_dense_general | PASS_COUNTEREXAMPLE | repro/stage202_dummy_padding_semantic_probe/semantic_probe.csv | dense general counterexample failures=0 | Declare a new structured distribution; do not claim dense-equivalence. |
| T3_resource_value | WEAK_PUBLIC_SIZE | repro/stage202_dummy_padding_semantic_probe/resource_model.csv | dummy padding has zero public-row saving versus dense | Show complete-SAB T_bootstrap/r value after semantic skipping and key materialization costs. |
| T4_noise_keygen_security | BLOCKED | repro/stage201_structured_selector_distribution_probe/proof_gate.csv | production keygen/noise/security proof not supplied | Production keygen, security reduction, noise recurrence, and multi-seed gates. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | source_anchor_intake | Reviewed 2025/686 full text is supplied locally. | Map source-specific SAB claims to inspected paper anchors. | waiting_external_artifact | repro/stage196_public_source_refresh/citation_gate.csv |
| P1 | production_selector_equation_probe | A real structured selector keygen equation is specified. | Replace toy active set, prove dummy rows are semantic zero, run finite production-shaped phase/noise checks. | blocked_on_keygen_equations | repro/stage202_dummy_padding_semantic_probe/proof_gate.csv |
| P2 | new_exact_mechanism_admission | A concrete exact-path backend/addmul/DFT mechanism is supplied. | Projection, correctness, noise/resource, and complete-SAB T_bootstrap/r gates. | waiting_new_mechanism | repro/stage200_formal_gap_model_with_probe/gap_projection.csv |
