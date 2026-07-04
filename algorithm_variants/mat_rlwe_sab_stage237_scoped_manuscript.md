# mat_rlwe_sab_stage237_scoped_manuscript

## Summary

- Parent algorithm: 2025/686 sparse amortized bootstrapping.
- Focused module: exact dense PVW/MAT-SAB complete bootstrapping.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: [selected binary matrix checked], [manuscript package ready], [broader claims blocked].
- Main hypothesis: exact dense PVW/MAT-SAB amortizes shared SAB work across r
  body lanes and improves per-lane full bootstrapping throughput versus
  repeated scalar SAB on selected binary parameter rows.

## Required Next Work

- Source-verified citation package for paper-facing prose.
- Optional native-counter attribution if implementation mechanism claims are
  needed.
- Separate proof/experiment gates for non-binary, compact, or theoretical
  optimality claims.
