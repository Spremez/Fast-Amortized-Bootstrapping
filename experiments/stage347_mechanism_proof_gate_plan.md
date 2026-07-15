# Stage347 Mechanism Proof Gate Plan

Goal: convert the open MAT-SAB new-algorithm question into one falsifiable
mechanism gate.

## Required Entry

Stage347 must start from Stage346. It cannot edit SAB hot-path code.

## Route A: Closed Structured State

Tasks:

- define the candidate accumulator state and selector key shape;
- write the per-step lane invariant;
- implement a finite checker for r=2 and r=4;
- include negative controls for invalid off-lane skipping and invalid
  shared-output collapse;
- map every passing equation to the later MOSFHET integration obligation.

Promotion gate:

- zero phase mismatches in the finite checker;
- negative controls fail;
- resource/key/noise obligations are named for Stage349.

## Route B: Current-Format Lower Bound

Tasks:

- define the restricted current-format model;
- prove or check why dense off-lane terms are required;
- state exactly what the lower bound does not cover.

Promotion gate:

- assumptions are explicit;
- result is suitable for a claim-boundary section, not a new speedup claim.

## Exit Policy

If neither route can produce a checker/proof artifact, the mechanism route is
closed and the project proceeds with the scoped exact-dense systems paper.
