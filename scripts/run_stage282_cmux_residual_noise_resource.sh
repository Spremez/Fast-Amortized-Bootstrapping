#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage282_cmux_residual_noise_resource/raw"
JOBS="${JOBS:-$(nproc)}"
TRIALS="${STAGE282_TRIALS:-3}"

mkdir -p "$RAW"
cd "$ROOT"

base_flags=(
  FFT_LIB=ffnt
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE_TEST=true
  SAB_PVW_INCLUDE_ZERO_FAST_RESOURCE_TRIALS="$TRIALS"
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
)

candidate_flags=(
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  SAB_PVW_DUAL_SUB_CMUX=true
)

cat >"$RAW/variant_plan.csv" <<CSV
variant,trials,extra_flags
fast_control,$TRIALS,
backend_sub_decomp_dual,$TRIALS,SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true SAB_PVW_DUAL_SUB_CMUX=true
CSV

run_case() {
  local variant="$1"
  shift
  local extra_flags=("$@")

  make clean >"$RAW/${variant}_clean.log" 2>&1
  make "${base_flags[@]}" "${extra_flags[@]}" \
    -j"$JOBS" >"$RAW/${variant}_build.log" 2>&1
  /usr/bin/time -v ./main >"$RAW/${variant}_run.log" 2>"$RAW/${variant}_time.log"
}

run_case fast_control
run_case backend_sub_decomp_dual "${candidate_flags[@]}"
