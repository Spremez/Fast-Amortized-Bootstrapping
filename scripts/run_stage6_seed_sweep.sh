#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 0 ]]; then
  seeds=("$@")
else
  seeds=(6862025 6862026 6862027)
fi

fft_lib="${FFT_LIB:-spqlios}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
r="${SAB_PVW_NOISE_R:-2}"
trials="${SAB_PVW_NOISE_TRIALS:-1}"
max_log2_gap="${SAB_PVW_NOISE_MAX_LOG2_GAP:-4.0}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE6_SWEEP_OUT_DIR:-repro/stage6_seed_sweep_smoke}"

mkdir -p "$out_dir"

make clean
make FFT_LIB="$fft_lib" MOSFHET_DETERMINISTIC_RNG=true \
  SAB_PVW_NOISE_TEST=true SAB_PVW_NOISE_R="$r" \
  SAB_PVW_NOISE_TRIALS="$trials" \
  SAB_PVW_NOISE_MAX_LOG2_GAP="$max_log2_gap" \
  KEY="$key" PARAM="$param" -j"$jobs"

summary_csv="$out_dir/summary.csv"
printf 'seed,status,points,pvw_failures,scalar_failures,pair_failures,pvw_log2_sigma_torus,scalar_log2_sigma_torus,pair_log2_sigma_torus,pvw_minus_scalar_log2,max_allowed_log2_gap\n' > "$summary_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | sed -n "s/.*${name}=\\([^ ]*\\).*/\\1/p"
}

for seed in "${seeds[@]}"; do
  log_file="$out_dir/seed_${seed}.log"
  MOSFHET_TEST_RNG_SEED="$seed" stdbuf -o0 ./main | tee "$log_file"

  summary_line="$(grep 'SAB_PVW_NOISE summary target_full' "$log_file" | tail -n 1)"
  gate_line="$(grep 'SAB_PVW_NOISE target full bootstrap gate:' "$log_file" | tail -n 1)"
  status="$(printf '%s\n' "$gate_line" | awk '{print $NF}')"

  points="$(extract_field "$summary_line" 'points')"
  pvw_failures="$(extract_field "$summary_line" 'pvw_failures')"
  scalar_failures="$(extract_field "$summary_line" 'scalar_failures')"
  pair_failures="$(extract_field "$summary_line" 'pair_failures')"
  pvw_log2_sigma="$(extract_field "$summary_line" 'pvw_log2_sigma_torus')"
  scalar_log2_sigma="$(extract_field "$summary_line" 'scalar_log2_sigma_torus')"
  pair_log2_sigma="$(extract_field "$summary_line" 'pair_log2_sigma_torus')"
  pvw_minus_scalar="$(extract_field "$summary_line" 'pvw_minus_scalar_log2')"
  allowed_gap="$(extract_field "$summary_line" 'max_allowed_log2_gap')"

  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$seed" "$status" "$points" "$pvw_failures" "$scalar_failures" \
    "$pair_failures" "$pvw_log2_sigma" "$scalar_log2_sigma" \
    "$pair_log2_sigma" "$pvw_minus_scalar" "$allowed_gap" >> "$summary_csv"
done

printf 'Stage 6 seed sweep summary: %s\n' "$summary_csv"
