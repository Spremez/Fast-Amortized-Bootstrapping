#!/usr/bin/env bash
# Stage359: noise readout (10 trials) for stock r-lane vs Path A at the
# corrected-security point h=41, sigma_out=2^-39 (SET_2_3_2048 shape, r=4).
# The make-based target-noise test reads sab_pvw_target_params() in main.c;
# patch the #else (SET_2_3_2048) block, run both builds back-to-back, restore.
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage359_pathA_noise_h41"
LOG="$OUT/run.log"
mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

log "=== STAGE359 noise h=41 sigma_out=2^-39 r=4 ==="
md5sum main.c | tee -a "$LOG"
cp main.c "$OUT/main.c.backup"
log "main.c backed up"

# patch #else block: h 39->41 (unique anchor), then sigma_out on next line
sed -i 's/(SAB_PVW_Target_Params){2048, 1, 2048, 1, 1, 23, 3, 39, 7,/(SAB_PVW_Target_Params){2048, 1, 2048, 1, 1, 23, 3, 41, 7,/' main.c
sed -i '/23, 3, 41, 7,/{n;s/pow(2, -50)/pow(2, -39)/;}' main.c
if grep -A1 '23, 3, 41, 7,' main.c | grep -q 'pow(2, -39)'; then
  log "patch OK"
else
  log "PATCH FAILED - restoring"; cp "$OUT/main.c.backup" main.c; exit 1
fi

FLAGS_COMMON="FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false KEY=BINARY PARAM=SET_2_3_2048"
NOISE="SAB_PVW_NONBINARY_TARGET_NOISE_TEST=true SAB_PVW_NONBINARY_TARGET_NOISE_R=4 SAB_PVW_NONBINARY_TARGET_NOISE_TRIALS=10 SAB_PVW_NONBINARY_TARGET_NOISE_INCLUDE_ZERO=true SAB_PVW_NONBINARY_TARGET_NOISE_TERNARY=false"
PATHA="MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true"

log "build stock r-lane (flags off)"
make clean > "$OUT/clean1.log" 2>&1
if ! make $FLAGS_COMMON $NOISE -j32 > "$OUT/build_stock.log" 2>&1; then
  log "STOCK BUILD FAIL"; cp "$OUT/main.c.backup" main.c; exit 1
fi
/usr/bin/time -v ./main > "$OUT/noise_stock.log" 2> "$OUT/noise_stock.time" || log "stock run nonzero exit"
grep -E "NOISE|noise|gate" "$OUT/noise_stock.log" | tail -20 | tee -a "$LOG"

log "build Path A (7 flags)"
make clean > "$OUT/clean2.log" 2>&1
if ! make $FLAGS_COMMON $NOISE $PATHA -j32 > "$OUT/build_pathA.log" 2>&1; then
  log "PATHA BUILD FAIL"; cp "$OUT/main.c.backup" main.c; exit 1
fi
/usr/bin/time -v ./main > "$OUT/noise_pathA.log" 2> "$OUT/noise_pathA.time" || log "pathA run nonzero exit"
grep -E "NOISE|noise|gate" "$OUT/noise_pathA.log" | tail -20 | tee -a "$LOG"

cp "$OUT/main.c.backup" main.c
log "main.c restored"
log "=== STAGE359 COMPLETE ==="
