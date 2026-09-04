#!/usr/bin/env bash
# Stage373: component timing profile at FINAL params (h=42, sigma_G=2^-49 default).
# Purpose: calibrate T2 cost model (D/F/I/A shares inside MV-EP) + epilogue share
#          (full vs blind-rotation) -> feeds F1/C1 G3 projection and C5 go/no-go.
# Method: build matrix-base r-lane probe with -DSAB_PVW_BODY_PROFILE
#         -DMAT_TRGSW_SPLIT_PROFILE; run r in {1,2,4}, 2 trials x 3 reps.
# Profiled builds are slower; timings here are for SHARES, not absolute claims.
set -uo pipefail
ROOT="$HOME/spz/dell-final-bench"
cd "$ROOT" || exit 1
OUT="$ROOT/repro_stage373"; LOG="$OUT/run.log"; mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){ for i in $(seq 90); do cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); [ "$cur" -lt 10 ] && return 0; sleep 60; done; log "WARN no-quiet load=$(cat /proc/loadavg)"; }
COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
PROF="-DSAB_PVW_BODY_PROFILE -DMAT_TRGSW_SPLIT_PROFILE"
log "=== STAGE373 component profile (FINAL h=42, sigma default 2^-49) ==="
make -B $COMMON probe_sq.exe -j32 > "$OUT/build_base.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BASE BUILD FAIL"; exit 1; }
log "base objects built"
rm -f probe_rl_prof
gcc $FLAGS $PROF -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_prof.o 2>> "$OUT/b1.log"
gcc $FLAGS $PROF -c src/sab_pvw.c -o build_fin/sab_pvw_prof.o 2>> "$OUT/b1.log"
gcc $FLAGS $PROF -c src/sab_pvw_sq.c -o build_fin/sab_pvw_sq_prof.o 2>> "$OUT/b1.log"
gcc $FLAGS $PROF -c src/probe_pvw_sq.c -o build_fin/probe_pvw_sq_prof.o 2>> "$OUT/b1.log"
OBJS(){ ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v probe_pvw_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' '; }
gcc $FLAGS build_fin/mattrgsw_prof.o build_fin/sab_pvw_prof.o build_fin/sab_pvw_sq_prof.o build_fin/probe_pvw_sq_prof.o $(OBJS) -lm -o probe_rl_prof 2>> "$OUT/b1.log"
[ -x ./probe_rl_prof ] && log "probe_rl_prof OK" || { log "PROF BUILD FAIL"; cat "$OUT/b1.log" | tail -5 | tee -a "$LOG"; exit 1; }

for r in 1 2 4; do
  for t in 1 2; do
    wait_quiet
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_PVW_SQ_N=2048 SAB_PVW_SQ_OUTN=2048 SAB_PVW_SQ_PREC=3 \
    SAB_SQ_H=42 SAB_PVW_SQ_REPS=3 \
    timeout 3600 ./probe_rl_prof > "$OUT/prof_r${r}_t${t}.txt" 2>/dev/null || log "r$r t$t RUN FAILED/EMPTY"
    grep -E "TIMING|sigma_shift" "$OUT/prof_r${r}_t${t}.txt" | sed "s/^/[r$r t$t] /" | tee -a "$LOG"
    grep -E "blind_rotate_us|mat_ep|decomp|direct_dft|ifft|split|us=" "$OUT/prof_r${r}_t${t}.txt" | tail -40 | sed "s/^/[r$r t$t prof] /" | tee -a "$LOG"
    log "r$r t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done
log "=== STAGE373 COMPLETE ==="
