# Stage155 Same-Format Frontier Model

For the current r-body MAT-RLWE SAB path, the sparse schedule still forces:

```text
CMUX/MAT_EP/from_DFT calls = (h+1) * r_prec * N = 40 * 7 * 2048 = 573440
NCMUX calls               = (h+1) * (2^r_prec - 1) = 40 * 127 = 5080
sub_a calls               = h = 39
```

The H14 backend path has already fused the add-back into backend
materialization, so `cmux_add_us=0` in the body profile. The remaining
`from_DFT` cost is therefore not a removable wrapper pass; it is the cost of
materializing every update in the same-format accumulator representation.

Consequences:

- same-format layout variants can only improve constants inside dense MAT EP
  or materialization;
- they do not reduce the schedule count;
- Stage153/154 show that the obvious local constant-factor branches are too
  small or negative at complete-SAB level;
- any larger improvement must change representation or reduce the number of
  materializations/dense terms.

This is not a proof of global optimality. It is a finite frontier bound for the
current code and representation.
