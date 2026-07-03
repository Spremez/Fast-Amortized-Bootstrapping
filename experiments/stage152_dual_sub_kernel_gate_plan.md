# Stage152 Dual-Sub Kernel Gate Plan

Date: 2026-07-03

## Objective

Test H14-C3 at the smallest meaningful implementation boundary before touching full SAB: can a shared-input dual-subtraction kernel beat two current `pvmtmlwe_sub`-equivalent operations by enough to justify integration?

## Gate

- Correctness: direct output equals `shared - direct_rhs`; NCMUX output equals `rotated - shared`.
- Local performance: fused/current speedup must be at least `1.10x`.
- Predicted body impact: Amdahl projection using current r=6 `cmux_sub/body` share must be at least `1.01x`.
- Scope: this is isolated kernel evidence, not a complete SAB claim.
