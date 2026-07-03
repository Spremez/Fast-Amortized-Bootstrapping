# Stage130 Shared-Source Compact EP Model

Date: 2026-07-03

Stage129 showed that compact addmul is positive but the `2r`
decomposition/DFT stream cost blocks r=4. Stage130 changes only the
source-side MAT-RLWE shape: one shared source polynomial plus r body
polynomials. Selector rows remain lane-local, so the phase equation is
checked per lane.

## Count Model

```text
dense_dft_terms           = T * (k+r)^2
shared_compact_dft_terms  = 4 * T * r
dense_decomp_streams      = T * (k+r)
shared_compact_streams    = T * (k+r)
```

## Results

| r | N | dense all us | shared compact all us | full speedup | decomp/DFT speedup | addmul speedup | DFT term ratio | total term ratio | decision |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 44.383867 | 45.858533 | 0.967843 | 0.974663 | 1.052528 | 1.125000 | 1.090909 | NEGATIVE_SHARED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 2 | 512 | 18.461267 | 18.647267 | 0.990025 | 1.029681 | 1.112785 | 1.125000 | 1.090909 | NEGATIVE_SHARED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 1024 | 98.423567 | 85.338133 | 1.153336 | 1.001350 | 1.506633 | 1.562500 | 1.428571 | POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY |
| 4 | 512 | 46.363400 | 36.185433 | 1.281272 | 1.022033 | 1.530580 | 1.562500 | 1.428571 | POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY |
| 6 | 1024 | 161.466767 | 117.894967 | 1.369582 | 1.002339 | 1.845567 | 2.041667 | 1.806452 | POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY |
| 6 | 512 | 82.865700 | 56.047933 | 1.478479 | 1.000692 | 2.020643 | 2.041667 | 1.806452 | POSITIVE_SHARED_COMPACT_FASTER_THAN_DENSE_PROXY |

## Boundary

This is isolated external-product evidence. It is not production header
code, AVX512 optimality, SAB schedule integration, randomized noise, or
complete `T_bootstrap/r` timing.
