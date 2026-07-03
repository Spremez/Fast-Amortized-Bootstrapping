# Stage156 Experiment Plan

Goal: decide whether the Stage155 `from_DFT` frontier can be attacked by a
naive lazy-DFT accumulator.

Inputs:

- `src/mosfhet/include/mosfhet.h` public API signatures.
- `src/mosfhet/src/mattrgsw.c` production MAT external product implementation.
- `src/mosfhet/src/polynomial.c` production gadget decomposition formula.
- `repro/stage155_same_format_frontier_refresh/summary.csv` route precondition.

Correctness gate:

- production scan must show the real EP boundary being evaluated.
- finite decomposition tests must find or fail to find counterexamples under
  MOSFHET-style decomposition.

Performance gate:

- no timing claim is made here; this gate only permits a later implementation
  if the representation is algebraically closed.

Failure handling:

- if naive DFT is not closed, do not implement it in `sab_pvw_*`.
- route to exact decomposed-cache or compact-state feasibility instead.
