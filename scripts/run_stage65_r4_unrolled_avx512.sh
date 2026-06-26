#!/usr/bin/env bash
set -euo pipefail

variants="${STAGE65_VARIANTS:-specialized r4_unrolled}"
kernel_runs="${STAGE65_KERNEL_RUNS:-1}"
full_runs="${STAGE65_FULL_SAB_RUNS:-1}"
full_reps="${SAB_PVW_BENCH_REPS:-1}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
kernel_key="${STAGE65_KERNEL_KEY:-BINARY}"
kernel_param="${STAGE65_KERNEL_PARAM:-SET_2_3}"
full_key="${KEY:-BINARY}"
full_param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE65_OUT_DIR:-repro/stage65_r4_unrolled_avx512}"

if [[ "$kernel_runs" -lt 1 || "$full_runs" -lt 0 || "$full_reps" -lt 1 ]]; then
  printf 'invalid config kernel_runs=%s full_runs=%s full_reps=%s\n' \
    "$kernel_runs" "$full_runs" "$full_reps" >&2
  exit 1
fi

mkdir -p "$out_dir"

kernel_csv="$out_dir/kernel_microbench.csv"
full_csv="$out_dir/full_sab_smoke.csv"
instr_csv="$out_dir/instruction_counts.csv"

printf 'variant,run,kind,r,reps,scalar_repeated_avg_us,scalar_lane_avg_us,mat_avg_us,mat_lane_avg_us,speedup_vs_scalar_repeated,source_log\n' > "$kernel_csv"
printf 'variant,r,run,status,pvw_avg_us,pvw_lane_avg_us,scalar_repeated_avg_us,scalar_lane_avg_us,speedup_vs_scalar_repeated,source_log\n' > "$full_csv"
printf 'variant,object_scope,vfmadd,vfnmadd,vfmsub,zmm_refs,ymm_refs,vmovapd,vmovupd,source_log\n' > "$instr_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | tr ' ' '\n' |
    awk -F= -v name="$name" '$1 == name {print $2; exit}' | sed 's/x$//'
}

instruction_count() {
  local pattern="$1"
  local file="$2"
  grep -E -c "$pattern" "$file" || true
}

variant_flags() {
  case "$1" in
    specialized)
      printf 'true false\n'
      ;;
    r4_unrolled)
      printf 'true true\n'
      ;;
    *)
      printf 'unknown Stage65 variant: %s\n' "$1" >&2
      exit 1
      ;;
  esac
}

