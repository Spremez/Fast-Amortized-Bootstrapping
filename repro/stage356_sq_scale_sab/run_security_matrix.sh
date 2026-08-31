#!/usr/bin/env bash
# stage361 COMPLETE SECURITY-AWARE BENCHMARK MATRIX
# Phase 1: stock viability under σ gradient
# Phase 2: Path A (optimized r-lane) under security correction
# Phase 3: SQ at all security levels
# Phase 4: True 128-bit comprehensive comparison
# Phase 5: Path A+B fusion attempts
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=repro/stage356_sq_scale_sab
LOG=$OUT/security_matrix.log
: > "$LOG"

COMMON="BUILD_DIR=./build_sec FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"

# Build the scalar probe
echo "=== BUILD $(date) ===" | tee -a "$LOG"
make -B $COMMON ENABLE_PVW_TMLWE=true probe_sq.exe -j32 > "$OUT/sec_build.log" 2>&1
[ -x ./probe_sq.exe ] || { echo "BUILD FAIL" | tee -a "$LOG"; exit 1; }
cp probe_sq.exe probe_sec
echo "build ok" | tee -a "$LOG"

# ═════════════════════════════════════════════════════════════
# PHASE 1: Stock σ gradient (scalar, h=42, Bg=23 default)
# ═════════════════════════════════════════════════════════════
echo "=== PHASE 1: Stock sigma gradient $(date) ===" | tee -a "$LOG"

run_sigma () { # sigma_shift label
  local ss=$1 label=$2
  echo "--- sigma+$ss ($label) h=42 $(date) ---" | tee -a "$LOG"
  for t in 1 2 3; do
    SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=$ss timeout 300 ./probe_sec 2>/dev/null \
      | grep -E "bootstrap:|noise|gate" \
      | sed "s/^/[sigma+$ss h=42 $label r$t] /" >> "$LOG" 2>&1
  done
}

run_sigma 0  "original"
run_sigma 1  "B1-actual"
run_sigma 6  "B4-actual"
run_sigma 11 "tight-rotational"     # ← KEY EXPERIMENT
run_sigma 15 "conservative"

# ═════════════════════════════════════════════════════════════
# PHASE 1b: Stock with Bg adjustment (if σ+11 fails)
# ═════════════════════════════════════════════════════════════
# Check if σ+11 passed
SIG11_PASS=$(grep "sigma+11.*gate: Pass" "$LOG" | wc -l)
if [ "$SIG11_PASS" -eq 0 ]; then
  echo "--- stock FAILED at sigma+11, trying Bg=16 ---" | tee -a "$LOG"
  # SQKS_AUT_BG adjusts the aut-KS gadget base for SQ only
  # For stock, we need to modify the KS key generation
  # This requires a different build — document the limitation
  echo "[NOTE] Stock Bg adjustment requires separate build (sab.h change)" | tee -a "$LOG"
  echo "[NOTE] SQ already handles this via SQKS_AUT_BG=16" | tee -a "$LOG"

  # Run SQ with refined KS to show it works
  echo "--- SQ with refined KS (SQKS_AUT_BG=16) at sigma+11 ---" | tee -a "$LOG"
  for t in 1 2 3; do
    SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=11 SQKS_AUT_L=4 SQKS_AUT_BG=16 \
      timeout 300 ./probe_sec 2>/dev/null \
      | grep -E "bootstrap:|noise|gate" \
      | sed "s/^/[sigma+11 SQ+refinedKS r$t] /" >> "$LOG" 2>&1
  done
fi

# ═════════════════════════════════════════════════════════════
# PHASE 2: Optimized r-lane under security correction
# ═════════════════════════════════════════════════════════════
echo "=== PHASE 2: Optimized r-lane security $(date) ===" | tee -a "$LOG"

# Build optimized stock r-lane with σ+11
# The optimized build needs the stage355 flags
OPT_FLAGS="MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true ENABLE_PVW_TMLWE=true"

# Note: running ./main with optimized flags runs test_sab (scalar)
# For r-lane we need the SAB_PVW_TARGET_TEST mode
echo "--- optimized stock r-lane at sigma+11 ---" | tee -a "$LOG"
echo "[NOTE] Optimized r-lane with sigma correction requires SAB_PVW mode" | tee -a "$LOG"
echo "[NOTE] Using stage355 data for sigma+0; sigma+11 r-lane TBD" | tee -a "$LOG"

# SQ r-lane at sigma+11
echo "--- SQ r-lane at sigma+11 ---" | tee -a "$LOG"
OBJS=$(ls build_sec/*.o | grep -v 'main\.o' | grep -v probe_sq | tr '\n' ' ')
gcc -O2 -g -Iinclude -Isrc/mosfhet/include -march=native \
    -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DBINARY \
    src/sab_pvw_sq.c src/probe_pvw_sq.c src/mosfhet/src/mattrgsw.c \
    $OBJS -lm -o probe_sec_rlane 2>&1 | grep -cE ' error'
if [ -x ./probe_sec_rlane ]; then
  for r in 1 4; do
    echo "--- SQ r-lane r=$r sigma+11 ---" | tee -a "$LOG"
    for t in 1 2; do
      SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=42 \
        SAB_SQ_SIGMA_SHIFT=11 SQKS_AUT_L=4 SQKS_AUT_BG=16 SAB_PVW_SQ_REPS=3 \
        timeout 600 ./probe_sec_rlane 2>/dev/null | grep -E "TIMING|r_prec" \
        | sed "s/^/[SQ-rlane r=$r sig+11 t$t] /" >> "$LOG" 2>&1
    done
  done
else
  echo "SQ r-lane BUILD FAIL" | tee -a "$LOG"
fi

# ═════════════════════════════════════════════════════════════
# PHASE 3: SQ σ gradient (confirmation)
# ═════════════════════════════════════════════════════════════
echo "=== PHASE 3: SQ sigma gradient with refined KS $(date) ===" | tee -a "$LOG"

run_sq_sigma () { # sigma_shift
  local ss=$1
  echo "--- SQ refined sigma+$ss ---" | tee -a "$LOG"
  for t in 1 2 3; do
    SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=$ss SQKS_AUT_L=4 SQKS_AUT_BG=16 \
      timeout 300 ./probe_sec 2>/dev/null \
      | grep -E "bootstrap:|noise|gate" \
      | sed "s/^/[SQ-refined sigma+$ss r$t] /" >> "$LOG" 2>&1
  done
}

run_sq_sigma 1
run_sq_sigma 6
run_sq_sigma 11
run_sq_sigma 15

echo "=== SECURITY MATRIX DONE $(date) ===" | tee -a "$LOG"
