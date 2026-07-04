#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE311_OUT_DIR:-$ROOT/repro/stage311_digit_narrow32_microbench}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
RUNS="${STAGE311_RUNS:-5}"
REPS="${STAGE311_REPS:-5000}"
R_VALUE="${STAGE311_R:-4}"
N_VALUE="${STAGE311_N:-2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"

mkdir -p "$RAW"
cd "$ROOT"

cat >"$RAW/variant_plan.csv" <<CSV
variant,r,N,reps,runs,fft_lib,flags
direct_baseline,$R_VALUE,$N_VALUE,$REPS,$RUNS,$FFT_LIB_VALUE,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true MAT_TRGSW_DIRECT_DFT_PROFILE=true
narrow32_digit,$R_VALUE,$N_VALUE,$REPS,$RUNS,$FFT_LIB_VALUE,MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true MAT_TRGSW_DIRECT_DFT_PROFILE=true MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32=true
CSV

build_and_run_variant() {
  local variant="$1"
  shift
  local variant_dir="$RAW/$variant"
  mkdir -p "$variant_dir"
  make clean >"$variant_dir/clean.log" 2>&1
  make FFT_LIB="$FFT_LIB_VALUE" \
    A_PRNG=none ENABLE_VAES=false \
    KEY=BINARY PARAM=SET_2_3 \
    MAT_TRGSW_SUB_DFT_BENCH=true \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    MAT_TRGSW_AVX512_SUB_DECOMP=true \
    MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true \
    MAT_TRGSW_DIRECT_DFT_PROFILE=true \
    "$@" \
    MAT_TRGSW_SUB_DFT_BENCH_N="$N_VALUE" \
    MAT_TRGSW_SUB_DFT_BENCH_R="$R_VALUE" \
    MAT_TRGSW_SUB_DFT_BENCH_REPS="$REPS" \
    -j"$JOBS" >"$variant_dir/build.log" 2>&1
  for run_idx in $(seq 0 "$((RUNS - 1))"); do
    ./main >"$variant_dir/run_${run_idx}.log" 2>&1
  done
}

build_and_run_variant direct_baseline

build_and_run_variant narrow32_digit \
  MAT_TRGSW_DIRECT_DFT_DIGIT_NARROW32=true

python3 scripts/build_stage311_digit_narrow32_microbench.py
