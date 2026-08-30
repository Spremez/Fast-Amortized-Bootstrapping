#!/usr/bin/env bash
# stage357-S2b: high-stat rerun with interleaved order + warmup.
# Exclusive-server check first; 5 reps per config at the fairness point.
set -uo pipefail
cd "$(dirname "$0")/../.."

OUT=repro/stage356_sq_scale_sab

echo "=== exclusivity check $(date) ==="
if pgrep -f '\./main|probe_sq|ppsq' > /dev/null 2>&1; then
  echo "BLOCK: other benchmark processes running"
  pgrep -af '\./main|probe_sq|ppsq' | head -3
  exit 1
fi
echo "server exclusive"

OBJS=$(ls build_pq/*.o | grep -v 'main\.o' | tr '\n' ' ')
gcc -O2 -g -Iinclude -Isrc/mosfhet/include -march=native \
    -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DBINARY \
    src/sab_pvw_sq.c src/probe_pvw_sq.c $OBJS -lm -o ppsq 2>&1 \
    | grep -E ' error' | head -5
[ -x ./ppsq ] || { echo "PPSQ BUILD FAILED"; exit 1; }

for r in 4 1; do
  echo "=== S2b r=$r h=42 5reps $(date) ==="
  SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=42 SAB_PVW_SQ_REPS=5 \
    ./ppsq 2>/dev/null | grep -E "TIMING|r_prec" >> "$OUT/pvw_sq_s2b_timing.log"
done
echo "=== done $(date) ==="
