#!/usr/bin/env bash
# Stage383: r-selection benchmark in the MAIN caliber (include-zero full-flag
# harness, same as stage382) -- r in {1,2,8} on SET_2_3_2048 and SET_4_5_2048,
# r=4 already measured by stage382. 3 runs each, gated, h=42.
set -uo pipefail
ROOT="$HOME/spz/dell-final-bench"
cd "$ROOT" || exit 1
OUT="$ROOT/repro_stage383"; LOG="$OUT/run.log"; mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){ for w in $(seq 90); do cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); [ "$cur" -lt 10 ] && return 0; sleep 60; done; log "WARN no-quiet"; }
BUILD_FLAGS_COMMON="FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true"
log "=== STAGE383 r-selection (main caliber, h=42) ==="
cp main.c "$OUT/main.orig.c"
for setname in SET_2_3_2048 SET_4_5_2048; do
  orig_h=39
  [ "$setname" = "SET_4_5_2048" ] && orig_h=42
  cp "$OUT/main.orig.c" main.c
  if [ "$orig_h" != "42" ]; then
    python3 - "$setname" "$orig_h" << 'PYEOF'
import sys
setname, orig = sys.argv[1], sys.argv[2]
s = open('main.c', encoding='utf-8').read()
blk = '#if defined(%s)' % setname if s.find('#if defined(%s)' % setname) >= 0 else '#elif defined(%s)' % setname
i = s.find(blk); j = s.find('#elif', i + 5)
if j < 0: j = s.find('#endif', i)
seg = s[i:j]
assert 'h_in = %s' % orig in seg
open('main.c', 'w', encoding='utf-8').write(s[:i] + seg.replace('h_in = %s' % orig, 'h_in = 42', 1) + s[j:])
PYEOF
  fi
  for r in 1 2 8; do
    wait_quiet
    make clean > "$OUT/${setname}_r${r}_clean.log" 2>&1
    if ! make $BUILD_FLAGS_COMMON PARAM="$setname" \
        SAB_PVW_NONBINARY_BENCH=true SAB_PVW_NONBINARY_BENCH_R="$r" \
        SAB_PVW_NONBINARY_BENCH_REPS=1 SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
        SAB_PVW_NONBINARY_BENCH_TERNARY=false -j32 > "$OUT/${setname}_r${r}_build.log" 2>&1; then
      log "$setname r=$r BUILD FAILED"; continue
    fi
    for i in 1 2 3; do
      wait_quiet
      ./main > "$OUT/${setname}_r${r}_run${i}.log" 2>&1
      ok=$(grep -c 'gate: Pass' "$OUT/${setname}_r${r}_run${i}.log")
      sp=$(grep -o 'speedup_vs_scalar_repeated=[0-9.]*' "$OUT/${setname}_r${r}_run${i}.log" | tail -1)
      pl=$(grep -o 'pvw_lane_avg_us=[0-9.]*' "$OUT/${setname}_r${r}_run${i}.log" | tail -1)
      log "$setname r=$r run$i: gate=$ok $sp $pl"
    done
  done
done
cp "$OUT/main.orig.c" main.c
log "=== STAGE383 COMPLETE ==="
