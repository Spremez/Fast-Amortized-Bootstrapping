#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage280_cmux_mat_ep_residual_screen/raw"
JOBS="${JOBS:-$(nproc)}"
REPS="${STAGE280_REPS:-1}"

mkdir -p "$RAW"
cd "$ROOT"

common_flags=(
  FFT_LIB=spqlios_avx512
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_NONBINARY_BENCH=true
  SAB_PVW_NONBINARY_BENCH_R=4
  SAB_PVW_NONBINARY_BENCH_REPS="$REPS"
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true
  SAB_PVW_NONBINARY_BENCH_TERNARY=false
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
  SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
)

write_plan() {
  cat >"$RAW/variant_plan.csv" <<'CSV'
variant,profile,extra_flags
fast_control,false,
backend_from_dft_add,false,SAB_PVW_BACKEND_FROM_DFT_ADD=true
sub_decomp_avx,false,SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true
backend_sub_decomp_avx,false,SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true
backend_sub_decomp_dual,false,SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true SAB_PVW_DUAL_SUB_CMUX=true
fast_control,true,
backend_from_dft_add,true,SAB_PVW_BACKEND_FROM_DFT_ADD=true
sub_decomp_avx,true,SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true
backend_sub_decomp_avx,true,SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true
backend_sub_decomp_dual,true,SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true SAB_PVW_DUAL_SUB_CMUX=true
CSV
}

run_case() {
  local variant="$1"
  local profile="$2"
  shift 2
  local extra_flags=("$@")
  local stem="${variant}"
  if [[ "$profile" == "true" ]]; then
    stem="${stem}_profile"
    extra_flags+=(SAB_PVW_BODY_PROFILE=true)
  fi

  make clean >"$RAW/${stem}_clean.log" 2>&1
  make "${common_flags[@]}" "${extra_flags[@]}" \
    -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
  ./main >"$RAW/${stem}_run.log" 2>&1
}

write_plan
run_case fast_control false
run_case backend_from_dft_add false SAB_PVW_BACKEND_FROM_DFT_ADD=true
run_case sub_decomp_avx false SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true
run_case backend_sub_decomp_avx false SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true
run_case backend_sub_decomp_dual false SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true SAB_PVW_DUAL_SUB_CMUX=true

run_case fast_control true
run_case backend_from_dft_add true SAB_PVW_BACKEND_FROM_DFT_ADD=true
run_case sub_decomp_avx true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true
run_case backend_sub_decomp_avx true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true
run_case backend_sub_decomp_dual true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true MAT_TRGSW_AVX512_SUB_DECOMP=true SAB_PVW_DUAL_SUB_CMUX=true
