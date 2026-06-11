# MAT_TRGSW external-product breakdown

Date: 2026-06-11

This note records a WSL/Linux `spqlios` comparison between:

- scalar repeated external products:
  `r * (TRGSW_DFT x TRLWE -> TRLWE_DFT)`
- one shared-mask matrix external product:
  `MAT_TRGSW_DFT x PVW_TMLWE -> PVW_TMLWE_DFT`

Command:

```bash
make -B FFT_LIB=spqlios A_PRNG=none ENABLE_VAES=false \
  ENABLE_PVW_TMLWE=true SAB_PVW_KERNEL_TEST=true
./main
```

Shape:

- `N=2048`
- `k=1`
- `l=1`
- `Bg_bit=23`
- `reps=1000`
- `r in {1,2,4}`

## Operation counts

For current `k=1,l=1`:

| r | scalar decompose/DFT rows | MAT decompose/DFT rows | scalar DFT mul/add | MAT DFT mul/add |
|---:|---:|---:|---:|---:|
| 1 | 2 | 2 | 4 | 4 |
| 2 | 4 | 3 | 8 | 9 |
| 4 | 8 | 5 | 16 | 25 |

The MAT path saves decomposition and torus-to-DFT rows by sharing the mask, but
the current mbfhe-style matrix accumulation is dense: every decomposed row is
multiplied into all `k+r` output components.

## Current end-to-end kernel A/B

These timings call the current external-product functions. Scalar calls the
existing `trgsw_mul_trlwe_DFT(...)` `r` times. MAT calls
`mat_trgsw_mul_pvmtmlwe_DFT(...)` once with preallocated MAT scratch.

Four runs:

| r | avg speedup vs scalar repeated | min | max |
|---:|---:|---:|---:|
| 1 | 1.071x | 0.949x | 1.217x |
| 2 | 1.019x | 0.929x | 1.175x |
| 4 | 1.162x | 1.075x | 1.264x |

The end-to-end timings still have noticeable run-to-run noise at this scale.

## Scratch-normalized phase breakdown

Both paths use preallocated decomposition scratch in this breakdown. This
isolates the arithmetic phases:

- `decompose`
- `torus_to_DFT`
- `clear` / output initialization
- `DFT mul/add`

Average over four runs, in microseconds per external-product comparison:

| r | path | phase sum | decompose | DFT convert | clear | DFT mul/add |
|---:|---|---:|---:|---:|---:|---:|
| 1 | scalar repeated | 10.028 | 0.905 | 5.913 | 0.000 | 3.210 |
| 1 | MAT shared-mask | 10.057 | 0.928 | 5.916 | 0.450 | 2.763 |
| 2 | scalar repeated | 19.866 | 2.342 | 11.401 | 0.000 | 6.123 |
| 2 | MAT shared-mask | 17.160 | 1.748 | 8.384 | 0.986 | 6.043 |
| 4 | scalar repeated | 40.198 | 4.736 | 22.622 | 0.000 | 12.840 |
| 4 | MAT shared-mask | 36.691 | 3.055 | 14.275 | 1.839 | 17.521 |

Percent of each phase sum:

| r | path | decompose | DFT convert | clear | DFT mul/add |
|---:|---|---:|---:|---:|---:|
| 1 | scalar repeated | 9.02% | 58.97% | 0.00% | 32.01% |
| 1 | MAT shared-mask | 9.23% | 58.82% | 4.47% | 27.48% |
| 2 | scalar repeated | 11.79% | 57.39% | 0.00% | 30.82% |
| 2 | MAT shared-mask | 10.19% | 48.86% | 5.74% | 35.21% |
| 4 | scalar repeated | 11.78% | 56.28% | 0.00% | 31.94% |
| 4 | MAT shared-mask | 8.33% | 38.91% | 5.01% | 47.75% |

## AVX512_OPT validation

The top-level `Makefile` now has rules for the MOSFHET `spqlios_avx512`
objects:

