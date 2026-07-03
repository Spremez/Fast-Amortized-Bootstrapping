# Stage114 Lane-Local Multimask Resource Model

Date: 2026-07-03

The current shared-mask PVW accumulator has `1+r` polynomial components
for k=1. A lane-local multimask accumulator has roughly `2r` components
because each lane needs its own mask/body pair.

The current dense external product has `(1+r)^2` product terms for
k=1,l=1. The lane-local body-linear target is modeled as `1+2r` terms.

This model is only a pre-implementation screen. It ignores allocator
behavior, cache effects, noise growth, key switching, and SAB schedule
integration.

## Symbolic Rows

| r | accumulator ratio | product ratio | coarse product/acc ratio |
|---:|---:|---:|---:|
| 2 | 1.333 | 1.800 | 1.350 |
| 4 | 1.600 | 2.778 | 1.736 |
| 6 | 1.714 | 3.769 | 2.199 |
| 8 | 1.778 | 4.765 | 2.680 |