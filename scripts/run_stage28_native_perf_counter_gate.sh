#!/usr/bin/env bash
set -euo pipefail

out_dir="${STAGE28_PERF_GATE_OUT_DIR:-repro/stage28_native_perf_counter_gate}"
run_bench="${STAGE28_RUN_BENCH:-0}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
key="${KEY:-BINARY}"
param="${PARAM:-SET_2_3_2048}"
r="${SAB_PVW_BENCH_R:-4}"
reps="${SAB_PVW_BENCH_REPS:-1}"
jobs="${JOBS:-$(nproc)}"

mkdir -p "$out_dir"

summary_csv="$out_dir/summary.csv"
env_log="$out_dir/environment.log"
perf_smoke_log="$out_dir/perf_smoke.log"
perf_smoke_err="$out_dir/perf_smoke.err"
bench_perf_log="$out_dir/bench_perf.log"
bench_run_log="$out_dir/bench_run.log"
bench_err_log="$out_dir/bench.err"

printf 'probe,status,evidence,detail\n' > "$summary_csv"

csv_row() {
  local probe="$1"
  local status="$2"
  local evidence="$3"
  local detail="$4"
  detail="${detail//$'\n'/ }"
  detail="${detail//,/;}"
  printf '%s,%s,%s,%s\n' "$probe" "$status" "$evidence" "$detail" >> "$summary_csv"
}

{
  printf 'date=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
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
} > "$env_log"

csv_row environment RECORDED "$env_log" "Platform metadata captured."

if ! command -v perf >/dev/null 2>&1; then
  printf 'perf not found in PATH\n' > "$perf_smoke_log"
  csv_row perf_command MISSING "$perf_smoke_log" "Install Linux perf tools or rerun on native Linux with perf in PATH."
  csv_row hardware_counter_gate BLOCKED "$summary_csv" "No perf command; MAT-AVX512 theoretical load/store claim remains blocked."
  printf 'Stage 28 perf-counter gate summary: %s\n' "$summary_csv"
  exit 0
fi

csv_row perf_command AVAILABLE "$(command -v perf)" "perf command found."

set +e
perf stat -e cycles,instructions,cache-references,cache-misses,branches,branch-misses \
  -o "$perf_smoke_log" -- true 2> "$perf_smoke_err"
perf_rc="$?"
set -e

if [[ "$perf_rc" -ne 0 ]]; then
  csv_row perf_smoke FAILED "$perf_smoke_err" "perf stat on true failed with rc=$perf_rc."
  csv_row hardware_counter_gate BLOCKED "$summary_csv" "perf exists but hardware counters are not usable under current permissions/platform."
  printf 'Stage 28 perf-counter gate summary: %s\n' "$summary_csv"
  exit 0
fi

csv_row perf_smoke PASS "$perf_smoke_log" "Basic hardware counters are usable."

if [[ "$run_bench" != "1" ]]; then
  csv_row bench_perf SKIPPED "$summary_csv" "Set STAGE28_RUN_BENCH=1 to run the heavy SAB benchmark under perf."
  csv_row hardware_counter_gate READY_FOR_BENCH "$summary_csv" "perf smoke passed; rerun with STAGE28_RUN_BENCH=1 for MAT-AVX512 attribution."
  printf 'Stage 28 perf-counter gate summary: %s\n' "$summary_csv"
  exit 0
fi

make clean
make FFT_LIB="$fft_lib" MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true \
  SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_BENCH=true \
  SAB_PVW_BENCH_R="$r" SAB_PVW_BENCH_REPS="$reps" \
  KEY="$key" PARAM="$param" -j"$jobs"

set +e
perf stat -e cycles,instructions,cache-references,cache-misses,branches,branch-misses \
  -o "$bench_perf_log" -- stdbuf -o0 ./main > "$bench_run_log" 2> "$bench_err_log"
bench_rc="$?"
set -e

if [[ "$bench_rc" -ne 0 ]]; then
  csv_row bench_perf FAILED "$bench_err_log" "SAB benchmark under perf failed with rc=$bench_rc."
  csv_row hardware_counter_gate BLOCKED "$summary_csv" "Cannot use this run for MAT-AVX512 hardware-counter attribution."
  printf 'Stage 28 perf-counter gate summary: %s\n' "$summary_csv"
  exit 0
fi

if ! grep -q 'SAB_PVW_BENCH correctness target_full .* Pass' "$bench_run_log"; then
  csv_row bench_correctness FAILED "$bench_run_log" "Expected SAB_PVW_BENCH target_full correctness Pass line not found."
  csv_row hardware_counter_gate BLOCKED "$summary_csv" "Benchmark ran but correctness gate did not prove target output."
  printf 'Stage 28 perf-counter gate summary: %s\n' "$summary_csv"
  exit 0
fi

csv_row bench_perf PASS "$bench_perf_log" "SAB benchmark completed under perf counters."
csv_row bench_correctness PASS "$bench_run_log" "target_full correctness line found."
csv_row hardware_counter_gate PASS "$summary_csv" "Hardware-counter attribution evidence is available for MAT-AVX512 audit."
printf 'Stage 28 perf-counter gate summary: %s\n' "$summary_csv"
