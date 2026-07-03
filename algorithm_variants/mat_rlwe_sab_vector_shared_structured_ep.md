# V122: Vector-Shared Structured External Product

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: vector-shared selector/external-product arithmetic.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[structured-ep-prototype]`, `[phase-supported]`, `[not-production-fft]`, `[not-hot-path]`.
- Main hypothesis: vector-shared objects can apply selector digits with two EP terms per lane while matching dense clean-reference phase.

## Mathematical Definition

For lane q, let `C_shared,q` and `C_body,q` be vector-shared ciphertext-like
objects. The structured EP output is

```text
Out_q = D_shared,q * C_shared,q + D_body,q * C_body,q.
```

The dense clean reference uses rows `0..r`, but off-lane rows carry zero
message. Stage122 requires `phase(Out_q)` to equal the dense clean
reference phase for every tested coefficient. It separately requires the
coefficient-domain structured EP and exact DFT-domain structured EP to
match.

## Pseudocode

```text
Input: r, N, seed
Output: structured EP arithmetic gate status
1. Generate lane secrets, dense clean rows, and vector-shared clean/noisy rows.
2. Build dense clean reference output using all rows.
3. Build structured output using only shared/body rows per lane.
4. Build the same structured output through exact DFT multiply-add.
5. Decrypt phases and compare dense vs structured and coefficient vs DFT.
6. Check noisy structured output against a conservative bound.
7. Verify body-only off-lane skip fails as a negative control.
```

## Complexity Change

- Dense EP arithmetic terms: `r(r+1)` per packed object in this prototype.
- Structured EP arithmetic terms: `2r`.
- Term ratio: `(r+1)/2`; this is arithmetic potential only.
- Selector-polynomial ratio: `(r+1)^2/(4r)`.
- What must be measured later: production FFT conversion, gadget
  decomposition, real key size, cache behavior, SAB schedule integration,
  and full `T_bootstrap/r`.

## Paper Contribution Candidate

`[experimental-gate-only]` Exact arithmetic evidence supports continuing
the vector-shared MAT-RLWE SAB branch. It is not yet a paper-level
bootstrapping acceleration claim.
