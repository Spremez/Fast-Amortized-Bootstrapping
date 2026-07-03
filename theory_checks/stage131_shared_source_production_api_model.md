# Stage131 Shared-Source Production API Model

Date: 2026-07-03

Stage131 productionizes only the Stage130 evidence boundary. The output
type is `MAT_TRGSW_COMPACT_OUTPUT_DFT`, which stores one mask/body DFT
pair per lane. It intentionally does not claim a true `PVW_TMLWE_DFT`
shared-output mask; that requires a later invariant gate.

## Public API

```text
MAT_TRGSW_COMPACT_DFT
MAT_TRGSW_COMPACT_OUTPUT_DFT
MAT_TRGSW_COMPACT_MUL_SCRATCH
mat_trgsw_compact_set_row_from_torus(...)
mat_trgsw_compact_mul_pvmtmlwe_DFT(...)
```

## Results

| r | N | seed | guards | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 512 | 0 | 0 | 0 | 0 | 0 | 1024 | 9654 | 9656 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 4 | 512 | 0 | 0 | 0 | 0 | 0 | 2048 | 13481 | 13475 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 6 | 512 | 0 | 0 | 0 | 0 | 0 | 3072 | 11352 | 11350 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 2 | 1024 | 0 | 0 | 0 | 0 | 0 | 2048 | 12372 | 12397 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 4 | 1024 | 0 | 0 | 0 | 0 | 0 | 4096 | 12190 | 12202 | PASS_SHARED_SOURCE_PRODUCTION_API |
| 6 | 1024 | 0 | 0 | 0 | 0 | 0 | 6144 | 12807 | 12817 | PASS_SHARED_SOURCE_PRODUCTION_API |

## Boundary

This is public API and correctness evidence only. It is not SAB CMUX
integration, complete `T_bootstrap/r`, AVX512 optimality, or a final
paper-level speedup claim.
