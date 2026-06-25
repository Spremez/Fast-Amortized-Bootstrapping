#!/usr/bin/env bash
set -euo pipefail

r_values="${STAGE19_SPARSE_PROFILE_R_VALUES:-2 4}"
runs="${STAGE19_SPARSE_PROFILE_RUNS:-1}"
reps="${SAB_PVW_BENCH_REPS:-1}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
fused_from_dft_add="${SAB_PVW_FUSED_FROM_DFT_ADD:-false}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE19_SPARSE_PROFILE_OUT_DIR:-repro/stage19_sparse_schedule_${fft_lib}_runs${runs}}"

if [[ "$runs" -lt 1 || "$reps" -lt 1 ]]; then
  printf 'invalid config runs=%s reps=%s\n' "$runs" "$reps" >&2
  exit 1
fi

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
bit_csv="$out_dir/bit_counts.csv"
printf 'r,run,status,pvw_avg_us,scalar_repeated_avg_us,speedup,in_N,h,r_prec,sparse_mul_calls,rgsw_monomial_calls,expected_rgsw,cmux_calls,expected_cmux,ncmux_calls,expected_ncmux,mat_ep_calls,sub_a_calls,expected_sub_a,copyback_calls,expected_copyback,bit_status,source_log\n' > "$summary_csv"
printf 'r,run,bit,status,ncmux_calls,expected_ncmux,direct_cmux_calls,expected_direct_cmux,total_update_calls,expected_total_update,ncmux_us,direct_cmux_us,source_log\n' > "$bit_csv"

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
    SAB_PVW_FUSED_FROM_DFT_ADD="$fused_from_dft_add" \
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
    copyback_calls="$(extract_field "$profile_line" copyback_calls)"

    if [[ -z "$in_N" || -z "$h" || -z "$r_prec" ||
          -z "$sparse_mul_calls" || -z "$rgsw_calls" ||
          -z "$cmux_calls" || -z "$ncmux_calls" ||
          -z "$mat_ep_calls" || -z "$sub_a_calls" ||
          -z "$copyback_calls" ]]; then
      printf 'failed to parse Stage 19 profile line in %s: %s\n' \
        "$log_file" "$profile_line" >&2
      exit 1
    fi

    expected_rgsw="$((sparse_mul_calls * (h + 1)))"
    expected_cmux="$((expected_rgsw * r_prec * in_N))"
    expected_ncmux="$((expected_rgsw * ((1 << r_prec) - 1)))"
    expected_sub_a="$((sparse_mul_calls * h))"
    if [[ "$((r_prec % 2))" -eq 1 ]]; then
      expected_copyback="$expected_rgsw"
    else
      expected_copyback=0
    fi

    status="PASS"
    if [[ "$rgsw_calls" -ne "$expected_rgsw" ||
          "$cmux_calls" -ne "$expected_cmux" ||
          "$ncmux_calls" -ne "$expected_ncmux" ||
          "$mat_ep_calls" -ne "$expected_cmux" ||
          "$sub_a_calls" -ne "$expected_sub_a" ||
          "$copyback_calls" -ne "$expected_copyback" ]]; then
      status="COUNT_FAIL"
      failures="$((failures + 1))"
    fi

    bit_status="PASS"
    for bit in $(seq 0 "$((r_prec - 1))"); do
      power="$((1 << bit))"
      bit_ncmux="$(extract_field "$profile_line" "bit${bit}_ncmux_calls")"
      bit_ncmux_us="$(extract_field "$profile_line" "bit${bit}_ncmux_us")"
      bit_direct="$(extract_field "$profile_line" "bit${bit}_direct_cmux_calls")"
      bit_direct_us="$(extract_field "$profile_line" "bit${bit}_direct_cmux_us")"
      bit_total="$(extract_field "$profile_line" "bit${bit}_total_update_calls")"
      if [[ -z "$bit_ncmux" || -z "$bit_ncmux_us" ||
            -z "$bit_direct" || -z "$bit_direct_us" ||
            -z "$bit_total" ]]; then
        printf 'missing bit=%s fields in %s\n' "$bit" "$log_file" >&2
        exit 1
      fi

      expected_bit_ncmux="$((expected_rgsw * power))"
      expected_bit_direct="$((expected_rgsw * (in_N - power)))"
      expected_bit_total="$((expected_rgsw * in_N))"
      this_bit_status="PASS"
      if [[ "$bit_ncmux" -ne "$expected_bit_ncmux" ||
            "$bit_direct" -ne "$expected_bit_direct" ||
            "$bit_total" -ne "$expected_bit_total" ]]; then
        this_bit_status="COUNT_FAIL"
        bit_status="COUNT_FAIL"
        failures="$((failures + 1))"
      fi

      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$r" "$run_idx" "$bit" "$this_bit_status" \
        "$bit_ncmux" "$expected_bit_ncmux" \
        "$bit_direct" "$expected_bit_direct" \
        "$bit_total" "$expected_bit_total" \
        "$bit_ncmux_us" "$bit_direct_us" "$log_file" >> "$bit_csv"
    done

    if [[ "$bit_status" != "PASS" && "$status" == "PASS" ]]; then
      status="COUNT_FAIL"
    fi

    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
      "$r" "$run_idx" "$status" \
      "$(extract_field "$bench_line" pvw_avg_us)" \
      "$(extract_field "$bench_line" scalar_repeated_avg_us)" \
      "$(extract_field "$bench_line" speedup_vs_scalar_repeated)" \
      "$in_N" "$h" "$r_prec" "$sparse_mul_calls" \
      "$rgsw_calls" "$expected_rgsw" \
      "$cmux_calls" "$expected_cmux" \
      "$ncmux_calls" "$expected_ncmux" \
      "$mat_ep_calls" "$sub_a_calls" "$expected_sub_a" \
      "$copyback_calls" "$expected_copyback" "$bit_status" "$log_file" \
      >> "$summary_csv"
  done
done

printf 'Stage 19 sparse schedule summary: %s\n' "$summary_csv"
printf 'Stage 19 per-bit schedule summary: %s\n' "$bit_csv"

if [[ "$failures" -ne 0 ]]; then
  printf 'Stage 19 sparse schedule audit failed with %s count mismatch(es)\n' \
    "$failures" >&2
  exit 1
fi
