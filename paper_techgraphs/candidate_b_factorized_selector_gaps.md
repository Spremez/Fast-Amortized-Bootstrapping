# Candidate B Factorized Selector Gaps

## Frozen And Active Scope

Candidate A is frozen only for the direct `4r` star-cycle support combined
with the current independently randomized PVW row mechanism. Its semantic
equations remain evidence.

Candidate B is active at repository state `INTAKE`. Task 1 validates the
source graph and advances only an in-memory view through
`TECHGRAPH_ANCHORED` and `EQUATIONS_DEFINED`. No repository campaign state or
production source is changed.

## Established

- `PVW_TMLWE` stores `k` masks and `r` bodies.
- Standard PVW sampling uses fresh mask material and independent body errors.
- MAT_TRGSW sampling creates independently randomized PVW rows and injects the
  selector through diagonal gadget terms.
- The exact coefficient-wise matrix is
  `C = mu h I_(k+r) + V [I_k | S] + [0 | E]`.
- The phase identity is
  `P(d^T C) = mu h P(d) + d^T E`.
- Stage203 and Stage329 establish finite star-cycle semantics, not a complete
  encrypted selector distribution.

## Exact-Distribution Gap

For target `k=1`, the noiseless matrix is a diagonal term plus a rank-one
randomization term:

```text
C = mu h I_(r+1) + v w^T + [0 | E].
```

The complete standard sampler also contains the independently sampled
`(r+1) x r` error matrix `E`. Over the torus polynomial ring, use the
multiplicative map `phi(f)=f(1) mod 2`. Explicit uniform-word inputs to the
current sampler formula produce even and odd outputs. Independent coefficient
sampling therefore supports a parity-pattern matrix whose image is
`[I_r;0]`, without requiring a zero coefficient. Any ring
factorization `E=UV` with inner dimension `q<r` maps to a GF(2)
factorization of rank at most `q`, so it cannot represent that complete
support exactly.

This rank argument is an exact-support obstruction, not a general security impossibility theorem.

A correlated or low-rank error distribution is a different cryptographic
mechanism. It must be routed to Candidate C unless it receives its own
assumption or reduction, noise recurrence, and complete cost analysis.

## Closure Gap

The four semantic families are shared row, shared column, diagonal, and
cycle. Diagonal and cycle actions require lane-dependent input coefficients.
A valid mechanism must realize those effects and still return one shared mask
with `r` bodies.

Existing lane-local compact output does not meet this invariant. Any new
lane-pair intermediate must provide a public, secure conversion whose
polynomial and transform costs do not reconstruct the dense path.

## Complete-Cost Gap

The target dense external product uses `(r+1)^2` polynomial add-multiply terms
at `k=T=1`. Object-count claims are invalid when each named object contains
Theta(r) polynomial components.

Every Candidate B mechanism must count:

- decomposed polynomial streams;
- forward and inverse DFT work;
- encrypted polynomial add-multiplies and accumulations;
- key bytes and key-generation work;
- conversion and scratch;
- relinearization or key switching; and
- complete endpoint `T_bootstrap/r`.

Factoring only `v w^T` leaves dense `d^T E` work. A relinearization or
key-switch construction is useful only if its complete counted path is
Theta(r) and has a positive complete-SAB Amdahl projection. For the generic
dense-factor path, Theta(r) requires `q=O(1)`. Generic two-sided factor
counts are not universal lower bounds; a structured full-rank mechanism must
be registered and costed separately.

## Next Executable Gates

1. Build deterministic standard selector matrices for `r=2,4,6` and
   `mu=0,1`.
2. Verify the phase identity and mutation controls.
3. Verify a rank-`r` parity-evaluation image and every constructed rank-`q`
   image control for `q<r`.
4. Count dense and generic-factor polynomial work without hiding conversions
   or calling implementation counts universal lower bounds.
5. Reject an exact standard-PVW low-rank route if no complete registered
   mechanism meets distribution, closure, and cost obligations.
6. On rejection, move Candidate C to `INTAKE` while keeping the overall Goal
   active and production permission false.

## Claim Boundary

Allowed after Task 1:

> The current implementation and Candidate B equation obligations are
> source-anchored.

Not allowed after Task 1:

- a general impossibility theorem for all compact MAT-SAB mechanisms;
- security of correlated errors or encrypted factors;
- a noise or failure-rate claim;
- a new SAB algorithm;
- a kernel acceleration claim;
- a complete bootstrapping acceleration claim; or
- a novelty claim.

No complete-SAB speedup is claimed by this intake package.
