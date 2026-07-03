# Structured Compact MAT-SAB Security/API Variant

Status: blocked for implementation.

The variant would replace the dense MAT selector with a compact structured
selector that omits body-to-body cross terms. Stage173 shows this is algebraic
phase-compatible in a finite toy model under zero-cross constraints.

The variant is not currently an executable SAB algorithm because:

- current dense MAT keygen encrypts all rows;
- deleting zero rows lacks a standard security reduction;
- existing compact output has lane-local masks;
- `sab_pvw_*` requires a closed PVW_TMLWE accumulator with one shared mask.

Executable work should continue on exact full-MAT `sab_pvw_*` until these
conditions are closed by a proof and API design.
