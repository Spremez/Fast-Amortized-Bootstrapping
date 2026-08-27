#!/usr/bin/env bash
# stage356 P0-a server runner: SQ v3 AVX-512 retest on spz (fab-main).
# 9 back-to-back ratio rounds (q=16), q=23 reference, sigma+15 hardening.
set -uo pipefail
cd "$(dirname "$0")"
OUT=repro/stage356_sq_scale_sab
mkdir -p "$OUT"

COMMON="BUILD_DIR=./build_srv FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native"

echo "=== build q16 $(date) ==="
make -B $COMMON SAB_SQ_Q=16 probe_sq.exe -j32 > "$OUT/server_build_q16.log" 2>&1
echo "build exit=$?"

echo "=== 9 ratio rounds q16 $(date) ==="
: > "$OUT/server_run_q16.log"
for t in $(seq 1 9); do
  ./probe_sq.exe > "/tmp/sq_round_$t.log" 2>&1
  ec=$?
  grep -E "bootstrap:|noise|gate" "/tmp/sq_round_$t.log" | sed "s/^/[r$t ec=$ec] /" >> "$OUT/server_run_q16.log"
  grep "bootstrap:" "/tmp/sq_round_$t.log" | sed 's/[^0-9,]*\([0-9,]*\).*/\1/' >> "$OUT/server_timing_q16.txt"
done

echo "=== q23 reference $(date) ==="
make -B $COMMON SAB_SQ_Q=23 probe_sq.exe -j32 > "$OUT/server_build_q23.log" 2>&1
./probe_sq.exe > "$OUT/server_run_q23.log" 2>&1
echo "q23 exit=$?"

echo "=== sigma+15 hardening (aut l=4 Bg=2^16) $(date) ==="
make -B $COMMON SAB_SQ_Q=16 probe_sq.exe -j32 > "$OUT/server_build_q16b.log" 2>&1
SQKS_AUT_L=4 SQKS_AUT_BG=16 SAB_SQ_SIGMA_SHIFT=15 ./probe_sq.exe > "$OUT/server_run_q16_sigma15.log" 2>&1
echo "sigma15 exit=$?"
echo "=== done $(date) ==="
