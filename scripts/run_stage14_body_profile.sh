#!/usr/bin/env bash
set -euo pipefail

r="${SAB_PVW_BENCH_R:-2}"
reps="${SAB_PVW_BENCH_REPS:-1}"
runs="${STAGE14_BODY_RUNS:-1}"
fft_lib="${FFT_LIB:-spqlios}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE14_BODY_OUT_DIR:-repro/stage14_body_profile_r${r}_reps${reps}_runs${runs}}"

if [[ "$r" -lt 1 || "$reps" -lt 1 || "$runs" -lt 1 ]]; then
  printf 'invalid config r=%s reps=%s runs=%s\n' "$r" "$reps" "$runs" >&2
  exit 1
fi

mkdir -p "$out_dir"

make clean
make FFT_LIB="$fft_lib" SAB_PVW_BENCH=true SAB_PVW_BODY_PROFILE=true \
  SAB_PVW_BENCH_R="$r" SAB_PVW_BENCH_REPS="$reps" \
  KEY="$key" PARAM="$param" -j"$jobs"

profile_csv="$out_dir/body_profile.csv"
bench_csv="$out_dir/bench_summary.csv"
printf 'run,call_index,lanes,in_N,out_N,h,r_prec,full_us,setup_tv_xb_calls,setup_tv_xb_us,blind_rotate_calls,blind_rotate_us,sparse_mul_calls,sparse_mul_us,rgsw_monomial_calls,rgsw_monomial_us,cmux_calls,cmux_us,ncmux_calls,ncmux_us,mat_ep_calls,mat_ep_us,sub_a_calls,sub_a_us,copyback_calls,copyback_us\n' > "$profile_csv"
printf 'run,status,pvw_avg_us,pvw_stddev_us,pvw_lane_avg_us,scalar_repeated_avg_us,scalar_stddev_us,scalar_lane_avg_us,speedup_vs_scalar_repeated,speedup_stddev\n' > "$bench_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | tr ' ' '\n' |
    awk -F= -v name="$name" '$1 == name {print $2; exit}' | sed 's/x$//'
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

  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$run_idx" "$status" "$pvw_avg" "$pvw_stddev" "$pvw_lane_avg" \
    "$scalar_avg" "$scalar_stddev" "$scalar_lane_avg" "$speedup" \
    "$speedup_stddev" >> "$bench_csv"

  call_idx=0
  while IFS= read -r profile_line; do
    lanes="$(extract_field "$profile_line" 'lanes')"
    in_N="$(extract_field "$profile_line" 'in_N')"
    out_N="$(extract_field "$profile_line" 'out_N')"
    h="$(extract_field "$profile_line" 'h')"
    r_prec="$(extract_field "$profile_line" 'r_prec')"
    full="$(extract_field "$profile_line" 'full_us')"
    setup_calls="$(extract_field "$profile_line" 'setup_tv_xb_calls')"
    setup_us="$(extract_field "$profile_line" 'setup_tv_xb_us')"
    blind_calls="$(extract_field "$profile_line" 'blind_rotate_calls')"
    blind_us="$(extract_field "$profile_line" 'blind_rotate_us')"
    sparse_calls="$(extract_field "$profile_line" 'sparse_mul_calls')"
    sparse_us="$(extract_field "$profile_line" 'sparse_mul_us')"
    rgsw_calls="$(extract_field "$profile_line" 'rgsw_monomial_calls')"
    rgsw_us="$(extract_field "$profile_line" 'rgsw_monomial_us')"
    cmux_calls="$(extract_field "$profile_line" 'cmux_calls')"
    cmux_us="$(extract_field "$profile_line" 'cmux_us')"
    ncmux_calls="$(extract_field "$profile_line" 'ncmux_calls')"
    ncmux_us="$(extract_field "$profile_line" 'ncmux_us')"
    mat_ep_calls="$(extract_field "$profile_line" 'mat_ep_calls')"
    mat_ep_us="$(extract_field "$profile_line" 'mat_ep_us')"
    sub_a_calls="$(extract_field "$profile_line" 'sub_a_calls')"
    sub_a_us="$(extract_field "$profile_line" 'sub_a_us')"
    copyback_calls="$(extract_field "$profile_line" 'copyback_calls')"
    copyback_us="$(extract_field "$profile_line" 'copyback_us')"
    if [[ -z "$lanes" || -z "$in_N" || -z "$out_N" || -z "$h" ||
          -z "$r_prec" || -z "$full" || -z "$setup_calls" ||
          -z "$setup_us" || -z "$blind_calls" || -z "$blind_us" ||
          -z "$sparse_calls" || -z "$sparse_us" ||
          -z "$rgsw_calls" || -z "$rgsw_us" ||
          -z "$cmux_calls" || -z "$cmux_us" ||
          -z "$ncmux_calls" || -z "$ncmux_us" ||
          -z "$mat_ep_calls" || -z "$mat_ep_us" ||
          -z "$sub_a_calls" || -z "$sub_a_us" ||
          -z "$copyback_calls" || -z "$copyback_us" ]]; then
      printf 'failed to parse profile line in %s: %s\n' "$log_file" "$profile_line" >&2
      exit 1
    fi
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$run_idx" "$call_idx" "$lanes" "$in_N" "$out_N" "$h" "$r_prec" \
      "$full" "$setup_calls" "$setup_us" "$blind_calls" "$blind_us" \
      "$sparse_calls" "$sparse_us" "$rgsw_calls" "$rgsw_us" \
      "$cmux_calls" "$cmux_us" "$ncmux_calls" "$ncmux_us" \
      "$mat_ep_calls" "$mat_ep_us" "$sub_a_calls" "$sub_a_us" \
      "$copyback_calls" "$copyback_us" >> "$profile_csv"
    call_idx="$((call_idx + 1))"
  done < <(grep 'SAB_PVW_BODY_PROFILE sample' "$log_file")

  if [[ "$call_idx" -eq 0 ]]; then
    printf 'missing body profile lines in %s\n' "$log_file" >&2
    exit 1
  fi
done

printf 'Stage 14 body profile summary: %s\n' "$profile_csv"
printf 'Stage 14 benchmark summary: %s\n' "$bench_csv"
