# Stage185 Research Loop Gap Model

The current exact route gives an implemented MAT-RLWE/r-body SAB path, but not
an optimality theorem.

Known measured quantities:

```text
T_bootstrap/r speedup mean = 1.131666667x
T_bootstrap/r speedup min  = 1.115000000x
T_bootstrap/r CI low       = 1.095041982x
sub-decompose 3pct need    = 0.103963271;1.389195069
DFT rows 3pct need         = 0.169104610;1.208076492
addmul 3pct need           = 0.221723249;1.151228774
AVX512 sub-decomp combined = 0.972794296x
```

Interpretation:

1. Exact same-format PVW/MAT-SAB has scoped complete-SAB speedup.
2. Same-format count reduction is closed under the current coefficient-domain
   decomposition API.
3. Existing AVX512 sub-decompose and addmul-layout routes do not support
   theoretical optimality or further code work.
4. A stronger algorithmic result requires a proof-gated representation change,
   most likely compact/shared-output MAT-SAB, plus complete-SAB validation.
