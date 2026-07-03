# Stage226 Exact MAT/PVW Counter Attribution

Decision: `PASS_STAGE226_EXACT_COUNTER_ATTRIBUTION_POSITIVE`.

Stage226 runs native perf counters for the two exact Stage224 variants:
`wrapper_fused_from_dft_add` and `backend_from_dft_add`. The primary
performance metric remains complete-SAB `T_bootstrap/r`; this stage only
checks whether native counters support a mechanism for the Stage224 timing
direction.

## Attribution Summary

| metric | value | interpretation | evidence |
| --- | --- | --- | --- |
| stage224_backend_vs_wrapper_mean_speedup | 1.024015000 | Fresh Stage224 complete-SAB per-lane timing; primary performance evidence. | repro/stage224_exact_pvw_mat_avx_resource_refresh/perf_comparison.csv |
| stage226_perf_run_backend_vs_wrapper_lane_speedup | 1.033292122 | Single native perf-stat run; mechanism evidence only, not a replacement for Stage224 repeated timing. | repro/stage226_exact_mat_avx_counter_attribution/run_metrics.csv |
| stage226_cycles_wrapper_over_backend | 1.017861569 | Values above 1 mean backend used fewer recorded cycles than wrapper. | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv |
| stage226_elapsed_wrapper_over_backend | 0.000000000 | Perf CSV may omit elapsed on this host; use lane timing and cycles for the Stage226 mechanism gate. | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv |
| stage226_loads_wrapper_over_backend | 1.011560486 | Values above 1 mean backend reduced retired loads. | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv |
| stage226_stores_wrapper_over_backend | 1.009880546 | Values above 1 mean backend reduced retired stores. | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv |
| stage226_load_store_per_cycle_wrapper_over_backend | 0.993217448 | Memory-op density comparison; not a standalone optimality proof. | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv |
| attribution_label | COUNTER_SUPPORTS_STAGE224_DIRECTION | Mechanism label is bounded to this exact-route native counter run. | repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv |

## Run Metrics

| variant | status | r | h | r_prec | reps | pvw_avg_us | pvw_lane_avg_us | scalar_repeated_avg_us | scalar_lane_avg_us | speedup_vs_scalar_repeated | source_log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backend_from_dft_add | Pass | 6 | 39 | 7 | 1 | 66520001.000 | 11086666.833 | 71314365.000 | 11885727.500 | 1.072 | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/run_backend_from_dft_add.log |
| wrapper_fused_from_dft_add | Pass | 6 | 39 | 7 | 1 | 68734593.000 | 11455765.500 | 71557125.000 | 11926187.500 | 1.041 | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/run_wrapper_fused_from_dft_add.log |

## Counter Summary

| variant | cycles | instructions | loads | stores | cache_references | cache_misses | fp512 | fp256 | elapsed_seconds | ipc | load_store_per_cycle | load_store_to_fp512 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| backend_from_dft_add | 991830854777 | 1650033998059 | 374112997913 | 209264677631 | 42087766794 | 14392218590 | 361110897498 | 67934709762 | 0.000000000 | 1.663624387 | 0.588182625 | 1.615508365 |
| wrapper_fused_from_dft_add | 1009546510314 | 1672973396511 | 378437925860 | 211332326920 | 41969149112 | 14228584316 | 360996742030 | 67928732142 | 0.000000000 | 1.657153365 | 0.584193246 | 1.633727356 |

## Counter Comparison

| metric | wrapper_value | backend_value | wrapper_over_backend | evidence |
| --- | --- | --- | --- | --- |
| cycles | 1009546510314 | 991830854777 | 1.017861569 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| instructions | 1672973396511 | 1650033998059 | 1.013902379 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| loads | 378437925860 | 374112997913 | 1.011560486 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| stores | 211332326920 | 209264677631 | 1.009880546 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| cache_references | 41969149112 | 42087766794 | 0.997181659 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| cache_misses | 14228584316 | 14392218590 | 0.988630365 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| fp512 | 360996742030 | 361110897498 | 0.999683877 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| fp256 | 67928732142 | 67934709762 | 0.999912009 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| elapsed_seconds | 0.000000000 | 0.000000000 |  | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| load_store_per_cycle | 0.584193246 | 0.588182625 | 0.993217448 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |
| load_store_to_fp512 | 1.633727356 | 1.615508365 | 1.011277559 | repro/stage226_exact_mat_avx_counter_attribution/counter_summary.csv |

## Remote Environment

