# Stage201 Structured Selector Distribution Probe

Decision: `PASS_STAGE201_STRUCTURED_SELECTOR_DISTRIBUTION_PROBE_PROOF_ONLY`.

Stage201 narrows the proof-only compact/shared-output route. It does not permit
production SAB code.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage201_inputs | PASS | required_inputs_present | 1 | repro/stage190_selector_distribution_distinguisher/summary.csv; repro/stage200_formal_gap_model_with_probe/counterexample_matrix.csv | Stage201 consumes Stage190 selector distinguishers and Stage200 proof obligations. | Repair missing inputs before using this probe. |
| stage201_distribution_probe | PASS | probe_rows | 12 | repro/stage201_structured_selector_distribution_probe/distribution_probe.csv | Finite public-pattern probes cover r=2/4/6 and four selector candidates. | Use candidate matrix for routing, not production claims. |
| stage201_candidate_matrix | PASS_RECORDED | rejected;proof_only | 3;1 | repro/stage201_structured_selector_distribution_probe/candidate_matrix.csv | Three candidates remain publicly distinguishable; dummy random padding is proof-only and not code permission. | Only semantic proof probes may continue the dummy route. |
| stage201_dummy_pattern_gate | PASS_PATTERN_ONLY | dummy_pattern_failures | 0 | repro/stage201_structured_selector_distribution_probe/proof_gate.csv | The only surviving public-pattern route retains dense public shape and still lacks functional/resource/noise proof. | Run semantic proof probe only; do not implement SAB code. |
| stage201_decision | PASS_STAGE201_STRUCTURED_SELECTOR_DISTRIBUTION_PROBE_PROOF_ONLY | goal_status | active | repro/stage201_structured_selector_distribution_probe/summary.csv | Structured selector proof route is narrowed; full goal remains active and implementation remains denied. | Proceed to source anchors, dummy semantic proof probe, or new exact mechanism admission. |

## Assumptions

| assumption_id | statement | scope | evidence | falsification |
| --- | --- | --- | --- | --- |
| A1_public_selector_rows | The selector public key exposes row count and mask coefficients. | finite public-distribution probe | repro/stage190_selector_distribution_distinguisher/distribution_probe.csv | A production format hiding row count and mask relations would need a separate API/proof. |
| A2_dense_reference | The dense exact full-MAT selector uses the dense row count as the public reference format. | current exact full-MAT route | repro/stage190_selector_distribution_distinguisher/distribution_probe.csv | Declare a new structured public key distribution rather than dense equivalence. |
| A3_dummy_padding_scope | Random dummy padding is tested only for simple public row/zero/equality distinguishers, not for semantic correctness or security. | proof-only candidate | repro/stage201_structured_selector_distribution_probe/distribution_probe.csv | A semantic proof or production keygen/noise gate may still reject it. |

## Candidate Matrix

| candidate | rows | public_pattern_failures | decision | resource_note | evidence |
| --- | --- | --- | --- | --- | --- |
| delete_body_cross_rows | 3 | 3 | REJECT_PUBLIC_DISTRIBUTION_EQUIVALENCE | intended compactness conflicts with public distribution | repro/stage201_structured_selector_distribution_probe/distribution_probe.csv |
| deterministic_zero_padding | 3 | 3 | REJECT_PUBLIC_DISTRIBUTION_EQUIVALENCE | intended compactness conflicts with public distribution | repro/stage201_structured_selector_distribution_probe/distribution_probe.csv |
| dummy_random_padding | 3 | 0 | KEEP_PROOF_ONLY_NO_CODE_PERMISSION | dense public row count retained; key-size saving not demonstrated | repro/stage201_structured_selector_distribution_probe/distribution_probe.csv |
| forced_shared_masks | 3 | 3 | REJECT_PUBLIC_DISTRIBUTION_EQUIVALENCE | intended compactness conflicts with public distribution | repro/stage201_structured_selector_distribution_probe/distribution_probe.csv |

## Proof Gates

| gate | status | evidence | missing_before_code |
| --- | --- | --- | --- |
| T1_public_distribution | PARTIAL_PATTERN_ONLY | repro/stage201_structured_selector_distribution_probe/distribution_probe.csv; repro/stage201_structured_selector_distribution_probe/candidate_matrix.csv | Hybrid/simulation proof that dummy rows are indistinguishable from the declared selector distribution. |
| T2_functional_correctness | BLOCKED | repro/stage200_formal_gap_model_with_probe/counterexample_matrix.csv | Proof that skipped/dummy rows are semantically zero for all SAB updates, not only public-pattern safe. |
| T3_resource_value | WEAK | repro/stage201_structured_selector_distribution_probe/candidate_matrix.csv | Show complete-SAB T_bootstrap/r value despite retaining dense public row count. |
| T4_noise_and_keygen | BLOCKED | repro/stage200_formal_gap_model_with_probe/proof_obligations.csv | Production keygen, noise recurrence, and multi-seed correctness gates. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | source_anchor_intake | Reviewed 2025/686 full text is supplied locally. | Map source-specific SAB claims to inspected paper anchors. | waiting_external_artifact | repro/stage196_public_source_refresh/citation_gate.csv |
| P1 | dummy_padding_semantic_probe | Continue the only public-pattern-surviving selector route. | Finite functional probe showing dummy/skipped rows are semantically zero under a declared structured keygen model. | proof_probe_only | repro/stage201_structured_selector_distribution_probe/proof_gate.csv |
| P2 | new_exact_mechanism_admission | A concrete exact-path backend/addmul/DFT mechanism is supplied. | Projection, correctness, noise/resource, and complete-SAB T_bootstrap/r gates. | waiting_new_mechanism | repro/stage200_formal_gap_model_with_probe/gap_projection.csv |
