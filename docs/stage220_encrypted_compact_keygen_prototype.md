# Stage220 Encrypted Compact Keygen Prototype

Decision: `PASS_STAGE220_ENCRYPTED_COMPACT_KEYGEN_READY_NOISE_RECURRENCE`.

Stage220 builds and runs a MOSFHET-linked encrypted compact keygen prototype.
Each row stores random-looking public mask/body material, explicit active or
semantic-zero-dummy role metadata, and deterministic finite noise. The gate
checks row phase, production DFT roundtrip, public-pattern constraints,
semantic-zero dummy preservation, and negative controls.

This is not a production security proof and does not enter `sab_pvw_*`.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage220_encrypted_compact_keygen_prototype/input_status.csv | Stage220 consumes Stage203 equations and Stage219 compact key API skeleton evidence. |
| G2_mosfhet_static_build | PASS | make_static_spqlios | true | repro/stage220_encrypted_compact_keygen_prototype/mosfhet_static_build.log | Prototype links against current MOSFHET static library. |
| G3_probe_compile_run | PASS | compile_ok;run_ok | true;true | repro/stage220_encrypted_compact_keygen_prototype/compile_probe.log; repro/stage220_encrypted_compact_keygen_prototype/run_probe.log | Standalone encrypted compact keygen prototype compiles and runs. |
| G4_keygen_phase_semantics | PASS | phase_mismatches;dummy_semantic_failures | 0;0 | repro/stage220_encrypted_compact_keygen_prototype/keygen_results.csv | Each encrypted row decrypts to semantic payload plus noise; dummy rows preserve semantic zero. |
| G5_public_pattern_and_dft | PASS | public_pattern_failures;dft_mismatches;max_dft_gap | 0;0;75 | repro/stage220_encrypted_compact_keygen_prototype/keygen_results.csv | Dense public row count uses nonzero/nonduplicate random masks and production DFT roundtrip remains within tolerance. |
| G6_negative_controls | PASS | min_missing_active_negative;min_random_dummy_negative | 1;9 | repro/stage220_encrypted_compact_keygen_prototype/keygen_results.csv | Skipping an active row and assigning nonzero dummy semantics both fail as required. |
| G7_noise_bound_and_layout | PASS | max_noise_abs;max_noise_bound | 1;28672 | repro/stage220_encrypted_compact_keygen_prototype/keygen_results.csv; repro/stage220_encrypted_compact_keygen_prototype/layout_results.csv | Deterministic prototype noise remains below bound and layout preserves dense public row count. |
| G8_production_admission | DENY_SAB_HOTPATH_CODE | missing_before_sab_code | security_reduction;production_noise_recurrence;compact_ep_integration;complete_sab_gate | repro/stage220_encrypted_compact_keygen_prototype/proof_gate.csv | Stage220 permits production-noise recurrence modeling only; no SAB integration or speedup claim. |
| G9_stage220_decision | PASS_STAGE220_ENCRYPTED_COMPACT_KEYGEN_READY_NOISE_RECURRENCE | decision | PASS_STAGE220_ENCRYPTED_COMPACT_KEYGEN_READY_NOISE_RECURRENCE | repro/stage220_encrypted_compact_keygen_prototype/proof_gate.csv | Encrypted compact keygen prototype is ready for production noise recurrence gate, still outside SAB hot path. |

## Input Status

| input | status | evidence | role | bytes |
| --- | --- | --- | --- | --- |
| stage203_equation_map | present | repro/stage203_production_selector_equation_probe/equation_map.csv | row-role source for generated encrypted keygen probe | 3693 |
| stage219_proof_gate | present | repro/stage219_mosfhet_compact_key_api_skeleton/proof_gate.csv | permission for encrypted compact keygen prototype only | 1842 |
| stage219_api_results | present | repro/stage219_mosfhet_compact_key_api_skeleton/api_results.csv | compiled API skeleton evidence | 572 |
| mosfhet_header | present | src/mosfhet/include/mosfhet.h | production MOSFHET public types/functions | 32723 |

## Keygen Results

