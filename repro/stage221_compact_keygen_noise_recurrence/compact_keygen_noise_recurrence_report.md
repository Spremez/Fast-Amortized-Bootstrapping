# Stage221 Compact Keygen Noise Recurrence

Decision: `PASS_STAGE221_COMPACT_KEYGEN_NOISE_RECURRENCE_READY_ISOLATED_EP`.

Stage221 binds the encrypted compact keygen prototype to the target SAB schedule
with an explicit relative noise/resource recurrence. The endpoint is still
`T_bootstrap/r`: compact rows are normalized per processed plaintext bit, and
row-count ceilings are separated from latency claims.

This stage permits only isolated compact external-product experiments. It does
not modify `sab_pvw_*`, does not prove standard key security, and does not claim
complete SAB speedup.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage221_compact_keygen_noise_recurrence/input_status.csv | Stage221 consumes Stage220 encrypted keygen data plus Stage203/Stage187 claim boundaries. |
| G2_stage220_admission | PASS | stage220_decision | present | repro/stage220_encrypted_compact_keygen_prototype/proof_gate.csv | Noise recurrence is only meaningful after encrypted compact keygen prototype passed. |
| G3_relative_noise_recurrence | PASS | max_active_over_dense_sigma;max_active_over_dense_l1 | 0.942809042;0.888888889 | repro/stage221_compact_keygen_noise_recurrence/recurrence_model.csv | Under the deterministic row-noise recurrence proxy, active-row compact evaluation is no worse than dense MAT. |
| G4_resource_boundary | PASS | public_key_row_saving;max_eval_row_reduction | 0;0.510204082 | repro/stage221_compact_keygen_noise_recurrence/resource_bound.csv | Public key rows remain dense; only evaluator row skipping is admitted. |
| G5_per_bit_normalization | PASS | compact_active_rows_per_bit | 4.000000000 | repro/stage221_compact_keygen_noise_recurrence/per_bit_normalization.csv | `T_bootstrap/r` normalization is explicit; row-count ceilings are not latency claims. |
| G6_production_admission | ALLOW_ISOLATED_COMPACT_EP_ONLY | missing_before_sab_code | compact_ep_phase_equivalence;complete_sab_gate;multi_seed_noise;security_reduction | repro/stage221_compact_keygen_noise_recurrence/proof_gate.csv | Stage221 can open isolated compact EP experiments only; SAB hot-path code remains denied. |
| G7_stage221_decision | PASS_STAGE221_COMPACT_KEYGEN_NOISE_RECURRENCE_READY_ISOLATED_EP | decision | PASS_STAGE221_COMPACT_KEYGEN_NOISE_RECURRENCE_READY_ISOLATED_EP | repro/stage221_compact_keygen_noise_recurrence/proof_gate.csv | Relative recurrence/resource/per-bit gates permit Stage222 isolated compact EP, not complete-SAB acceleration claims. |

## Recurrence Model

| backend | r | N | seeds | steps_per_lane | dense_rows | active_rows | dummy_rows | max_row_noise | dense_sigma_proxy | active_sigma_proxy | active_over_dense_sigma | dense_l1_proxy | active_l1_proxy | active_over_dense_l1 | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spqlios | 2 | 1024 | 2 | 286720 | 9 | 8 | 1 | 1.000000 | 1606.387251 | 1514.516424 | 0.942809042 | 2580480.000000 | 2293760.000000 | 0.888888889 | PASS_RELATIVE_RECURRENCE_NO_WORSE_THAN_DENSE_MAT |
| spqlios | 2 | 2048 | 1 | 573440 | 9 | 8 | 1 | 1.000000 | 2271.774637 | 2141.849668 | 0.942809042 | 5160960.000000 | 4587520.000000 | 0.888888889 | PASS_RELATIVE_RECURRENCE_NO_WORSE_THAN_DENSE_MAT |
| spqlios | 4 | 1024 | 2 | 286720 | 25 | 16 | 9 | 1.000000 | 2677.312085 | 2141.849668 | 0.800000000 | 7168000.000000 | 4587520.000000 | 0.640000000 | PASS_RELATIVE_RECURRENCE_NO_WORSE_THAN_DENSE_MAT |
| spqlios | 4 | 2048 | 1 | 573440 | 25 | 16 | 9 | 1.000000 | 3786.291061 | 3029.032849 | 0.800000000 | 14336000.000000 | 9175040.000000 | 0.640000000 | PASS_RELATIVE_RECURRENCE_NO_WORSE_THAN_DENSE_MAT |
| spqlios | 6 | 1024 | 2 | 286720 | 49 | 24 | 25 | 1.000000 | 3748.236919 | 2623.219396 | 0.699854212 | 14049280.000000 | 6881280.000000 | 0.489795918 | PASS_RELATIVE_RECURRENCE_NO_WORSE_THAN_DENSE_MAT |
| spqlios | 6 | 2048 | 1 | 573440 | 49 | 24 | 25 | 1.000000 | 5300.807486 | 3709.792447 | 0.699854212 | 28098560.000000 | 13762560.000000 | 0.489795918 | PASS_RELATIVE_RECURRENCE_NO_WORSE_THAN_DENSE_MAT |

