#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE18_CMUX_PROFILE_R_VALUES:-2 4}"
runs="${STAGE18_CMUX_PROFILE_RUNS:-1}"
reps="${SAB_PVW_BENCH_REPS:-1}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE18_CMUX_PROFILE_OUT_DIR:-repro/stage18_cmux_profile_${fft_lib}_runs${runs}}"

if [[ "$runs" -lt 1 || "$reps" -lt 1 ]]; then
  printf 'invalid config runs=%s reps=%s\n' "$runs" "$reps" >&2
  exit 1
fi

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
printf 'r,run,status,pvw_avg_us,scalar_repeated_avg_us,speedup,cmux_calls,mat_ep_calls,ncmux_calls,cmux_us,mat_ep_us,cmux_sub_us,cmux_from_dft_us,cmux_add_us,ncmux_auto_us,cmux_other_us,cmux_other_pct\n' > "$summary_csv"

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
  make FFT_LIB="$fft_lib" MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
    SAB_PVW_BENCH=true SAB_PVW_BODY_PROFILE=true \
    SAB_PVW_BENCH_R="$r" SAB_PVW_BENCH_REPS="$reps" \
    KEY="$key" PARAM="$param" -j"$jobs"

  for run_idx in $(seq 0 "$((runs - 1))"); do
    log_file="$r_out/run_${run_idx}.log"
    stdbuf -o0 ./main | tee "$log_file"

    correctness_line="$(grep 'SAB_PVW_BENCH correctness target_full' "$log_file" | tail -n 1)"
    bench_line="$(grep 'SAB_PVW_BENCH summary target_full' "$log_file" | tail -n 1)"
    profile_line="$(grep 'SAB_PVW_BODY_PROFILE sample' "$log_file" | tail -n 1)"
    if [[ -z "$correctness_line" || -z "$bench_line" || -z "$profile_line" ]]; then
      printf 'missing expected lines in %s\n' "$log_file" >&2
      exit 1
    fi

    status="$(printf '%s\n' "$correctness_line" | awk '{print $NF}')"
    if [[ "$status" != "Pass" ]]; then
      printf 'correctness gate failed in %s: %s\n' "$log_file" "$correctness_line" >&2
      exit 1
    fi

    cmux_calls="$(extract_field "$profile_line" cmux_calls)"
    mat_ep_calls="$(extract_field "$profile_line" mat_ep_calls)"
    ncmux_calls="$(extract_field "$profile_line" ncmux_calls)"
    cmux_sub_calls="$(extract_field "$profile_line" cmux_sub_calls)"
    cmux_from_dft_calls="$(extract_field "$profile_line" cmux_from_dft_calls)"
    cmux_add_calls="$(extract_field "$profile_line" cmux_add_calls)"
    ncmux_auto_calls="$(extract_field "$profile_line" ncmux_auto_calls)"
    if [[ "$cmux_calls" != "$mat_ep_calls" ||
          "$cmux_calls" != "$cmux_sub_calls" ||
          "$cmux_calls" != "$cmux_from_dft_calls" ||
          "$cmux_calls" != "$cmux_add_calls" ||
          "$ncmux_calls" != "$ncmux_auto_calls" ]]; then
      printf 'profile call count invariant failed in %s\n' "$log_file" >&2
      exit 1
    fi

    cmux_us="$(extract_field "$profile_line" cmux_us)"
    mat_ep_us="$(extract_field "$profile_line" mat_ep_us)"
    cmux_sub_us="$(extract_field "$profile_line" cmux_sub_us)"
    cmux_from_dft_us="$(extract_field "$profile_line" cmux_from_dft_us)"
    cmux_add_us="$(extract_field "$profile_line" cmux_add_us)"
    ncmux_auto_us="$(extract_field "$profile_line" ncmux_auto_us)"
    cmux_other_us="$(awk -v c="$cmux_us" -v m="$mat_ep_us" -v s="$cmux_sub_us" \
      -v f="$cmux_from_dft_us" -v a="$cmux_add_us" 'BEGIN { printf "%.3f", c - m - s - f - a }')"
    cmux_other_pct="$(awk -v o="$cmux_other_us" -v c="$cmux_us" \
      'BEGIN { if (c == 0) printf "0.000"; else printf "%.3f", 100.0 * o / c }')"

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$r" "$run_idx" "$status" \
      "$(extract_field "$bench_line" pvw_avg_us)" \
      "$(extract_field "$bench_line" scalar_repeated_avg_us)" \
      "$(extract_field "$bench_line" speedup_vs_scalar_repeated)" \
      "$cmux_calls" "$mat_ep_calls" "$ncmux_calls" \
      "$cmux_us" "$mat_ep_us" "$cmux_sub_us" "$cmux_from_dft_us" \
      "$cmux_add_us" "$ncmux_auto_us" "$cmux_other_us" "$cmux_other_pct" \
      >> "$summary_csv"
  done
done

printf 'Stage 18 CMUX profile summary: %s\n' "$summary_csv"
