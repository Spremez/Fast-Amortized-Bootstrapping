# Stage157 Sub-Decompose Fusion Model

Stage156 showed that decomposition cannot be maintained linearly across SAB
updates. Stage157 tests a narrower mechanism that remains exact:

```text
separate: sub = in2 - in1; D = decompose(sub)
fused:    D = decompose(in2 - in1)
```

The fused form does not change the decomposition formula or selector semantics.
It only removes the full intermediate sub write/read in the microbench. It
therefore targets the Stage155 `sub` share and possibly part of the memory
traffic immediately before MAT EP. It cannot reduce the 573440 external-product
or materialization count.
