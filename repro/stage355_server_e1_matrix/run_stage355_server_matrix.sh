#!/usr/bin/env bash
# Stage355-server: full binary parameter matrix on the benchmark server.
# Protocol identical to Stage340/354 (same build flags, 10 perf runs,
# 10-trial noise run under /usr/bin/time -v, correctness and gate checks).
# Cases ordered by evidence value: the resource-bound SET_8_9_4096 r=4 row
# first (251 GB RAM makes it feasible), then Boot8/Boot6-aligned rows, then
# the full 2048/4096 matrix for a single-machine homogeneous table.
set -uo pipefail

ROOT="$HOME/spz/Fast-Amortized-Bootstrapping-stage355-e1-server"
OUT="$ROOT/repro/stage355_server_e1_matrix/raw"
PERF_RUNS=10
NOISE_TRIALS=10
CASES=(
  "SET_8_9_4096 4"
  "SET_8_9_4096 2"
  "SET_6_7_4096 4"
  "SET_4_5_4096 4"
  "SET_4_5_4096 2"
  "SET_2_3_4096 4"
  "SET_2_3_4096 2"
  "SET_4_5_2048 4"
  "SET_4_5_2048 2"
  "SET_2_3_2048 4"
  "SET_2_3_2048 2"
)

cd "$ROOT" || exit 1
mkdir -p "$OUT"
{
  echo "# Stage355 server E1 matrix"
  echo "# started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# host: $(hostname), cores: $(nproc)"
} > "$OUT/driver.log"

{
  echo "field,value"
  echo "cpu_model,$(lscpu | grep 'Model name' | cut -d: -f2- | xargs)"
  echo "cores,$(nproc)"
  echo "memory_gb,$(free -g | awk '/^Mem:/{print $2}')"
  echo "avx512,$(grep -c avx512 /proc/cpuinfo | head -1)"
  echo "gcc,$(gcc --dumpversion)"
  echo "kernel,$(uname -r)"
  echo "source_tree_sha256,61eee15dff53b3e1b7069cf8acd7db94c51fa973d75e1e3dcc9335fc7fee81fe"
  echo "source_local_git_head,15fd7a6 (main tree, 6a5f113 is ancestor)"
  echo "protocol,stage340-identical flags; 10 perf runs; 10-trial noise; /usr/bin/time -v"
} > "$OUT/platform.csv"

BUILD_FLAGS_COMMON="FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true"

failures=0
for entry in "${CASES[@]}"; do
  set -- $entry
  param="$1"; r="$2"; case_id="${param}_r${r}"
  cdir="$OUT/$case_id"

  # resume support: skip a case whose 10 perf runs all passed and whose
  # noise run already recorded gate=Pass
  if [ -f "$cdir/noise/run.log" ] && grep -q "gate=Pass" "$cdir/noise/run.log" \
      && [ "$(ls "$cdir/perf"/run_*.log 2>/dev/null | wc -l)" -ge "$PERF_RUNS" ]; then
    all_pass=1
    for f in "$cdir/perf"/run_*.log; do
      grep -q "correctness .*: Pass" "$f" || { all_pass=0; break; }
    done
    if [ "$all_pass" = 1 ]; then
      echo "[$(date -u +%H:%M:%S)] $case_id resume-skip (complete)" >> "$OUT/driver.log"
      continue
    fi
  fi

  mkdir -p "$cdir/perf" "$cdir/noise"

  echo "[$(date -u +%H:%M:%S)] $case_id perf build" >> "$OUT/driver.log"
  make clean > "$cdir/perf/clean.log" 2>&1
  if ! make $BUILD_FLAGS_COMMON PARAM="$param" \
      SAB_PVW_NONBINARY_BENCH=true SAB_PVW_NONBINARY_BENCH_R="$r" \
      SAB_PVW_NONBINARY_BENCH_REPS=1 SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
      SAB_PVW_NONBINARY_BENCH_TERNARY=false -j32 > "$cdir/perf/build.log" 2>&1; then
    echo "[$(date -u +%H:%M:%S)] $case_id PERF_BUILD_FAILED" >> "$OUT/driver.log"
    failures=$((failures+1)); continue
  fi
  ok=1
  start_idx=0
  while [ -f "$cdir/perf/run_${start_idx}.log" ] \
      && grep -q "correctness .*: Pass" "$cdir/perf/run_${start_idx}.log" \
      && [ "$start_idx" -lt "$PERF_RUNS" ]; do
    start_idx=$((start_idx+1))
  done
  if [ "$start_idx" -gt 0 ] && [ "$start_idx" -lt "$PERF_RUNS" ]; then
    echo "[$(date -u +%H:%M:%S)] $case_id resume perf from run $start_idx" >> "$OUT/driver.log"
  fi
  for run_idx in $(seq "$start_idx" $((PERF_RUNS-1))); do
    ./main > "$cdir/perf/run_${run_idx}.log" 2>&1
    if ! grep -q "correctness .*: Pass" "$cdir/perf/run_${run_idx}.log"; then
      echo "[$(date -u +%H:%M:%S)] $case_id PERF_RUN_${run_idx}_FAILED" >> "$OUT/driver.log"
      failures=$((failures+1)); ok=0; break
    fi
    echo "[$(date -u +%H:%M:%S)] $case_id perf run $run_idx done" >> "$OUT/driver.log"
  done
  [ "$ok" = 1 ] || continue

  echo "[$(date -u +%H:%M:%S)] $case_id noise build" >> "$OUT/driver.log"
  make clean > "$cdir/noise/clean.log" 2>&1
  if ! make $BUILD_FLAGS_COMMON PARAM="$param" \
      SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true SAB_PVW_NONBINARY_TARGET_NOISE_R="$r" \
      SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS="$NOISE_TRIALS" \
      SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true \
      SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false -j32 > "$cdir/noise/build.log" 2>&1; then
    echo "[$(date -u +%H:%M:%S)] $case_id NOISE_BUILD_FAILED" >> "$OUT/driver.log"
    failures=$((failures+1)); continue
  fi
  /usr/bin/time -v ./main > "$cdir/noise/run.log" 2> "$cdir/noise/time.log"
  if grep -q "gate=Pass" "$cdir/noise/run.log"; then
    echo "[$(date -u +%H:%M:%S)] $case_id complete (noise Pass)" >> "$OUT/driver.log"
  else
    echo "[$(date -u +%H:%M:%S)] $case_id NOISE_GATE_MISSING" >> "$OUT/driver.log"
    failures=$((failures+1))
  fi
done

echo "# finished: $(date -u +%Y-%m-%dT%H:%M:%SZ) failures=$failures" >> "$OUT/driver.log"
exit "$failures"