| backend | r | N | seed | dense_rows | active_rows | dummy_rows | public_pattern_failures | phase_mismatches | dft_mismatches | dummy_semantic_failures | missing_active_negative_failures | random_dummy_negative_failures | max_dft_gap | max_noise_abs | noise_bound | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spqlios | 2 | 1024 | 0 | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 1 | 9 | 51 | 1 | 6144 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |
| spqlios | 2 | 1024 | 1 | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 1 | 9 | 45 | 1 | 6144 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |
| spqlios | 4 | 1024 | 0 | 25 | 16 | 9 | 0 | 0 | 0 | 0 | 1 | 24 | 51 | 1 | 10240 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |
| spqlios | 4 | 1024 | 1 | 25 | 16 | 9 | 0 | 0 | 0 | 0 | 1 | 24 | 52 | 1 | 10240 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |
| spqlios | 6 | 1024 | 0 | 49 | 24 | 25 | 0 | 0 | 0 | 0 | 1 | 45 | 51 | 1 | 14336 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |
| spqlios | 6 | 1024 | 1 | 49 | 24 | 25 | 0 | 0 | 0 | 0 | 1 | 44 | 52 | 1 | 14336 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |
| spqlios | 2 | 2048 | 0 | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 1 | 9 | 63 | 1 | 12288 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |
| spqlios | 4 | 2048 | 0 | 25 | 16 | 9 | 0 | 0 | 0 | 0 | 1 | 24 | 74 | 1 | 20480 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |
| spqlios | 6 | 2048 | 0 | 49 | 24 | 25 | 0 | 0 | 0 | 0 | 1 | 45 | 75 | 1 | 28672 | PASS_ENCRYPTED_COMPACT_KEYGEN_PROTOTYPE |

## Layout Results

| r | N | dense_rows | active_rows | dummy_rows | public_rows | active_over_dense | dummy_over_dense | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1024 | 9 | 8 | 1 | 9 | 0.888888889 | 0.111111111 | PASS_ENCRYPTED_KEYGEN_LAYOUT |
| 2 | 1024 | 9 | 8 | 1 | 9 | 0.888888889 | 0.111111111 | PASS_ENCRYPTED_KEYGEN_LAYOUT |
| 4 | 1024 | 25 | 16 | 9 | 25 | 0.640000000 | 0.360000000 | PASS_ENCRYPTED_KEYGEN_LAYOUT |
| 4 | 1024 | 25 | 16 | 9 | 25 | 0.640000000 | 0.360000000 | PASS_ENCRYPTED_KEYGEN_LAYOUT |
| 6 | 1024 | 49 | 24 | 25 | 49 | 0.489795918 | 0.510204082 | PASS_ENCRYPTED_KEYGEN_LAYOUT |
| 6 | 1024 | 49 | 24 | 25 | 49 | 0.489795918 | 0.510204082 | PASS_ENCRYPTED_KEYGEN_LAYOUT |
| 2 | 2048 | 9 | 8 | 1 | 9 | 0.888888889 | 0.111111111 | PASS_ENCRYPTED_KEYGEN_LAYOUT |
| 4 | 2048 | 25 | 16 | 9 | 25 | 0.640000000 | 0.360000000 | PASS_ENCRYPTED_KEYGEN_LAYOUT |
| 6 | 2048 | 49 | 24 | 25 | 49 | 0.489795918 | 0.510204082 | PASS_ENCRYPTED_KEYGEN_LAYOUT |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage221_compact_keygen_noise_recurrence | Stage220 encrypted compact keygen prototype passes phase/DFT/negative/noise gates. | Model production repeated-SAB noise recurrence and resource bounds before any compact EP/SAB integration. | selected | If recurrence or resource bound fails, compact route remains prototype-only. | repro/stage220_encrypted_compact_keygen_prototype/proof_gate.csv |
| P1 | stage222_isolated_compact_ep_integration | Production noise recurrence passes and keygen API remains closed. | Isolated compact external product integration; still no SAB schedule integration. | future_blocked | Record kernel-only negative or neutral result. | repro/stage220_encrypted_compact_keygen_prototype/keygen_results.csv |
| P2 | exact_pvw_mat_sab_report_fallback | Any compact keygen/noise gate fails. | Report only current exact PVW/MAT-SAB T_bootstrap/r evidence. | fallback | No compact algorithmic claim. | repro/stage219_mosfhet_compact_key_api_skeleton/proof_gate.csv |
