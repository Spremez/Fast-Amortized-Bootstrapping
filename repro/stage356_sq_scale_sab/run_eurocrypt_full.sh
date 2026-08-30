#!/usr/bin/env bash
# stage359 COMPREHENSIVE EUROCRYPT BENCHMARK
# Complete matrix: {all 10 sets} × {r=1 (scalar), r-lane 2/4} × {orig h, fair h} × {SQ, stock}
# Per-message and per-bit amortized costs, key sizes, gates, noise.
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=repro/stage356_sq_scale_sab
LOG=$OUT/eurocrypt_full.log
: > "$LOG"

COMMON="BUILD_DIR=./build_ec FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true ARCH_FLAGS=-march=native SAB_SQ_Q=16"

# ─── Part 1: scalar SQ vs stock (probe_sq) for all 10 sets ───
echo "=== PART 1: SCALAR (probe_sq) all sets $(date) ===" | tee -a "$LOG"
make -B $COMMON PARAM=SET_2_3_2048 probe_sq.exe -j32 > "$OUT/ec_build_sq.log" 2>&1
[ -x ./probe_sq.exe ] || { echo "BUILD FAIL probe_sq" | tee -a "$LOG"; exit 1; }
cp probe_sq.exe probe_ec

run_scalar () { # name n outn prec sig h686 hf
  local name=$1 n=$2 outn=$3 p=$4 sig=$5 h686=$6 hf=$7
  echo "--- $name n=$n p=$p ---" | tee -a "$LOG"
  for t in 1 2 3; do
    SAB_SQ_N=$n SAB_SQ_OUTN=$outn SAB_SQ_P=$p SAB_SQ_SIG_IN=$sig SAB_SQ_H=$h686 \
      timeout 300 ./probe_ec 2>/dev/null | grep -E "bootstrap:|noise|gate|r_prec" \
      | sed "s/^/[$name h=$h686 ORIG r$t] /" >> "$LOG" 2>&1
    SAB_SQ_N=$n SAB_SQ_OUTN=$outn SAB_SQ_P=$p SAB_SQ_SIG_IN=$sig SAB_SQ_H=$hf \
      timeout 300 ./probe_ec 2>/dev/null | grep -E "bootstrap:|noise|gate|r_prec" \
      | sed "s/^/[$name h=$hf FAIR r$t] /" >> "$LOG" 2>&1
  done
}

run_scalar SET_2_3_2048 2048 2048 3 15 39 42
run_scalar SET_4_5_2048 2048 2048 5 17 42 41
run_scalar SET_2_3_4096 4096 2048 3 15 32 36
run_scalar SET_4_5_4096 4096 2048 5 18 34 36
run_scalar SET_6_7_4096 4096 2048 7 21 33 36
run_scalar SET_8_9_4096 4096 8192 9 24 34 36
run_scalar SET_2_3_8192 8192 2048 3 15 25 32
run_scalar SET_4_5_8192 8192 2048 5 18 26 32
run_scalar SET_6_7_8192 8192 2048 7 21 27 32
run_scalar SET_8_9_8192 8192 8192 9 24 28 32

# ─── Part 2: r-lane SQ vs stock (probe_pvw_sq) at flagship sets ───
echo "=== PART 2: R-LANE (probe_pvw_sq) $(date) ===" | tee -a "$LOG"

# Build the r-lane probe
gcc -O2 -g -Iinclude -Isrc/mosfhet/include -march=native \
    -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DBINARY \
    src/sab_pvw_sq.c src/probe_pvw_sq.c \
    build_ec/mattrgsw.o $(ls build_ec/*.o | grep -v 'main\.o' | grep -v mattrgsw | grep -v probe_sq | tr '\n' ' ') \
    -lm -o probe_ec_rlane 2>&1 | grep -E ' error' | head -3
[ -x ./probe_ec_rlane ] || { echo "BUILD FAIL rlane" | tee -a "$LOG"; exit 1; }
echo "rlane probe built" | tee -a "$LOG"

# r-lane at SET_2_3_2048 for r=1,2,4
for r in 1 2 4; do
  for h in 39 42; do
    sec="ORIG"; [ "$h" = "42" ] && sec="FAIR"
    echo "--- r=$r h=$h $sec ---" | tee -a "$LOG"
    for t in 1 2 3; do
      SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=$h SAB_PVW_SQ_REPS=3 \
        timeout 600 ./probe_ec_rlane 2>/dev/null | grep -E "TIMING|r_prec" \
        | sed "s/^/[r=$r h=$h $sec t$t] /" >> "$LOG" 2>&1
    done
  done
done

# ─── Part 3: σ+15 hardening (flagship only) ───
echo "=== PART 3: HARDENING $(date) ===" | tee -a "$LOG"
SAB_SQ_H=42 SQKS_AUT_L=4 SQKS_AUT_BG=16 SAB_SQ_SIGMA_SHIFT=15 \
  timeout 300 ./probe_ec 2>/dev/null | grep -E "bootstrap:|noise|gate" \
  | sed "s/^/[HARDEN sigma+15 h=42] /" >> "$LOG" 2>&1

echo "=== EUROCRYPT FULL BENCHMARK DONE $(date) ===" | tee -a "$LOG"
