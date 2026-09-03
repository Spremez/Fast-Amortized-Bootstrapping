#!/usr/bin/env bash
# Stage369: coverage completion per user directive 2026-09-03.
#  A) precision sweep @2048: p=7, p=9 (scalar, FINAL h=42 sigma+0)   [multi-p]
#  B) 4096 completion: pathA + sqmat r-lane r=4; scalar p=5           [multi-N lanes]
#  C) 8192 family (h=34, t=10): scalar p=3 + r-lane r=4 stock/pathA   [multi-N]
#  D) r-fine sweep @2048 p=3: r=1..8 stock+pathA (marginal lane cost) [amortization]
#  E) BSK option-A support: sigma_G=2^-49 noise+gate (shift=+1)       [decision]
#  F) main-table scale-up: FINAL scalar p=3 x6 trials                 [sample size]
# All load-gated (<10). All FINAL params.
set -uo pipefail
ROOT="$HOME/spz/dell-final-bench"
cd "$ROOT" || exit 1
OUT="$ROOT/repro_stage369"; LOG="$OUT/run.log"; mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){ for i in $(seq 90); do cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); [ "$cur" -lt 10 ] && return 0; sleep 60; done; log "WARN no-quiet load=$(cat /proc/loadavg)"; }
COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
PATHA="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DMAT_TRGSW_AVX512_SUB_DECOMP -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST"
MATONLY="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_SUB_DECOMP -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT"
log "=== STAGE369 coverage completion ==="
make -B $COMMON probe_sq.exe -j32 > "$OUT/build_base.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BASE BUILD FAIL"; exit 1; }
log "probe_sq.exe BUILT"
if [ ! -x ./probe_rl_stock ] || [ ! -x ./probe_rl_pathA ] || [ ! -x ./probe_rl_sqmat ]; then
  gcc $FLAGS -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_plain.o 2>> "$OUT/b1.log"
  gcc $FLAGS -c src/sab_pvw.c -o build_fin/sab_pvw_plain.o 2>> "$OUT/b1.log"
  gcc $FLAGS $MATONLY -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_matonly.o 2>> "$OUT/b2.log"
  gcc $FLAGS $PATHA -c src/sab_pvw.c -o build_fin/sab_pvw_pathA.o 2>> "$OUT/b3.log"
  gcc $FLAGS $PATHA -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_pathA.o 2>> "$OUT/b3.log"
  OBJS(){ ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' '; }
  gcc $FLAGS src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_plain.o build_fin/sab_pvw_plain.o $(OBJS) -lm -o probe_rl_stock 2>> "$OUT/b1.log"
  gcc $FLAGS $MATONLY src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_matonly.o build_fin/sab_pvw_plain.o $(OBJS) -lm -o probe_rl_sqmat 2>> "$OUT/b2.log"
  gcc $FLAGS $PATHA src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_pathA.o build_fin/sab_pvw_pathA.o $(OBJS) -lm -o probe_rl_pathA 2>> "$OUT/b3.log"
fi
for b in probe_rl_stock probe_rl_sqmat probe_rl_pathA; do [ -x ./$b ] && log "$b OK" || { log "$b MISSING-FAIL"; exit 1; }; done

log "--- A) precision sweep 2048: p=7, p=9 (scalar) ---"
for P in 7 9; do
  for t in 1 2 3; do
    wait_quiet
    SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_N=2048 SAB_SQ_OUTN=2048 SAB_SQ_P=$P SAB_SQ_SIG_IN=$((P+12)) \
      timeout 1800 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
      | sed "s/^/[p$P h=42 t$t] /" | tee -a "$LOG" || log "p$P t$t FAILED/EMPTY"
    log "A: p$P t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done

