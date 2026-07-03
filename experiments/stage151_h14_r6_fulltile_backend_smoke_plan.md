# Stage151 H14 r=6 Fulltile Backend Smoke Plan

Date: 2026-07-03

## Objective

Test one concrete post-Stage150 implementation candidate: compose the Stage148 H14 backend FromDFT-add path with the r=6 fulltile MAT external-product layout.

## Hypothesis

Holding scalar/default behavior, active-buffer fusion, backend FromDFT-add, parameter set, and backend fixed, replacing the r>4 tile4 MAT layout with r=6 fulltile should improve complete SAB `T_bootstrap/r` only if its MAT EP locality gain survives the full SAB schedule.

## Gate

- correctness: both backend tile4 and backend fulltile full-SAB smoke pass;
- schedule: MAT EP call count remains 573440 and copyback remains zero;
- performance: `T_bootstrap/r` ratio above one is routing evidence; at least 1.01 plus MAT EP improvement is required to open a repeated Stage152 gate;
- claim policy: no default-path or paper-level wording from this smoke.