- `spqlios-fft-avx512.o`
- `spqlios-ifft-avx512.o`
- `spqlios-fft-impl-avx512.o`

Validation command:

```bash
make -B FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false \
  ENABLE_PVW_TMLWE=true SAB_PVW_KERNEL_TEST=true
./main
```

The WSL CPU exposes `avx512f`, `avx512dq`, `avx512bw`, and `avx512vl`.
`SAB_PVW_KERNEL_TEST` passed in all validation runs.

Function-level disassembly confirms that `polynomial_mul_addto_DFT` enters the
AVX512 branch:

```text
00000000000095f0 <polynomial_mul_addto_DFT>:
  vmovapd ...,%zmm2
  vfmsub132pd ...
  vfmsub231pd ...
  vfmadd132pd ...
  vfmadd231pd ...
```

Three-run average comparison, in microseconds:

| backend | r | scalar repeated | MAT shared-mask | end-to-end speedup |
|---|---:|---:|---:|---:|
| spqlios | 1 | 10.464 | 10.100 | 1.039x |
| spqlios_avx512 | 1 | 8.291 | 8.390 | 0.987x |
| spqlios | 2 | 20.454 | 18.585 | 1.107x |
| spqlios_avx512 | 2 | 16.136 | 15.525 | 1.054x |
| spqlios | 4 | 41.237 | 38.607 | 1.069x |
| spqlios_avx512 | 4 | 34.451 | 33.341 | 1.041x |

Scratch-normalized AVX512 phase breakdown, in microseconds:

| r | path | phase sum | decompose | DFT convert | clear | DFT mul/add |
|---:|---|---:|---:|---:|---:|---:|
| 1 | scalar repeated | 8.602 | 1.069 | 5.049 | 0.000 | 2.484 |
| 1 | MAT shared-mask | 9.269 | 1.103 | 5.088 | 0.653 | 2.425 |
| 2 | scalar repeated | 18.516 | 2.758 | 10.253 | 0.000 | 5.505 |
| 2 | MAT shared-mask | 16.566 | 2.119 | 7.846 | 1.114 | 5.487 |
| 4 | scalar repeated | 40.671 | 6.327 | 21.882 | 0.000 | 12.462 |
| 4 | MAT shared-mask | 35.759 | 3.926 | 13.705 | 2.364 | 15.765 |

AVX512 improves both scalar and MAT external products, but it does not change
the dense count model. For `r=4`, MAT still spends about 44% of its
scratch-normalized time in DFT mul/add. The relative MAT speedup is therefore
slightly smaller under AVX512 because both paths benefit from the faster DFT
backend and multiply-add code.

## Follow-up bench: AVX and full-output boundary

Raw logs:

- `build/bench_logs/mat_avx_mbfhe_20260611_133003`
- `build/bench_logs/mat_full_compare_20260611_133342`

The initial MOSFHET benchmark stops at DFT-domain output:

```text
input torus -> decompose -> torus_to_DFT -> DFT mul/add -> output DFT
```

mbfhe's matrix external-product benchmark converts the result back to torus:

```text
input torus -> decompose -> FFT -> FFT addmul -> inverse FFT -> output torus
```

To avoid mixing these boundaries, the follow-up MOSFHET benchmark also reports
`MAT_TRGSW_FULL vs scalar_full`, which adds `trlwe_from_DFT(...)` or
`pvmtmlwe_from_DFT(...)` after the external product.

Three-run average, DFT-output boundary:

| backend | r | scalar repeated | MAT shared-mask | speedup |
|---|---:|---:|---:|---:|
| spqlios | 1 | 10.208 | 9.062 | 1.126x |
| spqlios | 2 | 17.792 | 15.901 | 1.120x |
| spqlios | 4 | 36.439 | 36.316 | 1.005x |
| spqlios_avx512 | 1 | 6.186 | 6.912 | 0.904x |
| spqlios_avx512 | 2 | 12.878 | 11.722 | 1.116x |
| spqlios_avx512 | 4 | 26.129 | 25.784 | 1.012x |

