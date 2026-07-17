# Candidate C Rank-Bounded Shared-Mask State Model

## 1. Scope

This Task 1 model fixes a state representation and maps it onto the current
binary SAB schedule. It defines inputs for later finite rank-growth checks.
It does not establish cryptographic assumptions, an error bound, a conversion
construction, or an implementation result.

Production hot-path permission: `false`.

The current state equations and schedule obligations are source anchored.

## 2. State Invariant

For each lane `q`, represent its mask by

```text
a_q = a_shared + sum_(t=1..rho) lambda[q,t] delta_a[t]
```

and define its phase by

```text
phase_q = b_q - a_q s_q.
```

The state is

```text
(a_shared, delta_a[1..rho], lambda, b[0..r-1]).
```

The coefficients `lambda[q,t]` are public. Fix

```text
lambda[0,t]=0
```

and use lane zero as the reference, so

```text
rho = rank({a_q-a_0 : q=1,...,r-1}).
```

This choice is only a representation normalization. For any reference lane
`u`,

```text
a_q-a_u = (a_q-a_0) - (a_u-a_0)
a_q-a_0 = (a_q-a_u) - (a_0-a_u).
```

Each difference family spans the other. Therefore changing the reference lane does not change rho.

The later finite checker must state its coefficient domain and rank algorithm.
Task 1 does not silently identify polynomial-module rank with a field rank.

## 3. Rank Accounting

For a rank-bounded state `X`, let `Delta(X)` be the span of its lane-mask
differences. For an encrypted operator `E`, let `nu_E` denote newly introduced
independent mask directions modulo the input difference span. Let
`epsilon_E_q` name its lane-q phase error term without assigning a
distribution or bound.

The current exact-dense `mat_trgsw_mul_pvmtmlwe_DFT` path materializes the
standard shared-mask PVW output shape. For the current-format state this is

```text
rho=0.
```

A proposed compact operator may introduce lane-dependent mask directions.
Its finite checker must construct the output masks, compute `nu_E`, and apply
the corresponding rank rule. Storage labels or object counts cannot substitute
for this calculation.

## 4. CMUX Edge

Source anchors:

- `src/sab_pvw.c`: `void sab_pvw_CMUX(`
- `src/mosfhet/src/mattrgsw.c`:
  `void mat_trgsw_mul_pvmtmlwe_DFT(`

The current source forms `d=in2-in1`, evaluates the encrypted selector on
`d`, and adds `in1`. The public subtraction, addition, and schedule wiring are
linear; the encrypted selector action is not public. For selector bit `mu`,
the required phase equation is

```text
phase'_q =
  phase1_q + mu (phase2_q-phase1_q) + epsilon_CMUX_q.
```

A conservative affine-span rule is

```text
rho' <= min(r-1, rho1+rho2+nu_CMUX).
```

The current exact-dense output closes with `rho=0`. A compact CMUX must expose
any new directions and then feeds a direct butterfly output or its public
caller.

## 5. NCMUX Edge

Source anchor:

- `src/sab_pvw.c`: `void sab_pvw_NCMUX(`

NCMUX separates three operation classes:

1. Public `gen=2N-1` determines `tau_-1`, and `polynomial_permute` applies
   that public coefficient permutation. Public permutation and wiring route
   the evaluated result to the CMUX right-hand input.
2. `pvmtmlwe_keyswitch` using `sab->aut_minus1` applies automorphism
   evaluation-key work to the publicly permuted ciphertext. This
   evaluation-key/key-switch work is not public linear work.
3. `sab_pvw_CMUX` evaluates the encrypted MAT_TRGSW selector. This
   encrypted-selector CMUX is not public linear work.

The phase equation for the complete NCMUX edge is:

```text
phase'_q =
  phase1_q
  + mu (tau_-1(phase2_q)-phase1_q)
  + epsilon_NCMUX_q.
```

Record all compact automorphism/rekey and selector directions in `nu_NCMUX`:

```text
rho' <= min(r-1, rho1+rho2+nu_NCMUX).
```

