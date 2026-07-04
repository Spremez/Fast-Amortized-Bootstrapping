#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW="$ROOT/repro/stage273_sub_a_from_DFT_add_alias_microtest/raw"
JOBS="${JOBS:-$(nproc)}"

mkdir -p "$RAW"
cd "$ROOT"

common_flags=(
  FFT_LIB=spqlios_avx512
  KEY=BINARY
  PARAM=SET_2_3
  SAB_PVW_SUBA_ALIAS_TEST=true
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
)

run_case() {
  local variant="$1"
  shift
  local stem="${variant}_r4_alias_microtest"
  local clean_status=0
  local build_status=0
  local run_status=0

  set +e
  make clean >"$RAW/${stem}_clean.log" 2>&1
  clean_status=$?
  set -e

  if [[ "$clean_status" -eq 0 ]]; then
    set +e
    make "${common_flags[@]}" "$@" -j"$JOBS" >"$RAW/${stem}_build.log" 2>&1
    build_status=$?
    set -e
  else
    build_status=127
    : >"$RAW/${stem}_build.log"
  fi

  if [[ "$build_status" -eq 0 ]]; then
    set +e
    stdbuf -oL ./main >"$RAW/${stem}_run.log" 2>&1
    run_status=$?
    set -e
  else
    run_status=127
    : >"$RAW/${stem}_run.log"
  fi

  {
    printf 'variant,phase,exit_code\n'
    printf '%s,clean,%s\n' "$variant" "$clean_status"
    printf '%s,build,%s\n' "$variant" "$build_status"
    printf '%s,run,%s\n' "$variant" "$run_status"
  } >"$RAW/${stem}_exit_code.csv"
}

run_case default
run_case backend_from_dft_add SAB_PVW_BACKEND_FROM_DFT_ADD=true
