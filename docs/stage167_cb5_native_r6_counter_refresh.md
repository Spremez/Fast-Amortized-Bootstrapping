# Stage167 CB5 Native r=6 Counter Refresh

Decision: `PASS_STAGE167_CB5_NATIVE_R6_COUNTERS_RECORDED`.

Stage167 records native Linux perf counters for the current exact r=6
post-fusion PVW/MAT-SAB path. It temporarily lowers
`perf_event_paranoid` for the run; post-run verification records the remote
value restored to `4`. The remote password is consumed from
`STAGE167_SSHPASS` and scrubbed from logs.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage167_remote_secret | PASS | STAGE167_SSHPASS | present | environment variable only; not written to artifacts | Remote password is consumed from environment and scrubbed from logs. | Provide STAGE167_SSHPASS only at runtime. |
| stage167_sync | PASS | sync_rc | 0 | repro/stage167_cb5_native_r6_counter_refresh/sync.log | git archive HEAD synchronized to CB5 remote spz directory. | Fix SSH/sync before interpreting remote evidence. |
| stage167_remote_env | PASS | env_probe_rc | 0 | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.csv | Remote CPU, perf path, and perf_event_paranoid recorded. | Use native Linux AVX512 host for counter claims. |
| stage167_build | PASS | build_rc | 0 | repro/stage167_cb5_native_r6_counter_refresh/build.log | Build current r=6 post-fusion path on CB5. | Fix build before using counters. |
| stage167_perf | PASS | perf_rc | 0 | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | Run perf stat with temporary perf_event_paranoid lowering. | If perf fails, keep optimality claims blocked. |
| stage167_restore_verification | PASS | perf_event_paranoid_after | 4 | repro/stage167_cb5_native_r6_counter_refresh/post_restore_verification.csv | Verify remote perf_event_paranoid after the counter run. | Restore to the pre-run value before closing the stage. |
| stage167_counters | PASS | cycles;loads;stores;fp512 | 974318109068;367894314605;207104567619;360989564734 | repro/stage167_cb5_native_r6_counter_refresh/counter_metrics.csv | Native counter values recorded for current r=6 path. | Use counters for attribution, not as proof of theoretical optimality by themselves. |
| stage167_decision | PASS_STAGE167_CB5_NATIVE_R6_COUNTERS_RECORDED | speedup_vs_scalar_repeated | 1.127 | repro/stage167_cb5_native_r6_counter_refresh/summary.csv | Stage167 refreshes native counter evidence for the current exact r=6 path. | Interpret counters against Stage160/161/165 before any optimality wording. |

## Remote Environment

| key | value | evidence |
| --- | --- | --- |
| hostname | dell | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.log |
| whoami | delld | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.log |
| uname | Linux dell 6.8.0-111-generic #111~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 14 17:13:45 UTC  x86_64 x86_64 x86_64 GNU/Linux | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.log |
| perf | /usr/bin/perf | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.log |
| perf_event_paranoid | 4 | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.log |
| remote_dir | /home/delld/spz/Fast-Amortized-Bootstrapping-stage167-e587198 | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.log |
| cpu_model | Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.log |
| has_avx512f | yes | repro/stage167_cb5_native_r6_counter_refresh/remote_environment.log |

## Run Metrics

| metric | value | unit | evidence | detail |
| --- | --- | --- | --- | --- |
| target_full_correctness | PASS | gate | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | target_full correctness Pass line found |
| r | 6 | value | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | SAB_PVW_BENCH summary target_full r=6 reps=1 pvw_avg_us=63578097.000 pvw_stddev_us=0.000 pvw_lane_avg_us=10596349.500 scalar_repeated_avg_us=71628359.000 scalar_stddev_us=0.000 scalar_lane_avg_us=11938059.833 speedup_vs_scalar_repeated=1.127x speedup_stddev=0.000 |
| reps | 1 | value | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | SAB_PVW_BENCH summary target_full r=6 reps=1 pvw_avg_us=63578097.000 pvw_stddev_us=0.000 pvw_lane_avg_us=10596349.500 scalar_repeated_avg_us=71628359.000 scalar_stddev_us=0.000 scalar_lane_avg_us=11938059.833 speedup_vs_scalar_repeated=1.127x speedup_stddev=0.000 |
| pvw_avg_us | 63578097.000 | us | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | SAB_PVW_BENCH summary target_full r=6 reps=1 pvw_avg_us=63578097.000 pvw_stddev_us=0.000 pvw_lane_avg_us=10596349.500 scalar_repeated_avg_us=71628359.000 scalar_stddev_us=0.000 scalar_lane_avg_us=11938059.833 speedup_vs_scalar_repeated=1.127x speedup_stddev=0.000 |
| scalar_repeated_avg_us | 71628359.000 | us | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | SAB_PVW_BENCH summary target_full r=6 reps=1 pvw_avg_us=63578097.000 pvw_stddev_us=0.000 pvw_lane_avg_us=10596349.500 scalar_repeated_avg_us=71628359.000 scalar_stddev_us=0.000 scalar_lane_avg_us=11938059.833 speedup_vs_scalar_repeated=1.127x speedup_stddev=0.000 |
| speedup_vs_scalar_repeated | 1.127 | x | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | SAB_PVW_BENCH summary target_full r=6 reps=1 pvw_avg_us=63578097.000 pvw_stddev_us=0.000 pvw_lane_avg_us=10596349.500 scalar_repeated_avg_us=71628359.000 scalar_stddev_us=0.000 scalar_lane_avg_us=11938059.833 speedup_vs_scalar_repeated=1.127x speedup_stddev=0.000 |

## Counter Metrics

| metric | value | unit | evidence | detail |
| --- | --- | --- | --- | --- |
| cycles | 974318109068 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 974,318,109,068      cycles                                                                  (40.00%) |
| instructions | 1626553402233 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 1,626,553,402,233      instructions                     #    1.67  insn per cycle              (50.00%) |
| cache-references | 38765086697 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 38,765,086,697      cache-references                                                        (50.00%) |
| cache-misses | 14260548615 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 14,260,548,615      cache-misses                     #   36.79% of all cache refs           (50.00%) |
| branches | 107490487108 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 107,490,487,108      branches                                                                (50.00%) |
| branch-misses | 517610979 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 517,610,979      branch-misses                    #    0.48% of all branches             (50.00%) |
| mem_inst_retired.all_loads | 367894314605 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 367,894,314,605      mem_inst_retired.all_loads                                              (40.00%) |
| mem_inst_retired.all_stores | 207104567619 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 207,104,567,619      mem_inst_retired.all_stores                                             (40.00%) |
| fp_arith_inst_retired.512b_packed_double | 360989564734 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 360,989,564,734      fp_arith_inst_retired.512b_packed_double                                        (40.00%) |
| fp_arith_inst_retired.256b_packed_double | 67925434553 | count | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 67,925,434,553      fp_arith_inst_retired.256b_packed_double                                        (40.00%) |
| elapsed_seconds | 277.807063052 | seconds | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 277.807063052 seconds time elapsed |
| user_seconds | 275.951638000 | seconds | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 275.951638000 seconds user |
| sys_seconds | 1.798199000 | seconds | repro/stage167_cb5_native_r6_counter_refresh/run_perf.log | 1.798199000 seconds sys |

## Interpretation

This is attribution evidence for the current implementation. It does not prove
the MAT external product is theoretically optimal; it supplies native
load/store/FMA/cycle context for deciding the next optimization frontier.
