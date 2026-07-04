# Stage252 Report

Decision: `PASS_STAGE252_NONBINARY_MAT_SELECTOR_KEY_SKELETON_READY_ISOLATED_EQUIVALENCE`.

The skeleton keeps the current binary distance-bit selector family and adds
optional MAT selector families for `s_coff` and `s_sign`. For target
`h=39,r_prec=7`, binary has 280 distance-bit selector objects per input-key
component; include-zero or ternary adds 39 more, and the stress case with both
families has 358. These are selector-object counts only, not byte, noise, or
speed evidence.

Production SAB/PVW source files remain unchanged. The only admitted next step
is isolated `sub_a` equivalence for include-zero and ternary equations.