for variant in $variants; do
  read -r mat_flag r4_unrolled_flag < <(variant_flags "$variant")
  variant_out="$out_dir/$variant"
  mkdir -p "$variant_out"

  make clean
  make FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_flag" \
    MAT_TRGSW_AVX512_R4_UNROLLED_ROWS="$r4_unrolled_flag" \
    SAB_PVW_KERNEL_TEST=true KEY="$kernel_key" PARAM="$kernel_param" -j"$jobs"

  objdump_tmp="$variant_out/objdump_mattrgsw_polynomial.full.tmp"
  objdump_log="$variant_out/objdump_mattrgsw_polynomial.txt"
  objdump -d build/mattrgsw.o build/polynomial.o > "$objdump_tmp"
  {
    printf 'objdump snippets for build/mattrgsw.o and build/polynomial.o\n'
    printf 'Filtered to function labels plus AVX/FMA/vector-move instructions.\n'
    grep -E '<mat_trgsw_mul_pvmtmlwe_DFT|<polynomial_mul|vfmadd|vfnmadd|vfmsub|zmm|vmovapd|vmovupd' \
      "$objdump_tmp" | head -n 260 || true
  } > "$objdump_log"
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$variant" "mattrgsw+polynomial" \
    "$(instruction_count 'vfmadd' "$objdump_tmp")" \
    "$(instruction_count 'vfnmadd' "$objdump_tmp")" \
    "$(instruction_count 'vfmsub' "$objdump_tmp")" \
    "$(instruction_count 'zmm' "$objdump_tmp")" \
    "$(instruction_count 'ymm' "$objdump_tmp")" \
    "$(instruction_count 'vmovapd' "$objdump_tmp")" \
    "$(instruction_count 'vmovupd' "$objdump_tmp")" \
    "$objdump_log" >> "$instr_csv"
  rm -f "$objdump_tmp"

  for run_idx in $(seq 0 "$((kernel_runs - 1))"); do
    log_file="$variant_out/kernel_run_${run_idx}.log"
    stdbuf -o0 ./main | tee "$log_file"

    if ! grep -q 'MAT_TRGSW/PVW staged kernel test: Pass' "$log_file"; then
      printf 'staged MAT/PVW gate failed in %s\n' "$log_file" >&2
      exit 1
    fi

    while IFS= read -r line; do
      r="$(printf '%s\n' "$line" | awk '{print $4}' | sed 's/r=//')"
      reps="$(printf '%s\n' "$line" | awk '{print $5}' | sed 's/reps=//')"
      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$variant" "$run_idx" "dft_output" "$r" "$reps" \
        "$(extract_field "$line" scalar_repeated_avg_us)" \
        "$(extract_field "$line" scalar_lane_avg_us)" \
        "$(extract_field "$line" mat_avg_us)" \
        "$(extract_field "$line" mat_lane_avg_us)" \
        "$(extract_field "$line" speedup_vs_scalar_repeated)" \
        "$log_file" >> "$kernel_csv"
    done < <(grep '^MAT_TRGSW vs scalar r=' "$log_file")

    while IFS= read -r line; do
      r="$(printf '%s\n' "$line" | awk '{print $4}' | sed 's/r=//')"
      reps="$(printf '%s\n' "$line" | awk '{print $5}' | sed 's/reps=//')"
      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$variant" "$run_idx" "full_output" "$r" "$reps" \
        "$(extract_field "$line" scalar_repeated_avg_us)" \
        "$(extract_field "$line" scalar_lane_avg_us)" \
        "$(extract_field "$line" mat_avg_us)" \
        "$(extract_field "$line" mat_lane_avg_us)" \
        "$(extract_field "$line" speedup_vs_scalar_repeated)" \
        "$log_file" >> "$kernel_csv"
    done < <(grep '^MAT_TRGSW_FULL vs scalar_full r=' "$log_file")
  done

  if [[ "$full_runs" -gt 0 ]]; then
    full_variant_out="$variant_out/full_r4"
    mkdir -p "$full_variant_out"
    make clean
    make FFT_LIB="$fft_lib" \
      MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_flag" \
      MAT_TRGSW_AVX512_R4_UNROLLED_ROWS="$r4_unrolled_flag" \
      SAB_PVW_ACTIVE_BUFFER_FUSION=true \
      SAB_PVW_BENCH=true SAB_PVW_BENCH_R=4 \
      SAB_PVW_BENCH_REPS="$full_reps" \
      KEY="$full_key" PARAM="$full_param" -j"$jobs"

    for run_idx in $(seq 0 "$((full_runs - 1))"); do
      log_file="$full_variant_out/run_${run_idx}.log"
      stdbuf -o0 ./main | tee "$log_file"

      correctness_line="$(grep 'SAB_PVW_BENCH correctness target_full' "$log_file" | tail -n 1)"
      summary_line="$(grep 'SAB_PVW_BENCH summary target_full' "$log_file" | tail -n 1)"
      if [[ -z "$correctness_line" || -z "$summary_line" ]]; then
        printf 'missing full SAB benchmark lines in %s\n' "$log_file" >&2
        exit 1
      fi

      status="$(printf '%s\n' "$correctness_line" | awk '{print $NF}')"
      if [[ "$status" != "Pass" ]]; then
        printf 'full SAB correctness failed in %s: %s\n' \
          "$log_file" "$correctness_line" >&2
        exit 1
      fi

      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$variant" "4" "$run_idx" "$status" \
        "$(extract_field "$summary_line" pvw_avg_us)" \
        "$(extract_field "$summary_line" pvw_lane_avg_us)" \
        "$(extract_field "$summary_line" scalar_repeated_avg_us)" \
        "$(extract_field "$summary_line" scalar_lane_avg_us)" \
        "$(extract_field "$summary_line" speedup_vs_scalar_repeated)" \
        "$log_file" >> "$full_csv"
    done
  fi
done

printf 'Stage 65 r4 unrolled AVX512 variant: %s\n' "$out_dir"
printf 'kernel microbench CSV: %s\n' "$kernel_csv"
printf 'full SAB smoke CSV: %s\n' "$full_csv"
printf 'instruction count CSV: %s\n' "$instr_csv"
