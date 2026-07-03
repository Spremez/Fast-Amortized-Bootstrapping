# Stage178 Full-MAT Per-Bit Frontier

Decision: `PASS_STAGE178_FULLMAT_PERBIT_FRONTIER_SELECT_MAT_EP_AUDIT`.

Stage178 re-normalizes the current exact PVW/MAT-SAB evidence around the metric
the user requested: `T_bootstrap/r`, i.e. complete bootstrapping time divided by
the number of processed lanes/bits.

Current complete-SAB result:

- r = 6
- PVW/MAT-SAB mean: `10465305.389000000 us/lane`
- repeated scalar mean: `11837759.166666666 us/lane`
- speedup mean/min/CI95-low: `1.131666667x / 1.115000000x / 1.095041982x`

The next executable route is not compact SAB. Stage176/177 block that. The
only exact full-MAT target large enough to justify work is a bounded
microarchitecture audit of `mat_ep_subdecomp`.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage178_inputs | PASS | required_inputs_present | 1 | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv; repro/stage170_native_split_counter_microbench/run_metrics.csv; repro/stage177_verified_literature_novelty_gate/summary.csv | Stage178 consumes complete-SAB repeated evidence, split component counters, and literature/security routing. | Repair missing inputs before candidate selection. |
| stage178_perbit_endpoint | PASS | mean_speedup;min_speedup;ci95_low | 1.131666667;1.115000000;1.095041982 | repro/stage178_fullmat_perbit_frontier/per_bit_throughput.csv | Current exact full-MAT r=6 claim is T_bootstrap/r versus repeated scalar. | Do not report any other speedup dimension as final SAB acceleration. |
| stage178_component_attribution | PASS | hot_share;mat_share;from_dft_share;residual_share | 0.925461377;0.603899465;0.321561912;0.074538623 | repro/stage178_fullmat_perbit_frontier/component_attribution.csv | Split MAT EP/subdecomp plus from_DFT explains most of current complete-SAB runtime. | Primary exact-path work must target these components. |
| stage178_candidate_selection | PASS_SELECT_AUDIT | selected_candidate | C1_mat_ep_subdecomp_microarch_audit | repro/stage178_fullmat_perbit_frontier/candidate_matrix.csv | Select an audit, not immediate code. Prior layout/backend retuning had neutral/rejected gates. | Stage179 must produce a concrete mechanism or stop. |
| stage178_decision | PASS_STAGE178_FULLMAT_PERBIT_FRONTIER_SELECT_MAT_EP_AUDIT | route | stage179_mat_ep_audit | repro/stage178_fullmat_perbit_frontier/summary.csv | Avoid theory loop: compact remains blocked; next exact-path action is a bounded MAT EP microarchitecture audit. | Run Stage179. |

## Per-Bit Throughput

| metric | value | unit | evidence | interpretation |
| --- | --- | --- | --- | --- |
| pvw_full_bootstrap_mean_us | 62791832.333333336 | us | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | Time for one exact full-MAT PVW/MAT-SAB bootstrap carrying r lanes. |
| pvw_T_bootstrap_over_r_mean_us | 10465305.389000000 | us_per_lane | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | Primary amortized endpoint for the current exact path. |
| scalar_repeated_full_mean_us | 71026555.000000000 | us | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | Repeated scalar baseline for r independent lanes. |
| scalar_T_bootstrap_over_r_mean_us | 11837759.166666666 | us_per_lane | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | Scalar repeated baseline normalized per processed lane. |
| speedup_vs_scalar_repeated_mean | 1.131666667 | x | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | Mean complete-SAB T_bootstrap/r speedup. |
| speedup_vs_scalar_repeated_min | 1.115000000 | x | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | Conservative repeated-run minimum speedup. |
| speedup_vs_scalar_repeated_ci95_low | 1.095041982 | x | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | CI lower bound used for cautious claim wording. |

## Component Attribution

| component | per_call_us | estimated_full_us | share_of_pvw_full | source | interpretation |
| --- | --- | --- | --- | --- | --- |
| mat_ep_subdecomp | 66.127151855 | 37919953.959731199 | 0.603899465 | repro/stage170_native_split_counter_microbench/run_metrics.csv | Largest exact-path component; includes sub-decompose and MAT DFT addmul. |
| from_dft_materialize | 35.211114746 | 20191461.639946241 | 0.321561912 | repro/stage170_native_split_counter_microbench/run_metrics.csv | Second-largest exact-path component; Stage174 direct-scale attempt was neutral. |
| split_hot_components_total | 101.338266601 | 58111415.599677444 | 0.925461377 | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv; repro/stage170_native_split_counter_microbench/run_metrics.csv | Explains most of full-SAB time; good sanity check for attribution. |
| residual_setup_extract_ks_profile_gap |  | 4680416.733655892 | 0.074538623 | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | Too small to be the primary next optimization target unless a specific bug is found. |

## Amdahl Bounds

