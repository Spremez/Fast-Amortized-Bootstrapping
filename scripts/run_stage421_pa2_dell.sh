#!/usr/bin/env bash
# stage421 WS-7: dell authoritative three-table re-run for pre-aligned
# pack/batch/joint (plain tier + full production AVX-512 seven-flag tier).
# Gates first, then toy 7-config x6 reps both tiers, then FINAL matrix.
set -uo pipefail
cd ~/spz/dell-final-bench
OUT=repro/stage421_pa2_dell; mkdir -p "$OUT" build_pa2_plain build_pa2_flag
LOG="$OUT/run.log"; : > "$LOG"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){ for i in $(seq 60); do cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); [ "$cur" -lt 10 ] && return 0; sleep 30; done; log "WARN no-quiet load=$(cat /proc/loadavg)"; }

BASE="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DBINARY"
AVX="-DAVX512_OPT"
PATHA="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DMAT_TRGSW_AVX512_SUB_DECOMP -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST"

build_tier(){ # $1=dir $2=xflags(sab_pvw+mattrgsw) $3=fft(fma|avx512)
  # NOTE: AVX512_OPT must be GLOBAL for the avx512 tier: misc.c's
  # safe_aligned_malloc only switches to 64B posix_memalign when it sees
  # the define -- scoping it to FFT files alone yields 16B table buffers
  # and vmovapd faults inside fft/ifft.
  local D=$1 XF=$2 FS=$3 f GB
  if [ "$FS" = avx512 ]; then GB="$BASE $AVX"; else GB="$BASE"; fi
  for f in keyswitch bootstrap bootstrap_ga tlwe trlwe trgsw misc polynomial register pvwtlwe pvwtmlwe; do
    gcc $GB -c src/mosfhet/src/$f.c -o $D/$f.o 2>>"$OUT/build.log" || return 1; done
  gcc $GB -c src/mosfhet/src/sha3/fips202.c -o $D/fips202.o 2>>"$OUT/build.log" || return 1
  gcc $GB -c src/mosfhet/src/fft/karatsuba.c -o $D/karatsuba.o 2>>"$OUT/build.log" || return 1
  if [ "$FS" = avx512 ]; then
    gcc $BASE $AVX -c src/mosfhet/src/fft/spqlios/spqlios-fft-avx512.s -o $D/spqlios-fft.o 2>>"$OUT/build.log" || return 1
    gcc $BASE $AVX -c src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s -o $D/spqlios-ifft.o 2>>"$OUT/build.log" || return 1
    gcc $BASE $AVX -c src/mosfhet/src/fft/spqlios/spqlios-fft-impl-avx512.c -o $D/spqlios-fft-impl.o 2>>"$OUT/build.log" || return 1
    gcc $BASE $AVX -c src/mosfhet/src/fft/spqlios/fft_processor_spqlios.c -o $D/fft_processor_spqlios.o 2>>"$OUT/build.log" || return 1
  else
    gcc $BASE -c src/mosfhet/src/fft/spqlios/spqlios-fft-fma.s -o $D/spqlios-fft.o 2>>"$OUT/build.log" || return 1
    gcc $BASE -c src/mosfhet/src/fft/spqlios/spqlios-ifft-fma.s -o $D/spqlios-ifft.o 2>>"$OUT/build.log" || return 1
    gcc $BASE -c src/mosfhet/src/fft/spqlios/spqlios-fft-impl.c -o $D/spqlios-fft-impl.o 2>>"$OUT/build.log" || return 1
    gcc $BASE -c src/mosfhet/src/fft/spqlios/fft_processor_spqlios.c -o $D/fft_processor_spqlios.o 2>>"$OUT/build.log" || return 1
  fi
  gcc $GB $XF -c src/mosfhet/src/mattrgsw.c -o $D/mattrgsw.o 2>>"$OUT/build.log" || return 1
  gcc $GB $XF -c src/sab_pvw.c -o $D/sab_pvw.o 2>>"$OUT/build.log" || return 1
  for f in sparse_amortized_bootstrap sab_profile sab_rinput; do
    gcc $GB -c src/$f.c -o $D/$f.o 2>>"$OUT/build.log" || return 1; done
  gcc $GB -c src/probe_prealigned2.c -o $D/probe_prealigned2.o 2>>"$OUT/build.log" || return 1
  gcc $GB $D/probe_prealigned2.o $D/sparse_amortized_bootstrap.o $D/sab_profile.o $D/sab_pvw.o $D/sab_rinput.o \
    $D/keyswitch.o $D/bootstrap.o $D/bootstrap_ga.o $D/tlwe.o $D/trlwe.o $D/trgsw.o $D/misc.o $D/polynomial.o \
    $D/register.o $D/pvwtlwe.o $D/pvwtmlwe.o $D/mattrgsw.o $D/fips202.o $D/karatsuba.o \
    $D/spqlios-fft.o $D/spqlios-fft-impl.o $D/fft_processor_spqlios.o $D/spqlios-ifft.o \
    -lm -o $D/probe_prealigned2 -Wl,--allow-multiple-definition 2>>"$OUT/build.log" || return 1
}

