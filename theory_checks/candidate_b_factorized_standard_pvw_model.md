# Candidate B Standard-PVW Factorization Model

## 1. Scope

This document fixes the coefficient-wise algebra and complete-cost boundary
for Candidate B. It models the current source mechanism before any executable
finite-field checker is written.

It answers one narrow question: can the complete current standard-PVW
MAT_TRGSW selector, including its independently sampled errors, be represented
with Theta(r) complete encrypted work while returning the same one-mask,
r-body ciphertext type?

The model is an exact representation and support model. It is not a security
proof, a concrete noise analysis, or a complete-SAB performance result.

## 2. Current PVW State And Phase

Let the ring be `R` and let a PVW ciphertext contain

```text
a in R^k
b in R^r.
```

The secret is a matrix

```text
S in R^(k x r).
```

The current sampler chooses `a`, samples an independent error vector
`e in R^r`, and sets

```text
b = a S + e + m.
```

The phase map is

```text
P(a, b) = b - a S.
```

This form exposes why one shared mask can protect `r` body lanes: every body
uses the same `a` but a different column of `S`.

Source anchors:

- `src/mosfhet/include/mosfhet.h`: `typedef struct _PVW_TMLWE{`
- `src/mosfhet/src/pvwtmlwe.c`: `void pvmtmlwe_sample(`
- `src/mosfhet/src/pvwtmlwe.c`: `void pvmtmlwe_phase(`

## 3. General-k Selector Matrix

Let

```text
n = k + r.
```

At one gadget level, MAT_TRGSW creates `n` independently randomized PVW rows.
Collect their mask vectors as

```text
V in R^(n x k)
```

and their body-error vectors as

```text
E in R^(n x r).
```

Before selector injection, each row has coordinate form

```text
(V_i, V_i S + E_i).
```

The gadget-scaled hidden selector `mu h` is then added to the corresponding
diagonal coordinate. The complete public matrix is

```text
C = mu h I_(k+r) + V [I_k | S] + [0 | E].
```

Dimensions are:

```text
C             : (k+r) x (k+r)
V             : (k+r) x k
[I_k | S]     : k x (k+r)
[0 | E]       : (k+r) x (k+r)
E             : (k+r) x r.
```

The zero block in `[0 | E]` has `k` columns. The error block occupies the
`r` body columns.

Source anchor:

- `src/mosfhet/src/mattrgsw.c`: `void mat_trgsw_monomial_sample(`

## 4. Target k=1 Reduction

The target SAB path uses `k=1`. Set

```text
m = r + 1
v = V
w^T = (1, s_0, ..., s_(r-1)).
```

The matrix becomes

```text
C = mu h I_m + v w^T + [0 | E].
```

The expression `mu I + v w^T` is therefore only the noiseless skeleton. It
does not contain the complete standard selector distribution because it omits
the independently sampled matrix `E`.

It also does not make the factors evaluator-visible:

- `mu` is hidden in encrypted diagonal gadget coordinates;
- `w` contains the PVW secret;
- the diagonal mask coordinate combines randomization with the hidden
  selector term; and
- `E` contributes to every encrypted body row.

## 5. Phase Identity

Let `d in R^(k+r)` be the decomposed input digit vector and let the external
product output be

```text
y = d^T C.
```

Split `d` into mask and body coordinates:

```text
d = (d_a, d_b).
```

Applying the PVW phase map gives

```text
P(d^T C) = mu h P(d) + d^T E.
```

Derivation:

```text
d^T C
  = mu h d^T
    + (d^T V) [I_k | S]
    + d^T [0 | E].
```

The mask part of `(d^T V) [I_k | S]` is `d^T V`, and its body part is
`(d^T V) S`. These cancel under `P`. The remaining phase consists of the
selected input phase and the accumulated body error.

This identity separates two obligations:

1. semantic correctness of the selected message action; and
2. complete representation of the encrypted noise distribution.

Passing the first obligation does not imply the second.

## 6. Error-Rank Boundary

The torus polynomial ring is

```text
R = Z_(2^w)[X] / (X^N + 1).
```

Define

```text
phi: R -> GF(2),  phi(f) = f(1) mod 2.
```

This is a ring homomorphism. Coefficient reduction modulo two preserves sums
and products, and the quotient relation maps to
`1^N+1=0` in GF(2). Raw coefficient extraction would not be multiplicative
and is not used by the gate.

`pvmtmlwe_sample` calls `generate_torus_normal_random_array` independently
for each body. That routine calls `generate_normal_random` and
`double2torus` for every coefficient. At target `sigma=2^-50`, explicit
uniform-word inputs give:

