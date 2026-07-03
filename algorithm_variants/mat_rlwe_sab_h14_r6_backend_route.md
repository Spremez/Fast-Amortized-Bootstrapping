# MAT-RLWE SAB H14 r=6 Backend Route

Date: 2026-07-03

This variant uses r=6 MAT-RLWE/PVW lanes with the existing active-buffer sparse schedule and the backend FromDFT-add materialization callback.

It is an explicit route behind `SAB_PVW_BACKEND_FROM_DFT_ADD=true` and `MAT_TRGSW_AVX512_RGT4_FUSED=true`. It does not alter scalar `sab_rlwe_bootstrap` or default PVW/MAT-SAB behavior.
