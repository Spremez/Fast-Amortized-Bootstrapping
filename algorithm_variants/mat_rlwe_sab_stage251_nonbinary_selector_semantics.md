# MAT-RLWE SAB Stage251 Non-Binary Selector Semantics

## Candidate Status

- Parent route: exact dense binary PVW/MAT-SAB.
- Proposed extension: ternary/include-zero PVW/MAT-SAB.
- Current decision: blocked for production implementation.

## Required Delta

The extension needs MAT versions of scalar `s_sign` and `s_coff`, a keygen
path, isolated `sub_a` equivalence for every body lane, then full SAB
`T_bootstrap/r`, noise, and resource gates.

## Failure Mode Captured

The current binary PVW update performs `X^a` for every nonzero coefficient. For
ternary negative coefficients the scalar target is `X^{-a}`, so routing ternary
through `sab_pvw_sub_a_binary` is semantically wrong.
