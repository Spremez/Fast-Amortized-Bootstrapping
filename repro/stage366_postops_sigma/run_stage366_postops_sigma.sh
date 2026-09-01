#!/usr/bin/env bash
# Stage366: post-bootstrap capacity, iteration 3. Root causes so far:
#  - SAB-grade gadget (l=1,Bg=2^23): operand truncation (stage364)
#  - input-key sigma 2^-15 selector noise x Bg amplification ~ 2^-1.8 torus
#    (stage365; quantitatively matches sqrt(lN)*Bg/sqrt(12)*sigma model)
# Fix: clone the input secret at adjustable sampling sigma (SAB_SQ_POST_SIG),
# sweep sigma_G in {25,30,40} at l=8/Bg=2^8, on the main branch (h=41,+11).
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage366_postops_sigma"
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
make -B $COMMON probe_sq.exe -j32 > "$OUT/build.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BUILD FAIL"; exit 1; }
log "build OK (sigma-adjustable circuit keys)"

for psig in 25 30 40; do
  for t in 1 2; do
    wait_quiet
    SAB_SQ_H=41 SAB_SQ_SIGMA_SHIFT=11 SAB_SQ_POSTOPS=8 SAB_SQ_POST_L=8 SAB_SQ_POST_BG=8 SAB_SQ_POST_SIG=$psig \
      timeout 1800 ./probe_sq.exe 2>/dev/null \
      | grep -E "noise:|postop" \
      | sed "s/^/[h=41 sig+11 postsig=$psig t$t] /" | tee -a "$LOG"
    log "case postsig=$psig t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done
log "=== STAGE366 COMPLETE ==="
