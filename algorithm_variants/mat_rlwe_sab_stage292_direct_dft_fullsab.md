# Stage292 Direct DFT Full-SAB Variant

Flag:

```text
MAT_TRGSW_SUB_DECOMP_DFT_DIRECT=true
```

Required companion flags for this gate:

```text
SAB_PVW_SUB_DECOMP_FUSION=true
MAT_TRGSW_AVX512_SUB_DECOMP=true
MAT_TRGSW_AVX512_SMALLR_SPECIALIZED=true
```

Default status: off. Scalar `sab_rlwe_bootstrap` and the selected PVW-SAB
control path remain available as references.
