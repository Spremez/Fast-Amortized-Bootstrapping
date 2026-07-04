# Stage308 SPQLIOS IFFT Feasibility Model

Stage307 measured the direct sub-DTF materialization split as:

- digit-to-double share: 0.481687
- ifft share: 0.504577

Although `ifft` is slightly larger, the current SPQLIOS interface exposes only
`void ifft(const void *tables, double *data)`. The existing multi-row wrapper
still loops over rows and calls the same single-buffer entry, and Stage289/290
already found those wrapper-level ideas neutral. Therefore a true IFFT
optimization is not a small MAT-SAB C-layer change; it requires a backend API
and likely assembly/model work.

The local next step is the digit-to-double path because it is nearly half of
the direct profile and already lives in `mattrgsw.c` under AVX512. Any promoted
candidate still needs staged correctness, Stage307-style component reduction,
and complete SAB `T_bootstrap/r` A/B before it becomes a bootstrapping speed
claim.
