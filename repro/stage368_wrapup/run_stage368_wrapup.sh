#!/usr/bin/env bash
# Stage368: comprehensive wrap-up experiments (user directive: launch ALL).
#  A) r=8 quiet rerun (r-scaling completion)           [S2]
#  B) S4 E-PF: SQ r-lane +- mattrgsw-side flags A/B    [partial fusion]
#  C) S7: 10-trial noise at FINAL h=42 sigma+0         [make route, h patch]
#  D) postops anomaly triage: gadget/sigma variants     [capacity open item]
#  E) S5: multi-parameter-set measurements
#     - SET_4_5_2048 (5-bit) @ h=42 (same-n family)
#     - 4096 corrected point h=42 t=8 (scalar + r-lane)
# All load-gated (<10), all gates checked.
set -uo pipefail
ROOT="$HOME/spz/dell-final-bench"
cd "$ROOT" || exit 1
OUT="$ROOT/repro_stage368"
LOG="$OUT/run.log"
mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){
  for i in $(seq 90); do
    cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)
    [ "$cur" -lt 10 ] && return 0
    sleep 60
  done
  log "WARN no-quiet (load=$(cat /proc/loadavg))"
}

COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
PATHA="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_AVX512_SUB_DECOMP -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST"
MATONLY="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_AVX512_SUB_DECOMP -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT"

log "=== STAGE368 comprehensive wrap-up ==="
make -B $COMMON probe_sq.exe -j32 > "$OUT/build_base.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BASE BUILD FAIL"; exit 1; }
# stock-binary (mattrgsw unflagged) + pathA binary + SQ-matflags binary (E-PF)
gcc $FLAGS -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_plain.o 2>> "$OUT/b1.log"
gcc $FLAGS -c src/sab_pvw.c -o build_fin/sab_pvw_plain.o 2>> "$OUT/b1.log"
gcc $FLAGS $MATONLY -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_matonly.o 2>> "$OUT/b2.log"
gcc $FLAGS $PATHA -c src/sab_pvw.c -o build_fin/sab_pvw_pathA.o 2>> "$OUT/b3.log"
gcc $FLAGS $PATHA -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_pathA.o 2>> "$OUT/b3.log"
OBJS(){ ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | grep -v 'sab_pvw' | tr '\n' ' '; }
gcc $FLAGS src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_plain.o build_fin/sab_pvw_plain.o $(OBJS) -lm -o probe_rl_stock 2>> "$OUT/b1.log"
gcc $FLAGS $MATONLY src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_matonly.o build_fin/sab_pvw_plain.o $(OBJS) -lm -o probe_rl_sqmat 2>> "$OUT/b2.log"
gcc $FLAGS $PATHA src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_pathA.o build_fin/sab_pvw_pathA.o $(OBJS) -lm -o probe_rl_pathA 2>> "$OUT/b3.log"
for b in probe_rl_stock probe_rl_sqmat probe_rl_pathA; do [ -x ./$b ] && log "$b BUILT" || { log "$b FAIL"; exit 1; }; done

rl(){ # bin r h sig tag trials
  for t in $(seq 1 "$6"); do
    wait_quiet
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$2 SAB_SQ_H=$3 SAB_SQ_SIGMA_SHIFT=$4 SAB_PVW_SQ_REPS=3 \
      timeout 3600 ./$1 2>/dev/null | grep -E "TIMING|timing r=|r_prec|keygen|attempts" \
      | sed "s/^/[$1 $5 t$t] /" | tee -a "$LOG"
    log "case $1 $5 t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
}

log "--- A) r=8 quiet rerun (FINAL) ---"
rl probe_rl_stock 8 42 0 "FIN-r8" 2
rl probe_rl_pathA 8 42 0 "FIN-r8" 2

log "--- B) E-PF: SQ arm +- mattrgsw flags (r=4 FINAL) ---"
rl probe_rl_stock 4 42 0 "EPF-base" 2
rl probe_rl_sqmat 4 42 0 "EPF-matflags" 2

log "--- D) postops variants at FINAL (anomaly triage) ---"
for cfg in "8 8 25" "16 4 25" "8 8 30" "8 8 35" "8 8 15"; do
  set -- $cfg
  wait_quiet
  SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_POSTOPS=6 SAB_SQ_POST_L=$1 SAB_SQ_POST_BG=$2 SAB_SQ_POST_SIG=$3 \
    timeout 1800 ./probe_sq.exe 2>/dev/null | grep -E "noise:|postop" \
    | sed "s/^/[postops L=$1 BG=$2 SIG=$3] /" | tee -a "$LOG"
  log "postops variant L=$1 BG=$2 SIG=$3 done"
done

log "--- E) S5 multi-set ---"
log "E1: SET_4_5_2048 5-bit scalar (h=42, sigma+0) x3"
for t in 1 2 3; do
  wait_quiet
  SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_N=2048 SAB_SQ_OUTN=2048 SAB_SQ_P=5 SAB_SQ_SIG_IN=17 \
    timeout 1800 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
    | sed "s/^/[5bit h=42 t$t] /" | tee -a "$LOG"
done
log "E2: 4096 corrected (h=42, t=8) scalar + r-lane"
for t in 1 2; do
  wait_quiet
  SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_N=4096 SAB_SQ_OUTN=2048 SAB_SQ_P=3 SAB_SQ_SIG_IN=15 SAB_SQ_RPREC=8 \
    timeout 3600 ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise:|gate:" \
    | sed "s/^/[4096 h=42 t$t] /" | tee -a "$LOG"
done
log "E2b: 4096 r-lane (probe N env):"
wait_quiet
SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=4 SAB_PVW_SQ_N=4096 SAB_PVW_SQ_OUTN=2048 SAB_PVW_SQ_PREC=3 \
  SAB_SQ_H=42 SAB_SQ_SIGMA_SHIFT=0 SAB_SQ_RPREC=8 SAB_PVW_SQ_REPS=3 \
  timeout 3600 ./probe_rl_stock 2>/dev/null | grep -E "TIMING|r_prec|keygen|attempts" \
  | sed "s/^/[4096-rlane stock t1] /" | tee -a "$LOG"

log "--- C) S7 10-trial noise at FINAL (make route, h patch 39->42) ---"
cp main.c "$OUT/main.c.backup"
sed -i 's/(SAB_PVW_Target_Params){2048, 1, 2048, 1, 1, 23, 3, 39, 7,/(SAB_PVW_Target_Params){2048, 1, 2048, 1, 1, 23, 3, 42, 7,/' main.c
grep -q '23, 3, 42, 7,' main.c && log "h patch OK" || { log "PATCH FAIL"; cp "$OUT/main.c.backup" main.c; }
NOISE="SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true SAB_PVW_NONBINARY_TARGET_NOISE_R=4 SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS=10 SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false"
FC="FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false KEY=BINARY PARAM=SET_2_3_2048"
make clean > "$OUT/clean_c.log" 2>&1
if make $FC $NOISE -j32 > "$OUT/build_noise.log" 2>&1; then
  /usr/bin/time -v ./main > "$OUT/noise_h42.log" 2> "$OUT/noise_h42.time"
  grep -E "summary|gate" "$OUT/noise_h42.log" | tee -a "$LOG"
else
  log "S7 noise build FAIL"
fi
cp "$OUT/main.c.backup" main.c
log "main.c restored"
log "=== STAGE368 COMPLETE ==="