| component | component_speedup | share_of_pvw_full | full_sab_speedup_bound | interpretation |
| --- | --- | --- | --- | --- |
| mat_ep_subdecomp | 1.050000000 | 0.603899465 | 1.029608575 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| mat_ep_subdecomp | 1.100000000 | 0.603899465 | 1.058089037 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| mat_ep_subdecomp | 1.250000000 | 0.603899465 | 1.137371623 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| mat_ep_subdecomp | 1.500000000 | 0.603899465 | 1.252034277 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| mat_ep_subdecomp | 2.000000000 | 0.603899465 | 1.432561588 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| from_dft_materialize | 1.050000000 | 0.321561912 | 1.015550590 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| from_dft_materialize | 1.100000000 | 0.321561912 | 1.030113197 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| from_dft_materialize | 1.250000000 | 0.321561912 | 1.068732749 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| from_dft_materialize | 1.500000000 | 0.321561912 | 1.120055757 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| from_dft_materialize | 2.000000000 | 0.321561912 | 1.191584017 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| split_hot_components_total | 1.050000000 | 0.925461377 | 1.046101253 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| split_hot_components_total | 1.100000000 | 0.925461377 | 1.091861415 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| split_hot_components_total | 1.250000000 | 0.925461377 | 1.227132803 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| split_hot_components_total | 1.500000000 | 0.925461377 | 1.446104674 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| split_hot_components_total | 2.000000000 | 0.925461377 | 1.861263948 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| residual_setup_extract_ks_profile_gap | 1.050000000 | 0.074538623 | 1.003562102 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| residual_setup_extract_ks_profile_gap | 1.100000000 | 0.074538623 | 1.006822469 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| residual_setup_extract_ks_profile_gap | 1.250000000 | 0.074538623 | 1.015133328 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| residual_setup_extract_ks_profile_gap | 1.500000000 | 0.074538623 | 1.025479271 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |
| residual_setup_extract_ks_profile_gap | 2.000000000 | 0.074538623 | 1.038712084 | Amdahl bound relative to current exact PVW/MAT-SAB, not scalar baseline. |

## Candidate Matrix

| candidate | target | full_time_share | prior_evidence | decision | reason | gate |
| --- | --- | --- | --- | --- | --- | --- |
| C1_mat_ep_subdecomp_microarch_audit | mat_trgsw_mul_pvmtmlwe_sub_DFT exact r=6 tiled path | 0.603899465 | repro/stage159_sub_decomp_fusion_repeated_gate/summary.csv; repro/stage165_closed_fullmat_streaming_microbench/summary.csv | SELECT_FOR_STAGE179_AUDIT_ONLY | Largest remaining exact-path share. Code changes require a new load/store/FMA mechanism because sub-decomp fusion already exists and streaming lost. | Do not implement unless audit projects >=3% complete-SAB improvement and preserves exact PVW_TMLWE closure. |
| C2_from_dft_materialize_backend | pvmtmlwe_from_DFT_add / materialization | 0.321561912 | repro/stage174_from_dft_direct_scale_gate/comparison.csv | DEFER | Large share but direct AVX512 scale/copy gate was neutral; count reduction needs representation change, currently blocked. | Reopen only with a new mechanism beyond direct-scale or with closed representation proof. |
| C3_r6_layout_retuning | fulltile/bodymajor/streaming layout variants | 0.603899465 | repro/stage154_bodymajor_fullsab_closeout/summary.csv; repro/stage165_closed_fullmat_streaming_microbench/summary.csv | REJECT_RETUNING_WITHOUT_NEW_MECHANISM | Fulltile/bodymajor/streaming were already neutral or rejected at full-SAB/microbench gates. | No new branch unless it changes arithmetic/dataflow, not just layout naming. |
| C4_tail_postprocessing | setup/extract/packing KS/residual | 0.074538623 | repro/stage178_fullmat_perbit_frontier/component_attribution.csv | DEFER | Residual is small relative to MAT EP/from_DFT; tail-only work cannot materially move T_bootstrap/r. | Reopen only if new profile shows residual >15%. |
| C5_structured_compact | compact selector/representation |  | repro/stage177_verified_literature_novelty_gate/summary.csv | BLOCKED_BY_STAGE176_177 | Potentially higher algorithmic upside but no implementation permission or strong novelty claim. | Only proof/literature work, no SAB code. |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 179 | MAT EP/subdecomp microarchitecture audit | Stage178 selects C1 as audit-only candidate. | Find a concrete load/store/FMA/dataflow mechanism with projected >=3% complete-SAB gain, or reject. | If no mechanism is found, do not write code; record negative frontier. |
| P1 | 180 | exact-path implementation gate | Stage179 produces a concrete mechanism. | Implement behind a flag, run correctness, microbench, full-SAB repeated A/B, noise/resource. | Neutral/reject if complete-SAB T_bootstrap/r does not improve. |
| P2 | 181 | negative frontier package | Stage179 finds no viable exact-path mechanism. | Write the remaining-headroom and blocked-route report. | Do not continue speculative exact-path tuning. |
