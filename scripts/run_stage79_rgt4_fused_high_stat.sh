#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE79_OUT_DIR:-repro/stage79_rgt4_fused_high_stat}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
jobs="${JOBS:-$(nproc)}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"
full_sab_r="${STAGE79_FULL_SAB_R:-6}"
full_sab_runs="${STAGE79_FULL_SAB_RUNS:-10}"
noise_r_values="${STAGE79_NOISE_R_VALUES:-6}"
noise_seed_count="${STAGE79_NOISE_SEED_COUNT:-20}"
noise_start_seed="${STAGE79_NOISE_START_SEED:-6866025}"
noise_trials="${STAGE79_NOISE_TRIALS:-1}"
resource_r_values="${STAGE79_RESOURCE_R_VALUES:-6}"
resource_modes="${STAGE79_RESOURCE_MODES:-pvw scalar}"
resource_runs="${STAGE79_RESOURCE_RUNS:-3}"

mkdir -p "$out_dir"

STAGE20_ACTIVE_BENCH_RUNS="$full_sab_runs" \
STAGE20_ACTIVE_BENCH_OUT_DIR="$out_dir/full_sab_fused_r${full_sab_r}_runs${full_sab_runs}" \
FFT_LIB="$fft_lib" \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
MAT_TRGSW_AVX512_RGT4_FUSED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
SAB_PVW_BENCH_R="$full_sab_r" \
SAB_PVW_BENCH_REPS="$bench_reps" \
JOBS="$jobs" \
bash scripts/run_stage20_active_buffer_bench.sh

if [[ -n "$noise_r_values" ]]; then
  STAGE25_FINAL_NOISE_OUT_DIR="$out_dir/final_noise" \
  STAGE25_FINAL_NOISE_R_VALUES="$noise_r_values" \
  STAGE25_FINAL_NOISE_SEED_COUNT="$noise_seed_count" \
  STAGE25_FINAL_NOISE_START_SEED="$noise_start_seed" \
  SAB_PVW_NOISE_TRIALS="$noise_trials" \
  FFT_LIB="$fft_lib" \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  JOBS="$jobs" \
  bash scripts/run_stage25_final_noise_sweep.sh
fi

if [[ -n "$resource_r_values" && "$resource_runs" -gt 0 ]]; then
  for idx in $(seq 0 "$((resource_runs - 1))"); do
    STAGE25_RESOURCE_OUT_DIR="$out_dir/resource_run_${idx}" \
    STAGE25_RESOURCE_R_VALUES="$resource_r_values" \
    STAGE25_RESOURCE_MODES="$resource_modes" \
    FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    MAT_TRGSW_AVX512_RGT4_FUSED=true \
    SAB_PVW_ACTIVE_BUFFER_FUSION=true \
    JOBS="$jobs" \
    bash scripts/run_stage25_resource_matrix.sh
  done
fi

python3 scripts/build_stage79_rgt4_fused_high_stat.py
