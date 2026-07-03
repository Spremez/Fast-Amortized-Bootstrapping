# Stage215 Native Counter Execution

Decision: `PASS_STAGE215_NATIVE_COUNTERS_NO_HOTPATH_REOPEN`.

Stage215 executes the Stage214 native-counter handoff on the configured remote
host when runtime credentials are supplied. The gate remains scoped to native
split-probe attribution; it does not by itself prove complete-SAB speedup.

## Remote Environment

| key | value | evidence |
| --- | --- | --- |
| remote_env | 0 | repro/stage215_native_counter_execution/remote_environment.log |
| remote_unpack | 0 | repro/stage215_native_counter_execution/remote_unpack.log |
| remote_run | 0 | repro/stage215_native_counter_execution/remote_environment.log |
| remote_pull | 0 | repro/stage215_native_counter_execution/remote_environment.log |
| remote_user_host | delld@192.168.107.220 | repro/stage215_native_counter_execution/remote_environment.log |
| remote_dir | /home/delld/spz/Fast-Amortized-Bootstrapping-stage215-19c9c6c | repro/stage215_native_counter_execution/remote_unpack.log |
| perf_available | yes | repro/stage215_native_counter_execution/remote_environment.log |

## Comparison

| r | variant | baseline_mean_per_call_us | wrapper_mean_per_call_us | speedup_vs_baseline | decision |
| --- | --- | --- | --- | --- | --- |
| 2 | torus_to_dft_rows | 7.646820313 | 7.656380859 | 0.998751297 | NOT_PROMOTED |
| 2 | combined_current | 13.132247070 | 13.250950195 | 0.991041916 | NOT_PROMOTED |
| 4 | torus_to_dft_rows | 12.607589844 | 12.616477539 | 0.999295549 | NOT_PROMOTED |
| 4 | combined_current | 26.344212891 | 27.632251953 | 0.953386388 | NOT_PROMOTED |

## Counter Summary

| implementation | r | variant | cycles | instructions | loads | stores | fp512 | ipc | load_store_per_cycle | load_store_to_fp512 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 2 | combined_current | 122946990 | 240964805 | 39070248 | 27126553 | 41530462 | 1.959908128 | 0.538417419 | 1.593933653 |
| baseline | 2 | torus_to_dft_rows | 94021659 | 202666463 | 31928200 | 23984851 | 26946939 | 2.155529536 | 0.594682668 | 2.074931442 |
| baseline | 4 | combined_current | 232155506 | 408741632 | 76633677 | 43597424 | 74847069 | 1.760637251 | 0.517890370 | 1.606356837 |
| baseline | 4 | torus_to_dft_rows | 164815924 | 347705382 | 44217056 | 34848142 | 41112519 | 2.109658907 | 0.479718198 | 1.923141659 |
| wrapper | 2 | combined_current | 129209222 | 233988723 | 36246774 | 24520014 | 34472028 | 1.810928968 | 0.470297608 | 1.762785410 |
| wrapper | 2 | torus_to_dft_rows | 92639569 | 191463343 | 29759914 | 23763296 | 27437866 | 2.066755546 | 0.577757545 | 1.950706006 |
| wrapper | 4 | combined_current | 238536023 | 391496202 | 75077247 | 42960021 | 71675439 | 1.641245616 | 0.494840429 | 1.646830067 |
| wrapper | 4 | torus_to_dft_rows | 164785197 | 323590863 | 43612272 | 35085698 | 39555889 | 1.963713179 | 0.477579124 | 1.989538650 |

## Gates

| gate | status | metric | value | evidence | detail |
| --- | --- | --- | --- | --- | --- |
| G1_stage214_input | PASS | stage214_inputs | present | repro/stage214_frontier_native_counter_handoff/proof_gate.csv; repro/stage214_frontier_native_counter_handoff/run_native_stage214_counters.sh | Stage215 uses the Stage214 runner and route ledger. |
| G2_remote_execution | PASS | remote_rcs | {'remote_env': 0, 'remote_unpack': 0, 'remote_run': 0, 'remote_pull': 0} | repro/stage215_native_counter_execution | Remote archive, run, and pull must all pass before interpreting counters. |
| G3_correctness | PASS | correctness_rows | 8 | repro/stage215_native_counter_execution/correctness.csv | All split probe runs must remain exact. |
| G4_counter_capture | PASS | counter_rows | 80 | repro/stage215_native_counter_execution/counter_metrics.csv | Native perf counters must include load/store/FMA/cycle evidence. |
| G5_performance_admission | PASS_NO_REOPEN | min_combined_speedup | 0.953386388 | repro/stage215_native_counter_execution/comparison.csv | Complete-SAB A/B is authorized only if native integrated combined_current improves for r=2 and r=4. |
| G6_stage215_decision | PASS_STAGE215_NATIVE_COUNTERS_NO_HOTPATH_REOPEN | decision | PASS_STAGE215_NATIVE_COUNTERS_NO_HOTPATH_REOPEN | repro/stage215_native_counter_execution/proof_gate.csv | Stage215 decides whether counters reopen any hot-path implementation route. |

## Next Queue

| priority | route | entry_condition | gate | status | evidence |
| --- | --- | --- | --- | --- | --- |
| P0 | stage216_full_sab_ab_reopened_candidate | Stage215 promotes native integrated wrapper candidate. | Complete-SAB T_bootstrap/r A/B, noise/resource, claim audit. | not_ready | repro/stage215_native_counter_execution/proof_gate.csv |
| P1 | new_mechanism_or_formal_compact_proof | Counters do not promote current wrapper. | New proof/counter-backed mechanism before code. | required | repro/stage215_native_counter_execution/comparison.csv |
