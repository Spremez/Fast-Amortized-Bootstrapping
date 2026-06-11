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

This is a Stage 7 engineering benchmark, not the final performance claim.
Stage 6 now has multi-seed correctness/noise evidence for `r=2` and `r=4`,
but backend separation, memory/key-size, and broader repeated benchmark
campaigns remain open.

## Benchmark Entry

Build flag:

```text
SAB_PVW_BENCH=true
SAB_PVW_BENCH_R=<lane count, default 2>
SAB_PVW_BENCH_REPS=<paired timing repetitions, default 3>
```

Command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_BENCH=true SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=5 KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
./main
```

Latest `r=4` command:

```bash
make clean
make FFT_LIB=spqlios SAB_PVW_BENCH=true SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=3 KEY=BINARY PARAM=SET_2_3_2048 -j$(nproc)
stdbuf -o0 ./main | tee repro/stage7_pvw_bench_r4_reps3/main.log
```

## Target Shape

- backend: WSL/Linux `spqlios`
- `r = 2` in the latest `r=2` paired run
- `r = 4` in the latest `r=4` paired run
- `in_N = 2048`
- `out_N = 2048`
- `h = 39`
- `r_prec = 7`
- message precision: `3`
- output key: PVW ternary sparse, `h_out = 512`, sigma `2^-50`
- packing key: scalar ternary sparse, `h = 256`, sigma `2^-44`
- full packing KS: `ell = 2`, `base_bit = 14`
- HW-reducing KS: `ell = 12`, `base_bit = 1`
- paired benchmark repetitions: configurable; latest recorded run uses `5`

## Correctness Gate

Before timing, the benchmark compares each PVW output lane with the
corresponding scalar output lane:

```text
SAB_PVW_BENCH correctness target_full r=2 h=39 r_prec=7: Pass
```

## r=2 Result

Latest paired-statistics run:

```text
SAB_PVW_BENCH correctness target_full r=2 h=39 r_prec=7: Pass
SAB_PVW_BENCH sample target_full r=2 rep=0 pvw_us=19710710 scalar_repeated_us=24481110 speedup=1.242x
SAB_PVW_BENCH sample target_full r=2 rep=1 pvw_us=20936439 scalar_repeated_us=23437562 speedup=1.119x
SAB_PVW_BENCH sample target_full r=2 rep=2 pvw_us=20842623 scalar_repeated_us=24857840 speedup=1.193x
SAB_PVW_BENCH sample target_full r=2 rep=3 pvw_us=19631023 scalar_repeated_us=25016365 speedup=1.274x
SAB_PVW_BENCH sample target_full r=2 rep=4 pvw_us=20914470 scalar_repeated_us=23729391 speedup=1.135x
SAB_PVW_BENCH summary target_full r=2 reps=5 pvw_avg_us=20407053.000 pvw_stddev_us=673527.822 pvw_lane_avg_us=10203526.500 scalar_repeated_avg_us=24304453.600 scalar_stddev_us=693984.847 scalar_lane_avg_us=12152226.800 speedup_vs_scalar_repeated=1.191x speedup_stddev=0.067
```

Earlier initial run:

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
  bootstrap in the recorded `r=2` target-shape runs.
- The measured gain is a full-output throughput gain, not just raw external
  product speed.
- The current PVW path still materializes each lane after extraction and reuses
  scalar packing/HW KS per lane, so there is remaining overhead outside the
  batched blind-rotation path.
- The `reps=5` paired run gives a stronger engineering signal than the initial
  `reps=3` aggregate run, but it is still not paper-grade statistical evidence.

## r=4 Result

Latest paired-statistics run after the Stage 6 `r=4` 10-seed correctness/noise
sweep:

```text
SAB_PVW_BENCH correctness target_full r=4 h=39 r_prec=7: Pass
SAB_PVW_BENCH sample target_full r=4 rep=0 pvw_us=35823318 scalar_repeated_us=45736214 speedup=1.277x
SAB_PVW_BENCH sample target_full r=4 rep=1 pvw_us=35434510 scalar_repeated_us=47145138 speedup=1.330x
SAB_PVW_BENCH sample target_full r=4 rep=2 pvw_us=35653735 scalar_repeated_us=46108784 speedup=1.293x
SAB_PVW_BENCH summary target_full r=4 reps=3 pvw_avg_us=35637187.667 pvw_stddev_us=194931.465 pvw_lane_avg_us=8909296.917 scalar_repeated_avg_us=46330045.333 scalar_stddev_us=730057.630 scalar_lane_avg_us=11582511.333 speedup_vs_scalar_repeated=1.300x speedup_stddev=0.028
```

Artifact:

- `repro/stage7_pvw_bench_r4_reps3/main.log`

Interpretation:

- Same WSL/Linux `spqlios` backend and same target shape.
- The full-output PVW path was faster than four repeated scalar full
  bootstraps in all three paired samples.
- The average per-lane full-bootstrap time improved from `11,582,511.333 us`
  for repeated scalar to `8,909,296.917 us` for PVW.
- The recorded `r=4` full-output throughput speedup was `1.300x` with speedup
  stddev `0.028`.
- This is stronger than the earlier `r=2` `1.191x` run, but it is still an
  engineering result rather than final paper-grade performance evidence.

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

Latest scalar baseline after the paired benchmark harness change:

```text
Sparse bootstrapping with binary keys
Message precision: 3 - Repetitions: 3
Max monomial distance (log B): 7
Bootstrapping time: 12,275,965 us +- 562,656.030284
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

- repeat the benchmark across multiple runs and report variance;
- separate algorithmic gain from backend/SIMD effects;
- record key size, memory peak, and key generation time.
- add memory/key-size/keygen rows for `r=2` and `r=4`.
