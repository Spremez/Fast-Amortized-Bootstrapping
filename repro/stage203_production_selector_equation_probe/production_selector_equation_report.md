# Production-Shaped Selector Equation Probe

Decision: `PASS_STAGE203_PRODUCTION_SELECTOR_EQUATION_PROBE_PROOF_ONLY`.

Stage203 declares a finite equation candidate for the dummy-padding proof route
and checks phase/noise behavior with negative controls. It remains proof-only:
no production keygen, security reduction, or complete-SAB benchmark is supplied.

## Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage203_inputs | PASS | required_inputs_present | 1 | repro/stage202_dummy_padding_semantic_probe/summary.csv; repro/stage202_dummy_padding_semantic_probe/proof_gate.csv | Stage203 consumes Stage202 dummy semantics and proof-only route state. | Repair missing inputs before using this probe. |
| stage203_equation_map | PASS_RECORDED | equation_rows | 83 | repro/stage203_production_selector_equation_probe/equation_map.csv | Declared equation v0 records dense public rows, active roles, and dummy-zero rows for r=2/4/6. | Replace with real production keygen equations before code. |
| stage203_phase_noise_probe | PASS | phase_or_negative_failures | 0 | repro/stage203_production_selector_equation_probe/phase_noise_probe.csv | Finite checks pass declared phase equivalence and reject bad dummy/missing-equation controls. | Do not generalize beyond declared equation v0. |
| stage203_proof_gate | PROOF_ONLY | blocked_or_model_only_gates | 2 | repro/stage203_production_selector_equation_probe/proof_gate.csv | Production keygen/security and complete-SAB gates remain missing. | Do not implement compact SAB. |
| stage203_decision | PASS_STAGE203_PRODUCTION_SELECTOR_EQUATION_PROBE_PROOF_ONLY | goal_status | active | repro/stage203_production_selector_equation_probe/summary.csv | Declared selector equation route is narrowed to finite proof-only evidence; full goal remains active. | Proceed only via source anchors, production keygen design, or new exact mechanism. |

## Assumptions

| assumption_id | statement | scope | evidence | falsification |
| --- | --- | --- | --- | --- |
| A1_declared_equation_v0 | The finite probe declares four active equation classes per body lane and semantic-zero dummy equations elsewhere. | finite production-shaped probe, not production keygen | repro/stage203_production_selector_equation_probe/equation_map.csv | A real selector keygen equation may have a different active set or coefficient structure. |
| A2_dummy_semantic_zero | Inactive dense-shape rows are public dummy rows but must have zero semantic contribution. | dummy padding proof route | repro/stage203_production_selector_equation_probe/phase_noise_probe.csv | Random semantic dummy rows are a negative control and must mismatch. |
| A3_noise_skip_model | Evaluator-side skipping of semantic-zero dummy rows avoids dummy noise accumulation only after a proof identifies them. | noise/resource model | repro/stage203_production_selector_equation_probe/proof_gate.csv | If dummy rows must be evaluated, noise and runtime value degrade. |

## Negative Controls

| negative_control | expected | failures | decision | evidence |
| --- | --- | --- | --- | --- |
| random_dummy_semantics | must mismatch structured-zero reference | 0 | PASS_REJECTS_BAD_DUMMY | repro/stage203_production_selector_equation_probe/phase_noise_probe.csv |
| missing_active_equation | must mismatch structured-zero reference | 0 | PASS_REJECTS_MISSING_EQUATION | repro/stage203_production_selector_equation_probe/phase_noise_probe.csv |

## Resource Projection

| r | dense_rows_per_T | active_rows_per_T | dummy_rows_per_T | public_row_saving | evaluator_row_reduction_if_skip_proven | dense_eval_noise_over_skip_mean | interpretation | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 9 | 8 | 1 | 0 | 0.111111111 | 1.041666667 | Potential evaluator work/noise reduction exists only if dummy rows are proven identifiable semantic-zero rows. | repro/stage203_production_selector_equation_probe/phase_noise_probe.csv |
| 4 | 25 | 16 | 9 | 0 | 0.360000000 | 1.187500000 | Potential evaluator work/noise reduction exists only if dummy rows are proven identifiable semantic-zero rows. | repro/stage203_production_selector_equation_probe/phase_noise_probe.csv |
| 6 | 49 | 24 | 25 | 0 | 0.510204082 | 1.347222222 | Potential evaluator work/noise reduction exists only if dummy rows are proven identifiable semantic-zero rows. | repro/stage203_production_selector_equation_probe/phase_noise_probe.csv |

## Proof Gates

| gate | status | evidence | detail | missing_before_code |
| --- | --- | --- | --- | --- |
| E1_declared_equation_phase | PASS_FINITE | repro/stage203_production_selector_equation_probe/phase_noise_probe.csv | declared equation phase failures=0 | Map declared equations to actual production selector keygen. |
| E2_negative_controls | PASS | repro/stage203_production_selector_equation_probe/negative_controls.csv | negative control failures=0 | Keep negative controls in any production-shaped proof. |
| E3_noise_resource | MODEL_ONLY | repro/stage203_production_selector_equation_probe/resource_projection.csv | dummy row skipping has modeled value but public row count remains dense | Run production noise recurrence and complete-SAB T_bootstrap/r gates. |
| E4_security_keygen | BLOCKED | repro/stage202_dummy_padding_semantic_probe/proof_gate.csv | no production keygen or security reduction is supplied | Define production keygen equations and proof that dummy rows leak nothing beyond declared distribution. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | source_anchor_intake | Reviewed 2025/686 full text is supplied locally. | Map source-specific SAB claims to inspected paper anchors. | waiting_external_artifact | repro/stage196_public_source_refresh/citation_gate.csv |
| P1 | production_keygen_equation_design | A production selector keygen design is proposed using Stage203 declared equations. | Show public distribution, semantic zero, noise recurrence, key size, and complete-SAB T_bootstrap/r value. | blocked_on_real_keygen_design | repro/stage203_production_selector_equation_probe/proof_gate.csv |
| P2 | new_exact_mechanism_admission | A concrete exact-path backend/addmul/DFT mechanism is supplied. | Projection, correctness, noise/resource, and complete-SAB T_bootstrap/r gates. | waiting_new_mechanism | repro/stage200_formal_gap_model_with_probe/gap_projection.csv |


Full equation map and phase/noise rows are recorded in `repro/stage203_production_selector_equation_probe/equation_map.csv` and `repro/stage203_production_selector_equation_probe/phase_noise_probe.csv`.
