# V126: Compact Selector Encryption/Noise Simulator

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: compact selector encryption/noise semantics.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[encryption-noise-simulator]`, `[production-dft-linked]`, `[not-randomized-failure-rate]`, `[not-hot-path]`.
- Main hypothesis: compact selector rows preserve lane-local phase as clean gadget reference plus modeled selector noise.

## Mathematical Definition

For lane q and gadget level t, construct encrypted compact selector rows
`C_shared[t,q]` and `C_body[t,q]` with phase `G_t + e`. For decomposed
digits `d_shared[t,q]` and `d_body[t,q]`, the output phase must be
`sum_t d_shared[t,q] G_t + d_body[t,q] G_t + modeled_noise`.

## Pseudocode

```text
for lane q:
  for level t:
    C_shared[t,q] = Enc_q(G_t + e_shared[t,q])
    C_body[t,q]   = Enc_q(G_t + e_body[t,q])
    out_q += decompose(mask_q,t) * C_shared[t,q]
    out_q += decompose(body_q,t) * C_body[t,q]
  assert phase(out_q) == clean_reference_q + modeled_noise_q
```

## Required Next Gate

Stage127 should implement an isolated compact external-product kernel and
compare it with the current dense MAT external product before any SAB
schedule integration.
