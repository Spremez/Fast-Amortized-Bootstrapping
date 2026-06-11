# Stage 8 Clear-Elision Variant Log

Date: 2026-06-11

## Objective

Evaluate and implement the lowest-risk MAT external-product kernel variant:
remove the separate DFT-output clear pass in
`mat_trgsw_mul_pvmtmlwe_DFT(...)`.

This is an implementation variant, not a protocol change. It keeps the
`sab_pvw_*` lane invariant and scalar SAB path unchanged.

## Implementation

Changed files:

- `src/mosfhet/src/mattrgsw.c`
- `main.c`

Kernel change:

```text
old:
  clear output
  for every row:
    output += dec_dft[row] * selector[row]

new:
  output = dec_dft[0] * selector[0]
  for row = 1..rows-1:
    output += dec_dft[row] * selector[row]
```

The phase-breakdown microbench in `main.c` was updated to match the new kernel
boundary. Its MAT `clear_avg_us` is now expected to be `0.000`.

## Correctness Gates

### Kernel and Small API Gate

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
stdbuf -o0 ./main | tee repro/stage8_clear_elision_kernel_spqlios/main.log
```

Result:

```text
SAB_PVW isolated CMUX/NCMUX lane equivalence r=1: Pass
SAB_PVW isolated CMUX/NCMUX lane equivalence r=2: Pass
SAB_PVW isolated CMUX/NCMUX lane equivalence r=4: Pass
SAB_PVW API full bootstrap binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API full bootstrap binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API full bootstrap binary lane equivalence r=4 h=2 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

Kernel smoke from the same run:

```text
MAT_TRGSW_FULL vs scalar_full r=1 ... speedup_vs_scalar_repeated=1.045x
MAT_TRGSW_FULL vs scalar_full r=2 ... speedup_vs_scalar_repeated=1.250x
MAT_TRGSW_FULL vs scalar_full r=4 ... speedup_vs_scalar_repeated=1.266x
EP_BREAKDOWN mat_shared_mask r=1 ... clear_avg_us=0.000
EP_BREAKDOWN mat_shared_mask r=2 ... clear_avg_us=0.000
EP_BREAKDOWN mat_shared_mask r=4 ... clear_avg_us=0.000
```

Artifact:

- `repro/stage8_clear_elision_kernel_spqlios/main.log`

### Target-Shape PVW Gate

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
stdbuf -o0 ./main | tee repro/stage8_clear_elision_target_spqlios/main.log
```

Result:

```text
SAB_PVW target full bootstrap binary lane equivalence r=2 h=39 r_prec=7: Pass
SAB_PVW target full bootstrap gate: Pass
```

Artifact:

- `repro/stage8_clear_elision_target_spqlios/main.log`

### Scalar Baseline Gate

Command:

```bash
make clean
make FFT_LIB=spqlios KEY=BINARY PARAM=SET_2_3 -j$(nproc)
stdbuf -o0 ./main | tee repro/stage8_clear_elision_scalar_spqlios/main.log
```

Result:

```text
Sparse bootstrapping with binary keys
Bootstrapping time: 11,555,228 us +- 895,795.872240
Pass
```

Artifact:

- `repro/stage8_clear_elision_scalar_spqlios/main.log`

## Interpretation

- The variant removes a redundant clear pass from the MAT/PVW external-product
  hot path.
- The small `r=1/2/4` correctness gates, target-shape PVW gate, and default
  scalar SAB smoke all pass.
- Kernel-level timings remain noisy and should be treated as smoke evidence.
- A full Stage 7/8 repeated A/B matrix must be rerun after this change before
  claiming any new full SAB speedup number for the clear-elision variant.

## Next Gate

Run the target-shape full-output benchmark after clear-elision:

```bash
STAGE7_BENCH_OUT_DIR=repro/stage8_clear_elision_bench_r4_reps2_runs3 \
SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=2 STAGE7_BENCH_RUNS=3 \
bash scripts/run_stage7_bench_sweep.sh
```

`r=4` should be prioritized because it is the strongest and most stable lane
count across `spqlios` and `spqlios_avx512`.
