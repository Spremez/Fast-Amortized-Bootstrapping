# Stage317 Plan For Stage318

1. Implement an isolated `ifft_batch5_tile32` candidate or record a concrete
   assembly-level impossibility.
2. Benchmark it against five existing `ifft` calls with the same buffers and
   tables.
3. Verify row-wise output equivalence for all five rows.
4. Require >= 0.107769 isolated IFFT component reduction.
5. Do not connect the candidate to `mat_trgsw_sub_decompose_DFT_direct` until
   the isolated gate passes.
