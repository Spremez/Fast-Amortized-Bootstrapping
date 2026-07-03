# V128: Compact EP API Boundary

## Summary

- Parent algorithm: PVW/MAT-SAB r-body research track.
- Focused module: MOSFHET-adjacent compact EP API boundary.
- Optimization target: eventual complete-SAB `T_bootstrap/r`.
- Status labels: `[api-boundary]`, `[production-dft-linked]`, `[not-production-header]`, `[not-hot-path]`.
- Main hypothesis: the isolated compact EP kernel can be wrapped in explicit selector/output/scratch ownership without losing correctness or count invariants.

## API Shape

```text
CompactEpSelectorDft compact_ep_selector_dft_alloc(T, Bg_bit, k, r, N)
CompactEpOutputDft   compact_ep_output_dft_alloc(N)
CompactEpScratch     compact_ep_scratch_alloc(N)
int compact_ep_selector_set_row_from_torus(selector, t, q, rows...)
int compact_ep_kernel_dft_api(out, source_shared, source_body, selector, q, scratch)
```

## Required Next Gate

Stage129 should benchmark the isolated API-shaped kernel and attribute
time to decomposition, torus-to-DFT conversion, and DFT multiply-add before
any production MOSFHET or SAB integration.
