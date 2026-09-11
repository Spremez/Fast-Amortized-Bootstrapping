#!/usr/bin/env bash
# stage421 WS-9: add the row-tiled EP kernels (R4_UNROLLED + RGT4_FUSED,
# covering r=8 tiled dispatch) to the pathA stack; focused re-run.
set -uo pipefail
cd ~/spz/dell-final-bench
OUT=repro/stage421_pa2_dell; LOG="$OUT/ws9.log"; : >> "$LOG"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }
wait_quiet(){ for i in $(seq 60); do cur=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); [ "$cur" -lt 10 ] && return 0; sleep 30; done; }

BASE="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
KERNELS="-DMAT_TRGSW_AVX512_SMALLR_SPECIALIZED -DMAT_TRGSW_AVX512_R4_UNROLLED_ROWS -DMAT_TRGSW_AVX512_RGT4_FUSED"
PATHA="-DMAT_TRGSW_SUB_DECOMP_DFT_DIRECT -DMAT_TRGSW_AVX512_SUB_DECOMP -DSAB_PVW_BACKEND_FROM_DFT_ADD -DSAB_PVW_SUB_DECOMP_FUSION -DSAB_PVW_DUAL_SUB_CMUX -DSAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST"
D=build_pa2_flag2; mkdir -p $D

log "=== WS-9: flag2 tier = pathA + R4_UNROLLED + RGT4_FUSED ==="
for f in keyswitch bootstrap bootstrap_ga tlwe trlwe trgsw misc polynomial register pvwtlwe pvwtmlwe; do
  gcc $BASE -c src/mosfhet/src/$f.c -o $D/$f.o 2>>"$OUT/ws9_build.log" || { log "BUILD FAIL $f"; exit 1; }; done
gcc $BASE -c src/mosfhet/src/sha3/fips202.c -o $D/fips202.o 2>>"$OUT/ws9_build.log" || exit 1
gcc $BASE -c src/mosfhet/src/fft/karatsuba.c -o $D/karatsuba.o 2>>"$OUT/ws9_build.log" || exit 1
gcc $BASE -c src/mosfhet/src/fft/spqlios/spqlios-fft-avx512.s -o $D/spqlios-fft.o 2>>"$OUT/ws9_build.log" || exit 1
gcc $BASE -c src/mosfhet/src/fft/spqlios/spqlios-ifft-avx512.s -o $D/spqlios-ifft.o 2>>"$OUT/ws9_build.log" || exit 1
gcc $BASE -c src/mosfhet/src/fft/spqlios/spqlios-fft-impl-avx512.c -o $D/spqlios-fft-impl.o 2>>"$OUT/ws9_build.log" || exit 1
gcc $BASE -c src/mosfhet/src/fft/spqlios/fft_processor_spqlios.c -o $D/fft_processor_spqlios.o 2>>"$OUT/ws9_build.log" || exit 1
gcc $BASE $KERNELS -c src/mosfhet/src/mattrgsw.c -o $D/mattrgsw.o 2>>"$OUT/ws9_build.log" || { log "mattrgsw FAIL"; exit 1; }
gcc $BASE $PATHA -c src/sab_pvw.c -o $D/sab_pvw.o 2>>"$OUT/ws9_build.log" || { log "sab_pvw FAIL"; exit 1; }
for f in sparse_amortized_bootstrap sab_profile sab_rinput; do
  gcc $BASE -c src/$f.c -o $D/$f.o 2>>"$OUT/ws9_build.log" || exit 1; done
gcc $BASE -c src/probe_prealigned2.c -o $D/probe_prealigned2.o 2>>"$OUT/ws9_build.log" || exit 1
gcc $BASE $D/probe_prealigned2.o $D/sparse_amortized_bootstrap.o $D/sab_profile.o $D/sab_pvw.o $D/sab_rinput.o \
  $D/keyswitch.o $D/bootstrap.o $D/bootstrap_ga.o $D/tlwe.o $D/trlwe.o $D/trgsw.o $D/misc.o $D/polynomial.o \
  $D/register.o $D/pvwtlwe.o $D/pvwtmlwe.o $D/mattrgsw.o $D/fips202.o $D/karatsuba.o \
  $D/spqlios-fft.o $D/spqlios-fft-impl.o $D/fft_processor_spqlios.o $D/spqlios-ifft.o \
  -lm -o $D/probe_prealigned2 -Wl,--allow-multiple-definition 2>>"$OUT/ws9_build.log" || { log "LINK FAIL"; exit 1; }
log "flag2 BUILT"

log "--- gates ---"
log "equiv 2x2: $(SAB_PA_R1=2 SAB_PA_R2=2 ./$D/probe_prealigned2 2>/dev/null | grep PA2-GATE)"
log "equiv 4x2: $(SAB_PA_R1=4 SAB_PA_R2=2 ./$D/probe_prealigned2 2>/dev/null | grep PA2-GATE)"
log "func  4x2: $(SAB_PA_FUNC=1 SAB_PA_R1=4 SAB_PA_R2=2 ./$D/probe_prealigned2 2>/dev/null | grep FUNC-GATE)"

log "--- toy 3 reps (4x2, 2x4, 2x2) ---"
for cfg in "4 2" "2 4" "2 2"; do
  set -- $cfg
  for rep in 1 2 3; do
    wait_quiet
    a=$(SAB_PA_R1=$1 SAB_PA_R2=$2 ./$D/probe_prealigned2 2>/dev/null | grep -oE "speedup\(sep/joint_total\)=[0-9.]+x")
    log "r1=$1 r2=$2 rep$rep FLAG2 $a"
  done
done

log "--- FINAL ---"
FINAL="SAB_PA_IN_N=2048 SAB_PA_H=42 SAB_PA_RPREC=7"
for cfg in "4 2" "2 2"; do
  set -- $cfg
  wait_quiet
  out=$(env $FINAL SAB_PA_R1=$1 SAB_PA_R2=$2 ./$D/probe_prealigned2 2>/dev/null | grep -E "PA2-GATE|timing")
  log "FINAL flag2 r1=$1 r2=$2 :: $(echo "$out" | tr '\n' ' ')"
done
log "=== WS-9 DONE ==="
