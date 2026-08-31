#!/usr/bin/env bash
# stage363: Fix r-lane build + run full comparison + competitor fair benchmarks
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=repro/stage356_sq_scale_sab
LOG=$OUT/rerun.log
: > "$LOG"

echo "=== FIX + RERUN $(date) ===" | tee -a "$LOG"

# Step 1: Compile mattrgsw with dense multiply export
FLAGS="-O2 -g -Isrc/mosfhet/include -Iinclude -march=native -DMOSFHET_DETERMINISTIC_RNG -DUSE_SHAKE -DUSE_SPQLIOS -DAVX512_OPT -DBINARY"
gcc $FLAGS -c src/mosfhet/src/mattrgsw.c -o build_fin/mattrgsw_dense.o 2>&1 | grep -E ' error' | head -3
echo "mattrgsw_dense.o: $([ -f build_fin/mattrgsw_dense.o ] && echo OK || echo FAIL)" | tee -a "$LOG"

# Step 2: Build r-lane probe
OBJS=$(ls build_fin/*.o | grep -v 'main\.o' | grep -v probe_sq | grep -v mattrgsw | tr '\n' ' ')
echo "OBJS count: $(echo $OBJS | wc -w)" | tee -a "$LOG"
gcc $FLAGS src/sab_pvw_sq.c src/probe_pvw_sq.c build_fin/mattrgsw_dense.o $OBJS -lm -o probe_rl 2>&1 | grep -E 'error|undefined' | sort -u | head -5
[ -x ./probe_rl ] && echo "r-lane probe BUILT" | tee -a "$LOG" || { echo "r-lane BUILD FAIL" | tee -a "$LOG"; exit 1; }

# Step 3: Verify r-lane probe works (toy gate)
echo "--- toy gate test ---" | tee -a "$LOG"
timeout 60 ./probe_rl 2>/dev/null | head -4 | tee -a "$LOG"

# Step 4: Run r-lane at h={39,41,42} × σ+11
echo "=== R-LANE EXPERIMENTS $(date) ===" | tee -a "$LOG"
for h in 39 41 42; do
  for r in 1 4; do
    echo "--- r=$r h=$h sigma+11 ---" | tee -a "$LOG"
    for t in 1 2 3; do
      SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=$h \
        SAB_SQ_SIGMA_SHIFT=11 SAB_PVW_SQ_REPS=3 \
        timeout 600 ./probe_rl 2>/dev/null | grep -E "TIMING|r_prec" \
        | sed "s/^/[r=$r h=$h sig+11 t$t] /" >> "$LOG" 2>&1
    done
  done
done

# Step 5: Also run r-lane at sigma+0 for baseline comparison
for h in 41; do
  for r in 4; do
    echo "--- r=$r h=$h sigma+0 baseline ---" | tee -a "$LOG"
    for t in 1 2 3; do
      SAB_PVW_SQ_TIMING=1 SAB_PVW_SQ_R=$r SAB_SQ_H=$h \
        SAB_SQ_SIGMA_SHIFT=0 SAB_PVW_SQ_REPS=3 \
        timeout 600 ./probe_rl 2>/dev/null | grep -E "TIMING|r_prec" \
        | sed "s/^/[r=$r h=$h sig+0 t$t] /" >> "$LOG" 2>&1
    done
  done
done

# Step 6: Try to build optimized stock r-lane (Path A)
echo "=== PATH A BUILD $(date) ===" | tee -a "$LOG"
OPT_FLAGS="MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_SUB_DECOMP=true MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_DUAL_SUB_CMUX=true ENABLE_PVW_TMLWE=true"
make -B BUILD_DIR=./build_opt FFT_LIB=spqlios_avx512 A_PRNG=none MOSFHET_DETERMINISTIC_RNG=true ENABLE_VAES=false PARAM=SET_2_3_2048 ARCH_FLAGS=-march=native $OPT_FLAGS main -j32 > "$OUT/opt_build.log" 2>&1
echo "optimized build: $([ -x ./main ] && echo OK || echo FAIL)" | tee -a "$LOG"

if [ -x ./main ]; then
  # The optimized main runs test_sab by default (scalar)
  # We need the PVW target test mode
  echo "--- optimized scalar baseline ---" | tee -a "$LOG"
  for t in 1 2 3; do
    SAB_SQ_H=41 /usr/bin/time -f "%e real" timeout 300 ./main 2>&1 \
      | grep -E "bootstrap:|gate|noise|real" \
      | sed "s/^/[opt-scalar h=41 t$t] /" >> "$LOG" 2>&1
  done
fi

echo "=== ALL DONE $(date) ===" | tee -a "$LOG"
