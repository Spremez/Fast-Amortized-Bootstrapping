# MAT-RLWE SAB Dual-Sub Full-SAB Candidate

## Delta

`SAB_PVW_DUAL_SUB_CMUX=true` pairs the first `power` direct CMUX updates with
the `power` NCMUX updates in each `RGSW_monomial_mul_state` bit. It does not
change the scalar SAB path, selector format, external-product count, output
semantics, or default build.

## Status

`NEUTRAL_STAGE153_DUAL_SUB_FULLSAB_PAIR_FRACTION_LIMITED`

The candidate is now implemented as an explicit flag. Stage153 shows the
pairable fraction is the limiting factor; full promotion requires repeated
`T_bootstrap/r` evidence above the neutral band.
