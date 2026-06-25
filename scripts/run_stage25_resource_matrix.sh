#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE25_RESOURCE_R_VALUES:-1 2 4}"
modes="${STAGE25_RESOURCE_MODES:-pvw scalar}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE25_RESOURCE_OUT_DIR:-repro/stage25_resource_${fft_lib}}"

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
printf 'backend,r,mode,keygen_us,keygen_lane_avg_us,estimated_key_bytes,estimated_key_bytes_ratio_vs_scalar_repeated,internal_vmhwm_kb,time_max_rss_kb,source_log,time_log,notes\n' > "$summary_csv"

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
    SAB_PVW_RESOURCE_TEST=true SAB_PVW_RESOURCE_R="$r" \
    KEY="$key" PARAM="$param" -j"$jobs"

  for mode in $modes; do
    log_file="$r_out/${mode}.log"
    time_log="$r_out/${mode}.time.log"
    /usr/bin/time -v env SAB_PVW_RESOURCE_MODE="$mode" stdbuf -o0 ./main \
      > "$log_file" 2> "$time_log"

    gate_line="$(grep 'SAB_PVW_RESOURCE target_full gate:' "$log_file" | tail -n 1)"
    if [[ -z "$gate_line" || "$(printf '%s\n' "$gate_line" | awk '{print $NF}')" != "Pass" ]]; then
      printf 'resource gate failed in %s\n' "$log_file" >&2
      exit 1
    fi

    key_line="$(grep 'SAB_PVW_RESOURCE key_bytes target_full' "$log_file" | tail -n 1)"
    if [[ -z "$key_line" ]]; then
      printf 'missing key byte line in %s\n' "$log_file" >&2
      exit 1
    fi

    if [[ "$mode" == "pvw" ]]; then
      keygen_line="$(grep 'SAB_PVW_RESOURCE keygen target_full' "$log_file" | grep 'mode=pvw' | tail -n 1)"
      rss_line="$(grep 'SAB_PVW_RESOURCE rss target_full' "$log_file" | grep 'label=after_pvw_sab_keygen' | tail -n 1)"
      keygen_us="$(extract_field "$keygen_line" pvw_sab_keygen_us)"
      lane_avg="$(awk -v keygen="$keygen_us" -v r="$r" 'BEGIN { printf "%.3f", keygen / r }')"
      key_bytes="$(extract_field "$key_line" pvw_estimated_key_bytes)"
      ratio="$(extract_field "$key_line" pvw_vs_scalar_repeated_ratio)"
    else
      keygen_line="$(grep 'SAB_PVW_RESOURCE keygen target_full' "$log_file" | grep 'mode=scalar' | tail -n 1)"
      rss_line="$(grep 'SAB_PVW_RESOURCE rss target_full' "$log_file" | grep 'label=after_scalar_repeated_sab_keygen' | tail -n 1)"
      keygen_us="$(extract_field "$keygen_line" scalar_repeated_sab_keygen_us)"
      lane_avg="$(extract_field "$keygen_line" scalar_lane_avg_keygen_us)"
      key_bytes="$(extract_field "$key_line" scalar_repeated_estimated_key_bytes)"
      ratio="1.000000"
    fi

    internal_hwm="$(extract_field "$rss_line" vmhwm_kb)"
    time_max_rss="$(awk -F: '/Maximum resident set size/ {gsub(/^[ \t]+/, "", $2); print $2; exit}' "$time_log")"

    if [[ -z "$keygen_us" || -z "$lane_avg" || -z "$key_bytes" ||
          -z "$ratio" || -z "$internal_hwm" || -z "$time_max_rss" ]]; then
      printf 'failed to parse resource metrics in %s\n' "$log_file" >&2
      exit 1
    fi

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$fft_lib" "$r" "$mode" "$keygen_us" "$lane_avg" "$key_bytes" \
      "$ratio" "$internal_hwm" "$time_max_rss" "$log_file" "$time_log" \
      "public bootstrap key estimate excludes secret keys and tmp scratch" \
      >> "$summary_csv"
  done
done

printf 'Stage 25 resource matrix summary: %s\n' "$summary_csv"