```text
(0x9e3779b97f4a7c15, 0xa36a9465a325da06) -> -11446 (even)
(0x3c6ef372fe94f82a, 0x751fde9874b8c709) ->   1791 (odd)
```

Under the intended pseudorandom-byte model, these finite inputs have nonzero
support and calls consume fresh words. Choose polynomial coefficient parities
so diagonal entries in the first `r` rows have odd coefficient sum, while
off-diagonal entries and the final row have even coefficient sum. This does
not require any sampled coefficient to equal zero. The resulting supported
parity-pattern matrix has image

```text
phi(E) = [I_r; 0]
rank_GF(2)(phi(E)) = r.
```

Suppose an exact factorization uses inner dimension `q`:

```text
E = U V_e
U in R^((r+1) x q)
V_e in R^(q x r).
```

Applying `phi` entry-wise gives

```text
phi(E) = phi(U) phi(V_e).
```

Then

```text
rank_GF(2)(phi(E)) <= q.
```

For every `q < r`, the factorized support assigns no mass to the rank-`r`
image event, while the standard independent-error support assigns nonzero
mass to that witness under the stated sampler model. Consequently, a `q<r`
factorization cannot be an exact realization of the complete current error
distribution.

This is an exact-support obstruction for the tested representation. It is not
a general security impossibility theorem. Correlated or low-rank errors define
a different mechanism and require a separate assumption or reduction.

## 7. Semantic Star-Cycle Versus Encrypted Distribution

The star-cycle semantic map has four equation families:

```text
M_shared_row
M_shared_column
M_diagonal
M_cycle.
```

Their union has `4r` declared semantic support. This specifies required phase
interactions, including neighbor terms. It does not specify a complete
encrypted key distribution.

Calling the four families four encrypted objects is not a complexity result.
A standard PVW object contains polynomial components. Lane-dependent
diagonal and cycle actions can require one encrypted row per independent
input digit. If so, the representation reconstructs quadratic component
count even though it has only four top-level names.

An admitted Candidate B mechanism must simultaneously provide:

- the complete selector distribution or a clearly stated new mechanism;
- one shared output mask and `r` bodies;
- diagonal and neighbor/cycle phase effects;
- secret-independent public shape; and
- Theta(r) complete encrypted work.

## 8. Complete Work-Count Policy

At target `k=T=1`, there are

```text
m = r + 1
```

input and output coordinates. The dense contraction exposes

```text
m^2 = (r+1)^2
```

polynomial add-multiply terms per gadget level, in addition to decomposition,
DFT conversion, accumulation, and materialization.

For generic dense error factors with inner dimension `q`, a direct two-sided
implementation uses

```text
(r+1)q + qr
```

polynomial products before the diagonal selector action and any encrypted
conversion cost. Theta(r) complete work in this dense-factor model requires
`q=O(1)`. The homomorphic-image witness instead forces `q>=r`. At `q=r`, the
generic dense-factor count is

```text
2r^2 + r.
```

This is not below the dense count

```text
r^2 + 2r + 1.
```

For the tested `r>=2`, this generic layout is already more expensive by the
recorded polynomial-product count. This is not a universal arithmetic lower
bound: normalized, sparse, or permutation factors can skip products and may
fuse the diagonal. Such a structured full-rank mechanism is a separate
Candidate B construction and must register its complete operation, storage,
closure, security, and noise costs. Factoring only the noiseless `v w^T` term
does not remove the dense `d^T E` contraction and therefore does not establish
an asymptotic saving.

Every mechanism comparison must count:

- encrypted polynomial components;
- gadget decomposition streams;
- forward and inverse DFT work;
- polynomial add-multiply and accumulation operations;
- evaluation-key bytes and key generation;
- output conversion and scratch;
- relinearization;
- key switching; and
- any lane-pair to one-mask repacking.

The primary endpoint remains complete

```text
T_bootstrap/r
```

against repeated scalar SAB and exact-dense PVW/MAT-SAB. A kernel-only count
cannot support a bootstrapping acceleration claim.

## 9. Candidate B Gate Consequences

The executable gate must include:

- full-rank parity-evaluation-image positive controls for `r=2,4,6`;
- rank-`q` image controls for every `q < r`;
- phase-identity checks for `mu=0,1`;
- a mutation control that changes an error coordinate;
- dense and factorized polynomial-component counts; and
- explicit dispositions for changed-distribution, relinearized, and
  lane-pair conversion variants.

If no registered mechanism preserves complete standard distribution, closure,
and Theta(r) complete cost, Candidate B must record

```text
REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C
```

and Candidate C becomes the next intake. This outcome rejects only the exact
standard-PVW factorization route. It does not reject redesigned ciphertext
states or new selector distributions.
