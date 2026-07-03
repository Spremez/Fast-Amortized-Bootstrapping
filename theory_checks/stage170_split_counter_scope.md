# Stage170 Split Counter Scope

Stage170 answers one bounded question:

```text
What are the native per-call cycle, load/store, cache, and FP512 counter costs
for the current exact r=6 MAT EP/subdecomp and from_DFT materialization kernels?
```

It does not answer:

- whether the dense MAT algorithm is theoretically optimal;
- whether a new compact/key-distribution route is sound;
- whether complete SAB is accelerated beyond the Stage169 endpoint;
- whether all parameter sets or ternary/include-zero branches behave the same.

The MAT EP probe includes sub-decomposition and per-row torus-to-DFT because
that is the current production fused call boundary in `sab_pvw_CMUX_from_diff`.
The from_DFT probe includes the fused add path because that is the current
production materialization boundary in `sab_pvw_CMUX_materialize_internal`.
