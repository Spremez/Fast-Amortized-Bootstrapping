# Stage173 Validation Plan

Goal: advance structured compact MAT-SAB without falling into pure theory or
premature implementation.

Protocol:

- field: `65537`;
- r values: `2,4,6`;
- trials per r: `64`;
- SAB-like toy schedule: `in_N=16`, `r_prec=4`;
- phase gate: compact and structured dense outputs must match exactly;
- negative gate: an injected body-cross term must create a mismatch;
- noise gate: compact omitted-zero toy variance must be no larger than dense
  zero-padded toy variance.

Failure handling:

- phase failure blocks compact route;
- noise failure blocks compact route;
- pass keeps the route alive but does not permit implementation or paper claim.
