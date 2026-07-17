# Candidate C Concrete Operator Tensor Gate

## Scope

Task 3A constructs and checks two concrete selector objects, `K_0` and
`K_1`, in

```text
R_257,8 = GF(257)[X]/(X^8+1).
```

Every polynomial is an explicit length-8 coefficient vector. Products use
exact negacyclic convolution, including the sign change on terms wrapping
past degree 7. This is a finite equation and structural-count gate. It is not
a security proof, a noise proof, a production-ring correctness result, a
performance result, or a complete-SAB speedup.

## Orientation And Phase Equation

For `rho=min(2,r-1)` and `d=rho+1`, inputs are ordered

```text
M_0,...,M_(d-1),B_0,...,B_(r-1).
```

The public matrix is fixed for both selector values:

```text
Lambda[q,0] = 1
Lambda[0,u] = 0 for u>0
Lambda[q,:] = (1,q,q^2) for q>0 when rho=2
rank((I-1 e_0^T) Lambda) = rho.
```

For `rho=1`, the two rows are `(1,0)` and `(1,1)`. The phase projection is

```text
P_Lambda[q,M_u] = -Lambda[q,u] s_q
P_Lambda[q,B_j] = 1 if q=j and 0 otherwise.
```

The stored orientation is

```text
A_mu[level,output-mask-basis,input-component,coefficient]
B_mu[level,output-body-lane,input-component,coefficient].
```

Bodies are derived, rather than searched for, from

```text
B_mu[t,q,c] - s_q sum_v Lambda[q,v] A_mu[t,v,c]
  = mu h_t P_Lambda[q,c].
```

The registered finite gadget is `(1,16)`. Mask roots are deterministic
monomials that expose every basis row; they are not random finite witnesses.
The bodies are then fixed by the displayed identity. Separate `K_0` and
`K_1` objects cover every gadget level, input component, lane, and
coefficient basis direction.

## Joint Rank Orientation

For each polynomial, `C(A)` is its exact `8 x 8` negacyclic convolution
matrix. Stacking basis-output rows and concatenating all `(t,c)` blocks gives

```text
R_mu in GF(257)^(d*8 x ell*(d+r)*8).
```

Public lane mixing gives

```text
T_mu = (Lambda tensor I_8) R_mu
T_mu in GF(257)^(r*8 x ell*(d+r)*8).
```

The checker builds both sides of the common factorization:

```text
((L tensor I_8) T_mu)
  = ((L Lambda) tensor I_8) R_mu,
L = I-1 e_0^T.
```

It computes rank only after concatenating all levels and components. The
result is a field-expanded finite surrogate of module rank rho, not field
rank `rho`.

| r | rho | d | R_mu rows x columns | T_mu rows x columns | K_0 rank | K_1 rank | bound |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1 | 2 | 16 x 64 | 16 x 64 | 8 | 8 | 8 |
| 4 | 2 | 3 | 24 x 112 | 32 x 112 | 16 | 16 | 16 |
| 6 | 2 | 3 | 24 x 144 | 48 x 144 | 16 | 16 | 16 |

Controls include the exact-dense shared-mask tensor, a full-lane-rank C0
tensor, the common-Lambda rank-bounded tensor, and an `r=6` tensor whose two
levels have ranks 16 and 16 separately but rank 32 jointly. The latter proves
that per-level checks cannot replace the concatenated gate. A single body
coefficient mutation fails the same phase verifier. Noncanonical trailing
mask or body material is rejected before phase, rank, relation, or structural
accounting, so uncounted tensor entries cannot bypass the gate.

## Evaluator-Sample Relations

For one selector object at a time, `m=ell*(d+r)` and

```text
S_mu in GF(257)^(m x d*8)
M_mu,q in GF(257)^(m x 8).
```

Rows are `(level,input-component)`. A basis of the exact left kernel of
`S_mu` spans every scalar relation `z^T S_mu=0`. For each basis relation and
each lane, the checker computes `z^T M_mu,q` and records centered relation
coefficients, L1 and L2 norms, the centered retained-message gap, the
symbolic error multiplier, and registered error data when present.

