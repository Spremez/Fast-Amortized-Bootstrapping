# MAT-RLWE SAB Stage250 Exact Dense Gap Refresh

## Summary

- Parent algorithm: exact dense PVW/MAT-SAB.
- Focused module: lower-bound/optimality boundary.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status labels: `scoped_speedup_supported`, `optimality_open`,
  `no_speculative_hotpath_code`.
- Main hypothesis: exact dense remains useful but not proven optimal.

## Required Experiments Before New Code

- isolated equivalence for any changed MAT EP/fromDFT/addmul mechanism;
- native counter evidence for the changed mechanism;
- repeated complete-SAB A/B with `T_bootstrap/r`;
- noise/resource side conditions.
