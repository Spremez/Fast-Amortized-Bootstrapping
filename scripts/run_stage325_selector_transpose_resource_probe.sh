#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${STAGE325_OUT_DIR:-repro/stage325_selector_transpose_resource_probe}"
RUNS="${STAGE325_RUNS:-7}"
REPS="${STAGE325_REPS:-20000}"
BUILD_REPS="${STAGE325_BUILD_REPS:-200}"
CC_BIN="${CC:-gcc}"

mkdir -p "${OUT_DIR}/raw"

"${CC_BIN}" -O3 -std=c11 -D_POSIX_C_SOURCE=200809L -Wall -Wextra \
  -mavx512f -mfma -march=native \
  scripts/stage325_selector_transpose_microbench.c -lm \
  -o "${OUT_DIR}/stage325_selector_transpose_microbench"

{
  echo "date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "uname=$(uname -a)"
  echo "compiler=$(${CC_BIN} --version | head -n 1)"
  echo "runs=${RUNS}"
  echo "reps=${REPS}"
  echo "build_reps=${BUILD_REPS}"
  grep -m1 '^flags' /proc/cpuinfo || true
} > "${OUT_DIR}/environment.log"

for i in $(seq 0 $((RUNS - 1))); do
  "${OUT_DIR}/stage325_selector_transpose_microbench" "${REPS}" "${BUILD_REPS}" \
    > "${OUT_DIR}/raw/run_${i}.log"
done
