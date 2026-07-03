# Stage171 Validation Plan

Goal: decide whether compact/shared-output MAT-SAB is an implementation route
or only a new-proof route.

Procedure:

1. Restate the dense MAT versus structured compact term model.
2. Run finite-field checks showing structured matrices are compact-exact while
   random dense matrices remain blocked.
3. Split claim levels into ciphertext exactness, logical selector exactness,
   phase correctness, and complete-SAB speedup.
4. List proof obligations before any implementation.
5. Use Stage170 timings only for an upper-bound component projection.

Acceptance:

- structured finite checks pass for r=2/4/6/8;
- dense counterexamples remain nonzero;
- all proof obligations are explicit and blocking;
- no complete-SAB or theoretical-optimality claim is made.
