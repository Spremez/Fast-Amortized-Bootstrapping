# V120: Vector-Shared Real Struct Prototype

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: lane-local vector-shared external-product object.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[real-struct-prototype]`, `[phase-supported]`, `[not-DFT]`, `[not-hot-path]`.
- Main hypothesis: vector-shared lane-local objects can preserve polynomial phase correctness before DFT integration.

## Mathematical Definition

For lane q, define two ciphertext-like objects `(a_shared_q,b_shared_q)`
and `(a_body_q,b_body_q)`. Phase is computed as
`b - a*s_q` using negacyclic multiplication. The combined lane output is
`d_shared * phase(shared_q) + d_body_q * phase(body_q)`.

## Pseudocode

```text
Input: r, N, seed
Output: phase/noise gate status
1. Allocate r lane secrets and 2r ciphertext objects.
2. Encrypt shared/body messages with negacyclic mask*secret products.
3. Decrypt phases and compare with dense vector-shared reference.
4. Repeat with bounded coefficient noise.
5. Stop before DFT or SAB integration.
```

## Delta From Stage119

| Stage119 | Stage120 | Status |
| --- | --- | --- |
| coefficient-level toy equations | allocated C structs and polynomial arrays | implemented in repro prototype |
| scalar multiplication model | negacyclic polynomial multiplication | phase gate passed |
| toy noise bound | coefficient noise through phase decrypt | bounded in prototype |

## Required Next Experiments

- DFT/conversion prototype;
- structured external-product arithmetic prototype;
- r=2/4 equivalence against dense reference;
- only then isolated MOSFHET-adjacent kernel integration.
