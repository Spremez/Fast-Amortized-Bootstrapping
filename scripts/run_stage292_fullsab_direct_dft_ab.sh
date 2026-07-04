#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE292_OUT_DIR:-$ROOT/repro/stage292_fullsab_direct_dft_ab}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
RUNS="${STAGE292_RUNS:-3}"
REPS="${STAGE292_REPS:-1}"
R_VALUE="${STAGE292_R:-4}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"

mkdir -p "$RAW"
cd "$ROOT"

base_flags=(
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
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  SAB_PVW_DUAL_SUB_CMUX=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

cat >"$RAW/variant_plan.csv" <<CSV
variant,r,param,fft_lib,runs,reps,extra_flags
selected_control,$R_VALUE,$PARAM_VALUE,$FFT_LIB_VALUE,$RUNS,$REPS,
direct_dft_candidate,$R_VALUE,$PARAM_VALUE,$FFT_LIB_VALUE,$RUNS,$REPS,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
CSV

run_variant() {
  local variant="$1"
  shift
  local dir="$RAW/$variant"
  mkdir -p "$dir"
  make clean >"$dir/clean.log" 2>&1
  make "${base_flags[@]}" "$@" -j"$JOBS" >"$dir/build.log" 2>&1
  for run_idx in $(seq 0 "$((RUNS - 1))"); do
    ./main >"$dir/run_${run_idx}.log" 2>&1
  done
}

run_variant selected_control
run_variant direct_dft_candidate MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true

python3 scripts/build_stage292_fullsab_direct_dft_ab.py
