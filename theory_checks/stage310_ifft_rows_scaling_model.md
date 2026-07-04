# Stage310 IFFT Rows Scaling Model

The current direct DFT residual is almost evenly split between digit
materialization and SPQLIOS reverse FFT. Stage308 found no existing batch IFFT
API, so Stage310 measures whether the existing per-row loop already shows
enough sublinear per-row behavior to justify a C-level wrapper or cache-only
optimization.

The benchmark uses deterministic double buffers and records:

```text
ifft_est = time(copy rows + ifft rows) - time(copy rows)
```

This avoids repeatedly applying `ifft` to already-transformed buffers. A strong
C-level scaling signal would require rows=5 and rows=10 to improve per-row time
by at least 1.10x over rows=1. Without that, meaningful improvement requires a
true backend-level batch IFFT API/model/assembly change rather than another
wrapper around the same single-row entry.
