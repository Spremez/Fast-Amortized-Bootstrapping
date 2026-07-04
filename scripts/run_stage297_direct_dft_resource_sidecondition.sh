#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE297_OUT_DIR:-$ROOT/repro/stage297_direct_dft_resource_sidecondition}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
TRIALS="${STAGE297_TRIALS:-1}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
R_VALUE="${STAGE297_R:-4}"

mkdir -p "$RAW"
cd "$ROOT"

selected_flags=(
  FFT_LIB="$FFT_LIB_VALUE"
  A_PRNG=none
  ENABLE_VAES=false
  KEY=BINARY
  PARAM="$PARAM_VALUE"
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  SAB_PVW_DUAL_SUB_CMUX=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

cat >"$RAW/variant_plan.csv" <<CSV
variant,param,fft_lib,r,trials,extra_flags
selected_control,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$TRIALS,
direct_dft,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$TRIALS,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
CSV

run_case() {
  local variant="$1"
  shift
  local dir="$RAW/$variant"
  mkdir -p "$dir"
  make clean >"$dir/clean.log" 2>&1
  make "${selected_flags[@]}" "$@" \
    SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true \
    SAB_PVW_NONBINARY_TARGET_NOISE_R="$R_VALUE" \
    SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS="$TRIALS" \
    SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true \
    SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false \
    -j"$JOBS" >"$dir/build.log" 2>&1
  /usr/bin/time -v ./main >"$dir/run.log" 2>"$dir/time.log"
}

run_case selected_control
run_case direct_dft MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true

python3 scripts/build_stage297_direct_dft_resource_sidecondition.py
