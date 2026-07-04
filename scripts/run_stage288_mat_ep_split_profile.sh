#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage288_mat_ep_split_profile/raw"
JOBS="${JOBS:-$(nproc)}"
REPS="${STAGE288_REPS:-1}"

mkdir -p "$RAW"
cd "$ROOT"

common_flags=(
  FFT_LIB=spqlios_avx512
  A_PRNG=none
  ENABLE_VAES=false
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_NONBINARY_BENCH=true
  SAB_PVW_NONBINARY_BENCH_R=4
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

cat >"$RAW/variant_plan.csv" <<'CSV'
variant,r,mode,reps,profile_flags
backend_sub_decomp_dual,4,include_zero,1,SAB_PVW_BODY_PROFILE=true MAT_TRGSW_SPLIT_PROFILE=true
CSV

make clean >"$RAW/clean.log" 2>&1
make "${common_flags[@]}" -j"$JOBS" >"$RAW/build.log" 2>&1
./main >"$RAW/run.log" 2>&1
