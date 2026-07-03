# Stage179 Microarchitecture Model

Stage178 attributes `0.603899465` of current complete-SAB time to the
combined MAT EP/subdecomp block. A full-SAB improvement target `S` requires a
component speedup:

```text
x >= share / (1/S - (1 - share))
```

For example, a 3% complete-SAB gain requires a component speedup of
`1.050674268` on the MAT EP/subdecomp
block. That is plausible only if a real subcomponent bottleneck exists.

The audit therefore rejects blind implementation and selects a split probe.
