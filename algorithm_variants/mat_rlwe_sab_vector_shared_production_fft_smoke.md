# V123: Production FFT Smoke for Vector-Shared Structured EP

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: production MOSFHET torus/FFT boundary for structured EP.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[production-fft-smoke]`, `[not-hot-path]`, `[not-keygen]`, `[not-complete-sab]`.
- Main hypothesis: Stage122 structured EP arithmetic survives the production MOSFHET SPQLIOS DFT boundary within a fixed 1024 torus-unit tolerance.

## Mathematical Definition

For each lane q, the smoke constructs active shared/body terms
`D_i * C_i` in coefficient domain and in production DFT domain. It compares
the decrypted phases after inverse transform. The dense reference is the
message-domain phase because clean ciphertexts are constructed as
`body = mask * secret + message`.

## Pseudocode

```text
Input: r, N, seed
Output: production FFT smoke status
1. Build libmosfhet.a with FFT_LIB=spqlios.
2. Generate small torus secret, digit, mask, message, and noise polynomials.
3. Build coefficient structured EP output using MOSFHET naive torus multiplication.
4. Build production DFT structured EP output using MOSFHET DFT routines.
5. Convert DFT output to torus and decrypt phases.
6. Compare coefficient phase to message reference exactly.
7. Compare DFT phase to coefficient phase within tolerance.
8. Keep body-only off-lane skipping as a failing negative control.
```

## Complexity Change

This smoke does not add a new complexity claim. It preserves Stage122 term
ratios inside a production FFT API test and opens only type/API boundary
sketching.

## Required Experiments

- MOSFHET-adjacent vector-shared type/API sketch;
- gadget decomposition compatibility;
- real selector/key construction;
- isolated kernel equivalence;
- full SAB `T_bootstrap/r` only after the above pass.
