# Stage316 Plan For Stage317

1. Add an isolated AVX512 `ifft_batch5` symbol or stop with a concrete register
   pressure/ABI reason.
2. Add a microbench comparing five existing `ifft` calls against `ifft_batch5`.
3. Add a correctness check that compares every output row against the existing
   single-row transform.
4. Required promotion gate: >= 0.107769 IFFT component reduction.
5. Only after Stage317 passes may Stage318 wire the symbol into MAT direct
   sub-DTF under an explicit flag.
