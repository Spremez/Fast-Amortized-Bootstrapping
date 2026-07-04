# Stage290 Direct-Output DFT Model

Baseline `polynomial_torus_to_DFT` converts torus coefficients into the
FFT processor reverse buffer, runs an in-place reverse FFT, and copies the
double buffer into the destination DFT polynomial. Stage289's array wrapper
kept the same arithmetic and added a scratch-to-output copy.

`MAT_TRGSW_DFT_ARRAY_DIRECT_OUTPUT` writes converted doubles into
`out[i]->coeffs` and calls `ifft` in place on that destination. The arithmetic
count is unchanged, but one N-double copy per converted row is removed. The
candidate is therefore expected to help only when the removed copy is visible
relative to the reverse FFT cost.
