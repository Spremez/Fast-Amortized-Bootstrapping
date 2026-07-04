# Stage296 Direct DFT High-Stat Model

The primary endpoint remains:

```text
complete SAB amortized time = T_bootstrap / r
```

Stage296 does not introduce a new algorithmic variant. It checks whether the
Stage292/295 direct-DFT implementation-level improvement persists under a
larger local sample count. The required comparison is same-backend:

- selected PVW/MAT-SAB control without direct sub-decompose-to-DFT;
- direct-DFT PVW/MAT-SAB candidate;
- repeated scalar SAB only as the amortized baseline denominator.

The stage can support a local engineering claim, but theory-level optimality
still requires counter attribution, parameter generalization, and stage-wise
noise/resource accounting.
