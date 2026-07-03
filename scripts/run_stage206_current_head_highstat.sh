#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

out_dir="${STAGE206_OUT_DIR:-repro/stage206_current_head_highstat}"
fft_lib="${FFT_LIB:-spqlios_avx512}"
param="${PARAM:-SET_2_3_2048}"
key="${KEY:-BINARY}"
jobs="${JOBS:-$(nproc)}"
r_values="${STAGE206_R_VALUES:-2 4}"
perf_runs="${STAGE206_PERF_RUNS:-10}"
bench_reps="${SAB_PVW_BENCH_REPS:-1}"
noise_seeds="${STAGE206_NOISE_SEEDS:-20}"
noise_trials="${SAB_PVW_NOISE_TRIALS:-1}"
noise_start_seed="${STAGE206_NOISE_START_SEED:-6866206}"

mkdir -p "$out_dir"

{
  printf 'date_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'git_head=%s\n' "$(git rev-parse --short HEAD)"
  printf 'cwd=%s\n' "$(pwd)"
  printf 'fft_lib=%s\n' "$fft_lib"
  printf 'param=%s\n' "$param"
  printf 'key=%s\n' "$key"
  printf 'r_values=%s\n' "$r_values"
  printf 'perf_runs=%s\n' "$perf_runs"
  printf 'bench_reps=%s\n' "$bench_reps"
  printf 'noise_seeds=%s\n' "$noise_seeds"
  printf 'noise_trials=%s\n' "$noise_trials"
  printf 'noise_start_seed=%s\n' "$noise_start_seed"
  printf 'uname='
  uname -a || true
  printf 'cpu_model='
  grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//' || true
  printf 'cpu_flags='
  grep -m1 '^flags' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//' || true
} > "$out_dir/environment.log"

for r in $r_values; do
  run_dir="$out_dir/full_sab_ab_r${r}_runs${perf_runs}"
  driver_log="$out_dir/full_sab_ab_r${r}_runs${perf_runs}.driver.log"
  STAGE20_ACTIVE_BENCH_RUNS="$perf_runs" \
    SAB_PVW_BENCH_R="$r" \
    SAB_PVW_BENCH_REPS="$bench_reps" \
    STAGE20_ACTIVE_BENCH_OUT_DIR="$run_dir" \
    FFT_LIB="$fft_lib" \
    KEY="$key" \
    PARAM="$param" \
    JOBS="$jobs" \
    bash scripts/run_stage20_active_buffer_bench.sh 2>&1 | tee "$driver_log"
done

noise_dir="$out_dir/final_noise_seeds${noise_seeds}"
noise_driver_log="$out_dir/final_noise_seeds${noise_seeds}.driver.log"
STAGE25_FINAL_NOISE_R_VALUES="$r_values" \
  STAGE25_FINAL_NOISE_SEED_COUNT="$noise_seeds" \
  STAGE25_FINAL_NOISE_START_SEED="$noise_start_seed" \
  SAB_PVW_NOISE_TRIALS="$noise_trials" \
  STAGE25_FINAL_NOISE_OUT_DIR="$noise_dir" \
  FFT_LIB="$fft_lib" \
  KEY="$key" \
  PARAM="$param" \
  JOBS="$jobs" \
  bash scripts/run_stage25_final_noise_sweep.sh 2>&1 | tee "$noise_driver_log"

make clean >/dev/null 2>&1 || true

printf 'Stage206 high-stat current-head run complete: %s\n' "$out_dir"
