#!/usr/bin/env bash
# Stage371: BSK option-A landed default re-run (user-confirmed 2026-09-04).
# Default sigma_shift is now 1 in code (sigma_out = 2^-49), so this script
# deliberately NEVER sets SAB_SQ_SIGMA_SHIFT: every run must log
# sigma_shift=1 / 2^-49 from the committed default alone.
#  A) main-table scalar FINAL x6 (h=42, p=3, N=2048) SQ vs stock, noise+gate
#  B) r-lane r=4 x2 trials x {stock,sqmat,pathA} builds, N=2048 (in-build pairs)
#  C) multi-ring confirm x1: 4096 p5 (h=42,rprec=8); 8192 p3 (h=34,rprec=10)
# All load-gated (<10). All FINAL params otherwise.
set -uo pipefail
ROOT="$HOME/spz/dell-final-bench"
cd "$ROOT" || exit 1
OUT="$ROOT/repro_stage371"; LOG="$OUT/run.log"; mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){ for i in $(seq 90); do cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); [ "$cur" -lt 10 ] && return 0; sleep 60; done; log "WARN no-quiet load=$(cat /proc/loadavg)"; }
COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
PATHA="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DMAT_TRGSW_AVX512_SUB_DECOMP -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST"
MATONLY="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_SUB_DECOMP -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT"
log "=== STAGE371 BSK option-A default re-run (sigma_out default 2^-49) ==="
make -B $COMMON probe_sq.exe -j32 > "$OUT/build_base.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BASE BUILD FAIL"; exit 1; }
log "probe_sq.exe BUILT (recompiled with sigma_shift default 1)"
rm -f probe_rl_stock probe_rl_sqmat probe_rl_pathA
gcc $FLAGS -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_plain.o 2>> "$OUT/b1.log"
gcc $FLAGS -c src/sab_pvw.c -o build_fin/sab_pvw_plain.o 2>> "$OUT/b1.log"
gcc $FLAGS $MATONLY -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_matonly.o 2>> "$OUT/b2.log"
gcc $FLAGS $PATHA -c src/sab_pvw.c -o build_fin/sab_pvw_pathA.o 2>> "$OUT/b3.log"
gcc $FLAGS $PATHA -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_pathA.o 2>> "$OUT/b3.log"
OBJS(){ ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' '; }
gcc $FLAGS src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_plain.o build_fin/sab_pvw_plain.o $(OBJS) -lm -o probe_rl_stock 2>> "$OUT/b1.log"
gcc $FLAGS $MATONLY src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_matonly.o build_fin/sab_pvw_plain.o $(OBJS) -lm -o probe_rl_sqmat 2>> "$OUT/b2.log"
gcc $FLAGS $PATHA src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_pathA.o build_fin/sab_pvw_pathA.o $(OBJS) -lm -o probe_rl_pathA 2>> "$OUT/b3.log"
for b in probe_rl_stock probe_rl_sqmat probe_rl_pathA; do [ -x ./$b ] && log "$b OK" || { log "$b MISSING-FAIL"; exit 1; }; done

log "--- A) main-table scalar FINAL x6 (default sigma, expect shift=1 lines) ---"
for t in 1 2 3 4 5 6; do
  wait_quiet
  SAB_SQ_H=42 SAB_SQ_N=2048 SAB_SQ_OUTN=2048 SAB_SQ_P=3 SAB_SQ_SIG_IN=15 \
  timeout 1800 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:|2\^-4" \
  | sed "s/^/[optA-main t$t] /" | tee -a "$LOG" || log "A: main t$t FAILED/EMPTY"
  log "A: main t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
done

log "--- B) r-lane r=4 x2 x {stock,sqmat,pathA} (in-build pairs) ---"
for b in probe_rl_stock probe_rl_sqmat probe_rl_pathA; do
  for t in 1 2; do
    wait_quiet
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=4 SAB_PVW_SQ_N=2048 SAB_PVW_SQ_OUTN=2048 SAB_PVW_SQ_PREC=3 \
    SAB_SQ_H=42 SAB_PVW_SQ_REPS=3 \
    timeout 3600 ./$b 2>/dev/null | grep -E "TIMING|sigma_shift|r_prec|gate" \
    | sed "s/^/[optA-rlane $b t$t] /" | tee -a "$LOG" || log "B: $b t$t FAILED/EMPTY"
    log "B: $b t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done

log "--- C) multi-ring confirm x1 (default sigma) ---"
wait_quiet
SAB_SQ_H=42 SAB_SQ_N=4096 SAB_SQ_OUTN=2048 SAB_SQ_P=5 SAB_SQ_SIG_IN=17 SAB_SQ_RPREC=8 \
timeout 3600 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
| sed "s/^/[optA-4096 p5 h=42] /" | tee -a "$LOG" || log "C: 4096 FAILED/EMPTY"
log "C: 4096 done"
wait_quiet
SAB_SQ_H=34 SAB_SQ_N=8192 SAB_SQ_OUTN=2048 SAB_SQ_P=3 SAB_SQ_SIG_IN=15 SAB_SQ_RPREC=10 \
timeout 3600 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
| sed "s/^/[optA-8192 h=34] /" | tee -a "$LOG" || log "C: 8192 FAILED/EMPTY"
log "C: 8192 done"
log "=== STAGE371 COMPLETE ==="
