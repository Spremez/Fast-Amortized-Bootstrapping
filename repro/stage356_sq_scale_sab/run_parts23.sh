#!/usr/bin/env bash
# Fix Parts 2-3: use build_pq (has all PVW objects) for the r-lane probe
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=repro/stage356_sq_scale_sab
LOG=$OUT/parts23.log
: > "$LOG"

echo "=== PART 2: R-LANE $(date) ===" | tee -a "$LOG"

# Compile mattrgsw with the dense export + r-lane probe using build_pq objects
FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"

gcc $FLAGS -c src/mosfhet/src/mattrgsw.c -o build_pq/mattrgsw_dense.o 2>&1 | grep -E ' error' | head -3
OBJS=$(ls build_pq/*.o | grep -v 'main\.o' | grep -v mattrgsw | grep -v probe_sq | grep -v mattrgsw_dense | tr '\n' ' ')
gcc $FLAGS src/sab_pvw_sq.c src/probe_pvw_sq.c build_pq/mattrgsw_dense.o $OBJS -lm -o probe_p23 2>&1 | grep -E ' error|undefined' | head -5
[ -x ./probe_p23 ] || { echo "BUILD FAIL" | tee -a "$LOG"; exit 1; }
echo "r-lane probe built" | tee -a "$LOG"

# r-lane at SET_2_3_2048 for r=1,2,4 × {orig h=39, fair h=42}
for r in 1 2 4; do
  for h in 39 42; do
    sec="ORIG"; [ "$h" = "42" ] && sec="FAIR"
    echo "--- r=$r h=$h $sec ---" | tee -a "$LOG"
    for t in 1 2 3; do
      SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=$h SAB_PVW_SQ_REPS=3 \
        timeout 600 ./probe_p23 2>/dev/null | grep -E "TIMING|r_prec" \
        | sed "s/^/[r=$r h=$h $sec t$t] /" >> "$LOG" 2>&1
    done
  done
done

echo "=== PART 3: HARDENING $(date) ===" | tee -a "$LOG"
# Scalar probe with sigma+15 (uses build_ec)
SQKS_AUT_L=4 SQKS_AUT_BG=16 SAB_SQ_SIGMA_SHIFT=15 SAB_SQ_H=42 \
  timeout 300 ./probe_ec 2>/dev/null | grep -E "bootstrap:|noise|gate" \
  | sed "s/^/[HARDEN sigma+15 h=42] /" >> "$LOG" 2>&1

echo "=== PARTS 2-3 DONE $(date) ===" | tee -a "$LOG"
