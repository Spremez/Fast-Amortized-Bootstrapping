# Stage209 MAT-EP Split Model

The current exact MAT external product can be split as:

```text
combined_current ~= sub_decompose + torus_to_DFT_rows + addmul_from_dec_dft
```

The split probes are isolated and may not sum exactly to the combined path.
They support only Amdahl-style route selection. Any candidate still needs a
flag-only implementation gate, correctness, noise, resource, and full SAB
`T_bootstrap/r` A/B.
