#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage281_cmux_residual_repeated_gate/raw"
JOBS="${JOBS:-$(nproc)}"
LATENCY_REPS="${STAGE281_REPS:-3}"

mkdir -p "$RAW"
cd "$ROOT"

base_flags=(
  FFT_LIB=spqlios_avx512
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_NONBINARY_BENCH=true
  SAB_PVW_NONBINARY_BENCH_R=4
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true
  SAB_PVW_NONBINARY_BENCH_TERNARY=false
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

candidate_flags=(
  SAB_PVW_BACKEND_FROM_DFT_ADD=true
  SAB_PVW_SUB_DECOMP_FUSION=true
  MAT_TRGSW_AVX512_SUB_DECOMP=true
  SAB_PVW_DUAL_SUB_CMUX=true
)

cat >"$RAW/variant_plan.csv" <<CSV
variant,kind,reps,extra_flags
fast_control,latency,$LATENCY_REPS,
backend_sub_decomp_dual,latency,$LATENCY_REPS,SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true SAB_PVW_DUAL_SUB_CMUX=true
fast_control,profile,1,
backend_sub_decomp_dual,profile,1,SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true SAB_PVW_DUAL_SUB_CMUX=true
CSV

run_case() {
  local variant="$1"
  local kind="$2"
  local reps="$3"
  shift 3
  local extra_flags=("$@")
  local stem="${variant}_${kind}"
  if [[ "$kind" == "profile" ]]; then
    extra_flags+=(SAB_PVW_BODY_PROFILE=true)
  fi

  make clean >"$RAW/${stem}_clean.log" 2>&1
  make "${base_flags[@]}" SAB_PVW_NONBINARY_BENCH_REPS="$reps" \
    "${extra_flags[@]}" -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

run_case fast_control latency "$LATENCY_REPS"
run_case backend_sub_decomp_dual latency "$LATENCY_REPS" "${candidate_flags[@]}"
run_case fast_control profile 1
run_case backend_sub_decomp_dual profile 1 "${candidate_flags[@]}"
