# Stage346 Redesign Candidates

## Current Reference: Exact Dense PVW/MAT-SAB

Status: keep as scoped reference.

This path is already implemented and measured at the complete SAB
`T_bootstrap/r` endpoint. It should not be rewritten unless a new profile
budget is recorded.

## Candidate A: Closed Structured Lane-State MAT-SAB

Goal: replace dense off-lane MAT selector work with a state that stores a
shared component plus lane-local or lane-pair deltas, while preserving the
scalar SAB phase invariant for every lane.

Stage347 requirements:

- state tuple and selector rows are explicitly defined;
- CMUX/NCMUX, RGSW monomial, sparse_mul, sub_a, and extract obligations are
  listed;
- finite checker covers r=2 and r=4;
- negative controls fail when off-lane or dummy terms are removed incorrectly.

## Candidate B: Current-Format Dense Lower Bound

Goal: prove that with the existing `MAT_TRGSW_DFT` key/state format, loop-only
off-lane skipping is impossible and dense rows are locally necessary.

This is not a speedup candidate. It is a paper-boundary candidate: it can
justify why the current exact dense implementation is the best result under the
existing format, while leaving new-format algorithms open.

## Candidate C: Non-Binary Extension

Status: defer unless paper scope expands.

Non-binary MAT-SAB already has staged smoke/noise work, but it is not the main
route to a stronger binary MAT-SAB algorithmic claim.
