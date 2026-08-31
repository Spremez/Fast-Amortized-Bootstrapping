#!/usr/bin/env bash
# Stage358: Path A (stage355 fusion flags) under security-corrected sigma+11.
# Question: do the 7 fusion flags pass gates at sigma+11, and what is the
# Path-A factor under the identical probe protocol (same machine, same
# binary structure, back-to-back with the stock anchor) as rlane_final_v2?
#
# Note: in probe_pvw_sq.c the arm labelled "stock=" calls sab_pvw_* ; with
# this build's PATHA defines that arm IS Path A. The "sq=" arm is unaffected
# (sab_pvw_sq.c #undefs all SAB_PVW_* fusion flags).
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage358_pathA_sigma11"
LOG="$OUT/run.log"
mkdir -p "$OUT"

log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

log "=== STAGE358 PathA x sigma === host=$(hostname) nproc=$(nproc)"
log "load_at_start=$(cat /proc/loadavg)"

COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"

log "base build (no SAB_PVW flags)"
make -B $COMMON probe_sq.exe -j32 > "$OUT/build_base.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BASE BUILD FAIL"; exit 1; }
log "base build OK"

FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
PATHA="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_AVX512_SUB_DECOMP -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST"

log "compile stock r-lane objects"
gcc $FLAGS -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_dense.o 2>> "$OUT/build_stock.log"
gcc $FLAGS -c src/sab_pvw.c -o build_fin/sab_pvw_stock.o 2>> "$OUT/build_stock.log"
OBJS=$(ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' ')
gcc $FLAGS src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_dense.o build_fin/sab_pvw_stock.o $OBJS -lm -o probe_rl_stock 2>> "$OUT/build_stock.log"
[ -x ./probe_rl_stock ] && log "stock probe BUILT" || { log "stock probe BUILD FAIL"; exit 1; }

log "compile Path A objects (7 fusion flags)"
gcc $FLAGS $PATHA -c src/sab_pvw.c -o build_fin/sab_pvw_pathA.o 2>> "$OUT/build_pathA.log"
gcc $FLAGS $PATHA -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_pathA.o 2>> "$OUT/build_pathA.log"
OBJA=$(ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' ')
gcc $FLAGS $PATHA src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/sab_pvw_pathA.o build_fin/mattrgsw_pathA.o $OBJA -lm -o probe_rl_pathA 2>> "$OUT/build_pathA.log"
[ -x ./probe_rl_pathA ] && log "pathA probe BUILT" || { log "pathA probe BUILD FAIL"; exit 1; }

log "toy gates"
timeout 300 ./probe_rl_stock 2>/dev/null | grep -E "gate|mismatch|done" | tail -6 | tee -a "$LOG"
timeout 300 ./probe_rl_pathA 2>/dev/null | grep -E "gate|mismatch|done" | tail -6 | tee -a "$LOG"

run_case() { # $1=bin $2=sigma $3=h
  local bin="$1" sig="$2" h="$3"
  for t in 1 2 3; do
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=4 SAB_SQ_H=$h SAB_SQ_SIGMA_SHIFT=$sig SAB_PVW_SQ_REPS=3 \
      timeout 1800 ./$bin 2>/dev/null | grep -E "TIMING|r_prec|timing r=" \
      | sed "s/^/[$bin sig+$sig h=$h r=4 t$t] /" | tee -a "$LOG"
    log "case $bin sig+$sig h=$h trial$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
}

# Configs ordered by evidence value; stock/pathA back-to-back per config to
# control for shared-machine load drift.
for cfg in "11 41" "11 39" "0 39"; do
  set -- $cfg; sig="$1"; h="$2"
  log "--- config sigma+$sig h=$h r=4 ---"
  run_case probe_rl_stock "$sig" "$h"
  run_case probe_rl_pathA "$sig" "$h"
done

log "=== STAGE358 COMPLETE ==="
