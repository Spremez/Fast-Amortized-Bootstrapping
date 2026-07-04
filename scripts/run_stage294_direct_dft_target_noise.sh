#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE294_OUT_DIR:-$ROOT/repro/stage294_direct_dft_target_noise}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
TRIALS="${STAGE294_TRIALS:-3}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"

mkdir -p "$RAW/direct_dft_target_noise"
cd "$ROOT"

cat >"$RAW/variant_plan.csv" <<CSV
variant,param,fft_lib,r,trials,flags
direct_dft_target_noise,$PARAM_VALUE,$FFT_LIB_VALUE,4,$TRIALS,SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true selected PVW-SAB flags
CSV

make clean >"$RAW/direct_dft_target_noise/clean.log" 2>&1
make FFT_LIB="$FFT_LIB_VALUE" \
  A_PRNG=none ENABLE_VAES=false \
  KEY=BINARY PARAM="$PARAM_VALUE" \
  SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_R=4 \
  SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS="$TRIALS" \
  SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true \
  SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  MAT_TRGSW_AVX512_SUB_DECOMP=true \
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true \
  SAB_PVW_BACKEND_FROM_DFT_ADD=true \
  SAB_PVW_SUB_DECOMP_FUSION=true \
  SAB_PVW_DUAL_SUB_CMUX=true \
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true \
  -j"$JOBS" >"$RAW/direct_dft_target_noise/build.log" 2>&1

/usr/bin/time -v ./main \
  >"$RAW/direct_dft_target_noise/run.log" \
  2>"$RAW/direct_dft_target_noise/time.log"

python3 scripts/build_stage294_direct_dft_target_noise.py
