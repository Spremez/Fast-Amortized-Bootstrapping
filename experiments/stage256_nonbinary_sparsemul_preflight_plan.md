# Stage256 Non-Binary Sparse_Mul Preflight Plan

## Objective

Design and gate non-binary sparse_mul integration before writing production
code.

## Gates

- Stage255 actual isolated selector gate must pass.
- Source boundaries and required deltas must be explicit.
- Finite multi-round sparse schedule probe must pass positive and negative
  controls.
- Count/noise/resource recurrence obligations must be recorded.
- Stage257 permission is explicit new path only; no default binary changes.
