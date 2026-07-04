# Stage228 Counter-Driven Backend Kernel Search

Decision: `PASS_STAGE228_NO_NEW_HOTPATH_CODE_SELECT_PARAMETER_MATRIX`.

Stage228 reopens the exact MAT/PVW kernel question only as a falsifiable
candidate search. It does not implement new hot-path code because the current
counter signal is small and prior frontier gates already reject layout-only
retuning. The primary endpoint remains complete SAB `T_bootstrap/r`.

## Source Facts

| fact | status | evidence | interpretation |
| --- | --- | --- | --- |
| rgt4_tiled_avx512_present | present | src/mosfhet/src/mattrgsw.c | Current r=6/r=8 exact route already has MAT-aware tiled AVX512. |
| r6_fulltile_present | present | src/mosfhet/src/mattrgsw.c | Full-output r=6 layout exists and was previously screened. |
| r6_bodymajor_present | present | src/mosfhet/src/mattrgsw.c | Body-major r=6 layout exists and was previously screened. |
| backend_from_dft_add_present | present | src/mosfhet/src/pvwtmlwe.c | Current preferred path uses backend direct FromDFT+add. |
| backend_direct_add_primitive_present | present | src/mosfhet/src/polynomial.c | SPQLIOS backend has direct IFFT+add primitive already wired. |
| sub_decomp_fusion_present | present | src/mosfhet/Makefile.def; src/mosfhet/src/mattrgsw.c | Sub-decompose fusion path exists as an explicit flag. |

## Projection Thresholds

| component | share | required_local_speedup_for_3pct_full_sab | current_signal | evidence |
| --- | --- | --- | --- | --- |
| addmul_from_dec_dft | 0.221723249 | 1.151228774 | Stage183 denies layout-only code; Stage226 shows only backend materialization counter deltas. | repro/stage183_addmul_dataflow_screen/projection.csv; repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv |
| from_dft_materialization | 0.326046000 | 1.098094553 | Stage226 backend direct add is positive but already implemented; no new backend primitive exists. | repro/stage155_same_format_frontier_refresh/component_shares.csv; src/mosfhet/src/polynomial.c |
| sub_or_sub_decompose | 0.153191000 | 1.234766161 | Stage159 full-SAB fusion positive but Stage181 vectorizing sub-decompose itself is negative. | repro/stage159_sub_decomp_fusion_repeated_gate/perf_comparison.csv; repro/stage181_sub_decomp_avx512_gate/comparison.csv |

## Candidate Cards

| candidate_id | focused_module | hypothesis | required_evidence_before_code | current_evidence | code_permission | next_gate |
| --- | --- | --- | --- | --- | --- | --- |
| H228-C1-r6-dec-reuse-addmul | mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512 | A new r=6 dataflow that reduces duplicated dec-row loads across output tiles should improve addmul_from_dec_dft. | assembly/counter microprobe plus local addmul speedup >= 1.151228774 for 3pct full-SAB projection | Stage183 denies layout-only addmul code; fulltile/bodymajor/streaming variants already failed or were weak. | probe_only_no_hotpath_edit | static assembly + isolated addmul probe before any source modification |
| H228-C2-batched-direct-from-dft-add | pvmtmlwe_from_DFT_add / polynomial_DFT_to_torus_add | A true multi-row backend direct IFFT+add primitive could reduce materialization overhead beyond the current per-row direct add. | backend API or prototype showing local from_DFT speedup >= 1.098094553 for 3pct full-SAB projection | Stage226 supports current backend direct add, but Stage163/174-style backend retuning did not justify another blind path. | blocked_until_new_backend_primitive | backend primitive proof or external library support |
| H228-C3-sub-decomp-fusion-refresh | mat_trgsw_mul_pvmtmlwe_sub_DFT with SAB_PVW_SUB_DECOMP_FUSION | Combining existing sub-decomp fusion with the current exact backend path may still be worth a targeted refresh. | no new code; rerun existing flag only if current-head delta is unresolved; local sub speedup target 1.234766161 | Stage159 full-SAB positive; Stage181 exact AVX512 sub-decompose candidate negative, so new vector code is denied. | existing_flag_refresh_only | optional same-flags repeated refresh, not new implementation |

## Candidate Gates

