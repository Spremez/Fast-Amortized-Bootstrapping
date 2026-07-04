# Stage300 Current-Head Counter Route Audit

Decision: `PASS_STAGE300_COUNTER_CONTEXT_CURRENT_HEAD_REFRESH_REQUIRED`.

Stage300 is a routing and claim-boundary audit, not a new speed claim.
It checks whether the current direct-DFT PVW/MAT-SAB head has hardware
counter attribution, and separates current-head evidence from historical
native counter context.

## Evidence Matrix

| item | status | evidence | interpretation |
| --- | --- | --- | --- |
| current_direct_dft_target_highstat | PASS | repro/stage296_direct_dft_highstat/perf_summary.csv | SET_2_3_2048 direct/control=1.075398; direct/scalar=1.735849; samples=10. |
| current_direct_dft_added_param_preflight | PASS | repro/stage299_direct_dft_param_preflight/perf_summary.csv | SET_4_5_2048 direct/control=1.063481; direct/scalar=1.747795; samples=3. |
| local_counter_capability | BLOCKED | repro/stage300_current_head_counter_route/local_stage28_perf_probe/summary.csv | local perf_command=MISSING; current host route=BLOCKED. |
| historical_native_counter_context_stage101 | PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED | repro/stage101_cb5_remote_native_perf/summary.csv | Native counter evidence exists for an earlier PVW/MAT-SAB path; use as context only. |
| historical_exact_route_counter_context_stage226 | PASS_STAGE226_EXACT_COUNTER_ATTRIBUTION_POSITIVE | repro/stage226_exact_mat_avx_counter_attribution/counter_comparison.csv | Exact-route counters record small load/store/cycle direction; not current direct-DFT proof. |

## Proof Gate

| gate | status | value | interpretation |
| --- | --- | --- | --- |
| G1_current_direct_perf | PASS | stage296+stage299 | Current direct-DFT complete-SAB T/r evidence is available before counter routing. |
| G2_local_counter_capability | BLOCKED | BLOCKED | Local WSL can run current-head counters only if this is PASS or READY_FOR_BENCH. |
| G3_historical_counter_context | PASS | stage101=PASS_STAGE101_CB5_NATIVE_PERF_COUNTERS_RECORDED; stage226=PASS_STAGE226_EXACT_COUNTER_ATTRIBUTION_POSITIVE | Historical counters inform hypotheses but cannot replace current-head direct-DFT counters. |
| G4_claim_boundary | PASS_NO_OPTIMALITY_CLAIM | counter_refresh_required | Do not claim theoretical MAT-AVX512 optimality for direct DFT until current-head counters are recorded. |
| G5_decision | PASS_STAGE300_COUNTER_CONTEXT_CURRENT_HEAD_REFRESH_REQUIRED | PASS_STAGE300_COUNTER_CONTEXT_CURRENT_HEAD_REFRESH_REQUIRED | Controls Stage301 route. |

## Claim Boundary

The current complete-SAB metric remains `T_bootstrap/r`. Historical native
counter artifacts can guide mechanism hypotheses, but they do not prove
MAT-AVX512 optimality for the current direct-DFT candidate without a
current-head refresh.
