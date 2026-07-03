# Stage169 CB5 Native Repeated r=6 Gate

Decision: `PASS_STAGE169_NATIVE_REPEATED_R6_POSITIVE`.

Stage169 is the native no-perf repeated full-SAB gate requested by Stage168.
It evaluates the current exact r=6 PVW/MAT-SAB path with the primary endpoint
`T_bootstrap/r` against repeated scalar SAB.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage169_remote_secret | PASS | STAGE169_SSHPASS | present | environment variable only; not written to artifacts | Remote password is consumed from environment and scrubbed from logs. | Provide STAGE169_SSHPASS only at runtime. |
| stage169_sync | PASS | sync_rc | 0 | repro/stage169_cb5_native_repeated_r6_gate/sync.log | git archive HEAD synchronized to CB5. | Fix remote sync before interpreting runs. |
| stage169_build | PASS | build_rc | 0 | repro/stage169_cb5_native_repeated_r6_gate/build.log | Build current exact r=6 post-fusion path once on CB5. | Fix build before repeated timing. |
| stage169_runs | PASS | run_rcs | 0;0;0 | repro/stage169_cb5_native_repeated_r6_gate/run_results.csv | Native no-perf repeated full-SAB runs. | Rerun failed samples before claiming native throughput. |
| stage169_correctness | PASS | correctness | PASS;PASS;PASS | repro/stage169_cb5_native_repeated_r6_gate/run_results.csv | Every repeated run must pass target_full correctness. | Do not use performance numbers if any correctness fails. |
| stage169_speedup_stats | PASS | speedup_mean;min;ci95_low | 1.131666667;1.115000000;1.095041982 | repro/stage169_cb5_native_repeated_r6_gate/aggregate.csv | Primary endpoint is T_bootstrap/r versus repeated scalar. | Use mean/min/CI and not a single sample. |
| stage169_decision | PASS_STAGE169_NATIVE_REPEATED_R6_POSITIVE | native_repeated_r6_route | current_exact_path | repro/stage169_cb5_native_repeated_r6_gate/summary.csv | Stage169 upgrades Stage167 timing from perf-wrapped single run to native repeated no-perf evidence. | If positive, proceed to split component counters or final claim refresh. |

## Remote Environment

| key | value | evidence |
| --- | --- | --- |
| hostname | dell | repro/stage169_cb5_native_repeated_r6_gate/remote_environment.log |
| whoami | delld | repro/stage169_cb5_native_repeated_r6_gate/remote_environment.log |
| uname | Linux dell 6.8.0-111-generic #111~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 14 17:13:45 UTC  x86_64 x86_64 x86_64 GNU/Linux | repro/stage169_cb5_native_repeated_r6_gate/remote_environment.log |
| remote_dir | /home/delld/spz/Fast-Amortized-Bootstrapping-stage169-41795a6 | repro/stage169_cb5_native_repeated_r6_gate/remote_environment.log |
| cpu_model | Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz | repro/stage169_cb5_native_repeated_r6_gate/remote_environment.log |
| cpus | 104 | repro/stage169_cb5_native_repeated_r6_gate/remote_environment.log |
| has_avx512f | yes | repro/stage169_cb5_native_repeated_r6_gate/remote_environment.log |

## Run Results

| run | run_rc | correctness | r | pvw_lane_avg_us | scalar_lane_avg_us | speedup_vs_scalar_repeated | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | PASS | 6 | 10387872.667 | 11869316.167 | 1.143 | repro/stage169_cb5_native_repeated_r6_gate/run_1.log |
| 2 | 0 | PASS | 6 | 10713364.833 | 11941036.333 | 1.115 | repro/stage169_cb5_native_repeated_r6_gate/run_2.log |
| 3 | 0 | PASS | 6 | 10294678.667 | 11702925.000 | 1.137 | repro/stage169_cb5_native_repeated_r6_gate/run_3.log |

## Aggregates

| metric | samples | mean | median | min | max | stdev | ci95_low | ci95_high | unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pvw_avg_us | 3 | 62791832.333333336 | 62327236.000000000 | 61768072.000000000 | 64280189.000000000 | 1318927.697082874 | 59515169.861454941 | 66068494.805211730 | us |
| pvw_lane_avg_us | 3 | 10465305.389000000 | 10387872.666999999 | 10294678.666999999 | 10713364.833000001 | 219821.282470993 | 9919194.977954758 | 11011415.800045243 | us_per_lane |
| scalar_repeated_avg_us | 3 | 71026555.000000000 | 71215897.000000000 | 70217550.000000000 | 71646218.000000000 | 732912.585701051 | 69205752.259982109 | 72847357.740017891 | us |
| scalar_lane_avg_us | 3 | 11837759.166666666 | 11869316.166999999 | 11702925.000000000 | 11941036.333000001 | 122152.097518986 | 11534292.043573458 | 12141226.289759874 | us_per_lane |
| speedup_vs_scalar_repeated | 3 | 1.131666667 | 1.137000000 | 1.115000000 | 1.143000000 | 0.014742230 | 1.095041982 | 1.168291351 | x |
