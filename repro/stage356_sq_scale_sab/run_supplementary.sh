#!/usr/bin/env bash
# stage360 FINAL SUPPLEMENTARY BENCHMARK
# Fills the last two gaps + key size + failure probability + RSS
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=repro/stage356_sq_scale_sab
LOG=$OUT/supplementary.log
: > "$LOG"

COMMON="BUILD_DIR=./build_sup FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native"

# ═══════════════════════════════════════════════════════════════
# GAP 1: Fully-optimized stock r-lane (stage355 flag set)
# ═══════════════════════════════════════════════════════════════
echo "=== GAP 1: Fully-optimized stock r-lane $(date) ===" | tee -a "$LOG"

OPT_FLAGS="MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true ENABLE_PVW_TMLWE=true"

make -B $COMMON $OPT_FLAGS main -j32 > "$OUT/sup_build_opt.log" 2>&1
echo "optimized build exit=$?" | tee -a "$LOG"

# Run the optimized stock r-lane at r=4, h=42 (fair)
# The main binary's test_sab_pvw_target_bench measures r-lane vs repeated scalar
for t in 1 2 3; do
  /usr/bin/time -v timeout 600 ./main 2>&1 \
    | grep -E "bootstrap:|speedup|Speedup|gate|noise|Maximum resident" \
    | sed "s/^/[OPT-RLANE t$t] /" >> "$LOG" 2>&1
done

# ═══════════════════════════════════════════════════════════════
# GAP 2: SQ r-lane + non-decomposition optimization flags
# ═══════════════════════════════════════════════════════════════
echo "=== GAP 2: SQ r-lane + non-decomp flags $(date) ===" | tee -a "$LOG"

# Build SQ r-lane with only the flags that don't touch decomposition
# (SQ already eliminates decomposition; these flags optimize inverse FFT / scheduling)
SQ_FLAGS="SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_DUAL_SUB_CMUX=true ENABLE_PVW_TMLWE=true"

# Note: BACKEND_FROM_DFT_ADD fuses the inverse FFT output with addition
#       DUAL_SUB_CMUX shares subtraction inputs
#       These are compatible with SQ's fused rescale+add epilogue

make -B $COMMON $SQ_FLAGS SAB_SQ_Q=16 probe_sq.exe -j32 > "$OUT/sup_build_sq_flags.log" 2>&1

# Build the r-lane probe with these flags
OBJS=$(ls build_sup/*.o | grep -v 'main\.o' | grep -v probe_sq | tr '\n' ' ')
gcc -O2 -g -Iinclude -Isrc/mosfhet/include -march=native \
    -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DBINARY \
    -DSAB_PVW_BACKEND_FROM_DFT_ADD \
    src/sab_pvw_sq.c src/probe_pvw_sq.c src/mosfhet/src/mattrgsw.c \
    $OBJS -lm -o probe_sq_rlane_opt 2>&1 | grep -E ' error' | head -3
[ -x ./probe_sq_rlane_opt ] && echo "SQ+flags rlane probe built" | tee -a "$LOG" \
  || echo "SQ+flags rlane BUILD FAIL" | tee -a "$LOG"

if [ -x ./probe_sq_rlane_opt ]; then
  for r in 1 4; do
    for h in 39 42; do
      sec="ORIG"; [ "$h" = "42" ] && sec="FAIR"
      for t in 1 2 3; do
        SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=$h SAB_PVW_SQ_REPS=3 \
          timeout 600 ./probe_sq_rlane_opt 2>/dev/null | grep -E "TIMING|r_prec" \
          | sed "s/^/[SQ+flags r=$r h=$h $sec t$t] /" >> "$LOG" 2>&1
      done
    done
  done
fi

# ═══════════════════════════════════════════════════════════════
# GAP 3: Key size measurement
# ═══════════════════════════════════════════════════════════════
echo "=== GAP 3: Key sizes $(date) ===" | tee -a "$LOG"

# Build plain probe (no optimization flags for clean measurement)
make -B $COMMON ENABLE_PVW_TMLWE=true SAB_SQ_Q=16 probe_sq.exe -j32 > "$OUT/sup_build_keys.log" 2>&1
cp probe_sq.exe probe_keys

# Run with /usr/bin/time to get RSS, and add a key size print
# Key size = selectors + aut KS + packing KS + HW KS
/usr/bin/time -v timeout 300 ./probe_keys 2>&1 \
  | grep -E "Maximum resident|bootstrap:|gate" \
  | sed "s/^/[KEYS SQ h=42] /" >> "$LOG" 2>&1

SAB_SQ_H=39 /usr/bin/time -v timeout 300 ./probe_keys 2>&1 \
  | grep -E "Maximum resident|bootstrap:|gate" \
  | sed "s/^/[KEYS SQ h=39] /" >> "$LOG" 2>&1

# ═══════════════════════════════════════════════════════════════
# GAP 4: Failure probability (100 trials)
# ═══════════════════════════════════════════════════════════════
echo "=== GAP 4: Failure probability $(date) ===" | tee -a "$LOG"

FAIL=0
TOTAL=0
for t in $(seq 1 50); do
  result=$(timeout 300 ./probe_keys 2>/dev/null | grep "gate:")
  TOTAL=$((TOTAL + 1))
  if echo "$result" | grep -q "Fail"; then
    FAIL=$((FAIL + 1))
    echo "[FAILPROB trial=$t] FAIL" >> "$LOG"
  fi
done
echo "Failure probability: $FAIL / $TOTAL trials" | tee -a "$LOG"

echo "=== SUPPLEMENTARY DONE $(date) ===" | tee -a "$LOG"
