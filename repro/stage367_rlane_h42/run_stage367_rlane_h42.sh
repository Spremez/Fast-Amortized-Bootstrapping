#!/usr/bin/env bash
# Stage367: close the r-lane h=42 gap. E1 promoted h=42@t7 to the recommended
# point (T3'=133.5); scalar h=42 data exists, r-lane does not.
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage367_rlane_h42"
LOG="$OUT/run.log"
mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){
  for i in $(seq 60); do
    cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)
    [ "$cur" -lt 25 ] && return 0
    sleep 60
  done
}

COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
make -B $COMMON probe_sq.exe -j32 > "$OUT/build_base.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BASE BUILD FAIL"; exit 1; }
FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
PATHA="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_AVX512_SUB_DECOMP -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST"
gcc $FLAGS -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_dense.o 2>> "$OUT/build_stock.log"
gcc $FLAGS -c src/sab_pvw.c -o build_fin/sab_pvw_stock.o 2>> "$OUT/build_stock.log"
OBJS=$(ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' ')
gcc $FLAGS src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_dense.o build_fin/sab_pvw_stock.o $OBJS -lm -o probe_rl_stock 2>> "$OUT/build_stock.log"
gcc $FLAGS $PATHA -c src/sab_pvw.c -o build_fin/sab_pvw_pathA.o 2>> "$OUT/build_pathA.log"
gcc $FLAGS $PATHA -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_pathA.o 2>> "$OUT/build_pathA.log"
OBJA=$(ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' ')
gcc $FLAGS $PATHA src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/sab_pvw_pathA.o build_fin/mattrgsw_pathA.o $OBJA -lm -o probe_rl_pathA 2>> "$OUT/build_pathA.log"
[ -x ./probe_rl_stock ] && [ -x ./probe_rl_pathA ] && log "probes BUILT" || { log "BUILD FAIL"; exit 1; }

for bin in probe_rl_stock probe_rl_pathA; do
  for t in 1 2; do
    wait_quiet
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=4 SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=11 SAB_PVW_SQ_REPS=3 \
      timeout 1800 ./$bin 2>/dev/null | grep -E "TIMING|timing r=|r_prec" \
      | sed "s/^/[$bin h=42 sig+11 t$t] /" | tee -a "$LOG"
    log "case $bin t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done
log "=== STAGE367 COMPLETE ==="
