#!/usr/bin/env bash
set -euo pipefail

OUT="repro/stage266_current_head_nonbinary_native_counter/native_perf_raw"
mkdir -p "$OUT"
EVENTS="${STAGE266_EVENTS:-cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double}"
JOBS="${STAGE266_JOBS:-$(nproc)}"

{
  printf 'hostname,'
  hostname
  printf 'whoami,'
  whoami
  printf 'uname,'
  uname -a
  printf 'perf,'
  command -v perf || true
  printf 'perf_event_paranoid,'
  cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true
  lscpu
} > "$OUT/remote_environment.log"

run_mode() {
  local mode="$1"
  local include_zero="$2"
  local ternary="$3"
  make clean >/dev/null 2>&1 || true
  make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \
    SAB_PVW_NONBINARY_BENCH=true \
    SAB_PVW_NONBINARY_BENCH_R=4 \
    SAB_PVW_NONBINARY_BENCH_REPS=1 \
    SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO="$include_zero" \
    SAB_PVW_NONBINARY_BENCH_TERNARY="$ternary" \
    MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
    -j"$JOBS" > "$OUT/build_${mode}.log" 2>&1
  perf stat -x, -e "$EVENTS" -o "$OUT/perf_${mode}.log" -- \
    stdbuf -o0 ./main > "$OUT/run_${mode}.log" 2>&1
}

run_mode include_zero true false
run_mode ternary false true
make clean >/dev/null 2>&1 || true
echo "Stage266 native non-binary counter logs written to $OUT"
