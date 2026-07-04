# Stage288 MAT EP Split Profile Model

The split profile partitions the currently selected MAT EP timer into:

1. `decompose`: torus diff/decomposition or normal decomposition;
2. `torus_to_dft`: conversion of decomposed rows to DFT;
3. `dense_from_dec`: exact dense MAT multiplication after decomposition.

The result is instrumentation evidence. It can select an isolated microbench
target, but final acceleration still requires unprofiled complete-SAB
`T_bootstrap/r` A/B and noise/resource gates.
