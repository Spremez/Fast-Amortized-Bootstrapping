# Stage218 Compact Key-Object/Noise Prototype

Decision: `PASS_STAGE218_COMPACT_KEY_OBJECT_PROTOTYPE_READY_API_SKELETON`.

Stage218 builds an isolated finite key-object model for the Stage217 surviving
count-matched random dummy route. It verifies that semantic-zero dummy rows can
be skipped without changing phase in the finite model, that random dummy
semantics and missing-active skips fail, and that the toy skip-noise bound does
not exceed the dense toy bound.

This is still not a production SAB implementation. The only next route is a
MOSFHET-adjacent type/API skeleton outside SAB hot paths.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage218_compact_key_object_noise_prototype/input_status.csv | Stage218 consumes the Stage203 equation map and Stage217 pattern-only route. |
| G2_layout_count_matched | PASS | layout_rows | r=2/4/6 | repro/stage218_compact_key_object_noise_prototype/key_object_layout.csv | Prototype object keeps dense public row count and marks active versus semantic-zero dummy rows. |
| G3_phase_equivalence | PASS | phase_failures | 0 | repro/stage218_compact_key_object_noise_prototype/phase_noise_prototype.csv | Finite semantic-zero dummy skip must preserve phase. |
| G4_negative_controls | PASS | negative_failures | 0 | repro/stage218_compact_key_object_noise_prototype/negative_controls.csv | Random dummy semantics and missing-active skip must fail. |
| G5_noise_bound | PASS_TOY_BOUND | noise_failures | 0 | repro/stage218_compact_key_object_noise_prototype/noise_summary.csv | Skipping semantic-zero dummy rows does not exceed dense toy noise bound. |
| G6_production_admission | DENY_SAB_HOTPATH_CODE | missing_before_sab_code | MOSFHET type/API;encrypted keygen;security proof;production noise;complete-SAB gate | repro/stage218_compact_key_object_noise_prototype/proof_gate.csv | Stage218 permits only MOSFHET-adjacent API skeleton work. |
| G7_stage218_decision | PASS_STAGE218_COMPACT_KEY_OBJECT_PROTOTYPE_READY_API_SKELETON | decision | PASS_STAGE218_COMPACT_KEY_OBJECT_PROTOTYPE_READY_API_SKELETON | repro/stage218_compact_key_object_noise_prototype/proof_gate.csv | The compact key-object route remains bounded and can advance only to an isolated API skeleton. |

## Input Status

| input | status | evidence | role | bytes |
| --- | --- | --- | --- | --- |
| stage203_equation_map | present | repro/stage203_production_selector_equation_probe/equation_map.csv | declared compact selector equation map | 3693 |
| stage217_keygen_candidates | present | repro/stage217_compact_keygen_security_preflight/keygen_candidate_matrix.csv | surviving keygen shape | 956 |
| stage217_proof_gate | present | repro/stage217_compact_keygen_security_preflight/proof_gate.csv | pattern-only route gate | 1712 |

## Layout

| r | dense_public_rows | active_rows | dummy_zero_rows | public_rows | count_matched | active_over_dense | dummy_over_dense | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 9 | 8 | 1 | 9 | yes | 0.888888889 | 0.111111111 | repro/stage203_production_selector_equation_probe/equation_map.csv |
| 4 | 25 | 16 | 9 | 25 | yes | 0.640000000 | 0.360000000 | repro/stage203_production_selector_equation_probe/equation_map.csv |
| 6 | 49 | 24 | 25 | 49 | yes | 0.489795918 | 0.510204082 | repro/stage203_production_selector_equation_probe/equation_map.csv |

## Noise Summary

| r | samples | min_skip_over_dense | mean_skip_over_dense | max_skip_over_dense | failures | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 20 | 0.807692308 | 0.902548909 | 0.965517241 | 0 | repro/stage218_compact_key_object_noise_prototype/noise_summary.csv |
| 4 | 20 | 0.562500000 | 0.621147370 | 0.697368421 | 0 | repro/stage218_compact_key_object_noise_prototype/noise_summary.csv |
| 6 | 20 | 0.428571429 | 0.498045531 | 0.591549296 | 0 | repro/stage218_compact_key_object_noise_prototype/noise_summary.csv |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage219_mosfhet_adjacent_compact_key_api_skeleton | Stage218 finite key-object/noise prototype passes. | Compile-only MOSFHET-adjacent type/API skeleton with ownership, row-role, and no-hot-allocation checks. | selected | If API skeleton fails, keep compact route prototype-only and do not enter SAB integration. | repro/stage218_compact_key_object_noise_prototype/proof_gate.csv |
| P1 | production_noise_recurrence | API skeleton exists and maps to encrypted key objects. | Noise recurrence and parameter/resource bound before any complete-SAB integration. | future_blocked | Block compact route from SAB integration. | repro/stage218_compact_key_object_noise_prototype/noise_summary.csv |
| P2 | exact_pvw_mat_sab_report_fallback | Any compact gate fails. | Report only current exact PVW/MAT-SAB T_bootstrap/r evidence. | fallback | No new algorithmic compact claim. | repro/stage217_compact_keygen_security_preflight/proof_gate.csv |


Raw phase rows: `repro/stage218_compact_key_object_noise_prototype/phase_noise_prototype.csv`. Negative controls: `repro/stage218_compact_key_object_noise_prototype/negative_controls.csv`.
