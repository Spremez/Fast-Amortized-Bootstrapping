# Stage326 Exact Dense Frontier Model

The exact dense PVW/MAT-SAB route keeps the original dense selector equations:

```text
r = 4
rows = r + 1 = 5
outputs = k + r = 5
dense products per coefficient block = 25
```

Stages 321, 323, and 325 show that the remaining local implementation ideas do
not justify production integration:

- r4 pointer-hoist/unrolled rows: complete-SAB neutral;
- local dense loop rewrite: denied by static load/store model;
- selector coefficient-blocked layout: bit-exact but below the isolated
  speedup needed to project 1% complete-SAB gain.

This closes the current exact-dense implementation frontier, not the broader
research problem. A real next algorithmic route must reduce product count or
change the SAB schedule with proof-backed semantics.
