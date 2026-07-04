# Stage307 Direct IFFT Lifecycle Model

The Stage305 `torus_to_dft` bucket in the direct sub-DTF path combines two
operations:

1. signed gadget digit extraction from `in2 - in1` directly into a double
   buffer;
2. one SPQLIOS reverse FFT (`ifft`) per MAT row.

Stage307 measures those two operations under a compile-time-only profile flag.
The profile covers `sub_calls` only. Normal MAT external products still use the
ordinary decomposition/DFT path, so their small contribution remains in
`MAT_TRGSW_SPLIT_PROFILE.dft_us` but not in the direct lifecycle profile.

Recorded dominant direct subcomponent: `ifft`.

This stage is not a latency claim. It chooses the next implementation target:
if `ifft` dominates, investigate row batching or lifecycle reduction around
SPQLIOS reverse FFT; if digit materialization dominates, investigate AVX512
digit extraction and output layout.
