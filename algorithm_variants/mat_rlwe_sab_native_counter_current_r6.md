# Native Counter Current r=6 Path

Flags:

```text
FFT_LIB=spqlios_avx512 A_PRNG=none ENABLE_VAES=false PARAM=SET_2_3_2048 KEY=BINARY MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true MAT_TRGSW_AVX512_RGT4_FUSED=true SAB_PVW_ACTIVE_BUFFER_FUSION=true SAB_PVW_BACKEND_FROM_DFT_ADD=true SAB_PVW_SUB_DECOMP_FUSION=true SAB_PVW_BENCH=true SAB_PVW_BENCH_R=6 SAB_PVW_BENCH_REPS=1
```

Decision: `PASS_STAGE167_CB5_NATIVE_R6_COUNTERS_RECORDED`.

The tested path is the current exact r=6 post-fusion PVW/MAT-SAB path:
active-buffer fusion, backend FromDFT-add, sub-decompose fusion, and r>4 tiled
AVX512 MAT external product.
