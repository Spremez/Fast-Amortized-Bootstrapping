# Stage317 SPQLIOS IFFT Batch5 Skeleton

Decision: `PASS_STAGE317_IFFT_BATCH5_TILE32_SKELETON_STAGE318_MICRO_REQUIRED`.

Stage317 rejects a single full5 fused loop because the offloop would spill zmm registers. It selects a `tile3 + tile2` skeleton as the only admitted Stage318 isolated microbench target. This is not a SAB speed claim and does not modify the SAB hot path.

## Summary

| decision | selected_tile_plan | full5_required_zmm | tile3_required_zmm | tile2_required_zmm | required_ifft_component_reduction | static_nnloop_memop_reduction | next_stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PASS_STAGE317_IFFT_BATCH5_TILE32_SKELETON_STAGE318_MICRO_REQUIRED | tile3_plus_tile2 | 42 | 26 | 18 | 0.107769 | 0.120000 | stage318_isolated_ifft_batch5_tile32_microbench_or_stop |

## Register Budget

| case | required_zmm | status | interpretation |
| --- | --- | --- | --- |
| current_single_row_assembly | 16 | BASELINE | Current assembly uses zmm0-zmm15 even though AVX512 has zmm0-zmm31. |
| full5_offloop_no_spill | 42 | REJECT_SPILLS | Processing all five rows simultaneously needs too many live vectors in the offloop. |
| tile3_offloop | 26 | PASS_NO_ZMM_SPILL | First tile can share trig loads across three rows without zmm spills. |
| tile2_offloop | 18 | PASS_NO_ZMM_SPILL | Second tile handles the remaining two rows. |
| max_rows_per_tile_no_spill | 3 | TILE3_SELECTED | Static model selects tile3+tile2 for rows=5. |

## Static Memory Model

| loop_region | five_single_rows_vector_mem_ops | tile32_vector_mem_ops | static_memop_reduction | notes |
| --- | --- | --- | --- | --- |
| firstloop_with_trig | 30 | 24 | 0.200000 | Shares trig loads once per tile; data loads/stores unchanged. |
| nnloop_offloop_with_trig | 50 | 44 | 0.120000 | Dominant butterfly region; tile3+tile2 shares trig loads twice instead of five times. |
| size4_size2_no_trig | 20 | 20 | 0.000000 | No trig-table load sharing opportunity. |

## Routes

| route_id | status | mechanism | reason |
| --- | --- | --- | --- |
| R317-1-full5-single-tile | REJECT_ZMM_SPILL_RISK | Fuse all five rows in one AVX512 loop body. | Requires 42 zmm registers in offloop, above 32. |
| R317-2-tile3-plus-tile2 | SELECT_FOR_STAGE318_ISOLATED_MICROBENCH | Run shared-trig row tiles of 3 then 2 rows for each IFFT loop region. | Tile3 requires 26 zmm registers; tile2 requires 18. |
| R317-3-sab-integration | BLOCKED_UNTIL_ISOLATED_PASS | Wire batch5 into MAT direct sub-DTF. | Needs bit/float equivalence and isolated IFFT reduction before touching SAB. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage316_input | PASS | Stage316 decision | PASS_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_SELECT_ASM_BATCH5_SKETCH | Stage317 follows the selected isolated batch5 route. |
| G2_full5_rejected | PASS | full5 required zmm vs available | 42;32 | Reject all-five-row single tile to avoid zmm spilling. |
| G3_tile32_register_budget | PASS | tile3;tile2 required zmm | 26;18 | Tile3+tile2 is the only admitted register-feasible skeleton. |
| G4_static_potential | BORDERLINE_MEASURE | nnloop static memop reduction vs required IFFT component reduction | 0.120000;0.107769 | Static opportunity is close enough to require measurement, not promotion. |
| G5_no_sab_integration | PASS | policy | isolated microbench first | No full SAB code path may depend on this until Stage318 passes. |
| G6_decision | PASS_STAGE317_IFFT_BATCH5_TILE32_SKELETON_STAGE318_MICRO_REQUIRED | stage decision | PASS_STAGE317_IFFT_BATCH5_TILE32_SKELETON_STAGE318_MICRO_REQUIRED | Controls Stage318. |
