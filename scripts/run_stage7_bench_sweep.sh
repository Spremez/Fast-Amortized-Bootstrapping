#!/usr/bin/env bash
set -euo pipefail

r="${SAB_PVW_BENCH_R:-2}"
reps="${SAB_PVW_BENCH_REPS:-2}"
runs="${STAGE7_BENCH_RUNS:-3}"
fft_lib="${FFT_LIB:-spqlios}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE7_BENCH_OUT_DIR:-repro/stage7_bench_sweep_r${r}_reps${reps}_runs${runs}}"

if [[ "$r" -lt 1 || "$reps" -lt 1 || "$runs" -lt 1 ]]; then
  printf 'invalid config r=%s reps=%s runs=%s\n' "$r" "$reps" "$runs" >&2
  exit 1
fi

mkdir -p "$out_dir"

make clean
make FFT_LIB="$fft_lib" SAB_PVW_BENCH=true \
  SAB_PVW_BENCH_R="$r" SAB_PVW_BENCH_REPS="$reps" \
  KEY="$key" PARAM="$param" -j"$jobs"

summary_csv="$out_dir/summary.csv"
printf 'run,status,pvw_avg_us,pvw_stddev_us,pvw_lane_avg_us,scalar_repeated_avg_us,scalar_stddev_us,scalar_lane_avg_us,speedup_vs_scalar_repeated,speedup_stddev\n' > "$summary_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | sed -n "s/.*${name}=\\([^ ]*\\).*/\\1/p" | sed 's/x$//'
}

for run_idx in $(seq 0 "$((runs - 1))"); do
  log_file="$out_dir/run_${run_idx}.log"
  stdbuf -o0 ./main | tee "$log_file"

  correctness_line="$(grep 'SAB_PVW_BENCH correctness target_full' "$log_file" | tail -n 1)"
  summary_line="$(grep 'SAB_PVW_BENCH summary target_full' "$log_file" | tail -n 1)"
  if [[ -z "$correctness_line" || -z "$summary_line" ]]; then
    printf 'missing benchmark lines in %s\n' "$log_file" >&2
    exit 1
  fi

  status="$(printf '%s\n' "$correctness_line" | awk '{print $NF}')"
  if [[ "$status" != "Pass" ]]; then
    printf 'correctness gate failed in %s: %s\n' "$log_file" "$correctness_line" >&2
    exit 1
  fi

  pvw_avg="$(extract_field "$summary_line" 'pvw_avg_us')"
  pvw_stddev="$(extract_field "$summary_line" 'pvw_stddev_us')"
  pvw_lane_avg="$(extract_field "$summary_line" 'pvw_lane_avg_us')"
  scalar_avg="$(extract_field "$summary_line" 'scalar_repeated_avg_us')"
  scalar_stddev="$(extract_field "$summary_line" 'scalar_stddev_us')"
  scalar_lane_avg="$(extract_field "$summary_line" 'scalar_lane_avg_us')"
  speedup="$(extract_field "$summary_line" 'speedup_vs_scalar_repeated')"
  speedup_stddev="$(extract_field "$summary_line" 'speedup_stddev')"
  if [[ -z "$pvw_avg" || -z "$pvw_stddev" || -z "$pvw_lane_avg" ||
        -z "$scalar_avg" || -z "$scalar_stddev" || -z "$scalar_lane_avg" ||
        -z "$speedup" || -z "$speedup_stddev" ]]; then
    printf 'failed to parse summary in %s: %s\n' "$log_file" "$summary_line" >&2
    exit 1
  fi

  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$run_idx" "$status" "$pvw_avg" "$pvw_stddev" "$pvw_lane_avg" \
    "$scalar_avg" "$scalar_stddev" "$scalar_lane_avg" "$speedup" \
    "$speedup_stddev" >> "$summary_csv"
done

printf 'Stage 7 benchmark sweep summary: %s\n' "$summary_csv"
