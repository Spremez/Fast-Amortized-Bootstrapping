# Stage307 MAT_TRGSW_DIRECT_DFT_PROFILE

Flag: `MAT_TRGSW_DIRECT_DFT_PROFILE=true`.

Decision: `PASS_STAGE307_DIRECT_IFFT_LIFECYCLE_PROFILE_RECORDED`.

This is instrumentation only. It adds no new ciphertext format and no new
optimized path. The scalar SAB path and default PVW/MAT-SAB path remain
unchanged unless the profile flag is explicitly enabled.
