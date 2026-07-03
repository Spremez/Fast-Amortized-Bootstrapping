#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE208_PROFILE_OUT_DIR:-repro/stage208_current_head_profile_refresh}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"

mkdir -p "$out_dir"

export FFT_LIB="$fft_lib"
export MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized"
export SAB_PVW_ACTIVE_BUFFER_FUSION="$active_buffer"
export KEY="$key"
export PARAM="$param"
export JOBS="$jobs"

STAGE20_ACTIVE_PROFILE_R_VALUES="${STAGE20_ACTIVE_PROFILE_R_VALUES:-2 4}" \
STAGE20_ACTIVE_PROFILE_RUNS="${STAGE20_ACTIVE_PROFILE_RUNS:-1}" \
STAGE20_ACTIVE_PROFILE_OUT_DIR="$out_dir/active_buffer" \
bash scripts/run_stage20_active_buffer_profile.sh

STAGE18_CMUX_PROFILE_R_VALUES="${STAGE18_CMUX_PROFILE_R_VALUES:-2 4}" \
STAGE18_CMUX_PROFILE_RUNS="${STAGE18_CMUX_PROFILE_RUNS:-1}" \
STAGE18_CMUX_PROFILE_OUT_DIR="$out_dir/cmux" \
bash scripts/run_stage18_cmux_profile.sh

for r in ${STAGE208_POSTPROC_R_VALUES:-2 4}; do
  SAB_PVW_BENCH_R="$r" \
  STAGE13_POSTPROC_RUNS="${STAGE13_POSTPROC_RUNS:-1}" \
  STAGE13_POSTPROC_OUT_DIR="$out_dir/postproc_r${r}" \
  bash scripts/run_stage13_postproc_profile.sh
done

printf 'Stage208 current-head profile refresh: %s\n' "$out_dir"
