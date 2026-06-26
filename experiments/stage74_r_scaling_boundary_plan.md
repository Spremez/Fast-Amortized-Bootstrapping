# Stage74 R-Scaling Boundary Plan

Date: 2026-06-26

## Goal

Test whether directly increasing PVW/MAT-SAB lane count beyond the promoted
small-r range can improve complete SAB throughput under the current
`spqlios_avx512` active-buffer path.

## Hypothesis

If shared-mask schedule amortization continues to dominate dense MAT external
product cost, then `r=6` or `r=8` complete SAB should improve throughput over
the current r=4 promoted evidence. If dense `(k+r)^2` MAT accumulation and
generic-kernel overhead dominate, then r>4 should pass correctness but fail as
a promotion candidate.

## Commands

```bash
STAGE20_ACTIVE_BENCH_RUNS=1 \
SAB_PVW_BENCH_R=6 \
SAB_PVW_BENCH_REPS=1 \
STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage74_r_scaling_boundary/r6_reps1_runs1 \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
JOBS=$(nproc) \
bash scripts/run_stage20_active_buffer_bench.sh

STAGE20_ACTIVE_BENCH_RUNS=1 \
SAB_PVW_BENCH_R=8 \
SAB_PVW_BENCH_REPS=1 \
STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage74_r_scaling_boundary/r8_reps1_runs1 \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
JOBS=$(nproc) \
bash scripts/run_stage20_active_buffer_bench.sh

python scripts/build_stage74_r_scaling_boundary.py
```

## Gates

- r=6 and r=8 complete-SAB benchmark correctness lines must pass.
- r=6 and r=8 must remain faster than repeated scalar SAB to be useful as
  boundary evidence.
- Direct r>4 promotion requires smoke results to exceed the current r=4
  Stage36 10-run mean before expensive repeated/noise/resource gates are
  justified.
- If r=6 and r=8 are below the Stage36 r=4 10-run CI lower bound, mark direct
  r>4 scaling as not promoted.

## Failure Handling

- If correctness fails, do not run performance interpretation; record r>4 as
  unsupported under the current implementation.
- If performance is positive but below r=4, keep the result as a negative
  scaling-boundary ablation.
- If performance exceeds r=4, do not claim acceleration immediately; require
  repeated full-SAB, noise, resource, and closure gates first.
