# V140: Closed Full-MAT Attribution

## Summary

- Parent algorithm: PVW/MAT-SAB.
- Focused module: closed MAT external product used by CMUX/NCMUX.
- Optimization target: `T_bootstrap/r` through the production closed PVW_TMLWE path.
- Status labels: `[experimental gate]`, `[not full SAB speedup]`.
- Main hypothesis: once diagonal compact is rejected by closure, the valid route is to optimize the closed full-MAT decompose/DFT or addmul component without changing the accumulator invariant.

## Complexity Change

- Input DFT count lower bound: `(r+1)T`.
- Current production count: `(r+1)T`.
- Remaining measurable costs: DFT backend/lazy-state representation and dense `(r+1)^2 T` DFT addmul.
