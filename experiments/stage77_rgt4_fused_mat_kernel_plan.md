# Stage77 R>4 Fused MAT Kernel Plan

Date: 2026-06-26

## Goal

Move H11 from theory to an explicit experimental implementation by adding a
tiled r=6/r=8 MAT external-product kernel under
`MAT_TRGSW_AVX512_RGT4_FUSED`, then test whether the kernel signal propagates
to complete SAB smoke.

This stage does not replace scalar SAB, does not change the default
`sab_pvw_*` path, and does not promote r>4 by default.

## Implementation

- Add `MAT_TRGSW_AVX512_RGT4_FUSED` to `src/mosfhet/Makefile.def`.
- In `mat_trgsw_mul_pvmtmlwe_DFT`, dispatch only when
  `k == 1`, `l == 1`, and `r == 6 || r == 8`.
- Use a coefficient-loop and output-tile kernel with tile size 4, reducing
  repeated decomposed-row loads compared with one-polynomial-at-a-time generic
  calls.

## Commands

Kernel smoke:

```bash
make clean
make FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_RGT4_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
stdbuf -o0 ./main | tee repro/stage77_rgt4_fused_mat_kernel/generic.log

make clean
make FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_RGT4_KERNEL_TEST=true KEY=BINARY PARAM=SET_2_3 -j$(nproc)
stdbuf -o0 ./main | tee repro/stage77_rgt4_fused_mat_kernel/fused.log
```

Full-SAB smoke:

```bash
STAGE20_ACTIVE_BENCH_RUNS=1 SAB_PVW_BENCH_R=6 SAB_PVW_BENCH_REPS=1 \
  STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r6 \
  FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true JOBS=$(nproc) \
  bash scripts/run_stage20_active_buffer_bench.sh

STAGE20_ACTIVE_BENCH_RUNS=1 SAB_PVW_BENCH_R=8 SAB_PVW_BENCH_REPS=1 \
  STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage77_rgt4_fused_mat_kernel/full_sab_generic_r8 \
  FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true JOBS=$(nproc) \
  bash scripts/run_stage20_active_buffer_bench.sh

STAGE20_ACTIVE_BENCH_RUNS=1 SAB_PVW_BENCH_R=6 SAB_PVW_BENCH_REPS=1 \
  STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r6 \
  FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true JOBS=$(nproc) \
  bash scripts/run_stage20_active_buffer_bench.sh

STAGE20_ACTIVE_BENCH_RUNS=1 SAB_PVW_BENCH_R=8 SAB_PVW_BENCH_REPS=1 \
  STAGE20_ACTIVE_BENCH_OUT_DIR=repro/stage77_rgt4_fused_mat_kernel/full_sab_fused_r8 \
  FFT_LIB=spqlios_avx512 MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true JOBS=$(nproc) \
  bash scripts/run_stage20_active_buffer_bench.sh
```

Aggregation:

```bash
python scripts/build_stage77_rgt4_fused_mat_kernel.py
```

## Gates

- generic and fused r=6/r=8 kernel correctness must pass;
- fused kernel must beat generic in DFT-output and full-output microbench;
- fused complete-SAB r=6/r=8 smoke must pass correctness and beat same-stage
  generic r>4;
- no r>4 promotion is allowed until repeated full-SAB, noise, and resource
  gates pass.

## Failure Handling

- If correctness fails, disable the flag and fix the kernel before measuring
  performance.
- If kernel improves but full SAB does not, keep the result as kernel-only.
- If one-run full SAB improves, open repeated Stage78 gates rather than
  changing defaults.
