# Stage 15 AVX512 MAT Expectation Log

Date: 2026-06-25

## Goal

Advance the AVX512 implementation of `MAT_TRGSW_DFT x PVW_TMLWE` until the
implemented kernel reaches the practical expectation allowed by the current
dense MAT external-product model.

This stage is deliberately scoped:

```text
FFT_LIB=spqlios_avx512
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
k=1
l=1
r in {2,4}
N=2048
```

It does not claim general AVX512 support for all `k,l,r`, and it does not claim
multi-fold full SAB acceleration by MAT kernel work alone.

## Theory Boundary

For `k=1,l=1`, scalar repeated external product and MAT shared-mask external
product have the following dense counts:

| r | scalar decompose/DFT rows | MAT decompose/DFT rows | scalar complex products | MAT complex products |
|---:|---:|---:|---:|---:|
| 1 | 2 | 2 | 4 | 4 |
| 2 | 4 | 3 | 8 | 9 |
| 4 | 8 | 5 | 16 | 25 |

The MAT path saves decomposition and torus-to-DFT rows by sharing the mask. It
does not reduce the dense multiplication count; for `r=4`, MAT has more complex
products than repeated scalar. Therefore the theoretical expectation for the
current dense MAT model is a moderate throughput gain, not a `r`-fold speedup.

The practical target is:

```text
r=2/r=4 should be clearly positive at the MAT full-output boundary;
r=2/r=4 should be positive at the DFT-output boundary;
the staged lane-equivalence gate must pass;
target full-output correctness must pass;
full SAB smoke must remain positive.
```

## Implementation Delta

The AVX512 addmul helper now accumulates directly into ZMM accumulators:

```c
acc_re = fmadd(dec_re, sel_re, acc_re)
acc_re = fnmadd(dec_im, sel_im, acc_re)
acc_im = fmadd(dec_im, sel_re, acc_im)
acc_im = fmadd(dec_re, sel_im, acc_im)
```

This replaces the previous pattern:

```text
tmp = complex_mul(dec, selector)
acc += tmp
```

The old form used extra vector add/mul work after the complex product. The new
form follows the same fused-accumulation idea used by the existing
`polynomial_mul_addto_DFT()` AVX512 path.

For `r=2`, the fixed three-row `k=1,l=1,r=2` kernel also hoists row pointers
and explicitly accumulates rows 1 and 2. A similar pointer-array attempt for
`r=4` was tested and rejected because repeated runs showed worse MAT
mul/add-phase time from register/stack pressure. The final `r=4` variant keeps
the original row loop shape but uses the fused addmul helper.

Instruction audit artifact:

```text
repro/stage15_avx512_mat_instruction_snippet.txt
```

It contains `vfmadd*`, `vfnmadd*`, and `vfmsub*` instructions in
`mattrgsw.o`.

## Repro Tooling

New wrapper:

```text
scripts/run_stage15_avx512_mat_gate.sh
```

It builds:

```bash
make FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
```

Then it repeats `./main` and emits:

- `mat_vs_scalar.csv`;
- `mat_full_vs_scalar.csv`;
- `ep_breakdown.csv`;
- raw `run_*.log`.

## MAT Gate Results

Command:

```bash
STAGE15_AVX512_MAT_OUT_DIR=repro/stage15_avx512_mat_gate_runs3 \
STAGE15_AVX512_MAT_RUNS=3 \
bash scripts/run_stage15_avx512_mat_gate.sh
```

All three runs passed the staged MAT/PVW correctness gate.

Three-run averages:

| scope | r | scalar avg us | MAT avg us | speedup |
|---|---:|---:|---:|---:|
| DFT output | 1 | 7.058 | 6.380 | 1.121x |
| DFT output | 2 | 12.864 | 9.373 | 1.380x |
| DFT output | 4 | 28.107 | 22.130 | 1.267x |
| full output | 1 | 12.306 | 11.100 | 1.110x |
| full output | 2 | 22.660 | 16.031 | 1.416x |
| full output | 4 | 49.980 | 34.006 | 1.471x |

Phase averages:

| r | scalar phase sum | MAT phase sum | scalar mul | MAT mul |
|---:|---:|---:|---:|---:|
| 1 | 6.738 | 6.831 | 1.831 | 1.873 |
| 2 | 15.116 | 12.673 | 4.554 | 4.687 |
| 4 | 31.267 | 26.326 | 9.813 | 12.737 |

Interpretation:

```text
r=2: MAT saves decompose/DFT and only slightly increases dense mul count.
r=4: MAT saves decompose/DFT but pays the expected dense 25-vs-16 mul cost.
```

The measured `r=4` MAT mul phase is larger than repeated scalar, exactly as the
dense count model predicts. The full-output boundary is stronger because MAT
also reduces inverse DFT/output conversion repetition.

## SAB Path Smokes

Target full correctness:

```text
SAB_PVW target full bootstrap gate: Pass
```

One-run full SAB smokes:

| r | PVW avg us | scalar repeated avg us | speedup | label |
|---:|---:|---:|---:|---|
| 2 | 15,876,350 | 20,087,594 | 1.265x | smoke only |
| 4 | 30,022,641 | 40,716,798 | 1.356x | smoke only |

These are smoke checks only. They prove that the AVX512 MAT kernel remains
compatible with the target SAB path and positive in this run. They do not
replace repeated full SAB sweeps.

## Decision

Within the scoped shape `k=1,l=1,r in {2,4}`, the current AVX512 MAT
implementation has reached the practical expectation of the dense MAT model:

- staged correctness passes;
- target full correctness passes;
- DFT-output MAT is positive for `r=2` and `r=4`;
- full-output MAT is positive for `r=2` and `r=4`;
- full SAB smokes remain positive.

The remaining gap to multi-fold SAB acceleration is not primarily an AVX512
instruction issue. It is algorithmic:

```text
dense MAT external product still has (k+r)^2*l complex products;
Stage 14 showed CMUX and non-MAT CMUX work remain large;
future speedup must come from CMUX/RGSW/sparse-body fusion or a less dense
MAT/SAB-specific external-product formulation.
```

Promotion boundary:

```text
Do not enable MAT_TRGSW_AVX512_SMALLR_SPECIALIZED by default yet.
```

Required before default promotion:

- repeated full SAB sweeps under `spqlios_avx512`;
- noise/seed gate with the exact AVX512 variant;
- perf-counter audit;
- decision on whether non-AVX512/FMA fallback is required;
- broader `k,l,r` policy or explicit target-only documentation.
