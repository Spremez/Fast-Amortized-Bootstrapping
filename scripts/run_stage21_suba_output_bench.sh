#!/usr/bin/env bash
set -euo pipefail

r="${SAB_PVW_BENCH_R:-4}"
reps="${SAB_PVW_BENCH_REPS:-1}"
runs="${STAGE21_SUBA_BENCH_RUNS:-1}"
out_dir="${STAGE21_SUBA_BENCH_OUT_DIR:-repro/stage21_suba_output_bench_r${r}_reps${reps}_runs${runs}}"

STAGE7_BENCH_OUT_DIR="$out_dir" \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
SAB_PVW_SUBA_OUTPUT_FUSION=true \
SAB_PVW_BENCH_R="$r" \
SAB_PVW_BENCH_REPS="$reps" \
STAGE7_BENCH_RUNS="$runs" \
bash scripts/run_stage7_bench_sweep.sh
