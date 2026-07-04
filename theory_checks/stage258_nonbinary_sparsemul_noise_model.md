# Stage258 Non-Binary Sparse_Mul Noise Model

Stage258 measures a pairwise reference error, not absolute decryption failure.
For each PVW lane and scalar reference lane, the recorded torus error is:

```text
e_pair[q,i] = phase_pvw[q,i] - phase_scalar[q,i]
```

The gate requires zero pair failures over all recorded coefficients. This proves
that the PVW/MAT sparse_mul implementation is algebraically aligned with the
scalar reference for the tested sparse_mul scope.

This does not prove the final SAB failure rate because complete bootstrapping
adds blind rotation scheduling, extraction, optional packing/key switching, and
the target message decoding boundary. Those remain Stage259+ gates.
