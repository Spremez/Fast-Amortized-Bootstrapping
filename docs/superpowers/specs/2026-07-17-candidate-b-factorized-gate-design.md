# Candidate B Factorized Star-Cycle Gate Design

Date: 2026-07-17

## 1. Decision And Scope

Candidate A is frozen in the narrow terminal state recorded by
`research_state.yaml`:

```text
REJECT_CANDIDATE_A_STANDARD_PVW_RANDOMIZATION_ROUTE_TO_B
```

The frozen object is the direct `4r` star-cycle support combined with the
current standard PVW row-randomization mechanism. Candidate A's phase
equations and negative controls remain valid evidence. The freeze does not
freeze exact-dense MAT-SAB, AVX work, factorized mechanisms, or a redesigned
shared-mask state.

Candidate B asks one falsifiable question:

> Can the star-cycle selector be represented and evaluated with complete
> standard-distribution encrypted work that grows as Theta(r), while producing
> a closed one-mask, r-body PVW accumulator and avoiding an equivalent dense
> cost in decomposition, DFT, relinearization, key switching, or storage?

This work package answers that question before any C hot-path change.

## 2. Immutable Research Contract

- Target venue: CCS/USENIX Security class.
- Primary metric after mechanism admission: complete-SAB
  `T_bootstrap/r`.
- Baseline B0: repeated scalar SAB.
- Baseline B1: current exact-dense PVW/MAT-SAB.
- Candidate order: A, then B, then C.
- Production hot-path permission remains `false` in this work package.
- A finite-field model proves neither RLWE security nor concrete noise.
- A count of vector ciphertext objects is not a complexity result. Counts must
  include their polynomial components and all online transforms.
- No new dependency is permitted.

## 3. Source-Anchored Current Mechanism

For a PVW ciphertext with `k` masks and `r` bodies, order coordinates as

```text
(a_0, ..., a_{k-1}, b_0, ..., b_{r-1}).
```

The secret is a `k x r` matrix `S`. Current sampling in
`src/mosfhet/src/pvwtmlwe.c` chooses every mask uniformly, chooses a fresh
body error for every body, and forms

```text
b = a S + e + m.
```

The phase map is therefore

```text
P(a,b) = b - a S.
```

`src/mosfhet/src/mattrgsw.c` creates `T(k+r)` independent PVW encryptions of
zero and adds the gadget-scaled selector to the matching diagonal coordinate.
For one gadget level, its coefficient-wise public matrix is

```text
C = mu h I_(k+r) + V [I_k | S] + [0 | E],
```

where:

- `mu` is the encrypted selector bit;
- `V` is the independently sampled mask matrix;
- `E` is an independently sampled `(k+r) x r` body-error matrix; and
- `h` is the gadget weight.

For the target `k=1`, let `m=r+1`, `v` be the mask column, and
`w^T=(1,s_0,...,s_(r-1))`. Then

```text
C = mu h I_m + v w^T + [0 | E].
```

Given decomposed input digits `d`, the current external product computes

```text
d^T C = mu h d^T + (d^T v) w^T + d^T[0 | E].
```

The rank-one term cancels under the phase map, leaving the selected input
phase plus accumulated error. The implementation nevertheless has to process
all `m` input rows and all `m` output coordinates. At `k=T=1`, the dense
contraction contains `m^2=(r+1)^2` polynomial add-multiply terms.

## 4. Why The Noiseless Rank-One View Is Insufficient

The formula `mu I + v w^T` omits the independently sampled error matrix. It
also hides three evaluator-visibility constraints:

1. `mu` is not a public scalar. It appears only through encrypted diagonal
   gadget terms.
2. `w` contains the PVW secret and cannot be published as a plaintext factor.
3. The first diagonal mask coordinate contains both randomization and the
   hidden selector contribution, so the evaluator cannot generally separate
   `v` from `mu`.

Factoring only `v w^T` leaves the dense contraction `d^T E`. Moving the
secret multiplication into a key switch or relinearization is not a saving
unless the complete replacement, including decomposition, transforms,
evaluation keys, noise, and output conversion, is below the dense baseline.

## 5. Exact-Distribution Rank Obstruction