## Resource Boundary

| r | N | dense_public_rows | active_eval_rows | dummy_public_rows | public_key_row_saving | eval_row_reduction | rows_per_bit_dense_public | rows_per_bit_active_eval | rows_per_bit_dummy_public | stage203_eval_reduction_if_skip | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1024 | 9 | 8 | 1 | 0 | 0.111111111 | 4.500000000 | 4.000000000 | 0.500000000 | 0.111111111 | PASS_RESOURCE_BOUND_DECLARED_NO_KEY_SIZE_SAVING |
| 4 | 1024 | 25 | 16 | 9 | 0 | 0.360000000 | 6.250000000 | 4.000000000 | 2.250000000 | 0.360000000 | PASS_RESOURCE_BOUND_DECLARED_NO_KEY_SIZE_SAVING |
| 6 | 1024 | 49 | 24 | 25 | 0 | 0.510204082 | 8.166666667 | 4.000000000 | 4.166666667 | 0.510204082 | PASS_RESOURCE_BOUND_DECLARED_NO_KEY_SIZE_SAVING |
| 2 | 2048 | 9 | 8 | 1 | 0 | 0.111111111 | 4.500000000 | 4.000000000 | 0.500000000 | 0.111111111 | PASS_RESOURCE_BOUND_DECLARED_NO_KEY_SIZE_SAVING |
| 4 | 2048 | 25 | 16 | 9 | 0 | 0.360000000 | 6.250000000 | 4.000000000 | 2.250000000 | 0.360000000 | PASS_RESOURCE_BOUND_DECLARED_NO_KEY_SIZE_SAVING |
| 6 | 2048 | 49 | 24 | 25 | 0 | 0.510204082 | 8.166666667 | 4.000000000 | 4.166666667 | 0.510204082 | PASS_RESOURCE_BOUND_DECLARED_NO_KEY_SIZE_SAVING |

## Per-Bit Normalization

| r | N | processed_bits_per_batch | steps_per_lane | scalar_repeated_schedule_steps | mat_batch_schedule_steps | lane_amortization_step_ceiling | compact_vs_dense_mat_row_ceiling | compact_active_rows_per_bit | dense_mat_rows_per_bit | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1024 | 2 | 286720 | 573440 | 286720 | 2.000000000 | 1.125000000 | 4.000000000 | 4.500000000 | row-count/model ceiling only; requires Stage222 isolated EP and complete SAB A/B before latency claim |
| 4 | 1024 | 4 | 286720 | 1146880 | 286720 | 4.000000000 | 1.562500000 | 4.000000000 | 6.250000000 | row-count/model ceiling only; requires Stage222 isolated EP and complete SAB A/B before latency claim |
| 6 | 1024 | 6 | 286720 | 1720320 | 286720 | 6.000000000 | 2.041666667 | 4.000000000 | 8.166666667 | row-count/model ceiling only; requires Stage222 isolated EP and complete SAB A/B before latency claim |
| 2 | 2048 | 2 | 573440 | 1146880 | 573440 | 2.000000000 | 1.125000000 | 4.000000000 | 4.500000000 | row-count/model ceiling only; requires Stage222 isolated EP and complete SAB A/B before latency claim |
| 4 | 2048 | 4 | 573440 | 2293760 | 573440 | 4.000000000 | 1.562500000 | 4.000000000 | 6.250000000 | row-count/model ceiling only; requires Stage222 isolated EP and complete SAB A/B before latency claim |
| 6 | 2048 | 6 | 573440 | 3440640 | 573440 | 6.000000000 | 2.041666667 | 4.000000000 | 8.166666667 | row-count/model ceiling only; requires Stage222 isolated EP and complete SAB A/B before latency claim |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage222_isolated_compact_ep_integration | Stage221 recurrence/resource/per-bit gates pass. | Implement isolated compact external product reference and compare phase/noise versus dense MAT. | selected | If isolated EP fails, keep compact route outside SAB and report model-only result. | repro/stage221_compact_keygen_noise_recurrence/proof_gate.csv |
| P1 | stage223_compact_ep_microbench | Stage222 isolated compact EP correctness passes. | Measure compact active-row EP versus dense MAT under same backend before any SAB schedule work. | future_blocked | Record kernel-level neutral/negative result. | repro/stage221_compact_keygen_noise_recurrence/per_bit_normalization.csv |
| P2 | exact_pvw_mat_sab_report_fallback | Stage221 fails or Stage222 correctness fails. | Use already verified exact PVW/MAT-SAB `T_bootstrap/r` evidence only. | fallback | No compact algorithmic claim. | repro/stage220_encrypted_compact_keygen_prototype/proof_gate.csv |
