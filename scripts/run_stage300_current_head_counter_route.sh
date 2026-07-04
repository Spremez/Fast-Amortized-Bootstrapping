#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE300_OUT_DIR:-repro/stage300_current_head_counter_route}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"

mkdir -p "$out_dir"

{
  printf 'date_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'git_head=%s\n' "$(git rev-parse --short HEAD 2>/dev/null || true)"
  printf 'uname='
  uname -a || true
  printf 'cwd=%s\n' "$(pwd)"
  printf 'perf_path=%s\n' "$(command -v perf || true)"
  if [[ -r /proc/sys/kernel/perf_event_paranoid ]]; then
    printf 'perf_event_paranoid='
    cat /proc/sys/kernel/perf_event_paranoid
  else
    printf 'perf_event_paranoid=unreadable\n'
  fi
  if [[ -r /proc/cpuinfo ]]; then
    printf 'cpu_model='
    grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//' || true
    printf 'cpu_flags='
    grep -m1 '^flags' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//' || true
  fi
} > "$out_dir/environment.log"

stage28_out="$out_dir/local_stage28_perf_probe"
mkdir -p "$stage28_out"

set +e
STAGE28_PERF_GATE_OUT_DIR="$stage28_out" \
STAGE28_RUN_BENCH=0 \
FFT_LIB="$fft_lib" \
KEY="$key" \
PARAM="$param" \
bash scripts/run_stage28_native_perf_counter_gate.sh \
  > "$out_dir/local_stage28_stdout.log" \
  2> "$out_dir/local_stage28_stderr.log"
stage28_rc="$?"
set -e

printf 'stage28_probe_rc=%s\n' "$stage28_rc" > "$out_dir/local_stage28_rc.log"

python3 scripts/build_stage300_current_head_counter_route.py
