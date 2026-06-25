#!/usr/bin/env bash
set -euo pipefail

fft_lib="${FFT_LIB:-spqlios_avx512}"
param="${PARAM:-SET_2_3_2048}"
jobs="${JOBS:-$(nproc)}"
mat_specialized="${MAT_TRGSW_AVX512_SMALLR_SPECIALIZED:-true}"
active_buffer="${SAB_PVW_ACTIVE_BUFFER_FUSION:-true}"
run_ternary_build="${STAGE33_TERNARY_BUILD:-1}"
out_dir="${STAGE33_OUT_DIR:-repro/stage33_current_smoke}"

mkdir -p "$out_dir"
summary_csv="$out_dir/summary.csv"
printf 'step,backend,key,param,status,build_log,run_log,notes\n' > "$summary_csv"

csv_row() {
  local step="$1"
  local backend="$2"
  local key="$3"
  local param_name="$4"
  local status="$5"
  local build_log="$6"
  local run_log="$7"
  local notes="$8"
  notes="${notes//,/;}"
  printf '%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$step" "$backend" "$key" "$param_name" "$status" \
    "$build_log" "$run_log" "$notes" >> "$summary_csv"
}

run_scalar_binary() {
  local case_dir="$out_dir/scalar_binary_${param}"
  mkdir -p "$case_dir"
  local build_log="$case_dir/build.log"
  local run_log="$case_dir/run.log"

  make clean > /dev/null 2>&1 || true
  make FFT_LIB="$fft_lib" KEY=BINARY PARAM="$param" -j"$jobs" \
    > "$build_log" 2>&1
  stdbuf -o0 ./main > "$run_log" 2>&1

  if ! grep -q '^Pass$' "$run_log"; then
    printf 'scalar binary smoke did not end with Pass: %s\n' "$run_log" >&2
    exit 1
  fi
  csv_row "scalar_binary_full_run" "$fft_lib" "BINARY" "$param" "PASS" \
    "$build_log" "$run_log" "default scalar SAB path full run passed"
}

run_pvw_target() {
  local case_dir="$out_dir/pvw_target_${param}"
  mkdir -p "$case_dir"
  local build_log="$case_dir/build.log"
  local run_log="$case_dir/run.log"

  make clean > /dev/null 2>&1 || true
  make FFT_LIB="$fft_lib" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED="$mat_specialized" \
    SAB_PVW_ACTIVE_BUFFER_FUSION="$active_buffer" \
    SAB_PVW_TARGET_TEST=true KEY=BINARY PARAM="$param" -j"$jobs" \
    > "$build_log" 2>&1
  stdbuf -o0 ./main > "$run_log" 2>&1

  if ! grep -q 'SAB_PVW target full bootstrap gate: Pass' "$run_log"; then
    printf 'PVW target smoke did not pass: %s\n' "$run_log" >&2
    exit 1
  fi
  csv_row "pvw_target_full_gate" "$fft_lib" "BINARY" "$param" "PASS" \
    "$build_log" "$run_log" \
    "explicit sab_pvw target full bootstrap lane-equivalence gate passed"
}

run_scalar_ternary_build() {
  local case_dir="$out_dir/scalar_ternary_${param}"
  mkdir -p "$case_dir"
  local build_log="$case_dir/build.log"

  make clean > /dev/null 2>&1 || true
  make FFT_LIB="$fft_lib" KEY=TERNARY PARAM="$param" -j"$jobs" \
    > "$build_log" 2>&1
  csv_row "scalar_ternary_build" "$fft_lib" "TERNARY" "$param" "PASS" \
    "$build_log" "" "scalar non-binary build remains independent of PVW binary guard"
}

run_scalar_binary
run_pvw_target
if [[ "$run_ternary_build" == "1" ]]; then
  run_scalar_ternary_build
fi

make clean > /dev/null 2>&1 || true
printf 'Stage 33 current smoke summary: %s\n' "$summary_csv"
