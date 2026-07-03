# V121: Vector-Shared Exact DFT Conversion Prototype

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: vector-shared MAT-RLWE conversion boundary.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[conversion-prototype]`, `[phase-supported]`, `[not-production-fft]`, `[not-hot-path]`.
- Main hypothesis: vector-shared lane-local objects can preserve phase after exact frequency-domain conversion.

## Mathematical Definition

For each lane q and ciphertext-like object `(a_q,b_q)`, define
`A_q = DFT(a_q)`, `B_q = DFT(b_q)`, and `S_q = DFT(s_q)` over
`Z_12289[X]/(X^N+1)`. The DFT-domain phase is
`P_q = B_q - A_q*S_q`. The gate requires
`InvDFT(P_q) = b_q - a_q*s_q` for clean and noisy objects.

## Pseudocode

```text
Input: r, N, seed
Output: exact conversion gate status
1. Allocate the Stage120 vector-shared real struct object.
2. Encrypt clean and bounded-noise shared/body objects.
3. Find an exact 2N-th root modulo 12289.
4. Round-trip every mask/body/secret polynomial through DFT and inverse DFT.
5. Compute phase in coefficient domain and DFT domain.
6. Compare clean/noisy phases and digit-sum noise bounds.
7. Stop before structured external-product or SAB integration.
```

## Delta From Stage120

| Stage120 | Stage121 | Status |
| --- | --- | --- |
| coefficient-domain phase only | exact DFT-domain phase and inverse conversion | implemented in repro prototype |
| no transform round-trip | mask/body/secret DFT round-trip | gate required |
| real struct layout bound | DFT polynomial-count layout bound | recorded |

## Required Next Experiments

- structured vector-shared external-product arithmetic prototype;
- r=2/4/6 dense-reference equivalence for selector application;
- production torus/FFT conversion smoke;
- isolated MOSFHET-adjacent kernel only after the above pass.
