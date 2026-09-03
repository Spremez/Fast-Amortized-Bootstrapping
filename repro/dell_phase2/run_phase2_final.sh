#!/usr/bin/env bash
# Phase 2 (dell): full fair benchmark under the FINAL security-corrected
# parameters (FINAL_H / FINAL_SIG set by the E4 decision). Same-machine,
# same-session, load-gated (<10) per case. Covers: scalar 2x2, r-lane x
# {stock,SQ,pathA} x r={2,4}, r-scaling {2,4,6,8}, same-session scalar
# anchors (vs 686 x r), A0 reference (39,+0), cross-machine calibration
# (41,+11), and the postops capacity curve.
set -uo pipefail
ROOT="$HOME/spz/dell-final-bench"
cd "$ROOT" || exit 1
OUT="$ROOT/repro_dell_phase2"
LOG="$OUT/run.log"
mkdir -p "$OUT"
FINAL_H="${FINAL_H:-42}"
FINAL_SIG="${FINAL_SIG:-0}"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){
  for i in $(seq 90); do
    cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)
    [ "$cur" -lt 10 ] && return 0
    sleep 60
  done
  log "WARN: no quiet<10 window (load=$(cat /proc/loadavg))"
}

log "=== PHASE2 on dell: FINAL h=$FINAL_H sig+$FINAL_SIG ==="
log "cpu=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-)"

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

scalar(){ # $1=h $2=sig $3=tag $4=reps
  for t in 1 2 3; do
    wait_quiet
    SAB_SQ_H=$1 SAB_SQ_SIGMA_SHIFT=$2 timeout 900 ./probe_sq.exe 2>/dev/null \
      | grep -E "bootstrap:|noise:|gate:" | sed "s/^/[scalar $3 t$t] /" | tee -a "$LOG"
    log "scalar $3 t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
}
rl(){ # $1=bin $2=r $3=h $4=sig $5=tag $6=trials
  for t in $(seq 1 "$6"); do
    wait_quiet
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$2 SAB_SQ_H=$3 SAB_SQ_SIGMA_SHIFT=$4 SAB_PVW_SQ_REPS=3 \
      timeout 3600 ./$1 2>/dev/null | grep -E "TIMING|timing r=|r_prec" \
      | sed "s/^/[$1 $5 t$t] /" | tee -a "$LOG"
    log "case $1 $5 t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
}

log "--- 1. scalar FINAL (h=$FINAL_H sig+$FINAL_SIG) x3 ---"
scalar "$FINAL_H" "$FINAL_SIG" "FINAL" 3
log "--- 2. scalar A0 reference (39,+0) x3 ---"
scalar 39 0 "A0" 3
log "--- 3. scalar cross-machine calibration (41,+11) x3 ---"
scalar 41 11 "CAL41" 3

log "--- 4. r-lane FINAL r={2,4} x {stock,pathA} ---"
for r in 2 4; do
  rl probe_rl_stock "$r" "$FINAL_H" "$FINAL_SIG" "FINAL-r$r" 2
  rl probe_rl_pathA "$r" "$FINAL_H" "$FINAL_SIG" "FINAL-r$r" 2
done
log "--- 5. r-scaling r={6,8} ---"
for r in 6 8; do
  rl probe_rl_stock "$r" "$FINAL_H" "$FINAL_SIG" "FINAL-r$r" 2
  rl probe_rl_pathA "$r" "$FINAL_H" "$FINAL_SIG" "FINAL-r$r" 2
done
log "--- 6. capacity curve (postops, FINAL) ---"
for psig in 25 30; do
  wait_quiet
  SAB_SQ_H=$FINAL_H SAB_SQ_SIGMA_SHIFT=$FINAL_SIG SAB_SQ_POSTOPS=8 SAB_SQ_POST_SIG=$psig \
    timeout 1800 ./probe_sq.exe 2>/dev/null | grep -E "noise:|postop" \
    | sed "s/^/[postops sig=$psig] /" | tee -a "$LOG"
done
log "=== PHASE2 COMPLETE ==="
