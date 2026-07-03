# Stage112 Shared-Mask Body-Linear Counterexample

Date: 2026-07-03

## Phase Invariant

For a single shared-mask row with decomposition digit `d`, mask `A`, body
`B_q = A*s_q + m_q`, and lane secret `s_q`, the dense contribution to
lane `q` is:

```text
d * (B_q - A*s_q) = d*m_q
```

If the row is needed for one lane but the off-lane body term is dropped
while the shared mask contribution remains, the off-lane phase becomes:

```text
d * (0 - A*s_q)
```

which is not a zero encryption in general.

## Concrete Counterexample

With `d=2`, `A=7`, `s1=5`, and expected
off-lane message `0`, dropping the off-lane body gives phase
`-70` instead of `0`.

Therefore body-linear external product is not safe as a loop-only change
under the current shared-mask `MAT_TRGSW_DFT` format.