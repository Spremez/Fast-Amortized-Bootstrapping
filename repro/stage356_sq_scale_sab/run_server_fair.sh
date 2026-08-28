#!/usr/bin/env bash
# stage356-F fairness benchmark (server = sole reference environment):
# both schemes at the CRYPTO'26 (ex-279) corrected true-128-bit input key.
#   SAB_SQ_H=42 : estimator-tier fair point (T3 ceiling +8.4 bits over B1)
#   SAB_SQ_H=39 : T3 combinatorial tier anchor (one continuity run)
set -uo pipefail
cd "$(dirname "$0")/../.."

OUT=repro/stage356_sq_scale_sab
COMMON="BUILD_DIR=./build_srv FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native"

echo "=== build q16 (fair) $(date) ==="
make -B $COMMON SAB_SQ_Q=16 probe_sq.exe -j32 > "$OUT/fair_build.log" 2>&1
echo "build exit=$?"

echo "=== 9 rounds at h=42 (fair point) $(date) ==="
: > "$OUT/fair_run_h42.log"
: > "$OUT/fair_timing_h42.txt"
for t in $(seq 1 9); do
  SAB_SQ_H=42 ./probe_sq.exe > "/tmp/fair_r$t.log" 2>&1
  ec=$?
  grep -E "h = |gate|noise" "/tmp/fair_r$t.log" | sed "s/^/[r$t ec=$ec] /" >> "$OUT/fair_run_h42.log"
  grep "bootstrap:" "/tmp/fair_r$t.log" | sed 's/[^0-9,]*\([0-9,]*\).*/\1/' >> "$OUT/fair_timing_h42.txt"
done

echo "=== 1 anchor run at h=39 (T3 tier) $(date) ==="
SAB_SQ_H=39 ./probe_sq.exe > "$OUT/fair_run_h39_anchor.log" 2>&1
echo "h39 exit=$?"
echo "=== done $(date) ==="
