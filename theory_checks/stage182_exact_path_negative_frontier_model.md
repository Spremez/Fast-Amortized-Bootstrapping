# Stage182 Negative Frontier Model

Let `s_i` be the full-SAB share of component `i`. A local component speedup
`x_i` can at most provide:

```text
S_full <= 1 / ((1 - s_i) + s_i / x_i)
```

Stage180 derived the minimum component speedups needed for a 3% complete-SAB
gain:

- sub-decompose: `1.389195069x`
- torus-to-DFT rows: `1.208076492x`
- addmul from decomposed DFT rows: `1.151228774x`

Stage181 tested the most direct AVX512 sub-decompose candidate and observed a
combined-current speedup of `0.972794296x`,
which is a regression. Therefore no full-SAB gate is justified for that
candidate.
