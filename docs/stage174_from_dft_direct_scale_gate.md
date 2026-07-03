# Stage174 From-DFT Direct-Scale Gate

Decision: `NEUTRAL_STAGE174_DIRECT_SCALE_MICROBENCH_NOT_PROMOTED`.

Stage174 tests one bounded from_DFT backend/SIMD locality candidate:

```text
SPQLIOS_AVX512_DIRECT_SCALE=true
```

The candidate replaces the 256-bit inline-assembly scale/copy loop before
`execute_direct_torus64[_add]` with a 512-bit intrinsic loop under an explicit
flag. Baseline behavior remains unchanged when the flag is off.

This is not an algorithmic MAT-SAB improvement unless it passes the complete
SAB gate. Microbench evidence is only a promotion filter.

## Gate Summary

| gate | status | metric | value | evidence | detail | next_action |
| --- | --- | --- | --- | --- | --- | --- |
| stage174_remote_secret | PASS | STAGE174_SSHPASS | present | environment variable only; not written to artifacts | Remote password is consumed from environment and scrubbed from logs. | Provide STAGE174_SSHPASS only at runtime. |
| stage174_sync_upload | PASS | sync_rc;env_rc;upload_rc | 0;0;0 | repro/stage174_from_dft_direct_scale_gate/sync.log;repro/stage174_from_dft_direct_scale_gate/upload_fft_processor.log | Archive HEAD to CB5 and upload uncommitted flag/backend/probe files. | Fix remote state before interpreting results. |
| stage174_build_compile | PASS | build_rcs;compile_rcs | {'baseline': 0, 'direct_scale': 0};{'baseline': 0, 'direct_scale': 0} | repro/stage174_from_dft_direct_scale_gate | Build baseline and direct_scale static libraries and probes. | Fix compile before using timings. |
| stage174_micro_correctness | PASS | correctness | baseline=PASS;direct_scale=PASS | repro/stage174_from_dft_direct_scale_gate/correctness.csv | Each variant must match separate materialize+add. | Reject variant if exactness fails. |
| stage174_microbench | NEUTRAL_OR_REJECT | baseline/direct_scale | 0.990754925;0.949781500 | repro/stage174_from_dft_direct_scale_gate/comparison.csv | Microbench promotion requires stable speedup before full-SAB A/B. | Run full-SAB only on microbench promotion. |
| stage174_full_sab | SKIPPED_BY_GATE | full_attempted | no | repro/stage174_from_dft_direct_scale_gate/comparison.csv | Complete-SAB promotion remains the only allowed bootstrapping speedup claim. | Do not claim complete-SAB speedup if skipped or neutral. |
| stage174_decision | NEUTRAL_STAGE174_DIRECT_SCALE_MICROBENCH_NOT_PROMOTED | direct_scale_route | explicit_flag | repro/stage174_from_dft_direct_scale_gate/summary.csv | Stage174 tests one bounded backend/SIMD locality candidate. | Promote only if full-SAB evidence is positive; otherwise record neutral/reject. |

## Remote Environment

| key | value | evidence |
| --- | --- | --- |
| hostname | dell | repro/stage174_from_dft_direct_scale_gate/remote_environment.log |
| whoami | delld | repro/stage174_from_dft_direct_scale_gate/remote_environment.log |
| uname | Linux dell 6.8.0-111-generic #111~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 14 17:13:45 UTC  x86_64 x86_64 x86_64 GNU/Linux | repro/stage174_from_dft_direct_scale_gate/remote_environment.log |
| remote_dir | /home/delld/spz/Fast-Amortized-Bootstrapping-stage174-4696217 | repro/stage174_from_dft_direct_scale_gate/remote_environment.log |
| cpu_model | Intel(R) Xeon(R) Gold 6230R CPU @ 2.10GHz | repro/stage174_from_dft_direct_scale_gate/remote_environment.log |
| cpus | 104 | repro/stage174_from_dft_direct_scale_gate/remote_environment.log |
| has_avx512f | yes | repro/stage174_from_dft_direct_scale_gate/remote_environment.log |

## Correctness

| variant | check | mismatches | max_gap | status | evidence |
| --- | --- | --- | --- | --- | --- |
| baseline | separate_reference | 0 | 0 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_baseline.log |
| direct_scale | separate_reference | 0 | 0 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_direct_scale.log |

## Microbench Samples

| variant | run | r | N | items | components | reps | calls | per_call_us | status | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 0 | 6 | 2048 | 256 | 7 | 8 | 14336 | 4.973350516 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_baseline.log |
| baseline | 1 | 6 | 2048 | 256 | 7 | 8 | 14336 | 4.936878209 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_baseline.log |
| baseline | 2 | 6 | 2048 | 256 | 7 | 8 | 14336 | 4.908950753 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_baseline.log |
| baseline | 3 | 6 | 2048 | 256 | 7 | 8 | 14336 | 4.898847098 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_baseline.log |
| baseline | 4 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.145079660 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_baseline.log |
| baseline | 5 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.216516183 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_baseline.log |
| baseline | 6 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.015303850 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_baseline.log |
| direct_scale | 0 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.102719517 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_direct_scale.log |
| direct_scale | 1 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.056200963 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_direct_scale.log |
| direct_scale | 2 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.013848912 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_direct_scale.log |
| direct_scale | 3 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.040780343 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_direct_scale.log |
| direct_scale | 4 | 6 | 2048 | 256 | 7 | 8 | 14336 | 4.999533761 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_direct_scale.log |
| direct_scale | 5 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.051458147 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_direct_scale.log |
| direct_scale | 6 | 6 | 2048 | 256 | 7 | 8 | 14336 | 5.157867467 | PASS | repro/stage174_from_dft_direct_scale_gate/run_probe_direct_scale.log |

## Microbench Aggregate

| variant | metric | samples | mean | median | min | max | stdev | ci95_low | ci95_high | unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | per_call_us | 7 | 5.013560896 | 4.973350516 | 4.898847098 | 5.216516183 | 0.122536198 | 4.900229732 | 5.126892059 | us_per_call |
| direct_scale | per_call_us | 7 | 5.060344159 | 5.051458147 | 4.999533761 | 5.157867467 | 0.054229526 | 5.010188405 | 5.110499912 | us_per_call |

## Comparison

| scope | metric | value | promotion_threshold | status | evidence |
| --- | --- | --- | --- | --- | --- |
| microbench | baseline_mean/direct_scale_mean;baseline_min/direct_scale_max | 0.990754925;0.949781500 | mean>=1.02;minmax>=1.0 | NEUTRAL_OR_REJECT | repro/stage174_from_dft_direct_scale_gate/microbench_aggregate.csv |
| full_sab | not_run | microbench_not_promoted | microbench must promote first | SKIPPED_BY_GATE | repro/stage174_from_dft_direct_scale_gate/comparison.csv |

## Full SAB Runs

| variant | run | run_rc | correctness | r | pvw_lane_avg_us | scalar_lane_avg_us | speedup_vs_scalar_repeated | evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Full SAB Aggregate

| variant | metric | samples | mean | median | min | max | stdev | ci95_low | ci95_high | unit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Next Queue

| priority | stage | name | entry_condition | gate | failure_rule |
| --- | --- | --- | --- | --- | --- |
| P0 | 175 | post-Stage174 frontier refresh | Stage174 did not promote direct-scale. | Record neutral/reject and choose a different bounded route. | Do not keep tuning direct-scale blindly. |
| P1 | 173 | structured compact proof route | Engineering direct-scale route is neutral/rejected and user wants algorithmic proof route. | Formal phase/noise toy for compact keygen. | Keep compact blocked if equations do not close. |
