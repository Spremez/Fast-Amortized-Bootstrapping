# Candidate C Rank-Bounded State Gaps

## Current Boundary

Candidate C is the active `INTAKE` route after the recorded Candidate B
terminal decision. Task 1 creates no campaign transition and changes no
production source or ledger.

Production hot-path permission: `false`.

The current state equations and schedule obligations are source anchored.

All claim gates remain `BLOCKED`.

## Anchored Facts

- The current binary schedule repeats one RGSW monomial butterfly followed by
  `sub_a` for each of `h` rounds and then executes one final RGSW monomial.
- CMUX forms a difference, applies
  `mat_trgsw_mul_pvmtmlwe_DFT`, and adds the selected contribution.
- NCMUX applies the minus-one automorphism to its second input before CMUX.
- Binary `sub_a` applies `pvmtmlwe_mul_by_xai` independently at each public
  accumulator index.
- The current exact-dense PVW output shape has one shared mask, represented by
  `rho=0`.
- Stage203 fixes four semantic star-cycle equation classes.
- Stage345 identifies the historical scoped exact-dense binary baseline. It
  does not compare a Candidate C implementation.

## Equation Gaps

The Task 1 state is

```text
a_q = a_shared + sum_(t=1..rho) lambda[q,t] delta_a[t]
phase_q = b_q - a_q s_q
rho = rank({a_q-a_0 : q=1,...,r-1})
lambda[0,t]=0
```

Open finite obligations are:

1. define the coefficient domain and canonical rank algorithm used by the
   checker;
2. construct exact CMUX and NCMUX mask-direction witnesses;
3. measure `rho` after every butterfly bit and complete RGSW monomial;
4. propagate the state through every `sub_a` and full binary `sparse_mul`
   boundary;
5. verify lane phases against an independent scalar recurrence; and
6. include negative controls that make rank or phase checks fail.

Task 1 uses symbolic `epsilon_E_q` terms only to mark where an encrypted
operator contributes phase error. It derives no recurrence or bound.

## Variant Gaps

`C0 = independent_lane_directions` is only a negative control. The checker
must observe the independent difference rank rather than silently projecting
it to two directions.

`C1 = rank_two_basis_with_public_lambda` is admissible only if `rho<=2`
survives the registered schedule without conversion. No such closure result
is recorded here.

`C2 = rank_two_basis_with_periodic_public_relinearization` may invoke a
conversion only after a public block of butterfly steps. The missing
relinearization specification must define:

- its input and output state;
- public metadata and evaluation material;
- exact lane-phase preservation;
- resulting rank;
- key and scratch material;
- invocation frequency; and
- complete counted work.

A conversion after every CMUX is outside C2.

## Claim Gaps

- `security`: `BLOCKED`
- `noise`: `BLOCKED`
- `amdahl`: `BLOCKED`
- `kernel`: `BLOCKED`
- `full_sab`: `BLOCKED`
- `novelty`: `BLOCKED`
- `production`: `BLOCKED`

No Task 1 artifact upgrades any of these gates. The only Task 1 conclusion is:

> The current state equations and schedule obligations are source anchored.
