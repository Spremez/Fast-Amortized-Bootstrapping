# Stage189 Closed-State Linear Model

Let the compact output after one CMUX step contain lane-local masks `a_q` and
bodies `b_q`. Standard PVW_TMLWE requires one shared mask `a*` and r bodies.
For lane q, phase preservation without changing the secret relation requires:

```text
b'_q - S_q a* = b_q - S_q a_q
```

If `b'_q` is not allowed to include the secret-dependent correction
`(a* - a_q) * s_q`, then a public projection `a* = G(a_0,...,a_{r-1})` must
satisfy:

```text
S_q G = S_q E_q   for every q
```

where `E_q` selects lane q's mask. For full-rank `S_q`, this implies
`G = E_q` for every q. For r>1 the `E_q` matrices are different, so no single
public shared-mask projection exists. The generated rank probe instantiates
this over GF(65537) with full-rank monomial secret multiplication matrices.

This is a T2/API result, not a T1 key-distribution proof and not a T4 noise
bound.
