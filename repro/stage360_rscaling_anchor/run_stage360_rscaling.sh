#!/usr/bin/env bash
# Stage360: (A) same-session scalar anchor at h=41 sigma+11 (for the clean
# "vs 686 x r" column), (B) r-scaling r={2,6,8} for stock r-lane vs Path A
# at h=41 sigma+11 -- closes the body-linearity question C_mat(r)/(1+r)
# with measurements instead of assumptions.
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage360_rscaling_anchor"
LOG="$OUT/run.log"
mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
log "=== STAGE360 r-scaling + scalar anchor === load=$(cat /proc/loadavg)"

# stage359 make-cleaned the build dir; rebuild probes per stage358 recipe
COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
log "rebuild base objects"
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

# (A) same-session scalar anchor: SQ + stock scalar back-to-back, h=41 sig+11
log "--- A: scalar anchor h=41 sigma+11 (9 runs) ---"
for t in 1 2 3; do
  SAB_SQ_H=41 SAB_SQ_SIGMA_SHIFT=11 timeout 600 ./probe_sq.exe 2>/dev/null \
    | grep -E "bootstrap:|noise|gate" | sed "s/^/[scalar h=41 sig+11 t$t] /" | tee -a "$LOG"
done

# (B) r-scaling: stock vs pathA back-to-back per r
run_case(){ # $1=bin $2=r
  local bin="$1" r="$2"
  for t in 1 2; do
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=41 SAB_SQ_SIGMA_SHIFT=11 SAB_PVW_SQ_REPS=3 \
      timeout 2400 ./$bin 2>/dev/null | grep -E "TIMING|r_prec|timing r=" \
      | sed "s/^/[$bin h=41 sig+11 r=$r t$t] /" | tee -a "$LOG"
    log "case $bin r=$r trial$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
}
for r in 2 6 8; do
  log "--- B: r=$r h=41 sigma+11 ---"
  run_case probe_rl_stock "$r"
  run_case probe_rl_pathA "$r"
done
log "=== STAGE360 COMPLETE ==="
