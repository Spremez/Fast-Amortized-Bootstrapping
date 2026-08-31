#!/usr/bin/env bash
# stage362 FINAL COMPREHENSIVE BENCHMARK
# h={39,41,42} x sigma+11 x {scalar SQ, scalar stock, SQ r-lane, stock r-lane}
# Purpose: determine optimal h, then compare all methods at that h
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=repro/stage356_sq_scale_sab
LOG=$OUT/final_bench.log
: > "$LOG"

COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"

echo "=== BUILD $(date) ===" | tee -a "$LOG"
make -B $COMMON probe_sq.exe -j32 > "$OUT/fin_build.log" 2>&1
[ -x ./probe_sq.exe ] || { echo "BUILD FAIL probe_sq" | tee -a "$LOG"; exit 1; }
cp probe_sq.exe probe_fin

# Build r-lane probe
OBJS=$(ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | tr '\n' ' ')
gcc -O2 -g -Iinclude -Isrc/mosfhet/include -march=native \
    -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DBINARY \
    src/sab_pvw_sq.c src/probe_pvw_sq.c src/mosfhet/src/mattrgsw.c \
    $OBJS -lm -o probe_fin_rlane 2>&1 | grep -E ' error' | head -3
[ -x ./probe_fin_rlane ] && echo "r-lane probe built" | tee -a "$LOG" \
  || echo "r-lane BUILD FAIL" | tee -a "$LOG"

# ═══════════════════════════════════════════════════
# PART 1: Scalar at three h values with sigma+11
# ═══════════════════════════════════════════════════
echo "=== PART 1: Scalar h={39,41,42} sigma+11 $(date) ===" | tee -a "$LOG"

for h in 39 41 42; do
  echo "--- h=$h sigma+11 ---" | tee -a "$LOG"
  for t in 1 2 3; do
    SAB_SQ_H=$h SAB_SQ_SIGMA_SHIFT=11 timeout 300 ./probe_fin 2>/dev/null \
      | grep -E "bootstrap:|noise|gate" \
      | sed "s/^/[h=$h sig+11 r$t] /" >> "$LOG" 2>&1
  done
done

# ═══════════════════════════════════════════════════
# PART 2: r-lane at recommended h (41) with sigma+11
# ═══════════════════════════════════════════════════
if [ -x ./probe_fin_rlane ]; then
  echo "=== PART 2: r-lane h=41 sigma+11 $(date) ===" | tee -a "$LOG"
  for r in 1 4; do
    echo "--- r=$r h=41 sigma+11 ---" | tee -a "$LOG"
    for t in 1 2 3; do
      SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=41 \
        SAB_SQ_SIGMA_SHIFT=11 SAB_PVW_SQ_REPS=3 \
        timeout 600 ./probe_fin_rlane 2>/dev/null | grep -E "TIMING|r_prec" \
        | sed "s/^/[rlane r=$r h=41 sig+11 t$t] /" >> "$LOG" 2>&1
    done
  done

  # Also at h=42 for comparison with existing data
  for r in 4; do
    echo "--- r=$r h=42 sigma+11 ---" | tee -a "$LOG"
    for t in 1 2 3; do
      SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=42 \
        SAB_SQ_SIGMA_SHIFT=11 SAB_PVW_SQ_REPS=3 \
        timeout 600 ./probe_fin_rlane 2>/dev/null | grep -E "TIMING|r_prec" \
        | sed "s/^/[rlane r=$r h=42 sig+11 t$t] /" >> "$LOG" 2>&1
    done
  done
fi

# ═══════════════════════════════════════════════════
# PART 3: Scalar baseline (sigma+0) at h=39 for reference
# ═══════════════════════════════════════════════════
echo "=== PART 3: Baseline h=39 sigma+0 $(date) ===" | tee -a "$LOG"
for t in 1 2 3; do
  SAB_SQ_H=39 SAB_SQ_SIGMA_SHIFT=0 timeout 300 ./probe_fin 2>/dev/null \
    | grep -E "bootstrap:|noise|gate" \
    | sed "s/^/[h=39 sig+0 r$t] /" >> "$LOG" 2>&1
done

echo "=== FINAL BENCH DONE $(date) ===" | tee -a "$LOG"
