# Stage134 Generalized Lane-Pair Input EP Model

Date: 2026-07-03

Stage133 shows that after compact CMUX consumption the accumulator
state has one mask/body pair per lane. The generalized input kernel
therefore decomposes `2r` source streams, `(a_q, b_q)` for each lane
`q`, and applies lane-local compact selector rows.

The arithmetic is closed for lane-pair state, but its decomposition
count is `2*T*r`, not Stage130's `T*(1+r)` shared-source count. This
gate checks whether the closure-capable path still has enough
full-kernel timing signal to justify RGSW/sparse integration.

## Ratio Results

| r | N | dense all us | generalized all us | full speedup | decomp speedup | addmul speedup | total term ratio | decision |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 41.102100 | 46.537000 | 0.883213 | 0.705037 | 1.092605 | 1.000000 | NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 2 | 512 | 16.928667 | 22.483333 | 0.752943 | 0.748168 | 1.008307 | 1.000000 | NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 1024 | 93.328167 | 102.469300 | 0.910791 | 0.587589 | 1.508816 | 1.250000 | NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 4 | 512 | 39.863167 | 42.704133 | 0.933473 | 0.630645 | 1.537896 | 1.250000 | NEGATIVE_GENERALIZED_COMPACT_NOT_FASTER_THAN_DENSE_PROXY |
| 6 | 1024 | 156.724000 | 145.005800 | 1.080812 | 0.556462 | 1.889844 | 1.555556 | POSITIVE_GENERALIZED_COMPACT_FASTER_THAN_DENSE_PROXY |
| 6 | 512 | 73.445667 | 66.700767 | 1.101122 | 0.573445 | 1.855769 | 1.555556 | POSITIVE_GENERALIZED_COMPACT_FASTER_THAN_DENSE_PROXY |

## Stage130 Comparison

| r | N | generalized all us | Stage130 shared all us | generalized/shared cost | generalized speedup | Stage130 speedup | decision |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1024 | 46.537000 | 45.858533 | 1.014795 | 0.883213 | 0.967843 | CLOSURE_CORRECT_BUT_PERF_BLOCKED |
| 2 | 512 | 22.483333 | 18.647267 | 1.205717 | 0.752943 | 0.990025 | CLOSURE_CORRECT_BUT_PERF_BLOCKED |
| 4 | 1024 | 102.469300 | 85.338133 | 1.200745 | 0.910791 | 1.153336 | CLOSURE_CORRECT_BUT_PERF_BLOCKED |
| 4 | 512 | 42.704133 | 36.185433 | 1.180147 | 0.933473 | 1.281272 | CLOSURE_CORRECT_BUT_PERF_BLOCKED |
| 6 | 1024 | 145.005800 | 117.894967 | 1.229958 | 1.080812 | 1.369582 | CLOSURE_CORRECT_BUT_COSTLY |
| 6 | 512 | 66.700767 | 56.047933 | 1.190066 | 1.101122 | 1.478479 | CLOSURE_CORRECT_BUT_COSTLY |

## Boundary

This is still an isolated external-product gate. It is not a full
RGSW monomial step, not sparse schedule integration, and not a
complete `T_bootstrap/r` result.