The implementation ring is

```text
R = Z_(2^w)[X] / (X^N + 1).
```

Use the multiplicative map

```text
phi: R -> GF(2),  phi(f) = f(1) mod 2.
```

It is well defined: coefficient reduction modulo two is a ring homomorphism
and `X^N+1` evaluates to `1+1=0` in GF(2). This avoids the invalid operation
of treating an arbitrary raw coefficient extraction as multiplicative.

The current sampler applies `generate_normal_random` followed by
`double2torus` independently to every error coefficient and every body row.
For target `sigma=2^-50`, the following explicit uniform-word inputs witness
both output parities under the source formula:

```text
(0x9e3779b97f4a7c15, 0xa36a9465a325da06) -> -11446 (even)
(0x3c6ef372fe94f82a, 0x751fde9874b8c709) ->   1791 (odd)
```

Under the sampler's intended pseudorandom-byte model, these finite inputs
have nonzero support and calls use fresh words. Choose coefficient parities
so each diagonal error polynomial in the first `r` rows has odd coefficient
sum, while off-diagonal entries and the final row have even coefficient sum.
No coefficient is required to equal zero. The resulting supported
parity-pattern matrix maps under `phi` to `[I_r;0]`, has an `r x r` identity
minor, and has rank `r`.

Any exact ring factorization

```text
E = U V
```

with inner dimension `q < r` maps to

```text
phi(E) = phi(U) phi(V),
```

whose field rank is at most `q`. It cannot produce the supported rank-`r`
image witness. Such a factorization therefore cannot equal the complete
current MAT_TRGSW distribution under the stated sampler model.

This is an exact representation and support statement. It is not a general
security impossibility theorem. A correlated or low-rank error distribution
is a different cryptographic mechanism and requires its own assumption,
reduction, and noise analysis.

If `q >= r`, a generic dense two-sided evaluation uses

```text
(r+1)q + qr
```

factor contractions before diagonal and conversion costs. At `q=r`, this is
`2r^2+r`, compared with `(r+1)^2` dense contractions. A full-rank
generic factor layout does not provide the intended asymptotic saving and can
be strictly worse. This count is not a universal arithmetic lower bound:
sparse, normalized, or permutation factors may skip products or fuse the
diagonal. Such a structured full-rank alternative must be registered and
costed separately.

## 6. Four-Family Representation Boundary

Candidate B starts from the semantic decomposition

```text
M =
  M_shared_row
  + M_shared_column
  + M_diagonal
  + M_cycle.
```

Stage203 already established the `4r` semantic support. Merely renaming those
rows as four families is not a new mechanism.

A standard PVW ciphertext is a module element with one ring scalar acting on
its shared mask and every body. It cannot apply `r` independent input digits
component-wise to `r` bodies while retaining one common output mask. Thus a
family with lane-dependent diagonal or cycle coefficients needs either:

- one full PVW operator row per independent input digit, which restores
  Theta(r^2) polynomial components and products;
- a lane-pair state with multiple masks, which fails current PVW closure
  without a conversion;
- an encrypted factor plus a complete relinearization/key-switch mechanism;
  or
- a changed structured/correlated distribution.

The last three alternatives change the intermediate state or cryptographic
mechanism and must be accounted for explicitly. They cannot be credited as a
standard-PVW factorization by object-counting alone.

## 7. Candidate B Mechanism Variants

| ID | Mechanism | Admission condition | Expected disposition |
| --- | --- | --- | --- |
| B0 | Exact factorization of the complete current MAT_TRGSW distribution with `q=O(1)` | Phase, full distribution support, closure, and Theta(r) complete work all hold. | Test directly; rank obstruction forces `q>=r` and predicts rejection. |
| B1 | Factor only the noiseless `v w^T` term and retain dense independent errors | Complete work beats dense after all `d^T E` work is counted. | Reject if dense error work remains Theta(r^2). |
| B2 | Correlated or low-rank errors | A new security assumption/reduction and noise recurrence are provided. | Not standard PVW; route to Candidate C intake. |
| B3 | Encrypted factors plus relinearization/key switching | Final state is closed and all key, transform, noise, and online costs are Theta(r) with a positive Amdahl projection. | Admit only with an explicit construction; otherwise reject B. |
| B4 | Lane-pair intermediate followed by shared-mask conversion | Conversion is public, secure, closed, and does not restore dense cost. | Existing closure evidence predicts rejection unless a new conversion is supplied. |

