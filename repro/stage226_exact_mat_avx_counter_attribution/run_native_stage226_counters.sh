#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
OUT="repro/stage226_exact_mat_avx_counter_attribution/native_perf_raw"
mkdir -p "$OUT"

EVENTS="${STAGE226_EVENTS:-cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double}"
JOBS="${STAGE226_JOBS:-$(nproc)}"
BASE_ARGS=(FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3_2048 KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_RGT4_FUSED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_BENCH=true SAB_PVW_BENCH_R=6 SAB_PVW_BENCH_REPS=1)

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
  printf 'remote_pwd,'
  pwd
  lscpu
} > "$OUT/remote_environment.log"

if ! command -v perf >/dev/null 2>&1; then
  echo "perf not found on this host" >&2
  exit 2
fi

run_variant() {
  local variant="$1"
  shift
  local extra_args=("$@")
  make clean >/dev/null 2>&1 || true
  make "${BASE_ARGS[@]}" "${extra_args[@]}" -j"$JOBS" > "$OUT/build_${variant}.log" 2>&1
  perf stat -x, -e "$EVENTS" -o "$OUT/perf_${variant}.log" -- stdbuf -o0 ./main > "$OUT/run_${variant}.log" 2>&1
}

run_variant wrapper_fused_from_dft_add SAB_PVW_FUSED_FROM_DFT_ADD=true
run_variant backend_from_dft_add SAB_PVW_BACKEND_FROM_DFT_ADD=true
make clean >/dev/null 2>&1 || true

echo "Stage226 native counter logs written to $OUT"
