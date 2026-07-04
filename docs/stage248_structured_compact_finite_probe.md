# Stage248 Structured Compact Finite Probe

Decision: `PASS_STAGE248_STRUCTURED_COMPACT_FINITE_ALGEBRA_PASS_SECURITY_BLOCKED`.

Stage248 tests the Stage246 structured-compact proof-prototype route in a
finite r=2 model. The compact model omits exactly the two body-to-body off-lane
terms that Stage166 identified as missing from a shared-output compact
representation.

## Model

```text
state = [mask, body0, body1]
missing compact terms = body0 -> body1 and body1 -> body0
structured selector condition = both missing terms are zero
```

For structured off-lane-zero selectors, dense reference and compact application
must match. For random dense selectors and a single nonzero off-lane term, they
must differ.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_inputs | PASS | required inputs | all present | repro/stage248_structured_compact_finite_probe/input_status.csv | Stage248 starts from Stage246 admission and prior compact counterexamples. |
| G2_structured_algebra_positive | PASS | structured off-lane-zero mismatches | 0 for all seeds | repro/stage248_structured_compact_finite_probe/structured_matrix_probe.csv | Compact omission is algebraically exact for the constrained off-lane-zero class. |
| G3_negative_controls | PASS_COUNTEREXAMPLES | random/single-offlane dense mismatches | positive mismatches | repro/stage248_structured_compact_finite_probe/structured_matrix_probe.csv | The probe still rejects generic dense selectors and single off-lane nonzero terms. |
| G4_toy_noise | PASS_TOY_ONLY | toy bound equivalence/counterexample | structured equal; random dense differs | repro/stage248_structured_compact_finite_probe/toy_noise_probe.csv | Toy noise follows algebraic structure only; ring-level SAB noise remains open. |
| G5_security_boundary | PASS_SECURITY_BLOCKED_RECORDED | production permissions | all no | repro/stage248_structured_compact_finite_probe/security_gap_matrix.csv | Algebra pass does not permit production compact SAB implementation. |
| G6_stage248_decision | PASS_STAGE248_STRUCTURED_COMPACT_FINITE_ALGEBRA_PASS_SECURITY_BLOCKED | decision | PASS_STAGE248_STRUCTURED_COMPACT_FINITE_ALGEBRA_PASS_SECURITY_BLOCKED | repro/stage248_structured_compact_finite_probe/proof_gate.csv | Proceed to distribution/security preflight; no hot-path SAB edits yet. |


## Resource Model

| row_id | r | state_size | dense_terms | compact_terms_if_offlane_zero | removed_terms | dense_over_compact | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| term_count | 2 | 3 | 9 | 7 | 2 | 1.285714 | Term saving is algebraic only; it is not a complete-SAB speedup or security proof. |
| claim_boundary | 2 | 3 | 9 | 7 | 2 | 1.285714 | Any real value must survive keygen/security/noise and full-SAB T_bootstrap/r gates. |


## Security Gaps

| gap_id | topic | current_status | gap | required_next_evidence | production_permission |
| --- | --- | --- | --- | --- | --- |
| SEC248-1 | selector_distribution | blocked | Off-lane-zero public pattern may distinguish the structured selector distribution. | hybrid or simulation argument, or dummy/padding scheme with semantic-zero proof | no |
| SEC248-2 | keygen_security | blocked | No proof that constrained selector/keygen preserves the original security assumptions. | formal key distribution and reduction/simulation argument | no |
| SEC248-3 | noise_recurrence | toy_only | Toy coefficient bound equality is not a ring-LWE noise proof under SAB rotations and CMUX schedule. | ring-level noise recurrence plus multi-seed full-SAB noise if implemented | no |
| SEC248-4 | complete_sab_value | unmeasured | Term-count reduction is not complete-SAB T_bootstrap/r improvement. | after proof gates, implement behind flag and run same-backend complete-SAB A/B | no |


## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage249_structured_compact_distribution_security_preflight | Stage248 algebra and toy noise pass but security/public-pattern gates are blocked. | formal selector distribution, public-pattern hiding or dummy semantic-zero padding, keygen security argument | selected_next | freeze structured compact route before production implementation | repro/stage248_structured_compact_finite_probe/security_gap_matrix.csv |
| P1 | stage250_exact_dense_lower_bound_gap_refresh | Optimality wording remains desired. | lower-bound gap model tied to counters/assembly | analysis_gate | state measured engineering improvement only | theory_checks/mat_rlwe_sab_amortized_optimality.md |
| P2 | stage251_nonbinary_selector_semantics_preflight | Non-binary PVW-SAB claim is needed. | ternary/include-zero selector semantics and staged equivalence | blocked_until_design | keep non-binary PVW unsupported | repro/stage229_parameter_generalization_matrix/coverage_gaps.csv |


## Inputs

| input_id | path | status | bytes |
| --- | --- | --- | --- |
| stage246_proof_gate | repro/stage246_broader_algorithm_admission_gate/proof_gate.csv | present | 1750 |
| stage246_experiment_gate | repro/stage246_broader_algorithm_admission_gate/experiment_gate_matrix.csv | present | 1523 |
| stage166_counterexamples | repro/stage166_shared_output_compact_algebra_gate/finite_field_counterexamples.csv | present | 4364 |
| stage166_term_model | repro/stage166_shared_output_compact_algebra_gate/term_model.csv | present | 571 |
| stage202_semantic_probe | repro/stage202_dummy_padding_semantic_probe/summary.csv | present | 1488 |


Generated from head `74aaee0`. Raw structured probe rows are in
`repro/stage248_structured_compact_finite_probe/structured_matrix_probe.csv` and toy noise rows are in `repro/stage248_structured_compact_finite_probe/toy_noise_probe.csv`.
