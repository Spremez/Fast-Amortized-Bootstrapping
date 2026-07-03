# Stage115 Lane-Local Toy C Resource Gate

Date: 2026-07-03

Stage115 separates a measurable representation question from the later
cryptographic correctness question. The current shared-mask toy layout
allocates accumulator, dense selector, and decomposition scratch
components shaped like the existing `k=1,l=1` MAT path. The lane-local
toy layout allocates `2r` accumulator polynomials and compact
`2(1+2r)` selector polynomials, matching the conservative Stage114
resource model.

The gate uses requested bytes as the deterministic resource metric and
RSS as a platform sanity check. RSS is not used as a performance claim.

## Measured Requested-Byte Ratios

| r | N | lane/current requested bytes | product ratio | product/requested ratio |
|---:|---:|---:|---:|---:|
| 2 | 2048 | 1.333333 | 1.800000 | 1.350000 |
| 4 | 2048 | 1.100000 | 2.777778 | 2.525253 |
| 6 | 2048 | 0.914286 | 3.769231 | 4.122596 |
| 8 | 2048 | 0.777778 | 4.764706 | 6.126050 |
| 2 | 4096 | 1.333333 | 1.800000 | 1.350000 |
| 4 | 4096 | 1.100000 | 2.777778 | 2.525253 |
| 6 | 4096 | 0.914286 | 3.769231 | 4.122596 |
| 8 | 4096 | 0.777778 | 4.764706 | 6.126050 |
