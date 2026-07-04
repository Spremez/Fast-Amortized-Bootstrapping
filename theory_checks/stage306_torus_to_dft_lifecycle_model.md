# Stage306 Torus-to-DFT Lifecycle Model

Stage306 narrows the MAT/PVW-SAB optimization target after Stage305. In the
current direct path, `mat_trgsw_mul_pvmtmlwe_sub_DFT` no longer writes a torus
decomposition scratch and then converts that scratch to doubles. It computes
signed decomposition digits directly into the SPQLIOS reverse-FFT buffer and
then calls `ifft` row by row.

For k=1, l=1, r=4, each MAT external product materializes rows = k + r = 5
DFT rows. Stage305 measured the direct split as:

- decompose share: 0.002047
- torus_to_dft share: 0.616652
- dense share: 0.378154

The `torus_to_dft` label in this direct path means digit-to-double
materialization plus one reverse FFT per row. Stage289 and Stage290 show that
wrapping the existing per-row FFT lifecycle, or only avoiding an output copy,
does not produce a stable promoted candidate. Therefore the next admissible
research step is not a general AVX512 dense rewrite; it is a direct-path split
profile that separates digit extraction, double materialization, and `ifft`.

The speed budget in Stage306 is a profile model only. A later implementation
must still pass complete-SAB `T_bootstrap/r`, correctness, noise, and resource
gates before it can be called a bootstrapping acceleration.
