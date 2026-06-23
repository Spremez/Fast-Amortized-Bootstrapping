# Stage 13 Post-processing Validation Plan

Date: 2026-06-23

## Primary Question

How much of full-output PVW/MAT-SAB time is spent after
`bootstrap_wo_extract`, and does removing the intermediate `PVW_TLWE`
materialization materially change the next optimization priority?

## Gates

Correctness:

- staged `SAB_PVW_KERNEL_TEST=true` on `FFT_LIB=spqlios`;
- target-size `SAB_PVW_TARGET_TEST=true` on `FFT_LIB=spqlios`;
- preserve the old `sab_pvw_extract_pvwtlwe()` staged API.

Performance:

- profile one-run calls for `r=2` and `r=4`;
- run unprofiled one-run full SAB smokes for `r=2` and `r=4`;
- require three process runs before any accepted speedup claim.

Stats sanity:

- profile and one-run benchmark rows are `[engineering smoke only]`;
- use them for prioritization, not final claims.

## Commands

Staged correctness:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Target full correctness:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
./main
```

Post-processing profile:

```bash
STAGE13_POSTPROC_OUT_DIR=repro/stage13_postproc_profile_r2_reps1_runs1 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 STAGE13_POSTPROC_RUNS=1 FFT_LIB=spqlios bash scripts/run_stage13_postproc_profile.sh
STAGE13_POSTPROC_OUT_DIR=repro/stage13_postproc_profile_r4_reps1_runs1 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 STAGE13_POSTPROC_RUNS=1 FFT_LIB=spqlios bash scripts/run_stage13_postproc_profile.sh
```

Unprofiled full SAB smoke:

```bash
STAGE7_BENCH_OUT_DIR=repro/stage13_direct_extract_bench_r2_reps1_runs1 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 STAGE7_BENCH_RUNS=1 FFT_LIB=spqlios bash scripts/run_stage7_bench_sweep.sh
STAGE7_BENCH_OUT_DIR=repro/stage13_direct_extract_bench_r4_reps1_runs1 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 STAGE7_BENCH_RUNS=1 FFT_LIB=spqlios bash scripts/run_stage7_bench_sweep.sh
```

## Result Label

Current result:

```text
[implementation cleanup accepted]
[post-processing bottleneck not supported]
[full SAB speedup smoke only]
```

The profile data shows that direct extraction and packing/HW-KS are too small
to explain multi-fold speedups at the target shape. The next stage should focus
on sparse blind-rotation/fused CMUX work unless a direct-to-packing KS variant
can be implemented with very low complexity.
