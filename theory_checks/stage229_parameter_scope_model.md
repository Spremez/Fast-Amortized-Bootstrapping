# Stage229 Parameter Scope Model

PVW/MAT-SAB changes the ciphertext object from independent scalar RLWE bodies
to one shared-mask MAT/PVW object with `r` body lanes. Therefore the correct
comparison for the intended algorithm is amortized complete bootstrapping:

```text
T_per_bit_scalar = T_scalar_repeated / r
T_per_bit_pvw    = T_pvw / r
speedup          = T_per_bit_scalar / T_per_bit_pvw
```

Because both sides are divided by the same `r`, recorded speedup is equivalent
to `T_scalar_repeated / T_pvw`, but the interpretation is per processed
plaintext lane/bit. This is not the same as saying one PVW call has lower
single-output latency than one scalar SAB call.

Parameter generalization is an empirical and semantic claim:

- empirical: same-backend complete-SAB A/B, repeated runs, noise, and resource;
- semantic: the selector/key format must support the branch being claimed.

Current evidence supports binary parameters only. Non-binary PVW-SAB remains
blocked because sign/coefficient selector semantics require a separate design.
The exact dense MAT/PVW route remains empirically useful, but theoretical
optimality of r-body MAT-RLWE SAB is still open.
