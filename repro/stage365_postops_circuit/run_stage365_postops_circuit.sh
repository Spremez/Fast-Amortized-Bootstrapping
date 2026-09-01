#!/usr/bin/env bash
# Stage365: post-bootstrap capacity curve, corrected selector. Stage364 used
# the SAB's own TRGSW params (l=1, Bg=2^23) for the post-op selector -- a
# single 23-bit digit cannot cover the 64-bit torus, so the first EP
# truncated the operand to ~2^41 error and noise saturated at 2^63
# (measured: 0 EP capacity under SAB-grade selectors -- itself a valid
# observation). Now: circuit-grade gadget l=8, Bg=2^8 (full torus coverage),
# same three security branches, 8-step chain.
set -uo pipefail
ROOT="/home/luck/spz/fab-main"
cd "$ROOT" || exit 1
OUT="$ROOT/repro/stage365_postops_circuit"
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

COMMON="BUILD_DIR=./build_fin FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native SAB_SQ_Q=16"
make -B $COMMON probe_sq.exe -j32 > "$OUT/build.log" 2>&1
[ -x ./probe_sq.exe ] || { log "BUILD FAIL"; exit 1; }
log "build OK (circuit-grade postop gadget)"

for cfg in "41 11" "52 0" "39 0"; do
  set -- $cfg; h="$1"; sig="$2"
  for t in 1 2; do
    wait_quiet
    SAB_SQ_H=$h SAB_SQ_SIGMA_SHIFT=$sig SAB_SQ_POSTOPS=8 SAB_SQ_POST_L=8 SAB_SQ_POST_BG=8 \
      timeout 1800 ./probe_sq.exe 2>/dev/null \
      | grep -E "bootstrap:|noise:|postop|gate:" \
      | sed "s/^/[h=$h sig+$sig t$t] /" | tee -a "$LOG"
    log "case h=$h sig+$sig t$t done load=$(cut -d' ' -f1 /proc/loadavg)"
  done
done
log "=== STAGE365 COMPLETE ==="
