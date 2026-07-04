#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE305_OUT_DIR:-$ROOT/repro/stage305_materialization_split_probe}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
REPS="${STAGE305_REPS:-1}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
R_VALUE="${STAGE305_R:-4}"

mkdir -p "$RAW"
cd "$ROOT"

common_flags=(
  FFT_LIB="$FFT_LIB_VALUE"
  A_PRNG=none
  ENABLE_VAES=false
  KEY=BINARY
  PARAM="$PARAM_VALUE"
  SAB_PVW_NONBINARY_BENCH=true
  SAB_PVW_NONBINARY_BENCH_R="$R_VALUE"
  SAB_PVW_NONBINARY_BENCH_REPS="$REPS"
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true
  SAB_PVW_NONBINARY_BENCH_TERNARY=false
  SAB_PVW_BODY_PROFILE=true
  MAT_TRGSW_SPLIT_PROFILE=true
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  SAB_PVW_DUAL_SUB_CMUX=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

cat >"$RAW/variant_plan.csv" <<CSV
variant,param,fft_lib,r,reps,extra_flags
selected_control,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$REPS,
direct_dft,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$REPS,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
CSV

run_variant() {
  local variant="$1"
  local direct_flag="$2"
  local dir="$RAW/$variant"
  mkdir -p "$dir"
  make clean >"$dir/clean.log" 2>&1
  make "${common_flags[@]}" \
    MAT_TRGSW_SUB_DECOMP_DFT_DIRECT="$direct_flag" \
    -j"$JOBS" >"$dir/build.log" 2>&1
  ./main >"$dir/run.log" 2>&1
}

run_variant selected_control false
run_variant direct_dft true

python3 scripts/build_stage305_materialization_split_probe.py
