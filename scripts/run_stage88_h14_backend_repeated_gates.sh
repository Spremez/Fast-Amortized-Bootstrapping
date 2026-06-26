#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE88_OUT_DIR:-repro/stage88_h14_backend_repeated_gates}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
jobs="${JOBS:-$(nproc)}"
r_value="${SAB_PVW_BENCH_R:-6}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"
full_sab_runs="${STAGE88_FULL_SAB_RUNS:-3}"
noise_seed_count="${STAGE88_NOISE_SEED_COUNT:-3}"
noise_start_seed="${STAGE88_NOISE_START_SEED:-6868025}"
noise_trials="${STAGE88_NOISE_TRIALS:-1}"
resource_runs="${STAGE88_RESOURCE_RUNS:-1}"
resource_modes="${STAGE88_RESOURCE_MODES:-pvw scalar}"

mkdir -p "$out_dir"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | sed -n "s/.*${name}=\\([^ ]*\\).*/\\1/p" | sed 's/x$//'
}

run_full_sab_variant() {
  local variant="$1"
  local opt_flag="$2"
  local variant_dir="$out_dir/full_sab_${variant}_r${r_value}_runs${full_sab_runs}"
  mkdir -p "$variant_dir"

  make clean
  make -B FFT_LIB="$fft_lib" A_PRNG=none ENABLE_VAES=false \
    PARAM=SET_2_3_2048 KEY=BINARY \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    MAT_TRGSW_AVX512_RGT4_FUSED=true \
    SAB_PVW_ACTIVE_BUFFER_FUSION=true \
    "$opt_flag"=true SAB_PVW_BENCH=true \
    SAB_PVW_BENCH_R="$r_value" SAB_PVW_BENCH_REPS="$bench_reps" \
    -j"$jobs" > "$variant_dir/build.log" 2>&1

  local summary_csv="$variant_dir/summary.csv"
  printf 'variant,run,status,pvw_avg_us,pvw_stddev_us,pvw_lane_avg_us,scalar_repeated_avg_us,scalar_stddev_us,scalar_lane_avg_us,speedup_vs_scalar_repeated,speedup_stddev,source_log\n' > "$summary_csv"

  for run_idx in $(seq 0 "$((full_sab_runs - 1))"); do
    local log_file="$variant_dir/run_${run_idx}.log"
    stdbuf -o0 ./main > "$log_file" 2>&1

    local correctness_line
    local summary_line
    correctness_line="$(grep 'SAB_PVW_BENCH correctness target_full' "$log_file" | tail -n 1)"
    summary_line="$(grep 'SAB_PVW_BENCH summary target_full' "$log_file" | tail -n 1)"
    if [[ -z "$correctness_line" || -z "$summary_line" ]]; then
      printf 'missing benchmark lines in %s\n' "$log_file" >&2
      exit 1
    fi

    local status
    status="$(printf '%s\n' "$correctness_line" | awk '{print $NF}')"
    if [[ "$status" != "Pass" ]]; then
      printf 'correctness gate failed in %s: %s\n' "$log_file" "$correctness_line" >&2
      exit 1
    fi

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$variant" "$run_idx" "$status" \
      "$(extract_field "$summary_line" pvw_avg_us)" \
      "$(extract_field "$summary_line" pvw_stddev_us)" \
      "$(extract_field "$summary_line" pvw_lane_avg_us)" \
      "$(extract_field "$summary_line" scalar_repeated_avg_us)" \
      "$(extract_field "$summary_line" scalar_stddev_us)" \
      "$(extract_field "$summary_line" scalar_lane_avg_us)" \
      "$(extract_field "$summary_line" speedup_vs_scalar_repeated)" \
      "$(extract_field "$summary_line" speedup_stddev)" \
      "$log_file" >> "$summary_csv"
  done
}

run_full_sab_variant wrapper SAB_PVW_FUSED_FROM_DFT_ADD
run_full_sab_variant backend SAB_PVW_BACKEND_FROM_DFT_ADD

if [[ "$noise_seed_count" -gt 0 ]]; then
  STAGE25_FINAL_NOISE_OUT_DIR="$out_dir/final_noise" \
  STAGE25_FINAL_NOISE_R_VALUES="$r_value" \
  STAGE25_FINAL_NOISE_SEED_COUNT="$noise_seed_count" \
  STAGE25_FINAL_NOISE_START_SEED="$noise_start_seed" \
  SAB_PVW_NOISE_TRIALS="$noise_trials" \
  FFT_LIB="$fft_lib" \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_RGT4_FUSED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true \
  SAB_PVW_BACKEND_FROM_DFT_ADD=true \
  JOBS="$jobs" \
  bash scripts/run_stage25_final_noise_sweep.sh
fi

if [[ "$resource_runs" -gt 0 ]]; then
  for idx in $(seq 0 "$((resource_runs - 1))"); do
    STAGE25_RESOURCE_OUT_DIR="$out_dir/resource_run_${idx}" \
    STAGE25_RESOURCE_R_VALUES="$r_value" \
    STAGE25_RESOURCE_MODES="$resource_modes" \
    FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    MAT_TRGSW_AVX512_RGT4_FUSED=true \
    SAB_PVW_ACTIVE_BUFFER_FUSION=true \
    SAB_PVW_BACKEND_FROM_DFT_ADD=true \
    JOBS="$jobs" \
    bash scripts/run_stage25_resource_matrix.sh
  done
fi

python3 scripts/build_stage88_h14_backend_repeated_gates.py