log "=== stage421 WS-7 dell: build two tiers ==="
build_tier build_pa2_plain "" fma       && log "plain tier BUILT"  || { log "plain tier BUILD FAIL"; exit 1; }
build_tier build_pa2_flag "$PATHA" avx512 && log "flag tier BUILT" || { log "flag tier BUILD FAIL"; exit 1; }

log "--- quick gates both tiers ---"
for B in build_pa2_plain build_pa2_flag; do
  wait_quiet
  log "[$B] equiv 2x2: $(SAB_PA_R1=2 SAB_PA_R2=2 ./$B/probe_prealigned2 2>/dev/null | grep -E 'PA2-GATE' )"
  log "[$B] func  2x2: $(SAB_PA_FUNC=1 SAB_PA_R1=2 SAB_PA_R2=2 ./$B/probe_prealigned2 2>/dev/null | grep -E 'FUNC-GATE')"
done

log "--- toy 7-config x6 reps, both tiers (interleaved) ---"
for cfg in "1 2" "1 4" "2 1" "4 1" "2 2" "4 2" "2 4"; do
  set -- $cfg
  for rep in 1 2 3 4 5 6; do
    wait_quiet
    a=$(SAB_PA_R1=$1 SAB_PA_R2=$2 ./build_pa2_flag/probe_prealigned2 2>/dev/null | grep -oE "joint_total=[0-9]+ us, [0-9]+x-scalar=[0-9]+ us, speedup\(sep/joint_total\)=[0-9.]+x" | sed "s/us//g;s/ //g")
    b=$(SAB_PA_R1=$1 SAB_PA_R2=$2 ./build_pa2_plain/probe_prealigned2 2>/dev/null | grep -oE "joint_total=[0-9]+ us, [0-9]+x-scalar=[0-9]+ us, speedup\(sep/joint_total\)=[0-9.]+x" | sed "s/us//g;s/ //g")
    log "r1=$1 r2=$2 rep$rep FLAG $a"
    log "r1=$1 r2=$2 rep$rep PLAIN $b"
  done
done

log "--- FINAL matrix (n=2048 h=42 rp=7) ---"
FINAL="SAB_PA_IN_N=2048 SAB_PA_H=42 SAB_PA_RPREC=7"
for spec in "flag 2 2" "flag 1 4" "flag 4 1" "flag 4 2" "plain 2 2"; do
  set -- $spec; tier=$1
  wait_quiet
  out=$(env $FINAL SAB_PA_R1=$2 SAB_PA_R2=$3 ./build_pa2_$tier/probe_prealigned2 2>/dev/null | grep -E "PA2-GATE|timing")
  log "FINAL $tier r1=$2 r2=$3 :: $(echo "$out" | tr '\n' ' ')"
done
wait_quiet
out=$(env $FINAL SAB_PA_FUNC=1 SAB_PA_R1=2 SAB_PA_R2=2 ./build_pa2_flag/probe_prealigned2 2>/dev/null | grep -E "PA2-GATE|FUNC-GATE")
log "FINAL flag func 2x2 :: $(echo "$out" | tr '\n' ' ')"

log "=== STAGE421 WS-7 DONE ==="