| candidate_id | correctness_gate | performance_gate | failure_rule | status |
| --- | --- | --- | --- | --- |
| H228-C1-r6-dec-reuse-addmul | isolated dense MAT/PVW output equivalence r=6 plus full SAB deterministic correctness | isolated addmul >= projection threshold, then complete SAB T_bootstrap/r >= 1.03 over current backend control in 3 paired runs | If assembly/counter probe shows layout-only or projected gain <3pct, do not edit source. | not_selected_no_code_permission |
| H228-C2-batched-direct-from-dft-add | row-wise direct IFFT+add coefficient equality against current backend primitive | from_DFT local speedup >= projection threshold and complete SAB T_bootstrap/r positive under same backend | If no real backend primitive exists, keep blocked; do not emulate batching with extra copies. | blocked_external_backend_primitive |
| H228-C3-sub-decomp-fusion-refresh | existing SAB_PVW_SUB_DECOMP_FUSION deterministic full SAB correctness plus noise/resource if repeated | same current-head backend control, repeated complete SAB T_bootstrap/r; no new AVX512 sub-decompose code | If refresh is neutral or slower, close existing flag as non-default ablation. | deferred_existing_flag_refresh |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | inputs_present | true | repro/stage228_counter_driven_backend_kernel_search/input_status.csv | Stage228 consumes Stage227, Stage226, prior frontier gates, and current source. |
| G2_source_fact_check | PASS | facts_present | true | repro/stage228_counter_driven_backend_kernel_search/source_facts.csv | The project already has MAT-aware AVX512 and backend direct add paths. |
| G3_projection_gate | PASS | candidate_count | 3 | repro/stage228_counter_driven_backend_kernel_search/projection_thresholds.csv | Every code idea must clear a local speedup threshold before full-SAB work. |
| G4_code_permission | DENY_NEW_HOTPATH_CODE | allow_hotpath_edit_count | 0 | repro/stage228_counter_driven_backend_kernel_search/candidate_cards.csv | Stage228 does not permit speculative hot-path edits from the current evidence. |
| G5_stage228_decision | PASS_STAGE228_NO_NEW_HOTPATH_CODE_SELECT_PARAMETER_MATRIX | decision | PASS_STAGE228_NO_NEW_HOTPATH_CODE_SELECT_PARAMETER_MATRIX | repro/stage228_counter_driven_backend_kernel_search/proof_gate.csv | Move to parameter generalization unless a new counter-backed mechanism appears. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage229_parameter_generalization_matrix | Stage228 denies new exact hot-path code and Stage227 fixes T_bootstrap/r claim scope. | Run a parameter/branch matrix before broadening exact-route claims. | selected | Keep claims scoped to BINARY SET_2_3_2048 r=6. | repro/stage228_counter_driven_backend_kernel_search/proof_gate.csv |
| P1 | stage230_literature_novelty_audit | Before any paper novelty claim. | Source-verified related work; no fabricated references. | future | Engineering-only report. | repro/stage228_counter_driven_backend_kernel_search/candidate_cards.csv |
| P2 | stage231_new_backend_or_compact_proof_unlock | A new backend primitive or closed compact-state proof is supplied. | Proof or primitive first, then isolated tests, then full SAB. | blocked_until_new_evidence | Do not modify SAB hot path. | repro/stage228_counter_driven_backend_kernel_search/candidate_gates.csv |

## Inputs

| input | status | role | bytes |
| --- | --- | --- | --- |
| repro/stage227_exact_route_claim_boundary_update/proof_gate.csv | present | Stage227 fixed T_bootstrap/r claim boundary | 1368 |
| repro/stage227_exact_route_claim_boundary_update/next_stage_queue.csv | present | Stage227 selected Stage228 | 962 |
| repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | present | Stage226 native counter attribution | 1607 |
| repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv | present | Stage226 counter ratios | 1354 |
| repro/stage183_addmul_dataflow_screen/summary.csv | present | Prior addmul dataflow screen | 1161 |
| repro/stage183_addmul_dataflow_screen/mechanism_screen.csv | present | Prior exact addmul mechanism screen | 1702 |
| repro/stage183_addmul_dataflow_screen/projection.csv | present | Prior addmul projection threshold | 521 |
| repro/stage184_exact_route_closeout_claim_refresh/open_routes.csv | present | Prior exact-route closeout | 626 |
| repro/stage155_same_format_frontier_refresh/component_shares.csv | present | Prior component share frontier | 997 |
| repro/stage159_sub_decomp_fusion_repeated_gate/perf_comparison.csv | present | Prior sub-decomp fusion full-SAB gate | 473 |
| repro/stage181_sub_decomp_avx512_gate/comparison.csv | present | Prior AVX512 sub-decompose negative gate | 253 |
| src/mosfhet/src/mattrgsw.c | present | Current MAT external product source | 38109 |
| src/mosfhet/src/pvwtmlwe.c | present | Current PVW TMLWE materialization source | 33910 |
| src/mosfhet/src/polynomial.c | present | Current polynomial backend source | 19130 |
| src/mosfhet/Makefile.def | present | Current explicit build flags | 6791 |
| stage227_next_selects_stage228 | present | Prevents off-road kernel search. |  |
