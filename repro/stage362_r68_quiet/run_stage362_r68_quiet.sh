#!/usr/bin/env bash
# Stage362: quiet-machine re-measurement of r={6,8} (user directive). The
# stage360 r>=6 windows had unequal load (37-84) making pathA-vs-stock
# unresolvable. Chains after stage361; every case starts only when the
# 1-min load is < 25 (paused-wait, max 6h total). Includes one r=2 stock
# bridge case for cross-session normalization against stage360's r=2.
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage362_r68_quiet"
LOG="$OUT/run.log"
mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

for i in $(seq 240); do
  grep -q 'STAGE361 COMPLETE' repro/stage361_samesession_r4/run.log 2>/dev/null && break
  sleep 90
done
grep -q 'STAGE361 COMPLETE' repro/stage361_samesession_r4/run.log 2>/dev/null \
  || { log "stage361 not complete in 6h - aborting"; exit 1; }
log "stage361 complete"

wait_quiet(){
  for i in $(seq 60); do
    cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)
    [ "$cur" -lt 25 ] && return 0
    sleep 60
  done
  log "WARN: no quiet window before case (load=$(cat /proc/loadavg))"
}

run_case(){ # $1=bin $2=r $3=trials
  local bin="$1" r="$2" tmax="$3"
  for t in $(seq 1 "$tmax"); do
    wait_quiet
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=41 SAB_SQ_SIGMA_SHIFT=11 SAB_PVW_SQ_REPS=3 \
      timeout 3600 ./$bin 2>/dev/null | grep -E "TIMING|timing r=" \
      | sed "s/^/[$bin h=41 sig+11 r=$r t$t] /" | tee -a "$LOG"
    log "case $bin r=$r trial$t done load=$(cat /proc/loadavg)"
  done
}

log "--- bridge: r=2 stock (1 trial, cross-session normalization) ---"
run_case probe_rl_stock 2 1

for r in 6 8; do
  log "--- r=$r quiet re-measurement ---"
  run_case probe_rl_stock "$r" 2
  run_case probe_rl_pathA "$r" 2
done
log "=== STAGE362 COMPLETE ==="
