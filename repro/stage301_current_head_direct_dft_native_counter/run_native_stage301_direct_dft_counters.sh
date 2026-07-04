#!/usr/bin/env bash
set -euo pipefail

OUT="repro/stage301_current_head_direct_dft_native_counter/native_perf_raw"
mkdir -p "$OUT"
EVENTS="${STAGE301_EVENTS:-cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double}"
JOBS="${STAGE301_JOBS:-$(nproc)}"
PARAM="${STAGE301_PARAM:-SET_2_3_2048}"
R="${STAGE301_R:-4}"
REPS="${STAGE301_REPS:-1}"

{
  printf 'hostname,'
  hostname
  printf 'whoami,'
  whoami
  printf 'uname,'
  uname -a
  printf 'pwd,'
  pwd
  printf 'perf,'
  command -v perf || true
  printf 'perf_event_paranoid,'
  cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true
  lscpu
} > "$OUT/remote_environment.log"

run_variant() {
  local variant="$1"
  local direct_flag="$2"
  make clean >/dev/null 2>&1 || true
  make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM="$PARAM" \
    SAB_PVW_NONBINARY_BENCH=true \
    SAB_PVW_NONBINARY_BENCH_R="$R" \
    SAB_PVW_NONBINARY_BENCH_REPS="$REPS" \
    SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
    SAB_PVW_NONBINARY_BENCH_TERNARY=false \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    MAT_TRGSW_AVX512_SUB_DECOMP=true \
    SAB_PVW_BACKEND_FROM_DFT_ADD=true \
    SAB_PVW_SUB_DECOMP_FUSION=true \
    SAB_PVW_DUAL_SUB_CMUX=true \
    SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true \
    MAT_TRGSW_SUB_DECOMP_DFT_DIRECT="$direct_flag" \
    -j"$JOBS" > "$OUT/build_${variant}.log" 2>&1
  perf stat -x, -e "$EVENTS" -o "$OUT/perf_${variant}.log" -- \
    stdbuf -o0 ./main > "$OUT/run_${variant}.log" 2>&1
}

run_variant selected_control false
run_variant direct_dft true
make clean >/dev/null 2>&1 || true
echo "Stage301 native direct-DFT counter logs written to $OUT"
