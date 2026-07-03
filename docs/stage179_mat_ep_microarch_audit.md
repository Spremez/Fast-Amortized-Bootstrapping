# Stage179 MAT EP Microarchitecture Audit

Decision: `PASS_STAGE179_AUDIT_SELECT_MAT_EP_SPLIT_PROBE_NO_CODE`.

Stage179 answers a narrow question: is the current project missing a complete
MAT-aware AVX512 external-product implementation? No. The current r=6/r=8 path
already uses a MAT-aware AVX512 tiled kernel, and prior r=6 fulltile/bodymajor
variants have been tested.

The unresolved performance question is narrower: inside
`mat_trgsw_mul_pvmtmlwe_sub_DFT`, how much time is spent in
`mat_trgsw_sub_decompose`, row `torus_to_DFT`, and tiled addmul? Stage179 does
not grant code permission until Stage180 measures those subcomponents.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage179_inputs | PASS | stage178_and_code_present | 1 | repro/stage178_fullmat_perbit_frontier/summary.csv; src/mosfhet/src/mattrgsw.c | Stage179 consumes Stage178 frontier and current MAT external-product source. | Repair missing inputs before audit. |
| stage179_avx512_completeness | PASS_ALREADY_PRESENT | rgt4_tiled;r6_fulltile;r6_bodymajor | present;present;present | repro/stage179_mat_ep_microarch_audit/code_facts.csv | MAT-aware AVX512 implementations for the current r=6 path and prior variants already exist. | Do not claim the project lacks MAT AVX512; the issue is whether any remaining exact-path mechanism exists. |
| stage179_no_direct_code_permission | DENY_CODE_NOW | split_subcomponent_data_available | 0 | repro/stage179_mat_ep_microarch_audit/mechanism_screen.csv | The combined MAT EP/subdecomp block is hot, but internal shares are not split enough to justify code. | Run Stage180 split probe before implementation. |
| stage179_decision | PASS_STAGE179_AUDIT_SELECT_MAT_EP_SPLIT_PROBE_NO_CODE | route | stage180_mat_ep_split_probe | repro/stage179_mat_ep_microarch_audit/summary.csv | Avoid theory loop and blind retuning: the next step is a measurement probe, not another speculative AVX512 variant. | Run Stage180. |

## Code Facts

| fact | source | status | evidence | implication |
| --- | --- | --- | --- | --- |
| current_r_gt4_tiled_avx512_exists | src/mosfhet/src/mattrgsw.c | PRESENT | Current r=6/r=8 exact path has a MAT-aware AVX512 tiled output kernel. | The project is not missing a basic MAT-aware AVX512 external-product implementation. |
| r6_fulltile_variant_exists | src/mosfhet/src/mattrgsw.c | PRESENT | Full-output r=6 tile variant exists behind MAT_TRGSW_AVX512_R6_FULLTILE. | All-output register residency has already been tested and was not promoted. |
| r6_bodymajor_variant_exists | src/mosfhet/src/mattrgsw.c | PRESENT | Body-major r=6 variant exists behind MAT_TRGSW_AVX512_R6_BODYMAJOR. | Pure layout retuning has prior negative full-SAB evidence. |
| sub_decompose_is_separate_scalar_loop | src/mosfhet/src/mattrgsw.c | PRESENT | mat_trgsw_sub_decompose computes diff/offset/shift/mask into scratch->dec before DFT. | The remaining unmeasured mechanism is not another MAT multiply layout; it is subcomponent split and possible vectorized decompose/DFT dataflow. |
| sub_decompose_then_dft_then_addmul_boundary | src/mosfhet/src/mattrgsw.c | PRESENT | mat_trgsw_mul_pvmtmlwe_sub_DFT decomposes to scratch, converts every row to DFT, then calls the AVX512 addmul kernel. | Stage180 must split these three phases before deciding whether a code change is justified. |
| explicit_flags_exist | src/mosfhet/Makefile.def | PRESENT | All relevant exact MAT variants are controlled by explicit flags. | Any Stage180+ implementation must stay behind a flag and preserve scalar/default behavior. |

## Mechanism Screen

| mechanism | status | evidence | reason | required_gate |
| --- | --- | --- | --- | --- |
| M1_split_mat_ep_subcomponents | SELECT_FOR_STAGE180_PROBE | repro/stage178_fullmat_perbit_frontier/component_attribution.csv | Stage178 shows MAT EP/subdecomp is 60.39% of full time, but Stage170 only times the combined block. | Measure sub_decompose, torus_to_DFT rows, and tiled addmul separately before code. |
| M2_manual_avx512_sub_decompose | CONDITIONAL | src/mosfhet/src/mattrgsw.c | The decompose loop is scalar-looking, but its actual share is unknown. | Only implement if Stage180 shows enough share for >=3% full-SAB projection. |
| M3_fulltile_or_bodymajor_retuning | REJECT_NO_NEW_MECHANISM | repro/stage111_r6_fulltile_repeated_gate/summary.csv; repro/stage154_bodymajor_fullsab_closeout/summary.csv | Fulltile/bodymajor variants exist and were not promoted at complete-SAB gates. | Do not reopen without a different arithmetic/dataflow mechanism. |
| M4_streaming_row_dft | REJECT_NO_NEW_MECHANISM | repro/stage165_closed_fullmat_streaming_microbench/summary.csv | Closed full-MAT streaming was slower than current tiled AVX. | Do not reopen row-streaming unless the addmul locality problem is changed. |
| M5_from_dft_direct_scale | DEFER | repro/stage174_from_dft_direct_scale_gate/summary.csv | Stage174 direct-scale was neutral and is outside the selected MAT EP/subdecomp block. | Reopen only with a new from_DFT mechanism. |

## Projection Requirements

| target_full_sab_speedup | mat_ep_share | required_mat_ep_component_speedup | interpretation |
| --- | --- | --- | --- |
| 1.010000 | 0.603899465 | 1.016668376 | Minimum component speedup over the current MAT EP/subdecomp block needed to reach target full-SAB gain. |
| 1.020000 | 0.603899465 | 1.033558316 | Minimum component speedup over the current MAT EP/subdecomp block needed to reach target full-SAB gain. |
| 1.030000 | 0.603899465 | 1.050674268 | Minimum component speedup over the current MAT EP/subdecomp block needed to reach target full-SAB gain. |
| 1.050000 | 0.603899465 | 1.085602596 | Minimum component speedup over the current MAT EP/subdecomp block needed to reach target full-SAB gain. |
| 1.100000 | 0.603899465 | 1.177214029 | Minimum component speedup over the current MAT EP/subdecomp block needed to reach target full-SAB gain. |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 180 | MAT EP split probe | Stage179 selects split probe and denies code now. | Measure sub_decompose, torus_to_DFT, and tiled addmul inside mat_trgsw_mul_pvmtmlwe_sub_DFT. | If no subcomponent can project >=3% full-SAB gain, close exact-path tuning. |
| P1 | 181 | conditional AVX512 sub-decompose implementation | Stage180 shows sub_decompose share is large enough. | Implement behind flag, pass correctness, microbench, full-SAB repeated A/B. | Reject if full-SAB T_bootstrap/r does not improve. |
| P2 | 182 | negative frontier | Stage180 does not identify an implementable mechanism. | Record remaining exact-path headroom and stop blind optimization. | Do not retune old fulltile/bodymajor/streaming candidates. |
