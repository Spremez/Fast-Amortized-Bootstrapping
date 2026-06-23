# Variant: r-Specialized AVX512 MAT External Product

Date: 2026-06-23

## Objective

Test whether a body-aware AVX512 MAT kernel can improve the current
`sab_pvw_*` full SAB path for `r=2` and `r=4`.

## Delta From Current Algorithm

Current generic MAT kernel:

```text
for row in l(k+r):
  for output in k+r:
    polynomial_mul_addto_DFT(output, dec_dft[row], selector[row][output])
```

First specialized variant:

```text
for row in k+r:                 // k=1, l=1 only
  for AVX512 DFT coefficient block:
    load dec_dft[row] once
    update all k+r outputs with AVX512 complex FMA
```

The variant is compiled only when both flags are true:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
```

Default AVX512 and default scalar/SAB builds do not use this path.

## Theory Expectation

Expected benefit:

- fewer repeated dec-row vector loads;
- less generic function-call and loop overhead;
- clearer `r=2` and `r=4` specialization point for future register blocking.

Known risk:

- arithmetic count is unchanged;
- dense MAT addmul remains `(k+r)^2*l`;
- output count `k+r=5` at `r=4` creates register pressure;
- current variant still writes each output polynomial separately.

## Current Result

Status: not accepted as a positive optimization.

Evidence:

- `repro/stage11_avx512_rspecialized_r2_reps2_runs3/summary.csv`
- `repro/stage11_avx512_rspecialized_r4_reps2_runs3/summary.csv`
- `repro/stage11_avx512_smallr_replay_r2_reps1_runs1/summary.csv`
- `repro/stage11_avx512_smallr_replay_r4_reps1_runs1/summary.csv`
- `repro/stage11_avx512_smallr_replay_target_r2/main.log`
- `repro/stage11_avx512_rspecialized_kernel/main.log`
- `repro/stage11_avx512_smallr_explicit_kernel_fail/main.log`

Observed full SAB benchmark:

| r | runs | reps/run | PVW mean us | scalar repeated mean us | speedup |
|---:|---:|---:|---:|---:|---:|
| 2 | 3 | 2 | 19,906,032.000 | 24,913,602.333 | 1.253x |
| 4 | 1 | 2 | 38,436,010.000 | 45,685,124.000 | 1.189x |
| 2 | 1 | 1 | 20,037,221.000 | 22,216,297.000 | 1.109x |
| 4 | 1 | 1 | 36,911,855.000 | 49,943,206.000 | 1.353x |

The `r=2` target correctness replay passed with the explicit specialization
flag. The broader `SAB_PVW_KERNEL_TEST` run with the explicit flag segfaulted
during staged testing after the `r=1` full-encrypted RGSW-monomial case and
before any `r=2` RGSW-monomial result was printed, so the variant remains
experimental and is not enabled by default.

The `runs=1,reps=1` rows are explicit-flag replay smokes. They prove the new
Makefile flag and bench wrapper are runnable, but they are not statistically
strong enough to override the three-run decision.

## Decision

Do not claim this variant as an improvement. Keep it as a negative/neutral
engineering data point and use it to motivate a stronger second variant:

- explicit register blocking per output group;
- no pointer-array inner loop;
- separate hand-unrolled `r=2` and `r=4` functions;
- microbench first, full SAB only after staged correctness passes.
