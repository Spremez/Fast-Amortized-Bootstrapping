# MAT-RLWE SAB From-DFT Backend Batching

This is an isolated backend microbench variant, not a production `sab_pvw_*`
algorithm variant.

Delta from current explicit H14 r=6 path:

- keep the same `PVW_TMLWE` torus accumulator semantics;
- keep the same `573440` materialization count;
- compare current item-major `polynomial_DFT_to_torus_add` calls against a
  component-major batched loop order;
- require exact output equality against separate materialization plus add.

Decision: `NEUTRAL_STAGE163_BACKEND_ADD_ALREADY_DOMINANT_BATCHING_NOT_PROMOTED`.

Promotion rule: only a clearly positive microbench can proceed to a guarded
full SAB `T_bootstrap/r` A/B. A neutral or rejected result routes the research
loop to representation-changing exact-state designs.
