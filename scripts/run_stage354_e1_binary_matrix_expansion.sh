#!/usr/bin/env bash
# Stage354: E1 binary parameter-matrix expansion on the current main-tree head.
# Protocol identical to repro/stage340_parameter_matrix_current_head_gate
# (same build flags, 10 perf runs, 10-trial noise run with /usr/bin/time -v).
# Cases chosen for BatchBoot (USENIX Sec'26) n=4096 alignment and to fill the
# untested SET family rows within the documented 7 GB WSL memory budget.
set -uo pipefail

ROOT="/mnt/d/codexprograms/whFast-Amortized-Bootstrapping/Fast-Amortized-Bootstrapping"
OUT="$ROOT/repro/stage354_e1_binary_matrix_expansion/raw"
PERF_RUNS="${STAGE354_PERF_RUNS:-10}"
NOISE_TRIALS="${STAGE354_NOISE_TRIALS:-10}"
# risk-ascending: complete earlier rows even if a later row fails
CASES=(
  "SET_4_5_4096 2"
  "SET_4_5_4096 4"
  "SET_6_7_4096 4"
  "SET_8_9_4096 4"
)

cd "$ROOT"
mkdir -p "$OUT"
git rev-parse HEAD > "$OUT/run_git_head.txt" 2>/dev/null || true
{
  echo "# Stage354 E1 binary matrix expansion"
  echo "# started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# perf_runs=$PERF_RUNS noise_trials=$NOISE_TRIALS"
} > "$OUT/driver.log"

BUILD_FLAGS_COMMON="FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true"

failures=0
for entry in "${CASES[@]}"; do
  set -- $entry
  param="$1"; r="$2"; case_id="${param}_r${r}"
  cdir="$OUT/$case_id"
  mkdir -p "$cdir/perf" "$cdir/noise"

  echo "[$(date -u +%H:%M:%S)] $case_id perf build" >> "$OUT/driver.log"
  make clean > "$cdir/perf/clean.log" 2>&1
  if ! make $BUILD_FLAGS_COMMON PARAM="$param" \
      SAB_PVW_NONBINARY_BENCH=true SAB_PVW_NONBINARY_BENCH_R="$r" \
      SAB_PVW_NONBINARY_BENCH_REPS=1 SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
      SAB_PVW_NONBINARY_BENCH_TERNARY=false -j16 > "$cdir/perf/build.log" 2>&1; then
    echo "[$(date -u +%H:%M:%S)] $case_id PERF_BUILD_FAILED" >> "$OUT/driver.log"
    failures=$((failures+1)); continue
  fi
  for run_idx in $(seq 0 $((PERF_RUNS-1))); do
    ./main > "$cdir/perf/run_${run_idx}.log" 2>&1
    if [ ! -s "$cdir/perf/run_${run_idx}.log" ]; then
      echo "[$(date -u +%H:%M:%S)] $case_id PERF_RUN_${run_idx}_EMPTY_OR_KILLED" >> "$OUT/driver.log"
      failures=$((failures+1))
      break
    fi
    echo "[$(date -u +%H:%M:%S)] $case_id perf run $run_idx done" >> "$OUT/driver.log"
  done

  echo "[$(date -u +%H:%M:%S)] $case_id noise build" >> "$OUT/driver.log"
  make clean > "$cdir/noise/clean.log" 2>&1
  if ! make $BUILD_FLAGS_COMMON PARAM="$param" \
      SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true SAB_PVW_NONBINARY_TARGET_NOISE_R="$r" \
      SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS="$NOISE_TRIALS" \
      SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true \
      SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false -j16 > "$cdir/noise/build.log" 2>&1; then
    echo "[$(date -u +%H:%M:%S)] $case_id NOISE_BUILD_FAILED" >> "$OUT/driver.log"
    failures=$((failures+1)); continue
  fi
  /usr/bin/time -v ./main > "$cdir/noise/run.log" 2> "$cdir/noise/time.log"
  echo "[$(date -u +%H:%M:%S)] $case_id complete" >> "$OUT/driver.log"
done

echo "# finished: $(date -u +%Y-%m-%dT%H:%M:%SZ) failures=$failures" >> "$OUT/driver.log"
exit "$failures"
