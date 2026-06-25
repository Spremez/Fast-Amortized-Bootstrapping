#!/usr/bin/env bash
set -euo pipefail

r="${SAB_PVW_BENCH_R:-4}"
reps="${SAB_PVW_BENCH_REPS:-1}"
runs="${STAGE23_SCHEDULE_BENCH_RUNS:-1}"
out_dir="${STAGE23_SCHEDULE_BENCH_OUT_DIR:-repro/stage23_schedule_fused_bench_r${r}_reps${reps}_runs${runs}}"

STAGE7_BENCH_OUT_DIR="$out_dir" \
FFT_LIB=spqlios_avx512 \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
SAB_PVW_SCHEDULE_FUSED_CMUX=true \
SAB_PVW_BENCH_R="$r" \
SAB_PVW_BENCH_REPS="$reps" \
STAGE7_BENCH_RUNS="$runs" \
bash scripts/run_stage7_bench_sweep.sh
