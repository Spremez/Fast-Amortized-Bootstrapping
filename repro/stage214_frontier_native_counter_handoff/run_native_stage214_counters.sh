#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
OUT="repro/stage214_frontier_native_counter_handoff/native_perf_raw"
mkdir -p "$OUT"

EVENTS="${STAGE214_EVENTS:-cycles,instructions,cache-references,cache-misses,branches,branch-misses,mem_inst_retired.all_loads,mem_inst_retired.all_stores,fp_arith_inst_retired.512b_packed_double,fp_arith_inst_retired.256b_packed_double}"
JOBS="${STAGE214_JOBS:-$(nproc)}"

if ! command -v perf >/dev/null 2>&1; then
  echo "perf not found on this host" >&2
  exit 2
fi

if [ ! -f repro/stage213_dft_wrapper_integration_preflight/stage213_dft_wrapper_integration_preflight.c ]; then
  echo "Stage213 probe source is missing; run from repository root at a commit containing Stage213." >&2
  exit 3
fi

build_and_run() {
  local impl="$1"
  local extra_make="$2"
  local extra_cflags="$3"
  cd "$ROOT/src/mosfhet"
  make clean >/dev/null 2>&1 || true
  make static FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false ENABLE_PVW_TMLWE=true MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true $extra_make -j"$JOBS"
  cd "$ROOT"
  for r in 2 4; do
    local bin="$OUT/stage214_${impl}_r${r}_probe"
    gcc -O3 -march=native -Wall -Wextra -DUSE_SPQLIOS -DAVX512_OPT -DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED $extra_cflags       -DSTAGE209_R="$r" -DSTAGE209_N=2048 -DSTAGE209_ITEMS="${STAGE214_ITEMS:-128}"       -DSTAGE209_REPS="${STAGE214_REPS:-8}" -DSTAGE209_WARMUPS="${STAGE214_WARMUPS:-2}" -DSTAGE209_BG_BIT=23       -I . -I src/mosfhet/include       -o "$bin" repro/stage213_dft_wrapper_integration_preflight/stage213_dft_wrapper_integration_preflight.c src/mosfhet/lib/libmosfhet.a -lm
    for variant in torus_to_dft_rows combined_current; do
      perf stat -x, -e "$EVENTS" -o "$OUT/perf_${impl}_r${r}_${variant}.log" "$bin" "$variant" > "$OUT/run_${impl}_r${r}_${variant}.log" 2>&1
    done
    rm -f "$bin"
  done
}

build_and_run baseline "" ""
build_and_run wrapper "MAT_TRGSW_MULTIROW_DFT_WRAPPER=true" "-DMAT_TRGSW_MULTIROW_DFT_WRAPPER"

echo "Stage214 native counter logs written to $OUT"
