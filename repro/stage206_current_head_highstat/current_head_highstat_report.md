# Stage206 Current-Head High-Stat Evidence

Decision: `PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE`.

Stage206 is a high-stat current-head refresh for the existing explicit
active-buffer PVW/MAT-SAB path. The primary performance endpoint is
`T_bootstrap/r`, using same-backend repeated scalar SAB as the comparator.

## Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage206_performance | PASS_HIGHSTAT_CURRENT_HEAD | r_values | 2,4 | repro/stage206_current_head_highstat/performance_stats.csv | r=2/r=4 10-run complete-SAB A/B passes under T_bootstrap/r. | Use as current-head engineering evidence only. |
| stage206_noise | PASS_20SEED | noise_rows | 2 | repro/stage206_current_head_highstat/noise_stats.csv | r=2/r=4 final-output noise has 20 seeds each with zero failures. | Keep latency and noise evidence separated. |
| stage206_claim_boundary | PASS_BOUNDARY_RECORDED | blocked_claims | 4 | repro/stage206_current_head_highstat/proof_gate.csv | No hardware-counter, full-text theorem, resource-refresh, or broad-parameter claim is made here. | Proceed to resource/profile refresh or external unblockers. |
| stage206_decision | PASS_STAGE206_CURRENT_HEAD_HIGHSTAT_AB_NOISE | goal_status | active | repro/stage206_current_head_highstat/summary.csv | Stage206 strengthens complete-SAB evidence for current-head active-buffer PVW/MAT-SAB. | Continue with resource/profile/full-text gates; keep full research goal active. |

## Performance Statistics

| r | status | runs | backend | param | metric | pvw_per_lane_mean_us | scalar_repeated_per_lane_mean_us | mean_of_run_speedups | speedup_sd | ci95_low | ci95_high | min_speedup | max_speedup | ratio_of_mean_per_lane | claim_level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PASS_10RUN | 10 | spqlios_avx512 | SET_2_3_2048 | T_bootstrap_over_r | 7745747.650 | 10068053.650 | 1.300000 | 0.032907 | 1.276461 | 1.323539 | 1.237000 | 1.352000 | 1.299817 | current_head_highstat_engineering_evidence |
| 4 | PASS_10RUN | 10 | spqlios_avx512 | SET_2_3_2048 | T_bootstrap_over_r | 7377682.175 | 10007418.000 | 1.356900 | 0.032949 | 1.333331 | 1.380469 | 1.294000 | 1.402000 | 1.356445 | current_head_highstat_engineering_evidence |

## Noise Statistics

| r | status | seeds | points | pvw_failures | scalar_failures | pair_failures | min_pvw_minus_scalar_log2 | max_pvw_minus_scalar_log2 | avg_pvw_minus_scalar_log2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PASS_20SEED | 20 | 81920 | 0 | 0 | 0 | -0.514 | 0.532 | -0.089650 |
| 4 | PASS_20SEED | 20 | 163840 | 0 | 0 | 0 | -0.433 | 0.174 | -0.106500 |

## Proof Gates

| gate | status | evidence | detail | remaining_gap |
| --- | --- | --- | --- | --- |
| G1_raw_run_complete | PASS | repro/stage206_current_head_highstat/full_sab_ab_r2_runs10/summary.csv; repro/stage206_current_head_highstat/full_sab_ab_r4_runs10/summary.csv; repro/stage206_current_head_highstat/final_noise_seeds20/aggregate.csv | r=2/r=4 performance and final-output noise raw outputs exist. | None for Stage206 raw execution. |
| G2_performance_10run | PASS_HIGHSTAT_CURRENT_HEAD | repro/stage206_current_head_highstat/performance_stats.csv | Both r=2 and r=4 have 10 correctness-passing complete-SAB A/B samples with min speedup > 1. | Still WSL/current-head engineering evidence, not hardware-counter or paper-level proof. |
| G3_noise_20seed | PASS_20SEED | repro/stage206_current_head_highstat/noise_stats.csv | Both r=2 and r=4 have 20 seeds with zero PVW/scalar/pair failures. | Noise-instrumented runs are not latency evidence. |
| G4_claim_boundary | PASS_BOUNDARY_RECORDED | theory_checks/stage206_statistical_claim_boundary.md | Stage206 supports current-head complete-SAB throughput and noise only. | perf counters, full-text theorem anchors, resource refresh, and broader parameter/branch claims remain separate gates. |

## Next Queue

| priority | route | entry_condition | gate | current_status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | resource_refresh | Use current HEAD and same backend after Stage206 high-stat pass. | Record key size, RSS/memory, and keygen cost for r=2/r=4 under current promoted explicit path. | ready | repro/stage206_current_head_highstat/proof_gate.csv |
| P1 | profile_attribution_refresh | Run profile-only instrumentation separately from latency runs. | Attribute remaining time to MAT EP, CMUX/NCMUX, sub_a, extract/KS without mixing profile timing into speed claims. | ready | repro/stage206_current_head_highstat/performance_stats.csv |
| P2 | perf_counter_attribution | Linux perf is installed or native Linux is available. | Hardware-counter load/store/FMA attribution for MAT-aware AVX512. | blocked_perf_missing | repro/stage205_current_platform_probe/platform_gate.csv |
| P3 | full_text_anchor_table | Reviewed 2025/686 full text is available. | Map exact SAB equations, theorem claims, and reported experiments to paper anchors. | waiting_full_text | repro/stage204_source_anchor_intake/proof_gate.csv |
