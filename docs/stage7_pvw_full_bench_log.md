# Stage 7 PVW Full Bootstrap Benchmark Log

Date: 2026-06-11

## Objective

Create the first full SAB bootstrapping A/B benchmark for the target PVW path:

```text
sab_pvw_bootstrap_binary(..., r lanes)
vs
r repeated scalar sab_rlwe_bootstrap(...) calls
```

The benchmark excludes key generation. It measures full bootstrap calls,
including:

- setup/blind rotation;
- extraction;
- full packing KS;
- HW-reducing KS;
- final TRLWE outputs.

This is an initial Stage 7 engineering benchmark, not the final performance
claim. Multi-seed correctness/noise and repeated statistical runs remain open.

## Benchmark Entry

Build flag:

```text
SAB_PVW_BENCH=true
```

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_BENCH=true KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
./main
```

## Target Shape

- backend: WSL/Linux `spqlios`
- `r = 2`
- `in_N = 2048`
- `out_N = 2048`
- `h = 39`
- `r_prec = 7`
- message precision: `3`
- output key: PVW ternary sparse, `h_out = 512`, sigma `2^-50`
- packing key: scalar ternary sparse, `h = 256`, sigma `2^-44`
- full packing KS: `ell = 2`, `base_bit = 14`
- HW-reducing KS: `ell = 12`, `base_bit = 1`
- benchmark repetitions: `3`

## Correctness Gate

Before timing, the benchmark compares each PVW output lane with the
corresponding scalar output lane:

```text
SAB_PVW_BENCH correctness target_full r=2 h=39 r_prec=7: Pass
```

## Result

```text
SAB_PVW_BENCH target_full r=2 reps=3
pvw_avg_us=20329962.667
pvw_lane_avg_us=10164981.333
scalar_repeated_avg_us=24774453.000
scalar_lane_avg_us=12387226.500
speedup_vs_scalar_repeated=1.219x
```

Interpretation:

- Same backend and same target shape.
- PVW/MAT shared-mask full bootstrap is faster than repeated scalar full
  bootstrap in this first `r=2` run.
- The measured gain is a full-output throughput gain, not just raw external
  product speed.
- The current PVW path still materializes each lane after extraction and reuses
  scalar packing/HW KS per lane, so there is remaining overhead outside the
  batched blind-rotation path.

## Scalar Baseline Regression

Command:

```bash
make clean
make FFT_LIB=spqlios KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
Sparse bootstrapping with binary keys
Message precision: 3 - Repetitions: 3
Max monomial distance (log B): 7
Bootstrapping time: 12,169,956 us +- 507,161.167778
Pass
```

The default scalar build still does not link `sab_pvw.o`.

## FFNT Smoke

Command:

```bash
make clean
make FFT_LIB=ffnt SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Result:

```text
SAB_PVW API full bootstrap binary lane equivalence r=1 h=2 r_prec=3: Pass
SAB_PVW API full bootstrap binary lane equivalence r=2 h=2 r_prec=3: Pass
SAB_PVW API full bootstrap binary lane equivalence r=4 h=2 r_prec=3: Pass
MAT_TRGSW/PVW staged kernel test: Pass
```

FFNT remains a portability/correctness smoke only.

## Remaining Work

Before claiming final SAB acceleration:

- run multi-seed correctness/noise checks;
- repeat the benchmark across multiple runs and report variance;
- test `r=4` target shape if memory/time permits;
- separate algorithmic gain from backend/SIMD effects;
- record key size, memory peak, and key generation time.
