# mat_rlwe_sab_stage236_selected_binary_matrix

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping path.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [selected binary matrix checked], [broader claims blocked].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared-mask SAB work across
  r body lanes and improves per-lane full bootstrapping throughput versus
  repeated scalar SAB for the selected binary parameter rows.

## Matrix Scope

The checked rows are `SET_4_5_2048` r=2/r=4 and `SET_2_3_4096` r=2/r=4. This
is not an all-parameter, non-binary, compact-route, novelty, or theoretical
optimality statement.
