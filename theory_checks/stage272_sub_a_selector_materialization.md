# Stage272 Theory Check: Sub_a Selector Materialization

## Current Evidence

Stage271 shows `selector_mat_ep` dominates non-binary `sub_a`, while
`from_DFT + add` has a smaller but visible full-PVW Amdahl ceiling.

## Proof Obligations

1. Prove or test alias safety for `out == addend` before using a fused
   materialization helper in-place.
2. Preserve `phase(acc_pvw.body[q]) == phase(acc_scalar[q])` for include-zero
   and ternary branches.
3. Keep scalar SAB and default PVW/MAT-SAB behavior unchanged unless an
   explicit flag is enabled.
4. Report all speedups as `T_bootstrap/r`, not total batch latency alone.

## Claim Boundary

This is not a novelty claim and not a performance claim. It is a bounded
candidate design derived from measured Stage271 component shares.
