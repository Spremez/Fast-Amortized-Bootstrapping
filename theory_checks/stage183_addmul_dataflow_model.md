# Stage183 Addmul Dataflow Model

For the current exact r=6 full-MAT path, the closed dense map has:

```text
rows = r + 1 = 7
outputs = r + 1 = 7
complex vector products per coefficient block = rows * outputs = 49
```

The current tiled AVX512 implementation already shares each decomposed row
across output tiles. A full-output register-resident variant and an output-
major variant have already been tested. Row streaming was also tested and
lost to current all-row tiled AVX.

Thus an exact addmul improvement cannot be justified from theory alone. It
needs a new measured dataflow such as a changed selector layout with keygen/
resource gates, or a new assembly/counter preflight that demonstrates fewer
loads/stores/FMA pressure without breaking the dense closed map.
