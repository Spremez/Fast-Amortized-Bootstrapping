#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE82_OUT_DIR:-repro/stage82_post_h11_profile}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
jobs="${JOBS:-$(nproc)}"
r_value="${STAGE82_PROFILE_R:-6}"
runs="${STAGE82_PROFILE_RUNS:-1}"
reps="${SAB_PVW_BENCH_REPS:-1}"

mkdir -p "$out_dir"

STAGE20_ACTIVE_PROFILE_R_VALUES="$r_value" \
STAGE20_ACTIVE_PROFILE_RUNS="$runs" \
STAGE20_ACTIVE_PROFILE_OUT_DIR="$out_dir/body_profile_fused_r${r_value}" \
FFT_LIB="$fft_lib" \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
MAT_TRGSW_AVX512_RGT4_FUSED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
SAB_PVW_BENCH_REPS="$reps" \
JOBS="$jobs" \
bash scripts/run_stage20_active_buffer_profile.sh

python3 scripts/build_stage82_post_h11_profile.py
