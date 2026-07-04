# Stage251 Report

Decision: `PASS_STAGE251_NONBINARY_SELECTOR_SEMANTICS_PREFLIGHT_BLOCKS_IMPLEMENTATION`.

Scalar SAB has explicit selector semantics for non-binary branches: include-zero
uses `s_coff` to choose identity versus `X^a`, and ternary uses `s_sign` to
choose `X^a` versus `X^-a`. Current PVW/MAT-SAB does not have corresponding
MAT selector families and remains binary-only by constructor and harness guard.

The finite probe confirms the equation boundary, including the negative control
that a binary `X^a` update fails for ternary negative coefficients. Production
implementation is therefore denied. The next executable step is a
non-production MAT selector/key skeleton for `s_sign` and `s_coff`.
