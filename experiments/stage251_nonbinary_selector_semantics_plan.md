# Stage251 Non-Binary Selector Semantics Plan

## Objective

Define the scalar non-binary equations and decide whether current PVW/MAT-SAB
can implement them.

## Gates

- Source facts must show scalar `s_sign/s_coff` semantics.
- Finite semantics probes must pass positive equations and the binary negative
  control must fail as expected.
- Current PVW source must not be silently promoted when `s_sign/s_coff` are
  missing.
- Production code is admitted only after a separate selector/key skeleton and
  isolated equivalence stage.
