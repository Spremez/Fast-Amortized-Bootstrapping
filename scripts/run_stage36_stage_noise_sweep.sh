#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE36_STAGE_NOISE_R_VALUES:-2 4}"
start_seed="${STAGE36_STAGE_NOISE_START_SEED:-6864025}"
seed_count="${STAGE36_STAGE_NOISE_SEEDS:-10}"
trials="${SAB_PVW_NOISE_TRIALS:-1}"
max_log2_gap="${SAB_PVW_NOISE_MAX_LOG2_GAP:-4.0}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE36_STAGE_NOISE_OUT_DIR:-repro/stage36_stage_noise_seeds${seed_count}}"

if [[ "$seed_count" -lt 1 || "$trials" -lt 1 ]]; then
  printf 'invalid config seed_count=%s trials=%s\n' "$seed_count" "$trials" >&2
  exit 1
fi

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
aggregate_csv="$out_dir/aggregate.csv"
printf 'r,seed,stage,trials,points,pair_failures,pair_log2_sigma_torus,pair_log2_max_abs_torus,source_log\n' > "$summary_csv"
printf 'r,stage,seeds,total_trials,total_points,pair_failures,min_pair_log2_sigma,max_pair_log2_sigma,avg_pair_log2_sigma,worst_pair_log2_max_abs,status,source_summary\n' > "$aggregate_csv"

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

  for idx in $(seq 0 "$((seed_count - 1))"); do
    seed="$((start_seed + idx))"
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
      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$r" \
        "$seed" \
        "$(extract_field "$line" stage)" \
        "$(extract_field "$line" trials)" \
        "$(extract_field "$line" points)" \
        "$(extract_field "$line" pair_failures)" \
        "$(extract_field "$line" pair_log2_sigma_torus)" \
        "$(extract_field "$line" pair_log2_max_abs_torus)" \
        "$log_file" >> "$summary_csv"
    done < <(grep 'SAB_PVW_STAGE_NOISE summary stage=' "$log_file")
  done
done

awk -F, -v source="$summary_csv" '
  NR > 1 {
    key = $1 SUBSEP $3;
    if (!(key in seen)) {
      seen[key] = 1;
      order[++n] = key;
      r[key] = $1;
      stage[key] = $3;
      min_sigma[key] = $7 + 0;
      max_sigma[key] = $7 + 0;
      worst_abs[key] = $8 + 0;
    }
    seed_key = key SUBSEP $2;
    if (!(seed_key in seed_seen)) {
      seed_seen[seed_key] = 1;
      seed_count[key]++;
    }
    total_trials[key] += $4;
    total_points[key] += $5;
    failures[key] += $6;
    sigma = $7 + 0;
    if (sigma < min_sigma[key]) min_sigma[key] = sigma;
    if (sigma > max_sigma[key]) max_sigma[key] = sigma;
    sum_sigma[key] += sigma;
    samples[key]++;
    max_abs = $8 + 0;
    if (max_abs > worst_abs[key]) worst_abs[key] = max_abs;
  }
  END {
    for (i = 1; i <= n; i++) {
      key = order[i];
      status = (failures[key] == 0) ? "PASS" : "FAIL";
      printf "%s,%s,%d,%d,%d,%d,%.3f,%.3f,%.6f,%.3f,%s,%s\n",
        r[key], stage[key], seed_count[key], total_trials[key], total_points[key],
        failures[key], min_sigma[key], max_sigma[key],
        sum_sigma[key] / samples[key], worst_abs[key], status, source;
    }
  }' "$summary_csv" >> "$aggregate_csv"

printf 'Stage 36 stage-noise summary: %s\n' "$summary_csv"
printf 'Stage 36 stage-noise aggregate: %s\n' "$aggregate_csv"
