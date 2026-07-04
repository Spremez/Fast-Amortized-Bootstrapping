# Stage291 Sub-Decompose Direct-DFT Model

Stage288 measured MAT EP split time dominated by `torus_to_dft` and dense
multiply, with decompose still material. The selected SAB path has many more
`sub` MAT EP calls than normal calls. The direct-DFT candidate targets only
`mat_trgsw_mul_pvmtmlwe_sub_DFT`.

For each row, the old path writes a TorusPolynomial decomposition and then
reads it back to convert to the SPQLIOS reverse-FFT double buffer. The new path
computes the same signed decomposition digits directly as doubles and applies
`ifft` in place. It preserves the external-product algebra and should reduce
one torus write/read lifecycle per row. The FFT arithmetic and dense MAT
multiply are unchanged, so any benefit is bounded by the decompose+conversion
share of sub-DTF calls.
