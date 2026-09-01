#!/usr/bin/env bash
# Stage363: balance-tier parameter measurement (external joint-optimization
# framework, 2026-09-01). Direction: raise h (keep ORIGINAL sigma, i.e.
# original rho) instead of our sigma+11 branch -> maximizes noise headroom.
# Matrix: h=52 x rprec(B_gap) in {7 tight, 9 = N/4-loose} x {scalar, stock
# r-lane, pathA r-lane}, all sigma+0. Compare against h=41 sigma+11 rows.
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage363_balance_tier_h52"
LOG="$OUT/run.log"
mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

wait_quiet(){
  for i in $(seq 60); do
    cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)
    [ "$cur" -lt 25 ] && return 0
    sleep 60
  done
  log "WARN: no quiet window (load=$(cat /proc/loadavg))"
}

log "=== STAGE363 balance tier h=52 sigma+0 ==="

# rebuild with patched probe (SAB_SQ_RPREC env)
COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
make -B $COMMON probe_sq.exe -j32 > "$OUT/build_base.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BASE BUILD FAIL"; exit 1; }
FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
PATHA="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_AVX512_SUB_DECOMP -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST"
gcc $FLAGS -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_dense.o 2>> "$OUT/build_stock.log"
gcc $FLAGS -c src/sab_pvw.c -o build_fin/sab_pvw_stock.o 2>> "$OUT/build_stock.log"
OBJS=$(ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' ')
gcc $FLAGS src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_dense.o build_fin/sab_pvw_stock.o $OBJS -lm -o probe_rl_stock 2>> "$OUT/build_stock.log"
[ -x ./probe_rl_stock ] && log "stock probe BUILT" || { log "stock BUILD FAIL"; exit 1; }
gcc $FLAGS $PATHA -c src/sab_pvw.c -o build_fin/sab_pvw_pathA.o 2>> "$OUT/build_pathA.log"
gcc $FLAGS $PATHA -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_pathA.o 2>> "$OUT/build_pathA.log"
OBJA=$(ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' ')
gcc $FLAGS $PATHA src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/sab_pvw_pathA.o build_fin/mattrgsw_pathA.o $OBJA -lm -o probe_rl_pathA 2>> "$OUT/build_pathA.log"
[ -x ./probe_rl_pathA ] && log "pathA probe BUILT" || { log "pathA BUILD FAIL"; exit 1; }

# scalar: h=52 x rprec {7,9}, sigma+0 (noise readout is the key output)
for rp in 7 9; do
  for t in 1 2; do
    wait_quiet
    SAB_SQ_H=52 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_RPREC=$rp timeout 900 ./probe_sq.exe 2>/dev/null \
      | grep -E "bootstrap:|noise|gate|distance|r_prec|Input key" \
      | sed "s/^/[scalar h=52 sig+0 rp=$rp t$t] /" | tee -a "$LOG"
    log "scalar rp=$rp t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done

# r-lane: h=52 x rprec {7,9} x {stock, pathA}, r=4
for rp in 7 9; do
  for bin in probe_rl_stock probe_rl_pathA; do
    for t in 1 2; do
      wait_quiet
      SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=4 SAB_SQ_H=52 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_RPREC=$rp SAB_PVW_SQ_REPS=3 \
        timeout 2400 ./$bin 2>/dev/null | grep -E "TIMING|timing r=|r_prec" \
        | sed "s/^/[$bin h=52 sig+0 rp=$rp t$t] /" | tee -a "$LOG"
      log "case $bin rp=$rp t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
    done
  done
done
log "=== STAGE363 COMPLETE ==="
