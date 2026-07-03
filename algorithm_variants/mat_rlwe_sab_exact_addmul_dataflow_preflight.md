# Exact Addmul Dataflow Preflight Candidate

This is a preflight card, not an implementation.

## Candidate: dec-register cache across output tiles

- Parent algorithm: exact full-MAT PVW/MAT-SAB.
- Focused module: `mat_trgsw_mul_pvmtmlwe_DFT_from_dec` r>4 AVX512 addmul.
- Optimization target: complete-SAB `T_bootstrap/r`.
- Status: rejected before code.

## Reason

The candidate reduces duplicate dec-row loads in the current r=6 tile4 kernel,
but its optimistic upper bound does not reach the component speedup needed for
a 3% complete-SAB gain. It also risks register spills.

## Required Future Evidence To Reopen

- measured native counter evidence showing a larger-than-modeled load-store
  bottleneck;
- a new dataflow that reduces selector loads or FMA-equivalent operations, not
  only duplicate dec loads;
- deterministic equivalence and complete-SAB projection before implementation.
