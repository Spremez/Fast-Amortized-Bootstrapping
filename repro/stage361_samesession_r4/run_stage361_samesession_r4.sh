#!/usr/bin/env bash
# Stage361: same-session r=4 + scalar completion. stage360 anchored r={2,6,8}
# with the scalar anchor but r=4 lives in stage358 (different session); this
# closes the clean same-session matrix: scalar + r=4 stock/pathA back-to-back.
# Waits for stage360 completion marker first (no overlap contamination).
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage361_samesession_r4"
LOG="$OUT/run.log"
mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

grep -q 'STAGE360 COMPLETE' repro/stage360_rscaling_anchor/run.log 2>/dev/null \
  || { log "stage360 not complete - aborting"; exit 1; }
log "stage360 complete; waiting for quiet machine (1-min load < 25, max 6h)"

for i in $(seq 72); do
  cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)
  [ "$cur" -lt 25 ] && break
  sleep 300
done
log "starting at load=$(cat /proc/loadavg)"

log "--- scalar anchor h=41 sigma+11 (3 runs) ---"
for t in 1 2 3; do
  SAB_SQ_H=41 SAB_SQ_SIGMA_SHIFT=11 timeout 600 ./probe_sq.exe 2>/dev/null \
    | grep -E "bootstrap:" | sed "s/^/[scalar t$t] /" | tee -a "$LOG"
done

run_case(){ # $1=bin
  local bin="$1"
  for t in 1 2; do
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=4 SAB_SQ_H=41 SAB_SQ_SIGMA_SHIFT=11 SAB_PVW_SQ_REPS=3 \
      timeout 1800 ./$bin 2>/dev/null | grep -E "TIMING|timing r=" \
      | sed "s/^/[$bin r=4 t$t] /" | tee -a "$LOG"
    log "case $bin r=4 trial$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
}
run_case probe_rl_stock
run_case probe_rl_pathA
log "=== STAGE361 COMPLETE ==="
