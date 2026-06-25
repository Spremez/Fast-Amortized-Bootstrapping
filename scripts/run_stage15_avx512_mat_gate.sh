#!/usr/bin/env bash
set -euo pipefail

runs="${STAGE15_AVX512_MAT_RUNS:-3}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE15_AVX512_MAT_OUT_DIR:-repro/stage15_avx512_mat_gate_runs${runs}}"

if [[ "$runs" -lt 1 ]]; then
  printf 'invalid runs=%s\n' "$runs" >&2
  exit 1
fi

mkdir -p "$out_dir"

make clean
make FFT_LIB="$fft_lib" MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_KERNEL_TEST=true KEY="$key" PARAM="$param" -j"$jobs"

mat_csv="$out_dir/mat_vs_scalar.csv"
full_csv="$out_dir/mat_full_vs_scalar.csv"
phase_csv="$out_dir/ep_breakdown.csv"

printf 'run,r,reps,scalar_repeated_avg_us,scalar_lane_avg_us,mat_avg_us,mat_lane_avg_us,speedup_vs_scalar_repeated\n' > "$mat_csv"
printf 'run,r,reps,scalar_repeated_avg_us,scalar_lane_avg_us,mat_avg_us,mat_lane_avg_us,speedup_vs_scalar_repeated\n' > "$full_csv"
printf 'run,label,r,reps,phase_sum_avg_us,decompose_avg_us,decompose_pct,dft_avg_us,dft_pct,mul_avg_us,mul_pct\n' > "$phase_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | tr ' ' '\n' |
    awk -F= -v name="$name" '$1 == name {print $2; exit}' | sed 's/x$//'
}

for run_idx in $(seq 0 "$((runs - 1))"); do
  log_file="$out_dir/run_${run_idx}.log"
  stdbuf -o0 ./main | tee "$log_file"

  if ! grep -q 'MAT_TRGSW/PVW staged kernel test: Pass' "$log_file"; then
    printf 'staged MAT/PVW gate failed in %s\n' "$log_file" >&2
    exit 1
  fi

  while IFS= read -r line; do
    r="$(printf '%s\n' "$line" | awk '{print $4}' | sed 's/r=//')"
    reps="$(printf '%s\n' "$line" | awk '{print $5}' | sed 's/reps=//')"
    printf '%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$run_idx" "$r" "$reps" \
      "$(extract_field "$line" scalar_repeated_avg_us)" \
      "$(extract_field "$line" scalar_lane_avg_us)" \
      "$(extract_field "$line" mat_avg_us)" \
      "$(extract_field "$line" mat_lane_avg_us)" \
      "$(extract_field "$line" speedup_vs_scalar_repeated)" >> "$mat_csv"
  done < <(grep '^MAT_TRGSW vs scalar r=' "$log_file")

  while IFS= read -r line; do
    r="$(printf '%s\n' "$line" | awk '{print $4}' | sed 's/r=//')"
    reps="$(printf '%s\n' "$line" | awk '{print $5}' | sed 's/reps=//')"
    printf '%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$run_idx" "$r" "$reps" \
      "$(extract_field "$line" scalar_repeated_avg_us)" \
      "$(extract_field "$line" scalar_lane_avg_us)" \
      "$(extract_field "$line" mat_avg_us)" \
      "$(extract_field "$line" mat_lane_avg_us)" \
      "$(extract_field "$line" speedup_vs_scalar_repeated)" >> "$full_csv"
  done < <(grep '^MAT_TRGSW_FULL vs scalar_full r=' "$log_file")

  while IFS= read -r line; do
    label="$(printf '%s\n' "$line" | awk '{print $2}')"
    r="$(extract_field "$line" r)"
    reps="$(extract_field "$line" reps)"
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$run_idx" "$label" "$r" "$reps" \
      "$(extract_field "$line" phase_sum_avg_us)" \
      "$(extract_field "$line" decompose_avg_us)" \
      "$(extract_field "$line" decompose_pct)" \
      "$(extract_field "$line" dft_avg_us)" \
      "$(extract_field "$line" dft_pct)" \
      "$(extract_field "$line" mul_avg_us)" \
      "$(extract_field "$line" mul_pct)" >> "$phase_csv"
  done < <(grep '^EP_BREAKDOWN ' "$log_file")
done

printf 'Stage 15 AVX512 MAT gate: %s\n' "$out_dir"
printf 'MAT vs scalar CSV: %s\n' "$mat_csv"
printf 'MAT full-output CSV: %s\n' "$full_csv"
printf 'EP breakdown CSV: %s\n' "$phase_csv"
