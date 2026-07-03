# Stage162 Materialization Count Model

Date: 2026-07-03

The current production MAT EP API consumes torus-domain `PVW_TMLWE`, decomposes it, multiplies in DFT, and materializes the output before it can feed the next SAB bit. Stage156 shows that a naive DFT accumulator is not closed under exact gadget decomposition and SAB rotations.

Therefore, under the current exact torus-input API, each CMUX/NCMUX update has one DFT output that must be materialized for the next bit or final extraction. With `h=39`, `r_prec=7`, and `N=2048`, the lower bound is `40*7*2048 = 573440`, matching Stage160 observations.
