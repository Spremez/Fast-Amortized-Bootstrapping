# Stage 12 AVX512 Gate and V2 Small-r Kernel Log

Date: 2026-06-23

## Purpose

Stage 12 has two separate jobs:

1. Make the AVX512 staged correctness gate reliable enough to support later
   experiments.
2. Replace the Stage 11 first-generation small-r AVX512 MAT kernel with a
   second-generation `r=2/r=4` implementation that is measurable in isolation.

These jobs must stay separated. Fixing the staged gate is not by itself a
performance improvement, and an isolated MAT improvement is not by itself a
complete SAB acceleration result.

## AVX512 Staged Gate Finding

Stage 11 suggested that the explicit small-r specialization might be related to
the staged crash. Stage 12 reproduced the same crash with the default AVX512
path:

```text
FFT_LIB=spqlios_avx512
SAB_PVW_KERNEL_TEST=true
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED unset
```

Progress markers localized the failure to the small sparse/bootstrap staged
path, specifically before the `sparse_mul r=1 step=pvw_key` marker. The failing
boundary is the `N=16` staged TRLWE input-key helper, not the MAT small-r
specialized external product.

## Gate Policy

For `USE_SPQLIOS && AVX512_OPT`, the staged kernel test now:

- runs isolated CMUX/NCMUX lane equivalence for `r=1/2/4`;
- runs RGSW-monomial lane equivalence for encrypted bit selectors, trivial
  multibit selectors, and full-encrypted multibit selectors;
- runs the MAT external-product staged test and microbench sections;
- skips only the `N=16` sparse/bootstrap sub-gates with an explicit reason in
  the log.

The target-size full bootstrap gate remains mandatory for AVX512 evidence:

```text
FFT_LIB=spqlios_avx512
SAB_PVW_TARGET_TEST=true
KEY=BINARY
PARAM=SET_2_3_2048
```

Ordinary `FFT_LIB=spqlios` still runs the full small staged sparse/bootstrap
coverage.

## V2 Kernel Algorithm

The Stage 11 first-generation variant used a pointer-array loop over outputs.
That reduced some generic call overhead but still carried avoidable indirection
in the coefficient loop.

The Stage 12 v2 variant adds separate direct functions:

```text
mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r2_avx512()
mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_r4_avx512()
```

Applicability:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
k=1
l=1
r in {2,4}
```

For each AVX512 DFT coefficient block, v2 does:

```text
load row 0 decomposition block
compute initial output accumulators in ZMM registers
for each remaining row:
  load row decomposition block
  add complex products into the output accumulators
store shared mask output and all r body outputs once
```

The arithmetic count is unchanged. The intended benefit is lower loop overhead,
less output traffic inside the row loop, and a clearer specialization point for
`r=2` and `r=4`.

## Evidence

| run | backend | status | evidence |
|---|---|---:|---|
| default AVX512 staged crash localization | `spqlios_avx512` | FAIL recorded | `repro/stage12_avx512_default_sparse_progress/main.log` |
| default AVX512 staged gate after policy | `spqlios_avx512` | PASS | `repro/stage12_avx512_default_kernel_fixed/main.log` |
| ordinary staged regression | `spqlios` | PASS | `repro/stage12_spqlios_kernel_regression/main.log` |
| v2 staged gate and microbench | `spqlios_avx512` | PASS | `repro/stage12_avx512_smallr_v2_kernel/main.log` |
| v2 target full gate | `spqlios_avx512` | PASS | `repro/stage12_avx512_smallr_v2_target_full/main.log` |
| v2 full SAB `r=2` smoke | `spqlios_avx512` | SMOKE_ONLY | `repro/stage12_avx512_smallr_v2_bench_r2_reps1_runs1/summary.csv` |
| v2 full SAB `r=4` smoke | `spqlios_avx512` | SMOKE_ONLY | `repro/stage12_avx512_smallr_v2_bench_r4_reps1_runs1/summary.csv` |

Key microbench numbers from the v2 staged log:

| benchmark | r | speedup vs repeated scalar |
|---|---:|---:|
| MAT_TRGSW isolated | 1 | `1.006x` |
| MAT_TRGSW isolated | 2 | `1.226x` |
| MAT_TRGSW isolated | 4 | `1.584x` |
| MAT_TRGSW full-output | 1 | `0.861x` |
| MAT_TRGSW full-output | 2 | `1.449x` |
| MAT_TRGSW full-output | 4 | `1.481x` |
| full SAB smoke | 2 | `1.137x` |
| full SAB smoke | 4 | `1.253x` |

## Stats Sanity Label

```text
v2 isolated MAT evidence: engineering-positive, not paper-grade.
v2 target full correctness: passed for the recorded gate.
v2 full SAB performance: smoke only, not accepted as a final speedup claim.
```

The accepted full SAB result remains the Stage 10 clear-elision path on
`FFT_LIB=spqlios`:

```text
r=2: 1.269x
r=4: 1.337x
```

## Next Work

The v2 kernel proves that more direct AVX512 handling can improve isolated MAT
external product cost, but the full SAB smoke still leaves most of the
acceleration opportunity outside the standalone MAT kernel. The next high-value
work is:

1. PVW-aware post-processing for extraction, packing KS, and HW-KS.
2. SAB-specific sparse/fused variants that reduce `RGSW_monomial_mul` and
   `sparse_mul` overhead.
3. A 3-process v2 full SAB sweep only if v2 remains useful after comparing the
   smoke results against Stage 10.