Three-run average, full-output boundary:

| backend | r | scalar repeated full | MAT shared-mask full | speedup |
|---|---:|---:|---:|---:|
| spqlios | 1 | 17.607 | 18.004 | 0.981x |
| spqlios | 2 | 33.011 | 28.031 | 1.185x |
| spqlios | 4 | 65.310 | 52.086 | 1.257x |
| spqlios_avx512 | 1 | 10.405 | 11.348 | 0.919x |
| spqlios_avx512 | 2 | 21.246 | 18.102 | 1.175x |
| spqlios_avx512 | 4 | 45.017 | 35.500 | 1.268x |

At the full-output boundary, MAT benefits more clearly for `r=2` and `r=4`
because scalar repetition performs `2r` inverse DFT polynomial conversions,
while MAT performs `k+r` conversions.

## mbfhe comparison

mbfhe was run from `D:\projects\mbfhe-mb\build-codex-perf` with
`ENABLE_SPQLIOS_FMA=ON`, `N=2048`, `k=1`, `l=1`, `Bgbit=23`, `r in {1,2,4}`,
`iterations=1000`, `warmup=100`, and `pool=32`.

Matrix external-product results, in microseconds:

| r | method | mean | median | p95 | stddev |
|---:|---|---:|---:|---:|---:|
| 1 | original_as_is | 19.204 | 17.516 | 29.488 | 6.205 |
| 1 | full_decomp_ws | 19.227 | 17.780 | 28.436 | 6.306 |
| 1 | streaming_ws | 18.534 | 17.195 | 28.198 | 5.164 |
| 2 | original_as_is | 36.997 | 33.587 | 53.172 | 10.446 |
| 2 | full_decomp_ws | 30.226 | 28.159 | 41.717 | 6.021 |
| 2 | streaming_ws | 29.917 | 27.443 | 41.314 | 7.522 |
| 4 | original_as_is | 97.841 | 97.793 | 152.291 | 30.659 |
| 4 | full_decomp_ws | 60.380 | 55.743 | 85.208 | 12.683 |
| 4 | streaming_ws | 58.773 | 53.884 | 84.216 | 13.520 |

mbfhe CMUX-level matrix vs repeated scalar results:

| r | matrix CMUX mean | scalar-repeat CMUX mean | matrix speedup |
|---:|---:|---:|---:|
| 1 | 23.598 | 23.075 | 0.978x |
| 2 | 38.727 | 48.093 | 1.242x |
| 4 | 76.165 | 103.082 | 1.353x |

The mbfhe data supports the same qualitative claim: matrix/shared-mask is not
better for `r=1`, but becomes useful for `r=2` and `r=4` once repeated scalar
work is included. Its `streaming_ws` variant is slightly faster than
`full_decomp_ws`, but it does not change the dense `(k+r)^2*l` DFT addmul count.

Do not directly compare MOSFHET DFT-output timings against mbfhe full-output
timings as absolute library speed. The fair conclusions are:

- within MOSFHET, MAT wins for `r=2,4` at the full-output boundary;
- within mbfhe, matrix CMUX wins for `r=2,4`;
- both libraries use dense row accumulation for MAT external product;
- AVX/FMA improves per-polynomial addmul, but does not create a special
  large-matrix algorithmic advantage unless the kernel is fused across output
  components.

## Strict scalar-vs-MAT external-product bench

This follow-up adds a strict mbfhe pure external-product method named
`scalar_repeat_full_ws` to
`D:\projects\mbfhe-mb\src\test\test-matrix-external-product-bench.cpp`.

Strict protocol:

- same parameters: `N=2048`, `k=1`, `l=1`, `Bgbit=23`, `r in {1,2,4}`;
- full-output boundary: torus input to torus output;
- selector is precomputed in FFT/DFT form;
- decomposition/FFT/addmul/iFFT workspace is preallocated;
- timed region excludes allocation, key generation, selector conversion, input
  copy, CMUX copy/sub/add, and free;
