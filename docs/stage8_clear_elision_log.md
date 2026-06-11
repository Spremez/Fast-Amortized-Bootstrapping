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
- A full Stage 7/8 repeated A/B matrix must be rerun after this change for each
  lane count before claiming new final full SAB speedup numbers.

## r=4 Full-Output Benchmark

Command:

```bash
STAGE7_BENCH_OUT_DIR=repro/stage8_clear_elision_bench_r4_reps2_runs3 \
SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=2 STAGE7_BENCH_RUNS=3 \
bash scripts/run_stage7_bench_sweep.sh
```

Machine-readable tables:

- `repro/stage8_clear_elision_bench_r4_reps2_runs3/summary.csv`
- `repro/stage8_clear_elision_bench_summary.csv`

Result:

| variant | backend | r | runs | reps/run | PVW mean us | scalar repeated mean us | speedup mean | sample stddev | range |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pre-variant | spqlios | 2 | 3 | 2 | 19,266,121.667 | 22,848,639.333 | 1.188x | 0.066 | 1.132x-1.261x |
| clear-elision | spqlios | 2 | 3 | 2 | 18,684,294.000 | 23,642,989.000 | 1.269x | 0.096 | 1.172x-1.364x |
| pre-variant | spqlios | 4 | 3 | 2 | 35,402,965.167 | 46,436,548.167 | 1.312x | 0.014 | 1.302x-1.328x |
| clear-elision | spqlios | 4 | 3 | 2 | 35,044,592.833 | 46,848,311.333 | 1.337x | 0.012 | 1.323x-1.345x |

Interpretation:

- Every clear-elision process-level run passed the full-output correctness gate.
- The `r=4` clear-elision sweep is stable and positive.
- The `r=2` clear-elision sweep is positive but still has visible process-level
  variance.
- Compared with the earlier pre-variant `spqlios` sweeps:
  - `r=2` speedup mean rises from `1.188x` to `1.269x`;
  - `r=4` speedup mean rises from `1.312x` to `1.337x`.
- This is encouraging but not a strict paired variant A/B because the
  pre-variant and clear-elision measurements are from separate process
  campaigns and commits. Treat it as Stage 8 engineering evidence, not a final
  paper-grade optimization claim.

## Remaining Gates

- Stage 6-style smoke noise checks have been rerun after clear-elision:

| variant | backend | r | trials | points | failures | PVW log2 sigma | scalar log2 sigma | PVW-scalar gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| clear-elision | spqlios | 2 | 3 | 12,288 | 0 / 0 / 0 | -8.395 | -8.311 | -0.083 |
| clear-elision | spqlios | 4 | 1 | 8,192 | 0 / 0 / 0 | -8.349 | -8.160 | -0.189 |

Machine-readable table:

- `repro/stage8_clear_elision_noise_summary.csv`

Artifacts:

- `repro/stage8_clear_elision_noise_r2_trials3/main.log`
- `repro/stage8_clear_elision_noise_r4_trials1/main.log`

Deterministic multi-seed sweeps have also been rerun after clear-elision:

```bash
STAGE6_SWEEP_OUT_DIR=repro/stage8_clear_elision_seed_sweep_r2_10 \
SAB_PVW_NOISE_R=2 bash scripts/run_stage6_seed_sweep_range.sh 6862025 10

STAGE6_SWEEP_OUT_DIR=repro/stage8_clear_elision_seed_sweep_r2_40_more \
SAB_PVW_NOISE_R=2 bash scripts/run_stage6_seed_sweep_range.sh 6862035 40

STAGE6_SWEEP_OUT_DIR=repro/stage8_clear_elision_seed_sweep_r4_10 \
SAB_PVW_NOISE_R=4 bash scripts/run_stage6_seed_sweep_range.sh 6862025 10
```

Machine-readable table:

- `repro/stage8_clear_elision_seed_sweep_summary.csv`

| variant | backend | r | seeds | points | failures | gap range | average gap |
|---|---|---:|---:|---:|---:|---:|---:|
| clear-elision | spqlios | 2 | 50 | 204,800 | 0 / 0 / 0 | -0.470 to 0.636 | -0.0039 |
| clear-elision | spqlios | 4 | 10 | 81,920 | 0 / 0 / 0 | -0.541 to 0.510 | -0.2026 |

Artifacts:

- `repro/stage8_clear_elision_seed_sweep_r2_50_aggregate.csv`
- `repro/stage8_clear_elision_seed_sweep_r2_10/summary.csv`
- `repro/stage8_clear_elision_seed_sweep_r2_10/seed_6862025.log` through
  `repro/stage8_clear_elision_seed_sweep_r2_10/seed_6862034.log`
- `repro/stage8_clear_elision_seed_sweep_r2_40_more/summary.csv`
- `repro/stage8_clear_elision_seed_sweep_r2_40_more/seed_6862035.log`
  through
  `repro/stage8_clear_elision_seed_sweep_r2_40_more/seed_6862074.log`
- `repro/stage8_clear_elision_seed_sweep_r4_10/summary.csv`
- `repro/stage8_clear_elision_seed_sweep_r4_10/seed_6862025.log` through
  `repro/stage8_clear_elision_seed_sweep_r4_10/seed_6862034.log`

- The `r=2` clear-elision sweep now matches the earlier pre-variant 50-seed
  engineering gate. It is enough for Stage 8 engineering evidence, but a final
  paper-grade failure-rate claim still needs explicit statistical treatment.
- Repeat resource metrics only if key layout or allocation changes; this variant
  does not change key material.