## 8. Executable Gate

The gate uses deterministic finite-field controls for `r=2,4,6`.

### Positive controls

- Build the exact standard selector matrix and verify
  `phase(d^T C) = mu h phase(d) + d^T E`.
- Use explicit sampler parity witnesses and the multiplicative
  parity-evaluation image of a supported ring witness
  and verify rank `r`.
- Verify dense work counts match `(r+1)^2`.

### Negative controls

- For every `q=1,...,r-1`, construct a GF(2) image factorization of rank
  exactly `q` and verify that the image-rank test admits it.
- Remove or alter one error coordinate and verify the phase/noise identity
  detects the mutation.
- Verify that retaining a dense error matrix after noiseless factorization
  still has a quadratic polynomial-component count.

### Decision rule

Candidate B is admitted to `ADVERSARIAL_CHECKER_PASS` only if a registered
mechanism:

1. represents the complete standard distribution, not only the noiseless
   message action;
2. preserves one-mask r-body closure with cycle/neighbor terms;
3. has `q=O(1)` for the direct dense-factor path, or another explicitly
   counted Theta(r) complete mechanism;
4. does not move dense work to key switching, relinearization, or conversion;
5. has a secret-independent public shape; and
6. leaves a positive complete-SAB Amdahl projection.

Registration requires both a hash-bound artifact package and a
mechanism-specific semantic checker registered in code. A package that only
labels its own proof rows `PASS` cannot admit Candidate B.

If B0 fails and no B3/B4 construction satisfying all six conditions is
registered, record:

```text
REJECT_CANDIDATE_B_EXACT_STANDARD_PVW_FACTORIZATION_ROUTE_TO_C
```

Candidate C then becomes `INTAKE`. The overall Goal remains active and
production hot-path permission remains `false`.

## 9. Evidence And Claim Boundary

The gate will produce:

- source mapping;
- scoped literature claims with full-text versus metadata-only support levels;
- explicit sampler-support witnesses;
- phase-identity rows;
- rank controls;
- factor-cost rows;
- mechanism disposition rows;
- proof-gate rows;
- exact reproduction commands;
- input-manifest and execution-environment records;
- artifact checksums;
- state, hypothesis, run-log, manifest, and checklist updates.

Primary-source boundary:

- Guimaraes and Pereira,
  `https://eprint.iacr.org/2025/686`, defines the target sparse amortized
  bootstrapping algorithm. It does not define this repository's CM/PVW
  factorized selector.
- Bergerat et al.,
  `https://eprint.iacr.org/2025/2112`, defines common-mask ciphertexts and
  type-preserving CM-GGSW operations. Its standard CM-GGSW size and published
  external-product work retain a quadratic `(k+r)^2` lane factor.
- Brakerski, Gentry, and Halevi,
  `https://eprint.iacr.org/2012/565.pdf`, establishes packed/PVW-style
  ciphertext and relinearization machinery, but does not provide the target
  rank-one selector evaluation.
- Chillotti et al.,
  `https://eprint.iacr.org/2018/421`, provides the standard
  GGSW-times-GLWE external-product closure boundary.

These sources establish prior-art and mechanism boundaries. The absence of a
matching construction in the reviewed set is not a novelty proof.

Allowed conclusion:

> The current independently randomized MAT_TRGSW distribution does or does
> not admit the tested exact low-rank factorized realization.

Blocked conclusions:

- general impossibility of all compact MAT-SAB designs;
- RLWE security from finite-field tests;
- a new bootstrapping algorithm before Candidate C or another admitted
  construction passes the complete research pipeline;
- complete-SAB speedup from this mechanism gate; and
- novelty without a verified related-work comparison.

## 10. Implementation Boundary

This work package may create Python research models, tests, Markdown, CSV,
state transitions, and reproducibility metadata. It must not modify the C
implementation, public C headers, `main.c`, or `Makefile`.
