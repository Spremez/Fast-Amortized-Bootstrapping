#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE321_OUT_DIR:-$ROOT/repro/stage321_r4_unrolled_fullsab_ab}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
RUNS="${STAGE321_RUNS:-5}"
REPS="${STAGE321_REPS:-1}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"
R_VALUE="${STAGE321_R:-4}"

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
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  SAB_PVW_DUAL_SUB_CMUX=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

cat >"$RAW/variant_plan.csv" <<CSV
variant,param,fft_lib,r,runs,reps,extra_flags
direct_baseline,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$RUNS,$REPS,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
r4_unrolled_direct,$PARAM_VALUE,$FFT_LIB_VALUE,$R_VALUE,$RUNS,$REPS,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true
CSV

build_and_run_variant() {
  local variant="$1"
  shift
  local dir="$RAW/$variant"
  mkdir -p "$dir"
  make clean >"$dir/clean.log" 2>&1
  make "${common_flags[@]}" "$@" -j"$JOBS" >"$dir/build.log" 2>&1
  for run_idx in $(seq 0 "$((RUNS - 1))"); do
    ./main >"$dir/run_${run_idx}.log" 2>&1
  done
}

build_and_run_variant direct_baseline

build_and_run_variant r4_unrolled_direct \
  MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true

python3 scripts/build_stage321_r4_unrolled_fullsab_ab.py
