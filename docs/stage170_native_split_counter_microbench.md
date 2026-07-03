# Stage170 Native Split Counter Microbench

Decision: `PASS_STAGE170_NATIVE_SPLIT_COUNTERS_RECORDED`.

Stage170 isolates native CB5 perf counters for the current exact r=6
PVW/MAT-SAB component kernels:

- `mat_trgsw_mul_pvmtmlwe_sub_DFT`, including sub-decomposition, per-row DFT,
  and the r>4 tiled AVX512 dense MAT addmul;
- `pvmtmlwe_from_DFT_add`, including inverse DFT materialization and addend
  fusion under the current backend flag.

This stage is component attribution. It is not a complete-SAB speedup claim and
not a proof of theoretical optimality.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage170_remote_secret | PASS | STAGE170_SSHPASS | present | environment variable only; not written to artifacts | Remote password is consumed from environment and scrubbed from logs. | Provide STAGE170_SSHPASS only at runtime. |
| stage170_sync | PASS | sync_rc | 0 | repro/stage170_native_split_counter_microbench/sync.log | git archive HEAD synchronized to CB5. | Fix SSH/sync before interpreting counters. |
| stage170_probe_upload | PASS | upload_rc | 0 | repro/stage170_native_split_counter_microbench/upload_probe_source.log | The uncommitted generated C probe is copied after archive sync. | Fix upload before compile. |
| stage170_build_compile | PASS | build_rc;compile_rc | 0;0 | repro/stage170_native_split_counter_microbench/build_static.log;repro/stage170_native_split_counter_microbench/compile_probe.log | Build static MOSFHET and compile the isolated split-counter probe. | Fix build before running perf. |
| stage170_perf_runs | PASS | perf_rcs | mat_ep_subdecomp=0;from_dft_materialize=0 | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log;repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | Run native perf stat separately for MAT EP/subdecomp and from_DFT materialization. | Use split counters as attribution, not final speedup. |
| stage170_correctness | PASS | correctness | mat_ep_subdecomp:streaming_reference=PASS;from_dft_materialize:fused_add_reference=PASS | repro/stage170_native_split_counter_microbench/correctness.csv | MAT EP is checked against streaming reference; from_DFT_add is checked against materialize+add. | Ignore counters if correctness fails. |
| stage170_restore_verification | PASS | perf_event_paranoid_before;after | 4;4 | repro/stage170_native_split_counter_microbench/post_restore_verification.csv | Verify remote perf_event_paranoid after split counter runs. | Restore the remote setting before closing if values differ. |
| stage170_counters | PASS | cycles;loads;stores;fp512 | mat_ep_subdecomp:cycles=733921233;loads=219525198;stores=111144650;fp512=237840216 \| from_dft_materialize:cycles=522086334;loads=139846481;stores=99966844;fp512=124917084 | repro/stage170_native_split_counter_microbench/counter_metrics.csv | Native component counter values are recorded separately. | Use ratios to decide Stage171/172, not as theoretical optimality proof. |
| stage170_decision | PASS_STAGE170_NATIVE_SPLIT_COUNTERS_RECORDED | split_component_counter_route | mat_ep_subdecomp;from_dft_materialize | repro/stage170_native_split_counter_microbench/summary.csv | Stage170 isolates the current exact r=6 component counters. | Update frontier claims and only pursue new variants with a falsifiable gate. |

## Remote Environment

