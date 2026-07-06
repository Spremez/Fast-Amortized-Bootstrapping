# Stage336 Exact PVW/MAT Frontier Model

Let the measured complete-SAB endpoint be `T_bootstrap/r`.  Stage336 keeps the
comparison at the algorithm layer: one r-body PVW/MAT-SAB execution versus r
repeated scalar SAB executions.

The frontier is constrained to closed exact-state changes.  A candidate is
admissible only if it preserves:

- the shared mask and r body lanes;
- lane phase equivalence to scalar references;
- the same selector semantics;
- scalar SAB default behavior.

The compact selector route is excluded from hot-path work because its current
state is not expressive enough for neighbor/cross-body selector equations.
The r4-unrolled MAT kernel is excluded because full-SAB A/B was neutral.

The direct IFFT lifecycle remains admissible because Stage288/307 identify it
as a measured profile component while preserving the exact MAT representation.
