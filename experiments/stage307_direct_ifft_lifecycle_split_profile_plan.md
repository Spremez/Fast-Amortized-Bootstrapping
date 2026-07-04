# Stage307 Experiment Plan

1. Build the complete include-zero target benchmark with direct sub-DTF enabled.
2. Enable `MAT_TRGSW_SPLIT_PROFILE` and `MAT_TRGSW_DIRECT_DFT_PROFILE`.
3. Require target full correctness to pass.
4. Check direct-profile rows against split-profile sub-call rows.
5. Route Stage308 to the dominant direct lifecycle subcomponent only.