| key | value | evidence |
| --- | --- | --- |
| remote_probe | 0 | repro/stage226_exact_mat_avx_counter_attribution/remote_probe.log |
| remote_unpack | 0 | repro/stage226_exact_mat_avx_counter_attribution/remote_unpack.log |
| remote_install_runner | 0 | repro/stage226_exact_mat_avx_counter_attribution/remote_install_runner.log |
| remote_run | 0 | repro/stage226_exact_mat_avx_counter_attribution/remote_run_stage226_runner.log |
| remote_pull | 0 | repro/stage226_exact_mat_avx_counter_attribution/remote_pull_native_perf_raw.log |
| remote_user_host | delld@192.168.107.220 | repro/stage226_exact_mat_avx_counter_attribution/remote_probe.log |
| remote_dir | /home/delld/spz/Fast-Amortized-Bootstrapping-stage226-8e28f16 | repro/stage226_exact_mat_avx_counter_attribution/remote_unpack.log |
| stage226_events | cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double | repro/stage226_exact_mat_avx_counter_attribution/run_native_stage226_counters.sh |
| hostname | dell | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/remote_environment.log |
| whoami | delld | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/remote_environment.log |
| uname | Linux dell 6.8.0-111-generic #111~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 14 17:13:45 UTC  x86_64 x86_64 x86_64 GNU/Linux | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/remote_environment.log |
| perf | /usr/bin/perf | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/remote_environment.log |
| perf_event_paranoid | 1 | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/remote_environment.log |
| remote_pwd | /home/delld/spz/Fast-Amortized-Bootstrapping-stage226-8e28f16 | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/remote_environment.log |
| cpu_model | Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/remote_environment.log |
| has_avx512f | yes | repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw/remote_environment.log |

## Proof Gates

| gate | status | metric | value | evidence | interpretation |
| --- | --- | --- | --- | --- | --- |
| G1_required_inputs | PASS | inputs_present | true | repro/stage226_exact_mat_avx_counter_attribution/input_status.csv | Stage226 can run only after Stage224 performance and Stage225 side-condition gates. |
| G2_remote_native_execution | PASS | remote_rcs | {'remote_probe': 0, 'remote_unpack': 0, 'remote_install_runner': 0, 'remote_run': 0, 'remote_pull': 0} | repro/stage226_exact_mat_avx_counter_attribution | Native perf execution must complete before any counter attribution. |
| G3_full_sab_correctness | PASS | variant_rows | 2 | repro/stage226_exact_mat_avx_counter_attribution/run_metrics.csv | Both wrapper and backend exact routes must pass full SAB correctness under perf. |
| G4_counter_capture | PASS | counter_rows | 20 | repro/stage226_exact_mat_avx_counter_attribution/counter_metrics.csv | Required native counters include cycles, loads, stores and AVX512 FP arithmetic. |
| G5_attribution_boundary | COUNTER_SUPPORTS_STAGE224_DIRECTION | attribution_label | COUNTER_SUPPORTS_STAGE224_DIRECTION | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv | Counters explain or fail to explain the Stage224 timing direction; they do not prove theoretical optimality. |
| G6_claim_boundary | PASS_NO_OPTIMALITY_OR_NOVELTY_CLAIM | claim_boundary | counter_attribution_only | theory_checks/stage226_counter_attribution_scope.md | Stage226 is a mechanism check for the exact path, not a new algorithmic claim. |
| G7_stage226_decision | PASS_STAGE226_EXACT_COUNTER_ATTRIBUTION_POSITIVE | decision | PASS_STAGE226_EXACT_COUNTER_ATTRIBUTION_POSITIVE | repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv | The next stage is claim-boundary update unless counters reveal a new implementation target. |

## Next Queue

| priority | route | entry_condition | gate | status | failure_action | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | stage227_exact_route_claim_boundary_update | Stage224 performance, Stage225 side conditions, and Stage226 counters are recorded. | Separate exact MAT/PVW engineering acceleration from compact route and optimality claims. | selected | Keep exact route as measured engineering result only. | repro/stage226_exact_mat_avx_counter_attribution/proof_gate.csv |
| P1 | stage228_targeted_counter_driven_kernel_followup | Stage226 identifies a clear cycles/load/store regression source. | New micro-hypothesis with full-SAB promotion gate. | candidate | Do not reopen hot path without a counter-backed implementation target. | repro/stage226_exact_mat_avx_counter_attribution/attribution_summary.csv |
| P2 | neighbor_capable_compact_state_proof | Only if a new closed compact algebra is proposed. | Proof before hot-path implementation. | proof_only_deferred | Do not touch SAB hot path. | repro/stage224_exact_pvw_mat_avx_resource_refresh/proof_gate.csv |
