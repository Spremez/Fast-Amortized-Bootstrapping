# Stage 23 Schedule-Fused CMUX/NCMUX Plan

Date: 2026-06-25

## Objective

Evaluate an explicit `SAB_PVW_SCHEDULE_FUSED_CMUX=true` candidate that applies
the Stage 18 `from_DFT_add` epilogue fusion only where the SAB RGSW monomial
schedule guarantees the destination accumulator is not the first CMUX input.

This is a schedule-level ablation above the public `sab_pvw_CMUX` API. It is
not a scalar SAB change and is not a new accumulator-index packing algorithm.

## Hypothesis

For the binary target path, each RGSW monomial update writes from active buffer
`p[in]` to inactive buffer `p[out]`. Therefore `out != in1` for every direct
CMUX/NCMUX inside the bit loops. Calling a schedule-local fused CMUX wrapper
can remove the separate PVW add pass from the hot schedule without changing the
external public CMUX behavior.

Expected call counts for `BINARY SET_2_3_2048`:

```text
rgsw_monomial_calls      = 40
cmux_calls               = 573440
ncmux_calls              = 5080
schedule_fused_cmux      = 573440 - 5080 = 568360
schedule_fused_ncmux     = 5080
mat_ep_calls             = 573440
sub_a_calls              = 39
copyback_calls           = 0 with Stage 20 active-buffer fusion
```

## Implementation Gate

- keep `sab_pvw_CMUX` and `sab_pvw_NCMUX` public semantics unchanged;
- add schedule-local wrappers only inside `sab_pvw_RGSW_monomial_mul_state`;
- require `SAB_PVW_ACTIVE_BUFFER_FUSION=true` for the main benchmark baseline;
- record `schedule_fused_cmux_calls` and `schedule_fused_ncmux_calls` under
  `SAB_PVW_BODY_PROFILE=true`.

## Correctness Gate

```bash
make clean
make FFT_LIB=spqlios_avx512 \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_SCHEDULE_FUSED_CMUX=true \
  SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
./main
```

Run a default target regression without the Stage 23 flag after the candidate
passes.

## Profile Gate

```bash
STAGE23_SCHEDULE_PROFILE_RUNS=1 \
STAGE23_SCHEDULE_PROFILE_R_VALUES="2 4" \
STAGE23_SCHEDULE_PROFILE_OUT_DIR=repro/stage23_schedule_fused_profile_avx512_runs1 \
bash scripts/run_stage23_schedule_fused_profile.sh
```

The count gate must match the static model before any timing is interpreted.
Profile timing is instrumented evidence only.

## Performance Gate

```bash
SAB_PVW_BENCH_R=4 \
SAB_PVW_BENCH_REPS=1 \
STAGE23_SCHEDULE_BENCH_RUNS=1 \
STAGE23_SCHEDULE_BENCH_OUT_DIR=repro/stage23_schedule_fused_bench_r4_reps1_runs1 \
bash scripts/run_stage23_schedule_fused_bench.sh
```

If r=4 smoke is positive against the current Stage 20/22 practical baseline,
run three process-level runs. If the smoke is neutral or negative, record the
candidate as a neutral ablation and do not promote it.

## Interpretation Rules

- A one-run timing is smoke only.
- Full SAB throughput, not CMUX profile timing, decides promotion.
- If the candidate reduces `cmux_add` work but does not improve full SAB, it
  remains a schedule-local implementation result.
- Any correctness or count mismatch blocks promotion and sends the work back to
  schedule understanding.
