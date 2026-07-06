# Stage337 Frontier Correction

Decision: `PASS_STAGE337_FRONTIER_CORRECTED_NO_REPEAT_FAILED_CANDIDATES`.

This stage prevents a theory loop.  The direct IFFT lifecycle candidate selected
by Stage336 is not reopened, because prior isolated batch5 IFFT implementations
were correct but slower.  Digit narrowing, r4-unrolled rows, and selector
transpose are also already neutral or closed under complete-SAB or projection
gates.

The active goal remains open, but the allowed next work is narrower and more
honest: either introduce a genuinely new measured mechanism, provide a formal
compact/structured proof, or package the scoped `T_bootstrap/r` result with the
negative ablations.

## Gates

| gate | status | metric | value | interpretation |
| --- | --- | --- | --- | --- |
| G1_stage336_input | PASS | Stage336 frontier | present | Stage337 corrects Stage336 candidate selection with earlier closure evidence. |
| G2_no_repeat_candidates | PASS | closed candidate families | ifft;digit;r4_unrolled;selector_transpose | Do not rerun old candidates unless a new mechanism changes the hypothesis. |
| G3_exact_dense_closeout | PASS | Stage326 frontier | closed_under_current_evidence | Exact dense/local routes are closed under current evidence, not globally optimal. |
| G4_compact_boundary | PASS | Stage335 compact | denied | Compact/structured route requires proof, not hot-path coding. |
| G5_decision | PASS_STAGE337_FRONTIER_CORRECTED_NO_REPEAT_FAILED_CANDIDATES | stage decision | no_repeat_failed_candidates | Next execution must supply a new mechanism/proof or stay in scoped claim/parameter work. |
