# Stage261 Reproduction Commands

All commands are run from the repository root.

```bash
make clean
make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \
  SAB_PVW_NONBINARY_BENCH=true \
  SAB_PVW_NONBINARY_BENCH_R=2 \
  SAB_PVW_NONBINARY_BENCH_REPS=1 \
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
  SAB_PVW_NONBINARY_BENCH_TERNARY=false \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
./main
```

Repeat with `SAB_PVW_NONBINARY_BENCH_R=4` and with
`SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=false
SAB_PVW_NONBINARY_BENCH_TERNARY=true` for the ternary branch.

```bash
python3 scripts/build_stage261_nonbinary_target_perf_preflight.py
```
