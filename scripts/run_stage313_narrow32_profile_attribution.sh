#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE313_OUT_DIR:-$ROOT/repro/stage313_narrow32_profile_attribution}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
REPS="${STAGE313_REPS:-1}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
R_VALUE="${STAGE313_R:-4}"

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
  MAT_TRGSW_DIRECT_DFT_PROFILE=true
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  SAB_PVW_DUAL_SUB_CMUX=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

cat >"$RAW/variant_plan.csv" <<CSV
variant,param,fft_lib,r,reps,extra_flags
direct_profile,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$REPS,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true MAT_TRGSW_DIRECT_DFT_PROFILE=true
narrow32_profile,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$REPS,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true MAT_TRGSW_DIRECT_DFT_PROFILE=true MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32=true
CSV

run_variant() {
  local variant="$1"
  shift
  local dir="$RAW/$variant"
  mkdir -p "$dir"
  make clean >"$dir/clean.log" 2>&1
  make "${common_flags[@]}" "$@" -j"$JOBS" >"$dir/build.log" 2>&1
  ./main >"$dir/run.log" 2>&1
}

run_variant direct_profile

run_variant narrow32_profile \
  MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32=true

python3 scripts/build_stage313_narrow32_profile_attribution.py
