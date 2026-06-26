#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE64_OUT_DIR:-repro/stage64_post_variant_refresh}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
r_values="${STAGE64_R_VALUES:-2 4}"
bench_runs="${STAGE64_BENCH_RUNS:-3}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"
noise_seed_count="${STAGE64_NOISE_SEED_COUNT:-1}"
noise_start_seed="${STAGE64_NOISE_START_SEED:-6864025}"
noise_trials="${SAB_PVW_NOISE_TRIALS:-1}"
python_bin="${PYTHON:-python3}"

if [[ "$bench_runs" -lt 1 || "$bench_reps" -lt 1 ||
      "$noise_seed_count" -lt 1 || "$noise_trials" -lt 1 ]]; then
  printf 'invalid config bench_runs=%s bench_reps=%s noise_seed_count=%s noise_trials=%s\n' \
    "$bench_runs" "$bench_reps" "$noise_seed_count" "$noise_trials" >&2
  exit 1
fi

mkdir -p "$out_dir"

STAGE33_OUT_DIR="$out_dir/current_smoke" \
FFT_LIB="$fft_lib" \
PARAM="$param" \
JOBS="$jobs" \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
STAGE33_TERNARY_BUILD=1 \
  bash scripts/run_stage33_current_smoke.sh

for r in $r_values; do
  STAGE20_ACTIVE_BENCH_OUT_DIR="$out_dir/full_sab_r${r}" \
  FFT_LIB="$fft_lib" \
  KEY=BINARY \
  PARAM="$param" \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  STAGE20_ACTIVE_BENCH_RUNS="$bench_runs" \
  SAB_PVW_BENCH_R="$r" \
  SAB_PVW_BENCH_REPS="$bench_reps" \
  JOBS="$jobs" \
    bash scripts/run_stage20_active_buffer_bench.sh
done

STAGE25_FINAL_NOISE_OUT_DIR="$out_dir/final_noise" \
FFT_LIB="$fft_lib" \
KEY=BINARY \
PARAM="$param" \
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
SAB_PVW_ACTIVE_BUFFER_FUSION=true \
STAGE25_FINAL_NOISE_R_VALUES="$r_values" \
STAGE25_FINAL_NOISE_SEED_COUNT="$noise_seed_count" \
STAGE25_FINAL_NOISE_START_SEED="$noise_start_seed" \
SAB_PVW_NOISE_TRIALS="$noise_trials" \
JOBS="$jobs" \
  bash scripts/run_stage25_final_noise_sweep.sh

"$python_bin" scripts/build_stage50_performance_evidence_matrix.py
STAGE64_OUT_DIR="$out_dir" "$python_bin" scripts/build_stage64_post_variant_refresh_log.py