The current exact-dense output closes with `rho=0`. The NCMUX output is the
wraparound branch of the butterfly.

## 6. Butterfly And RGSW Monomial Edges

Source anchor:

- `src/sab_pvw.c`:
  `static uint64_t sab_pvw_RGSW_monomial_mul_state(`

For public bit index `bit`, the source sets `power=2^bit`. Wraparound outputs
use NCMUX:

```text
phi'_(q,j) =
  phi_(q,j)
  + mu_bit (tau_-1(phi_(q,N-power+j))-phi_(q,j))
  + epsilon_(bit,q,j).
```

Direct outputs use CMUX:

```text
phi'_(q,j+power) =
  phi_(q,j+power)
  + mu_bit (phi_(q,j)-phi_(q,j+power))
  + epsilon_(bit,q,j+power).
```

Each output applies its CMUX or NCMUX rank rule. Write the complete recurrence
abstractly as

```text
phi^(bit+1)_(q,j) =
  B_(mu_bit,2^bit)(phi^bit_q)_j + epsilon_(bit,q,j).
```

The RGSW monomial output rank is the maximum output-state rank after the final
bit. A finite checker must retain the per-bit trace because temporary growth
determines whether C2 has a usable public block boundary.

The current exact-dense butterfly stays at `rho=0`. A compact butterfly may
introduce lane-dependent mask directions through its encrypted CMUX/NCMUX
operators.

## 7. Rotation And Binary sub_a Edges

Source anchors:

- `src/sab_pvw.c`: `static void sab_pvw_sub_a_binary_to(`
- `src/mosfhet/src/pvwtmlwe.c`: `void pvmtmlwe_mul_by_xai(`

For a public exponent `u`, define the lane-uniform public map

```text
L_u(f) = X^u f.
```

The rotation applies `L_u` to every mask and body polynomial:

```text
phase'_q
  = X^u b_q - (X^u a_q)s_q
  = X^u phase_q.
```

It also gives

```text
a'_shared = X^u a_shared
delta'_a[t] = X^u delta_a[t]
lambda'[q,t] = lambda[q,t]
rho' <= rho.
```

Thus rotation introduces no new lane-mask basis direction. Binary `sub_a`
uses exponent `u=a[idx]` independently at every public accumulator index and
feeds the next RGSW monomial.

The current exact-dense rotation remains at `rho=0`. The compact
representation obligation is to rotate every stored basis polynomial, not to
collapse the basis.

## 8. Real Binary sparse_mul Schedule

Source anchor:

- `src/sab_pvw.c`: `void sab_pvw_sparse_mul_binary(`

The source schedule is

```text
repeat [RGSW monomial, sub_a] h times, then RGSW monomial.
```

The future checker must propagate phase equations and rank records across
every edge in that order. It must not replace the complete schedule with one
isolated CMUX result.

## 9. Stage203 Semantic Inputs

Stage203 records these four exact equation classes:

```text
mask_output_from_body_input
body_output_from_mask_input
lane_self_body_interaction
lane_neighbor_body_interaction
```

They constrain selector semantics for later Candidate C operators. They do not
construct a compact encrypted operator, bound `nu_E`, or provide a conversion.

## 10. Finite Variant Register

Exactly three variants are registered:

```text
C0 = independent_lane_directions
C1 = rank_two_basis_with_public_lambda
C2 = rank_two_basis_with_periodic_public_relinearization
```

C0 is the negative control. Independent nonreference lane directions must
produce `rho=r-1`.

C1 must maintain `rho<=2` through the registered schedule with public
`lambda` and no conversion.

C2 may carry measured temporary growth only until a public block of butterfly
steps ends. A future registered relinearization must then restore `rho<=2`
without changing any lane phase. Invoking it after every CMUX is forbidden.

Task 1 does not assert that C1 or C2 satisfies these requirements.

## 11. Claim Boundary

The security, noise, Amdahl, kernel, full-SAB, novelty, and production gates
are `BLOCKED`. Stage345 is referenced only as the historical exact-dense
baseline. No Candidate C comparison or promotion follows from this model.
