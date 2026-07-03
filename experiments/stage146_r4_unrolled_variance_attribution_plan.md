# Stage146 r4-Unrolled Variance Attribution Plan

Date: 2026-07-03

## Objective

Explain why Stage144 produced weak repeated complete-SAB evidence for the r4-unrolled AVX512 path.

## Procedure

1. Reuse Stage144 repeated run rows and compute robust paired statistics.
2. Flag r4-only slow samples by relative-median deviation.
3. Run one diagnostic `SAB_PVW_BODY_PROFILE` pair for generic active and r4-unrolled active.
4. Route the next stage without changing scalar/default behavior.

## Boundary

Profile timings are attribution evidence only. Final speedup still requires repeated complete-SAB `T_bootstrap/r` gates.
