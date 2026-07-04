# mat_rlwe_sab_stage234_highstat_slice: SET_4_5_2048 r=2

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping path.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [experiment checked for one high-stat slice], [SET_4_5_2048 r=2/r=4 complete], [full matrix incomplete].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared-mask work across r
  body lanes and improves per-lane full bootstrapping throughput versus repeated
  scalar SAB for `SET_4_5_2048`, r=2.

## Required Next Experiments

- `SET_2_3_4096` r=2/r=4 high-stat slices if the broader added-parameter matrix
  is used in a main claim.
- Non-binary or compact design gates before any broader algorithmic claim.
