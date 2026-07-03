# Stage129 Compact EP Microbench Model

Date: 2026-07-03

Stage129 uses an isolated dense-count proxy and the Stage128 compact
all-lane API kernel. The dense proxy is a cost proxy for current dense
`(k+r)^2` DFT multiply-add work, not a complete SAB or production key-format
benchmark. Compact timing is measured over all r lanes, so the endpoint is
compatible with the amortized `T_kernel/r` lens.

## Count Model

For k=1 and gadget level T:

```text
dense_dft_terms   = T * (k+r)^2
compact_dft_terms = 4 * T * r
dense_total_terms = dense_dft_terms + T * (k+r)
compact_total     = compact_dft_terms + 2 * T * r
```

The timing gate separately records full kernel, decomposition/DFT-only,
and DFT-addmul-only measurements.

## Results

| r | N | dense all us | compact all us | full speedup | decomp/DFT speedup | addmul speedup | DFT term ratio | total term ratio | decision |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 43.514000 | 55.423500 | 0.785118 | 0.731624 | 0.891968 | 1.125000 | 1.000000 | NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 2 | 512 | 19.101600 | 23.130367 | 0.825823 | 0.747152 | 1.009838 | 1.125000 | 1.000000 | NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 1024 | 92.304300 | 103.942533 | 0.888032 | 0.615331 | 1.369610 | 1.562500 | 1.250000 | NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 512 | 44.274367 | 47.828667 | 0.925687 | 0.619392 | 1.488801 | 1.562500 | 1.250000 | NEGATIVE_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 6 | 1024 | 214.858233 | 193.580300 | 1.109918 | 0.580632 | 1.796338 | 2.041667 | 1.555556 | POSITIVE_COMPACT_FASTER_THAN_DENSE_PROXY |
| 6 | 512 | 77.767733 | 73.112533 | 1.063672 | 0.588463 | 1.867126 | 2.041667 | 1.555556 | POSITIVE_COMPACT_FASTER_THAN_DENSE_PROXY |

## Boundary

This is isolated microbench evidence only. It is not AVX512 theoretical
optimality, production MOSFHET API evidence, SAB schedule integration,
randomized noise/failure-rate evidence, or complete `T_bootstrap/r` timing.
