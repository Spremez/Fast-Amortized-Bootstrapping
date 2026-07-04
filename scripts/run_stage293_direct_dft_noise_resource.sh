#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${STAGE293_OUT_DIR:-$ROOT/repro/stage293_direct_dft_noise_resource}"
RAW="$OUT/raw"
JOBS="${JOBS:-$(nproc)}"
PARAM_VALUE="${PARAM:-SET_2_3_2048}"
FFT_LIB_VALUE="${FFT_LIB:-spqlios_avx512}"

mkdir -p "$RAW"
cd "$ROOT"

candidate_flags=(
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
  MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
)

cat >"$RAW/variant_plan.csv" <<CSV
case,param,fft_lib,flags
target_correctness,$PARAM_VALUE,$FFT_LIB_VALUE,SAB_PVW_TARGET_TEST=true plus selected direct-DFT flags
target_resource,$PARAM_VALUE,$FFT_LIB_VALUE,SAB_PVW_RESOURCE_TEST=true SAB_PVW_RESOURCE_R=4 plus selected direct-DFT flags
unstable_noise_attempt,$PARAM_VALUE,$FFT_LIB_VALUE,optional previous/explicit SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE_TEST attempt; not a pass gate
CSV

run_case() {
  local stem="$1"
  shift
  local dir="$RAW/$stem"
  mkdir -p "$dir"
  make clean >"$dir/clean.log" 2>&1
  make "${candidate_flags[@]}" "$@" -j"$JOBS" >"$dir/build.log" 2>&1
  /usr/bin/time -v ./main >"$dir/run.log" 2>"$dir/time.log"
}

run_case target_correctness SAB_PVW_TARGET_TEST=true
run_case target_resource SAB_PVW_RESOURCE_TEST=true SAB_PVW_RESOURCE_R=4

if [[ "${STAGE293_RUN_UNSTABLE_NOISE_ATTEMPT:-0}" == "1" ]]; then
  set +e
  run_case unstable_noise_attempt \
    SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE_TEST=true \
    SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE_TRIALS="${STAGE293_TRIALS:-1}"
  set -e
fi

python3 scripts/build_stage293_direct_dft_noise_resource.py
