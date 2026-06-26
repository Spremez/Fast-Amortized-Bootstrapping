#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT_DIR="${STAGE98_OUT_DIR:-repro/stage98_current_smoke_refresh}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
JOBS_VALUE="${JOBS:-$(nproc)}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$OUT_DIR"
RAW_CSV="$OUT_DIR/raw_smoke.csv"
printf 'step,backend,key,param,status,build_log,run_log,notes\n' > "$RAW_CSV"

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
    "$build_log" "$run_log" "$notes" >> "$RAW_CSV"
}

run_scalar_binary() {
  local case_dir="$OUT_DIR/scalar_binary_${PARAM_VALUE}"
  mkdir -p "$case_dir"
  local build_log="$case_dir/build.log"
  local run_log="$case_dir/run.log"

  make clean > /dev/null 2>&1 || true
  make -B FFT_LIB="$FFT_LIB_VALUE" A_PRNG=none ENABLE_VAES=false \
    KEY=BINARY PARAM="$PARAM_VALUE" -j"$JOBS_VALUE" \
    > "$build_log" 2>&1
  stdbuf -o0 ./main > "$run_log" 2>&1

  if ! grep -q '^Pass$' "$run_log"; then
    printf 'Stage98 scalar binary smoke failed: %s\n' "$run_log" >&2
    exit 1
  fi
  csv_row "scalar_binary_full_run" "$FFT_LIB_VALUE" "BINARY" "$PARAM_VALUE" \
    "PASS" "$build_log" "$run_log" "default scalar SAB path full run passed"
}

run_active_pvw_target() {
  local case_dir="$OUT_DIR/active_pvw_target_${PARAM_VALUE}"
  mkdir -p "$case_dir"
  local build_log="$case_dir/build.log"
  local run_log="$case_dir/run.log"

  make clean > /dev/null 2>&1 || true
  make -B FFT_LIB="$FFT_LIB_VALUE" A_PRNG=none ENABLE_VAES=false \
    KEY=BINARY PARAM="$PARAM_VALUE" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    SAB_PVW_ACTIVE_BUFFER_FUSION=true \
    SAB_PVW_TARGET_TEST=true -j"$JOBS_VALUE" \
    > "$build_log" 2>&1
  stdbuf -o0 ./main > "$run_log" 2>&1

  if ! grep -q 'SAB_PVW target full bootstrap gate: Pass' "$run_log"; then
    printf 'Stage98 active PVW target smoke failed: %s\n' "$run_log" >&2
    exit 1
  fi
  csv_row "active_pvw_target_full_gate" "$FFT_LIB_VALUE" "BINARY" "$PARAM_VALUE" \
    "PASS" "$build_log" "$run_log" \
    "explicit active-buffer sab_pvw target full bootstrap lane-equivalence gate passed"
}

run_backend_pvw_target() {
  local case_dir="$OUT_DIR/backend_pvw_target_${PARAM_VALUE}"
  mkdir -p "$case_dir"
  local build_log="$case_dir/build.log"
  local run_log="$case_dir/run.log"

  make clean > /dev/null 2>&1 || true
  make -B FFT_LIB="$FFT_LIB_VALUE" A_PRNG=none ENABLE_VAES=false \
    KEY=BINARY PARAM="$PARAM_VALUE" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    MAT_TRGSW_AVX512_RGT4_FUSED=true \
    SAB_PVW_ACTIVE_BUFFER_FUSION=true \
    SAB_PVW_BACKEND_FROM_DFT_ADD=true \
    SAB_PVW_TARGET_TEST=true -j"$JOBS_VALUE" \
    > "$build_log" 2>&1
  stdbuf -o0 ./main > "$run_log" 2>&1

  if ! grep -q 'SAB_PVW target full bootstrap gate: Pass' "$run_log"; then
    printf 'Stage98 backend PVW target smoke failed: %s\n' "$run_log" >&2
    exit 1
  fi
  csv_row "backend_pvw_target_full_gate" "$FFT_LIB_VALUE" "BINARY" "$PARAM_VALUE" \
    "PASS" "$build_log" "$run_log" \
    "explicit H14 backend sab_pvw target full bootstrap lane-equivalence gate passed"
}

run_scalar_ternary_build() {
  local case_dir="$OUT_DIR/scalar_ternary_${PARAM_VALUE}"
  mkdir -p "$case_dir"
  local build_log="$case_dir/build.log"

  make clean > /dev/null 2>&1 || true
  make -B FFT_LIB="$FFT_LIB_VALUE" A_PRNG=none ENABLE_VAES=false \
    KEY=TERNARY PARAM="$PARAM_VALUE" -j"$JOBS_VALUE" \
    > "$build_log" 2>&1
  csv_row "scalar_ternary_build" "$FFT_LIB_VALUE" "TERNARY" "$PARAM_VALUE" \
    "PASS" "$build_log" "" "scalar non-binary build remains independent of PVW binary guards"
}

{
  echo "Stage98 current-head smoke refresh"
  date -u
  git rev-parse --short HEAD
  run_scalar_binary
  run_active_pvw_target
  run_backend_pvw_target
  run_scalar_ternary_build
  make clean > /dev/null 2>&1 || true
  "$PYTHON_BIN" scripts/build_stage98_current_smoke_refresh.py --out-dir "$OUT_DIR"
} 2>&1 | tee "$OUT_DIR/stage98_run.log"
