# Stage346 MAT-SAB Algorithm Gap Model

## Baseline Object

Repeated scalar SAB evaluates r independent scalar bootstraps and compares to
PVW/MAT-SAB by the amortized endpoint:

```text
T_scalar_per_lane = T_repeated_scalar / r
T_mat_per_lane    = T_pvw_mat_sab / r
```

The current PVW/MAT-SAB object is an r-body RLWE-like accumulator:

```text
C = (a, b_0, ..., b_{r-1})
```

All lanes share the mask component `a`; each body `b_q` carries one output
lane. SAB correctness requires a stepwise invariant:

```text
phase(C.body[q]) == phase(scalar_SAB_lane[q])
```

for each lane q after CMUX/NCMUX, RGSW monomial updates, sparse multiplication,
sub_a, extraction, and key switching.

## Exact Dense Path

The implemented path uses MAT external products for the r-body object. For
`k=1`, the dense MAT dimension is `m = 1 + r`. Shared-mask decomposition and
body batching reduce repeated work, but dense selector rows still introduce
off-lane terms. Therefore the measured 1.6x-1.75x complete-SAB per-lane
speedup is meaningful but far from ideal r-fold scaling, especially for r=4.

The exact dense path is a valid scoped systems result. It is not a proof that
MAT-SAB is optimal, because the model has not ruled out structured selector or
closed lane-state representations with fewer off-lane terms.

## New Algorithm Requirement

A stronger algorithm needs one of two outcomes:

1. Closed structured-state route:
   - define a state representation that stays closed under the full SAB
     schedule;
   - define selector/key material that updates each lane without re-densifying
     into the full `(1+r) x (1+r)` matrix;
   - prove or check the lane phase invariant after each SAB step;
   - then implement behind a new explicit path.

2. Current-format lower-bound route:
   - define the allowed key/state model;
   - prove that dense off-lane work is unavoidable inside that model;
   - downgrade the contribution to exact-dense optimality under that restricted
     model, not global MAT-SAB optimality.

Stage347 must choose one of these outcomes. It may not produce only informal
theory text; it must create a finite checker or a lower-bound proof artifact
with explicit assumptions.
