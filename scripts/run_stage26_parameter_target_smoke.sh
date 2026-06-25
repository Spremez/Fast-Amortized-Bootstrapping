#!/usr/bin/env bash
set -euo pipefail

params="${STAGE26_PARAM_VALUES:-SET_2_3_2048 SET_4_5_2048 SET_2_3_4096}"
unsupported_keys="${STAGE26_UNSUPPORTED_KEYS:-TERNARY}"
unsupported_param="${STAGE26_UNSUPPORTED_PARAM:-SET_2_3_2048}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
jobs="${JOBS:-$(nproc)}"
out_dir="${STAGE26_OUT_DIR:-repro/stage26_parameter_branch_smoke_${fft_lib}}"

mkdir -p "$out_dir"

summary_csv="$out_dir/parameter_summary.csv"
branch_csv="$out_dir/branch_summary.csv"
printf 'backend,param,key,r,h,r_prec,status,build_log,run_log\n' > "$summary_csv"
printf 'backend,param,key,mode,status,build_log,notes\n' > "$branch_csv"

extract_field() {
  local line="$1"
  local name="$2"
  printf '%s\n' "$line" | tr ' ' '\n' |
    awk -F= -v name="$name" '$1 == name {print $2; exit}' | sed 's/://; s/x$//'
}

for param in $params; do
  case_dir="$out_dir/binary_${param}"
  mkdir -p "$case_dir"
  build_log="$case_dir/build.log"
  run_log="$case_dir/run.log"

  make clean > /dev/null 2>&1 || true
  make FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
    SAB_PVW_ACTIVE_BUFFER_FUSION="$active_buffer" \
    SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM="$param" -j"$jobs" \
    > "$build_log" 2>&1
  stdbuf -o0 ./main > "$run_log" 2>&1

  target_line="$(grep 'SAB_PVW target full bootstrap binary lane equivalence' "$run_log" | tail -n 1)"
  gate_line="$(grep 'SAB_PVW target full bootstrap gate:' "$run_log" | tail -n 1)"
  if [[ -z "$target_line" || -z "$gate_line" ]]; then
    printf 'missing target summary for %s\n' "$param" >&2
    exit 1
  fi
  status="$(printf '%s\n' "$gate_line" | awk '{print $NF}')"
  if [[ "$status" != "Pass" ]]; then
    printf 'target gate failed for %s: %s\n' "$param" "$gate_line" >&2
    exit 1
  fi

  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$fft_lib" "$param" "BINARY" \
    "$(extract_field "$target_line" r)" \
    "$(extract_field "$target_line" h)" \
    "$(extract_field "$target_line" r_prec)" \
    "$status" "$build_log" "$run_log" >> "$summary_csv"
done

for key in $unsupported_keys; do
  case_dir="$out_dir/unsupported_${key}_${unsupported_param}"
  mkdir -p "$case_dir"
  build_log="$case_dir/pvw_build.log"

  make clean > /dev/null 2>&1 || true
  if make FFT_LIB="$fft_lib" \
      MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
      SAB_PVW_TARGET_TEST=true KEY="$key" PARAM="$unsupported_param" \
      -j"$jobs" > "$build_log" 2>&1; then
    printf 'unexpected PVW build pass for unsupported key=%s param=%s\n' \
      "$key" "$unsupported_param" >&2
    exit 1
  fi
  if ! grep -q 'SAB_PVW target harness currently supports only KEY=BINARY' "$build_log"; then
    printf 'unsupported-key build failed for the wrong reason: %s\n' "$build_log" >&2
    exit 1
  fi
  printf '%s,%s,%s,%s,%s,%s,%s\n' \
    "$fft_lib" "$unsupported_param" "$key" "pvw_target" \
    "EXPECTED_UNSUPPORTED" "$build_log" \
    "PVW target harness is binary-only; scalar path is checked separately" \
    >> "$branch_csv"

  scalar_build_log="$case_dir/scalar_build.log"
  make clean > /dev/null 2>&1 || true
  make FFT_LIB="$fft_lib" KEY="$key" PARAM="$unsupported_param" -j"$jobs" \
    > "$scalar_build_log" 2>&1
  printf '%s,%s,%s,%s,%s,%s,%s\n' \
    "$fft_lib" "$unsupported_param" "$key" "scalar_build" \
    "PASS" "$scalar_build_log" \
    "Scalar non-binary build is unaffected by the PVW binary-only guard" \
    >> "$branch_csv"
done

make clean > /dev/null 2>&1 || true

printf 'Stage 26 parameter summary: %s\n' "$summary_csv"
printf 'Stage 26 branch summary: %s\n' "$branch_csv"
