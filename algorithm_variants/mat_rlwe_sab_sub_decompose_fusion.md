# MAT-RLWE SAB Sub-Decompose Fusion Variant

Candidate:

```text
Add a guarded internal path that accepts two PVW_TMLWE operands and computes
DFT gadget digits for their difference directly.
```

Required later production shape if Stage157 is positive:

- keep scalar/default SAB unchanged;
- add a new explicit flag;
- preserve `sab_pvw_CMUX_from_sub_internal` as reference;
- validate exact per-step phase equality;
- run complete SAB `T_bootstrap/r` A/B.

Stage157 itself is only an isolated preflight.
