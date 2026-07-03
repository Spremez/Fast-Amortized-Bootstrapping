# Scoped Paper Outline

1. Motivation
   - Sparse amortized bootstrapping and the per-lane cost objective.
2. Algorithm Object
   - Exact PVW/MAT-SAB as r-body shared-mask MAT-RLWE bootstrapping.
3. Complexity and Boundary Model
   - Complete-SAB `T_bootstrap/r`, dense full-MAT costs, and measured Amdahl
     requirements.
4. Implementation
   - Explicit sab_pvw paths, MAT-aware AVX512 variants, active exact route,
     negative ablations.
5. Experiments
   - Complete-SAB A/B, noise/resource gates, split component gates, rejected
     candidates.
6. Claim Boundary
   - Scoped speedup allowed; novelty, optimality, compact implementation
     denied.
7. Future Work
   - Compact/shared-output proof route and new dataflow preflights.
