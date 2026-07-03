# Stage163 Validation Plan

Goal: test whether `from_DFT` backend batching or loop-order vectorization can
lower per-call wall time under the current exact torus-input MAT-RLWE SAB API.

Primary endpoint: `per_call_us` for `N=2048`, `r=6`,
`items=256`, `runs=7`, `reps=3`.

Variants:

1. `separate_current_order`: `polynomial_DFT_to_torus` plus an explicit torus
   add in current item-major order.
2. `backend_current_order`: `polynomial_DFT_to_torus_add` in current
   item-major order.
3. `backend_component_major`: `polynomial_DFT_to_torus_add` with the batch
   loop grouped by component/lane.

Gates:

- exact output equality against `separate_current_order`;
- `backend_add_over_separate` records current backend fused-add value;
- `component_major_batch_over_backend_current >= 1.02` with positive minimum
  is required before any production batching integration;
- all claims remain backend wall-time claims until complete SAB `T_bootstrap/r`
  A/B passes.
