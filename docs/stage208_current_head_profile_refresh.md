# Stage208 Current-Head Profile Refresh

Decision: `PASS_STAGE208_CURRENT_HEAD_PROFILE_ATTRIBUTION`.

Stage208 records profile-only attribution for the current explicit
PVW/MAT-SAB path. These timings are used for route selection, not for final
latency claims.

## Component Attribution

| r | status | pvw_profile_speedup | cmux_calls | ncmux_calls | copyback_calls | copyback_saved_vs_legacy | mat_ep_pct_of_cmux | from_dft_pct_of_cmux | cmux_sub_pct_of_cmux | cmux_add_pct_of_cmux | postproc_tail_pct_max | primary_bottleneck |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PASS | 1.285 | 573440 | 5080 | 0 | 40 | 40.879 | 25.869 | 16.657 | 15.799 | 1.218 | mat_ep |
| 4 | PASS | 1.372 | 573440 | 5080 | 0 | 40 | 47.760 | 23.419 | 14.169 | 14.330 | 1.222 | mat_ep |

## Gates

| gate | status | evidence | detail | remaining_gap |
| --- | --- | --- | --- | --- |
| G1_profile_counts | PASS | repro/stage208_current_head_profile_refresh/component_attribution.csv | CMUX, NCMUX, MAT EP, sub_a, and active-buffer copyback counts match the current target schedule. | Profile timing is instrumentation evidence only. |
| G2_component_attribution | PASS_MAT_EP_REMAINS_PRIMARY | repro/stage208_current_head_profile_refresh/component_attribution.csv | MAT EP is the largest CMUX subcomponent, with from_DFT, subtract, and add still material. | Hardware counters are still needed for load/store/FMA attribution. |
| G3_postproc_filter | PASS_POSTPROC_DEFER | repro/stage208_current_head_profile_refresh/component_attribution.csv | Post-processing tail remains below the 2 percent implementation threshold. | Do not spend hot-path effort on extract/KS unless body path changes the tail share. |
| G4_decision | PASS_STAGE208_CURRENT_HEAD_PROFILE_ATTRIBUTION | repro/stage208_current_head_profile_refresh/proof_gate.csv | Current-head profile attribution is recorded and routes next work away from postproc-only tuning. | Next executable route needs a new MAT EP/from_DFT dataflow mechanism or native counters. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | mat_ep_split_or_counter_refresh | Stage208 shows MAT EP is the largest CMUX subcomponent. | Use native/perf counters if available; otherwise run a bounded split microbench before code. | ready_but_counter_limited | repro/stage208_current_head_profile_refresh/component_attribution.csv |
| P1 | from_dft_dataflow_preflight | from_DFT remains material but prior direct-scale variants were neutral. | Require a specific new dataflow mechanism before implementation. | preflight_only | repro/stage208_current_head_profile_refresh/component_attribution.csv |
| P2 | postproc_deferred | postproc tail max is below 2 percent in Stage208. | Reopen only if future body optimizations raise postproc share. | deferred | repro/stage208_current_head_profile_refresh/component_attribution.csv |
