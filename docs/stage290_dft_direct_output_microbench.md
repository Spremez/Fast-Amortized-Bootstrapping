# Stage290 DFT Direct-Output Microbench

Decision: `NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION`.

Stage290 tests `MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT`, an explicit opt-in path
that converts torus rows directly into the DFT output buffer and runs `ifft`
there, avoiding the extra scratch-to-output copy in the Stage289 wrapper.

| metric | value |
|---|---:|
| runs | 5 |
| correct runs | 5 |
| scalar loop mean us | 9.752400 |
| direct array mean us | 9.706200 |
| speedup mean | 1.003200x |
| speedup min | 0.920000x |
| speedup max | 1.067000x |

This is still a microbench-only result. A positive decision only admits Stage291
complete-SAB A/B; it does not prove bootstrapping acceleration by itself.

## Proof Gate

| gate | status | value |
|---|---|---|
| G1_logs | PASS | 5 |
| G2_correctness | PASS | 5/5 |
| G3_microbench | NO_PROMOTION | 0.920000 |
| G4_claim_boundary | PASS | isolated direct-output DFT only |
| G5_decision | NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION | NEUTRAL_STAGE290_DFT_DIRECT_OUTPUT_NO_PROMOTION |
