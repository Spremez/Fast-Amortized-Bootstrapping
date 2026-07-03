# Stage153 Dual-Sub Full-SAB Gate Plan

## Objective

Integrate the Stage152 shared-input dual-sub kernel behind `SAB_PVW_DUAL_SUB_CMUX`
and test it at the complete SAB endpoint `T_bootstrap/r`.

## Gates

- Correctness: control and dual-sub complete SAB smoke must pass.
- Pair count: dynamic `dual_sub_pair_calls` must equal `(h+1)*(2^r_prec-1)`.
- Performance: compare dual-sub against the same H14 r=6 backend path.
- Claim boundary: this is a smoke gate; repeated statistics are required for
  any positive promotion.