`K_0` has `NO_RETAINED_MESSAGE_RELATION`. `K_1` has
`RELATION_RECORDED_NO_SECURITY_DECISION`: no distribution and no decision
inequality are registered, so modular containment failure cannot reject C1.
The shared-mask PVW and independent-mask dense controls likewise produce no
unsupported insecurity decision. A synthetic same-secret, zero-error object
with the registered inequality
`retained_gap > combined_error_bound` produces
`REGISTERED_SHORT_ERROR_RELATION_FAIL`. A body/message mutation changes the
diagnostic hash. This finite diagnostic is not a security proof.
It is not a universal impossibility theorem.

## Source Binding

Stage203 is classified only as
`SUPPORT_ONLY_NO_NUMERIC_COEFFICIENTS`. Its exact seven-column support schema
is accepted; adding a numeric coefficient column is rejected. Coefficients
for the concrete tensor do not come from Stage203.

| Binding | Classification | SHA-256 |
|---|---|---|
| `src/mosfhet/src/mattrgsw.c` | `EXACT_SOURCE` | `5da51089a748f7f1f54b56f81c2948ced14f0be4dd431bcffb2339af97c527fa` |
| `research/mat_sab/star_cycle_model.py` | `EXACT_SOURCE` | `f3cacf3bfd4df8f7c94352297a2acbb8052722e0ee1f88400ca3e63584e15d44` |
| `research/mat_sab/candidate_c_schedule.py` | `EXACT_SOURCE` | `4f07b3d1a8dcb55cdb2f0b7ea55d39d7d7c4184152f3ab56c04478dc618ada71` |
| Stage203 equation map | `SUPPORT_ONLY_NO_NUMERIC_COEFFICIENTS` | `5c146ee16c6c6cc2dac542e8c8ac4af74cd8bd017844929683190d5bdd2ab574` |
| Stage222 proof gate | `EXACT_ARTIFACT` | `6e08a0820bcf4d0d09499ae2553bb186e93fff1c2ad0da322e2bd019fc64bbbe` |
| Stage345 proof gate | `EXACT_ARTIFACT` | `39c717f67e87f2b230ad3c6f1010761f108870eb4ea61303b9a7ebb6022b8adf` |

The exact Task 3 schedule hash is
`a42e89d07964b289fa3ca06156a566887c4b4c76b6e68533dac32e59fd76f1b9`.
The MAT binding requires the current key-row formula, independent PVW sample
call, gadget injection entry point, and dense add-multiply loop.

## Structural Count

Counts include both `K_0` and `K_1`; online add-multiplies and transforms are
per selected operator evaluation.

| r | object | mask roots | body polynomials | gadget rows | decomposition inputs | add-multiplies | transforms | public mixing | bytes |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | C1 | 32 | 32 | 16 | 4 | 32 | 12 | 3 | 1024 |
| 2 | dense | 12 | 24 | 12 | 3 | 18 | 9 | 2 | 576 |
| 4 | C1 | 84 | 112 | 28 | 7 | 98 | 21 | 10 | 3136 |
| 4 | dense | 20 | 80 | 20 | 5 | 50 | 15 | 4 | 1600 |
| 6 | C1 | 108 | 216 | 36 | 9 | 162 | 27 | 16 | 5184 |
| 6 | dense | 28 | 168 | 28 | 7 | 98 | 21 | 6 | 3136 |

The concrete common-Lambda mask factorization still reconstructs
`ell*r*(d+r)` body polynomials per selector object. This is `Theta(r^2)`
body work and exceeds the exact-dense control for every registered `r`.
Consequently it cannot pass the structural-improvement gate.

## Terminal Result

For `r=2,4,6`, phase passes, joint rank passes, and the unregistered relation
diagnostic does not make a security decision. Complete structural counts are
nonpositive against exact dense. Recomputing the decision therefore gives

```text
REJECT_C1_NONPOSITIVE_STRUCTURAL_COST_TERMINAL
```

for all three values of `r`. Changing only the stored decision fails result
verification. This is a scoped rejection of this concrete no-conversion C1
operator, not a claim about all cryptographic constructions. The rejection
is terminal under Task 3A because relinearization cannot repair its
nonpositive structural cost. Task 3B is not entered, no C2 seed is routed,
and Tasks 3C, 4, and 5 are outside this work.
