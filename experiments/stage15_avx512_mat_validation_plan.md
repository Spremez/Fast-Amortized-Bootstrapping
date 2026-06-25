# Stage 15 AVX512 MAT Validation Plan

Date: 2026-06-25

## Primary Question

Has the scoped AVX512 MAT external-product implementation reached the practical
performance expected from the dense shared-mask MAT model?

## Scope

Supported in this stage:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
k=1
l=1
r in {2,4}
```

Out of scope:

- default promotion;
- AVX2/FMA fallback;
- generic `k,l,r`;
- final full SAB speedup claim.

## Correctness Gates

- staged `SAB_PVW_KERNEL_TEST=true` under `spqlios_avx512`;
- target full-output gate under `spqlios_avx512`;
- full SAB smoke correctness for `r=2` and `r=4`.

## Performance Gates

MAT gate:

```bash
STAGE15_AVX512_MAT_OUT_DIR=repro/stage15_avx512_mat_gate_runs3 \
STAGE15_AVX512_MAT_RUNS=3 \
bash scripts/run_stage15_avx512_mat_gate.sh
```

Full SAB smokes:

```bash
STAGE11_BENCH_OUT_DIR=repro/stage15_avx512_mat_full_sab_r2_reps1_runs1 \
SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 STAGE11_BENCH_RUNS=1 \
bash scripts/run_stage11_avx512_smallr_bench.sh

STAGE11_BENCH_OUT_DIR=repro/stage15_avx512_mat_full_sab_r4_reps1_runs1 \
SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 STAGE11_BENCH_RUNS=1 \
bash scripts/run_stage11_avx512_smallr_bench.sh
```

## Pass Criteria

Stage 15 passes if:

- staged MAT/PVW correctness passes in every gate run;
- target full-output correctness passes;
- `r=2` and `r=4` DFT-output MAT are positive over repeated scalar;
- `r=2` and `r=4` full-output MAT are positive over repeated scalar;
- full SAB smokes are positive.

This pass criterion means:

```text
AVX512 MAT is good enough for the currently supported dense-MAT scoped shape.
```

It does not mean:

```text
AVX512 MAT is complete, default-ready, or sufficient for multi-fold SAB speedup.
```

## Failure Rules

- If `r=2` or `r=4` DFT-output MAT is not positive, continue kernel work before
  touching full SAB.
- If MAT is positive but full-output MAT is not, inspect inverse DFT/output
  conversion.
- If MAT gates pass but full SAB is not positive, return to Stage 14/15 body
  profile and optimize CMUX/RGSW/sparse scheduling.
- If r=4 pointer-hoisting regresses `mul_avg_us`, reject it even if one
  end-to-end speedup line looks positive.

## Current Result

Result label:

```text
[scoped AVX512 MAT expectation met]
[default promotion pending]
[full SAB speedup smoke only]
```