| key | value | evidence |
| --- | --- | --- |
| hostname | dell | repro/stage170_native_split_counter_microbench/remote_environment.log |
| whoami | delld | repro/stage170_native_split_counter_microbench/remote_environment.log |
| uname | Linux dell 6.8.0-111-generic #111~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 14 17:13:45 UTC  x86_64 x86_64 x86_64 GNU/Linux | repro/stage170_native_split_counter_microbench/remote_environment.log |
| perf | /usr/bin/perf | repro/stage170_native_split_counter_microbench/remote_environment.log |
| perf_event_paranoid | 4 | repro/stage170_native_split_counter_microbench/remote_environment.log |
| remote_dir | /home/delld/spz/Fast-Amortized-Bootstrapping-stage170-015de8a | repro/stage170_native_split_counter_microbench/remote_environment.log |
| cpu_model | Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz | repro/stage170_native_split_counter_microbench/remote_environment.log |
| cpus | 104 | repro/stage170_native_split_counter_microbench/remote_environment.log |
| has_avx512f | yes | repro/stage170_native_split_counter_microbench/remote_environment.log |

## Correctness

| variant | check | mismatches | max_gap | status | evidence |
| --- | --- | --- | --- | --- | --- |
| mat_ep_subdecomp | streaming_reference | 0 | 0 | PASS | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log |
| from_dft_materialize | fused_add_reference | 0 | 0 | PASS | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log |

## Run Metrics

| variant | run_rc | r | N | items | reps | calls | per_call_us | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mat_ep_subdecomp | 0 | 6 | 2048 | 256 | 8 | 2048 | 66.127151855 | PASS | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log |
| from_dft_materialize | 0 | 6 | 2048 | 256 | 8 | 2048 | 35.211114746 | PASS | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log |

## Counter Metrics

| variant | metric | value | unit | evidence | detail |
| --- | --- | --- | --- | --- | --- |
| mat_ep_subdecomp | cycles | 733921233 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 733,921,233      cycles                                                                  (39.41%) |
| mat_ep_subdecomp | instructions | 998314882 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 998,314,882      instructions                     #    1.36  insn per cycle              (49.51%) |
| mat_ep_subdecomp | cache-references | 44921006 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 44,921,006      cache-references                                                        (49.31%) |
| mat_ep_subdecomp | cache-misses | 5367767 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 5,367,767      cache-misses                     #   11.95% of all cache refs           (50.33%) |
| mat_ep_subdecomp | branches | 80683507 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 80,683,507      branches                                                                (50.39%) |
| mat_ep_subdecomp | branch-misses | 167907 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 167,907      branch-misses                    #    0.21% of all branches             (50.50%) |
| mat_ep_subdecomp | mem_inst_retired.all_loads | 219525198 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 219,525,198      mem_inst_retired.all_loads                                              (40.39%) |
| mat_ep_subdecomp | mem_inst_retired.all_stores | 111144650 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 111,144,650      mem_inst_retired.all_stores                                             (40.20%) |
| mat_ep_subdecomp | fp_arith_inst_retired.512b_packed_double | 237840216 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 237,840,216      fp_arith_inst_retired.512b_packed_double                                        (39.95%) |
| mat_ep_subdecomp | fp_arith_inst_retired.256b_packed_double | 23097198 | count | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 23,097,198      fp_arith_inst_retired.256b_packed_double                                        (39.51%) |
| mat_ep_subdecomp | elapsed_seconds | 0.231272782 | seconds | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 0.231272782 seconds time elapsed |
| mat_ep_subdecomp | user_seconds | 0.192062000 | seconds | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 0.192062000 seconds user |
| mat_ep_subdecomp | sys_seconds | 0.039217000 | seconds | repro/stage170_native_split_counter_microbench/run_mat_ep_subdecomp_perf.log | 0.039217000 seconds sys |
| from_dft_materialize | cycles | 522086334 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 522,086,334      cycles                                                                  (39.27%) |
| from_dft_materialize | instructions | 830267579 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 830,267,579      instructions                     #    1.59  insn per cycle              (49.54%) |
| from_dft_materialize | cache-references | 14145189 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 14,145,189      cache-references                                                        (50.15%) |
| from_dft_materialize | cache-misses | 9151348 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 9,151,348      cache-misses                     #   64.70% of all cache refs           (50.75%) |
| from_dft_materialize | branches | 64573571 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 64,573,571      branches                                                                (51.34%) |
| from_dft_materialize | branch-misses | 219205 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 219,205      branch-misses                    #    0.34% of all branches             (51.06%) |
| from_dft_materialize | mem_inst_retired.all_loads | 139846481 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 139,846,481      mem_inst_retired.all_loads                                              (40.19%) |
| from_dft_materialize | mem_inst_retired.all_stores | 99966844 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 99,966,844      mem_inst_retired.all_stores                                             (39.59%) |
| from_dft_materialize | fp_arith_inst_retired.512b_packed_double | 124917084 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 124,917,084      fp_arith_inst_retired.512b_packed_double                                        (39.00%) |
| from_dft_materialize | fp_arith_inst_retired.256b_packed_double | 35409226 | count | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 35,409,226      fp_arith_inst_retired.256b_packed_double                                        (38.66%) |
| from_dft_materialize | elapsed_seconds | 0.169954448 | seconds | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 0.169954448 seconds time elapsed |
| from_dft_materialize | user_seconds | 0.116682000 | seconds | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 0.116682000 seconds user |
| from_dft_materialize | sys_seconds | 0.053312000 | seconds | repro/stage170_native_split_counter_microbench/run_from_dft_materialize_perf.log | 0.053312000 seconds sys |

