# Candidate B Factorized Gate Experiment

Decision: `REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C`.

## Fixed Inputs

- finite field: GF(257)
- body counts: r=2,4,6
- selector bits: mu=0,1
- factor ranks: q=1,...,r
- deterministic masks, digits, errors, and mutations

## Gates

1. Source anchors and scoped local literature-review evidence must be present.
2. Exact selector phase identities must pass.
3. Error mutation controls must change the predicted lane.
4. Explicit current-sampler inputs must witness even and odd Torus outputs.
5. A multiplicative GF(2) image of a supported rank-r ring witness must
   reject every q<r.
6. Constructed rank-q image controls must be admitted at exactly q.
7. Generic dense-factor and retained-error costs must be recorded without
   calling them universal lower bounds.
8. Failed evidence is inconclusive; only failed mechanisms route B to C.

## Reproduction

```text
python scripts/run_candidate_b_factorized_gate.py
python -m unittest tests.research.test_candidate_b_gate -v
```

No benchmark or production-code claim is made.
