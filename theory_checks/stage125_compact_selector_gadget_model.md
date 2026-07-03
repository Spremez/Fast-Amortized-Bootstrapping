# Stage125 Compact Selector Gadget Model

Date: 2026-07-03

Stage125 checks the finite gadget-injection boundary after Stage124's type
API skeleton. For each lane q and gadget level t, the probe decomposes
the lane-local mask and body polynomials with MOSFHET
`polynomial_decompose_i`. It then applies two compact selector rows:
`shared[t,q]` injects the diagonal gadget into the lane-local mask
component and `body[t,q]` injects it into the lane-local body component.

The gate compares coefficient-domain gadget application with production
SPQLIOS DFT multiply-add. This is not selector encryption or a noise proof.

## Gadget Rows

| backend | r | N | T | Bg | seed | DFT mismatches | negative failures | max gap | tolerance | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| spqlios | 2 | 1024 | 7 | 7 | 0 | 0 | 2048 | 8192 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 2 | 1024 | 7 | 7 | 1 | 0 | 2048 | 8192 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 4 | 1024 | 7 | 7 | 0 | 0 | 4096 | 7680 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 4 | 1024 | 7 | 7 | 1 | 0 | 4096 | 8192 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 6 | 1024 | 7 | 7 | 0 | 0 | 6144 | 10240 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 6 | 1024 | 7 | 7 | 1 | 0 | 6144 | 9216 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 2 | 2048 | 7 | 7 | 0 | 0 | 4096 | 9216 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 4 | 2048 | 7 | 7 | 0 | 0 | 8192 | 9216 | 16384 | PASS_COMPACT_SELECTOR_GADGET |
| spqlios | 6 | 2048 | 7 | 7 | 0 | 0 | 12288 | 8192 | 16384 | PASS_COMPACT_SELECTOR_GADGET |

## Layout Rows

| r | N | selector ratio | dec overhead | selector+dec ratio | status |
|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 1.125000 | 1.333333 | 1.000000 | PASS_LAYOUT_MODEL |
| 2 | 1024 | 1.125000 | 1.333333 | 1.000000 | PASS_LAYOUT_MODEL |
| 4 | 1024 | 1.562500 | 1.600000 | 1.250000 | PASS_LAYOUT_MODEL |
| 4 | 1024 | 1.562500 | 1.600000 | 1.250000 | PASS_LAYOUT_MODEL |
| 6 | 1024 | 2.041667 | 1.714286 | 1.555556 | PASS_LAYOUT_MODEL |
| 6 | 1024 | 2.041667 | 1.714286 | 1.555556 | PASS_LAYOUT_MODEL |
| 2 | 2048 | 1.125000 | 1.333333 | 1.000000 | PASS_LAYOUT_MODEL |
| 4 | 2048 | 1.562500 | 1.600000 | 1.250000 | PASS_LAYOUT_MODEL |
| 6 | 2048 | 2.041667 | 1.714286 | 1.555556 | PASS_LAYOUT_MODEL |

## Boundary

This stage does not encrypt compact selector rows, model cryptographic
noise, implement AVX512 kernels, integrate SAB schedules, or measure
complete `T_bootstrap/r`.
