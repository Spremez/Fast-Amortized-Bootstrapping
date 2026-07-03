# MAT-RLWE/PVW-SAB Stage150 Final Scope

Date: 2026-07-03

## Algorithm Object

The current promoted object is not a replacement for scalar `sab_rlwe_bootstrap`. It is an explicit `sab_pvw_*` H14 r=6 path with:

- `r=6` independent LUT/SAB body lanes packed into one MAT-RLWE/PVW state;
- shared-mask external-product processing;
- active-buffer sparse-schedule state;
- backend FromDFT-add materialization;
- default-false flags and scalar/default isolation.

## Comparison Unit

`T_complete_bootstrap(6)/6` is compared against repeated scalar SAB per lane.

## Current Non-Goals

Stage150 does not promote default behavior, does not prove an r-body lower bound, and does not claim novelty.
