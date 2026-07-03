# Stage171 Structured Compact Keygen Model

Let `m = 1 + r`. The current dense MAT external product represents a generic
`m x m` encrypted selector map. A compact structured map keeps:

```text
shared output: M[0, 0..r]
body q output: M[q,0] and M[q,q]
omitted: M[q,j] for q != j and q,j > 0
```

Thus the compact map is exact only when the logical selector satisfies:

```text
M[q,j] = 0 for q != j and q,j > 0.
```

This is not a drop-in replacement for the current dense encrypted selector.
It is a different keygen/distribution claim. The unresolved question is whether
omitted body-cross zero encryptions can be removed or simulated without
weakening security and while preserving SAB phase and noise bounds.

The Stage171 speed projection is deliberately limited. It assumes MAT EP cost
scales with selector term count and from_DFT cost stays fixed. That produces a
component upper bound, not a complete-SAB benchmark or lower bound.
