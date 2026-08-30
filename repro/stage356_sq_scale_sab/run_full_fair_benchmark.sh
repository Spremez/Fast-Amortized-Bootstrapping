#!/usr/bin/env bash
# stage358 FULL FAIR BENCHMARK: 686's complete binary parameter matrix,
# re-measured at the CRYPTO'26 (ex-279) corrected security points.
# For every set: stock scalar SAB vs SQ-SAB (q=16), same h, same sigma,
# same binary, back-to-back, 3 rounds, full-slot message gates.
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=repro/stage356_sq_scale_sab
LOG=$OUT/full_fair_benchmark.log
: > "$LOG"

COMMON="BUILD_DIR=./build_pq FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false ARCH_FLAGS=-march=native SAB_SQ_Q=16"

run_set () { # name in_N out_N prec sig_exp h_fair h686
  local name=$1 n=$2 outn=$3 p=$4 sig=$5 hf=$6 h686=$7
  echo "=== $name: N=$n outN=$outn prec=$p h686=$h686 h_fair=$hf $(date) ===" | tee -a "$LOG"
  make -B $COMMON PARAM=$1 probe_sq.exe -j32 > "$OUT/ffb_build_$name.log" 2>&1
  if [ $? -ne 0 ]; then echo "BUILD FAIL $name" | tee -a "$LOG"; return; fi
  # original security point (686's published h)
  for t in 1 2 3; do
    SAB_SQ_N=$n SAB_SQ_OUTN=$outn SAB_SQ_P=$p SAB_SQ_SIG_IN=$sig SAB_SQ_H=$h686 \
      ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise|gate" \
      | sed "s/^/[$name h=$h686 r$t] /" >> "$LOG"
  done
  # fair security point (CRYPTO'26 corrected)
  for t in 1 2 3; do
    SAB_SQ_N=$n SAB_SQ_OUTN=$outn SAB_SQ_P=$p SAB_SQ_SIG_IN=$sig SAB_SQ_H=$hf \
      ./probe_sq.exe 2>/dev/null | grep -E "bootstrap:|noise|gate" \
      | sed "s/^/[$name h=$hf FAIR r$t] /" >> "$LOG"
  done
}

run_set SET_2_3_2048 2048 2048 3 15 42 39
run_set SET_4_5_2048 2048 2048 5 17 41 42
run_set SET_2_3_4096 4096 2048 3 15 36 32
run_set SET_4_5_4096 4096 2048 5 18 36 34
run_set SET_6_7_4096 4096 2048 7 21 36 33
run_set SET_8_9_4096 4096 8192 9 24 36 34
run_set SET_2_3_8192 8192 2048 3 15 32 25
run_set SET_4_5_8192 8192 2048 5 18 32 26
run_set SET_6_7_8192 8192 2048 7 21 32 27
run_set SET_8_9_8192 8192 8192 9 24 32 28

echo "=== FULL FAIR BENCHMARK DONE $(date) ===" | tee -a "$LOG"
