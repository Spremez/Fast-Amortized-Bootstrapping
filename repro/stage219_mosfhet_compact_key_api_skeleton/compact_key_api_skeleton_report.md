# Stage219 MOSFHET Compact Key API Skeleton

Decision: `PASS_STAGE219_MOSFHET_COMPACT_KEY_API_SKELETON_READY_ENCRYPTED_KEYGEN`.

Stage219 compiles and runs a MOSFHET-adjacent compact key API skeleton. The C
probe uses real MOSFHET `TorusPolynomial`/`DFT_Polynomial` allocation and DFT
conversion functions, while keeping the new compact key row-role metadata in a
repro-only skeleton. It does not modify production headers or `sab_pvw_*`.

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | missing_inputs |  | repro/stage219_mosfhet_compact_key_api_skeleton/input_status.csv | Stage219 consumes Stage203 equation rows and Stage218 API-skeleton permission. |
| G2_mosfhet_static_build | PASS | make_static_spqlios | true | repro/stage219_mosfhet_compact_key_api_skeleton/mosfhet_static_build.log | Probe links against current MOSFHET static library. |
| G3_probe_compile_run | PASS | compile_ok;run_ok | true;true | repro/stage219_mosfhet_compact_key_api_skeleton/compile_probe.log; repro/stage219_mosfhet_compact_key_api_skeleton/run_probe.log | Standalone compact key API skeleton compiles and runs. |
| G4_ownership_roles_guards | PASS | max_gap;max_hot_alloc_delta | 1;0 | repro/stage219_mosfhet_compact_key_api_skeleton/api_results.csv | DFT rows are non-aliased, row roles match generated equations, invalid guards pass, and hot role scan allocates nothing. |
| G5_stage218_layout_match | PASS | layout_mismatches | 0 | repro/stage219_mosfhet_compact_key_api_skeleton/layout_results.csv; repro/stage218_compact_key_object_noise_prototype/key_object_layout.csv | Compiled API skeleton preserves Stage218 dense/active/dummy row counts for r=2/4/6. |
| G6_production_admission | DENY_SAB_HOTPATH_CODE | missing_before_sab_code | encrypted_keygen;security_reduction;production_noise;compact_ep_integration;complete_sab_gate | repro/stage219_mosfhet_compact_key_api_skeleton/proof_gate.csv | Stage219 permits encrypted compact keygen prototype only; no SAB integration or speedup claim. |
| G7_stage219_decision | PASS_STAGE219_MOSFHET_COMPACT_KEY_API_SKELETON_READY_ENCRYPTED_KEYGEN | decision | PASS_STAGE219_MOSFHET_COMPACT_KEY_API_SKELETON_READY_ENCRYPTED_KEYGEN | repro/stage219_mosfhet_compact_key_api_skeleton/proof_gate.csv | MOSFHET-adjacent compact key API skeleton is ready for encrypted keygen prototype, still outside SAB hot path. |

## Input Status

| input | status | evidence | role | bytes |
| --- | --- | --- | --- | --- |
| stage203_equation_map | present | repro/stage203_production_selector_equation_probe/equation_map.csv | row-role source for generated C probe | 3693 |
| stage218_layout | present | repro/stage218_compact_key_object_noise_prototype/key_object_layout.csv | expected dense/active/dummy layout | 440 |
| stage218_proof_gate | present | repro/stage218_compact_key_object_noise_prototype/proof_gate.csv | permission for API skeleton only | 1577 |
| mosfhet_header | present | src/mosfhet/include/mosfhet.h | production MOSFHET public types/functions | 32723 |
| mattrgsw_compact_impl | present | src/mosfhet/src/mattrgsw.c | current compact allocator/function implementation | 38109 |

## API Results

| backend | r | N | dense_rows | active_rows | dummy_rows | pointer_failures | role_failures | guard_failures | roundtrip_mismatches | max_gap | tolerance | hot_alloc_delta | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spqlios | 2 | 1024 | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 1 | 2048 | 0 | PASS_COMPACT_KEY_API_SKELETON |
| spqlios | 4 | 1024 | 25 | 16 | 9 | 0 | 0 | 0 | 0 | 1 | 2048 | 0 | PASS_COMPACT_KEY_API_SKELETON |
| spqlios | 6 | 1024 | 49 | 24 | 25 | 0 | 0 | 0 | 0 | 1 | 2048 | 0 | PASS_COMPACT_KEY_API_SKELETON |
| spqlios | 2 | 2048 | 9 | 8 | 1 | 0 | 0 | 0 | 0 | 1 | 2048 | 0 | PASS_COMPACT_KEY_API_SKELETON |
| spqlios | 4 | 2048 | 25 | 16 | 9 | 0 | 0 | 0 | 0 | 1 | 2048 | 0 | PASS_COMPACT_KEY_API_SKELETON |
| spqlios | 6 | 2048 | 49 | 24 | 25 | 0 | 0 | 0 | 0 | 1 | 2048 | 0 | PASS_COMPACT_KEY_API_SKELETON |

## Layout Results

| r | N | dense_rows | active_rows | dummy_rows | skippable_rows | active_over_dense | dummy_over_dense | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1024 | 9 | 8 | 1 | 1 | 0.888888889 | 0.111111111 | PASS_ROLE_LAYOUT |
| 4 | 1024 | 25 | 16 | 9 | 9 | 0.640000000 | 0.360000000 | PASS_ROLE_LAYOUT |
| 6 | 1024 | 49 | 24 | 25 | 25 | 0.489795918 | 0.510204082 | PASS_ROLE_LAYOUT |
| 2 | 2048 | 9 | 8 | 1 | 1 | 0.888888889 | 0.111111111 | PASS_ROLE_LAYOUT |
| 4 | 2048 | 25 | 16 | 9 | 9 | 0.640000000 | 0.360000000 | PASS_ROLE_LAYOUT |
| 6 | 2048 | 49 | 24 | 25 | 25 | 0.489795918 | 0.510204082 | PASS_ROLE_LAYOUT |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage220_encrypted_compact_keygen_prototype | Stage219 compact key API skeleton passes compile/run/role/ownership gates. | Prototype encrypted compact keygen rows with semantic-zero dummy role preservation and negative controls. | selected | If encrypted keygen semantics fail, compact route remains API-only and SAB integration is denied. | repro/stage219_mosfhet_compact_key_api_skeleton/proof_gate.csv |
| P1 | production_noise_recurrence | Encrypted compact keygen prototype exists. | Noise recurrence and parameter/resource bound before complete-SAB integration. | future_blocked | Block compact route from SAB integration. | repro/stage218_compact_key_object_noise_prototype/proof_gate.csv |
| P2 | exact_pvw_mat_sab_report_fallback | Any compact API/keygen gate fails. | Report only current exact PVW/MAT-SAB T_bootstrap/r evidence. | fallback | No compact algorithmic claim. | repro/stage218_compact_key_object_noise_prototype/proof_gate.csv |
