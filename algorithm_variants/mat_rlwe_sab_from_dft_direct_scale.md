# From-DFT AVX512 Direct-Scale Variant

Flag:

```text
SPQLIOS_AVX512_DIRECT_SCALE=true
```

Decision:

```text
NEUTRAL_STAGE174_DIRECT_SCALE_MICROBENCH_NOT_PROMOTED
```

Scope:

```text
backend/SIMD constant-factor candidate for spqlios_avx512 from_DFT
```

Blocked unless full-SAB gate promotes:

```text
complete SAB acceleration claim
default enablement
algorithmic complexity claim
```
