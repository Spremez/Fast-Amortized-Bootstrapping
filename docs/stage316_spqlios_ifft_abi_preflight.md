# Stage316 SPQLIOS IFFT ABI Preflight

Decision: `PASS_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_SELECT_ASM_BATCH5_SKETCH`.

Stage316 audits the actual SPQLIOS ABI and rejects another C-wrapper loop. The only admitted route is an isolated AVX512 `ifft_batch5` symbol, because the r=4 direct sub-DTF path has rows=k+r=5.

## Summary

| decision | existing_batch_abi | c_wrapper_rows5_vs_rows1 | c_wrapper_rows10_vs_rows1 | required_ifft_component_reduction | selected_next_stage |
| --- | --- | --- | --- | --- | --- |
| PASS_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_SELECT_ASM_BATCH5_SKETCH | NO | 0.961223 | 1.131833 | 0.107769 | stage317_spqlios_ifft_batch5_asm_skeleton_or_stop |

## ABI Symbol Audit

| artifact | evidence | count | interpretation |
| --- | --- | --- | --- |
| src/mosfhet/src/fft/spqlios/spqlios-fft.h | single-row ifft declaration | 1 | public ABI exposes `ifft(tables, data)` only |
| src/mosfhet/src/fft/spqlios/spqlios-fft.h | batch ifft declaration | 0 | no batch ABI is currently declared |
| src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s | single-row ifft symbol | 2 | AVX512 backend exports only the single-row ifft symbol |
| src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s | batch ifft symbol | 0 | no AVX512 batch ifft symbol exists |
| src/mosfhet/src/polynomial.c | array wrapper loop | 1 | high-level array conversion remains a per-row wrapper |
| src/mosfhet/src/mattrgsw.c | direct sub-DTF ifft calls | 3 | MAT direct sub-DTF still calls single-row ifft per row |

## Routes

| route_id | status | required_change | why | next_action |
| --- | --- | --- | --- | --- |
| R1-c-wrapper-loop | REJECT_DUPLICATE_STAGE310 | Wrap five calls to existing `ifft` in C. | Stage310 already shows rows=5 per-row speedup below 1 and no true ABI change. | Do not implement. |
| R2-c-model-batch | REJECT_FOR_PERFORMANCE_CLAIM | Port `ifft_model` to a rows=5 C model loop. | Useful for correctness documentation but cannot justify AVX512 performance claims. | Only use as a reference if an assembly prototype is implemented. |
| R3-avx512-ifft-batch5-symbol | SELECT_HIGH_RISK_STAGE317 | Add isolated `ifft_batch5(tables,row0,row1,row2,row3,row4)` symbol and benchmark outside SAB. | Only route that can share trig-table loads/schedule across the rows=k+r=5 direct sub-DTF case. | Stage317 assembly skeleton or explicit stop if register pressure/ABI is too large. |
| R4-full-sab-integration | BLOCK_UNTIL_ISOLATED_PASS | Call batch5 inside `mat_trgsw_sub_decompose_DFT_direct`. | No SAB integration before isolated correctness and IFFT reduction pass. | Only after Stage317 isolated gates. |

## Source Anchors

| anchor | file | lines | fact |
| --- | --- | --- | --- |
| single_row_ifft_header | src/mosfhet/src/fft/spqlios/spqlios-fft.h | 17-24 | Header declares `ifft(const void*, double*)`; no batch rows variant. |
| avx512_ifft_symbol | src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s | 1-18 | Assembly exports only `ifft`/`_ifft` and takes one data pointer. |
| avx512_ifft_dataflow | src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s | 64-158 | Main loops load one real/imag row and shared trig tables per transform. |
| array_wrapper | src/mosfhet/src/polynomial.c | 435-465 | Array conversion loops over rows; Stage310 rejected wrapper-only work. |
| direct_sub_dtf_rows | src/mosfhet/src/mattrgsw.c | 1110-1163 | Direct sub-DTF calls `ifft` once for each of rows=k+r. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage315_input | PASS | Stage315 decision | PASS_STAGE315_BACKEND_IFFT_ADMISSION_SELECT_STAGE316_ABI_PREFLIGHT | Stage316 is valid only after Stage315 selects backend IFFT. |
| G2_no_existing_batch_abi | PASS | header_batch;asm_batch | 0;0 | No existing batch ABI can be reused. |
| G3_c_wrapper_rejected | PASS | Stage310 rows5/rows1;rows10/rows1 | 0.961223;1.131833 | Wrapper-only batching remains rejected. |
| G4_selected_route | PASS_HIGH_RISK | route | R3-avx512-ifft-batch5-symbol | Only a new isolated assembly/backend symbol is admitted. |
| G5_sab_integration_block | PASS | policy | no full SAB changes before isolated gate | Avoids theoretical drift and protects scalar/PVW baseline. |
| G6_decision | PASS_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_SELECT_ASM_BATCH5_SKETCH | stage decision | PASS_STAGE316_BACKEND_IFFT_ABI_PREFLIGHT_SELECT_ASM_BATCH5_SKETCH | Controls Stage317. |
