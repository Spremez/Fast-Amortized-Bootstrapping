# Stage165 Validation Plan

Goal: test whether row-streaming the closed full-MAT decompose/DFT/addmul
boundary can beat the current all-row r=6 tiled AVX512 implementation.

Primary endpoint: per external-product call time for `r=6`,
`N=2048`, `items=64`, `runs=5`, `reps=2`.

Variants:

- `current_allrow_tiled_avx`: current production MAT EP with all decomposed
  rows converted to DFT before the r>4 tiled AVX512 addmul.
- `streaming_row_generic`: one row is decomposed, converted, and added to the
  DFT output at a time.

Promotion requires torus equivalence and `current_over_streaming >= 1.02` with
positive minimum across paired runs. If not, the streaming route is closed.
