#!/usr/bin/env bash
# Stage364: post-bootstrap capacity curve (headroom-as-output metric).
# For each parameter branch, apply 8 external products after the bootstrap
# (multiply-by-one TRGSW under the input key) and record noise after each:
#   slope  = noise growth per post-bootstrap EP (bits/EP)
#   depth  = floor((budget - noise_0) / slope)   -- reported as an OUTPUT
# Branches: A0 (39,+0) reference | B1-ours (41,+11) | balance-tier (52,+0).
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage364_postops_capacity"
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

for i in $(seq 200); do
  grep -q 'STAGE363 COMPLETE' repro/stage363_balance_tier_h52/run.log 2>/dev/null && break
  sleep 90
done
grep -q 'STAGE363 COMPLETE' repro/stage363_balance_tier_h52/run.log 2>/dev/null \
  || { log "stage363 not complete - aborting"; exit 1; }
log "stage363 complete; rebuilding probe_sq with POSTOPS"

COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
make -B $COMMON probe_sq.exe -j32 > "$OUT/build.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BUILD FAIL"; exit 1; }
log "build OK"

for cfg in "41 11" "52 0" "39 0"; do
  set -- $cfg; h="$1"; sig="$2"
  for t in 1 2; do
    wait_quiet
    SAB_SQ_H=$h SAB_SQ_SIGMA_SHIFT=$sig SAB_SQ_POSTOPS=8 timeout 1800 ./probe_sq.exe 2>/dev/null \
      | grep -E "bootstrap:|noise:|postop|gate:" \
      | sed "s/^/[h=$h sig+$sig t$t] /" | tee -a "$LOG"
    log "case h=$h sig+$sig t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done
log "=== STAGE364 COMPLETE ==="
