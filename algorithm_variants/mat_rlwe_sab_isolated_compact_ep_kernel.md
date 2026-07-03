# V127: Isolated Compact External-Product Kernel

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: isolated compact external-product kernel.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[isolated-kernel]`, `[production-dft-linked]`, `[not-api]`, `[not-hot-path]`.
- Main hypothesis: Stage126 compact selector encryption/noise semantics can be factored into a reusable DFT kernel without losing phase/noise correctness or the count model.

## Mathematical Definition

For lane q, the compact EP kernel computes:

```text
Out_q = sum_t D_shared[t,q] * C_shared[t,q] + D_body[t,q] * C_body[t,q]
```

where `D_*` are decomposed lane-local source digits and `C_*` are compact
encrypted selector rows.

## Pseudocode

```text
Input: source_shared_q, source_body_q, compact selector rows
Output: DFT mask/body output for lane q
for t in 0..T-1:
  dec_shared = decompose(source_shared_q, t)
  dec_body   = decompose(source_body_q, t)
  out_a += DFT(dec_shared) * shared_a[t,q]
  out_b += DFT(dec_shared) * shared_b[t,q]
  out_a += DFT(dec_body) * body_a[t,q]
  out_b += DFT(dec_body) * body_b[t,q]
```

## Required Next Gate

Stage128 should define MOSFHET-adjacent structs/function signatures and
compile-check API ownership around this kernel. SAB integration remains
blocked until API, multi-seed noise, and isolated microbench gates pass.
