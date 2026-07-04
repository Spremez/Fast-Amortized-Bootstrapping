# Stage308 IFFT/Digit Route Selection

Decision: `PASS_STAGE308_IFFT_BACKEND_LOWLEVEL_REQUIRED_DIGIT_PATH_NEXT`.

No behavior-changing variant is introduced. The near-term implementation route
is `stage309_digit_to_double_avx512_candidate`; the high-risk backend route is
`stage310_spqlios_batched_ifft_design`.
