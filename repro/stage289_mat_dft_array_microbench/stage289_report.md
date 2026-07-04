# Stage289 MAT DFT Array Microbench

Decision: `NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION`.

Stage288 found `torus_to_dft` as the largest measured MAT EP split component.
Stage289 isolates the existing `polynomial_torus_to_DFT_array` wrapper against
the scalar per-row loop for the MAT-SAB r=4 shape: rows=5, N=2048.

## Result

| metric | value |
|---|---:|
| runs | 3 |
| correct runs | 3 |
| scalar loop mean us | 10.838000 |
| array wrapper mean us | 11.405667 |
| speedup mean | 0.948000x |
| speedup min | 0.923000x |
| speedup max | 0.995000x |

## Interpretation

The wrapper is correctness-clean but is not promoted unless every repeated run
beats the scalar loop by at least 1.02x. This is a microbench-only gate and does
not claim complete SAB acceleration. If the decision is neutral, the next DFT
candidate must reduce the conversion lifecycle itself, not merely wrap the same
row-wise reverse FFT work.

## Proof Gate

| gate | status | value |
|---|---|---|
| G1_logs | PASS | 3 |
| G2_correctness | PASS | 3/3 |
| G3_performance | NO_PROMOTION | 0.923000 |
| G4_claim_boundary | PASS | isolated torus_to_DFT wrapper only |
| G5_decision | NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION | NEUTRAL_STAGE289_DFT_ARRAY_WRAPPER_NO_PROMOTION |
