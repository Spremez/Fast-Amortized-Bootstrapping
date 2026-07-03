# MAT-RLWE SAB Same-Format Frontier

Stage155 classifies the current same-format PVW/MAT-SAB route.

Current valid endpoint:

```text
T_complete_bootstrap(r) / r
```

Allowed claim:

- explicit H14 r=6 backend path has scoped amortized complete-SAB evidence.

Disallowed claims:

- body-major layout is beneficial;
- dual-sub pair sharing provides meaningful full-SAB speedup;
- current MAT AVX512 is theoretically optimal;
- another same-format layout is worth implementing without a new mechanism.

Next algorithmic target:

- a representation-changing feasibility gate for DFT/lazy accumulator state or
  compact/shared-source state, before any SAB hot-path integration.
