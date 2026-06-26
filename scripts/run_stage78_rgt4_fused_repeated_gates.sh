#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE78_OUT_DIR:-repro/stage78_rgt4_fused_repeated_gates}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
jobs="${JOBS:-$(nproc)}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"
full_sab_r_values="${STAGE78_FULL_SAB_R_VALUES:-6 8}"
noise_r_values="${STAGE78_NOISE_R_VALUES:-6 8}"
resource_r_values="${STAGE78_RESOURCE_R_VALUES:-6 8}"
r6_runs="${STAGE78_FULL_SAB_R6_RUNS:-3}"
r8_runs="${STAGE78_FULL_SAB_R8_RUNS:-1}"
default_runs="${STAGE78_FULL_SAB_DEFAULT_RUNS:-1}"
noise_seed_count="${STAGE78_NOISE_SEED_COUNT:-3}"
noise_trials="${STAGE78_NOISE_TRIALS:-1}"
resource_modes="${STAGE78_RESOURCE_MODES:-pvw scalar}"

mkdir -p "$out_dir"

stage78_runs_for_r() {
  local r="$1"
  case "$r" in
    6) printf '%s\n' "$r6_runs" ;;
    8) printf '%s\n' "$r8_runs" ;;
    *) printf '%s\n' "$default_runs" ;;
  esac
}

for r in $full_sab_r_values; do
  runs="$(stage78_runs_for_r "$r")"
  STAGE20_ACTIVE_BENCH_RUNS="$runs" \
  STAGE20_ACTIVE_BENCH_OUT_DIR="$out_dir/full_sab_fused_r${r}_runs${runs}" \
  FFT_LIB="$fft_lib" \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_BENCH_R="$r" \
  SAB_PVW_BENCH_REPS="$bench_reps" \
  JOBS="$jobs" \
  bash scripts/run_stage20_active_buffer_bench.sh
done

if [[ -n "$noise_r_values" ]]; then
  STAGE25_FINAL_NOISE_OUT_DIR="$out_dir/final_noise" \
  STAGE25_FINAL_NOISE_R_VALUES="$noise_r_values" \
  STAGE25_FINAL_NOISE_SEED_COUNT="$noise_seed_count" \
  SAB_PVW_NOISE_TRIALS="$noise_trials" \
  FFT_LIB="$fft_lib" \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  JOBS="$jobs" \
  bash scripts/run_stage25_final_noise_sweep.sh
fi

if [[ -n "$resource_r_values" ]]; then
  STAGE25_RESOURCE_OUT_DIR="$out_dir/resource" \
  STAGE25_RESOURCE_R_VALUES="$resource_r_values" \
  STAGE25_RESOURCE_MODES="$resource_modes" \
  FFT_LIB="$fft_lib" \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  JOBS="$jobs" \
  bash scripts/run_stage25_resource_matrix.sh
fi

python3 scripts/build_stage78_rgt4_fused_repeated_gates.py
