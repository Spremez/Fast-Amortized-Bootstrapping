# Stage324 Selector Layout Route Model

The exact PVW/MAT-SAB r=4 dense external product performs:

```text
rows = r + 1 = 5
outputs = k + r = 5
complex products per coefficient block = 25
```

Stage323 shows the current AVX512 loop already reuses decomposed rows across
all five outputs and stores each output once. Therefore a selector-transpose
layout cannot reduce the dense product count. Its only admissible exact-route
mechanism is better selector locality, fewer pointer/cache misses, or easier
prefetching.

With measured dense share `0.212353`, a selector-transpose
probe must deliver at least `1.048905` dense-addmul
speedup to project a 1% complete-SAB `T_bootstrap/r` improvement. Anything
below that is not worth integrating into `sab_pvw_*`.

Structured/compact selector remains a separate proof branch: it may reduce the
active r=4 semantic rows by `0.360000` only if semantic-zero dummy
rows are proven production-safe. Current public row saving is
`0.000000`, so it has no production speedup claim.
