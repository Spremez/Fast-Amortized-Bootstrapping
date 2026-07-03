# Native Split Counter Microbench for Current r=6 Path

This is not a production implementation variant. It is an isolated probe for
the current exact r=6 path.

Measured call boundaries:

```text
mat_ep_subdecomp      -> mat_trgsw_mul_pvmtmlwe_sub_DFT
from_dft_materialize -> pvmtmlwe_from_DFT_add
```

Decision: `PASS_STAGE170_NATIVE_SPLIT_COUNTERS_RECORDED`.

Allowed claim level:

```text
component native counter attribution
```

Blocked claim level:

```text
theoretical optimality
complete-SAB speedup beyond Stage169
paper-level novelty
```
