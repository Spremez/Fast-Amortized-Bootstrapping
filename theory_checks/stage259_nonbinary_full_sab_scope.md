# Stage259 Non-Binary Full SAB Scope

The new path changes the SAB body update, not the final post-processing:

```text
binary:     sparse_mul_binary
nonbinary:  sparse_mul_nonbinary(mode in include_zero, ternary)
```

Post-processing is lane-wise and identical after the PVW accumulator has been
materialized into per-lane TLWE arrays. Therefore Stage259 tests only the new
body-route integration plus the existing post-processing boundary.

The proof obligation left open is target-parameter statistical correctness and
the primary performance endpoint:

```text
amortized latency = T_bootstrap / r
```