- measured methods include repeated scalar external product and MAT external
  product.

Raw log:

- `build/bench_logs/strict_external_product_20260611_135128`

MOSFHET strict full-output external product, five-run average:

| backend | r | scalar repeat | MAT shared-mask | MAT speedup |
|---|---:|---:|---:|---:|
| spqlios | 1 | 21.461 | 22.102 | 0.977x |
| spqlios | 2 | 42.298 | 33.422 | 1.266x |
| spqlios | 4 | 82.929 | 61.910 | 1.340x |
| spqlios_avx512 | 1 | 11.280 | 12.160 | 0.928x |
| spqlios_avx512 | 2 | 24.265 | 20.245 | 1.199x |
| spqlios_avx512 | 4 | 49.362 | 40.904 | 1.216x |

mbfhe strict full-output external product, `spqlios-fma`, 1000 iterations:

| r | scalar repeat | MAT full-decomp | MAT speedup | MAT streaming | streaming speedup |
|---:|---:|---:|---:|---:|---:|
| 1 | 18.333 | 17.658 | 1.038x | 18.186 | 1.008x |
| 2 | 37.115 | 30.025 | 1.236x | 30.215 | 1.228x |
| 4 | 63.909 | 49.478 | 1.292x | 48.209 | 1.326x |

This is the cleanest current evidence for MAT vs repeated scalar:

- in both MOSFHET and mbfhe, MAT is not meaningfully better at `r=1`;
- in both MOSFHET and mbfhe, MAT wins clearly at `r=2` and `r=4`;
- mbfhe `spqlios-fma` scalar repeat is faster than MOSFHET non-AVX512
  `spqlios` scalar repeat in this run;
- MOSFHET `spqlios_avx512` is faster than mbfhe `spqlios-fma`, but this is a
  backend comparison, not proof that MOSFHET's scalar algorithm is inherently
  better.

## Same-backend algorithm-only comparison

For algorithm comparison, the valid quantity is the speedup inside one fixed
backend:

```text
algorithm speedup = repeated scalar full-output time / MAT full-output time
```

This avoids mixing MOSFHET scalar timings with mbfhe MAT timings, or AVX512
timings with AVX/FMA timings.

| implementation/backend | low-level kernel | r=1 | r=2 | r=4 |
|---|---|---:|---:|---:|
| MOSFHET `spqlios` | same MOSFHET backend for scalar and MAT | 0.977x | 1.266x | 1.340x |
| MOSFHET `spqlios_avx512` | same AVX512 backend for scalar and MAT | 0.928x | 1.199x | 1.216x |
| mbfhe `spqlios-fma` full-decomp | same AVX/FMA backend for scalar and MAT | 1.038x | 1.236x | 1.292x |
| mbfhe `spqlios-fma` streaming | same AVX/FMA backend for scalar and MAT | 1.008x | 1.228x | 1.326x |

Same-backend conclusion:

- `r=1`: MAT has no stable algorithmic advantage.
- `r=2`: MAT gives about `1.20x-1.27x` algorithmic speedup.
- `r=4`: MAT gives about `1.22x-1.34x` algorithmic speedup.

The exact number depends on backend and workspace layout, but the direction is
consistent across fixed-backend experiments.

To compare MOSFHET and mbfhe absolute implementation speed fairly, one of these
extra engineering steps is required:

- port mbfhe's AVX/FMA `LagrangeHalfCPolynomialAddMul`-style kernel into
  MOSFHET and compare both on AVX/FMA; or
- add an AVX512 backend to mbfhe and compare both on AVX512; or
- build both libraries against a shared standalone DFT addmul kernel.

Until then, cross-library absolute timings are backend comparisons, not pure
algorithm comparisons.

## Same-level AVX/FMA MAT implementation comparison

