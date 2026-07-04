# Stage228 Counter-Driven Kernel Model

For a component with full-SAB share p, a local speedup s changes total time by
`1 / (1 - p + p/s)`. Stage228 requires at least a 3% projected complete-SAB
`T_bootstrap/r` gain before permitting a new exact hot-path implementation.

Stage226 shows small backend counter improvements, but this supports the
existing backend FromDFT-add route rather than a new MAT addmul rewrite.
