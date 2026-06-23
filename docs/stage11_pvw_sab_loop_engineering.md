# Stage 11 PVW-SAB Loop Engineering

Date: 2026-06-23

## Objective

Start the next optimization loop after the Stage 10 engineering result. The
goal is to investigate whether PVW/MAT external products can produce larger
SAB speedups through:

- `r=2/r=4` specialized AVX512 MAT kernels;
- fuller PVW post-processing rather than scalar per-lane KS;
- SAB-specific structure in the MAT selector and monomial schedule.

## Loop Structure

Each optimization loop must follow:

```text
theory hypothesis
-> isolated kernel implementation
-> staged correctness
-> target correctness
-> noise check if arithmetic changed
-> full SAB A/B benchmark
-> stats sanity label
-> accept, reject, or redesign
```

## Implemented First Variant

The first implemented variant adds an explicit experimental compile flag:

```text
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
```

When combined with:

```text
FFT_LIB=spqlios_avx512
```

the MAT external product dispatches `k=1,l=1,r in {2,4}` to a fused
row/output AVX512 accumulation path. The default path is unchanged.

## Algorithmic Detail

Generic MAT accumulation:

```text
for row in [0, k+r):
  for out in [0, k+r):
    out[out] += dec_dft[row] * selector[row][out]
```

First AVX512 variant:

```text
for row in [0, k+r):
  for DFT vector block:
    dec = load dec_dft[row]
    for out in [0, k+r):
      out[out] += complex_mul(dec, selector[row][out])
```

This reduces repeated decomposed-row loads, but it does not change the dense
`(k+r)^2` arithmetic count. The first experiment confirms that this is not
enough.

## Experimental Evidence

Raw artifacts:

- `repro/stage11_avx512_rspecialized_kernel/main.log`
- `repro/stage11_avx512_smallr_explicit_kernel_fail/main.log`
- `repro/stage11_avx512_smallr_replay_target_r2/main.log`
- `repro/stage11_avx512_rspecialized_r2_reps2_runs3/summary.csv`
- `repro/stage11_avx512_rspecialized_r4_reps2_runs3/summary.csv`
- `repro/stage11_avx512_smallr_replay_r2_reps1_runs1/summary.csv`
- `repro/stage11_avx512_smallr_replay_r4_reps1_runs1/summary.csv`
- `repro/stage11_avx512_rspecialized_summary.csv`

Full SAB results:

| variant | backend | r | runs | reps/run | PVW mean us | scalar repeated mean us | speedup | status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| smallr_avx512_v1 | spqlios_avx512 | 2 | 3 | 2 | 19,906,032.000 | 24,913,602.333 | 1.253x | not accepted |
| smallr_avx512_v1 | spqlios_avx512 | 4 | 1 | 2 | 38,436,010.000 | 45,685,124.000 | 1.189x | smoke only |
| smallr_avx512_v1 explicit replay | spqlios_avx512 | 2 | 1 | 1 | 20,037,221.000 | 22,216,297.000 | 1.109x | smoke only |
| smallr_avx512_v1 explicit replay | spqlios_avx512 | 4 | 1 | 1 | 36,911,855.000 | 49,943,206.000 | 1.353x | smoke only |

The first two rows were generated before the specialization was put behind the
explicit `MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true` flag. The code path is the
same first variant, but strict reproduction should use the explicit replay rows
or rerun `scripts/run_stage11_avx512_smallr_bench.sh`.

Correctness:

- target `r=2` full bootstrap replay with the explicit specialization flag:
  Pass;
- explicit one-run full SAB benchmark replays for `r=2` and `r=4`: Pass;
- default AVX512 target full bootstrap without the flag: Pass.

Negative result:

- `SAB_PVW_KERNEL_TEST` with the explicit specialization flag crashes during
  staged testing. The last successful line is the `r=1` full-encrypted
  RGSW-monomial lane-equivalence case; the crash occurs before any `r=2`
  RGSW-monomial result is printed. The variant is therefore not promoted to
  default.

## Interpretation

The first AVX512 specialization is insufficient because it preserves the dense
MAT addmul count and still uses a pointer-array output loop inside the vector
loop. The experiment supports the theory risk: for `r=4`, register pressure
and dense accumulation dominate unless the kernel is truly hand-unrolled or the
selector is made sparse/fused at the SAB level.

The accepted Stage 10 result therefore remains the best supported full SAB
optimization: clear-elision on `spqlios` gives `1.269x` at `r=2` and `1.337x`
at `r=4` with 50-seed final-output correctness/noise gates. Stage 11 is an
optimization loop starting point, not a replacement for that result.

## Next Work

1. Hand-unrolled `r=2` and `r=4` kernels:
   - no output pointer arrays in the vector loop;
   - separate functions for each `r`;
   - benchmark only after staged correctness passes.
2. PVW post-processing:
   - PVW packing KS;
   - PVW HW reducing KS;
   - final materialization only.
3. SAB-specific sparse/fused variants:
   - monomial selector special cases;
   - NCMUX automorphism fused with external product;
   - RGSW monomial step fusion.

The current evidence does not justify a multi-fold speedup claim. It justifies
the next loop: reducing dense MAT accumulation and removing the scalar
post-processing tail.
