# Stage250 Exact Dense Lower-Bound Gap Model

The exact dense route currently has:

- measured complete-SAB amortized speedup on selected binary rows;
- profile evidence that MAT external product remains the largest CMUX term;
- native counter attribution for a backend-vs-wrapper implementation choice.

It does not have:

- a validated `A_lower(r)` denominator for `gap(r)=A_impl(r)/A_lower(r)`;
- an admissible compact/body-linear lower bound, because compact production is
  blocked by distribution/security gates;
- code permission for speculative AVX/MAT rewrites.

Therefore exact dense optimality remains open. Future lower-bound work must
produce measurable lower-bound components and tie them to counters/assembly and
complete-SAB A/B.
