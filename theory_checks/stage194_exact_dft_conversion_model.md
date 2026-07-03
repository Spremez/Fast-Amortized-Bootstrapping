# Stage194 Exact DFT/Conversion Model

Current exact MAT-RLWE SAB has a torus-input MAT external product:

```text
torus accumulator -> gadget decomposition -> torus_to_DFT rows -> DFT addmul -> DFT_to_torus materialization
```

Stage162 proves that same-format materialization count is tight: observed
`from_DFT` calls equal the MAT EP calls under the current API. Stage156 rejects
the naive lazy-DFT accumulator because the next gadget decomposition is
coefficient-domain and nonlinear.

Therefore a valid Stage194 implementation candidate must either:

1. make the backend DFT/conversion primitive faster enough to exceed the
   Stage180 complete-SAB projection threshold; or
2. change the representation/API and then satisfy closure, phase, noise, and
   resource gates.

No current local candidate satisfies these conditions.
