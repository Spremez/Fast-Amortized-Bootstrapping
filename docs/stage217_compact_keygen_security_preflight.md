# Stage217 Compact Keygen/Security Preflight

Decision: `PASS_STAGE217_PATTERN_ONLY_KEYGEN_PREFLIGHT_NO_SAB_CODE`.

Stage217 tests the compact selector route selected by Stage216. It does not
implement SAB code. The finite public-pattern probe rejects row deletion,
deterministic zero dummy rows, and forced equal dummy masks. Count-matched
random dummy padding survives only this simple public-pattern screen.

The result is deliberately limited: production SAB integration remains denied
until standard keygen distribution, noise recurrence, resource bounds, and
complete-SAB `T_bootstrap/r` gates exist.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage217_compact_keygen_security_preflight/input_status.csv | Stage217 consumes Stage201/202/203 proof-only compact evidence and Stage216 route selection. |
| G2_public_pattern_negative_controls | PASS | unexpected_probe_failures | 0 | repro/stage217_compact_keygen_security_preflight/public_distribution_probe.csv | Row deletion, deterministic zero rows, and forced equal dummy masks must remain distinguishable. |
| G3_surviving_keygen_shape | PATTERN_ONLY_SURVIVES | surviving_candidate | count_matched_random_dummy | repro/stage217_compact_keygen_security_preflight/keygen_candidate_matrix.csv | Only count-matched random dummy padding survives simple public-pattern probes, and only as pattern-only evidence. |
| G4_equation_resource_signal | PASS_MODEL_VALUE_RECORDED | min_evaluator_row_reduction_if_skip_proven | 0.111111111 | repro/stage217_compact_keygen_security_preflight/equation_resource_summary.csv | Modeled evaluator work reduction is positive, but public key row count remains dense and security is not proven. |
| G5_production_sab_admission | DENY_SAB_HOTPATH_CODE | missing_before_sab_code | standard_keygen_distribution;noise_recurrence;resource_bound;complete_sab_gate | repro/stage217_compact_keygen_security_preflight/proof_gate.csv | Stage217 may route to isolated key-object/noise prototype only; no SAB integration or speedup claim. |
| G6_stage217_decision | PASS_STAGE217_PATTERN_ONLY_KEYGEN_PREFLIGHT_NO_SAB_CODE | decision | PASS_STAGE217_PATTERN_ONLY_KEYGEN_PREFLIGHT_NO_SAB_CODE | repro/stage217_compact_keygen_security_preflight/proof_gate.csv | Compact route remains alive but proof-bounded; next work must be isolated key-object/noise prototype. |

## Input Status

| input | status | evidence | role | bytes |
| --- | --- | --- | --- | --- |
| stage201_public_pattern | present | repro/stage201_structured_selector_distribution_probe/summary.csv | prior public-pattern gate | 1602 |
| stage202_dummy_semantics | present | repro/stage202_dummy_padding_semantic_probe/summary.csv | semantic-zero dummy toy gate | 1488 |
| stage203_equation_map | present | repro/stage203_production_selector_equation_probe/equation_map.csv | declared production-shaped equation map | 3693 |
| stage203_resource_projection | present | repro/stage203_production_selector_equation_probe/resource_projection.csv | modeled evaluator-row/noise value | 823 |
| stage203_proof_gate | present | repro/stage203_production_selector_equation_probe/proof_gate.csv | remaining security/keygen blockers | 926 |
| stage216_frontier | present | repro/stage216_post_counter_frontier/proof_gate.csv | post-counter route selection | 1208 |

## Keygen Candidate Matrix

| candidate | status | probe_rows | unexpected_failures | code_permission | reason | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| row_deletion | REJECT_PUBLICLY_DISTINGUISHABLE | 30 | 0 | deny | Negative control must remain publicly distinguishable. | repro/stage217_compact_keygen_security_preflight/public_distribution_probe.csv |
| deterministic_zero_dummy | REJECT_PUBLICLY_DISTINGUISHABLE | 30 | 0 | deny | Negative control must remain publicly distinguishable. | repro/stage217_compact_keygen_security_preflight/public_distribution_probe.csv |
| forced_equal_dummy | REJECT_PUBLICLY_DISTINGUISHABLE | 30 | 0 | deny | Negative control must remain publicly distinguishable. | repro/stage217_compact_keygen_security_preflight/public_distribution_probe.csv |
| count_matched_random_dummy | PATTERN_ONLY_SURVIVES | 30 | 0 | stage218_isolated_object_probe_only | Matches dense public row count with random dummy masks in finite simple-pattern probes; still lacks security/noise proof. | repro/stage217_compact_keygen_security_preflight/public_distribution_probe.csv |

## Equation/Resource Summary

| r | dense_rows_per_T | active_rows_per_T | dummy_rows_per_T | skippable_rows_if_proven | active_over_dense | evaluator_row_reduction_if_skip_proven | dense_eval_noise_over_skip_mean | admission | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 9 | 8 | 1 | 1 | 0.888888889 | 0.111111111 | 1.041666667 | model_value_positive_but_public_key_size_not_reduced | repro/stage203_production_selector_equation_probe/equation_map.csv; repro/stage203_production_selector_equation_probe/resource_projection.csv |
| 4 | 25 | 16 | 9 | 9 | 0.640000000 | 0.360000000 | 1.187500000 | model_value_positive_but_public_key_size_not_reduced | repro/stage203_production_selector_equation_probe/equation_map.csv; repro/stage203_production_selector_equation_probe/resource_projection.csv |
| 6 | 49 | 24 | 25 | 25 | 0.489795918 | 0.510204082 | 1.347222222 | model_value_positive_but_public_key_size_not_reduced | repro/stage203_production_selector_equation_probe/equation_map.csv; repro/stage203_production_selector_equation_probe/resource_projection.csv |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage218_compact_key_object_noise_prototype | Stage217 count-matched random dummy padding survives simple public-pattern probes. | Standalone compact key object/noise prototype with negative controls; no SAB hot-path integration. | selected | If prototype closure/noise fails, compact route is blocked and reporting falls back to exact PVW/MAT-SAB only. | repro/stage217_compact_keygen_security_preflight/keygen_candidate_matrix.csv; repro/stage217_compact_keygen_security_preflight/proof_gate.csv |
| P1 | full_text_source_anchor_review | Reviewed 2025/686 full text is supplied locally. | Anchor every theorem/equation claim to inspected paper text. | waiting_artifact | Keep source claims metadata-safe. | repro/stage203_production_selector_equation_probe/proof_gate.csv |
| P2 | external_backend_mechanism | A real backend primitive is supplied. | Exact conversion equivalence and complete-SAB T_bootstrap/r. | waiting_external_mechanism | Record neutral/failed backend ablation. | repro/stage216_post_counter_frontier/proof_gate.csv |


Raw public-pattern rows: `repro/stage217_compact_keygen_security_preflight/public_distribution_probe.csv`.
