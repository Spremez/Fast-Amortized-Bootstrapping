# Stage209 Current-Head MAT-EP Split Preflight

Decision: `PASS_STAGE209_CURRENT_HEAD_MAT_EP_SPLIT_PREFLIGHT`.

Stage209 splits the current r=2/r=4 MAT external-product block into
`sub_decompose`, `torus_to_dft_rows`, and `addmul_from_dec_dft`. It is a
preflight for route selection. It does not change production SAB code and does
not replace Stage206 complete-SAB latency evidence.

## Split Projection

| r | variant | per_call_us | combined_current_us | share_of_combined | estimated_full_sab_share | component_speedup_for_3pct_full_gain | route_value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | sub_decompose | 4.283314453 | 15.000221680 | 0.285550 | 0.111381 | 1.354099 | candidate |
| 2 | torus_to_dft_rows | 9.283705078 | 15.000221680 | 0.618905 | 0.241408 | 1.137206 | candidate |
| 2 | addmul_from_dec_dft | 2.991871094 | 15.000221680 | 0.199455 | 0.077799 | 1.598411 | candidate |
| 2 | split_sum_over_combined | 16.558890625 | 15.000221680 | 1.103910 |  |  | coverage_check |
| 4 | sub_decompose | 12.609452148 | 36.008648437 | 0.350178 | 0.160159 | 1.222282 | candidate |
| 4 | torus_to_dft_rows | 15.319426758 | 36.008648437 | 0.425437 | 0.194580 | 1.176038 | candidate |
| 4 | addmul_from_dec_dft | 12.594865234 | 36.008648437 | 0.349773 | 0.159974 | 1.222596 | candidate |
| 4 | split_sum_over_combined | 40.523744140 | 36.008648437 | 1.125389 |  |  | coverage_check |

## Gates

| gate | status | evidence | detail | remaining_gap |
| --- | --- | --- | --- | --- |
| G1_environment | PASS_COUNTER_BLOCKED_RECORDED | repro/stage209_current_head_mat_ep_split/environment.csv | WSL environment and perf availability are recorded. | Hardware counter claims remain blocked when perf is unavailable. |
| G2_build_run | PASS | repro/stage209_current_head_mat_ep_split/run_metrics.csv | r=2/r=4 split variants build and emit RESULT209 rows. | Microbench only; not complete-SAB latency evidence. |
| G3_correctness | PASS | repro/stage209_current_head_mat_ep_split/correctness.csv | Combined current equals split decompose -> DFT -> addmul for every r/variant run. | Does not prove alternative implementation correctness. |
| G4_projection | PASS_PREFLIGHT_CANDIDATES_RECORDED | repro/stage209_current_head_mat_ep_split/split_projection.csv | Split projection estimates which subcomponents can plausibly move complete SAB. | Any implementation still needs a flag-only code gate and complete-SAB A/B. |
| G5_decision | PASS_STAGE209_CURRENT_HEAD_MAT_EP_SPLIT_PREFLIGHT | repro/stage209_current_head_mat_ep_split/proof_gate.csv | Stage209 is a preflight gate; it grants route selection, not speedup claims. | Native counters and implementation gates remain separate. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | stage210_candidate_selection | Stage209 correctness and split projection pass. | Select a bounded implementation candidate, currently first=torus_to_dft_rows. | ready | repro/stage209_current_head_mat_ep_split/split_projection.csv |
| P1 | native_counter_refresh | perf/native Linux is available. | Collect load/store/FMA counters for the same r=2/r=4 split variants. | blocked_if_no_perf | repro/stage209_current_head_mat_ep_split/environment.csv |
| P2 | no_postproc_work | Stage208 postproc tail remains below threshold. | Keep extract/KS work deferred unless future body changes increase tail share. | deferred | repro/stage208_current_head_profile_refresh/component_attribution.csv |
