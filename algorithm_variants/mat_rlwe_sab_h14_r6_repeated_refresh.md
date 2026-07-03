# MAT-RLWE SAB H14 r=6 Repeated Refresh

Date: 2026-07-03

Focused route: r=6 MAT-RLWE/PVW lanes, active-buffer sparse schedule, r>4 fused MAT kernel, and backend FromDFT-add materialization.

The path is explicit-only: `SAB_PVW_BACKEND_FROM_DFT_ADD=true` and `MAT_TRGSW_AVX512_RGT4_FUSED=true`. Scalar SAB and default PVW/MAT-SAB behavior remain unchanged.
