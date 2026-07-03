# Stage128 Compact EP API Boundary Model

Date: 2026-07-03

Stage128 defines MOSFHET-adjacent API shapes around the Stage127 isolated
kernel:

```text
CompactEpSelectorDft
CompactEpOutputDft
CompactEpScratch
compact_ep_selector_set_row_from_torus(...)
compact_ep_kernel_dft_api(...)
```

The gate checks ownership, metadata, invalid-lane rejection, no API-owned
allocation inside the hot kernel, and the same component/phase/noise
equivalence as Stage127.

## API Rows

| backend | r | N | seed | ownership | metadata | guards | kernel allocs | component mismatches | phase mismatches | noise mismatches | negative failures | max component gap | max phase gap | DFT ratio | total ratio | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 512 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1024 | 11267 | 11269 | 1.125000 | 1.000000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 2 | 512 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1024 | 8922 | 8914 | 1.125000 | 1.000000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 4 | 512 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2048 | 11570 | 11572 | 1.562500 | 1.250000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 4 | 512 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2048 | 11364 | 11371 | 1.562500 | 1.250000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 6 | 512 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3072 | 14605 | 14608 | 2.041667 | 1.555556 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 6 | 512 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3072 | 10412 | 10418 | 2.041667 | 1.555556 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 2 | 1024 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2048 | 12598 | 12623 | 1.125000 | 1.000000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 4 | 1024 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4096 | 12921 | 12909 | 1.562500 | 1.250000 | PASS_COMPACT_EP_API_BOUNDARY |
| spqlios | 6 | 1024 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6144 | 12921 | 12936 | 2.041667 | 1.555556 | PASS_COMPACT_EP_API_BOUNDARY |

## Boundary

This is not a production MOSFHET header change, AVX512 specialization,
randomized noise/failure-rate proof, SAB schedule integration, or complete
`T_bootstrap/r` benchmark.
