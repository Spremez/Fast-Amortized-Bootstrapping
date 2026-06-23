#!/usr/bin/env bash
set -euo pipefail

r="${SAB_PVW_BENCH_R:-2}"
reps="${SAB_PVW_BENCH_REPS:-2}"
runs="${STAGE11_BENCH_RUNS:-3}"
out_dir="${STAGE11_BENCH_OUT_DIR:-repro/stage11_avx512_smallr_r${r}_reps${reps}_runs${runs}}"

STAGE7_BENCH_OUT_DIR="$out_dir" \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_BENCH_R="$r" \
SAB_PVW_BENCH_REPS="$reps" \
STAGE7_BENCH_RUNS="$runs" \
bash scripts/run_stage7_bench_sweep.sh
