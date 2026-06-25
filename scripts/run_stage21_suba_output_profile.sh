#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE21_SUBA_PROFILE_R_VALUES:-2 4}"
runs="${STAGE21_SUBA_PROFILE_RUNS:-1}"
reps="${SAB_PVW_BENCH_REPS:-1}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE21_SUBA_PROFILE_OUT_DIR:-repro/stage21_suba_output_profile_${fft_lib}_runs${runs}}"

if [[ "$runs" -lt 1 || "$reps" -lt 1 ]]; then
  printf 'invalid config runs=%s reps=%s\n' "$runs" "$reps" >&2
  exit 1
fi

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
printf 'r,run,status,pvw_avg_us,scalar_repeated_avg_us,speedup,in_N,h,r_prec,rgsw_monomial_calls,cmux_calls,expected_cmux,ncmux_calls,expected_ncmux,mat_ep_calls,sub_a_calls,expected_sub_a,sub_a_output_fusion_calls,expected_sub_a_output_fusion,copyback_calls,expected_copyback,stage20_copyback,sub_a_us,sub_a_output_fusion_us,source_log\n' > "$summary_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | tr ' ' '\n' |
    awk -F= -v name="$name" '$1 == name {print $2; exit}' | sed 's/x$//'
}

failures=0

for r in $r_values; do
  r_out="$out_dir/r${r}"
  mkdir -p "$r_out"

  make clean
  make FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
    SAB_PVW_ACTIVE_BUFFER_FUSION=true \
    SAB_PVW_SUBA_OUTPUT_FUSION=true \
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

    correctness_status="$(printf '%s\n' "$correctness_line" | awk '{print $NF}')"
    if [[ "$correctness_status" != "Pass" ]]; then
      printf 'correctness gate failed in %s: %s\n' "$log_file" "$correctness_line" >&2
      exit 1
    fi

    in_N="$(extract_field "$profile_line" in_N)"
    h="$(extract_field "$profile_line" h)"
    r_prec="$(extract_field "$profile_line" r_prec)"
    sparse_mul_calls="$(extract_field "$profile_line" sparse_mul_calls)"
    rgsw_calls="$(extract_field "$profile_line" rgsw_monomial_calls)"
    cmux_calls="$(extract_field "$profile_line" cmux_calls)"
    ncmux_calls="$(extract_field "$profile_line" ncmux_calls)"
    mat_ep_calls="$(extract_field "$profile_line" mat_ep_calls)"
    sub_a_calls="$(extract_field "$profile_line" sub_a_calls)"
    sub_a_us="$(extract_field "$profile_line" sub_a_us)"
    sub_a_output_fusion_calls="$(extract_field "$profile_line" sub_a_output_fusion_calls)"
    sub_a_output_fusion_us="$(extract_field "$profile_line" sub_a_output_fusion_us)"
    copyback_calls="$(extract_field "$profile_line" copyback_calls)"

    if [[ -z "$in_N" || -z "$h" || -z "$r_prec" ||
          -z "$sparse_mul_calls" || -z "$rgsw_calls" ||
          -z "$cmux_calls" || -z "$ncmux_calls" ||
          -z "$mat_ep_calls" || -z "$sub_a_calls" ||
          -z "$sub_a_us" || -z "$sub_a_output_fusion_calls" ||
          -z "$sub_a_output_fusion_us" || -z "$copyback_calls" ]]; then
      printf 'failed to parse Stage 21 profile line in %s: %s\n' \
        "$log_file" "$profile_line" >&2
      exit 1
    fi

    expected_rgsw="$((sparse_mul_calls * (h + 1)))"
    expected_cmux="$((expected_rgsw * r_prec * in_N))"
    expected_ncmux="$((expected_rgsw * ((1 << r_prec) - 1)))"
    expected_sub_a="$((sparse_mul_calls * h))"
    expected_sub_a_output_fusion="$expected_sub_a"
    stage20_copyback=0
    expected_copyback="$((((h + 1) * (r_prec % 2) + h) % 2))"

    status="PASS"
    if [[ "$rgsw_calls" -ne "$expected_rgsw" ||
          "$cmux_calls" -ne "$expected_cmux" ||
          "$ncmux_calls" -ne "$expected_ncmux" ||
          "$mat_ep_calls" -ne "$expected_cmux" ||
          "$sub_a_calls" -ne "$expected_sub_a" ||
          "$sub_a_output_fusion_calls" -ne "$expected_sub_a_output_fusion" ||
          "$copyback_calls" -ne "$expected_copyback" ]]; then
      status="COUNT_FAIL"
      failures="$((failures + 1))"
    fi

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$r" "$run_idx" "$status" \
      "$(extract_field "$bench_line" pvw_avg_us)" \
      "$(extract_field "$bench_line" scalar_repeated_avg_us)" \
      "$(extract_field "$bench_line" speedup_vs_scalar_repeated)" \
      "$in_N" "$h" "$r_prec" "$rgsw_calls" \
      "$cmux_calls" "$expected_cmux" \
      "$ncmux_calls" "$expected_ncmux" \
      "$mat_ep_calls" "$sub_a_calls" "$expected_sub_a" \
      "$sub_a_output_fusion_calls" "$expected_sub_a_output_fusion" \
      "$copyback_calls" "$expected_copyback" "$stage20_copyback" \
      "$sub_a_us" "$sub_a_output_fusion_us" "$log_file" >> "$summary_csv"
  done
done

printf 'Stage 21 sub_a output-fusion profile summary: %s\n' "$summary_csv"

if [[ "$failures" -ne 0 ]]; then
  printf 'Stage 21 sub_a output-fusion profile failed with %s count mismatch(es)\n' \
    "$failures" >&2
  exit 1
fi
