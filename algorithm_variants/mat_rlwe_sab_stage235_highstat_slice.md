# mat_rlwe_sab_stage235_highstat_slice: SET_2_3_4096 r=2

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping path.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [experiment checked for one high-stat slice], [full matrix incomplete].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared-mask SAB work across
  r body lanes and improves per-lane full bootstrapping throughput versus
  repeated scalar SAB for `SET_2_3_4096`, r=2.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| r independent scalar SAB calls | one exact dense PVW/MAT-SAB call with r bodies | amortizes shared selector/schedule work while preserving lane outputs | Stage235 high-stat slice |
| scalar comparison by total time | amortized `T_bootstrap/r` comparison | aligns with processed plaintext lane/bit count | Stage235 metric gate |

## Required Next Experiments

- `SET_2_3_4096` r=4 high-stat slice with the same 10-run/20-seed/resource gate.
- Scoped manuscript table after the added-parameter matrix is complete.
- Separate design gates for non-binary, compact, or theoretical-optimal claims.
