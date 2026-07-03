# Stage165 Closed Full-MAT Streaming Model

The current r=6 path stores all `(1+r)` decomposed rows and DFT rows, then uses
a MAT-aware tiled AVX512 kernel to accumulate all output polynomials. A
row-streamed implementation can reduce scratch lifetime and row-array traffic,
but it repeatedly touches the output DFT polynomials and does not use the
current register-tiled r>4 AVX512 addmul.

Expected tradeoff:

- possible win: less scratch row storage and simpler lifecycle;
- possible loss: more output read/write traffic and loss of multi-row tiled
  AVX512 accumulation.

The microbench decides this empirically under exact torus-output equivalence.
