# Stage 14 Body Profile Validation Plan

Date: 2026-06-23

## Primary Question

After Stage 13 removed the obvious post-processing materialization overhead,
which internal part of `sab_pvw_bootstrap_wo_extract_binary()` should drive the
next PVW/MAT-SAB optimization?

## Gates

Correctness:

- default `SAB_PVW_BODY_PROFILE=false` staged PVW regression must pass;
- profiled target full-output benchmark must print `Pass`;
- scalar SAB default path must not be modified.

Performance:

- collect parseable body-profile CSV for `r=2` and `r=4`;
- record the complete body call structure and verify expected MAT EP count;
- treat one-run benchmark timing as smoke-level only.

Stats sanity:

- one process run is `[engineering smoke only]`;
- percentages are used to choose the next implementation target, not to claim
  final speedup;
- accepted speedup still requires repeated process runs and no correctness/noise
  regression.

## Commands

Default staged regression:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Body profile:

```bash
STAGE14_BODY_OUT_DIR=repro/stage14_body_profile_r2_reps1_runs1 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 STAGE14_BODY_RUNS=1 FFT_LIB=spqlios bash scripts/run_stage14_body_profile.sh
STAGE14_BODY_OUT_DIR=repro/stage14_body_profile_r4_reps1_runs1 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 STAGE14_BODY_RUNS=1 FFT_LIB=spqlios bash scripts/run_stage14_body_profile.sh
```

## Expected Structural Counts

For `BINARY SET_2_3_2048`:

```text
RGSW_monomial calls = h + 1 = 40
MAT EP calls = (h + 1) * r_prec * in_N = 40 * 7 * 2048 = 573440
NCMUX calls = (h + 1) * (2^r_prec - 1) = 40 * 127 = 5080
sub_a calls = h = 39
copy-back calls = h + 1 = 40
```

## Decision Rules

If MAT EP is the only dominant cost:

```text
promote Stage 17 MAT AVX512/FMA completion first
```

If CMUX is dominant but MAT EP is only about half of CMUX:

```text
prioritize Stage 15 fused CMUX/NCMUX before deeper AVX512-only work
```

If copy-back or `sub_a` is unexpectedly large:

```text
prioritize Stage 16 sparse/RGSW layout and schedule fusion
```

Observed Stage 14 result:

```text
CMUX dominates nearly all body time.
MAT EP is important but only about 44%-47% of the body.
CMUX wrapper/non-MAT time is about 49%-52% of the body.
```

Therefore the next implementation stage is:

```text
Stage 15: fused CMUX/NCMUX helper plus scratch-aware dataflow.
Stage 16: sparse RGSW-monomial schedule/copy reduction.
Stage 17: MAT AVX512 completion after body fusion has a stable target.
```

## Result Label

Current Stage 14 evidence:

```text
[profile tooling accepted]
[target structural counts verified]
[next optimization target identified]
[full speedup claim unchanged]
```
