# Stage321 r4-Unrolled Direct Full-SAB Variant

Additional flag:

```text
MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true
```

Inherited selected direct baseline flags:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
SAB_PVW_BACKEND_FROM_DFT_ADD=true
SAB_PVW_SUB_DECOMP_FUSION=true
SAB_PVW_DUAL_SUB_CMUX=true
SAB_PVW_SUBA_INCLUDE_ZERO_COEFF_ONE_FAST=true
```

Default status: off. Scalar `sab_rlwe_bootstrap` and the selected direct
PVW/MAT-SAB control remain available as references.
