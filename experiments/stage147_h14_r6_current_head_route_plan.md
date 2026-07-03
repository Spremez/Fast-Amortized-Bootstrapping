# Stage147 H14 r=6 Current-Head Route Plan

Date: 2026-07-03

## Objective

After Stage146 keeps r4-unrolled explicit-only, verify whether the prior H14 backend FromDFT-add r=6 route is still the correct next candidate on current head.

## Gate

- Compare wrapper fused FromDFT-add and backend FromDFT-add under the same r=6 MAT-RLWE full-SAB shape.
- Use `T_bootstrap/r` as the primary smoke metric.
- Use `SAB_PVW_BODY_PROFILE=true` only for attribution, not final latency claims.
- Keep scalar SAB and default PVW/MAT-SAB behavior unchanged.

## Promotion Boundary

A one-run current-head smoke can only route Stage148. It cannot replace Stage88 repeated/noise/resource gates or establish final paper-level speedup.
