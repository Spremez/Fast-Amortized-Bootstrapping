#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE25_STAGE_NOISE_R_VALUES:-1 2 4}"
trials="${SAB_PVW_NOISE_TRIALS:-1}"
seed="${MOSFHET_TEST_RNG_SEED:-6862025}"
max_log2_gap="${SAB_PVW_NOISE_MAX_LOG2_GAP:-4.0}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE25_STAGE_NOISE_OUT_DIR:-repro/stage25_stage_noise_${fft_lib}_trials${trials}}"

if [[ "$trials" -lt 1 ]]; then
  printf 'invalid config trials=%s\n' "$trials" >&2
  exit 1
fi

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
printf 'r,stage,trials,points,pair_failures,pair_log2_sigma_torus,pair_log2_max_abs_torus,source_log\n' > "$summary_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | tr ' ' '\n' |
    awk -F= -v name="$name" '$1 == name {print $2; exit}' | sed 's/x$//'
}

for r in $r_values; do
  r_out="$out_dir/r${r}"
  mkdir -p "$r_out"

  make clean
  make FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
    SAB_PVW_ACTIVE_BUFFER_FUSION="$active_buffer" \
    MOSFHET_DETERMINISTIC_RNG=true \
    SAB_PVW_STAGE_NOISE_TEST=true SAB_PVW_NOISE_R="$r" \
    SAB_PVW_NOISE_TRIALS="$trials" \
    SAB_PVW_NOISE_MAX_LOG2_GAP="$max_log2_gap" \
    KEY="$key" PARAM="$param" -j"$jobs"

  log_file="$r_out/seed_${seed}.log"
  MOSFHET_TEST_RNG_SEED="$seed" stdbuf -o0 ./main | tee "$log_file"

  gate_line="$(grep 'SAB_PVW_STAGE_NOISE target full bootstrap stage gate:' "$log_file" | tail -n 1)"
  if [[ -z "$gate_line" ]]; then
    printf 'missing stage-noise gate line in %s\n' "$log_file" >&2
    exit 1
  fi
  status="$(printf '%s\n' "$gate_line" | awk '{print $NF}')"
  if [[ "$status" != "Pass" ]]; then
    printf 'stage-noise gate failed in %s: %s\n' "$log_file" "$gate_line" >&2
    exit 1
  fi

  while IFS= read -r line; do
    printf '%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$r" \
      "$(extract_field "$line" stage)" \
      "$(extract_field "$line" trials)" \
      "$(extract_field "$line" points)" \
      "$(extract_field "$line" pair_failures)" \
      "$(extract_field "$line" pair_log2_sigma_torus)" \
      "$(extract_field "$line" pair_log2_max_abs_torus)" \
      "$log_file" >> "$summary_csv"
  done < <(grep 'SAB_PVW_STAGE_NOISE summary stage=' "$log_file")
done

printf 'Stage 25 stage-level noise summary: %s\n' "$summary_csv"
