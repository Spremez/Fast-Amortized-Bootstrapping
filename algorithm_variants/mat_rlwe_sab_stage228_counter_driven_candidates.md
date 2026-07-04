# Stage228 Candidate Algorithm Cards

## H228-C1-r6-dec-reuse-addmul

- Parent algorithm: exact dense MAT/PVW-SAB.
- Focused module: `mat_trgsw_mul_pvmtmlwe_DFT_k1_l1_rgt4_tiled_avx512`.
- Main hypothesis: a new r=6 addmul dataflow could reduce duplicated dec-row loads.
- Status labels: probe-only, experiment-pending, no hot-path permission.
- Required gate: isolated addmul projection plus complete-SAB `T_bootstrap/r`.

## H228-C2-batched-direct-from-dft-add

- Parent algorithm: exact dense MAT/PVW-SAB.
- Focused module: backend direct FromDFT+add.
- Main hypothesis: a true multi-row backend primitive could reduce materialization.
- Status labels: blocked until backend primitive exists.

## H228-C3-sub-decomp-fusion-refresh

- Parent algorithm: exact dense MAT/PVW-SAB.
- Focused module: existing `SAB_PVW_SUB_DECOMP_FUSION` flag.
- Main hypothesis: existing full-SAB positive evidence may merit refresh, but no new AVX512 sub-decompose code is allowed.
- Status labels: existing-flag refresh only.