MOSFHET was extended with a `DFT_FMA_OPT` path in
`polynomial_mul_DFT(...)` and `polynomial_mul_addto_DFT(...)`. This keeps
MOSFHET on `FFT_LIB=spqlios` for FFT/IFFT and uses 256-bit AVX/FMA for DFT
polynomial multiply/add, matching the ISA level used by mbfhe `spqlios-fma`.

Build command:

```bash
make -B FFT_LIB=spqlios ARCH_FLAGS='-march=native -DDFT_FMA_OPT' \
  A_PRNG=none ENABLE_VAES=false ENABLE_PVW_TMLWE=true \
  SAB_PVW_KERNEL_TEST=true
```

Disassembly check:

```text
polynomial_mul_addto_DFT: has ymm, vfmadd/vfnmadd; no zmm
```

Raw log:

- `build/bench_logs/same_backend_fma_mat_compare_20260611_140333`

Same-level AVX/FMA full-output MAT comparison:

| r | MOSFHET MAT | mbfhe MAT full-decomp | MOSFHET / mbfhe |
|---:|---:|---:|---:|
| 1 | 18.726 | 17.659 | 1.060x |
| 2 | 29.112 | 27.754 | 1.049x |
| 4 | 54.352 | 55.542 | 0.979x |

Using mbfhe's streaming MAT variant:

| r | MOSFHET MAT | mbfhe MAT streaming | MOSFHET / mbfhe |
|---:|---:|---:|---:|
| 1 | 18.726 | 18.128 | 1.033x |
| 2 | 29.112 | 27.830 | 1.046x |
| 4 | 54.352 | 55.198 | 0.985x |

Interpretation:

- with AVX512 removed from MOSFHET, the absolute MAT implementation gap is
  small;
- mbfhe is about `5-6%` faster for `r=1,2` in full-decomp mode;
- MOSFHET is about `2%` faster for `r=4` in this run;
- these differences are much smaller than the scalar-vs-MAT algorithmic
  speedups, so current evidence does not support a strong claim that either MAT
  implementation is decisively better once the SIMD level is aligned.

This is still not a literal shared-object-code comparison: MOSFHET and mbfhe use
separate AVX/FMA kernels and memory layouts. It is, however, the first fair
same-ISA-level implementation comparison in this project.

## Interpretation

The measured data matches the count model:

- MAT reduces decompose + DFT conversion work.
- MAT increases dense DFT mul/add work as `r` grows.

For `r=2`, the saved decompose/DFT time is larger than the extra dense
accumulation cost.

For `r=4`, MAT still wins in the scratch-normalized phase sum in these runs, but
the bottleneck moves: DFT mul/add rises to about 48% of MAT time. This is the
expected dense-matrix effect.

Using the observed `r=4` averages:

```text
scalar decompose+DFT: 4.736 + 22.622 = 27.358 us
MAT decompose+DFT:    3.055 + 14.275 = 17.330 us
saved:                10.028 us

scalar mul/add:       12.840 us
MAT mul/add:          17.521 us
extra:                 4.681 us

MAT clear overhead:    1.839 us
net phase advantage:   about 3.5 us
```

So the current MAT form is better only while DFT-conversion savings dominate the
dense mul/add overhead. With `k=1,l=1`, the rough break-even condition is:

```text
C_decompose+DFT_per_row > (r - 1) * C_mul_per_DFT_polynomial
```

The measured ratio suggests `r=4` can still be useful, but larger `r` is likely
to lose unless the dense accumulation is optimized or sparsity/structure is
exploited.

## Optimization implication

The next MAT-kernel optimization target is not decomposition. The data shows
`torus_to_DFT` is already reduced by shared-mask batching. The next target is
the dense accumulation:

- skip structurally zero selector components if available;
- specialize small `k=1,l=1,r={2,4}` kernels;
- avoid clearing output separately by using first row as initialization where
  correct;
- batch polynomial mul/add loops to improve cache locality;
- test whether selector structure from SAB CMUX permits a sparser matrix than
  the general mbfhe-style dense external product.
