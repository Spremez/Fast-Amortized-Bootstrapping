# Stage262 Reproduction Commands

All rows use `FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true SAB_PVW_NONBINARY_BENCH=true
SAB_PVW_NONBINARY_BENCH_REPS=3`.

Run each `r in {1,2,4}` twice:

```bash
make clean
make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \
  SAB_PVW_NONBINARY_BENCH=true \
  SAB_PVW_NONBINARY_BENCH_R=<1|2|4> \
  SAB_PVW_NONBINARY_BENCH_REPS=3 \
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=true \
  SAB_PVW_NONBINARY_BENCH_TERNARY=false \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
./main
```

Then rerun with `SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=false` and
`SAB_PVW_NONBINARY_BENCH_TERNARY=true`.

```bash
python3 scripts/build_stage262_nonbinary_target_repeated_stats.py
```
