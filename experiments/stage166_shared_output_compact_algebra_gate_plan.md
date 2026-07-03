# Stage166 Validation Plan

Goal: decide whether shared-output compact SAB can be treated as a generic
implementation optimization, or whether it requires a new keygen/proof route.

Model:

- Dense MAT selector: arbitrary `(1+r) x (1+r)` matrix over a finite field.
- Compact shared-output lane-local selector: shared mask output can depend on
  all inputs, but body lane q depends only on shared input and body q.

Gate:

- random dense finite-field matrices must produce nonzero mismatches under the
  compact projection;
- if mismatches exist for all tested r/trials, generic compact exactness is
  blocked and structured keygen proof is required.
