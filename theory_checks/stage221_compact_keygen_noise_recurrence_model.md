# Stage221 Compact Keygen Noise Recurrence Model

For each encrypted compact selector row, Stage220 measured a deterministic
prototype noise bound `eta_row`. Stage221 uses a conservative independent-row
proxy over the SAB schedule:

```text
steps(N) = (h + 1) * r_prec * N = 40 * 7 * N
sigma_dense  = sqrt(steps(N) * dense_rows  * eta_row^2)
sigma_active = sqrt(steps(N) * active_rows * eta_row^2)
```

The gate is relative: `sigma_active <= sigma_dense` and the L1 proxy is also no
worse. This is enough to admit isolated compact external-product experiments,
but not enough for a production security theorem or a complete-SAB speedup
claim. Later stages must add phase equivalence, multi-seed noise, and full SAB
`T_bootstrap/r` benchmarks.
