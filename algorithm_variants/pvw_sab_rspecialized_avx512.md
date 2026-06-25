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

## Stage 12 V2 Update

Status: implemented behind the same explicit flag, but still not enabled by
default.

V2 replaces the first pointer-array coefficient loop with two direct kernels:

```text
mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r2_avx512()
mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_avx512()
```

The dispatch is active only for:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
k=1
l=1
r in {2,4}
```

Algorithmic change inside one DFT block:

```text
for coeff block:
  initialize all output accumulators from row 0
  for row in 1..(k+r-1):
    accumulate complex products into all output accumulators
  store the shared mask output and r body outputs once
```

This keeps the arithmetic count unchanged at `(k+r)^2 * l` complex products,
but removes the pointer-array output loop from the hot coefficient path and
keeps output accumulators in AVX512 registers while rows are accumulated.

Evidence:

| artifact | status | result |
|---|---|---|
| `repro/stage12_avx512_smallr_v2_kernel/main.log` | PASS | staged correctness and isolated microbench passed |
| `repro/stage12_avx512_smallr_v2_target_full/main.log` | PASS | target full-output correctness passed |
| `repro/stage12_avx512_smallr_v2_bench_r2_reps1_runs1/summary.csv` | SMOKE_ONLY | full SAB `r=2` one-run speedup `1.137x` |
| `repro/stage12_avx512_smallr_v2_bench_r4_reps1_runs1/summary.csv` | SMOKE_ONLY | full SAB `r=4` one-run speedup `1.253x` |

Microbench signal:

| benchmark | r | speedup vs repeated scalar |
|---|---:|---:|
| isolated MAT_TRGSW | 2 | `1.226x` |
| isolated MAT_TRGSW | 4 | `1.584x` |
| full-output MAT_TRGSW | 2 | `1.449x` |
| full-output MAT_TRGSW | 4 | `1.481x` |

Decision:

```text
V2 is accepted as a staged-correct isolated MAT kernel experiment, but it is not
accepted as a new full SAB acceleration claim. The next algorithmic target is
PVW-aware post-processing and SAB-specific sparse/fused batching, not more MAT
micro-optimization alone.
```

## Stage 15 FMA-Accumulate Update

Status: scoped AVX512 MAT expectation met for `k=1,l=1,r in {2,4}`.

Delta:

```text
mat_avx512_complex_addmul()
```

now accumulates directly with AVX512 FMA instructions:

```text
acc_re = fmadd(dec_re, sel_re, acc_re)
acc_re = fnmadd(dec_im, sel_im, acc_re)
acc_im = fmadd(dec_im, sel_re, acc_im)
acc_im = fmadd(dec_re, sel_im, acc_im)
```

The previous helper computed a temporary complex product and then added that
temporary into the accumulator. The new form reduces extra vector add/mul work
in the row accumulation path.

Additional `r=2` specialization:

```text
The fixed three-row r=2 kernel hoists dec/selector pointers and explicitly
accumulates rows 1 and 2.
```

Rejected sub-variant:

```text
An r=4 pointer-array hoist was tested and rejected. Repeated runs showed worse
MAT mul/add phase time, consistent with register/stack pressure at five output
accumulators and five selector rows.
```

Evidence:

| artifact | status | result |
|---|---|---|
| `repro/stage15_avx512_mat_gate_runs3/mat_vs_scalar.csv` | PASS | DFT-output MAT speedups: r=2 `1.380x`, r=4 `1.267x` |
| `repro/stage15_avx512_mat_gate_runs3/mat_full_vs_scalar.csv` | PASS | full-output MAT speedups: r=2 `1.416x`, r=4 `1.471x` |
| `repro/stage15_avx512_mat_target_full.log` | PASS | target full-output correctness |
| `repro/stage15_avx512_mat_full_sab_r2_reps1_runs1/summary.csv` | SMOKE_ONLY | full SAB r=2 `1.265x` |
| `repro/stage15_avx512_mat_full_sab_r4_reps1_runs1/summary.csv` | SMOKE_ONLY | full SAB r=4 `1.356x` |
| `repro/stage15_avx512_mat_instruction_snippet.txt` | PASS | contains AVX512 FMA instructions |

Decision:

```text
Keep the FMA-accumulate helper and r=2 pointer-hoisted specialization.
Do not enable the explicit flag by default.
Move next to repeated full SAB sweeps or SAB-level CMUX/RGSW/sparse fusion.
```