log "--- B) 4096 completion: pathA+sqmat r-lane r=4, scalar p=5 ---"
for b in probe_rl_pathA probe_rl_sqmat; do
  for t in 1 2; do
    wait_quiet
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=4 SAB_PVW_SQ_N=4096 SAB_PVW_SQ_OUTN=2048 SAB_PVW_SQ_PREC=3 \
      SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_RPREC=8 SAB_PVW_SQ_REPS=3 \
      timeout 3600 ./$b 2>/dev/null | grep -E "TIMING|r_prec|keygen|attempts" \
      | sed "s/^/[4096-rlane $b t$t] /" | tee -a "$LOG" || log "4096 $b t$t FAILED/EMPTY"
    log "B: 4096 $b t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done
for t in 1 2; do
  wait_quiet
  SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_N=4096 SAB_SQ_OUTN=2048 SAB_SQ_P=5 SAB_SQ_SIG_IN=17 SAB_SQ_RPREC=8 \
    timeout 3600 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
    | sed "s/^/[4096 p5 h=42 t$t] /" | tee -a "$LOG" || log "4096 p5 t$t FAILED/EMPTY"
  log "B: 4096 p5 t$t done"
done

log "--- C) 8192 family (h=34, t=10): scalar p=3 + r-lane r=4 ---"
for t in 1 2; do
  wait_quiet
  SAB_SQ_H=34 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_N=8192 SAB_SQ_OUTN=2048 SAB_SQ_P=3 SAB_SQ_SIG_IN=15 SAB_SQ_RPREC=10 \
    timeout 3600 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
    | sed "s/^/[8192 h=34 t$t] /" | tee -a "$LOG" || log "8192 scalar t$t FAILED/EMPTY"
  log "C: 8192 scalar t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
done
for b in probe_rl_stock probe_rl_pathA; do
  wait_quiet
  SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=4 SAB_PVW_SQ_N=8192 SAB_PVW_SQ_OUTN=2048 SAB_PVW_SQ_PREC=3 \
    SAB_SQ_H=34 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_RPREC=10 SAB_PVW_SQ_REPS=3 \
    timeout 3600 ./$b 2>/dev/null | grep -E "TIMING|r_prec|keygen|attempts" \
    | sed "s/^/[8192-rlane $b t1] /" | tee -a "$LOG" || log "8192 $b FAILED/EMPTY"
  log "C: 8192 rlane $b done load=$(cut -d' ' -f1 /proc/loadavg)"
done

log "--- D) r-fine sweep 2048 p=3 FINAL: r=1..8 stock+pathA (marginal lane) ---"
for r in 1 2 3 4 5 6 7 8; do
  for b in probe_rl_stock probe_rl_pathA; do
    wait_quiet
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_PVW_SQ_REPS=3 \
      timeout 3600 ./$b 2>/dev/null | grep -E "TIMING|r_prec" \
      | sed "s/^/[rfine $b r$r] /" | tee -a "$LOG" || log "rfine $b r$r FAILED/EMPTY"
    log "D: rfine $b r$r done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done

log "--- E) BSK option-A support: sigma_G=2^-49 (shift=+1) noise+gate ---"
for t in 1 2 3; do
  wait_quiet
  SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=1 SAB_SQ_N=2048 SAB_SQ_OUTN=2048 SAB_SQ_P=3 SAB_SQ_SIG_IN=15 \
    timeout 1800 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
    | sed "s/^/[BSKoptA sig49 t$t] /" | tee -a "$LOG" || log "BSKoptA t$t FAILED/EMPTY"
  log "E: BSKoptA t$t done"
done

log "--- F) main-table scale-up: FINAL scalar p=3 x6 ---"
for t in 1 2 3 4 5 6; do
  wait_quiet
  SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_N=2048 SAB_SQ_OUTN=2048 SAB_SQ_P=3 SAB_SQ_SIG_IN=15 \
    timeout 1800 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
    | sed "s/^/[FINAL-main t$t] /" | tee -a "$LOG" || log "main t$t FAILED/EMPTY"
  log "F: main t$t done"
done
log "=== STAGE369 COMPLETE ==="
