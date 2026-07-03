# V142: AVX512 FMA-Order Fixed Closed Full-MAT Kernel

## Summary

- Parent algorithm: PVW/MAT-SAB.
- Focused module: closed full-MAT external product for PVW_TMLWE.
- Optimization target: reliable MAT-aware AVX512 kernel before full SAB A/B.
- Status labels: `[kernel correctness repaired]`, `[full SAB rerun pending]`.
- Main hypothesis: matching generic AVX512 FMA order removes Stage141 exact-equivalence failures while keeping r=4 unrolled kernel speed useful.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| Generic full-MAT DFT addmul | Same operation with MAT-aware r=2/r=4 AVX512 specialization | implements | Stage142 exact DFT gate |
| Stage141 specialized FMA grouping | Stage142 grouping matching `polynomial_mul_addto_DFT` | preserves operation, changes rounding path | correctness repair |

## Required Next Experiment

Full SAB A/B with `MAT_TRGSW_AVX512_R4_UNROLLED_ROWS=true` against repeated scalar SAB on the same backend, using `T_bootstrap/r` as the primary metric.
