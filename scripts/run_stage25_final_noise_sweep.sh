#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE25_FINAL_NOISE_R_VALUES:-1 2 4}"
start_seed="${STAGE25_FINAL_NOISE_START_SEED:-6862025}"
seed_count="${STAGE25_FINAL_NOISE_SEED_COUNT:-3}"
trials="${SAB_PVW_NOISE_TRIALS:-1}"
max_log2_gap="${SAB_PVW_NOISE_MAX_LOG2_GAP:-4.0}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE25_FINAL_NOISE_OUT_DIR:-repro/stage25_final_noise_${fft_lib}_seeds${seed_count}}"

if [[ "$seed_count" -lt 1 || "$trials" -lt 1 ]]; then
  printf 'invalid config seed_count=%s trials=%s\n' "$seed_count" "$trials" >&2
  exit 1
fi

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
aggregate_csv="$out_dir/aggregate.csv"
printf 'r,seed,status,points,pvw_failures,scalar_failures,pair_failures,pvw_log2_sigma_torus,scalar_log2_sigma_torus,pair_log2_sigma_torus,pvw_minus_scalar_log2,max_allowed_log2_gap,source_log\n' > "$summary_csv"
printf 'r,seeds,points,pvw_failures,scalar_failures,pair_failures,min_pvw_minus_scalar_log2,max_pvw_minus_scalar_log2,avg_pvw_minus_scalar_log2,status\n' > "$aggregate_csv"

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
    SAB_PVW_NOISE_TEST=true SAB_PVW_NOISE_R="$r" \
    SAB_PVW_NOISE_TRIALS="$trials" \
    SAB_PVW_NOISE_MAX_LOG2_GAP="$max_log2_gap" \
    KEY="$key" PARAM="$param" -j"$jobs"

  for idx in $(seq 0 "$((seed_count - 1))"); do
    seed="$((start_seed + idx))"
    log_file="$r_out/seed_${seed}.log"
    MOSFHET_TEST_RNG_SEED="$seed" stdbuf -o0 ./main | tee "$log_file"

    gate_line="$(grep 'SAB_PVW_NOISE target full bootstrap gate:' "$log_file" | tail -n 1)"
    summary_line="$(grep 'SAB_PVW_NOISE summary target_full' "$log_file" | tail -n 1)"
    if [[ -z "$gate_line" || -z "$summary_line" ]]; then
      printf 'missing noise summary lines in %s\n' "$log_file" >&2
      exit 1
    fi

    status="$(printf '%s\n' "$gate_line" | awk '{print $NF}')"
    if [[ "$status" != "Pass" ]]; then
      printf 'noise gate failed in %s: %s\n' "$log_file" "$gate_line" >&2
      exit 1
    fi

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$r" "$seed" "$status" \
      "$(extract_field "$summary_line" points)" \
      "$(extract_field "$summary_line" pvw_failures)" \
      "$(extract_field "$summary_line" scalar_failures)" \
      "$(extract_field "$summary_line" pair_failures)" \
      "$(extract_field "$summary_line" pvw_log2_sigma_torus)" \
      "$(extract_field "$summary_line" scalar_log2_sigma_torus)" \
      "$(extract_field "$summary_line" pair_log2_sigma_torus)" \
      "$(extract_field "$summary_line" pvw_minus_scalar_log2)" \
      "$(extract_field "$summary_line" max_allowed_log2_gap)" \
      "$log_file" >> "$summary_csv"
  done

  awk -F, -v r="$r" '
    NR > 1 && $1 == r {
      seeds++;
      points += $4;
      pvw_fail += $5;
      scalar_fail += $6;
      pair_fail += $7;
      gap = $11 + 0;
      if (seeds == 1 || gap < min_gap) min_gap = gap;
      if (seeds == 1 || gap > max_gap) max_gap = gap;
      sum_gap += gap;
    }
    END {
      status = (pvw_fail == 0 && scalar_fail == 0 && pair_fail == 0) ? "PASS" : "FAIL";
      printf "%s,%d,%d,%d,%d,%d,%.3f,%.3f,%.6f,%s\n",
        r, seeds, points, pvw_fail, scalar_fail, pair_fail,
        min_gap, max_gap, sum_gap / seeds, status;
    }' "$summary_csv" >> "$aggregate_csv"
done

printf 'Stage 25 final-output noise summary: %s\n' "$summary_csv"
printf 'Stage 25 final-output noise aggregate: %s\n' "$aggregate_csv"
