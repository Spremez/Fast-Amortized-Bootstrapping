# Stage210 Candidate Admission

Decision: `PASS_STAGE210_SELECT_DFT_ROWS_PREFLIGHT_NO_HOTPATH_CODE`.

Stage210 converts Stage209 split measurements into code-admission policy. The
largest current component is `torus_to_dft_rows`, but old same-format DFT
routes are not reopened because prior gates already rejected or neutralized
them.

## Candidate Matrix

| candidate | stage209_component | max_estimated_full_sab_share | min_component_speedup_for_3pct | decision | code_permission | next_gate |
| --- | --- | --- | --- | --- | --- | --- |
| C1_reopen_existing_dft_batching_or_direct_scale | torus_to_dft_rows | 0.241408 | 1.137206 | REJECT_REOPEN_OLD_MECHANISMS | denied | Only a new FFT/dataflow mechanism may proceed. |
| C2_new_multirow_fft_api_or_dft_dataflow | torus_to_dft_rows | 0.241408 | 1.137206 | ADMIT_PREFLIGHT_ONLY | preflight_only | Stage211 must inspect/build a bounded FFT/dataflow probe before production code. |
| C3_sub_decompose_avx512_or_fusion_reopen | sub_decompose | 0.160159 | 1.222282 | REJECT_DIRECT_REOPEN | denied | Native counter refresh may reopen if it shows a different mechanism. |
| C4_addmul_retiling_reopen | addmul_from_dec_dft | 0.159974 | 1.222596 | REJECT_WITHOUT_NEW_ASSEMBLY_COUNTER_MECHANISM | denied | Native counter or assembly-backed mechanism required. |

## Gates

| gate | status | evidence | detail | remaining_gap |
| --- | --- | --- | --- | --- |
| G1_stage209_input | PASS | repro/stage209_current_head_mat_ep_split/split_projection.csv | Stage209 split projection is present and current-head r=2/r=4 scoped. | Microbench route selection only. |
| G2_old_mechanism_guard | PASS_OLD_DFT_ROUTES_REJECTED | repro/stage210_candidate_admission/candidate_matrix.csv | Known DFT batching/direct-scale/subdecomp/addmul reopen routes are denied. | Does not block genuinely new FFT/dataflow preflights. |
| G3_candidate_selection | PASS_PREFLIGHT_SELECTED | repro/stage210_candidate_admission/candidate_matrix.csv | Selected preflight target C2_new_multirow_fft_api_or_dft_dataflow with max estimated full-SAB share 0.241408. | Hot-path implementation remains unauthorized until Stage211 preflight passes. |
| G4_decision | PASS_STAGE210_SELECT_DFT_ROWS_PREFLIGHT_NO_HOTPATH_CODE | repro/stage210_candidate_admission/proof_gate.csv | Stage210 routes to a bounded preflight instead of speculative hot-path implementation. | Implementation and complete-SAB A/B remain future gates. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | stage211_fft_dataflow_preflight | Stage210 admits only a new DFT/FFT dataflow preflight. | Produce a concrete probe or reject code permission. | ready | repro/stage210_candidate_admission/candidate_matrix.csv |
| P1 | native_counter_refresh | Native perf is available. | Collect counters for Stage209 split variants. | blocked_by_stage209_environment | repro/stage209_current_head_mat_ep_split/environment.csv |
| P2 | production_hotpath_code | Stage211 or native counters provides a new mechanism. | Flag-only implementation, correctness, noise/resource, full SAB A/B. | denied_now | repro/stage210_candidate_admission/proof_gate.csv |
