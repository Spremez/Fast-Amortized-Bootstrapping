# Stage211 FFT/DFT Dataflow Model

The exact MAT external product boundary is:

```text
PVW_TMLWE pair -> coefficient-domain sub/decompose -> rows of torus
polynomials -> row-wise reverse DFT -> DFT-domain selector addmul -> output
PVW_TMLWE_DFT
```

Under the current source API, `polynomial_torus_to_DFT` calls
`execute_reverse_torus64` once per polynomial. The SPQLIOS processor exposes
one reverse scratch buffer, so reducing row conversion overhead is not a local
SAB call-site edit. It is either:

- a backend/API problem: define a multirow reverse DFT primitive with safe
  scratch layout and prove bit-identical output against the single-row API; or
- a representation-change problem: bypass coefficient-domain torus rows, which
  requires exact closure for subtract/offset/shift/mask decomposition and a
  noise proof.

Prior stages already rejected or neutralized old same-format batching,
direct-scale, and naive lazy-state routes. Therefore Stage211 denies hot-path
implementation and routes only to a standalone backend/API probe.
