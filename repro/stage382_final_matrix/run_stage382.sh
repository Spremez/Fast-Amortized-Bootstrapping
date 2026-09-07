#!/usr/bin/env bash
# Stage382: corrected-security FULL main matrix (Eurocrypt-grade table).
# Harness = stage380-validated (SAB_PVW_NONBINARY_BENCH include-zero, full
# 7-flag build, same-binary paired scalar baseline, R=4), across all six
# parameter sets with corrected h per family (2048->42, 4096->42; 8192-family
# input rows live in 4096 sets). 3 runs each, load-gated, correctness-gated.
set -uo pipefail
ROOT="$HOME/spz/dell-final-bench"
cd "$ROOT" || exit 1
OUT="$ROOT/repro_stage382"; LOG="$OUT/run.log"; mkdir -p "$OUT"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){ for i in $(seq 90); do cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); [ "$cur" -lt 10 ] && return 0; sleep 60; done; log "WARN no-quiet"; }
BUILD_FLAGS_COMMON="FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true"
patch_h(){ # set_name orig_h -> sed the h_in inside that set's #elif block
  python3 - "$1" "$2" << 'PYEOF'
import sys, re
setname, orig = sys.argv[1], sys.argv[2]
s = open('main.c', encoding='utf-8').read()
blk = '#elif defined(%s)' % setname
i = s.find(blk)
assert i >= 0, setname
j = s.find('#elif', i + 5)
if j < 0: j = s.find('#endif', i)
seg = s[i:j]
assert 'h_in = %s' % orig in seg, (setname, orig)
seg2 = seg.replace('h_in = %s' % orig, 'h_in = 42', 1)
open('main.c', 'w', encoding='utf-8').write(s[:i] + seg2 + s[j:])
print('patched', setname, orig, '-> 42')
PYEOF
}
log "=== STAGE382 corrected-security full matrix (R=4, 3 runs/set) ==="
cp main.c "$OUT/main.orig.c"
run_set(){ # set_name orig_h
  local setname="$1" orig_h="$2"
  cp "$OUT/main.orig.c" main.c
  if [ "$orig_h" != "42" ]; then patch_h "$setname" "$orig_h" || { log "$setname PATCH FAIL"; return; }; fi
  wait_quiet
  make clean > "$OUT/${setname}_clean.log" 2>&1
  if ! make $BUILD_FLAGS_COMMON PARAM="$setname" \
      SAB_PVW_NONBINARY_BENCH=true SAB_PVW_NONBINARY_BENCH_R=4 \
      SAB_PVW_NONBINARY_BENCH_REPS=1 SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
      SAB_PVW_NONBINARY_BENCH_TERNARY=false -j32 > "$OUT/${setname}_build.log" 2>&1; then
    log "$setname BUILD FAILED"; return
  fi
  for i in 1 2 3; do
    wait_quiet
    ./main > "$OUT/${setname}_run${i}.log" 2>&1
    ok=$(grep -c 'gate: Pass' "$OUT/${setname}_run${i}.log")
    sp=$(grep -o 'speedup_vs_scalar_repeated=[0-9.]*' "$OUT/${setname}_run${i}.log" | tail -1)
    pl=$(grep -o 'pvw_lane_avg_us=[0-9.]*' "$OUT/${setname}_run${i}.log" | tail -1)
    log "$setname run$i: gate=$ok $sp $pl"
  done
}
run_set SET_2_3_2048 39
run_set SET_4_5_2048 42
run_set SET_2_3_4096 32
run_set SET_4_5_4096 34
run_set SET_6_7_4096 33
run_set SET_8_9_4096 34
cp "$OUT/main.orig.c" main.c
log "=== STAGE382 COMPLETE ==="
