# Stage207 Current-Head Resource Refresh

Decision: `PASS_STAGE207_CURRENT_HEAD_RESOURCE_REFRESH`.

Stage207 refreshes the resource side of the current-head PVW/MAT-SAB evidence.
It is paired with Stage206 complete-SAB throughput results, but resource
instrumentation remains separate from latency claims.

## Resource And Throughput Link

| r | backend | param | throughput_speedup_T_bootstrap_over_r | key_bytes_ratio | keygen_per_lane_ratio | time_max_rss_ratio | internal_vmhwm_ratio | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | spqlios_avx512 | SET_2_3_2048 | 1.299817 | 1.013617 | 1.101017 | 0.989539 | 0.990118 | single_resource_sample_cost_refresh |
| 4 | spqlios_avx512 | SET_2_3_2048 | 1.356445 | 1.065349 | 1.197131 | 0.997004 | 0.997138 | single_resource_sample_cost_refresh |

## Gates

| gate | status | evidence | detail | remaining_gap |
| --- | --- | --- | --- | --- |
| G1_resource_raw | PASS | repro/stage207_current_head_resource_refresh/summary.csv | Current-head r=2/r=4 PVW and repeated-scalar resource rows exist. | Single sample only; use as cost refresh, not statistical resource distribution. |
| G2_cost_bound | PASS_COST_BOUNDED | repro/stage207_current_head_resource_refresh/resource_comparison.csv | PVW key bytes stay within 1.10x repeated scalar and max RSS is not higher in this sample. | Keygen per lane is slower and must be reported with throughput claims. |
| G3_throughput_with_cost | PASS_THROUGHPUT_COST_RECORDED | repro/stage207_current_head_resource_refresh/resource_comparison.csv | Stage206 T_bootstrap/r speedup is linked to Stage207 resource costs for the same current-head path. | This does not prove AVX512 optimality, novelty, or broader branch support. |
| G4_decision | PASS_STAGE207_CURRENT_HEAD_RESOURCE_REFRESH | repro/stage207_current_head_resource_refresh/proof_gate.csv | Resource refresh is sufficient for current-head engineering reporting. | Profile attribution and full-text theorem anchors remain separate gates. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | profile_attribution_refresh | Stage206 high-stat throughput and Stage207 resource costs are recorded. | Attribute remaining full-SAB time to MAT EP, CMUX/NCMUX, sub_a, extract/KS. | ready | repro/stage207_current_head_resource_refresh/proof_gate.csv |
| P1 | native_or_remote_perf_counters | Native Linux/perf or CB host is available. | Load/store/FMA counter attribution for MAT-aware AVX512. | blocked_on_perf_access | repro/stage205_current_platform_probe/platform_gate.csv |
| P2 | full_text_anchor_table | Reviewed 2025/686 full text is available. | Map exact SAB equations and theorem claims to source anchors. | waiting_full_text | repro/stage204_source_anchor_intake/proof_gate.csv |
