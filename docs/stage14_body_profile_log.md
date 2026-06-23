# Stage 14 PVW Body Profile Log

Date: 2026-06-23

## Goal

Stage 13 showed that full-output post-processing is not the dominant cost:
`bootstrap_wo_extract` accounted for about 98.5%-99.0% of the profiled full
PVW SAB call. Stage 14 therefore instruments the PVW sparse blind-rotation
body:

```text
setup_tv_xb -> blind_rotate -> sparse_mul
  -> RGSW_monomial_mul
    -> CMUX/NCMUX
      -> MAT external product
```

The profile is decision evidence for the next algorithmic optimization stage.
It is not a final speedup claim.

## Tooling Added

`SAB_PVW_BODY_PROFILE=true` enables inclusive timing counters for:

- `setup_tv_xb`;
- `blind_rotate`;
- `sparse_mul`;
- `RGSW_monomial_mul`;
- `CMUX`;
- `NCMUX`;
- MAT external product;
- `sub_a`;
- RGSW monomial copy-back.

The wrapper script is:

```text
scripts/run_stage14_body_profile.sh
```

The script runs `SAB_PVW_BENCH=true`, checks the target full-output correctness
line, and writes:

- `body_profile.csv`;
- `bench_summary.csv`;
- raw `run_0.log`.

Timing labels are inclusive. For example, `blind_rotate_us` includes
`sparse_mul_us`, and `cmux_us` includes MAT external-product time. The useful
exclusive proxy for CMUX wrapper overhead is `cmux_us - mat_ep_us`.

## Correctness Gate

The ordinary `spqlios` staged PVW regression still passes with the profile code
compiled out:

```text
make clean
make FFT_LIB=spqlios SAB_PVW_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
./main
```

Artifact:

```text
repro/stage14_spqlios_kernel_regression.log
```

## Target Profile Runs

Commands:

```bash
STAGE14_BODY_OUT_DIR=repro/stage14_body_profile_r2_reps1_runs1 SAB_PVW_BENCH_R=2 SAB_PVW_BENCH_REPS=1 STAGE14_BODY_RUNS=1 FFT_LIB=spqlios bash scripts/run_stage14_body_profile.sh
STAGE14_BODY_OUT_DIR=repro/stage14_body_profile_r4_reps1_runs1 SAB_PVW_BENCH_R=4 SAB_PVW_BENCH_REPS=1 STAGE14_BODY_RUNS=1 FFT_LIB=spqlios bash scripts/run_stage14_body_profile.sh
```

The profile script emits two body-profile rows per run:

- `call_index=0`: correctness preflight inside `SAB_PVW_BENCH`;
- `call_index=1`: the timed benchmark sample.

The table below uses `call_index=1`.

## Results

Target shape:

```text
KEY=BINARY
PARAM=SET_2_3_2048
in_N=2048
out_N=2048
h=39
r_prec=7
```

The measured MAT external-product call count is:

```text
(h + 1) * r_prec * in_N = 40 * 7 * 2048 = 573440
```

This matches the profile for both `r=2` and `r=4`.

| r | full us | blind rotate | RGSW monomial | CMUX | MAT EP | CMUX minus MAT EP | sub_a | copy-back |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 22,922,300 | 99.803% | 98.071% | 95.546% | 43.805% | 51.741% | 1.732% | 1.775% |
| 4 | 42,393,097 | 99.920% | 98.261% | 95.988% | 47.199% | 48.789% | 1.659% | 1.670% |

Per-call timing:

| r | CMUX calls | MAT EP calls | avg CMUX us | avg MAT EP us | NCMUX calls |
|---:|---:|---:|---:|---:|---:|
| 2 | 573,440 | 573,440 | 38.193 | 17.510 | 5,080 |
| 4 | 573,440 | 573,440 | 70.962 | 34.893 | 5,080 |

Instrumented one-run full SAB smokes:

| r | PVW avg us | scalar repeated avg us | speedup | label |
|---:|---:|---:|---:|---|
| 2 | 23,185,027 | 27,798,279 | 1.199x | smoke only |
| 4 | 42,893,673 | 57,447,839 | 1.339x | smoke only |

These numbers are lower-quality performance evidence than the accepted Stage 10
three-process clear-elision result. They are used for prioritization.

## Interpretation

MAT external product is a real hot component, but it is not the whole body:

```text
r=2: MAT EP is 43.805% of no-extract body.
r=4: MAT EP is 47.199% of no-extract body.
```

The full CMUX layer is much larger:

```text
r=2: CMUX is 95.546% of no-extract body.
r=4: CMUX is 95.988% of no-extract body.
```

Therefore, a pure AVX512 MAT kernel can improve an important subcomponent, but
it cannot by itself justify a multi-fold SAB-level acceleration claim. The next
algorithmic target must reduce work around the CMUX layer and the sparse
RGSW-monomial schedule:

- fuse or specialize `pvmtmlwe_sub -> MAT EP -> from_DFT -> add`;
- reduce array ping-pong and copy-back in `RGSW_monomial_mul`;
- fuse `RGSW_monomial_mul` and `sub_a` where the binary sparse schedule permits;
- precompute the `r_prec=7` butterfly/index schedule for the target shape;
- only then revisit AVX512 MAT completion with full SAB sweeps and counters.

## MAT AVX512 Boundary

The current MAT AVX512 work remains experimental:

```text
supported shape: FFT_LIB=spqlios_avx512, k=1, l=1, r in {2,4}
status: staged/target correctness positive, isolated speed positive
missing: default promotion, AVX2/FMA fallback, perf-counter audit,
         broader k/l/r support, repeated full SAB proof
```

For paper claims, Stage 14 supports this narrower statement:

```text
The next SAB acceleration opportunity is CMUX/RGSW/sparse-body fusion, with
MAT external product as the largest inner kernel but not the only dominant
cost.
```

It does not support this stronger statement:

```text
The current AVX512 MAT implementation is complete or sufficient to prove a
multi-fold SAB bootstrapping speedup.
```
