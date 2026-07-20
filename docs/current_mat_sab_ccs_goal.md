# Current MAT-SAB CCS/USENIX Goal

The controlling design is:

`docs/superpowers/specs/2026-07-20-lut-late-binding-operator-sab-design.md`

The active research candidate is Candidate D, LUT-Late-Binding Operator SAB.
Its objective is to evaluate the sparse SAB schedule once as a bounded,
LUT-independent encrypted operator and bind `r` public LUTs after the hot
schedule. The target is to remove or reduce the exact-dense `Theta(r^2)`
selector work while retaining standard RLWE/GGSW security objects.

The external workload remains one SAB input and `r` independent LUT/output
lanes. The primary metric is:

```text
T_complete_bootstrap / (r * N_active)
```

The existing result remains an immutable baseline:

- complete exact-dense PVW/MAT-SAB is implemented;
- six binary r=2/r=4 rows report `1.612100x` to `1.747647x` over repeated
  scalar SAB;
- this is a supported systems result, not a new asymptotic algorithm or
  theoretical-optimality result.

Candidates A, B, and C are frozen as rejected under their registered gates.
Their negative results are scoped and do not imply a general impossibility
theorem.

Candidate D is admitted only if:

- the binary SAB operator closure has at most four channels;
- all channels and selector keys reduce to standard RLWE/GGSW objects;
- exact basis-vector and negative-control checkers pass;
- covariance-aware late-binding noise remains decodable;
- complete r=4 cost projection is at least 10% better than B1; and
- complete measured `T/(r*N_active)` improves over exact-dense MAT-SAB.

No algorithm hot-path code is permitted until the written design and
implementation plan are reviewed and the D2/D3 admission gates pass.
Conference acceptance is external; the repository-controlled success state
is `PAPER_READY`.
