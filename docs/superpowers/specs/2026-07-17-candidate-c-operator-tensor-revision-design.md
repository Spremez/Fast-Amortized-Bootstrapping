# Candidate C Operator Tensor Revision Design

## Decision

Candidate C consumes its one permitted equation revision before complete-cost
work. Task 3 proved the binary SAB schedule and its exact counts, but also
proved that Stage203 contains only a support map. It does not contain the
numeric compact selector needed to determine lane-mask rank, phase, key
distribution, or relinearization cost.

The revision inserts three finite gates before the existing complete-cost
Task 4:

1. Task 3A synthesizes a concrete selector tensor or proves a scoped
   obstruction for the no-conversion C1 class.
2. Task 3B specifies and gates the secret-dependent conversion required by
   C2.
3. Task 3C replays the exact Task 3 event stream only with a registered
   tensor and, for C2, registered conversion material.

This is the final Candidate C equation revision. Failure does not create a
Candidate D.

## Mathematical Object

Task 3A is an exact finite-ring surrogate over

```text
R_257,8 = GF(257)[X]/(X^8+1).
```

It is not a proof for the production ring dimension or Torus arithmetic.
Gadget levels, coefficient directions, and selector bits remain separate
dimensions. Every `A_mu[t,v,c]`, `B_mu[t,q,c]`, and `s_q` is an explicit
length-8 polynomial vector. Multiplication by a polynomial uses its exact
`8 x 8` negacyclic convolution matrix.

Fix `d=rho+1` mask-basis components and one public lane matrix

```text
Lambda in GF(257)^(r x d)
Lambda[q,0] = 1
Lambda[0,u] = 0 for u>0
rank(L Lambda) = rho
L = I - 1 e_0^T.
```

An input state has mask bases `a_u`, `u=0,...,d-1`, and bodies `b_q`,
`q=0,...,r-1`. Its lane-q mask and phase are

```text
a_q = sum_u Lambda[q,u] a_u
phase_q = b_q - s_q a_q.
```

Input component `c` ranges over the ordered set

```text
M_0,...,M_(d-1), B_0,...,B_(r-1).
```

For each selector bit `mu`, use a distinct tensor family

```text
K_mu[t,v,c] = A_mu[t,v,c]     for output mask basis v
K_mu[t,q,c] = B_mu[t,q,c]     for output body q.
```

For one gadget value `h_t`, exact phase requires

```text
B_mu[t,q,c]
  - s_q sum_v Lambda[q,v] A_mu[t,v,c]
  = mu h_t P_Lambda[q,c],

P_Lambda[q,M_u] = -Lambda[q,u] s_q,
P_Lambda[q,B_j] = 1 if q=j and 0 otherwise.
```

Define the lane-expanded selector polynomial

```text
Abar_mu[t,q,c] = sum_v Lambda[q,v] A_mu[t,v,c].
```

For each `(mu,t,c)`, replace `A_mu[t,v,c]` by its `8 x 8` negacyclic
convolution matrix and stack the `d` basis-output row blocks. Concatenating
every `(t,c)` block gives

```text
R_mu in GF(257)^(d*8 x ell*(d+r)*8).
```

Apply `Lambda` to those basis-output rows:

```text
T_mu = (Lambda tensor I_8) R_mu
T_mu in GF(257)^(r*8 x ell*(d+r)*8).
```

This `T_mu` is exactly the concatenation obtained by replacing
`Abar_mu[t,q,c]` with its `8 x 8` convolution matrix and stacking lane blocks.
The evaluator applies the same public `Lambda` at every level, input
component, and coefficient direction. Therefore

```text
((L tensor I_8) T_mu)
  = ((L Lambda) tensor I_8) R_mu
rank((L tensor I_8) T_mu) <= rho * 8.
```

The checker verifies both the common factorization and the concatenated field
rank over every level, component, and finite coefficient direction. This is
a finite surrogate for module rank `rho`; it is not called field rank
`rho`. Per-level rank checks alone are insufficient.

The exact-dense MAT operator is the positive control. Stage203 supplies a
support classification only; it cannot supply coefficients for `A_mu` or
`B_mu`.

## Evaluator-Sample Relation Gate

Lane-mask rank is not a security rank. Different lanes use different secrets,
and a raw relation among lane masks does not cancel
`sum_q s_q a_q`. The relation audit therefore fixes one selector value `mu`
and uses a separate field-expanded matrix whose rows are evaluator-visible
key samples `(t,c)` and whose columns are the `d*n` mask-basis coefficient
coordinates.

`K_0` and `K_1` are audited separately; counterfactual selector objects are
never stacked into one sample matrix. For one selector object and one secret
lane `q`, put `m=ell*(d+r)` and let:

```text
S_mu in GF(257)^(m x d*8)
M_mu,q in GF(257)^(m x 8).
```

Row `(t,c)` of `S_mu` concatenates the eight coefficients of every
`A_mu[t,v,c]`. Row `(t,c)` of `M_mu,q` contains the eight coefficients of the
corresponding phase/message polynomial. A public scalar sample relation
`z in GF(257)^m` is relevant only when

```text
z^T S_mu = 0.
```

The exact finite audit checks whether the same relation leaves a nonzero
retained message polynomial:

```text
z^T M_mu,q != 0
```

for any `q`. The algebraic diagnostic is

