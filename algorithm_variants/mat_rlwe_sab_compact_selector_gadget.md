# V125: Compact Selector Gadget Injection

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: compact selector decomposition and diagonal gadget injection.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[gadget-smoke]`, `[production-dft-linked]`, `[not-encrypted]`, `[not-hot-path]`.

## Pseudocode

```text
for lane q:
  for gadget level t:
    d_shared[t,q] = decompose(mask_q, t)
    d_body[t,q]   = decompose(body_q, t)
    out.a[q] += d_shared[t,q] * G_t
    out.b[q] += d_body[t,q] * G_t
```

The production DFT path must match this coefficient reference. The
body-only negative control must fail because shared-mask gadget rows are
required for lane-local ciphertext reconstruction.

## Required Next Gate

Stage126 must add compact selector encryption/noise modeling. If encryption
requires restoring dense `MAT_TRGSW_DFT` rows, this branch must be
rejected or redesigned before any SAB integration.
