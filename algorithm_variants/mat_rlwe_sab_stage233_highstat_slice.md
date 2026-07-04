# mat_rlwe_sab_stage233_highstat_slice: SET_4_5_2048 r=4

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping path.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [experiment checked for one high-stat slice], [matrix incomplete].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared-mask work across r
  body lanes and improves per-lane full bootstrapping throughput versus repeated
  scalar SAB for `SET_4_5_2048`, r=4.

## Delta From Original Algorithm

| Original component | Variant component | Relationship | Evidence/status |
| --- | --- | --- | --- |
| r independent scalar SAB executions | one exact dense PVW/MAT-SAB execution with r body lanes | amortizes shared state and key flow | `repro/stage233_set_4_5_2048_r4_highstat_slice/performance_stats.csv` |
| scalar-only side accounting | PVW/MAT and scalar resource accounting | reports keygen/key/RSS side cost | `repro/stage233_set_4_5_2048_r4_highstat_slice/resource_comparison.csv` |
| preflight statistics | 10-run/20-seed slice | improves statistical support for one slice | `repro/stage233_set_4_5_2048_r4_highstat_slice/gate_matrix.csv` |

## Required Next Experiments

- Remaining high-stat matrix slices if this result is used in a broad added
  parameter table.
- Non-binary or compact design gates before any broader algorithmic claim.