```text
left_kernel(S_mu) subseteq intersection_q left_kernel(M_mu,q)
columnspace([M_mu,0 | ... | M_mu,r-1]) subseteq columnspace(S_mu).
```

Containment failure alone is not a security decision in noisy LWE/PVW. For
each retained-message relation, the audit records:

```text
centered relation coefficients
L1 and L2 coefficient norms
retained centered message gap
symbolic error multiplier
registered sigma/error bound, if one exists
decision inequality, if one exists
```

Without a registered error distribution and inequality, the status is
`RELATION_RECORDED_NO_SECURITY_DECISION`. The audit must not reject shared-
mask PVW merely because a modular relation exists. A synthetic same-secret
zero-error control may reject because its error bound is explicitly zero.
For an actual C1 tensor, only a registered inequality proving that the
centered retained message remains distinguishable after the relation's
combined error may emit `REGISTERED_SHORT_ERROR_RELATION_FAIL`. Both C1
admission and routing a high-rank seed to C2 exclude that status.
Passing this preflight does not prove RLWE/PVW security.

## Candidate Classes

### Dense Control

The current MAT selector and external product remain the correctness,
distribution, and operation-count control. They may cost `Theta(r^2)` and
are not Candidate C.

### C1: No Conversion

C1 must provide one concrete tensor that simultaneously passes:

- phase identity for `mu=0,1`;
- one fixed `Lambda` and concatenated
  field-rank bound `rho*8` for arbitrary independent levels, components, and
  finite coefficient directions;
- a completed evaluator-sample relation record, without treating it as a
  security proof;
- a complete evaluator algorithm with no hidden dense materialization;
- operation and key-object counts strictly below exact dense at the
  structural level.

Security remains blocked after a finite preflight. A finite phase witness
alone cannot admit the mechanism to schedule replay.

### C2: Registered Conversion

C2 may start only from a concrete phase-correct high-rank seed tensor emitted
by Task 3A. It cannot repair a phase-invalid tensor. It must register a
conversion from `(a_q,b_q)` to `(\tilde a_q,\tilde b_q)` satisfying

```text
\tilde b_q = b_q + (\tilde a_q-a_q) s_q
phase(\tilde a_q,\tilde b_q) = phase(a_q,b_q).
```

The evaluator cannot compute the secret-dependent correction as a public
projection. The design must therefore name the evaluation material,
decomposition levels, transforms, products, errors, key bytes, and live
scratch.

The schedule model distinguishes:

- algebraic postponement on one state;
- batching conversions of independent accumulator indices;
- conversion at a butterfly-bit boundary;
- conversion after every CMUX/NCMUX.

Batching independent states does not by itself reduce the number of
cryptographic products. C2 is rejected if the next consumer requires a
converted state after every selector, if the only valid block is `B=1`, or
if the structural conversion lower bound already removes all possible
savings. Measured-central complete cost remains a later Task 4 gate.

## Exact Gates

All finite algebra uses exact GF(257) arithmetic and covers `r=2,4,6`.
The target rank is `min(2,r-1)`.

Task 3A has six terminal outcomes:

```text
ADMIT_C1_OPERATOR_TO_SCHEDULE_REPLAY
ROUTE_PHASE_CORRECT_HIGH_RANK_OPERATOR_TO_C2
REJECT_C1_PHASE_IDENTITY_TERMINAL
REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
REJECT_C1_REGISTERED_SHORT_ERROR_RELATION_TERMINAL
TERMINAL_INCONCLUSIVE_C1_EVIDENCE_EXHAUSTED
```

Task 3B has four terminal outcomes:

```text
ADMIT_C2_RELINEARIZATION_TO_SCHEDULE_REPLAY
REJECT_C2_CONVERSION_CLOSURE
REJECT_C2_NONPOSITIVE_STRUCTURAL_COST
TERMINAL_INCONCLUSIVE_C2_EVIDENCE_EXHAUSTED
```

Task 3C may admit at most one of C1 or C2 to existing Task 4. A scoped
mechanism rejection closes Candidate C as rejected. Missing evidence closes
the finite campaign as terminal inconclusive without converting it to a
mechanism rejection. Task 4 is skipped unless Task 3C emits one fully
hash-bound registered operator.

## Evidence And Controls

Each gate must include:

- exact dense positive control;
- C0 full-rank negative control;
- shared-mask PVW relation positive control;
- same-secret cancellation negative control;
- one phase mutation;
- one mask-rank mutation;
- one evaluator-sample/message mutation;
- one conversion-key or correction mutation for C2;
- deterministic generation and artifact hashes.

No test may obtain its expected result by assigning a decision label after a
mutation flag. Mutations must pass through the same validators as baseline
objects.

## Claim Boundary

Passing 3A proves finite operator equations only. Passing 3B proves a finite
conversion specification and structural accounting only. Passing 3C proves
finite schedule closure only.

Security, ring-noise bounds, production correctness, AVX performance,
complete-SAB speedup, and novelty remain blocked until their later gates.
No C/C++ source may change under this revision.

## Termination

This revision is finite:

- one tensor equation family;
- C1 then C2, with no third mechanism;
- `r=2,4,6` and GF(257);
- no favorable coefficient invention from support-only artifacts;
- no automatic equation rewrite after rejection;
- no Candidate D.

The research loop terminates with an admitted concrete object, a scoped
rejection artifact, or a terminal inconclusive evidence-exhaustion artifact.
None of these outcomes can return to an unbounded theory-design loop.
