# Stage325 Selector-Transpose Resource Probe Plan

Input decision: `PASS_STAGE324_SELECT_SELECTOR_TRANSPOSE_RESOURCE_PREFLIGHT_COMPACT_REMAINS_FROZEN`.

Goal: execute a concrete, bounded experiment for selector-transposed key
layout before any SAB hot-path code.

Tasks:

- allocate current row/poly selector layout and coefficient-blocked
  selector-transposed layout for r=4, k=1, l=1, N=2048;
- verify exact dense addmul equality against the current layout;
- measure transposed-view build cost and memory ratio;
- microbench current layout versus transposed layout under the same AVX512
  arithmetic;
- project complete-SAB value using measured dense share
  `0.212353`.

Promotion gate:

- correctness must pass;
- isolated dense speedup must be at least `1.048905` to
  project 1% complete-SAB `T_bootstrap/r` improvement;
- duplicate-view key memory must be explicitly reported and cannot be hidden
  inside the speedup claim.

Failure handling: if Stage325 is neutral or negative, close selector-layout
work and move to final claim/literature packaging or a user-supplied formal
compact proof route.
