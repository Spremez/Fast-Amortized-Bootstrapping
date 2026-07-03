# Stage183 Plan

Goal: screen addmul dataflow candidates before implementation.

Rules:

- Existing MAT-aware AVX512 code counts as implemented baseline, not future
  work.
- A new branch must be a new mechanism, not a renamed tile/fulltile/bodymajor
  variant.
- Kernel-only or source-only arguments cannot become complete-SAB claims.

Decision: no code permission; route to exact-route closeout or proof-gated
compact work.
