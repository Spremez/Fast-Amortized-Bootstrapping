# MAT-RLWE SAB Post-Fusion Attribution Variant

Date: 2026-07-03

Profiled explicit path:

```text
MAT_TRGSW_AVX512_RGT4_FUSED=true
SAB_PVW_ACTIVE_BUFFER_FUSION=true
SAB_PVW_BACKEND_FROM_DFT_ADD=true
SAB_PVW_SUB_DECOMP_FUSION=true
```

The source dispatch is `mat_trgsw_mul_pvmtmlwe_sub_DFT -> mat_trgsw_sub_decompose -> mat_trgsw_mul_pvmtmlwe_DFT_from_dec -> rgt4_tiled_avx512` for r=6.
