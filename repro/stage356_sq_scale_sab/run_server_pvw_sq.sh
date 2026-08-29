#!/usr/bin/env bash
# stage357-S2: SQ x r-lane server timing (AVX-512, fairness point).
set -uo pipefail
cd "$(dirname "$0")/../.."

OUT=repro/stage356_sq_scale_sab
mkdir -p "$OUT"

echo "=== build (avx512) $(date) ==="
make BUILD_DIR=./build_pq FFT_LIB=spqlios_avx512 A_PRNG=none \
     MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ENABLE_PVW_TMLWE=true \
     PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native main -j32 \
     > "$OUT/pvw_sq_build.log" 2>&1
echo "make exit=$?"

OBJS=$(ls build_pq/*.o | grep -v 'main\.o' | tr '\n' ' ')
gcc -O2 -g -Iinclude -Isrc/mosfhet/include -march=native \
    -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DBINARY \
    src/sab_pvw_sq.c src/probe_pvw_sq.c $OBJS -lm -o ppsq 2>&1 \
    | grep -E ' error' | head -5
[ -x ./ppsq ] || { echo "PPSQ BUILD FAILED"; exit 1; }
echo "ppsq built"

for r in 1 4; do
  for h in 39 42; do
    echo "=== r=$r h=$h $(date) ==="
    SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=$h ./ppsq 2>/dev/null \
      | grep -E "TIMING|r_prec" >> "$OUT/pvw_sq_server_timing.log"
  done
done
echo "=== done $(date) ==="