## Derived Ratios

| variant | metric | value | unit | interpretation |
| --- | --- | --- | --- | --- |
| mat_ep_subdecomp | cycles_per_call | 358359.977050781 | cycles/call | Primary per-call native counter cost for this isolated component. |
| mat_ep_subdecomp | instructions_per_call | 487458.438476562 | instructions/call | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| mat_ep_subdecomp | loads_per_call | 107190.038085938 | loads/call | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| mat_ep_subdecomp | stores_per_call | 54269.848632812 | stores/call | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| mat_ep_subdecomp | fp512_per_call | 116132.917968750 | fp512/call | Checks whether AVX512 arithmetic is actually exercised by the component. |
| mat_ep_subdecomp | fp256_per_call | 11277.928710938 | fp256/call | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| mat_ep_subdecomp | ipc | 1.360247990 | instructions/cycle | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| mat_ep_subdecomp | load_store_to_fp512_ratio | 1.390302505 | (loads+stores)/fp512 | Higher values mean memory traffic remains important relative to FP512 work. |
| mat_ep_subdecomp | cache_miss_rate | 0.119493473 | cache-misses/cache-references | Locality proxy; not a standalone proof of a better layout. |
| mat_ep_subdecomp | elapsed_seconds | 0.231272782 | seconds | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| mat_ep_subdecomp | calls | 2048.000000000 | calls | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| from_dft_materialize | cycles_per_call | 254924.967773438 | cycles/call | Primary per-call native counter cost for this isolated component. |
| from_dft_materialize | instructions_per_call | 405404.091308594 | instructions/call | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| from_dft_materialize | loads_per_call | 68284.414550781 | loads/call | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| from_dft_materialize | stores_per_call | 48811.935546875 | stores/call | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| from_dft_materialize | fp512_per_call | 60994.669921875 | fp512/call | Checks whether AVX512 arithmetic is actually exercised by the component. |
| from_dft_materialize | fp256_per_call | 17289.661132812 | fp256/call | Residual FFT/backend width signal for materialization. |
| from_dft_materialize | ipc | 1.590287899 | instructions/cycle | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| from_dft_materialize | load_store_to_fp512_ratio | 1.919780044 | (loads+stores)/fp512 | Higher values mean memory traffic remains important relative to FP512 work. |
| from_dft_materialize | cache_miss_rate | 0.646958340 | cache-misses/cache-references | Locality proxy; not a standalone proof of a better layout. |
| from_dft_materialize | elapsed_seconds | 0.169954448 | seconds | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
| from_dft_materialize | calls | 2048.000000000 | calls | Component-level attribution only; do not claim full-SAB acceleration from this row alone. |
