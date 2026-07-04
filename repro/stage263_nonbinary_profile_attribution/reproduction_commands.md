# Stage263 Reproduction Commands

Use WSL2/Linux or native Linux with AVX512 exposed.

```bash
make clean
make FFT_LIB=spqlios_avx512 KEY=BINARY PARAM=SET_2_3 \
  SAB_PVW_NONBINARY_BENCH=true \
  SAB_PVW_NONBINARY_BENCH_R=<2|4> \
  SAB_PVW_NONBINARY_BENCH_REPS=1 \
  SAB_PVW_NONBINARY_BENCH_INCLUDE_ZERO=<true|false> \
  SAB_PVW_NONBINARY_BENCH_TERNARY=<false|true> \
  SAB_PVW_BODY_PROFILE=true \
  MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
./main
```

Run r=2 and r=4 for include-zero and ternary, then:

```bash
python3 scripts/build_stage263_nonbinary_profile_attribution.py
```
