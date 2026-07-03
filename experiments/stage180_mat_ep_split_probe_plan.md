# Stage180 Plan

Goal: split the current exact MAT EP/subdecomp hot block before granting any
new AVX512 implementation permission.

Correctness gate:

- Combined current output must match split decompose -> DFT -> addmul output.

Performance gate:

- Record per-call timings and perf counters for `sub_decompose`,
  `torus_to_dft_rows`, `addmul_from_dec_dft`, and `combined_current`.
- A later implementation branch needs a projection to at least 3% complete-SAB
  gain.

Failure handling:

- Missing remote credentials, compile failure, run failure, or correctness
  failure all block code work.
