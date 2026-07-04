# Stage315 Backend IFFT Admission

Decision: `PASS_STAGE315_BACKEND_IFFT_ADMISSION_SELECT_STAGE316_ABI_PREFLIGHT`.

Stage315 converts the Stage314 closeout into one executable next route. The primary endpoint remains complete SAB `T_bootstrap/r`, i.e. bootstrapping time divided by the number of independent PVW body lanes processed by one MAT/PVW bootstrapping call.

## Admission Summary

| decision | primary_metric | stage310_ifft_route | stage313_ifft_share_of_body | ifft_reduction_required_for_1p02_body | selected_next_stage |
| --- | --- | --- | --- | --- | --- |
| PASS_STAGE315_BACKEND_IFFT_ADMISSION_SELECT_STAGE316_ABI_PREFLIGHT | complete_sab_T_bootstrap_over_r | PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED | 0.181943 | 0.107769 | stage316_spqlios_ifft_batch_abi_preflight |

## Component Thresholds

| component | share_of_body_profile | component_reduction_required_for_1p02_body | projected_speedup_if_10pct_reduction | projected_speedup_if_25pct_reduction |
| --- | --- | --- | --- | --- |
| digit_to_double | 0.172510 | 0.113662 | 1.017554 | 1.045071 |
| spqlios_ifft | 0.181943 | 0.107769 | 1.018531 | 1.047653 |
| dense_mat_addmul | 0.215408 | 0.091026 | 1.022015 | 1.056917 |
| mat_ep_lifecycle | 0.585042 | 0.033515 | 1.062140 | 1.171317 |

## Candidate Selection

| candidate_id | status | mechanism | budget |
| --- | --- | --- | --- |
| H315-C1-spqlios-batch-ifft-abi | SELECT_FOR_STAGE316_ABI_PREFLIGHT | Replace the current rows independent `ifft(proc->tables_reverse, row)` inside direct sub-DTF materialization with an isolated backend batch ABI/prototype that computes the same rows. | Stage313 IFFT share=0.181943; requires >=0.107769 component reduction for a 1.02 body budget. |
| H315-C2-local-digit-microvariant | CLOSED_BY_STAGE314 | Further AVX digit conversion tweaks without broader lifecycle change. | Stage314 projected observed narrow32-only body gain is 1.007439. |
| H315-C3-wrapper-from-dft-add | ALREADY_IN_CURRENT_BASELINE | Use `SAB_PVW_BACKEND_FROM_DFT_ADD` / backend add during materialization. | Stage312/313 common flags already include SAB_PVW_BACKEND_FROM_DFT_ADD=true; old Stage88 r=6 backend mean=1.437 vs wrapper mean=1.384. |
| H315-C4-lazy-dft-schedule-state | DEFER_NO_COUNT_REDUCTION_PROOF | Keep CMUX outputs in DFT form across butterfly windows. | No admitted budget because next SAB operations consume torus-domain state. |
| H315-C5-dense-mat-avx-rewrite | DEFER | Rewrite dense MAT addmul layout/register tiling. | Stage313 dense share=0.215408; reopen only with assembly/counter hypothesis and full-SAB budget. |

## Code Anchors

| anchor | file | lines | fact | stage315_use |
| --- | --- | --- | --- | --- |
| direct_sub_dft_ifft_loop | src/mosfhet/src/mattrgsw.c | 1110-1163 | direct sub-DTF materialization converts each gadget row to double and calls `ifft` per row. | Stage316 target implementation boundary. |
| r4_rowbatch_digit_existing | src/mosfhet/src/mattrgsw.c | 1039-1107 | r=4 row-batched digit conversion already exists, but still loops `ifft` per row. | Shows remaining non-digit backend work. |
| pvw_cmux_materialization | src/sab_pvw.c | 615-655 | CMUX materializes MAT EP output and may use backend from_DFT_add. | This path is already in the current direct baseline, not the new target. |
| pvm_from_dft_add_backend_flag | src/mosfhet/src/pvwtmlwe.c | 763-781 | `SAB_PVW_BACKEND_FROM_DFT_ADD` calls `polynomial_DFT_to_torus_add`. | Records why wrapper materialization is not selected again. |
| spqlios_reverse_transform_api | src/mosfhet/src/polynomial.c | 373-379,435-465 | current torus-to-DFT array wrapper still iterates per row; no real batch IFFT API is exposed. | Stage316 must operate at backend ABI/prototype level. |

## Proof Gate

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage314_route | PASS | Stage314 decision | PASS_STAGE314_LOCAL_DIGIT_MICROVARIANTS_CLOSED_BACKEND_OR_SCHEDULE_NEXT | Local digit variants must be closed before choosing Stage315. |
| G2_stage310_backend_requirement | PASS | Stage310 decision | PASS_STAGE310_IFFT_ROWS_SCALING_BACKEND_REQUIRED | C-wrapper IFFT is insufficient; backend ABI preflight is required. |
| G3_budget_materiality | PASS | required IFFT component reduction for 1.02 body | 0.107769 | Stage316 must show at least this isolated IFFT reduction before SAB integration. |
| G4_duplicate_route_blocked | PASS | backend from_DFT_add | already in Stage312/313 common flags | Do not claim an old materialization flag as new work. |
| G5_primary_metric | PASS | metric | T_bootstrap/r | All future comparisons must be amortized per processed body/lane. |
| G6_decision | PASS_STAGE315_BACKEND_IFFT_ADMISSION_SELECT_STAGE316_ABI_PREFLIGHT | stage decision | PASS_STAGE315_BACKEND_IFFT_ADMISSION_SELECT_STAGE316_ABI_PREFLIGHT | Controls Stage316. |
