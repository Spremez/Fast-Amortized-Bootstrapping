# Stage205 Current Platform Probe

Decision: `PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB`.

Stage205 moves the active loop back to executable evidence. The primary
complete-SAB metric is amortized latency per processed lane,
`T_bootstrap / r`; for same-r comparison this equals the total-time ratio
between repeated scalar SAB and one PVW/MAT-SAB run.

## Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage205_platform | PASS_WITH_PERF_BLOCKED | platform_gates | 4 | repro/stage205_current_platform_probe/platform_gate.csv | WSL/spqlios_avx512 is usable for smoke/A-B, but perf counter attribution is blocked. | Install perf or rerun on native Linux for hardware-counter conclusions. |
| stage205_current_smoke | PASS | smoke_rows | 4 | repro/stage205_current_platform_probe/stage98_current_smoke/summary.csv | Current-head scalar and explicit PVW smoke gates pass. | Use this only as runnability evidence. |
| stage205_full_sab_ab | PASS_SMALL_SAMPLE | ab_rows | 2 | repro/stage205_current_platform_probe/full_sab_ab_summary.csv | Sequential r=2/r=4 complete-SAB A/B shows positive T_bootstrap/r speedup under same backend. | Run high-stat A/B and noise gates before upgrading claim level. |
| stage205_invalid_parallel_rejection | PASS_REJECTED_INVALID | invalid_rows | 2 | repro/stage205_current_platform_probe/invalid_run_log.csv | Concurrent benchmark outputs are excluded due shared build/main race. | Do not run make-based benchmark variants in parallel in one worktree. |
| stage205_decision | PASS_STAGE205_CURRENT_PLATFORM_SMALL_SAMPLE_AB | goal_status | active | repro/stage205_current_platform_probe/proof_gate.csv | Current-head execution moved from metadata-only back to concrete A/B evidence, with strict claim boundary. | Proceed to high-stat current-head A/B or perf-counter attribution. |

## Platform Gates

| gate | status | evidence | detail | impact |
| --- | --- | --- | --- | --- |
| wsl_toolchain | PASS | repro/stage205_current_platform_probe/stage28_perf_smoke/environment.log | cpu_model=11th Gen Intel(R) Core(TM) i7-11700 @ 2.50GHz; perf_event_paranoid=2 | WSL can run current-head smoke and same-backend small-sample A/B. |
| avx512_vaes_flags | PASS | repro/stage205_current_platform_probe/stage28_perf_smoke/environment.log | CPU flags expose avx512 and vaes under WSL. | spqlios_avx512 path is admissible for smoke/small-sample A/B. |
| hardware_perf_counters | BLOCKED | repro/stage205_current_platform_probe/stage28_perf_smoke/summary.csv | MISSING | MAT-AVX512 load/store/FMA attribution remains blocked on this WSL image because perf is missing. |
| current_head_smoke | PASS_STAGE98_CURRENT_HEAD_SMOKE_REFRESH | repro/stage205_current_platform_probe/stage98_current_smoke/summary.csv | scalar binary full run, explicit active-buffer PVW gate, explicit backend PVW gate, and scalar ternary build pass. | Current HEAD is runnable before interpreting A/B samples. |

## Complete-SAB A/B

| r | status | runs | backend | param | metric | pvw_total_mean_us | scalar_repeated_total_mean_us | pvw_per_lane_mean_us | scalar_repeated_per_lane_mean_us | mean_of_run_speedups | min_speedup | max_speedup | ratio_of_mean_per_lane | claim_level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PASS | 3 | spqlios_avx512 | SET_2_3_2048 | T_bootstrap_over_r | 15836333.000 | 20155496.667 | 7918166.500 | 10077748.333 | 1.273000 | 1.256000 | 1.284000 | 1.272738 | current_head_small_sample_only |
| 4 | PASS | 3 | spqlios_avx512 | SET_2_3_2048 | T_bootstrap_over_r | 29313274.667 | 39428296.667 | 7328318.667 | 9857074.167 | 1.345000 | 1.336000 | 1.350000 | 1.345066 | current_head_small_sample_only |

## Rejected Invalid Run

| invalid_id | status | expected_r | observed_r_values | reason | evidence |
| --- | --- | --- | --- | --- | --- |
| parallel_race_labeled_r2 | REJECTED | 2 | 4;4;4 | r2 and r4 builds were launched concurrently in one workspace and raced on build/main; outputs are preserved but excluded. | repro/stage205_current_platform_probe/invalid_parallel_race_labeled_r2/summary.csv |
| parallel_race_labeled_r4 | REJECTED | 4 | 4;4;4 | r2 and r4 builds were launched concurrently in one workspace and raced on build/main; outputs are preserved but excluded. | repro/stage205_current_platform_probe/invalid_parallel_race_labeled_r4/summary.csv |

## Proof Gates

| gate | status | evidence | detail | remaining_gap |
| --- | --- | --- | --- | --- |
| G1_platform | PASS_WITH_PERF_BLOCKED | repro/stage205_current_platform_probe/platform_gate.csv | WSL/spqlios_avx512 can run smoke and A/B; hardware counters are unavailable. | Install Linux perf or rerun on native Linux for load/store/FMA attribution. |
| G2_current_head_smoke | PASS | repro/stage205_current_platform_probe/stage98_current_smoke/summary.csv | Current scalar/default and explicit PVW paths pass smoke. | Smoke is not a speed claim. |
| G3_complete_sab_ab_small_sample | PASS_SMALL_SAMPLE | repro/stage205_current_platform_probe/full_sab_ab_summary.csv | Sequential r=2/r=4 complete-SAB A/B uses T_bootstrap/r under the same backend. | Increase runs/seeds and separate noise instrumentation before paper-grade claims. |
| G4_invalid_parallel_run_rejected | PASS_REJECTED_INVALID | repro/stage205_current_platform_probe/invalid_run_log.csv | Concurrent make/main race output is preserved but excluded. | Run build-and-benchmark jobs sequentially or isolate worktrees. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | high_stat_current_head_ab | Use isolated sequential worktree/build directories or single-run serialization. | 10+ complete-SAB runs for r=2/r=4 and 20+ noise seeds with T_bootstrap/r endpoint. | ready | repro/stage205_current_platform_probe/full_sab_ab_summary.csv |
| P1 | perf_counter_attribution | Linux perf is installed and hardware counters are usable. | Record cycles, instructions, cache, load/store/FMA proxy counters for scalar vs MAT paths. | blocked_perf_missing | repro/stage205_current_platform_probe/platform_gate.csv |
| P2 | full_text_anchor_table | Reviewed 2025/686 full text is available. | Map SAB equations and reported complexity to paper anchors. | waiting_full_text | repro/stage204_source_anchor_intake/proof_gate.csv |
